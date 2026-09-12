# 第二阶段：语义层、混合检索与自动评测

## 架构变化

```text
用户问题
  ├─ Qdrant Dense 语义召回
  └─ BM25 Lexical 精确召回
           ↓
         RRF 融合
           ↓
  LLM 过滤表、字段和指标
           ↓
  Semantic Layer 注入指标公式
           ↓
  Schema Graph 补全中间表和 JOIN 键
           ↓
      生成与安全执行 SQL
```

## 业务语义层

`conf/semantic_layer.yaml` 是业务口径的唯一可信来源，定义：

- 指标标准名称、展示名称与别名；
- 可执行 SQL 表达式；
- 基础事实表和必需字段；
- 可用分析维度和固定过滤条件；
- 事实表与维度表的可信 JOIN 关系。

当前内置 GMV、AOV、订单数、商品销量。新增指标只需扩展 YAML，无需修改
数据库表结构。

## 混合检索

- Dense：BGE Embedding + Qdrant；
- Lexical：元数据配置上的 BM25；
- Fusion：Reciprocal Rank Fusion；
- Trace：状态和日志记录候选 ID、融合分数、召回来源。

可在 `app_config.yaml` 覆盖：

```yaml
retrieval:
  dense_limit: 8
  lexical_limit: 8
  fusion_limit: 10
  rrf_k: 60
```

## Schema Graph

`enrich_schema` 节点在 LLM 过滤之后运行。它会：

1. 补全指标表达式依赖字段；
2. 为多张维度表寻找最短连接路径；
3. 自动加入桥接事实表；
4. 补全 JOIN 两端的主外键；
5. 将可信连接关系显式传给 SQL Prompt。

## 自动评测

启动后端后运行：

```powershell
python -m app.scripts.evaluate
```

只运行前两条用例：

```powershell
python -m app.scripts.evaluate --limit 2
```

报告默认写入 `evals/report.json`，包括：

- 端到端成功率；
- SQL 解析成功率；
- 表召回率；
- 字段召回率；
- 空/非空结果判断准确率；
- 平均端到端耗时；
- 每条用例生成的 SQL、行数和错误信息。

评测会真实调用模型 API，运行前应注意调用次数和费用。
