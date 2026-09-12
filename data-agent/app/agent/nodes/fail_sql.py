from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.errors import user_message
from app.core.log import logger


async def fail_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    error_code = state.get("error_code")
    correction_count = state.get("correction_count", 0)
    logger.error(
        f"SQL流程终止 code={error_code} corrections={correction_count} "
        f"detail={state.get('error')}"
    )
    runtime.stream_writer({
        "type": "error",
        "code": error_code or "internal_error",
        "message": user_message(error_code),
    })
