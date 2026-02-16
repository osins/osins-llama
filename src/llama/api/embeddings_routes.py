import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Union, Optional
import logging


logger = logging.getLogger(__name__)

router = APIRouter()


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str
    encoding_format: Optional[str] = "float"  # "float" or "base64"
    user: Optional[str] = None  # Optional field for specifying the end-user


class Embedding(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[Embedding]
    model: str
    usage: EmbeddingUsage


@router.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for the given input(s)
    """
    from src.llama.core.model_manager import ModelManager
    from src.llama.exceptions.service_error import ServiceError

    # Note: Actual LLM libraries like llama.cpp don't typically support embeddings
    # This is a mock implementation that returns random vectors of appropriate dimensions
    # In a real implementation, you'd need to use a model that supports embeddings
    
    # Get the model info to determine embedding dimensions
    model_manager = ModelManager.get_instance()
    model_path = model_manager.config.model.path
    model_name = model_path.split('/')[-1] if '/' in model_path else model_path.split('\\')[-1]
    
    # For now, return a mock embedding of dimension 384
    embedding_dimension = 384
    
    inputs = request.input if isinstance(request.input, list) else [request.input]
    embeddings_data = []
    
    for idx, inp in enumerate(inputs):
        # Generate a mock embedding - in reality, this would come from the model
        mock_embedding = np.random.normal(size=(embedding_dimension,)).tolist()
        
        embeddings_data.append(Embedding(
            embedding=mock_embedding,
            index=idx
        ))
    
    # Calculate token usage (mock values)
    total_tokens = sum(len(inp.split()) for inp in inputs)
    
    response = EmbeddingResponse(
        data=embeddings_data,
        model=model_name,
        usage=EmbeddingUsage(
            prompt_tokens=total_tokens,
            total_tokens=total_tokens
        )
    )
    
    return response