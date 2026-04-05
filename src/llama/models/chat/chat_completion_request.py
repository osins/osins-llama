# src/llama/models/chat/chat_completion_request.py

from pydantic import ConfigDict, Field, field_validator
from typing import Optional, Union, List, Dict, Any
from .chat_message import ChatMessage
from .stream_options import StreamOptions
from ..common.base_model import BaseDataModel


class ChatCompletionRequest(BaseDataModel):
    """
    Chat Completion Request 数据模型
    表示 ChatCompletion API 的请求对象，支持多 message、content parts、tool calls 等功能。
    严格遵循 OpenAI ChatCompletions API 规范。
    """
    model_config = ConfigDict(extra="allow", frozen=True)

    messages: List[ChatMessage] = Field(..., min_length=1)
    model: str = Field(..., min_length=1, max_length=255)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Union[Dict[str, float], List[Any]]] = Field(default=None, description="logit偏差")
    max_tokens: Optional[int] = Field(default=None, ge=1)
    max_completion_tokens: Optional[int] = Field(default=None, ge=1)
    n: Optional[int] = Field(default=1, ge=1, le=10)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    seed: Optional[int] = Field(default=None, ge=0, le=2147483647)
    stop: Optional[Union[str, List[str]]] = Field(default=None, max_length=4)
    stream: Optional[bool] = False
    stream_options: Optional[StreamOptions] = Field(default=None)
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.95, ge=0.0, le=1.0)
    top_logprobs: Optional[int] = Field(default=None, ge=0, le=20)
    logprobs: Optional[bool] = Field(default=None)
    user: Optional[str] = Field(default=None, min_length=1, max_length=255)
    store: Optional[bool] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    modalities: Optional[List[str]] = Field(default=None)
    audio: Optional[Dict[str, Any]] = Field(default=None)
    prediction: Optional[Dict[str, Any]] = Field(default=None)
    reasoning_effort: Optional[str] = Field(default=None)
    service_tier: Optional[str] = Field(default=None)
    parallel_tool_calls: Optional[bool] = Field(default=None)
    response_format: Optional[Dict[str, Any]] = Field(default=None)
    
    # 扩展字段：支持 OpenAI 标准 API 之外的参数（如 top_k, min_p 等）
    # 这些参数会被传递到底层 llama.cpp server
    extra_body: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Extra parameters for llama.cpp server (e.g., top_k, min_p)"
    )

    @field_validator('logit_bias', mode='before')
    @classmethod
    def validate_logit_bias(cls, v):
        if v is None:
            return v
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            if len(v) == 0:
                return {}
            return {}
        return v
    
    @field_validator('stream_options', mode='before')
    @classmethod
    def validate_stream_options(cls, v):
        if v is None:
            return None
        if isinstance(v, StreamOptions):
            return v
        if isinstance(v, dict):
            return StreamOptions(**v)
        return v

    tools: Optional[List[Dict[str, Any]]] = Field(default=None)
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(default=None)
