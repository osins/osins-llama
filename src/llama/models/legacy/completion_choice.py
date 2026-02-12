# src/llama/models/legacy/completion_choice.py

from pydantic import ConfigDict, Field
from typing import Optional, Dict, Any
from .completion_finish_reason import CompletionFinishReason
from ..common.base_model import BaseDataModel


class CompletionChoice(BaseDataModel):
    """
    Completion Choice 数据模型
    表示 Legacy Completion API 的生成选择结果，严格遵循 OpenAI Completions API 规范。
    仅包含text输出，与Chat模型完全隔离。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    text: str = Field(..., max_length=10000)  # 限制文本长度
    index: int = Field(..., ge=0, le=100)  # 限制index范围
    logprobs: Optional[Dict[str, Any]] = Field(default=None, max_length=10000)
    finish_reason: CompletionFinishReason