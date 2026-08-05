from __future__ import annotations

import json

import pytest

from deepdiff import DeepDiff, DeepHash, DeepSearch, Delta, extract, grep
from deepdiff.operator import BaseOperator, PrefixOrSuffixOperator

from conftest import Box, apply_delta


@pytest.mark.depends_on("test_nested_dictionary_value_change_reports_old_new_values_and_path")
@pytest.mark.depends_on("test_parse_path_and_extract_round_trip_nested_value")
def test_diff_then_extract_changed_nested_value():
    left = {"payload": {"items": [{"status": "new"}]}}
    right = {"payload": {"items": [{"status": "ready"}]}}
    diff = DeepDiff(left, right)

    path = next(iter(diff["values_changed"]))
    assert path == "root['payload']['items'][0]['status']"
    assert extract(right, path) == diff["values_changed"][path]["new_value"]


@pytest.mark.depends_on("test_delta_applies_value_addition_and_set_changes")
@pytest.mark.depends_on("test_delta_mutate_false_preserves_input_identity")
def test_diff_delta_pipeline_reconstructs_nested_mapping():
    left = {"profile": {"name": "Ada"}, "events": [1, 2]}
    right = {"profile": {"name": "Grace"}, "events": [1, 2, 3]}
    delta = Delta(DeepDiff(left, right))

    rebuilt = delta + left
    assert rebuilt == right
    assert left != rebuilt


@pytest.mark.depends_on("test_deepdiff_json_is_parseable_and_contains_semantic_change_fields")
@pytest.mark.depends_on("test_nested_dictionary_value_change_reports_old_new_values_and_path")
def test_json_projection_round_trips_diff_categories():
    diff = DeepDiff({"a": 1, "b": 2}, {"a": 3, "b": 2, "c": 4})
    payload = json.loads(diff.to_json(force_use_builtin_json=True))

    assert set(payload) == {"values_changed", "dictionary_item_added"}
    assert payload["values_changed"]["root['a']"]["new_value"] == 3
    assert payload["dictionary_item_added"] == ["root['c']"]


@pytest.mark.depends_on("test_tree_view_exposes_path_objects_and_text_view_has_same_path")
@pytest.mark.depends_on("test_affected_paths_projects_changed_paths")
def test_tree_and_text_views_preserve_affected_path_projection():
    tree = DeepDiff({"a": [1, 2], "b": 3}, {"a": [1, 4], "b": 5}, view="tree")
    text = tree.to_dict()

    assert {node.path() for node in tree["values_changed"]} == set(text["values_changed"])
    assert {node.path() for node in tree["values_changed"]} == {node.path() for node in tree.affected_paths}


@pytest.mark.depends_on("test_include_paths_limits_comparison_to_selected_branch")
@pytest.mark.depends_on("test_exclude_paths_removes_selected_branch_from_comparison")
def test_include_then_exclude_workflow_selects_only_allowed_branch():
    left = {"keep": {"x": 1}, "skip": {"x": 1}}
    right = {"keep": {"x": 2}, "skip": {"x": 2}}
    included = DeepDiff(left, right, include_paths="root['keep']")
    excluded = DeepDiff(left, right, exclude_paths="root['skip']")

    assert set(included["values_changed"]) == {"root['keep']['x']"}
    assert set(excluded["values_changed"]) == {"root['keep']['x']"}


@pytest.mark.depends_on("test_ignore_order_matches_nested_dictionaries_by_content")
@pytest.mark.depends_on("test_ignore_order_can_report_repetition_changes")
def test_ignore_order_workflow_distinguishes_reordering_from_repetition():
    same = DeepDiff([{"id": 1}, {"id": 2}], [{"id": 2}, {"id": 1}], ignore_order=True)
    repeated = DeepDiff([1, 1, 2], [1, 2, 2], ignore_order=True, report_repetition=True)

    assert same.to_dict() == {}
    assert set(repeated["repetition_change"]) == {"root[0]", "root[2]"}


@pytest.mark.depends_on("test_custom_object_attributes_are_compared")
@pytest.mark.depends_on("test_delta_bytes_restore_and_apply_to_original")
def test_custom_object_diff_and_delta_preserve_object_type():
    left = Box("record", 1)
    right = Box("record", 5)

    rebuilt = Delta(DeepDiff(left, right)) + left
    assert isinstance(rebuilt, Box)
    assert rebuilt.name == "record"
    assert rebuilt.value == 5


@pytest.mark.depends_on("test_custom_base_operator_can_accept_small_numeric_variation")
@pytest.mark.depends_on("test_prefix_or_suffix_operator_accepts_prefix_relationship")
def test_custom_operator_workflow_combines_numeric_and_string_rules():
    class ApproximateOperator(BaseOperator):
        def match(self, level):
            return level.path() == "root['score']"

        def give_up_diffing(self, level, diff_instance):
            return abs(level.t1 - level.t2) <= 2

    diff = DeepDiff(
        {"score": 10, "message": "hello"},
        {"score": 12, "message": "hello world"},
        custom_operators=[ApproximateOperator(), PrefixOrSuffixOperator()],
    )

    assert diff.to_dict() == {}


@pytest.mark.depends_on("test_deepsearch_finds_case_insensitive_string_paths")
@pytest.mark.depends_on("test_deepsearch_regexp_mode_matches_selected_strings")
def test_search_workflow_finds_literal_then_regexp_matches():
    value = {"users": [{"name": "Alice"}, {"name": "Bob"}], "alias": "Alina"}
    literal = DeepSearch(value, "alice")
    regexp = DeepSearch(value, r"^Ali", use_regexp=True)

    assert set(literal["matched_values"]) == {"root['users'][0]['name']"}
    assert set(regexp["matched_values"]) == {"root['users'][0]['name']", "root['alias']"}


@pytest.mark.depends_on("test_grep_operator_searches_an_object_with_pipe_syntax")
@pytest.mark.depends_on("test_parse_path_and_extract_round_trip_nested_value")
def test_grep_search_paths_can_be_extracted_from_source_object():
    value = {"records": [{"role": "admin"}, {"role": "user"}]}
    matches = value | grep("admin")
    path = next(iter(matches["matched_values"]))

    assert path == "root['records'][0]['role']"
    assert extract(value, path) == "admin"


@pytest.mark.depends_on("test_tuple_value_change_and_append_are_structural")
@pytest.mark.depends_on("test_set_membership_changes_are_reported_at_the_set_path")
def test_tuple_list_set_workflow_reports_and_applies_container_changes():
    left = {"tuple": (1, 2), "set": {1, 2}, "list": [1, 2]}
    right = {"tuple": (1, 3, 4), "set": {2, 3}, "list": [1, 4]}

    diff = DeepDiff(left, right)
    rebuilt = Delta(diff) + left
    assert rebuilt == right
    assert "root['tuple'][1]" in diff["values_changed"]
    assert set(diff["set_item_added"]) == {"root['set'][3]"}


@pytest.mark.depends_on("test_type_changes_include_type_objects_and_values")
@pytest.mark.depends_on("test_ignore_numeric_type_changes_suppresses_int_float_only_change")
def test_type_policy_workflow_can_strictly_report_or_ignore_numeric_types():
    strict = DeepDiff({"value": 1}, {"value": 1.0})
    relaxed = DeepDiff({"value": 1}, {"value": 1.0}, ignore_numeric_type_changes=True)

    assert "root['value']" in strict["type_changes"]
    assert relaxed.to_dict() == {}


@pytest.mark.depends_on("test_significant_digits_suppresses_small_decimal_difference")
@pytest.mark.depends_on("test_significant_digits_reports_difference_beyond_precision")
def test_precision_workflow_changes_diff_visibility_and_json_projection():
    close = DeepDiff({"x": 1.23456}, {"x": 1.23451}, significant_digits=3)
    far = DeepDiff({"x": 1.23456}, {"x": 1.23999}, significant_digits=3)

    assert close.to_dict() == {}
    assert json.loads(far.to_json(force_use_builtin_json=True))["values_changed"]


@pytest.mark.depends_on("test_ignore_string_case_suppresses_case_only_change")
@pytest.mark.depends_on("test_ignore_order_suppresses_reordering_of_scalar_list")
def test_case_and_order_policies_apply_together_to_nested_lists():
    left = [{"name": "Alpha"}, {"name": "Beta"}]
    right = [{"name": "beta"}, {"name": "alpha"}]

    assert DeepDiff(left, right, ignore_order=True, ignore_string_case=True).to_dict() == {}


@pytest.mark.depends_on("test_delta_dumps_are_deterministic_for_same_diff")
@pytest.mark.depends_on("test_delta_bytes_restore_and_apply_to_original")
def test_delta_serialization_workflow_is_repeatable_and_reversible():
    left = {"a": 1, "items": [1, 2]}
    right = {"a": 2, "items": [1, 3, 4]}
    forward = Delta(DeepDiff(left, right))
    reverse = right - Delta(DeepDiff(left, right), bidirectional=True)
    encoded = forward.dumps()

    assert encoded == Delta(DeepDiff(left, right)).dumps()
    assert Delta(encoded) + left == right
    assert reverse == left


@pytest.mark.depends_on("test_deephash_is_stable_for_equal_nested_values")
@pytest.mark.depends_on("test_equal_nested_objects_have_empty_diff")
def test_hash_and_diff_workflow_agree_on_equal_nested_content():
    left = {"a": [1, 2], "b": {"x", "y"}}
    right = {"b": {"y", "x"}, "a": [1, 2]}

    assert DeepHash(left)[left] == DeepHash(right)[right]
    assert DeepDiff(left, right).to_dict() == {}


@pytest.mark.depends_on("test_affected_root_keys_projects_top_level_keys")
@pytest.mark.depends_on("test_affected_paths_projects_changed_paths")
def test_affected_path_workflow_groups_changes_by_top_level_key():
    diff = DeepDiff({"a": {"x": 1}, "b": [1]}, {"a": {"x": 2}, "b": [2]})
    paths = set(diff.affected_paths)

    assert paths == {"root['a']['x']", "root['b'][0]"}
    assert diff.affected_root_keys == {"a", "b"}


@pytest.mark.depends_on("test_exclude_regex_paths_removes_matching_nested_path")
@pytest.mark.depends_on("test_deepdiff_json_is_parseable_and_contains_semantic_change_fields")
def test_regex_exclusion_workflow_leaves_json_public_branch_only():
    diff = DeepDiff(
        {"public": {"x": 1}, "secret": {"x": 1}},
        {"public": {"x": 2}, "secret": {"x": 2}},
        exclude_regex_paths=r"root\['secret'\]",
    )
    payload = json.loads(diff.to_json(force_use_builtin_json=True))

    assert set(payload["values_changed"]) == {"root['public']['x']"}


@pytest.mark.depends_on("test_custom_object_attributes_are_compared")
@pytest.mark.depends_on("test_deepdiff_json_is_parseable_and_contains_semantic_change_fields")
def test_custom_object_workflow_uses_mapping_for_json_serialization():
    left = Box("a", 1)
    right = Box("a", 2)
    diff = DeepDiff(left, right)

    payload = json.loads(diff.to_json(default_mapping={Box: lambda item: {"name": item.name, "value": item.value}}))
    assert payload["values_changed"]["root.value"]["new_value"] == 2


@pytest.mark.depends_on("test_exclude_paths_removes_selected_branch_from_comparison")
@pytest.mark.depends_on("test_include_paths_limits_comparison_to_selected_branch")
def test_branch_selection_workflow_is_consistent_for_nested_changes():
    left = {"a": {"x": 1, "y": 1}, "b": {"x": 1}}
    right = {"a": {"x": 2, "y": 2}, "b": {"x": 2}}
    included = DeepDiff(left, right, include_paths=["root['a']['x']"])
    excluded = DeepDiff(left, right, exclude_paths=["root['a']['y']", "root['b']"])

    assert set(included["values_changed"]) == {"root['a']['x']"}
    assert set(excluded["values_changed"]) == {"root['a']['x']"}


@pytest.mark.depends_on("test_math_epsilon_suppresses_flat_numeric_difference")
@pytest.mark.depends_on("test_significant_digits_reports_difference_beyond_precision")
def test_numeric_policy_workflow_combines_epsilon_and_precision():
    close = DeepDiff({"x": 10.0}, {"x": 10.001}, math_epsilon=0.01, significant_digits=2)
    far = DeepDiff({"x": 10.0}, {"x": 10.9}, math_epsilon=0.01, significant_digits=2)

    assert close.to_dict() == {}
    assert "root['x']" in far["values_changed"]


@pytest.mark.depends_on("test_delta_applies_value_addition_and_set_changes")
@pytest.mark.depends_on("test_delta_dumps_are_deterministic_for_same_diff")
def test_delta_workflow_replays_same_serialized_patch_twice():
    left = {"status": "new", "values": [1, 2]}
    right = {"status": "done", "values": [1, 2, 3]}
    payload = Delta(DeepDiff(left, right)).dumps()

    assert Delta(payload) + left == right
    assert Delta(payload) + {"status": "new", "values": [1, 2]} == right


@pytest.mark.depends_on("test_ignore_order_can_report_repetition_changes")
@pytest.mark.depends_on("test_delta_bytes_restore_and_apply_to_original")
def test_repetition_report_can_be_serialized_as_a_semantic_delta():
    left = {"values": [1, 1, 2]}
    right = {"values": [1, 2, 2]}
    diff = DeepDiff(left, right, ignore_order=True, report_repetition=True)

    assert set(diff["repetition_change"]) == {"root['values'][0]", "root['values'][2]"}
    assert diff.to_dict()["repetition_change"]["root['values'][0]"]["new_repeat"] == 1


@pytest.mark.depends_on("test_deepsearch_can_match_values_and_dictionary_keys")
@pytest.mark.depends_on("test_grep_operator_searches_an_object_with_pipe_syntax")
def test_search_workflow_cross_checks_literal_and_key_matches():
    value = {"needle": "top", "nested": {"needle": "deep"}}
    search = DeepSearch(value, "needle")
    grep_search = value | grep("top")

    assert "root['nested']['needle']" in set(search["matched_paths"])
    assert "root['needle']" in set(search["matched_paths"])
    assert set(grep_search["matched_values"]) == {"root['needle']"}


@pytest.mark.depends_on("test_parse_path_and_extract_round_trip_nested_value")
@pytest.mark.depends_on("test_delta_applies_value_addition_and_set_changes")
def test_path_extract_and_delta_workflow_targets_same_nested_location():
    left = {"records": [{"score": 4}]}
    right = {"records": [{"score": 9}]}
    diff = DeepDiff(left, right)
    path = next(iter(diff["values_changed"]))
    rebuilt = Delta(diff) + left

    assert extract(rebuilt, path) == 9
    assert extract(left, path) == 4


@pytest.mark.depends_on("test_equal_nested_objects_have_empty_diff")
@pytest.mark.depends_on("test_deephash_is_stable_for_equal_nested_values")
def test_ordered_tuple_and_unordered_set_hash_diff_workflow():
    left = {"tuple": (1, 2), "set": {"a", "b"}}
    same = {"tuple": (1, 2), "set": {"b", "a"}}
    altered = {"tuple": (2, 1), "set": {"a", "c"}}

    assert DeepDiff(left, same).to_dict() == {}
    assert DeepHash(left)[left] == DeepHash(same)[same]
    assert DeepDiff(left, altered).to_dict()


@pytest.mark.depends_on("test_verbose_level_zero_keeps_change_paths_without_values")
@pytest.mark.depends_on("test_deepdiff_json_is_parseable_and_contains_semantic_change_fields")
def test_verbose_projection_workflow_preserves_paths_at_two_detail_levels():
    full = DeepDiff({"x": 1}, {"x": 2}, verbose_level=1)
    paths_only = DeepDiff({"x": 1}, {"x": 2}, verbose_level=0)

    assert full.to_dict()["values_changed"]["root['x']"]["old_value"] == 1
    assert paths_only.to_dict() == {}


@pytest.mark.depends_on("test_custom_base_operator_reports_large_numeric_variation")
@pytest.mark.depends_on("test_delta_applies_value_addition_and_set_changes")
def test_custom_operator_then_delta_workflow_changes_only_unaccepted_value():
    class ApproximateOperator(BaseOperator):
        def match(self, level):
            return level.path() == "root['score']"

        def give_up_diffing(self, level, diff_instance):
            return abs(level.t1 - level.t2) <= 1

    left = {"score": 10, "count": 1}
    right = {"score": 12, "count": 2}
    diff = DeepDiff(left, right, custom_operators=[ApproximateOperator()])
    rebuilt = Delta(diff) + left

    assert diff.to_dict() == {
        "values_changed": {
            "root['score']": {"new_value": 12, "old_value": 10},
            "root['count']": {"new_value": 2, "old_value": 1},
        }
    }
    assert rebuilt == {"score": 12, "count": 2}


@pytest.mark.depends_on("test_prefix_or_suffix_operator_accepts_prefix_relationship")
@pytest.mark.depends_on("test_delta_bytes_restore_and_apply_to_original")
def test_prefix_operator_then_delta_workflow_preserves_accepted_text():
    left = {"message": "hello", "code": "A"}
    right = {"message": "hello world", "code": "B"}
    diff = DeepDiff(left, right, custom_operators=[PrefixOrSuffixOperator()])

    assert diff.to_dict() == {"values_changed": {"root['code']": {"new_value": "B", "old_value": "A"}}}
    assert Delta(diff) + left == {"message": "hello", "code": "B"}


@pytest.mark.depends_on("test_deepdiff_json_is_parseable_and_contains_semantic_change_fields")
@pytest.mark.depends_on("test_delta_bytes_restore_and_apply_to_original")
def test_json_diff_and_binary_delta_serve_distinct_restore_projections():
    left = {"value": 1}
    right = {"value": 2}
    diff = DeepDiff(left, right)
    json_payload = json.loads(diff.to_json(force_use_builtin_json=True))
    delta_payload = Delta(diff).dumps()

    assert json_payload["values_changed"]["root['value']"]["new_value"] == 2
    assert Delta(delta_payload) + left == right
