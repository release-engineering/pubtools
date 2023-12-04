.. _tracing:

Tracing
=======

.. contents::
    :depth: 3


Overview
--------

It provides an instrument tracing wrapper function to use to instrument functions manually in pubtools-* projects.


Usage
.....................

Set environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~

Following environment variables are used in the module:

- ``OTEL_TRACING``: set ``true`` to enable instrument tracing, otherwise tracing is disabled.
- ``OTEL_SERVICE_NAME``: required, set the value of the service.name resource attribute. It's
  expected to be unique within the same namespace.


OTEL Exporter
~~~~~~~~~~~~~~

In order to visualize and analyze telemetry, an exporter is required to export tracing data to
a backend, e.g: `jaeger <https://www.jaegertracing.io/>`_. As part of OpenTelemetry Python you
will find many exporters being available. Which exporter should be used depends on usage scenarios, e.g:
`ConsoleSpanExporter <https://opentelemetry.io/docs/instrumentation/python/exporters/#console-exporter/>`_
is useful for development and debugging tasks, while
`OTLPSpanExporter <https://opentelemetry.io/docs/instrumentation/python/exporters/#otlp-endpoint-or-collector/>`_
can be more suitable on production environment. So choosing different exporters for different scenarios is expected.

In order to have a exporter you expected, the hook :meth:`otel_exporter` is needed to be implemented,
otherwise `ConsoleSpanExporter <https://opentelemetry.io/docs/instrumentation/python/exporters/#console-exporter/>`_
will be used.

Instrument tracing for functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before instrument tracing for functions, :class:`TracingWrapper` should be called once in the service, which
initializes trace provider, batch span processor and exporter.

.. code-block:: python

     from pubtools.tracing import TracingWrapper

     # Initialize a trace provider, batch span processor and exporter.
     tracing_wrapper = TracingWrapper()

**Basic instrument tracing for a function**

.. code-block:: python

     from pubtools.tracing import instrument_func, TracingWrapper

     # Initialize a trace provider, batch span processor and exporter.
     tracing_wrapper = TracingWrapper()

     # Create a span for the function foo.
     @instrument_func(span_name="foo_span", args_to_attr=True)
     def foo(p1="p1"):
         pass
     ...

The function foo will be instrumented, the span name is ``foo_span``, and the input parameters
``p1="p1"`` are added in the span attributes.

The input parameter ``span_name`` and ``args_to_attr`` are optional, if ``span_name`` is not
specified, the span name will use the function's name.

**Instrument a function with carrier**

Imaging the case that trace context is propagated cross application systems. A carrier which carries
trace context along with a call is passed to from upstream service to downstream service, then
downstream service will extract trace context from the carrier.

The wrapper function is able to extract trace context from the carrier if it's provided. For example:

.. code-block:: python

     from pubtools.tracing import instrument_func

     # carrier={'traceparent': '00-355989206d66228f21ff34634b77ae1a-97efa33ebed5d06c-01',...}

     @instrument_func(carrier=carrier):
     def foo():
         pass
     ...

The span "foo" will appear in the trace extracted from ``carrier`` and be as a child span of
the caller span.

**Instrument functions with environment variables**

Trace context can be extracted from environment variables.

.. code-block:: python

     from pubtools.tracing import instrument_func

     # 'traceparent' environment variable is set.
     # os.environ["traceparent"] = "00-355989206d66228f21ff34634b77ae1a-97efa33ebed5d06c-01"

     @instrument_func():
     def foo():
         pass
     ...

It's similar as extracting trace context from the function parameter carrier.

It's useful in multiple threads scenario. As opentelemetry-python library uses
`contextvars <https://docs.python.org/3/library/contextvars.html>`_ under the hood, trace context
can not be passed across threads. It provides a solution to implement context pass in this case,
for example:

.. code-block:: python

     from pubtools.tracing import instrument_func

     @instrument_func(span_name="sub_thread_span")
     def sub_thread():
         return 1

     @instrument_func(span_name="main_thread_span")
     def main_thread(param1, param2):
         with ThreadPoolExecutor(max_workers=2) as executor:
             future_res = [executor.submit(sub_thread) for i in range(1, 3)]
             as_completed(future_res)
             ...

The span ``sub_thread_span`` and ``main_thread_span`` are in the same trace and the ``sub_thread_span``
is the child of ``main_thread_span`` span.

API reference
-------------

.. autofunction:: pubtools.tracing.instrument_func
