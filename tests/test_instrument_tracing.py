import os
from unittest.mock import Mock

import pytest
from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
    OTLPSpanExporter

from pubtools.tracing import TracingWrapper, instrument_func


def test_instrument_func():
    os.environ["PUB_OTEL_TRACING"] = "true"
    os.environ[
        "traceparent"
    ] = "00-cefb2b8db35d5f3c0dfdf79d5aab1451-1f2bb7927f140744-01"

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


def test_not_enable_tracing():
    os.environ["PUB_OTEL_TRACING"] = ""

    mock_export = Mock()
    OTLPSpanExporter.export = mock_export

    @instrument_func()
    def func_normal():
        return 1

    assert not TracingWrapper()
    assert func_normal() == 1
    mock_export.assert_not_called()
