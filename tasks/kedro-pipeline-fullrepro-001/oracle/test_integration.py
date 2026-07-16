# Spec2Repo oracle - integration tests for kedro-pipeline-fullrepro-001
from __future__ import annotations

import os

import pytest

from kedro.config import MissingConfigException, OmegaConfigLoader
from kedro.io import (
    AbstractDataset,
    DataCatalog,
    DatasetError,
    DatasetNotFoundError,
    MemoryDataset,
)
from kedro.pipeline import GroupedNodes, Node, Pipeline, node, pipeline
from kedro.runner import SequentialRunner


os.environ.setdefault("KEDRO_DISABLE_TELEMETRY", "1")


def _add_one(x):
    return x + 1


def _double(x):
    return x * 2


def _to_text(x):
    return str(x)


def _sum_values(a, b):
    return a + b


def _split_pair(x):
    return x, x + 1


def _return_mapping(x):
    return {"left": x, "right": x + 1}


def _make_basic_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(_add_one, "raw", "clean", name="clean", tags="prep"),
            node(_double, "clean", "model", name="model", tags="train"),
            node(_to_text, "model", "report", name="report", tags={"report"}),
        ]
    )

class ConfirmableMemoryDataset(MemoryDataset):
    def __init__(self, data=None):
        super().__init__(data)
        self.confirmed = False

    def confirm(self):
        self.confirmed = True


class BrokenLoadDataset(AbstractDataset):
    def _load(self):
        raise RuntimeError("boom")

    def _save(self, data):
        self.data = data

    def _describe(self):
        return {}


class BrokenSaveDataset(AbstractDataset):
    def _load(self):
        return None

    def _save(self, data):
        raise RuntimeError("save failed")

    def _describe(self):
        return {}


def test_config_catalog_projection_builds_loadable_dataset(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "catalog.yml").write_text("answer:\n  type: MemoryDataset\n  data: 42\n", encoding="utf-8")
    config = OmegaConfigLoader(str(conf), base_env="base")["catalog"]
    catalog = DataCatalog.from_config(config)
    assert catalog.load("answer") == 42


def test_runner_shares_catalog_state_across_dependent_nodes():
    pipe = Pipeline([node(_add_one, "seed", "middle", name="first"), node(_double, "middle", "result", name="second")])
    result = SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(4)}))
    assert result["result"].load() == 10


def test_runner_joins_outputs_from_parallel_branches():
    pipe = Pipeline(
        [
            node(_add_one, "seed", "left", name="left"),
            node(_double, "seed", "right", name="right"),
            node(_sum_values, ["left", "right"], "total", name="join"),
        ]
    )
    result = SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(3)}))
    assert result["total"].load() == 10


def test_runner_uses_dependency_order_instead_of_declaration_order():
    calls = []

    def first(value):
        calls.append("first")
        return value + 1

    def second(value):
        calls.append("second")
        return value * 2

    pipe = Pipeline([node(second, "middle", "result", name="second"), node(first, "seed", "middle", name="first")])
    SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(2)}))
    assert calls == ["first", "second"]


def test_runner_executes_pipeline_slice_from_selected_input():
    selected = _make_basic_pipeline().from_inputs("clean")
    result = SequentialRunner().run(selected, DataCatalog({"clean": MemoryDataset(5)}))
    assert result["report"].load() == "10"


def test_runner_executes_pipeline_slice_to_selected_output():
    selected = _make_basic_pipeline().to_outputs("model")
    result = SequentialRunner().run(selected, DataCatalog({"raw": MemoryDataset(4)}))
    assert set(result) == {"model"}
    assert result["model"].load() == 10


def test_runner_executes_tag_filtered_node_with_catalog_input():
    selected = _make_basic_pipeline().only_nodes_with_tags("train")
    result = SequentialRunner().run(selected, DataCatalog({"clean": MemoryDataset(6)}))
    assert result["model"].load() == 12


def test_runner_executes_named_node_subset_in_dependency_order():
    selected = _make_basic_pipeline().only_nodes("clean", "model")
    result = SequentialRunner().run(selected, DataCatalog({"raw": MemoryDataset(5)}))
    assert result["model"].load() == 12


def test_runner_executes_namespace_filtered_pipeline():
    pipe = Pipeline(
        [
            node(_add_one, "seed", "middle", name="first", namespace="etl"),
            node(_double, "middle", "result", name="second", namespace="etl"),
            node(_to_text, "result", "report", name="third", namespace="reporting"),
        ]
    )
    selected = pipe.only_nodes_with_namespaces(["etl"])
    result = SequentialRunner().run(selected, DataCatalog({"seed": MemoryDataset(3)}))
    assert result["result"].load() == 8


def test_runner_missing_free_input_prevents_node_execution():
    called = []
    pipe = Pipeline([node(lambda value: called.append(value), "missing", None, name="consumer")])
    with pytest.raises(ValueError):
        SequentialRunner().run(pipe, DataCatalog())
    assert called == []


def test_runner_upstream_error_prevents_downstream_execution():
    called = []

    def fail(value):
        raise RuntimeError("upstream failed")

    pipe = Pipeline([node(fail, "seed", "middle", name="fail"), node(lambda value: called.append(value), "middle", None, name="downstream")])
    with pytest.raises(RuntimeError, match="upstream failed"):
        SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(1)}))
    assert called == []


def test_runner_save_error_prevents_downstream_execution():
    called = []
    pipe = Pipeline([node(_add_one, "seed", "middle", name="produce"), node(lambda value: called.append(value), "middle", None, name="downstream")])
    catalog = DataCatalog({"seed": MemoryDataset(1), "middle": BrokenSaveDataset()})
    with pytest.raises(DatasetError):
        SequentialRunner().run(pipe, catalog)
    assert called == []


def test_runner_load_error_prevents_node_execution():
    called = []
    pipe = Pipeline([node(lambda value: called.append(value), "seed", None, name="consumer")])
    with pytest.raises(DatasetError):
        SequentialRunner().run(pipe, DataCatalog({"seed": BrokenLoadDataset()}))
    assert called == []


def test_environment_override_changes_runner_input(tmp_path):
    conf = tmp_path / "config"
    (conf / "base").mkdir(parents=True)
    (conf / "local").mkdir()
    (conf / "base" / "parameters.yml").write_text("value: 2\n", encoding="utf-8")
    (conf / "local" / "parameters.yml").write_text("value: 7\n", encoding="utf-8")
    params = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local")["parameters"]
    pipe = Pipeline([node(_double, "params:value", "result", name="double")])
    result = SequentialRunner().run(pipe, DataCatalog({"params:value": MemoryDataset(params["value"])}))
    assert result["result"].load() == 14


def test_soft_merged_config_values_feed_runner(tmp_path):
    conf = tmp_path / "config"
    (conf / "base").mkdir(parents=True)
    (conf / "local").mkdir()
    (conf / "base" / "parameters.yml").write_text("values:\n  left: 2\n  right: 3\n", encoding="utf-8")
    (conf / "local" / "parameters.yml").write_text("values:\n  right: 8\n", encoding="utf-8")
    params = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local", merge_strategy={"parameters": "soft"})["parameters"]
    pipe = Pipeline([node(_sum_values, ["left", "right"], "total", name="sum")])
    catalog = DataCatalog({"left": MemoryDataset(params["values"]["left"]), "right": MemoryDataset(params["values"]["right"])})
    assert SequentialRunner().run(pipe, catalog)["total"].load() == 10


def test_runtime_parameter_override_feeds_runner(tmp_path):
    conf = tmp_path / "config"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "parameters.yml").write_text("value: 2\n", encoding="utf-8")
    params = OmegaConfigLoader(str(conf), base_env="base", runtime_params={"value": 9})["parameters"]
    pipe = Pipeline([node(_add_one, "params:value", "result", name="increment")])
    result = SequentialRunner().run(pipe, DataCatalog({"params:value": MemoryDataset(params["value"])}))
    assert result["result"].load() == 10


def test_catalog_configuration_builds_runner_input(tmp_path):
    conf = tmp_path / "config"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "catalog.yml").write_text("seed:\n  type: MemoryDataset\n  data: 6\n", encoding="utf-8")
    catalog = DataCatalog.from_config(OmegaConfigLoader(str(conf), base_env="base")["catalog"])
    pipe = Pipeline([node(_double, "seed", "result", name="double")])
    assert SequentialRunner().run(pipe, catalog)["result"].load() == 12


def test_runner_consumes_multiple_outputs_in_later_node():
    pipe = Pipeline([node(_split_pair, "seed", ["left", "right"], name="split"), node(_sum_values, ["left", "right"], "total", name="sum")])
    result = SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(4)}))
    assert result["total"].load() == 9


def test_runner_applies_dataset_confirmation_after_node_completion():
    audit = ConfirmableMemoryDataset("ready")
    pipe = Pipeline([node(_add_one, "seed", "result", name="produce", confirms="audit")])
    SequentialRunner().run(pipe, DataCatalog({"seed": MemoryDataset(1), "audit": audit}))
    assert audit.confirmed is True


def test_pipeline_catalog_runner_cross_view_output_names_align():
    pipe = Pipeline([node(_add_one, "x", "y", name="add"), node(_double, "y", "z", name="double")])
    catalog = DataCatalog({"x": MemoryDataset(4)})
    from kedro.runner import SequentialRunner

    result = SequentialRunner().run(pipe, catalog)
    assert pipe.outputs() == {"z"}
    assert set(result) == {"z"}
    assert result["z"].load() == 10
    assert catalog.load("z") == 10


def test_raw_catalog_assignment_cross_view_returns_memory_dataset_value():
    catalog = DataCatalog()
    catalog["seed"] = 11
    assert isinstance(catalog["seed"], MemoryDataset)
    assert catalog.load("seed") == 11
