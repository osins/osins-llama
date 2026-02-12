# src/llama/models/legacy/completion_response.py

from pydantic import ConfigDict, Field
from typing import List
from .completion_choice import CompletionChoice
from ..common.usage import Usage
from ..common.base_model import BaseDataModel


class CompletionResponse(BaseDataModel):
    """
    Completion Response 数据模型
    表示 Legacy Completion API 的完整响应对象，严格遵循 OpenAI Completions API 规范。
    与Chat模型完全隔离，不共享任何Response模型。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    id: str = Field(..., min_length=1, max_length=100)
    object: str = "text_completion"
    created: int = Field(..., ge=0, le=2147483647)  # Unix timestamp
    model: str = Field(..., min_length=1, max_length=255)
    choices: List[CompletionChoice] = Field(..., min_length=1, max_length=10)  # 限制choices数量
    usage: Usage