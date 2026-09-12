# DataPilot —— 企业级智能问数 Agent

DataPilot 是一个面向电商经营分析场景的自然语言问数系统。用户使用自然语言提出业务问题后，系统会自动理解指标与维度、检索数据库元数据、生成并安全执行 SQL，并通过流式界面展示 Agent 的执行过程与查询结果。

## 核心能力

- **Agent 工作流**：基于 LangGraph 编排关键词解析、元数据召回、Schema 筛选、SQL 生成、校验、执行和纠错节点，支持并行召回、条件路由以及最多 3 次 SQL 自动纠错。
- **混合 RAG**：融合 BGE Embedding + Qdrant 向量检索与 BM25 关键词检索，并使用 RRF 完成结果排序；结合业务语义层和 Schema Graph 补全指标口径、关联字段及 JOIN 路径。
- **SQL 安全防护**：基于 SQLGlot 对生成 SQL 进行 AST 解析与动态白名单校验，仅允许单条只读查询，并结合 EXPLAIN、执行超时、返回行数限制及只读数据库账号降低执行风险。
- **性能与可观测性**：通过模型分层、两级 TTL 缓存和防缓存击穿减少模型调用；支持 SSE 流式响应、请求链路追踪、节点耗时统计及 P50/P95 延迟监控。

## 技术栈

- 后端：Python、FastAPI、LangGraph、LangChain
- 检索：RAG、Qdrant、BM25、RRF、Elasticsearch、BGE Embedding
- 数据与安全：MySQL、SQLAlchemy、SQLGlot
- 前端：Vue 3、Vite
- 工程化：Docker Compose、uv、Pytest

## 工作流程

```text
用户问题
   ↓
关键词解析
   ├── 字段召回（Qdrant + BM25）
   ├── 指标召回（Qdrant + BM25）
   └── 枚举值召回（Elasticsearch）
   ↓
RRF 融合与 Schema 筛选
   ↓
语义层增强与 JOIN 路径补全
   ↓
SQL 生成 → 安全校验 → 执行
                ↑         │
                └── 自动纠错
```

## 项目结构

```text
DataPilot/
├── data-agent/           # FastAPI + LangGraph 后端
│   ├── app/              # Agent、API、检索、数据访问与基础设施
│   ├── conf/             # 配置模板、语义层和元数据配置
│   ├── docs/             # 安全、RAG、评测与性能设计文档
│   ├── evals/            # Text-to-SQL 评测用例
│   └── tests/            # 自动化测试
└── data-agent-fronted/   # Vue 3 前端
```

## 本地运行

### 1. 启动基础服务

项目依赖 MySQL、Qdrant、Elasticsearch 和 BGE Embedding 服务，请先通过 Docker Compose 启动这些服务，并确认对应端口可用。

### 2. 配置并启动后端

```powershell
cd data-agent
Copy-Item conf/app_config.example.yaml conf/app_config.yaml
```

编辑 `conf/app_config.yaml`，填写数据库连接、模型地址和 API Key，然后执行：

```powershell
uv sync
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
uv run python main.py
```

后端默认运行在 `http://localhost:8000`。

### 3. 启动前端

```powershell
cd data-agent-fronted
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`。

## 测试与评测

```powershell
cd data-agent
uv run pytest -q
uv run python -m app.scripts.evaluate
uv run python -m app.scripts.benchmark --rounds 2
```

- `pytest`：运行单元测试与安全校验测试。
- `evaluate`：输出 Text-to-SQL 成功率、Schema 召回率和端到端耗时等指标。
- `benchmark`：对比冷请求与缓存命中后的响应延迟。
