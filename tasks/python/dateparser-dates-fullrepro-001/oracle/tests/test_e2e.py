from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.support import closed_workflow, open_owners


def test_e01_success_then_source_fence_failure_survives_full_reopen():
    from dateparser.reliable import ReliablePipeline, StaleGenerationError
    with TemporaryDirectory() as td:
        root = Path(td)
        owners, pipeline, closed, context = closed_workflow(root, "amber")
        owners["source"].advance("document", 2, 1)
        with pytest.raises(StaleGenerationError):
            pipeline.process(
                "event-after", "document", "arrival 2112-04-15", context["source_generation"],
                "decision-after", datetime(2111, 4, 15, 12), "PORT", "HOME", context["timezone_generation"],
                "message-after", {"event": "after"}, datetime(2111, 4, 15, 12), context["schedule"],
                "stream", context["lease"], "delivery-after",
            )
        reopened = open_owners(root)
        restored = ReliablePipeline(**reopened)
        assert restored.verify(closed)
        assert reopened["index"].snapshot().revision == 1
        assert len(reopened["outbox"].snapshot().acknowledged_ids) == 1
        assert reopened["replay"].snapshot("stream").cursor == 1


def test_e02_success_then_stale_replay_failure_preserves_closure_after_reopen():
    from dateparser.reliable import ReliablePipeline, StaleGenerationError
    with TemporaryDirectory() as td:
        root = Path(td)
        owners, _, closed, context = closed_workflow(root, "birch")
        outbox_ack = owners["outbox"].receipt(closed.dependencies[owners["outbox"].owner_id])
        owners["replay"].acquire("stream", "worker-new", 2, 1)
        with pytest.raises(StaleGenerationError):
            owners["replay"].advance("stream", context["lease"], [outbox_ack], 1)
        reopened = open_owners(root)
        restored = ReliablePipeline(**reopened)
        assert restored.verify(closed)
        assert reopened["replay"].snapshot("stream").generation == 2
        assert reopened["replay"].snapshot("stream").cursor == 1
        assert len(reopened["outbox"].snapshot().acknowledged_ids) == 1


def test_e03_success_then_retired_timezone_failure_blocks_delivery_after_reopen():
    from dateparser.reliable import ReliablePipeline, StaleGenerationError
    with TemporaryDirectory() as td:
        root = Path(td)
        owners, pipeline, closed, context = closed_workflow(root, "cinder")
        replacement = owners["timezone"].publish("zones-replacement", {"PORT": 300, "HOME": 0}, 1)
        owners["timezone"].retire(context["timezone_generation"], replacement)
        with pytest.raises(StaleGenerationError):
            pipeline.process(
                "event-later", "document", "arrival 2112-05-16", context["source_generation"],
                "decision-later", datetime(2111, 5, 16, 12), "PORT", "HOME", context["timezone_generation"],
                "message-later", {"event": "later"}, datetime(2111, 5, 16, 12), context["schedule"],
                "stream", context["lease"], "delivery-later",
            )
        reopened = open_owners(root)
        restored = ReliablePipeline(**reopened)
        assert restored.verify(closed)
        assert len(reopened["outbox"].snapshot().acknowledged_ids) == 1
        assert reopened["replay"].snapshot("stream").cursor == 1
        assert reopened["timezone"].generation_status(1) == "retired"


def test_e04_success_then_unacked_delivery_recovers_before_replay_after_reopen():
    from dateparser.reliable import Receipt, ReliablePipeline
    with TemporaryDirectory() as td:
        root = Path(td)
        owners, pipeline, closed, context = closed_workflow(root, "delta")
        source_appended = owners["source"].append(
            "event-followup", "document", "arrival 2112-06-17", context["source_generation"],
            owners["source"].snapshot().position,
        )
        source_ack = owners["source"].acknowledge(source_appended)
        indexed = owners["index"].project(owners["source"], source_ack, 1)
        timezone_ack = owners["timezone"].retry("decision-delta").receipt
        prepared = owners["outbox"].prepare(
            "message-followup", {"event": "followup"}, datetime(2111, 6, 17, 12),
            context["schedule"], [source_ack],
        )
        visible = owners["outbox"].make_visible(prepared)
        delivered = owners["outbox"].deliver(visible, "delivery-followup", [timezone_ack])

        reopened = open_owners(root)
        assert reopened["outbox"].snapshot().recoverable_ids == ("message-followup",)
        assert reopened["replay"].snapshot("stream").cursor == 1
        outbox_ack = reopened["outbox"].acknowledge(delivered)
        cursor = reopened["replay"].advance("stream", context["lease"], [outbox_ack, indexed], 1)
        restored = ReliablePipeline(**reopened)
        resumed = Receipt.chain(restored.owner_id, "workflow.closed", cursor.revision, [source_ack, indexed, timezone_ack, outbox_ack, cursor])
        assert restored.verify(closed) and restored.verify(resumed)
        assert reopened["outbox"].snapshot().recoverable_ids == ()
        assert reopened["replay"].snapshot("stream").cursor == 2
