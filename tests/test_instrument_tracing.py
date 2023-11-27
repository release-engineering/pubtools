import os
from unittest import mock
from unittest.mock import Mock

import pytest
from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
    OTLPSpanExporter

from pubtools.tracing import TracingWrapper, instrument_func


@mock.patch.dict(
    os.environ, {"PUB_OTEL_TRACING": "true", "traceparent": "00-xxxx-xxx-01"}
)
def test_instrument_func_enabled():
    mock_export = Mock()
    OTLPSpanExporter.export = mock_export

    @instrument_func(args_to_attr=True)
    def func_normal():
        return 1

    @instrument_func()
    def func_with_exception():
        raise Exception()

    assert TracingWrapper()
    assert func_normal() == 1
    with pytest.raises(Exception):
        func_with_exception()

    TracingWrapper.processor.force_flush()
    mock_export.assert_called()


@mock.patch.dict(os.environ, {"PUB_OTEL_TRACING": "false"})
def test_instrument_func_disabled():
    mock_export = Mock()
    OTLPSpanExporter.export = mock_export

    @instrument_func()
    def func_normal():
        return 1

    assert not TracingWrapper()
    assert func_normal() == 1
    mock_export.assert_not_called()
