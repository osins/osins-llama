import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from llama.services.scheduler import RequestScheduler, ConcurrentRequestLimiter
from llama.config.config import Config


@pytest.fixture
def mock_config():
    """模拟配置对象"""
    config = Mock(spec=Config)
    config.service.max_concurrent_requests = 5
    config.service.request_timeout_seconds = 30
    return config


@pytest.mark.asyncio
async def test_request_scheduler_initialization(mock_config):
    """测试调度器初始化"""
    scheduler = RequestScheduler(mock_config)
    
    assert scheduler.config == mock_config
    assert scheduler._request_timeout == 30
    assert scheduler._semaphore._value == 5  # 初始可用槽位数


@pytest.mark.asyncio
async def test_request_scheduler_submit_task_success(mock_config):
    """测试成功提交任务"""
    scheduler = RequestScheduler(mock_config)
    
    async def sample_task(x, y):
        await asyncio.sleep(0.1)  # 模拟异步任务
        return x + y
    
    result = await scheduler.submit_task(sample_task, 2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_request_scheduler_timeout(mock_config):
    """测试任务超时"""
    # 修改配置以测试超时
    mock_config.service.request_timeout_seconds = 0.1
    
    scheduler = RequestScheduler(mock_config)
    
    async def slow_task():
        await asyncio.sleep(1)  # 故意超过超时时间
        return "result"
    
    with pytest.raises(asyncio.TimeoutError):
        await scheduler.submit_task(slow_task)


@pytest.mark.asyncio
async def test_concurrent_request_limiter():
    """测试并发请求限制器"""
    limiter = ConcurrentRequestLimiter(2)
    
    # 获取两个许可
    await limiter.acquire()
    await limiter.acquire()
    
    # 此时应该没有更多可用许可
    assert limiter.available_permits() == 0
    assert limiter.max_concurrent() == 2
    
    # 尝试获取第三个许可，这会阻塞
    async def try_acquire():
        await limiter.acquire()
        limiter.release()
    
    # 创建一个任务尝试获取许可，但由于没有可用许可，它会被阻塞
    task = asyncio.create_task(try_acquire())
    
    # 确认任务还没有完成（因为它在等待许可）
    await asyncio.sleep(0.01)  # 短暂等待
    assert not task.done()
    
    # 释放一个许可，使任务能够继续
    limiter.release()
    
    # 等待任务完成
    await task
    
    # 现在应该有一个可用许可
    assert limiter.available_permits() == 1