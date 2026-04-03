"""Tests for the CLI start command security features."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, mock_open
import os
import stat
from pathlib import Path

from llama.cli.start import start, secure_open_model, validate_host, parse_api_keys, validate_and_check_pid_file


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@patch('os.open')
@patch('os.fstat')
@patch('os.getuid')
def test_secure_open_model_valid(mock_getuid, mock_fstat, mock_open_fd):
    """Test secure_open_model with valid parameters."""
    # Mock the required functions
    mock_open_fd.return_value = 123
    mock_getuid.return_value = 1000
    
    # Create a mock stat result
    mock_st = MagicMock()
    mock_st.st_mode = stat.S_IFREG | 0o600  # Regular file with rw------- permissions
    mock_st.st_uid = 1000
    mock_st.st_nlink = 1
    mock_st.st_size = 1024
    mock_fstat.return_value = mock_st
    
    # Test the function
    fd, st = secure_open_model(Path('/valid/model/path.gguf'))
    
    # Verify the results
    assert fd == 123
    assert st == mock_st
    mock_open_fd.assert_called_once()
    mock_fstat.assert_called_once_with(123)


@patch('os.open')
def test_secure_open_model_invalid_file_type(mock_open_fd):
    """Test secure_open_model with invalid file type."""
    # Mock to simulate opening a directory
    mock_open_fd.side_effect = OSError("Not a regular file")
    
    with pytest.raises(Exception):
        secure_open_model(Path('/invalid/directory'))


@patch('os.open')
@patch('os.fstat')
@patch('os.getuid')
def test_secure_open_model_world_writable(mock_getuid, mock_fstat, mock_open_fd):
    """Test secure_open_model with world-writable file."""
    # Mock the required functions
    mock_open_fd.return_value = 123
    mock_getuid.return_value = 1000
    
    # Create a mock stat result with world-writable permissions
    mock_st = MagicMock()
    mock_st.st_mode = stat.S_IFREG | 0o666  # Regular file with rw-rw-rw- permissions
    mock_st.st_uid = 1000
    mock_st.st_nlink = 1
    mock_st.st_size = 1024
    mock_fstat.return_value = mock_st
    
    with pytest.raises(Exception):
        secure_open_model(Path('/world/writable/model.gguf'))


def test_validate_host_valid_ipv4():
    """Test validate_host with valid IPv4 address."""
    assert validate_host(None, None, '192.168.1.1') == '192.168.1.1'


def test_validate_host_valid_ipv6():
    """Test validate_host with valid IPv6 address."""
    assert validate_host(None, None, '2001:0db8:85a3:0000:0000:8a2e:0370:7334') == '2001:0db8:85a3:0000:0000:8a2e:0370:7334'


def test_validate_host_valid_hostname():
    """Test validate_host with valid hostname."""
    assert validate_host(None, None, 'example.com') == 'example.com'


def test_validate_host_invalid_format():
    """Test validate_host with invalid format."""
    with pytest.raises(Exception):
        validate_host(None, None, 'invalid-ip-format')


def test_parse_api_keys_valid():
    """Test parse_api_keys with valid keys."""
    keys = parse_api_keys('key123456789012345,keyabcdefghijklmnop')
    assert len(keys) == 2
    assert keys[0] == 'key123456789012345'
    assert keys[1] == 'keyabcdefghijklmnop'


def test_parse_api_keys_invalid_format():
    """Test parse_api_keys with invalid key format."""
    with pytest.raises(Exception):
        parse_api_keys('invalid_key,validkey123456789012345')


def test_parse_api_keys_duplicate():
    """Test parse_api_keys with duplicate keys."""
    keys = parse_api_keys('key123456789012345,key123456789012345,keyabcdefghijklmnop')
    assert len(keys) == 2  # Duplicates should be removed


@patch('os.open')
@patch('os.fstat')
@patch('os.kill')
def test_validate_and_check_pid_file_not_exists(mock_kill, mock_fstat, mock_open_fd):
    """Test validate_and_check_pid_file when PID file does not exist."""
    # Mock to simulate file not found
    mock_open_fd.side_effect = FileNotFoundError
    
    # This should not raise an exception
    validate_and_check_pid_file(Path('/nonexistent/pid/file.pid'))


@patch('os.open')
@patch('os.fdopen')
@patch('os.fstat')
@patch('os.kill')
def test_validate_and_check_pid_file_process_not_running(mock_kill, mock_fstat, mock_fdopen, mock_open_fd):
    """Test validate_and_check_pid_file when process is not running."""
    # Mock the required functions
    mock_open_fd.return_value = 123
    mock_file = MagicMock()
    mock_file.read.return_value = '1234'
    mock_fdopen.return_value.__enter__.return_value = mock_file
    
    # Mock kill to raise ESRCH (process not found)
    mock_kill.side_effect = OSError(3, "No such process")
    
    # Mock stat functions
    mock_st = MagicMock()
    mock_st.st_ino = 12345
    mock_fstat.return_value = mock_st
    
    with patch('os.stat') as mock_stat:
        mock_stat.return_value.st_ino = 12345
        with patch('os.unlink') as mock_unlink:
            # This should not raise an exception and should clean up the stale PID file
            validate_and_check_pid_file(Path('/path/to/pid/file.pid'))
            mock_unlink.assert_called_once()


@patch('os.open')
@patch('os.fdopen')
@patch('os.fstat')
@patch('os.kill')
def test_validate_and_check_pid_file_process_running(mock_kill, mock_fstat, mock_fdopen, mock_open_fd):
    """Test validate_and_check_pid_file when process is already running."""
    # Mock the required functions
    mock_open_fd.return_value = 123
    mock_file = MagicMock()
    mock_file.read.return_value = '1234'
    mock_fdopen.return_value.__enter__.return_value = mock_file
    
    # Mock kill to not raise an exception (process is running)
    mock_kill.return_value = None
    
    # This should raise an exception
    with pytest.raises(Exception):
        validate_and_check_pid_file(Path('/path/to/pid/file.pid'))


@patch('src.llama.cli.start.ProcessManager')
@patch('src.llama.cli.start.ConfigManager')
@patch('src.llama.cli.start.secure_open_model')
@patch('src.llama.cli.start.validate_and_check_pid_file')
@patch('src.llama.cli.start.create_pid_file_secure')
def test_start_command_success(
    mock_create_pid,
    mock_validate_pid,
    mock_secure_open,
    mock_config_manager,
    mock_process_manager,
    runner
):
    """Test start command with successful execution."""
    # Mock the required functions
    mock_secure_open.return_value = (123, MagicMock())
    
    mock_config = MagicMock()
    mock_config.host = '127.0.0.1'
    mock_config.port = 31301
    mock_config.model_path = Path('/valid/model/path.gguf')
    
    mock_config_instance = MagicMock()
    mock_config_instance.load.return_value = mock_config
    mock_config_manager.return_value = mock_config_instance
    
    mock_process_instance = MagicMock()
    mock_process_manager.return_value = mock_process_instance
    
    # Run the command
    result = runner.invoke(start, [
        '--model-path', '/valid/model/path.gguf',
        '--host', '127.0.0.1',
        '--port', '31301'
    ])
    
    # Verify the results
    assert result.exit_code == 0
    assert 'Server started successfully' in result.output


@patch('src.llama.cli.start.secure_open_model')
def test_start_command_invalid_model_path(mock_secure_open, runner):
    """Test start command with invalid model path."""
    # Mock secure_open_model to raise an exception
    mock_secure_open.side_effect = Exception("Invalid model path")
    
    # Run the command
    result = runner.invoke(start, [
        '--model-path', '/invalid/model/path.gguf',
        '--host', '127.0.0.1',
        '--port', '31301'
    ])
    
    # Verify the results
    assert result.exit_code != 0
    assert 'Invalid model path' in result.output


@patch('src.llama.cli.start.secure_open_model')
@patch('src.llama.cli.start.validate_and_check_pid_file')
def test_start_command_invalid_host(mock_validate_pid, mock_secure_open, runner):
    """Test start command with invalid host."""
    # Run the command with invalid host
    result = runner.invoke(start, [
        '--model-path', '/valid/model/path.gguf',
        '--host', 'invalid-host',
        '--port', '31301'
    ])
    
    # Verify the results
    assert result.exit_code != 0
    assert 'Invalid value' in result.output
    assert 'host' in result.output
