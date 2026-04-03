import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from pydantic import BaseModel


router = APIRouter()


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "llama-api"


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard]


@router.get("/v1/models")
async def list_models():
    """
    List all available models
    """
    from llama.core.model_manager import ModelManager
    
    model_manager = ModelManager.get_instance()
    model_path = model_manager.config.model.path
    
    # Extract model name from path
    import os
    model_filename = os.path.basename(model_path)
    
    models = [
        ModelCard(
            id=model_filename,
            created=0,
            owned_by="llama-api"
        )
    ]
    
    return ModelList(data=models)


@router.get("/v1/models/{model}")
async def retrieve_model(model: str):
    """
    Retrieve a specific model
    """
    from llama.core.model_manager import ModelManager
    from llama.exceptions.service_error import ServiceError
    
    model_manager = ModelManager.get_instance()
    model_path = model_manager.config.model.path
    current_model_name = os.path.basename(model_path)
    
    if model != current_model_name:
        raise ServiceError(
            message=f"The model '{model}' does not exist",
            error_type="invalid_request_error",
            status_code=404
        )
    
    model_card = ModelCard(
        id=model,
        created=0,
        owned_by="llama-api"
    )
    
    return model_card