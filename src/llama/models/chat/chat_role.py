# src/llama/models/chat/chat_role.py

from enum import Enum


class ChatRole(str, Enum):
    """
    Chat Role 枚举
    表示 Chat API 中的角色类型，严格遵循 OpenAI Chat API 规范。
    必须包含 'user', 'assistant', 'system', 'tool' 角色以支持 function/tool calling。
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"