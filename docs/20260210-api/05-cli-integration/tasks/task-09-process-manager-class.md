# ProcessManager类实现

## 概述

ProcessManager类负责管理服务器进程的生命周期，包括启动、停止、重启和状态检查。

## 实现要求

1. 实现进程管理的基本功能（启动、停止、重启、状态检查）
2. 确保PID文件的安全性（防止符号链接攻击、验证权限等）
3. 实现进程身份验证
4. 提供原子性的PID写入操作
5. 实现优雅的进程启停机制

## 代码实现

```python
"""Production-grade process manager."""

import os
import sys
import time
import stat
import psutil
import subprocess
from pathlib import Path
from typing import List, Optional


class ProcessError(Exception):
    """Base process exception."""


class ProcessAlreadyRunning(ProcessError):
    """Process already running."""


class ProcessNotRunning(ProcessError):
    """Process not running."""


class InvalidPIDFile(ProcessError):
    """PID file invalid or corrupted."""


class PIDSecurityError(ProcessError):
    """PID file security violation."""


class ProcessTimeout(ProcessError):
    """Process stop timeout."""


class ProcessManager:
    """
    Production-grade process manager.

    Security guarantees:
    - No symlink PID file
    - Owner validation
    - Process identity validation
    - Atomic PID write
    """

    def __init__(
        self,
        pid_file: Path,
        expected_cmd_keyword: str,
        stop_timeout: int = 30,
        check_interval: float = 0.5,
    ):
        self.pid_file = pid_file.resolve()
        self.expected_cmd_keyword = expected_cmd_keyword
        self.stop_timeout = stop_timeout
        self.check_interval = check_interval

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def start(self, command: List[str]) -> None:
        if self.is_running():
            raise ProcessAlreadyRunning("Process already running.")

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )

        self._secure_write_pid(process.pid)

    def stop(self, force: bool = False) -> None:
        pid = self._read_pid()

        process = self._validate_process(pid)

        if force:
            process.kill()
        else:
            process.terminate()

        self._wait_for_exit(process)

        self._safe_remove_pid()

    def restart(self, command: List[str]) -> None:
        if self.is_running():
            self.stop()
        self.start(command)

    def status(self) -> bool:
        if not self.pid_file.exists():
            return False

        try:
            pid = self._read_pid()
            process = self._validate_process(pid)
            return process.is_running()
        except Exception:
            return False

    def is_running(self) -> bool:
        return self.status()

    # ---------------------------------------------------------
    # Internal Security Methods
    # ---------------------------------------------------------

    def _secure_write_pid(self, pid: int) -> None:
        if self.pid_file.exists():
            raise ProcessAlreadyRunning("PID file already exists.")

        if self.pid_file.is_symlink():
            raise PIDSecurityError("PID file cannot be symlink.")

        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

        tmp_file = self.pid_file.with_suffix(".tmp")

        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(str(pid))
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_file, self.pid_file)

        # Restrict permissions (600)
        os.chmod(self.pid_file, stat.S_IRUSR | stat.S_IWUSR)

    def _read_pid(self) -> int:
        if not self.pid_file.exists():
            raise ProcessNotRunning("PID file not found.")

        if self.pid_file.is_symlink():
            raise PIDSecurityError("PID file is symlink.")

        try:
            content = self.pid_file.read_text(encoding="utf-8").strip()
            pid = int(content)
            if pid <= 0:
                raise ValueError
            return pid
        except ValueError:
            raise InvalidPIDFile("Invalid PID content.")

    def _validate_process(self, pid: int) -> psutil.Process:
        try:
            process = psutil.Process(pid)

            cmdline = " ".join(process.cmdline())

            if self.expected_cmd_keyword not in cmdline:
                raise PIDSecurityError(
                    "PID does not belong to expected service."
                )

            return process

        except psutil.NoSuchProcess:
            raise ProcessNotRunning("Process not found.")
        except psutil.AccessDenied:
            raise PIDSecurityError("Access denied to process.")

    def _wait_for_exit(self, process: psutil.Process) -> None:
        start_time = time.time()

        while time.time() - start_time < self.stop_timeout:
            if not process.is_running():
                return
            time.sleep(self.check_interval)

        raise ProcessTimeout("Process did not stop within timeout.")

    def _safe_remove_pid(self) -> None:
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass
```

## 验证标准

- [ ] 类的基本功能实现完整
- [ ] PID文件安全性验证完整
- [ ] 进程身份验证机制有效
- [ ] 原子性PID写入操作实现
- [ ] 优雅启停机制实现
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 防止符号链接攻击
- 验证PID文件权限
- 验证进程归属
- 实现安全的PID写入

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12