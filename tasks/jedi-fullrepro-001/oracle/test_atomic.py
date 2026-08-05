from __future__ import annotations

from jedi import Interpreter, Project, Script


def test_script_can_open_local_project_file(app_script, project_tree):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert result.name == "make_greeter"
    assert result.module_path == project_tree["lib"]


def test_infer_resolves_local_factory_to_instance(app_script):
    result = app_script.infer(4, 0)[0]

    assert result.name == "Greeter"
    assert result.type == "instance"
    assert result.full_name == "lib.Greeter"


def test_infer_resolves_repeat_alias_to_local_function(app_script, project_tree):
    result = app_script.infer(6, 0)[0]

    assert result.name == "make_greeter"
    assert result.type == "function"
    assert result.full_name == "lib.make_greeter"
    assert result.module_path == project_tree["lib"]


def test_goto_without_follow_imports_stays_at_local_reference(app_script):
    result = app_script.goto(4, 0)[0]

    assert result.name == "person"
    assert result.line == 4
    assert result.column == 0


def test_goto_follow_imports_reaches_local_definition(app_script, project_tree):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert result.name == "make_greeter"
    assert result.type == "function"
    assert result.line == 11
    assert result.column == 4
    assert result.module_path == project_tree["lib"]


def test_name_public_attributes_describe_a_local_definition(app_script):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert (
        result.name,
        result.type,
        result.full_name,
        result.line,
        result.column,
    ) == (
        "make_greeter",
        "function",
        "lib.make_greeter",
        11,
        4,
    )
    assert isinstance(result.description, str)
    assert result.description


def test_name_definition_positions_cover_the_function(app_script):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert result.get_definition_start_position() == (11, 0)
    assert result.get_definition_end_position() == (13, 24)


def test_name_raw_docstring_is_the_local_function_documentation(app_script):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert result.docstring(raw=True) == "Build a greeter."


def test_name_get_line_code_returns_the_definition_line(app_script):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert result.get_line_code() == 'def make_greeter(name: str = "Ada") -> Greeter:\n'


def test_name_parent_reports_the_module_scope():
    result = Script("class Local:\n    pass\nLocal").goto()[0]

    assert result.parent().type == "module"


def test_class_name_defined_names_lists_public_members(app_script):
    result = app_script.goto(2, 18, follow_imports=True)[0]

    assert result.type == "class"
    assert {"__init__", "greet"} <= {name.name for name in result.defined_names()}


def test_reference_result_exposes_its_source_line(app_script):
    references = app_script.get_references(4, 0)
    use = next(reference for reference in references if reference.line == 5)

    assert use.name == "person"
    assert use.get_line_code() == 'message = person.greet("Hi")\n'


def test_name_module_path_points_to_the_local_module(app_script, project_tree):
    result = app_script.goto(6, 9, follow_imports=True)[0]

    assert result.module_path == project_tree["lib"]
    assert result.module_name == "lib"


def test_script_search_returns_public_name_results(app_script):
    results = list(app_script.search("person"))

    assert [(result.name, result.type, result.line) for result in results] == [
        ("person", "statement", 4)
    ]


def test_script_search_imported_factory_keeps_import_location(app_script, project_tree):
    result = next(iter(app_script.search("make_greeter")))

    assert result.name == "make_greeter"
    assert result.type == "function"
    assert result.full_name == "lib.make_greeter"
    assert (result.line, result.column) == (2, 25)
    assert result.module_path == project_tree["app"]


def test_script_complete_search_returns_a_completion_remainder(app_script):
    results = list(app_script.complete_search("per"))

    assert [(result.name, result.complete, result.type) for result in results] == [
        ("person", "son", "statement")
    ]


def test_completion_exposes_name_remainder_and_prefix(project_tree):
    script = Script(
        "from lib import Greeter\nGreeter().gr",
        project=project_tree["project"],
    )
    result = next(completion for completion in script.complete() if completion.name == "greet")

    assert result.complete == "eet"
    assert result.name_with_symbols == "greet"
    assert result.type == "function"
    assert result.get_completion_prefix_length() == 2


def test_fuzzy_completion_has_no_literal_remainder(project_tree):
    script = Script('value = "hello"\nvalue.up', project=project_tree["project"])
    results = script.complete(fuzzy=True)

    assert "upper" in {result.name for result in results}
    assert all(result.complete is None for result in results)


def test_signature_exposes_index_bracket_and_text(signature_script):
    signature = signature_script.get_signatures()[0]

    assert signature.name == "greet"
    assert signature.type == "function"
    assert signature.index == 1
    assert signature.bracket_start == (3, 5)
    assert signature.to_string() == 'greet(name: str="Ada", count: int=1) -> str'


def test_signature_parameters_expose_names_and_kinds(signature_script):
    signature = signature_script.get_signatures()[0]

    assert [param.name for param in signature.params] == ["name", "count"]
    assert [param.kind.name for param in signature.params] == [
        "POSITIONAL_OR_KEYWORD",
        "POSITIONAL_OR_KEYWORD",
    ]
    assert [param.to_string() for param in signature.params] == [
        'name: str="Ada"',
        "count: int=1",
    ]


def test_signature_parameter_defaults_infer_public_types(signature_script):
    signature = signature_script.get_signatures()[0]

    inferred = [param.infer_default()[0] for param in signature.params]

    assert [(value.name, value.type) for value in inferred] == [
        ("str", "instance"),
        ("int", "instance"),
    ]


def test_signature_parameter_annotations_infer_public_types(signature_script):
    signature = signature_script.get_signatures()[0]

    inferred = [param.infer_annotation()[0] for param in signature.params]

    assert [(value.name, value.type) for value in inferred] == [
        ("str", "instance"),
        ("int", "instance"),
    ]


def test_get_context_identifies_the_application_module(app_script):
    context = app_script.get_context(4, 0)

    assert context.name == "app"
    assert context.type == "module"


def test_get_names_returns_top_level_definitions(app_script):
    names = app_script.get_names()

    assert {name.name for name in names} == {
        "Greeter",
        "make_greeter",
        "person",
        "message",
        "repeat",
    }


def test_get_names_all_scopes_includes_class_members(lib_script):
    names = lib_script.get_names(all_scopes=True)

    assert {"Greeter", "__init__", "greet", "make_greeter"} <= {
        name.name for name in names
    }


def test_syntax_error_result_exposes_public_positions():
    result = Script("def bad(:\n    pass").get_syntax_errors()[0]

    assert (result.line, result.column) == (1, 8)
    assert (result.until_line, result.until_column) == (1, 9)


def test_valid_local_source_has_no_syntax_errors(project_tree):
    script = Script(path=project_tree["lib"], project=project_tree["project"])

    assert script.get_syntax_errors() == []


def test_interpreter_completion_reads_a_namespace_value(interpreter_namespace):
    results = Interpreter("message.up", [interpreter_namespace]).complete()

    upper = next(result for result in results if result.name == "upper")
    assert upper.type == "function"
    assert upper.complete == "per"


def test_interpreter_infer_reads_a_namespace_value(interpreter_namespace):
    result = Interpreter("message", [interpreter_namespace]).infer()[0]

    assert result.name == "str"
    assert result.type == "instance"


def test_project_properties_preserve_explicit_configuration(project_tree):
    project = project_tree["project"]

    assert project.path == project_tree["root"]
    assert project.sys_path == [str(project_tree["root"])]
    assert project.smart_sys_path is False
    assert project.load_unsafe_extensions is False
