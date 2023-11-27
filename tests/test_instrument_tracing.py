import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest import mock

from opentelemetry.sdk.trace.export import SpanExportResult

from pubtools.tracing import TracingWrapper, instrument_func


def test_instrument_func_multiple_threads():
    trace_id = "cefb2b8db35d5f3c0dfdf79d5aab1451"
    span_id = "1f2bb7927f140744"
    os.environ["PUB_OTEL_TRACING"] = "true"
    os.environ["traceparent"] = f"00-{trace_id}-{span_id}-01"
    os.environ["OTEL_SERVICE_NAME"] = "local-test"
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://mock"

    # save spans
    queue = deque()

    # mock OTLPSpanExporter.export()
    def mock_export(spans):
        for span in spans:
            queue.append(span)
        return SpanExportResult.SUCCESS

    otlp_exporter = TracingWrapper().processor.span_exporter
    otlp_exporter.export = mock_export

    @instrument_func(span_name="sub_thread_span")
    def sub_thread():
        return 1

    @instrument_func(span_name="main_thread_span", args_to_attr=True)
    def main_thread(param1, param2):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_res = [executor.submit(sub_thread) for i in range(1, 2)]
            as_completed(future_res)

    main_thread("p1", param2="p2")

    TracingWrapper.processor.force_flush()

    out_spans = list(queue)
    # There are two spans which named main_thread_span and sub_thread_span respectively
    assert len(out_spans) == 2

    main_thread_span = None
    sub_thread_span = None
    for span in out_spans:
        if span.name == "main_thread_span":
            main_thread_span = span
        if span.name == "sub_thread_span":
            sub_thread_span = span

    assert main_thread_span
    assert sub_thread_span

    # Both are in the same trace
    assert sub_thread_span.context.trace_id == main_thread_span.context.trace_id

    # The span's parent in sub-thread is the span in main thread.
    assert sub_thread_span.parent.span_id == main_thread_span.context.span_id

    # The parent of the span in main thread
    assert str(hex(main_thread_span.parent.span_id)) == f"0x{span_id}"

    # Assert function parameters in span attributes
    assert (
        "args" in main_thread_span.attributes
        and main_thread_span.attributes["args"] == "p1"
    )
    assert (
        "kwargs" in main_thread_span.attributes
        and main_thread_span.attributes["kwargs"] == "param2=p2"
    )


@mock.patch.dict(os.environ, {"PUB_OTEL_TRACING": "false"})
def test_instrument_func_disabled():
    @instrument_func()
    def func_normal():
        return 1

    assert not TracingWrapper()
    assert func_normal() == 1
