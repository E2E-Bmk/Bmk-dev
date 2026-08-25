from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from tests.concurrency_support import synchronized_workers
from tests.support import GATE, assert_raises, candidate_root, file_tree, process_env, workspace


def _surface():
    from cookiecutter.release import (
        ArtifactCatalog,
        ChannelRegistry,
        DeliveryOutbox,
        LeaseRegistry,
        LineageLedger,
        PublicationReconciler,
    )

    return ArtifactCatalog, ChannelRegistry, DeliveryOutbox, LeaseRegistry, LineageLedger, PublicationReconciler


def _exceptions():
    from cookiecutter import exceptions

    return exceptions


def _project(root: Path, name: str, body: bytes) -> Path:
    project = root / name
    (project / "docs").mkdir(parents=True)
    (project / "docs" / "guide.bin").write_bytes(body)
    (project / "metadata.json").write_text(json.dumps({"name": name, "size": len(body)}), encoding="utf-8")
    return project


def _public_objects(root: Path):
    ArtifactCatalog, ChannelRegistry, DeliveryOutbox, LeaseRegistry, LineageLedger, PublicationReconciler = _surface()
    catalog = ArtifactCatalog(root / "catalog")
    channels = ChannelRegistry(root / "channels", catalog)
    outbox = DeliveryOutbox(root / "outbox", catalog)
    leases = LeaseRegistry(root / "leases")
    lineages = LineageLedger(root / "lineages")
    reconciler = PublicationReconciler(root / "coordination", catalog, channels, outbox, lineages, leases)
    return SimpleNamespace(catalog=catalog, channels=channels, outbox=outbox, leases=leases, lineages=lineages, reconciler=reconciler)


def _payload(value: str) -> dict:
    return {"cookiecutter": {"slug": "release", "value": value}, "revision": value}


def _bundle(root: Path, label: str = "north", *, closure_owner: str = "builder", plan_owner: str = "planner", two_artifacts: bool = False):
    objects = _public_objects(root)
    prior = objects.catalog.seal(_project(root, f"prior-{label}", b"prior-" + label.encode()), context={"release": "prior"}, owner="baseline-builder")
    primary = objects.catalog.seal(_project(root, f"primary-{label}", b"primary-" + label.encode()), context={"release": label}, owner=closure_owner)
    artifact_ids = [primary.artifact_id]
    if two_artifacts:
        supplement = objects.catalog.seal(_project(root, f"supplement-{label}", b"supplement-" + label.encode()), context={"release": label}, owner=closure_owner)
        artifact_ids.append(supplement.artifact_id)
    closure = objects.catalog.close(artifact_ids, context={"release": label, "_private": "excluded"}, owner=closure_owner)
    base_state = objects.channels.commit(objects.channels.reserve("stable/blue", prior.artifact_id, expected_epoch=0, owner="baseline-publisher"))
    replay = root / "replays" / "release.json"
    replay.parent.mkdir(parents=True)
    replay.write_text(json.dumps(_payload("base"), sort_keys=True, separators=(",", ":")), encoding="utf-8")
    planned = _payload(label)
    plan = objects.reconciler.prepare("stable/blue", closure.closure_id, replay, planned, expected_epoch=base_state.epoch, owner=plan_owner, route="edge/eu")
    return SimpleNamespace(**objects.__dict__, prior=prior, primary=primary, closure=closure, base_state=base_state, replay=replay, planned=planned, plan=plan, root=root)


def _prefix() -> str:
    return f"""
import os,sys
sys.path.insert(0,{str(GATE)!r})
sys.path.insert(1,{str(candidate_root())!r})
sys.path.insert(2,{str((GATE / '../../.venv-reference/Lib/site-packages').resolve())!r})
if os.environ.get('COOKIECUTTER_SYNTHETIC_PROFILE'):
 from reference_patch import apply
 apply()
"""


def _run(root: Path, body: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, "-c", _prefix() + body],
        cwd=root,
        env=process_env(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == expected, completed.stdout + completed.stderr
    return completed


def _object_script(bundle, action: str) -> str:
    setup = f"""
from cookiecutter.release import ArtifactCatalog,ChannelRegistry,DeliveryOutbox,LeaseRegistry,LineageLedger,PublicationReconciler
from pathlib import Path
root=Path({str(bundle.root)!r})
catalog=ArtifactCatalog(root/'catalog')
channels=ChannelRegistry(root/'channels',catalog)
outbox=DeliveryOutbox(root/'outbox',catalog)
leases=LeaseRegistry(root/'leases')
lineages=LineageLedger(root/'lineages')
reconciler=PublicationReconciler(root/'coordination',catalog,channels,outbox,lineages,leases)
plan=reconciler.plan({bundle.plan.plan_id!r})
"""
    return setup + action


def _commit_process(bundle, owner: str = "publisher", patch: str = "") -> None:
    _run(bundle.root, _object_script(bundle, patch + f"\nreconciler.commit(plan,owner={owner!r})\n"))


def _deliver_process(bundle, owner: str = "courier") -> None:
    _run(bundle.root, _object_script(bundle, f"\nentry=outbox.current(plan.delivery_id)\nclaim=outbox.claim(plan.delivery_id,owner={owner!r})\noutbox.acknowledge(claim,receipt_digest=entry.payload_digest,owner={owner!r})\n"))


def _close_process(bundle, owner: str = "auditor") -> None:
    _run(bundle.root, _object_script(bundle, f"\nreconciler.close_receipts(plan.plan_id,owner={owner!r})\n"))


def _finish(bundle, *, publisher: str = "publisher", courier: str = "courier", auditor: str = "auditor"):
    _commit_process(bundle, publisher)
    _deliver_process(bundle, courier)
    _close_process(bundle, auditor)
    receipt = bundle.reconciler.receipt_closure(bundle.plan.plan_id)
    assert receipt is not None
    assert len(receipt.owners) >= 4
    return receipt


def _a13_lease_acquire() -> None:
    with workspace() as root:
        leases = _public_objects(root).leases
        grant = leases.acquire("project/lilac", owner="owner-a")
        assert grant.generation == 1 and grant.parent_token is None
        assert leases.current("project/lilac") == grant and leases.history("project/lilac") == [grant]


def _a14_lease_recover_generation() -> None:
    with workspace() as root:
        body = f"from cookiecutter.release import LeaseRegistry\nLeaseRegistry({str(root/'leases')!r}).acquire('project/moss',owner='departed')\n"
        _run(root, body)
        leases = _public_objects(root).leases
        recovered = leases.recover("project/moss", owner="rescuer")
        assert recovered.generation == 2 and recovered.parent_token
        assert [item.owner for item in leases.history("project/moss")] == ["departed", "rescuer"]


def _a15_lineage_prepare_commit() -> None:
    with workspace() as root:
        ledger = _public_objects(root).lineages
        prepared = ledger.prepare("release/lime", payload_digest="a" * 64, owner="planner")
        committed = ledger.commit(prepared, owner="publisher")
        assert (prepared.sequence, committed.sequence) == (1, 2)
        assert committed.parent_token == prepared.token and committed.payload_digest == prepared.payload_digest


def _a16_lineage_ack() -> None:
    with workspace() as root:
        ledger = _public_objects(root).lineages
        prepared = ledger.prepare("release/rose", payload_digest="b" * 64, owner="planner")
        committed = ledger.commit(prepared, owner="publisher")
        acknowledged = ledger.acknowledge(committed, receipt_digest="c" * 64, owner="auditor")
        assert acknowledged.phase == "ack" and acknowledged.parent_token == committed.token
        assert [item.phase for item in ledger.history("release/rose")] == ["prepare", "commit", "ack"]


def _a17_manifest_closure() -> None:
    with workspace() as root:
        objects = _public_objects(root)
        artifact = objects.catalog.seal(_project(root, "cobalt", b"closure"), context={"color": "cobalt"}, owner="builder")
        closure = objects.catalog.close([artifact.artifact_id], context={"color": "cobalt", "_secret": 9}, owner="manifest-owner")
        assert len(closure.closure_id) == 64 and closure.artifact_ids == (artifact.artifact_id,)
        assert objects.catalog.inspect_closure(closure.closure_id) == closure


def _a18_manifest_requires_verified_artifacts() -> None:
    with workspace() as root:
        objects = _public_objects(root)
        exc = _exceptions()
        assert_raises(exc.ManifestClosureException, objects.catalog.close, ["f" * 64], context={"x": 1}, owner="builder")
        assert objects.catalog.list_closures() == []


def _a19_outbox_enqueue_claim() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        entry = bundle.outbox.current(bundle.plan.delivery_id)
        claim = bundle.outbox.claim(entry.delivery_id, owner="worker-a")
        assert entry.status == "pending" and claim.attempt == 1 and claim.delivery_id == entry.delivery_id


def _a20_outbox_ack() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        entry = bundle.outbox.current(bundle.plan.delivery_id)
        claim = bundle.outbox.claim(entry.delivery_id, owner="worker-b")
        receipt = bundle.outbox.acknowledge(claim, receipt_digest=entry.payload_digest, owner="worker-b")
        assert receipt.closure_id == bundle.closure.closure_id
        assert bundle.outbox.current(entry.delivery_id).status == "delivered"


def _a21_publication_plan_binding() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        assert bundle.plan.closure_id == bundle.closure.closure_id
        assert bundle.plan.artifact_id == bundle.primary.artifact_id
        assert bundle.plan.expected_epoch == 1 and bundle.outbox.current(bundle.plan.delivery_id).status == "pending"


def _a22_precommit_compensation() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        prior = bundle.replay.read_bytes()
        result = bundle.reconciler.reconcile(bundle.plan.plan_id, owner="rescuer")
        assert result.outcome == "compensated" and bundle.replay.read_bytes() == prior
        assert bundle.channels.current("stable/blue") == bundle.base_state
        assert bundle.outbox.current(bundle.plan.delivery_id).status == "cancelled"


def _a23_receipt_closure() -> None:
    with workspace() as root:
        receipt = _finish(_bundle(root))
        assert len(receipt.receipt_ids) == 6 and len(receipt.owners) >= 4


def _a24_receipt_closure_reopen() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        receipt = _finish(bundle)
        reopened = _public_objects(root).reconciler.inspect_receipt_closure(receipt.receipt_closure_id)
        assert reopened == receipt
        try:
            receipt.owner = "changed"
        except Exception:
            pass
        else:
            raise AssertionError("receipt closure must be immutable")


def _i07_live_lease_conflict() -> None:
    with workspace() as root:
        leases = _public_objects(root).leases
        leases.acquire("shared", owner="first")
        assert_raises(_exceptions().LeaseConflictException, leases.acquire, "shared", owner="second")


def _i08_lease_handoff_single_use() -> None:
    with workspace() as root:
        leases = _public_objects(root).leases
        first = leases.acquire("handoff", owner="first")
        second = leases.handoff(first, owner="second")
        assert second.generation == 2 and second.parent_token == first.token
        assert_raises(_exceptions().LeaseConflictException, leases.acknowledge, first, receipt_digest="d" * 64, owner="first")
        assert leases.acknowledge(second, receipt_digest="d" * 64, owner="second").generation == 2


def _i09_cross_process_lease_recovery() -> None:
    _a14_lease_recover_generation()


def _i10_independent_lease_resources() -> None:
    with workspace() as root:
        leases = _public_objects(root).leases
        resources = ("project/alpha", "project/beta")
        assert resources[0] != resources[1]
        results = synchronized_workers({
            resource: (lambda resource=resource: leases.acquire(resource, owner=f"owner:{resource}"))
            for resource in resources
        })
        assert set(results) == set(resources)
        assert {grant.resource for grant in results.values()} == set(resources)
        assert len({grant.token for grant in results.values()}) == 2
        for resource in resources:
            assert leases.current(resource) == results[resource]
            assert leases.history(resource) == [results[resource]]


def _i11_lineage_append_order() -> None:
    _a16_lineage_ack()


def _i12_lineage_crash_recovery() -> None:
    with workspace() as root:
        body = f"from cookiecutter.release import LineageLedger\nLineageLedger({str(root/'lineages')!r}).prepare('crashed',payload_digest='e'*64,owner='departed')\n"
        _run(root, body)
        ledger = _public_objects(root).lineages
        recovered = ledger.recover("crashed", owner="rescuer")
        assert recovered.phase == "compensate"
        assert [item.owner for item in ledger.history("crashed")] == ["departed", "rescuer"]


def _i13_borrowed_lineage_token() -> None:
    with workspace() as root:
        ledger = _public_objects(root).lineages
        prepared = ledger.prepare("borrowed", payload_digest="f" * 64, owner="one")
        assert_raises(_exceptions().LineageConflictException, ledger.commit, replace(prepared, owner="two"), owner="two")


def _i14_lineage_reopen_after_ack() -> None:
    with workspace() as root:
        ledger = _public_objects(root).lineages
        first = ledger.prepare("roundtrip", payload_digest="1" * 64, owner="a")
        committed = ledger.commit(first, owner="b")
        ledger.acknowledge(committed, receipt_digest="2" * 64, owner="c")
        reopened = _public_objects(root).lineages
        second = reopened.prepare("roundtrip", payload_digest="3" * 64, owner="d")
        assert second.sequence == 4 and second.parent_token == reopened.history("roundtrip")[-2].token


def _i15_closure_deduplication() -> None:
    with workspace() as root:
        objects = _public_objects(root)
        artifact = objects.catalog.seal(_project(root, "dedupe", b"same"), context={"v": 1}, owner="a")
        first = objects.catalog.close([artifact.artifact_id], context={"v": 1}, owner="first")
        second = objects.catalog.close([artifact.artifact_id], context={"v": 1}, owner="second")
        assert first.closure_id == second.closure_id and len(objects.catalog.list_closures()) == 1


def _i16_closure_context_partition() -> None:
    with workspace() as root:
        objects = _public_objects(root)
        artifact = objects.catalog.seal(_project(root, "partition", b"same"), context={"v": 1}, owner="a")
        first = objects.catalog.close([artifact.artifact_id], context={"region": "east"}, owner="a")
        second = objects.catalog.close([artifact.artifact_id], context={"region": "west"}, owner="a")
        assert first.closure_id != second.closure_id and first.context_digest != second.context_digest


def _i17_closure_failure_isolated() -> None:
    with workspace() as root:
        objects = _public_objects(root)
        artifact = objects.catalog.seal(_project(root, "valid", b"valid"), context={}, owner="a")
        valid = objects.catalog.close([artifact.artifact_id], context={}, owner="a")
        assert_raises(_exceptions().ManifestClosureException, objects.catalog.close, [artifact.artifact_id, "0" * 64], context={}, owner="b")
        assert objects.catalog.inspect_closure(valid.closure_id) == valid


def _i18_concurrent_closure_converges() -> None:
    with workspace() as root:
        objects = _public_objects(root)
        artifact = objects.catalog.seal(_project(root, "concurrent", b"same"), context={}, owner="a")
        owners = ("closer/one", "closer/two")
        results = synchronized_workers({
            owner: (lambda owner=owner: objects.catalog.close(
                [artifact.artifact_id], context={"lane": "same"}, owner=owner
            ))
            for owner in owners
        })
        assert set(results) == set(owners)
        assert len({item.closure_id for item in results.values()}) == 1
        closure = next(iter(results.values()))
        assert closure.artifact_ids == (artifact.artifact_id,)
        assert objects.catalog.inspect_closure(closure.closure_id).closure_id == closure.closure_id
        assert [item.closure_id for item in objects.catalog.list_closures()] == [closure.closure_id]


def _i19_outbox_claim_conflict() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        bundle.outbox.claim(bundle.plan.delivery_id, owner="first")
        assert_raises(_exceptions().DeliveryConflictException, bundle.outbox.claim, bundle.plan.delivery_id, owner="second")


def _i20_stale_delivery_attempt() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        body = _object_script(bundle, "\noutbox.claim(plan.delivery_id,owner='departed-courier')\n")
        _run(root, body)
        assert bundle.outbox.recover() == 1
        claim = bundle.outbox.claim(bundle.plan.delivery_id, owner="replacement-courier")
        assert claim.attempt == 2


def _i21_delivery_receipt_binding() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        claim = bundle.outbox.claim(bundle.plan.delivery_id, owner="courier")
        assert_raises(_exceptions().DeliveryConflictException, bundle.outbox.acknowledge, claim, receipt_digest="0" * 64, owner="courier")
        borrowed = replace(claim, owner="borrower")
        assert_raises(_exceptions().DeliveryConflictException, bundle.outbox.acknowledge, borrowed, receipt_digest=bundle.plan.payload_digest, owner="borrower")


def _i22_delivery_reopen_projection() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        reopened = _public_objects(root).outbox
        assert reopened.pending("edge/eu")[0].delivery_id == bundle.plan.delivery_id
        claim = reopened.claim(bundle.plan.delivery_id, owner="courier")
        receipt = reopened.acknowledge(claim, receipt_digest=bundle.plan.payload_digest, owner="courier")
        assert reopened.receipts("edge/eu") == [receipt] and reopened.pending() == []


def _i23_plan_cross_owner_bindings() -> None:
    _a21_publication_plan_binding()


def _i24_publication_commit_handoffs() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        result = bundle.reconciler.commit(bundle.plan, owner="publisher")
        assert result.outcome == "committed" and bundle.channels.current("stable/blue").artifact_id == bundle.primary.artifact_id
        assert json.loads(bundle.replay.read_text(encoding="utf-8"))["revision"] == bundle.planned["revision"]
        assert bundle.outbox.current(bundle.plan.delivery_id).status == "pending"
        assert [item.phase for item in bundle.lineages.history(f"publication:{bundle.plan.plan_id}")] == ["prepare", "commit"]


def _i25_precommit_reconcile_compensation() -> None:
    _a22_precommit_compensation()


def _i26_post_channel_compensation() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        bundle.channels.commit(bundle.channels.reserve(bundle.plan.channel, bundle.plan.artifact_id, expected_epoch=1, owner="crashed-publisher"))
        result = bundle.reconciler.reconcile(bundle.plan.plan_id, owner="compensator")
        assert result.outcome == "compensated" and bundle.channels.current(bundle.plan.channel).artifact_id == bundle.prior.artifact_id
        assert bundle.channels.current(bundle.plan.channel).epoch == 3


def _i27_channel_winner_preserved() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        competitor = bundle.catalog.seal(_project(root, "winner", b"winner"), context={"v": "winner"}, owner="other-builder")
        winner = bundle.channels.commit(bundle.channels.reserve(bundle.plan.channel, competitor.artifact_id, expected_epoch=1, owner="other-publisher"))
        result = bundle.reconciler.reconcile(bundle.plan.plan_id, owner="loser-compensator")
        assert result.outcome == "compensated" and bundle.channels.current(bundle.plan.channel) == winner


def _i28_delivery_recovery_after_commit() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        bundle.reconciler.commit(bundle.plan, owner="publisher")
        _run(root, _object_script(bundle, "\noutbox.claim(plan.delivery_id,owner='departed')\n"))
        assert bundle.outbox.recover() == 1
        claim = bundle.outbox.claim(bundle.plan.delivery_id, owner="replacement")
        receipt = bundle.outbox.acknowledge(claim, receipt_digest=bundle.plan.payload_digest, owner="replacement")
        assert receipt.owner == "replacement" and claim.attempt == 2


def _i29_cross_surface_receipt_digest() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        receipt = _finish(bundle)
        assert receipt.payload_digest == bundle.plan.payload_digest
        assert bundle.outbox.receipts()[0].receipt_id in receipt.receipt_ids


def _i30_minimum_owner_quorum() -> None:
    with workspace() as root:
        bundle = _bundle(root, closure_owner="same", plan_owner="same")
        bundle.reconciler.commit(bundle.plan, owner="same")
        claim = bundle.outbox.claim(bundle.plan.delivery_id, owner="same")
        bundle.outbox.acknowledge(claim, receipt_digest=bundle.plan.payload_digest, owner="same")
        assert_raises(_exceptions().ReceiptClosureException, bundle.reconciler.close_receipts, bundle.plan.plan_id, owner="same")


def _i31_receipt_closure_single_use() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        _finish(bundle)
        assert_raises(_exceptions().ReceiptClosureException, bundle.reconciler.close_receipts, bundle.plan.plan_id, owner="second-auditor")


def _i32_receipt_closure_reopen() -> None:
    _a24_receipt_closure_reopen()


def _i33_lease_generation_to_lineage() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        bundle.reconciler.commit(bundle.plan, owner="publisher")
        resource = f"publication:{bundle.plan.channel}:{bundle.replay.resolve()}"
        history = bundle.leases.history(resource)
        lineage = bundle.lineages.history(f"publication:{bundle.plan.plan_id}")
        assert [item.generation for item in history] == [1, 2]
        assert [item.owner for item in history] == ["planner", "publisher"] and [item.owner for item in lineage] == ["planner", "publisher"]


def _i34_manifest_to_outbox_handoff() -> None:
    with workspace() as root:
        bundle = _bundle(root, two_artifacts=True)
        entry = bundle.outbox.current(bundle.plan.delivery_id)
        assert entry.closure_id == bundle.closure.closure_id
        assert bundle.catalog.inspect_closure(entry.closure_id).artifact_ids == bundle.closure.artifact_ids


def _i35_publication_views_agree() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        _finish(bundle)
        state = bundle.channels.current(bundle.plan.channel)
        delivery = bundle.outbox.receipts()[0]
        assert state.artifact_id in bundle.closure.artifact_ids
        assert delivery.closure_id == bundle.closure.closure_id
        assert json.loads(bundle.replay.read_text(encoding="utf-8")) == bundle.planned


def _i36_compensation_lineage_closure() -> None:
    with workspace() as root:
        bundle = _bundle(root)
        result = bundle.reconciler.reconcile(bundle.plan.plan_id, owner="rescuer")
        history = bundle.lineages.history(f"publication:{bundle.plan.plan_id}")
        assert result.outcome == "compensated" and [item.phase for item in history] == ["prepare", "compensate"]
        assert_raises(_exceptions().ReceiptClosureException, bundle.reconciler.close_receipts, bundle.plan.plan_id, owner="auditor")


def _retry_after_compensation(bundle, label: str):
    plan = bundle.reconciler.prepare(bundle.plan.channel, bundle.closure.closure_id, bundle.replay, _payload(label), expected_epoch=bundle.channels.current(bundle.plan.channel).epoch, owner=f"planner-{label}", route="edge/eu")
    bundle.plan = plan
    bundle.planned = _payload(label)
    return bundle


def _system(root_id: str) -> None:
    with workspace() as root:
        mode = root_id
        bundle = _bundle(root, label=f"system-{mode.lower()}", two_artifacts=mode in {"S06", "S09", "S12"})
        if mode == "S02":
            bundle.reconciler.reconcile(bundle.plan.plan_id, owner="preflight-rescuer")
            bundle = _retry_after_compensation(bundle, "s02-retry")
        elif mode == "S03":
            competitor = bundle.catalog.seal(_project(root, "race-winner", b"winner"), context={"race": 1}, owner="winner-builder")
            bundle.channels.commit(bundle.channels.reserve(bundle.plan.channel, competitor.artifact_id, expected_epoch=1, owner="winner-publisher"))
            bundle.reconciler.reconcile(bundle.plan.plan_id, owner="race-compensator")
            bundle = _retry_after_compensation(bundle, "s03-retry")
        elif mode == "S04":
            crash = "\nreal_commit=channels.commit\ndef crash(reservation):\n state=real_commit(reservation)\n os._exit(93)\nchannels.commit=crash\n"
            _run(root, _object_script(bundle, crash + "\nreconciler.commit(plan,owner='crashed-publisher')\n"), expected=93)
            bundle.reconciler.reconcile(bundle.plan.plan_id, owner="channel-compensator")
            bundle = _retry_after_compensation(bundle, "s04-retry")
        elif mode == "S05":
            crash = "\nreal_commit=lineages.commit\ndef crash(record,owner):\n value=real_commit(record,owner=owner)\n os._exit(94)\nlineages.commit=crash\n"
            _run(root, _object_script(bundle, crash + "\nreconciler.commit(plan,owner='lineage-crash-publisher')\n"), expected=94)
            result = bundle.reconciler.reconcile(bundle.plan.plan_id, owner="lineage-rescuer")
            assert result.outcome == "committed"
        elif mode == "S07":
            bundle.reconciler.reconcile(bundle.plan.plan_id, owner="first-rescuer")
            bundle = _retry_after_compensation(bundle, "s07-generation-two")
        elif mode == "S08":
            bundle.replay.write_text(json.dumps(_payload("external-base"), sort_keys=True, separators=(",", ":")), encoding="utf-8")
            bundle.reconciler.reconcile(bundle.plan.plan_id, owner="replay-compensator")
            bundle = _retry_after_compensation(bundle, "s08-current")
        elif mode == "S11":
            sibling = _bundle(root / "sibling", label="sibling-route")
            _finish(sibling, publisher="sibling-publisher", courier="sibling-courier", auditor="sibling-auditor")

        if mode not in {"S05"}:
            _commit_process(bundle, owner=f"publisher-{mode.lower()}")

        if mode in {"S06", "S10", "S12"}:
            _run(root, _object_script(bundle, f"\noutbox.claim(plan.delivery_id,owner='departed-{mode.lower()}')\n"))
            assert bundle.outbox.recover() == 1
            courier = f"replacement-courier-{mode.lower()}"
        else:
            courier = f"courier-{mode.lower()}"
        _deliver_process(bundle, courier)
        _close_process(bundle, owner=f"auditor-{mode.lower()}")
        closure = bundle.reconciler.receipt_closure(bundle.plan.plan_id)
        assert closure is not None
        assert len(closure.owners) >= 4
        assert bundle.catalog.inspect_closure(bundle.plan.closure_id).closure_id in closure.receipt_ids
        assert bundle.outbox.receipts()[0].receipt_id in closure.receipt_ids
        assert bundle.plan.payload_digest == closure.payload_digest


ATOMIC = {
    "A13": _a13_lease_acquire,
    "A14": _a14_lease_recover_generation,
    "A15": _a15_lineage_prepare_commit,
    "A16": _a16_lineage_ack,
    "A17": _a17_manifest_closure,
    "A18": _a18_manifest_requires_verified_artifacts,
    "A19": _a19_outbox_enqueue_claim,
    "A20": _a20_outbox_ack,
    "A21": _a21_publication_plan_binding,
    "A22": _a22_precommit_compensation,
    "A23": _a23_receipt_closure,
    "A24": _a24_receipt_closure_reopen,
}


COMPOSITION = {
    "I07": _i07_live_lease_conflict,
    "I08": _i08_lease_handoff_single_use,
    "I09": _i09_cross_process_lease_recovery,
    "I10": _i10_independent_lease_resources,
    "I11": _i11_lineage_append_order,
    "I12": _i12_lineage_crash_recovery,
    "I13": _i13_borrowed_lineage_token,
    "I14": _i14_lineage_reopen_after_ack,
    "I15": _i15_closure_deduplication,
    "I16": _i16_closure_context_partition,
    "I17": _i17_closure_failure_isolated,
    "I18": _i18_concurrent_closure_converges,
    "I19": _i19_outbox_claim_conflict,
    "I20": _i20_stale_delivery_attempt,
    "I21": _i21_delivery_receipt_binding,
    "I22": _i22_delivery_reopen_projection,
    "I23": _i23_plan_cross_owner_bindings,
    "I24": _i24_publication_commit_handoffs,
    "I25": _i25_precommit_reconcile_compensation,
    "I26": _i26_post_channel_compensation,
    "I27": _i27_channel_winner_preserved,
    "I28": _i28_delivery_recovery_after_commit,
    "I29": _i29_cross_surface_receipt_digest,
    "I30": _i30_minimum_owner_quorum,
    "I31": _i31_receipt_closure_single_use,
    "I32": _i32_receipt_closure_reopen,
    "I33": _i33_lease_generation_to_lineage,
    "I34": _i34_manifest_to_outbox_handoff,
    "I35": _i35_publication_views_agree,
    "I36": _i36_compensation_lineage_closure,
    **{f"S{index:02d}": (lambda root_id=f"S{index:02d}": _system(root_id)) for index in range(1, 13)},
}


def atomic_workflow(root_id: str) -> None:
    ATOMIC[root_id]()


def composition_workflow(root_id: str) -> None:
    COMPOSITION[root_id]()
