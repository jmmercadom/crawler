# Gaceta Oficial Crawler

[![codecov](https://codecov.io/github/jmmercadom/crawler/graph/badge.svg?token=CIJ6ULTG2N)](https://codecov.io/github/jmmercadom/crawler)
[![Test Suite](https://github.com/jmmercadom/crawler/actions/workflows/tests.yml/badge.svg)](https://github.com/jmmercadom/crawler/actions/workflows/tests.yml)

Extract edition data from Gaceta Oficial HTML index files and output as JSON.

## Installation

```bash
uv sync
```

## Usage

```bash
# Extract editions from HTML file
uv run gaceta extract -in samples/index-2025-11-07.html

# Execute URL and detect changes
uv run gaceta execute <url>
```

### Extract Command Options:
- `-in` - Input HTML file (required)
- `-out` - Output JSON file (optional, defaults to `output/<input_filename>-editions.json`)

### Environment Variables

- `LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Optional: OpenTelemetry Integration

This crawler includes optional OpenTelemetry instrumentation for distributed tracing and observability. **The crawler works perfectly fine without it.**

To disable tracing:

```bash
export OTEL_TRACES_ENABLED=false
```

For setup instructions and advanced configuration, see [OPENTELEMETRY.md](OPENTELEMETRY.md)

## Output Format

```json
[
  {
    "number": "1234",
    "type": "Ordinaria",
    "published_date": "2025-11-07",
    "administration": "Gobierno Nacional"
  }
]
```

## Testing

The project includes comprehensive tests covering unit, integration, and end-to-end scenarios. For detailed testing information, see [TESTING.md](TESTING.md).

Quick test commands:
```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=html

# Run specific test types
uv run pytest -m unit        # Unit tests only
uv run pytest -m integration # Integration tests only
uv run pytest -m e2e         # End-to-end tests only
```

### Run All Quality Checks

For a comprehensive check of the entire codebase, use the `check-all` command:

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

The `check-all` command provides clear feedback for each check and will exit with an error code if any check fails.

## Development

### Code Quality
This project uses tools to maintain code consistency and catch issues early:

```bash
# Install development dependencies
uv sync --extra dev

# Format code (Ruff provides both linting and formatting)
uv run ruff format .

# Lint code
uv run ruff check .

# Fix auto-fixable linting issues
uv run ruff check --fix .

# Type check
uv run mypy .
```

For detailed code quality setup and configuration, see [CODE_QUALITY.md](CODE_QUALITY.md).
