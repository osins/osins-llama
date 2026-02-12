# 服务器实现开发指南

## 概述

本指南详细描述了基于 llama-cpp-python 的生产级推理 API 服务的服务器实现，兼容 OpenAI Chat/Completion 接口风格。实现目标包括高并发、可观测、安全、可测试、可扩展的系统架构。

## 技术栈

### 核心框架
- FastAPI（API 框架）
- Uvicorn + Gunicorn（生产部署）
- Pydantic v2（数据校验）
- llama-cpp-python（推理核心）

### 并发控制
- asyncio
- anyio
- 自定义请求队列

### 安全
- OAuth2 Bearer Token
- HMAC 校验（可选）
- IP 白名单（可选）
- TLS（反向代理层）

### 观测
- structlog（结构化日志）
- Prometheus（指标）
- OpenTelemetry（链路追踪）

### 缓存
- Redis（可选，token缓存/限流）

### 测试
- pytest
- httpx
- pytest-asyncio

## 系统架构

### 架构分层

```
API 层
→ 路由
→ 请求校验
→ 鉴权

服务层
→ 推理调度器
→ 模型管理器
→ Token 统计
→ 并发控制

核心层
→ llama_cpp 封装
→ 生成逻辑
→ Stream 管理

基础设施层
→ 日志
→ 指标
→ 配置
→ 异常体系
```

## 目录结构设计

```
src/
server/
app.py
config.py
dependency.py
lifecycle.py

api/
routes/
health.py
completion.py
chat.py
models.py

services/
inference_service.py
model_manager.py
scheduler.py
token_service.py

core/
llama_wrapper.py
stream_generator.py
error_codes.py

schemas/
completion_request.py
completion_response.py
chat_request.py
chat_response.py
usage.py
error_response.py

middleware/
auth_middleware.py
logging_middleware.py
rate_limit_middleware.py

utils/
token_utils.py
id_generator.py

tests/
unit/
integration/
```

## 数据模型设计（Pydantic v2）

### 1. CompletionRequest

字段：
- model: str
- prompt: Union[str, List[str]]
- max_tokens: int
- temperature: float
- top_p: float
- stream: bool
- stop: Optional[List[str]]
- presence_penalty: float
- frequency_penalty: float
- user: Optional[str]

必须校验：
- max_tokens > 0
- temperature ∈ [0, 2]
- top_p ∈ (0, 1]
- prompt 非空

### 2. ChatMessage

- role: Literal["system","user","assistant"]
- content: str

### 3. ChatCompletionRequest

- model
- messages: List[ChatMessage]
- stream
- 其他生成参数

必须：
- 至少一个 user 消息
- message 顺序合法

### 4. Usage

- prompt_tokens
- completion_tokens
- total_tokens

### 5. ErrorResponse

- error:
  - code
  - message
  - type
  - param

## 核心模块设计

### 一）ModelManager

职责：
- 加载模型
- 卸载模型
- 获取实例
- 线程安全管理

函数级任务：
- load_model(model_name: str) -> None
- unload_model(model_name: str) -> None
- get_model(model_name: str) -> Llama
- list_models() -> List[str]
- validate_model_exists(model_name: str)

安全：
- 禁止路径遍历
- 强制模型目录白名单

### 二）InferenceService

职责：
- 执行推理
- 控制参数
- 处理异常

函数：
- generate_completion(request: CompletionRequest)
- generate_chat_completion(request: ChatCompletionRequest)
- _stream_completion(...)
- _validate_generation_args(...)
- _calculate_usage(...)

必须：
- 严格异常捕获
- 防止阻塞主线程
- 控制最大 tokens 上限

### 三）Scheduler（并发控制）

职责：
- 请求排队
- 限制最大并发
- 超时控制

函数：
- submit_task(task)
- _acquire_slot()
- _release_slot()
- handle_timeout()

实现：
- asyncio.Semaphore
- 队列长度上限
- 请求超时自动取消

### 四）TokenService

职责：
- 统一 token 计算
- 与模型 tokenizer 对齐

函数：
- count_tokens(text)
- count_tokens_messages(messages)
- validate_context_length(prompt_tokens, max_tokens)

## API 路由设计

### 1. GET /v1/health
返回：
- status
- model_loaded
- queue_length

### 2. GET /v1/models
返回模型列表

### 3. POST /v1/completions
支持 stream

### 4. POST /v1/chat/completions
支持 stream

流式实现：
- 使用 StreamingResponse
- 生成 SSE 格式
- 每 chunk 包含 id + delta

## 中间件设计

### 1. AuthMiddleware

- 验证 Bearer Token
- 校验签名
- 失败返回 401

### 2. RateLimitMiddleware

- 基于 IP 或 user
- Redis 计数
- 超限返回 429

### 3. LoggingMiddleware

- 请求 ID
- 响应时间
- Token 用量

## 异常体系

统一错误码：
- MODEL_NOT_FOUND
- INVALID_REQUEST
- CONTEXT_OVERFLOW
- RATE_LIMIT_EXCEEDED
- AUTH_FAILED
- INTERNAL_ERROR

实现：
```python
class LLMServiceException(Exception):
    code
    message
    http_status
```

全局异常处理器统一格式输出

## 安全设计

1. 禁止动态加载任意路径模型
2. 限制 max_tokens 最大值
3. 限制 prompt 长度
4. 禁止空 token 无限生成
5. 流式必须检测客户端断开
6. 超时强制取消任务
7. 严格类型校验

## 测试设计

### 单元测试
- 参数校验边界
- token 统计
- 并发上限
- 超时取消

### 集成测试
- 正常 completion
- stream completion
- 并发 50 请求
- 非法参数
- 未授权访问

### 性能测试
- QPS 基准
- 内存泄漏测试
- 长时间稳定性

## 开发计划（细化到函数）

### 阶段 1：基础结构
- app.py 初始化
- config 加载
- 生命周期管理
- 健康检查接口

### 阶段 2：模型管理
- 实现 ModelManager
- 实现模型加载校验
- 单元测试

### 阶段 3：推理服务
- Completion
- Chat
- Stream
- Usage 统计

### 阶段 4：并发与限流
- Scheduler
- Middleware
- 超时机制

### 阶段 5：安全增强
- 鉴权
- 参数白名单
- 错误体系

### 阶段 6：测试与压测
- 单元覆盖 > 90%
- 集成测试
- CI 校验

## 生产部署建议

推荐部署方式：
- Gunicorn + UvicornWorker
- 多 worker
- 单 worker 内限制最大并发

Nginx 反向代理：
- 启用 TLS
- 限制请求体大小

容器化：
- 禁止 root
- 限制内存
- 限制 CPU

## 可扩展能力预留

- 多模型路由
- LoRA 动态加载
- 分布式调度
- 计费模块
- 审计日志
- 灰度发布

## 验收标准

- [ ] 所有路由功能正常工作
- [ ] 参数校验准确
- [ ] OpenAI兼容性达到100%
- [ ] 错误处理机制完善
- [ ] 流式和非流式响应功能正确
- [ ] 性能满足要求
- [ ] 并发控制功能正常
- [ ] 单元测试覆盖率≥90%
- [ ] Token计算准确
- [ ] 安全验证可靠
- [ ] 限流功能有效
- [ ] 类型注解完整
- [ ] 统一异常处理
- [ ] 全面日志记录
- [ ] 测试覆盖率达标