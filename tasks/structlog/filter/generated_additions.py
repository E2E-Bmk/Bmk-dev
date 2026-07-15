"""Track-B additions derived from the v3 public candidate specification only."""

import logging

import pytest
import structlog
from structlog import dev, stdlib


class RecordingReturnLoggerFactory:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return structlog.ReturnLogger()


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


def test_processor_formatter_requires_a_processor_configuration():
    with pytest.raises(TypeError):
        stdlib.ProcessorFormatter()


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
