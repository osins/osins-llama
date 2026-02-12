# Chat Completion Request模型任务文档

## 任务概述
- **任务编号**: 16
- **任务名称**: Chat Completion Request模型
- **文件路径**: `models/chat/chat_completion_request.py`
- **任务状态**: 待开发
- **优先级**: 高

## 任务描述
实现ChatCompletionRequest数据模型，用于表示ChatCompletion API的请求对象。该模型需要严格遵循OpenAI ChatCompletions API规范，支持多message、content parts、tool calls等功能。

## 技术要求
- 使用Pydantic BaseModel作为基类
- 包含以下字段：
  - messages: List[ChatMessage] - 消息列表
  - model: str - 模型名称
  - frequency_penalty: Optional[float] - 频率惩罚
  - logit_bias: Optional[Dict[str, float]] - Logit偏差
  - max_tokens: Optional[int] - 最大令牌数
  - n: Optional[int] - 生成数量
  - presence_penalty: Optional[float] - 存在惩罚
  - seed: Optional[int] - 随机种子
  - stop: Optional[Union[str, List[str]]] - 停止词
  - stream: Optional[bool] - 是否流式
  - temperature: Optional[float] - 温度
  - top_p: Optional[float] - Top-p采样
  - user: Optional[str] - 用户标识
  - tools: Optional[List[Dict[str, Any]]] - 工具列表
  - tool_choice: Optional[Union[str, Dict[str, Any]]] - 工具选择
- 遵循OpenAI API的ChatCompletionRequest对象结构
- 使用Pydantic v2语法

## 实现规范
- messages字段为ChatMessage对象列表
- 支持多message、content parts、tool calls
- 不允许额外字段（extra="forbid"）
- 遵循100% OpenAI兼容策略
- 使用Pydantic v2的model_config语法
- 与Legacy Completion模型完全隔离

## 代码实现
```python
# models/chat/chat_completion_request.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, Union, List, Dict, Any
from .chat_message import ChatMessage

class ChatCompletionRequest(BaseModel):
    """
    Chat Completion Request 数据模型
    表示 ChatCompletion API 的请求对象，支持多 message、content parts、tool calls 等功能。
    严格遵循 OpenAI ChatCompletions API 规范。
    """
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段

    messages: List[ChatMessage]
    model: str
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    user: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
```

## 验证标准
- 模型能够正确序列化和反序列化
- 与OpenAI官方API的ChatCompletionRequest结构完全一致
- 通过单元测试验证字段正确性
- 多余字段会被拒绝
- 支持所有必需的参数

## 相关文档
- [主数据模型设计文档](../../../20260210-api/02-data-models-design/implementation-guide.md)
- [实施指南](../../implementation-guide.md)
- [Chat Message模型文档](task-11-chat-message.md)

## 依赖关系
- 依赖: `models/chat/chat_message.py`

## 备注
此模型为ChatCompletion API的请求模型，支持完整的聊天功能。