```markdown
# LLM 服务路由设计文档

**文件名:** `llm-service-routes-design.md`

---

## 1. 设计目标

- 实现 OpenAI 兼容的 API 接口  
- 支持 `/v1/completions` 与 `/v1/chat/completions`  
- 支持流式和非流式响应  
- 并发控制、排队、超时由 `config.yaml` 配置  
- API Key 验证与限流  

---

## 2. 文件结构

```

src/llama/api/
├── completion_routes.py   # /v1/completions 路由
├── chat_routes.py         # /v1/chat/completions 路由

```
```

src/llama/services/
├── completion_service.py  # Completion 服务逻辑
├── chat_service.py        # Chat Completion 服务逻辑

```

---

## 3. Route 设计

### 3.1 completion_routes.py

- 路径：`/v1/completions`  
- 方法：POST  
- 功能：处理文本生成请求  
- 参数验证：Pydantic 模型  
- 流程：
  1. API Key 校验  
  2. 请求体长度与 token 数量校验  
  3. 调用 `completion_service.generate()`  
  4. 根据配置返回流式或完整响应  
- 异常处理：统一返回 JSON，HTTP 状态码：
  - 400: 参数错误  
  - 401: 未授权  
  - 429: 排队超限  
  - 504: 超时  

### 3.2 chat_routes.py

- 路径：`/v1/chat/completions`  
- 方法：POST  
- 功能：处理多轮对话生成请求  
- 参数验证：Pydantic 模型（支持 messages 列表）  
- 流程：
  1. API Key 校验  
  2. 请求体长度与 token 数量校验  
  3. 调用 `chat_service.generate()`  
  4. 根据配置返回流式或完整响应  
- 异常处理：与 `/v1/completions` 保持一致  

---

## 4. Service 层设计

- **completion_service.py / chat_service.py**  
- 调用 `ModelManager.get_instance(config).generate()`  
- 对 prompt 或 messages 做 token 限制检查  
- 对生成结果进行 OpenAI 兼容格式化  
- 处理流式返回逻辑（按 token 或按 chunk）  
- 捕获模型生成异常，统一转换为 HTTP 错误  

---

## 5. 并发与排队

- 使用 `asyncio.Semaphore` 控制最大同时请求数  
- 队列长度由 `config.resources.max_queue_size` 配置  
- 超过队列或请求超时返回 429 / 504  
- 严格串行确保单一模型实例安全推理  

---

## 6. 安全策略

- API Key 验证（可配置多 Key）  
- 限流：RPS / RPM  
- 请求体大小限制由 `config.api.max_request_body_size` 控制  

---

## 7. 调用链示意

```

HTTP POST /v1/completions 或 /v1/chat/completions
↓
Route Layer (completion_routes.py / chat_routes.py)
↓
Service Layer (completion_service.py / chat_service.py)
↓
ModelManager.generate() (单实例 + Semaphore + 排队 + 超时)
↓
llama-cpp-python 推理
↓
Service 格式化为 OpenAI 兼容 JSON
↓
Route 返回 HTTP Response

```

---

## 8. 配置动态生效

- Route 层和 Service 层根据 `config.yaml` 控制流式、并发、排队、超时等行为  
- 修改配置需重启服务生效  
- 核心模型实例保持单例，避免重复加载  
