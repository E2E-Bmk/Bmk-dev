"""Six public-API rewrites of upstream behavioral tests.

They are kept separate from generated_tests.py so import provenance remains
auditable.  No private structlog import is used here.
"""
import pytest
import structlog
from structlog.testing import CapturingLogger, capture_logs


@pytest.fixture(autouse=True)
def reset_structlog():
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()


def test_rewrite_get_logger_initial_context():
    with capture_logs() as events:
        structlog.get_logger(a=1).info("e")
    assert events[0]["a"] == 1


def test_rewrite_bind_overrides_prior_value():
    assert structlog.get_context(structlog.get_logger(a=1).bind(a=2))["a"] == 2


def test_rewrite_unbind_removes_present_key():
    assert structlog.get_context(structlog.get_logger(a=1).unbind("a")) == {}


def test_rewrite_capture_records_event_field():
    with capture_logs() as events:
        structlog.get_logger().info("event")
    assert events[0]["event"] == "event"


def test_rewrite_configured_processor_is_called():
    seen = []
    def record(logger, method, event):
        seen.append(method)
        return event
    structlog.configure(processors=[record], logger_factory=CapturingLogger)
    structlog.get_logger().info("event")
    assert seen == ["info"]


def test_rewrite_drop_event_returns_none():
    def drop(logger, method, event):
        raise structlog.DropEvent
    assert structlog.wrap_logger(structlog.ReturnLogger(), processors=[drop]).info("event") is None
