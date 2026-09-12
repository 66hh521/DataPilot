from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock

from app.conf.app_config import app_config


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(round((len(ordered) - 1) * percentile), len(ordered) - 1)
    return round(ordered[index], 2)


class RuntimeMetrics:
    def __init__(self, recent_requests: int):
        self._records = deque(maxlen=recent_requests)
        self._lock = Lock()

    def record(self, trace: dict) -> None:
        with self._lock:
            self._records.append(trace)

    def snapshot(self) -> dict:
        with self._lock:
            records = list(self._records)
        durations = [float(item["total_duration_ms"]) for item in records]
        node_durations: dict[str, list[float]] = defaultdict(list)
        for item in records:
            for node, duration in item.get("node_durations_ms", {}).items():
                node_durations[node].append(float(duration))
        successful = sum(bool(item.get("success")) for item in records)
        return {
            "request_count": len(records),
            "success_rate": round(successful / len(records), 4) if records else 0.0,
            "latency_ms": {
                "average": round(sum(durations) / len(durations), 2) if durations else 0.0,
                "p50": _percentile(durations, 0.50),
                "p95": _percentile(durations, 0.95),
            },
            "node_average_ms": {
                node: round(sum(values) / len(values), 2)
                for node, values in sorted(node_durations.items())
            },
            "recent": records[-10:],
        }


runtime_metrics = RuntimeMetrics(app_config.observability.recent_requests)
