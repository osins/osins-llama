"""Rate Limit Middleware for Llama API."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from collections import defaultdict, deque


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit_requests: int, rate_limit_window: int):
        super().__init__(app)
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        # Dictionary to store request timestamps for each IP
        self.requests = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        
        # Get current time
        now = time.time()
        
        # Clean old requests outside the window
        while (self.requests[client_ip] and 
               self.requests[client_ip][0] <= now - self.rate_limit_window):
            self.requests[client_ip].popleft()
        
        # Check if request count exceeds the limit
        if len(self.requests[client_ip]) >= self.rate_limit_requests:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Maximum {self.rate_limit_requests} requests per {self.rate_limit_window} seconds."
            )
        
        # Add current request timestamp
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response