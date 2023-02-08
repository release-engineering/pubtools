"""A hook to support tuning of malloc at task start.

This hook will use mallopt() to set malloc flags according to the usual
glibc environment variables such as MALLOC_ARENA_MAX and so on.

This may seem redundant since glibc is already documented as configuring
itself by those env vars, so why would we need to do the same? Indeed
it is redundant when running tasks standalone, but if running in Pub or
another hosted environment the sequence of events is expected to be
something like this:

1. Look up which entry point implements the current task
2. Look up some settings for the current task & target
3. Set environment variables from those settings
4. Invoke entry point *in the current process*

A problem is that malloc only looks at the env vars a single time, on
initialization. At step (3), it is far too late for any changes to the
env vars to have any effect for the current process, and we're not going
to make a new process for the task. So it is therefore not possible to
tune malloc behavior via env vars in the target settings.

This hook makes it possible by explicitly looking at the env vars and
calling mallopt() with found values during task start, thus making it
possible for the env vars to be used as documented.
"""

import logging
import sys
from ctypes import cdll
from os import environ

from pubtools.pluggy import hookimpl, pm

LOG = logging.getLogger("pubtools")

# Constants are not available via ctypes, so copy them from source:
# https://sourceware.org/git/?p=glibc.git;a=blob;f=malloc/malloc.h;h=60a23e16f387756b07c424975ba11471ee9dad49;hb=71e2a681f18f617ab962bf8a139bd86d4d440e22#l133
M_TRIM_THRESHOLD = -1
M_TOP_PAD = -2
M_MMAP_THRESHOLD = -3
M_MMAP_MAX = -4
M_PERTURB = -6
M_ARENA_TEST = -7
M_ARENA_MAX = -8


# Mappings from environment variable names to mallopt() flags.
# See 'man mallopt' or https://man7.org/linux/man-pages/man3/mallopt.3.html
TUNABLES = {
    "MALLOC_ARENA_MAX": M_ARENA_MAX,
    "MALLOC_ARENA_TEST": M_ARENA_TEST,
    # Note: trailing '_' below is not an error, the env vars are
    # really named that way
    "MALLOC_MMAP_MAX_": M_MMAP_MAX,
    "MALLOC_MMAP_THRESHOLD_": M_MMAP_THRESHOLD,
    "MALLOC_PERTURB_": M_PERTURB,
    "MALLOC_TRIM_THRESHOLD_": M_TRIM_THRESHOLD,
    "MALLOC_TOP_PAD_": M_TOP_PAD,
}


def set_mallopt_tunables():
    # Set malloc options via mallopt() for all defined tunables.
    # Raises an exception on any type of error.
    libc = cdll.LoadLibrary("libc.so.6")
    for varname, flag in TUNABLES.items():
        if varname in environ:
            value = int(environ[varname])
            if libc.mallopt(flag, value) != 1:
                # no error details are available when mallopt fails.
                raise RuntimeError("mallopt() for %s failed" % varname)
            LOG.debug("mallopt() done for %s %s", varname, value)


def set_mallopt_tunables_safe():
    # Like set_mallopt_tunables() but catches and logs on errors.
    # We need to tolerate all kinds of errors as we have no way of knowing
    # for sure whether mallopt() is provided by the platform and what flags
    # and values it accepts.

    # If there is no attempt to tune anything at all, just do nothing.
    # We mainly do this so we don't even try to load libc.so.6 in that
    # case, on the off chance we're running in an environment without it.
    if not any([varname in environ for varname in TUNABLES.keys()]):
        return

    try:
        set_mallopt_tunables()
    except Exception:  # pylint: disable=broad-except
        LOG.warning(
            "Failed to configure malloc from environment variables", exc_info=True
        )


@hookimpl
def task_start():
    # Try to tune malloc on task start.
    set_mallopt_tunables_safe()


pm.register(sys.modules[__name__])
