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
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

from pubtools.pluggy import pm

propagator = TraceContextTextMapPropagator()
baggage_propagator = W3CBaggagePropagator()
log = logging.getLogger(__name__)


def get_trace_wrapper():
    """return a global trace wrapper instance"""
    return TracingWrapper()


class TracingWrapper:
    """Wrapper class to initialize opentelemetry instrumentation and provide a helper function
    for instrumenting a function"""

    def __new__(cls):
        if not hasattr(TracingWrapper, "instance"):
            cls.instance = super().__new__(cls)
            if os.getenv("OTEL_TRACING", "").lower() == "true":
                log.info("Creating TracingWrapper instance")
                exporter = pm.hook.otel_exporter() or ConsoleSpanExporter()
                cls.provider = TracerProvider(
                    resource=Resource.create(
                        {SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME")}
                    )
                )
                cls.processor = BatchSpanProcessor(exporter)
                cls.provider.add_span_processor(cls.processor)
                trace.set_tracer_provider(cls.provider)
                set_global_textmap(propagator)
                cls.tracer = trace.get_tracer(__name__)
        return cls.instance

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

                if not os.getenv("OTEL_TRACING", "").lower() == "true":
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
        if hasattr(self, "processor"):
            self.processor.force_flush()
