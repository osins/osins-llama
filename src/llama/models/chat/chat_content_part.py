# src/llama/models/chat/chat_content_part.py

from pydantic import ConfigDict, Field
from typing import Literal, Union, Optional
from .content_type import ContentType
from .image_url import ImageUrl
from ..common.base_model import BaseDataModel


class ChatContentPart(BaseDataModel):
    """
    Chat Content Part 数据模型
    表示 Chat API 中消息内容的部件，支持文本、图像等多种内容类型。
    不能简单使用 str 类型，必须是结构化 content parts。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    type: ContentType
    text: Optional[str] = Field(default=None, min_length=1, max_length=10000)  # 限制文本长度
    image_url: Optional[ImageUrl] = None