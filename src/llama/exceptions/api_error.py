"""
自定义异常类定义
遵循高级实现规范中的异常分层要求
"""


class APIError(Exception):
    """基础API异常类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)