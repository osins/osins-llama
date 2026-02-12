from pydantic import ConfigDict, Field
from .base_model import BaseDataModel


class Usage(BaseDataModel):
    """
    Usage 数据模型
    表示 API 调用的使用量统计信息，严格遵循 OpenAI 官方 API Usage 对象格式。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt_tokens: int = Field(..., ge=0, le=100000, description="提示令牌数量")
    completion_tokens: int = Field(..., ge=0, le=100000, description="完成令牌数量")
    total_tokens: int = Field(..., ge=0, le=200000, description="总令牌数量")