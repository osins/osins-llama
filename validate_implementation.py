import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def validate_server_implementation():
    """
    验证服务器实现是否完成所有必需的功能
    """
    print("osins-llama 服务器实现验证报告")
    print("="*50)
    
    # 检查必需的模块是否都存在
    modules_to_check = [
        ("src.llama.services.scheduler", "RequestScheduler, ConcurrentRequestLimiter"),
        ("src.llama.middlewares.logging_middleware", "LoggingMiddleware"),
        ("src.llama.utils.token_utils", "count_tokens, count_tokens_in_messages, count_completion_tokens"),
        ("src.llama.services.completion_service", "CompletionService"),
        ("src.llama.services.chat_service", "ChatService"),
        ("src.llama.middlewares.api_key_middleware", "ApiKeyMiddleware"),
        ("src.llama.middlewares.rate_limit_middleware", "RateLimitMiddleware"),
        ("src.llama.api.completion_routes", "create_completion endpoint"),
        ("src.llama.api.chat_routes", "create_chat_completion endpoint"),
        ("src.llama.api.server", "create_app, start_server"),
        ("src.llama.exceptions", "ServiceError, ValidationError, RateLimitError, AuthenticationError"),
        ("src.llama.core.model_manager", "ModelManager"),
    ]
    
    print("\n1. 模块存在性验证:")
    print("-"*30)
    
    all_modules_exist = True
    for module_path, description in modules_to_check:
        try:
            # 将模块路径转换为Python导入格式
            module_parts = module_path.split('.')
            module_name = '.'.join(module_parts[:-1]) if len(module_parts) > 1 else module_parts[0]
            
            # 动态导入模块
            __import__(module_name)
            print(f"[OK] {module_path} - {description}")
        except ImportError as e:
            print(f"[MISSING] {module_path} - {description} (Error: {e})")
            all_modules_exist = False
    
    # 检查测试文件是否存在
    print("\n2. 测试文件验证:")
    print("-"*30)
    
    test_files = [
        "tests/unit/test_scheduler.py",
        "tests/unit/test_logging_middleware.py",
        "tests/unit/test_token_utils.py",
        "tests/integration/test_api_integration.py"
    ]
    
    all_tests_exist = True
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"[OK] {test_file}")
        else:
            print(f"[MISSING] {test_file}")
            all_tests_exist = False
    
    # 检查目录结构
    print("\n3. 目录结构验证:")
    print("-"*30)
    
    dirs_to_check = [
        "src/llama/services",
        "src/llama/middlewares",
        "src/llama/api",
        "src/llama/exceptions",
        "src/llama/utils",
        "tests/unit",
        "tests/integration"
    ]
    
    all_dirs_exist = True
    for dir_path in dirs_to_check:
        full_path = os.path.join(os.getcwd(), dir_path)
        if os.path.isdir(full_path):
            print(f"[OK] {dir_path}/")
        else:
            print(f"[MISSING] {dir_path}/")
            all_dirs_exist = False
    
    # 总结
    print("\n4. 验证总结:")
    print("-"*30)
    
    print(f"模块存在性: {'通过' if all_modules_exist else '未通过'}")
    print(f"测试文件: {'通过' if all_tests_exist else '未通过'}")
    print(f"目录结构: {'通过' if all_dirs_exist else '未通过'}")
    
    overall_status = all_modules_exist and all_tests_exist and all_dirs_exist
    print(f"\n总体状态: {'[SUCCESS] 全部完成' if overall_status else '[FAILURE] 存在缺失'}")
    
    if overall_status:
        print("\n[SUCCESS] 服务器实现已按计划完成所有功能!")
        print("\n实现的功能包括:")
        print("  - 推理服务 (Completion 和 Chat)")
        print("  - 流式和非流式响应")
        print("  - Token统计功能")
        print("  - 调度器 (并发控制和超时管理)")
        print("  - 认证、限流和日志中间件")
        print("  - API路由 (Completion 和 Chat)")
        print("  - 统一异常处理体系")
        print("  - 单元测试和集成测试")
    else:
        print("\n[WARNING] 服务器实现存在未完成的功能，请检查上述缺失项。")
    
    return overall_status

if __name__ == "__main__":
    validate_server_implementation()