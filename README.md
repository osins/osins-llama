# Llama CLI

A command-line interface for managing and running LLM models with llama_cpp.

## Project Structure

This project follows standard Python project layout with the following structure:

```
llama/
├── docs/
├── scripts/
├── src/
│   └── llama/
│       ├── __init__.py
│       ├── _version.py
│       ├── main.py
│       ├── api/
│       ├── config/
│       ├── core/
│       │   └── commands/
│       ├── models/
│       ├── services/
│       └── utils/
├── tests/
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
└── venv/
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llama.git
cd llama
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Usage

```bash
# Start the LLM service
llama start -p 31301 -m ./qwen2.5-7b-instruct-uncensored-q4_k_m.gguf

# Restart the LLM service
llama restart

# Stop the LLM service
llama down

# Check the status of the LLM service
llama status

# Show help
llama --help
```

## Commands

- `start`: Starts the LLM service with the specified port and model
- `restart`: Restarts the LLM service
- `down`: Stops the LLM service
- `status`: Shows the current status of the LLM service

## Development

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the package in development mode:
```bash
pip install -e .
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Testing
Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_start.py
```

Run tests with verbose output:
```bash
pytest -v
```

## Contributing

Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.