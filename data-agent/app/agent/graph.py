import asyncio

from langgraph.constants import START, END
from langgraph.graph import StateGraph

from app.agent.context import DataAgentContext
from app.agent.nodes.add_extra_context import add_extra_context
from app.agent.nodes.correct_sql import correct_sql
from app.agent.nodes.execute_sql import execute_sql
from app.agent.nodes.enrich_schema import enrich_schema
from app.agent.nodes.extract_keywords import extract_keywords
from app.agent.nodes.fail_sql import fail_sql
from app.agent.nodes.filter_metric import filter_metric
from app.agent.nodes.filter_table import filter_table
from app.agent.nodes.generate_sql import generate_sql
from app.agent.nodes.merge_retrieved_info import merge_retrieved_info
from app.agent.nodes.recall_column import recall_column
from app.agent.nodes.recall_metric import recall_metric
from app.agent.nodes.recall_value import recall_value
from app.agent.nodes.validate_sql import validate_sql
from app.agent.state import DataAgentState
from app.conf.app_config import app_config
from app.core.errors import NON_RETRYABLE_SQL_ERRORS
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.observability.instrumentation import instrument_node

graph_builder = StateGraph(state_schema=DataAgentState, context_schema=DataAgentContext)

# 添加带耗时埋点的节点
nodes = {
    "extract_keywords": extract_keywords,
    "recall_column": recall_column,
    "recall_value": recall_value,
    "recall_metric": recall_metric,
    "merge_retrieved_info": merge_retrieved_info,
    "filter_metric": filter_metric,
    "filter_table": filter_table,
    "add_extra_context": add_extra_context,
    "generate_sql": generate_sql,
    "validate_sql": validate_sql,
    "correct_sql": correct_sql,
    "execute_sql": execute_sql,
    "fail_sql": fail_sql,
    "enrich_schema": enrich_schema,
}
for node_name, node in nodes.items():
    graph_builder.add_node(node_name, instrument_node(node_name, node))

# 添加关系
graph_builder.add_edge(START, "extract_keywords")
graph_builder.add_edge("extract_keywords", "recall_column")
graph_builder.add_edge("extract_keywords", "recall_value")
graph_builder.add_edge("extract_keywords", "recall_metric")
graph_builder.add_edge("recall_column", "merge_retrieved_info")
graph_builder.add_edge("recall_value", "merge_retrieved_info")
graph_builder.add_edge("recall_metric", "merge_retrieved_info")
graph_builder.add_edge("merge_retrieved_info", "filter_table")
graph_builder.add_edge("merge_retrieved_info", "filter_metric")
graph_builder.add_edge("filter_table", "enrich_schema")
graph_builder.add_edge("filter_metric", "enrich_schema")
graph_builder.add_edge("enrich_schema", "add_extra_context")
graph_builder.add_edge("add_extra_context", "generate_sql")
graph_builder.add_edge("generate_sql", "validate_sql")

def route_sql_result(state: DataAgentState) -> str:
    if state.get("error") is None:
        return "execute_sql"
    if state.get("error_code") in NON_RETRYABLE_SQL_ERRORS:
        return "fail_sql"
    if state.get("correction_count", 0) >= app_config.query.max_corrections:
        return "fail_sql"
    return "correct_sql"


def route_execution_result(state: DataAgentState) -> str:
    if state.get("error") is None:
        return "end"
    if state.get("error_code") in NON_RETRYABLE_SQL_ERRORS:
        return "fail_sql"
    if state.get("correction_count", 0) >= app_config.query.max_corrections:
        return "fail_sql"
    return "correct_sql"


graph_builder.add_conditional_edges(
    "validate_sql",
    route_sql_result,
    {
        "execute_sql": "execute_sql",
        "correct_sql": "correct_sql",
        "fail_sql": "fail_sql",
    },
)

graph_builder.add_edge("correct_sql", "validate_sql")
graph_builder.add_conditional_edges(
    "execute_sql",
    route_execution_result,
    {"end": END, "correct_sql": "correct_sql", "fail_sql": "fail_sql"},
)
graph_builder.add_edge("fail_sql", END)

graph = graph_builder.compile()



if __name__ == '__main__':
    async def test():
        embedding_client_manager.init()
        qdrant_client_manager.init()
        es_client_manager.init()
        meta_mysql_client_manager.init()
        dw_mysql_client_manager.init()

        async with meta_mysql_client_manager.session_factory() as meta_session, dw_mysql_client_manager.session_factory() as dw_session:
            meta_mysql_repository = MetaMySQLRepository(meta_session)
            dw_mysql_repository = DWMySQLRepository(dw_session)
            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
            value_es_repository = ValueESRepository(es_client_manager.client)
            metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)

            context = DataAgentContext(
                embedding_client=embedding_client_manager.client,
                column_qdrant_repository=column_qdrant_repository,
                value_es_repository=value_es_repository,
                metric_qdrant_repository=metric_qdrant_repository,
                meta_mysql_repository=meta_mysql_repository,
                dw_mysql_repository=dw_mysql_repository
            )
            state = DataAgentState(query="统计去年各地区的销售总额")
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                print(chunk)

        await qdrant_client_manager.close()
        await es_client_manager.close()
        await meta_mysql_client_manager.close()
        await dw_mysql_client_manager.close()


    asyncio.run(test())
