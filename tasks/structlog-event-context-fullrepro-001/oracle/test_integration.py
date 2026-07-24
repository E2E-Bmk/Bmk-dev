"""Public behavioral oracle for the structlog task."""

import io
import json
import logging

import pytest

import structlog
from structlog import contextvars, dev, processors, stdlib
from structlog.testing import CapturingLogger, capture_logs


def test_bind_is_immutable_and_merges_values():
    """Seam: state consistency — bind creates new logger without mutating original context."""
    original = structlog.get_logger(service="web")
    changed = original.bind(request_id="r1")
    assert structlog.get_context(original) == {"service": "web"}
    assert structlog.get_context(changed) == {"service": "web", "request_id": "r1"}


def test_try_unbind_ignores_missing_key():
    """Seam: protocol handoff — try_unbind silently skips absent keys."""
    logger = structlog.get_logger(a=1).try_unbind("missing")
    assert structlog.get_context(logger) == {"a": 1}


def test_new_replaces_local_context():
    """Seam: state consistency — new() replaces bound context while preserving logger identity."""
    logger = structlog.get_logger().bind(old=1).new(current=2)
    assert structlog.get_context(logger) == {"current": 2}


def test_get_context_is_live_for_compatible_logger():
    """Seam: state consistency — get_context view reflects live bound-context mutations."""
    logger = structlog.get_logger(a=1)
    context = structlog.get_context(logger)
    context["b"] = 2
    assert structlog.get_context(logger)["b"] == 2


@pytest.mark.parametrize("method", ["debug", "info", "warning", "error", "critical"])
def test_log_call_assembles_context_event_and_normalized_level(method):
    """Seam: protocol handoff — bound context + log call → normalized event dict."""
    with capture_logs() as entries:
        getattr(structlog.get_logger(bound=1), method)("event-name", call=2)
    assert entries == [{"bound": 1, "call": 2, "event": "event-name", "log_level": method}]


@pytest.mark.parametrize("level", [logging.DEBUG, "debug", "INFO", logging.WARNING, "error", "critical", "notset"])
def test_filtering_bound_logger_accepts_documented_levels(level):
    """Seam: config interaction — filtering wrapper accepts documented level inputs."""
    wrapper = structlog.make_filtering_bound_logger(level)
    structlog.configure(wrapper_class=wrapper)
    with capture_logs() as entries:
        structlog.get_logger().critical("kept")
    assert entries[0]["event"] == "kept"


def test_filtering_bound_logger_suppresses_lower_level_delivery():
    """Seam: config interaction — INFO threshold suppresses DEBUG delivery."""
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
    with capture_logs() as entries:
        result = structlog.get_logger().debug("hidden")
    assert result is None
    assert entries == []


def test_processor_chain_passes_result_to_delivery():
    """Seam: protocol handoff — processor chain output reaches wrapped logger delivery."""
    captured = CapturingLogger()
    logger = structlog.wrap_logger(captured, processors=[lambda logger, method, event: "rendered"])
    logger.info("original", value=1)
    assert captured.calls[0].method_name == "info"
    assert captured.calls[0].args == ("rendered",)


def test_invalid_final_processor_result_raises_value_error():
    """Seam: error propagation — non-str/non-dict processor result raises ValueError."""
    logger = structlog.wrap_logger(CapturingLogger(), processors=[lambda logger, method, event: 42])
    with pytest.raises(ValueError):
        logger.info("bad")


def test_bind_contextvars_returns_tokens_and_get_returns_copy():
    """Seam: state consistency — bind_contextvars tokens ↔ get_contextvars copy isolation."""
    tokens = contextvars.bind_contextvars(request_id="r1")
    copied = contextvars.get_contextvars()
    copied["request_id"] = "changed"
    assert set(tokens) == {"request_id"}
    assert contextvars.get_contextvars() == {"request_id": "r1"}


def test_merge_contextvars_preserves_event_precedence():
    """Seam: config interaction — merge_contextvars prefers event dict over contextvars."""
    contextvars.bind_contextvars(shared="context", only_context="yes")
    event = contextvars.merge_contextvars(None, "info", {"shared": "event"})
    assert event == {"shared": "event", "only_context": "yes"}


def test_get_merged_contextvars_prefers_bound_logger_values():
    """Seam: config interaction — bound logger values override contextvars on conflict."""
    contextvars.bind_contextvars(shared="context", context_only=1)
    merged = contextvars.get_merged_contextvars(structlog.get_logger(shared="local", local_only=2))
    assert merged == {"shared": "local", "context_only": 1, "local_only": 2}


def test_bound_contextvars_restores_values_after_normal_exit():
    """Seam: lifecycle crossing — bound_contextvars restores prior context on exit."""
    contextvars.bind_contextvars(existing="before")
    with contextvars.bound_contextvars(existing="during", new="value"):
        assert contextvars.get_contextvars() == {"existing": "during", "new": "value"}
    assert contextvars.get_contextvars() == {"existing": "before"}


def test_bound_contextvars_restores_values_after_exception():
    """Seam: lifecycle crossing — bound_contextvars restores context after exception."""
    with pytest.raises(RuntimeError):
        with contextvars.bound_contextvars(temporary=True):
            raise RuntimeError("stop")
    assert contextvars.get_contextvars() == {}


@pytest.mark.parametrize("method", ["debug", "info", "warning", "error", "critical"])
def test_capture_logs_records_normalized_method(method):
    """Seam: protocol handoff — capture_logs records normalized method and event field."""
    with capture_logs() as entries:
        getattr(structlog.get_logger(), method)("captured")
    assert entries[0]["event"] == "captured"
    assert entries[0]["log_level"] == method


def test_capture_logs_runs_supplied_processors_before_capture():
    """Seam: protocol handoff — capture_logs applies custom processors before recording."""
    def add_marker(logger, method, event):
        event["marker"] = method
        return event
    with capture_logs(processors=[add_marker]) as entries:
        structlog.get_logger().info("captured")
    assert entries[0]["marker"] == "info"


@pytest.mark.parametrize("request_id", ["r1", "r2", "r3"])
def test_representative_context_to_capture_workflow(request_id):
    """Seam: lifecycle crossing — contextvars + filtering + merge + capture end-to-end."""
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
    contextvars.bind_contextvars(request_id=request_id)
    with capture_logs(processors=[contextvars.merge_contextvars]) as entries:
        structlog.get_logger(service="billing").info("invoice-created", invoice_id=7)
    assert entries[0] == {"service": "billing", "request_id": request_id, "invoice_id": 7, "event": "invoice-created", "log_level": "info"}


def test_processor_formatter_requires_a_processor_configuration():
    """Seam: error propagation — ProcessorFormatter without processors raises TypeError."""
    with pytest.raises(TypeError):
        stdlib.ProcessorFormatter()


def test_rewrite_get_logger_initial_context():
    """Seam: state consistency — get_logger initial kwargs appear in captured event."""
    with capture_logs() as events:
        structlog.get_logger(a=1).info("e")
    assert events[0]["a"] == 1


def test_rewrite_bind_overrides_prior_value():
    """Seam: state consistency — bind overrides existing context key value."""
    assert structlog.get_context(structlog.get_logger(a=1).bind(a=2))["a"] == 2


def test_rewrite_unbind_removes_present_key():
    """Seam: state consistency — unbind removes key from logger context."""
    assert structlog.get_context(structlog.get_logger(a=1).unbind("a")) == {}


def test_rewrite_capture_records_event_field():
    """Seam: protocol handoff — capture_logs preserves event field from info call."""
    with capture_logs() as events:
        structlog.get_logger().info("event")
    assert events[0]["event"] == "event"


def test_rewrite_configured_processor_is_called():
    """Seam: protocol handoff — configured processor invoked with method name."""
    seen = []
    def record(logger, method, event):
        seen.append(method)
        return event
    structlog.configure(processors=[record], logger_factory=CapturingLogger)
    structlog.get_logger().info("event")
    assert seen == ["info"]


def test_getLogger_passes_factory_args_and_initial_values_to_the_event():
    """Seam: protocol handoff — configure + getLogger + info assemble factory event."""
    factory = RecordingReturnLoggerFactory()
    structlog.reset_defaults()
    try:
        structlog.configure(processors=(), logger_factory=factory)

        result = structlog.getLogger("audit", component="api").info(
            "ready", request_id=7
        )

        assert factory.calls == [("audit",)]
        assert result == (
            (),
            {"component": "api", "request_id": 7, "event": "ready"},
        )
    finally:
        structlog.reset_defaults()

def test_getLogger_matches_get_logger_for_factory_arguments_and_event_assembly():
    """Seam: protocol handoff — getLogger and get_logger share factory event assembly."""
    factory = RecordingReturnLoggerFactory()
    structlog.reset_defaults()
    try:
        structlog.configure(processors=(), logger_factory=factory)

        from_alias = structlog.getLogger("same", scope="worker").warning(
            "alert", code=4
        )
        from_canonical_name = structlog.get_logger("same", scope="worker").warning(
            "alert", code=4
        )

        assert factory.calls == [("same",), ("same",)]
        assert from_alias == from_canonical_name
        assert from_alias == (
            (),
            {"scope": "worker", "code": 4, "event": "alert"},
        )
    finally:
        structlog.reset_defaults()

def test_getLogger_defers_and_propagates_logger_factory_failure():
    """Seam: error propagation — logger factory failure deferred until log call."""
    class FactoryFailure(Exception):
        pass

    calls = []

    def failing_factory(*args):
        calls.append(args)
        raise FactoryFailure()

    structlog.reset_defaults()
    try:
        structlog.configure(processors=(), logger_factory=failing_factory)

        logger = structlog.getLogger("deferred")
        assert calls == []

        try:
            logger.info("later")
        except FactoryFailure:
            pass
        else:
            raise AssertionError("logger-factory failure was not propagated")

        assert calls == [("deferred",)]
    finally:
        structlog.reset_defaults()

def test_recreate_defaults_configures_standard_logging_at_requested_level(capsys):
    """Seam: config interaction — recreate_defaults wires stdlib logging output."""
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level
    structlog.reset_defaults()
    try:
        stdlib.recreate_defaults(log_level=logging.INFO)
        assert root.level == logging.INFO

        structlog.get_logger().info("recreated-through-logging")
        assert "recreated-through-logging" in capsys.readouterr().out
    finally:
        root.handlers = old_handlers
        root.setLevel(old_level)
        structlog.reset_defaults()

# --- composition fix additions (2026-07-20) ---


def test_logging_call_keyword_overrides_bound_context_value():
    """Seam: config interaction — log-call keyword overrides bound context value."""
    logger = structlog.get_logger().bind(color="blue")
    with capture_logs() as entries:
        logger.info("painted", color="red")
    assert entries == [{"color": "red", "event": "painted", "log_level": "info"}]


def test_clear_contextvars_removes_fields_from_later_merged_events():
    """Seam: lifecycle crossing — clear_contextvars stops fields in later merged events."""
    contextvars.bind_contextvars(request_id="r-1")
    with capture_logs(processors=[contextvars.merge_contextvars]) as first:
        structlog.get_logger().info("before")
    contextvars.clear_contextvars()
    with capture_logs(processors=[contextvars.merge_contextvars]) as second:
        structlog.get_logger().info("later")
    assert first == [{"request_id": "r-1", "event": "before", "log_level": "info"}]
    assert second == [{"event": "later", "log_level": "info"}]


def test_processor_chain_delivers_rendered_json_string_to_wrapped_logger():
    """Seam: protocol handoff — processor chain renders JSON string to wrapped logger."""
    captured = CapturingLogger()
    logger = structlog.wrap_logger(
        captured, processors=[processors.add_log_level, processors.JSONRenderer()]
    )
    logger.info("saved", a=1)
    call = captured.calls[0]
    assert call.method_name == "info"
    assert json.loads(call.args[0]) == {"event": "saved", "a": 1, "level": "info"}
