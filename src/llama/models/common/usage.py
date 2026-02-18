from pydantic import ConfigDict, Field
from typing import Optional
from .base_model import BaseDataModel


class PromptTokensDetails(BaseDataModel):
    """
    Prompt Tokens Details 数据模型
    表示提示令牌的详细信息，严格遵循 OpenAI API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    cached_tokens: Optional[int] = Field(default=None, ge=0, le=100000, description="缓存的令牌数量")
    audio_tokens: Optional[int] = Field(default=None, ge=0, le=100000, description="音频令牌数量")


class CompletionTokensDetails(BaseDataModel):
    """
    Completion Tokens Details 数据模型
    表示完成令牌的详细信息，严格遵循 OpenAI API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    reasoning_tokens: Optional[int] = Field(default=None, ge=0, le=100000, description="推理令牌数量")
    audio_tokens: Optional[int] = Field(default=None, ge=0, le=100000, description="音频令牌数量")


class Usage(BaseDataModel):
    """
    Usage 数据模型
    表示 API 调用的使用量统计信息，严格遵循 OpenAI 官方 API Usage 对象格式。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt_tokens: int = Field(..., ge=0, le=100000, description="提示令牌数量")
    completion_tokens: int = Field(..., ge=0, le=100000, description="完成令牌数量")
    total_tokens: int = Field(..., ge=0, le=200000, description="总令牌数量")
    prompt_tokens_details: Optional[PromptTokensDetails] = Field(
        default=None,
        description="提示令牌详细信息"
    )
    completion_tokens_details: Optional[CompletionTokensDetails] = Field(
        default=None,
        description="完成令牌详细信息"
    )