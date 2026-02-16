from pydantic import BaseModel, field_validator
from typing import List
from src.llama.core.logger_manager import logger


class SecurityConfig(BaseModel):
    api_keys: List[str] = []
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    max_concurrent_requests: int = 10

    @field_validator('api_keys')
    @classmethod
    def validate_api_keys(cls, v):
        """验证API密钥"""
        if v is None:
            v = []
        
        # 检查API密钥格式（基本验证）
        for key in v:
            if not isinstance(key, str) or len(key) < 10:
                logger.warning(f"Warning: API key appears to be too short: {key[:10]}...")
        
        if not v:
            logger.warning("Warning: No API keys configured. This is insecure for production use.")
        
        return v

    @field_validator('rate_limit_requests')
    @classmethod
    def validate_rate_limit_requests(cls, v):
        """验证速率限制请求次数"""
        if v <= 0:
            raise ValueError("Rate limit requests must be positive")
        if v > 10000:
            logger.warning(f"Warning: High rate limit set: {v}. Ensure infrastructure can handle this load.")
        return v

    @field_validator('max_concurrent_requests')
    @classmethod
    def validate_max_concurrent_requests(cls, v):
        """验证最大并发请求数"""
        if v <= 0:
            raise ValueError("Max concurrent requests must be positive")
        if v > 1000:
            logger.warning(f"Warning: High concurrent request limit set: {v}. Consider reducing for production use.")
        return v