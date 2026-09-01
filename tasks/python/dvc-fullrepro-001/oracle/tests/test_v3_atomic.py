from __future__ import annotations

import inspect
import os
from pathlib import Path

import pytest

from conftest import case_root, declare, init_project, open_repo, write_text


def test_a01_public_package_metadata_is_typed():
    import dvc

    assert isinstance(dvc.__version__, str) and dvc.__version__
    assert isinstance(dvc.version_tuple, tuple) and len(dvc.version_tuple) >= 2


def test_a02_repository_projects_canonical_root():
    from dvc.repo import Repo

    with case_root("a02") as root:
        root.mkdir(exist_ok=True)
        with Repo(os.fspath(root), uninitialized=True) as repo:
            assert Path(repo.root_dir).resolve() == root


def test_a03_public_data_filesystem_reads_caller_content():
    from dvc.api import DVCFileSystem

    with case_root("a03") as root:
        project = root / "project"
        init_project(project)
        write_text(project / "visible.txt", "native-public-data")
        filesystem = DVCFileSystem(url=os.fspath(project))
        try:
            with filesystem.open("visible.txt", "r", encoding="utf-8") as stream:
                assert stream.read() == "native-public-data"
        finally:
            filesystem.close()


def test_a04_remote_failure_category_is_public_and_exact():
    from dvc.config import NoRemoteError, RemoteConfigError

    with case_root("a04") as root:
        project = root / "project"
        init_project(project)
        with open_repo(project) as repo:
            with pytest.raises(NoRemoteError) as captured:
                repo.cloud.get_remote()
        assert type(captured.value) is NoRemoteError
        assert issubclass(NoRemoteError, RemoteConfigError)


def test_a05_reproduction_exposes_native_selection_controls():
    from dvc.repo import Repo

    parameters = inspect.signature(Repo.reproduce).parameters
    assert {"targets", "recursive", "pipeline", "downstream", "single_item"} <= set(parameters)
    with case_root("a05") as root:
        project = root / "project"
        init_project(project)
        with open_repo(project) as repo:
            assert repo.reproduce(all_pipelines=True, dry=True) == []


def test_a06_native_stage_declaration_exposes_public_name():
    with case_root("a06") as root:
        project = root / "project"
        init_project(project)
        script = write_text(project / "native.py", "print('native')\n")
        stage = declare(project, "native", script)
        assert stage.name == "native"
        assert callable(stage.reproduce)


def test_a07_graph_declarations_advance_append_only_generation():
    from dvc.durable import GraphDeclarations

    with case_root("a07") as root:
        graph = GraphDeclarations(root)
        first = graph.declare("shape", "python shape.py", deps=("z", "a"), outs=("result",))
        second = graph.declare("report", "python report.py", deps=("result",), outs=("report",))
        view = graph.view()
        assert first["generation"] == 1 and second["generation"] == 2
        assert [event["generation"] for event in view["events"]] == [1, 2]
        assert view["stages"]["shape"]["deps"] == ["a", "z"]


def test_a08_graph_replacement_requires_current_fence():
    from dvc.durable import FenceConflict, GraphDeclarations

    with case_root("a08") as root:
        graph = GraphDeclarations(root)
        first = graph.declare("train", "python old.py", outs=("model",))
        before = graph.view()
        with pytest.raises(FenceConflict):
            graph.replace("train", "python stale.py", expected_generation=first["generation"] - 1, outs=("model",))
        assert graph.view() == before
        replaced = graph.replace("train", "python fresh.py", expected_generation=first["generation"], outs=("model",))
        assert replaced["generation"] == 2


def test_a09_execution_journal_rejects_unattested_plan():
    from dvc.durable import ExecutionJournal, ReceiptError

    with case_root("a09") as root:
        journal = ExecutionJournal(root)
        with pytest.raises(ReceiptError):
            journal.begin("unattested", {"owner": "graph", "kind": "generation", "token": "invented"})
        assert not (root / ".dvc" / "durable" / "execution" / "journal.json").exists()


def test_a10_content_prepare_requires_committed_execution():
    from dvc.durable import ContentLineage, ReceiptError

    with case_root("a10") as root:
        lineage = ContentLineage(root)
        with pytest.raises(ReceiptError):
            lineage.prepare(b"uncommitted", {"owner": "execution", "kind": "terminal", "outcome": "aborted", "token": "invented"})
        assert not (root / ".dvc" / "durable" / "content" / "state.json").exists()


def test_a11_run_cache_replay_rejects_unknown_identity():
    from dvc.durable import ReceiptError, RunCacheResults

    with case_root("a11") as root:
        cache = RunCacheResults(root)
        with pytest.raises(ReceiptError):
            cache.replay("never-stored", {"owner": "graph", "kind": "generation", "token": "invented"})


def test_a12_remote_outbox_starts_empty_and_rejects_unacked_content():
    from dvc.durable import ReceiptError, RemoteOutbox

    with case_root("a12") as root:
        outbox = RemoteOutbox(root)
        assert outbox.pending() == []
        with pytest.raises(ReceiptError):
            outbox.enqueue({"owner": "content", "kind": "published", "token": "invented"}, b"payload")


def test_a13_workspace_publication_requires_closing_receipt():
    from dvc.durable import ReceiptError, WorkspacePublisher

    with case_root("a13") as root:
        workspace = WorkspacePublisher(root)
        assert workspace.visible() is None
        with pytest.raises(ReceiptError):
            workspace.prepare("unclosed", {"out.txt": b"x"}, {"owner": "content", "kind": "ack", "token": "invented"})


def test_a14_durable_failures_have_distinct_public_categories():
    from dvc.durable import DurableError, FenceConflict, PublicationError, ReceiptError, StaleReplay

    assert all(issubclass(error, DurableError) for error in (FenceConflict, PublicationError, ReceiptError, StaleReplay))
    assert len({FenceConflict, PublicationError, ReceiptError, StaleReplay}) == 4

