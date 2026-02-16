"""请求调度器模块，负责并发控制和超时管理"""

import asyncio
import time
from typing import Callable, Any, Optional
from asyncio import Semaphore
from src.llama.config.config import Config
from src.llama.core.logger_manager import logger


class RequestScheduler:
    """
    请求调度器，负责管理并发请求和超时控制
    """
    
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, config: Config = None):
        """
        初始化调度器
        
        Args:
            config: 配置对象
        """
        self.config = config or Config.from_env()
        
        # 并发控制信号量
        self._semaphore = Semaphore(self.config.service.max_concurrent_requests)
        
        # 存储活跃任务
        self._active_tasks = {}
        
        # 超时设置
        self._request_timeout = self.config.service.request_timeout_seconds

    @classmethod
    async def get_instance(cls, config: Config = None):
        """
        获取调度器单例实例
        
        Args:
            config: 配置对象
            
        Returns:
            RequestScheduler实例
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config)
        return cls._instance

    async def submit_task(self, task_func: Callable, *args, **kwargs) -> Any:
        """
        提交任务到调度器
        
        Args:
            task_func: 要执行的任务函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            任务执行结果
            
        Raises:
            asyncio.TimeoutError: 请求超时时抛出
            Exception: 任务执行异常时抛出
        """
        # 获取并发槽位
        await self._acquire_slot()
        
        task_id = f"task_{int(time.time() * 1000000)}"
        start_time = time.time()
        
        try:
            # 创建带超时的任务
            task = asyncio.create_task(
                self._execute_with_timeout(task_func, *args, **kwargs)
            )
            
            # 记录活跃任务
            self._active_tasks[task_id] = {
                'task': task,
                'start_time': start_time,
                'args': args,
                'kwargs': kwargs
            }
            
            # 等待任务完成
            result = await task
            
            logger.info(
                f"Task {task_id} completed successfully in {time.time() - start_time:.2f}s"
            )
            
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Task {task_id} timed out after {self._request_timeout}s")
            raise
        except Exception as e:
            logger.error(f"Task {task_id} failed with error: {str(e)}")
            raise
        finally:
            # 清理任务记录
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
                
            # 释放并发槽位
            self._release_slot()

    async def _acquire_slot(self):
        """
        获取并发槽位，如果达到最大并发数则等待
        """
        await self._semaphore.acquire()

    def _release_slot(self):
        """
        释放并发槽位
        """
        self._semaphore.release()

    async def _execute_with_timeout(self, func: Callable, *args, **kwargs):
        """
        在指定超时时间内执行函数
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            asyncio.TimeoutError: 超时时抛出
        """
        try:
            # 使用asyncio.wait_for设置超时
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self._request_timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Request timed out after {self._request_timeout} seconds")
            raise

    async def get_status(self) -> dict:
        """
        获取调度器状态
        
        Returns:
            包含调度器状态信息的字典
        """
        active_count = len(self._active_tasks)
        available_slots = self._semaphore._value  # 当前可用槽位数
        
        return {
            "active_requests": active_count,
            "max_concurrent_requests": self.config.service.max_concurrent_requests,
            "available_slots": available_slots,
            "queued_requests": max(0, active_count - (self.config.service.max_concurrent_requests - available_slots)),
            "avg_processing_time": self._calculate_avg_processing_time(),
            "total_processed_requests": getattr(self, '_total_processed_requests', 0)
        }

    def _calculate_avg_processing_time(self) -> float:
        """
        计算平均处理时间
        
        Returns:
            平均处理时间（秒）
        """
        # 这里简化处理，实际应用中可能需要维护历史统计数据
        return 0.0

    async def handle_timeout(self, task_id: str):
        """
        处理超时任务
        
        Args:
            task_id: 超时任务ID
        """
        if task_id in self._active_tasks:
            task_info = self._active_tasks[task_id]
            task = task_info['task']
            
            logger.warning(f"Cancelling timed out task: {task_id}")
            
            # 取消任务
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Task {task_id} was successfully cancelled due to timeout")
            except Exception as e:
                logger.error(f"Error during cancellation of task {task_id}: {str(e)}")
            finally:
                # 清理任务记录
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
                    
                # 释放并发槽位
                self._release_slot()


class ConcurrentRequestLimiter:
    """
    并发请求限制器，用于控制同时处理的请求数量
    """
    
    def __init__(self, max_concurrent: int):
        """
        初始化限制器
        
        Args:
            max_concurrent: 最大并发数
        """
        self._semaphore = Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent

    async def acquire(self):
        """
        获取执行许可
        """
        await self._semaphore.acquire()

    def release(self):
        """
        释放执行许可
        """
        self._semaphore.release()

    def available_permits(self) -> int:
        """
        获取可用许可数
        
        Returns:
            可用许可数
        """
        return self._semaphore._value

    def max_concurrent(self) -> int:
        """
        获取最大并发数
        
        Returns:
            最大并发数
        """
        return self._max_concurrent