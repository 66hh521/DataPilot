from types import SimpleNamespace

import pytest

from app.observability.instrumentation import instrument_node
from app.observability.metrics import RuntimeMetrics


@pytest.mark.asyncio
async def test_instrumented_node_emits_duration():
    events = []

    async def node(state, runtime):
        return {"value": state["value"] + 1}

    wrapped = instrument_node("demo", node)
    result = await wrapped(
        {"value": 1}, SimpleNamespace(stream_writer=events.append)
    )

    assert result == {"value": 2}
    assert events[-1]["type"] == "node_metric"
    assert events[-1]["node"] == "demo"
    assert events[-1]["duration_ms"] >= 0


def test_runtime_metrics_calculates_latency_and_success_rate():
    metrics = RuntimeMetrics(recent_requests=10)
    metrics.record(
        {
            "success": True,
            "total_duration_ms": 100,
            "node_durations_ms": {"generate_sql": 80},
        }
    )
    metrics.record(
        {
            "success": False,
            "total_duration_ms": 300,
            "node_durations_ms": {"generate_sql": 200},
        }
    )
    snapshot = metrics.snapshot()
    assert snapshot["success_rate"] == 0.5
    assert snapshot["latency_ms"]["average"] == 200
    assert snapshot["node_average_ms"]["generate_sql"] == 140
