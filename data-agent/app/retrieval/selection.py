from __future__ import annotations

from copy import deepcopy

from app.agent.state import MetricInfoState, RetrievalTraceState, TableInfoState
from app.retrieval.catalog import metadata_catalog
from app.semantic.registry import semantic_registry


def select_metrics(
    query: str, metric_infos: list[MetricInfoState], limit: int = 2
) -> list[MetricInfoState]:
    normalized = query.lower()
    scored: list[tuple[int, int, MetricInfoState]] = []
    for index, metric_info in enumerate(metric_infos):
        semantic = semantic_registry.get_metric(metric_info["name"])
        terms = [
            metric_info["name"],
            metric_info.get("display_name", ""),
            *metric_info.get("alias", []),
        ]
        if semantic:
            terms.extend([semantic.display_name, *semantic.aliases])
        matches = [term for term in terms if term and term.lower() in normalized]
        score = max((len(term) for term in matches), default=0)
        scored.append((score, -index, metric_info))

    direct = [item for item in scored if item[0] > 0]
    candidates = direct or scored[:1]
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [deepcopy(item[2]) for item in candidates[:limit]]


def select_tables(
    query: str,
    table_infos: list[TableInfoState],
    metric_infos: list[MetricInfoState],
    trace: list[RetrievalTraceState],
    column_limit: int = 8,
) -> list[TableInfoState]:
    trace_ids = [item["id"] for item in trace[:column_limit]]
    lexical_ids = [
        item.item_id
        for item in metadata_catalog.search_columns(query, limit=column_limit)
    ]
    selected_ids = set([*trace_ids, *lexical_ids])

    required_ids: set[str] = set()
    required_tables: set[str] = set()
    for metric in metric_infos:
        base_table = metric.get("base_table")
        if base_table:
            required_tables.add(base_table)
        required_ids.update(
            metric.get("required_columns", metric.get("relevant_columns", []))
        )
    selected_ids.update(required_ids)

    selected: list[TableInfoState] = []
    for table in table_infos:
        table_name = table["name"]
        keep_table = table_name in required_tables or any(
            item_id.startswith(f"{table_name}.") for item_id in selected_ids
        )
        if not keep_table:
            continue

        columns = []
        for column in table["columns"]:
            column_id = f"{table_name}.{column['name']}"
            if (
                column_id in selected_ids
                or column_id in required_ids
                or column.get("role") in {"primary_key", "foreign_key"}
            ):
                columns.append(deepcopy(column))
        if columns:
            copied = deepcopy(table)
            copied["columns"] = columns
            selected.append(copied)

    return selected or deepcopy(table_infos[:1])
