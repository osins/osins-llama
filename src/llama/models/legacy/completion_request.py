# src/llama/models/legacy/completion_request.py

from pydantic import BaseModel, ConfigDict
from .completion_params import CompletionParams
from ..common.base_model import BaseDataModel


class CompletionRequest(CompletionParams):
    """
    Completion Request 数据模型
    表示 Legacy Completion API 的请求对象，严格遵循 OpenAI Completions API 规范。
    继承CompletionParams的所有字段，无额外字段。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen