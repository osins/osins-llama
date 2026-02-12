# src/llama/models/chat/chat_completion_response.py

from pydantic import ConfigDict, Field
from typing import List
from .chat_completion_choice import ChatCompletionChoice
from ..common.usage import Usage
from ..common.base_model import BaseDataModel


class ChatCompletionResponse(BaseDataModel):
    """
    Chat Completion Response 数据模型
    表示 ChatCompletion API 的完整响应对象，包含 choices 和 usage 信息。
    严格遵循 OpenAI ChatCompletions API 规范。
    与流式响应模型分离。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    id: str = Field(..., min_length=1, max_length=100)
    object: str = "chat.completion"
    created: int = Field(..., ge=0, le=2147483647)  # Unix timestamp
    model: str = Field(..., min_length=1, max_length=255)
    choices: List[ChatCompletionChoice] = Field(..., min_length=1, max_length=10)  # 限制choices数量
    usage: Usage