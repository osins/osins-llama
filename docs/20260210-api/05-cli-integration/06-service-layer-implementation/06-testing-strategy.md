# 测试策略

## 概述

测试策略文档定义了CLI服务层的测试方法、覆盖率要求和测试类型。

## 单元测试

针对各个服务组件进行独立测试：

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import socket
from contextlib import contextmanager
import threading
import time
import requests
import signal


def test_command_parser_start_command():
    """测试命令解析器的启动命令解析功能"""
    parser = CommandParser()
    args = {
        'model_path': './test_model.gguf',
        'host': 'localhost',
        'port': '8080',
        'n_ctx': '2048',
        'n_threads': '4',
        'debug': 'true'
    }
    
    params = parser.parse_start_command(args)
    
    assert params.model_path == Path('./test_model.gguf')
    assert params.host == 'localhost'
    assert params.port == 8080
    assert params.n_ctx == 2048
    assert params.n_threads == 4
    assert params.debug is True


def test_command_parser_invalid_port():
    """测试命令解析器对无效端口的处理"""
    parser = CommandParser()
    args = {
        'port': '999999'  # 超出范围的端口
    }
    
    with pytest.raises(ValueError):
        parser.parse_start_command(args)


def test_command_parser_path_traversal():
    """测试命令解析器对路径遍历的检测"""
    parser = CommandParser()
    args = {
        'model_path': '../secret_file.txt'
    }
    
    with pytest.raises(ValueError) as excinfo:
        parser.parse_start_command(args)
    assert "path traversal" in str(excinfo.value)


def test_config_validator_start_config():
    """测试配置验证器的启动配置验证功能"""
    validator = ConfigValidator()
    
    # 创建测试参数
    params = Mock()
    params.model_path = Path('./test_model.gguf')
    params.port = 31301
    params.n_ctx = 2048
    params.n_threads = 8
    params.max_concurrent_requests = 10
    
    errors = validator.validate_start_config(params)
    
    # 模型路径不存在，应该有错误
    assert len(errors) == 1
    assert "does not exist" in errors


def test_security_checker_api_keys_file_large():
    """测试安全检查器对大API密钥文件的检测"""
    checker = SecurityChecker()
    
    # 创建一个大于1MB的大文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        # 写入超过1MB的内容
        for i in range(1024*1024//50):  # 1MB / 50 chars per line
            f.write(f"sk-test{i:010}\n")
        temp_api_file = Path(f.name)
    
    try:
        errors = checker.validate_api_keys_file(temp_api_file)
        # 文件过大，应该有错误
        assert any("too large" in error for error in errors)
    finally:
        temp_api_file.unlink()


def test_security_checker_path_traversal():
    """测试安全检查器对路径遍历的检测"""
    result = SecurityChecker.check_path_traversal("../secret.txt")
    assert result is False
    
    result = SecurityChecker.check_path_traversal("./normal_path.txt")
    assert result is True


@contextmanager
def create_temp_file(content=""):
    """创建临时文件的上下文管理器"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        if content:
            f.write(content)
        temp_path = Path(f.name)
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_log_processor_tail_log_file_missing():
    """测试日志处理器对缺失文件的处理"""
    processor = LogProcessor()
    fake_path = Path("/nonexistent/logfile.log")
    
    result = processor.tail_log_file(fake_path, 10)
    assert "does not exist" in result


def test_config_validator_port_availability():
    """测试配置验证器对端口可用性的检查"""
    # 使用一个临时端口进行测试
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        addr, port = s.getsockname()
    
    is_available = ConfigValidator.validate_server_availability('localhost', port)
    assert is_available is False  # 端口被占用，应该不可用


def test_concurrent_access_to_shared_resource():
    """测试并发访问共享资源的处理"""
    import threading
    import time
    
    # 创建一个临时文件用于测试并发访问
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Initial content\n")
        temp_file = Path(f.name)
    
    try:
        results = []
        
        def write_to_file(thread_id):
            try:
                with open(temp_file, 'a') as f:
                    f.write(f"Content from thread {thread_id}\n")
                results.append(True)
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        # 创建多个线程同时写入文件
        threads = []
        for i in range(5):
            t = threading.Thread(target=write_to_file, args=(i,))
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证所有线程都成功写入
        assert all(isinstance(r, bool) and r for r in results)
        
        # 验证文件内容
        with open(temp_file, 'r') as f:
            content = f.read()
            assert "Initial content" in content
            for i in range(5):
                assert f"Content from thread {i}" in content
                
    finally:
        # 清理临时文件
        temp_file.unlink()


def test_file_permissions_error():
    """测试文件权限错误的处理"""
    if os.name == 'nt':  # Windows系统跳过此测试
        pytest.skip("Skipping permission test on Windows")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # 修改文件权限为只读
        temp_path.chmod(0o444)  # 只读权限
        
        # 尝试写入文件，应该失败
        with pytest.raises(PermissionError):
            with open(temp_path, 'w') as f:
                f.write("test")
    finally:
        # 恢复文件权限并删除
        temp_path.chmod(0o666)
        temp_path.unlink()


def test_network_timeout_error():
    """测试网络超时异常的处理"""
    # 创建一个永远不会响应的服务器
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        addr, port = s.getsockname()
        
        # 在另一个线程中监听，但不响应
        def server_thread():
            s.listen(1)
            conn, addr = s.accept()
            # 不读取数据，模拟挂起
            time.sleep(1)
            conn.close()
        
        thread = threading.Thread(target=server_thread)
        thread.daemon = True
        thread.start()
        
        # 尝试连接，应该超时
        start_time = time.time()
        try:
            response = requests.get(f"http://localhost:{port}", timeout=0.1)
        except requests.Timeout:
            elapsed = time.time() - start_time
            assert elapsed >= 0.1  # 至少等待了超时时间
            assert elapsed < 1.0  # 但没有等待太久
        else:
            pytest.fail("Expected timeout exception")


def test_io_error_handling():
    """测试IO错误的处理"""
    # 创建一个损坏的模型文件
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        # 写入损坏的数据
        f.write(b"corrupted\x00\x01\x02data")
        corrupt_file = Path(f.name)
    
    try:
        # 尝试读取损坏的文件
        with open(corrupt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 某些编码错误可能会被处理
    except UnicodeDecodeError:
        # 这是预期的错误
        pass
    finally:
        corrupt_file.unlink()
```

## 集成测试

测试服务之间的交互：

```python
def test_config_service_integration():
    """测试配置服务的集成"""
    import yaml
    
    # 使用上下文管理器创建临时配置文件
    with create_temp_file() as config_path:
        yaml_content = """
model:
  path: "./test_model.gguf"
  n_ctx: 2048
  n_threads: 4
"""
        config_path.write_text(yaml_content)
        
        # 测试加载配置
        config_service = ConfigService()
        config = config_service.load_config(config_path)
        
        assert config.model.path == Path("./test_model.gguf")
        assert config.model.n_ctx == 2048
        assert config.model.n_threads == 4


def test_command_executor_with_retry():
    """测试带重试的命令执行器"""
    mock_service = Mock()
    
    # 第一次失败，第二次成功
    mock_service.execute.side_effect = [
        CommandResult(success=False, output="", error="First attempt failed", exit_code=1, execution_time=0.1),
        CommandResult(success=True, output="Success", error="", exit_code=0, execution_time=0.1)
    ]
    
    executor = BusinessLogicExecutor(
        command_parser=Mock(),
        log_processor=Mock(),
        config_validator=Mock(),
        status_checker=Mock(),
        security_checker=Mock()
    )
    params = StartParams(model_path=Path("./test_model.gguf"))
    
    result = executor.execute_with_retry(mock_service, params, max_retries=3)
    
    assert result.success
    assert mock_service.execute.call_count == 2  # 调用了两次
```

## 性能/压力测试

```python
def test_performance_under_load():
    """测试高负载下的性能"""
    import time
    
    # 模拟大量并发请求
    start_time = time.time()
    
    # 创建大量线程
    threads = []
    for i in range(100):
        t = threading.Thread(target=lambda: time.sleep(0.01))  # 模拟轻量级操作
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    # 验证在合理时间内完成
    assert total_time < 5.0  # 应该在5秒内完成


def test_memory_usage():
    """测试内存使用情况"""
    import gc
    import tracemalloc
    
    # 开始追踪内存
    tracemalloc.start()
    
    # 执行一些操作
    data = []
    for i in range(1000):
        data.append([j for j in range(100)])
    
    # 获取当前内存快照
    current, peak = tracemalloc.get_traced_memory()
    
    # 停止追踪
    tracemalloc.stop()
    
    # 验证内存使用在合理范围内
    assert current < 100 * 1024 * 1024  # 小于100MB
```

## CI/CD 集成

```python
# 示例：pytest 配置文件 (pytest.ini)
"""
[tool:pytest]
testpaths = tests
addopts = 
    -ra
    -q
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=90
    --maxfail=1
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
"""

# 示例：GitHub Actions 工作流 (.github/workflows/test.yml)
"""
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
"""
```

## 覆盖率要求

- 单元测试覆盖率: ≥90%
- 集成测试覆盖率: ≥80%
- 端到端测试覆盖率: ≥70%

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12