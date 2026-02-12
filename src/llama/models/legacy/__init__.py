# src/llama/models/legacy/__init__.py

"""
Legacy Completion模型
包含旧版Completion API的模型
"""

from .completion_params import CompletionParams
from .completion_request import CompletionRequest
from .completion_response import CompletionResponse
from .completion_choice import CompletionChoice
from .completion_finish_reason import CompletionFinishReason

__all__ = [
    "CompletionParams",
    "CompletionRequest",
    "CompletionResponse",
    "CompletionChoice",
    "CompletionFinishReason",
]