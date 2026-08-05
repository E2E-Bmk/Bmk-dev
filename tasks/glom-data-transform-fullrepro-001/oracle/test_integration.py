from __future__ import annotations

import pytest

from glom import (
    A,
    And,
    Assign,
    Check,
    Coalesce,
    Delete,
    Flatten,
    GlomError,
    Glommer,
    Inspect,
    Invoke,
    CoalesceError,
    Match,
    Not,
    Or,
    Path,
    Regex,
    S,
    Spec,
    STOP,
    Switch,
    T,
    Val,
    assign,
    delete,
    flatten,
    glom,
)


@pytest.mark.depends_on("test_path_accesses_literal_keys_and_list_positions", "test_path_supports_length_values_items_and_slicing")
def test_nested_path_projection_combines_literal_key_and_list_access():
    target = {"rows": [{"key.with.dot": {"value": 3}}, {"key.with.dot": {"value": 8}}]}
    result = glom(target, {"first": Path("rows", 0, "key.with.dot", "value"), "last": Path("rows", 1, "key.with.dot", "value")})
    assert result == {"first": 3, "last": 8}


@pytest.mark.depends_on("test_t_and_s_project_target_and_scope_values", "test_val_preserves_literal_strings_in_constructed_output")
def test_scope_binding_and_literal_values_build_a_summary(nested_record):
    spec = (S(name=T["profile"]["name"], count=Invoke(len).specs(T["profile"]["scores"])), {"label": S.name, "count": S.count, "kind": Val("summary")})
    assert glom(nested_record, spec) == {"label": "Ada", "count": 3, "kind": "summary"}


@pytest.mark.depends_on("test_t_can_call_object_methods_and_slice_values", "test_invoke_combines_constants_and_specs")
def test_object_method_and_invoke_transform_one_record(object_record):
    spec = {"label": T.label(prefix="user:"), "total": Invoke(sum).specs("values")}
    assert glom(object_record, spec) == {"label": "user:Ada", "total": 15}


@pytest.mark.depends_on("test_stop_stops_list_spec_iteration", "test_flatten_spec_and_function_flatten_one_level")
def test_stop_and_flatten_process_nested_batches():
    batches = [[1, 2], [3], [4, 5]]
    assert glom(batches, Flatten()) == [1, 2, 3, 4, 5]
    assert glom([1, 2, 3], [(lambda item: item if item < 2 else STOP)]) == [1]


@pytest.mark.depends_on("test_coalesce_uses_first_available_path", "test_coalesce_supports_default_and_default_factory")
def test_coalesce_selects_a_contact_fallback_then_projects_it(nested_record):
    spec = {"email": Coalesce("profile.contact.missing", "profile.contact.email"), "name": "profile.name"}
    assert glom(nested_record, spec) == {"email": "ada@example.test", "name": "Ada"}


@pytest.mark.depends_on("test_coalesce_can_skip_values", "test_coalesce_error_exposes_spec_skipped_values_and_path")
def test_coalesce_skip_and_failure_modes_are_distinct():
    assert glom({"primary": None, "secondary": "ready"}, Coalesce("primary", "secondary", skip=None)) == "ready"
    with pytest.raises(CoalesceError) as exc_info:
        glom({}, Coalesce("primary", "secondary"))
    assert exc_info.value.coal_obj.subspecs == ("primary", "secondary")


@pytest.mark.depends_on("test_s_binds_values_for_later_scope_access", "test_spec_compiles_a_reusable_public_transformation")
def test_s_and_spec_reuse_transform_two_records():
    compiled = Spec((S(name=T["name"]), {"name": S.name, "score": "score"}))
    assert [compiled.glom(item) for item in ({"name": "Ada", "score": 7}, {"name": "Grace", "score": 9})] == [
        {"name": "Ada", "score": 7},
        {"name": "Grace", "score": 9},
    ]


@pytest.mark.depends_on("test_inspect_echo_false_preserves_transformation_result", "test_t_and_s_project_target_and_scope_values")
def test_inspect_can_wrap_a_scoped_projection_without_changing_result(nested_record):
    spec = (S(name=T["profile"]["name"]), {"name": Inspect(S.name, echo=False), "score": "profile.scores.0"})
    assert glom(nested_record, spec) == {"name": "Ada", "score": 4}


@pytest.mark.depends_on("test_assign_updates_nested_dict_and_list_in_place", "test_assign_can_create_missing_nested_dicts")
def test_assign_then_read_back_a_created_nested_record():
    target = {"items": [{"sku": "A"}], "summary": {}}
    assign(target, "items.0.price", 12, missing=dict)
    assign(target, "summary.second", "B", missing=dict)
    assert glom(target, {"first": "items.0.price", "second": "summary.second"}) == {"first": 12, "second": "B"}


@pytest.mark.depends_on("test_assign_can_copy_a_value_with_spec", "test_delete_removes_nested_dict_key_and_list_item")
def test_assign_copy_then_delete_restructures_a_mapping():
    target = {"source": {"value": 11}, "obsolete": True}
    glom(target, Assign("copied", Spec("source.value")))
    glom(target, Delete("obsolete"))
    assert target == {"source": {"value": 11}, "copied": 11}


@pytest.mark.depends_on("test_assign_reports_semantic_path_assign_error", "test_delete_reports_path_delete_error_for_missing_list_item")
def test_mutation_errors_leave_the_original_container_observable():
    target = {"items": (1, 2)}
    with pytest.raises(GlomError):
        assign(target, "items.0", 9)
    with pytest.raises(GlomError):
        delete([], T[0])
    assert target["items"] == (1, 2)


@pytest.mark.depends_on("test_delete_can_ignore_missing_paths", "test_delete_removes_nested_dict_key_and_list_item")
def test_delete_optional_cleanup_can_follow_a_present_cleanup():
    target = {"temp": {"marker": True}, "keep": 7}
    delete(target, "temp.marker")
    delete(target, "temp.missing", ignore_missing=True)
    assert target == {"temp": {}, "keep": 7}


@pytest.mark.depends_on("test_flatten_supports_levels_and_custom_initializer", "test_flatten_lazy_mode_returns_an_iterator")
def test_flatten_two_levels_then_lazily_flatten_followup_batches():
    nested = [[[1], [2]], [[3], [4]]]
    assert flatten(nested, levels=2) == [1, 2, 3, 4]
    assert list(flatten([[5], [6]], init="lazy")) == [5, 6]


@pytest.mark.depends_on("test_match_validates_nested_mapping_and_list_shapes", "test_match_default_and_matches_methods")
def test_match_then_project_only_verified_fields():
    target = {"id": 7, "tags": ["one", "two"]}
    verified = glom(target, Match({"id": int, "tags": [str]}))
    assert glom(verified, {"id": "id", "tag_count": ("tags", len)}) == {"id": 7, "tag_count": 2}


@pytest.mark.depends_on("test_match_failure_exposes_public_error_types", "test_match_boolean_combinators_and_regex_are_composable")
def test_match_combinators_validate_an_event_record():
    event = {"kind": "login", "user": "Ada"}
    spec = Match({"kind": Or("login", "export"), "user": Regex(r"[A-Z][a-z]+")})
    assert glom(event, spec) == event
    assert glom(event["user"], And(str, MISSING_USER_PATTERN)) == "Ada"


MISSING_USER_PATTERN = Regex(r"[A-Z][a-z]+")


@pytest.mark.depends_on("test_switch_routes_matching_cases_and_default", "test_match_validates_nested_mapping_and_list_shapes")
def test_switch_routes_event_kinds_into_normalized_records():
    spec = Switch([
        (Match({"kind": "login", "ok": bool}), Val({"category": "access"})),
        (Match({"kind": "export", "ok": bool}), Val({"category": "transfer"})),
    ], default={"category": "other"})
    assert glom({"kind": "login", "ok": True}, spec) == {"category": "access"}
    assert glom({"kind": "other"}, spec) == {"category": "other"}


@pytest.mark.depends_on("test_check_passes_through_valid_value_and_can_default", "test_check_error_exposes_messages_check_object_and_path")
def test_check_validates_a_projected_score_and_supplies_fallback():
    target = {"profile": {"scores": [4, 7, 9]}}
    spec = {"score": ("profile.scores.1", Check(type=int, validate=lambda value: value > 5))}
    assert glom(target, spec) == {"score": 7}
    assert glom({"profile": {"scores": ["bad"]}}, ("profile.scores.0", Check(type=int, default=-1))) == -1


@pytest.mark.depends_on("test_path_access_error_exposes_public_path_attributes", "test_glom_default_handles_a_path_access_error")
def test_path_error_can_be_recovered_inside_a_composed_projection():
    target = {"profile": {"name": "Ada"}}
    result = glom(target, {"name": "profile.name", "email": Coalesce("profile.email", default="unknown")})
    assert result == {"name": "Ada", "email": "unknown"}


@pytest.mark.depends_on("test_glom_wraps_non_glom_errors_as_glom_error", "test_glom_default_handles_a_path_access_error")
def test_default_recovery_handles_both_path_and_callable_failures():
    assert glom({}, "missing", default=0) == 0
    with pytest.raises(GlomError):
        glom({"value": "bad"}, ("value", int))


@pytest.mark.depends_on("test_path_accesses_literal_keys_and_list_positions", "test_t_and_s_project_target_and_scope_values")
def test_mixed_path_and_t_projection_restructures_nested_data(nested_record):
    spec = {"identity": Path("profile", "name"), "scores": T["profile"]["scores"], "first_event": T["events"][0]["kind"]}
    assert glom(nested_record, spec) == {"identity": "Ada", "scores": [4, 7, 9], "first_event": "login"}


@pytest.mark.depends_on("test_invoke_supports_starred_positional_specs", "test_flatten_spec_and_function_flatten_one_level")
def test_invoke_and_flatten_normalize_matrix_rows():
    target = {"rows": [[1, 2], [3, 4]]}
    row_totals = glom(target, ("rows", [Invoke(sum).specs(T)]))
    assert row_totals == [3, 7]
    assert flatten([row_totals, [8]]) == [3, 7, 8]


@pytest.mark.depends_on("test_spec_compiles_a_reusable_public_transformation", "test_glommer_provides_an_isolated_public_runner")
def test_compiled_spec_and_glommer_agree_on_nested_output():
    target = {"user": {"name": "Ada", "roles": ["admin", "writer"]}}
    spec = {"name": "user.name", "role_count": ("user.roles", len)}
    assert Spec(spec).glom(target) == Glommer().glom(target, spec)


@pytest.mark.depends_on("test_t_can_call_object_methods_and_slice_values", "test_delete_removes_nested_dict_key_and_list_item")
def test_object_attribute_workflow_reads_then_removes_a_field(object_record):
    before = glom(object_record, {"name": T.name, "tail": T.values[1:]})
    delete(object_record, "meta")
    assert before == {"name": "Ada", "tail": [5, 8]}
    assert not hasattr(object_record, "meta")


@pytest.mark.depends_on("test_stop_stops_list_spec_iteration", "test_val_preserves_literal_strings_in_constructed_output")
def test_stop_and_val_filter_a_list_into_literal_labeled_rows():
    target = [{"value": 1}, {"value": 2}, {"value": 3}]
    filtered = glom(target, [(lambda item: item if item["value"] < 2 else STOP)])
    assert glom(filtered, [{"value": "value", "kind": Val("row")}]) == [{"value": 1, "kind": "row"}]


@pytest.mark.depends_on("test_coalesce_can_skip_values", "test_check_passes_through_valid_value_and_can_default")
def test_coalesce_and_check_form_a_tolerant_score_pipeline():
    target = {"primary": None, "backup": 8}
    score = glom(target, Coalesce("primary", "backup", skip=None))
    assert glom(score, Check(type=int, validate=lambda value: value > 0)) == 8


@pytest.mark.depends_on("test_switch_routes_matching_cases_and_default", "test_invoke_combines_constants_and_specs")
def test_switch_then_invoke_formats_a_status_label():
    route = Switch([("kind", Val("login")), ("other", Val("other"))])
    category = glom({"kind": "present"}, route)
    label = glom({"category": category}, Invoke(lambda value, suffix: value + suffix).specs("category").constants(suffix="-event"))
    assert label == "login-event"


@pytest.mark.depends_on("test_assign_can_create_missing_nested_dicts", "test_match_validates_nested_mapping_and_list_shapes")
def test_assign_builds_then_match_verifies_a_local_payload():
    payload = {}
    assign(payload, "user.name", "Ada", missing=dict)
    assign(payload, "user.roles", ["admin"], missing=dict)
    assert glom(payload, Match({"user": {"name": str, "roles": [str]}})) == payload


@pytest.mark.depends_on("test_delete_can_ignore_missing_paths", "test_glom_default_handles_a_path_access_error")
def test_cleanup_and_default_access_leave_a_stable_summary():
    payload = {"data": {"value": 4}, "temporary": True}
    delete(payload, "temporary")
    summary = glom(payload, {"value": "data.value", "missing": Coalesce("data.other", default=0)})
    assert summary == {"value": 4, "missing": 0}


@pytest.mark.depends_on("test_flatten_supports_levels_and_custom_initializer", "test_switch_routes_matching_cases_and_default")
def test_flattened_events_are_routed_into_categories():
    events = [[{"kind": "login"}], [{"kind": "export"}]]
    flat = flatten(events)
    spec = [Switch([("kind", T["kind"])], default="other")]
    assert glom(flat, spec) == ["login", "export"]


@pytest.mark.depends_on("test_match_boolean_combinators_and_regex_are_composable", "test_check_passes_through_valid_value_and_can_default")
def test_regex_match_and_check_validate_a_user_projection():
    target = {"name": "Ada", "age": 36}
    assert glom(target, {"name": ("name", Regex(r"[A-Z][a-z]+")), "age": ("age", Check(type=int, validate=lambda value: value >= 18))}) == target


@pytest.mark.depends_on("test_path_supports_length_values_items_and_slicing", "test_assign_can_copy_a_value_with_spec")
def test_path_metadata_and_assignment_copy_keep_source_data_intact():
    target = {"source": {"nested": {"value": 5}}}
    path = Path("source", "nested", "value")
    glom(target, Assign("result", path))
    assert path.values() == ("source", "nested", "value")
    assert target == {"source": {"nested": {"value": 5}}, "result": 5}
