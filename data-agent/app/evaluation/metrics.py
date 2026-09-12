from __future__ import annotations

from sqlglot import exp, parse_one

from app.evaluation.dataset import EvaluationCase


def recall(expected: list[str], actual: set[str]) -> float:
    if not expected:
        return 1.0
    return len({item.lower() for item in expected} & actual) / len(set(expected))


def evaluate_case(
    case: EvaluationCase,
    sql: str | None,
    rows: list[dict] | None,
    error: str | None,
    latency_seconds: float,
) -> dict:
    tables: set[str] = set()
    columns: set[str] = set()
    parse_success = False
    if sql:
        try:
            expression = parse_one(sql, read="mysql")
            tables = {table.name.lower() for table in expression.find_all(exp.Table)}
            columns = {
                column.name.lower()
                for column in expression.find_all(exp.Column)
                if not column.is_star
            }
            parse_success = True
        except Exception:
            pass

    non_empty_match = True
    if case.expected_non_empty is not None and rows is not None:
        non_empty_match = bool(rows) == case.expected_non_empty

    return {
        "id": case.id,
        "question": case.question,
        "success": error is None and rows is not None,
        "parse_success": parse_success,
        "table_recall": recall(case.expected_tables, tables),
        "column_recall": recall(case.expected_columns, columns),
        "non_empty_match": non_empty_match,
        "latency_seconds": round(latency_seconds, 3),
        "sql": sql,
        "row_count": len(rows) if rows is not None else None,
        "error": error,
    }


def summarize(results: list[dict]) -> dict:
    if not results:
        return {"case_count": 0}

    def average(field: str) -> float:
        return round(sum(float(item[field]) for item in results) / len(results), 4)

    latencies = sorted(float(item["latency_seconds"]) for item in results)
    p95_index = min(round((len(latencies) - 1) * 0.95), len(latencies) - 1)
    return {
        "case_count": len(results),
        "success_rate": average("success"),
        "sql_parse_rate": average("parse_success"),
        "table_recall": average("table_recall"),
        "column_recall": average("column_recall"),
        "non_empty_accuracy": average("non_empty_match"),
        "average_latency_seconds": round(
            sum(item["latency_seconds"] for item in results) / len(results), 3
        ),
        "p95_latency_seconds": round(latencies[p95_index], 3),
    }
