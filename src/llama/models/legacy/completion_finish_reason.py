# src/llama/models/legacy/completion_finish_reason.py

from enum import Enum


class CompletionFinishReason(str, Enum):
    """
    Completion Finish Reason 枚举
    表示 Legacy Completion API 的完成原因，严格遵循 OpenAI Completions API 规范。
    仅包含Completion API允许的值，与ChatFinishReason枚举完全分离。
    """
    STOP = "stop"
    LENGTH = "length"
    CONTENT_FILTER = "content_filter"