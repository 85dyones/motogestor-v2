"""Observability helpers: structured logging, metrics, tracing."""

import json
import logging
import os
import time
import uuid
from logging.config import dictConfig
from typing import Optional

from flask import Flask, g, has_request_context, request
from prometheus_client import Counter, Histogram
from prometheus_flask_exporter import PrometheusMetrics

try:  # opentelemetry is optional at runtime
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except Exception:  # pragma: no cover - optional dependency handling
    trace = None  # type: ignore


REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "Request latency by route",
    ["service", "method", "route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Request count by status",
    ["service", "method", "route", "status"],
)
AUTH_ERRORS_COUNTER = Counter(
    "auth_errors_total",
    "Authentication and authorization errors",
    ["service"],
)

# Specific to management-service, but shared name keeps Prometheus consistency
OS_CREATED_COUNTER = Counter(
    "os_created_total", "Service Orders created per tenant", ["tenant_id"]
)

_APP_INFO_REGISTERED = False


class RequestContextFilter(logging.Filter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - plumbing
        record.service = self.service_name
        record.trace_id = getattr(g, "trace_id", None)
        record.tenant_id = getattr(g, "current_tenant_id", None)
        record.route = getattr(g, "route_label", None)
        if not record.route and has_request_context():
            record.route = getattr(request, "path", None)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - plumbing
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "service": getattr(record, "service", None),
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "route": getattr(record, "route", None),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(service_name: str, default_level: str = "INFO") -> None:
    log_level = os.getenv("LOG_LEVEL", default_level).upper()
    dictConfig(
        {
            "version": 1,
            "formatters": {"json": {"()": JsonFormatter}},
            "filters": {
                "request": {
                    "()": RequestContextFilter,
                    "service_name": service_name,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "json",
                    "filters": ["request"],
                }
            },
            "root": {"level": log_level, "handlers": ["console"]},
        }
    )


def _setup_tracing(app: Flask, service_name: str) -> Optional[object]:
    if trace is None:
        return None

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return None

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=endpoint, insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true") == "true")
    )
    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    return provider


def register_observability(app: Flask, service_name: str) -> None:
    setup_logging(service_name)

    global _APP_INFO_REGISTERED
    metrics = PrometheusMetrics(app, defaults_prefix=service_name)
    if not _APP_INFO_REGISTERED:
        metrics.info(
            "app_info", "Application info", version=os.getenv("APP_VERSION", "0.0.1")
        )
        _APP_INFO_REGISTERED = True

    _setup_tracing(app, service_name)

    @app.before_request
    def _start_timer_and_trace():  # pragma: no cover - glue
        g.request_start_time = time.perf_counter()
        incoming = request.headers.get("X-Trace-Id")
        g.trace_id = incoming or uuid.uuid4().hex
        g.route_label = request.url_rule.rule if request.url_rule else request.path

    @app.after_request
    def _after(response):  # pragma: no cover - glue
        try:
            duration = time.perf_counter() - getattr(g, "request_start_time", time.perf_counter())
            REQUEST_LATENCY.labels(
                service=service_name, method=request.method, route=g.route_label
            ).observe(duration)
            REQUEST_COUNT.labels(
                service=service_name,
                method=request.method,
                route=g.route_label,
                status=str(response.status_code),
            ).inc()
            if response.status_code in (401, 403):
                AUTH_ERRORS_COUNTER.labels(service=service_name).inc()

            if trace is not None:
                span = trace.get_current_span()
                if span and span.is_recording():
                    span.set_attribute("tenant.id", getattr(g, "current_tenant_id", None))
                    span.set_attribute("http.route", g.route_label)
                    span.set_attribute("http.trace_id", getattr(g, "trace_id", None))
        finally:
            response.headers["X-Trace-Id"] = getattr(g, "trace_id", "")
        return response

