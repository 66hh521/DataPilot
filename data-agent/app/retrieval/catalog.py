from __future__ import annotations

from pathlib import Path

from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.entities.metric_info import MetricInfo
from app.retrieval.bm25 import BM25Index, SearchResult
from app.semantic.registry import SemanticRegistry, semantic_registry


class MetadataCatalog:
    def __init__(self, meta_path: Path, semantics: SemanticRegistry):
        context = OmegaConf.load(meta_path)
        schema = OmegaConf.structured(MetaConfig)
        self.config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
        self.semantics = semantics

        column_documents: dict[str, str] = {}
        for table in self.config.tables or []:
            for column in table.columns:
                column_id = f"{table.name}.{column.name}"
                column_documents[column_id] = " ".join(
                    [table.name, table.description, column.name, column.description, *column.alias]
                )

        metric_documents: dict[str, str] = {}
        self._metrics: dict[str, MetricInfo] = {}
        for metric in self.config.metrics or []:
            self._metrics[metric.name] = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias,
            )
            metric_documents[metric.name] = " ".join(
                [metric.name, metric.description, *metric.alias]
            )

        for metric in semantics.all_metrics():
            self._metrics[metric.name] = MetricInfo(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.required_columns,
                alias=metric.aliases,
            )
            metric_documents[metric.name] = " ".join(
                [metric.name, metric.display_name, metric.description, *metric.aliases]
            )

        self.column_index = BM25Index(column_documents)
        self.metric_index = BM25Index(metric_documents)

    def search_columns(self, query: str, limit: int = 8) -> list[SearchResult]:
        return self.column_index.search(query, limit=limit)

    def search_metrics(self, query: str, limit: int = 8) -> list[SearchResult]:
        return self.metric_index.search(query, limit=limit)

    def get_metric(self, metric_id: str) -> MetricInfo | None:
        return self._metrics.get(metric_id)


meta_config_file = Path(__file__).parents[2] / "conf" / "meta_config.yaml"
metadata_catalog = MetadataCatalog(meta_config_file, semantic_registry)
