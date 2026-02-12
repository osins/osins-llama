# Chat Completion Choice模型任务文档

## 任务概述
- **任务编号**: 15
- **任务名称**: Chat Completion Choice模型
- **文件路径**: `models/chat/chat_completion_choice.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatCompletionChoice数据模型，用于表示ChatCompletion API的生成选择结果。该模型需要严格遵循OpenAI ChatCompletions API规范，包含message和finish_reason字段。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - index: int - 选择索引
  - message: ChatMessage - 消息对象
  - finish_reason: ChatFinishReason - 完成原因
  - logprobs: Optional[dict] - 日志概率（可选）
- 遵循OpenAI API的ChatCompletionChoice对象结构
- 使用Pydantic v2语法

## 实现规范
- finish_reason使用ChatFinishReason枚举值
- message字段为ChatMessage对象
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Legacy Completion模型完全隔离

## 代码实现
```python
# models/chat/chat_completion_choice.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from .chat_message import ChatMessage
from .chat_finish_reason import ChatFinishReason

class ChatCompletionChoice(BaseModel):
    """
    Chat Completion Choice 数据模型
    表示 ChatCompletion API 的生成选择结果，包含 message 和 finish_reason。
    严格遵循 OpenAI ChatCompletions API 规范。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    index: int
    message: ChatMessage
    finish_reason: ChatFinishReason
    logprobs: Optional[dict] = None
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的ChatCompletionChoice结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- finish_reason仅接受合法的ChatFinishReason值

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Chat Message模型文档](task-11-chat-message.md)
- [Chat Finish Reason模型文档](task-14-chat-finish-reason.md)

## 依赖关系
- 依赖: `models/chat/chat_message.py`
- 依赖: `models/chat/chat_finish_reason.py`

## 备注
此模型为ChatCompletion API的选择模型，与Legacy Completion选择模型完全隔离。