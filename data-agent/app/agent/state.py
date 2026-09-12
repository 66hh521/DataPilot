from typing import NotRequired, Required, TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]
    display_name: NotRequired[str]
    expression: NotRequired[str]
    base_table: NotRequired[str]
    required_columns: NotRequired[list[str]]
    dimensions: NotRequired[list[str]]
    filters: NotRequired[list[str]]


class SchemaLinkState(TypedDict):
    left: str
    right: str
    join_type: str


class RetrievalTraceState(TypedDict):
    id: str
    score: float
    sources: list[str]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str


class DataAgentState(TypedDict, total=False):
    query: Required[str]  # 用户查询
    keywords: list[str]  # 用户查询的关键字

    retrieved_columns: list[ColumnInfo]  # 召回的字段信息
    retrieved_values: list[ValueInfo]  # 召回的值信息
    retrieved_metrics: list[MetricInfo]  # 召回的指标信息

    table_infos: list[TableInfoState]  # 表信息
    metric_infos: list[MetricInfoState]  # 指标信息
    schema_links: list[SchemaLinkState]  # Schema Graph补充的连接关系
    column_retrieval_trace: list[RetrievalTraceState]
    metric_retrieval_trace: list[RetrievalTraceState]

    date_info: DateInfoState  # 日期信息
    db_info: DBInfoState  # 数据库信息

    sql: str  # 生成的SQL

    error: str | None  # SQL验证或执行错误
    error_code: str | None  # 结构化错误类型
    correction_count: int  # 已执行的SQL校正次数
    result: NotRequired[list[dict]]
