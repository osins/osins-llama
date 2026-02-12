# src/llama/models/chat/image_detail.py

from enum import Enum


class ImageDetail(str, Enum):
    """
    图像细节枚举
    """
    AUTO = "auto"
    LOW = "low"
    HIGH = "high"