import sys
import os
# 添加src目录到Python路径，以便能够导入llama模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from click.testing import CliRunner
from llama.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    """Test that the CLI shows help."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Llama CLI - A tool for managing and running LLM models with llama_cpp.' in result.output
    assert 'start' in result.output
    assert 'restart' in result.output
    assert 'down' in result.output
    assert 'status' in result.output