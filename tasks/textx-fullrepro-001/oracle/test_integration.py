from pathlib import Path

import pytest

from conftest import WORKFLOW_GRAMMAR, WORKFLOW_MODEL
from textx import (
    GeneratorDesc,
    LanguageDesc,
    TextXRegistrationError,
    TextXSemanticError,
    get_children,
    get_children_of_type,
    get_location,
    get_metamodel,
    get_model,
    get_parent_of_type,
    language_for_file,
    languages_for_file,
    metamodel_for_file,
    metamodel_for_language,
    metamodel_from_file,
    metamodel_from_str,
    register_generator,
    register_language,
)
from textx.export import PlantUmlRenderer, metamodel_export, model_export


def model_summary(model):
    return {
        "project": model.project.name,
        "states": [state.name for state in model.states],
        "events": [event.name for event in model.events],
        "transitions": [transition.name for transition in model.transitions],
    }


@pytest.mark.depends_on(
    "test_metamodel_from_file_uses_local_grammar_file",
    "test_get_location_exposes_public_position_keys",
)
def test_file_based_model_preserves_values_and_filename(workflow_files):
    grammar_file, model_file = workflow_files
    model = metamodel_from_file(str(grammar_file)).model_from_file(str(model_file))
    location = get_location(model.transitions[0])
    assert model_summary(model)["transitions"] == ["t_submit", "t_approve"]
    assert Path(location["filename"]).name == "sample.workflow"


@pytest.mark.depends_on(
    "test_metamodel_from_str_parses_minimal_project",
    "test_repeated_state_order_is_preserved",
)
def test_model_from_file_and_str_share_object_graph_projection(workflow_files):
    grammar_file, model_file = workflow_files
    metamodel = metamodel_from_file(str(grammar_file))
    from_file = metamodel.model_from_file(str(model_file))
    from_str = metamodel.model_from_str(WORKFLOW_MODEL)
    assert model_summary(from_file) == model_summary(from_str)


@pytest.mark.depends_on(
    "test_metamodel_from_str_parses_minimal_project",
    "test_get_children_of_type_returns_contained_states",
)
def test_metamodel_dot_export_contains_model_classes(tmp_path):
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    output = tmp_path / "workflow.dot"
    metamodel_export(metamodel, str(output))
    text = output.read_text(encoding="utf-8")
    assert "digraph textX" in text
    assert "Workflow" in text
    assert "Transition" in text


@pytest.mark.depends_on(
    "test_metamodel_from_str_parses_minimal_project",
    "test_abstract_action_instantiates_send_variant",
)
def test_metamodel_plantuml_export_contains_action_variants(tmp_path):
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    output = tmp_path / "workflow.pu"
    metamodel_export(metamodel, str(output), renderer=PlantUmlRenderer())
    text = output.read_text(encoding="utf-8")
    assert "@startuml" in text
    assert "SendAction" in text
    assert "LogAction" in text


@pytest.mark.depends_on(
    "test_model_from_str_projects_single_value_fields",
    "test_state_references_resolve_to_named_objects",
)
def test_model_dot_export_contains_runtime_values(tmp_path, workflow_metamodel):
    model = workflow_metamodel.model_from_str(WORKFLOW_MODEL)
    output = tmp_path / "model.dot"
    model_export(model, str(output))
    text = output.read_text(encoding="utf-8")
    assert "Demo" in text
    assert "t_submit" in text
    assert "notify" in text


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_metamodel_from_str_parses_minimal_project",
)
def test_language_registration_finds_pattern_and_parses_file(
    clean_textx_registrations, workflow_files
):
    grammar_file, model_file = workflow_files
    register_language(
        LanguageDesc(
            "workflowcase",
            "*.workflow",
            "workflow language",
            lambda: metamodel_from_file(str(grammar_file)),
        )
    )
    language = language_for_file(str(model_file))
    model = metamodel_for_language(language.name).model_from_file(str(model_file))
    assert language.name == "workflowcase"
    assert model.project.name == "Demo"


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_repeated_state_order_is_preserved",
)
def test_languages_for_file_returns_all_matching_public_descriptors(
    clean_textx_registrations, workflow_metamodel
):
    register_language("firstflow", "*.flow", "first", workflow_metamodel)
    register_language("secondflow", "*.flow", "second", workflow_metamodel)
    names = sorted(language.name for language in languages_for_file("sample.flow"))
    assert names == ["firstflow", "secondflow"]


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_metamodel_from_str_parses_minimal_project",
)
def test_metamodel_for_file_uses_registered_language(clean_textx_registrations):
    register_language(
        "directflow",
        "*.direct",
        "direct metamodel",
        lambda: metamodel_from_str(WORKFLOW_GRAMMAR),
    )
    metamodel = metamodel_for_file("demo.direct")
    model = metamodel.model_from_str("project Demo 1\nstate draft initial\n")
    assert model.states[0].initial is True


@pytest.mark.depends_on(
    "test_object_processor_receives_completed_object",
    "test_get_children_predicate_can_select_events",
)
def test_processors_and_children_projection_share_event_order():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    processed = []

    def remember_event(event):
        processed.append(event.name)

    metamodel.register_obj_processors({"Event": remember_event})
    model = metamodel.model_from_str(WORKFLOW_MODEL)
    traversed = [
        event.name
        for event in get_children(lambda obj: obj.__class__.__name__ == "Event", model)
    ]
    assert processed == traversed == ["submit", "approve"]


@pytest.mark.depends_on(
    "test_object_processor_can_add_public_derived_attribute",
    "test_event_reference_resolves_to_named_object",
)
def test_processor_derived_event_values_are_visible_through_references():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)

    def derive_event(event):
        event.slug = f"{event.name}:{event.code}"

    metamodel.register_obj_processors({"Event": derive_event})
    model = metamodel.model_from_str(WORKFLOW_MODEL)
    assert [transition.event.slug for transition in model.transitions] == [
        "submit:10",
        "approve:20",
    ]


@pytest.mark.depends_on(
    "test_custom_scope_provider_can_resolve_case_insensitive_reference",
    "test_state_references_resolve_to_named_objects",
)
def test_custom_scope_provider_combines_with_default_target_resolution():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)

    def source_scope(obj, attr, obj_ref):
        for state in get_model(obj).states:
            if state.name.casefold() == obj_ref.obj_name.casefold():
                return state
        return None

    metamodel.register_scope_providers({"Transition.source": source_scope})
    model = metamodel.model_from_str(
        "project Demo 1\nstate draft\nstate review\n"
        "event submit 10\ntransition t1 from DRAFT to review on submit send \"ok\"\n"
    )
    assert model.transitions[0].source.name == "draft"
    assert model.transitions[0].target.name == "review"


@pytest.mark.depends_on(
    "test_invalid_syntax_raises_public_syntax_error",
    "test_metamodel_from_str_parses_minimal_project",
    "test_get_children_of_type_returns_contained_states",
)
def test_invalid_model_does_not_prevent_independent_metamodel_export(tmp_path):
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    with pytest.raises(TextXSemanticError):
        metamodel.model_from_str(
            "project Demo 1\nstate draft\n"
            "event submit 10\ntransition missing from draft to absent on submit log audit\n"
        )
    output = tmp_path / "after_error.dot"
    metamodel_export(metamodel, str(output))
    assert "Transition" in output.read_text(encoding="utf-8")


@pytest.mark.depends_on(
    "test_get_children_of_type_returns_contained_states",
    "test_get_parent_of_type_finds_workflow_for_transition",
)
def test_state_parent_links_and_child_collection_agree(workflow_model):
    states = get_children_of_type("State", workflow_model)
    parents = [get_parent_of_type("Workflow", state) for state in states]
    assert states == workflow_model.states
    assert parents == [workflow_model, workflow_model, workflow_model]


@pytest.mark.depends_on(
    "test_get_model_returns_root_for_nested_action",
    "test_get_metamodel_returns_originating_metamodel",
)
def test_nested_action_projects_root_and_metamodel(workflow_model):
    action = workflow_model.transitions[1].action
    assert get_model(action).project.name == "Demo"
    assert get_metamodel(action) is get_metamodel(workflow_model)


@pytest.mark.depends_on(
    "test_children_first_traversal_places_root_after_children",
    "test_repeated_state_order_is_preserved",
)
def test_should_follow_limits_containment_traversal(workflow_model):
    objects = get_children(
        lambda obj: obj.__class__.__name__ == "State",
        workflow_model,
        should_follow=lambda obj: obj.__class__.__name__ != "Transition",
    )
    assert [state.name for state in objects] == ["draft", "review", "done"]


@pytest.mark.depends_on(
    "test_integer_terminal_converts_event_codes",
    "test_metamodel_from_str_parses_minimal_project",
    "test_abstract_action_instantiates_send_variant",
)
def test_plantuml_export_and_runtime_model_share_rule_names(tmp_path, workflow_model):
    output = tmp_path / "workflow.pu"
    metamodel_export(get_metamodel(workflow_model), str(output), renderer=PlantUmlRenderer())
    text = output.read_text(encoding="utf-8")
    assert workflow_model.events[0].__class__.__name__ in text
    assert workflow_model.transitions[0].action.__class__.__name__ in text


@pytest.mark.depends_on(
    "test_metamodel_from_file_uses_local_grammar_file",
    "test_model_from_str_projects_single_value_fields",
    "test_state_references_resolve_to_named_objects",
)
def test_file_model_export_keeps_same_public_transition_names(tmp_path, workflow_files):
    grammar_file, model_file = workflow_files
    model = metamodel_from_file(str(grammar_file)).model_from_file(str(model_file))
    output = tmp_path / "file-model.dot"
    model_export(model, str(output))
    text = output.read_text(encoding="utf-8")
    assert all(name in text for name in ["t_submit", "t_approve"])


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_object_processor_can_add_public_derived_attribute",
)
def test_generator_registration_uses_parsed_model_projection(clean_textx_registrations, tmp_path):
    written = tmp_path / "summary.txt"

    def write_summary(metamodel, model, output_path, overwrite, debug):
        Path(output_path).write_text(
            f"{model.project.name}:{len(model.states)}:{len(model.transitions)}",
            encoding="utf-8",
        )

    register_generator(GeneratorDesc("workflowcase", "summary", "summary", write_summary))
    from textx import generator_for_language_target

    generator = generator_for_language_target("workflowcase", "summary")
    model = metamodel_from_str(WORKFLOW_GRAMMAR).model_from_str(WORKFLOW_MODEL)
    generator(get_metamodel(model), model, str(written), True, False)
    assert written.read_text(encoding="utf-8") == "Demo:3:2"


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_model_from_str_projects_single_value_fields",
)
def test_any_generator_fallback_uses_public_generator_lookup(clean_textx_registrations, tmp_path):
    written = tmp_path / "events.txt"

    def write_events(metamodel, model, output_path, overwrite, debug):
        Path(output_path).write_text(
            ",".join(event.name for event in model.events), encoding="utf-8"
        )

    register_generator(GeneratorDesc("any", "events", "event list", write_events))
    from textx import generator_for_language_target

    generator = generator_for_language_target("workflowcase", "events", any_permitted=True)
    model = metamodel_from_str(WORKFLOW_GRAMMAR).model_from_str(WORKFLOW_MODEL)
    generator(get_metamodel(model), model, str(written), True, False)
    assert written.read_text(encoding="utf-8") == "submit,approve"


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_metamodel_from_str_parses_minimal_project",
)
def test_duplicate_language_registration_raises_without_altering_first_entry(
    clean_textx_registrations, workflow_metamodel
):
    register_language("unique", "*.unique", "first", workflow_metamodel)
    with pytest.raises(TextXRegistrationError):
        register_language("unique", "*.other", "second", workflow_metamodel)
    assert language_for_file("sample.unique").description == "first"


@pytest.mark.depends_on(
    "test_registration_error_is_public_exception",
    "test_metamodel_from_str_parses_minimal_project",
)
def test_duplicate_generator_registration_keeps_first_generator(
    clean_textx_registrations, workflow_model
):
    calls = []

    def first(metamodel, model, output_path, overwrite, debug):
        calls.append(model.project.name)

    def second(metamodel, model, output_path, overwrite, debug):
        calls.append(output_path)

    register_generator(GeneratorDesc("workflowcase", "audit", "first", first))
    with pytest.raises(TextXRegistrationError):
        register_generator(GeneratorDesc("workflowcase", "audit", "second", second))
    from textx import generator_for_language_target

    generator_for_language_target("workflowcase", "audit")(
        get_metamodel(workflow_model), workflow_model, "unused", True, False
    )
    assert calls == ["Demo"]


@pytest.mark.depends_on(
    "test_state_references_resolve_to_named_objects",
    "test_get_children_predicate_can_select_events",
)
def test_cross_references_are_not_duplicated_by_containment_traversal(workflow_model):
    objects = get_children(lambda obj: obj.__class__.__name__ in {"State", "Event"}, workflow_model)
    labels = [(obj.__class__.__name__, obj.name) for obj in objects]
    assert labels == [
        ("State", "draft"),
        ("State", "review"),
        ("State", "done"),
        ("Event", "submit"),
        ("Event", "approve"),
    ]


@pytest.mark.depends_on(
    "test_string_terminal_unquotes_message",
    "test_abstract_action_instantiates_log_variant",
)
def test_action_variants_share_transition_projection(workflow_model):
    projection = [
        (transition.name, transition.action.__class__.__name__)
        for transition in workflow_model.transitions
    ]
    assert projection == [("t_submit", "SendAction"), ("t_approve", "LogAction")]


@pytest.mark.depends_on(
    "test_boolean_assignment_sets_true_and_false",
    "test_repeated_state_order_is_preserved",
)
def test_state_flags_and_order_survive_file_round_trip(workflow_files):
    grammar_file, model_file = workflow_files
    model = metamodel_from_file(str(grammar_file)).model_from_file(str(model_file))
    assert [(state.name, state.initial) for state in model.states] == [
        ("draft", True),
        ("review", False),
        ("done", False),
    ]


@pytest.mark.depends_on(
    "test_get_location_exposes_public_position_keys",
    "test_model_from_str_projects_single_value_fields",
)
def test_locations_align_with_project_and_transition_lines(workflow_model):
    project_location = get_location(workflow_model.project)
    transition_location = get_location(workflow_model.transitions[0])
    assert project_location["line"] < transition_location["line"]
    assert project_location["filename"] == transition_location["filename"]


@pytest.mark.depends_on(
    "test_object_processor_receives_completed_object",
    "test_unresolved_reference_raises_public_semantic_error",
)
def test_processor_can_raise_public_semantic_error_for_model_policy():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)

    def require_even_code(event):
        if event.code % 2:
            raise TextXSemanticError("odd event code")

    metamodel.register_obj_processors({"Event": require_even_code})
    with pytest.raises(TextXSemanticError):
        metamodel.model_from_str("project Demo 1\nstate draft\nevent odd 11\n")


@pytest.mark.depends_on("test_metamodel_from_file_uses_local_grammar_file")
def test_cli_check_accepts_grammar_and_valid_model(workflow_files):
    from click.testing import CliRunner
    from textx.cli import textx

    grammar_file, model_file = workflow_files
    result = CliRunner().invoke(
        textx,
        ["check", "--grammar", str(grammar_file), str(model_file)],
    )
    assert result.exit_code == 0


@pytest.mark.depends_on("test_invalid_syntax_raises_public_syntax_error")
def test_cli_check_rejects_invalid_model(workflow_files, tmp_path):
    import logging

    from click.testing import CliRunner
    from textx.cli import textx

    grammar_file, _ = workflow_files
    invalid_model = tmp_path / "invalid.workflow"
    invalid_model.write_text("project Demo\n", encoding="utf-8")
    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        result = CliRunner().invoke(
            textx,
            ["check", "--grammar", str(grammar_file), str(invalid_model)],
        )
    finally:
        logging.disable(previous_disable_level)
    assert result.exit_code != 0


@pytest.mark.depends_on("test_metamodel_from_file_uses_local_grammar_file")
def test_cli_check_validates_a_grammar_file(workflow_files):
    from click.testing import CliRunner
    from textx.cli import textx

    grammar_file, _ = workflow_files
    result = CliRunner().invoke(textx, ["check", str(grammar_file)])
    assert result.exit_code == 0
