import pytest
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from pubtools.pluggy import hookimpl, pm


class FakeSpanExporterImp(SpanExporter):
    def __init__(self):
        self._spans = None

    def export(self, spans) -> SpanExportResult:
        self._spans = spans
        return SpanExportResult.SUCCESS

    def get_spans(self):
        return self._spans


class FakeSpanExporter:
    @hookimpl
    def otel_exporter(self):
        return FakeSpanExporterImp()


@pytest.fixture(scope="function")
def fake_span_exporter():
    """Installs a hookimpl for span exporter."""
    span_exporter = FakeSpanExporter()
    pm.register(span_exporter)
    yield
    pm.unregister(span_exporter)
