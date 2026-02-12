# src/llama/models/common/error_model.py

from pydantic import ConfigDict
from .error_response import ErrorResponse
from .base_model import BaseDataModel


class ErrorModel(BaseDataModel):
    """
    Error包装模型
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    error: ErrorResponse