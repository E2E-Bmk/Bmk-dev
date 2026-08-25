from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.support import BASE, base_settings


def test_a01_native_direct_absolute():
    from dateparser import parse
    assert parse("23 October 1974", languages=["en"], settings=base_settings()) == datetime(1974, 10, 23)


def test_a02_native_structured_precision():
    from dateparser import DateDataParser
    value = DateDataParser(languages=["en"], settings=base_settings()).get_date_data("September 2016")
    assert (value.date_obj.year, value.date_obj.month, value.period) == (2016, 9, "month")


def test_a03_native_no_match():
    from dateparser import DateDataParser
    value = DateDataParser(languages=["en"], settings=base_settings()).get_date_data("ordinary words without time")
    assert value.date_obj is None and value.period == "day"


def test_a04_native_search_order():
    from dateparser.search import search_dates
    values = search_dates("first 2047-08-09 then 2047-10-11", languages=["en"], settings=base_settings())
    assert [item[0] for item in values] == ["2047-08-09", "2047-10-11"]


def test_a05_native_timestamp():
    from dateparser import parse
    value = parse("1924992000", languages=["en"], settings=base_settings(PARSERS=["timestamp"], TIMEZONE="UTC", RETURN_AS_TIMEZONE_AWARE=False))
    assert value == datetime(2031, 1, 1)


def test_a06_native_explicit_format_order():
    from dateparser import parse
    value = parse("05-06-2007", date_formats=["%d-%m-%Y", "%m-%d-%Y"], languages=["en"], settings=base_settings())
    assert value == datetime(2007, 6, 5)


def test_a07_native_relative_base():
    from dateparser import parse
    assert parse("in 2 days", languages=["en"], settings=base_settings()) == BASE + timedelta(days=2)


def test_a08_native_explicit_language_bypasses_detection():
    from dateparser import parse
    calls = []
    def detector(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("must not be called")
    assert parse("18 January 1986", languages=["en"], detect_languages_function=detector) == datetime(1986, 1, 18)
    assert calls == []


def test_a09_native_embedded_timezone_instant():
    from dateparser import parse
    value = parse("2008-07-06 10:00 +0200", languages=["en"], settings=base_settings(TIMEZONE="UTC", TO_TIMEZONE="Asia/Tokyo", RETURN_AS_TIMEZONE_AWARE=True))
    assert value.hour == 17 and value.utcoffset() == timedelta(hours=9)


def test_a10_native_french_locale():
    from dateparser import parse
    assert parse("21 juillet 1987", languages=["fr"], settings=base_settings()) == datetime(1987, 7, 21)


def test_a11_source_generation_requires_strict_advance():
    from dateparser.reliable import RevisionConflict, SourceLedger
    with TemporaryDirectory() as td:
        source = SourceLedger(Path(td) / "source.json")
        source.advance("manual", 2, 0)
        with pytest.raises(RevisionConflict):
            source.advance("manual", 2, 2)


def test_a12_timezone_prepare_and_ack_are_distinct():
    from dateparser.reliable import Receipt, TimezoneStore
    with TemporaryDirectory() as td:
        store = TimezoneStore(Path(td) / "timezone.json")
        generation = store.publish("zones-c", {"PORT": 120, "HOME": 0}, 0)
        source = Receipt.issue("source-c", "source.acknowledged", 1)
        decision = store.resolve("trip-c", datetime(2050, 1, 2, 12), "PORT", "HOME", generation, [source])
        acknowledged = store.acknowledge(decision.receipt)
        assert decision.status == "prepared" and acknowledged.kind == "timezone.acknowledged"


def test_a13_delivery_and_ack_are_distinct():
    from dateparser.reliable import DeliveryOutbox, Receipt
    with TemporaryDirectory() as td:
        outbox = DeliveryOutbox(Path(td) / "outbox.json")
        schedule = outbox.publish_schedule("window", [(datetime(2050, 1, 1), datetime(2051, 1, 1))], 0)
        source = Receipt.issue("source-d", "source.acknowledged", 1)
        prepared = outbox.prepare("message-d", {"x": 1}, datetime(2050, 5, 1), schedule, [source])
        delivered = outbox.deliver(outbox.make_visible(prepared), "delivery-d")
        assert outbox.snapshot().messages["message-d"]["status"] == "delivered"
        acknowledged = outbox.acknowledge(delivered)
        assert acknowledged.kind == "outbox.acknowledged"


def test_a14_receipt_wire_is_detached():
    from dateparser.reliable import Receipt
    original = Receipt.issue("owner-r", "kind-r", 4, {"upstream": "token-a"})
    wire = original.as_dict()
    restored = Receipt.from_dict(wire)
    wire["dependencies"]["upstream"] = "changed"
    assert restored.verify() and restored.dependencies == {"upstream": "token-a"}


def test_a15_source_append_and_ack_are_distinct():
    from dateparser.reliable import SourceLedger
    with TemporaryDirectory() as td:
        source = SourceLedger(Path(td) / "source.json")
        generation = source.advance("manual", 1, 0)
        appended = source.append("evt-coral", "manual", "2051-04-16", generation, expected_position=0)
        assert source.snapshot().events[0]["status"] == "appended"
        acknowledged = source.acknowledge(appended)
        assert acknowledged.kind == "source.acknowledged" and source.snapshot().events[0]["status"] == "acknowledged"


def test_a16_index_owns_empty_revision():
    from dateparser.reliable import AcknowledgedIndex
    with TemporaryDirectory() as td:
        index = AcknowledgedIndex(Path(td) / "index.json")
        snapshot = index.snapshot()
        assert snapshot.revision == 0 and snapshot.sources == {} and snapshot.hits == ()


def test_a17_timezone_generation_retires():
    from dateparser.reliable import TimezoneStore
    with TemporaryDirectory() as td:
        store = TimezoneStore(Path(td) / "timezone.json")
        first = store.publish("release-a", {"PORT": 60, "HOME": 0}, 0)
        second = store.publish("release-b", {"PORT": 120, "HOME": 0}, 1)
        retired = store.retire(first, second)
        assert retired.kind == "timezone.retired" and store.generation_status(1) == "retired"
        assert store.snapshot().generation == 2


def test_a18_outbox_prepare_is_invisible():
    from dateparser.reliable import DeliveryOutbox, Receipt
    with TemporaryDirectory() as td:
        outbox = DeliveryOutbox(Path(td) / "outbox.json")
        schedule = outbox.publish_schedule("window", [(datetime(2052, 1, 1), datetime(2053, 1, 1))], 0)
        upstream = Receipt.issue("source-x", "source.acknowledged", 1)
        outbox.prepare("message-cove", {"v": 1}, datetime(2052, 5, 1), schedule, [upstream])
        snap = outbox.snapshot()
        assert snap.messages["message-cove"]["status"] == "prepared" and snap.visible_ids == ()


def test_a19_replay_takeover_fences_old_lease():
    from dateparser.reliable import ReplayLedger, Receipt, StaleGenerationError
    with TemporaryDirectory() as td:
        replay = ReplayLedger(Path(td) / "replay.json")
        old = replay.acquire("stream", "worker-old", 1, 0)
        replay.acquire("stream", "worker-new", 2, 1)
        acknowledged = Receipt.issue("outbox-x", "outbox.acknowledged", 1)
        with pytest.raises(StaleGenerationError):
            replay.advance("stream", old, [acknowledged], expected_cursor=0)


def test_a20_source_history_survives_reopen():
    from dateparser.reliable import SourceLedger
    with TemporaryDirectory() as td:
        path = Path(td) / "source.json"
        source = SourceLedger(path)
        generation = source.advance("manual", 3, 0)
        appended = source.append("evt-dune", "manual", "2054-06-18", generation, expected_position=0)
        acknowledged = source.acknowledge(appended)
        reopened = SourceLedger(path)
        assert reopened.verify(acknowledged) and reopened.snapshot().events[0]["generation"] == 3
