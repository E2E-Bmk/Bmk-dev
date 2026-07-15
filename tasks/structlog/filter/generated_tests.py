"""Public-API behavioral oracle generated from the structlog specification.

The tests intentionally use only documented imports and observable results.
"""

import io
import logging

import pytest

import structlog
from structlog import contextvars, processors
from structlog.testing import CapturingLogger, capture_logs


@pytest.fixture(autouse=True)
def reset_structlog():
    structlog.reset_defaults()
    contextvars.clear_contextvars()
    yield
    contextvars.clear_contextvars()
    structlog.reset_defaults()


@pytest.mark.parametrize(
    "name",
    [
        "BoundLogger", "BoundLoggerBase", "BytesLogger", "BytesLoggerFactory",
        "DropEvent", "PrintLogger", "PrintLoggerFactory", "ReturnLogger",
        "ReturnLoggerFactory", "WriteLogger", "WriteLoggerFactory", "configure",
        "configure_once", "getLogger", "get_config", "get_context", "get_logger",
        "is_configured", "make_filtering_bound_logger", "reset_defaults", "wrap_logger",
    ],
)
def test_installable_surface(name):
    assert getattr(structlog, name) is not None


@pytest.mark.parametrize("namespace", ["contextvars", "dev", "processors", "stdlib", "testing", "threadlocal", "tracebacks", "types", "typing"])
def test_public_namespaces_importable(namespace):
    assert __import__(f"structlog.{namespace}", fromlist=["*"])


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


def test_drop_event_suppresses_delivery():
    captured = CapturingLogger()
    logger = structlog.wrap_logger(captured, processors=[lambda logger, method, event: (_ for _ in ()).throw(structlog.DropEvent)])
    assert logger.info("hidden") is None
    assert captured.calls == []


def test_invalid_final_processor_result_raises_value_error():
    logger = structlog.wrap_logger(CapturingLogger(), processors=[lambda logger, method, event: 42])
    with pytest.raises(ValueError):
        logger.info("bad")


def test_json_renderer_uses_structlog_method_before_repr():
    class Value:
        def __structlog__(self):
            return {"serialized": True}
    rendered = processors.JSONRenderer()(None, "info", {"value": Value()})
    assert '"serialized": true' in rendered


def test_key_value_renderer_respects_requested_key_order():
    rendered = processors.KeyValueRenderer(key_order=["event", "first"])(None, "info", {"later": 3, "event": "go", "first": 1})
    assert rendered.index("event=") < rendered.index("first=") < rendered.index("later=")


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


def test_capturing_logger_stores_method_args_and_keywords():
    logger = CapturingLogger()
    assert logger.info("hello", answer=42) is None
    call = logger.calls[0]
    assert (call.method_name, call.args, call.kwargs) == ("info", ("hello",), {"answer": 42})


@pytest.mark.parametrize("tool", ["BoundLogger", "LoggerFactory", "filter_by_level", "ProcessorFormatter"])
def test_stdlib_public_tools_importable(tool):
    import structlog.stdlib
    assert getattr(structlog.stdlib, tool) is not None


def test_console_renderer_is_importable():
    assert structlog.dev.ConsoleRenderer is not None


@pytest.mark.parametrize("request_id", ["r1", "r2", "r3"])
def test_representative_context_to_capture_workflow(request_id):
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
    contextvars.bind_contextvars(request_id=request_id)
    with capture_logs(processors=[contextvars.merge_contextvars]) as entries:
        structlog.get_logger(service="billing").info("invoice-created", invoice_id=7)
    assert entries[0] == {"service": "billing", "request_id": request_id, "invoice_id": 7, "event": "invoice-created", "log_level": "info"}
