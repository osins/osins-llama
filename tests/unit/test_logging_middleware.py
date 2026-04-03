import pytest
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from llama.middlewares.logging_middleware import LoggingMiddleware, setup_logging_config


@pytest.fixture
def app_with_logging():
    """创建带有日志中间件的FastAPI应用"""
    app = FastAPI()
    
    # 添加日志中间件
    logger = logging.getLogger("test_logger")
    app.add_middleware(LoggingMiddleware, logger=logger)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    return app


@pytest.fixture
def client(app_with_logging):
    """创建测试客户端"""
    return TestClient(app_with_logging)


def test_logging_middleware_initialization():
    """测试日志中间件初始化"""
    app = FastAPI()
    logger = logging.getLogger("test_logger")
    
    middleware = LoggingMiddleware(app, logger)
    
    assert middleware.logger == logger


def test_logging_middleware_request_response(client):
    """测试日志中间件记录请求和响应"""
    with patch.object(logging.getLogger("test_logger"), 'info') as mock_log_info:
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # 验证日志被记录
        assert mock_log_info.called
        # 检查是否记录了请求开始和结束
        call_args_list = mock_log_info.call_args_list
        assert len(call_args_list) >= 2  # 至少有开始和结束日志


def test_sanitize_headers():
    """测试请求头清理功能"""
    app = FastAPI()
    logger = logging.getLogger("test_logger")
    middleware = LoggingMiddleware(app, logger)
    
    headers = {
        'authorization': 'Bearer secret-token',
        'x-api-key': 'secret-key',
        'cookie': 'session=abc123',
        'user-agent': 'test-agent'
    }
    
    sanitized = middleware._sanitize_headers(headers)
    
    # 敏感头应该被隐藏
    assert sanitized['authorization'] == "***REDACTED***"
    assert sanitized['x-api-key'] == "***REDACTED***"
    assert sanitized['cookie'] == "***REDACTED***"
    
    # 非敏感头应该保留
    assert sanitized['user-agent'] == 'test-agent'


def test_setup_logging_config():
    """测试日志配置设置"""
    # 这个函数主要是配置日志，我们只是确保它不会抛出异常
    setup_logging_config()
    
    # 验证根记录器已被配置
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO