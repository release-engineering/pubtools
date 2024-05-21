"""Instrument functions.

Usage:
    @instrument_func()
      def func():
          pass

"""

import functools
import logging
import os
import threading

from opentelemetry import baggage, context, trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from pubtools.pluggy import pm

propagator = TraceContextTextMapPropagator()
baggage_propagator = W3CBaggagePropagator()
TRACE_WRAPPER = None
log = logging.getLogger(__name__)


def get_trace_wrapper():
    """return a global trace wrapper instance"""
    global TRACE_WRAPPER
    if TRACE_WRAPPER is None:
        TRACE_WRAPPER = TracingWrapper()
    return TRACE_WRAPPER


class TracingWrapper:
    """Wrapper class to initialize opentelemetry instrumentation and provide a helper function
    for instrumenting a function"""

    def __init__(self):
        self._processor = None
        self._provider = None
        self._enabled_trace = None
        self._reset()

    def _reset(self):
        # Construct the needed resources, if and only if OTEL_TRACING is enabled
        # and the resources were not already constructed.
        #
        # This method is intended only for use during tests to make sure that the current
        # TracingWrapper has tracing enabled, even if __init__ was already called while
        # OTEL_TRACING was set to false.
        #
        # Actually flipping the TracingWrapper between enabled/disabled/enabled and back
        # at runtime is NOT supported due to limitations in opentelemetry, e.g. the
        # trace.set_tracer_provider global singleton set below can *never* be set up
        # more than once in a single process.

        self._enabled_trace = os.getenv("OTEL_TRACING", "").lower() == "true"
        if self._enabled_trace and not self._processor:
            log.info("Creating TracingWrapper instance")
            exporter = pm.hook.otel_exporter() or ConsoleSpanExporter()
            self._processor = BatchSpanProcessor(exporter)
            self._provider = TracerProvider(
                resource=Resource.create({SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME")})
            )
            self._provider.add_span_processor(self._processor)
            trace.set_tracer_provider(self._provider)
            set_global_textmap(propagator)

    def instrument_func(self, span_name=None, carrier=None, args_to_attr=False):
        """Instrument tracing for a function.

        Args:
            span_name: str
                Span name. It's assigned with the function's name by default if it's omitted.
            carrier: dict
                A dictionary which holds trace context. Trace context will be extracted from it if
                if it's provided.
            args_to_attr: boolean
                Add function parameters into span attributes or not.

        Returns:
            The decorated function
        """
        tracer = trace.get_tracer(__name__)

        def _instrument_func(func):
            @functools.wraps(func)
            def wrap(*args, **kwargs):
                attributes = {
                    "function_name": func.__qualname__,
                }
                if args_to_attr:
                    attributes["args"] = ", ".join(map(str, args))
                    attributes["kwargs"] = ", ".join(
                        "{}={}".format(k, v) for k, v in kwargs.items()
                    )

                if not self._enabled_trace:
                    return func(*args, **kwargs)

                trace_ctx = None
                token = None
                if not context.get_current():
                    # Extract trace context from carrier.
                    if carrier:
                        trace_ctx = propagator.extract(carrier=carrier)
                        trace_ctx = baggage_propagator.extract(
                            carrier=carrier, context=trace_ctx
                        )
                    else:
                        # Try to extract trace context from environment variables.
                        trace_ctx = propagator.extract(carrier=os.environ)
                        trace_ctx = baggage_propagator.extract(
                            carrier=os.environ, context=trace_ctx
                        )

                if trace_ctx:
                    token = context.attach(trace_ctx)

                with tracer.start_as_current_span(
                    name=span_name or func.__qualname__,
                    attributes=attributes,
                ) as span:
                    try:
                        # Put trace context in environment variables in the main thread.
                        if threading.current_thread() is threading.main_thread():
                            propagator.inject(os.environ)
                            baggage_propagator.inject(os.environ)

                        result = func(*args, **kwargs)
                    except Exception as exc:
                        span.set_status(Status(StatusCode.ERROR))
                        span.record_exception(exc)
                        raise
                    finally:
                        # Add baggage data into span attributes
                        span.set_attributes(baggage.get_all())
                        if token:
                            context.detach(token)
                    return result

            return wrap

        return _instrument_func

    def force_flush(self):
        """Flush trace data into OTEL collectors"""
        if self._processor:
            self._processor.force_flush()
        log.info("Flush trace data into OTEL collectors")

    @property
    def provider(self):
        """Trace provider"""
        return self._provider
