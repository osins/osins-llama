# src/llama/models/chat/chat_completion_chunk_choice.py

from pydantic import ConfigDict, Field
from typing import Optional, Dict, Any
from .chat_completion_delta import ChatCompletionDelta
from ..common.base_model import BaseDataModel


class ChatCompletionChunkChoice(BaseDataModel):
    """
    Chat Completion Chunk Choice 数据模型
    表示 ChatCompletion Chunk 中的单个选择。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    index: int = Field(..., ge=0, le=100)  # 限制index范围
    delta: ChatCompletionDelta
    finish_reason: Optional[str] = Field(default=None, max_length=100)  # 限制finish_reason长度
    logprobs: Optional[Dict[str, Any]] = Field(default=None, max_length=10000)  # 限制logprobs长度