import asyncio
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
import requests
import threading
from src.llama.services.chat_service import ChatService
from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_role import ChatRole


class TestPerformance:
    """性能测试类"""
    
    @pytest.fixture(scope="class")
    def chat_service(self):
        """创建聊天服务实例"""
        service = ChatService.get_instance()
        yield service
        # 清理代码（如有需要）
    
    def test_single_request_performance(self, chat_service):
        """测试单个请求的性能"""
        request = ChatCompletionRequest(
            model="test-model",
            messages=[
                ChatMessage(
                    role=ChatRole.USER,
                    content="Hello, how are you?"
                )
            ]
        )
        
        start_time = time.time()
        response = asyncio.run(chat_service.generate(request))
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Single request took {duration:.2f} seconds")
        
        # 断言响应时间小于5秒
        assert duration < 5.0
    
    def test_multiple_sequential_requests(self, chat_service):
        """测试多个连续请求的性能"""
        requests_list = []
        for i in range(5):
            req = ChatCompletionRequest(
                model="test-model",
                messages=[
                    ChatMessage(
                        role=ChatRole.USER,
                        content=f"Hello, this is request {i}"
                    )
                ]
            )
            requests_list.append(req)
        
        start_time = time.time()
        for req in requests_list:
            asyncio.run(chat_service.generate(req))
        end_time = time.time()
        
        total_duration = end_time - start_time
        avg_duration = total_duration / len(requests_list)
        
        print(f"Average duration per request: {avg_duration:.2f} seconds")
        assert avg_duration < 5.0  # 平均每个请求小于5秒
    
    @pytest.mark.asyncio
    async def test_async_performance(self, chat_service):
        """测试异步性能"""
        async def make_request(i):
            req = ChatCompletionRequest(
                model="test-model",
                messages=[
                    ChatMessage(
                        role=ChatRole.USER,
                        content=f"Async request {i}"
                    )
                ]
            )
            return await chat_service.generate(req)
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(5)]
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_duration = end_time - start_time
        print(f"Async requests took {total_duration:.2f} seconds")
        assert total_duration < 10.0  # 5个异步请求应在10秒内完成


def test_token_calculation_performance():
    """测试token计算性能"""
    from src.llama.utils.token_utils import count_tokens
    
    # 测试短文本
    short_text = "Hello world"
    start_time = time.time()
    tokens = count_tokens(short_text)
    short_duration = time.time() - start_time
    
    # 测试长文本
    long_text = "Hello world. " * 1000
    start_time = time.time()
    tokens = count_tokens(long_text)
    long_duration = time.time() - start_time
    
    print(f"Short text token calculation: {short_duration:.4f}s")
    print(f"Long text token calculation: {long_duration:.4f}s")
    
    # 确保长文本处理时间合理（小于1秒）
    assert long_duration < 1.0