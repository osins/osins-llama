import sys
import os
# 添加src目录到Python路径，以便能够导入llama模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from click.testing import CliRunner
import json
import os
from llama.core.commands.down import down_command


@pytest.fixture
def runner():
    return CliRunner()


def test_down_command_not_running(runner):
    """Test that down command handles case when service is not running."""
    # Ensure server_info.json doesn't exist
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')
    
    result = runner.invoke(down_command)
    
    assert result.exit_code == 0  # Not an error, just informational
    assert "LLM service is not currently running." in result.output


def test_down_command_success(runner):
    """Test that down command works when service is running."""
    # Create server_info.json to simulate running service
    server_info = {
        'port': 31301,
        'model': './test_model.gguf',
        'pid': 12345
    }
    
    with open('server_info.json', 'w') as f:
        json.dump(server_info, f)
    
    result = runner.invoke(down_command)
    
    assert result.exit_code == 0
    assert "Stopping LLM service on port 31301" in result.output
    assert "LLM service stopped successfully." in result.output
    
    # Verify that server_info.json was removed
    assert not os.path.exists('server_info.json')


def test_down_command_corrupted_server_info(runner):
    """Test that down command handles corrupted server info file."""
    # Create a corrupted server_info.json
    with open('server_info.json', 'w') as f:
        f.write("invalid json content")
    
    result = runner.invoke(down_command)
    
    assert result.exit_code == 0  # Not an error, just informational
    assert "Server information file is corrupted." in result.output
    
    # Cleanup
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')