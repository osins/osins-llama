# src/llama/models/embeddings/embedding_request.py

from pydantic import ConfigDict, Field
from typing import Optional, Union, List
from ..common.base_model import BaseDataModel


class EmbeddingRequest(BaseDataModel):
    """
    Embedding Request 数据模型
    表示 Embedding API 的请求对象，严格遵循 OpenAI Embeddings API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    input: Union[str, List[str]] = Field(..., description="Input text to embed")
    model: str = Field(..., min_length=1, max_length=255, description="Model to use for embedding")
    encoding_format: Optional[str] = Field(default="float", description="Format for returned embeddings")
    dimensions: Optional[int] = Field(default=None, ge=1, le=3072, description="Number of dimensions")
    user: Optional[str] = Field(default=None, min_length=1, max_length=255, description="End-user identifier")
