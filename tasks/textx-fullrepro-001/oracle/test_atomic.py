import pytest

from conftest import WORKFLOW_GRAMMAR, WORKFLOW_MODEL
from textx import (
    TextXRegistrationError,
    TextXSemanticError,
    TextXSyntaxError,
    get_children,
    get_children_of_type,
    get_location,
    get_metamodel,
    get_model,
    get_parent_of_type,
    metamodel_from_file,
    metamodel_from_str,
    textx_isinstance,
)


def state_names(model):
    return [state.name for state in model.states]


def transition_names(model):
    return [transition.name for transition in model.transitions]


def test_metamodel_from_str_parses_minimal_project(workflow_metamodel):
    model = workflow_metamodel.model_from_str("project Solo 7\nstate start initial\n")
    assert model.project.name == "Solo"
    assert model.states[0].name == "start"


def test_model_from_str_projects_single_value_fields(workflow_model):
    assert workflow_model.project.name == "Demo"
    assert workflow_model.project.version == 1


def test_repeated_state_order_is_preserved(workflow_model):
    assert state_names(workflow_model) == ["draft", "review", "done"]


def test_boolean_assignment_sets_true_and_false(workflow_model):
    assert [state.initial for state in workflow_model.states] == [True, False, False]


def test_integer_terminal_converts_event_codes(workflow_model):
    assert [event.code for event in workflow_model.events] == [10, 20]


def test_string_terminal_unquotes_message(workflow_model):
    assert workflow_model.transitions[0].action.message == "notify"


def test_abstract_action_instantiates_send_variant(workflow_model):
    assert workflow_model.transitions[0].action.__class__.__name__ == "SendAction"


def test_abstract_action_instantiates_log_variant(workflow_model):
    assert workflow_model.transitions[1].action.__class__.__name__ == "LogAction"


def test_state_references_resolve_to_named_objects(workflow_model):
    transition = workflow_model.transitions[0]
    assert transition.source is workflow_model.states[0]
    assert transition.target is workflow_model.states[1]


def test_event_reference_resolves_to_named_object(workflow_model):
    assert workflow_model.transitions[1].event is workflow_model.events[1]


def test_get_children_of_type_returns_contained_states(workflow_model):
    assert [state.name for state in get_children_of_type("State", workflow_model)] == [
        "draft",
        "review",
        "done",
    ]


def test_get_children_predicate_can_select_events(workflow_model):
    events = get_children(lambda obj: obj.__class__.__name__ == "Event", workflow_model)
    assert [event.name for event in events] == ["submit", "approve"]


def test_children_first_traversal_places_root_after_children(workflow_model):
    objects = get_children(lambda obj: True, workflow_model, children_first=True)
    assert objects[-1] is workflow_model
    assert workflow_model.states[0] in objects[:3]


def test_get_parent_of_type_finds_workflow_for_transition(workflow_model):
    assert get_parent_of_type("Workflow", workflow_model.transitions[0]) is workflow_model


def test_get_model_returns_root_for_nested_action(workflow_model):
    assert get_model(workflow_model.transitions[0].action) is workflow_model


def test_get_metamodel_returns_originating_metamodel(workflow_metamodel, workflow_model):
    assert get_metamodel(workflow_model.transitions[0]) is workflow_metamodel


def test_get_location_exposes_public_position_keys(workflow_model):
    location = get_location(workflow_model.transitions[0])
    assert set(location) == {"line", "col", "nchar", "filename"}
    assert location["line"] > 0
    assert location["col"] > 0


def test_textx_isinstance_accepts_dynamic_rule_class(workflow_model):
    state_class = workflow_model.states[0].__class__
    assert textx_isinstance(workflow_model.states[1], state_class)


def test_invalid_syntax_raises_public_syntax_error(workflow_metamodel):
    with pytest.raises(TextXSyntaxError):
        workflow_metamodel.model_from_str("project Demo\nstate draft\n")


def test_unresolved_reference_raises_public_semantic_error(workflow_metamodel):
    with pytest.raises(TextXSemanticError):
        workflow_metamodel.model_from_str(
            "project Demo 1\nstate draft\n"
            "event submit 10\n"
            "transition missing from draft to absent on submit log audit\n"
        )


def test_object_processor_receives_completed_object():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    seen = []

    def remember_event(event):
        seen.append((event.name, event.code))

    metamodel.register_obj_processors({"Event": remember_event})
    metamodel.model_from_str(WORKFLOW_MODEL)
    assert seen == [("submit", 10), ("approve", 20)]


def test_object_processor_can_add_public_derived_attribute():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)

    def derive_event(event):
        event.slug = f"{event.name}:{event.code}"

    metamodel.register_obj_processors({"Event": derive_event})
    model = metamodel.model_from_str(WORKFLOW_MODEL)
    assert [event.slug for event in model.events] == ["submit:10", "approve:20"]


def test_model_processor_receives_completed_model_and_metamodel():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    seen = []

    def remember_model(model, originating_metamodel):
        seen.append((model.project.name, originating_metamodel is metamodel))

    metamodel.register_model_processor(remember_model)
    metamodel.model_from_str(WORKFLOW_MODEL)
    assert seen == [("Demo", True)]


def test_object_processor_return_replaces_public_object_value():
    grammar = """
    Model: values*=Value;
    Value: value=INT;
    """
    metamodel = metamodel_from_str(grammar)
    metamodel.register_obj_processors({"Value": lambda value: value.value * 2})
    model = metamodel.model_from_str("3 4")
    assert model.values == [6, 8]


def test_custom_scope_provider_can_resolve_case_insensitive_reference():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)

    def casefold_state_scope(obj, attr, obj_ref):
        root = get_model(obj)
        for state in root.states:
            if state.name.casefold() == obj_ref.obj_name.casefold():
                return state
        return None

    metamodel.register_scope_providers({"Transition.source": casefold_state_scope})
    model = metamodel.model_from_str(
        "project Demo 1\nstate draft\nstate review\n"
        "event submit 10\ntransition t1 from DRAFT to review on submit log audit\n"
    )
    assert model.transitions[0].source is model.states[0]


def test_metamodel_from_file_uses_local_grammar_file(workflow_files):
    grammar_file, model_file = workflow_files
    metamodel = metamodel_from_file(str(grammar_file))
    model = metamodel.model_from_file(str(model_file))
    assert transition_names(model) == ["t_submit", "t_approve"]


def test_registration_error_is_public_exception(clean_textx_registrations):
    from textx import language_for_file

    with pytest.raises(TextXRegistrationError):
        language_for_file("missing.workflow")


def test_metamodel_rule_lookup_exposes_dynamic_rule_class(
    workflow_metamodel, workflow_model
):
    state_class = workflow_metamodel["State"]

    assert state_class.__name__ == "State"
    assert textx_isinstance(workflow_model.states[0], state_class)


def test_ignore_case_accepts_keyword_case_without_changing_identifier():
    metamodel = metamodel_from_str("Root: 'project' name=ID;", ignore_case=True)

    model = metamodel.model_from_str("PROJECT Demo")

    assert model.name == "Demo"


def test_custom_user_class_receives_parent_and_typed_values():
    class Point:
        def __init__(self, parent, x, y):
            self.parent = parent
            self.x = x
            self.y = y

    metamodel = metamodel_from_str(
        "Root: point=Point; Point: x=INT ',' y=INT;",
        classes=[Point],
    )
    model = metamodel.model_from_str("4,7")

    assert isinstance(model.point, Point)
    assert (model.point.x, model.point.y) == (4, 7)
    assert model.point.parent is model


def test_model_from_str_file_name_projects_public_location_filename():
    metamodel = metamodel_from_str(WORKFLOW_GRAMMAR)
    model = metamodel.model_from_str(WORKFLOW_MODEL, file_name="memory.workflow")

    location = get_location(model.transitions[0])

    assert location["filename"].endswith("memory.workflow")
    assert location["line"] == 8
