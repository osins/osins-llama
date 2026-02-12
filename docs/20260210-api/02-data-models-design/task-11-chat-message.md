# Chat Message模型任务文档

## 任务概述
- **任务编号**: 11
- **任务名称**: Chat Message模型
- **文件路径**: `models/chat/chat_message.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatMessage数据模型，用于表示Chat API中的单条消息。该模型需要严格遵循OpenAI Chat API规范，包含role和content（结构化parts）字段。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - role: ChatRole - 消息角色
  - content: Union[str, List[ChatContentPart]] - 消息内容（支持结构化parts）
  - name: Optional[str] - 发送者名称（可选）
  - tool_calls: Optional[List['ToolCall']] - 工具调用列表（可选）
  - tool_call_id: Optional[str] - 工具调用ID（可选）
- 遵循OpenAI API的ChatMessage对象结构
- 使用Pydantic v2语法

## 实现规范
- role字段使用ChatRole枚举
- content字段支持字符串或ChatContentPart列表（结构化parts）
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Legacy Completion模型完全隔离
- 处理循环引用（ToolCall）

## 代码实现
```python
# models/chat/chat_message.py

from pydantic import BaseModel, ConfigDict
from typing import Union, List, Optional
from .chat_role import ChatRole
from .chat_content_part import ChatContentPart
from .tool_call import ToolCall

class ChatMessage(BaseModel):
    """
    Chat Message 数据模型
    表示 Chat API 中的单条消息，包含 role 和 content（结构化 parts）。
    严格遵循 OpenAI Chat API 规范。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    role: ChatRole
    content: Union[str, List[ChatContentPart]]
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

# 解决循环引用
ChatMessage.model_rebuild()
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的ChatMessage结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- 正确处理循环引用

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Chat Role模型文档](task-09-chat-role.md)
- [Chat Content Part模型文档](task-10-chat-content-part.md)
- [Tool Call模型文档](task-12-chat-tool-call.md)

## 依赖关系
- 依赖: `models/chat/chat_role.py`
- 依赖: `models/chat/chat_content_part.py`
- 依赖: `models/chat/tool_call.py`

## 备注
此模型是Chat API的核心组成部分，必须严格按照OpenAI官方schema实现，不得进行任何优化。