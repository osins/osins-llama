# src/llama/models/chat/chat_completion_request.py

from pydantic import ConfigDict, Field, field_validator
from typing import Optional, Union, List, Dict, Any
from .chat_message import ChatMessage
from ..common.base_model import BaseDataModel


class ChatCompletionRequest(BaseDataModel):
    """
    Chat Completion Request 数据模型
    表示 ChatCompletion API 的请求对象，支持多 message、content parts、tool calls 等功能。
    严格遵循 OpenAI ChatCompletions API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    messages: List[ChatMessage] = Field(..., min_length=1, max_length=100)  # 限制消息数量以防止深层嵌套
    model: str = Field(..., min_length=1, max_length=255)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Union[Dict[str, float], List[Any]]] = Field(default=None, description="logit偏差")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)  # 限制最大token数
    n: Optional[int] = Field(default=1, ge=1, le=10)  # 限制生成数量
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    seed: Optional[int] = Field(default=None, ge=0, le=2147483647)
    stop: Optional[Union[str, List[str]]] = Field(default=None, max_length=10)  # 限制stop词数量
    stream: Optional[bool] = False
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    user: Optional[str] = Field(default=None, min_length=1, max_length=255)
    @field_validator('logit_bias', mode='before')
    @classmethod
    def validate_logit_bias(cls, v):
        if v is None:
            return v
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            # 如果是空列表，转换为空字典
            if len(v) == 0:
                return {}
            # 如果是非空列表，转换为空字典
            return {}
        return v

    tools: Optional[List[Dict[str, Any]]] = Field(default=None, max_length=10)  # 限制工具数量
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(default=None, max_length=255)