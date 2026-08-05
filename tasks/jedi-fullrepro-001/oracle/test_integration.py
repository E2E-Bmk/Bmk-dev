from __future__ import annotations

import pytest

from jedi import Interpreter, Project, RefactoringError, Script


@pytest.mark.depends_on(
    "test_infer_resolves_local_factory_to_instance",
    "test_project_properties_preserve_explicit_configuration",
)
def test_file_and_project_views_agree_on_factory(app_script, project_tree):
    inferred = app_script.infer(4, 0)[0]
    searched = next(project_tree["project"].search("Greeter"))

    assert inferred.full_name == searched.full_name == "lib.Greeter"
    assert inferred.type == "instance"
    assert searched.type == "class"


@pytest.mark.depends_on(
    "test_completion_exposes_name_remainder_and_prefix",
    "test_infer_resolves_local_factory_to_instance",
)
def test_completion_and_inference_share_local_class_member(project_tree):
    script = Script(
        "from lib import Greeter\nGreeter().gr",
        project=project_tree["project"],
    )
    completion = next(result for result in script.complete() if result.name == "greet")
    inferred = script.infer(2, 0)[0]

    assert completion.type == "function"
    assert inferred.full_name == "lib.Greeter"
    assert inferred.type == "class"


@pytest.mark.depends_on(
    "test_reference_result_exposes_its_source_line",
    "test_script_search_returns_public_name_results",
)
def test_reference_search_matches_local_assignment_and_use(app_script):
    references = app_script.get_references(4, 0)
    searched = list(app_script.search("person"))

    assert searched[0].name == references[0].name == "person"
    assert searched[0].line == references[0].line == 4
    assert any(reference.line == 5 for reference in references)


@pytest.mark.depends_on(
    "test_goto_follow_imports_reaches_local_definition",
    "test_project_properties_preserve_explicit_configuration",
)
def test_project_search_finds_definition_used_by_script(app_script, project_tree):
    searched = next(project_tree["project"].search("make_greeter"))
    reached = app_script.goto(6, 9, follow_imports=True)[0]

    assert searched.full_name == reached.full_name == "lib.make_greeter"
    assert searched.type == reached.type == "function"


@pytest.mark.depends_on(
    "test_infer_resolves_repeat_alias_to_local_function",
    "test_project_properties_preserve_explicit_configuration",
)
def test_repeat_alias_inference_matches_project_factory_search(app_script, project_tree):
    inferred = app_script.infer(6, 0)[0]
    searched = next(project_tree["project"].search("make_greeter"))

    assert inferred.full_name == searched.full_name == "lib.make_greeter"
    assert inferred.type == searched.type == "function"
    assert inferred.module_path == searched.module_path == project_tree["lib"]


@pytest.mark.depends_on(
    "test_script_complete_search_returns_a_completion_remainder",
    "test_get_names_all_scopes_includes_class_members",
)
def test_project_and_script_complete_search_share_local_members(lib_script, project_tree):
    script_results = {
        result.name: result.complete
        for result in lib_script.complete_search("gree", all_scopes=True)
    }
    project_results = {
        result.name: result.complete
        for result in project_tree["project"].complete_search("gree", all_scopes=True)
    }

    assert script_results == project_results == {"Greeter": "ter", "greet": "t"}


@pytest.mark.depends_on(
    "test_class_name_defined_names_lists_public_members",
    "test_project_properties_preserve_explicit_configuration",
)
def test_project_search_all_scopes_finds_a_class_method(lib_script, project_tree):
    results = list(project_tree["project"].search("greet", all_scopes=True))
    local = next(result for result in results if result.full_name == "lib.Greeter.greet")
    class_result = next(iter(lib_script.search("Greeter")))

    assert local.type == "function"
    assert local.name == "greet"
    assert class_result.type == "class"


@pytest.mark.depends_on("test_project_properties_preserve_explicit_configuration")
def test_project_save_load_round_trip_preserves_public_properties(project_tree):
    original = Project(
        project_tree["root"],
        sys_path=[str(project_tree["root"] / "extra")],
        smart_sys_path=False,
    )
    original.save()
    loaded = Project.load(project_tree["root"])

    assert loaded.path == original.path
    assert loaded.sys_path == original.sys_path
    assert loaded.smart_sys_path is False
    assert loaded.load_unsafe_extensions is False


@pytest.mark.depends_on(
    "test_name_module_path_points_to_the_local_module",
    "test_project_properties_preserve_explicit_configuration",
)
def test_project_search_module_and_class_views_share_a_file(project_tree):
    module = next(
        result
        for result in project_tree["project"].search("lib")
        if result.type == "module"
    )
    cls = next(
        result
        for result in project_tree["project"].search("Greeter")
        if result.type == "class"
    )

    assert module.full_name == "lib"
    assert cls.full_name == "lib.Greeter"
    assert module.module_path == cls.module_path == project_tree["lib"]


@pytest.mark.depends_on(
    "test_interpreter_completion_reads_a_namespace_value",
    "test_fuzzy_completion_has_no_literal_remainder",
)
def test_interpreter_and_script_views_agree_on_string_members(
    interpreter_namespace, project_tree
):
    interpreter_names = {
        result.name for result in Interpreter("message.up", [interpreter_namespace]).complete()
    }
    script_names = {
        result.name
        for result in Script('value = "hello"\nvalue.up', project=project_tree["project"]).complete(
            fuzzy=True
        )
    }

    assert "upper" in interpreter_names
    assert "upper" in script_names


@pytest.mark.depends_on(
    "test_signature_exposes_index_bracket_and_text",
    "test_interpreter_infer_reads_a_namespace_value",
)
def test_interpreter_signature_and_script_signature_share_parameter_shape(
    interpreter_namespace, signature_script
):
    interpreter_signature = Interpreter(
        "greet(", [interpreter_namespace]
    ).get_signatures()[0]
    script_signature = signature_script.get_signatures()[0]

    assert interpreter_signature.name == "namespace_greet"
    assert script_signature.name == "greet"
    assert [param.name for param in interpreter_signature.params] == [
        "name",
        "count",
    ]
    assert [param.name for param in script_signature.params] == ["name", "count"]


@pytest.mark.depends_on(
    "test_signature_parameter_defaults_infer_public_types",
    "test_signature_parameter_annotations_infer_public_types",
)
def test_signature_defaults_and_annotations_project_the_same_types(signature_script):
    signature = signature_script.get_signatures()[0]

    for param in signature.params:
        assert param.infer_default()[0].name == param.infer_annotation()[0].name


@pytest.mark.depends_on(
    "test_name_raw_docstring_is_the_local_function_documentation",
    "test_name_definition_positions_cover_the_function",
)
def test_search_and_goto_share_docstring_and_definition_position(app_script, project_tree):
    searched = next(project_tree["project"].search("make_greeter"))
    reached = app_script.goto(6, 9, follow_imports=True)[0]

    assert searched.docstring(raw=True) == reached.docstring(raw=True) == "Build a greeter."
    assert searched.get_definition_start_position() == reached.get_definition_start_position()
    assert searched.get_definition_end_position() == reached.get_definition_end_position()


@pytest.mark.depends_on(
    "test_goto_without_follow_imports_stays_at_local_reference",
    "test_reference_result_exposes_its_source_line",
)
def test_refactor_rename_changes_all_local_references(app_script, project_tree):
    refactoring = app_script.rename(4, 0, new_name="primary")
    changed = refactoring.get_changed_files()[project_tree["app"]]
    code = changed.get_new_code()

    assert "primary = make_greeter" in code
    assert "message = primary.greet" in code
    assert "person" not in code


@pytest.mark.depends_on(
    "test_goto_without_follow_imports_stays_at_local_reference",
    "test_reference_result_exposes_its_source_line",
    "test_name_get_line_code_returns_the_definition_line",
)
def test_refactor_rename_diff_describes_the_changed_file(app_script, project_tree):
    refactoring = app_script.rename(4, 0, new_name="primary")
    diff = refactoring.get_diff()

    assert str(project_tree["app"].name) in diff
    assert "-person = make_greeter" in diff
    assert "+primary = make_greeter" in diff


@pytest.mark.depends_on(
    "test_goto_without_follow_imports_stays_at_local_reference",
    "test_reference_result_exposes_its_source_line",
)
def test_refactor_rename_apply_updates_file_and_references(app_script, project_tree):
    refactoring = app_script.rename(4, 0, new_name="primary")
    refactoring.apply()

    assert "primary = make_greeter" in project_tree["app"].read_text(encoding="utf-8")
    updated = Script(path=project_tree["app"], project=project_tree["project"])
    assert {result.name for result in updated.get_references(4, 0)} == {
        "primary"
    }


@pytest.mark.depends_on(
    "test_project_properties_preserve_explicit_configuration",
    "test_name_definition_positions_cover_the_function",
)
def test_refactor_extract_variable_projects_statement_and_diff(project_tree):
    script = Script(path=project_tree["calc"], project=project_tree["project"])
    refactoring = script.extract_variable(
        4,
        13,
        new_name="combined",
        until_line=4,
        until_column=27,
    )
    changed = refactoring.get_changed_files()[project_tree["calc"]]

    assert "combined = first + second" in changed.get_new_code()
    assert "result = combined" in changed.get_new_code()
    assert "+    combined = first + second" in changed.get_diff()


@pytest.mark.depends_on(
    "test_project_properties_preserve_explicit_configuration",
    "test_name_definition_positions_cover_the_function",
)
def test_refactor_extract_variable_apply_updates_file(project_tree):
    script = Script(path=project_tree["calc"], project=project_tree["project"])
    refactoring = script.extract_variable(
        4,
        13,
        new_name="combined",
        until_line=4,
        until_column=27,
    )
    refactoring.apply()

    code = project_tree["calc"].read_text(encoding="utf-8")
    assert "combined = first + second" in code
    assert "result = combined" in code


@pytest.mark.depends_on(
    "test_project_properties_preserve_explicit_configuration",
    "test_name_definition_positions_cover_the_function",
)
def test_refactor_extract_function_projects_helper_and_call(project_tree):
    script = Script(path=project_tree["calc"], project=project_tree["project"])
    refactoring = script.extract_function(
        4,
        13,
        new_name="add_values",
        until_line=4,
        until_column=27,
    )
    changed = refactoring.get_changed_files()[project_tree["calc"]]

    assert "def add_values(first, second):" in changed.get_new_code()
    assert "return first + second" in changed.get_new_code()
    assert "result = add_values(first, second)" in changed.get_new_code()


@pytest.mark.depends_on(
    "test_project_properties_preserve_explicit_configuration",
    "test_name_definition_positions_cover_the_function",
)
def test_refactor_extract_function_apply_updates_file(project_tree):
    script = Script(path=project_tree["calc"], project=project_tree["project"])
    refactoring = script.extract_function(
        4,
        13,
        new_name="add_values",
        until_line=4,
        until_column=27,
    )
    refactoring.apply()

    code = project_tree["calc"].read_text(encoding="utf-8")
    assert "def add_values(first, second):" in code
    assert "result = add_values(first, second)" in code


@pytest.mark.depends_on(
    "test_project_properties_preserve_explicit_configuration",
    "test_name_definition_positions_cover_the_function",
)
def test_changed_file_methods_expose_code_and_no_renames(project_tree):
    script = Script(path=project_tree["calc"], project=project_tree["project"])
    refactoring = script.extract_variable(
        4,
        13,
        new_name="combined",
        until_line=4,
        until_column=27,
    )
    changed = refactoring.get_changed_files()[project_tree["calc"]]

    assert changed.get_new_code() != project_tree["calc"].read_text(encoding="utf-8")
    assert "--- calc.py" in changed.get_diff()
    assert refactoring.get_renames() == []


@pytest.mark.depends_on("test_goto_without_follow_imports_stays_at_local_reference")
def test_refactoring_without_a_path_raises_the_public_error_type(tmp_path):
    project = Project(tmp_path, sys_path=[], smart_sys_path=False)
    refactoring = Script("value = 1\nvalue", project=project).rename(
        2, 0, new_name="other"
    )

    with pytest.raises(RefactoringError):
        refactoring.apply()


@pytest.mark.depends_on(
    "test_project_properties_preserve_explicit_configuration",
    "test_goto_follow_imports_reaches_local_definition",
)
def test_saved_project_still_resolves_local_imports(project_tree):
    project = Project(
        project_tree["root"],
        sys_path=[str(project_tree["root"])],
        smart_sys_path=False,
    )
    project.save()
    loaded = Project.load(project_tree["root"])
    result = Script(path=project_tree["app"], project=loaded).goto(
        6, 9, follow_imports=True
    )[0]

    assert result.full_name == "lib.make_greeter"
    assert result.module_path == project_tree["lib"]


@pytest.mark.depends_on(
    "test_script_search_returns_public_name_results",
    "test_script_complete_search_returns_a_completion_remainder",
)
def test_file_search_and_completion_share_the_written_module(app_script):
    searched = list(app_script.search("message"))
    completed = list(app_script.complete_search("mess"))

    assert searched[0].name == completed[0].name == "message"
    assert searched[0].line == completed[0].line == 5
    assert completed[0].complete == "age"


@pytest.mark.depends_on(
    "test_script_search_imported_factory_keeps_import_location",
    "test_script_complete_search_returns_a_completion_remainder",
)
def test_import_search_and_completion_share_factory_identity(app_script):
    searched = next(iter(app_script.search("make_greeter")))
    completed = next(iter(app_script.complete_search("make")))

    assert searched.name == completed.name == "make_greeter"
    assert searched.full_name == completed.full_name == "lib.make_greeter"
    assert searched.type == completed.type == "function"
    assert searched.line == completed.line == 2
    assert completed.complete == "_greeter"


@pytest.mark.depends_on(
    "test_reference_result_exposes_its_source_line",
    "test_name_module_path_points_to_the_local_module",
)
def test_reference_scope_distinguishes_file_and_project_views(app_script, project_tree):
    file_results = app_script.get_references(2, 18, scope="file")
    project_results = app_script.get_references(2, 18, scope="project")
    file_paths = {result.module_path for result in file_results if result.module_path}
    project_paths = {result.module_path for result in project_results if result.module_path}

    assert file_paths <= {project_tree["app"]}
    assert project_tree["lib"] in project_paths


@pytest.mark.depends_on(
    "test_goto_follow_imports_reaches_local_definition",
    "test_name_public_attributes_describe_a_local_definition",
)
def test_search_and_reference_results_share_factory_identity(app_script, project_tree):
    reference = next(
        result
        for result in app_script.get_references(6, 9)
        if result.module_path == project_tree["lib"]
    )
    searched = next(project_tree["project"].search("make_greeter"))

    assert (reference.name, reference.full_name, reference.type) == (
        searched.name,
        searched.full_name,
        searched.type,
    )


@pytest.mark.depends_on(
    "test_script_complete_search_returns_a_completion_remainder",
    "test_name_raw_docstring_is_the_local_function_documentation",
)
def test_project_completion_exposes_public_result_attributes(project_tree):
    result = next(
        result
        for result in project_tree["project"].complete_search("gree", all_scopes=True)
        if result.name == "greet"
    )

    assert result.complete == "t"
    assert result.type == "function"
    assert result.docstring(raw=True) == "Return a greeting."


@pytest.mark.depends_on(
    "test_goto_follow_imports_reaches_local_definition",
    "test_name_module_path_points_to_the_local_module",
)
def test_project_search_and_script_goto_share_module_identity(app_script, project_tree):
    searched = next(project_tree["project"].search("make_greeter"))
    reached = app_script.goto(6, 9, follow_imports=True)[0]

    assert searched.module_name == reached.module_name == "lib"
    assert searched.full_name == reached.full_name
    assert searched.module_path == reached.module_path == project_tree["lib"]


@pytest.mark.depends_on(
    "test_name_definition_positions_cover_the_function",
    "test_goto_follow_imports_reaches_local_definition",
)
def test_search_and_goto_ranges_are_consistent(app_script, project_tree):
    searched = next(project_tree["project"].search("make_greeter"))
    reached = app_script.goto(6, 9, follow_imports=True)[0]

    assert (searched.line, searched.column) == (reached.line, reached.column) == (11, 4)
    assert searched.get_definition_start_position() == (11, 0)
    assert searched.get_definition_end_position() == (13, 24)
