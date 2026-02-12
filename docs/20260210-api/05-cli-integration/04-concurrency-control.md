# CLI 并发控制

## 概述

CLI并发控制模块负责管理CLI命令执行时的并发请求和资源竞争，确保系统在高负载情况下依然能够稳定运行。本模块通过队列管理、限流机制和资源池管理来实现有效的并发控制。

## 并发场景

### 1. 多命令并发执行
- 同时执行多个CLI命令
- 防止资源竞争
- 确保命令执行顺序

### 2. 进程管理并发
- 启动、停止、重启服务器
- 防止重复操作
- 确保进程状态一致性

### 3. 文件访问并发
- 配置文件读写
- PID文件管理
- 日志文件写入

## 并发控制策略

### 1. 队列管理
- 使用先进先出(FIFO)队列
- 限制队列大小
- 超时处理机制

### 2. 限流机制
- 控制命令执行频率
- 限制并发数量
- 防止系统过载

### 3. 资源池管理
- 管理系统资源使用
- 预防资源泄漏
- 优化资源分配

## 实现方案

### 1. 命令执行队列

```python
import asyncio
import threading
from collections import deque
from typing import Callable, Any
from dataclasses import dataclass
from enum import Enum
import time
import logging


class CommandType(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    STATUS = "status"
    CONFIG = "config"
    LOGS = "logs"
    HEALTH = "health"


@dataclass
class CommandTask:
    command_type: CommandType
    command_func: Callable
    args: tuple
    kwargs: dict
    submit_time: float
    timeout: int = 30
    callback: callable = None  # 任务完成回调


class CommandQueue:
    def __init__(self, max_size: int = 10, timeout: int = 30):
        self.queue = deque()
        self.max_size = max_size
        self.timeout = timeout
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.running = False
        self.worker_thread = None
        self.logger = logging.getLogger(__name__)

    def submit(self, task: CommandTask) -> bool:
        """提交任务到队列"""
        with self.condition:
            if len(self.queue) >= self.max_size:
                self.logger.warning(f"Command queue is full, rejecting task {task.command_type.value}")
                return False  # 队列已满
            
            self.queue.append(task)
            self.condition.notify()
            self.logger.info(f"Task {task.command_type.value} submitted to queue")
            return True

    def get_next_task(self) -> CommandTask:
        """从队列获取下一个任务"""
        with self.condition:
            while not self.queue and self.running:
                self.condition.wait(timeout=self.timeout)
            
            if self.queue:
                return self.queue.popleft()
            return None

    def start_worker(self):
        """启动工作线程"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.start()

    def stop_worker(self):
        """停止工作线程"""
        self.running = False
        with self.condition:
            self.condition.notify_all()
        
        if self.worker_thread:
            self.worker_thread.join()

    def _worker(self):
        """工作线程执行任务"""
        while self.running:
            task = self.get_next_task()
            if task:
                try:
                    # 检查任务是否超时
                    if time.time() - task.submit_time > task.timeout:
                        self.logger.warning(f"Task {task.command_type.value} timed out")
                        continue
                    
                    # 执行任务
                    result = task.command_func(*task.args, **task.kwargs)
                    
                    # 执行回调
                    if task.callback:
                        task.callback(result)
                        
                    self.logger.info(f"Task {task.command_type.value} completed successfully")
                except Exception as e:
                    self.logger.error(f"Error executing task {task.command_type.value}: {str(e)}")
                    # 可以选择重试或记录错误
                    if task.callback:
                        task.callback(None, error=e)
```

### 2. 限流实现

```python
import time
from typing import Dict
from collections import defaultdict, deque
import threading


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str = "default") -> bool:
        """检查请求是否被允许"""
        with self.lock:
            now = time.time()
            
            # 清理过期的请求记录 - 使用双端队列优化
            while (self.requests[identifier] and 
                   now - self.requests[identifier][0] >= self.window_seconds):
                self.requests[identifier].popleft()
            
            # 检查是否超过限制
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # 记录当前请求
            self.requests[identifier].append(now)
            return True


class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int):
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.current_count = 0
        self.lock = threading.Lock()

    def acquire(self, timeout: float = None) -> bool:
        """获取执行许可，支持超时"""
        acquired = self.semaphore.acquire(timeout=timeout)
        if acquired:
            with self.lock:
                self.current_count += 1
        return acquired

    def release(self):
        """释放执行许可"""
        with self.lock:
            if self.current_count > 0:
                self.current_count -= 1
        self.semaphore.release()
```

### 3. 资源锁管理

```python
import threading
from contextlib import contextmanager
from typing import Dict


class ResourceLockManager:
    def __init__(self):
        self.locks: Dict[str, threading.RLock] = {}
        self.global_lock = threading.RLock()  # 使用RLock避免死锁

    @contextmanager
    def lock_resource(self, resource_id: str):
        """获取资源锁的上下文管理器"""
        with self.global_lock:
            if resource_id not in self.locks:
                self.locks[resource_id] = threading.RLock()
            lock = self.locks[resource_id]
        
        acquired = lock.acquire(timeout=10)  # 10秒超时
        if not acquired:
            raise TimeoutError(f"Could not acquire lock for resource {resource_id}")
        
        try:
            yield
        finally:
            lock.release()

    def is_locked(self, resource_id: str) -> bool:
        """检查资源是否被锁定（简化实现）"""
        with self.global_lock:
            return resource_id in self.locks and self.locks[resource_id]._is_owned()
```

## 线程安全实现

### 1. 线程安全的PID文件管理

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

### 2. 线程安全的日志记录

```python
import threading
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


class ThreadSafeLogger:
    def __init__(self, name: str, log_file: Path, level: str = "INFO", max_bytes: int = 10*1024*1024, backup_count: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 防止重复添加handler
        if not self.logger.handlers:
            # 使用旋转日志处理器
            handler = RotatingFileHandler(
                str(log_file), 
                maxBytes=max_bytes, 
                backupCount=backup_count
            )
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.lock = threading.Lock()

    def log(self, level: str, message: str, **kwargs):
        """线程安全地记录日志"""
        with self.lock:
            log_method = getattr(self.logger, level.lower())
            if kwargs:
                log_method(message, extra=kwargs)
            else:
                log_method(message)
```

## 性能优化

### 1. 连接池管理

```python
import threading
from queue import Queue, Empty
from typing import TypeVar, Generic
import time


T = TypeVar('T')


class ObjectPool(Generic[T]):
    def __init__(self, create_func, reset_func=None, max_size=10, timeout=30):
        self.create_func = create_func
        self.reset_func = reset_func
        self.max_size = max_size
        self.timeout = timeout
        self.pool = Queue(maxsize=max_size)
        self.lock = threading.Lock()
        self.created_count = 0

    def acquire(self) -> T:
        """获取对象，支持超时等待"""
        try:
            # 尝试立即获取
            obj = self.pool.get_nowait()
        except Empty:
            with self.lock:
                if self.created_count < self.max_size:
                    # 创建新对象
                    obj = self.create_func()
                    self.created_count += 1
                else:
                    # 等待可用对象
                    try:
                        obj = self.pool.get(timeout=self.timeout)
                    except Empty:
                        raise TimeoutError("Could not acquire object from pool within timeout")
        
        return obj

    def release(self, obj: T):
        """释放对象"""
        if self.reset_func:
            try:
                self.reset_func(obj)
            except Exception as e:
                # 重置失败的对象不应放回池中
                return
        
        try:
            self.pool.put_nowait(obj)
        except:
            # 池已满，丢弃对象
            pass
```

### 2. 缓存策略

```python
import threading
import time
from typing import Any, Optional
from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # 检查是否过期
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: Any):
        """设置缓存值"""
        with self.lock:
            if key in self.cache:
                # 更新现有键
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                # 删除最久未使用的项
                oldest_key, _ = self.cache.popitem(last=False)
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
```

## 测试策略

### 1. 并发测试

```python
import threading
import time
import pytest
from concurrent.futures import ThreadPoolExecutor


def test_concurrent_command_execution():
    """测试并发命令执行"""
    # 创建命令队列
    queue = CommandQueue(max_size=5)
    queue.start_worker()
    
    results = []
    errors = []
    
    def execute_command(cmd_id):
        try:
            # 模拟命令执行
            time.sleep(0.1)
            results.append(cmd_id)
        except Exception as e:
            errors.append(str(e))
    
    # 并发执行多个命令
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(execute_command, i) for i in range(10)]
        for future in futures:
            future.result()
    
    queue.stop_worker()
    
    assert len(results) == 10
    assert len(errors) == 0


def test_rate_limiter():
    """测试限流器"""
    limiter = RateLimiter(max_requests=5, window_seconds=1)
    
    # 前5个请求应该被允许
    for i in range(5):
        assert limiter.is_allowed("test") == True
    
    # 第6个请求应该被拒绝
    assert limiter.is_allowed("test") == False
    
    # 等待窗口期过去
    time.sleep(1)
    assert limiter.is_allowed("test") == True


def test_concurrency_limiter():
    """测试并发限制器"""
    limiter = ConcurrencyLimiter(max_concurrent=2)
    
    results = []
    
    def worker():
        if limiter.acquire(timeout=1):
            try:
                time.sleep(0.1)  # 模拟工作
                results.append("success")
            finally:
                limiter.release()
        else:
            results.append("failed")
    
    # 启动3个线程，但只有2个能获得许可
    threads = []
    for _ in range(3):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # 应该有2个成功，1个失败
    assert results.count("success") == 2
    assert results.count("failed") == 1
```

## 最佳实践

### 1. 避免死锁
- 按固定顺序获取锁
- 使用超时机制
- 避免在持有锁时调用外部代码

### 2. 资源管理
- 使用上下文管理器
- 及时释放资源
- 监控资源使用情况

### 3. 性能监控
- 监控队列长度
- 跟踪响应时间
- 记录错误率

### 4. 异常处理
- 捕获并记录异常
- 避免任务丢失
- 实现重试机制