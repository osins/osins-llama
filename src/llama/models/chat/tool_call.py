# src/llama/models/chat/tool_call.py

from pydantic import ConfigDict, Field
from typing import Optional
from .tool_call_function import FunctionCall
from ..common.base_model import BaseDataModel


class ToolCall(BaseDataModel):
    """
    Tool Call 数据模型
    表示 Chat API 中的工具调用，支持函数调用等功能。
    严格遵循 OpenAI Chat API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    id: str = Field(..., min_length=1, max_length=100)
    type: str = Field(default="function", min_length=1, max_length=50)
    function: FunctionCall