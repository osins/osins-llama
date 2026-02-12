from .api_error import APIError


class ValidationError(APIError):
    """请求参数验证错误"""
    def __init__(self, message: str = "Invalid request parameters"):
        super().__init__(message, 400)