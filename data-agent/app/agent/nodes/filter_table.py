from copy import deepcopy

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import fast_llm, fast_model_name
from app.agent.llm_cache import cached_ainvoke
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt
from app.retrieval.selection import select_tables


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤表格", "status": "running"})

    query = state["query"]
    table_infos = state["table_infos"]
    try:
        if app_config.retrieval.selection_mode == "llm":
            prompt = PromptTemplate(
                template=load_prompt("filter_table_info"),
                input_variables=["query", "table_infos"],
            )
            chain = prompt | fast_llm | JsonOutputParser()
            payload = {
                "query": query,
                "table_infos": yaml.dump(
                    table_infos, allow_unicode=True, sort_keys=False
                ),
                "model": fast_model_name,
            }
            cached = await cached_ainvoke("filter_table", chain, payload)
            selection = cached.value
            filtered = []
            for table in table_infos:
                selected_columns = set(selection.get(table["name"], []))
                if not selected_columns:
                    continue
                copied = deepcopy(table)
                copied["columns"] = [
                    deepcopy(column)
                    for column in table["columns"]
                    if column["name"] in selected_columns
                ]
                if copied["columns"]:
                    filtered.append(copied)
            writer({"type": "cache", "namespace": "filter_table", "hit": cached.hit})
        else:
            filtered = select_tables(
                query=query,
                table_infos=table_infos,
                metric_infos=state.get("metric_infos", []),
                trace=state.get("column_retrieval_trace", []),
                column_limit=app_config.retrieval.selection_column_limit,
            )

        writer({"type": "progress", "step": "过滤表格", "status": "success"})
        logger.info(f"过滤后的表信息: {[table['name'] for table in filtered]}")
        return {"table_infos": filtered}
    except Exception as e:
        writer({"type": "progress", "step": "过滤表格", "status": "error"})
        logger.error(f"过滤表失败:{str(e)}")
        raise
