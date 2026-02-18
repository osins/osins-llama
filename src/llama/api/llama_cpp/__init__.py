from src.llama.api.llama_cpp.custom_routes import router as custom_router
from src.llama.api.llama_cpp.llama_completion_routes import router as llama_completion_router

__all__ = [
    "custom_router",
    "llama_completion_router",
]
