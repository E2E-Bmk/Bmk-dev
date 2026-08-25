from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import (
    case_root,
    declare,
    durable_content,
    durable_execution,
    durable_graph,
    durable_remote,
    init_project,
    load_yaml,
    open_repo,
    run_dvc,
    working_directory,
    write_text,
)


def _lineage(root: Path, *, name="build", data=b"durable-payload"):
    graph, graph_receipt = durable_graph(root, name)
    execution, execution_receipt = durable_execution(root, graph_receipt, f"tx-{name}")
    content, content_receipt = durable_content(root, execution_receipt, data)
    return graph, graph_receipt, execution, execution_receipt, content, content_receipt


def test_i01_native_init_closes_repo_and_control_directory_views():
    with case_root("i01") as root:
        project = root / "project"
        init_project(project)
        with open_repo(project) as repo:
            assert Path(repo.root_dir).resolve() == project
        assert (project / ".dvc" / "config").is_file()


def test_i02_native_declaration_closes_python_and_serialized_views():
    with case_root("i02") as root:
        project = root / "project"
        init_project(project)
        script = write_text(project / "assemble.py", "print('assembled')\n")
        stage = declare(project, "assemble", script, deps=("assemble.py",), outs=("artifact.bin",))
        declaration = load_yaml(project / "dvc.yaml")["stages"]["assemble"]
        assert stage.name == "assemble"
        assert declaration["deps"] == ["assemble.py"]
        assert declaration["outs"] == ["artifact.bin"]


def test_i03_native_output_conflict_preserves_prior_graph_receipt():
    with case_root("i03") as root:
        project = root / "project"
        init_project(project)
        first = write_text(project / "first.py", "print('first')\n")
        second = write_text(project / "second.py", "print('second')\n")
        declare(project, "first", first, outs=("products",))
        before = (project / "dvc.yaml").read_bytes()
        with pytest.raises(Exception):
            declare(project, "second", second, outs=("products/child",))
        assert (project / "dvc.yaml").read_bytes() == before


def test_i04_native_freeze_round_trip_closes_graph_serialization():
    with case_root("i04") as root:
        project = root / "project"
        init_project(project)
        script = write_text(project / "freeze.py", "print('freeze')\n")
        declare(project, "freeze-me", script)
        with working_directory(project):
            with open_repo(project) as repo:
                repo.freeze("freeze-me")
        assert load_yaml(project / "dvc.yaml")["stages"]["freeze-me"]["frozen"] is True
        with working_directory(project):
            with open_repo(project) as repo:
                repo.unfreeze("freeze-me")
        assert "frozen" not in load_yaml(project / "dvc.yaml")["stages"]["freeze-me"]


def test_i05_native_stage_list_closes_declaration_and_console_views():
    with case_root("i05") as root:
        project = root / "project"
        init_project(project)
        one = write_text(project / "one.py", "print('one')\n")
        two = write_text(project / "two.py", "print('two')\n")
        declare(project, "one", one)
        declare(project, "two", two)
        completed = run_dvc(project, "stage", "list")
        assert "one" in completed.stdout and "two" in completed.stdout


def test_i06_graph_generation_receipt_opens_execution_transaction():
    from dvc.durable import ExecutionJournal, GraphDeclarations

    with case_root("i06") as root:
        graph = GraphDeclarations(root)
        generation = graph.declare("index", "python index.py", outs=("index.bin",))
        journal = ExecutionJournal(root)
        prepared = journal.begin("index-17", generation)
        terminal = journal.commit("index-17")
        assert prepared["transaction"] == terminal["transaction"]
        assert terminal["graph_token"] == generation["token"]


def test_i07_execution_terminal_receipt_closes_content_ack():
    with case_root("i07") as root:
        _, graph_receipt = durable_graph(root)
        _, terminal = durable_execution(root, graph_receipt)
        content, acknowledged = durable_content(root, terminal, b"lineage-seven")
        assert acknowledged["kind"] == "ack"
        assert content.read(acknowledged) == b"lineage-seven"
        assert content.phase(acknowledged["digest"]) == "acknowledged"


def test_i08_content_ack_and_graph_generation_close_run_cache_identity():
    from dvc.durable import RunCacheResults

    with case_root("i08") as root:
        _, graph_receipt, _, _, _, content_receipt = _lineage(root, data=b"cached-eight")
        cache = RunCacheResults(root)
        stored = cache.store("stage=build|params=8", content_receipt, graph_receipt, b"result-eight")
        replayed = RunCacheResults(root).replay("stage=build|params=8", graph_receipt)
        assert stored["identity"] == replayed["receipt"]["identity"]
        assert replayed["data"] == b"result-eight"


def test_i09_content_ack_closes_remote_delivery_acknowledgement():
    with case_root("i09") as root:
        remote = root / "remote"
        _, _, _, _, _, content_receipt = _lineage(root, data=b"transfer-nine")
        outbox, acknowledged = durable_remote(root, content_receipt, remote, b"transfer-nine")
        assert acknowledged["kind"] == "ack"
        assert outbox.pending() == []
        assert Path(acknowledged["remote"]).read_bytes() == b"transfer-nine"


def test_i10_remote_ack_closes_atomic_workspace_publication():
    from dvc.durable import WorkspacePublisher

    with case_root("i10") as root:
        remote = root / "remote"
        _, _, _, _, _, content_receipt = _lineage(root)
        _, remote_receipt = durable_remote(root, content_receipt, remote)
        workspace = WorkspacePublisher(root)
        prepared = workspace.prepare("release-ten", {"result/a": "A", "result/b": "B"}, remote_receipt)
        published = workspace.publish(prepared)
        assert published["kind"] == "published"
        assert (root / "result" / "a").read_text(encoding="utf-8") == "A"
        assert workspace.visible()["publication"] == "release-ten"


def test_i11_interrupted_execution_is_adopted_only_under_same_graph_receipt():
    from dvc.durable import ExecutionJournal, ReceiptError

    with case_root("i11") as root:
        graph, generation = durable_graph(root)
        journal = ExecutionJournal(root)
        journal.begin("recover-eleven", generation)
        journal.record("recover-eleven", "first")
        journal.crash("recover-eleven")
        next_generation = graph.declare("peer", "python peer.py", outs=("peer.out",))
        with pytest.raises(ReceiptError):
            ExecutionJournal(root).adopt("recover-eleven", next_generation)
        adopted = ExecutionJournal(root).adopt("recover-eleven", generation)
        assert adopted["epoch"] == 1
        assert ExecutionJournal(root).commit("recover-eleven")["outcome"] == "committed"


def test_i12_aborted_execution_receipt_blocks_content_prepare():
    from dvc.durable import ContentLineage, ExecutionJournal, ReceiptError

    with case_root("i12") as root:
        _, generation = durable_graph(root)
        journal = ExecutionJournal(root)
        journal.begin("abort-twelve", generation)
        aborted = journal.abort("abort-twelve")
        with pytest.raises(ReceiptError):
            ContentLineage(root).prepare(b"must-not-stage", aborted)
        assert not (root / ".dvc" / "durable" / "content" / "state.json").exists()


def test_i13_graph_replacement_rejects_stale_run_cache_result():
    from dvc.durable import RunCacheResults, StaleReplay

    with case_root("i13") as root:
        graph, generation, _, _, _, content_receipt = _lineage(root)
        cache = RunCacheResults(root)
        cache.store("identity-thirteen", content_receipt, generation, b"old-result")
        newer = graph.replace("build", "python changed.py", expected_generation=generation["generation"], deps=("build.in",), outs=("build.out",))
        with pytest.raises(StaleReplay):
            RunCacheResults(root).replay("identity-thirteen", newer)


def test_i14_reopened_outbox_retries_delivery_before_ack():
    from dvc.durable import RemoteOutbox

    with case_root("i14") as root:
        remote = root / "remote"
        _, _, _, _, _, content_receipt = _lineage(root, data=b"retry-fourteen")
        first_owner = RemoteOutbox(root)
        enqueued = first_owner.enqueue(content_receipt, b"retry-fourteen")
        delivered = first_owner.deliver(enqueued, remote)
        assert RemoteOutbox(root).pending() == [enqueued["item"]]
        repeated = RemoteOutbox(root).deliver(enqueued, remote)
        assert repeated["remote"] == delivered["remote"]
        RemoteOutbox(root).acknowledge(repeated)
        assert RemoteOutbox(root).pending() == []


def test_i15_run_cache_replay_receipt_closes_workspace_publication():
    from dvc.durable import RunCacheResults, WorkspacePublisher

    with case_root("i15") as root:
        _, generation, _, _, _, content_receipt = _lineage(root)
        cache = RunCacheResults(root)
        cache.store("identity-fifteen", content_receipt, generation, b"restored-fifteen")
        replayed = cache.replay("identity-fifteen", generation)
        workspace = WorkspacePublisher(root)
        prepared = workspace.prepare("replay-fifteen", {"restored.txt": replayed["data"]}, replayed["receipt"])
        workspace.publish(prepared)
        assert (root / "restored.txt").read_bytes() == b"restored-fifteen"


def test_i16_stale_replay_cannot_open_workspace_publication():
    from dvc.durable import RunCacheResults, StaleReplay, WorkspacePublisher

    with case_root("i16") as root:
        graph, generation, _, _, _, content_receipt = _lineage(root)
        cache = RunCacheResults(root)
        cache.store("identity-sixteen", content_receipt, generation, b"stale")
        newer = graph.replace("build", "python newer.py", expected_generation=1, deps=("build.in",), outs=("build.out",))
        workspace = WorkspacePublisher(root)
        with pytest.raises(StaleReplay):
            cache.replay("identity-sixteen", newer)
        assert workspace.visible() is None and not (root / "stale.txt").exists()


def test_i17_interrupted_workspace_publication_recovers_prior_files():
    from dvc.durable import PublicationError, WorkspacePublisher

    with case_root("i17") as root:
        remote = root / "remote"
        write_text(root / "one.txt", "old-one")
        write_text(root / "two.txt", "old-two")
        _, _, _, _, _, content_receipt = _lineage(root)
        _, remote_receipt = durable_remote(root, content_receipt, remote)
        workspace = WorkspacePublisher(root)
        prepared = workspace.prepare("recover-seventeen", {"one.txt": "new-one", "two.txt": "new-two"}, remote_receipt)
        with pytest.raises(PublicationError):
            workspace.publish(prepared, interrupt_after=1)
        WorkspacePublisher(root).recover("recover-seventeen")
        assert (root / "one.txt").read_text(encoding="utf-8") == "old-one"
        assert (root / "two.txt").read_text(encoding="utf-8") == "old-two"
        assert WorkspacePublisher(root).visible() is None


def test_i18_two_execution_owners_close_independent_terminal_receipts():
    from dvc.durable import ExecutionJournal

    with case_root("i18") as root:
        _, generation = durable_graph(root)
        journal = ExecutionJournal(root)
        journal.begin("left-eighteen", generation)
        journal.begin("right-eighteen", generation)
        left = journal.commit("left-eighteen")
        right = journal.commit("right-eighteen")
        reopened = ExecutionJournal(root)
        assert left["token"] != right["token"]
        assert reopened.status("left-eighteen")["state"] == "committed"
        assert reopened.status("right-eighteen")["state"] == "committed"

