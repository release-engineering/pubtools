from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from opentelemetry import trace
from opentelemetry.trace.status import StatusCode

from pubtools._impl.tracing import TracingWrapper
from pubtools._impl import tracing
from pubtools.tracing import get_trace_wrapper
import logging


def test_instrument_func_in_context(monkeypatch, fake_span_exporter):
    monkeypatch.setenv("OTEL_TRACING", "true")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "local-test2")

    tw = get_trace_wrapper()
    tw._reset()

    @tw.instrument_func(span_name="child_span")
    def foo():
        pass

    with trace.get_tracer(__name__).start_as_current_span(name="parent_span"):
        foo()

    tw.force_flush()
    out_spans = tw._processor.span_exporter.get_spans()
    assert len(out_spans) == 2
    if out_spans[0].name == "parent_span":
        parent_span = out_spans[0]
        child_span = out_spans[1]
    else:
        parent_span = out_spans[1]
        child_span = out_spans[0]

    assert child_span.context.trace_id == parent_span.context.trace_id
    assert child_span.parent.span_id == parent_span.context.span_id


def test_instrument_func_carrier(monkeypatch, fake_span_exporter):
    root_trace_id = "cefb2b8db35d5f3c0dfdf79d5aab1451"
    root_span_id = "1f2bb7927f140744"

    monkeypatch.setenv("OTEL_TRACING", "true")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "local-test2")
    carrier = {"traceparent": f"00-{root_trace_id}-{root_span_id}-01"}

    tw = get_trace_wrapper()
    tw._reset()

    @tw.instrument_func(span_name="func_with_carrier", carrier=carrier)
    def foo():
        pass

    foo()

    tw.force_flush()
    out_spans = tw._processor.span_exporter.get_spans()
    assert len(out_spans) == 1
    span = out_spans[0]
    assert span.name == "func_with_carrier"
    assert span.context.trace_id == int(root_trace_id, 16)
    assert span.parent.span_id == int(root_span_id, 16)


def test_instrument_func_multiple_threads(monkeypatch, fake_span_exporter):
    root_trace_id = "cefb2b8db35d5f3c0dfdf79d5aab1451"
    root_span_id = "1f2bb7927f140744"

    monkeypatch.setenv("OTEL_TRACING", "true")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "local-test1")
    monkeypatch.setenv("traceparent", f"00-{root_trace_id}-{root_span_id}-01")

    tw = get_trace_wrapper()
    tw._reset()

    @tw.instrument_func(span_name="sub_thread_span")
    def sub_thread():
        return 1

    @tw.instrument_func(span_name="main_thread_span", args_to_attr=True)
    def main_thread(param1, param2):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_res = [executor.submit(sub_thread) for i in range(1, 2)]
            as_completed(future_res)

    main_thread("p1", param2="p2")
    tw.force_flush()

    main_thread_span = None
    sub_thread_span = None
    for span in tw._processor.span_exporter.get_spans():
        if span.name == "main_thread_span":
            main_thread_span = span
        if span.name == "sub_thread_span":
            sub_thread_span = span

    assert main_thread_span
    assert sub_thread_span

    # Both are in the same trace
    assert (
        sub_thread_span.context.trace_id
        == main_thread_span.context.trace_id
        == int(root_trace_id, 16)
    )

    # Verify span parent and child relation
    assert sub_thread_span.parent.span_id == main_thread_span.context.span_id
    assert main_thread_span.parent.span_id == int(root_span_id, 16)

    # Assert function parameters in span attributes
    assert (
        "args" in main_thread_span.attributes
        and main_thread_span.attributes["args"] == "p1"
    )
    assert (
        "kwargs" in main_thread_span.attributes
        and main_thread_span.attributes["kwargs"] == "param2=p2"
    )


def test_instrument_func_exception(monkeypatch, fake_span_exporter):
    monkeypatch.setenv("OTEL_TRACING", "true")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "local-test3")
    tw = get_trace_wrapper()
    tw._reset()

    @tw.instrument_func(span_name="func_with_exception")
    def func_with_exception():
        raise Exception("failed with exception")

    with pytest.raises(Exception):
        func_with_exception()

    tw.force_flush()
    out_spans = tw._processor.span_exporter.get_spans()

    assert len(out_spans) == 1
    span = out_spans[0]
    assert span.name == "func_with_exception"
    assert span.status.status_code == StatusCode.ERROR
    assert len(span.events) >= 1
    assert span.events[0].attributes["exception.message"] == "failed with exception"


def test_instrument_func_disabled(monkeypatch):
    monkeypatch.setenv("OTEL_TRACING", "false")
    # Recreate an instance of TracingWrapper
    tw = TracingWrapper()

    @tw.instrument_func()
    def foo():
        return 1

    assert foo() == 1
    assert tw.provider is None

def test_otel_not_available(caplog, monkeypatch):
    monkeypatch.setenv("OTEL_TRACING", "true")
    monkeypatch.setattr(tracing, "OPENTELEMETRY_AVAILABLE", False)
    caplog.set_level(logging.DEBUG)

    # Recreate an instance of TracingWrapper
    tw = TracingWrapper()

    @tw.instrument_func()
    def foo():
        return 1

    assert foo() == 1
    assert tw.provider is None
    assert "Tracing is enabled but the open telemetry package is unavailable. " \
           "Tracing functionality will be disabled." in caplog.text
