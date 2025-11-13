# Testing Guide

Run tests with pytest using uv:

```bash
# Install test dependencies
uv sync --extra test

# All tests
uv run pytest

# By type
uv run pytest -m unit          # Unit tests
uv run pytest -m integration   # Integration tests
uv run pytest -m e2e          # End-to-end tests

# Specific files
uv run pytest tests/unit/
uv run pytest tests/integration/test_services.py

# With coverage
uv run pytest --cov --cov-report=html
# View: open htmlcov/index.html
```

## Test Structure

- **Unit tests** (`tests/unit/`) - Test individual components in isolation
- **Integration tests** (`tests/integration/`) - Test component interactions
- **E2E tests** (`tests/e2e/`) - Test complete CLI workflows

## Fixtures

Test data is in `tests/fixtures/`:
- `html/` - Input HTML files
- `expected/` - Expected JSON outputs

Use helper functions to load fixtures:
```python
from tests.helpers.fixtures import load_html_fixture, load_expected_json
```

## Writing Tests

```python
import pytest

class TestComponent:
    @pytest.mark.unit  # or integration/e2e
    def test_specific_behavior(self):
        # Arrange
        component = Component()

        # Act
        result = component.method()

        # Assert
        assert result == expected
```

## Configuration

Test settings are in `pyproject.toml` under `[tool.pytest.ini_options]`. Test dependencies are managed by uv.

## Code Quality Checks

Before submitting code or creating pull requests, ensure code quality checks pass:

### Option 1: Run All Checks at Once

The easiest way to run all quality checks is with the `check-all` command:

```bash
# Install all required dependencies (test + dev)
uv sync --extra test --extra dev

# Run all quality checks (tests, linting, formatting, type checking)
uv run check-all
```

This command runs:
- **Tests with coverage**: `uv run pytest --cov`
- **Linting**: `uv run ruff check .`
- **Formatting verification**: `uv run ruff format --check .`
- **Type checking**: `uv run mypy .`

The `check-all` script provides detailed output for each check and will exit with an error code if any check fails.

### Option 2: Run Checks Individually

```bash
# Install development dependencies
uv sync --extra dev

# Format code with Ruff
uv run ruff format .

# Lint code with Ruff
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Type check with MyPy
uv run mypy .
```

These checks help maintain consistent code style and catch potential issues early. Ruff provides both linting and formatting while maintaining compatibility with Black's style guide.

## Best Practices

- Use descriptive test names
- Add docstrings explaining what is tested
- Use fixtures from `conftest.py`
- Test edge cases and error conditions
- Keep tests isolated and independent
- Run code quality checks before committing changes