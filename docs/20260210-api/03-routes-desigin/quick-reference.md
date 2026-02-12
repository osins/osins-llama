# 路由设计快速参考

## 架构概览
路由设计分为多层：
- API层：`completion_routes.py` 和 `chat_routes.py`
- 服务层：`completion_service.py` 和 `chat_service.py`
- 工具层：`token_utils.py`, `rate_limiter.py`, `security.py`, `concurrency_controller.py`

## 关键约束
1. **API Schema层禁止泛型**：泛型只能存在于内部推理或适配层
2. **严格OpenAI兼容**：所有响应格式必须与OpenAI API完全一致
3. **错误处理一致性**：错误响应格式必须与OpenAI API一致
4. **并发安全**：确保模型实例在并发请求下的安全性
5. **准确Token计数**：使用适当的tokenizer进行准确的token计数
6. **分布式兼容**：在分布式环境下使用Redis等外部存储实现限流和会话管理

## 实现顺序
1. `completion_routes.py` - 实现/v1/completions路由
2. `chat_routes.py` - 实现/v1/chat/completions路由
3. `completion_service.py` - 实现Completion服务逻辑
4. `chat_service.py` - 实现Chat服务逻辑
5. `token_utils.py` - 实现token计算工具
6. API Key验证功能
7. 限流功能（支持Redis分布式存储）
8. 并发控制功能（支持Redis分布式协调）

## 验证标准
- Schema校验与拒绝策略：对外API启用严格校验
- OpenAPI生成一致性：生成的API文档与OpenAI官方字段名/可选性完全一致
- SDK直连验收：官方Python/JS SDK可无适配代码直连使用

## 配置项
- `config.resources.max_concurrent_requests` - 最大并发请求数
- `config.resources.max_queue_size` - 最大队列长度
- `config.resources.request_timeout_seconds` - 请求超时时间
- `config.resources.max_prompt_tokens` - 最大prompt token数
- `config.api.require_api_key` - 是否需要API Key验证
- `config.security.rate_limit_rps` - 每秒请求数限制
- `config.storage.redis_host` - Redis主机地址
- `config.storage.redis_port` - Redis端口
- `config.storage.redis_db` - Redis数据库索引