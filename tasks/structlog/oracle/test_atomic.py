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


class RecordingReturnLoggerFactory:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return structlog.ReturnLogger()


def test_reset_defaults_restores_unconfigured_state():
    structlog.configure(processors=[])
    assert structlog.is_configured() is True
    structlog.reset_defaults()
    assert structlog.is_configured() is False


def test_configure_preserves_unspecified_defaults_and_returns_independent_mapping():
    before = structlog.get_config()
    marker = lambda logger, method, event: event
    structlog.configure(processors=[marker])
    after = structlog.get_config()
    assert after["processors"] == [marker]
    assert after["context_class"] is before["context_class"]
    after["processors"] = []
    assert structlog.get_config()["processors"] == [marker]


def test_configure_once_warns_and_does_not_replace_existing_settings():
    first = lambda logger, method, event: event
    second = lambda logger, method, event: event
    structlog.configure(processors=[first])
    with pytest.warns(RuntimeWarning):
        structlog.configure_once(processors=[second])
    assert structlog.get_config()["processors"] == [first]


def test_getlogger_alias_matches_get_logger_behavior():
    with capture_logs() as entries:
        structlog.getLogger(component="api").info("started")
    assert entries[0]["component"] == "api"
    assert entries[0]["event"] == "started"


def test_drop_event_suppresses_delivery():
    captured = CapturingLogger()
    logger = structlog.wrap_logger(captured, processors=[lambda logger, method, event: (_ for _ in ()).throw(structlog.DropEvent)])
    assert logger.info("hidden") is None
    assert captured.calls == []


def test_json_renderer_uses_structlog_method_before_repr():
    class Value:
        def __structlog__(self):
            return {"serialized": True}
    rendered = processors.JSONRenderer()(None, "info", {"value": Value()})
    assert '"serialized": true' in rendered


def test_key_value_renderer_respects_requested_key_order():
    rendered = processors.KeyValueRenderer(key_order=["event", "first"])(None, "info", {"later": 3, "event": "go", "first": 1})
    assert rendered.index("event=") < rendered.index("first=") < rendered.index("later=")


@pytest.mark.parametrize("args,kwargs,expected", [(('one',), {}, 'one'), (('one', 'two'), {}, (("one", "two"), {})), ((), {"x": 1}, ((), {"x": 1})), (("one",), {"x": 1}, (("one",), {"x": 1}))])
def test_return_logger_return_contract(args, kwargs, expected):
    assert structlog.ReturnLogger().msg(*args, **kwargs) == expected


@pytest.mark.parametrize("logger_type,message,expected", [(structlog.PrintLogger, "text", "text\n"), (structlog.WriteLogger, "text", "text\n")])
def test_text_output_loggers_write_newline(logger_type, message, expected):
    stream = io.StringIO()
    logger_type(stream).msg(message)
    assert stream.getvalue() == expected


def test_bytes_logger_writes_newline_bytes():
    stream = io.BytesIO()
    structlog.BytesLogger(stream).msg(b"bytes")
    assert stream.getvalue() == b"bytes\n"


def test_capturing_logger_stores_method_args_and_keywords():
    logger = CapturingLogger()
    assert logger.info("hello", answer=42) is None
    call = logger.calls[0]
    assert (call.method_name, call.args, call.kwargs) == ("info", ("hello",), {"answer": 42})


def test_getLogger_passes_factory_args_and_initial_values_to_the_event():
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


def test_stdlib_filter_by_level_returns_the_supplied_event_when_accepted():
    logger = logging.getLogger("structlog-stage3-accepted")
    logger.setLevel(logging.DEBUG)
    event = {"event": "accepted"}

    assert stdlib.filter_by_level(logger, "debug", event) is event


def test_stdlib_filter_by_level_drops_an_event_when_rejected():
    logger = logging.getLogger("structlog-stage3-rejected")
    logger.setLevel(logging.INFO)

    with pytest.raises(structlog.DropEvent):
        stdlib.filter_by_level(logger, "debug", {"event": "rejected"})


def test_console_renderer_returns_human_readable_event_text_without_colors():
    rendered = dev.ConsoleRenderer(colors=False)(None, "info", {"event": "hello-console"})

    assert isinstance(rendered, str)
    assert "hello-console" in rendered


def test_recreate_defaults_configures_standard_logging_at_requested_level(capsys):
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


def test_rewrite_drop_event_returns_none():
    def drop(logger, method, event):
        raise structlog.DropEvent
    assert structlog.wrap_logger(structlog.ReturnLogger(), processors=[drop]).info("event") is None
