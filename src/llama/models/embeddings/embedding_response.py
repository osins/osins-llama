# src/llama/models/embeddings/embedding_response.py

from pydantic import ConfigDict, Field
from typing import List, Optional
from ..common.base_model import BaseDataModel


class EmbeddingObject(BaseDataModel):
    """
    Embedding Object 数据模型
    表示单个嵌入向量对象，严格遵循 OpenAI Embeddings API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    object: str = Field(default="embedding", description="Object type")
    embedding: List[float] = Field(..., description="Embedding vector")
    index: int = Field(..., ge=0, description="Index of the embedding")


class EmbeddingUsage(BaseDataModel):
    """
    Embedding Usage 数据模型
    表示嵌入API的使用量统计，严格遵循 OpenAI Embeddings API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt_tokens: int = Field(..., ge=0, le=1000000, description="Number of tokens in the prompt")
    total_tokens: int = Field(..., ge=0, le=1000000, description="Total tokens used")


class EmbeddingResponse(BaseDataModel):
    """
    Embedding Response 数据模型
    表示嵌入API的响应对象，严格遵循 OpenAI Embeddings API 规范。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    object: str = Field(default="list", description="Object type")
    data: List[EmbeddingObject] = Field(..., description="List of embeddings")
    model: str = Field(..., min_length=1, max_length=255, description="Model used")
    usage: EmbeddingUsage = Field(..., description="Usage statistics")
