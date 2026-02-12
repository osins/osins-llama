import asyncio
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from unittest.mock import patch, MagicMock
from src.llama.core.rate_limiter import RateLimiter
from src.llama.config.config import Config
from src.llama.core.security import ConcurrencyController


class TestConcurrency:
    """并发测试类"""
    
    def test_concurrent_requests_handling(self):
        """测试并发请求处理"""
        config = Config.from_env()
        controller = ConcurrencyController(config)
        
        # 模拟多个并发请求
        async def simulate_request(request_id):
            await controller.acquire()
            try:
                # 模拟处理时间
                await asyncio.sleep(0.1)
                return f"Request {request_id} processed"
            finally:
                await controller.release()
        
        async def run_concurrent_requests():
            tasks = [simulate_request(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results
        
        start_time = time.time()
        results = asyncio.run(run_concurrent_requests())
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"Concurrent requests completed in {total_time:.2f} seconds")
        print(f"Results: {results}")
        
        # 验证所有请求都成功处理
        assert len(results) == 5
        assert all("processed" in result for result in results)
        
        # 验证并发控制器状态
        status = asyncio.run(controller.get_status())
        assert status["active_requests"] == 0  # 所有请求应已完成
    
    def test_rate_limiter_concurrent_access(self):
        """测试限流器的并发访问"""
        config = Config.from_env()
        rate_limiter = RateLimiter(config)
        
        def check_rate_limit(identifier):
            return rate_limiter.is_allowed(identifier)
        
        # 使用线程池模拟并发请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_rate_limit, f"client_{i % 3}") for i in range(20)]  # 3个不同的客户端
            results = [future.result() for future in as_completed(futures)]
        
        # 统计允许的请求数量
        allowed_count = sum(1 for result in results if result)
        print(f"Allowed {allowed_count} out of 20 concurrent requests")
        
        # 由于默认配置允许60个请求/分钟，所以应该大部分请求被允许
        assert allowed_count >= 15  # 至少允许大部分请求
    
    def test_semaphore_concurrent_access(self):
        """测试信号量的并发访问控制"""
        config = Config.from_env()
        controller = ConcurrencyController(config)
        
        results = []
        lock = threading.Lock()
        
        def worker(worker_id):
            async def run():
                await controller.acquire()
                try:
                    # 模拟处理
                    await asyncio.sleep(0.05)
                    with lock:
                        results.append(f"Worker {worker_id} completed")
                finally:
                    await controller.release()
            
            # 在新的事件循环中运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run())
            finally:
                loop.close()
        
        # 创建多个线程模拟并发
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(results) == 10
        assert all("completed" in result for result in results)
        
        # 验证最终状态
        status = asyncio.run(controller.get_status())
        assert status["active_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_high_concurrency_simulation(self):
        """模拟高并发场景"""
        config = Config.from_env()
        controller = ConcurrencyController(config)
        
        async def high_concurrency_worker(worker_id):
            await controller.acquire()
            try:
                # 模拟快速处理
                await asyncio.sleep(0.01)
                return f"Worker {worker_id} done"
            finally:
                await controller.release()
        
        # 创建大量并发任务
        start_time = time.time()
        tasks = [high_concurrency_worker(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        print(f"High concurrency test completed in {total_time:.2f} seconds")
        assert len(results) == 20
        assert all("done" in result for result in results)
        
        # 验证最终状态
        status = await controller.get_status()
        assert status["active_requests"] == 0