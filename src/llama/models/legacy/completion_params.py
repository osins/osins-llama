# src/llama/models/legacy/completion_params.py

from pydantic import ConfigDict, Field
from typing import Optional, Union, List, Dict, Any
from typing import Literal
from ..common.base_model import BaseDataModel


class CompletionParams(BaseDataModel):
    """
    Completion Params 数据模型
    表示 Legacy Completion API 的通用生成参数，严格遵循 OpenAI Completions API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    model: str = Field(..., min_length=1, max_length=255)
    prompt: Union[str, List[str]] = Field(..., max_length=100000)
    max_tokens: Optional[int] = Field(default=16, ge=1, le=4096)  # 限制最大token数
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1, le=10)  # 限制生成数量
    stream: Optional[bool] = False
    logprobs: Optional[int] = Field(default=None, ge=0, le=5)
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = Field(default=None, max_length=10)  # 限制stop词数量
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    best_of: Optional[int] = Field(default=1, ge=1, le=10)  # 限制best_of数量
    logit_bias: Optional[Dict[str, Any]] = Field(default=None, max_length=1000)
    user: Optional[str] = Field(default=None, min_length=1, max_length=255)