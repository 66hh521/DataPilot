from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import fast_llm, fast_model_name
from app.agent.llm_cache import cached_ainvoke
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.log import logger
from app.core.cache import build_cache_key, retrieval_cache
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt
from app.retrieval.catalog import metadata_catalog
from app.retrieval.expansion import expand_keywords_locally
from app.retrieval.fusion import reciprocal_rank_fusion


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]

    embedding_client = runtime.context['embedding_client']
    metric_qdrant_repository = runtime.context['metric_qdrant_repository']

    try:
        async def compute_retrieval():
            if app_config.retrieval.keyword_expansion_mode == "llm":
                prompt = PromptTemplate(
                    template=load_prompt("extend_keywords_for_metric_recall"),
                    input_variables=["query"],
                )
                chain = prompt | fast_llm | JsonOutputParser()
                expanded = await cached_ainvoke(
                    "metric_keyword_expansion",
                    chain,
                    {"query": query, "model": fast_model_name},
                )
                result = expanded.value
            else:
                result = expand_keywords_locally(query, keywords, domain="metric")

            retrieved_metrics_map: dict[str, MetricInfo] = {}

            expanded_keywords = list(dict.fromkeys([query, *keywords, *result]))
            logger.info(f"召回指标信息扩展关键词：{expanded_keywords}")
            embeddings = await embedding_client.aembed_documents(expanded_keywords)
            dense_batches = await asyncio.gather(*[
                metric_qdrant_repository.search(
                    embedding, limit=app_config.retrieval.dense_limit
                )
                for embedding in embeddings
            ])
            dense_ranking: list[str] = []
            for payloads in dense_batches:
                for payload in payloads:
                    retrieved_metrics_map[payload.id] = payload
                    if payload.id not in dense_ranking:
                        dense_ranking.append(payload.id)

            lexical_ranking = [
                item.item_id
                for item in metadata_catalog.search_metrics(
                    " ".join(expanded_keywords),
                    limit=app_config.retrieval.lexical_limit,
                )
            ]
            fused = reciprocal_rank_fusion(
                {"dense": dense_ranking, "lexical": lexical_ranking},
                k=app_config.retrieval.rrf_k,
                limit=app_config.retrieval.fusion_limit,
            )

            retrieved_metrics: list[MetricInfo] = []
            for item in fused:
                metric = retrieved_metrics_map.get(item.item_id) or metadata_catalog.get_metric(item.item_id)
                if metric is not None:
                    retrieved_metrics.append(metric)

            trace = [
                {"id": item.item_id, "score": item.score, "sources": list(item.sources)}
                for item in fused
            ]
            return {
                "retrieved_metrics": retrieved_metrics,
                "metric_retrieval_trace": trace,
            }

        cache_key = build_cache_key(
            "metric_retrieval",
            {
                "query": query,
                "keywords": keywords,
                "mode": app_config.retrieval.keyword_expansion_mode,
                "dense_limit": app_config.retrieval.dense_limit,
                "lexical_limit": app_config.retrieval.lexical_limit,
                "fusion_limit": app_config.retrieval.fusion_limit,
            },
        )
        cached = await retrieval_cache.get_or_compute(cache_key, compute_retrieval)
        result = cached.value

        writer({"type": "progress", "step": "召回指标", "status": "success"})
        writer({"type": "cache", "namespace": "metric_retrieval", "hit": cached.hit})
        logger.info(f"混合召回指标信息 cache_hit={cached.hit}：{result['metric_retrieval_trace']}")
        return result
    except Exception as e:
        writer({"type": "progress", "step": "召回指标", "status": "error"})
        logger.error(f"召回指标信息失败: {str(e)}")
        raise
import asyncio
