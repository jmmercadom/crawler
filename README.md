# Gaceta Oficial Crawler

Extract edition data from Gaceta Oficial HTML index files and output as JSON.

## Installation

```bash
uv sync
```

## Usage

```bash
python extract_editions.py -in samples/index-2025-11-07.html
```

Options:
- `-in` - Input HTML file (required)
- `-out` - Output JSON file (optional, defaults to `output/index-{date}-editions.json`)

### Environment Variables

**Logging:**
- `LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**OpenTelemetry:**
- `OTEL_SERVICE_NAME` - Service name for traces (default: `gaceta-crawler`)
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTLP endpoint URL (default: `http://localhost:4318`)
- `OTEL_TRACES_ENABLED` - Enable/disable tracing (default: `true`)

Example with OpenTelemetry enabled:

```bash
export OTEL_SERVICE_NAME=gaceta-crawler
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export LOG_LEVEL=INFO
python extract_editions.py -in samples/index-2025-11-07.html
```

Example with OpenTelemetry disabled:

```bash
export OTEL_TRACES_ENABLED=false
python extract_editions.py -in samples/index-2025-11-07.html
```

## OpenTelemetry Integration

This crawler includes OpenTelemetry instrumentation for distributed tracing. Traces provide visibility into:
- Overall execution time
- File reading performance
- HTML parsing duration
- Individual edition extraction
- JSON output generation

### Setting up a Trace Collector

To view traces, you need an OTLP-compatible collector. Here are some options:

**Option 1: Jaeger (Quick Start)**

```bash
docker run -d --name jaeger \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

Then access the Jaeger UI at `http://localhost:16686`

**Option 2: Grafana Tempo**

```bash
docker run -d --name tempo \
  -p 4318:4318 \
  grafana/tempo:latest
```

**Option 3: Disable Tracing**

If you don't need tracing, simply disable it:

```bash
export OTEL_TRACES_ENABLED=false
```

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
