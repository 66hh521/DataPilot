import asyncio

import pytest

from app.core.cache import AsyncTTLCache


@pytest.mark.asyncio
async def test_cache_returns_deep_copied_hit():
    cache = AsyncTTLCache(max_entries=2, ttl_seconds=60)
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return {"items": [1]}

    first = await cache.get_or_compute("same", factory)
    first.value["items"].append(2)
    second = await cache.get_or_compute("same", factory)

    assert first.hit is False
    assert second.hit is True
    assert second.value == {"items": [1]}
    assert calls == 1


@pytest.mark.asyncio
async def test_cache_coalesces_concurrent_misses():
    cache = AsyncTTLCache(max_entries=2, ttl_seconds=60)
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return "done"

    results = await asyncio.gather(
        cache.get_or_compute("same", factory),
        cache.get_or_compute("same", factory),
    )

    assert [result.value for result in results] == ["done", "done"]
    assert calls == 1
    assert cache.stats()["coalesced"] == 1
