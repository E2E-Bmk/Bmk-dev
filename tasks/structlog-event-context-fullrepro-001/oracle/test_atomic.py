"""Public behavioral oracle for the structlog task."""

import io
import json
import logging

import pytest

import structlog
from structlog import contextvars, dev, processors, stdlib
from structlog.testing import CapturingLogger, capture_logs

from conftest import RecordingReturnLoggerFactory


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




def test_rewrite_drop_event_returns_none():
    def drop(logger, method, event):
        raise structlog.DropEvent
    assert structlog.wrap_logger(structlog.ReturnLogger(), processors=[drop]).info("event") is None


# --- composition fix additions (2026-07-20) ---


def test_add_log_level_adds_normalized_level_key():
    event_dict = processors.add_log_level(None, "info", {"event": "x"})
    assert event_dict == {"event": "x", "level": "info"}


def test_json_renderer_renders_event_dict_as_json_text():
    rendered = processors.JSONRenderer()(None, "info", {"event": "go", "n": 1})
    assert json.loads(rendered) == {"event": "go", "n": 1}


def test_print_logger_factory_builds_logger_ignoring_positional_args():
    stream = io.StringIO()
    logger = structlog.PrintLoggerFactory(stream)("ignored", "args")
    logger.msg("factory-made")
    assert stream.getvalue() == "factory-made\n"


def test_unbind_reports_missing_key():
    with pytest.raises(KeyError):
        structlog.get_logger().unbind("missing")


def test_filtering_bound_logger_rejects_unknown_level_name():
    with pytest.raises(KeyError):
        structlog.make_filtering_bound_logger("loud")

# --- supplemental atomic tests (2026-07-23) ---

def test_write_logger_raises_type_error_for_non_string_message():
    stream = io.StringIO()
    with pytest.raises(TypeError):
        structlog.WriteLogger(stream).msg(12345)

def test_bytes_logger_raises_type_error_for_non_bytes_message():
    stream = io.BytesIO()
    with pytest.raises(TypeError):
        structlog.BytesLogger(stream).msg("not-bytes")

def test_bytes_logger_accepts_optional_name_argument():
    stream = io.BytesIO()
    logger = structlog.BytesLogger(stream, name="custom")
    logger.msg(b"data")
    assert stream.getvalue() == b"data\n"

def test_key_value_renderer_omits_absent_requested_key():
    rendered = processors.KeyValueRenderer(
        key_order=["event", "missing_key"], drop_missing=True
    )(
        None, "info", {"event": "go", "extra": 2}
    )
    assert "missing_key" not in rendered
    assert "event=" in rendered
    assert "extra=" in rendered

def test_return_logger_factory_reuses_single_instance():
    with pytest.raises(TypeError):
        structlog.ReturnLoggerFactory("unsupported")
    factory = structlog.ReturnLoggerFactory()
    first = factory()
    second = factory("ignored-arg")
    assert first is second
    assert isinstance(first, structlog.ReturnLogger)

def test_write_logger_factory_creates_write_logger():
    stream = io.StringIO()
    factory = structlog.WriteLoggerFactory(stream)
    logger = factory("positional", "ignored")
    logger.msg("factory-line")
    assert stream.getvalue() == "factory-line\n"
    assert isinstance(logger, structlog.WriteLogger)

def test_bytes_logger_factory_creates_bytes_logger():
    stream = io.BytesIO()
    factory = structlog.BytesLoggerFactory(stream)
    logger = factory("positional")
    logger.msg(b"factory-bytes")
    assert stream.getvalue() == b"factory-bytes\n"
    assert isinstance(logger, structlog.BytesLogger)

def test_log_capture_appends_entry_and_raises_drop_event():
    from structlog.testing import LogCapture
    lc = LogCapture()
    with pytest.raises(structlog.DropEvent):
        lc(None, "warning", {"event": "captured", "value": 3})
    assert lc.entries == [
        {"event": "captured", "value": 3, "log_level": "warning"}
    ]

def test_timestamper_adds_timestamp_to_event():
    timestamper = processors.TimeStamper()
    result = timestamper(None, "info", {"event": "go"})
    assert "timestamp" in result
    assert result["event"] == "go"

def test_console_renderer_renders_true_exc_info_after_log_line():
    import sys
    try:
        raise ValueError("test-exc-94")
    except ValueError:
        exc = sys.exc_info()
    rendered = dev.ConsoleRenderer(colors=False)(
        None, "error", {"event": "crash", "exc_info": exc}
    )
    event_position = rendered.index("crash")
    exception_position = rendered.index("ValueError: test-exc-94")
    assert event_position < exception_position
