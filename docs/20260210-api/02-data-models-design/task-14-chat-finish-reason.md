# Chat Finish Reason模型任务文档

## 任务概述
- **任务编号**: 14
- **任务名称**: Chat Finish Reason模型
- **文件路径**: `models/chat/chat_finish_reason.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatFinishReason枚举，用于表示ChatCompletion API的完成原因。该枚举需要严格遵循OpenAI ChatCompletions API规范，包含Completion API和Chat API允许的值，与Legacy Completion的FinishReason枚举分离。

## 技术要求
- 使用Python Enum作为基类
- 包含以下枚举值：
  - STOP: "stop" - 达到自然停止点
  - LENGTH: "length" - 达到最大长度
  - TOOL_CALLS: "tool_calls" - 工具调用完成
  - CONTENT_FILTER: "content_filter" - 内容过滤器触发
- 遵循OpenAI API的ChatFinishReason枚举结构
- 与CompletionFinishReason枚举完全分离

## 实现规范
- 允许"stop", "length", "tool_calls", "content_filter"值
- 包含Chat API专用的"tool_calls"值
- 使用StrEnum或继承str和Enum以支持JSON序列化
- 遵循100% OpenAI兼容策略
- 与CompletionFinishReason枚举完全物理隔离

## 代码实现
```python
# models/chat/chat_finish_reason.py

from enum import Enum

class ChatFinishReason(str, Enum):
    """
    Chat Finish Reason 枚举
    表示 ChatCompletion API 的完成原因，严格遵循 OpenAI ChatCompletions API 规范。
    包含Chat API专用的值，与CompletionFinishReason枚举完全分离。
    """
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
```

## 验证标准
- 枚举值与OpenAI官方API完全一致
- 包含所有必需的枚举值
- 包含Chat API专用的"tool_calls"值
- 通过单元测试验证枚举值正确性

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)

## 依赖关系
- 无前置依赖

## 备注
此枚举与CompletionFinishReason完全分离，确保Chat API能正确表达tool_calls完成原因。