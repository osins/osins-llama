from .api_error import APIError


class AuthenticationError(APIError):
    """认证错误"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)