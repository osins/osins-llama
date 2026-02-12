#!/usr/bin/env python
"""
简化验证脚本，测试重构的核心功能
"""
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_basic_imports():
    """测试基本导入"""
    print("Testing basic imports...")
    
    try:
        from src.llama.config.config import Config
        print("[OK] Config import successful")
    except ImportError as e:
        print(f"[ERROR] Config import failed: {e}")
        return False
    
    try:
        from src.llama.core.model_manager import ModelManager
        print("[OK] ModelManager import successful")
    except ImportError as e:
        print(f"[ERROR] ModelManager import failed: {e}")
        return False

    # 测试API路由导入
    try:
        from src.llama.api.chat_routes import router as chat_router
        from src.llama.api.completion_routes import router as completion_router
        print("[OK] API routes import successful")
    except ImportError as e:
        print(f"[ERROR] API routes import failed: {e}")
        return False

    # 测试服务导入
    try:
        from src.llama.services.chat_service import ChatService
        from src.llama.services.completion_service import CompletionService
        print("[OK] Services import successful")
    except ImportError as e:
        print(f"[ERROR] Services import failed: {e}")
        return False

    return True

def test_config_separation():
    """测试配置类是否已正确分离"""
    print("\nTesting config separation...")

    try:
        # 尝试导入分离后的配置类
        from src.llama.config.model_config import ModelConfig
        from src.llama.config.resources_config import ResourcesConfig
        from src.llama.config.security_config import SecurityConfig
        from src.llama.config.service_config import ServiceConfig
        print("[OK] Individual config classes import successful")

        # 导入Config类
        from src.llama.config.config import Config
        
        # 验证Config类仍然包含这些字段
        config = Config(
            model=ModelConfig(path="/tmp/test.bin"),
            resources=ResourcesConfig(),
            security=SecurityConfig(),
            service=ServiceConfig()
        )
        print("[OK] Config class works correctly")

    except Exception as e:
        print(f"[ERROR] Config separation test failed: {e}")
        return False

    return True

def test_exception_separation():
    """测试异常类是否已正确分离"""
    print("\nTesting exception separation...")
    
    try:
        # 尝试导入分离后的异常类
        from src.llama.exceptions.api_error import APIError
        from src.llama.exceptions.validation_error import ValidationError
        from src.llama.exceptions.rate_limit_error import RateLimitError
        from src.llama.exceptions.service_error import ServiceError
        from src.llama.exceptions.model_load_error import ModelLoadError
        from src.llama.exceptions.authentication_error import AuthenticationError
        print("[OK] Individual exception classes import successful")
        
        # 测试异常是否可以正常工作
        try:
            raise ValidationError("Test validation error")
        except ValidationError as e:
            print("[OK] ValidationError works correctly")
        
    except Exception as e:
        print(f"[ERROR] Exception separation test failed: {e}")
        return False
    
    return True

def test_security_module_structure():
    """测试安全模块的基本结构"""
    print("\nTesting security module structure...")
    
    try:
        # 测试ConcurrencyController是否在security.py中
        from src.llama.core.security import ConcurrencyController
        print("[OK] ConcurrencyController in security module")
        
        # 测试RateLimiter是否在rate_limiter.py中
        from src.llama.core.rate_limiter import RateLimiter
        print("[OK] RateLimiter in rate_limiter module")
        
        # 验证security.py中仍然有必要的函数
        from src.llama.core.security import verify_api_key, get_concurrency_controller
        print("[OK] Security functions in security module")
        
    except Exception as e:
        print(f"[ERROR] Security module structure test failed: {e}")
        return False
    
    return True

def test_removed_comments():
    """测试是否已移除注释"""
    print("\nTesting removed comments...")
    
    import inspect
    from src.llama.utils.token_utils import count_tokens
    
    # 获取函数源码
    source = inspect.getsource(count_tokens)
    
    # 检查是否还有注释
    if '#' in source:
        print("[ERROR] Comments still present in token_utils.py")
        return False
    else:
        print("[OK] Comments removed from token_utils.py")
    
    return True

def main():
    """主函数"""
    print("Starting simplified validation tests...\n")
    
    success = True
    success &= test_basic_imports()
    success &= test_config_separation()
    success &= test_exception_separation()
    success &= test_security_module_structure()
    success &= test_removed_comments()
    
    if success:
        print("\n[SUCCESS] All simplified tests passed!")
        print("The refactoring was successful!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())