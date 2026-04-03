"""Security utilities for osins-llama CLI."""
import os
import stat
import json
import yaml
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
import click
import ijson  # 用于流式解析大JSON文件


SAFE_CONFIG_DIR = "/etc/osins-llama"

# 敏感字段关键词列表
SENSITIVE_FIELD_KEYWORDS = [
    'password', 'secret', 'key', 'token', 'api_key', 'access_token', 
    'database_password', 'oauth_token', 'pwd', 'tok', 'auth', 'authorization',
    'client_secret', 'refresh_token', 'bearer_token', 'session_token'
]


def is_valid_port(port: int) -> bool:
    """验证端口号是否在有效范围内 (1-65535)"""
    return 1 <= port <= 65535


def is_valid_host(host: str) -> bool:
    """验证主机地址是否为有效的IPv4、IPv6或域名格式"""
    import ipaddress
    try:
        # 尝试解析为IP地址
        ipaddress.ip_address(host)
        return True
    except ValueError:
        # 如果不是IP地址，尝试验证为域名
        # 域名验证的基本正则
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        return bool(domain_pattern.match(host))


def is_valid_db_connection_string(connection_string: str) -> bool:
    """验证数据库连接字符串格式"""
    # 基本的数据库连接字符串格式验证
    db_pattern = re.compile(
        r'^(postgresql|mysql|mariadb|sqlite)://[a-zA-Z0-9_.-]+:[^@]+@[\w.-]+(:\d+)?/[a-zA-Z0-9_.-]*$'
    )
    return bool(db_pattern.match(connection_string))


def is_valid_jwt(token: str) -> bool:
    """验证JWT Token格式（三个由点分隔的部分）"""
    jwt_pattern = re.compile(r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$')
    return bool(jwt_pattern.match(token))


def is_valid_oauth_token(token: str) -> bool:
    """验证OAuth Token格式（长度和字符集）"""
    # OAuth Token通常较长，包含字母、数字和可能的特殊字符
    return len(token) >= 20


def is_valid_password(password: str) -> bool:
    """验证密码强度（至少8位，包含数字、字母、特殊符号）"""
    if len(password) < 8:
        return False
    
    has_digit = bool(re.search(r'\d', password))
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    return has_digit and has_letter and has_special


def detect_sensitive_fields(data: Dict[str, Any], path: str = "") -> List[str]:
    """检测配置数据中的潜在敏感字段"""
    sensitive_fields = []
    
    for key, value in data.items():
        current_path = f"{path}.{key}" if path else key
        
        # 检查字段名是否包含敏感关键词
        if any(keyword in key.lower() for keyword in SENSITIVE_FIELD_KEYWORDS):
            sensitive_fields.append(current_path)
        
        # 递归检查嵌套对象
        if isinstance(value, dict):
            sensitive_fields.extend(detect_sensitive_fields(value, current_path))
    
    return sensitive_fields


def validate_json_config(path: Path) -> None:
    """校验JSON配置文件内容格式和关键字段"""
    try:
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 验证必需字段
        required_fields = ["server_port", "host"]
        for field in required_fields:
            if field not in data:
                raise click.BadParameter(f"Config {path} missing required field '{field}'")
                
        # 验证端口号
        if "server_port" in data:
            port = data["server_port"]
            if not isinstance(port, int) or not is_valid_port(port):
                raise click.BadParameter(f"Config {path} has invalid server_port value: {port}. Port must be between 1 and 65535.")
                
        # 验证主机地址
        if "host" in data:
            host = data["host"]
            if not isinstance(host, str) or not is_valid_host(host):
                raise click.BadParameter(f"Config {path} has invalid host value: {host}. Host must be a valid IP address or domain name.")
                
        # 验证数据库连接字符串（如果存在）
        if "database_url" in data:
            db_url = data["database_url"]
            if not isinstance(db_url, str) or not is_valid_db_connection_string(db_url):
                raise click.BadParameter(f"Config {path} has invalid database_url format: {db_url}")
                
        # 检测敏感字段
        sensitive_fields = detect_sensitive_fields(data)
        if sensitive_fields:
            # 这里可以选择记录警告而不是抛出错误，取决于安全策略
            from llama.core.logger_manager import logger
            logger.warning(f"Config {path} contains potentially sensitive fields: {sensitive_fields}")
            
        # 验证JWT Token（如果存在）
        if "jwt_token" in data:
            token = data["jwt_token"]
            if not isinstance(token, str) or not is_valid_jwt(token):
                raise click.BadParameter(f"Config {path} has invalid JWT token format: {token}")
                
        # 验证OAuth Token（如果存在）
        if "oauth_token" in data:
            token = data["oauth_token"]
            if not isinstance(token, str) or not is_valid_oauth_token(token):
                raise click.BadParameter(f"Config {path} has invalid OAuth token format: {token}")
                
        # 验证密码字段（如果存在）
        for key, value in data.items():
            if any(keyword in key.lower() for keyword in SENSITIVE_FIELD_KEYWORDS) and isinstance(value, str):
                if not is_valid_password(value):
                    raise click.BadParameter(f"Config {path} has weak password in field '{key}'. Password must be at least 8 characters with numbers, letters, and special symbols.")
                    
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Config {path} is not a valid JSON file: {e}")


def validate_yaml_config(path: Path) -> None:
    """校验YAML配置文件内容格式和关键字段"""
    try:
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        # 验证必需字段
        required_fields = ["server_port", "host"]
        for field in required_fields:
            if field not in data:
                raise click.BadParameter(f"Config {path} missing required field '{field}'")
                
        # 验证端口号
        if "server_port" in data:
            port = data["server_port"]
            if not isinstance(port, int) or not is_valid_port(port):
                raise click.BadParameter(f"Config {path} has invalid server_port value: {port}. Port must be between 1 and 65535.")
                
        # 验证主机地址
        if "host" in data:
            host = data["host"]
            if not isinstance(host, str) or not is_valid_host(host):
                raise click.BadParameter(f"Config {path} has invalid host value: {host}. Host must be a valid IP address or domain name.")
                
        # 验证数据库连接字符串（如果存在）
        if "database_url" in data:
            db_url = data["database_url"]
            if not isinstance(db_url, str) or not is_valid_db_connection_string(db_url):
                raise click.BadParameter(f"Config {path} has invalid database_url format: {db_url}")
                
        # 检测敏感字段
        sensitive_fields = detect_sensitive_fields(data)
        if sensitive_fields:
            # 这里可以选择记录警告而不是抛出错误，取决于安全策略
            from llama.core.logger_manager import logger
            logger.warning(f"Config {path} contains potentially sensitive fields: {sensitive_fields}")
            
        # 验证JWT Token（如果存在）
        if "jwt_token" in data:
            token = data["jwt_token"]
            if not isinstance(token, str) or not is_valid_jwt(token):
                raise click.BadParameter(f"Config {path} has invalid JWT token format: {token}")
                
        # 验证OAuth Token（如果存在）
        if "oauth_token" in data:
            token = data["oauth_token"]
            if not isinstance(token, str) or not is_valid_oauth_token(token):
                raise click.BadParameter(f"Config {path} has invalid OAuth token format: {token}")
                
        # 验证密码字段（如果存在）
        for key, value in data.items():
            if any(keyword in key.lower() for keyword in SENSITIVE_FIELD_KEYWORDS) and isinstance(value, str):
                if not is_valid_password(value):
                    raise click.BadParameter(f"Config {path} has weak password in field '{key}'. Password must be at least 8 characters with numbers, letters, and special symbols.")
                    
    except yaml.YAMLError as e:
        raise click.BadParameter(f"Config {path} is not a valid YAML file: {e}")


def validate_config_content(path: Path) -> None:
    """根据文件扩展名选择适当的校验方法"""
    if path.suffix.lower() == '.json':
        validate_json_config(path)
    elif path.suffix.lower() in ['.yaml', '.yml']:
        validate_yaml_config(path)
    else:
        raise click.BadParameter(f"Unsupported config file format: {path.suffix}")


def validate_config_path(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Optional[str]:
    """验证配置文件路径的安全性"""
    if value is None:
        return value
    abs_path = os.path.abspath(value)
    if not abs_path.startswith(str(Path(SAFE_CONFIG_DIR).resolve())):
        raise click.BadParameter(f"Config path {value} is outside of allowed directory.")
    if os.path.islink(abs_path):
        raise click.BadParameter(f"Config path {value} must not be a symbolic link.")
    if not os.path.isfile(abs_path):
        raise click.BadParameter(f"Config path {value} must be a regular file.")

    # 检查文件权限
    file_stat = os.stat(abs_path)
    if not bool(file_stat.st_mode & stat.S_IRUSR):
        raise click.BadParameter(f"Config file {value} is not readable by the current user.")

    # 校验配置文件内容
    validate_config_content(Path(abs_path))

    return abs_path