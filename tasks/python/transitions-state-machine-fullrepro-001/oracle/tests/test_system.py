from __future__ import annotations

import json
import pytest


def services(tmp_path, api):
    journal = api("TransitionJournal")(tmp_path / "journal.log")
    scheduler = api("LeaseScheduler")(tmp_path / "scheduler.json")
    topology = api("TopologyRegistry")(tmp_path / "topology.json")
    attachments = api("AttachmentStore")(tmp_path / "attachments.json")
    outbox = api("PublicationOutbox")(tmp_path / "outbox.json")
    coordinator = api("DurableMachine")(journal, scheduler, topology, attachments, outbox)
    return journal, scheduler, topology, attachments, outbox, coordinator


def start(tmp_path, api, entity, states, edge):
    journal, scheduler, topology, attachments, outbox, coordinator = services(tmp_path, api)
    topology.create(states, [edge])
    attached = attachments.attach(entity, "workflow", topology_generation=1, state=states[0])
    attachments.claim_owner(entity, "process-a", expected_attachment_generation=attached["attachment_generation"])
    helper = attachments.helper_token(entity, edge[0])
    return journal, scheduler, topology, attachments, outbox, coordinator, helper


@pytest.mark.system
def test_e01_immediate_commit_closes_four_owner_receipts_then_publication(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = start(
        tmp_path, api, "document-9", ["draft", "ready"], ("approve", "draft", "ready")
    )
    result = coordinator.transition("document-9", "approve", helper_token=helper, idempotency_key="approve-doc", expected_revision=0)
    assert attachments.current("document-9")["state"] == "ready"
    assert journal.replay("document-9", initial="draft") == "ready"
    assert outbox.visible("document-9") == []
    published = coordinator.publish_due("publisher", now=0, lease_seconds=2, external_receipt={"offset": 91})
    assert published["journal_id"] == result["journal_receipt"]["journal_id"]
    assert published["topology_digest"] == topology.receipt(1)["digest"]


@pytest.mark.system
def test_e02_delayed_retry_commits_and_publishes_one_receipt(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = start(
        tmp_path, api, "message-7", ["queued", "sent"], ("send", "queued", "sent")
    )
    scheduled = coordinator.schedule("message-7", "send", helper_token=helper, due_at=3, idempotency_key="send-message")
    first = scheduler.claim("worker-a", now=3, lease_seconds=2)
    scheduler.retry(first["delivery_id"], first["lease_token"], due_at=8, reason="transport")
    result = coordinator.run_due("worker-b", now=8, lease_seconds=3)
    assert scheduler.get(scheduled["delivery_id"])["status"] == "acked"
    assert len(journal.history("message-7")) == 1 and attachments.current("message-7")["state"] == "sent"
    assert outbox.visible("message-7") == []
    coordinator.publish_due("publisher", now=8, lease_seconds=2, external_receipt={"offset": 7})
    assert outbox.visible("message-7")[0]["journal_id"] == result["journal_receipt"]["journal_id"]


@pytest.mark.system
def test_e03_migration_interleaving_rejects_old_intent_without_partial_visibility(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = start(
        tmp_path, api, "change-5", ["new", "review"], ("review", "new", "review")
    )
    coordinator.schedule("change-5", "review", helper_token=helper, due_at=2, idempotency_key="old-intent")
    migration = topology.migrate(expected_generation=1, add_states=["merged"], add_transitions=[("merge", "review", "merged")], aliases={"queued": "new"})
    detached = attachments.detach("change-5", expected_attachment_generation=1)
    rebound = attachments.rebind("change-5", "workflow", topology_generation=2, state="queued", expected_attachment_generation=detached["attachment_generation"])
    attachments.claim_owner("change-5", "process-b", expected_attachment_generation=rebound["attachment_generation"])
    with pytest.raises(api("StaleHelperError")):
        coordinator.run_due("worker", now=2, lease_seconds=2)
    assert journal.history("change-5") == [] and outbox.visible("change-5") == []
    current = attachments.helper_token("change-5", "review")
    result = coordinator.transition("change-5", "review", helper_token=current, idempotency_key="reconciled", expected_revision=0)
    assert result["topology_receipt_digest"] == migration["digest"] and attachments.current("change-5")["state"] == "review"


@pytest.mark.system
def test_e04_new_process_recovers_expired_preparation_with_current_owner(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = start(
        tmp_path, api, "batch-11", ["pending", "complete"], ("complete", "pending", "complete")
    )
    scheduled = coordinator.schedule("batch-11", "complete", helper_token=helper, due_at=1, idempotency_key="complete-batch")
    delivery = scheduler.claim("crashed", now=1, lease_seconds=2)
    prepared = journal.prepare("batch-11", "complete", "pending", "complete", expected_revision=0, idempotency_key="complete-batch")
    attachments.claim_owner("batch-11", "recovery-process", expected_attachment_generation=1)
    reopened = api("DurableMachine")(
        api("TransitionJournal")(journal.path),
        api("LeaseScheduler")(scheduler.path),
        api("TopologyRegistry")(topology.path),
        api("AttachmentStore")(attachments.path),
        api("PublicationOutbox")(outbox.path),
    )
    recovered = reopened.recover(prepared["prepare_id"], delivery["delivery_id"], now=4, worker="recovery")
    assert len(reopened.journal.history("batch-11")) == 1
    assert reopened.scheduler.get(scheduled["delivery_id"])["status"] == "acked"
    assert reopened.attachments.current("batch-11")["state"] == "complete"
    assert reopened.outbox.get(recovered["publication"]["publication_id"])["owner_generation"] == 2


@pytest.mark.system
def test_e05_duplicate_recovery_and_publication_redelivery_converge(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = start(
        tmp_path, api, "report-12", ["held", "released"], ("release", "held", "released")
    )
    result = coordinator.transition("report-12", "release", helper_token=helper, idempotency_key="release-once", expected_revision=0)
    duplicate = outbox.stage(result["journal_receipt"], topology.receipt(1), attachments.current("report-12"), idempotency_key="release-once")
    old = outbox.claim("publisher-a", now=0, lease_seconds=1)
    current = outbox.claim("publisher-b", now=2, lease_seconds=2)
    with pytest.raises(api("LeaseError")):
        outbox.ack(old["publication_id"], old["lease_token"], {"offset": 1})
    outbox.ack(current["publication_id"], current["lease_token"], {"offset": 2})
    assert duplicate["publication_id"] == result["publication"]["publication_id"]
    assert len(journal.history("report-12")) == len(outbox.visible("report-12")) == 1


@pytest.mark.system
def test_e06_fresh_process_observes_closed_receipt_chain(tmp_path, api, fresh_process):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = start(
        tmp_path, api, "ticket-13", ["open", "closed"], ("close", "open", "closed")
    )
    result = coordinator.transition("ticket-13", "close", helper_token=helper, idempotency_key="close-ticket", expected_revision=0)
    coordinator.publish_due("publisher", now=0, lease_seconds=2, external_receipt={"offset": 13})
    code = (
        "import json,transitions;"
        f"j=transitions.TransitionJournal({str(journal.path)!r});"
        f"t=transitions.TopologyRegistry({str(topology.path)!r});"
        f"a=transitions.AttachmentStore({str(attachments.path)!r});"
        f"o=transitions.PublicationOutbox({str(outbox.path)!r});"
        "v=o.visible('ticket-13');"
        "print(json.dumps({'history':len(j.history('ticket-13')),'state':a.current('ticket-13')['state'],'verified':t.verify_receipt(t.receipt(1)),'visible':len(v),'journal_id':v[0]['journal_id']}))"
    )
    observed = fresh_process(code)
    assert observed == {
        "history": 1,
        "state": "closed",
        "verified": True,
        "visible": 1,
        "journal_id": result["journal_receipt"]["journal_id"],
    }
