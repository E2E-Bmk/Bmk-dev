"""Integration oracle tests for kedro-pipeline-fullrepro-001.

Each test crosses ≥2 public API boundaries to verify composition seams.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from kedro.config import OmegaConfigLoader
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, DatasetError, DatasetNotFoundError, MemoryDataset
from kedro.pipeline import Pipeline, node
from kedro.runner import SequentialRunner

from conftest import (
    add_one, double, to_text, sum_values, split_pair,
    make_three_step_pipeline, write_kedro_project,
    ConfirmableMemoryDataset, BrokenLoadDataset, BrokenSaveDataset,
)


# ===== Config → Catalog (state consistency seam) =====

class TestConfigCatalogSeam:
    def test_config_catalog_entry_builds_loadable_dataset(self, tmp_path):
        """Seam: state consistency — config catalog entry builds loadable DataCatalog dataset."""
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "catalog.yml").write_text(
            "answer:\n  type: MemoryDataset\n  data: 44\n", encoding="utf-8"
        )
        config = OmegaConfigLoader(str(conf), base_env="base")["catalog"]
        catalog = DataCatalog.from_config(config)
        assert catalog.load("answer") == 44

    def test_env_override_changes_dataset_value_from_config(self, tmp_path):
        """Seam: config interaction — env override changes dataset value from config loader."""
        conf = tmp_path / "config"
        (conf / "base").mkdir(parents=True)
        (conf / "local").mkdir()
        (conf / "base" / "catalog.yml").write_text(
            "seed:\n  type: MemoryDataset\n  data: 3\n", encoding="utf-8"
        )
        (conf / "local" / "catalog.yml").write_text(
            "seed:\n  type: MemoryDataset\n  data: 9\n", encoding="utf-8"
        )
        config = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local")["catalog"]
        catalog = DataCatalog.from_config(config)
        assert catalog.load("seed") == 9


# ===== Runner ↔ Pipeline ↔ Catalog (protocol handoff seams) =====

class TestRunnerPipelineCatalog:
    def test_runner_shares_catalog_state_across_dependent_nodes(self):
        """Seam: state consistency — runner shares catalog state across dependent nodes."""
        pipe = Pipeline([
            node(add_one, "seed", "middle", name="first"),
            node(double, "middle", "result", name="second"),
        ])
        result = SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(5)}))
        assert result["result"].load() == 12

    def test_runner_joins_outputs_from_parallel_branches(self):
        """Seam: protocol handoff — runner joins outputs from parallel pipeline branches."""
        pipe = Pipeline([
            node(add_one, "seed", "left", name="left"),
            node(double, "seed", "right", name="right"),
            node(sum_values, ["left", "right"], "total", name="join"),
        ])
        result = SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(4)}))
        assert result["total"].load() == 13

    def test_runner_uses_dependency_order(self):
        """Seam: protocol handoff — runner executes nodes in dependency order."""
        calls = []

        def first(v):
            calls.append("first")
            return v + 1

        def second(v):
            calls.append("second")
            return v * 2

        pipe = Pipeline([
            node(second, "mid", "out", name="second"),
            node(first, "in", "mid", name="first"),
        ])
        SequentialRunner().run(pipe, DataCatalog({"in": MemoryDataset(3)}))
        assert calls == ["first", "second"]

    def test_runner_consumes_multiple_outputs_in_later_node(self):
        """Seam: protocol handoff — runner consumes multiple upstream outputs in join node."""
        pipe = Pipeline([
            node(split_pair, "seed", ["left", "right"], name="split"),
            node(sum_values, ["left", "right"], "total", name="sum"),
        ])
        result = SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(5)}))
        assert result["total"].load() == 11


# ===== Runner ↔ Pipeline Filtering (config interaction seam) =====

class TestRunnerFiltering:
    def test_from_inputs_slice_executed_by_runner(self):
        """Seam: config interaction — from_inputs pipeline slice executed by runner."""
        selected = make_three_step_pipeline().from_inputs("clean")
        result = SequentialRunner().run(selected, DataCatalog({"clean": MemoryDataset(6)}))
        assert result["report"].load() == "12"

    def test_to_outputs_slice_executed_by_runner(self):
        """Seam: config interaction — to_outputs pipeline slice limits runner outputs."""
        selected = make_three_step_pipeline().to_outputs("model")
        result = SequentialRunner().run(selected, DataCatalog({"raw": MemoryDataset(5)}))
        assert set(result) == {"model"}
        assert result["model"].load() == 12

    def test_tag_filtered_node_executed_with_catalog_input(self):
        """Seam: config interaction — tag-filtered pipeline node executed with catalog input."""
        selected = make_three_step_pipeline().only_nodes_with_tags("train")
        result = SequentialRunner().run(selected, DataCatalog({"clean": MemoryDataset(7)}))
        assert result["model"].load() == 14

    def test_named_node_subset_in_dependency_order(self):
        """Seam: config interaction — named node subset runs in dependency order."""
        selected = make_three_step_pipeline().only_nodes("clean", "model")
        result = SequentialRunner().run(selected, DataCatalog({"raw": MemoryDataset(6)}))
        assert result["model"].load() == 14

    def test_namespace_filtered_pipeline(self):
        """Seam: config interaction — namespace filter limits runner to namespace nodes."""
        pipe = Pipeline([
            node(add_one, "seed", "middle", name="first", namespace="etl"),
            node(double, "middle", "result", name="second", namespace="etl"),
            node(to_text, "result", "report", name="third", namespace="reporting"),
        ])
        selected = pipe.only_nodes_with_namespaces(["etl"])
        result = SequentialRunner().run(selected, DataCatalog({"seed": MemoryDataset(4)}))
        assert result["result"].load() == 10


# ===== Runner Error Propagation (error propagation seam) =====

class TestRunnerErrors:
    def test_missing_free_input_prevents_execution(self):
        """Seam: error propagation — missing free input prevents node execution."""
        called = []
        pipe = Pipeline([node(lambda v: called.append(v), "missing", None, name="consumer")])
        with pytest.raises(ValueError):
            SequentialRunner().run(pipe, DataCatalog())
        assert called == []

    def test_upstream_exception_prevents_downstream(self):
        """Seam: error propagation — upstream exception prevents downstream node execution."""
        called = []

        def fail(v):
            raise RuntimeError("upstream")

        pipe = Pipeline([
            node(fail, "seed", "mid", name="fail"),
            node(lambda v: called.append(v), "mid", None, name="down"),
        ])
        with pytest.raises(RuntimeError):
            SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(1)}))
        assert called == []

    def test_save_error_prevents_downstream(self):
        """Seam: error propagation — dataset save error prevents downstream nodes."""
        called = []
        pipe = Pipeline([
            node(add_one, "seed", "middle", name="produce"),
            node(lambda v: called.append(v), "middle", None, name="down"),
        ])
        catalog = DataCatalog({"seed": MemoryDataset(1), "middle": BrokenSaveDataset()})
        with pytest.raises(DatasetError):
            SequentialRunner().run(pipe, catalog)
        assert called == []

    def test_load_error_prevents_node(self):
        """Seam: error propagation — dataset load error prevents consuming node."""
        called = []
        pipe = Pipeline([node(lambda v: called.append(v), "seed", None, name="consumer")])
        with pytest.raises(DatasetError):
            SequentialRunner().run(pipe, DataCatalog({"seed": BrokenLoadDataset()}))
        assert called == []


# ===== Runner Confirmations (lifecycle crossing seam) =====

class TestRunnerConfirmations:
    def test_runner_applies_dataset_confirmation_after_node(self):
        """Seam: lifecycle crossing — runner applies dataset confirmation after node completes."""
        audit = ConfirmableMemoryDataset("ready")
        pipe = Pipeline([node(add_one, "seed", "result", name="produce", confirms="audit")])
        SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(2), "audit": audit}))
        assert audit.confirmed is True


# ===== Config ↔ Catalog ↔ Runner (multi-seam composition) =====

class TestConfigCatalogRunner:
    def test_env_override_feeds_runner_via_config(self, tmp_path):
        """Seam: config interaction — env override feeds runner via OmegaConfigLoader parameters."""
        conf = tmp_path / "config"
        (conf / "base").mkdir(parents=True)
        (conf / "local").mkdir()
        (conf / "base" / "parameters.yml").write_text("value: 2\n", encoding="utf-8")
        (conf / "local" / "parameters.yml").write_text("value: 8\n", encoding="utf-8")
        params = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local")["parameters"]
        pipe = Pipeline([node(double, "params:value", "result", name="double")])
        result = SequentialRunner().run(pipe, DataCatalog({"params:value": MemoryDataset(params["value"])}))
        assert result["result"].load() == 16

    def test_soft_merged_config_values_feed_runner(self, tmp_path):
        """Seam: config interaction — soft-merged config values feed runner pipeline."""
        conf = tmp_path / "config"
        (conf / "base").mkdir(parents=True)
        (conf / "local").mkdir()
        (conf / "base" / "parameters.yml").write_text("values:\n  left: 3\n  right: 4\n", encoding="utf-8")
        (conf / "local" / "parameters.yml").write_text("values:\n  right: 9\n", encoding="utf-8")
        params = OmegaConfigLoader(
            str(conf), base_env="base", default_run_env="local",
            merge_strategy={"parameters": "soft"},
        )["parameters"]
        pipe = Pipeline([node(sum_values, ["left", "right"], "total", name="sum")])
        catalog = DataCatalog({
            "left": MemoryDataset(params["values"]["left"]),
            "right": MemoryDataset(params["values"]["right"]),
        })
        assert SequentialRunner().run(pipe, catalog)["total"].load() == 12

    def test_runtime_param_override_feeds_runner(self, tmp_path):
        """Seam: config interaction — runtime param override feeds runner via config loader."""
        conf = tmp_path / "config"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "parameters.yml").write_text("value: 3\n", encoding="utf-8")
        params = OmegaConfigLoader(str(conf), base_env="base", runtime_params={"value": 11})["parameters"]
        pipe = Pipeline([node(add_one, "params:value", "result", name="inc")])
        result = SequentialRunner().run(pipe, DataCatalog({"params:value": MemoryDataset(params["value"])}))
        assert result["result"].load() == 12

    def test_catalog_config_builds_runner_input(self, tmp_path):
        """Seam: state consistency — catalog config builds runner input dataset."""
        conf = tmp_path / "config"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "catalog.yml").write_text("seed:\n  type: MemoryDataset\n  data: 7\n", encoding="utf-8")
        catalog = DataCatalog.from_config(OmegaConfigLoader(str(conf), base_env="base")["catalog"])
        pipe = Pipeline([node(double, "seed", "result", name="double")])
        assert SequentialRunner().run(pipe, catalog)["result"].load() == 14


# ===== Cross-View Invariants =====

class TestCrossViewInvariants:
    def test_pipeline_inputs_match_catalog_load_keys(self):
        """CVI-N: pipeline inputs match catalog load keys across runner execution."""
        pipe = Pipeline([node(add_one, "source", "result", name="add")])
        catalog = DataCatalog({"source": MemoryDataset(5)})
        assert pipe.inputs() == {"source"}
        assert catalog.load(next(iter(pipe.inputs()))) == 5
        assert SequentialRunner().run(pipe, catalog)["result"].load() == 6

    def test_pipeline_outputs_match_catalog_saved_values(self):
        """CVI-N: pipeline outputs match catalog saved values after runner."""
        pipe = Pipeline([node(double, "source", "product", name="double")])
        catalog = DataCatalog({"source": MemoryDataset(4)})
        result = SequentialRunner().run(pipe, catalog)
        output_name = next(iter(pipe.outputs()))
        assert output_name == "product"
        assert result[output_name].load() == catalog.load(output_name) == 8

    def test_raw_assignment_cross_view_returns_memory_dataset(self):
        """CVI-N: raw catalog assignment returns MemoryDataset with consistent load."""
        catalog = DataCatalog()
        catalog["seed"] = 13
        assert isinstance(catalog["seed"], MemoryDataset)
        assert catalog.load("seed") == 13

    def test_save_load_release_share_dataset_state(self):
        """CVI-N: save, load, and release share consistent dataset state in catalog."""
        ds = MemoryDataset()
        catalog = DataCatalog({"value": ds})
        catalog.save("value", {"answer": 44})
        assert catalog["value"] is ds
        assert catalog.load("value") == {"answer": 44}
        catalog.release("value")
        with pytest.raises(DatasetError):
            catalog.load("value")

    def test_config_catalog_runner_use_same_dataset_name(self, tmp_path):
        """CVI-N: config, catalog, and runner agree on dataset name keys."""
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "catalog.yml").write_text("seed:\n  type: MemoryDataset\n  data: 9\n", encoding="utf-8")
        configured = OmegaConfigLoader(str(conf), base_env="base")["catalog"]
        catalog = DataCatalog.from_config(configured)
        pipe = Pipeline([node(add_one, "seed", "result", name="add")])
        assert set(configured) == pipe.inputs()
        assert SequentialRunner().run(pipe, catalog)["result"].load() == 10

    def test_filtered_graph_is_the_graph_executed(self):
        """CVI-N: filtered pipeline graph matches the graph actually executed by runner."""
        complete = make_three_step_pipeline()
        selected = complete.filter(tags=["prep"])
        catalog = DataCatalog({"raw": MemoryDataset(11)})
        result = SequentialRunner().run(selected, catalog)
        assert [n.name for n in selected.nodes] == ["clean"]
        assert set(result) == selected.outputs() == {"clean"}
        assert result["clean"].load() == 12


# ===== Session Execution (lifecycle crossing seam) =====

class TestSessionExecution:
    def test_bootstrap_runtime_params_drive_pipeline(self, tmp_path, monkeypatch):
        """Seam: lifecycle crossing — bootstrap runtime params drive KedroSession pipeline run."""
        marker = write_kedro_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        metadata = bootstrap_project(tmp_path)
        with KedroSession.create(project_path=tmp_path, runtime_params={"value": 6}) as session:
            result = session.run()
        assert metadata.project_path == tmp_path
        assert result["result"].load() == 14
        assert marker.read_text(encoding="utf-8") == "first:6|second:7"

    def test_session_uses_explicit_environment(self, tmp_path, monkeypatch):
        """Seam: config interaction — session explicit env selects config values for pipeline run."""
        marker = write_kedro_project(tmp_path, base_value=3, env_value=8)
        monkeypatch.chdir(tmp_path)
        bootstrap_project(tmp_path)
        with KedroSession.create(project_path=tmp_path, env="special") as session:
            result = session.run()
        assert result["result"].load() == 18
        assert marker.read_text(encoding="utf-8") == "first:8|second:9"

    def test_session_rejects_second_run(self, tmp_path, monkeypatch):
        """Seam: lifecycle crossing — KedroSession rejects second run after first completion."""
        write_kedro_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_project(tmp_path)
        with KedroSession.create(project_path=tmp_path) as session:
            session.run()
            with pytest.raises((RuntimeError, ValueError, TypeError)):
                session.run()


# ===== CLI Execution (full lifecycle seam) =====

class TestCLIExecution:
    def test_run_outside_project_exits_nonzero(self, tmp_path):
        """Seam: error propagation — CLI run outside project exits with non-zero code."""
        result = subprocess.run(
            [sys.executable, "-m", "kedro", "run"],
            cwd=tmp_path, text=True, capture_output=True,
            env={**os.environ, "KEDRO_DISABLE_TELEMETRY": "1"},
        )
        assert result.returncode != 0

    def test_run_default_pipeline_with_runtime_params(self, tmp_path):
        """Seam: lifecycle crossing — CLI run with runtime params drives pipeline execution."""
        marker = write_kedro_project(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "kedro", "run", "--params", "value=10"],
            cwd=tmp_path, text=True, capture_output=True,
            env={**os.environ, "KEDRO_DISABLE_TELEMETRY": "1"},
        )
        assert result.returncode == 0, result.stderr
        assert marker.read_text(encoding="utf-8") == "first:10|second:11"

    def test_run_pipeline_and_tag_selection(self, tmp_path):
        """Seam: config interaction — CLI pipeline and tag selection filters execution."""
        marker = write_kedro_project(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "kedro", "run", "--pipeline", "math", "--tags", "first"],
            cwd=tmp_path, text=True, capture_output=True,
            env={**os.environ, "KEDRO_DISABLE_TELEMETRY": "1"},
        )
        assert result.returncode == 0, result.stderr
        assert marker.read_text(encoding="utf-8") == "first:2"

    def test_session_bootstrap_named_pipeline_lifecycle(self, tmp_path, monkeypatch):
        """Seam: lifecycle crossing — session bootstrap and named pipeline run lifecycle."""
        marker = write_kedro_project(tmp_path, base_value=5)
        monkeypatch.chdir(tmp_path)
        metadata = bootstrap_project(tmp_path)
        with KedroSession.create(project_path=metadata.project_path) as session:
            output = session.run(pipeline_name="math")
        assert output["result"].load() == 12
        assert marker.read_text(encoding="utf-8") == "first:5|second:6"
