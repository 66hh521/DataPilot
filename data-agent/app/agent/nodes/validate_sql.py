from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.errors import DataAgentError, ErrorCode
from app.core.log import logger
from app.security.sql_guard import SQLGuard, SQLPolicy


sql_guard = SQLGuard(SQLPolicy(max_rows=app_config.query.max_rows))


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "验证SQL", "status": "running"})

    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    sql = state["sql"]
    allowed_schema = {
        table["name"]: {column["name"] for column in table["columns"]}
        for table in state["table_infos"]
    }

    try:
        safe_sql = sql_guard.validate_and_rewrite(sql, allowed_schema)
        await dw_mysql_repository.validate_sql(
            safe_sql, timeout_seconds=app_config.query.timeout_seconds
        )
        writer({"type": "progress", "step": "验证SQL", "status": "success"})
        logger.info(f"SQL验证成功: {safe_sql}")
        return {"sql": safe_sql, "error": None, "error_code": None}
    except DataAgentError as e:
        writer({"type": "progress", "step": "验证SQL", "status": "error"})
        logger.warning(f"SQL验证失败 code={e.code.value}: {e}")
        return {"error": str(e), "error_code": e.code.value}
    except Exception as e:
        writer({"type": "progress", "step": "验证SQL", "status": "error"})
        logger.warning(f"SQL数据库验证失败: {e}")
        return {"error": str(e), "error_code": ErrorCode.SQL_VALIDATION_ERROR.value}
