import sys

from pkg_resources import EntryPoint, get_distribution

from pubtools.pluggy import task_context


def test_task_context_loads_entry_points(monkeypatch):
    """task_context eagerly resolves console_scripts and pubtools.hooks entry points."""

    # Need some valid distribution to use here; don't care which one.
    # Just pick something we know is installed.
    dist = get_distribution("pytest")

    entry_map = dist.get_entry_map()

    # This group already exists in pytest.
    scripts = entry_map["console_scripts"]

    # This is a new group we'll force onto the map.
    hooks = {}
    monkeypatch.setitem(entry_map, "pubtools.hooks", hooks)

    # Set up some console scripts entry points. We'll make them point at existing
    # modules so that an import will succeed.
    #
    # This one is pubtools.* , so it should be imported
    monkeypatch.setitem(
        scripts, "some-script", EntryPoint("some-script", "pubtools.pluggy")
    )

    # This should be ignored
    monkeypatch.setitem(
        scripts, "other-script", EntryPoint("other-script", "something.non.existent")
    )

    # Set up a hook entry point.
    monkeypatch.setitem(hooks, "anything", EntryPoint("anything", "pytest"))

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
