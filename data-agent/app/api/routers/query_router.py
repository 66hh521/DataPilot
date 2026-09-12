from fastapi import APIRouter
from fastapi.params import Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.core.cache import cache_stats
from app.core.context import request_id_ctx_var
from app.observability.metrics import runtime_metrics
from app.services.query_service import QueryService

query_router = APIRouter()


@query_router.post("/api/query")
async def query(
    query: QuerySchema, query_service: QueryService = Depends(get_query_service)
):
    return StreamingResponse(
        query_service.query(query.query, str(request_id_ctx_var.get())),
        media_type="text/event-stream",
        headers={"X-Request-ID": str(request_id_ctx_var.get())},
    )


@query_router.get("/api/metrics")
async def metrics():
    return {
        "runtime": runtime_metrics.snapshot(),
        "cache": cache_stats(),
    }
