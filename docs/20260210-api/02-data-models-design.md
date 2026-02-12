# 数据模型设计

## 总体兼容策略
对外行为 100% 对齐 OpenAI 官方 API，包括：
- URL 路径
- 请求/响应 JSON 结构
- 字段命名、可选性、枚举值
- 错误返回格式

允许 legacy 模式，但必须显式分层：
- Legacy 仅用于 `/v1/completions` 接口和旧客户端
- ChatCompletion 是"当前稳定层"，需完全实现且结构与官方一致

## 目录结构
```
models/
├── common/           # 公共基础模型（强制复用）
│   ├── usage.py      # 使用量统计
│   └── error_response.py  # 错误响应
├── legacy/           # Legacy Completion 层（冻结能力）
│   ├── completion_request.py
│   ├── completion_params.py
│   ├── completion_choice.py
│   ├── completion_response.py
│   ├── completion_finish_reason.py          # 完成原因枚举
│   └── completion_stream_delta.py           # 流式响应增量（若支持stream）
└── chat/             # ChatCompletion 稳定层（主力）
    ├── chat_role.py
    ├── chat_content_part.py
    ├── chat_message.py
    ├── tool_call.py
    ├── tool_call_function.py                # 工具调用函数结构
    ├── chat_finish_reason.py                # 聊天完成原因枚举
    ├── chat_completion_choice.py
    ├── chat_completion_request.py
    ├── chat_completion_response.py
    ├── chat_completion_delta.py             # 流式响应增量
    └── chat_completion_chunk.py             # 流式响应块
```

## 分层模型规范

### 1. 公共基础模型（强制复用）
#### `models/common/usage.py`
- 使用量统计数据模型
- 所有接口统一使用，不允许复制定义
- 严格遵循 OpenAI 格式

#### `models/common/error_response.py`
- 错误响应数据模型
- 必须 100% 符合 OpenAI 格式

### 2. Legacy Completion 层（冻结能力）
适用于接口：`POST /v1/completions`

强约束：
- 只允许 text 输出
- 不允许 tool / function / multimodal
- 不与 chat 共享任何 Choice / Message 模型

#### `models/legacy/completion_request.py`
- 文本生成请求数据模型
- 严格遵循 OpenAI completions API 规范

#### `models/legacy/completion_params.py`
- 通用生成参数数据模型
- 包含 temperature, max_tokens 等参数

#### `models/legacy/completion_choice.py`
- 文本生成选择数据模型
- 仅包含 text 输出字段

#### `models/legacy/completion_response.py`
- 文本生成响应数据模型
- 包含 usage 信息

该层一旦完成，禁止再加字段，只做 bugfix。

### 3. ChatCompletion 稳定层（主力）
适用于接口：`POST /v1/chat/completions`

必须支持：
- 多 message
- content parts（非 str）
- tool calls
- streaming delta（结构预留）
- 严格 role 枚举

#### `models/chat/chat_role.py`
- 聊天角色枚举
- 必须包含 'user', 'assistant', 'system', 'tool' 等值

#### `models/chat/chat_content_part.py`
- 聊天内容部件数据模型
- 支持文本、图像等多种内容类型
- 不能简单使用 str 类型

#### `models/chat/chat_message.py`
- 聊天消息数据模型
- 包含 role 和 content（结构化 parts）

#### `models/chat/tool_call.py`
- 工具调用数据模型
- 支持函数调用等功能

#### `models/chat/chat_completion_choice.py`
- 聊天生成选择数据模型
- 包含 message 和 finish_reason

#### `models/chat/chat_completion_request.py`
- 聊天生成请求数据模型
- 严格遵循 OpenAI chat completions API 规范

#### `models/chat/chat_completion_response.py`
- 聊天生成响应数据模型
- 包含 choices 和 usage 信息

## 技术约束（硬性规定）
1. **API Schema 层禁止泛型**：泛型只能存在于内部推理或适配层
2. **Content 结构化**：`chat_message.content` 必须是结构化的 content parts，不能是简单的 str
3. **Role 枚举完整性**：必须包含 'user', 'assistant', 'system', 'tool' 等角色以支持 function/tool calling
4. **Completion/Chat 模型分离**：禁止混用字段，避免客户端解析出现未定义行为
5. **FinishReason 枚举按接口区分**：Completion 和 ChatCompletion 的 finish_reason 枚举必须分别定义
   - Completion finish_reason：`"stop"`, `"length"`, `"content_filter"`
   - ChatCompletion finish_reason：`"stop"`, `"length"`, `"tool_calls"`, `"content_filter"`
   - 禁止复用同一个 FinishReason 枚举，否则 Chat tool_calls 无法正确表达，Completion 可能出现非法值
6. **Streaming 协议行为独立**：ChatCompletionResponse 是非 streaming 完整响应模型，Streaming 使用独立的 delta schema，不复用 response model
   - ChatCompletionResponse 仅用于非流式响应
   - 流式响应使用独立的 delta 结构
   - 否则 OpenAI SDK streaming 会解析失败
7. **ErrorResponse 独立于 HTTP 状态码**：HTTP 状态码 ≠ error.type
   - 即使 HTTP 200，也可能返回 error（部分 SDK 允许）
   - 这是 OpenAI 官方行为，必须在 error_response 中体现

## 设计原则
- 每个数据模型职责单一
- 严格遵循 OpenAI API 规范（100%兼容）
- 分层架构清晰，避免模型混用
- 优先实现公共模型以确保一致性

## 实现执行顺序（最小返工风险）
按以下顺序实现，以降低后期返工风险：

### 阶段 1：公共基础模型
1. `models/common/usage.py`
2. `models/common/error_response.py`

（公共层一旦稳定，后续不会再动）

### 阶段 2：Legacy Completion 模型
3. `models/legacy/completion_params.py`
4. `models/legacy/completion_request.py`
5. `models/legacy/completion_choice.py`
6. `models/legacy/completion_response.py`
7. `models/legacy/completion_finish_reason.py`
8. `models/legacy/completion_stream_delta.py` （若支持stream）

（Legacy 层一次性完成并冻结）

### 阶段 3：Chat 模型核心
9. `models/chat/chat_role.py`
10. `models/chat/chat_content_part.py`
11. `models/chat/tool_call.py`
12. `models/chat/tool_call_function.py`
13. `models/chat/chat_message.py`
14. `models/chat/chat_finish_reason.py`

（Chat 的语义核心，最为重要）

### 阶段 4：Chat Completion 接口模型
15. `models/chat/chat_completion_choice.py`
16. `models/chat/chat_completion_request.py`
17. `models/chat/chat_completion_response.py`
18. `models/chat/chat_completion_delta.py`
19. `models/chat/chat_completion_chunk.py`

## 实现阶段强制校验清单
为确保实现阶段同样"不可回退"，以下校验标准必须满足：

### 1. Schema 校验与拒绝策略
- 对外 API 必须启用严格校验（缺字段/多字段即 4xx）
- 禁止"容错解析"（例如将 str 自动转为 content parts）
- 严格按照 OpenAI 官方 API 规范进行数据校验

### 2. OpenAPI 生成一致性
- 从这些模型生成 OpenAPI 文档后，与 OpenAI 官方字段名/可选性逐项 diff
- 不允许通过 alias 或隐式转换掩盖不一致
- 生成的 API 文档必须与 OpenAI 官方文档保持完全一致

### 3. SDK 直连验收
至少使用官方 Python/JS SDK 完成以下测试：
- 非流式 ChatCompletion
- 流式 ChatCompletion（delta）
- Legacy Completion

以"无自定义适配代码"为通过标准，确保与官方 SDK 完全兼容。

## 重要实现提醒
在实现 `models/chat/chat_content_part.py` 和 `models/chat/tool_call.py` 时，务必严格对齐 OpenAI 官方字段层级和命名，不得进行任何"更合理"的抽象或优化。即使认为 OpenAI 的 schema 设计不够优雅，也必须完全照抄，以确保官方 SDK 在各种边界情况下都能正常工作，特别是在 streaming 和 tool_calls 的场景中。