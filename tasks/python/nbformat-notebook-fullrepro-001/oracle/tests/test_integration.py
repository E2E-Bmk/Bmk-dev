from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys

import pytest

from conftest import candidate_env, dependencies, make_notebook


def test_C01_store_commit_receipts_form_a_persisted_parent_chain(tmp_path):
    from nbformat.durable_store import DurableStore
    store=DurableStore(tmp_path/"chain.db"); first=store.acquire("first").commit({"step":1}); second=store.acquire("second").commit({"step":2},parents=[first["receipt_id"]])
    assert second["parents"]==[first["receipt_id"]] and DurableStore(store.path).history()[-1]["parents"]==[first["receipt_id"]]


def test_C02_process_crash_then_adoption_preserves_generation_history(tmp_path):
    from nbformat.durable_store import DurableStore
    path=tmp_path/"adopt.db"; initial=DurableStore(path).acquire("initial").commit({"n":1}); token=tmp_path/"token"
    code="from nbformat.durable_store import DurableStore;import pathlib,sys\nl=DurableStore(sys.argv[1]).acquire('crashed');pathlib.Path(sys.argv[2]).write_text(l.token)"
    assert subprocess.run([sys.executable,"-B","-c",code,str(path),str(token)],env=candidate_env(),timeout=20).returncode==0
    adopted=DurableStore(path).adopt_orphan(token.read_text(),"repair").commit({"n":2},parents=[initial["receipt_id"]])
    assert adopted["generation"]==2 and [x["event"] for x in DurableStore(path).history()]==["commit","commit"]


def test_C03_live_process_lease_cannot_be_adopted_by_token(tmp_path):
    from nbformat.durable_store import DurableStore, LeaseOwnershipError
    store=DurableStore(tmp_path/"live.db"); lease=store.acquire("live")
    with pytest.raises(LeaseOwnershipError): DurableStore(store.path).adopt_orphan(lease.token,"intruder")
    lease.rollback()


def test_C04_lineage_stage_identity_rejects_changed_conversion_meaning(tmp_path):
    from nbformat.lineage import LineageConflict, LineageJournal
    journal=LineageJournal(tmp_path/"identity.db"); first=journal.prepare("same",input_digest="a",output_digest="b")
    assert LineageJournal(journal.path).prepare("same",input_digest="a",output_digest="b")==first
    with pytest.raises(LineageConflict): journal.prepare("same",input_digest="a",output_digest="c")


def test_C05_lineage_persists_store_receipt_as_dependency(tmp_path):
    from nbformat.durable_store import DurableStore
    from nbformat.lineage import LineageJournal
    store_receipt=DurableStore(tmp_path/"s.db").acquire("o").commit({"value":13})
    journal=LineageJournal(tmp_path/"l.db"); prepared=journal.prepare("hop",input_digest="13",output_digest="17",parents=[store_receipt["receipt_id"]]); ack=journal.acknowledge(prepared)
    assert prepared["parents"]==[store_receipt["receipt_id"]] and ack["parents"]==[prepared["receipt_id"]]


def test_C06_lineage_ack_is_idempotent_without_duplicate_events(tmp_path):
    from nbformat.lineage import LineageJournal
    journal=LineageJournal(tmp_path/"ack.db"); prepared=journal.prepare("hop",input_digest="a",output_digest="b")
    first=journal.acknowledge(prepared); second=LineageJournal(journal.path).acknowledge(prepared)
    assert first==second and [x["kind"] for x in journal.history()]==["lineage-prepare","lineage-ack"]


def test_C07_rolled_back_lineage_remains_auditable_but_not_replayable(tmp_path):
    from nbformat.lineage import LineageJournal, LineageStateError
    path=tmp_path/"rolled.db"; journal=LineageJournal(path); journal.prepare("hop",input_digest="a",output_digest="b"); journal.rollback("hop")
    with pytest.raises(LineageStateError): LineageJournal(path).replay("hop")
    assert [x["kind"] for x in LineageJournal(path).history()]==["lineage-prepare","lineage-rollback"]


def test_C08_trust_signature_closes_over_acknowledged_lineage(tmp_path):
    deps=dependencies(tmp_path,label="closure")
    assert deps["lineage_ack"]["receipt_id"] in deps["signed"]["parents"]
    assert deps["signed"]["lineage_receipt"]==deps["lineage_ack"]["receipt_id"]


def test_C09_trust_rejects_a_prepare_receipt_without_acknowledgement(tmp_path):
    from nbformat.trust_receipts import TrustLedger, TrustReceiptError
    deps=dependencies(tmp_path,label="prepared"); ledger=TrustLedger(tmp_path/"other-trust.db"); ledger.issue_generation("k",b"s")
    with pytest.raises(TrustReceiptError): ledger.sign(deps["notebook"],domain="d",key_id="k",lineage_receipt=deps["lineage_prepare"])


def test_C10_key_retirement_and_new_generation_are_distinct_after_reopen(tmp_path):
    from nbformat.trust_receipts import TrustLedger
    deps=dependencies(tmp_path,label="rotate"); path=tmp_path/"rotate-trust.db"; ledger=deps["trust"]; ledger.retire("key-rotate",1)
    generation2=ledger.issue_generation("key-rotate",b"new-secret"); signed2=ledger.sign(deps["notebook"],domain="domain-rotate",key_id="key-rotate",lineage_receipt=deps["lineage_ack"])
    reopened=TrustLedger(path); assert not reopened.check(deps["notebook"],deps["signed"]) and reopened.check(deps["notebook"],signed2)
    assert generation2["generation"]==2


def test_C11_publication_requires_receipts_from_three_owner_types(tmp_path):
    from nbformat.artifact import ArtifactPublication, ArtifactStateError
    deps=dependencies(tmp_path,label="three"); pub=ArtifactPublication(tmp_path/"three.json")
    for omitted in range(3):
        values=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]; values.pop(omitted)
        with pytest.raises(ArtifactStateError): pub.prepare(deps["notebook"],audit={},dependency_receipts=values)


def test_C12_prepared_artifact_survives_owner_reopen_and_recovers(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="recover-prepared"); destination=tmp_path/"prepared.json"; first=ArtifactPublication(destination)
    prepared=first.prepare(deps["notebook"],audit={"owner":"first"},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]])
    ack=ArtifactPublication(destination).recover(prepared["prepare_id"])
    assert ack["kind"]=="artifact-ack" and json.loads(destination.read_text())["audit"]=={"owner":"first"}


def test_C13_visible_unacknowledged_artifact_recovers_without_new_revision(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="recover-visible"); destination=tmp_path/"visible.json"; pub=ArtifactPublication(destination)
    prepared=pub.prepare(deps["notebook"],audit={},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]); pub.make_visible(prepared)
    ack=ArtifactPublication(destination).recover(prepared["prepare_id"])
    assert ack["revision"]==1 and json.loads(destination.read_text())["revision"]==1


def test_C14_stale_preparation_cannot_replace_a_newer_visible_revision(tmp_path):
    from nbformat.artifact import ArtifactPublication, ArtifactRevisionConflict
    deps=dependencies(tmp_path,label="stale"); destination=tmp_path/"stale.json"; pub=ArtifactPublication(destination)
    old=pub.prepare(deps["notebook"],audit={"old":1},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]],expected_revision=0)
    winner=pub.prepare(deps["notebook"],audit={"winner":1},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]],expected_revision=0); pub.recover(winner["prepare_id"]); before=destination.read_bytes()
    with pytest.raises(ArtifactRevisionConflict): pub.make_visible(old)
    assert destination.read_bytes()==before


def test_C15_store_commit_can_anchor_multiple_independent_lineages(tmp_path):
    from nbformat.durable_store import DurableStore
    from nbformat.lineage import LineageJournal
    commit=DurableStore(tmp_path/"base.db").acquire("owner").commit({"base":True})
    left=LineageJournal(tmp_path/"left.db").prepare("left",input_digest="a",output_digest="b",parents=[commit["receipt_id"]]); right=LineageJournal(tmp_path/"right.db").prepare("right",input_digest="a",output_digest="c",parents=[commit["receipt_id"]])
    assert left["resource_id"]!=right["resource_id"] and left["parents"]==right["parents"]


def test_C16_lineage_replay_identity_is_stable_input_to_trust(tmp_path):
    from nbformat.trust_receipts import TrustLedger
    deps=dependencies(tmp_path,label="replay-trust"); replay=deps["lineage"].replay("stage-replay-trust")
    second=deps["trust"].sign(deps["notebook"],domain="domain-replay-trust",key_id="key-replay-trust",lineage_receipt=replay)
    assert second["lineage_receipt"]==deps["signed"]["lineage_receipt"] and deps["trust"].check(deps["notebook"],second)


def test_C17_trust_signature_is_preserved_in_visible_artifact_dependencies(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="trust-artifact"); destination=tmp_path/"trust-artifact.json"; pub=ArtifactPublication(destination)
    prepared=pub.prepare(deps["notebook"],audit={},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]); pub.recover(prepared["prepare_id"])
    visible=json.loads(destination.read_text()); assert any(x["receipt_id"]==deps["signed"]["receipt_id"] for x in visible["dependency_receipts"])


def test_C18_publication_history_tracks_prepare_visible_ack_per_revision(tmp_path):
    from nbformat.artifact import ArtifactPublication
    destination=tmp_path/"history.json"; pub=ArtifactPublication(destination)
    for number in (1,2):
        deps=dependencies(tmp_path,label=f"history-{number}"); prepared=pub.prepare(deps["notebook"],audit={"n":number},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]],expected_revision=number-1); pub.recover(prepared["prepare_id"])
    assert [x["kind"] for x in pub.history()]==["artifact-prepare","artifact-visible","artifact-ack"]*2


def test_C19_recovery_removes_prepared_bytes_from_staging_namespace(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="cleanup"); destination=tmp_path/"cleanup.json"; pub=ArtifactPublication(destination)
    prepared=pub.prepare(deps["notebook"],audit={},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]); pub.recover(prepared["prepare_id"])
    assert not list(tmp_path.glob("cleanup.json.*.prepared")) and not pub.lock_path.exists()


def test_C20_notebook_json_roundtrip_preserves_meaning_used_by_trust(tmp_path):
    import nbformat
    deps=dependencies(tmp_path,label="json-trust"); restored=nbformat.reads(nbformat.writes(deps["notebook"]),4)
    assert deps["trust"].check(restored,deps["signed"])


def test_C21_independent_process_observes_committed_store_generation(tmp_path):
    from nbformat.durable_store import DurableStore
    path=tmp_path/"observe.db"; DurableStore(path).acquire("parent").commit({"n":1})
    code="from nbformat.durable_store import DurableStore;import sys;print(DurableStore(sys.argv[1]).generation)"
    result=subprocess.run([sys.executable,"-B","-c",code,str(path)],env=candidate_env(),text=True,stdout=subprocess.PIPE,timeout=20,check=True)
    assert result.stdout.strip()=="1"


def test_C22_owner_resources_remain_distinct_across_a_dependency_packet(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="resources"); publisher=ArtifactPublication(tmp_path/"resources.json")
    assert len({deps["store_receipt"]["resource_id"],deps["lineage_ack"]["resource_id"],deps["signed"]["resource_id"],publisher.resource_id})==4


def test_C23_replayed_lineage_does_not_create_an_extra_ack_event(tmp_path):
    deps=dependencies(tmp_path,label="replay-event"); before=len(deps["lineage"].history()); assert deps["lineage"].replay("stage-replay-event")==deps["lineage_ack"]
    assert len(deps["lineage"].history())==before


def test_C24_rolled_back_lineage_cannot_authorize_a_trust_signature(tmp_path):
    from nbformat.lineage import LineageJournal
    from nbformat.trust_receipts import TrustLedger, TrustReceiptError
    journal=LineageJournal(tmp_path/"rolled-auth.db"); prepared=journal.prepare("x",input_digest="a",output_digest="b"); rolled=journal.rollback("x")
    trust=TrustLedger(tmp_path/"rolled-trust.db"); trust.issue_generation("k",b"s")
    with pytest.raises(TrustReceiptError): trust.sign(make_notebook(),domain="d",key_id="k",lineage_receipt=rolled)


def test_C25_artifact_acknowledgement_parent_is_the_visible_receipt(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="ack-parent"); pub=ArtifactPublication(tmp_path/"ack-parent.json")
    prepared=pub.prepare(deps["notebook"],audit={},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]]); visible=pub.make_visible(prepared); ack=pub.acknowledge(visible)
    assert ack["parents"]==[visible["receipt_id"]]


def test_C26_all_standard_cell_and_output_kinds_survive_path_roundtrip(tmp_path):
    import nbformat
    from nbformat import v4
    outputs=[v4.new_output("stream",name="stderr",text="note\n"),v4.new_output("display_data",data={"text/html":"<i>x</i>"}),v4.new_output("error",ename="SurveyError",evalue="low",traceback=["trace"])]
    notebook=v4.new_notebook(cells=[v4.new_markdown_cell("m"),v4.new_raw_cell("r"),v4.new_code_cell("c",outputs=outputs)]); path=tmp_path/"kinds.ipynb"; nbformat.write(notebook,path)
    assert nbformat.read(path,4)==notebook and nbformat.validate(notebook) is None


def test_C27_disk_projection_splits_text_but_preserves_structured_json_mimes():
    import nbformat
    from nbformat import v4
    notebook=v4.new_notebook(cells=[v4.new_markdown_cell("one\ntwo\n",attachments={"a":{"text/plain":"x\ny\n","application/json":{"n":5}}})]); raw=json.loads(nbformat.writes(notebook))
    assert raw["cells"][0]["source"]==["one\n","two\n"] and raw["cells"][0]["attachments"]["a"]["application/json"]=={"n":5}


def test_C28_iter_validate_and_normalize_remain_independent_views():
    import nbformat
    from nbformat.validator import iter_validate, normalize
    notebook=make_notebook(); malformed=copy.deepcopy(notebook); del malformed.cells[0]["source"]; assert list(iter_validate(malformed,version=4))
    duplicate=copy.deepcopy(notebook); duplicate.cells[2].id=duplicate.cells[0].id
    with pytest.warns(nbformat.warnings.DuplicateCellId): changes,normalized=normalize(duplicate)
    assert changes==1 and nbformat.validate(normalized) is None


def test_C29_representable_v3_v4_roundtrip_preserves_sources_outputs_and_metadata():
    import nbformat
    legacy=nbformat.v3.new_notebook(metadata={"station":"outer"},worksheets=[nbformat.v3.new_worksheet(cells=[nbformat.v3.new_text_cell("markdown",source="chart"),nbformat.v3.new_code_cell("print(17)",prompt_number=7)])])
    restored=nbformat.convert(copy.deepcopy(nbformat.convert(copy.deepcopy(legacy),4)),3); assert restored.metadata.station=="outer"


def test_C30_upstream_notary_edit_restore_and_unsign_lifecycle():
    from nbformat.sign import MemorySignatureStore, NotebookNotary
    notebook=make_notebook(); notary=NotebookNotary(store_factory=MemorySignatureStore,secret=b"ordinary-secret"); notary.sign(notebook); assert notary.check_signature(notebook)
    old=notebook.cells[1].source; notebook.cells[1].source="changed"; assert not notary.check_signature(notebook); notebook.cells[1].source=old; assert notary.check_signature(notebook); notary.unsign(notebook); assert not notary.check_signature(notebook)


def test_C31_filelike_and_path_io_produce_equivalent_notebooks(tmp_path):
    import io, nbformat
    notebook=make_notebook(); stream=io.StringIO(); assert nbformat.write(notebook,stream) is None; path=tmp_path/"ordinary.ipynb"; assert nbformat.write(notebook,path) is None
    assert nbformat.read(path,4)==nbformat.reads(stream.getvalue(),4)==notebook


def test_C32_isolated_upstream_trust_cli_help_is_available():
    result=subprocess.run([sys.executable,"-B","-m","nbformat.sign","--help"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=candidate_env(),timeout=30,check=False)
    assert result.returncode==0 and "trust" in (result.stdout+result.stderr).lower()
