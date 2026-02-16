"""API Key Middleware for Llama API."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_keys: list):
        super().__init__(app)
        self.api_keys = api_keys
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        # Log incoming request
        self.logger.info(f"ApiKeyMiddleware: Processing request to {request.url.path}")
        
        # Extract API key from header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            self.logger.warning(f"ApiKeyMiddleware: Missing or invalid Authorization header for {request.url.path}")
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        provided_key = auth_header[len("Bearer "):]
        self.logger.info(f"ApiKeyMiddleware: Extracted API key, validating...")

        # Validate API key
        if provided_key not in self.api_keys:
            self.logger.warning(f"ApiKeyMiddleware: Invalid API key for {request.url.path}")
            raise HTTPException(status_code=401, detail="Invalid API key")

        self.logger.info(f"ApiKeyMiddleware: API key validation passed for {request.url.path}")
        
        # Add API key to request state for later use
        request.state.api_key = provided_key

        response = await call_next(request)
        return response