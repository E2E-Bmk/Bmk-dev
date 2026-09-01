from __future__ import annotations

import asyncio
import io
import json
import logging
from pathlib import Path
import threading

import loguru
from loguru import logger


def _reset() -> None:
    logger.remove()


def test_a01(tmp_path: Path) -> None:
    assert isinstance(loguru.__version__, str) and loguru.__version__
    expected = {"TRACE": 5, "DEBUG": 10, "INFO": 20, "SUCCESS": 25,
                "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    assert {name: logger.level(name).no for name in expected} == expected


def test_a02(tmp_path: Path) -> None:
    _reset(); output = io.StringIO()
    first = logger.add(output, format="{level.name}|{message}", level="INFO")
    second = logger.add(lambda message: None, format="{message}")
    assert first != second
    logger.debug("hidden"); logger.info("hello {}", "world")
    logger.remove(second); logger.warning("again"); logger.remove(first)
    assert output.getvalue().splitlines() == ["INFO|hello world", "WARNING|again"]


def test_a03(tmp_path: Path) -> None:
    _reset(); output = io.StringIO()
    level = logger.level("NOTICE_V2", no=27, color="<blue>", icon="!")
    logger.add(output, level="NOTICE_V2", format="{level.name}:{level.no}:{level.icon}:{message}")
    logger.log(26, "low"); logger.log("NOTICE_V2", "shown")
    assert (level.name, level.no, level.icon) == ("NOTICE_V2", 27, "!")
    assert output.getvalue().strip() == "NOTICE_V2:27:!:shown"


def test_a04(tmp_path: Path) -> None:
    _reset(); records = []
    logger.add(lambda message: records.append(dict(message.record["extra"])), format="{message}")
    bound = logger.bind(request="r-1")
    bound.info("one", region="east"); logger.info("two")
    assert records == [{"request": "r-1", "region": "east"}, {}]


def test_a05(tmp_path: Path) -> None:
    _reset(); records = []
    logger.add(lambda message: records.append(dict(message.record["extra"])), format="{message}")
    with logger.contextualize(scope="outer", shared=1):
        logger.info("outer")
        with logger.contextualize(scope="inner", child=2): logger.info("inner")
        logger.info("restored")
    logger.info("empty")
    assert records == [
        {"scope": "outer", "shared": 1},
        {"scope": "inner", "shared": 1, "child": 2},
        {"scope": "outer", "shared": 1},
        {},
    ]


def test_a06(tmp_path: Path) -> None:
    _reset(); observed = []
    def configured(record):
        observed.append("configured"); record["extra"]["order"] = "C"
    def local(record):
        observed.append("local"); record["extra"]["order"] += "L"
    logger.configure(extra={"base": 1}, patcher=configured)
    logger.add(lambda message: observed.append(message.record["extra"]["order"]), format="{message}")
    logger.patch(local).info("x")
    assert observed == ["configured", "local", "CL"]
    logger.configure(extra={}, patcher=lambda record: None)


def test_a07(tmp_path: Path) -> None:
    _reset(); left = io.StringIO(); right = io.StringIO()
    logger.add(left, filter=lambda record: record["extra"].get("side") == "left", format="{message}")
    logger.add(right, filter=lambda record: record["extra"].get("side") == "right", format="{message}")
    logger.bind(side="left").info("L"); logger.bind(side="right").info("R"); logger.info("none")
    assert left.getvalue() == "L\n" and right.getvalue() == "R\n"


def test_a08(tmp_path: Path) -> None:
    _reset(); output = io.StringIO()
    logger.add(output, serialize=True, format="{level.name}|{extra[token]}|{message}")
    logger.bind(token="t").success("ready {}", 2)
    value = json.loads(output.getvalue())
    assert value["text"] == "SUCCESS|t|ready 2\n"
    record = value["record"]
    assert record["message"] == "ready 2" and record["level"]["name"] == "SUCCESS" and record["extra"] == {"token": "t"}


def test_i01(tmp_path: Path) -> None:
    _reset(); low = io.StringIO(); high = io.StringIO()
    logger.add(low, level="DEBUG", filter=lambda record: record["extra"].get("tenant") == "a", format="{level.no}:{message}")
    logger.add(high, level="ERROR", format="{extra[tenant]}:{message}")
    view = logger.bind(tenant="a")
    view.debug("debug"); view.error("error")
    assert low.getvalue().splitlines() == ["10:debug", "40:error"]
    assert high.getvalue() == "a:error\n"


def test_i02(tmp_path: Path) -> None:
    _reset(); fallback = io.StringIO()
    class Broken:
        def write(self, message): raise LookupError("sink-broke")
    logger.add(Broken(), catch=True, format="{message}")
    logger.add(fallback, format="ok:{message}")
    logger.info("survives")
    assert fallback.getvalue() == "ok:survives\n"
    logger.remove(); logger.add(Broken(), catch=False, format="{message}")
    try: logger.info("raises")
    except LookupError as exc: assert str(exc) == "sink-broke"
    else: raise AssertionError("uncaught sink failure was suppressed")


def test_i03(tmp_path: Path) -> None:
    _reset(); captured = []
    class Capture(logging.Handler):
        def emit(self, record): captured.append(record)
    logger.add(Capture(), format="{message}")
    logger.bind(request_id="r7").warning("hello {}", "adapter")
    record = captured[0]
    assert record.getMessage() == "hello adapter" and record.levelno == 30 and record.extra == {"request_id": "r7"}


def test_i04(tmp_path: Path) -> None:
    _reset(); delivered = []
    async def sink(message):
        await asyncio.sleep(0); delivered.append((str(message).strip(), message.record["extra"]["job"]))
    async def scenario():
        logger.add(sink, format="{message}")
        logger.bind(job="j1").info("one"); logger.bind(job="j2").info("two")
        await logger.complete()
    asyncio.run(scenario())
    assert delivered == [("one", "j1"), ("two", "j2")]


def test_s01(tmp_path: Path) -> None:
    _reset(); console = io.StringIO(); path = tmp_path / "application.log"
    logger.add(console, level="INFO", format="console:{level.name}:{message}")
    logger.add(path, level="DEBUG", format="file:{level.name}:{extra[request]}:{message}", encoding="utf-8")
    view = logger.bind(request="r42")
    view.debug("detail"); view.info("visible"); logger.remove()
    assert console.getvalue() == "console:INFO:visible\n"
    assert path.read_text(encoding="utf-8").splitlines() == ["file:DEBUG:r42:detail", "file:INFO:r42:visible"]


def test_s02(tmp_path: Path) -> None:
    _reset(); records = []; guard = threading.Lock()
    def sink(message):
        with guard: records.append((message.record["extra"]["worker"], message.record["message"]))
    logger.add(sink, format="{message}")
    def run(worker):
        with logger.contextualize(worker=worker):
            logger.info("start"); logger.info("finish")
    threads = [threading.Thread(target=run, args=(name,)) for name in ("left", "right")]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert sorted(records) == [("left", "finish"), ("left", "start"), ("right", "finish"), ("right", "start")]
