from __future__ import annotations

import json
from pathlib import Path

import pytest

from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from jupyter_client.provisioning import KernelProvisionerFactory
from jupyter_client.session import Session

from assets.public_provisioner import PublicFixtureProvisioner
from helpers import EntryPoints, FakeEntryPoint, RecordingProvisioner, assert_carries, connection_info, wire, write_kernel_spec


def test_e01_signed_replay_transcript_terminal_chain_rejects_invalid_publication():
    from jupyter_client.receipts import ReceiptValidationError
    from jupyter_client.transcript import CausalTranscript
    signer = Session(key=b"system-transcript")
    receiver = signer.clone(replay_domain={"kernel": "kernel-system", "session": signer.session, "generation": 12})
    request, _, request_wire = wire(signer, "execute_request", content={"code": "value=307"})
    reply, _, reply_wire = wire(signer, "execute_reply", content={"status": "ok"}, parent=request)
    idle, _, idle_wire = wire(signer, "status", content={"execution_state": "idle"}, parent=request)
    transcript = CausalTranscript("kernel-system", signer.session, 12)
    accepted = []
    for channel, encoded in (("shell", reply_wire), ("iopub", idle_wire), ("shell", request_wire)):
        decoded = receiver.deserialize(encoded, channel=channel, request_generation=12)
        decoded.update({"kernel_id": "kernel-system", "connection_generation": 12})
        receipt = transcript.accept_delivery(receiver, channel, decoded)
        assert_carries(receipt, decoded["delivery_receipt"])
        accepted.append(receipt)
    before = transcript.snapshot()
    forged = dict(receiver.deserialize(reply_wire, channel="shell", request_generation=12))
    forged.update({"kernel_id": "kernel-system", "connection_generation": 12})
    forged["delivery_receipt"] = accepted[0]
    with pytest.raises(ReceiptValidationError):
        transcript.accept_delivery(receiver, "shell", forged)
    assert transcript.snapshot() == before
    assert before["terminal_status"] == (request["msg_id"],)


def test_e02_catalog_selection_connection_and_lifecycle_propagate_stale_provider(tmp_path, monkeypatch):
    from jupyter_client.receipts import ReceiptValidationError
    root = tmp_path / "kernels"; root.mkdir(); write_kernel_spec(root, "system", "System One", provisioner="public-fixture")
    entries = EntryPoints([FakeEntryPoint("public-fixture", "system.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    kernels = KernelSpecManager(kernel_dirs=[str(root)], ensure_native_kernel=False); providers = KernelProvisionerFactory()
    kc = kernels.refresh_catalog(); pc = providers.refresh_catalog()
    selection = kernels.select_kernel("system", providers, kernel_catalog_generation=kc["generation"], provisioner_catalog_generation=pc["generation"], kernel_id="system-one")
    manager = KernelManager(); connection = manager.refresh_connection_info(connection_info(201))
    running = manager.lifecycle_from_selection(selection, providers, connection_receipt=connection, process_status={"pid": 10200})
    assert_carries(running["receipt"], selection["receipt"], connection, running["lease_receipt"])
    entries[:] = [FakeEntryPoint("public-fixture", "system.two:PublicFixtureProvisioner", PublicFixtureProvisioner)]; providers.refresh_catalog()
    before = manager.lifecycle_snapshot()
    providers.evict_catalog(pc["generation"])
    with pytest.raises(ReceiptValidationError):
        manager.lifecycle_from_selection(selection, providers, connection_receipt=connection, process_status={"pid": 10201})
    assert manager.lifecycle_snapshot() == before


def test_e03_durable_selection_lifecycle_rotation_rollback_retry_and_shutdown(tmp_path, monkeypatch):
    root = tmp_path / "kernels"; root.mkdir(); write_kernel_spec(root, "durable", "Durable", provisioner="public-fixture")
    entries = EntryPoints([FakeEntryPoint("public-fixture", "durable.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    kernels = KernelSpecManager(kernel_dirs=[str(root)], ensure_native_kernel=False); providers = KernelProvisionerFactory()
    kc = kernels.refresh_catalog(); pc = providers.refresh_catalog()
    selection = kernels.select_kernel("durable", providers, kernel_catalog_generation=kc["generation"], provisioner_catalog_generation=pc["generation"], kernel_id="durable-one")
    manager = KernelManager(connection_file=str(tmp_path / "durable.json"))
    connection = manager.refresh_connection_info(connection_info(211))
    started = manager.lifecycle_from_selection(selection, providers, connection_receipt=connection, process_status={"pid": 10211}, owner="owner-a")
    manager.write_connection_file(); persisted = json.loads(Path(manager.connection_file).read_text(encoding="utf-8"))
    rotated = manager.rotate_connection_key(b"durable-rotated")
    provisioner = selection["provisioner"]
    with pytest.raises(RuntimeError):
        manager.lifecycle_operation("restart", provisioner, connection_receipt=rotated, process_status={"pid": 10212}, owner="bad", fail_at="commit")
    restarted = manager.lifecycle_operation("restart", provisioner, connection_receipt=rotated, process_status={"pid": 10213}, owner="owner-c")
    stopped = manager.lifecycle_operation("shutdown", provisioner)
    assert persisted["receipt"]["digest"] == connection.digest
    assert restarted["receipt"].parent_digest == started["receipt"].digest
    assert_carries(restarted["receipt"], rotated, restarted["lease_receipt"])
    assert stopped["state"] == "stopped" and stopped["receipt"].parent_digest == restarted["receipt"].digest


def test_e04_foreign_connection_and_delivery_fail_before_independent_resource_mutation(tmp_path, monkeypatch):
    from jupyter_client.receipts import ReceiptValidationError
    root = tmp_path / "kernels"; root.mkdir(); write_kernel_spec(root, "guarded", "Guarded", provisioner="public-fixture")
    entries = EntryPoints([FakeEntryPoint("public-fixture", "guard.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    kernels = KernelSpecManager(kernel_dirs=[str(root)], ensure_native_kernel=False); providers = KernelProvisionerFactory()
    kc = kernels.refresh_catalog(); pc = providers.refresh_catalog()
    selection = kernels.select_kernel("guarded", providers, kernel_catalog_generation=kc["generation"], provisioner_catalog_generation=pc["generation"])
    owner = KernelManager(); foreign = KernelManager()
    own_receipt = owner.refresh_connection_info(connection_info(221)); foreign_receipt = foreign.refresh_connection_info(connection_info(222))
    running = owner.lifecycle_from_selection(selection, providers, connection_receipt=own_receipt, process_status={"pid": 10220})
    assert_carries(running["receipt"], selection["receipt"], own_receipt, running["lease_receipt"])
    before_lifecycle = owner.lifecycle_snapshot()
    with pytest.raises(ReceiptValidationError):
        owner.lifecycle_from_selection(selection, providers, connection_receipt=foreign_receipt, process_status={"pid": 10221})
    assert owner.lifecycle_snapshot() == before_lifecycle and owner.latest_connection_receipt == own_receipt
    from jupyter_client.transcript import CausalTranscript
    signer = Session(key=b"guard-delivery"); receiver = signer.clone(replay_domain={"kernel": "guard-k", "session": signer.session, "generation": 1})
    request, _, core = wire(signer, "execute_request", content={"code": "guard"})
    decoded = receiver.deserialize(core, channel="shell", request_generation=1); decoded.update({"kernel_id": "guard-k", "connection_generation": 1})
    transcript = CausalTranscript("guard-k", signer.session, 1)
    accepted = transcript.accept_delivery(receiver, "shell", decoded)
    assert_carries(accepted, decoded["delivery_receipt"])
    before_transcript = transcript.snapshot()
    forged = dict(decoded); forged["msg_id"] = "forged-guard"; forged["header"] = dict(decoded["header"]) | {"msg_id": "forged-guard"}
    forged["delivery_receipt"] = own_receipt
    with pytest.raises(ReceiptValidationError):
        transcript.accept_delivery(receiver, "shell", forged)
    assert transcript.snapshot() == before_transcript and request["msg_id"]
