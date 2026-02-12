# src/llama/models/chat\chat_completion_chunk.py

from pydantic import ConfigDict, Field
from typing import List, Optional
from .chat_completion_chunk_choice import ChatCompletionChunkChoice
from ..common.usage import Usage
from ..common.base_model import BaseDataModel


class ChatCompletionChunk(BaseDataModel):
    """
    Chat Completion Chunk 数据模型
    表示 ChatCompletion API 流式响应的数据块，严格遵循 OpenAI ChatCompletions API 规范。
    与非流式响应模型完全分离。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    id: str = Field(..., min_length=1, max_length=100)
    object: str = "chat.completion.chunk"
    created: int = Field(..., ge=0, le=2147483647)  # Unix timestamp
    model: str = Field(..., min_length=1, max_length=255)
    choices: List[ChatCompletionChunkChoice] = Field(..., min_length=1, max_length=10)  # 限制choices数量
    usage: Optional[Usage] = None  # 仅在最终chunk中提供