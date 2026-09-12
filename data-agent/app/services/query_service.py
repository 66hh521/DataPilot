import asyncio
import json
from time import perf_counter

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.llm import fast_model_name, reasoning_model_name
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.context import request_id_ctx_var
from app.core.errors import ErrorCode, sanitize_exception, user_message
from app.core.log import logger
from app.observability.metrics import runtime_metrics
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


class QueryService:
    def __init__(
        self,
        embedding_client: HuggingFaceEndpointEmbeddings,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueESRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        meta_mysql_repository: MetaMySQLRepository,
        dw_mysql_repository: DWMySQLRepository,
    ):
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository

    async def query(self, query: str, request_id: str | None = None):
        context = DataAgentContext(
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            dw_mysql_repository=self.dw_mysql_repository,
        )
        state = DataAgentState(query=query, correction_count=0)
        request_id = request_id or str(request_id_ctx_var.get())
        started = perf_counter()
        node_durations: dict[str, float] = {}
        cache_hits = 0
        cache_misses = 0
        success = False
        error_code = None

        yield _sse({"type": "request", "request_id": request_id})
        try:
            async with asyncio.timeout(app_config.query.workflow_timeout_seconds):
                async for chunk in graph.astream(
                    input=state, context=context, stream_mode="custom"
                ):
                    event_type = chunk.get("type")
                    if event_type == "node_metric":
                        node_durations[chunk["node"]] = chunk["duration_ms"]
                    elif event_type == "cache":
                        if chunk.get("hit"):
                            cache_hits += 1
                        else:
                            cache_misses += 1
                    elif event_type == "result":
                        success = True
                    elif event_type == "error":
                        error_code = chunk.get("code")
                    yield _sse(chunk)
        except TimeoutError:
            error_code = ErrorCode.QUERY_TIMEOUT.value
            logger.error("智能体工作流执行超时")
            yield _sse(
                {
                    "type": "error",
                    "code": error_code,
                    "message": user_message(ErrorCode.QUERY_TIMEOUT),
                }
            )
        except asyncio.CancelledError:
            logger.info("客户端断开连接，取消智能体工作流")
            raise
        except Exception as exc:
            error_code = ErrorCode.INTERNAL_ERROR.value
            logger.exception("智能体工作流执行失败")
            yield _sse(
                {
                    "type": "error",
                    "code": error_code,
                    "message": sanitize_exception(exc),
                }
            )

        trace = {
            "type": "trace",
            "request_id": request_id,
            "success": success,
            "error_code": error_code,
            "total_duration_ms": round((perf_counter() - started) * 1000, 2),
            "node_durations_ms": node_durations,
            "cache": {"hits": cache_hits, "misses": cache_misses},
            "models": {
                "fast": fast_model_name,
                "reasoning": reasoning_model_name,
            },
        }
        runtime_metrics.record(trace)
        logger.info(
            f"请求完成 success={success} duration_ms={trace['total_duration_ms']} "
            f"cache={trace['cache']} nodes={node_durations}"
        )
        yield _sse(trace)
