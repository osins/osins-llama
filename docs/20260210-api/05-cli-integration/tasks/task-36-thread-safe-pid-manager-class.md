# ThreadSafePIDManager类实现

## 概述

ThreadSafePIDManager类用于线程安全地管理PID文件，防止多个线程同时操作PID文件。

## 实现要求

1. 实现线程安全的PID文件管理
2. 支持PID文件的读写操作
3. 防止竞态条件
4. 确保文件操作的原子性

## 代码实现

```python
import threading
from pathlib import Path
import os
import stat


class ThreadSafePIDManager:
    def __init__(self, pid_file: Path):
        self.pid_file = pid_file
        self.lock = threading.RLock()

    def write_pid(self, pid: int):
        """线程安全地写入PID"""
        with self.lock:
            try:
                # 创建临时文件
                tmp_file = self.pid_file.with_suffix('.tmp')
                with open(tmp_file, 'w') as f:
                    f.write(str(pid))
                    f.flush()
                    os.fsync(f.fileno())  # 确保写入磁盘

                # 原子替换
                os.replace(tmp_file, self.pid_file)

                # 设置权限为 600
                os.chmod(self.pid_file, stat.S_IRUSR | stat.S_IWUSR)
            except IOError as e:
                raise RuntimeError(f"Failed to write PID file: {e}")

    def read_pid(self) -> int:
        """线程安全地读取PID"""
        with self.lock:
            if not self.pid_file.exists():
                raise FileNotFoundError("PID file does not exist")
            try:
                with open(self.pid_file, 'r') as f:
                    content = f.read().strip()
                    return int(content)
            except ValueError:
                raise ValueError("Invalid PID in file")
            except IOError as e:
                raise RuntimeError(f"Failed to read PID file: {e}")

    def remove_pid(self):
        """线程安全地删除PID文件"""
        with self.lock:
            try:
                if self.pid_file.exists():
                    self.pid_file.unlink()
            except IOError as e:
                raise RuntimeError(f"Failed to remove PID file: {e}")
```

## 验证标准

- [ ] 线程安全PID管理功能实现完整
- [ ] PID文件读写操作支持
- [ ] 竞态条件防护
- [ ] 文件操作原子性保证
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止PID文件篡改
- 验证文件权限

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12