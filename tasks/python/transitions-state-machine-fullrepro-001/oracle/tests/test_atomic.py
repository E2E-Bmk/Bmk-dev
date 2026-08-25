from __future__ import annotations

import pytest

import transitions


class Model:
    pass


@pytest.mark.atomic
def test_a01_package_exports_core_vocabulary():
    assert all(hasattr(transitions, name) for name in ("Machine", "State", "MachineError"))
    assert isinstance(transitions.__version__, str) and transitions.__version__


@pytest.mark.atomic
def test_a02_state_declaration_is_inspectable():
    state = transitions.State("queued", on_enter="notice", final=True)
    assert state.name == state.value == "queued"
    assert state.on_enter == ["notice"] and state.final is True


@pytest.mark.atomic
def test_a03_basic_model_binding_and_transition():
    model = Model()
    machine = transitions.Machine(model=model, states=["cold", "warm"], initial="cold", auto_transitions=False)
    machine.add_transition("heat", "cold", "warm")
    assert model.heat() is True
    assert model.state == "warm" and model.is_warm()


@pytest.mark.atomic
def test_a04_conditions_block_without_commit():
    model = Model()
    machine = transitions.Machine(model=model, states=["off", "on"], initial="off", auto_transitions=False)
    machine.add_transition("enable", "off", "on", conditions=lambda: False)
    assert model.enable() is False and model.state == "off"


@pytest.mark.atomic
def test_a05_internal_and_reflexive_modes_differ():
    trace = []
    model = Model()
    state = transitions.State("steady", on_exit=lambda: trace.append("exit"), on_enter=lambda: trace.append("enter"))
    machine = transitions.Machine(model=model, states=[state], initial="steady", auto_transitions=False)
    machine.add_transition("inspect", "steady", None, after=lambda: trace.append("after"))
    machine.add_transition("renew", "steady", "=")
    assert model.inspect() and trace == ["after"]
    assert model.renew() and trace == ["after", "exit", "enter"]


@pytest.mark.atomic
def test_a06_transition_query_tracks_removal():
    machine = transitions.Machine(states=["ink", "dry"], initial="ink", auto_transitions=False)
    machine.add_transition("set", "ink", "dry")
    assert [(edge.source, edge.dest) for edge in machine.get_transitions("set")] == [("ink", "dry")]
    machine.remove_transition("set", source="ink", dest="dry")
    assert machine.get_transitions("set") == []


@pytest.mark.atomic
def test_a07_models_keep_independent_state():
    left, right = Model(), Model()
    machine = transitions.Machine(model=[left, right], states=["idle", "busy"], initial="idle", auto_transitions=False)
    machine.add_transition("start", "idle", "busy")
    assert left.start() and left.state == "busy" and right.state == "idle"


@pytest.mark.atomic
def test_a08_event_data_is_fresh_per_invocation():
    seen = []
    model = Model()
    machine = transitions.Machine(model=model, states=["x"], initial="x", auto_transitions=False, send_event=True)
    machine.add_transition("touch", "x", "=", before=lambda event: seen.append(event))
    assert model.touch() and model.touch()
    assert len(seen) == 2 and seen[0] is not seen[1]


@pytest.mark.atomic
def test_a09_journal_enforces_expected_revision_and_idempotency(tmp_path, api):
    Journal, Conflict = api("TransitionJournal"), api("RevisionConflict")
    journal = Journal(tmp_path / "journal.log")
    first = journal.prepare("ticket-17", "open", "new", "ready", expected_revision=0, idempotency_key="k-one")
    receipt = journal.commit(first["prepare_id"])
    assert receipt["revision"] == 1 and receipt["status"] == "committed"
    assert journal.prepare("ticket-17", "open", "new", "ready", expected_revision=0, idempotency_key="k-one") == receipt
    with pytest.raises(Conflict):
        journal.prepare("ticket-17", "close", "ready", "done", expected_revision=0, idempotency_key="k-two")


@pytest.mark.atomic
def test_a10_scheduler_fences_expired_lease(tmp_path, api):
    Scheduler, LeaseError = api("LeaseScheduler"), api("LeaseError")
    scheduler = Scheduler(tmp_path / "work.json")
    scheduler.schedule("job-8", "publish", due_at=12, idempotency_key="deliver-8")
    delivery = scheduler.claim("worker-a", now=12, lease_seconds=2)
    current = scheduler.claim("worker-b", now=15, lease_seconds=3)
    with pytest.raises(LeaseError):
        scheduler.ack(delivery["delivery_id"], delivery["lease_token"], {"revision": 1})
    assert current["attempt"] == 2


@pytest.mark.atomic
def test_a11_topology_migration_checks_generation_and_receipt(tmp_path, api):
    Registry, GenerationConflict = api("TopologyRegistry"), api("GenerationConflict")
    registry = Registry(tmp_path / "topology.json")
    created = registry.create(["draft", "ready"], [("approve", "draft", "ready")])
    assert created["generation"] == 1
    with pytest.raises(GenerationConflict):
        registry.migrate(expected_generation=0, add_states=["done"])


@pytest.mark.atomic
def test_a12_attachment_owner_generation_rejects_stale_helper(tmp_path, api):
    Store, StaleHelperError = api("AttachmentStore"), api("StaleHelperError")
    store = Store(tmp_path / "attachments.json")
    attached = store.attach("doc-4", "machine-blue", topology_generation=1, state="draft")
    store.claim_owner("doc-4", "process-a", expected_attachment_generation=attached["attachment_generation"])
    old = store.helper_token("doc-4", "approve")
    store.claim_owner("doc-4", "process-b", expected_attachment_generation=attached["attachment_generation"])
    with pytest.raises(StaleHelperError):
        store.validate_helper(old)


@pytest.mark.atomic
def test_a13_outbox_requires_commit_and_ack_for_visibility(tmp_path, api):
    Outbox, PublicationError = api("PublicationOutbox"), api("PublicationError")
    outbox = Outbox(tmp_path / "publications.json")
    topology = {"generation": 2, "digest": "topology-digest"}
    attachment = {"attachment_generation": 3, "owner_generation": 4}
    with pytest.raises(PublicationError):
        outbox.stage({"status": "prepared", "entity_id": "card-2"}, topology, attachment, idempotency_key="p-1")
    staged = outbox.stage({"status": "committed", "entity_id": "card-2", "journal_id": "j-1", "revision": 1}, topology, attachment, idempotency_key="p-1")
    assert outbox.visible("card-2") == []
    lease = outbox.claim("publisher", now=0, lease_seconds=2)
    outbox.ack(staged["publication_id"], lease["lease_token"], {"offset": 9})
    assert outbox.visible("card-2")[0]["external_receipt"] == {"offset": 9}
