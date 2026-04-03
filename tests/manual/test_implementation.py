import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# 简单测试新创建的模块是否可以导入
def test_imports():
    try:
        from llama.services.scheduler import RequestScheduler, ConcurrentRequestLimiter
        print("[OK] Scheduler module imported successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import scheduler: {e}")
        
    try:
        from llama.middlewares.logging_middleware import LoggingMiddleware
        print("[OK] Logging middleware imported successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import logging middleware: {e}")
        
    try:
        from llama.utils.token_utils import count_tokens, count_tokens_in_messages
        print("[OK] Token utils imported successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import token utils: {e}")

    # 测试token计数功能
    try:
        token_count = count_tokens("Hello, world!")
        print(f"[OK] Token counting works: 'Hello, world!' has {token_count} tokens")
    except Exception as e:
        print(f"[ERROR] Token counting failed: {e}")

    # 测试调度器基本功能
    try:
        import asyncio
        from llama.config.config import Config
        
        async def test_scheduler():
            config = Config.from_env()
            scheduler = RequestScheduler(config)
            print(f"[OK] Scheduler created with max_concurrent={config.service.max_concurrent_requests}")
            
            async def sample_task(x, y):
                return x + y
                
            result = await scheduler.submit_task(sample_task, 2, 3)
            print(f"[OK] Scheduler task execution works: 2 + 3 = {result}")
            
        asyncio.run(test_scheduler())
    except Exception as e:
        print(f"[ERROR] Scheduler test failed: {e}")

if __name__ == "__main__":
    print("Testing module imports and basic functionality...")
    test_imports()
    print("\nAll tests completed.")