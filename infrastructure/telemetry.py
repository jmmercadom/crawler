"""
Telemetry infrastructure setup.

This module provides OpenTelemetry configuration for distributed tracing.
"""

import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Get logger for this module
logger = logging.getLogger(__name__)


def setup_opentelemetry() -> None:
    """
    Initialize OpenTelemetry tracing.

    Configuration is controlled by environment variables:
    - OTEL_SERVICE_NAME: Service name (default: gaceta-crawler)
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4318)
    - OTEL_TRACES_ENABLED: Enable/disable tracing (default: true)
    """
    # Check if tracing is enabled
    traces_enabled = os.getenv("OTEL_TRACES_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    if not traces_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return

    # Get service name from environment or use default
    service_name = os.getenv("OTEL_SERVICE_NAME", "gaceta-crawler")

    # Create resource with service name
    resource = Resource(attributes={SERVICE_NAME: service_name})

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Get OTLP endpoint from environment or use default
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    try:
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")

        # Add batch span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set the tracer provider
        trace.set_tracer_provider(provider)

        # Instrument logging to correlate logs with traces
        LoggingInstrumentor().instrument(set_logging_format=False)

        logger.info(
            "OpenTelemetry initialized: service=%s, endpoint=%s",
            service_name,
            otlp_endpoint,
        )
    except Exception as e:
        logger.warning("Failed to initialize OpenTelemetry: %s", str(e))


def get_tracer():  # type: ignore
    """Get configured OpenTelemetry tracer"""
    return trace.get_tracer(__name__)
