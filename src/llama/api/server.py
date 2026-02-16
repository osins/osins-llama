from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import argparse
from typing import Optional
import json
import asyncio

from src.llama.api.completion_routes import router as completion_router
from src.llama.api.chat_routes import router as chat_router
from src.llama.api.models_routes import router as models_router
from src.llama.api.embeddings_routes import router as embeddings_router
from src.llama.api.custom_routes import router as custom_router
from src.llama.core.model_manager import ModelManager
from src.llama.config.config import Config
from src.llama.exceptions.service_error import ServiceError
from src.llama.middlewares.rate_limit_middleware import RateLimitMiddleware
from src.llama.middlewares.api_key_middleware import ApiKeyMiddleware
from src.llama.middlewares.logging_middleware import LoggingMiddleware
from src.llama.core.logger_manager import logger


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

    # Store the config in app state so it can be accessed by services
    app.state.config = config

    # Add logging middleware for debugging
    app.add_middleware(LoggingMiddleware)

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
    app.include_router(completion_router, tags=["completions"])  # Already prefixed with /v1 in routes file
    app.include_router(chat_router, tags=["chat"])  # Already prefixed with /v1 in routes file
    app.include_router(models_router, tags=["models"])  # Already prefixed with /v1 in routes file
    app.include_router(embeddings_router, tags=["embeddings"])  # Already prefixed with /v1 in routes file
    app.include_router(custom_router)  # No prefix for custom endpoints like /props

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

    # Global exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"VALIDATION_ERROR - URL: {request.url} | ClientIP: {request.client.host if request.client else 'unknown'} | Errors: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )

    # Global exception handler for response validation errors
    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
        logger.error(f"RESPONSE_VALIDATION_ERROR - URL: {request.url} | ClientIP: {request.client.host if request.client else 'unknown'} | Errors: {exc.errors()}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Response validation error", "errors": exc.errors()}
        )

    return app


def start_server(config: Config):
    """Start the API server with the given configuration"""
    # Create the app (this will load the model)
    app = create_app(config)

    print(f"Starting server on {config.service.host}:{config.service.port}")
    print(f"Access the API at: http://{config.service.host}:{config.service.port}")
    print(f"API documentation available at: http://{config.service.host}:{config.service.port}/docs")

    # Import and use the new logger manager
    from src.llama.core.logger_manager import logger
    # Set debug mode based on config
    if config.service.debug:
        logger.debug = lambda msg, *args, **kwargs: logger.logger.debug(msg, *args, **kwargs)

    # Start the server
    uvicorn.run(
        app,
        host=config.service.host,
        port=config.service.port,
        log_level="info" if not config.service.debug else "debug",
        reload=False  # Disable reload in production
    )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Start the Llama API server")
    parser.add_argument("--host", type=str, default=None, help="Server host address")
    parser.add_argument("--port", type=int, default=None, help="Server port")
    parser.add_argument("--model-path", type=str, default=None, help="Path to model file")
    parser.add_argument("--n-ctx", type=int, default=None, help="Context length")
    parser.add_argument("--n-threads", type=int, default=None, help="Number of threads")
    parser.add_argument("--api-keys", type=str, default=None, help="API key list (comma separated)")
    parser.add_argument("--max-concurrent-requests", type=int, default=None, help="Max concurrent requests")
    parser.add_argument("--rate-limit-requests", type=int, default=None, help="Rate limit requests per window")
    parser.add_argument("--rate-limit-window", type=int, default=None, help="Rate limit window in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    return parser.parse_args()


def merge_config_with_args(config: Config, args) -> Config:
    """Merge configuration with command line arguments"""
    # Override service config with command line args if provided
    if args.host is not None:
        config.service.host = args.host
    if args.port is not None:
        config.service.port = args.port
    if args.debug:
        config.service.debug = args.debug
        
    # Override model config with command line args if provided
    if args.model_path is not None:
        config.model.path = args.model_path
    if args.n_ctx is not None:
        config.model.n_ctx = args.n_ctx
    if args.n_threads is not None:
        config.model.n_threads = args.n_threads
        
    # Override security config with command line args if provided
    if args.api_keys is not None:
        api_keys_list = [key.strip() for key in args.api_keys.split(",") if key.strip()]
        config.security.api_keys = api_keys_list
    if args.max_concurrent_requests is not None:
        config.security.max_concurrent_requests = args.max_concurrent_requests
    if args.rate_limit_requests is not None:
        config.security.rate_limit_requests = args.rate_limit_requests
    if args.rate_limit_window is not None:
        config.security.rate_limit_window = args.rate_limit_window
        
    return config


if __name__ == "__main__":
    try:
        args = parse_args()
        
        # Load the initial config from environment variables
        # If model path is provided via command line, pass it to from_env to bypass validation temporarily
        model_path = args.model_path if args.model_path else None
        config = Config.from_env(model_path=model_path)
        
        # Override with command line arguments if provided
        config = merge_config_with_args(config, args)
        
        start_server(config)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)