"""Process management for osins-llama server."""
import subprocess
import signal
import os
from pathlib import Path
from typing import List, Optional
import time
import sys
from .exceptions import ProcessAlreadyRunning


class ProcessManager:
    """管理osins-llama服务器进程的启动、停止等操作"""

    def __init__(self, pid_file: Path, expected_cmd_keyword: str, stop_timeout: int = 30):
        self.pid_file = pid_file
        self.expected_cmd_keyword = expected_cmd_keyword
        self.stop_timeout = stop_timeout

    def start(self, cmd: List[str]):
        """启动服务器进程"""
        # 检查是否已有进程在运行
        if self.is_running():
            raise ProcessAlreadyRunning(f"Server is already running (PID: {self.get_pid()})")

        # 启动新进程
        process = subprocess.Popen(cmd)
        
        # 将PID写入文件
        with open(self.pid_file, 'w') as f:
            f.write(str(process.pid))

    def stop(self):
        """停止服务器进程"""
        pid = self.get_pid()
        if not pid:
            return False

        try:
            # 尝试向进程发送信号终止它
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程结束
            # 这里是一个简化的方法，实际应用中可能需要更复杂的逻辑
            time.sleep(1)  # 等待进程结束
            
            # 删除PID文件
            if self.pid_file.exists():
                self.pid_file.unlink()
                
            return True
        except OSError:
            # 进程已经不存在或无权访问
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False

    def restart(self):
        """重启服务器进程"""
        self.stop()
        time.sleep(1)  # 等待进程完全停止
        # 注意：重启需要重新启动命令，这里只是停止，启动需要额外的命令

    def status(self):
        """检查服务器进程状态"""
        pid = self.get_pid()
        if not pid:
            return {"running": False, "pid": None}

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
                if self.pid_file.exists():
                    self.pid_file.unlink()
                return {"running": False, "pid": None}
        except (OSError, subprocess.SubprocessError):
            # 进程不存在或检查失败，清理PID文件
            if self.pid_file.exists():
                self.pid_file.unlink()
            return {"running": False, "pid": None}

    def is_running(self):
        """检查服务器是否正在运行"""
        status = self.status()
        return status["running"]

    def get_pid(self):
        """从PID文件获取进程ID"""
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
                return pid
        except (ValueError, IOError):
            return None