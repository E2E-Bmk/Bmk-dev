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


def test_node_factory_returns_node_with_public_properties():
    created = node(_add_one, "x", "y", name="add.node", tags={"math"})
    assert isinstance(created, Node)
    assert created.name == "add.node"
    assert created.short_name == "add.node"
    assert created.namespace is None
    assert created.inputs == ["x"]
    assert created.outputs == ["y"]
    assert created.tags == {"math"}


def test_node_rejects_non_callable_function():
    with pytest.raises(ValueError):
        node("not-callable", "x", "y")


def test_node_rejects_empty_inputs_and_outputs():
    with pytest.raises(ValueError):
        node(_add_one, None, None)


def test_node_rejects_inputs_that_do_not_bind_to_signature():
    with pytest.raises(TypeError):
        node(_add_one, ["x", "extra"], "y")


def test_node_rejects_duplicate_output_names():
    with pytest.raises(ValueError):
        node(_split_pair, "x", ["y", "y"])


def test_node_rejects_same_input_and_output_dataset():
    with pytest.raises(ValueError):
        node(_add_one, "same", "same")


def test_node_run_uses_single_string_input_and_output():
    created = node(_add_one, "x", "y")
    assert created.run({"x": 2}) == {"y": 3}


def test_node_run_uses_list_inputs_in_order():
    created = node(_sum_values, ["a", "b"], "total")
    assert created.run({"a": 2, "b": 5}) == {"total": 7}


def test_node_run_uses_dict_inputs_as_keyword_arguments():
    created = node(_sum_values, {"a": "left", "b": "right"}, "total")
    assert created.run({"left": 4, "right": 6}) == {"total": 10}


def test_node_run_with_no_outputs_returns_empty_mapping():
    created = node(lambda x: x + 1, "x", None)
    assert created.run({"x": 10}) == {}


def test_node_run_list_outputs_require_matching_sequence_length():
    created = node(_split_pair, "x", ["left", "right"])
    assert created.run({"x": 3}) == {"left": 3, "right": 4}
    with pytest.raises(ValueError):
        node(_split_pair, "x", ["a", "b", "c"]).run({"x": 1})


def test_node_run_dict_outputs_map_return_keys_to_dataset_names():
    created = node(_return_mapping, "x", {"left": "a", "right": "b"})
    assert created.run({"x": 5}) == {"a": 5, "b": 6}


def test_node_run_requires_exact_runtime_inputs():
    created = node(_add_one, "x", "y")
    with pytest.raises(ValueError):
        created.run({"x": 1, "extra": 2})


def test_node_tag_returns_new_node_and_preserves_original():
    original = node(_add_one, "x", "y", tags="base")
    tagged = original.tag(["new", "base"])
    assert original.tags == {"base"}
    assert tagged.tags == {"base", "new"}
    assert tagged is not original


def test_namespaced_node_reports_namespace_and_prefixes():
    created = node(_add_one, "x", "y", name="add", namespace="outer.inner")
    assert created.name == "outer.inner.add"
    assert created.short_name == "add"
    assert created.namespace == "outer.inner"
    assert created.namespace_prefixes == ["outer", "outer.inner"]


def test_pipeline_orders_nodes_by_dependencies_not_input_order():
    second = node(_double, "clean", "model", name="model")
    first = node(_add_one, "raw", "clean", name="clean")
    pipe = Pipeline([second, first])
    assert [item.name for item in pipe.nodes] == ["clean", "model"]


def test_pipeline_reports_free_inputs_outputs_and_all_datasets():
    pipe = _make_basic_pipeline()
    assert pipe.inputs() == {"raw"}
    assert pipe.outputs() == {"report"}
    assert pipe.all_inputs() == {"raw", "clean", "model"}
    assert pipe.all_outputs() == {"clean", "model", "report"}
    assert pipe.datasets() == {"raw", "clean", "model", "report"}


def test_pipeline_node_dependencies_identify_upstream_nodes():
    pipe = _make_basic_pipeline()
    dependencies = {item.name: {dep.name for dep in deps} for item, deps in pipe.node_dependencies.items()}
    assert dependencies == {"clean": set(), "model": {"clean"}, "report": {"model"}}


def test_pipeline_filter_by_inputs_and_outputs_returns_dependency_slices():
    pipe = _make_basic_pipeline()
    assert [item.name for item in pipe.from_inputs("raw").nodes] == ["clean", "model", "report"]
    assert [item.name for item in pipe.to_outputs("model").nodes] == ["clean", "model"]


def test_pipeline_filter_by_node_names_and_tags_intersects_dimensions():
    pipe = _make_basic_pipeline()
    filtered = pipe.filter(node_names=["clean", "model"], tags=["train"])
    assert [item.name for item in filtered.nodes] == ["model"]


def test_pipeline_filter_missing_dimension_raises_value_error():
    with pytest.raises(ValueError):
        _make_basic_pipeline().filter(tags=["missing"])


def test_pipeline_only_nodes_with_namespaces_selects_namespaced_nodes():
    pipe = Pipeline([node(_add_one, "x", "y", name="add", namespace="space")])
    assert [item.name for item in pipe.only_nodes_with_namespaces(["space"]).nodes] == ["space.add"]


def test_pipeline_union_subtraction_and_intersection_return_new_pipelines():
    pipe = _make_basic_pipeline()
    clean = pipe.only_nodes("clean")
    model = pipe.only_nodes("model")
    assert [item.name for item in (clean + model).nodes] == ["clean", "model"]
    assert [item.name for item in (pipe - clean).nodes] == ["model", "report"]
    assert [item.name for item in (pipe & model).nodes] == ["model"]


def test_pipeline_constructor_rejects_duplicate_outputs():
    with pytest.raises(Exception):
        Pipeline([node(_add_one, "x", "same"), node(_double, "y", "same")])


def test_pipeline_constructor_rejects_circular_dependencies():
    with pytest.raises(Exception):
        Pipeline([node(_add_one, "a", "b"), node(_double, "b", "a")])


def test_pipeline_describe_contains_execution_order_node_names():
    described = _make_basic_pipeline().describe(names_only=True)
    assert described.index("clean") < described.index("model") < described.index("report")


def test_data_catalog_mapping_includes_registered_datasets():
    catalog = DataCatalog({"x": MemoryDataset(2)})
    assert list(catalog.keys()) == ["x"]
    assert "x" in catalog
    assert len(catalog) == 1
    assert isinstance(catalog["x"], MemoryDataset)
    assert catalog.load("x") == 2


def test_data_catalog_assignment_wraps_raw_values_as_memory_dataset():
    catalog = DataCatalog()
    catalog["raw"] = {"items": [1, 2]}
    assert isinstance(catalog["raw"], MemoryDataset)
    assert catalog.load("raw") == {"items": [1, 2]}


def test_data_catalog_reassignment_replaces_previous_dataset():
    catalog = DataCatalog({"value": MemoryDataset(1)})
    catalog["value"] = 99
    assert isinstance(catalog["value"], MemoryDataset)
    assert catalog.load("value") == 99


def test_data_catalog_get_returns_none_for_missing_dataset():
    catalog = DataCatalog()
    assert catalog.get("missing") is None
    with pytest.raises(DatasetNotFoundError):
        _ = catalog["missing"]


def test_data_catalog_load_save_release_cycle_with_memory_dataset():
    catalog = DataCatalog({"x": MemoryDataset()})
    catalog.save("x", {"value": 7})
    assert catalog.exists("x") is True
    assert catalog.load("x") == {"value": 7}
    catalog.release("x")
    assert catalog.exists("x") is False
    with pytest.raises(DatasetError):
        catalog.load("x")


def test_data_catalog_missing_dataset_operations_raise_not_found():
    catalog = DataCatalog()
    for operation in (catalog.load, catalog.release, catalog.confirm):
        with pytest.raises(DatasetNotFoundError):
            operation("missing")
    with pytest.raises(DatasetNotFoundError):
        catalog.save("missing", 1)


def test_data_catalog_confirm_calls_public_confirm_method():
    dataset = ConfirmableMemoryDataset(1)
    catalog = DataCatalog({"ready": dataset})
    catalog.confirm("ready")
    assert dataset.confirmed is True


def test_data_catalog_confirm_without_confirm_method_raises_dataset_error():
    catalog = DataCatalog({"plain": MemoryDataset(1)})
    with pytest.raises(DatasetError):
        catalog.confirm("plain")


def test_data_catalog_wraps_dataset_load_failures_in_dataset_error():
    catalog = DataCatalog({"broken": BrokenLoadDataset()})
    with pytest.raises(DatasetError):
        catalog.load("broken")


def test_data_catalog_from_config_builds_memory_dataset_by_class_name():
    catalog = DataCatalog.from_config({"sample": {"type": "MemoryDataset", "data": 12}})
    assert list(catalog.keys()) == ["sample"]
    assert catalog.load("sample") == 12


def test_data_catalog_from_config_rejects_invalid_entry_shape():
    with pytest.raises(DatasetError):
        DataCatalog.from_config({"bad": "not-a-dict"})
    with pytest.raises(DatasetError):
        DataCatalog.from_config({"bad": {"data": 1}})


def test_data_catalog_from_config_rejects_unknown_load_version_dataset():
    with pytest.raises(DatasetNotFoundError):
        DataCatalog.from_config({}, load_versions={"missing": "2024-01-01"})


def test_memory_dataset_load_before_save_raises_dataset_error():
    with pytest.raises(DatasetError):
        MemoryDataset().load()


def test_memory_dataset_deepcopy_mode_isolates_loaded_mutation():
    dataset = MemoryDataset([{"value": 1}], copy_mode="deepcopy")
    loaded = dataset.load()
    loaded[0]["value"] = 9
    assert dataset.load() == [{"value": 1}]


def test_memory_dataset_assign_mode_returns_same_object_reference():
    data = {"value": []}
    dataset = MemoryDataset(data, copy_mode="assign")
    loaded = dataset.load()
    loaded["value"].append(1)
    assert dataset.load() is data
    assert data == {"value": [1]}


def test_memory_dataset_rejects_invalid_copy_mode():
    with pytest.raises(DatasetError):
        MemoryDataset(1, copy_mode="unknown").load()


def test_omega_config_loader_loads_base_and_default_environment(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "local").mkdir()
    (conf / "base" / "parameters.yml").write_text("alpha: 1\nnested:\n  base: true\n", encoding="utf-8")
    (conf / "local" / "parameters.yml").write_text("alpha: 2\nbeta: 3\n", encoding="utf-8")
    loader = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local")
    assert loader["parameters"] == {"alpha": 2, "nested": {"base": True}, "beta": 3}


def test_omega_config_loader_runtime_params_override_parameter_files(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "parameters.yml").write_text("alpha: 1\nnested:\n  value: file\n", encoding="utf-8")
    loader = OmegaConfigLoader(str(conf), base_env="base", runtime_params={"alpha": 5, "nested": {"value": "runtime"}})
    assert loader["parameters"]["alpha"] == 5
    assert loader["parameters"]["nested"]["value"] == "runtime"


def test_omega_config_loader_soft_merge_preserves_nested_base_keys(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "local").mkdir()
    (conf / "base" / "parameters.yml").write_text("nested:\n  keep: yes\n  replace: base\n", encoding="utf-8")
    (conf / "local" / "parameters.yml").write_text("nested:\n  replace: local\n", encoding="utf-8")
    loader = OmegaConfigLoader(
        str(conf),
        base_env="base",
        default_run_env="local",
        merge_strategy={"parameters": "soft"},
    )
    assert loader["parameters"] == {"nested": {"keep": True, "replace": "local"}}


def test_omega_config_loader_destructive_merge_replaces_top_level_keys(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "local").mkdir()
    (conf / "base" / "catalog.yml").write_text("ds:\n  type: MemoryDataset\n  data: 1\n  metadata:\n    owner: base\n", encoding="utf-8")
    (conf / "local" / "catalog.yml").write_text("ds:\n  type: MemoryDataset\n  data: 2\n", encoding="utf-8")
    loader = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local")
    assert loader["catalog"] == {"ds": {"type": "MemoryDataset", "data": 2}}


def test_omega_config_loader_supports_yaml_yml_and_json_files(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "parameters.yml").write_text("a: 1\n", encoding="utf-8")
    (conf / "base" / "parameters_extra.yaml").write_text("b: 2\n", encoding="utf-8")
    (conf / "base" / "parameters_more.json").write_text('{"c": 3}', encoding="utf-8")
    assert OmegaConfigLoader(str(conf), base_env="base")["parameters"] == {"a": 1, "b": 2, "c": 3}


def test_omega_config_loader_unknown_key_and_missing_config_errors(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    loader = OmegaConfigLoader(str(conf), base_env="base")
    with pytest.raises(KeyError):
        loader["unknown"]
    with pytest.raises(MissingConfigException):
        loader["parameters"]
    assert loader["globals"] == {}


def test_omega_config_loader_duplicate_keys_in_same_environment_raise(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "parameters.yml").write_text("alpha: 1\n", encoding="utf-8")
    (conf / "base" / "parameters_extra.yml").write_text("alpha: 2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        OmegaConfigLoader(str(conf), base_env="base")["parameters"]


def test_omega_config_loader_omits_hidden_top_level_config_keys(tmp_path):
    conf = tmp_path / "conf"
    (conf / "base").mkdir(parents=True)
    (conf / "base" / "catalog.yml").write_text("_hidden: 1\nvisible:\n  type: MemoryDataset\n  data: 4\n", encoding="utf-8")
    assert OmegaConfigLoader(str(conf), base_env="base")["catalog"] == {"visible": {"type": "MemoryDataset", "data": 4}}


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
