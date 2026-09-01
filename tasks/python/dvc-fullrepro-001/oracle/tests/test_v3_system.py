from __future__ import annotations

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
    write_text,
)


def _copy_script(path: Path, source: str, output: str, suffix: str) -> Path:
    return write_text(
        path,
        "from pathlib import Path\n"
        f"Path({output!r}).write_text(Path({source!r}).read_text(encoding='utf-8')+{suffix!r}, encoding='utf-8')\n",
    )


def _durable_chain(root: Path, data=b"system-payload"):
    graph, generation = durable_graph(root)
    execution, terminal = durable_execution(root, generation)
    content, content_ack = durable_content(root, terminal, data)
    return graph, generation, execution, terminal, content, content_ack


def test_s01_native_pipeline_closes_graph_lock_cache_workspace_and_status():
    with case_root("s01") as root:
        project = root / "project"
        init_project(project)
        write_text(project / "input.txt", "native-seed")
        first = _copy_script(project / "first.py", "input.txt", "middle.txt", "|first")
        second = _copy_script(project / "second.py", "middle.txt", "output.txt", "|second")
        declare(project, "first", first, deps=("input.txt", "first.py"), outs=("middle.txt",))
        declare(project, "second", second, deps=("middle.txt", "second.py"), outs=("output.txt",))
        run_dvc(project, "repro", "second")
        assert (project / "output.txt").read_text(encoding="utf-8") == "native-seed|first|second"
        assert set(load_yaml(project / "dvc.lock")["stages"]) == {"first", "second"}
        with open_repo(project) as repo:
            assert repo.status() == {}


def test_s02_all_durable_owners_close_one_visible_publication():
    from dvc.durable import RemoteOutbox, RunCacheResults, WorkspacePublisher

    with case_root("s02") as root:
        remote = root / "remote"
        _, generation, _, _, _, content_ack = _durable_chain(root, b"system-two")
        cache = RunCacheResults(root)
        cache.store("system-two", content_ack, generation, b"system-two")
        replay = RunCacheResults(root).replay("system-two", generation)
        outbox = RemoteOutbox(root)
        queued = outbox.enqueue(content_ack, replay["data"])
        delivered = outbox.deliver(queued, remote)
        transfer_ack = RemoteOutbox(root).acknowledge(delivered)
        workspace = WorkspacePublisher(root)
        prepared = workspace.prepare("system-two", {"published/result.bin": replay["data"]}, transfer_ack)
        workspace.publish(prepared)
        assert WorkspacePublisher(root).visible()["publication"] == "system-two"
        assert (root / "published" / "result.bin").read_bytes() == b"system-two"


def test_s03_new_graph_generation_propagates_stale_replay_without_workspace_change():
    from dvc.durable import RunCacheResults, StaleReplay, WorkspacePublisher

    with case_root("s03") as root:
        graph, generation, _, _, _, content_ack = _durable_chain(root, b"system-three")
        cache = RunCacheResults(root)
        cache.store("system-three", content_ack, generation, b"obsolete")
        newer = graph.replace("build", "python rebuild.py", expected_generation=1, deps=("build.in",), outs=("build.out",))
        with pytest.raises(StaleReplay):
            RunCacheResults(root).replay("system-three", newer)
        assert WorkspacePublisher(root).visible() is None
        assert not (root / "published.bin").exists()


def test_s04_crash_adoption_reopens_then_closes_content_transfer_and_workspace():
    from dvc.durable import ContentLineage, ExecutionJournal, RemoteOutbox, WorkspacePublisher

    with case_root("s04") as root:
        remote = root / "remote"
        _, generation = durable_graph(root)
        journal = ExecutionJournal(root)
        journal.begin("system-four", generation)
        journal.record("system-four", "produce", "partial")
        journal.crash("system-four")
        reopened = ExecutionJournal(root)
        reopened.adopt("system-four", generation)
        terminal = reopened.commit("system-four")
        content = ContentLineage(root)
        prepared = content.prepare(b"recovered-four", terminal)
        content_ack = ContentLineage(root).acknowledge(ContentLineage(root).publish(prepared))
        outbox = RemoteOutbox(root)
        queued = outbox.enqueue(content_ack, b"recovered-four")
        transfer_ack = RemoteOutbox(root).acknowledge(RemoteOutbox(root).deliver(queued, remote))
        workspace = WorkspacePublisher(root)
        workspace.publish(workspace.prepare("system-four", {"four.bin": b"recovered-four"}, transfer_ack))
        assert (root / "four.bin").read_bytes() == b"recovered-four"


def test_s05_unacknowledged_delivery_blocks_visibility_until_receipt_closes():
    from dvc.durable import ReceiptError, RemoteOutbox, WorkspacePublisher

    with case_root("s05") as root:
        remote = root / "remote"
        _, _, _, _, _, content_ack = _durable_chain(root, b"system-five")
        outbox = RemoteOutbox(root)
        queued = outbox.enqueue(content_ack, b"system-five")
        delivered = outbox.deliver(queued, remote)
        workspace = WorkspacePublisher(root)
        with pytest.raises(ReceiptError):
            workspace.prepare("system-five", {"five.bin": b"system-five"}, delivered)
        assert workspace.visible() is None
        transfer_ack = RemoteOutbox(root).acknowledge(delivered)
        workspace.publish(workspace.prepare("system-five", {"five.bin": b"system-five"}, transfer_ack))
        assert (root / "five.bin").read_bytes() == b"system-five"


def test_s06_partial_workspace_failure_recovers_then_new_receipt_publishes():
    from dvc.durable import PublicationError, WorkspacePublisher

    with case_root("s06") as root:
        remote = root / "remote"
        write_text(root / "left.bin", "old-left")
        write_text(root / "right.bin", "old-right")
        _, _, _, _, _, content_ack = _durable_chain(root, b"system-six")
        _, transfer_ack = durable_remote(root, content_ack, remote, b"system-six")
        workspace = WorkspacePublisher(root)
        first = workspace.prepare("system-six-failed", {"left.bin": "new-left", "right.bin": "new-right"}, transfer_ack)
        with pytest.raises(PublicationError):
            workspace.publish(first, interrupt_after=1)
        WorkspacePublisher(root).recover("system-six-failed")
        assert (root / "left.bin").read_text(encoding="utf-8") == "old-left"
        second = WorkspacePublisher(root).prepare("system-six-good", {"left.bin": "new-left", "right.bin": "new-right"}, transfer_ack)
        WorkspacePublisher(root).publish(second)
        assert (root / "left.bin").read_text(encoding="utf-8") == "new-left"
        assert (root / "right.bin").read_text(encoding="utf-8") == "new-right"


def test_s07_aborted_transaction_propagates_without_downstream_owner_state():
    from dvc.durable import ContentLineage, ExecutionJournal, ReceiptError, RemoteOutbox, WorkspacePublisher

    with case_root("s07") as root:
        _, generation = durable_graph(root)
        journal = ExecutionJournal(root)
        journal.begin("system-seven", generation)
        aborted = journal.abort("system-seven")
        with pytest.raises(ReceiptError):
            ContentLineage(root).prepare(b"forbidden", aborted)
        assert RemoteOutbox(root).pending() == []
        assert WorkspacePublisher(root).visible() is None
        assert not (root / ".dvc" / "durable" / "content" / "state.json").exists()


def test_s08_latest_lineage_publishes_while_prior_generation_stays_stale():
    from dvc.durable import RunCacheResults, StaleReplay, WorkspacePublisher

    with case_root("s08") as root:
        graph, first_generation, _, _, _, first_content = _durable_chain(root, b"first-eight")
        cache = RunCacheResults(root)
        cache.store("system-eight-old", first_content, first_generation, b"first-eight")
        second_generation = graph.replace("build", "python second.py", expected_generation=1, deps=("build.in",), outs=("build.out",))
        _, second_terminal = durable_execution(root, second_generation, "tx-system-eight-new")
        _, second_content = durable_content(root, second_terminal, b"second-eight")
        cache.store("system-eight-new", second_content, second_generation, b"second-eight")
        with pytest.raises(StaleReplay):
            cache.replay("system-eight-old", second_generation)
        latest = cache.replay("system-eight-new", second_generation)
        workspace = WorkspacePublisher(root)
        workspace.publish(workspace.prepare("system-eight", {"eight.bin": latest["data"]}, latest["receipt"]))
        assert (root / "eight.bin").read_bytes() == b"second-eight"


def test_s09_two_outbox_items_require_independent_acknowledgements():
    from dvc.durable import ReceiptError, RemoteOutbox, WorkspacePublisher

    with case_root("s09") as root:
        remote = root / "remote"
        _, _, _, _, _, content_ack = _durable_chain(root, b"system-nine")
        outbox = RemoteOutbox(root)
        first = outbox.enqueue(content_ack, b"first-nine")
        second = outbox.enqueue(content_ack, b"second-nine")
        first_ack = outbox.acknowledge(outbox.deliver(first, remote))
        second_delivery = outbox.deliver(second, remote)
        workspace = WorkspacePublisher(root)
        workspace.publish(workspace.prepare("first-nine", {"first-nine.bin": b"first-nine"}, first_ack))
        with pytest.raises(ReceiptError):
            workspace.prepare("second-nine", {"second-nine.bin": b"second-nine"}, second_delivery)
        assert outbox.pending() == [second["item"]]
        second_ack = RemoteOutbox(root).acknowledge(second_delivery)
        WorkspacePublisher(root).publish(WorkspacePublisher(root).prepare("second-nine", {"second-nine.bin": b"second-nine"}, second_ack))
        assert (root / "second-nine.bin").read_bytes() == b"second-nine"


def test_s10_every_owner_reopens_and_preserves_receipt_chain():
    from dvc.durable import ContentLineage, ExecutionJournal, GraphDeclarations, RemoteOutbox, RunCacheResults, WorkspacePublisher

    with case_root("s10") as root:
        remote = root / "remote"
        graph = GraphDeclarations(root)
        generation = graph.declare("reopen", "python reopen.py", outs=("reopen.bin",))
        generation = GraphDeclarations(root).receipt()
        execution = ExecutionJournal(root)
        execution.begin("system-ten", generation)
        execution.crash("system-ten")
        ExecutionJournal(root).adopt("system-ten", generation)
        terminal = ExecutionJournal(root).commit("system-ten")
        prepared = ContentLineage(root).prepare(b"system-ten", terminal)
        published = ContentLineage(root).publish(prepared)
        content_ack = ContentLineage(root).acknowledge(published)
        cache = RunCacheResults(root)
        cache.store("system-ten", content_ack, generation, b"system-ten")
        replay = RunCacheResults(root).replay("system-ten", generation)
        queued = RemoteOutbox(root).enqueue(content_ack, replay["data"])
        delivered = RemoteOutbox(root).deliver(queued, remote)
        transfer_ack = RemoteOutbox(root).acknowledge(delivered)
        workspace = WorkspacePublisher(root)
        prepared_workspace = workspace.prepare("system-ten", {"ten.bin": replay["data"]}, transfer_ack)
        WorkspacePublisher(root).publish(prepared_workspace)
        assert WorkspacePublisher(root).visible()["publication"] == "system-ten"
        assert (root / "ten.bin").read_bytes() == b"system-ten"
