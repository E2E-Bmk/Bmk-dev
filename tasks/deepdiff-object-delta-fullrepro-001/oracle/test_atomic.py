from __future__ import annotations

import json
import re

from deepdiff import DeepDiff, DeepHash, DeepSearch, Delta, extract, grep, parse_path
from deepdiff.operator import BaseOperator, PrefixOrSuffixOperator

from conftest import Box, apply_delta, changed_paths, diff_dict


def test_public_import_surface_exposes_diff_search_hash_delta_and_paths():
    assert DeepDiff is not None
    assert DeepSearch is not None
    assert DeepHash is not None
    assert Delta is not None
    assert extract is not None
    assert parse_path is not None
    assert grep is not None


def test_equal_nested_objects_have_empty_diff():
    value = {"a": [1, {"b": (2, 3)}], "s": {"x", "y"}}

    assert DeepDiff(value, {"a": [1, {"b": (2, 3)}], "s": {"y", "x"}}).to_dict() == {}


def test_nested_dictionary_value_change_reports_old_new_values_and_path():
    result = diff_dict({"profile": {"age": 30}}, {"profile": {"age": 31}})

    assert result["values_changed"]["root['profile']['age']"] == {"old_value": 30, "new_value": 31}


def test_dictionary_addition_and_removal_use_distinct_categories():
    result = diff_dict({"keep": 1, "removed": 2}, {"keep": 1, "added": 3})

    assert set(result["dictionary_item_added"]) == {"root['added']"}
    assert set(result["dictionary_item_removed"]) == {"root['removed']"}


def test_list_addition_and_removal_report_index_paths():
    result = diff_dict([10, 20], [10, 30, 40])

    assert result["values_changed"]["root[1]"]["new_value"] == 30
    assert result["iterable_item_added"]["root[2]"] == 40


def test_tuple_value_change_and_append_are_structural():
    changed = diff_dict((1, 2), (1, 3))
    extended = diff_dict((1, 2), (1, 2, 3))

    assert changed["values_changed"]["root[1]"]["old_value"] == 2
    assert changed["values_changed"]["root[1]"]["new_value"] == 3
    assert extended["iterable_item_added"]["root[2]"] == 3


def test_set_membership_changes_are_reported_at_the_set_path():
    result = diff_dict({"red", "blue"}, {"red", "green"})

    assert set(result["set_item_removed"]) == {"root['blue']"}
    assert set(result["set_item_added"]) == {"root['green']"}


def test_custom_object_attributes_are_compared():
    result = diff_dict(Box("item", 1), Box("item", 2))

    assert result["values_changed"]["root.value"] == {"old_value": 1, "new_value": 2}


def test_type_changes_include_type_objects_and_values():
    result = diff_dict({"count": 1}, {"count": 1.0})

    change = result["type_changes"]["root['count']"]
    assert change["old_type"] is int
    assert change["new_type"] is float
    assert change["old_value"] == 1
    assert change["new_value"] == 1.0


def test_ignore_numeric_type_changes_suppresses_int_float_only_change():
    assert diff_dict({"count": 1}, {"count": 1.0}, ignore_numeric_type_changes=True) == {}


def test_ignore_string_case_suppresses_case_only_change():
    assert diff_dict({"name": "Alpha"}, {"name": "alpha"}, ignore_string_case=True) == {}


def test_significant_digits_suppresses_small_decimal_difference():
    assert diff_dict({"price": 1.23456}, {"price": 1.23451}, significant_digits=3) == {}


def test_significant_digits_reports_difference_beyond_precision():
    result = diff_dict({"price": 1.23456}, {"price": 1.23999}, significant_digits=3)

    assert "root['price']" in result["values_changed"]


def test_math_epsilon_suppresses_flat_numeric_difference():
    assert diff_dict({"value": 1.000}, {"value": 1.001}, math_epsilon=0.01) == {}


def test_include_paths_limits_comparison_to_selected_branch():
    result = diff_dict(
        {"left": {"value": 1}, "right": {"value": 1}},
        {"left": {"value": 2}, "right": {"value": 2}},
        include_paths="root['left']",
    )

    assert changed_paths(result, "values_changed") == {"root['left']['value']"}


def test_exclude_paths_removes_selected_branch_from_comparison():
    result = diff_dict(
        {"left": {"value": 1}, "right": {"value": 1}},
        {"left": {"value": 2}, "right": {"value": 2}},
        exclude_paths="root['left']",
    )

    assert changed_paths(result, "values_changed") == {"root['right']['value']"}


def test_exclude_regex_paths_removes_matching_nested_path():
    result = diff_dict(
        {"public": 1, "secret": 1},
        {"public": 2, "secret": 2},
        exclude_regex_paths=re.compile(r"root\['secret'\]"),
    )

    assert changed_paths(result, "values_changed") == {"root['public']"}


def test_ignore_order_suppresses_reordering_of_scalar_list():
    assert diff_dict([1, 2, 3], [3, 1, 2], ignore_order=True) == {}


def test_ignore_order_matches_nested_dictionaries_by_content():
    left = [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}]
    right = [{"id": 2, "tags": ["c"]}, {"id": 1, "tags": ["a", "b"]}]

    assert diff_dict(left, right, ignore_order=True) == {}


def test_ignore_order_can_report_repetition_changes():
    result = diff_dict([1, 1, 2], [1, 2, 2], ignore_order=True, report_repetition=True)

    assert result["repetition_change"]["root[0]"]["old_repeat"] == 2
    assert result["repetition_change"]["root[2]"]["new_repeat"] == 2


def test_ignore_order_without_repetition_reporting_ignores_duplicate_positions():
    assert diff_dict([1, 1, 2], [1, 2, 1], ignore_order=True) == {}


def test_tree_view_exposes_path_objects_and_text_view_has_same_path():
    tree = DeepDiff({"items": [1, 2]}, {"items": [1, 3]}, view="tree")
    text = tree.to_dict()

    node = next(iter(tree["values_changed"]))
    assert node.path() == "root['items'][1]"
    assert set(text["values_changed"]) == {"root['items'][1]"}


def test_affected_paths_projects_changed_paths():
    diff = DeepDiff({"a": 1, "b": [2]}, {"a": 2, "b": [3]})

    assert set(diff.affected_paths) == {"root['a']", "root['b'][0]"}


def test_affected_root_keys_projects_top_level_keys():
    diff = DeepDiff({"a": 1, "b": 2}, {"a": 3, "b": 4})

    assert diff.affected_root_keys == {"a", "b"}


def test_verbose_level_zero_keeps_change_paths_without_values():
    result = DeepDiff({"x": 1}, {"x": 2}, verbose_level=0).to_dict()

    assert result == {}


def test_custom_base_operator_can_accept_small_numeric_variation():
    class ApproximateOperator(BaseOperator):
        def match(self, level):
            return level.path() == "root['score']"

        def give_up_diffing(self, level, diff_instance):
            return abs(level.t1 - level.t2) <= 2

    assert diff_dict({"score": 10}, {"score": 12}, custom_operators=[ApproximateOperator()]) == {}


def test_custom_base_operator_reports_large_numeric_variation():
    class ApproximateOperator(BaseOperator):
        def match(self, level):
            return level.path() == "root['score']"

        def give_up_diffing(self, level, diff_instance):
            return abs(level.t1 - level.t2) <= 2

    result = diff_dict({"score": 10}, {"score": 15}, custom_operators=[ApproximateOperator()])

    assert result["values_changed"]["root['score']"]["new_value"] == 15


def test_prefix_or_suffix_operator_accepts_prefix_relationship():
    result = diff_dict(
        {"message": "hello"},
        {"message": "hello world"},
        custom_operators=[PrefixOrSuffixOperator()],
    )

    assert result == {}


def test_deepsearch_finds_case_insensitive_string_paths():
    result = DeepSearch({"users": [{"name": "Alice"}, {"name": "Bob"}]}, "alice")

    assert set(result["matched_values"]) == {"root['users'][0]['name']"}


def test_deepsearch_can_match_values_and_dictionary_keys():
    result = DeepSearch({"target": {"needle": "value"}, "needle": "other"}, "needle")

    assert "root['target']['needle']" in set(result["matched_paths"])
    assert "root['needle']" in set(result["matched_paths"])


def test_deepsearch_regexp_mode_matches_selected_strings():
    result = DeepSearch({"a": "alpha", "b": "beta"}, r"^al", use_regexp=True)

    assert set(result["matched_values"]) == {"root['a']"}


def test_grep_operator_searches_an_object_with_pipe_syntax():
    result = {"records": [{"role": "admin"}, {"role": "user"}]} | grep("admin")

    assert set(result["matched_values"]) == {"root['records'][0]['role']"}


def test_parse_path_and_extract_round_trip_nested_value():
    value = {"a": [{"b": 7}]}
    path = "root['a'][0]['b']"

    assert parse_path(path) == ["a", 0, "b"]
    assert extract(value, path) == 7


def test_deephash_is_stable_for_equal_nested_values():
    left = {"a": [1, 2], "b": {"x", "y"}}

    assert DeepHash(left)[left] == DeepHash({"b": {"y", "x"}, "a": [1, 2]})[{"b": {"x", "y"}, "a": [1, 2]}]


def test_delta_applies_value_addition_and_set_changes():
    left = {"count": 1, "items": [1, 2], "flags": {"a", "b"}}
    right = {"count": 2, "items": [1, 3, 4], "flags": {"b", "c"}}

    result = Delta(DeepDiff(left, right)) + left

    assert result == right
    assert left == {"count": 1, "items": [1, 2], "flags": {"a", "b"}}


def test_delta_mutate_false_preserves_input_identity():
    left = {"value": 1}
    result = Delta(DeepDiff(left, {"value": 2})) + left

    assert result == {"value": 2}
    assert left == {"value": 1}


def test_delta_dumps_are_deterministic_for_same_diff():
    left = {"value": 1, "items": [1, 2]}
    diff = DeepDiff(left, {"value": 2, "items": [1, 3, 4]})

    first = Delta(diff).dumps()
    second = Delta(diff).dumps()

    assert isinstance(first, bytes)
    assert first == second


def test_delta_bytes_restore_and_apply_to_original():
    left = {"value": 1, "items": [1, 2]}
    delta_bytes = Delta(DeepDiff(left, {"value": 2, "items": [1, 3, 4]})).dumps()

    assert Delta(delta_bytes) + left == {"value": 2, "items": [1, 3, 4]}


def test_deepdiff_json_is_parseable_and_contains_semantic_change_fields():
    encoded = DeepDiff({"value": 1}, {"value": 2}).to_json(force_use_builtin_json=True)
    decoded = json.loads(encoded)

    assert decoded["values_changed"]["root['value']"] == {"new_value": 2, "old_value": 1}
