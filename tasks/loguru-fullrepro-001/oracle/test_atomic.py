# Spec2Repo oracle - atomic tests for loguru-fullrepro-001

import asyncio

import gzip

import importlib

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

def test_remove_simple(writer):
    handler_id = logger.add(writer, format="{message}")
    logger.debug("1")
    logger.remove(handler_id)
    logger.debug("2")
    assert writer.read() == "1\n"

def test_invalid_handler_id_value(writer):
    logger.add(writer)
    with pytest.raises(ValueError):
        logger.remove(42)

@pytest.mark.parametrize("handler_id", [sys.stderr, sys, object(), int])
def test_invalid_handler_id_type(handler_id):
    with pytest.raises(TypeError):
        logger.remove(handler_id)

def test_log_int_level(writer):
    logger.add(writer, format="{level.name} -> {level.no} -> {message}", colorize=False)
    logger.log(10, "test")
    assert writer.read() == "Level 10 -> 10 -> test\n"

def test_log_str_level(writer):
    logger.add(writer, format="{level.name} -> {level.no} -> {message}", colorize=False)
    logger.log("DEBUG", "test")
    assert writer.read() == "DEBUG -> 10 -> test\n"

def test_edit_existing_level(writer):
    original = logger.level("DEBUG")
    try:
        logger.level("DEBUG", icon="!")
        logger.add(writer, format="{level.no}, {level.name}, {level.icon}, {message}", colorize=False)
        logger.debug("a")
        assert writer.read() == "10, DEBUG, !, a\n"
    finally:
        logger.level("DEBUG", color=original.color, icon=original.icon)

def test_get_level():
    logger.level("lvl", 11, "<red>", "[!]")
    registered = logger.level("lvl")
    assert registered.name == "lvl"
    assert registered.no == 11
    assert registered.color == "<red>"
    assert registered.icon == "[!]"

def test_get_existing_level():
    assert logger.level("DEBUG").name == "DEBUG"
    assert logger.level("DEBUG").no == 10

def test_updating_level_no_not_allowed_default():
    with pytest.raises(ValueError):
        logger.level("DEBUG", 100)

@pytest.mark.parametrize("level", [3.4, object(), set()])
def test_log_invalid_level_type(writer, level):
    logger.add(writer)
    with pytest.raises(TypeError):
        logger.log(level, "test")

@pytest.mark.parametrize("level", [-1, -999])
def test_log_invalid_level_value(writer, level):
    logger.add(writer)
    with pytest.raises(ValueError):
        logger.log(level, "test")

@pytest.mark.parametrize("level", ["unknown_level_for_loguru_stage3", "debug"])
def test_log_unknown_level(writer, level):
    logger.add(writer)
    with pytest.raises(ValueError):
        logger.log(level, "test")

def test_parse_file(tmp_path):
    file = tmp_path / "test.log"
    file.write_text(TEXT)
    result, *_ = list(logger.parse(file, r"(?P<num>\d+)"))
    assert result == dict(num="123456789")

def test_parse_fileobj(tmp_path):
    file = tmp_path / "test.log"
    file.write_text(TEXT)
    with open(str(file)) as fileobj:
        result, *_ = list(logger.parse(fileobj, r"^(?P<t>\w+)"))
    assert result == dict(t="This")

def test_parse_pathlib(tmp_path):
    file = tmp_path / "test.log"
    file.write_text(TEXT)
    result, *_ = list(logger.parse(pathlib.Path(str(file)), r"(?P<r>Random)"))
    assert result == dict(r="Random")

def test_parse_regex_pattern(fileobj):
    regex = re.compile(r"(?P<maj>[a-z]*![a-z]*)", flags=re.I)
    result, *_ = list(logger.parse(fileobj, regex))
    assert result == dict(maj="ABC!DEF")

def test_parse_multiline_pattern(fileobj):
    result, *_ = list(logger.parse(fileobj, r"(?P<text>This[\s\S]*Text\n)"))
    assert result == dict(text="This\nIs\nRandom\nText\n")

def test_parse_without_group(fileobj):
    result, *_ = list(logger.parse(fileobj, r"\d+"))
    assert result == {}

def test_parse_bytes():
    with io.BytesIO(b"Testing bytes!") as fileobj:
        result, *_ = list(logger.parse(fileobj, rb"(?P<punct>[?!:])"))
    assert result == dict(punct=b"!")

def test_parse_cast_dict(tmp_path):
    file = tmp_path / "test.log"
    file.write_text("[123] [1.1] [2017-03-29 11:11:11]\n")
    regex = r"\[(?P<num>.*)\] \[(?P<val>.*)\] \[(?P<date>.*)\]"
    caster = dict(num=int, val=float, date=lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S"))
    result = next(logger.parse(file, regex, cast=caster))
    assert result == dict(num=123, val=1.1, date=datetime(2017, 3, 29, 11, 11, 11))

def test_parse_cast_function(tmp_path):
    file = tmp_path / "test.log"
    file.write_text("[123] [1.1] [2017-03-29 11:11:11]\n")
    regex = r"\[(?P<num>.*)\] \[(?P<val>.*)\] \[(?P<date>.*)\]"

    def caster(groups):
        groups["num"] = int(groups["num"])
        groups["val"] = float(groups["val"])
        groups["date"] = datetime.strptime(groups["date"], "%Y-%m-%d %H:%M:%S")

    result = next(logger.parse(file, regex, cast=caster))
    assert result == dict(num=123, val=1.1, date=datetime(2017, 3, 29, 11, 11, 11))

def test_invalid_file():
    with pytest.raises(TypeError):
        next(logger.parse(object(), r"pattern"))

def test_invalid_pattern(fileobj):
    with pytest.raises(TypeError):
        next(logger.parse(fileobj, object()))

def test_imported_logger_emits_to_public_sink():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.info("hello")
    assert str(messages[0]) == "hello\n"

def test_module_logger_is_same_public_object():
    assert loguru.logger is logger
    messages, sink = make_writer()
    loguru.logger.add(sink, format="{message}")
    logger.warning("same")
    assert str(messages[0]) == "same\n"

def test_version_is_public_non_empty_string():
    assert isinstance(loguru.__version__, str)
    assert loguru.__version__

def test_importlib_protocol_exposes_logger_object():
    module = importlib.import_module("loguru")
    assert module.logger is logger

def test_from_import_protocol_uses_installed_package_logger():
    namespace = {}
    exec("from loguru import logger as imported_logger", namespace)
    messages, sink = make_writer()
    namespace["imported_logger"].add(sink, format="{message}")
    logger.info("from import")
    assert str(messages[0]) == "from import\n"

def test_import_protocol_exposes_version_on_module():
    module = importlib.import_module("loguru")
    assert isinstance(module.__version__, str)
    assert module.__version__

def test_add_returns_distinct_integer_handler_ids():
    ids = [logger.add(lambda _: None), logger.add(lambda _: None)]
    assert all(isinstance(handler_id, int) for handler_id in ids)
    assert len(set(ids)) == 2

def test_remove_without_id_removes_all_handlers():
    first, first_sink = make_writer()
    second, second_sink = make_writer()
    logger.add(first_sink, format="{message}")
    logger.add(second_sink, format="{message}")
    logger.remove()
    logger.info("ignored")
    assert first == []
    assert second == []

def test_remove_unknown_handler_id_raises_value_error():
    with pytest.raises(ValueError):
        logger.remove(123456789)

def test_remove_invalid_handler_id_type_raises_type_error():
    with pytest.raises(TypeError):
        logger.remove("not-an-id")

def test_default_add_level_is_debug_when_environment_unset(monkeypatch):
    monkeypatch.delenv("LOGURU_LEVEL", raising=False)
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}")
    logger.debug("visible")
    logger.trace("hidden")
    assert [str(message) for message in messages] == ["DEBUG:visible\n"]

def test_callable_sink_receives_string_like_message_with_record():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}")
    logger.success("done")
    message = messages[0]
    assert str(message) == "SUCCESS:done\n"
    assert message.record["message"] == "done"
    assert message.record["level"].name == "SUCCESS"

def test_record_contains_documented_core_keys():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.info("record")
    keys = set(messages[0].record)
    assert {
        "elapsed",
        "exception",
        "extra",
        "file",
        "function",
        "level",
        "line",
        "message",
        "module",
        "name",
        "process",
        "thread",
        "time",
    } <= keys

def test_record_level_exposes_name_number_and_icon_not_color():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.info("level")
    level = messages[0].record["level"]
    assert (level.name, level.no) == ("INFO", 20)
    assert isinstance(level.icon, str)
    assert not hasattr(level, "color")

def test_format_string_uses_positional_and_keyword_arguments():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.info("{} {name}", "hello", name="world")
    assert str(messages[0]) == "hello world\n"

def test_format_callable_receives_record():
    messages, sink = make_writer()

    def formatter(record):
        return "{level.name}:{extra[tag]}:{message}\n"

    bound = logger.bind(tag="callable")
    bound.add(sink, format=formatter)
    bound.info("formatted")
    assert str(messages[0]) == "INFO:callable:formatted\n"

def test_format_argument_mismatch_raises():
    logger.add(lambda _: None, format="{message}")
    with pytest.raises(ValueError):
        logger.info("{} {} {}", "only-one")

def test_filter_callable_selects_records():
    messages, sink = make_writer()
    logger.add(sink, format="{message}", filter=lambda record: record["extra"].get("keep"))
    logger.bind(keep=False).info("hidden")
    logger.bind(keep=True).info("shown")
    assert [str(message) for message in messages] == ["shown\n"]

def test_filter_string_matches_module_namespace():
    messages, sink = make_writer()
    logger.add(sink, format="{message}", filter=__name__)
    logger.info("accepted")
    assert str(messages[0]) == "accepted\n"

def test_handler_level_threshold_rejects_lower_records():
    messages, sink = make_writer()
    logger.add(sink, format="{level.name}:{message}", level="ERROR")
    logger.warning("hidden")
    logger.error("shown")
    assert [str(message) for message in messages] == ["ERROR:shown\n"]

def test_sink_exception_propagates_when_catch_false():
    logger.add(BrokenSink(), catch=False)
    with pytest.raises(RuntimeError):
        logger.info("boom")

def test_sink_exception_is_suppressed_when_catch_true(capsys):
    sink = BrokenSink()
    logger.add(sink, catch=True)
    logger.info("boom")
    captured = capsys.readouterr()
    assert sink.calls == 1
    assert "RuntimeError" in captured.err
    assert "sink failed" in captured.err

def test_serialize_outputs_json_text_and_record():
    messages, sink = make_writer()
    logger.add(sink, format="{message}", serialize=True)
    logger.info("json {value}", value=3)
    payload = json.loads(str(messages[0]))
    assert payload["text"] == "json 3\n"
    assert payload["record"]["message"] == "json 3"
    assert payload["record"]["level"]["name"] == "INFO"

def test_colorize_true_converts_markup_to_ansi():
    stream = NonTtyStream()
    logger.add(stream, format="<red>{message}</red>", colorize=True)
    logger.info("red")
    assert "\x1b[" in stream.getvalue()
    assert "red" in stream.getvalue()

def test_colorize_false_strips_format_markup():
    stream = TtyStream()
    logger.add(stream, format="<red>{message}</red>", colorize=False)
    logger.info("plain")
    assert stream.getvalue() == "plain\n"

def test_opt_raw_bypasses_handler_format():
    messages, sink = make_writer()
    logger.add(sink, format="PREFIX:{message}")
    logger.opt(raw=True).info("raw")
    assert str(messages[0]) == "raw"

def test_opt_record_allows_record_placeholder_in_message():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")
    logger.opt(record=True).info("function={record[function]}")
    assert "test_opt_record_allows_record_placeholder_in_message" in str(messages[0])

def test_opt_capture_false_excludes_kwargs_from_extra():
    messages, sink = make_writer()
    logger.add(sink, format="{extra}")
    logger.opt(capture=False).info("hello {name}", name="world")
    assert str(messages[0]) == "{}\n"

def test_builtin_levels_have_documented_numbers():
    expected = {
        "TRACE": 5,
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    assert {name: logger.level(name).no for name in expected} == expected

def test_custom_level_can_be_created_and_used():
    messages, sink = make_writer()
    logger.level("NOTICE", no=35, color="<cyan>", icon="N")
    logger.add(sink, format="{level.name}:{level.no}:{level.icon}:{message}", level="NOTICE")
    logger.log("NOTICE", "custom")
    assert str(messages[0]) == "NOTICE:35:N:custom\n"

def test_existing_level_color_and_icon_can_be_updated():
    old = logger.level("INFO")
    try:
        updated = logger.level("INFO", color="<red>", icon="I")
        assert updated.no == old.no
        assert updated.color == "<red>"
        assert updated.icon == "I"
    finally:
        logger.level("INFO", color=old.color, icon=old.icon)

def test_unknown_level_query_raises_value_error():
    with pytest.raises(ValueError):
        logger.level("DOES_NOT_EXIST")

def test_file_sink_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "logs" / "app.log"
    logger.add(path, format="{message}")
    logger.info("created")
    logger.remove()
    assert path.read_text() == "created\n"

def test_file_sink_delay_opens_on_first_message(tmp_path):
    path = tmp_path / "delayed.log"
    logger.add(path, format="{message}", delay=True)
    assert not path.exists()
    logger.info("now")
    logger.remove()
    assert path.read_text() == "now\n"

def test_complete_returns_awaitable_object():
    async def sink(message):
        return None

    logger.add(sink, format="{message}")
    logger.info("awaitable")
    completer = logger.complete()
    assert hasattr(completer, "__await__")

    async def wait_for_completion():
        await completer

    asyncio.run(wait_for_completion())

def test_catch_exclude_does_not_suppress_excluded_exception():
    messages, sink = make_writer()
    logger.add(sink, format="{message}")

    @logger.catch(exception=Exception, exclude=RuntimeError, default="ignored")
    def fail():
        raise RuntimeError("excluded")

    with pytest.raises(RuntimeError):
        fail()
    assert messages == []

def test_parse_yields_named_groups_from_file(tmp_path):
    path = tmp_path / "parsed.log"
    path.write_text("level=INFO message=hello\nlevel=ERROR message=boom\n")
    rows = list(logger.parse(path, r"level=(?P<level>\w+) message=(?P<message>\w+)"))
    assert rows == [{"level": "INFO", "message": "hello"}, {"level": "ERROR", "message": "boom"}]

def test_parse_cast_mapping_transforms_values(tmp_path):
    path = tmp_path / "numbers.log"
    path.write_text("value=1\nvalue=2\n")
    rows = list(logger.parse(path, r"value=(?P<value>\d+)", cast={"value": int}))
    assert rows == [{"value": 1}, {"value": 2}]

def test_parse_cast_callable_transforms_dict(tmp_path):
    path = tmp_path / "callable.log"
    path.write_text("name=alice\n")

    def cast(row):
        row["name"] = row["name"].upper()
        return row

    assert list(logger.parse(path, r"name=(?P<name>\w+)", cast=cast)) == [{"name": "ALICE"}]

def test_parse_missing_file_propagates_os_error(tmp_path):
    with pytest.raises(OSError):
        list(logger.parse(tmp_path / "missing.log", r"(?P<anything>.*)"))

def test_start_and_stop_alias_add_and_remove():
    messages, sink = make_writer()
    handler_id = logger.start(sink, format="{message}")
    logger.info("legacy")
    logger.stop(handler_id)
    logger.info("hidden")
    assert [str(message) for message in messages] == ["legacy\n"]

def test_public_type_stub_file_is_packaged():
    package_dir = os.path.dirname(loguru.__file__)
    stub_path = os.path.join(package_dir, "__init__.pyi")
    assert os.path.exists(stub_path)
    with open(stub_path, encoding="utf8") as stub:
        content = stub.read()
    assert "class Logger" in content
    assert "class RecordLevel" in content

def test_type_stub_documents_record_level_without_color():
    package_dir = os.path.dirname(loguru.__file__)
    with open(os.path.join(package_dir, "__init__.pyi"), encoding="utf8") as stub:
        content = stub.read()
    record_level_block = content.split("class RecordLevel", 1)[1].split("class RecordThread", 1)[0]
    assert "name: str" in record_level_block
    assert "no: int" in record_level_block
    assert "icon: str" in record_level_block
    assert "color:" not in record_level_block
