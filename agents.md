# Llama CLI Project - Agents Guide

## Project Overview
A CLI tool for managing and running LLM models with llama_cpp. Provides commands to start, stop, restart, and monitor LLM server instances.

## Build/Lint/Test Commands

### Environment Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a single test file
pytest tests/cli/test_start.py

# Run a single test function
pytest tests/cli/test_start.py::test_validate_host_valid_ipv4

# Run tests with coverage
pytest --cov=llama --cov-report=term-missing

# Run specific test directories
pytest tests/unit/
pytest tests/integration/
pytest tests/cli/
```

### Linting & Type Checking
```bash
# Run flake8 linter
flake8 src/ tests/

# Run mypy type checker
mypy src/llama/

# Format code with black
black src/ tests/

# Check formatting without changes
black --check src/ tests/
```

### Build & Install
```bash
pip install -e .
pip install -e ".[dev]"
pip install build
python -m build
```

## Project Structure
```
src/llama/
├── api/           # API server implementation
├── cli/           # CLI commands (start, stop, restart, status, etc.)
├── config/        # Configuration management
├── core/          # Core business logic
├── exceptions/    # Custom exception classes (one per file)
├── middlewares/   # FastAPI middlewares
├── models/        # Data models (dataclasses)
└── utils/         # Utility functions
tests/
├── cli/           # CLI command tests
├── unit/          # Unit tests
├── integration/   # Integration tests
└── conftest.py    # Shared pytest fixtures
```

## Code Style Guidelines

### Imports
```python
# Standard library first (alphabetical)
import os
import sys
from pathlib import Path
from typing import Optional, List

# Third-party imports next
import click
import pytest

# Local imports last (relative imports for internal modules)
from ..config.config_manager import ConfigManager
from .process import ProcessManager
```

### Type Annotations
- All functions MUST have type annotations (enforced by mypy strict mode)
- Use `Optional[T]` for nullable parameters/returns
- Use `List[T]`, `Dict[K, V]` from typing module (Python 3.8 compatibility)
- Dataclasses should use `Optional[T] = None` for optional fields

```python
def validate_host(ctx, param, value) -> str:
    ...

def parse_api_keys(value: Optional[str]) -> Optional[List[str]]:
    ...
```

### Naming Conventions
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions: prefix with underscore `_private_function`
- CLI command functions: lowercase command name (e.g., `start`, `stop`)
- Exception classes: suffix with `Error` (e.g., `APIError`, `ValidationError`)

### Docstrings
- Use triple double quotes for docstrings
- Include description, Args, and Returns sections for complex functions
- Simple functions can have single-line docstrings

```python
def wait_for_port(host: str, port: int, timeout: float = 30.0) -> bool:
    """
    Wait for port to be ready for listening.
    
    Args:
        host: Host address
        port: Port number
        timeout: Timeout in seconds
    
    Returns:
        bool: True if port is ready within timeout, False otherwise
    """
```

### Error Handling
- Use custom exceptions from `src/llama/exceptions/`
- One exception class per file
- Raise specific exceptions, not generic `Exception`
- Use `click.BadParameter` for CLI validation errors
- Use `click.ClickException` for CLI runtime errors
- Always clean up resources in `finally` blocks

```python
from ..exceptions import ValidationError, APIError

def validate_input(value: str) -> str:
    if not value:
        raise ValidationError("Value cannot be empty")
    return value
```

### CLI Commands
- Use Click decorators for command definition
- Use `@click.pass_context` for commands that need context
- Validate inputs early with callbacks
- Provide helpful error messages

```python
@click.command()
@click.option('-p', '--port', type=click.IntRange(1024, 65535), default=31301)
@click.pass_context
def start(ctx, port: int) -> None:
    """Start the LLM server."""
    ...
```

### Data Models
- Use `@dataclass` decorator for data models
- Place all model classes in `src/llama/models/`
- Use `Optional[T] = None` for optional fields

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PidData:
    model_path: Optional[str] = None
    port: Optional[int] = None
```

### Testing
- Test file naming: `test_<module_name>.py`
- Test function naming: `test_<function_name>_<scenario>`
- Use `pytest.fixture` for shared setup
- Use `unittest.mock.patch` for mocking
- Group related tests in test classes when appropriate

```python
@pytest.fixture
def runner():
    return CliRunner()

def test_validate_host_valid_ipv4():
    assert validate_host(None, None, '192.168.1.1') == '192.168.1.1'

@patch('os.open')
def test_secure_open_model_invalid(mock_open_fd):
    with pytest.raises(Exception):
        secure_open_model(Path('/invalid'))
```

### Code Formatting
- Max line length: 88 characters (Black default)
- Use 4 spaces for indentation
- No tabs
- Blank line between functions/classes
- Trailing commas in multi-line structures

### Security Considerations
- Validate all user inputs
- Use secure file operations (check ownership, permissions)
- Avoid TOCTOU race conditions
- Sanitize paths before file operations
- Never expose sensitive data in logs

### Platform Compatibility
- Handle Windows/Unix differences with `sys.platform` checks
- Use `hasattr(os, 'O_NOFOLLOW')` for Unix-specific flags
- Prefer `pathlib.Path` over string paths

## CLI Commands Reference
```bash
llama start -m <model_path> -p 31301  # Start LLM server
llama stop                            # Stop LLM server
llama restart                         # Restart LLM server
llama status                          # Check server status
llama health                          # Health check
llama logs                            # View logs
llama config                          # Configuration management
llama --help                          # Show help
```
