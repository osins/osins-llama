# src/llama/models/chat/chat_completion_delta.py

from pydantic import ConfigDict, Field
from typing import Optional, List
from .chat_role import ChatRole
from .chat_completion_tool_call_delta import ChatCompletionToolCallDelta
from ..common.base_model import BaseDataModel


class ChatCompletionDelta(BaseDataModel):
    """
    Chat Completion Delta 数据模型
    表示 ChatCompletion API 流式响应的增量数据，严格遵循 OpenAI ChatCompletions API 规范。
    与非流式响应模型完全分离，仅用于流式响应。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    role: Optional[ChatRole] = None
    content: Optional[str] = Field(default=None, max_length=10000)  # 限制内容长度
    tool_calls: Optional[List[ChatCompletionToolCallDelta]] = Field(default=None, max_length=10)  # 限制工具调用数量