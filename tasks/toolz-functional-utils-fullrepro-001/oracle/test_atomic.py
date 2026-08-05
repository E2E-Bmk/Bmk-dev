from __future__ import annotations

from collections import OrderedDict
from operator import add, mul
from random import Random

import pytest

import toolz
from toolz import curried


def test_public_import_surface_exposes_functional_names():
    names = (
        "accumulate",
        "assoc",
        "compose",
        "concat",
        "curry",
        "groupby",
        "juxt",
        "memoize",
        "merge",
        "partition",
        "pipe",
        "reduceby",
        "update_in",
    )
    assert all(callable(getattr(toolz, name)) for name in names)
    assert callable(curried.map)
    assert callable(curried.get_in)


def test_identity_apply_and_basic_aliases():
    assert toolz.identity("value") == "value"
    assert toolz.apply(add, 4, 5) == 9
    assert toolz.comp(str, toolz.identity)(7) == "7"


def test_accumulate_supports_default_and_initial():
    assert list(toolz.accumulate(add, [1, 2, 3, 4])) == [1, 3, 6, 10]
    assert list(toolz.accumulate(add, [1, 2, 3], 10)) == [10, 11, 13, 16]
    assert list(toolz.accumulate(mul, [])) == []


def test_groupby_accepts_callable_and_member_key():
    records = [
        {"name": "Ada", "team": "red"},
        {"name": "Lin", "team": "blue"},
        {"name": "Max", "team": "red"},
    ]
    assert toolz.groupby("team", records) == {
        "red": [records[0], records[2]],
        "blue": [records[1]],
    }
    assert toolz.groupby(len, ["a", "bb", "c"]) == {1: ["a", "c"], 2: ["bb"]}


def test_iterable_slicing_helpers_materialize_expected_values():
    values = [0, 1, 2, 3, 4, 5]
    assert list(toolz.take(3, values)) == [0, 1, 2]
    assert list(toolz.drop(3, values)) == [3, 4, 5]
    assert list(toolz.take_nth(2, values)) == [0, 2, 4]
    assert toolz.tail(2, values) == [4, 5]


def test_get_supports_scalar_multiple_and_default():
    data = {"a": 10, "b": 20}
    assert toolz.get("a", data) == 10
    assert toolz.get(["a", "missing"], data, None) == (10, None)
    assert toolz.get([], data) == ()


def test_first_second_nth_last_access_sequences():
    values = ("zero", "one", "two", "three")
    assert toolz.first(values) == "zero"
    assert toolz.second(values) == "one"
    assert toolz.nth(2, iter(values)) == "two"
    assert toolz.last(values) == "three"


def test_concat_concatv_and_mapcat_flatten_sequences():
    assert list(toolz.concat([[1, 2], (), [3]])) == [1, 2, 3]
    assert list(toolz.concatv([1], [2, 3])) == [1, 2, 3]
    assert list(toolz.mapcat(lambda text: text.upper(), ["ab", "c"])) == [
        "A",
        "B",
        "C",
    ]


def test_cons_and_interpose_preserve_order():
    assert list(toolz.cons("start", ["middle", "end"])) == [
        "start",
        "middle",
        "end",
    ]
    assert list(toolz.interpose("|", ["a", "b", "c"])) == ["a", "|", "b", "|", "c"]


def test_frequencies_counts_hashable_values():
    assert toolz.frequencies(["red", "blue", "red", "red", "blue"]) == {
        "red": 3,
        "blue": 2,
    }


def test_reduceby_groups_and_reduces_with_init():
    rows = [
        {"team": "red", "score": 2},
        {"team": "blue", "score": 5},
        {"team": "red", "score": 3},
    ]
    result = toolz.reduceby(
        "team",
        lambda total, row: total + row["score"],
        rows,
        0,
    )
    assert result == {"red": 5, "blue": 5}


def test_partition_and_partition_all_handle_remainders():
    assert list(toolz.partition(2, [1, 2, 3, 4, 5])) == [(1, 2), (3, 4)]
    assert list(toolz.partition(2, [1, 2, 3], pad=None)) == [(1, 2), (3, None)]
    assert list(toolz.partition_all(2, [1, 2, 3])) == [(1, 2), (3,)]


def test_pluck_and_sliding_window_project_data():
    assert list(toolz.pluck("name", [{"name": "A"}, {"name": "B"}])) == ["A", "B"]
    assert list(toolz.pluck("name", [{"name": "A"}, {}], default="?")) == ["A", "?"]
    assert list(toolz.sliding_window(3, [1, 2, 3, 4])) == [(1, 2, 3), (2, 3, 4)]


def test_unique_and_isdistinct_preserve_first_occurrences():
    assert list(toolz.unique(["ant", "ape", "ant", "bat"])) == ["ant", "ape", "bat"]
    assert list(toolz.unique(["ant", "mouse", "cat"], key=len)) == ["ant", "mouse"]
    assert toolz.isdistinct([1, 2, 3]) is True
    assert toolz.isdistinct([1, 2, 1]) is False


def test_merge_sorted_and_topk_order_values():
    assert list(toolz.merge_sorted([1, 4], [2, 3], [5])) == [1, 2, 3, 4, 5]
    assert toolz.topk(2, [4, 1, 9, 3]) == (9, 4)
    assert toolz.topk(2, ["ant", "elephant", "cat"], key=len) == (
        "elephant",
        "ant",
    )


def test_diff_and_peek_helpers_preserve_stream_views():
    assert list(toolz.diff([1, 2, 3], [1, 4, 3])) == [(2, 4)]
    first, replayable = toolz.peek(iter([10, 20, 30]))
    assert first == 10
    assert list(replayable) == [10, 20, 30]
    head, replayable = toolz.peekn(2, iter([10, 20, 30]))
    assert head == (10, 20)
    assert list(replayable) == [10, 20, 30]


def test_count_works_for_materialized_and_generator():
    assert toolz.count([1, 2, 3]) == 3
    assert toolz.count(item for item in [1, 2, 3, 4]) == 4


def test_merge_and_merge_with_precedence():
    assert toolz.merge({"a": 1, "shared": "old"}, {"b": 2, "shared": "new"}) == {
        "a": 1,
        "b": 2,
        "shared": "new",
    }
    assert toolz.merge_with(sum, {"a": 1, "b": 2}, {"a": 3, "c": 4}) == {
        "a": 4,
        "b": 2,
        "c": 4,
    }


def test_mapping_transforms_preserve_key_value_relationships():
    data = {"a": 1, "b": 2}
    assert toolz.valmap(lambda value: value * 10, data) == {"a": 10, "b": 20}
    assert toolz.keymap(str.upper, data) == {"A": 1, "B": 2}
    assert toolz.itemmap(lambda item: (item[0] * 2, item[1] + 1), data) == {
        "aa": 2,
        "bb": 3,
    }


def test_mapping_filters_select_by_predicate():
    data = {"a": 1, "b": 2, "c": 3}
    assert toolz.valfilter(lambda value: value % 2, data) == {"a": 1, "c": 3}
    assert toolz.keyfilter(lambda key: key != "b", data) == {"a": 1, "c": 3}
    assert toolz.itemfilter(lambda item: item[1] > 1, data) == {"b": 2, "c": 3}


def test_assoc_and_dissoc_return_copies():
    original = {"a": 1, "b": 2}
    changed = toolz.assoc(original, "a", 9)
    removed = toolz.dissoc(original, "b", "missing")
    assert original == {"a": 1, "b": 2}
    assert changed == {"a": 9, "b": 2}
    assert removed == {"a": 1}
    assert changed is not original


def test_nested_dict_updates_are_immutable():
    original = {"profile": {"name": "Ada", "visits": 1}}
    changed = toolz.assoc_in(original, ["profile", "name"], "Lin")
    incremented = toolz.update_in(
        original,
        ["profile", "visits"],
        lambda value: value + 1,
        0,
    )
    assert original["profile"] == {"name": "Ada", "visits": 1}
    assert changed["profile"] == {"name": "Lin", "visits": 1}
    assert incremented["profile"]["visits"] == 2


def test_get_in_reads_nested_sequences_with_default():
    data = {"items": [{"name": "first"}, {"name": "second"}]}
    assert toolz.get_in(["items", 1, "name"], data) == "second"
    assert toolz.get_in(["items", 5, "name"], data, "missing") == "missing"


def test_compose_compose_left_and_pipe_order():
    add_one = lambda value: value + 1
    double = lambda value: value * 2
    assert toolz.compose(str, double, add_one)(3) == "8"
    assert toolz.compose_left(add_one, double)(3) == 8
    assert toolz.pipe(3, add_one, double) == 8


def test_juxt_returns_parallel_results():
    measure = toolz.juxt(len, lambda value: value[0])
    assert measure("abcd") == (4, "a")
    assert toolz.juxt([lambda x: x + 1, lambda x: x * 2])(3) == (4, 6)


def test_curry_supports_partial_positional_and_keyword_application():
    def combine(prefix, value, suffix="!"):
        return prefix + str(value) + suffix

    curried = toolz.curry(combine)
    assert curried("item")(3) == "item3!"
    assert curried("item", suffix=".")(3) == "item3."
    assert curried(prefix="item")(value=3, suffix="?") == "item3?"


def test_curry_exposes_public_bound_arguments():
    def add_three(a, b, c=0):
        return a + b + c

    bound = toolz.curry(add_three, 1, c=4)
    assert bound.func is add_three
    assert bound.args == (1,)
    assert bound.keywords == {"c": 4}
    assert bound(2) == 7


def test_memoize_reuses_result_without_timing():
    calls = []

    def square(value):
        calls.append(value)
        return value * value

    cached = toolz.memoize(square)
    assert cached(5) == 25
    assert cached(5) == 25
    assert cached(6) == 36
    assert calls == [5, 6]


def test_do_and_complement_compose_side_effect_and_predicate():
    observed = []
    remember = lambda value: toolz.do(observed.append, value)
    assert toolz.compose(lambda value: value * 2, remember)(4) == 8
    assert observed == [4]
    assert toolz.complement(lambda value: value % 2 == 0)(3) is True
    assert toolz.complement(lambda value: value % 2 == 0)(4) is False


def test_thread_first_and_thread_last_place_values():
    assert toolz.thread_first(2, (add, 3), (mul, 4)) == 20
    assert toolz.thread_last(2, (add, 3), (mul, 4)) == 20
    assert list(toolz.thread_last([1, 2, 3], (map, lambda x: x + 1))) == [2, 3, 4]


def test_flip_and_excepts_adapt_callables():
    assert toolz.flip(lambda left, right: left - right, 2, 10) == 8
    safe_index = toolz.excepts(ValueError, lambda value: [1, 2].index(value), lambda _: -1)
    assert safe_index(2) == 1
    assert safe_index(9) == -1


def test_curried_iterable_functions_accept_partial_arguments():
    data = [1, 2, 3, 4]
    assert list(curried.take(2)(data)) == [1, 2]
    assert list(curried.map(lambda value: value * 2)(data)) == [2, 4, 6, 8]
    assert list(curried.filter(lambda value: value % 2)(data)) == [1, 3]


def test_curried_dict_functions_accept_partial_arguments():
    data = {"a": 1, "b": 2, "c": 3}
    assert curried.valmap(lambda value: value + 1)(data) == {"a": 2, "b": 3, "c": 4}
    assert curried.keyfilter(lambda key: key != "b")(data) == {"a": 1, "c": 3}
    assert curried.get_in(["nested", "value"])({"nested": {"value": 7}}) == 7


def test_curried_compose_and_pipe_workflow():
    transform = curried.compose(str, lambda value: value + 2)
    assert transform(5) == "7"
    assert curried.pipe(3, lambda value: value * 2, str) == "6"


def test_custom_factories_are_used_for_mapping_results():
    data = {"a": 1, "b": 2}
    merged = toolz.merge({"a": 1}, {"b": 2}, factory=OrderedDict)
    mapped = toolz.valmap(lambda value: value * 2, data, factory=OrderedDict)
    assert isinstance(merged, OrderedDict)
    assert isinstance(mapped, OrderedDict)
    assert list(mapped.items()) == [("a", 2), ("b", 4)]


def test_update_in_applies_function_to_default_for_missing_path():
    seen = []

    def add_to_zero(value):
        seen.append(value)
        return value + 5

    result = toolz.update_in({}, ["stats", "count"], add_to_zero, 0)
    assert result == {"stats": {"count": 5}}
    assert seen == [0]


def test_random_sample_is_repeatable_with_explicit_seed():
    first = list(toolz.random_sample(0.4, range(12), random_state=Random(17)))
    second = list(toolz.random_sample(0.4, range(12), random_state=Random(17)))
    assert first == second


def test_join_matches_records_by_public_key_functions():
    left = [("a", 1), ("b", 2)]
    right = [("b", "B"), ("c", "C")]
    assert list(toolz.join(0, left, 0, right)) == [(("b", 2), ("b", "B"))]
