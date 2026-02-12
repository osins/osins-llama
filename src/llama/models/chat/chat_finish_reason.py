# src/llama/models/chat/chat_finish_reason.py

from enum import Enum


class ChatFinishReason(str, Enum):
    """
    Chat Finish Reason 枚举
    表示 ChatCompletion API 的完成原因，严格遵循 OpenAI ChatCompletions API 规范。
    包含Chat API专用的值，与CompletionFinishReason枚举完全分离。
    """
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"