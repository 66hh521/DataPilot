from dataclasses import dataclass, field
import os
from pathlib import Path

from omegaconf import OmegaConf

from app.conf.config_loader import load_config


# 日志配置
@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str


@dataclass
class Console:
    enable: bool
    level: str


@dataclass
class LoggingConfig:
    file: File
    console: Console


# 数据库配置
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int


@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str


@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str


@dataclass
class LLMConfig:
    model_name: str
    api_key: str
    base_url: str
    fast_model_name: str = ""
    reasoning_model_name: str = ""
    timeout_seconds: float = 90.0
    max_retries: int = 2


@dataclass
class QueryConfig:
    max_rows: int = 500
    timeout_seconds: float = 15.0
    workflow_timeout_seconds: float = 180.0
    max_corrections: int = 3


@dataclass
class RetrievalConfig:
    dense_limit: int = 8
    lexical_limit: int = 8
    fusion_limit: int = 10
    rrf_k: int = 60
    keyword_expansion_mode: str = "local"
    selection_mode: str = "deterministic"
    selection_column_limit: int = 8
    selection_metric_limit: int = 2


@dataclass
class CacheConfig:
    enabled: bool = True
    ttl_seconds: float = 900.0
    max_entries: int = 512


@dataclass
class ObservabilityConfig:
    recent_requests: int = 200


@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig
    query: QueryConfig = field(default_factory=QueryConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)


config_file = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
context = OmegaConf.load(config_file)
schema = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))


def _apply_environment_overrides(config: AppConfig) -> None:
    """Environment variables take precedence over the YAML file."""
    string_overrides = {
        "DATA_AGENT_LLM_API_KEY": (config.llm, "api_key"),
        "DATA_AGENT_LLM_BASE_URL": (config.llm, "base_url"),
        "DATA_AGENT_LLM_MODEL": (config.llm, "model_name"),
        "DATA_AGENT_LLM_FAST_MODEL": (config.llm, "fast_model_name"),
        "DATA_AGENT_LLM_REASONING_MODEL": (config.llm, "reasoning_model_name"),
        "DATA_AGENT_DW_DB_USER": (config.db_dw, "user"),
        "DATA_AGENT_DW_DB_PASSWORD": (config.db_dw, "password"),
    }
    for env_name, (target, attribute) in string_overrides.items():
        if value := os.getenv(env_name):
            setattr(target, attribute, value)


_apply_environment_overrides(app_config)

if __name__ == '__main__':
    print(app_config.es.host)
