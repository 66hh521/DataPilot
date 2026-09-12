import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import fast_llm, fast_model_name
from app.agent.llm_cache import cached_ainvoke
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.cache import build_cache_key, retrieval_cache
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt
from app.retrieval.expansion import expand_keywords_locally


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段取值", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]
    value_es_repository = runtime.context["value_es_repository"]

    try:
        async def compute_retrieval():
            if app_config.retrieval.keyword_expansion_mode == "llm":
                prompt = PromptTemplate(
                    template=load_prompt("extend_keywords_for_value_recall"),
                    input_variables=["query"],
                )
                chain = prompt | fast_llm | JsonOutputParser()
                expanded = await cached_ainvoke(
                    "value_keyword_expansion",
                    chain,
                    {"query": query, "model": fast_model_name},
                )
                result = expanded.value
            else:
                result = expand_keywords_locally(query, keywords, domain="value")

            expanded_keywords = list(dict.fromkeys([*keywords, *result]))
            logger.info(f"召回字段取值扩展关键词：{expanded_keywords}")
            batches = await asyncio.gather(
                *[value_es_repository.search(keyword) for keyword in expanded_keywords]
            )
            values_map: dict[str, ValueInfo] = {}
            for values in batches:
                for value in values:
                    if value.id not in values_map:
                        values_map[value.id] = value
            return {"retrieved_values": list(values_map.values())}

        cache_key = build_cache_key(
            "value_retrieval",
            {
                "query": query,
                "keywords": keywords,
                "mode": app_config.retrieval.keyword_expansion_mode,
            },
        )
        cached = await retrieval_cache.get_or_compute(cache_key, compute_retrieval)
        result = cached.value

        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        writer({"type": "cache", "namespace": "value_retrieval", "hit": cached.hit})
        logger.info(
            f"召回字段取值 cache_hit={cached.hit}："
            f"{[value.id for value in result['retrieved_values']]}"
        )
        return result
    except Exception as e:
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        logger.error(f"召回字段取值失败: {str(e)}")
        raise
