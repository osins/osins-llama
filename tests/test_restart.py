import sys
import os
# 添加src目录到Python路径，以便能够导入llama模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from click.testing import CliRunner
import json
import os
from unittest.mock import patch, MagicMock
from llama.core.commands.restart import restart


@pytest.fixture
def runner():
    return CliRunner()


def test_restart_command_not_running(runner):
    """Test that restart command handles case when service is not running."""
    # Ensure server_info.json doesn't exist
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')
    
    result = runner.invoke(restart_command)
    
    assert result.exit_code == 0  # Not an error, just informational
    assert "LLM service is not currently running." in result.output


@patch.dict('sys.modules', {'llama_cpp': MagicMock()})
@patch('llama_cpp.Llama')
def test_restart_command_success(mock_llama_class, runner, tmp_path):
    """Test that restart command works when service is running."""
    import llama_cpp
    from llama_cpp import Llama
    
    # Create server_info.json to simulate running service
    server_info = {
        'port': 31301,
        'model': str(tmp_path / "test_model.gguf"),
        'pid': 12345
    }
    
    with open('server_info.json', 'w') as f:
        json.dump(server_info, f)
    
    # Create a mock model file
    model_file = tmp_path / "test_model.gguf"
    model_file.write_text("fake model content")
    
    # Mock the Llama instance
    mock_llama_instance = MagicMock()
    mock_llama_class.return_value = mock_llama_instance
    
    result = runner.invoke(restart_command)
    
    assert result.exit_code == 0
    assert "Stopping LLM service on port 31301" in result.output
    assert "LLM service restarted successfully on port 31301" in result.output
    
    # Cleanup
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')


def test_restart_command_corrupted_server_info(runner):
    """Test that restart command handles corrupted server info file."""
    # Create a corrupted server_info.json
    with open('server_info.json', 'w') as f:
        f.write("invalid json content")
    
    result = runner.invoke(restart_command)
    
    assert result.exit_code == 0  # Not an error, just informational
    assert "Server information file is corrupted." in result.output
    
    # Cleanup
    if os.path.exists('server_info.json'):
        os.remove('server_info.json')