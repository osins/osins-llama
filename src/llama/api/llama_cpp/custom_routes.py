from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from typing import Optional
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.services.completion_service import CompletionService
from src.llama.core.security import verify_api_key
from src.llama.exceptions import ValidationError, RateLimitError, ServiceError, AuthenticationError
from fastapi import HTTPException


router = APIRouter()


class PropsResponse(BaseModel):
    model: str
    context_length: int
    embedding_dimension: Optional[int] = 384  # Default value


@router.get("/props")
async def get_props(model: str = None):
    """
    Get model properties - a custom endpoint that might be expected by certain clients
    """
    from src.llama.core.model_manager import ModelManager

    model_manager = ModelManager.get_instance()
    model_path = model_manager.config.model.path
    model_name = model_path.split('/')[-1] if '/' in model_path else model_path.split('\\')[-1]

    # Use provided model name or default to loaded model
    response_model = model if model else model_name

    props = PropsResponse(
        model=response_model,
        context_length=model_manager.config.model.n_ctx or 2048,
        embedding_dimension=384
    )

    return props


