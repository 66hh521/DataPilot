from types import SimpleNamespace

import pytest

from app.agent.nodes.enrich_schema import enrich_schema
from app.entities.column_info import ColumnInfo
from app.entities.table_info import TableInfo


class FakeMetaRepository:
    async def get_column_info_by_id(self, column_id):
        table_id, name = column_id.split(".", 1)
        return ColumnInfo(
            id=column_id,
            name=name,
            type="varchar(20)",
            role="foreign_key" if table_id == "fact_order" else "primary_key",
            examples=[],
            description=name,
            alias=[],
            table_id=table_id,
        )

    async def get_table_info_by_id(self, table_id):
        return TableInfo(id=table_id, name=table_id, role="fact", description=table_id)


@pytest.mark.asyncio
async def test_enrich_schema_adds_bridge_table_and_join_keys():
    events = []
    runtime = SimpleNamespace(
        stream_writer=events.append,
        context={"meta_mysql_repository": FakeMetaRepository()},
    )
    state = {
        "table_infos": [
            {
                "name": "dim_region",
                "role": "dim",
                "description": "region",
                "columns": [],
            },
            {
                "name": "dim_product",
                "role": "dim",
                "description": "product",
                "columns": [],
            },
        ],
        "metric_infos": [],
    }

    result = await enrich_schema(state, runtime)

    tables = {table["name"]: table for table in result["table_infos"]}
    assert "fact_order" in tables
    assert {column["name"] for column in tables["fact_order"]["columns"]} >= {
        "region_id",
        "product_id",
    }
    assert len(result["schema_links"]) == 2
    assert events[-1]["status"] == "success"
