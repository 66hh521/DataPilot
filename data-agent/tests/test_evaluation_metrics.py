from app.evaluation.dataset import EvaluationCase
from app.evaluation.metrics import evaluate_case, summarize


def test_execution_evaluation_extracts_schema_recall():
    case = EvaluationCase(
        id="case",
        question="按省份统计销售额",
        expected_tables=["fact_order", "dim_region"],
        expected_columns=["order_amount", "province"],
        expected_non_empty=True,
    )
    result = evaluate_case(
        case,
        "SELECT r.province, SUM(f.order_amount) FROM fact_order f "
        "JOIN dim_region r ON f.region_id = r.region_id GROUP BY r.province",
        [{"province": "广东省", "sales": 100}],
        None,
        1.2,
    )
    assert result["success"] is True
    assert result["table_recall"] == 1
    assert result["column_recall"] == 1
    assert summarize([result])["success_rate"] == 1
