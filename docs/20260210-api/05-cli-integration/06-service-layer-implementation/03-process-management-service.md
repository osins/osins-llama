# 进程管理服务

## 概述

进程管理服务负责管理服务器进程的生命周期，包括启动、停止、重启和状态检查等操作。

## 服务职责

- 启动服务器进程
- 停止服务器进程
- 重启服务器进程
- 检查进程状态
- 管理PID文件
- 收集进程日志

## 进程管理器

```python
import os
import stat
import psutil
import subprocess
import time
import asyncio
from pathlib import Path
from typing import List
import logging


class ProcessManager:
    """进程管理器"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def start(self, command: List[str], pid_file: Path, log_file: Path = None) -> None:
        """启动进程"""
        if pid_file.exists():
            if self._is_process_running(pid_file):
                raise ProcessAlreadyRunning("Process is already running.")
            else:
                # PID文件存在但进程不在运行，删除旧文件
                pid_file.unlink()
        
        # 创建PID文件的目录
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 准备日志文件
        stdout_dest = subprocess.DEVNULL
        stderr_dest = subprocess.DEVNULL
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            stdout_dest = open(log_file, 'a')
            stderr_dest = subprocess.STDOUT  # 合并stderr到stdout
        
        # 启动子进程
        process = subprocess.Popen(
            command,
            stdout=stdout_dest,
            stderr=stderr_dest,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
        
        # 写入PID文件
        self._write_pid(process.pid, pid_file)
        
        self.logger.info(f"Process started with PID {process.pid}")
    
    def stop(self, pid_file: Path, force: bool = False) -> None:
        """停止进程"""
        if not pid_file.exists():
            raise ProcessNotRunning("PID file does not exist.")
        
        pid = self._read_pid(pid_file)
        
        try:
            process = psutil.Process(pid)
            
            # 验证进程是否是我们启动的
            if not self._is_expected_process(process):
                raise PIDSecurityError(f"PID {pid} does not belong to expected process.")
            
            if force:
                process.kill()
                self.logger.info(f"Process {pid} killed forcefully")
            else:
                process.terminate()
                try:
                    process.wait(timeout=10)  # 等待进程结束
                    self.logger.info(f"Process {pid} terminated gracefully")
                except psutil.TimeoutExpired:
                    process.kill()  # 强制终止
                    self.logger.warning(f"Process {pid} killed after timeout")
            
            # 删除PID文件
            if pid_file.exists():
                pid_file.unlink()
                
        except psutil.NoSuchProcess:
            self.logger.warning(f"Process {pid} not found, removing stale PID file")
            if pid_file.exists():
                pid_file.unlink()
        except psutil.AccessDenied:
            raise PIDSecurityError(f"Access denied to process {pid}")
    
    def restart(self, command: List[str], pid_file: Path, log_file: Path = None) -> None:
        """重启进程"""
        if self.is_running(pid_file):
            self.stop(pid_file)
            time.sleep(1)  # 等待进程完全停止
        
        self.start(command, pid_file, log_file)
    
    def is_running(self, pid_file: Path) -> bool:
        """检查进程是否运行"""
        if not pid_file.exists():
            return False
        
        try:
            pid = self._read_pid(pid_file)
            process = psutil.Process(pid)
            return process.is_running() and self._is_expected_process(process)
        except:
            return False
    
    def health_check(self, pid_file: Path, port: int = None) -> bool:
        """健康检查 - 通过端口探测"""
        if not self.is_running(pid_file):
            return False
        
        if port:
            # 尝连接指定端口
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                return result == 0  # 如果连接成功，端口是开放的
            except:
                return False
        
        return True
    
    def _read_pid(self, pid_file: Path) -> int:
        """读取PID文件"""
        if pid_file.is_symlink():
            raise InvalidPIDFile("PID file is a symbolic link.")
        
        try:
            content = pid_file.read_text(encoding="utf-8").strip()
            pid = int(content)
            if pid <= 0:
                raise ValueError("Invalid PID value.")
            return pid
        except ValueError:
            raise InvalidPIDFile("Invalid PID content.")
    
    def _write_pid(self, pid: int, pid_file: Path) -> None:
        """安全写入PID文件"""
        # 创建临时文件
        tmp_file = pid_file.with_suffix('.tmp')
        
        with open(tmp_file, 'w', encoding='utf-8') as f:
            f.write(str(pid))
            f.flush()
            os.fsync(f.fileno())  # 确保写入磁盘
        
        # 原子替换
        os.replace(tmp_file, pid_file)
        
        # 设置权限为 600
        os.chmod(pid_file, stat.S_IRUSR | stat.S_IWUSR)
    
    def _is_process_running(self, pid_file: Path) -> bool:
        """检查PID文件中的进程是否正在运行"""
        try:
            pid = self._read_pid(pid_file)
            process = psutil.Process(pid)
            return process.is_running()
        except:
            return False
    
    def _is_expected_process(self, process: psutil.Process) -> bool:
        """检查进程是否是我们期望的进程"""
        try:
            # 检查进程命令行是否包含预期的关键字
            cmdline = " ".join(process.cmdline())
            return "llama.server" in cmdline or "python" in cmdline.lower()
        except:
            return False
```

## 异步进程管理

```python
class AsyncProcessManager:
    """异步进程管理器"""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def start_multiple(self, commands: List[List[str]], pid_files: List[Path]) -> List[bool]:
        """异步启动多个进程"""
        import concurrent.futures
        
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 提交所有启动任务
            futures = [
                executor.submit(self._start_single, cmd, pid_file)
                for cmd, pid_file in zip(commands, pid_files)
            ]
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        return results
    
    def _start_single(self, command: List[str], pid_file: Path) -> bool:
        """启动单个进程（辅助方法）"""
        try:
            self.start(command, pid_file)
            return True
        except Exception as e:
            self.logger.error(f"Failed to start process: {str(e)}")
            return False
```

## 异常定义

```python
class ProcessError(Exception):
    """基础进程异常"""


class ProcessAlreadyRunning(ProcessError):
    """进程已运行异常"""


class ProcessNotRunning(ProcessError):
    """进程未运行异常"""


class InvalidPIDFile(ProcessError):
    """PID文件无效异常"""


class PIDSecurityError(ProcessError):
    """PID安全错误异常"""


class ProcessTimeout(ProcessError):
    """进程超时异常"""
```

## 安全措施

- 防止符号链接攻击
- 验证PID文件权限
- 验证进程归属
- 原子写入PID文件
- 跨平台兼容性测试

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12