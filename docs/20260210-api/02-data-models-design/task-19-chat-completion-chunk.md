# Chat Completion Chunk模型任务文档

## 任务概述
- **任务编号**: 19
- **任务名称**: Chat Completion Chunk模型
- **文件路径**: `models/chat/chat_completion_chunk.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatCompletionChunk数据模型，用于表示ChatCompletion API流式响应的数据块。该模型需要严格遵循OpenAI ChatCompletions API流式响应规范，包含delta和finish_reason字段。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - id: str - 响应ID
  - object: str - 对象类型（固定为"chat.completion.chunk"）
  - created: int - 创建时间戳
  - model: str - 模型名称
  - choices: List[ChatCompletionChunkChoice] - 选择列表
  - usage: Optional[Usage] - 使用量统计（仅在最后一块中提供）
- 遵循OpenAI API的ChatCompletionChunk对象结构
- 使用Pydantic v2语法

## 实现规范
- object字段固定为"chat.completion.chunk"
- choices字段为ChatCompletionChunkChoice对象列表
- usage字段仅在最终chunk中提供
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与非流式响应模型完全隔离
- 与Legacy Completion流式模型完全隔离

## 代码实现
```python
# models/chat/chat_completion_chunk.py

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .chat_completion_delta import ChatCompletionDelta
from ..common.usage import Usage

class ChatCompletionChunkChoice(BaseModel):
    """
    Chat Completion Chunk Choice 数据模型
    表示 ChatCompletion Chunk 中的单个选择。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    index: int
    delta: ChatCompletionDelta
    finish_reason: Optional[str] = None
    logprobs: Optional[dict] = None

class ChatCompletionChunk(BaseModel):
    """
    Chat Completion Chunk 数据模型
    表示 ChatCompletion API 流式响应的数据块，严格遵循 OpenAI ChatCompletions API 规范。
    与非流式响应模型完全分离。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    id: str
    object: str = "chat.completion.chunk"
    created: int  # Unix timestamp
    model: str
    choices: List[ChatCompletionChunkChoice]
    usage: Optional[Usage] = None  # 仅在最终chunk中提供
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的ChatCompletionChunk结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- object字段默认值正确
- usage字段仅在适当时候提供

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Chat Completion Delta模型文档](task-18-chat-completion-delta.md)
- [Usage模型文档](task-01-common-usage.md)

## 依赖关系
- 依赖: `models/chat/chat_completion_delta.py`
- 依赖: `models/common/usage.py`

## 备注
此模型用于支持ChatCompletion API的流式响应，是实现官方SDK streaming功能的关键。