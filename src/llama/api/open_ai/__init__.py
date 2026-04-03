from llama.api.open_ai.chat_routes import router as chat_router
from llama.api.open_ai.completion_routes import router as completion_router
from llama.api.open_ai.embeddings_routes import router as embeddings_router
from llama.api.open_ai.models_routes import router as models_router

__all__ = [
    "chat_router",
    "completion_router",
    "embeddings_router",
    "models_router",
]
