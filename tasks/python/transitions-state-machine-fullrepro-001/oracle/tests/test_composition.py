from __future__ import annotations

import json
import pytest
import transitions


class Model:
    pass


def durable(tmp_path, api):
    journal = api("TransitionJournal")(tmp_path / "journal.log")
    scheduler = api("LeaseScheduler")(tmp_path / "scheduler.json")
    topology = api("TopologyRegistry")(tmp_path / "topology.json")
    attachments = api("AttachmentStore")(tmp_path / "attachments.json")
    outbox = api("PublicationOutbox")(tmp_path / "outbox.json")
    return journal, scheduler, topology, attachments, outbox


def bound(tmp_path, api, *, entity="item-1", states=("draft", "ready"), edge=("approve", "draft", "ready")):
    journal, scheduler, topology, attachments, outbox = durable(tmp_path, api)
    topology.create(list(states), [edge])
    attached = attachments.attach(entity, "machine", topology_generation=1, state=states[0])
    attachments.claim_owner(entity, "process-a", expected_attachment_generation=attached["attachment_generation"])
    helper = attachments.helper_token(entity, edge[0])
    coordinator = api("DurableMachine")(journal, scheduler, topology, attachments, outbox)
    return journal, scheduler, topology, attachments, outbox, coordinator, helper


@pytest.mark.composition
def test_c01_success_aligns_model_predicate_query_and_callbacks():
    trace = []
    model = Model()
    machine = transitions.Machine(model=model, states=["cold", transitions.State("hot", on_enter=lambda: trace.append("enter"))], initial="cold", auto_transitions=False)
    machine.add_transition("heat", "cold", "hot", after=lambda: trace.append("after"))
    assert model.heat() is True
    assert (model.state, model.is_hot(), machine.get_model_state(model).name) == ("hot", True, "hot")
    assert trace == ["enter", "after"]


@pytest.mark.composition
def test_c02_blocked_event_preserves_views_and_callbacks():
    trace = []
    model = Model()
    machine = transitions.Machine(model=model, states=["closed", "open"], initial="closed", auto_transitions=False)
    machine.add_transition("open", "closed", "open", conditions=lambda: False, before=lambda: trace.append("before"))
    assert model.may_open() is False and model.open() is False
    assert model.state == "closed" and model.is_closed() and trace == []


@pytest.mark.composition
def test_c03_callback_arguments_follow_state_visibility():
    trace = []
    model = Model()
    machine = transitions.Machine(model=model, states=["new", "paid"], initial="new", auto_transitions=False)
    machine.add_transition("pay", "new", "paid", before=lambda amount: trace.append(("before", amount, model.state)), after=lambda amount: trace.append(("after", amount, model.state)))
    assert model.pay(23) is True
    assert trace == [("before", 23, "new"), ("after", 23, "paid")]


@pytest.mark.composition
def test_c04_dispatch_aggregates_independent_model_results():
    left, right = Model(), Model()
    left.allowed, right.allowed = True, False
    machine = transitions.Machine(model=[left, right], states=["held", "free"], initial="held", auto_transitions=False, send_event=True)
    machine.add_transition("release", "held", "free", conditions=lambda event: event.model.allowed)
    assert machine.dispatch("release") is False
    assert left.state == "free" and right.state == "held"


@pytest.mark.composition
def test_c05_process_reopen_preserves_preparation_and_expired_delivery(tmp_path, api, fresh_process):
    journal, scheduler, topology, attachments, outbox = durable(tmp_path, api)
    prepared = journal.prepare("parcel-5", "send", "held", "sent", expected_revision=0, idempotency_key="send-5")
    scheduled = scheduler.schedule("parcel-5", "send", due_at=2, idempotency_key="send-5")
    first = scheduler.claim("worker-a", now=2, lease_seconds=2)
    code = (
        "import json,transitions;"
        f"j=transitions.TransitionJournal({str(journal.path)!r});"
        f"s=transitions.LeaseScheduler({str(scheduler.path)!r});"
        "d=s.claim('worker-b',now=5,lease_seconds=3);"
        "print(json.dumps({'pending':len(j.pending()),'attempt':d['attempt'],'token':d['lease_token']}))"
    )
    observed = fresh_process(code)
    assert observed["pending"] == 1 and observed["attempt"] == 2
    assert observed["token"] != first["lease_token"] and scheduled["delivery_id"] == first["delivery_id"]
    assert prepared["status"] == "prepared"


@pytest.mark.composition
def test_c06_stale_scheduler_token_cannot_close_prepared_journal(tmp_path, api):
    journal, scheduler, topology, attachments, outbox = durable(tmp_path, api)
    prepared = journal.prepare("asset-6", "publish", "draft", "live", expected_revision=0, idempotency_key="asset-pub")
    delivery = scheduler.schedule("asset-6", "publish", due_at=1, idempotency_key="asset-pub")
    old = scheduler.claim("lost", now=1, lease_seconds=1)
    current = scheduler.claim("current", now=3, lease_seconds=2)
    with pytest.raises(api("LeaseError")):
        scheduler.ack(delivery["delivery_id"], old["lease_token"], journal.commit(prepared["prepare_id"]))
    assert scheduler.ack(delivery["delivery_id"], current["lease_token"], journal.history("asset-6")[0])["status"] == "acked"


@pytest.mark.composition
def test_c07_retry_and_journal_idempotency_converge_after_reopen(tmp_path, api):
    journal, scheduler, topology, attachments, outbox = durable(tmp_path, api)
    scheduler.schedule("job-7", "finish", due_at=1, idempotency_key="finish-once")
    first = scheduler.claim("one", now=1, lease_seconds=2)
    scheduler.retry(first["delivery_id"], first["lease_token"], due_at=5, reason="restart")
    prepared = journal.prepare("job-7", "finish", "open", "done", expected_revision=0, idempotency_key="finish-once")
    receipt = api("TransitionJournal")(journal.path).commit(prepared["prepare_id"])
    reopened = api("LeaseScheduler")(scheduler.path)
    second = reopened.claim("two", now=5, lease_seconds=2)
    reopened.ack(second["delivery_id"], second["lease_token"], receipt)
    assert len(api("TransitionJournal")(journal.path).history("job-7")) == 1
    assert reopened.get(second["delivery_id"])["ack_receipt"]["journal_id"] == receipt["journal_id"]


@pytest.mark.composition
def test_c08_duplicate_delivery_cannot_duplicate_commit(tmp_path, api):
    journal, scheduler, topology, attachments, outbox = durable(tmp_path, api)
    scheduler.schedule("mail-8", "deliver", due_at=0, idempotency_key="mail-once")
    first = scheduler.claim("first", now=0, lease_seconds=1)
    prepared = journal.prepare("mail-8", "deliver", "queued", "sent", expected_revision=0, idempotency_key="mail-once")
    receipt = journal.commit(prepared["prepare_id"])
    second = scheduler.claim("second", now=2, lease_seconds=2)
    assert journal.prepare("mail-8", "deliver", "queued", "sent", expected_revision=0, idempotency_key="mail-once") == receipt
    scheduler.ack(second["delivery_id"], second["lease_token"], receipt)
    assert len(journal.history("mail-8")) == 1 and first["lease_token"] != second["lease_token"]


@pytest.mark.composition
def test_c09_migration_blocks_queued_old_generation_until_rebind(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    coordinator.schedule("item-1", "approve", helper_token=helper, due_at=1, idempotency_key="queued-old")
    topology.migrate(expected_generation=1, add_states=["archived"], add_transitions=[("archive", "ready", "archived")])
    with pytest.raises(api("StaleHelperError")):
        coordinator.run_due("worker", now=1, lease_seconds=2)
    assert journal.history("item-1") == [] and outbox.visible("item-1") == []


@pytest.mark.composition
def test_c10_alias_migration_needs_current_attachment_and_helper(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    migration = topology.migrate(expected_generation=1, aliases={"waiting": "draft"})
    detached = attachments.detach("item-1", expected_attachment_generation=1)
    attachments.rebind("item-1", "machine", topology_generation=migration["generation"], state="waiting", expected_attachment_generation=detached["attachment_generation"])
    with pytest.raises(api("StaleHelperError")):
        coordinator.transition("item-1", "approve", helper_token=helper, idempotency_key="old-helper", expected_revision=0)
    current = attachments.helper_token("item-1", "approve")
    result = coordinator.transition("item-1", "approve", helper_token=current, idempotency_key="current-helper", expected_revision=0)
    assert result["topology_receipt_digest"] == migration["digest"]


@pytest.mark.composition
def test_c11_topology_receipt_bound_to_committed_journal_envelope(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    result = coordinator.transition("item-1", "approve", helper_token=helper, idempotency_key="bind-receipts", expected_revision=0)
    staged = outbox.get(result["publication"]["publication_id"])
    assert staged["journal_id"] == result["journal_receipt"]["journal_id"]
    assert staged["topology_digest"] == topology.receipt(1)["digest"]
    assert staged["attachment_generation"] == attachments.current("item-1")["attachment_generation"]


@pytest.mark.composition
def test_c12_old_generation_receipt_cannot_authorize_new_edge(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    old = topology.receipt(1)
    topology.migrate(expected_generation=1, add_states=["done"], add_transitions=[("finish", "ready", "done")])
    assert topology.verify_receipt(old)
    assert not topology.allows("finish", "ready", "done", generation=old["generation"])
    assert journal.history("item-1") == [] and outbox.visible("item-1") == []


@pytest.mark.composition
def test_c13_process_owner_transfer_stales_persisted_helper(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    attachments.claim_owner("item-1", "process-b", expected_attachment_generation=1)
    reopened = api("AttachmentStore")(attachments.path)
    with pytest.raises(api("StaleHelperError")):
        reopened.validate_helper(helper)
    assert reopened.current("item-1")["owner_generation"] == 2


@pytest.mark.composition
def test_c14_owner_transfer_during_preparation_blocks_replay_commit(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    prepared = journal.prepare("item-1", "approve", "draft", "ready", expected_revision=0, idempotency_key="prepared-owner")
    attachments.claim_owner("item-1", "process-b", expected_attachment_generation=1)
    with pytest.raises(api("StaleHelperError")):
        attachments.validate_helper(helper)
    assert prepared in journal.pending() and outbox.visible("item-1") == []


@pytest.mark.composition
def test_c15_detach_during_active_lease_leaves_no_commit_or_publication(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    coordinator.schedule("item-1", "approve", helper_token=helper, due_at=1, idempotency_key="detach-race")
    attachments.detach("item-1", expected_attachment_generation=1)
    with pytest.raises(api("StaleHelperError")):
        coordinator.run_due("worker", now=1, lease_seconds=2)
    assert journal.history("item-1") == [] and outbox.visible("item-1") == []


@pytest.mark.composition
def test_c16_rebind_generation_is_captured_by_publication(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    migration = topology.migrate(expected_generation=1, aliases={"waiting": "draft"})
    detached = attachments.detach("item-1", expected_attachment_generation=1)
    rebound = attachments.rebind("item-1", "machine", topology_generation=2, state="waiting", expected_attachment_generation=detached["attachment_generation"])
    attachments.claim_owner("item-1", "process-b", expected_attachment_generation=rebound["attachment_generation"])
    current = attachments.helper_token("item-1", "approve")
    result = coordinator.transition("item-1", "approve", helper_token=current, idempotency_key="rebound", expected_revision=0)
    publication = outbox.get(result["publication"]["publication_id"])
    assert (publication["attachment_generation"], publication["owner_generation"], publication["topology_digest"]) == (3, 1, migration["digest"])


@pytest.mark.composition
def test_c17_committed_transition_is_invisible_until_publication_ack(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    result = coordinator.transition("item-1", "approve", helper_token=helper, idempotency_key="visibility", expected_revision=0)
    assert journal.history("item-1") and outbox.visible("item-1") == []
    coordinator.publish_due("publisher", now=0, lease_seconds=3, external_receipt={"offset": 17})
    visible = outbox.visible("item-1")
    assert len(visible) == 1 and visible[0]["journal_id"] == result["journal_receipt"]["journal_id"]


@pytest.mark.composition
def test_c18_uncommitted_or_aborted_work_cannot_be_published(tmp_path, api):
    journal, scheduler, topology, attachments, outbox = durable(tmp_path, api)
    top = topology.create(["one", "two"], [("next", "one", "two")])
    attached = attachments.attach("entity-18", "machine", topology_generation=1, state="one")
    prepared = journal.prepare("entity-18", "next", "one", "two", expected_revision=0, idempotency_key="never-visible")
    with pytest.raises(api("PublicationError")):
        outbox.stage(prepared, top, attached, idempotency_key="never-visible")
    journal.abort(prepared["prepare_id"], reason="cancelled")
    assert outbox.visible("entity-18") == []


@pytest.mark.composition
def test_c19_publication_lease_expiry_fences_stale_ack(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    coordinator.transition("item-1", "approve", helper_token=helper, idempotency_key="lease-publication", expected_revision=0)
    old = outbox.claim("publisher-a", now=0, lease_seconds=2)
    current = outbox.claim("publisher-b", now=3, lease_seconds=2)
    with pytest.raises(api("LeaseError")):
        outbox.ack(old["publication_id"], old["lease_token"], {"offset": 1})
    outbox.ack(current["publication_id"], current["lease_token"], {"offset": 2})
    assert outbox.visible("item-1")[0]["external_receipt"]["offset"] == 2


@pytest.mark.composition
def test_c20_duplicate_commit_and_reopen_stage_one_publication(tmp_path, api):
    journal, scheduler, topology, attachments, outbox, coordinator, helper = bound(tmp_path, api)
    first = coordinator.transition("item-1", "approve", helper_token=helper, idempotency_key="once", expected_revision=0)
    reopened = api("PublicationOutbox")(outbox.path)
    duplicate = reopened.stage(first["journal_receipt"], topology.receipt(1), attachments.current("item-1"), idempotency_key="once")
    assert duplicate["publication_id"] == first["publication"]["publication_id"]
    lease = reopened.claim("publisher", now=0, lease_seconds=2)
    reopened.ack(lease["publication_id"], lease["lease_token"], {"offset": 20})
    assert len(reopened.visible("item-1")) == 1 and len(journal.history("item-1")) == 1
