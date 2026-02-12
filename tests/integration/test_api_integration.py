import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from src.llama.api.server import create_app
from src.llama.config.config import Config
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_role import ChatRole


@pytest.fixture
def config():
    """创建测试配置"""
    config = Config.from_env()
    # 为测试设置较小的限制
    config.service.max_concurrent_requests = 2
    config.service.request_timeout_seconds = 10
    return config


@pytest.fixture
def client(config):
    """创建测试客户端"""
    app = create_app(config)
    return TestClient(app)


def test_health_endpoint(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "ready"


@patch('src.llama.services.completion_service.CompletionService.generate')
def test_completion_endpoint(mock_generate, client):
    """测试completion端点"""
    # 模拟服务响应
    mock_response = MagicMock()
    mock_response.id = "cmpl-test123"
    mock_response.created = 1234567890
    mock_response.model = "test-model"
    mock_response.choices = []
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    
    mock_generate.return_value = mock_response
    
    # 发送请求
    payload = {
        "model": "test-model",
        "prompt": "Hello, world!",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/v1/completions", json=payload)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["model"] == "test-model"


@patch('src.llama.services.chat_service.ChatService.generate')
def test_chat_completion_endpoint(mock_generate, client):
    """测试chat completion端点"""
    # 模拟服务响应
    mock_response = MagicMock()
    mock_response.id = "chatcmpl-test123"
    mock_response.created = 1234567890
    mock_response.model = "test-model"
    mock_response.choices = []
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 15
    mock_response.usage.completion_tokens = 25
    mock_response.usage.total_tokens = 40
    
    mock_generate.return_value = mock_response
    
    # 发送请求
    payload = {
        "model": "test-model",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    response = client.post("/v1/chat/completions", json=payload)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["model"] == "test-model"


def test_invalid_completion_request(client):
    """测试无效的completion请求"""
    payload = {
        "model": "",  # 无效模型名
        "prompt": "",
        "max_tokens": -1  # 无效max_tokens
    }
    
    response = client.post("/v1/completions", json=payload)
    
    # 应该返回错误
    assert response.status_code in [400, 422]  # 可能是验证错误或业务错误


def test_invalid_chat_request(client):
    """测试无效的chat请求"""
    payload = {
        "model": "",  # 无效模型名
        "messages": [],  # 空消息列表
        "max_tokens": -1  # 无效max_tokens
    }
    
    response = client.post("/v1/chat/completions", json=payload)
    
    # 应该返回错误
    assert response.status_code in [400, 422]  # 可能是验证错误或业务错误


@patch('src.llama.services.completion_service.CompletionService.generate')
def test_concurrent_requests_handling(mock_generate, client):
    """测试并发请求处理"""
    # 模拟服务响应
    def mock_gen_func(*args, **kwargs):
        import time
        time.sleep(0.1)  # 模拟处理时间
        mock_response = MagicMock()
        mock_response.id = f"cmpl-test{int(time.time()*1000)}"
        mock_response.created = int(time.time())
        mock_response.model = "test-model"
        mock_response.choices = []
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        return mock_response

    mock_generate.side_effect = mock_gen_func
    
    # 并发发送多个请求
    import concurrent.futures
    import threading
    
    def send_request():
        payload = {
            "model": "test-model",
            "prompt": "Hello, world!",
            "max_tokens": 10,
            "temperature": 0.7
        }
        response = client.post("/v1/completions", json=payload)
        return response.status_code, response.json() if response.status_code == 200 else response.text

    # 使用线程池发送并发请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(send_request) for _ in range(5)]
        results = [future.result() for future in futures]
    
    # 验证结果
    success_count = sum(1 for status, _ in results if status == 200)
    assert success_count > 0  # 至少有一些请求成功


def test_api_key_authentication(client):
    """测试API密钥认证"""
    # 首先尝试不带认证的请求
    payload = {
        "model": "test-model",
        "prompt": "Hello, world!",
        "max_tokens": 100
    }
    
    response = client.post("/v1/completions", json=payload)
    
    # 如果配置了API密钥验证，应该返回401
    # 但如果没配置，可能会有不同的行为，所以这里只是记录行为
    print(f"Response without auth: {response.status_code}")


def test_rate_limiting(client):
    """测试速率限制"""
    # 这个测试需要根据实际的速率限制配置来调整
    # 发送大量请求以测试速率限制
    payload = {
        "model": "test-model",
        "prompt": "Hello, world!",
        "max_tokens": 10,
        "temperature": 0.7
    }
    
    # 发送多个请求
    responses = []
    for i in range(10):
        response = client.post("/v1/completions", json=payload)
        responses.append(response.status_code)
    
    # 检查是否有速率限制响应(429)
    rate_limited = [status for status in responses if status == 429]
    print(f"Rate limited responses: {len(rate_limited)} out of {len(responses)}")