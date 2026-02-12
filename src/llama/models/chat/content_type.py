# src/llama/models/chat/content_type.py

from enum import Enum


class ContentType(str, Enum):
    """
    内容类型枚举
    """
    TEXT = "text"
    IMAGE_URL = "image_url"