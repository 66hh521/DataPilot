from __future__ import annotations

from enum import StrEnum
from html import unescape
import re


class ErrorCode(StrEnum):
    SQL_PARSE_ERROR = "sql_parse_error"
    SQL_SECURITY_ERROR = "sql_security_error"
    SQL_SCHEMA_ERROR = "sql_schema_error"
    SQL_VALIDATION_ERROR = "sql_validation_error"
    SQL_EXECUTION_ERROR = "sql_execution_error"
    QUERY_TIMEOUT = "query_timeout"
    DATABASE_UNAVAILABLE = "database_unavailable"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    INTERNAL_ERROR = "internal_error"


class DataAgentError(Exception):
    def __init__(self, message: str, code: ErrorCode):
        super().__init__(message)
        self.code = code


class QueryTimeoutError(DataAgentError):
    def __init__(self, message: str = "数据库查询超时"):
        super().__init__(message, ErrorCode.QUERY_TIMEOUT)


USER_MESSAGES = {
    ErrorCode.SQL_PARSE_ERROR: "生成的 SQL 无法解析，请换一种方式描述问题。",
    ErrorCode.SQL_SECURITY_ERROR: "生成的查询未通过安全检查，已阻止执行。",
    ErrorCode.SQL_SCHEMA_ERROR: "生成的 SQL 引用了不可用的表或字段。",
    ErrorCode.SQL_VALIDATION_ERROR: "SQL 多次校正后仍未通过验证，请补充更明确的查询条件。",
    ErrorCode.SQL_EXECUTION_ERROR: "查询执行失败，请稍后重试或调整查询条件。",
    ErrorCode.QUERY_TIMEOUT: "查询耗时过长，已自动终止。请缩小时间范围或增加筛选条件。",
    ErrorCode.DATABASE_UNAVAILABLE: "数据库暂时不可用，请稍后重试。",
    ErrorCode.EXTERNAL_SERVICE_ERROR: "外部模型或检索服务暂时不可用，请稍后重试。",
    ErrorCode.INTERNAL_ERROR: "系统处理失败，请稍后重试。",
}


def user_message(code: ErrorCode | str | None) -> str:
    try:
        normalized = ErrorCode(code) if code else ErrorCode.INTERNAL_ERROR
    except ValueError:
        normalized = ErrorCode.INTERNAL_ERROR
    return USER_MESSAGES[normalized]


def sanitize_exception(exc: Exception, max_length: int = 300) -> str:
    """Remove HTML and bound error text before it is sent to a browser."""
    message = unescape(str(exc)).strip()
    if "<!DOCTYPE html" in message or "<html" in message.lower():
        return user_message(ErrorCode.EXTERNAL_SERVICE_ERROR)
    message = re.sub(r"<[^>]+>", " ", message)
    message = re.sub(r"\s+", " ", message).strip()
    return message[:max_length] or user_message(ErrorCode.INTERNAL_ERROR)


NON_RETRYABLE_SQL_ERRORS = {
    ErrorCode.SQL_SECURITY_ERROR.value,
    ErrorCode.QUERY_TIMEOUT.value,
    ErrorCode.DATABASE_UNAVAILABLE.value,
}
