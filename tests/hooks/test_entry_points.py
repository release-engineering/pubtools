import sys

if sys.version_info >= (3, 10):
    from importlib.metadata import EntryPoint
else:
    from importlib_metadata import EntryPoint

from pubtools._impl import pluggy
from pubtools.pluggy import task_context


def test_task_context_loads_entry_points(monkeypatch):
    """task_context eagerly resolves console_scripts and pubtools.hooks entry points."""

    # importlib.metadata.entry_points() reads from installed package metadata;
    # there is no mutable entry map to patch. Patch entry_points in the pluggy
    # module so it returns our custom entry points by group.
    console_scripts = [
        # This one is pubtools.*, so it should be loaded by resolve_hooks.
        EntryPoint("some-script", "pubtools.pluggy", "console_scripts"),
        # This should be ignored (module does not start with "pubtools").
        EntryPoint("other-script", "something.non.existent", "console_scripts"),
    ]
    pubtools_hooks = [
        EntryPoint("anything", "pytest", "pubtools.hooks"),
    ]

    def fake_entry_points(group=None):
        if group == "console_scripts":
            return console_scripts
        if group == "pubtools.hooks":
            return pubtools_hooks
        return []

    monkeypatch.setattr(pluggy, "entry_points", fake_entry_points)

    # Effectively "un-import" these modules so we can observe that task_context
    # has the side-effect of importing them.
    assert "pubtools.pluggy" in sys.modules
    assert "pytest" in sys.modules
    del sys.modules["pubtools.pluggy"]
    del sys.modules["pytest"]

    with task_context():
        # As soon as we've entered the task context, the modules referenced from
        # those entry points should be imported, ensuring we can now use hooks with
        # everything registered
        assert "pubtools.pluggy" in sys.modules
        assert "pytest" in sys.modules
