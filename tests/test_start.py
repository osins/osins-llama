import sys
import os
# 添加src目录到Python路径，以便能够导入llama模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import json
import os
from llama.core.commands.start import start_command


@pytest.fixture
def runner():
    return CliRunner()


@patch.dict('sys.modules', {'llama_cpp': MagicMock()})
@patch('llama_cpp.Llama')
def test_start_command_success(mock_llama_class, runner, tmp_path):
    """Test that start command works correctly with a valid model."""
    import llama_cpp
    from llama_cpp import Llama
    
    # Create a mock model file
    model_file = tmp_path / "test_model.gguf"
    model_file.write_text("fake model content")
    
    # Mock the Llama instance
    mock_llama_instance = MagicMock()
    mock_llama_class.return_value = mock_llama_instance
    
    # Run the command
    result = runner.invoke(start_command, ['-p', '31301', '-m', str(model_file)])
    
    # Assertions
    assert result.exit_code == 0
    assert "Starting LLM service on port 31301" in result.output
    assert "LLM service started successfully on port 31301" in result.output
    
    # Check that server_info.json was created
    assert os.path.exists('server_info.json')
    
    # Verify the content of server_info.json
    with open('server_info.json', 'r') as f:
        server_info = json.load(f)
        assert server_info['port'] == 31301
        assert server_info['model'] == str(model_file.absolute())


def test_start_command_invalid_model(runner):
    """Test that start command fails with invalid model."""
    result = runner.invoke(start_command, ['-p', '31301', '-m', 'nonexistent_model.gguf'])
    
    assert result.exit_code != 0
    assert "Error: Model file does not exist:" in result.output


def test_start_command_llama_import_error(runner, tmp_path):
    """Test that start command handles import errors."""
    # Create a mock model file
    model_file = tmp_path / "test_model.gguf"
    model_file.write_text("fake model content")

    # Since llama-cpp-python is installed, we'll test with a fake import error
    # by temporarily replacing the Llama class with one that raises ImportError
    import llama_cpp
    original_Llama = llama_cpp.Llama
    
    # Replace with a class that raises ImportError when instantiated
    class ImportErrorLlama:
        def __init__(self, *args, **kwargs):
            raise ImportError("No module named 'llama_cpp'")
    
    llama_cpp.Llama = ImportErrorLlama
    
    try:
        result = runner.invoke(start_command, ['-p', '31301', '-m', str(model_file)])
        assert result.exit_code != 0
        assert "Error: llama-cpp-python is not installed." in result.output
    finally:
        # Restore the original Llama class
        llama_cpp.Llama = original_Llama