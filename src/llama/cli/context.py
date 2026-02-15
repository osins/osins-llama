"""CLI Context for osins-llama."""
import threading
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import json
import yaml
from ..utils.logging_utils import setup_logging
from ..utils.cli_tools import mask_sensitive


class ErrorSeverity(Enum):
    """错误严重性等级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class CLIContext:
    """CLI上下文对象，封装命令行参数和共享资源"""

    def __init__(self, verbose: bool = False, config_path: Optional[Path] = None):
        self.verbose = verbose
        self.config_path = config_path
        self.config_data = self._load_config_data()  # 解析配置文件
        self.cache = {}  # 临时缓存
        self.command_status = {}  # 命令执行状态
        self.status_lock = threading.RLock()  # 线程安全锁
        self.logger = self._init_logger()

        if verbose:
            self.logger.debug("CLIContext initialized with verbose mode")
            self.logger.debug(f"Configuration file path: {mask_sensitive(str(config_path)) if config_path else 'None'}")

    def _init_logger(self) -> logging.Logger:
        return setup_logging(self.verbose)

    def _load_config_data(self):
        """加载并解析配置文件数据"""
        if self.config_path and self.config_path.exists():
            if self.config_path.suffix.lower() == '.json':
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            elif self.config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
        return {}

    def update_command_status(self, command_name: str, status: str, message: str = "") -> None:
        """
        更新命令执行状态
        
        :param command_name: 命令名称
        :param status: 状态（如 'running', 'success', 'failed' 等）
        :param message: 状态消息
        """
        with self.status_lock:
            self.command_status[command_name] = {
                "status": status,
                "message": message,
                "timestamp": self._get_current_timestamp()
            }

    def get_command_status(self, command_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定命令的执行状态
        
        :param command_name: 命令名称
        :return: 命令状态信息，如果不存在则返回 None
        """
        with self.status_lock:
            return self.command_status.get(command_name)

    def rollback_failed_command(self, command_name: str) -> None:
        """
        在命令执行失败时回滚状态
        
        :param command_name: 命令名称
        """
        with self.status_lock:
            if command_name in self.command_status:
                # 记录回滚操作
                self.logger.warning(f"Rolling back command status for {command_name}")
                del self.command_status[command_name]

    def _get_current_timestamp(self) -> str:
        """
        获取当前时间戳
        
        :return: 格式化的当前时间戳字符串
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_error_and_exit(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, exit_code: int = 1) -> None:
        """
        记录错误并退出程序
        
        :param message: 错误消息
        :param severity: 错误严重性等级
        :param exit_code: 退出码
        """
        # 根据严重性记录不同级别的日志
        if severity == ErrorSeverity.LOW:
            self.logger.info(f"[LOW SEVERITY ERROR] {message}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"[MEDIUM SEVERITY ERROR] {message}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"[HIGH SEVERITY ERROR] {message}")
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"[CRITICAL SEVERITY ERROR] {message}")
        
        # 退出程序
        import sys
        sys.exit(exit_code)

    def show_progress(self, message: str, progress: float) -> None:
        """
        显示操作进度
        
        :param message: 进度消息
        :param progress: 进度百分比 (0-100)
        """
        bar_length = 40
        filled_length = int(bar_length * progress // 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f"\r{message} |{bar}| {progress:.1f}% ", end='', flush=True)
        
        if progress == 100:
            print()  # 完成后换行

    def confirm_action(self, message: str) -> bool:
        """
        请求用户确认操作
        
        :param message: 确认消息
        :return: 用户确认结果 (True/False)
        """
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ('y', 'yes')

    def collect_diagnostic_info(self) -> Dict[str, Any]:
        """
        收集诊断信息
        
        :return: 包含诊断信息的字典
        """
        import platform
        import psutil
        import os
        
        diagnostic_info = {
            "timestamp": self._get_current_timestamp(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            "cli_context_state": {
                "verbose": self.verbose,
                "config_path": str(self.config_path) if self.config_path else None,
                "command_count": len(self.command_status),
                "cache_size": len(self.cache)
            }
        }
        
        return diagnostic_info