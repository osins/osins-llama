from .api_error import APIError


class RateLimitError(APIError):
    """请求频率限制错误"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, 429)