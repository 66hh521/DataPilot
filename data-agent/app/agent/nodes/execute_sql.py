from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.errors import DataAgentError, ErrorCode
from app.core.log import logger


async def execute_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "执行SQL", "status": "running"})

    sql = state["sql"]

    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        result = await dw_mysql_repository.execute_sql(
            sql, timeout_seconds=app_config.query.timeout_seconds
        )

        writer({"type": "progress", "step": "执行SQL", "status": "success"})
        writer({
            "type": "result",
            "data": result,
            "row_count": len(result),
            "message": None if result else "未查询到符合条件的数据",
            "sql": sql,
        })
        logger.info(f"执行SQL结果: {result}")
        return {"result": result, "error": None, "error_code": None}
    except DataAgentError as e:
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        logger.warning(f"执行SQL失败 code={e.code.value}: {e}")
        return {"error": str(e), "error_code": e.code.value}
    except Exception as e:
        writer({"type": "progress", "step": "执行SQL", "status": "error"})
        logger.error(f"执行SQL失败:{str(e)}")
        return {"error": str(e), "error_code": ErrorCode.SQL_EXECUTION_ERROR.value}
