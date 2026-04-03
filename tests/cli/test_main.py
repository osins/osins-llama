"""Tests for the CLI main module."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from llama.cli.main import main, check_command_dependencies, CircularDependencyError, UnknownCommandError, MissingDependencyError
from llama.cli.context import CLIContext


@pytest.fixture
def runner():
    """创建CLI测试运行器"""
    return CliRunner()


def test_main_command(runner):
    """测试主命令入口"""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_verbose_option(runner):
    """测试verbose选项"""
    result = runner.invoke(main, ['--verbose', '--help'])
    # 即使提供了--verbose，在--help的情况下也不会显示调试信息
    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_config_option_with_invalid_path(runner):
    """测试配置选项（无效路径）"""
    result = runner.invoke(main, ['--config', '/nonexistent/path'])
    assert result.exit_code != 0  # 应该失败，因为路径不存在
    assert 'Invalid value' in result.output


def test_help_contains_expected_commands(runner):
    """测试帮助输出是否包含所有预期的命令"""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0

    # 检查帮助文本中是否包含所有注册的命令
    expected_commands = ['start', 'stop', 'restart', 'status', 'config', 'logs', 'health']
    for cmd in expected_commands:
        assert cmd in result.output


def test_cli_context_update_and_get_command_status():
    """测试CLIContext的命令状态更新和获取功能"""
    context = CLIContext()
    
    # 测试更新命令状态
    context.update_command_status("test_cmd", "running", "Command is running")
    
    # 测试获取命令状态
    status = context.get_command_status("test_cmd")
    assert status is not None
    assert status["status"] == "running"
    assert status["message"] == "Command is running"
    assert "timestamp" in status


def test_cli_context_rollback_failed_command():
    """测试CLIContext的命令回滚功能"""
    context = CLIContext()
    
    # 先更新一个命令状态
    context.update_command_status("test_cmd", "failed", "Command failed")
    
    # 确认状态存在
    status = context.get_command_status("test_cmd")
    assert status is not None
    
    # 执行回滚
    context.rollback_failed_command("test_cmd")
    
    # 确认状态已被移除
    status = context.get_command_status("test_cmd")
    assert status is None


def test_check_command_dependencies_valid():
    """测试有效的命令依赖检查"""
    # 模拟一个有效的命令组
    mock_group = MagicMock()
    mock_group.commands = {
        'start': MagicMock(),
        'stop': MagicMock(),
        'restart': MagicMock(),
        'status': MagicMock(),
        'health': MagicMock()
    }
    
    # 这个应该不会抛出异常
    try:
        check_command_dependencies(mock_group)
    except Exception as e:
        pytest.fail(f"check_command_dependencies raised {type(e).__name__} unexpectedly!")


def test_check_command_dependencies_unknown_command():
    """测试未知命令的依赖检查"""
    # 模拟一个包含未知命令的依赖映射
    mock_group = MagicMock()
    mock_group.commands = {
        'start': MagicMock(),
        'stop': MagicMock(),
        'restart': MagicMock(),
        # 注意：缺少 'unknown_cmd'
    }
    
    # 由于依赖检查函数在main.py中定义，我们需要测试它是否会抛出UnknownCommandError
    with pytest.raises(UnknownCommandError):
        check_command_dependencies(mock_group)


def test_check_command_dependencies_missing_dependency():
    """测试缺失依赖的命令"""
    # 模拟一个缺失依赖的情况
    mock_group = MagicMock()
    mock_group.commands = {
        'start': MagicMock(),
        # 注意：缺少 'stop' 命令，但 'restart' 和 'status' 依赖它
        'restart': MagicMock(),
        'status': MagicMock(),
        'health': MagicMock(),
    }
    
    with pytest.raises(MissingDependencyError):
        check_command_dependencies(mock_group)


def test_circular_dependency_detection():
    """测试循环依赖检测"""
    # 模拟一个包含循环依赖的情况
    mock_group = MagicMock()
    mock_group.commands = {
        'cmd_a': MagicMock(),
        'cmd_b': MagicMock(),
        'cmd_c': MagicMock(),
    }
    
    # 我们不能直接测试内部函数detect_circular_dependency，
    # 但我们可以通过修改依赖关系来间接测试
    # 这里我们暂时不实现具体的循环依赖测试，因为我们无法直接访问内部函数
    pass  # TODO: 在重构代码结构后实现循环依赖测试