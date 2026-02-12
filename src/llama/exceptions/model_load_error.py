from .api_error import APIError


class ModelLoadError(APIError):
    """模型加载错误"""
    def __init__(self, message: str = "Failed to load model"):
        super().__init__(message, 503)