.. _devguide:

Developer Guide
===============

This document is a reference for developers of projects within the ``pubtools``
family.

.. contents::
  :local:
  :depth: 2

Project setup
-------------

Naming
......

If you are introducing a new ``pubtools`` project, please follow these conventions:

- **For task libraries**:
   - Name the project ``pubtools-<foo>`` where ``foo`` identifies the most relevant target
     system. (example: ``pubtools-pulp`` is for pushing content to Pulp.)
   - Put all Python code under the "pubtools" namespace.
   - ("Task library" means the scope of the project is to provide ``console_scripts``-based
     tasks, as described in :ref:`a later section <task>`.)
- **For any other kind of project**:
   - If you are developing a project associated with ``pubtools`` but not a task library, there is no specific convention.
     Give the project any sensible name.
   - If the project can be of general use, you do not have to name it with a ``pubtools-``
     prefix.

Target platforms
................

Projects should aim to be compatible with the following environments:

- Python 2.6 (yes, really)
- Python 3.8 and later
- Red Hat flavored operating systems (RHEL, CentOS, Fedora)

The requirement to support Python 2 is likely to be dropped during 2022.

.. _task:

Understanding tasks
-------------------

Task interface
..............

The interface to any ``pubtools`` task is a standard ``console_scripts``
entry point. See `the setuptools manual`_ for information on these.

Entry points by convention are named as ``<project_name>-<task_name>``.
For example, the ``pubtools-pulp`` project has a ``publish`` task which is
defined in ``setup.py`` as:

.. code:: python

  entry_points={
    "console_scripts": [
      "pubtools-pulp-publish = pubtools._pulp.tasks.publish:entry_point",
    ]
  },

Inputs
~~~~~~

Tasks should accept all necessary inputs to perform their work via:

- command-line arguments
   - read from ``sys.argv`` using any preferred method (e.g. :mod:`argparse`)
   - **do not use for secrets**
- environment variables
   - read from ``os.environ`` as usual
   - recommended method of passing secrets

Note that reading data from local files is not recommended. This is because it
breaks or at least complicates the :ref:`Standalone vs Hosted <hosted>` paradigm:
if you read inputs or configuration from files, you must somehow arrange for those
files to be deployed onto the hosted environment and cleaned up when no longer needed.

There's a notable exception to this: if you need to process very large amounts of
data, you may find that the argument list becomes too long to launch a new process
(see `argmax`_).

This is not a problem within the hosted environment, since that doesn't
launch new processes for new tasks. However, argument limits may interfere with
local development and testing. You may therefore wish to add some optional
functionality to read from local files as a workaround to the limit, to be used
primarily during development.

Outputs
~~~~~~~

Tasks should use the following approaches to produce output.
(Note we refer to logging-style outputs here, not the primary side-effects a task
aims to implement).

- use the :ref:`logging` system to log messages
- use the `pushcollector`_ library to save additional (small) files and push item metadata
   - example: save a snapshot in JSON format of some remote resource prior to updating, to
     ensure an audit trail exists

.. _hosted:

Standalone vs Hosted
....................

Tasks provided by ``pubtools`` libraries are designed to work within two different
contexts, with significant differences between them. These are:

- Invoked directly as command-line interface tools
   - We refer to this as **Standalone** execution.
- Invoked from within a Python-based service using the "entry points" system
   - We refer to this as **Hosted** execution.

The following table summarizes the major differences between these contexts:

.. list-table::
   :widths: 20 40 40
   :header-rows: 1

   * -
     - Standalone
     - Hosted
   * - usage scenario
     - development, testing, emergencies
     - production
   * - inputs
     - ``sys.argv`` populated by command-line arguments
     - ``sys.argv`` populated by the hosting service
   * - secrets
     - environment variables set by caller
     - environment variables set by the hosting service
   * - ``sys.stdout``
     - connected to standard output
     - redirected to logger
   * - logging
     - logging subsystem uses default (empty) configuration
     - loggers are configured prior to task execution
   * - hooks
     - :ref:`hooks` are available
     - hooks are available, hosting service may provide some ``@hookimpls``
   * - pushsource
     - pushsource library uses default (generic) configuration
     - pushsource library is bound to specific environments
   * - pushcollector
     - pushcollector library uses default ``local`` backend
     - pushcollector library uses a backend specific to the hosting service

In principle, the ``pubtools`` family of projects are able to be integrated
with any number of services. In practice, tasks are almost always hosted in
one specific system known as **Pub**.

Argument conventions
--------------------

In this section we document some common arguments supported across multiple
task libraries.

If you need to support any of the functionality below, it is best to follow
these conventions. Using consistent arguments across the projects helps to
avoid errors while integrating tasks into Pub or other task hosting
environments.


.. _arglist:

Arguments with multiple values
..............................

For cases where you want to accept multiple values as a list, it's recommended
to support *both* the following argument styles simultaneously:

``--key val1 --key val2 --key val3``
  This style tends to be simpler for programmatic usage.

``--key val1,val2,val3``
  This style is more user-friendly for humans.

  (Of course, you may not accept this style if you need values which
  themselves contain the ``,`` character.)

.. _debug:

``--debug``: enable debug logging
.................................

As explained at :ref:`logconfig`, task libraries in general should refrain
from configuring loggers; in production scenarios, this is the responsibility of
the task hosting environment.

However, while locally developing and testing task libraries, there will commonly
arise the need to enable verbose logging. If you want to enable this, it's suggested
to provide a ``--debug`` option with semantics:

no ``--debug``
  Enable root logger at ``INFO`` level.

``--debug``
  Enable root logger at ``INFO`` level and this project's logger at ``DEBUG`` level.

``--debug`` more than once
  Enable even more loggers at ``DEBUG`` level, perhaps even the root logger, depending on
  how may times the argument is used.

Keep in mind that this option is intended for local development or testing purposes only.
The option should never be used when the task runs in a hosted environment.


``--skip``, ``--step``: execute subset of task
..............................................

Some tasks might be made up of several discrete steps, and you may want to allow
callers to skip some of them in certain cases.

If so, it's suggested to enable this via the following arguments:

``--skip a,b,c``
  Don't execute steps ``"a"``, ``"b"`` or ``"c"``.

``--step a,b,c``
  Execute only steps ``"a"``, ``"b"`` and ``"c"``.

Here are some implementation guidelines for these arguments:

* Follow the advice in :ref:`arglist`.
* Don't validate step names.
   * If passed any unknown steps, simply ignore them.
   * Validating the step names would make the interface more brittle (e.g. removing a step is
     a backwards-incompatible interface change).
   * If you're familiar with ansible - compare with `ansible tags`_, where it's not an error
     to specify a tag matching zero tasks.
* The target audience includes developers and power users.
   * By default, a task should do the right thing without having to be passed any ``--step`` or
     ``--skip``.
   * It may be used during development to focus only on relevant parts of code.
   * It may be used in production as an emergency workaround to skip failing but non-critical
     portions of a task.
   * It's not expected that all possible combinations of steps will work or shall be
     tested.

``--source``: obtain content via ``pushsource``
...............................................

If your task consumes content via the `pushsource`_ library, it's strongly recommended to
use the URL-based configuration mechanism from the library, and accept the URL via a
``--source`` argument:

``--source <some-pushsource-url>``
  Use content from the specified source.

Accepting other arguments to configure the ``pushsource`` library is discouraged.  Strictly
using URLs for configuration will ensure that your task is forwards-compatible with new features
and improvements in future versions of that library.


.. _logging:

Logging
-------

Libraries can make use of the standard :mod:`logging` module.
Following the guidelines below will help ensure that your logging works effectively
in both the :ref:`standalone and hosted execution modes <hosted>`.

Use loggers as primary output mechanism
.......................................

Use standard :class:`~logging.Logger` objects for user-oriented output
from your task. Don't write to stdout or stderr.

(Note: although it's mentioned earlier that stdout will be redirected to a logger
within the hosted environment, this is intended as a last resort to avoid losing
valuable information while debugging; relying on it is bad practice.)

.. _logconfig:

Avoid changing logger configuration
...................................

When invoked in the hosted environment, loggers will already be configured by the
time your task's entry point is called. In this case, you **must not** adjust or
overwrite the configuration of the loggers (particularly the root logger).
Logger configuration is considered to be the responsibility of the hosting service;
tasks should avoid interfering with it.

Note that the standard :func:`logging.basicConfig` function implements useful behavior:
it installs basic log configuration writing to ``sys.stderr`` if and only if the root
logger is not already configured.

Therefore, a simple and recommended way to set up loggers correctly for both the
standalone and hosted case is to insert a call to `basicConfig` near the top of your
task's entry point, such as:

.. code:: python

    logging.basicConfig(level=logging.INFO)


Name loggers after your project
...............................

If your project is named ``pubtools-foo``, you should use loggers under the ``pubtools.foo``
hierarchy. This ensures there is a simple and predictable way to control the logging for
each project.


Use appropriate log levels
..........................

Log levels within the ``pubtools`` projects are typically used as follows:

``DEBUG``
  Messages of interest to developers.

  Hidden by default, only enabled when debugging problems.
  Log anything you may find useful while debugging.

``INFO``
  Messages of interest to end-users.

  This level and all later levels are enabled by default for ``pubtools.*``
  loggers when executing in a hosted environment.

  Should be verbose enough to understand any major side-effects of a task
  (e.g. writing data to a remote system), but not so verbose as to cause
  performance issues or make the log unreasonably noisy.

``WARNING``
  Messages indicating a potential but non-fatal issue, or adding information
  which may explain the root cause of an error encountered elsewhere.

``ERROR``
  Messages indicating that something has certainly gone wrong and some action
  is likely needed.

  Refrain from using these levels for any recoverable errors (e.g. if task
  retries an operation, only use ``ERROR`` after all retries are exhausted).

  Note that users will sometimes be concerned or confused by ``ERROR`` logs
  even if a task ultimately ends up succeeding.  A useful rule of thumb is
  to ask yourself: when this code path is reached, do I want users to file a
  ticket/bug for me?  If the answer is "No", then ``ERROR`` may be too
  severe.

Structured logging via ``extra``
................................

The logging system supports adding structured metadata onto log events via
the optional ``extra`` argument, which is a dict of arbitrary key-value pairs.

Within the ``pubtools`` family of projects we have the convention of an
``event`` attribute, of the following form:

.. code:: python

  {
    "event": {
      "type": "foo-happened",  # brief string identifying what just happened
      "key1": "value1",        # & then any arbitrary fields relating to
      "key2": "value2",        # this event (don't add timestamp, it's implied)
    }
  }

If your project creates logging events using this structure, these may be
collected by the hosting environment and used in various interesting ways
(e.g. recorded into metrics-collecting systems).

It's recommended to make use of this whenever a logged event might be interesting
in order to programmatically monitor the performance or health of a service.

Here is an example from ``pubtools-pulplib``, logging metadata on the Pulp task
queue.

.. code:: python

  LOG.info(
    "Still waiting on Pulp, load: %s running, %s waiting",
    running_count,
    waiting_count,
    extra={
      "event": {
        "type": "awaiting-pulp",
        "running-tasks": running_count,
        "waiting-tasks": waiting_count,
      }
    },
  )

Any string may be used as an event type, though a few conventions exist:

.. list-table::
   :widths: 20 40
   :header-rows: 1

   * - ``event.type``
     - Usage
   * - ``<x>-start``
     - The current task has started a step named ``<x>``.
   * - ``<x>-end``
     - Step ``<x>`` completed normally.
   * - ``<x>-error``
     - Step ``<x>`` returned early due to a fatal error.

.. _the setuptools manual: https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html#console-scripts
.. _argmax: https://web.archive.org/web/20210425060951/https://www.in-ulm.de/~mascheck/various/argmax/
.. _pushcollector: https://release-engineering.github.io/pushcollector/
.. _pushsource: https://release-engineering.github.io/pushsource/
.. _ansible tags: http://web.archive.org/web/20210503191336/https://docs.ansible.com/ansible/latest/user_guide/playbooks_tags.html#selecting-or-skipping-tags-when-you-run-a-playbook
