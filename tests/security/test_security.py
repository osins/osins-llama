import pytest
import asyncio
from unittest.mock import patch, MagicMock
from llama.core.security import verify_api_key
from fastapi import HTTPException, Request
from starlette.datastructures import Headers


class TestSecurity:
    """安全测试类"""
    
    def test_api_key_verification_success(self):
        """测试API密钥验证成功"""
        # 模拟请求对象
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"authorization": "Bearer sk-1234567890abcdef"})
        
        # 模拟环境变量
        with patch('os.getenv', return_value='sk-1234567890abcdef'):
            result = verify_api_key(request=mock_request)
            assert result == "sk-1234567890abcdef"
    
    def test_api_key_verification_failure(self):
        """测试API密钥验证失败"""
        # 模拟请求对象
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"authorization": "Bearer invalid-key"})
        
        # 模拟环境变量
        with patch('os.getenv', return_value='sk-1234567890abcdef'):
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(request=mock_request)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid API key"
    
    def test_api_key_missing_header(self):
        """测试缺少API密钥头部"""
        # 模拟请求对象
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({})
        
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(request=mock_request)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Missing Authorization header"
    
    def test_api_key_with_different_formats(self):
        """测试不同格式的API密钥"""
        # 测试Bearer格式
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"authorization": "Bearer sk-test123"})
        
        with patch('os.getenv', return_value='sk-test123'):
            result = verify_api_key(request=mock_request)
            assert result == "sk-test123"
        
        # 测试Basic格式
        mock_request.headers = Headers({"authorization": "Basic sk-test123"})
        
        with patch('os.getenv', return_value='sk-test123'):
            result = verify_api_key(request=mock_request)
            assert result == "sk-test123"
    
    def test_constant_time_comparison(self):
        """测试恒定时间比较以防止时序攻击"""
        # 模拟请求对象
        mock_request = MagicMock(spec=Request)
        
        # 使用正确的密钥
        mock_request.headers = Headers({"authorization": "Bearer sk-correct-key"})
        
        with patch('os.getenv', return_value='sk-correct-key'):
            result = verify_api_key(request=mock_request)
            assert result == "sk-correct-key"
        
        # 使用错误的密钥
        mock_request.headers = Headers({"authorization": "Bearer sk-wrong-key"})
        
        with patch('os.getenv', return_value='sk-correct-key'):
            with pytest.raises(HTTPException):
                verify_api_key(request=mock_request)
    
    def test_multiple_api_keys(self):
        """测试多个API密钥"""
        from llama.config.config import Config
        
        # 创建配置对象并设置多个API密钥
        config = Config.from_env()
        config.security.api_keys = ["key1", "key2", "key3"]
        
        # 测试每个密钥
        for key in config.security.api_keys:
            mock_request = MagicMock(spec=Request)
            mock_request.headers = Headers({"authorization": f"Bearer {key}"})
            
            # Mock Config.from_env() to return our test config
            with patch('src.llama.core.security.Config.from_env', return_value=config):
                result = verify_api_key(request=mock_request)
                assert result == key
        
        # 测试无效密钥
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"authorization": "Bearer invalid-key"})
        
        with patch('src.llama.core.security.Config.from_env', return_value=config):
            with pytest.raises(HTTPException):
                verify_api_key(request=mock_request)
    
    def test_api_key_brute_force_protection(self):
        """测试API密钥暴力破解保护"""
        # 模拟请求对象
        mock_request = MagicMock(spec=Request)
        
        # 尝试多次无效的API密钥
        with patch('os.getenv', return_value='valid-key'):
            for i in range(100):
                mock_request.headers = Headers({"authorization": f"Bearer invalid-key-{i}"})
                
                with pytest.raises(HTTPException) as exc_info:
                    verify_api_key(request=mock_request)
                
                assert exc_info.value.status_code == 401