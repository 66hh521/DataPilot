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
from app.retrieval.selection import select_metrics


async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "过滤指标", "status": "running"})

    query = state["query"]
    metric_infos = state["metric_infos"]
    try:
        if app_config.retrieval.selection_mode == "llm":
            prompt = PromptTemplate(
                template=load_prompt("filter_metric_info"),
                input_variables=["query", "metric_infos"],
            )
            chain = prompt | fast_llm | JsonOutputParser()
            payload = {
                "query": query,
                "metric_infos": yaml.dump(
                    metric_infos, allow_unicode=True, sort_keys=False
                ),
                "model": fast_model_name,
            }
            cached = await cached_ainvoke("filter_metric", chain, payload)
            names = set(cached.value)
            filtered = [metric for metric in metric_infos if metric["name"] in names]
            writer({"type": "cache", "namespace": "filter_metric", "hit": cached.hit})
        else:
            filtered = select_metrics(
                query,
                metric_infos,
                limit=app_config.retrieval.selection_metric_limit,
            )

        writer({"type": "progress", "step": "过滤指标", "status": "success"})
        logger.info(f"过滤后的指标: {[metric['name'] for metric in filtered]}")
        return {"metric_infos": filtered}
    except Exception as e:
        writer({"type": "progress", "step": "过滤指标", "status": "error"})
        logger.error(f"过滤指标失败:{str(e)}")
        raise
