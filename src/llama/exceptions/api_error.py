"""
自定义异常类定义
遵循高级实现规范中的异常分层要求
"""


class APIError(Exception):
    """基础API异常类"""
    def __init__(self, message: str, status_code: int = 500, error_type: str = "internal_error"):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(self.message)