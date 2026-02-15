"""Custom exceptions for osins-llama CLI."""


class ProcessAlreadyRunning(Exception):
    """当尝试启动已在运行的进程时引发的异常"""
    pass


class ProcessNotRunning(Exception):
    """当尝试停止未运行的进程时引发的异常"""
    pass


class PIDSecurityError(Exception):
    """当PID文件存在安全问题时引发的异常"""
    pass


class ProcessTimeout(Exception):
    """当进程操作超时时引发的异常"""
    pass


class ProcessError(Exception):
    """当进程操作发生一般错误时引发的异常"""
    pass