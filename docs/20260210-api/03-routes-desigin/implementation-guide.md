# 路由设计实施指南

## 概述
本文档提供了路由设计的实施步骤和最佳实践，确保与OpenAI API的完全兼容性。

## 实施步骤

### 1. completion_routes.py 实现
- 路径：`/v1/completions`
- 方法：POST
- 功能：处理文本生成请求
- 参数验证：使用Pydantic模型验证请求体
- 流程：
  1. API Key校验
  2. 请求体长度与token数量校验
  3. 调用`completion_service.generate()`
  4. 根据配置返回流式或完整响应
- 异常处理：统一返回JSON，HTTP状态码：
  - 400: 参数错误
  - 401: 未授权
  - 429: 排队超限
  - 504: 超时

### 2. chat_routes.py 实现
- 路径：`/v1/chat/completions`
- 方法：POST
- 功能：处理多轮对话生成请求
- 参数验证：使用Pydantic模型验证请求体（支持messages列表）
- 流程：
  1. API Key校验
  2. 请求体长度与token数量校验
  3. 调用`chat_service.generate()`
  4. 根据配置返回流式或完整响应
- 异常处理：与`/v1/completions`保持一致

### 3. 服务层集成
- 调用`ModelManager.get_instance(config).generate()`
- 对prompt或messages做token限制检查
- 对生成结果进行OpenAI兼容格式化
- 处理流式返回逻辑（按token或按chunk）
- 捕获模型生成异常，统一转换为HTTP错误

### 4. 并发与排队
- 使用`asyncio.Semaphore`控制最大同时请求数
- 队列长度由`config.resources.max_queue_size`配置
- 超过队列或请求超时返回429/504
- 严格串行确保单一模型实例安全推理

### 5. 安全策略
- API Key验证（可配置多Key）
- 限流：RPS/RPM
- 请求体大小限制由`config.api.max_request_body_size`控制

## 实施顺序

### 阶段1：基础路由框架
1. 创建`src/llama/api/completion_routes.py`
2. 创建`src/llama/api/chat_routes.py`
3. 设置基本路由结构和错误处理

### 阶段2：服务层集成
4. 创建`src/llama/services/completion_service.py`
5. 创建`src/llama/services/chat_service.py`
6. 集成ModelManager

### 阶段3：配置与安全
7. 实现API Key验证
8. 实现限流功能
9. 实现并发控制

## 常见错误避免

### 1. 混合使用流式和非流式响应
- 错误：在同一个端点中混合处理流式和非流式响应
- 解决：严格按配置决定响应类型

### 2. 忽略OpenAI兼容性
- 错误：修改OpenAI API响应格式
- 解决：严格遵循OpenAI官方API响应格式

### 3. 不正确的错误处理
- 错误：返回非标准错误格式
- 解决：遵循OpenAI错误响应格式

### 4. 缺少安全措施
- 错误：忽略API Key验证或限流
- 解决：实现完整的安全策略

### 5. 状态标记不一致
- 错误：不同组件间的状态标记不一致，导致系统行为异常
- 解决：确保所有状态标记的一致性，如finish_reason枚举值、请求状态等

### 6. 不正确的Token计算
- 错误：使用简单字符串分割计算Token，导致与实际模型使用的Token数量不一致
- 解决：使用适当的tokenizer进行准确的Token计数

## 验证标准

### 1. 功能验证
- 非流式Completion请求正常工作
- 流式Completion请求正常工作
- 非流式ChatCompletion请求正常工作
- 流式ChatCompletion请求正常工作

### 2. 兼容性验证
- 响应格式与OpenAI API完全一致
- 错误处理与OpenAI API行为一致
- 参数验证与OpenAI API一致

### 3. 性能验证
- 并发控制按配置生效
- 队列机制正常工作
- 超时处理正常工作

## 预计实施时间
- 阶段1：2小时
- 阶段2：4小时
- 阶段3：2小时
- 总计：8小时