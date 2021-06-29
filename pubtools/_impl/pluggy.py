from __future__ import absolute_import

import sys
from contextlib import contextmanager

import pluggy

pm = pluggy.PluginManager("pubtools")
hookspec = pluggy.HookspecMarker("pubtools")
hookimpl = pluggy.HookimplMarker("pubtools")


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

    * :func:`task_start` is invoked when the block is entered.
    * :func:`task_stop` is invoked when the block is exited.
    """
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


pm.add_hookspecs(sys.modules[__name__])
