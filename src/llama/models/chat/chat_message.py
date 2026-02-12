from pydantic import ConfigDict, Field
from typing import Union, List, Optional
from .chat_role import ChatRole
from .chat_content_part import ChatContentPart
from .tool_call import ToolCall
from ..common.base_model import BaseDataModel


class ChatMessage(BaseDataModel):
    """
    Chat Message 数据模型
    表示 Chat API 中的单条消息，包含 role 和 content（结构化 parts）。
    严格遵循 OpenAI Chat API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: ChatRole
    content: Union[str, List[ChatContentPart]] = Field(..., max_length=100000)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    tool_calls: Optional[List[ToolCall]] = Field(default=None, max_length=10)
    tool_call_id: Optional[str] = Field(default=None, min_length=1, max_length=255)


ChatMessage.model_rebuild()