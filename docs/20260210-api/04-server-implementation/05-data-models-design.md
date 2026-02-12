# 服务器数据模型设计规范

## 数据模型概述

数据模型是服务器的核心组件，定义了 API 请求和响应的数据结构，确保与 OpenAI API 的兼容性。

## 基础模型设计

### 1. 请求模型 (Request Models)

#### CompletionRequest
- `model` - 模型标识符
- `prompt` - 提示文本 (str 或 List[str])
- `max_tokens` - 最大生成 token 数
- `temperature` - 温度参数 (0.0-2.0)
- `top_p` - Top-p 采样参数 (0.0-1.0)
- `stream` - 是否流式响应 (bool)
- `stop` - 停止序列 (可选 List[str])
- `presence_penalty` - 存在惩罚 (-2.0-2.0)
- `frequency_penalty` - 频率惩罚 (-2.0-2.0)
- `user` - 用户标识 (可选)

##### 验证规则
- max_tokens > 0 且不超过限制
- temperature 在 [0, 2] 范围内
- top_p 在 (0, 1] 范围内
- prompt 非空
- stop 序列长度合理

#### ChatCompletionRequest
- `model` - 模型标识符
- `messages` - 消息列表 (ChatMessage[])
- `max_tokens` - 最大生成 token 数
- `temperature` - 温度参数
- `top_p` - Top-p 采样参数
- `stream` - 是否流式响应
- `stop` - 停止序列
- `presence_penalty` - 存在惩罚
- `frequency_penalty` - 频率惩罚
- `user` - 用户标识 (可选)

##### 验证规则
- messages 非空且至少包含一个用户消息
- 消息顺序合法
- max_tokens 验证
- 其他参数同 CompletionRequest

#### ChatMessage
- `role` - 角色 ("system", "user", "assistant")
- `content` - 消息内容 (str)
- `name` - 发送者名称 (可选 str)

##### 验证规则
- role 必须是允许值之一
- content 非空

### 2. 响应模型 (Response Models)

#### CompletionResponse
- `id` - 响应 ID
- `object` - 对象类型 ("text_completion")
- `created` - 创建时间戳
- `model` - 使用的模型
- `choices` - 选择列表 (CompletionChoice[])
- `usage` - 使用统计 (Usage)

#### ChatCompletionResponse
- `id` - 响应 ID
- `object` - 对象类型 ("chat.completion")
- `created` - 创建时间戳
- `model` - 使用的模型
- `choices` - 选择列表 (ChatCompletionChoice[])
- `usage` - 使用统计 (Usage)

#### CompletionChoice
- `text` - 生成的文本
- `index` - 选择索引
- `logprobs` - 对数概率 (可选)
- `finish_reason` - 完成原因

#### ChatCompletionChoice
- `message` - 生成的消息 (ChatMessage)
- `index` - 选择索引
- `finish_reason` - 完成原因

#### Usage
- `prompt_tokens` - 提示 token 数
- `completion_tokens` - 生成 token 数
- `total_tokens` - 总 token 数

##### 验证规则
- 各 token 数量非负
- total_tokens = prompt_tokens + completion_tokens

#### ErrorResponse
- `error` - 错误信息对象
  - `type` - 错误类型
  - `message` - 错误消息
  - `code` - 错误代码
  - `param` - 相关参数 (可选)

## 流式响应模型

### StreamResponse
- 用于流式传输的 SSE 格式响应
- 每个数据块包含增量更新
- 包含结束标记

### CompletionStreamChoice
- `text` - 增量文本
- `index` - 选择索引
- `finish_reason` - 完成原因 (可选)

### ChatCompletionStreamChoice
- `delta` - 消息增量 (ChatMessage)
- `index` - 选择索引
- `finish_reason` - 完成原因 (可选)

## 枚举类型定义

### FinishReason
- `stop` - 达到最大 token 数或遇到停止序列
- `length` - 达到最大 token 数
- `content_filter` - 内容过滤器激活
- `tool_calls` - 工具调用完成

### Role
- `system` - 系统消息
- `user` - 用户消息
- `assistant` - 助手消息

## 模型验证规则

### 通用验证
- 使用 Pydantic v2 进行数据验证
- 所有必需字段必须提供
- 类型验证严格
- 长度和范围验证

### 特定验证
- 模型名称格式验证
- Token 数量合理性检查
- 消息内容安全性检查
- 参数组合合法性验证

## 模型序列化

### JSON 序列化
- 使用 Pydantic 的 model_dump_json()
- 保持与 OpenAI API 的兼容性
- 正确处理嵌套对象

### 反序列化
- 使用 Pydantic 的 model_validate()
- 严格的类型转换
- 验证后处理

## 性能优化

### 模型缓存
- 缓存模型验证器
- 预编译验证逻辑
- 减少重复验证开销

### 内存管理
- 使用 __slots__ 减少内存占用
- 避免不必要的字段
- 及时释放大对象

## 扩展性设计

### 版本兼容性
- 支持向后兼容
- 可选字段设计
- 默认值策略

### 扩展字段
- 预留扩展空间
- 支持插件化功能
- 配置驱动的字段

## 安全考虑

### 输入验证
- 防止注入攻击
- 限制字段长度
- 验证特殊字符

### 敏感信息
- 不在模型中存储敏感数据
- 使用哈希或加密
- 访问控制

## 测试覆盖

### 验证测试
- 测试所有验证规则
- 边界值测试
- 异常情况测试

### 序列化测试
- JSON 序列化/反序列化测试
- 兼容性测试
- 性能测试

## 最佳实践

1. 严格遵循 OpenAI API 数据格式
2. 使用 Pydantic v2 进行类型验证
3. 实现完整的验证规则
4. 确保序列化兼容性
5. 优化模型性能
6. 考虑扩展性需求
7. 实施安全验证
8. 全面的测试覆盖