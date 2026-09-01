from __future__ import annotations


def test_a01(tmp_path):
    import structlog
    structlog.reset_defaults()
    before = structlog.get_config()
    assert isinstance(before["processors"], list)
    marker = lambda logger, method, event: event
    structlog.configure(processors=[marker], cache_logger_on_first_use=False)
    first = structlog.get_config()
    second = structlog.get_config()
    assert first["processors"] is second["processors"] and second["processors"] == [marker]
    assert second["cache_logger_on_first_use"] is False
    structlog.reset_defaults()


def test_a02(tmp_path):
    import structlog
    base = structlog.wrap_logger(structlog.ReturnLogger(), processors=[]).bind(owner="base")
    child = base.bind(owner="child", value=2)
    assert base.info("base") == ((), {"owner": "base", "event": "base"})
    assert child.info("child") == ((), {"owner": "child", "value": 2, "event": "child"})


def test_a03(tmp_path):
    import structlog
    logger = structlog.ReturnLogger()
    assert logger.info("message") == "message"
    assert logger.info("message", x=1) == (("message",), {"x": 1})
    assert logger.info(x=1) == ((), {"x": 1})


def test_a04(tmp_path):
    from structlog.processors import UnicodeDecoder, UnicodeEncoder
    encoded = UnicodeEncoder("utf-8")(None, "info", {"text": "café", "n": 1})
    assert encoded == {"text": "café".encode(), "n": 1}
    decoded = UnicodeDecoder("utf-8")(None, "info", encoded)
    assert decoded == {"text": "café", "n": 1}


def test_a05(tmp_path):
    from structlog.processors import JSONRenderer
    class Custom:
        def __structlog__(self):
            return {"kind": "custom"}
    rendered = JSONRenderer(sort_keys=True)(None, "info", {"value": Custom()})
    assert rendered == '{"value": {"kind": "custom"}}'


def test_a06(tmp_path):
    from structlog.contextvars import bind_contextvars, clear_contextvars, get_contextvars, reset_contextvars
    clear_contextvars()
    tokens = bind_contextvars(request="outer", number=1)
    inner = bind_contextvars(request="inner")
    assert get_contextvars() == {"request": "inner", "number": 1}
    reset_contextvars(request=inner["request"])
    assert get_contextvars()["request"] == "outer"
    clear_contextvars()


def test_i01(tmp_path):
    import structlog
    seen = []
    def first(logger, method, event):
        seen.append((method, event["event"])); return {"event": event["event"].upper(), "n": 1}
    def second(logger, method, event):
        seen.append((method, event["n"])); event["n"] += 1; return event
    logger = structlog.wrap_logger(structlog.ReturnLogger(), processors=[first, second])
    assert logger.info("hello") == ((), {"event": "HELLO", "n": 2})
    assert seen == [("info", "hello"), ("info", 1)]


def test_i02(tmp_path):
    import structlog
    from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars
    clear_contextvars(); bind_contextvars(shared="context", request="r1")
    logger = structlog.wrap_logger(structlog.ReturnLogger(), processors=[merge_contextvars], shared="bound", owner="api")
    assert logger.info("event", shared="call") == ((), {"shared": "call", "owner": "api", "event": "event", "request": "r1"})
    clear_contextvars()


def test_i03(tmp_path):
    import logging
    import structlog
    logger = structlog.make_filtering_bound_logger(logging.INFO)(structlog.ReturnLogger(), [], {})
    assert logger.debug("hidden") is None
    assert logger.info("visible", value=1) == ((), {"value": 1, "event": "visible"})


def test_i04(tmp_path):
    import structlog
    structlog.reset_defaults()
    original = structlog.get_config()["processors"]
    with structlog.testing.capture_logs(processors=[lambda logger, method, event: {**event, "captured": True}]) as events:
        structlog.get_logger().info("inside", n=1)
    assert events == [{"n": 1, "event": "inside", "captured": True, "log_level": "info"}]
    assert structlog.get_config()["processors"] == original
    structlog.reset_defaults()


def test_s01(tmp_path):
    from structlog.processors import ExceptionRenderer
    renderer = ExceptionRenderer(lambda exc: {"type": exc[0].__name__, "message": str(exc[1])})
    try:
        raise ValueError("broken")
    except ValueError:
        first = renderer(None, "error", {"event": "failed", "exc_info": True})
    second = renderer(None, "info", {"event": "ok"})
    assert first["exception"] == {"type": "ValueError", "message": "broken"}
    assert "exc_info" not in first and second == {"event": "ok"}


def test_s02(tmp_path):
    import logging
    from structlog.stdlib import ProcessorFormatter
    order = []
    def foreign(logger, method, event): order.append("foreign"); return event
    def common(logger, method, event): order.append("common"); return event["event"]
    formatter = ProcessorFormatter(foreign_pre_chain=[foreign], processors=[common])
    record = logging.LogRecord("demo", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    msg, args = record.msg, record.args
    assert formatter.format(record) == "hello world"
    assert order == ["foreign", "common"] and record.msg == msg and record.args == args


def test_s03(tmp_path):
    import asyncio
    import logging
    import structlog
    from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars
    async def run():
        clear_contextvars(); bind_contextvars(request="async")
        calls = []
        class Recording:
            def info(self, *args, **kwargs): calls.append((args, kwargs))
        logger = structlog.make_filtering_bound_logger(logging.INFO)(Recording(), [merge_contextvars], {})
        assert await logger.adebug("hidden") is None
        assert await logger.ainfo("visible") is None
        clear_contextvars(); return calls
    assert asyncio.run(run()) == [((), {"event": "visible", "request": "async"})]


def test_s04(tmp_path):
    from structlog.stdlib import render_to_log_kwargs
    row = render_to_log_kwargs(None, "warning", {"event": "hello", "owner": "api", "exc_info": False, "stack_info": True})
    assert row == {"msg": "hello", "extra": {"owner": "api"}, "exc_info": False, "stack_info": True}
