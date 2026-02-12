# CommandQueue类实现

## 概述

CommandQueue类用于管理CLI命令的执行队列，确保命令按顺序执行。

## 实现要求

1. 实现命令队列功能
2. 支持FIFO队列
3. 限制队列大小
4. 实现超时处理机制
5. 确保线程安全

## 代码实现

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

## 验证标准

- [ ] 命令队列功能实现完整
- [ ] FIFO队列支持
- [ ] 队列大小限制
- [ ] 超时处理机制
- [ ] 线程安全实现
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整
- [ ] 异常处理机制完善

## 安全考虑

- 确保线程安全
- 防止队列溢出
- 验证任务参数安全性

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12