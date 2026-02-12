# src/llama/models/chat/tool_call_function.py

from pydantic import ConfigDict, Field
from typing import Optional
from ..common.base_model import BaseDataModel


class FunctionCall(BaseDataModel):
    """
    Function Call 数据模型
    表示 Chat API 中工具调用的函数部分，包含函数名称和参数。
    严格遵循 OpenAI Chat API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    name: str = Field(..., min_length=1, max_length=100)
    arguments: str = Field(..., min_length=0, max_length=10000)  # JSON字符串格式，限制长度