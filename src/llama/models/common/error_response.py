# src/llama/models/common/error_response.py

from pydantic import ConfigDict, Field
from typing import Optional
from .base_model import BaseDataModel


class ErrorResponse(BaseDataModel):
    """
    Error Response 数据模型
    表示 API 调用的错误响应信息，严格遵循 OpenAI 官方 API Error Response 对象格式。
    HTTP状态码与error.type解耦，允许HTTP 200时返回error。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    message: str = Field(..., min_length=1, max_length=1000)
    type: str = Field(..., min_length=1, max_length=100)
    param: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code: Optional[str] = Field(default=None, min_length=1, max_length=100)