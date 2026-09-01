from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from conftest import candidate_env, dependencies, make_notebook


def test_A01_durable_lease_is_visible_to_an_independent_process(tmp_path):
    from nbformat.durable_store import DurableStore
    store=DurableStore(tmp_path/"lease.db"); lease=store.acquire("parent")
    code="from nbformat.durable_store import DurableStore,LeaseBusy;import sys\ntry: DurableStore(sys.argv[1]).acquire('child')\nexcept LeaseBusy: raise SystemExit(23)\nraise SystemExit(0)"
    result=subprocess.run([sys.executable,"-B","-c",code,str(store.path)],env=candidate_env(),timeout=20,check=False)
    assert result.returncode==23
    lease.rollback()


def test_A02_crashed_process_lease_requires_tokened_adoption(tmp_path):
    from nbformat.durable_store import DurableStore, LeaseOwnershipError
    database=tmp_path/"crash.db"; token_file=tmp_path/"token.txt"
    code="from nbformat.durable_store import DurableStore;import pathlib,sys\nl=DurableStore(sys.argv[1]).acquire('departed');pathlib.Path(sys.argv[2]).write_text(l.token,encoding='utf-8')"
    assert subprocess.run([sys.executable,"-B","-c",code,str(database),str(token_file)],env=candidate_env(),timeout=20,check=False).returncode==0
    reopened=DurableStore(database)
    with pytest.raises(LeaseOwnershipError): reopened.adopt_orphan("wrong","recovery")
    receipt=reopened.adopt_orphan(token_file.read_text(encoding="utf-8"),"recovery").commit({"restored":True})
    assert receipt["adopted"] is True and receipt["generation"]==1


def test_A03_store_generation_and_history_are_append_only(tmp_path):
    from nbformat.durable_store import DurableStore, GenerationConflict
    store=DurableStore(tmp_path/"history.db")
    first=store.acquire("alpha",expected_generation=0).commit({"n":1})
    with pytest.raises(GenerationConflict): store.acquire("stale",expected_generation=0)
    second=store.acquire("beta",expected_generation=1).commit({"n":2},parents=[first["receipt_id"]])
    assert [x["generation"] for x in store.history()]==[1,2] and second["parents"]==[first["receipt_id"]]


def test_A04_lineage_acknowledgement_replays_identically_after_reopen(tmp_path):
    from nbformat.lineage import LineageJournal
    path=tmp_path/"lineage.db"; journal=LineageJournal(path)
    prepared=journal.prepare("convert-a",input_digest="in-31",output_digest="out-47")
    acknowledged=journal.acknowledge(prepared)
    assert LineageJournal(path).replay("convert-a")==acknowledged
    assert LineageJournal(path).acknowledge(prepared)==acknowledged


def test_A05_lineage_rollback_is_terminal_and_durable(tmp_path):
    from nbformat.lineage import LineageJournal, LineageStateError
    path=tmp_path/"rollback.db"; journal=LineageJournal(path)
    prepared=journal.prepare("convert-b",input_digest="x",output_digest="y")
    rolled=journal.rollback("convert-b",reason="projection rejected")
    with pytest.raises(LineageStateError): LineageJournal(path).acknowledge(prepared)
    assert rolled["kind"]=="lineage-rollback" and len(LineageJournal(path).history())==2


def test_A06_trust_generation_and_signature_survive_reopen(tmp_path):
    from nbformat.trust_receipts import TrustLedger
    deps=dependencies(tmp_path,label="trust-a"); path=tmp_path/"trust-a-trust.db"
    reopened=TrustLedger(path)
    assert reopened.check(deps["notebook"],deps["signed"]) is True
    changed=copy.deepcopy(deps["notebook"]); changed.cells[0].source="changed"
    assert reopened.check(changed,deps["signed"]) is False


def test_A07_retired_key_generation_does_not_authorize_after_reopen(tmp_path):
    from nbformat.trust_receipts import TrustLedger
    deps=dependencies(tmp_path,label="retire"); ledger=deps["trust"]
    retirement=ledger.retire("key-retire",1)
    assert TrustLedger(tmp_path/"retire-trust.db").check(deps["notebook"],deps["signed"]) is False
    assert retirement["parents"]==[deps["generation"]["receipt_id"]]


def test_A08_artifact_prepare_visibility_and_ack_are_distinct(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="artifact-a"); destination=tmp_path/"release.json"; publisher=ArtifactPublication(destination)
    prepared=publisher.prepare(deps["notebook"],audit={"kind":"survey"},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]])
    assert not destination.exists()
    visible=publisher.make_visible(prepared)
    assert json.loads(destination.read_text(encoding="utf-8"))["publication"]["acknowledged"] is False
    ack=publisher.acknowledge(visible)
    assert json.loads(destination.read_text(encoding="utf-8"))["publication"]["acknowledged"] is True and ack["kind"]=="artifact-ack"


def test_A09_artifact_expected_revision_is_rechecked_after_prepare(tmp_path):
    from nbformat.artifact import ArtifactPublication, ArtifactRevisionConflict
    deps=dependencies(tmp_path,label="artifact-b"); destination=tmp_path/"revision.json"; pub=ArtifactPublication(destination)
    first=pub.prepare(deps["notebook"],audit={},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]],expected_revision=0)
    contender=pub.prepare(deps["notebook"],audit={"second":True},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]],expected_revision=0)
    pub.acknowledge(pub.make_visible(first)); before=destination.read_bytes()
    with pytest.raises(ArtifactRevisionConflict): pub.make_visible(contender)
    assert destination.read_bytes()==before


def test_A10_artifact_recovery_handles_prepared_and_visible_unacked_states(tmp_path):
    from nbformat.artifact import ArtifactPublication
    deps=dependencies(tmp_path,label="artifact-c"); destination=tmp_path/"recover.json"; pub=ArtifactPublication(destination)
    prepared=pub.prepare(deps["notebook"],audit={"recover":1},dependency_receipts=[deps["store_receipt"],deps["lineage_ack"],deps["signed"]])
    ack=ArtifactPublication(destination).recover(prepared["prepare_id"])
    assert ack["kind"]=="artifact-ack"
    deps2=dependencies(tmp_path,label="artifact-d"); pub2=ArtifactPublication(destination)
    prepared2=pub2.prepare(deps2["notebook"],audit={"recover":2},dependency_receipts=[deps2["store_receipt"],deps2["lineage_ack"],deps2["signed"]],expected_revision=1)
    visible=pub2.make_visible(prepared2)
    assert ArtifactPublication(destination).recover(prepared2["prepare_id"])["parents"]==[visible["receipt_id"]]


def test_A11_notebooknode_attribute_mapping_and_recursive_conversion():
    import nbformat
    node=nbformat.from_dict({"outer":[{"value":31}]}); node.answer=47
    assert node["answer"]==47 and node.outer[0].value==31
    with pytest.raises(AttributeError): _=node.absent


def test_A12_v4_constructors_validate_and_do_not_share_mutable_defaults():
    import nbformat
    from nbformat import v4
    first,second=v4.new_code_cell("a"),v4.new_code_cell("b"); first.metadata["owner"]="one"; first.outputs.append(v4.new_output("stream",name="stdout",text="a\n"))
    notebook=v4.new_notebook(cells=[first,second]); assert nbformat.validate(notebook) is None and second.metadata=={} and second.outputs==[]


def test_A13_reads_writes_roundtrip_bytes_and_text_without_input_mutation():
    import nbformat
    notebook=make_notebook(); before=copy.deepcopy(notebook); text=nbformat.writes(notebook)
    assert nbformat.reads(text,4)==notebook and nbformat.reads(text.encode(),4)==notebook and notebook==before


def test_A14_validation_failure_is_public_and_nonmutating():
    import nbformat
    notebook=make_notebook(); del notebook.cells[0]["source"]; before=copy.deepcopy(notebook)
    with pytest.raises(nbformat.ValidationError): nbformat.validate(notebook)
    assert notebook==before


def test_A15_normalize_returns_repaired_copy_for_duplicate_ids():
    import nbformat
    from nbformat.validator import normalize
    notebook=make_notebook(); notebook.cells[1].id=notebook.cells[0].id; before=copy.deepcopy(notebook)
    with pytest.warns(nbformat.warnings.DuplicateCellId): changes,normalized=normalize(notebook)
    assert changes==1 and notebook==before and len({x.id for x in normalized.cells})==len(normalized.cells)


def test_A16_convert_same_major_returns_same_object():
    import nbformat
    notebook=make_notebook(); assert nbformat.convert(notebook,4) is notebook


def test_A17_legacy_v3_upgrade_preserves_sources_and_stream_output():
    import nbformat
    legacy=nbformat.v3.new_notebook(worksheets=[nbformat.v3.new_worksheet(cells=[nbformat.v3.new_code_cell("depth = 23",prompt_number=2,outputs=[nbformat.v3.new_output("stream",output_text="23\n")])])])
    upgraded=nbformat.convert(legacy,4); assert upgraded.cells[0].source=="depth = 23" and upgraded.cells[0].outputs[0].text=="23\n"


def test_A18_upstream_memory_signature_store_supports_store_check_remove():
    from nbformat.sign import MemorySignatureStore
    store=MemorySignatureStore(); store.store_signature("digest-a","sha256"); assert store.check_signature("digest-a","sha256")
    store.remove_signature("digest-a","sha256"); assert not store.check_signature("digest-a","sha256")


def test_A19_upstream_sqlite_signature_store_survives_reopen(tmp_path):
    from nbformat.sign import SQLiteSignatureStore
    path=tmp_path/"native.db"; first=SQLiteSignatureStore(db_file=str(path)); first.store_signature("digest-b","sha256"); first.close()
    second=SQLiteSignatureStore(db_file=str(path)); assert second.check_signature("digest-b","sha256"); second.close()


def test_A20_reader_distinguishes_invalid_json_and_unsupported_version():
    import nbformat
    with pytest.raises(nbformat.reader.NotJSONError): nbformat.reads("not-json",4)
    with pytest.raises(nbformat.NBFormatError): nbformat.reads(json.dumps({"nbformat":91,"nbformat_minor":0,"metadata":{},"cells":[]}),nbformat.NO_CONVERT)
