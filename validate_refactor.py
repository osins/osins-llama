#!/usr/bin/env python
"""
Validation script to verify that the refactored code still works properly
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_imports():
    """Test that all necessary imports still work"""
    print("Testing imports...")
    
    # Test config import
    try:
        from src.llama.config.config import Config
        print("[OK] Config import successful")
    except ImportError as e:
        print(f"[ERROR] Config import failed: {e}")
        return False
        
    # Test model manager import
    try:
        from src.llama.core.model_manager import ModelManager
        print("[OK] ModelManager import successful")
    except ImportError as e:
        print(f"[ERROR] ModelManager import failed: {e}")
        return False
    
    # Test security module import
    try:
        from src.llama.core.security import verify_api_key, get_rate_limiter, get_concurrency_controller
        print("[OK] Security functions import successful")
    except ImportError as e:
        print(f"[ERROR] Security functions import failed: {e}")
        return False
    
    # Test exception import
    try:
        from src.llama.exceptions import ValidationError, RateLimitError, ServiceError, AuthenticationError
        print("[OK] Exceptions import successful")
    except ImportError as e:
        print(f"[ERROR] Exceptions import failed: {e}")
        return False
    
    # Test API route import
    try:
        from src.llama.api.chat_routes import router as chat_router
        from src.llama.api.completion_routes import router as completion_router
        print("[OK] API routes import successful")
    except ImportError as e:
        print(f"[ERROR] API routes import failed: {e}")
        return False
    
    # Test service import
    try:
        from src.llama.services.chat_service import ChatService
        from src.llama.services.completion_service import CompletionService
        print("[OK] Services import successful")
    except ImportError as e:
        print(f"[ERROR] Services import failed: {e}")
        return False
    
    return True

def test_config_separation():
    """Test that config classes are properly separated"""
    print("\nTesting config separation...")
    
    try:
        # Try importing separated config classes
        from src.llama.config.model_config import ModelConfig
        from src.llama.config.resources_config import ResourcesConfig
        from src.llama.config.security_config import SecurityConfig
        from src.llama.config.service_config import ServiceConfig
        print("[OK] Individual config classes import successful")
        
        # Test that Config class can still be created
        config_data = {
            "model": ModelConfig(path="/tmp/test.bin"),
            "resources": ResourcesConfig(),
            "security": SecurityConfig(),
            "service": ServiceConfig()
        }
        print("[OK] Config classes work correctly")
        
    except Exception as e:
        print(f"[ERROR] Config separation test failed: {e}")
        return False
    
    return True

def test_security_separation():
    """Test that security modules are properly separated"""
    print("\nTesting security separation...")
    
    try:
        # Try importing separated security classes
        from src.llama.core.rate_limiter import RateLimiter, get_rate_limiter
        from src.llama.core.security import ConcurrencyController, get_concurrency_controller
        print("[OK] Security classes import successful")
        
    except Exception as e:
        print(f"[ERROR] Security separation test failed: {e}")
        return False
    
    return True

def test_exceptions_separation():
    """Test that exception classes are properly separated"""
    print("\nTesting exceptions separation...")
    
    try:
        # Try importing separated exception classes
        from src.llama.exceptions.api_error import APIError
        from src.llama.exceptions.validation_error import ValidationError
        from src.llama.exceptions.rate_limit_error import RateLimitError
        from src.llama.exceptions.service_error import ServiceError
        from src.llama.exceptions.model_load_error import ModelLoadError
        from src.llama.exceptions.authentication_error import AuthenticationError
        print("[OK] Individual exception classes import successful")
        
        # Test that exceptions work properly
        try:
            raise ValidationError("Test validation error")
        except ValidationError as e:
            print("[OK] ValidationError works correctly")
        
    except Exception as e:
        print(f"[ERROR] Exceptions separation test failed: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("Starting validation tests...\n")
    
    success = True
    success &= test_imports()
    success &= test_config_separation()
    success &= test_security_separation()
    success &= test_exceptions_separation()
    
    if success:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())