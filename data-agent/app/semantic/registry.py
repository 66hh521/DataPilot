from __future__ import annotations

from collections import deque
from pathlib import Path

from omegaconf import OmegaConf

from app.semantic.models import JoinRelationship, SemanticLayerConfig, SemanticMetric


class SemanticRegistry:
    def __init__(self, config_path: Path):
        context = OmegaConf.load(config_path)
        schema = OmegaConf.structured(SemanticLayerConfig)
        self.config: SemanticLayerConfig = OmegaConf.to_object(
            OmegaConf.merge(schema, context)
        )
        self._metrics = {metric.name: metric for metric in self.config.metrics}
        self._adjacency: dict[str, list[tuple[str, JoinRelationship]]] = {}
        for relationship in self.config.joins:
            self._adjacency.setdefault(relationship.left_table, []).append(
                (relationship.right_table, relationship)
            )
            self._adjacency.setdefault(relationship.right_table, []).append(
                (relationship.left_table, relationship)
            )

    def get_metric(self, name: str) -> SemanticMetric | None:
        return self._metrics.get(name)

    def all_metrics(self) -> list[SemanticMetric]:
        return list(self._metrics.values())

    def enrich_metric(self, name: str) -> dict:
        metric = self.get_metric(name)
        if metric is None:
            return {}
        return {
            "display_name": metric.display_name,
            "expression": metric.expression,
            "base_table": metric.base_table,
            "required_columns": metric.required_columns,
            "dimensions": metric.dimensions,
            "filters": metric.filters,
        }

    def connect_tables(self, tables: set[str]) -> list[JoinRelationship]:
        """Return join edges needed to connect the requested tables."""
        remaining = set(tables)
        if len(remaining) < 2:
            return []

        connected = {remaining.pop()}
        selected: list[JoinRelationship] = []
        selected_keys: set[tuple[str, str]] = set()

        while remaining:
            path = self._shortest_path(connected, remaining)
            if not path:
                break
            for relationship in path:
                key = tuple(sorted((relationship.left, relationship.right)))
                if key not in selected_keys:
                    selected.append(relationship)
                    selected_keys.add(key)
                connected.add(relationship.left_table)
                connected.add(relationship.right_table)
            remaining -= connected
        return selected

    def _shortest_path(
        self, sources: set[str], targets: set[str]
    ) -> list[JoinRelationship]:
        queue = deque((source, []) for source in sources)
        visited = set(sources)
        while queue:
            table, path = queue.popleft()
            for neighbor, relationship in self._adjacency.get(table, []):
                if neighbor in visited:
                    continue
                next_path = [*path, relationship]
                if neighbor in targets:
                    return next_path
                visited.add(neighbor)
                queue.append((neighbor, next_path))
        return []


semantic_config_file = Path(__file__).parents[2] / "conf" / "semantic_layer.yaml"
semantic_registry = SemanticRegistry(semantic_config_file)
