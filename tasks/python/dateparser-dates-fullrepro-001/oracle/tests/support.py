from __future__ import annotations

from datetime import datetime


BASE = datetime(2046, 7, 8, 9, 10, 11)


def base_settings(**overrides):
    values = {"RELATIVE_BASE": BASE, "PREFER_DATES_FROM": "past"}
    values.update(overrides)
    return values


def open_owners(root):
    from dateparser.reliable import AcknowledgedIndex, DeliveryOutbox, ReplayLedger, SourceLedger, TimezoneStore

    return {
        "source": SourceLedger(root / "source.json"),
        "index": AcknowledgedIndex(root / "index.json"),
        "timezone": TimezoneStore(root / "timezone.json"),
        "outbox": DeliveryOutbox(root / "outbox.json"),
        "replay": ReplayLedger(root / "replay.json"),
    }


def acknowledged_source(source, suffix="a", text="2111-03-14", generation=1):
    current = source.snapshot().generations.get("document", 0)
    if current < generation:
        generation_receipt = source.advance("document", generation, current)
    else:
        generation_receipt = source.generation_receipt("document", generation)
    appended = source.append(
        f"event-{suffix}", "document", text, generation_receipt,
        expected_position=source.snapshot().position,
    )
    return source.acknowledge(appended), generation_receipt


def projected_source(source, index, suffix="a", text="2111-03-14", generation=1):
    acknowledged, generation_receipt = acknowledged_source(source, suffix, text, generation)
    projected = index.project(source, acknowledged, expected_revision=index.snapshot().revision)
    return acknowledged, projected, generation_receipt


def active_timezone(store, label="zones-a", input_offset=120):
    current = store.snapshot().generation
    return store.publish(label, {"PORT": input_offset, "HOME": 0}, expected_generation=current)


def acknowledged_timezone(store, prerequisite, suffix="a", generation=None):
    generation = generation or active_timezone(store)
    decision = store.resolve(
        f"decision-{suffix}", datetime(2111, 3, 14, 12), "PORT", "HOME",
        generation, prerequisites=[prerequisite],
    )
    return store.acknowledge(decision.receipt), generation


def current_schedule(outbox, suffix="a"):
    return outbox.publish_schedule(
        f"schedule-{suffix}",
        [(datetime(2110, 1, 1), datetime(2113, 1, 1))],
        expected_revision=outbox.snapshot().schedule_revision,
    )


def acknowledged_delivery(outbox, prerequisite, suffix="a", extra=()):
    schedule = current_schedule(outbox, suffix)
    prepared = outbox.prepare(
        f"message-{suffix}", {"value": suffix}, datetime(2111, 3, 14, 12),
        schedule, prerequisites=[prerequisite],
    )
    visible = outbox.make_visible(prepared)
    delivered = outbox.deliver(visible, f"delivery-{suffix}", prerequisites=list(extra))
    return outbox.acknowledge(delivered), schedule, delivered


def closed_workflow(root, suffix="a"):
    from dateparser.reliable import ReliablePipeline

    owners = open_owners(root)
    source_generation = owners["source"].advance("document", 1, 0)
    timezone_generation = active_timezone(owners["timezone"], f"zones-{suffix}")
    schedule = current_schedule(owners["outbox"], suffix)
    lease = owners["replay"].acquire("stream", "worker-a", 1, 0)
    pipeline = ReliablePipeline(**owners)
    receipt = pipeline.process(
        f"event-{suffix}", "document", f"arrival {2111 + len(suffix)}-03-14",
        source_generation,
        f"decision-{suffix}", datetime(2111, 3, 14, 12), "PORT", "HOME",
        timezone_generation,
        f"message-{suffix}", {"event": suffix}, datetime(2111, 3, 14, 12),
        schedule, "stream", lease, f"delivery-{suffix}",
    )
    return owners, pipeline, receipt, {
        "source_generation": source_generation,
        "timezone_generation": timezone_generation,
        "schedule": schedule,
        "lease": lease,
    }
