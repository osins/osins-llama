---
name: "osins-llama"
description: "Development assistant for osins-llama project. Invoke when working on this LLM API server codebase, writing new features, fixing bugs, or understanding project architecture."
---

# osins-llama Development Assistant

This skill provides context-aware assistance for developing the osins-llama project - a production-ready, OpenAI-compatible API server for LLM models using llama.cpp.

## Project Context

**Environment:**
- Windows 11
- CUDA 12.5
- RTX 3060 12GB
- Python 3.11+
- llama-cpp-python

**Tech Stack:**
- FastAPI for API server
- llama.cpp for LLM inference
- Click for CLI
- pytest for testing

## Project Structure

```
osins-llama/
├── src/llama/
│   ├── api/           # API routes and controllers
│   ├── cli/           # CLI commands (start, stop, restart, status)
│   ├── config/        # Configuration management
│   ├── core/          # Core business logic
│   │   └── commands/  # CLI command implementations
│   ├── exceptions/    # Custom exceptions
│   ├── middlewares/   # Request/response middleware
│   ├── models/        # Data models (chat, legacy, common)
│   ├── services/      # Business services
│   └── utils/         # Utility functions
├── tests/             # Test suite (unit, integration, performance, security)
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

## Development Rules (MUST FOLLOW)

### Code Style (PEP 8)
- Module names: lowercase with underscores (`completion_request.py`)
- Class names: PascalCase (`CompletionRequest`)
- Functions/variables: snake_case (`create_completion`)
- Constants: UPPER_SNAKE_CASE (`DEFAULT_PORT = 31301`)
- 4 spaces indentation, max 79 characters per line

### Control Flow (STRICT)
- **NO `else` statements** - use Early Return pattern
- **NO ternary expressions**
- All branches must use Early Return
- All exceptions must use Guard Clauses
- Function nesting depth <= 2 layers
- **One class or function per file** - strictly enforced

### Type Annotations (PEP 484 + PEP 526)
- All functions must have complete type annotations
- All variables should have type annotations where appropriate
- Must pass `mypy --strict`

### Documentation (PEP 257)
- Module-level docstrings required
- Class-level docstrings required
- Function-level docstrings with Args, Returns, Raises sections

### API Compatibility
- **Strict OpenAI API compatibility** - response fields must match exactly
- No custom response data structures
- Use appropriate HTTP status codes

### Testing Requirements
- Test coverage >= 90%
- Use pytest framework
- Follow unit test specification: `docs/20260210-unit-test-specification.md`
- Test categories: normal path, boundary conditions, exception path, null values, concurrency

### Security
- No hardcoded secrets
- No `eval()` or `exec()`
- File operations must limit path scope
- Network requests must have timeouts
- No global mutable state

### Logging
- Use `logging` module
- NO `print` statements
- No sensitive information in logs
- Distinguish log levels appropriately

## CLI Commands

```bash
llama start -p 31301 -m /path/to/model.gguf  # Start server
llama restart                                 # Restart server
llama down                                    # Stop server
llama status                                  # Check status
llama --help                                  # Show help
```

## Testing Commands

```bash
pytest                          # Run all tests
pytest --cov=src --cov-report=html  # With coverage
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests
pytest tests/security/          # Security tests
```

## Key Files to Reference

- Development specification: `docs/2026021001-development-specification.md`
- Code style guide: `docs/20060216-python-code-style-guide.md`
- Unit test spec: `docs/20260210-unit-test-specification.md`
- API design docs: `docs/20260210-api/`

## Terminology

- "AI Model" or "LLM" - refers to language models
- "Domain Model" - refers to business logic entities
- "Data Model" - refers to data structure definitions
- Avoid standalone "Model" to prevent confusion

## When This Skill Helps

1. Writing new features for the LLM API server
2. Fixing bugs in existing code
3. Understanding project architecture
4. Writing tests that meet coverage requirements
5. Ensuring code follows project conventions
6. Working with CLI commands
7. Implementing OpenAI-compatible endpoints
