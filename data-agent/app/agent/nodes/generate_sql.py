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


async def generate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "生成SQL", "status": "running"})

    query = state["query"]
    table_infos = state["table_infos"]
    metric_infos = state["metric_infos"]
    date_info = state["date_info"]
    db_info = state["db_info"]
    schema_links = state.get("schema_links", [])

    try:
        prompt = PromptTemplate(template=load_prompt("generate_sql"),
                                input_variables=["query", "table_infos", "metric_infos", "schema_links", "date_info", "db_info"])
        output_parser = StrOutputParser()

        chain = prompt | reasoning_llm | output_parser

        payload = {
            "query": query,
            "table_infos": yaml.dump(table_infos, allow_unicode=True, sort_keys=False),
            "metric_infos": yaml.dump(metric_infos, allow_unicode=True, sort_keys=False),
            "schema_links": yaml.dump(schema_links, allow_unicode=True, sort_keys=False),
            "date_info": yaml.dump(date_info, allow_unicode=True, sort_keys=False),
            "db_info": yaml.dump(db_info, allow_unicode=True, sort_keys=False),
            "model": reasoning_model_name,
        }
        cached = await cached_ainvoke("generate_sql", chain, payload)
        result = cached.value

        writer({"type": "progress", "step": "生成SQL", "status": "success"})
        writer({"type": "cache", "namespace": "generate_sql", "hit": cached.hit})
        logger.info(f"生成的SQL cache_hit={cached.hit}: {result}")
        return {"sql": result}
    except Exception as e:
        writer({"type": "progress", "step": "生成SQL", "status": "error"})
        logger.error(f"生成SQL失败: {str(e)}")
        raise
