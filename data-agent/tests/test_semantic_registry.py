from pathlib import Path

from app.semantic.registry import SemanticRegistry


def test_metric_has_executable_expression():
    registry = SemanticRegistry(Path("conf/semantic_layer.yaml"))
    metric = registry.get_metric("AOV")
    assert metric is not None
    assert "COUNT(DISTINCT fact_order.order_id)" in metric.expression
    assert "fact_order.order_amount" in metric.required_columns


def test_schema_graph_connects_dimensions_through_fact_table():
    registry = SemanticRegistry(Path("conf/semantic_layer.yaml"))
    relationships = registry.connect_tables({"dim_region", "dim_product"})
    tables = {
        table
        for relationship in relationships
        for table in (relationship.left_table, relationship.right_table)
    }
    assert {"dim_region", "fact_order", "dim_product"} <= tables
