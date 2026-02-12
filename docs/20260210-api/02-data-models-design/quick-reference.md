# 数据模型设计快速参考

## 架构概览

```
models/
├── common/           # 公共基础模型（强制复用）
│   ├── usage.py      # 使用量统计
│   └── error_response.py  # 错误响应
├── legacy/           # Legacy Completion 层（冻结能力）
│   ├── completion_request.py
│   ├── completion_params.py
│   ├── completion_choice.py
│   └── completion_response.py
└── chat/             # ChatCompletion 稳定层（主力）
    ├── chat_role.py
    ├── chat_content_part.py
    ├── chat_message.py
    ├── tool_call.py
    ├── chat_completion_choice.py
    ├── chat_completion_request.py
    └── chat_completion_response.py
```

## 关键约束速查

### 1. 模型隔离
- ✅ Legacy与Chat模型完全物理隔离
- ❌ 禁止共享Choice/Message模型

### 2. 枚举分离
- **Completion finish_reason**:
  - `"stop"`
  - `"length"`
  - `"content_filter"`

- **ChatCompletion finish_reason**:
  - `"stop"`
  - `"length"`
  - `"tool_calls"`
  - `"content_filter"`

### 3. Content结构
- ✅ `chat_message.content` 使用结构化content parts
- ❌ 禁止使用简单str类型

### 4. 角色枚举
- 必须包含: `'user'`, `'assistant'`, `'system'`, `'tool'`

### 5. 泛型限制
- ✅ API Schema层禁止泛型
- ✅ 泛型仅限内部推理层使用

### 6. Streaming协议
- ✅ ChatCompletionResponse用于非流式响应
- ✅ Streaming使用独立的delta结构
- ❌ 禁止复用response model

### 7. Error处理
- ✅ HTTP状态码 ≠ error.type
- ✅ 允许HTTP 200时返回error

## 实现顺序（最小返工路径）

### 阶段1：公共基础模型
1. `models/common/usage.py`
2. `models/common/error_response.py`

### 阶段2：Legacy Completion模型
3. `models/legacy/completion_params.py`
4. `models/legacy/completion_request.py`
5. `models/legacy/completion_choice.py`
6. `models/legacy/completion_response.py`

### 阶段3：Chat模型核心
7. `models/chat/chat_role.py`
8. `models/chat/chat_content_part.py`
9. `models/chat/tool_call.py`
10. `models/chat/chat_message.py`

### 阶段4：Chat Completion接口模型
11. `models/chat/chat_completion_choice.py`
12. `models/chat/chat_completion_request.py`
13. `models/chat/chat_completion_response.py`

## 验收检查清单

### Schema校验
- [ ] 缺字段返回4xx错误
- [ ] 多字段返回4xx错误
- [ ] 禁止容错解析

### OpenAPI一致性
- [ ] 生成文档与OpenAI官方字段名一致
- [ ] 可选性与官方一致
- [ ] 无alias或隐式转换

### SDK直连测试
- [ ] 官方Python SDK非流式ChatCompletion
- [ ] 官方Python SDK流式ChatCompletion
- [ ] 官方JS SDK非流式ChatCompletion
- [ ] 官方JS SDK流式ChatCompletion
- [ ] 官方Python/JS SDK Legacy Completion
- [ ] 无自定义适配代码

## 常见陷阱

1. **Content Part实现**: 严格按照OpenAI官方schema，不要优化
2. **Tool Call实现**: 严格按照OpenAI官方字段层级，不要抽象
3. **Streaming Delta**: 与Response模型完全分离
4. **FinishReason**: 按接口类型分别定义枚举