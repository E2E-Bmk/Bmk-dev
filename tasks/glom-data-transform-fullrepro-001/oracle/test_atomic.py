from __future__ import annotations

import pytest

from glom import (
    A,
    And,
    Assign,
    Check,
    CheckError,
    Coalesce,
    CoalesceError,
    Delete,
    Flatten,
    GlomError,
    Glommer,
    Inspect,
    Invoke,
    M,
    Match,
    MatchError,
    Not,
    Or,
    Path,
    PathAccessError,
    PathDeleteError,
    Regex,
    S,
    Spec,
    STOP,
    Switch,
    T,
    TypeMatchError,
    Val,
    assign,
    delete,
    flatten,
    glom,
)


def test_public_import_surface_exposes_transformers_and_errors():
    assert callable(glom)
    assert all(
        callable(value)
        for value in (assign, delete, flatten)
    )
    assert all(
        isinstance(value, type)
        for value in (
            Path,
            Coalesce,
            Invoke,
            Assign,
            Delete,
            Switch,
            Flatten,
            Match,
            Check,
            GlomError,
            PathAccessError,
        )
    )


def test_path_accesses_literal_keys_and_list_positions():
    key = ("literal", 4)
    target = {"outer": {key: ["zero", "one", "two"]}}
    assert glom(target, Path("outer", key, 1)) == "one"


def test_path_supports_length_values_items_and_slicing():
    path = Path("profile", "scores", 1)
    assert len(path) == 3
    assert path.values() == ("profile", "scores", 1)
    assert path.items()[-1] == ("P", 1)
    assert path[:2] == Path("profile", "scores")


def test_t_and_s_project_target_and_scope_values():
    target = {"left": 3, "right": 4}
    spec = (S(total=T["left"] + T["right"]), {"total": S.total})
    assert glom(target, spec) == {"total": 7}


def test_t_can_call_object_methods_and_slice_values(object_record):
    assert glom(object_record, T.label(prefix="acct:")) == "acct:Ada"
    assert glom(object_record, T.values[1:]) == [5, 8]


def test_val_preserves_literal_strings_in_constructed_output():
    target = {"name": "Ada"}
    assert glom(target, {"name": "name", "literal": Val("name")}) == {
        "name": "Ada",
        "literal": "name",
    }


def test_stop_stops_list_spec_iteration():
    assert glom([1, 2, 3, 4], [T]) == [1, 2, 3, 4]
    assert glom([1, 2, 3, 4], [(lambda item: item if item < 2 else STOP)]) == [1]


def test_coalesce_uses_first_available_path(nested_record):
    assert glom(nested_record, Coalesce("missing", "profile.contact.email")) == (
        "ada@example.test"
    )


def test_coalesce_supports_default_and_default_factory():
    assert glom({}, Coalesce("missing", default="fallback")) == "fallback"
    assert glom({}, Coalesce("missing", default_factory=lambda: ["created"])) == [
        "created"
    ]


def test_coalesce_can_skip_values():
    assert glom({"a": None, "b": 5}, Coalesce("a", "b", skip=None)) == 5


def test_coalesce_error_exposes_spec_skipped_values_and_path():
    with pytest.raises(CoalesceError) as exc_info:
        glom({}, Coalesce("a", "b"))
    error = exc_info.value
    assert isinstance(error, GlomError)
    assert error.coal_obj.subspecs == ("a", "b")
    assert len(error.skipped) == 2
    assert error.path == []


def test_s_binds_values_for_later_scope_access(nested_record):
    spec = (S(name=T["profile"]["name"]), {"copied": S.name})
    assert glom(nested_record, spec) == {"copied": "Ada"}


def test_invoke_combines_constants_and_specs():
    spec = Invoke(pow).specs("base").constants(exp=2)
    assert glom({"base": 6}, spec) == 36


def test_invoke_supports_starred_positional_specs():
    spec = Invoke(max).star(args="parts")
    assert glom({"parts": [2, 3, 5]}, spec) == 5


def test_spec_compiles_a_reusable_public_transformation():
    compiled = Spec({"name": "profile.name", "score": "profile.scores.1"})
    assert compiled.glom({"profile": {"name": "Ada", "scores": [4, 7]}}) == {
        "name": "Ada",
        "score": 7,
    }


def test_glommer_provides_an_isolated_public_runner():
    glommer = Glommer()
    assert glommer.glom({"value": 8}, "value") == 8


def test_inspect_echo_false_preserves_transformation_result(nested_record):
    assert glom(nested_record, Inspect("profile.name", echo=False)) == "Ada"


def test_assign_updates_nested_dict_and_list_in_place():
    target = {"profile": {"scores": [1, 2, 3]}}
    result = assign(target, "profile.scores.1", 20)
    assert result is target
    assert target["profile"]["scores"] == [1, 20, 3]


def test_assign_can_create_missing_nested_dicts():
    target = {}
    assign(target, "profile.contact.email", "ada@example.test", missing=dict)
    assert target == {"profile": {"contact": {"email": "ada@example.test"}}}


def test_assign_can_copy_a_value_with_spec():
    target = {"source": {"value": 11}}
    assert glom(target, Assign("copy", Spec("source.value")))["copy"] == 11


def test_assign_reports_semantic_path_assign_error():
    target = {"items": (1, 2)}
    with pytest.raises(GlomError) as exc_info:
        assign(target, "items.0", 9)
    assert exc_info.value.__class__.__name__ in {"PathAssignError", "UnregisteredTarget"}


def test_delete_removes_nested_dict_key_and_list_item():
    target = {"profile": {"name": "Ada", "scores": [4, 7, 9]}}
    result = delete(target, "profile.scores.1")
    assert result is target
    assert target == {"profile": {"name": "Ada", "scores": [4, 9]}}


def test_delete_can_ignore_missing_paths():
    target = {"present": True}
    assert delete(target, "missing.value", ignore_missing=True) is target
    assert target == {"present": True}


def test_delete_reports_path_delete_error_for_missing_list_item():
    with pytest.raises(PathDeleteError) as exc_info:
        delete([], T[0])
    assert isinstance(exc_info.value, GlomError)
    assert exc_info.value.dest_name == 0


def test_flatten_spec_and_function_flatten_one_level():
    target = [[1, 2], [3], [4, 5]]
    assert glom(target, Flatten()) == [1, 2, 3, 4, 5]
    assert flatten(target) == [1, 2, 3, 4, 5]


def test_flatten_supports_levels_and_custom_initializer():
    assert flatten([[1, 2], [3, 4]], init=int, levels=2) == 10
    assert flatten([(1,), (2,)], init=tuple) == (1, 2)


def test_flatten_lazy_mode_returns_an_iterator():
    result = flatten([[1], [2, 3]], init="lazy")
    assert iter(result) is result
    assert list(result) == [1, 2, 3]


def test_match_validates_nested_mapping_and_list_shapes():
    target = {"id": 7, "tags": ["one", "two"]}
    assert glom(target, Match({"id": int, "tags": [str]})) == target


def test_match_default_and_matches_methods():
    matcher = Match({"id": int}, default={"id": 0})
    assert matcher.verify({"id": "bad"}) == {"id": 0}
    assert matcher.matches({"id": 3}) is True
    assert Match({"id": int}).matches({"id": "bad"}) is False


def test_match_failure_exposes_public_error_types():
    with pytest.raises(TypeMatchError):
        glom({"id": "bad"}, Match({"id": int}))
    with pytest.raises(MatchError):
        glom({"id": 1}, Match({"other": int}))


def test_switch_routes_matching_cases_and_default():
    spec = Switch([("kind", Val("literal")), (T["value"], T["value"])], default="unknown")
    assert glom({"kind": "present"}, spec) == "literal"
    assert glom({"value": 9}, spec) == 9
    assert glom("other", Switch([("kind", Val("literal"))], default="unknown")) == "unknown"


def test_check_passes_through_valid_value_and_can_default():
    assert glom({"count": 4}, ("count", Check(type=int))) == 4
    assert glom({"count": "bad"}, ("count", Check(type=int, default=0))) == 0


def test_check_error_exposes_messages_check_object_and_path():
    with pytest.raises(CheckError) as exc_info:
        glom({"count": "bad"}, Check("count", type=int))
    error = exc_info.value
    assert isinstance(error.msgs, list)
    assert error.check_obj.spec == "count"
    assert error.path == []


def test_match_boolean_combinators_and_regex_are_composable():
    pattern = And(Match(int), M > 0)
    assert glom(4, pattern) == 4
    assert glom("Ada", Regex(r"[A-Z][a-z]+")) == "Ada"
    assert glom("guest", Not(Or("admin", "owner"))) == "guest"


def test_path_access_error_exposes_public_path_attributes():
    with pytest.raises(PathAccessError) as exc_info:
        glom({"profile": {}}, "profile.contact.email")
    error = exc_info.value
    assert isinstance(error, GlomError)
    assert error.path == Path("profile", "contact", "email")
    assert error.part_idx == 1
    assert isinstance(error.exc, KeyError)


def test_glom_default_handles_a_path_access_error():
    assert glom({}, "missing.value", default={"value": 0}) == {"value": 0}


def test_glom_wraps_non_glom_errors_as_glom_error():
    with pytest.raises(GlomError) as exc_info:
        glom({"value": "not-int"}, ("value", int))
    assert isinstance(exc_info.value, GlomError)
    assert exc_info.value.args
