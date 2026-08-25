from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.support import (
    BASE,
    acknowledged_delivery,
    acknowledged_source,
    acknowledged_timezone,
    active_timezone,
    base_settings,
    current_schedule,
    open_owners,
    projected_source,
)


def test_c01_index_projects_acknowledged_source():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        acknowledged, _ = acknowledged_source(owners["source"], "cedar", "meet 2061-02-03")
        projected = owners["index"].project(owners["source"], acknowledged, 0)
        snapshot = owners["index"].snapshot()
        assert projected.depends_on(acknowledged) and snapshot.hits[0]["text"] == "2061-02-03"


def test_c02_index_rejects_unacknowledged_source():
    from dateparser.reliable import ReceiptError
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        generation = owners["source"].advance("document", 1, 0)
        appended = owners["source"].append("event-elm", "document", "2062-03-04", generation, 0)
        with pytest.raises(ReceiptError):
            owners["index"].project(owners["source"], appended, 0)
        assert owners["index"].snapshot().revision == 0


def test_c03_reopened_source_ack_projects_once():
    from dateparser.reliable import AcknowledgedIndex, SourceLedger
    with TemporaryDirectory() as td:
        root = Path(td)
        owners = open_owners(root)
        acknowledged, _ = acknowledged_source(owners["source"], "fir", "2063-04-05")
        source = SourceLedger(root / "source.json")
        index = AcknowledgedIndex(root / "index.json")
        first = index.project(source, acknowledged, 0)
        second = index.project(source, acknowledged, 1)
        assert first.token == second.token and index.snapshot().revision == 1


def test_c04_source_fence_blocks_stale_index_input():
    from dateparser.reliable import StaleGenerationError
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        old = owners["source"].advance("document", 1, 0)
        owners["source"].advance("document", 2, 1)
        with pytest.raises(StaleGenerationError):
            owners["source"].append("event-grove", "document", "2064-05-06", old, 0)
        assert owners["index"].snapshot().revision == 0


def test_c05_index_ack_projection_is_exactly_once():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        acknowledged, _ = acknowledged_source(owners["source"], "harbor", "2065-06-07")
        first = owners["index"].project(owners["source"], acknowledged, 0)
        second = owners["index"].project(owners["source"], acknowledged, 1)
        assert first.token == second.token and owners["index"].snapshot().revision == 1


def test_c06_index_history_retains_ack_dependency():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        first, _ = acknowledged_source(owners["source"], "iris", "2066-07-08")
        owners["index"].project(owners["source"], first, 0)
        second, _ = acknowledged_source(owners["source"], "juniper", "2066-09-10")
        owners["index"].project(owners["source"], second, 1)
        old = owners["index"].snapshot(1)
        assert old.acknowledgements == {"document": first.token}
        assert owners["index"].snapshot().acknowledgements == {"document": second.token}


def test_c07_timezone_decision_carries_source_ack():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        acknowledged, _ = acknowledged_source(owners["source"], "kite")
        generation = active_timezone(owners["timezone"])
        decision = owners["timezone"].resolve("trip-kite", datetime(2067, 8, 9, 12), "PORT", "HOME", generation, [acknowledged])
        assert decision.receipt.depends_on(acknowledged) and decision.projected == datetime(2067, 8, 9, 10)


def test_c08_timezone_decision_closes_index_receipt():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        _, projected, _ = projected_source(owners["source"], owners["index"], "lagoon")
        generation = active_timezone(owners["timezone"])
        decision = owners["timezone"].resolve("trip-lagoon", datetime(2068, 9, 10, 12), "PORT", "HOME", generation, [projected])
        acknowledged = owners["timezone"].acknowledge(decision.receipt)
        assert acknowledged.depends_on(projected) and owners["timezone"].verify(acknowledged)


def test_c09_retired_timezone_generation_rejects_new_source():
    from dateparser.reliable import StaleGenerationError
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "marsh")
        old = active_timezone(owners["timezone"], "old-zones", 60)
        new = owners["timezone"].publish("new-zones", {"PORT": 180, "HOME": 0}, 1)
        owners["timezone"].retire(old, new)
        with pytest.raises(StaleGenerationError):
            owners["timezone"].resolve("trip-marsh", datetime(2069, 10, 11, 12), "PORT", "HOME", old, [source_ack])
        assert owners["source"].verify(source_ack)


def test_c10_unacknowledged_timezone_retry_rotates_and_keeps_source():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "north")
        old = active_timezone(owners["timezone"], "zones-old", 60)
        decision = owners["timezone"].resolve("trip-north", datetime(2070, 11, 12, 12), "PORT", "HOME", old, [source_ack])
        new = owners["timezone"].publish("zones-new", {"PORT": 240, "HOME": 0}, 1)
        owners["timezone"].retire(old, new)
        retried = owners["timezone"].retry("trip-north")
        assert retried.provider_label == "zones-new" and retried.projected == datetime(2070, 11, 12, 8)
        assert retried.receipt.depends_on(source_ack) and decision.projected != retried.projected


def test_c11_acknowledged_timezone_decision_pins_index_dependency():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        _, projected, _ = projected_source(owners["source"], owners["index"], "orchard")
        old = active_timezone(owners["timezone"], "zones-pin", 60)
        decision = owners["timezone"].resolve("trip-orchard", datetime(2071, 12, 13, 12), "PORT", "HOME", old, [projected])
        accepted = owners["timezone"].acknowledge(decision.receipt)
        new = owners["timezone"].publish("zones-drift", {"PORT": 300, "HOME": 0}, 1)
        owners["timezone"].retire(old, new)
        retried = owners["timezone"].retry("trip-orchard")
        assert retried.provider_label == "zones-pin" and retried.receipt.token == accepted.token
        assert retried.receipt.depends_on(projected)


def test_c12_source_and_timezone_receipts_verify_after_reopen():
    from dateparser.reliable import SourceLedger, TimezoneStore
    with TemporaryDirectory() as td:
        root = Path(td)
        owners = open_owners(root)
        source_ack, _ = acknowledged_source(owners["source"], "prairie")
        timezone_ack, _ = acknowledged_timezone(owners["timezone"], source_ack, "prairie")
        source = SourceLedger(root / "source.json")
        timezone = TimezoneStore(root / "timezone.json")
        assert source.verify(source_ack) and timezone.verify(timezone_ack) and timezone_ack.depends_on(source_ack)


def test_c13_outbox_prepare_carries_source_ack():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "quarry")
        schedule = current_schedule(owners["outbox"], "quarry")
        prepared = owners["outbox"].prepare("message-quarry", {"q": 1}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        assert prepared.depends_on(source_ack) and owners["outbox"].snapshot().visible_ids == ()


def test_c14_visibility_preserves_source_dependency():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "ridge")
        schedule = current_schedule(owners["outbox"], "ridge")
        prepared = owners["outbox"].prepare("message-ridge", {}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        visible = owners["outbox"].make_visible(prepared)
        assert visible.depends_on(source_ack) and owners["outbox"].snapshot().visible_ids == ("message-ridge",)


def test_c15_delivery_requires_timezone_ack():
    from dateparser.reliable import ReceiptError
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "summit")
        timezone_generation = active_timezone(owners["timezone"])
        decision = owners["timezone"].resolve("trip-summit", datetime(2111, 3, 14, 12), "PORT", "HOME", timezone_generation, [source_ack])
        schedule = current_schedule(owners["outbox"], "summit")
        prepared = owners["outbox"].prepare("message-summit", {}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        visible = owners["outbox"].make_visible(prepared)
        with pytest.raises(ReceiptError):
            owners["outbox"].deliver(visible, "delivery-summit", [decision.receipt])
        timezone_ack = owners["timezone"].acknowledge(decision.receipt)
        delivered = owners["outbox"].deliver(visible, "delivery-summit", [timezone_ack])
        assert delivered.depends_on(timezone_ack)


def test_c16_replay_advances_only_from_delivery_ack():
    from dateparser.reliable import ReceiptError
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "timber")
        schedule = current_schedule(owners["outbox"], "timber")
        prepared = owners["outbox"].prepare("message-timber", {}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        delivered = owners["outbox"].deliver(owners["outbox"].make_visible(prepared), "delivery-timber")
        lease = owners["replay"].acquire("stream", "worker", 1, 0)
        with pytest.raises(ReceiptError):
            owners["replay"].advance("stream", lease, [delivered], 0)
        acknowledged = owners["outbox"].acknowledge(delivered)
        cursor = owners["replay"].advance("stream", lease, [acknowledged], 0)
        assert cursor.revision == 1 and cursor.depends_on(acknowledged)


def test_c17_prepared_message_remains_invisible_after_owner_reopen():
    from dateparser.reliable import DeliveryOutbox, SourceLedger
    with TemporaryDirectory() as td:
        root = Path(td)
        owners = open_owners(root)
        source_ack, _ = acknowledged_source(owners["source"], "upland")
        schedule = current_schedule(owners["outbox"], "upland")
        owners["outbox"].prepare("message-upland", {}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        source = SourceLedger(root / "source.json")
        outbox = DeliveryOutbox(root / "outbox.json")
        assert source.verify(source_ack) and outbox.snapshot().visible_ids == ()
        assert outbox.snapshot().messages["message-upland"]["status"] == "prepared"


def test_c18_delivered_unacknowledged_message_is_recoverable():
    from dateparser.reliable import DeliveryOutbox, SourceLedger
    with TemporaryDirectory() as td:
        root = Path(td)
        owners = open_owners(root)
        source_ack, _ = acknowledged_source(owners["source"], "valley")
        schedule = current_schedule(owners["outbox"], "valley")
        prepared = owners["outbox"].prepare("message-valley", {}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        owners["outbox"].deliver(owners["outbox"].make_visible(prepared), "delivery-valley")
        source = SourceLedger(root / "source.json")
        outbox = DeliveryOutbox(root / "outbox.json")
        assert source.verify(source_ack) and outbox.snapshot().recoverable_ids == ("message-valley",)


def test_c19_delivery_attempt_is_exactly_once_with_timezone_ack():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, _ = acknowledged_source(owners["source"], "willow")
        timezone_ack, _ = acknowledged_timezone(owners["timezone"], source_ack, "willow")
        schedule = current_schedule(owners["outbox"], "willow")
        prepared = owners["outbox"].prepare("message-willow", {}, datetime(2111, 3, 14, 12), schedule, [source_ack])
        visible = owners["outbox"].make_visible(prepared)
        first = owners["outbox"].deliver(visible, "delivery-willow", [timezone_ack])
        second = owners["outbox"].deliver(visible, "delivery-willow", [timezone_ack])
        assert first.token == second.token and first.depends_on(timezone_ack)


def test_c20_replay_cursor_closes_index_receipt():
    with TemporaryDirectory() as td:
        owners = open_owners(Path(td))
        source_ack, projected, _ = projected_source(owners["source"], owners["index"], "xylem")
        delivery_ack, _, _ = acknowledged_delivery(owners["outbox"], source_ack, "xylem")
        lease = owners["replay"].acquire("stream", "worker", 1, 0)
        cursor = owners["replay"].advance("stream", lease, [delivery_ack, projected], 0)
        assert cursor.depends_on(delivery_ack) and cursor.depends_on(projected)
        assert owners["replay"].snapshot("stream").cursor == 1


def test_c21_native_direct_and_structured_absolute_agree():
    from dateparser import DateDataParser, parse
    direct = parse("26 February 1979", languages=["en"], settings=base_settings())
    structured = DateDataParser(languages=["en"], settings=base_settings()).get_date_data("26 February 1979")
    assert direct == structured.date_obj == datetime(1979, 2, 26)


def test_c22_native_relative_views_use_complete_base():
    from dateparser import DateDataParser, parse
    direct = parse("3 days ago", languages=["en"], settings=base_settings())
    structured = DateDataParser(languages=["en"], settings=base_settings()).get_date_data("3 days ago")
    assert direct == structured.date_obj == BASE - timedelta(days=3)


def test_c23_native_explicit_language_bypasses_both_detectors():
    from dateparser import DateDataParser, parse
    calls = []
    def detector(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("must not run")
    direct = parse("19 March 1989", languages=["en"], detect_languages_function=detector)
    structured = DateDataParser(languages=["en"], detect_languages_function=detector).get_date_data("19 March 1989")
    assert direct == structured.date_obj == datetime(1989, 3, 19) and calls == []


def test_c24_native_timezone_views_preserve_same_instant():
    from dateparser import DateDataParser, parse
    settings = base_settings(TIMEZONE="UTC", TO_TIMEZONE="America/New_York", RETURN_AS_TIMEZONE_AWARE=True)
    text = "2010-11-12 14:00 +0300"
    direct = parse(text, languages=["en"], settings=settings)
    structured = DateDataParser(languages=["en"], settings=settings).get_date_data(text)
    assert direct == structured.date_obj and direct.utcoffset() == timedelta(hours=-5)


def test_c25_native_search_and_direct_parse_agree():
    from dateparser import parse
    from dateparser.search import search_dates
    settings = base_settings()
    found = search_dates("recorded on 2012-04-16", languages=["en"], settings=settings)
    assert found[0][1] == parse(found[0][0], languages=["en"], settings=settings)


def test_c26_native_explicit_format_order_matches_structured_view():
    from dateparser import DateDataParser, parse
    formats = ["%d.%m.%Y", "%m.%d.%Y"]
    text = "07.08.2013"
    direct = parse(text, date_formats=formats, languages=["en"], settings=base_settings())
    structured = DateDataParser(languages=["en"], settings=base_settings()).get_date_data(text, date_formats=formats)
    assert direct == structured.date_obj == datetime(2013, 8, 7)
