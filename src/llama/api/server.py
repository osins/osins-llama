from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import sys

from src.llama.api.completion_routes import router as completion_router
from src.llama.api.chat_routes import router as chat_router
from src.llama.core.model_manager import ModelManager
from src.llama.config.config import Config
from src.llama.exceptions.service_error import ServiceError
from src.llama.middlewares.rate_limit_middleware import RateLimitMiddleware
from src.llama.middlewares.api_key_middleware import ApiKeyMiddleware


def create_app(config: Config):
    """Create the FastAPI app and initialize the model manager"""

    # Initialize the model manager (this will load the model)
    ModelManager.get_instance(config)

    app = FastAPI(
        title="Llama API",
        description="OpenAI-compatible API for Llama models",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add security middlewares
    if config.security.api_keys:
        app.add_middleware(ApiKeyMiddleware, api_keys=config.security.api_keys)
    
    app.add_middleware(RateLimitMiddleware, 
                      rate_limit_requests=config.security.rate_limit_requests,
                      rate_limit_window=config.security.rate_limit_window)

    # Include routers
    app.include_router(completion_router, prefix="/v1", tags=["completions"])
    app.include_router(chat_router, prefix="/v1", tags=["chat"])

    @app.get("/", include_in_schema=False)
    def read_root():
        return {"message": "Welcome to the Llama API", "status": "ready"}

    @app.get("/health", include_in_schema=False)
    def health_check():
        model_manager = ModelManager.get_instance()
        model = model_manager.get_model()
        return {"status": "healthy", "model_loaded": model is not None}

    # Global exception handler for ServiceError
    @app.exception_handler(ServiceError)
    async def handle_service_error(request, exc: ServiceError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.error_type,
                    "message": exc.message
                }
            }
        )

    return app


def start_server(config: Config):
    """Start the API server with the given configuration"""
    # Create the app (this will load the model)
    app = create_app(config)

    print(f"Starting server on {config.service.host}:{config.service.port}")
    print(f"Access the API at: http://{config.service.host}:{config.service.port}")
    print(f"API documentation available at: http://{config.service.host}:{config.service.port}/docs")

    # Configure logging
    logging.basicConfig(level=logging.INFO if not config.service.debug else logging.DEBUG)

    # Start the server
    uvicorn.run(
        app,
        host=config.service.host,
        port=config.service.port,
        log_level="info" if not config.service.debug else "debug",
        reload=False  # Disable reload in production
    )


if __name__ == "__main__":
    try:
        config = Config.from_env()
        start_server(config)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)