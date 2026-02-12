# src/llama/models/chat/chat_completion_tool_call_delta_function.py

from pydantic import ConfigDict, Field
from typing import Optional
from ..common.base_model import BaseDataModel


class ChatCompletionToolCallDeltaFunction(BaseDataModel):
    """
    Chat Completion Tool Call Delta Function 数据模型
    表示工具调用增量中的函数部分。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)  # 限制名称长度
    arguments: Optional[str] = Field(default=None, max_length=10000)  # 限制参数长度