"""Public behavioral oracle for the structlog task."""

import io
import logging

import pytest

import structlog
from structlog import contextvars, dev, processors, stdlib
from structlog.testing import CapturingLogger, capture_logs


@pytest.fixture(autouse=True)
def reset_structlog():
    structlog.reset_defaults()
    contextvars.clear_contextvars()
    yield
    contextvars.clear_contextvars()
    structlog.reset_defaults()


def test_bind_is_immutable_and_merges_values():
    original = structlog.get_logger(service="web")
    changed = original.bind(request_id="r1")
    assert structlog.get_context(original) == {"service": "web"}
    assert structlog.get_context(changed) == {"service": "web", "request_id": "r1"}


def test_unbind_reports_missing_key():
    with pytest.raises(KeyError):
        structlog.get_logger().unbind("missing")


def test_try_unbind_ignores_missing_key():
    logger = structlog.get_logger(a=1).try_unbind("missing")
    assert structlog.get_context(logger) == {"a": 1}


def test_new_replaces_local_context():
    logger = structlog.get_logger().bind(old=1).new(current=2)
    assert structlog.get_context(logger) == {"current": 2}


def test_get_context_is_live_for_compatible_logger():
    logger = structlog.get_logger(a=1)
    context = structlog.get_context(logger)
    context["b"] = 2
    assert structlog.get_context(logger)["b"] == 2


@pytest.mark.parametrize("method", ["debug", "info", "warning", "error", "critical"])
def test_log_call_assembles_context_event_and_normalized_level(method):
    with capture_logs() as entries:
        getattr(structlog.get_logger(bound=1), method)("event-name", call=2)
    assert entries == [{"bound": 1, "call": 2, "event": "event-name", "log_level": method}]


@pytest.mark.parametrize("level", [logging.DEBUG, "debug", "INFO", logging.WARNING, "error", "critical", "notset"])
def test_filtering_bound_logger_accepts_documented_levels(level):
    wrapper = structlog.make_filtering_bound_logger(level)
    structlog.configure(wrapper_class=wrapper)
    with capture_logs() as entries:
        structlog.get_logger().critical("kept")
    assert entries[0]["event"] == "kept"


def test_filtering_bound_logger_rejects_unknown_level_name():
    with pytest.raises(KeyError):
        structlog.make_filtering_bound_logger("loud")


def test_filtering_bound_logger_suppresses_lower_level_delivery():
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
    with capture_logs() as entries:
        result = structlog.get_logger().debug("hidden")
    assert result is None
    assert entries == []


def test_processor_chain_passes_result_to_delivery():
    captured = CapturingLogger()
    logger = structlog.wrap_logger(captured, processors=[lambda logger, method, event: "rendered"])
    logger.info("original", value=1)
    assert captured.calls[0].method_name == "info"
    assert captured.calls[0].args == ("rendered",)


def test_invalid_final_processor_result_raises_value_error():
    logger = structlog.wrap_logger(CapturingLogger(), processors=[lambda logger, method, event: 42])
    with pytest.raises(ValueError):
        logger.info("bad")


def test_bind_contextvars_returns_tokens_and_get_returns_copy():
    tokens = contextvars.bind_contextvars(request_id="r1")
    copied = contextvars.get_contextvars()
    copied["request_id"] = "changed"
    assert set(tokens) == {"request_id"}
    assert contextvars.get_contextvars() == {"request_id": "r1"}


def test_merge_contextvars_preserves_event_precedence():
    contextvars.bind_contextvars(shared="context", only_context="yes")
    event = contextvars.merge_contextvars(None, "info", {"shared": "event"})
    assert event == {"shared": "event", "only_context": "yes"}


def test_get_merged_contextvars_prefers_bound_logger_values():
    contextvars.bind_contextvars(shared="context", context_only=1)
    merged = contextvars.get_merged_contextvars(structlog.get_logger(shared="local", local_only=2))
    assert merged == {"shared": "local", "context_only": 1, "local_only": 2}


def test_bound_contextvars_restores_values_after_normal_exit():
    contextvars.bind_contextvars(existing="before")
    with contextvars.bound_contextvars(existing="during", new="value"):
        assert contextvars.get_contextvars() == {"existing": "during", "new": "value"}
    assert contextvars.get_contextvars() == {"existing": "before"}


def test_bound_contextvars_restores_values_after_exception():
    with pytest.raises(RuntimeError):
        with contextvars.bound_contextvars(temporary=True):
            raise RuntimeError("stop")
    assert contextvars.get_contextvars() == {}


@pytest.mark.parametrize("method", ["debug", "info", "warning", "error", "critical"])
def test_capture_logs_records_normalized_method(method):
    with capture_logs() as entries:
        getattr(structlog.get_logger(), method)("captured")
    assert entries[0]["event"] == "captured"
    assert entries[0]["log_level"] == method


def test_capture_logs_runs_supplied_processors_before_capture():
    def add_marker(logger, method, event):
        event["marker"] = method
        return event
    with capture_logs(processors=[add_marker]) as entries:
        structlog.get_logger().info("captured")
    assert entries[0]["marker"] == "info"


@pytest.mark.parametrize("request_id", ["r1", "r2", "r3"])
def test_representative_context_to_capture_workflow(request_id):
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
    contextvars.bind_contextvars(request_id=request_id)
    with capture_logs(processors=[contextvars.merge_contextvars]) as entries:
        structlog.get_logger(service="billing").info("invoice-created", invoice_id=7)
    assert entries[0] == {"service": "billing", "request_id": request_id, "invoice_id": 7, "event": "invoice-created", "log_level": "info"}


def test_processor_formatter_requires_a_processor_configuration():
    with pytest.raises(TypeError):
        stdlib.ProcessorFormatter()


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
