# src/llama/models/chat/chat_completion_choice.py

from pydantic import ConfigDict, Field
from typing import Optional, Dict, Any
from .chat_message import ChatMessage
from .chat_finish_reason import ChatFinishReason
from ..common.base_model import BaseDataModel


class ChatCompletionChoice(BaseDataModel):
    """
    Chat Completion Choice 数据模型
    表示 ChatCompletion API 的生成选择结果，包含 message 和 finish_reason。
    严格遵循 OpenAI ChatCompletions API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    index: int = Field(..., ge=0, le=100)  # 限制index范围
    message: ChatMessage
    finish_reason: ChatFinishReason
    logprobs: Optional[Dict[str, Any]] = Field(default=None, max_length=10000)