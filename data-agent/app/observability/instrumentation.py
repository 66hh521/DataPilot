from __future__ import annotations

from functools import wraps
from time import perf_counter


def instrument_node(name: str, node):
    """Emit a structured timing event for every LangGraph node."""

    @wraps(node)
    async def wrapped(state, runtime):
        started = perf_counter()
        status = "success"
        try:
            result = await node(state, runtime)
            if isinstance(result, dict) and result.get("error"):
                status = "error"
            return result
        except BaseException:
            status = "error"
            raise
        finally:
            runtime.stream_writer(
                {
                    "type": "node_metric",
                    "node": name,
                    "status": status,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                }
            )

    return wrapped
