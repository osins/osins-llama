"""Process management for osins-llama server."""
import subprocess
import signal
import os
from pathlib import Path
from typing import Optional
import time
import sys
from .exceptions import ProcessAlreadyRunning
from .pid_file_manager import PidFileManager  # 修改导入路径
from ..models.pid_data import PidData


class ProcessManager:
    """管理osins-llama服务器进程的启动、停止等操作"""

    def __init__(self, expected_cmd_keyword: str, stop_timeout: int = 30):
        self.expected_cmd_keyword = expected_cmd_keyword
        self.stop_timeout = stop_timeout
        # 创建 PidFileManager 实例，它会从环境变量获取 PID 文件路径
        self.pid_manager = PidFileManager()

    def start(self):
        """启动服务器进程"""
        # 检查是否已有进程在运行
        if self.is_running():
            raise ProcessAlreadyRunning(f"Server is already running (PID: {self.get_pid()})")

        # 从pid_manager获取命令
        cmd = self.pid_manager.get_cmd()
        
        if cmd:
            # 启动新进程
            process = subprocess.Popen(cmd)

            # 使用PID管理器的set_pid方法更新PID
            self.pid_manager.set_pid(process.pid)
        else:
            # 如果没有保存的数据，无法启动
            raise Exception("No saved data found in PID file, unable to start")

    def stop(self):
        """停止服务器进程"""
        # 通过pid_manager获取PID
        pid_data = self.pid_manager.read()
        if not pid_data or not pid_data.pid:
            return False

        pid = pid_data.pid
        try:
            # 尝试向进程发送信号终止它
            os.kill(pid, signal.SIGTERM)

            # 等待进程结束
            time.sleep(1)  # 等待进程结束

            # 删除PID文件
            self.pid_manager.delete()

            return True
        except OSError:
            # 进程已经不存在或无权访问
            self.pid_manager.delete()
            return False

    def restart(self):
        """重启服务器进程"""
        # 获取保存的启动参数
        saved_data = self.pid_manager.read()
        if not saved_data:
            raise Exception("No saved data found in PID file, unable to restart")

        self.stop()
        time.sleep(1)  # 等待进程完全停止

        self.start()  # 调用修改后的 start 方法

    def status(self):
        """检查服务器进程状态"""
        pid_data = self.pid_manager.read()
        if not pid_data or not pid_data.pid:
            return {"running": False, "pid": None}

        pid = pid_data.pid
        try:
            if sys.platform == 'win32':
                # Windows-specific process check using tasklist
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
                    capture_output=True,
                    text=True
                )
                process_exists = f'"{pid}"' in result.stdout
            else:
                # Unix-specific process check
                os.kill(pid, 0)
                process_exists = True

            if process_exists:
                return {"running": True, "pid": pid}
            else:
                # 进程不存在，清理PID文件
                self.pid_manager.delete()
                return {"running": False, "pid": None}
        except (OSError, subprocess.SubprocessError):
            # 进程不存在或检查失败，清理PID文件
            self.pid_manager.delete()
            return {"running": False, "pid": None}

    def is_running(self):
        """检查服务器是否正在运行"""
        status = self.status()
        return status["running"]

    def get_pid(self):
        """从PID文件获取进程ID，支持新旧格式"""
        return self.pid_manager.get_pid()
