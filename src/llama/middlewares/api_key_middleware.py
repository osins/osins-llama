"""API Key Middleware for Llama API."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from src.llama.core.logger_manager import logger


PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_keys: list):
        super().__init__(app)
        self.api_keys = api_keys
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        self.logger.info(f"ApiKeyMiddleware: Processing request to {request.url.path}")

        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            self.logger.warning(f"ApiKeyMiddleware: Missing or invalid Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        provided_key = auth_header[len("Bearer "):]
        self.logger.info(f"ApiKeyMiddleware: Extracted API key, validating...")

        if provided_key not in self.api_keys:
            self.logger.warning(f"ApiKeyMiddleware: Invalid API key for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )

        self.logger.info(f"ApiKeyMiddleware: API key validation passed for {request.url.path}")

        request.state.api_key = provided_key

        response = await call_next(request)
        return response