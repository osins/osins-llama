"""Embeddings Routes - OpenAI compatible embedding endpoints."""

from fastapi import APIRouter, Request
from typing import Union

from src.llama.models.embeddings.embedding_request import EmbeddingRequest
from src.llama.models.embeddings.embedding_response import EmbeddingResponse
from src.llama.services.embedding_service import EmbeddingService
from src.llama.exceptions import ServiceError
from src.llama.core.logger_manager import logger


router = APIRouter()


def get_embedding_service(request: Request) -> EmbeddingService:
    """Dependency to get EmbeddingService with the app's config"""
    config = getattr(request.app.state, 'config', None)
    return EmbeddingService.get_instance(config)


@router.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest, req: Request):
    """
    Generate embeddings for the given input(s)
    
    This endpoint creates vector representations of the input text(s).
    The embeddings can be used for semantic search, clustering, and other NLP tasks.
    
    Note: Not all models support embeddings. If the loaded model does not have
    embedding capabilities, this endpoint will return a 501 error.
    """
    service = get_embedding_service(req)
    
    try:
        # Try to create real embeddings
        response = await service.create_embeddings(
            inputs=request.input,
            model=request.model,
            encoding_format=request.encoding_format,
            dimensions=request.dimensions
        )
        return response
        
    except ServiceError as e:
        if e.status_code == 501:
            # Model doesn't support embeddings
            logger.warning(f"Model does not support native embeddings, using fallback: {e.message}")
            
            # Use fallback method (deterministic pseudo-embeddings)
            try:
                response = await service.create_embeddings_fallback(
                    inputs=request.input,
                    model=request.model,
                    encoding_format=request.encoding_format,
                    dimensions=request.dimensions
                )
                return response
            except ServiceError as fallback_error:
                logger.error(f"Fallback embedding generation failed: {fallback_error.message}")
                raise
        else:
            logger.error(f"Embedding generation error: {e.message}")
            raise
    
    except Exception as e:
        logger.error(f"Unexpected error in embedding generation: {e}", exc_info=True)
        raise ServiceError(f"Internal server error: {str(e)}")
