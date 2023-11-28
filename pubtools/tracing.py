"""Instrument Pub task functions.

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
from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import \
    TraceContextTextMapPropagator

propagator = TraceContextTextMapPropagator()
baggage_propagator = W3CBaggagePropagator()
log = logging.getLogger(__name__)


class TracingWrapper:
    """Wrapper class that will wrap all methods of calls with the instrument_tracing decorator."""

    __instance = None

    def __new__(cls):
        """Create a new instance if one does not exist."""
        if not os.getenv("PUB_OTEL_TRACING", "").lower() == "true":
            return None

        if TracingWrapper.__instance is None:
            log.info("Creating TracingWrapper instance")
            cls.__instance = super().__new__(cls)
            otlp_exporter = OTLPSpanExporter(
                endpoint=f"{os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')}/v1/traces",
            )
            cls.provider = TracerProvider(
                resource=Resource.create({SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME")})
            )
            cls.processor = BatchSpanProcessor(otlp_exporter)
            cls.provider.add_span_processor(cls.processor)
            trace.set_tracer_provider(cls.provider)
            set_global_textmap(propagator)
            cls.tracer = trace.get_tracer(__name__)
        return cls.__instance


def instrument_func(span_name=None, args_to_attr=False):
    """Instrument tracing for a function.

    Args:
        span_name: str
            Span name.
        args_to_attr: boolean
            Add function parameters into span attributes.

    Returns:
        The decorated function or class
    """
    tracer = trace.get_tracer(__name__)

    def _instrument_func(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            if not os.getenv("PUB_OTEL_TRACING", "").lower() == "true":
                return func(*args, **kwargs)

            trace_ctx = None
            token = None
            # Try to extract trace context from environment variables.
            if not context.get_current():
                trace_ctx = propagator.extract(carrier=os.environ)
                trace_ctx = baggage_propagator.extract(
                    carrier=os.environ, context=trace_ctx
                )

            if trace_ctx:
                token = context.attach(trace_ctx)

            attributes = {
                "function_name": func.__qualname__,
            }
            if args_to_attr:
                attributes["args"] = ", ".join(map(str, args))
                attributes["kwargs"] = ", ".join(
                    "{}={}".format(k, v) for k, v in kwargs.items()
                )

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