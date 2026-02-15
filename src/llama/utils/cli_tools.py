"""CLI Tools for osins-llama."""
import os
import re
from functools import lru_cache
from typing import Optional


# 预编译正则表达式以提高性能
API_KEY_PATTERN = re.compile(r'\bsk-[a-zA-Z0-9]{20,}\b|\bpk-[a-zA-Z0-9]{20,}\b', re.IGNORECASE)
JWT_TOKEN_PATTERN = re.compile(r'\beyJ[a-zA-Z0-9_]+\.eyJ[a-zA-Z0-9_]+\.[a-zA-Z0-9_-]+\b', re.IGNORECASE)
GENERIC_KEY_TOKEN_PATTERN = re.compile(r'\b(?:secret|key|token|password|pwd|tok|auth|client_secret|refresh_token|bearer_token|session_token)\s*[:=]\s*["\']?[\w-]{10,}["\']?', re.IGNORECASE)
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', re.IGNORECASE)
ID_CARD_PATTERN = re.compile(r'\b\d{17}[\dXx]\b', re.IGNORECASE)


@lru_cache(maxsize=128)
def cached_mask_sensitive(data: str) -> str:
    """
    使用LRU缓存的脱敏函数，提高性能
    """
    return _perform_masking(data)


def mask_sensitive(data: str) -> str:
    """
    对敏感信息进行脱敏处理，支持路径、PID、URL等
    """
    # 限制单行日志的最大处理长度
    if len(data) > 10240:  # 10KB
        # 对超长日志进行分段处理
        segments = []
        for i in range(0, len(data), 10240):
            segment = data[i:i+10240]
            segments.append(_perform_masking(segment))
        return "".join(segments)
    else:
        return _perform_masking(data)


def _perform_masking(data: str) -> str:
    """
    执行实际的脱敏操作
    """
    # 脱敏路径信息
    if "/" in data or "\\" in data:
        parts = data.split(os.sep) if os.sep in data else data.split("/")
        if len(parts) > 1:
            return os.sep.join(["***" if i != len(parts)-1 else parts[i] for i in range(len(parts))])
    
    # 脱敏可能的PID
    if re.match(r'^\d+$', data) and len(data) < 10:  # 假设PID不超过10位数
        return "***"
    
    # 脱敏URL中的密码部分
    data = re.sub(r'://[^@]*@', '://***@', data)
    
    # 按优先级进行脱敏处理
    
    # 高优先级 - API密钥
    data = API_KEY_PATTERN.sub(lambda m: f"{m.group()[:5]}***{m.group()[-3:]}", data)
    
    # 高优先级 - JWT令牌
    data = JWT_TOKEN_PATTERN.sub(lambda m: f"{m.group()[:10]}***{m.group()[-10:]}", data)
    
    # 中优先级 - 通用密钥/令牌
    data = GENERIC_KEY_TOKEN_PATTERN.sub(lambda m: re.sub(r'(?<=[:=]\s*["\']?)[^"\']+(?=["\']?)', '***', m.group()), data)
    
    # 低优先级 - 信用卡号
    data = CREDIT_CARD_PATTERN.sub(lambda m: f"{m.group()[:4]}-****-****-{m.group()[-4:]}", data)
    
    # 低优先级 - 身份证号
    data = ID_CARD_PATTERN.sub(lambda m: f"{m.group()[:6]}***********{m.group()[-2:]}", data)
    
    return data