.. _hooks:

Hooks
=====

.. contents::
    :depth: 3


Overview
--------

pubtools projects can be extended via a hook/event/callback system
based on `pluggy <https://pluggy.readthedocs.io/>`_.

This system is mainly intended for use as a publish-subscribe event dispatcher
and enables the following scenarios:

- When something happens in ``pubtools-foo``, trigger some code in ``pubtools-bar``,
  without ``pubtools-foo`` having a direct dependency on ``pubtools-bar``.

- When something happens in ``pubtools-foo``, trigger some code in
  :ref:`the hosting service <hosted>` if the task is running hosted; otherwise, do
  nothing.

All features provided by pluggy may be used as normal.
The next few sections provide a crash course on basic usage of pluggy.


Guide: hook providers
.....................

If you are implementing a ``pubtools`` project and you want to provide hooks
(which can also be considered "emitting events"), you should do the following:

1. Define hookspecs
~~~~~~~~~~~~~~~~~~~

You need to specify your hooks before using them. This can be done by defining
some functions with ``@hookspec`` decorator.

.. code-block:: python

    # Import the pluggy objects bound to 'pubtools' namespace
    from pubtools.pluggy import pm, hookspec
    import sys

    # Define a hookspec. This is just a plain old function, typically
    # with an empty implementation (only doc string).
    #
    # The doc string should explain the circumstances under which this
    # hook is invoked.

    @hookspec
    def kettle_on(kettle):
        """Called immediately before a kettle is turned on."""

    @hookspec
    def kettle_off(kettle):
        """Called after a kettle has been turned off."""

    # Add these hookspecs onto the plugin manager.
    pm.add_hookspecs(sys.module['__name__'])

Be aware that:

- There is one flat namespace for hooks across all ``pubtools`` projects, so you must
  take care to avoid name clashes

- You must ensure that the module containing your hookspecs is imported when your library
  is imported. If you forget to import the module, your hooks won't be available.


2. Invoke hooks
~~~~~~~~~~~~~~~

At the appropriate times according to the documented behavior of your hooks,
invoke them via ``pm.hook``.

.. code-block:: python

    from pubtools.pluggy import pm

    def make_tea(...):
       kettle.fill_water()

       # notify anyone interested that we're turning the kettle on
       pm.hook.kettle_on(kettle)

       kettle.start_boil()
       kettle.wait_boil()

       # notify again
       pm.hook.kettle_off(kettle)

       # Proceed as normal
       cup.fill_water(source=kettle)
       # (...)

When a hook is called, any plugins with matching registered ``@hookimpls`` will be
invoked in LIFO order. If no plugins have registered, nothing will happen.

The above example shows a pure event emitter. More advanced patterns are possible,
such as making use of values returned by hooks. See the pluggy documentation for
more information.


Guide: hook implementers
........................

If you want to implement hooks (which can also be considered as "receiving events"),
you need to declare hook implementations in your project and register them with
the pubtools plugin manager. Note that it is not necessary for a project to belong
to the ``pubtools`` project family in order to do this.

Hook implementations can be defined using the ``@hookimpl`` decorator. The function
names and signatures should match exactly the names of the corresponding hookspecs.

.. code-block:: python

    # Import the pluggy objects bound to 'pubtools' namespace
    from pubtools.pluggy import pm, hookimpl
    import sys

    # Define a hookimpl. Match exactly the hookspecs declared
    # in the previous example.

    @hookimpl
    def kettle_on(kettle):
        # Kettle causes huge spike in power consumption, we'd better
        # enable the power reserves.
        # https://en.wikipedia.org/wiki/TV_pickup
        powerbank.enable()

    @hookimpl
    def kettle_off(kettle):
        # Don't need the extra power any more
        powerbank.disable()

    # Register this module as a plugin.
    pm.register(sys.modules['__name__'])

Be aware that:

- Your hookimpl could be invoked by any thread. Blocking the current thread
  may be inappropriate. It's best to do only small amounts of work
  within a hookimpl.

- If your hookimpl raises an exception, it will propagate upwards through
  to the hook caller.


Guide: managing context
.......................

In the above naive example, hookimpls are standalone functions within a module,
with no mechanism for passing context between themselves.
For instance, the above example can't maintain a count of boiling kettles
(excluding antipatterns such as mutating globals).

A more realistic approach of registering hookimpls which allows passing around
some context is to register your plugins in a two-stage process:

- First, attach to some initial event allowing you to establish context.
  pubtools provides :func:`task_start` for this purpose.

- When that hook is invoked, set up desired context and then register additional hooks.

.. code-block:: python

    # Import the pluggy objects bound to 'pubtools' namespace
    from pubtools.pluggy import pm, hookimpl
    import sys

    class KettleSpikeHandler:
        def __init__(self):
            # Do anything I like here - configure myself from
            # settings, etc.
            self.powerbank = (...)

            # We can now maintain state between hookimpls.
            self.kettlecount = 0

        # Instance methods work OK for hookimpls.

        @hookimpl
        def kettle_on(self, kettle):
            self.kettlecount += 1
            self.powerbank.enable()

        @hookimpl
        def kettle_off(self, kettle):
            self.kettlecount -= 1
            if not self.kettlecount:
                self.powerbank.disable()

    @hookimpl
    def task_start():
        # When task starts, we register an instance of this object
        # as an additional plugin. This allows the object to keep
        # its own state between calls to different hookimpls.
        pm.register(KettleSpikeHandler())

    # Register this module as a plugin.
    # This will only register the top-level 'task_start' hookimpl.
    pm.register(sys.modules['__name__'])


:func:`task_start` and :func:`task_stop` are two standard hooks intended for
use in setting up or tearing down a plugin context. Note that these are only
conventions and may not be used uniformly across all pubtools task libraries.


API reference
-------------

.. py:attribute:: pubtools.pluggy.pm

  :type: :class:`pluggy.PluginManager`

  A PluginManager configured for the ``pubtools`` namespace.


.. py:attribute:: pubtools.pluggy.hookspec

  A hookspec decorator configured for the ``pubtools`` namespace.


.. py:attribute:: pubtools.pluggy.hookimpl

  A hookimpl decorator configured for the ``pubtools`` namespace.


.. autofunction:: pubtools.pluggy.task_context



Hook reference
--------------

This section lists all known hooks defined in the pubtools
namespace.

.. include:: _build/hooks
