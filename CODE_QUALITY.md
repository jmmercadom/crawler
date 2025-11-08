# Code Quality Guide

This project uses automated tools to maintain code consistency, catch issues early, and ensure type safety.

## Tools Overview

### Ruff (Linter and Formatter)
- **Purpose**: Provides fast Python linting and code formatting
- **Version**: 0.14.4+
- **Configuration**: Configured in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.format]`
- **Note**: Ruff replaces both Black (formatting) and Flake8 (linting) while maintaining compatibility with Black's style

### MyPy (Type Checker)
- **Purpose**: Static type checking for Python code
- **Version**: 1.5.0+
- **Configuration**: Default settings (can be customized in `pyproject.toml`)

## Setup

### Installation
```bash
# Install development dependencies
uv sync --extra dev
```

### Usage
```bash
# Format all Python files
uv run ruff format .

# Check formatting without modifying files
uv run ruff format --check .

# Lint all Python files
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix

# Type check all Python files
uv run mypy .

# Type check specific file
uv run mypy path/to/file.py
```

## Best Practices

1. **Run tools frequently**: Don't wait until the end to check formatting/linting
2. **Fix issues incrementally**: Address each tool's output before moving to the next
3. **Use IDE integration**: Real-time feedback is more efficient than batch processing
4. **Document exceptions**: If you need to ignore specific rules, document why

## Troubleshooting

### Ruff not found
```bash
# Ensure dev dependencies are installed
uv sync --extra dev

# Verify installation
uv run ruff --version
```

### MyPy type errors
1. Add type hints to function signatures
2. Use `typing` module for complex types
3. Add `# type: ignore` comments for unavoidable issues
4. Consider using stubs for external libraries
