from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from jupyter_client import AsyncKernelManager, KernelManager
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
from jupyter_client.provisioning import KernelProvisionerFactory, LocalProvisioner
from jupyter_client.session import Session

from assets.public_provisioner import PublicFixtureProvisioner
from helpers import EntryPoints, FakeEntryPoint, RecordingProvisioner, assert_carries, connection_info, transcript_message, wire, write_kernel_spec


def test_c01_connection_commit_persists_and_reload_carries_file_lineage(tmp_path):
    manager = KernelManager(connection_file=str(tmp_path / "connection.json"))
    committed = manager.refresh_connection_info(connection_info(101))
    manager.write_connection_file()
    disk = json.loads(Path(manager.connection_file).read_text(encoding="utf-8"))
    assert disk["receipt"]["digest"] == committed.digest
    restored = KernelManager(connection_file=manager.connection_file); restored.load_connection_file()
    reloaded = restored.latest_connection_receipt
    assert committed.digest in reloaded.dependencies
    assert restored.get_connection_info()["generation"] == committed.sequence


def test_c02_refresh_and_clients_carry_validated_old_and_new_receipts():
    manager = KernelManager()
    first = manager.refresh_connection_info(connection_info(111)); old = manager.client(connection_receipt=first)
    second = manager.refresh_connection_info(connection_info(112)); new = manager.client(connection_receipt=second)
    assert old.connection_receipt == first and new.connection_receipt == second
    assert old.session.key == b"key-111" and new.session.key == b"key-112"
    assert old.session.connection_receipt.digest == first.digest
    assert new.session.connection_receipt.digest == second.digest


def test_c03_rotation_clients_and_wires_preserve_receipt_parentage():
    manager = KernelManager(); first = manager.refresh_connection_info(connection_info(121))
    old = manager.client(connection_receipt=first)
    rotated = manager.rotate_connection_key(b"rotated-121"); new = manager.client(connection_receipt=rotated)
    _, _, old_wire = wire(old.session, content={"credential": "old"})
    _, _, new_wire = wire(new.session, content={"credential": "new"})
    assert old.session.deserialize(old_wire)["content"] == {"credential": "old"}
    assert new.session.deserialize(new_wire)["content"] == {"credential": "new"}
    with pytest.raises(ValueError):
        new.session.deserialize(old_wire)
    assert rotated.parent_digest == first.digest
    assert old.connection_receipt.digest != new.connection_receipt.digest


def test_c04_foreign_receipt_rejection_preserves_prior_client_snapshot():
    from jupyter_client.receipts import ReceiptValidationError
    manager = KernelManager(); other = KernelManager()
    own = manager.refresh_connection_info(connection_info(131)); retained = manager.client(connection_receipt=own)
    foreign = other.refresh_connection_info(connection_info(132))
    with pytest.raises(ReceiptValidationError):
        manager.client(connection_receipt=foreign)
    assert retained.connection_receipt == own and retained.session.key == b"key-131"
    assert manager.latest_connection_receipt == own


def test_c05_signed_delivery_replay_domains_expose_validated_receipts():
    signer = Session(key=b"domain-saffron")
    shell = signer.clone(replay_domain={"kernel": "kd", "session": signer.session, "channel": "shell", "generation": 9})
    iopub = signer.clone(replay_domain={"kernel": "kd", "session": signer.session, "channel": "iopub", "generation": 9})
    _, _, core = wire(signer, content={"ordinal": 211})
    first = shell.deserialize(core, channel="shell", request_generation=9)
    duplicate = shell.deserialize(core, channel="shell", request_generation=9)
    sibling = iopub.deserialize(core, channel="iopub", request_generation=9)
    assert shell.validate_delivery_receipt(first["delivery_receipt"], first)
    assert duplicate["delivery_receipt"] == first["delivery_receipt"]
    assert iopub.validate_delivery_receipt(sibling["delivery_receipt"], sibling)
    assert sibling["delivery_receipt"].digest != first["delivery_receipt"].digest


def test_c06_invalid_wire_cannot_reserve_receipt_before_valid_retry():
    signer = Session(key=b"domain-cedar"); receiver = signer.clone(replay_domain={"kernel": "kc"})
    _, _, core = wire(signer, content={"ordinal": 223})
    bad = list(core); bad[0] = b"1" * len(bytes(bad[0]))
    with pytest.raises(ValueError):
        receiver.deserialize(bad, channel="control", request_generation=4)
    assert receiver.delivery_receipts() == ()
    accepted = receiver.deserialize(core, channel="control", request_generation=4)
    assert receiver.validate_delivery_receipt(accepted["delivery_receipt"], accepted)
    assert accepted["duplicate"] is False


def test_c07_delivery_receipts_flow_into_pending_and_attachment_receipts():
    from jupyter_client.transcript import CausalTranscript
    signer = Session(key=b"transcript-lake"); receiver = signer.clone(replay_domain={"kernel": "kernel-violet", "session": signer.session, "generation": 7})
    request, _, request_wire = wire(signer, "execute_request", content={"code": "x=1"})
    reply, _, reply_wire = wire(signer, "execute_reply", content={"status": "ok"}, parent=request)
    transcript = CausalTranscript("kernel-violet", signer.session, 7)
    decoded_reply = receiver.deserialize(reply_wire, channel="shell", request_generation=7); decoded_reply.update({"kernel_id": "kernel-violet", "connection_generation": 7})
    pending = transcript.accept_delivery(receiver, "shell", decoded_reply)
    decoded_request = receiver.deserialize(request_wire, channel="shell", request_generation=7); decoded_request.update({"kernel_id": "kernel-violet", "connection_generation": 7})
    attached = transcript.accept_delivery(receiver, "shell", decoded_request)
    assert_carries(pending, decoded_reply["delivery_receipt"])
    assert_carries(attached, decoded_reply["delivery_receipt"], decoded_request["delivery_receipt"])
    assert transcript.snapshot()["unattached"] == [] and reply["msg_id"] != request["msg_id"]


def test_c08_validated_conflict_records_failure_and_retains_receipt_lineage():
    from jupyter_client.transcript import CausalTranscript, TranscriptConflict
    signer = Session(key=b"transcript-moss"); receiver = signer.clone(replay_domain={"kernel": "kernel-violet", "session": signer.session, "generation": 8})
    first_msg, _, first_wire = wire(signer, "execute_request", content={"code": "alpha"})
    transcript = CausalTranscript("kernel-violet", signer.session, 8)
    first = receiver.deserialize(first_wire, channel="shell", request_generation=8); first.update({"kernel_id": "kernel-violet", "connection_generation": 8})
    accepted = transcript.accept_delivery(receiver, "shell", first)
    conflict = dict(first); conflict["content"] = {"code": "beta"}; conflict["delivery_receipt"] = first["delivery_receipt"]
    with pytest.raises(TranscriptConflict):
        transcript.record_delivery("shell", conflict, first["delivery_receipt"])
    snapshot = transcript.snapshot()
    assert snapshot["receipts"] == (accepted,) and len(snapshot["failures"]) == 1
    assert snapshot["requests"][0]["message"]["msg_id"] == first_msg["msg_id"]


def test_c09_replay_clear_does_not_rewrite_accepted_transcript_receipt():
    from jupyter_client.transcript import CausalTranscript
    signer = Session(key=b"clear-umber"); receiver = signer.clone(replay_domain={"kernel": "clear-k", "session": signer.session, "generation": 3})
    message, _, core = wire(signer, "execute_request", content={"ordinal": 229})
    decoded = receiver.deserialize(core, channel="shell", request_generation=3); decoded.update({"kernel_id": "clear-k", "connection_generation": 3})
    transcript = CausalTranscript("clear-k", signer.session, 3)
    accepted = transcript.accept_delivery(receiver, "shell", decoded)
    assert receiver.clear_replay({"channel": "shell", "generation": 3}) == 1
    assert receiver.delivery_receipts() == ()
    assert transcript.snapshot()["receipts"] == (accepted,)
    assert transcript.snapshot()["requests"][0]["message"]["msg_id"] == message["msg_id"]


def test_c10_lifecycle_start_carries_connection_and_participant_lease():
    manager = KernelManager(); provisioner = RecordingProvisioner("provisioner-slate")
    connection = manager.refresh_connection_info(connection_info(141))
    running = manager.lifecycle_operation("start", provisioner, connection_receipt=connection, process_status={"pid": 8141}, owner="owner-a")
    assert running["state"] == "running"
    assert_carries(running["receipt"], connection, running["lease_receipt"])
    assert manager.latest_lifecycle_receipt == running["receipt"]


def test_c11_rotation_failed_restart_and_retry_keep_two_parent_chains():
    manager = KernelManager(); provisioner = RecordingProvisioner("provisioner-copper")
    first = manager.refresh_connection_info(connection_info(151))
    started = manager.lifecycle_operation("start", provisioner, connection_receipt=first, process_status={"pid": 8151}, owner="old")
    rotated = manager.rotate_connection_key(b"key-rotated-151")
    before = manager.lifecycle_snapshot()
    with pytest.raises(RuntimeError):
        manager.lifecycle_operation("restart", provisioner, connection_receipt=rotated, process_status={"pid": 8152}, owner="bad", fail_at="commit")
    assert manager.lifecycle_snapshot() == before
    restarted = manager.lifecycle_operation("restart", provisioner, connection_receipt=rotated, process_status={"pid": 8153}, owner="new")
    assert restarted["receipt"].parent_digest == started["receipt"].digest
    assert_carries(restarted["receipt"], rotated, restarted["lease_receipt"])
    assert manager.lifecycle_failures()[-1]["operation"] == "restart"


def test_c12_async_lifecycle_results_form_serialized_parent_chain():
    async def scenario():
        manager = AsyncKernelManager(); provisioner = RecordingProvisioner("provisioner-async")
        first = manager.refresh_connection_info(connection_info(161))
        start = await manager.async_lifecycle_operation("start", provisioner, connection_receipt=first, process_status={"pid": 9161}, owner="one")
        results = await asyncio.gather(
            manager.async_lifecycle_operation("interrupt", provisioner),
            manager.async_lifecycle_operation("shutdown", provisioner),
        )
        return manager, start, results
    manager, start, results = asyncio.run(scenario())
    assert results[0]["receipt"].parent_digest == start["receipt"].digest
    assert results[1]["receipt"].parent_digest == results[0]["receipt"].digest
    assert manager.lifecycle_state == "stopped"


def test_c13_catalog_join_carries_kernel_provider_and_native_spec_receipts(tmp_path, monkeypatch):
    root = tmp_path / "kernels"; root.mkdir(); write_kernel_spec(root, "joined", "Joined", provisioner="public-fixture")
    entries = EntryPoints([FakeEntryPoint("public-fixture", "join.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    kernels = KernelSpecManager(kernel_dirs=[str(root)], ensure_native_kernel=False); providers = KernelProvisionerFactory()
    kc = kernels.refresh_catalog(); pc = providers.refresh_catalog()
    selected = kernels.select_kernel("joined", providers, kernel_catalog_generation=kc["generation"], provisioner_catalog_generation=pc["generation"], kernel_id="joined-one")
    assert_carries(selected["receipt"], kc["receipt"], pc["receipt"], selected["provisioner"].provider_receipt)
    assert selected["kernel_spec"].display_name == "Joined"


def test_c14_retained_catalog_receipts_survive_independent_current_changes(tmp_path, monkeypatch):
    first = tmp_path / "first"; second = tmp_path / "second"; first.mkdir(); second.mkdir()
    write_kernel_spec(first, "shared", "First", provisioner="public-fixture"); write_kernel_spec(second, "shared", "Second", provisioner="public-fixture")
    entries = EntryPoints([FakeEntryPoint("public-fixture", "retain.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    kernels = KernelSpecManager(kernel_dirs=[str(first), str(second)], ensure_native_kernel=False); providers = KernelProvisionerFactory()
    k1 = kernels.refresh_catalog(); p1 = providers.refresh_catalog()
    entries[:] = [FakeEntryPoint("public-fixture", "retain.two:PublicFixtureProvisioner", PublicFixtureProvisioner)]; kernels.kernel_dirs = [str(second), str(first)]
    k2 = kernels.refresh_catalog(); p2 = providers.refresh_catalog()
    retained = kernels.select_kernel("shared", providers, kernel_catalog_generation=k1["generation"], provisioner_catalog_generation=p1["generation"])
    current = kernels.select_kernel("shared", providers, kernel_catalog_generation=k2["generation"], provisioner_catalog_generation=p2["generation"])
    assert retained["kernel_spec"].display_name == "First" and current["kernel_spec"].display_name == "Second"
    assert_carries(retained["receipt"], k1["receipt"], p1["receipt"])
    assert_carries(current["receipt"], k2["receipt"], p2["receipt"])


def test_c15_catalog_selection_connection_and_lifecycle_receipts_close(tmp_path, monkeypatch):
    root = tmp_path / "kernels"; root.mkdir(); write_kernel_spec(root, "launchable", "Launchable", provisioner="public-fixture")
    entries = EntryPoints([FakeEntryPoint("public-fixture", "launch.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    kernels = KernelSpecManager(kernel_dirs=[str(root)], ensure_native_kernel=False); providers = KernelProvisionerFactory()
    kc = kernels.refresh_catalog(); pc = providers.refresh_catalog()
    selection = kernels.select_kernel("launchable", providers, kernel_catalog_generation=kc["generation"], provisioner_catalog_generation=pc["generation"], kernel_id="launch-one")
    manager = KernelManager(); connection = manager.refresh_connection_info(connection_info(171))
    running = manager.lifecycle_from_selection(selection, providers, connection_receipt=connection, process_status={"pid": 9171}, owner="selected-owner")
    assert running["state"] == "running"
    assert_carries(running["receipt"], selection["receipt"], connection, running["lease_receipt"])


def test_c16_native_connection_file_manager_client_round_trip(tmp_path):
    from jupyter_client.blocking.client import BlockingKernelClient
    from jupyter_client.connect import write_connection_file
    path = tmp_path / "native.json"; _, written = write_connection_file(str(path), key=b"roundtrip-native")
    client = BlockingKernelClient(connection_file=str(path)); client.load_connection_file()
    assert client.session.key == b"roundtrip-native"
    assert all(getattr(client, name) == written[name] for name in ("shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))


def test_c17_native_routed_multipart_repeat_split_and_verify():
    signer = Session(key=b"multipart-native")
    message, identities, core = wire(signer, "comm_msg", content={"value": "native"}, ident=[b"a", b"b"], buffers=[memoryview(b"one"), memoryview(b"two")])
    routed = signer.serialize(message, ident=identities); routed.extend([memoryview(b"one"), memoryview(b"two")])
    ids_one, core_one = signer.feed_identities(routed); ids_two, core_two = signer.feed_identities(routed)
    assert ids_one == ids_two == identities
    assert Session(key=b"multipart-native").deserialize(core_one)["content"] == Session(key=b"multipart-native").deserialize(core_two)["content"]


def test_c18_native_spec_and_two_provisioner_payloads_do_not_mix(tmp_path):
    resource = write_kernel_spec(tmp_path, "native-spec", "Native Spec")
    spec = KernelSpec.from_resource_dir(str(resource)); assert json.loads(spec.to_json()) == spec.to_dict()
    left = LocalProvisioner(kernel_id="left", kernel_spec=spec, parent=None); right = PublicFixtureProvisioner(kernel_id="right", kernel_spec=spec, parent=None)
    left.connection_info = {"owner": "left"}; right.connection_info = {"owner": "right"}
    left_receiver = LocalProvisioner(kernel_id="lr", kernel_spec=spec, parent=None); right_receiver = PublicFixtureProvisioner(kernel_id="rr", kernel_spec=spec, parent=None)
    asyncio.run(left_receiver.load_provisioner_info(asyncio.run(left.get_provisioner_info())))
    asyncio.run(right_receiver.load_provisioner_info(asyncio.run(right.get_provisioner_info())))
    assert left_receiver.connection_info == {"owner": "left"}
    assert right_receiver.connection_info == {"owner": "right"}
