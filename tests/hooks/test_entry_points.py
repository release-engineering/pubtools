import sys

from importlib import metadata
from importlib.metadata import EntryPoint

from pubtools.pluggy import task_context


def test_task_context_loads_entry_points(monkeypatch):
    """task_context eagerly resolves console_scripts and pubtools.hooks entry points."""

    target_mod = "pydoc"

    # Define the mock entry points EntryPoint(name, value, group)
    ep1 = EntryPoint(name="some-script", value="pubtools.pluggy", group="console_scripts")
    ep2 = EntryPoint(name="anything", value=target_mod, group="pubtools.hooks")

    mock_entry_points = [ep1, ep2]

    # Monkeypatch metadata.entry_points globally
    # In the new API, mock the function that task_context() will call
    def mock_eps(**kwargs):
        group = kwargs.get("group")
        if group:
            return [ep for ep in mock_entry_points if ep.group == group]
        return metadata.EntryPoints(mock_entry_points)

    monkeypatch.setattr(metadata, "entry_points", mock_eps)

    # "un-import" these modules (Ensure they are in sys.modules first so del doesn't fail, 
    # though usually they are already there from imports above)
    for mod in ["pubtools.pluggy", target_mod]:
        if mod in sys.modules:
            del sys.modules[mod]

    with task_context():
        # As soon as we've entered the task context, the modules referenced from
        # those entry points should be imported, ensuring we can now use hooks with
        # everything registered
        assert "pubtools.pluggy" in sys.modules
        assert target_mod in sys.modules