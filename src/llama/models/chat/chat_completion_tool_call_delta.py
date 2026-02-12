# src/llama/models/chat/chat_completion_tool_call_delta.py

from pydantic import ConfigDict, Field
from typing import Optional
from .chat_completion_tool_call_delta_function import ChatCompletionToolCallDeltaFunction
from ..common.base_model import BaseDataModel


class ChatCompletionToolCallDelta(BaseDataModel):
    """
    Chat Completion Tool Call Delta 数据模型
    表示工具调用的增量部分。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    index: int = Field(..., ge=0, le=100)  # 限制index范围
    id: Optional[str] = Field(default=None, min_length=1, max_length=100)  # 限制ID长度
    function: Optional[ChatCompletionToolCallDeltaFunction] = None