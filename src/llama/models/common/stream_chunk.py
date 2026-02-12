# src/llama/models/common/stream_chunk.py

from pydantic import ConfigDict, Field
from typing import List, Optional, Union, Dict, Any
from .base_model import BaseDataModel


class StreamChunk(BaseDataModel):
    """
    流式数据块模型
    用于表示流式API响应中的单个数据块
    """
    model_config = ConfigDict(extra="forbid", frozen=True)  # 禁止额外字段，启用frozen

    id: str = Field(..., min_length=1, max_length=100)
    object: str = Field(default="text_completion.chunk")
    created: int = Field(..., ge=0, le=2147483647)  # Unix timestamp
    model: str = Field(..., min_length=1, max_length=255)
    choices: List[Dict[str, Any]] = Field(..., min_length=0, max_length=10)  # 限制choices数量
    error: Optional[str] = Field(default=None, max_length=1000)