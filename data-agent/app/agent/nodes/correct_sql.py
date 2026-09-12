import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import reasoning_llm, reasoning_model_name
from app.agent.llm_cache import cached_ainvoke
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def correct_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "校正SQL", "status": "running"})

    sql = state["sql"]
    error = state["error"]

    query = state["query"]
    table_infos = state["table_infos"]
    metric_infos = state["metric_infos"]
    date_info = state["date_info"]
    db_info = state["db_info"]
    schema_links = state.get("schema_links", [])

    try:
        prompt = PromptTemplate(
            template=load_prompt("correct_sql"),
            input_variables=[
                "query", "table_infos", "metric_infos", "date_info",
                "db_info", "schema_links", "sql", "error",
            ],
        )
        output_parser = StrOutputParser()

        chain = prompt | reasoning_llm | output_parser

        payload = {
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "schema_links": yaml.dump(schema_links, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "sql": sql,
            "error": error,
            "model": reasoning_model_name,
        }
        cached = await cached_ainvoke("correct_sql", chain, payload)
        result = cached.value
        correction_count = state.get("correction_count", 0) + 1
        writer({"type": "progress", "step": "校正SQL", "status": "success"})
        writer({"type": "cache", "namespace": "correct_sql", "hit": cached.hit})
        logger.info(
            f"第 {correction_count} 次校正后的SQL cache_hit={cached.hit}: {result}"
        )
        return {"sql": result, "correction_count": correction_count}
    except Exception as e:
        writer({"type": "progress", "step": "校正SQL", "status": "error"})
        logger.error(f"校正SQL失败:{str(e)}")
        raise
