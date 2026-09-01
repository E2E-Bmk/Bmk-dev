from __future__ import annotations

import asyncio
import json

import pytest

from jupyter_client import KernelManager
from jupyter_client.connect import write_connection_file
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
from jupyter_client.provisioning import KernelProvisionerFactory, LocalProvisioner
from jupyter_client.session import Session

from assets.public_provisioner import PublicFixtureProvisioner
from helpers import EntryPoints, FakeEntryPoint, RecordingProvisioner, connection_info, transcript_message, wire, write_kernel_spec


def sample_delivery(message, sequence=1):
    from jupyter_client.receipts import TransitionReceipt
    return TransitionReceipt.create(
        surface="delivery",
        owner="sample-session",
        sequence=sequence,
        facts={"message": message, "domain": {"channel": "shell", "generation": 1}},
    )


def test_a01_complete_refresh_commits_one_owner_validated_receipt():
    manager = KernelManager()
    receipt = manager.refresh_connection_info(connection_info(11))
    assert receipt.surface == "connection" and receipt.sequence == 1
    assert manager.latest_connection_receipt == receipt
    assert manager.validate_connection_receipt(receipt)
    before = (manager.get_connection_info(), manager.connection_receipts())
    with pytest.raises(ValueError):
        manager.refresh_connection_info({"transport": "tcp", "generation": 9})
    assert (manager.get_connection_info(), manager.connection_receipts()) == before


def test_a02_client_requires_owner_journal_receipt_and_snapshots_it():
    from jupyter_client.receipts import ReceiptValidationError
    owner = KernelManager(); foreign = KernelManager()
    own_receipt = owner.refresh_connection_info(connection_info(21))
    foreign_receipt = foreign.refresh_connection_info(connection_info(22))
    client = owner.client(connection_receipt=own_receipt)
    assert client.connection_receipt == own_receipt
    assert client.connection_generation == own_receipt.sequence == 1
    assert client.session.key == b"key-21"
    with pytest.raises(ReceiptValidationError):
        owner.client(connection_receipt=foreign_receipt)


def test_a03_rotation_commits_child_receipt_without_endpoint_drift():
    manager = KernelManager()
    first = manager.refresh_connection_info(connection_info(31))
    before_ports = tuple(manager.get_connection_info()[name] for name in ("shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))
    rotated = manager.rotate_connection_key(b"rotated-citrine", "hmac-sha512")
    after_ports = tuple(manager.get_connection_info()[name] for name in ("shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))
    assert rotated.parent_digest == first.digest
    assert rotated.sequence == 2 and manager.session.key == b"rotated-citrine"
    assert before_ports == after_ports


def test_a04_authentication_precedes_owner_validated_delivery_receipt():
    signer = Session(key=b"delivery-amber")
    receiver = signer.clone(replay_domain={"kernel": "ka", "session": signer.session, "channel": "shell", "generation": 4})
    message, _, core = wire(signer, content={"ordinal": 41})
    accepted = receiver.deserialize(core, channel="shell", request_generation=4)
    receipt = accepted["delivery_receipt"]
    assert receipt.surface == "delivery"
    assert receiver.validate_delivery_receipt(receipt, accepted)
    bad = list(core); bad[0] = b"0" * len(bytes(bad[0]))
    before = receiver.delivery_receipts()
    with pytest.raises(ValueError):
        receiver.deserialize(bad, channel="shell", request_generation=4)
    assert receiver.delivery_receipts() == before
    assert accepted["msg_id"] == message["msg_id"]


def test_a05_duplicate_reuses_receipt_while_sibling_domain_is_independent():
    signer = Session(key=b"delivery-birch")
    shell = signer.clone(replay_domain={"kernel": "kb", "session": signer.session, "channel": "shell", "generation": 5})
    control = signer.clone(replay_domain={"kernel": "kb", "session": signer.session, "channel": "control", "generation": 5})
    _, _, core = wire(signer, content={"ordinal": 53})
    first = shell.deserialize(core, channel="shell", request_generation=5)
    duplicate = shell.deserialize(core, channel="shell", request_generation=5)
    sibling = control.deserialize(core, channel="control", request_generation=5)
    assert duplicate["duplicate"] is True
    assert duplicate["delivery_receipt"] == first["delivery_receipt"]
    assert sibling["delivery_receipt"].digest != first["delivery_receipt"].digest


def test_a06_transcript_pending_child_commits_attachment_lineage():
    from jupyter_client.transcript import CausalTranscript
    transcript = CausalTranscript("kernel-violet", "session-lake", 1)
    child = transcript_message("reply-61", "execute_reply", "session-lake", parent_id="request-61")
    parent = transcript_message("request-61", "execute_request", "session-lake")
    child_receipt = sample_delivery(child, 1)
    parent_receipt = sample_delivery(parent, 2)
    pending = transcript.record_delivery("shell", child, child_receipt)
    attached = transcript.record_delivery("shell", parent, parent_receipt)
    assert pending.dependencies == (child_receipt.digest,)
    assert {child_receipt.digest, parent_receipt.digest} <= set(attached.dependencies)
    assert transcript.snapshot()["unattached"] == []


def test_a07_transcript_conflict_retains_first_success_receipt():
    from jupyter_client.transcript import CausalTranscript, TranscriptConflict
    transcript = CausalTranscript("kernel-violet", "session-moss", 1)
    first = transcript_message("request-71", "execute_request", "session-moss", content={"code": "alpha"})
    conflict = transcript_message("request-71", "execute_request", "session-moss", content={"code": "beta"})
    receipt = transcript.record_delivery("shell", first, sample_delivery(first, 1))
    with pytest.raises(TranscriptConflict):
        transcript.record_delivery("shell", conflict, sample_delivery(conflict, 2))
    snapshot = transcript.snapshot()
    assert snapshot["requests"][0]["message"]["content"] == {"code": "alpha"}
    assert snapshot["receipts"][0] == receipt and len(snapshot["failures"]) == 1


def test_a08_lifecycle_preparation_lease_is_owner_validated():
    from jupyter_client.receipts import ReceiptValidationError
    manager = KernelManager(); provisioner = RecordingProvisioner("lease-copper")
    lease = manager.prepare_lifecycle("start", provisioner)
    assert lease.surface == "lifecycle-lease"
    assert manager.validate_lifecycle_lease(lease)
    assert provisioner.allocated == {"start"}
    other = KernelManager()
    with pytest.raises(ReceiptValidationError):
        other.validate_lifecycle_lease(lease, raise_error=True)


def test_a09_aborted_lease_cleans_and_records_failure_without_success():
    manager = KernelManager(); provisioner = RecordingProvisioner("lease-slate")
    before = manager.lifecycle_snapshot()
    lease = manager.prepare_lifecycle("restart", provisioner)
    manager.abort_lifecycle(lease, provisioner, RuntimeError("replacement failed"))
    assert manager.lifecycle_snapshot() == before
    assert manager.latest_lifecycle_receipt is None
    assert manager.lifecycle_failures()[-1]["lease_digest"] == lease.digest
    assert provisioner.allocated == set()
    assert manager.lifecycle_operation("shutdown", provisioner) == before


def test_a10_kernel_catalog_receipt_tracks_files_policy_and_no_change(tmp_path):
    root = tmp_path / "kernels"; root.mkdir()
    write_kernel_spec(root, "Quartz", "Quartz One")
    manager = KernelSpecManager(kernel_dirs=[str(root)], ensure_native_kernel=False)
    first = manager.refresh_catalog(); same = manager.refresh_catalog()
    assert first["receipt"] == same["receipt"]
    broken = root / "broken"; broken.mkdir(); (broken / "kernel.json").write_text("{bad", encoding="utf-8")
    second = manager.refresh_catalog()
    assert second["receipt"].parent_digest == first["receipt"].digest
    assert second["provenance"]["broken"]["status"] == "invalid"
    assert manager.validate_kernel_catalog_receipt(first["receipt"])


def test_a11_provisioner_catalog_and_created_provider_have_distinct_receipts(monkeypatch):
    entries = EntryPoints([FakeEntryPoint("public-fixture", "fixture.one:PublicFixtureProvisioner", PublicFixtureProvisioner)])
    monkeypatch.setattr("importlib.metadata.entry_points", lambda: entries)
    factory = KernelProvisionerFactory(); catalog = factory.refresh_catalog()
    spec = KernelSpec(metadata={"kernel_provisioner": {"provisioner_name": "public-fixture"}})
    provider = factory.create_provisioner_instance("provider-a", spec, parent=None, catalog_generation=catalog["generation"])
    assert factory.validate_provisioner_catalog_receipt(catalog["receipt"])
    assert provider.provider_receipt.surface == "provider"
    assert catalog["receipt"].digest in provider.provider_receipt.dependencies


def test_a12_native_connection_json_types_and_load(tmp_path):
    path = tmp_path / "connection-native.json"
    filename, written = write_connection_file(str(path), ip="127.0.0.1", key=b"native-coral")
    assert filename == str(path)
    assert all(isinstance(written[name], int) and written[name] > 0 for name in ("shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))
    assert json.loads(path.read_text(encoding="utf-8"))["key"] == "native-coral"
    manager = KernelManager(connection_file=str(path)); manager.load_connection_file()
    assert manager.session.key == b"native-coral"


def test_a13_native_signed_routing_buffers_and_invalid_signature():
    signer = Session(key=b"native-lilac")
    message, identities, core = wire(signer, "comm_msg", content={"value": 119}, ident=[b"route-x", b"route-y"], buffers=[memoryview(b"buffer-z")])
    decoded = Session(key=b"native-lilac").deserialize(core)
    assert identities == [b"route-x", b"route-y"] and decoded["msg_id"] == message["msg_id"]
    assert [bytes(item) for item in decoded["buffers"]] == [b"buffer-z"]
    bad = list(core); bad[0] = b"x" * len(bytes(bad[0]))
    with pytest.raises(ValueError):
        Session(key=b"native-lilac").deserialize(bad)


def test_a14_native_kernelspec_and_provisioner_retry_are_transactional(tmp_path):
    resource = write_kernel_spec(tmp_path, "MixedName", "Native Display")
    parsed = KernelSpec.from_resource_dir(str(resource))
    assert json.loads(parsed.to_json()) == parsed.to_dict()
    receiver = LocalProvisioner(kernel_id="receiver", kernel_spec=KernelSpec(), parent=None)
    receiver.connection_info = {"transport": "tcp", "ip": "127.0.0.81"}
    before = (receiver.kernel_id, dict(receiver.connection_info))
    with pytest.raises(KeyError):
        asyncio.run(receiver.load_provisioner_info({"connection_info": {"transport": "ipc"}}))
    assert (receiver.kernel_id, receiver.connection_info) == before
    source = LocalProvisioner(kernel_id="source", kernel_spec=KernelSpec(), parent=None)
    source.connection_info = {"transport": "ipc", "ip": "kernel-native"}
    asyncio.run(receiver.load_provisioner_info(asyncio.run(source.get_provisioner_info())))
    assert receiver.kernel_id == "source"
