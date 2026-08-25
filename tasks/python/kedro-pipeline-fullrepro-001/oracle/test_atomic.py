"""Atomic oracle tests for kedro-pipeline-fullrepro-001.

Each test exercises ONE public API entry point and ONE behavior.
"""
from __future__ import annotations

import pytest

from kedro.config import MissingConfigException, OmegaConfigLoader
from kedro.io import DataCatalog, DatasetError, DatasetNotFoundError, MemoryDataset
from kedro.pipeline import Pipeline, node, pipeline
from kedro.runner import SequentialRunner

from conftest import (
    add_one, double, to_text, sum_values, split_pair, return_mapping,
    make_three_step_pipeline, ConfirmableMemoryDataset, BrokenLoadDataset,
)


# ===== Node Construction =====

class TestNodeConstruction:
    def test_node_factory_returns_node_with_correct_properties(self):
        created = node(add_one, "x", "y", name="inc.node", tags={"math"})
        assert created.name == "inc.node"
        assert created.short_name == "inc.node"
        assert created.namespace is None
        assert created.inputs == ["x"]
        assert created.outputs == ["y"]
        assert created.tags == {"math"}

    def test_node_rejects_non_callable_function(self):
        with pytest.raises(ValueError):
            node("not-callable", "input", "output")

    def test_node_requires_at_least_one_input_or_output(self):
        with pytest.raises(ValueError):
            node(add_one, None, None)

    def test_node_rejects_inputs_not_binding_to_signature(self):
        with pytest.raises(TypeError):
            node(add_one, ["a", "b"], "out")

    def test_node_rejects_duplicate_output_names(self):
        with pytest.raises(ValueError):
            node(split_pair, "x", ["dup", "dup"])

    def test_node_rejects_same_input_and_output_name(self):
        with pytest.raises(ValueError):
            node(add_one, "shared", "shared")

    def test_namespaced_node_metadata(self):
        created = node(add_one, "x", "y", name="inc", namespace="outer.inner")
        assert created.name == "outer.inner.inc"
        assert created.short_name == "inc"
        assert created.namespace == "outer.inner"
        assert created.namespace_prefixes == ["outer", "outer.inner"]


# ===== Node.run Behavior =====

class TestNodeRun:
    def test_single_string_input_and_output(self):
        created = node(add_one, "x", "y")
        assert created.run({"x": 7}) == {"y": 8}

    def test_none_inputs_calls_function_without_arguments(self):
        created = node(lambda: 99, None, "answer")
        assert created.run() == {"answer": 99}
        assert created.run(None) == {"answer": 99}

    def test_list_inputs_passed_in_declared_order(self):
        created = node(sum_values, ["a", "b"], "total")
        assert created.run({"a": 3, "b": 7}) == {"total": 10}

    def test_dict_inputs_passed_as_keyword_arguments(self):
        created = node(sum_values, {"a": "left", "b": "right"}, "total")
        assert created.run({"left": 5, "right": 9}) == {"total": 14}

    def test_none_outputs_returns_empty_dict(self):
        created = node(lambda x: x + 1, "x", None)
        assert created.run({"x": 10}) == {}

    def test_list_outputs_require_matching_sequence_length(self):
        created = node(split_pair, "x", ["left", "right"])
        assert created.run({"x": 4}) == {"left": 4, "right": 5}

    def test_list_outputs_length_mismatch_raises_value_error(self):
        with pytest.raises(ValueError):
            node(split_pair, "x", ["a", "b", "c"]).run({"x": 1})

    def test_dict_outputs_map_return_keys_to_dataset_names(self):
        created = node(return_mapping, "x", {"left": "alpha", "right": "beta"})
        assert created.run({"x": 6}) == {"alpha": 6, "beta": 7}

    def test_runtime_input_mismatch_raises_value_error(self):
        created = node(add_one, "x", "y")
        with pytest.raises(ValueError):
            created.run({"x": 1, "extra": 2})


# ===== Node Tagging =====

class TestNodeTag:
    def test_tag_returns_new_node_preserving_original(self):
        original = node(add_one, "x", "y", tags="base")
        tagged = original.tag(["added"])
        assert original.tags == {"base"}
        assert tagged.tags == {"base", "added"}
        assert tagged is not original


# ===== Pipeline Construction and Properties =====

class TestPipelineProperties:
    def test_nodes_ordered_by_dependency_not_input_order(self):
        second = node(double, "clean", "model", name="model")
        first = node(add_one, "raw", "clean", name="clean")
        pipe = Pipeline([second, first])
        assert [n.name for n in pipe.nodes] == ["clean", "model"]

    def test_free_inputs_outputs_all_inputs_outputs_datasets(self):
        pipe = make_three_step_pipeline()
        assert pipe.inputs() == {"raw"}
        assert pipe.outputs() == {"report"}
        assert pipe.all_inputs() == {"raw", "clean", "model"}
        assert pipe.all_outputs() == {"clean", "model", "report"}
        assert pipe.datasets() == {"raw", "clean", "model", "report"}

    def test_node_dependencies_identify_upstream(self):
        pipe = make_three_step_pipeline()
        deps = {n.name: {d.name for d in ds} for n, ds in pipe.node_dependencies.items()}
        assert deps == {"clean": set(), "model": {"clean"}, "report": {"model"}}

    def test_describe_names_only_shows_execution_order(self):
        described = make_three_step_pipeline().describe(names_only=True)
        assert described.index("clean") < described.index("model") < described.index("report")

    def test_rejects_duplicate_produced_outputs(self):
        from kedro.pipeline import OutputNotUniqueError
        with pytest.raises((OutputNotUniqueError, ValueError)):
            Pipeline([node(add_one, "x", "same"), node(double, "y", "same")])

    def test_rejects_circular_dependencies(self):
        from kedro.pipeline import CircularDependencyError
        with pytest.raises((CircularDependencyError, ValueError)):
            Pipeline([node(add_one, "a", "b"), node(double, "b", "a")])


# ===== Pipeline Filtering =====

class TestPipelineFiltering:
    def test_from_inputs_and_to_outputs(self):
        pipe = make_three_step_pipeline()
        assert [n.name for n in pipe.from_inputs("raw").nodes] == ["clean", "model", "report"]
        assert [n.name for n in pipe.to_outputs("model").nodes] == ["clean", "model"]

    def test_from_nodes_and_to_nodes(self):
        pipe = make_three_step_pipeline()
        assert [n.name for n in pipe.from_nodes("model").nodes] == ["model", "report"]
        assert [n.name for n in pipe.to_nodes("model").nodes] == ["clean", "model"]

    def test_only_nodes_with_tags(self):
        pipe = make_three_step_pipeline()
        assert [n.name for n in pipe.only_nodes_with_tags("prep").nodes] == ["clean"]
        assert [n.name for n in pipe.only_nodes_with_tags("prep", "train").nodes] == ["clean", "model"]

    def test_only_nodes_with_inputs_and_outputs(self):
        pipe = make_three_step_pipeline()
        assert [n.name for n in pipe.only_nodes_with_inputs("clean").nodes] == ["model"]
        assert [n.name for n in pipe.only_nodes_with_outputs("clean").nodes] == ["clean"]

    def test_only_nodes_with_namespaces(self):
        pipe = Pipeline([node(add_one, "x", "y", name="inc", namespace="space")])
        assert [n.name for n in pipe.only_nodes_with_namespaces(["space"]).nodes] == ["space.inc"]

    def test_filter_intersects_dimensions(self):
        pipe = make_three_step_pipeline()
        filtered = pipe.filter(node_names=["clean", "model"], tags=["train"])
        assert [n.name for n in filtered.nodes] == ["model"]

    def test_filter_missing_dimension_raises_value_error(self):
        with pytest.raises(ValueError):
            make_three_step_pipeline().filter(tags=["nonexistent"])


# ===== Pipeline Operators and Factory =====

class TestPipelineOperators:
    def test_union_subtraction_intersection(self):
        pipe = make_three_step_pipeline()
        clean = pipe.only_nodes("clean")
        model = pipe.only_nodes("model")
        assert [n.name for n in (clean + model).nodes] == ["clean", "model"]
        assert [n.name for n in (pipe - clean).nodes] == ["model", "report"]
        assert [n.name for n in (pipe & model).nodes] == ["model"]

    def test_pipeline_tag_adds_tags_leaving_original_unchanged(self):
        pipe = make_three_step_pipeline()
        tagged = pipe.tag(["extra"])
        assert all("extra" in n.tags for n in tagged.nodes)
        assert all("extra" not in n.tags for n in pipe.nodes)

    def test_pipeline_factory_namespace_prefixes_datasets(self):
        namespaced = pipeline(make_three_step_pipeline(), namespace="ns", inputs={"raw"})
        assert [n.name for n in namespaced.nodes] == ["ns.clean", "ns.model", "ns.report"]
        assert namespaced.inputs() == {"raw"}
        assert namespaced.outputs() == {"ns.report"}
        assert namespaced.datasets() == {"raw", "ns.clean", "ns.model", "ns.report"}


# ===== DataCatalog Mapping =====

class TestDataCatalogMapping:
    def test_keys_containment_len_and_indexing(self):
        catalog = DataCatalog({"x": MemoryDataset(3)})
        assert list(catalog.keys()) == ["x"]
        assert "x" in catalog
        assert len(catalog) == 1
        assert isinstance(catalog["x"], MemoryDataset)
        assert catalog.load("x") == 3

    def test_assignment_wraps_raw_values(self):
        catalog = DataCatalog()
        catalog["raw"] = {"items": [4, 5]}
        assert isinstance(catalog["raw"], MemoryDataset)
        assert catalog.load("raw") == {"items": [4, 5]}

    def test_reassignment_replaces_previous(self):
        catalog = DataCatalog({"value": MemoryDataset(1)})
        catalog["value"] = 77
        assert catalog.load("value") == 77

    def test_get_returns_none_for_missing(self):
        catalog = DataCatalog()
        assert catalog.get("absent") is None

    def test_indexing_missing_raises_not_found(self):
        with pytest.raises(DatasetNotFoundError):
            DataCatalog()["absent"]


# ===== DataCatalog Load/Save/Lifecycle =====

class TestDataCatalogLifecycle:
    def test_save_load_exists_release_cycle(self):
        catalog = DataCatalog({"x": MemoryDataset()})
        catalog.save("x", {"value": 8})
        assert catalog.exists("x") is True
        assert catalog.load("x") == {"value": 8}
        catalog.release("x")
        assert catalog.exists("x") is False
        with pytest.raises(DatasetError):
            catalog.load("x")

    def test_operations_on_missing_dataset_raise_not_found(self):
        catalog = DataCatalog()
        with pytest.raises(DatasetNotFoundError):
            catalog.load("missing")
        with pytest.raises(DatasetNotFoundError):
            catalog.save("missing", 1)

    def test_confirm_calls_public_confirm_method(self):
        ds = ConfirmableMemoryDataset(1)
        catalog = DataCatalog({"ready": ds})
        catalog.confirm("ready")
        assert ds.confirmed is True

    def test_confirm_without_method_raises_dataset_error(self):
        catalog = DataCatalog({"plain": MemoryDataset(1)})
        with pytest.raises(DatasetError):
            catalog.confirm("plain")

    def test_load_failure_wrapped_in_dataset_error(self):
        catalog = DataCatalog({"broken": BrokenLoadDataset()})
        with pytest.raises(DatasetError):
            catalog.load("broken")


# ===== DataCatalog.from_config =====

class TestDataCatalogFromConfig:
    def test_builds_memory_dataset_by_class_name(self):
        catalog = DataCatalog.from_config({"sample": {"type": "MemoryDataset", "data": 15}})
        assert catalog.load("sample") == 15

    def test_rejects_non_dict_entry(self):
        with pytest.raises(DatasetError):
            DataCatalog.from_config({"bad": "not-a-dict"})

    def test_rejects_entry_without_type(self):
        with pytest.raises(DatasetError):
            DataCatalog.from_config({"bad": {"data": 1}})

    def test_unknown_load_version_raises_not_found(self):
        with pytest.raises(DatasetNotFoundError):
            DataCatalog.from_config({}, load_versions={"missing": "2024-06-15"})


# ===== MemoryDataset =====

class TestMemoryDataset:
    def test_load_before_save_raises_dataset_error(self):
        with pytest.raises(DatasetError):
            MemoryDataset().load()

    def test_deepcopy_mode_isolates_mutations(self):
        ds = MemoryDataset([{"val": 1}], copy_mode="deepcopy")
        loaded = ds.load()
        loaded[0]["val"] = 99
        assert ds.load() == [{"val": 1}]

    def test_assign_mode_returns_same_reference(self):
        data = {"val": []}
        ds = MemoryDataset(data, copy_mode="assign")
        loaded = ds.load()
        loaded["val"].append(1)
        assert ds.load() is data
        assert data == {"val": [1]}

    def test_copy_mode_shallow_copies(self):
        ds = MemoryDataset(copy_mode="copy")
        ds.save([10, 20])
        loaded = ds.load()
        loaded.append(30)
        assert ds.load() == [10, 20]

    def test_invalid_copy_mode_raises_dataset_error(self):
        with pytest.raises(DatasetError):
            MemoryDataset(1, copy_mode="unknown").load()

    def test_release_clears_stored_value(self):
        ds = MemoryDataset(copy_mode="copy")
        ds.save(42)
        assert ds.exists() is True
        ds.release()
        assert ds.exists() is False
        with pytest.raises(DatasetError):
            ds.load()


# ===== OmegaConfigLoader =====

class TestOmegaConfigLoader:
    def test_loads_base_and_default_env_with_destructive_merge(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "local").mkdir()
        (conf / "base" / "parameters.yml").write_text("alpha: 1\nnested:\n  base: true\n", encoding="utf-8")
        (conf / "local" / "parameters.yml").write_text("alpha: 3\nbeta: 4\n", encoding="utf-8")
        loader = OmegaConfigLoader(str(conf), base_env="base", default_run_env="local")
        assert loader["parameters"] == {"alpha": 3, "nested": {"base": True}, "beta": 4}

    def test_runtime_params_override_file_values(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "parameters.yml").write_text("alpha: 1\n", encoding="utf-8")
        loader = OmegaConfigLoader(str(conf), base_env="base", runtime_params={"alpha": 8})
        assert loader["parameters"]["alpha"] == 8

    def test_soft_merge_preserves_nested_base_keys(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "local").mkdir()
        (conf / "base" / "parameters.yml").write_text("nested:\n  keep: yes\n  replace: base\n", encoding="utf-8")
        (conf / "local" / "parameters.yml").write_text("nested:\n  replace: local\n", encoding="utf-8")
        loader = OmegaConfigLoader(
            str(conf), base_env="base", default_run_env="local",
            merge_strategy={"parameters": "soft"},
        )
        assert loader["parameters"] == {"nested": {"keep": True, "replace": "local"}}

    def test_supports_yml_yaml_and_json_files(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "parameters.yml").write_text("a: 1\n", encoding="utf-8")
        (conf / "base" / "parameters_extra.yaml").write_text("b: 2\n", encoding="utf-8")
        (conf / "base" / "parameters_more.json").write_text('{"c": 3}', encoding="utf-8")
        assert OmegaConfigLoader(str(conf), base_env="base")["parameters"] == {"a": 1, "b": 2, "c": 3}

    def test_unknown_key_raises_key_error(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        with pytest.raises(KeyError):
            OmegaConfigLoader(str(conf), base_env="base")["unknown"]

    def test_missing_config_files_raise_missing_config_exception(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        with pytest.raises(MissingConfigException):
            OmegaConfigLoader(str(conf), base_env="base")["parameters"]

    def test_globals_returns_empty_when_absent(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        assert OmegaConfigLoader(str(conf), base_env="base")["globals"] == {}

    def test_duplicate_keys_in_same_env_raise_value_error(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "parameters.yml").write_text("alpha: 1\n", encoding="utf-8")
        (conf / "base" / "parameters_dup.yml").write_text("alpha: 2\n", encoding="utf-8")
        with pytest.raises(ValueError):
            OmegaConfigLoader(str(conf), base_env="base")["parameters"]

    def test_hidden_top_level_keys_omitted_from_non_parameter_config(self, tmp_path):
        conf = tmp_path / "conf"
        (conf / "base").mkdir(parents=True)
        (conf / "base" / "catalog.yml").write_text(
            "_hidden: 1\nvisible:\n  type: MemoryDataset\n  data: 5\n", encoding="utf-8"
        )
        assert OmegaConfigLoader(str(conf), base_env="base")["catalog"] == {
            "visible": {"type": "MemoryDataset", "data": 5}
        }
