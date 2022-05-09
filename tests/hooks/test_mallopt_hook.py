import os
import ctypes

import pytest

from pubtools._impl import mallopt


class FakeMallopt(object):
    def __init__(self, return_value=1):
        self.calls = []
        self.return_value = return_value

    def __call__(self, flag, value):
        self.calls.append((flag, value))
        return self.return_value


class FakeLibc(object):
    def __init__(self):
        self.mallopt = FakeMallopt()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # Ensure all the malloc tuning env vars are unset (since they potentially
    # could be set in the test execution environment)
    for var in (
        "MALLOC_ARENA_MAX",
        "MALLOC_ARENA_TEST",
        "MALLOC_MMAP_MAX_",
        "MALLOC_MMAP_THRESHOLD_",
        "MALLOC_PERTURB_",
        "MALLOC_TRIM_THRESHOLD_",
        "MALLOC_TOP_PAD_",
    ):
        if var in os.environ:
            monkeypatch.delenv(var)


def test_tune_noopt(caplog):
    """Hook should do nothing (successfully) when no vars are set"""
    mallopt.task_start()

    assert caplog.records == []


def test_tune_calls_mallopt(monkeypatch):
    """Hook should call mallopt() for the present env vars"""
    fake_libc = FakeLibc()
    monkeypatch.setattr(ctypes.cdll, "LoadLibrary", lambda _: fake_libc)

    monkeypatch.setenv("MALLOC_ARENA_MAX", "2")
    monkeypatch.setenv("MALLOC_MMAP_MAX_", "123")

    mallopt.task_start()

    # Should have made the expected calls
    assert sorted(fake_libc.mallopt.calls) == [
        (mallopt.M_ARENA_MAX, 2),
        (mallopt.M_MMAP_MAX, 123),
    ]


def test_logs_on_failure(caplog, monkeypatch):
    """Hook should warn on failure"""
    fake_libc = FakeLibc()
    monkeypatch.setattr(ctypes.cdll, "LoadLibrary", lambda _: fake_libc)

    # Simulate that calls to mallopt() fail
    fake_libc.mallopt.return_value = 0

    monkeypatch.setenv("MALLOC_ARENA_MAX", "2")
    monkeypatch.setenv("MALLOC_MMAP_MAX_", "123")

    mallopt.task_start()

    # It should have complained
    assert "Failed to configure malloc" in caplog.text
