# src/llama/models/chat/image_url.py

from pydantic import ConfigDict, Field
from typing import Optional
from .image_detail import ImageDetail
from ..common.base_model import BaseDataModel


class ImageUrl(BaseDataModel):
    """
    图像URL模型
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    url: str = Field(..., min_length=1, max_length=2048)  # 限制URL长度
    detail: Optional[ImageDetail] = ImageDetail.AUTO