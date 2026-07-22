"""Integration tests for astroid.

Each test exercises ≥2 public API boundaries or validates cross-view invariants.
"""
import subprocess
import sys

import pytest

import astroid
from astroid import MANAGER, inference_tip, register_module_extender, nodes
from astroid.exceptions import (
    AstroidBuildingError,
    AstroidSyntaxError,
    AttributeInferenceError,
    UseInferenceDefault,
)


# ── Manager: build from string + cache ────────────────────────────

@pytest.mark.depends_on("test_parse_returns_module_with_name_and_path")
def test_manager_ast_from_string_returns_cached_named_module():
    """Seam: state consistency — integration path for manager ast from string returns cached named module across cooperating public APIs."""
    name = "generated_cache_module_stage3"
    MANAGER.clear_cache()
    module = MANAGER.ast_from_string("x = 1", modname=name)
    again = MANAGER.ast_from_module_name(name)
    assert isinstance(module, nodes.Module)
    assert again is module


def test_manager_ast_from_string_sets_filepath_when_provided(tmp_path):
    """Seam: state consistency — integration path for manager ast from string sets filepath when provided across cooperating public APIs."""
    path = tmp_path / "mod_for_astroid.py"
    module = MANAGER.ast_from_string("x = 1", modname="mod_for_filepath", filepath=str(path))
    assert module.file == str(path)


# ── Manager: build from file + fully_defined ──────────────────────

@pytest.mark.depends_on("test_module_fully_defined_false_for_string_parsed_module")
def test_manager_ast_from_file_builds_python_file_module(tmp_path):
    """Seam: state consistency — integration path for manager ast from file builds python file module across cooperating public APIs."""
    path = tmp_path / "sample_module.py"
    path.write_text("value = 7\n", encoding="utf-8")
    module = MANAGER.ast_from_file(str(path), modname="sample_module_for_generated")
    assert isinstance(module, nodes.Module)
    assert module.getattr("value")
    assert module.fully_defined() is True


def test_manager_ast_from_file_missing_without_fallback_raises(tmp_path):
    """Seam: error propagation — integration path for manager ast from file missing without fallback raises across cooperating public APIs."""
    with pytest.raises(AstroidBuildingError):
        MANAGER.ast_from_file(str(tmp_path / "missing.py"), modname="missing_for_generated", fallback=False)


# ── Manager: build from module name ──────────────────────────────

def test_manager_ast_from_module_name_none_raises_building_error():
    """Seam: error propagation — integration path for manager ast from module name none raises building error across cooperating public APIs."""
    with pytest.raises(AstroidBuildingError):
        MANAGER.ast_from_module_name(None)


def test_manager_ast_from_module_name_returns_stub_for_main():
    """Seam: state consistency — integration path for manager ast from module name returns stub for main across cooperating public APIs."""
    module = MANAGER.ast_from_module_name("__main__", use_cache=False)
    assert isinstance(module, nodes.Module)
    assert module.name == "__main__"


# ── Manager: build from live objects ──────────────────────────────

def test_manager_ast_from_module_builds_live_module():
    """Seam: state consistency — integration path for manager ast from module builds live module across cooperating public APIs."""
    import math
    module = MANAGER.ast_from_module(math, modname="math")
    assert isinstance(module, nodes.Module)
    assert module.name == "math"


def test_manager_ast_from_class_returns_classdef():
    """Seam: error propagation — integration path for manager ast from class returns classdef across cooperating public APIs."""
    klass = MANAGER.ast_from_class(ValueError)
    assert isinstance(klass, nodes.ClassDef)
    assert klass.name == "ValueError"


# ── Manager: cache_module keeps first ─────────────────────────────

@pytest.mark.depends_on("test_manager_ast_from_string_returns_cached_named_module")
def test_manager_cache_module_keeps_first_module_for_name():
    """Seam: state consistency — integration path for manager cache module keeps first module for name across cooperating public APIs."""
    MANAGER.clear_cache()
    first = astroid.parse("x = 1", module_name="cache_keep_first")
    second = astroid.parse("x = 2", module_name="cache_keep_first")
    MANAGER.cache_module(first)
    MANAGER.cache_module(second)
    assert MANAGER.astroid_cache["cache_keep_first"] is first


# ── Manager: clear_cache keeps builtins ──────────────────────────

def test_manager_clear_cache_keeps_builtin_import_working():
    """Seam: state consistency — integration path for manager clear cache keeps builtin import working across cooperating public APIs."""
    MANAGER.clear_cache()
    builtins_module = MANAGER.ast_from_module_name("builtins")
    assert builtins_module.getattr("len")


# ── Transforms ────────────────────────────────────────────────────

@pytest.mark.depends_on("test_parse_apply_transforms_false_skips_registered_transform")
def test_register_transform_applies_to_matching_future_nodes():
    """Seam: protocol handoff — integration path for register transform applies to matching future nodes across cooperating public APIs."""
    def bump(node):
        node.value = 420043
        return node

    MANAGER.register_transform(nodes.Const, bump, lambda node: getattr(node, "value", None) == 420042)
    transformed = astroid.parse("answer = 420042")
    value = next(transformed.igetattr("answer"))
    assert value.value == 420043


# ── Inference tips ────────────────────────────────────────────────

def test_inference_tip_installs_custom_inference_and_returns_node():
    """Seam: protocol handoff — integration path for inference tip installs custom inference and returns node across cooperating public APIs."""
    replacement = astroid.extract_node("99")

    def infer_generated(node, context=None):
        yield replacement

    transform = inference_tip(infer_generated)
    MANAGER.register_transform(nodes.Name, transform, lambda node: node.name == "generated_tip_name")
    inferred = list(astroid.extract_node("generated_tip_name").infer())
    assert [node.value for node in inferred] == [99]


@pytest.mark.depends_on("test_infer_constant_binary_expression_returns_const_value")
def test_inference_tip_can_request_default_inference():
    """Seam: protocol handoff — integration path for inference tip can request default inference across cooperating public APIs."""
    def defaulting(node, context=None):
        raise UseInferenceDefault
        yield node

    transform = inference_tip(defaulting)
    MANAGER.register_transform(nodes.Name, transform, lambda node: node.name == "default_tip_name")
    module = astroid.parse("default_tip_name = 12\nresult = default_tip_name")
    inferred = list(module.body[1].value.infer())
    assert [node.value for node in inferred] == [12]


# ── Module extenders ──────────────────────────────────────────────

@pytest.mark.depends_on("test_module_public_names_omits_private_names")
def test_register_module_extender_exposes_extension_public_names(tmp_path, monkeypatch):
    """Seam: state consistency — integration path for register module extender exposes extension public names across cooperating public APIs."""
    module_name = "generated_extender_module_stage3"
    (tmp_path / f"{module_name}.py").write_text("existing = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    def extension_module():
        return astroid.parse("class Provided:\n    pass\nvalue = 5")

    register_module_extender(MANAGER, module_name, extension_module)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    assert "Provided" in module.public_names()
    assert [node.value for node in module.igetattr("value")] == [5]


# ── Failed-import hooks ──────────────────────────────────────────

def test_failed_import_hook_supplies_module_graph():
    """Seam: error propagation — integration path for failed import hook supplies module graph across cooperating public APIs."""
    module_name = "generated_missing_hook_stage3"

    def hook(modname):
        if modname == module_name:
            return astroid.parse("hooked = 123", module_name=module_name)
        raise AstroidBuildingError("not handled")

    MANAGER.register_failed_import_hook(hook)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    assert [node.value for node in module.igetattr("hooked")] == [123]


@pytest.mark.depends_on("test_lookup_finds_visible_local_assignment")
def test_failed_import_hook_result_supports_lookup_and_getattr():
    """Seam: error propagation — integration path for failed import hook result supports lookup and getattr across cooperating public APIs."""
    module_name = "generated_missing_hook_lookup_stage3"

    def hook(modname):
        if modname == module_name:
            return astroid.parse("visible = 321", module_name=module_name)
        raise AstroidBuildingError("not handled")

    MANAGER.register_failed_import_hook(hook)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    scope, statements = module.lookup("visible")
    assert scope is module
    assert statements == module.getattr("visible")


# ── CLI ──────────────────────────────────────────────────────────

def test_cli_ast_command_prints_repr_tree_for_valid_file(tmp_path):
    """Seam: protocol handoff — integration path for cli ast command prints repr tree for valid file across cooperating public APIs."""
    path = tmp_path / "cli_sample.py"
    path.write_text("value = 10\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "astroid", "ast", str(path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert proc.returncode == 0
    assert "Module" in proc.stdout
    assert "Assign" in proc.stdout


def test_cli_without_subcommand_returns_usage_error():
    """Seam: error propagation — integration path for cli without subcommand returns usage error across cooperating public APIs."""
    proc = subprocess.run(
        [sys.executable, "-m", "astroid"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert proc.returncode == 2
    assert "usage:" in proc.stderr.lower() or "usage:" in proc.stdout.lower()


# ── CVI-1: parse → root consistency ──────────────────────────────

@pytest.mark.depends_on("test_module_descendant_root_points_to_parse_root")
def test_cross_view_parse_lookup_infer_and_root_are_consistent():
    """CVI-1: parse, lookup, infer, and root() agree on the same module graph."""
    module = astroid.parse("value = 20 + 22\nresult = value")
    result = module.body[1].value
    scope, statements = result.lookup("value")
    inferred = list(result.infer())
    assert scope is module
    assert statements[0].root() is module
    assert [node.value for node in inferred] == [42]


# ── CVI-2: extract_node parent chain + rendering ─────────────────

@pytest.mark.depends_on("test_extract_node_wrapper_returns_inner_expression")
def test_cross_view_extract_node_parent_chain_and_rendering():
    """CVI-2: extract_node parent chain, statement(), and as_string() stay aligned."""
    selected = astroid.extract_node("base = 1\nvalue = __(base + 2)")
    assert selected.as_string() == "base + 2"
    assert isinstance(selected.root(), nodes.Module)
    assert selected.statement().as_string() == "value = base + 2"


# ── CVI-5: manager cache preserves lookup ─────────────────────────

@pytest.mark.depends_on("test_manager_ast_from_string_returns_cached_named_module")
def test_cross_view_manager_cache_preserves_lookup_results(tmp_path):
    """CVI-5: manager cache preserves lookup and inference results across reload."""
    path = tmp_path / "cache_view.py"
    path.write_text("answer = 42\n", encoding="utf-8")
    first = MANAGER.ast_from_file(str(path), modname="cache_view_generated")
    second = MANAGER.ast_from_module_name("cache_view_generated")
    assert second is first
    assert [node.value for node in second.igetattr("answer")] == [42]


# ── CVI-7: extender public_names + getattr + inference ────────────

@pytest.mark.depends_on("test_register_module_extender_exposes_extension_public_names")
def test_cross_view_extender_public_names_getattr_inference_agree(tmp_path, monkeypatch):
    """CVI-7: module extender keeps public_names, getattr, and inference consistent."""
    module_name = "generated_extender_cross_view_stage3"
    (tmp_path / f"{module_name}.py").write_text("existing = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    def extension_module():
        return astroid.parse("provided = 808")

    register_module_extender(MANAGER, module_name, extension_module)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    assert "provided" in module.public_names()
    assert module.getattr("provided")
    assert [node.value for node in module.igetattr("provided")] == [808]


# ── CVI-6: failed-import hook cache + inference ──────────────────

@pytest.mark.depends_on("test_failed_import_hook_supplies_module_graph")
def test_cross_view_failed_import_hook_cache_and_inference_agree():
    """CVI-6: failed-import hook cache and inference agree on hooked module state."""
    module_name = "generated_hook_cache_cross_view_stage3"

    def hook(modname):
        if modname == module_name:
            return astroid.parse("hook_value = 515", module_name=module_name)
        raise AstroidBuildingError("not handled")

    MANAGER.register_failed_import_hook(hook)
    first = MANAGER.ast_from_module_name(module_name, use_cache=True)
    second = MANAGER.ast_from_module_name(module_name, use_cache=True)
    assert second is first
    assert first.getattr("hook_value")
    assert [node.value for node in second.igetattr("hook_value")] == [515]


# ── CVI-4: transform changes parse + lookup + inference ──────────

@pytest.mark.depends_on("test_register_transform_applies_to_matching_future_nodes")
def test_cross_view_transform_changes_future_parse_lookup_inference():
    """CVI-4: registered transform changes parse, lookup, and inference together."""
    def transform(node):
        node.value = 7301
        return node

    MANAGER.register_transform(nodes.Const, transform, lambda node: getattr(node, "value", None) == 7300)
    module = astroid.parse("changed = 7300")
    scope, statements = module.lookup("changed")
    assert scope is module
    assert statements == module.getattr("changed")
    assert [node.value for node in module.igetattr("changed")] == [7301]


# ── CVI: class instance + attribute lookup share tree state ──────

@pytest.mark.depends_on("test_instantiate_class_returns_instance_for_classdef")
def test_cross_view_class_instance_and_attribute_lookup_share_tree():
    """CVI: class instance inference and attribute lookup share the same tree state."""
    module = astroid.parse("class Generated:\n    label = 'ok'\n\ninst = Generated()")
    instance = next(module.body[-1].value.infer())
    klass = module.body[0]
    assert isinstance(instance, astroid.Instance)
    assert klass.root() is module
    assert klass.getattr("label")
    assert [node.value for node in instance.igetattr("label")] == ["ok"]


# ── Representative workflow: parse + infer + extract + extend ─────

def test_representative_workflow_parse_infer_extract_and_extend(tmp_path, monkeypatch):
    """Seam: state consistency — integration path for representative workflow parse infer extract and extend across cooperating public APIs."""
    module = astroid.parse("""
    def func(first, second):
        return first + second

    arg_1 = 2
    arg_2 = 3
    func(arg_1, arg_2)
    """)
    call_expr = module.body[-1].value
    inferred = next(call_expr.infer())
    selected = astroid.extract_node("a = 1 #@\nb = __(a + 2)")

    workflow_module_name = "generated_representative_workflow_stage3"
    (tmp_path / f"{workflow_module_name}.py").write_text("existing = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    def fake_module():
        return astroid.parse("class Provided:\n    pass")

    register_module_extender(MANAGER, workflow_module_name, fake_module)
    extended = MANAGER.ast_from_module_name(workflow_module_name, use_cache=False)

    assert isinstance(inferred, nodes.Const)
    assert inferred.value == 5
    assert isinstance(selected, list)
    assert "Provided" in extended.public_names()


# ── Representative workflow: file + manager cache + CLI render ────

def test_representative_workflow_file_manager_cache_and_cli_render(tmp_path):
    """Seam: protocol handoff — integration path for representative workflow file manager cache and cli render across cooperating public APIs."""
    path = tmp_path / "workflow_file.py"
    path.write_text("answer = 40 + 2\n", encoding="utf-8")
    module = MANAGER.ast_from_file(str(path), modname="generated_workflow_file_stage3")
    cached = MANAGER.ast_from_module_name("generated_workflow_file_stage3")
    proc = subprocess.run(
        [sys.executable, "-m", "astroid", "ast", str(path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert cached is module
    assert [node.value for node in cached.igetattr("answer")] == [42]
    assert proc.returncode == 0
    assert "Assign" in proc.stdout


# ── Representative workflow: failed-import hook → lookup → infer ──

def test_representative_workflow_failed_import_hook_then_lookup_infer():
    """Seam: error propagation — integration path for representative workflow failed import hook then lookup infer across cooperating public APIs."""
    module_name = "generated_representative_hook_stage3"

    def hook(modname):
        if modname == module_name:
            return astroid.parse("provided = 600 + 7", module_name=module_name)
        raise AstroidBuildingError("not handled")

    MANAGER.register_failed_import_hook(hook)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    scope, statements = module.lookup("provided")
    inferred = list(module.igetattr("provided"))
    assert scope is module
    assert statements == module.getattr("provided")
    assert [node.value for node in inferred] == [607]


# ── CVI-9: CLI render matches repr_tree for valid file ────────────

@pytest.mark.depends_on("test_repr_tree_includes_linenos_when_requested")
def test_cli_repr_tree_matches_parse_repr_tree(tmp_path):
    """Seam: protocol handoff — integration path for cli repr tree matches parse repr tree across cooperating public APIs."""
    path = tmp_path / "cli_roundtrip.py"
    path.write_text("x = 42\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "astroid", "ast", str(path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    module = astroid.parse(path.read_text(), module_name="cli_roundtrip")
    assert proc.returncode == 0
    assert "Module" in proc.stdout
    assert "Const" in proc.stdout
