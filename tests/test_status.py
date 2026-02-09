import sys
import os
# 添加src目录到Python路径，以便能够导入llama模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from click.testing import CliRunner
import json
import os
from llama.core.commands.status import status_command


@pytest.fixture
def runner():
    return CliRunner()


def test_status_command_not_running(runner):
    """Test that status command handles case when service is not running."""
    # Ensure server_info.json doesn't exist
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')
    
    result = runner.invoke(status_command)
    
    assert result.exit_code == 0  # Not an error, just informational
    assert "LLM service is not currently running." in result.output


def test_status_command_success(runner):
    """Test that status command works when service is running."""
    # Create server_info.json to simulate running service
    server_info = {
        'port': 31301,
        'model': './test_model.gguf',
        'pid': 12345
    }
    
    with open('server_info.json', 'w') as f:
        json.dump(server_info, f)
    
    result = runner.invoke(status_command)
    
    assert result.exit_code == 0
    assert "LLM service is running:" in result.output
    assert "Port: 31301" in result.output
    assert "Model: test_model.gguf" in result.output
    assert "PID: 12345" in result.output
    
    # Cleanup
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')


def test_status_command_corrupted_server_info(runner):
    """Test that status command handles corrupted server info file."""
    # Create a corrupted server_info.json
    with open('server_info.json', 'w') as f:
        f.write("invalid json content")
    
    result = runner.invoke(status_command)
    
    assert result.exit_code == 0  # Not an error, just informational
    assert "Server information file is corrupted." in result.output
    
    # Cleanup
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')