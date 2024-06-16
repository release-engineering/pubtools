import logging
import sys
from contextlib import contextmanager

import pkg_resources
import pluggy

LOG = logging.getLogger("pubtools")

pm = pluggy.PluginManager("pubtools")
hookspec = pluggy.HookspecMarker("pubtools")
hookimpl = pluggy.HookimplMarker("pubtools")


def resolve_hooks():
    # A private helper to ensure all code defining hookspecs/hookimpls has been imported
    # before continuing.

    # 1. Eagerly load any pubtools console_scripts entry points.
    #
    # This will pick up hookspecs from task libraries such as pubtools-quay.
    #
    for ep in pkg_resources.iter_entry_points("console_scripts"):
        if ep.module_name.startswith("pubtools"):
            # Method resolve() was introduced in setuptools 11.3 to replace load()
            ep.resolve() if hasattr(ep, "resolve") else ep.load(require=False)
            LOG.debug("Resolved %s", ep)

    # 2. Eagerly load any pubtools.hooks entry points.
    #
    # This is a group we provide so that any hook-only modules, which might otherwise
    # not be imported by anyone, can request themselves to be imported.
    #
    for ep in pkg_resources.iter_entry_points("pubtools.hooks"):
        ep.resolve() if hasattr(ep, "resolve") else ep.load(require=False)
        LOG.debug("Resolved %s", ep)


@hookspec
def task_start():
    """Called when a task starts.

    This hook can be used to register additional hook implementations with
    desired context.
    """


@hookspec
def task_stop(failed):
    """Called when a task ends.

    If :func:`task_start` was used to register additional hook implementations,
    this hook should be used to unregister them.

    :param failed: True if the task is failing (i.e. exiting with non-zero exit code, or
                   raising an exception).
    :type failed: bool
    """


@contextmanager
def task_context():
    """Run a block of code within a task context, ensuring task lifecycle hooks are invoked
    when appropriate.

    This is a context manager for use within pubtools task libraries where hooks
    shall be provided. It can be used in a ``with`` statement, as in example:

    >>> with task_context():
    >>>    self.do_task()

    The context manager will ensure that:

    * hookspecs/hookimpls are resolved across all installed libraries.
    * :func:`task_start` is invoked when the block is entered.
    * :func:`task_stop` is invoked when the block is exited.
    """
    resolve_hooks()

    pm.hook.task_start()

    failed = True
    try:
        yield
        failed = False
    except SystemExit as exit:
        failed = exit.code != 0
        raise
    except Exception:
        failed = True
        raise
    finally:
        pm.hook.task_stop(failed=failed)


@hookspec(firstresult=True)
def get_cert_key_paths(server_url):
    """Get location of SSL certificates used to authenticate with a given service.

    If there are multiple hook implementations and multiple values are returned, the first
    non-empty answer is considered canonical. The first answer is returned by the hook
    implementation which was registered last.

    The certificates are expected to be in PEM format. It's permitted for paths to cert and key
    to be the same. Callers of this hook should be prepared to receive no result, and should
    implement a reasonable fallback strategy in that case.

    :param server_url: Service URL.
    :type server_url: str
    :return: Paths to SSL certificate and key.
    :rtype: (str, str)
    """


@hookspec(firstresult=True)
def otel_exporter():
    """Return an OTEL exporter, used by OTEL instrumentation.

    If OTEL tracing is enabled and this hook is not implemented, a default
    `ConsoleSpanExporter` will be used.

    :return: Instance of SpanExporter.
    :rtype: opentelemetry.sdk.trace.export.SpanExporter
    """


pm.add_hookspecs(sys.modules[__name__])
