import pytest

from app.core.errors import ErrorCode
from app.security.sql_guard import SQLGuard, SQLGuardError, SQLPolicy


SCHEMA = {
    "fact_order": {"order_id", "region_id", "date_id", "order_amount"},
    "dim_region": {"region_id", "province"},
    "dim_date": {"date_id", "year", "month"},
}


@pytest.fixture
def guard():
    return SQLGuard(SQLPolicy(max_rows=100))


def test_valid_query_is_normalized_and_limited(guard):
    sql = guard.validate_and_rewrite(
        """
        SELECT r.province, SUM(f.order_amount) AS total_sales
        FROM fact_order f
        JOIN dim_region r ON f.region_id = r.region_id
        GROUP BY r.province
        ORDER BY total_sales DESC
        """,
        SCHEMA,
    )

    assert "LIMIT 100" in sql
    assert "fact_order" in sql


def test_existing_large_limit_is_capped(guard):
    sql = guard.validate_and_rewrite(
        "SELECT order_id FROM fact_order LIMIT 10000", SCHEMA
    )
    assert "LIMIT 100" in sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM fact_order",
        "UPDATE fact_order SET order_amount = 0",
        "DROP TABLE fact_order",
        "SELECT order_id FROM fact_order; SELECT region_id FROM fact_order",
        "SELECT SLEEP(10)",
    ],
)
def test_dangerous_sql_is_rejected(guard, sql):
    with pytest.raises(SQLGuardError) as exc_info:
        guard.validate_and_rewrite(sql, SCHEMA)
    assert exc_info.value.code == ErrorCode.SQL_SECURITY_ERROR


def test_unknown_table_is_retryable_schema_error(guard):
    with pytest.raises(SQLGuardError) as exc_info:
        guard.validate_and_rewrite("SELECT id FROM users", SCHEMA)
    assert exc_info.value.code == ErrorCode.SQL_SCHEMA_ERROR


def test_unknown_column_is_retryable_schema_error(guard):
    with pytest.raises(SQLGuardError) as exc_info:
        guard.validate_and_rewrite("SELECT password FROM fact_order", SCHEMA)
    assert exc_info.value.code == ErrorCode.SQL_SCHEMA_ERROR


def test_select_star_is_rejected_but_count_star_is_allowed(guard):
    with pytest.raises(SQLGuardError):
        guard.validate_and_rewrite("SELECT * FROM fact_order", SCHEMA)

    sql = guard.validate_and_rewrite("SELECT COUNT(*) AS total FROM fact_order", SCHEMA)
    assert "COUNT(*)" in sql


def test_markdown_fence_is_removed(guard):
    sql = guard.validate_and_rewrite(
        "```sql\nSELECT order_id FROM fact_order\n```", SCHEMA
    )
    assert "```" not in sql
