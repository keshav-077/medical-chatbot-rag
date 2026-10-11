"""Request IDs, with OpenTelemetry spans when an exporter is configured."""

import logging
import os
import uuid

logger = logging.getLogger(__name__)
_ready = False


def init_telemetry(app):
    global _ready
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint or _ready:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(
            resource=Resource.create({"service.name": "bloom-india"})
        )
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        FlaskInstrumentor().instrument_app(app)
        _ready = True
        logger.info("OpenTelemetry exporter enabled")
    except Exception as exc:
        logger.warning("OpenTelemetry not active: %s", exc)


def new_request_id() -> str:
    return str(uuid.uuid4())
