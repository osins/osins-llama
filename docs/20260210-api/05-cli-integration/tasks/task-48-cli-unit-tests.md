# CLI单元测试实现

## 概述

CLI单元测试用于验证CLI各个组件的功能正确性，确保代码质量。

## 实现要求

1. 实现CLI各组件的单元测试
2. 覆盖所有主要功能点
3. 包含边界条件测试
4. 包含异常路径测试
5. 达到90%以上代码覆盖率

## 代码实现

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
    assert "does not exist" in errors[0]


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

## 验证标准

- [ ] 单元测试覆盖所有主要功能点
- [ ] 边界条件测试包含
- [ ] 异常路径测试包含
- [ ] 代码覆盖率≥90%
- [ ] 测试用例设计合理
- [ ] 代码符合PEP 8规范
- [ ] 类型注解完整

## 安全考虑

- 测试安全相关的功能
- 验证安全机制的有效性
- 测试异常情况下的安全处理

## 版本信息
- 版本: 1.0
- 创建日期: 2026-02-12
- 最后更新: 2026-02-12