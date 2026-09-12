from __future__ import annotations

from dataclasses import dataclass
import re

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.core.errors import DataAgentError, ErrorCode


FORBIDDEN_NODE_NAMES = {
    "Alter",
    "Command",
    "Commit",
    "Create",
    "Delete",
    "Drop",
    "Grant",
    "Insert",
    "Into",
    "LoadData",
    "Lock",
    "Merge",
    "Revoke",
    "Rollback",
    "Set",
    "Transaction",
    "TruncateTable",
    "Unlock",
    "Update",
    "Use",
}

FORBIDDEN_FUNCTIONS = {
    "BENCHMARK",
    "LOAD_FILE",
    "SLEEP",
}


class SQLGuardError(DataAgentError):
    pass


@dataclass(frozen=True)
class SQLPolicy:
    max_rows: int = 500
    dialect: str = "mysql"


class SQLGuard:
    def __init__(self, policy: SQLPolicy | None = None):
        self.policy = policy or SQLPolicy()

    def validate_and_rewrite(
        self, sql: str, allowed_schema: dict[str, set[str]]
    ) -> str:
        cleaned = self._strip_markdown(sql)
        try:
            statements = [item for item in parse(cleaned, read=self.policy.dialect) if item]
        except ParseError as exc:
            raise SQLGuardError(str(exc), ErrorCode.SQL_PARSE_ERROR) from exc

        if len(statements) != 1:
            raise SQLGuardError("只允许执行一条 SQL", ErrorCode.SQL_SECURITY_ERROR)

        statement = statements[0]
        if not isinstance(statement, exp.Query):
            raise SQLGuardError("只允许 SELECT 查询", ErrorCode.SQL_SECURITY_ERROR)

        for node in statement.walk():
            if type(node).__name__ in FORBIDDEN_NODE_NAMES:
                raise SQLGuardError(
                    f"禁止执行 {type(node).__name__} 语句",
                    ErrorCode.SQL_SECURITY_ERROR,
                )
            function_name = (
                node.name if isinstance(node, exp.Anonymous) else node.sql_name()
            ) if isinstance(node, exp.Func) else ""
            if function_name.upper() in FORBIDDEN_FUNCTIONS:
                raise SQLGuardError(
                    f"禁止调用函数: {function_name}",
                    ErrorCode.SQL_SECURITY_ERROR,
                )
            if isinstance(node, exp.Star) and node.find_ancestor(exp.Count) is None:
                raise SQLGuardError(
                    "禁止使用 SELECT *，请显式选择字段",
                    ErrorCode.SQL_SCHEMA_ERROR,
                )

        normalized_schema = {
            table.lower(): {column.lower() for column in columns}
            for table, columns in allowed_schema.items()
        }
        self._validate_tables_and_columns(statement, normalized_schema)
        statement = self._apply_limit(statement)
        return statement.sql(dialect=self.policy.dialect)

    def _validate_tables_and_columns(
        self, statement: exp.Query, allowed_schema: dict[str, set[str]]
    ) -> None:
        cte_names = {
            cte.alias_or_name.lower()
            for cte in statement.find_all(exp.CTE)
            if cte.alias_or_name
        }
        table_aliases: dict[str, str] = {}

        for table in statement.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name in cte_names:
                continue
            if table_name not in allowed_schema:
                raise SQLGuardError(
                    f"查询引用了未授权表: {table.name}",
                    ErrorCode.SQL_SCHEMA_ERROR,
                )
            table_aliases[(table.alias_or_name or table.name).lower()] = table_name
            table_aliases[table_name] = table_name

        select_aliases = {
            alias.alias.lower()
            for alias in statement.find_all(exp.Alias)
            if alias.alias
        }

        for column in statement.find_all(exp.Column):
            if column.is_star:
                if column.find_ancestor(exp.Count) is None:
                    raise SQLGuardError(
                        "禁止使用 SELECT *，请显式选择字段",
                        ErrorCode.SQL_SCHEMA_ERROR,
                    )
                continue

            column_name = column.name.lower()
            qualifier = column.table.lower() if column.table else None

            if qualifier:
                if qualifier in cte_names:
                    continue
                table_name = table_aliases.get(qualifier)
                if not table_name or column_name not in allowed_schema[table_name]:
                    raise SQLGuardError(
                        f"查询引用了未授权字段: {column.sql()}",
                        ErrorCode.SQL_SCHEMA_ERROR,
                    )
            elif column_name not in select_aliases and not any(
                column_name in columns for columns in allowed_schema.values()
            ):
                raise SQLGuardError(
                    f"查询引用了未授权字段: {column.name}",
                    ErrorCode.SQL_SCHEMA_ERROR,
                )

    def _apply_limit(self, statement: exp.Query) -> exp.Query:
        limit = statement.args.get("limit")
        if limit is None:
            return statement.limit(self.policy.max_rows)

        limit_expression = limit.expression
        if not isinstance(limit_expression, exp.Literal) or not limit_expression.is_int:
            raise SQLGuardError("LIMIT 必须是整数", ErrorCode.SQL_SECURITY_ERROR)
        if int(limit_expression.this) > self.policy.max_rows:
            return statement.limit(self.policy.max_rows, copy=False)
        return statement

    @staticmethod
    def _strip_markdown(sql: str) -> str:
        cleaned = sql.strip()
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()
