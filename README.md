# Gaceta Oficial Crawler

Extract edition data from Gaceta Oficial HTML index files and output as JSON.

## Installation

```bash
uv sync
```

## Usage

```bash
python main.py -in samples/index-2025-11-07.html
```

Options:
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
