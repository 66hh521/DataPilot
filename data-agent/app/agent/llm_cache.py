from __future__ import annotations

from app.core.cache import CacheResult, build_cache_key, llm_response_cache


async def cached_ainvoke(namespace: str, chain, payload: dict) -> CacheResult:
    key = build_cache_key(namespace, payload)
    return await llm_response_cache.get_or_compute(
        key, lambda: chain.ainvoke(payload)
    )
