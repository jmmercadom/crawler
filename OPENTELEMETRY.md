# OpenTelemetry Integration

This crawler includes optional OpenTelemetry instrumentation for distributed tracing. **The crawler works perfectly fine without OpenTelemetry** - this is purely for observability and debugging purposes.

## What You Get

Traces provide visibility into:
- Overall execution time
- File reading performance
- HTML parsing duration
- Individual edition extraction
- JSON output generation

## Configuration

### Environment Variables

- `OTEL_SERVICE_NAME` - Service name for traces (default: `gaceta-crawler`)
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OTLP endpoint URL (default: `http://localhost:4318`)
- `OTEL_TRACES_ENABLED` - Enable/disable tracing (default: `true`)

### Running with OpenTelemetry Enabled

```bash
export OTEL_SERVICE_NAME=gaceta-crawler
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
uv run gaceta extract -in samples/index-2025-11-07.html
```

### Running with OpenTelemetry Disabled

```bash
export OTEL_TRACES_ENABLED=false
uv run gaceta extract -in samples/index-2025-11-07.html
```

## Setting up a Trace Collector

To view traces, you need an OTLP-compatible collector. Here are some options:

### Option 1: Jaeger (Quick Start)

```bash
docker run -d --name jaeger \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

Then access the Jaeger UI at `http://localhost:16686`

### Option 2: Grafana Tempo

```bash
docker run -d --name tempo \
  -p 4318:4318 \
  grafana/tempo:latest
```

### Option 3: Cloud Services

You can also use cloud-based observability platforms that support OTLP:
- Grafana Cloud
- Honeycomb
- New Relic
- DataDog
- Lightstep

Simply set `OTEL_EXPORTER_OTLP_ENDPOINT` to your provider's endpoint URL.

## Troubleshooting

If you see warnings about OpenTelemetry initialization failing, it's safe to ignore them or disable tracing with `OTEL_TRACES_ENABLED=false`. The crawler will continue to work normally.

