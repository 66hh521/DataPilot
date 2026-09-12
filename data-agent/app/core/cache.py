from __future__ import annotations

import asyncio
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from time import monotonic
from typing import Awaitable, Callable, Generic, TypeVar

from app.conf.app_config import app_config


T = TypeVar("T")


@dataclass(frozen=True)
class CacheResult(Generic[T]):
    value: T
    hit: bool


class AsyncTTLCache:
    """Small process-local TTL cache with request coalescing.

    Identical concurrent misses share one task, which prevents a burst of equal
    user questions from triggering duplicate model and retrieval calls.
    """

    def __init__(self, max_entries: int, ttl_seconds: float, enabled: bool = True):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        self._values: OrderedDict[str, tuple[float, object]] = OrderedDict()
        self._inflight: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._coalesced = 0
        self._evictions = 0

    async def get_or_compute(
        self, key: str, factory: Callable[[], Awaitable[T]]
    ) -> CacheResult[T]:
        if not self.enabled:
            return CacheResult(value=await factory(), hit=False)

        owner = False
        async with self._lock:
            now = monotonic()
            cached = self._values.get(key)
            if cached is not None:
                expires_at, value = cached
                if expires_at > now:
                    self._values.move_to_end(key)
                    self._hits += 1
                    return CacheResult(value=deepcopy(value), hit=True)
                self._values.pop(key, None)

            task = self._inflight.get(key)
            if task is None:
                task = asyncio.create_task(factory())
                self._inflight[key] = task
                self._misses += 1
                owner = True
            else:
                self._coalesced += 1

        try:
            value = await task
        except BaseException:
            if owner:
                async with self._lock:
                    self._inflight.pop(key, None)
            raise

        if owner:
            async with self._lock:
                self._inflight.pop(key, None)
                self._values[key] = (monotonic() + self.ttl_seconds, deepcopy(value))
                self._values.move_to_end(key)
                while len(self._values) > self.max_entries:
                    self._values.popitem(last=False)
                    self._evictions += 1
        return CacheResult(value=deepcopy(value), hit=not owner)

    async def clear(self) -> None:
        async with self._lock:
            self._values.clear()
            self._inflight.clear()

    def stats(self) -> dict[str, int | bool | float]:
        return {
            "enabled": self.enabled,
            "size": len(self._values),
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl_seconds,
            "hits": self._hits,
            "misses": self._misses,
            "coalesced": self._coalesced,
            "evictions": self._evictions,
        }


def build_cache_key(namespace: str, payload: object) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


llm_response_cache = AsyncTTLCache(
    max_entries=app_config.cache.max_entries,
    ttl_seconds=app_config.cache.ttl_seconds,
    enabled=app_config.cache.enabled,
)
retrieval_cache = AsyncTTLCache(
    max_entries=app_config.cache.max_entries,
    ttl_seconds=app_config.cache.ttl_seconds,
    enabled=app_config.cache.enabled,
)


def cache_stats() -> dict[str, dict]:
    return {
        "llm": llm_response_cache.stats(),
        "retrieval": retrieval_cache.stats(),
    }
