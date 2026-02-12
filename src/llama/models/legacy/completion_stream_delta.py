# src/llama/models/legacy/completion_stream_delta.py

from pydantic import ConfigDict, Field
from typing import Optional
from .completion_finish_reason import CompletionFinishReason
from ..common.base_model import BaseDataModel


class CompletionStreamDelta(BaseDataModel):
    """
    Completion Stream Delta 数据模型
    表示 Legacy Completion API 流式响应的增量数据，严格遵循 OpenAI Completions API 规范。
    与非流式响应模型完全分离，仅用于流式响应。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    text: str = Field(default="", max_length=10000)  # 限制文本长度
    index: int = Field(..., ge=0, le=100)  # 限制index范围
    finish_reason: Optional[CompletionFinishReason] = None