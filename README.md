# osins-llama

A production-ready, OpenAI-compatible API server for LLM models using llama.cpp.

## Overview

osins-llama is a production-grade LLM API service that provides OpenAI-compatible endpoints for chat and completion models. Built with FastAPI and llama.cpp, it offers high performance and low resource consumption.

## Features

- ✅ **OpenAI Compatible**: Full compatibility with OpenAI API specification
- 🔐 **Secure**: API key authentication, rate limiting, and concurrency controls
- ⚡ **Fast**: Asynchronous processing with FastAPI
- 📊 **Observable**: Comprehensive logging and monitoring
- 🛡️ **Production Ready**: Hardened security, proper error handling, and configuration validation
- 📁 **Clean Architecture**: Well-separated layers with enforced boundaries

## Project Structure

```
osins-llama/
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── src/                     # Source code
│   └── llama/
│       ├── __init__.py
│       ├── _version.py
│       ├── main.py          # CLI entry point
│       ├── api/             # API routes and controllers
│       ├── config/          # Configuration management
│       ├── core/            # Core business logic
│       │   └── commands/    # CLI commands
│       ├── exceptions/      # Custom exceptions
│       ├── middlewares/     # Request/response middleware
│       ├── models/          # Data models
│       ├── services/        # Business services
│       └── utils/           # Utility functions
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── performance/        # Performance tests
│   ├── concurrency/        # Concurrency tests
│   └── security/           # Security tests
├── pyproject.toml          # Package configuration
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- A compatible GGUF model file

### Quick Start
1. Clone the repository:
```bash
git clone https://github.com/osins-llm/osins-llama.git
cd osins-llama
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

## Configuration

Configure the service using environment variables:

```bash
export LLAMA_MODEL_PATH="/path/to/your/model.gguf"
export LLAMA_API_KEYS="sk-1234567890,sk-0987654321"  # Multiple keys supported
export LLAMA_PORT=31301
export LLAMA_HOST=0.0.0.0
export LLAMA_N_CTX=4096  # Context size
export LLAMA_RATE_LIMIT_REQUESTS=60  # Requests per minute
export LLAMA_MAX_CONCURRENT_REQUESTS=10  # Max concurrent requests
```

## Usage

### CLI Commands

```bash
# Start the LLM service
llama start -p 31301 -m /path/to/model.gguf

# Restart the LLM service
llama restart

# Stop the LLM service
llama down

# Check the status of the LLM service
llama status

# Show help
llama --help
```

### API Usage

The service provides OpenAI-compatible endpoints:

```bash
# Chat completions
curl -X POST http://localhost:31301/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "your-model-name",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# Completions
curl -X POST http://localhost:31301/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "your-model-name",
    "prompt": "Once upon a time"
  }'
```

## Development

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

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

Run specific test suites:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# Security tests
pytest tests/security/
```

### Architecture Validation
Validate the code architecture:
```bash
python scripts/architecture_check.py
```

## Production Deployment

For production deployments, ensure:

1. **Security**: Set strong API keys and enable HTTPS
2. **Resource Limits**: Configure appropriate context sizes and thread counts
3. **Monitoring**: Enable logging and set up monitoring
4. **Environment Variables**: Use secure methods to manage environment variables

## Contributing

Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.