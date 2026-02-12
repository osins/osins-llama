from .api_error import APIError


class ServiceError(APIError):
    """服务内部错误"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, 500)