"""API Key Middleware for Llama API."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_keys: list):
        super().__init__(app)
        self.api_keys = api_keys

    async def dispatch(self, request: Request, call_next):
        # Extract API key from header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        
        provided_key = auth_header[len("Bearer "):]
        
        # Validate API key
        if provided_key not in self.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Add API key to request state for later use
        request.state.api_key = provided_key
        
        response = await call_next(request)
        return response