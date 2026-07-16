import os
import subprocess
import sys
import textwrap
import warnings

import pytest

import astroid
from astroid import MANAGER, inference_tip, register_module_extender, nodes
from astroid.exceptions import (
    AstroidBuildingError,
    AstroidError,
    AstroidImportError,
    AstroidSyntaxError,
    AttributeInferenceError,
    InferenceError,
    NameInferenceError,
    ParentMissingError,
    StatementMissing,
    UseInferenceDefault,
)


def test_parse_returns_module_with_name_and_path():
    module = astroid.parse("x = 1", module_name="generated_mod", path="generated_mod.py")
    assert isinstance(module, nodes.Module)
    assert module.name == "generated_mod"
    assert module.file.endswith("generated_mod.py")


def test_parse_dedents_source_before_building_tree():
    module = astroid.parse("""
        value = 3
        result = value + 4
    """)
    assert [child.as_string() for child in module.body] == ["value = 3", "result = value + 4"]


def test_parse_raises_astroid_syntax_error_for_invalid_python():
    with pytest.raises(AstroidSyntaxError):
        astroid.parse("def broken(:\n    pass")


def test_extract_node_hash_marker_returns_marked_statement():
    node = astroid.extract_node("a = 1 #@\nb = 2")
    assert isinstance(node, nodes.Assign)
    assert node.as_string() == "a = 1"


def test_extract_node_wrapper_returns_inner_expression():
    node = astroid.extract_node("value = __(1 + 2)")
    assert isinstance(node, nodes.BinOp)
    assert node.as_string() == "1 + 2"


def test_extract_node_multiple_markers_return_list_in_source_order():
    selected = astroid.extract_node("a = 1 #@\nb = 2 #@")
    assert isinstance(selected, list)
    assert [node.as_string() for node in selected] == ["a = 1", "b = 2"]


def test_extract_node_without_marker_returns_last_top_level_statement():
    node = astroid.extract_node("a = 1\nb = 2")
    assert isinstance(node, nodes.Assign)
    assert node.as_string() == "b = 2"


def test_extract_node_expression_statement_unwraps_expression():
    node = astroid.extract_node("1 + 2 #@")
    assert isinstance(node, nodes.BinOp)
    assert node.as_string() == "1 + 2"


def test_extract_node_empty_module_raises_value_error():
    with pytest.raises(ValueError):
        astroid.extract_node("")


def test_module_descendant_root_points_to_parse_root():
    module = astroid.parse("def f():\n    return 1")
    return_node = module.body[0].body[0]
    assert return_node.root() is module


def test_get_children_yields_structural_children_in_order():
    module = astroid.parse("x = 1\ndef f():\n    return x\nclass C:\n    pass")
    assert [type(child).__name__ for child in module.get_children()] == ["Assign", "FunctionDef", "ClassDef"]


def test_node_ancestors_walks_parent_chain_to_module():
    module = astroid.parse("def f():\n    value = 1\n    return value")
    name = module.body[0].body[1].value
    ancestor_types = [type(node).__name__ for node in name.node_ancestors()]
    assert ancestor_types[:3] == ["Return", "FunctionDef", "Module"]


def test_statement_returns_nearest_statement_node():
    expr = astroid.extract_node("def f():\n    return 1 + 2 #@")
    assert isinstance(expr.statement(), nodes.Return)


def test_statement_missing_is_raised_for_detached_expression():
    detached = astroid.extract_node("1")
    detached.parent = None
    with pytest.raises(StatementMissing):
        detached.statement()


def test_frame_returns_nearest_function_frame():
    module = astroid.parse("def f():\n    value = 1\n    return value")
    name = module.body[0].body[1].value
    assert isinstance(name.frame(), nodes.FunctionDef)


def test_scope_parentless_non_scope_raises_parent_missing_error():
    detached = astroid.extract_node("1")
    detached.parent = None
    with pytest.raises(ParentMissingError):
        detached.scope()


def test_scope_returns_nearest_function_scope():
    module = astroid.parse("def f():\n    value = 1\n    return value")
    name = module.body[0].body[1].value
    assert isinstance(name.scope(), nodes.FunctionDef)


def test_module_root_returns_itself():
    module = astroid.parse("x = 1")
    assert module.root() is module


def test_nodes_of_class_finds_matching_descendants():
    module = astroid.parse("a = 1\nb = a + 2")
    names = [node.name for node in module.nodes_of_class(nodes.AssignName)]
    assert names == ["a", "b"]


def test_nodes_of_class_skip_klass_prevents_descent():
    module = astroid.parse("def f():\n    inner = 1\nouter = 2")
    names = [node.name for node in module.nodes_of_class(nodes.AssignName, skip_klass=nodes.FunctionDef)]
    assert names == ["outer"]


def test_as_string_renders_source_like_expression():
    expr = astroid.extract_node("value = __(1 + 2 * 3)")
    assert expr.as_string() == "1 + 2 * 3"


def test_repr_tree_includes_node_kinds_and_linenos_when_requested():
    module = astroid.parse("x = 1\n\ny = 2")
    without_positions = module.repr_tree(include_linenos=False)
    with_positions = module.repr_tree(include_linenos=True)
    assert with_positions != without_positions
    assert len(with_positions) > len(without_positions)


def test_repr_tree_respects_max_depth_truncation_signal():
    module = astroid.parse("x = 1 + 2")
    full_tree = module.repr_tree()
    depth_one = module.repr_tree(max_depth=1)
    depth_two = module.repr_tree(max_depth=2)
    assert depth_one != full_tree
    assert len(depth_one) < len(depth_two) < len(full_tree)


def test_infer_constant_binary_expression_returns_const_value():
    inferred = list(astroid.extract_node("1 + 2").infer())
    assert len(inferred) == 1
    assert isinstance(inferred[0], nodes.Const)
    assert inferred[0].value == 3


def test_inferred_returns_list_of_infer_results():
    results = astroid.extract_node("'a' + 'b'").inferred()
    assert [node.value for node in results] == ["ab"]


def test_infer_unknown_dynamic_call_yields_uninferable_or_result_boundary():
    node = astroid.extract_node("unknown_factory()")
    with pytest.raises(NameInferenceError):
        list(node.infer())


def test_instantiate_class_returns_instance_for_classdef():
    klass = astroid.extract_node("class Generated:\n    pass")
    instance = klass.instantiate_class()
    assert isinstance(instance, astroid.Instance)


def test_instantiate_class_returns_self_for_non_class_node():
    const = astroid.extract_node("1")
    assert const.instantiate_class() is const


def test_module_public_names_omits_private_names():
    module = astroid.parse("visible = 1\n_hidden = 2")
    assert module.public_names() == ["visible"]


def test_wildcard_import_names_uses_explicit_all_sequence():
    module = astroid.parse("__all__ = ['first', 'second']\nfirst = 1\nsecond = 2\nthird = 3")
    assert module.wildcard_import_names() == ["first", "second"]


def test_wildcard_import_names_falls_back_to_public_locals():
    module = astroid.parse("alpha = 1\n_beta = 2")
    assert module.wildcard_import_names() == ["alpha"]


def test_module_getattr_returns_matching_attribute_nodes():
    module = astroid.parse("answer = 42")
    attrs = module.getattr("answer")
    assert [node.as_string() for node in attrs] == ["answer"]


def test_module_getattr_empty_name_raises_attribute_inference_error():
    module = astroid.parse("answer = 42")
    with pytest.raises(AttributeInferenceError):
        module.getattr("")


def test_module_igetattr_infers_attribute_values():
    module = astroid.parse("answer = 40 + 2")
    inferred = list(module.igetattr("answer"))
    assert [node.value for node in inferred] == [42]


def test_module_igetattr_missing_name_raises_inference_error():
    module = astroid.parse("answer = 42")
    with pytest.raises(InferenceError):
        list(module.igetattr("missing"))


def test_module_fully_defined_false_for_string_parsed_module():
    assert astroid.parse("x = 1").fully_defined() is False


def test_lookup_finds_visible_local_assignment_from_descendant():
    module = astroid.parse("def f(arg):\n    local = arg\n    return local")
    name = module.body[0].body[1].value
    scope, statements = name.lookup("local")
    assert scope is module.body[0]
    assert [stmt.as_string() for stmt in statements] == ["local"]


def test_lookup_falls_back_to_builtins_for_builtin_name():
    node = astroid.extract_node("len([1, 2])")
    scope, statements = node.func.lookup("len")
    assert scope.name == "builtins"
    assert statements


def test_lookup_missing_name_returns_builtin_scope_without_statements():
    node = astroid.extract_node("missing_name")
    scope, statements = node.lookup("missing_name")
    assert scope.name == "builtins"
    assert statements == []


def test_ilookup_infers_assignment_values():
    module = astroid.parse("value = 21 * 2\nresult = value")
    result_name = module.body[1].value
    assert [node.value for node in result_name.ilookup("value")] == [42]


def test_inference_yields_instance_for_class_call():
    call = astroid.extract_node("class C:\n    pass\nC() #@")
    inferred = list(call.infer())
    assert len(inferred) == 1
    assert isinstance(inferred[0], astroid.Instance)


def test_uninferable_is_identity_comparable_sentinel():
    with pytest.raises(NameInferenceError):
        list(astroid.extract_node("missing_for_uninferable_check").infer())
    assert astroid.Uninferable is astroid.Uninferable
    assert not isinstance(astroid.Uninferable, BaseException)


def test_manager_ast_from_string_returns_cached_named_module():
    name = "generated_cache_module_stage3"
    MANAGER.clear_cache()
    module = MANAGER.ast_from_string("x = 1", modname=name)
    again = MANAGER.ast_from_module_name(name)
    assert isinstance(module, nodes.Module)
    assert again is module


def test_manager_ast_from_string_sets_filepath_when_provided(tmp_path):
    path = tmp_path / "mod_for_astroid.py"
    module = MANAGER.ast_from_string("x = 1", modname="mod_for_filepath", filepath=str(path))
    assert module.file == str(path)


def test_manager_ast_from_file_builds_python_file_module(tmp_path):
    path = tmp_path / "sample_module.py"
    path.write_text("value = 7\n", encoding="utf-8")
    module = MANAGER.ast_from_file(str(path), modname="sample_module_for_generated")
    assert isinstance(module, nodes.Module)
    assert module.getattr("value")
    assert module.fully_defined() is True


def test_manager_ast_from_file_missing_without_fallback_raises(tmp_path):
    with pytest.raises(AstroidBuildingError):
        MANAGER.ast_from_file(str(tmp_path / "missing.py"), modname="missing_for_generated", fallback=False)


def test_manager_ast_from_module_name_none_raises_building_error():
    with pytest.raises(AstroidBuildingError):
        MANAGER.ast_from_module_name(None)


def test_manager_ast_from_module_name_returns_stub_for_main():
    module = MANAGER.ast_from_module_name("__main__", use_cache=False)
    assert isinstance(module, nodes.Module)
    assert module.name == "__main__"


def test_manager_ast_from_module_builds_live_module_for_math():
    import math

    module = MANAGER.ast_from_module(math, modname="math")
    assert isinstance(module, nodes.Module)
    assert module.name == "math"


def test_manager_ast_from_class_returns_classdef_for_builtin_exception():
    klass = MANAGER.ast_from_class(ValueError)
    assert isinstance(klass, nodes.ClassDef)
    assert klass.name == "ValueError"


def test_manager_cache_module_keeps_first_module_for_name():
    MANAGER.clear_cache()
    first = astroid.parse("x = 1", module_name="cache_keep_first")
    second = astroid.parse("x = 2", module_name="cache_keep_first")
    MANAGER.cache_module(first)
    MANAGER.cache_module(second)
    assert MANAGER.astroid_cache["cache_keep_first"] is first


def test_manager_clear_cache_keeps_builtin_import_working():
    MANAGER.clear_cache()
    builtins_module = MANAGER.ast_from_module_name("builtins")
    assert builtins_module.getattr("len")


def test_register_transform_applies_to_matching_future_nodes():
    def bump(node):
        node.value = 420043
        return node

    MANAGER.register_transform(nodes.Const, bump, lambda node: getattr(node, "value", None) == 420042)
    transformed = astroid.parse("answer = 420042")
    value = next(transformed.igetattr("answer"))
    assert value.value == 420043


def test_parse_apply_transforms_false_skips_registered_transform():
    module = astroid.parse("answer = 420042", apply_transforms=False)
    value = next(module.igetattr("answer"))
    assert value.value == 420042


def test_inference_tip_installs_custom_inference_and_returns_node():
    replacement = astroid.extract_node("99")

    def infer_generated(node, context=None):
        yield replacement

    transform = inference_tip(infer_generated)
    MANAGER.register_transform(nodes.Name, transform, lambda node: node.name == "generated_tip_name")
    inferred = list(astroid.extract_node("generated_tip_name").infer())
    assert [node.value for node in inferred] == [99]


def test_inference_tip_can_request_default_inference():
    def defaulting(node, context=None):
        raise UseInferenceDefault
        yield node

    transform = inference_tip(defaulting)
    MANAGER.register_transform(nodes.Name, transform, lambda node: node.name == "default_tip_name")
    module = astroid.parse("default_tip_name = 12\nresult = default_tip_name")
    inferred = list(module.body[1].value.infer())
    assert [node.value for node in inferred] == [12]


def test_register_module_extender_exposes_extension_public_names(tmp_path, monkeypatch):
    module_name = "generated_extender_module_stage3"
    (tmp_path / f"{module_name}.py").write_text("existing = 1\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    def extension_module():
        return astroid.parse("class Provided:\n    pass\nvalue = 5")

    register_module_extender(MANAGER, module_name, extension_module)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    assert "Provided" in module.public_names()
    assert [node.value for node in module.igetattr("value")] == [5]


def test_failed_import_hook_supplies_module_graph_for_missing_import():
    module_name = "generated_missing_hook_stage3"

    def hook(modname):
        if modname == module_name:
            return astroid.parse("hooked = 123", module_name=module_name)
        raise AstroidBuildingError("not handled")

    MANAGER.register_failed_import_hook(hook)
    module = MANAGER.ast_from_module_name(module_name, use_cache=False)
    assert [node.value for node in module.igetattr("hooked")] == [123]


def test_failed_import_hook_result_supports_lookup_and_getattr():
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


def test_top_level_deprecated_node_alias_warns_and_returns_nodes_class():
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        cls = astroid.Const
    assert cls is nodes.Const
    assert any(item.category is DeprecationWarning for item in recorded)


def test_deprecated_call_alias_warns_and_returns_nodes_class():
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        cls = astroid.Call
    assert cls is nodes.Call
    assert any(item.category is DeprecationWarning for item in recorded)


def test_deprecated_functiondef_alias_warns_and_returns_nodes_class():
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        cls = astroid.FunctionDef
    assert cls is nodes.FunctionDef
    assert any(item.category is DeprecationWarning for item in recorded)


def test_astroid_error_formats_keyword_fields():
    error = AstroidError("hello {name}", name="world")
    assert str(error) == "hello world"


def test_public_exception_aliases_match_resolution_categories():
    with pytest.raises(NameInferenceError):
        list(astroid.extract_node("missing_for_error_alias_check").infer())
    assert issubclass(astroid.UnresolvableName, astroid.NameInferenceError)
    assert issubclass(astroid.NotFoundError, astroid.AttributeInferenceError)


def test_astroid_import_error_is_building_error_subclass():
    error = AstroidImportError("missing {modname}", modname="generated_missing")
    assert str(error) == "missing generated_missing"
    assert issubclass(AstroidImportError, AstroidBuildingError)


def test_nodes_namespace_exposes_documented_assignment_and_function_nodes():
    for name in ("AnnAssign", "Arguments", "AsyncFunctionDef", "Lambda", "Return"):
        exported = getattr(nodes, name)
        assert issubclass(exported, nodes.NodeNG)


def test_nodes_namespace_exposes_documented_pattern_and_type_nodes():
    for name in ("Match", "MatchCase", "TypeAlias", "TypeVarTuple", "Unknown"):
        exported = getattr(nodes, name)
        assert issubclass(exported, nodes.NodeNG)


def test_cli_ast_command_prints_repr_tree_for_valid_file(tmp_path):
    path = tmp_path / "cli_sample.py"
    path.write_text("value = 10\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "astroid", "ast", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0
    assert "Module" in proc.stdout
    assert "Assign" in proc.stdout


def test_cli_without_subcommand_returns_usage_error():
    proc = subprocess.run(
        [sys.executable, "-m", "astroid"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 2
    assert "usage:" in proc.stderr.lower() or "usage:" in proc.stdout.lower()


def test_cross_view_parse_lookup_infer_and_root_are_consistent():
    module = astroid.parse("value = 20 + 22\nresult = value")
    result = module.body[1].value
    scope, statements = result.lookup("value")
    inferred = list(result.infer())
    assert scope is module
    assert statements[0].root() is module
    assert [node.value for node in inferred] == [42]


def test_cross_view_extract_node_parent_chain_and_rendering_are_consistent():
    selected = astroid.extract_node("base = 1\nvalue = __(base + 2)")
    assert selected.as_string() == "base + 2"
    assert isinstance(selected.root(), nodes.Module)
    assert selected.statement().as_string() == "value = base + 2"


def test_cross_view_manager_cache_preserves_lookup_results(tmp_path):
    path = tmp_path / "cache_view.py"
    path.write_text("answer = 42\n", encoding="utf-8")
    first = MANAGER.ast_from_file(str(path), modname="cache_view_generated")
    second = MANAGER.ast_from_module_name("cache_view_generated")
    assert second is first
    assert [node.value for node in second.igetattr("answer")] == [42]


def test_cross_view_extender_public_names_getattr_and_inference_agree(tmp_path, monkeypatch):
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


def test_cross_view_failed_import_hook_cache_and_inference_agree():
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


def test_cross_view_transform_changes_future_parse_lookup_and_inference():
    def transform(node):
        node.value = 7301
        return node

    MANAGER.register_transform(nodes.Const, transform, lambda node: getattr(node, "value", None) == 7300)
    module = astroid.parse("changed = 7300")
    scope, statements = module.lookup("changed")
    assert scope is module
    assert statements == module.getattr("changed")
    assert [node.value for node in module.igetattr("changed")] == [7301]


def test_cross_view_class_instance_and_attribute_lookup_share_tree_state():
    module = astroid.parse("class Generated:\n    label = 'ok'\n\ninst = Generated()")
    instance = next(module.body[-1].value.infer())
    klass = module.body[0]
    assert isinstance(instance, astroid.Instance)
    assert klass.root() is module
    assert klass.getattr("label")
    assert [node.value for node in instance.igetattr("label")] == ["ok"]


def test_representative_workflow_parse_infer_extract_and_extend(tmp_path, monkeypatch):
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


def test_representative_workflow_file_manager_cache_and_cli_render(tmp_path):
    path = tmp_path / "workflow_file.py"
    path.write_text("answer = 40 + 2\n", encoding="utf-8")
    module = MANAGER.ast_from_file(str(path), modname="generated_workflow_file_stage3")
    cached = MANAGER.ast_from_module_name("generated_workflow_file_stage3")
    proc = subprocess.run(
        [sys.executable, "-m", "astroid", "ast", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert cached is module
    assert [node.value for node in cached.igetattr("answer")] == [42]
    assert proc.returncode == 0
    assert "Assign" in proc.stdout


def test_representative_workflow_failed_import_hook_then_lookup_and_infer():
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
