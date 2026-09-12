# 第三阶段：性能、缓存与可观测性

## 默认快速链路

默认配置将关键词扩展与 Schema 筛选改为确定性本地计算，只有 SQL 生成和发生错误时的 SQL 纠错调用推理模型。这样把正常请求的大模型调用从约 6 次降为 1 次。

- `retrieval.keyword_expansion_mode: local`：基于业务指标别名、常见同义词和日期模式扩展。
- `retrieval.selection_mode: deterministic`：结合 RRF 排名、BM25 命中、指标必需字段筛选表和字段。
- 两项都可以改成 `llm`，用于消融实验或复杂场景对照。

## 模型分层

`llm.fast_model_name` 服务于关键词扩展和 Schema 筛选，`llm.reasoning_model_name` 服务于 SQL 生成和纠错。留空时都复用 `llm.model_name`，因此旧配置可以直接启动。

生产环境可给 fast 模型配置低成本、低延迟模型，给 reasoning 模型配置推理能力更强的模型。环境变量：

```powershell
$env:DATA_AGENT_LLM_FAST_MODEL="your-fast-model"
$env:DATA_AGENT_LLM_REASONING_MODEL="your-reasoning-model"
```

## 两级缓存

- Retrieval Cache：缓存字段、指标和值的完整混合召回结果。
- LLM Cache：缓存关键词扩展、筛选、SQL 生成和 SQL 纠错结果。
- 相同并发请求会共享同一个计算任务，避免缓存击穿。
- 缓存仅位于当前进程内，TTL 和容量由 `cache` 配置控制；服务重启自动清空。

## 可观测性

SSE 新增三种事件：

- `request`：返回 request_id。
- `node_metric`：节点名称、状态和耗时。
- `trace`：整条链路耗时、各节点耗时、缓存命中次数和模型分层信息。

查询聚合指标：

```text
GET http://localhost:8000/api/metrics
```

返回成功率、平均/P50/P95 延迟、节点平均耗时、最近请求以及缓存统计。

## 性能对比

后端启动后连续执行同一个问题两次：

```powershell
python -m app.scripts.benchmark --rounds 2
```

输出冷请求、热请求延迟、缓存命中情况和加速倍数。完整准确率回归仍使用：

```powershell
python -m app.scripts.evaluate
```
