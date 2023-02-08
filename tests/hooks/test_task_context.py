import sys

import pytest

from pubtools.pluggy import hookimpl, pm, task_context


class EventSpy(object):
    def __init__(self):
        self.events = []

    @hookimpl
    def task_start(self):
        self.events.append("task_start")

    @hookimpl
    def task_stop(self, failed):
        self.events.append(("task_stop", failed))


@pytest.fixture
def spy():
    instance = EventSpy()
    pm.register(instance)
    yield instance
    pm.unregister(instance)


def test_task_ok(spy):
    """task_context emits expected events during successful non-exit case"""

    # Initially no events
    assert not spy.events

    # Simulate a task
    with task_context():
        # task_start should have already been fired
        assert spy.events == ["task_start"]

    # Task is now done, and it didn't fail
    assert spy.events == ["task_start", ("task_stop", False)]


def test_task_exit_ok(spy):
    """task_context emits expected events during successful exit case"""

    # Initially no events
    assert not spy.events

    with pytest.raises(SystemExit):
        with task_context():
            # task_start should have already been fired
            assert spy.events == ["task_start"]

            # exit successfully
            sys.exit(0)

    # Task is now done, and it didn't fail
    assert spy.events == ["task_start", ("task_stop", False)]


def test_task_exit_failed(spy):
    """task_context emits expected events during unsuccessful exit case"""

    # Initially no events
    assert not spy.events

    with pytest.raises(SystemExit):
        with task_context():
            # task_start should have already been fired
            assert spy.events == ["task_start"]

            # exit unsuccessfully
            sys.exit(12)

    # Task is now done, and it failed
    assert spy.events == ["task_start", ("task_stop", True)]


def test_task_raised(spy):
    """task_context emits expected events during unsuccessful raising case"""

    # Initially no events
    assert not spy.events

    with pytest.raises(RuntimeError):
        with task_context():
            # task_start should have already been fired
            assert spy.events == ["task_start"]

            raise RuntimeError("something went wrong")

    # Task is now done, and it failed
    assert spy.events == ["task_start", ("task_stop", True)]
