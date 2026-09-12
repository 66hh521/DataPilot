from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import ColumnInfoState, DataAgentState, SchemaLinkState, TableInfoState
from app.core.log import logger
from app.semantic.registry import semantic_registry


async def enrich_schema(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "扩展Schema关系", "status": "running"})
    repository = runtime.context["meta_mysql_repository"]

    try:
        table_map: dict[str, TableInfoState] = {
            table["name"]: table for table in state.get("table_infos", [])
        }
        required_columns: set[str] = set()
        seed_tables = set(table_map)

        for metric in state.get("metric_infos", []):
            base_table = metric.get("base_table")
            if base_table:
                seed_tables.add(base_table)
            required_columns.update(
                metric.get("required_columns", metric.get("relevant_columns", []))
            )

        relationships = semantic_registry.connect_tables(seed_tables)
        for relationship in relationships:
            seed_tables.add(relationship.left_table)
            seed_tables.add(relationship.right_table)
            required_columns.add(relationship.left)
            required_columns.add(relationship.right)

        for column_id in sorted(required_columns):
            if "." not in column_id:
                continue
            table_id, _ = column_id.split(".", 1)
            column = await repository.get_column_info_by_id(column_id)
            if column is None:
                logger.warning(f"语义层字段不存在: {column_id}")
                continue
            if table_id not in table_map:
                table = await repository.get_table_info_by_id(table_id)
                if table is None:
                    logger.warning(f"语义层表不存在: {table_id}")
                    continue
                table_map[table_id] = TableInfoState(
                    name=table.name,
                    role=table.role,
                    description=table.description,
                    columns=[],
                )

            existing = {item["name"] for item in table_map[table_id]["columns"]}
            if column.name not in existing:
                table_map[table_id]["columns"].append(
                    ColumnInfoState(
                        name=column.name,
                        type=column.type,
                        role=column.role,
                        examples=column.examples,
                        description=column.description,
                        alias=column.alias,
                    )
                )

        schema_links: list[SchemaLinkState] = [
            SchemaLinkState(
                left=relationship.left,
                right=relationship.right,
                join_type=relationship.join_type,
            )
            for relationship in relationships
        ]
        writer({"type": "progress", "step": "扩展Schema关系", "status": "success"})
        logger.info(
            f"Schema Graph扩展: tables={list(table_map)}, links={schema_links}"
        )
        return {"table_infos": list(table_map.values()), "schema_links": schema_links}
    except Exception as exc:
        writer({"type": "progress", "step": "扩展Schema关系", "status": "error"})
        logger.error(f"Schema Graph扩展失败: {exc}")
        raise
