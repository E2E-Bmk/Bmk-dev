from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from conftest import candidate_env, dependencies, make_notebook


def test_E01_workflow_publishes_a_four_owner_receipt_closure(tmp_path):
    from nbformat.artifact import verify_receipt_closure
    from nbformat.workflow import publish_workflow
    result=publish_workflow(make_notebook(),store_path=tmp_path/"store.db",lineage_path=tmp_path/"lineage.db",trust_path=tmp_path/"trust.db",destination=tmp_path/"release.json",owner="survey",stage_id="project",key_id="release",secret=b"secret")
    assert verify_receipt_closure(result["receipts"],result["terminal_receipt"])
    assert result["artifact"]["revision"]==1 and result["artifact"]["publication"]["acknowledged"] is True


def test_E02_crash_adoption_feeds_lineage_trust_and_publication(tmp_path):
    from nbformat._receipts import canonical
    from nbformat.artifact import ArtifactPublication, verify_receipt_closure
    from nbformat.durable_store import DurableStore
    from nbformat.lineage import LineageJournal
    from nbformat.trust_receipts import TrustLedger
    notebook=make_notebook(); store_path=tmp_path/"crash-store.db"; token_file=tmp_path/"crash-token"
    code="from nbformat.durable_store import DurableStore;import pathlib,sys\nl=DurableStore(sys.argv[1]).acquire('lost');pathlib.Path(sys.argv[2]).write_text(l.token)"
    assert subprocess.run([sys.executable,"-B","-c",code,str(store_path),str(token_file)],env=candidate_env(),timeout=20).returncode==0
    store_receipt=DurableStore(store_path).adopt_orphan(token_file.read_text(),"adopter").commit({"recovered":True})
    lineage=LineageJournal(tmp_path/"crash-lineage.db"); prepare=lineage.prepare("recovered",input_digest="x",output_digest="y",parents=[store_receipt["receipt_id"]]); ack=lineage.acknowledge(prepare)
    trust=TrustLedger(tmp_path/"crash-trust.db"); generation=trust.issue_generation("k",b"s",parents=[store_receipt["receipt_id"]]); signed=trust.sign(notebook,domain="d",key_id="k",lineage_receipt=ack)
    pub=ArtifactPublication(tmp_path/"crash-release.json"); p=pub.prepare(notebook,audit={"crash":True},dependency_receipts=[store_receipt,ack,signed]); v=pub.make_visible(p); terminal=pub.acknowledge(v)
    assert verify_receipt_closure([store_receipt,prepare,ack,generation,signed,p,v],terminal)


def test_E03_lineage_rollback_preserves_previous_artifact_and_trust_state(tmp_path):
    from nbformat.lineage import LineageJournal
    from nbformat.workflow import publish_workflow
    first=publish_workflow(make_notebook(),store_path=tmp_path/"s1.db",lineage_path=tmp_path/"l1.db",trust_path=tmp_path/"t1.db",destination=tmp_path/"protected.json",owner="one",stage_id="one",key_id="k",secret=b"s")
    before=(tmp_path/"protected.json").read_bytes(); journal=LineageJournal(tmp_path/"failed-lineage.db"); journal.prepare("failed",input_digest="a",output_digest="b"); journal.rollback("failed")
    assert (tmp_path/"protected.json").read_bytes()==before and first["artifact"]["revision"]==1


def test_E04_two_prepared_publications_have_one_visible_winner(tmp_path):
    from nbformat.artifact import ArtifactPublication, ArtifactRevisionConflict
    deps=dependencies(tmp_path,label="race"); destination=tmp_path/"race.json"; pub=ArtifactPublication(destination); packet=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]
    first=pub.prepare(deps["notebook"],audit={"owner":"first"},dependency_receipts=packet,expected_revision=0); second=pub.prepare(deps["notebook"],audit={"owner":"second"},dependency_receipts=packet,expected_revision=0)
    pub.recover(first["prepare_id"])
    with pytest.raises(ArtifactRevisionConflict): pub.make_visible(second)
    assert json.loads(destination.read_text())["audit"]=={"owner":"first"}


def test_E05_all_four_owners_reopen_and_revalidate_the_terminal_closure(tmp_path):
    from nbformat.artifact import ArtifactPublication, verify_receipt_closure
    from nbformat.durable_store import DurableStore
    from nbformat.lineage import LineageJournal
    from nbformat.trust_receipts import TrustLedger
    from nbformat.workflow import publish_workflow
    paths={"store":tmp_path/"reopen-store.db","lineage":tmp_path/"reopen-lineage.db","trust":tmp_path/"reopen-trust.db","artifact":tmp_path/"reopen.json"}
    result=publish_workflow(make_notebook(),store_path=paths["store"],lineage_path=paths["lineage"],trust_path=paths["trust"],destination=paths["artifact"],owner="reopen",stage_id="reopen",key_id="key",secret=b"secret")
    assert DurableStore(paths["store"]).generation==1 and LineageJournal(paths["lineage"]).replay("reopen")["kind"]=="lineage-ack"
    signed=next(x for x in result["receipts"] if x["kind"]=="trust-sign"); assert TrustLedger(paths["trust"]).check(make_notebook(),signed)
    terminal=ArtifactPublication(paths["artifact"]).recover(result["terminal_receipt"]["prepare_id"]); assert verify_receipt_closure(result["receipts"],terminal)


def test_E06_retirement_blocks_old_trust_before_a_new_artifact_revision(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="retire-system"); destination=tmp_path/"retire-system.json"; pub=ArtifactPublication(destination); packet=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]
    first=pub.prepare(deps["notebook"],audit={"key":1},dependency_receipts=packet); pub.recover(first["prepare_id"]); deps["trust"].retire("key-retire-system",1)
    assert not deps["trust"].check(deps["notebook"],deps["signed"])
    generation=deps["trust"].issue_generation("key-retire-system",b"new"); signed=deps["trust"].sign(deps["notebook"],domain="domain-retire-system",key_id="key-retire-system",lineage_receipt=deps["lineage_ack"])
    second=pub.prepare(deps["notebook"],audit={"key":generation["generation"]},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],signed],expected_revision=1); pub.recover(second["prepare_id"])
    assert json.loads(destination.read_text())["revision"]==2 and deps["trust"].check(deps["notebook"],signed)


def test_E07_missing_owner_receipt_breaks_closure_even_when_artifact_is_visible(tmp_path):
    from nbformat.artifact import ArtifactPublication, verify_receipt_closure
    deps=dependencies(tmp_path,label="missing"); pub=ArtifactPublication(tmp_path/"missing.json"); prepared=pub.prepare(deps["notebook"],audit={},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]); visible=pub.make_visible(prepared); terminal=pub.acknowledge(visible)
    incomplete=[deps["store_receipt"],deps["lineage_prepare"],deps["lineage_ack"],deps["signed"],prepared,visible]
    assert verify_receipt_closure(incomplete,terminal) is False


def test_E08_native_construct_validate_sign_persist_convert_and_restore(tmp_path):
    import nbformat
    from nbformat.sign import MemorySignatureStore, NotebookNotary
    notebook=make_notebook(); notary=NotebookNotary(store_factory=MemorySignatureStore,secret=b"native-system"); notary.sign(notebook); path=tmp_path/"native.ipynb"; nbformat.write(notebook,path); restored=nbformat.read(path,4)
    assert notary.check_signature(restored); legacy=nbformat.convert(copy.deepcopy(restored),3); current=nbformat.convert(legacy,4); assert [x.source for x in current.cells]==[x.source for x in notebook.cells] and nbformat.validate(current) is None
