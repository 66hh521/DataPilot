from app.retrieval.expansion import expand_keywords_locally
from app.retrieval.selection import select_metrics, select_tables


def test_local_expansion_understands_business_metric():
    expanded = expand_keywords_locally("查询各省销售额", ["省", "销售额"], "metric")
    assert "GMV" in expanded
    assert "成交金额" in expanded


def test_deterministic_metric_selection_uses_semantic_alias():
    metrics = [
        {"name": "AOV", "description": "客单价", "alias": ["客单价"]},
        {"name": "GMV", "description": "销售额", "alias": ["销售额"]},
    ]
    selected = select_metrics("统计各地区销售额", metrics, limit=1)
    assert [metric["name"] for metric in selected] == ["GMV"]


def test_deterministic_table_selection_removes_low_rank_noise():
    tables = [
        {
            "name": "dim_region",
            "role": "dimension",
            "description": "地区",
            "columns": [
                {"name": "province", "role": "attribute"},
                {"name": "region_id", "role": "primary_key"},
            ],
        },
        {
            "name": "dim_product",
            "role": "dimension",
            "description": "商品",
            "columns": [{"name": "category", "role": "attribute"}],
        },
        {
            "name": "fact_order",
            "role": "fact",
            "description": "订单",
            "columns": [
                {"name": "order_amount", "role": "measure"},
                {"name": "region_id", "role": "foreign_key"},
            ],
        },
    ]
    metrics = [
        {
            "name": "GMV",
            "description": "销售额",
            "alias": ["销售额"],
            "base_table": "fact_order",
            "required_columns": ["fact_order.order_amount"],
        }
    ]
    trace = [
        {"id": "dim_region.province", "score": 1.0, "sources": ["lexical"]},
        {"id": "fact_order.order_amount", "score": 0.9, "sources": ["dense"]},
    ]

    selected = select_tables("各省销售额", tables, metrics, trace, column_limit=2)
    assert {table["name"] for table in selected} == {"dim_region", "fact_order"}
