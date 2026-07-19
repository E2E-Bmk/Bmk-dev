# Spec2Repo oracle - integration tests for loguru-fullrepro-001

import asyncio

import gzip

import io

import json

import logging

import os

import sys

import time

import pytest

import loguru

from loguru import logger

@pytest.fixture(autouse=True)
def clean_logger():
    logger.remove()
    logger.configure(extra={}, patcher=lambda record: None, activation=[(__name__, True)])
    yield
    logger.remove()
    logger.configure(extra={}, patcher=lambda record: None, activation=[(__name__, True)])

def make_writer():
    messages = []

    def sink(message):
        messages.append(message)

    return messages, sink

class TtyStream(io.StringIO):
    def isatty(self):
        return True

class NonTtyStream(io.StringIO):
    def isatty(self):
        return False

class BrokenSink:
    def __init__(self):
        self.calls = 0

    def write(self, message):
        self.calls += 1
        raise RuntimeError("sink failed")

import asyncio

import io

import pathlib

import re

import sys

import threading

from datetime import datetime

import pytest

from loguru import logger

@pytest.fixture(autouse=True)
def clean_logger():
    logger.remove()
    logger.configure(extra={}, patcher=lambda record: None, activation=[(__name__, True)])
    yield
    logger.remove()
    logger.configure(extra={}, patcher=lambda record: None, activation=[(__name__, True)])

@pytest.fixture
def writer():
    class Writer:
        def __init__(self):
            self.messages = []

        def write(self, message):
            self.messages.append(message)

        def read(self):
            return "".join(map(str, self.messages))

    return Writer()

TEXT = "This\nIs\nRandom\nText\n123456789\nABC!DEF\nThis Is The End\n"

@pytest.fixture
def fileobj():
    with io.StringIO(TEXT) as file:
        yield file

def test_remove_all(tmp_path, writer, capsys):
    file = tmp_path / "test.log"
    logger.add(file, format="{message}")
    logger.add(sys.stdout, format="{message}")
    logger.add(sys.stderr, format="{message}")
    logger.add(writer, format="{message}")
    logger.debug("some message")
    logger.remove()
    logger.debug("hidden")
    out, err = capsys.readouterr()
    assert file.read_text() == "some message\n"
    assert out == "some message\n"
    assert err == "some message\n"
    assert writer.read() == "some message\n"

def test_remove_enqueue(writer):
    handler_id = logger.add(writer, format="{message}", enqueue=True)
    logger.debug("1")
    logger.complete()
    logger.remove(handler_id)
    logger.debug("2")
    assert writer.read() == "1\n"

def test_remove_enqueue_filesink(tmp_path):
    file = tmp_path / "test.log"
    handler_id = logger.add(file, format="{message}", enqueue=True)
    logger.debug("1")
    logger.remove(handler_id)
    assert file.read_text() == "1\n"

def test_bind_after_add(writer):
    logger.add(writer, format="{extra[a]} {message}")
    logger_bound = logger.bind(a=0)
    logger_bound.debug("A")
    assert writer.read() == "0 A\n"

def test_bind_before_add(writer):
    logger_bound = logger.bind(a=0)
    logger.add(writer, format="{extra[a]} {message}")
    logger_bound.debug("A")
    assert writer.read() == "0 A\n"

def test_add_using_bound(writer):
    logger.configure(extra={"a": -1})
    logger_bound = logger.bind(a=0)
    logger_bound.add(writer, format="{extra[a]} {message}")
    logger.debug("A")
    logger_bound.debug("B")
    assert writer.read() == "-1 A\n0 B\n"

def test_bound_logger_does_not_override_parent(writer):
    logger_1 = logger.bind(a="a")
    logger_2 = logger_1.bind(a="A")
    logger.add(writer, format="{extra[a]} {message}")
    logger_1.debug("1")
    logger_2.debug("2")
    assert writer.read() == "a 1\nA 2\n"

def test_override_previous_bound(writer):
    logger.add(writer, format="{extra[x]} {message}")
    logger.bind(x=1).bind(x=2).debug("3")
    assert writer.read() == "2 3\n"

def test_bind_and_add_level(writer):
    logger_bound = logger.bind()
    logger.add(writer, format="{level.name} {message}")
    logger_bound.level("bar", 15)
    logger.log("bar", "root")
    logger_bound.log("bar", "bound")
    assert writer.read() == "bar root\nbar bound\n"

def test_patch_after_add(writer):
    logger.add(writer, format="{extra[a]} {message}")
    logger_patched = logger.patch(lambda record: record["extra"].update(a=0))
    logger_patched.debug("A")
    assert writer.read() == "0 A\n"

def test_patch_before_add(writer):
    logger_patched = logger.patch(lambda record: record["extra"].update(a=0))
    logger.add(writer, format="{extra[a]} {message}")
    logger_patched.debug("A")
    assert writer.read() == "0 A\n"

def test_add_using_patched(writer):
    logger.configure(patcher=lambda record: record["extra"].update(a=-1))
    logger_patched = logger.patch(lambda record: record["extra"].update(a=0))
    logger_patched.add(writer, format="{extra[a]} {message}")
    logger.debug("A")
    logger_patched.debug("B")
    assert writer.read() == "-1 A\n0 B\n"

def test_multiple_patches(writer):
    def patch_1(record):
        record["extra"]["a"] = 5

    def patch_2(record):
        record["extra"]["a"] += 1

    def patch_3(record):
        record["extra"]["a"] *= 2

    logger.add(writer, format="{extra[a]} {message}")
    logger.patch(patch_1).patch(patch_2).patch(patch_3).info("Test")
    assert writer.read() == "12 Test\n"

def test_contextualize(writer):
    logger.add(writer, format="{message} {extra[foo]} {extra[baz]}")
    with logger.contextualize(foo="bar", baz=123):
        logger.info("Contextualized")
    assert writer.read() == "Contextualized bar 123\n"

def test_contextualize_as_decorator(writer):
    logger.add(writer, format="{message} {extra[foo]} {extra[baz]}")

    @logger.contextualize(foo=123, baz="bar")
    def task():
        logger.info("Contextualized")

    task()
    assert writer.read() == "Contextualized 123 bar\n"

def test_contextualize_reset():
    contexts = []
    output = []

    def sink(message):
        contexts.append(dict(message.record["extra"]))
        output.append(str(message))

    logger.add(sink, format="{level} {message}")
    logger.info("A")
    with logger.contextualize(abc="def"):
        logger.debug("B")
        logger.warning("C")
    logger.info("D")
    assert contexts == [{}, {"abc": "def"}, {"abc": "def"}, {}]
    assert output == ["INFO A\n", "DEBUG B\n", "WARNING C\n", "INFO D\n"]

def test_contextualize_async(writer):
    logger.add(writer, format="{message} {extra[i]}", catch=False)

    async def task():
        logger.info("Start")
        await asyncio.sleep(0)
        logger.info("End")

    async def worker(i):
        with logger.contextualize(i=i):
            await task()

    async def main():
        await asyncio.gather(*(worker(i) for i in range(5)))
        await logger.complete()

    asyncio.run(main())
    assert sorted(writer.read().splitlines()) == [f"End {i}" for i in range(5)] + [
        f"Start {i}" for i in range(5)
    ]

def test_contextualize_thread(writer):
    logger.add(writer, format="{message} {extra[i]}")

    def worker(entry_barrier, exit_barrier, i):
        with logger.contextualize(i=i):
            entry_barrier.wait()
            logger.info("Processing")
            exit_barrier.wait()

    entry_barrier = threading.Barrier(5)
    exit_barrier = threading.Barrier(5)
    threads = [
        threading.Thread(target=worker, args=(entry_barrier, exit_barrier, i)) for i in range(5)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(writer.read().splitlines()) == [f"Processing {i}" for i in range(5)]

def test_contextualize_before_bind(writer):
    logger.add(writer, format="{message} {extra[foobar]}")
    logger_2 = logger.bind(foobar="baz")
    with logger.contextualize(foobar="baz_2"):
        logger.info("A")
        logger_2.info("B")
    logger_2.info("C")
    assert writer.read() == "A baz_2\nB baz\nC baz\n"

def test_context_reset_despite_error(writer):
    logger.add(writer, format="{message} {extra}")
    try:
        with logger.contextualize(foobar=456):
            logger.info("Division")
            1 / 0
    except ZeroDivisionError:
        logger.info("Error")
    assert writer.read() == "Division {'foobar': 456}\nError {}\n"

def test_add_level_then_log_with_int_value(writer):
    logger.level("foo", 16)
    logger.add(writer, level="foo", format="{level.name} {level.no} {message}", colorize=False)
    logger.log(16, "test")
    assert writer.read() == "Level 16 16 test\n"

def test_public_logger_works_without_user_constructor():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.info("constructed by package")
    assert str(messages[0]) == "constructed by package\n"

def test_import_surface_remains_reusable_after_handler_changes():
    messages, sink = make_writer()
    handler_id = logger.add(sink, format="{message}")
    logger.remove(handler_id)
    logger.add(sink, format="{message}")
    logger.info("reused")
    assert str(messages[0]) == "reused\n"

def test_logger_coordinates_formatting_record_and_sink_delivery():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}:{extra[component]}")
    logger.bind(component="overview").success("ready")
    message = messages[0]
    assert str(message) == "SUCCESS:ready:overview\n"
    assert message.record["extra"]["component"] == "overview"

def test_remove_deactivates_one_handler_only():
    first, first_sink = make_writer()
    second, second_sink = make_writer()
    first_id = logger.add(first_sink, format="{message}")
    logger.add(second_sink, format="{message}")
    logger.remove(first_id)
    logger.info("kept")
    assert first == []
    assert str(second[0]) == "kept\n"

def test_filter_dict_threshold_combines_with_handler_level():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}", level="DEBUG", filter={__name__: "WARNING"})
    logger.info("hidden")
    logger.error("visible")
    assert [str(message) for message in messages] == ["ERROR:visible\n"]

def test_colorize_none_uses_stream_tty_detection():
    tty = TtyStream()
    not_tty = NonTtyStream()
    logger.add(tty, format="<blue>{message}</blue>", colorize=None)
    logger.add(not_tty, format="<blue>{message}</blue>", colorize=None)
    logger.info("auto")
    assert "\x1b[" in tty.getvalue()
    assert not_tty.getvalue() == "auto\n"

def test_colorize_none_is_false_for_path_sink(tmp_path):
    path = tmp_path / "plain.log"
    logger.add(path, format="<green>{message}</green>", colorize=None)
    logger.info("file")
    logger.remove()
    assert path.read_text() == "file\n"

def test_no_color_environment_disables_standard_stream_auto_color(monkeypatch):
    stream = TtyStream()
    monkeypatch.setattr(sys, "stderr", stream)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    logger.add(stream, format="<red>{message}</red>", colorize=None)
    logger.info("plain")
    assert stream.getvalue() == "plain\n"

def test_force_color_environment_enables_standard_stream_auto_color(monkeypatch):
    stream = NonTtyStream()
    monkeypatch.setattr(sys, "stderr", stream)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    logger.add(stream, format="<red>{message}</red>", colorize=None)
    logger.info("forced")
    assert "\x1b[" in stream.getvalue()

def test_bind_adds_extra_without_mutating_parent_logger():
    base_messages, base_sink = make_writer()
    bound_messages, bound_sink = make_writer()
    logger.add(base_sink, format="{extra}", filter=lambda record: "user" not in record["extra"])
    logger.bind(user="alice").add(bound_sink, format="{extra[user]}")
    logger.info("base")
    logger.bind(user="alice").info("bound")
    assert "{}\n" in [str(message) for message in base_messages]
    assert "alice\n" in [str(message) for message in bound_messages]

def test_contextualize_adds_and_restores_extra():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.info("before")
    with logger.contextualize(request="r1"):
        logger.info("inside")
    logger.info("after")
    assert [message.record["extra"].get("request", "-") for message in messages] == [
        "-",
        "r1",
        "-",
    ]

def test_extra_conflict_precedence_call_over_bind_over_context_over_configure():
    messages, sink = make_writer()
    logger.configure(extra={"value": "configured"})
    bound = logger.bind(value="bound")
    bound.add(sink, format="{extra[value]}")
    with logger.contextualize(value="context"):
        bound.info("msg")
        bound.info("msg", value="call")
    assert [str(message) for message in messages] == ["bound\n", "call\n"]

def test_contextualize_isolated_across_async_tasks():
    messages, sink = make_writer()
    logger.add(sink, format="{extra[task]}:{message}")

    async def emit(task):
        with logger.contextualize(task=task):
            await asyncio.sleep(0)
            logger.info("done")

    async def run():
        await asyncio.gather(emit("a"), emit("b"))

    asyncio.run(run())
    assert sorted(str(message) for message in messages) == ["a:done\n", "b:done\n"]

def test_patch_mutates_record_seen_by_formatter():
    messages, sink = make_writer()
    patched = logger.patch(lambda record: record["extra"].update(patched=True))
    patched.add(sink, format="{extra[patched]}:{message}")
    patched.info("ok")
    assert str(messages[0]) == "True:ok\n"

def test_configured_patcher_runs_before_logger_view_patcher():
    messages, sink = make_writer()
    logger.configure(patcher=lambda record: record["extra"].update(order=["configured"]))

    def append_view(record):
        record["extra"]["order"].append("view")

    patched = logger.patch(append_view)
    patched.add(sink, format="{extra[order]}")
    patched.info("order")
    assert str(messages[0]) == "['configured', 'view']\n"

def test_opt_lazy_defers_callable_when_record_filtered_out():
    calls = []
    logger.add(lambda _: None, level="ERROR")
    logger.opt(lazy=True).debug("{}", lambda: calls.append("called") or "value")
    assert calls == []

def test_disable_and_enable_module_namespace():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.disable(__name__)
    logger.info("hidden")
    logger.enable(__name__)
    logger.info("visible")
    assert [str(message) for message in messages] == ["visible\n"]

def test_disabled_namespace_suppresses_records_added_after_disable():
    messages, sink = make_writer()
    logger.disable(__name__)
    logger.add(sink, format="{message}")
    logger.info("hidden")
    logger.enable(__name__)
    logger.info("shown")
    assert [str(message) for message in messages] == ["shown\n"]

def test_enable_restores_only_subsequent_library_records():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.disable(__name__)
    logger.info("before")
    logger.enable(__name__)
    logger.info("after")
    assert [str(message) for message in messages] == ["after\n"]

def test_configure_replaces_handlers_and_returns_new_ids():
    old_messages, old_sink = make_writer()
    new_messages, new_sink = make_writer()
    logger.add(old_sink, format="{message}")
    ids = logger.configure(handlers=[{"sink": new_sink, "format": "{message}"}])
    logger.info("new")
    assert all(isinstance(handler_id, int) for handler_id in ids)
    assert old_messages == []
    assert str(new_messages[0]) == "new\n"

def test_configure_extra_is_visible_to_formatters():
    messages, sink = make_writer()
    logger.configure(extra={"app": "demo"})
    logger.add(sink, format="{extra[app]}:{message}")
    logger.info("configured")
    assert str(messages[0]) == "demo:configured\n"

def test_file_sink_writes_accepted_records(tmp_path):
    path = tmp_path / "app.log"
    logger.add(path, format="{message}")
    logger.info("file-one")
    logger.info("file-two")
    logger.remove()
    assert path.read_text() == "file-one\nfile-two\n"

def test_application_workflow_writes_console_and_file_views(tmp_path):
    console = io.StringIO()
    file_path = tmp_path / "workflow.log"
    logger.add(console, format="console:{level.name}:{message}", level="INFO")
    logger.add(file_path, format="file:{level.name}:{extra[request]}:{message}", level="DEBUG")
    request_logger = logger.bind(request="r42")
    request_logger.debug("debug detail")
    request_logger.info("user visible")
    logger.remove()
    assert console.getvalue() == "console:INFO:user visible\n"
    assert file_path.read_text() == "file:DEBUG:r42:debug detail\nfile:INFO:r42:user visible\n"

def test_application_workflow_keeps_console_threshold_above_file(tmp_path):
    console = io.StringIO()
    file_path = tmp_path / "workflow-threshold.log"
    logger.add(console, level="WARNING", format="console:{level.name}:{message}")
    logger.add(file_path, level="DEBUG", format="file:{level.name}:{message}")
    logger.info("info-only-file")
    logger.warning("visible-both")
    logger.remove()
    assert console.getvalue() == "console:WARNING:visible-both\n"
    assert file_path.read_text() == "file:INFO:info-only-file\nfile:WARNING:visible-both\n"

def test_application_workflow_bound_context_is_written_to_file(tmp_path):
    console = io.StringIO()
    file_path = tmp_path / "workflow-extra.log"
    request_logger = logger.bind(request_id="abc")
    logger.add(console, level="INFO", format="{message}")
    logger.add(file_path, level="INFO", format="{extra[request_id]}:{message}")
    request_logger.info("created")
    logger.remove()
    assert console.getvalue() == "created\n"
    assert file_path.read_text() == "abc:created\n"

def test_file_sink_rotation_creates_multiple_files(tmp_path):
    path = tmp_path / "rotating.log"
    logger.add(path, format="{message}", rotation="10 B")
    logger.info("abcdefghij")
    logger.info("klmnopqrst")
    logger.remove()
    files = list(tmp_path.iterdir())
    assert len(files) >= 2
    assert path in files

def test_file_sink_compression_creates_gzip_rotated_file(tmp_path):
    path = tmp_path / "compressed.log"
    logger.add(path, format="{message}", rotation="10 B", compression="gz")
    logger.info("abcdefghij")
    logger.info("klmnopqrst")
    logger.remove()
    gz_files = list(tmp_path.glob("*.gz"))
    assert gz_files
    compressed_text = []
    for gz_file in gz_files:
        with gzip.open(gz_file, "rt") as compressed:
            compressed_text.append(compressed.read())
    assert any("abcdefghij" in text or "klmnopqrst" in text for text in compressed_text)

def test_file_sink_watch_reopens_replaced_file(tmp_path):
    path = tmp_path / "watched.log"
    logger.add(path, format="{message}", watch=True)
    logger.info("before")
    path.unlink()
    logger.info("after")
    logger.remove()
    assert path.read_text() == "after\n"

def test_enqueue_complete_drains_queued_messages():
    messages, sink = make_writer()
    logger.add(sink, format="{message}", enqueue=True)
    for index in range(5):
        logger.info("queued {}", index)
    logger.complete()
    assert [str(message) for message in messages] == [f"queued {index}\n" for index in range(5)]

def test_coroutine_sink_is_completed_by_awaitable():
    received = []

    async def sink(message):
        await asyncio.sleep(0)
        received.append(str(message))

    async def run():
        logger.add(sink, format="{message}")
        logger.info("async")
        await logger.complete()

    asyncio.run(run())
    assert received == ["async\n"]

def test_standard_logging_handler_receives_log_record():
    class ListHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []

        def emit(self, record):
            self.records.append(record)

    handler = ListHandler()
    logger.add(handler, format="{message}")
    logger.warning("standard {}", "handler")
    assert handler.records[0].getMessage() == "standard handler"
    assert handler.records[0].levelname == "WARNING"

def test_standard_logging_can_be_forwarded_to_loguru():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}")

    class Forward(logging.Handler):
        def emit(self, record):
            logger.opt(depth=6, exception=record.exc_info).log(record.levelno, record.getMessage())

    logging_logger = logging.getLogger("generated.forward")
    logging_logger.handlers[:] = []
    logging_logger.propagate = False
    logging_logger.setLevel(logging.DEBUG)
    logging_logger.addHandler(Forward())
    try:
        logging_logger.error("forwarded")
    finally:
        logging_logger.handlers[:] = []
    assert str(messages[0]) == "Level 40:forwarded\n"

def test_catch_decorator_logs_and_returns_default():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}")

    @logger.catch(default="fallback")
    def fail():
        raise ValueError("bad")

    assert fail() == "fallback"
    assert messages[0].record["exception"].type is ValueError
    assert str(messages[0]).startswith("ERROR:")

def test_catch_context_reraises_when_requested():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    with pytest.raises(KeyError):
        with logger.catch(reraise=True):
            raise KeyError("missing")
    assert messages[0].record["exception"].type is KeyError

def test_exception_method_attaches_current_exception():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}")
    try:
        raise ZeroDivisionError("zero")
    except ZeroDivisionError:
        logger.exception("caught")
    assert messages[0].record["exception"].type is ZeroDivisionError
    assert str(messages[0]).startswith("ERROR:caught\n")

def test_log_record_views_agree_across_serialized_and_callable_sinks():
    callable_messages, callable_sink = make_writer()
    serialized_messages, serialized_sink = make_writer()
    logger.add(callable_sink, format="{message}")
    logger.add(serialized_sink, format="{message}", serialize=True)
    logger.bind(flow="same").info("cross")
    serialized = json.loads(str(serialized_messages[0]))
    assert callable_messages[0].record["extra"]["flow"] == "same"
    assert serialized["record"]["extra"]["flow"] == "same"
    assert callable_messages[0].record["message"] == serialized["record"]["message"] == "cross"

def test_removed_handler_does_not_affect_remaining_state():
    first, first_sink = make_writer()
    second, second_sink = make_writer()
    first_id = logger.add(first_sink, format="{message}")
    logger.add(second_sink, format="{extra[tag]}:{message}")
    scoped = logger.bind(tag="state")
    scoped.info("before")
    logger.remove(first_id)
    scoped.info("after")
    assert [str(message) for message in first] == ["before\n"]
    assert [str(message) for message in second] == ["state:before\n", "state:after\n"]

def test_configure_replacement_affects_only_subsequent_records():
    before, before_sink = make_writer()
    after, after_sink = make_writer()
    logger.add(before_sink, format="{message}")
    logger.info("before")
    logger.configure(handlers=[{"sink": after_sink, "format": "{message}"}])
    logger.info("after")
    assert [str(message) for message in before] == ["before\n"]
    assert [str(message) for message in after] == ["after\n"]

def test_reinstall_keeps_simple_logger_usable():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.reinstall()
    logger.info("usable")
    assert str(messages[0]) == "usable\n"
