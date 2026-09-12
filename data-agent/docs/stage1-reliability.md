# 第一阶段：可靠性与安全性改造

## 已实现

- 使用 SQLGlot AST 解析 SQL，只允许单条只读查询。
- 根据 RAG 筛选后的表和字段建立动态白名单。
- 禁止写操作、多语句、`SELECT *` 和高风险函数。
- 自动将查询结果限制在 `query.max_rows` 以内。
- 对 `EXPLAIN` 和正式查询设置超时。
- SQL 解析、Schema 或执行错误最多自动纠正 `query.max_corrections` 次。
- 安全违规、数据库不可用和超时不会盲目重试。
- SSE 错误信息分类并脱敏，HTML 错误页不会直接展示给用户。
- 空结果显示明确提示。
- 支持通过环境变量覆盖 LLM 密钥和数仓只读账号。
- `.gitignore` 默认忽略真实的 `conf/app_config.yaml`，使用
  `conf/app_config.example.yaml` 作为可提交模板。

## 可选配置

可在 `conf/app_config.yaml` 增加：

```yaml
query:
  max_rows: 500
  timeout_seconds: 15
  workflow_timeout_seconds: 180
  max_corrections: 3
```

缺省时会自动使用上述默认值。

## 只读数据库账号

修改 `docs/create_readonly_user.sql` 中的密码，然后以 MySQL 管理员执行。
通过 `DATA_AGENT_DW_DB_USER` 和 `DATA_AGENT_DW_DB_PASSWORD` 配置运行账号。

## 测试

```powershell
uv sync
uv run pytest -q
```
