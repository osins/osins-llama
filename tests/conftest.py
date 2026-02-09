import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_server_info():
    """Create a temporary server info file for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    server_info_path = temp_dir / "server_info.json"
    
    # Create sample server info
    import json
    server_info = {
        'port': 31301,
        'model': './test_model.gguf',
        'pid': 12345
    }
    
    with open(server_info_path, 'w') as f:
        json.dump(server_info, f)
    
    yield server_info_path
    
    # Cleanup
    server_info_path.unlink()
    temp_dir.rmdir()