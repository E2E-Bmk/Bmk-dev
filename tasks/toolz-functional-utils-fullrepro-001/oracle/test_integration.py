from __future__ import annotations

from operator import add

import pytest

import toolz
from toolz import curried


@pytest.mark.depends_on(
    "test_concat_concatv_and_mapcat_flatten_sequences",
    "test_frequencies_counts_hashable_values",
    "test_merge_sorted_and_topk_order_values",
)
def test_text_analytics_pipeline_combines_flatten_count_and_ranking():
    words = ["Ada", "Ada", "Lin", "Max"]
    tokens = toolz.mapcat(lambda word: [word.lower(), word[0].lower()], words)
    counts = toolz.frequencies(tokens)
    assert set(toolz.topk(2, counts.items(), key=lambda item: item[1])) == {
        ("a", 2),
        ("ada", 2),
    }


@pytest.mark.depends_on("test_groupby_accepts_callable_and_member_key", "test_reduceby_groups_and_reduces_with_init")
def test_grouped_scores_workflow_uses_grouping_then_reduction():
    rows = [
        {"team": "red", "score": 2},
        {"team": "blue", "score": 5},
        {"team": "red", "score": 3},
    ]
    groups = toolz.groupby("team", rows)
    totals = toolz.reduceby("team", lambda total, row: total + row["score"], rows, 0)
    assert sorted(groups) == ["blue", "red"]
    assert totals == {"red": 5, "blue": 5}


@pytest.mark.depends_on(
    "test_partition_and_partition_all_handle_remainders",
    "test_concat_concatv_and_mapcat_flatten_sequences",
)
def test_chunk_transform_workflow_reassembles_normalized_values():
    chunks = toolz.partition_all(2, ["a", "b", "c", "d", "e"])
    normalized = toolz.mapcat(lambda chunk: [item.upper() for item in chunk], chunks)
    assert list(toolz.concat([normalized])) == ["A", "B", "C", "D", "E"]


@pytest.mark.depends_on("test_iterable_slicing_helpers_materialize_expected_values", "test_count_works_for_materialized_and_generator")
def test_lazy_window_selection_workflow_preserves_source_count():
    source = (value for value in range(8))
    selected = toolz.take(3, toolz.drop(2, source))
    assert list(selected) == [2, 3, 4]
    assert toolz.count([2, 3, 4]) == 3


@pytest.mark.depends_on("test_merge_sorted_and_topk_order_values", "test_diff_and_peek_helpers_preserve_stream_views")
def test_sorted_stream_comparison_workflow_reports_ranked_differences():
    merged = toolz.merge_sorted([1, 4], [2, 5])
    first, replay = toolz.peek(merged)
    differences = list(toolz.diff(list(replay), [1, 2, 3, 5]))
    assert first == 1
    assert differences == [(4, 3)]
    assert toolz.topk(2, differences, key=lambda pair: pair[0]) == ((4, 3),)


@pytest.mark.depends_on(
    "test_diff_and_peek_helpers_preserve_stream_views",
    "test_get_supports_scalar_multiple_and_default",
)
def test_peek_and_index_workflow_reads_a_replayable_record_stream():
    first, replay = toolz.peek(iter([("a", 10), ("b", 20)]))
    labels = list(toolz.pluck(0, replay))
    assert first == ("a", 10)
    assert labels == ["a", "b"]
    assert toolz.get(1, first) == 10


@pytest.mark.depends_on("test_assoc_and_dissoc_return_copies", "test_get_in_reads_nested_sequences_with_default", "test_nested_dict_updates_are_immutable")
def test_nested_profile_workflow_updates_then_reads_without_mutation():
    profile = {"user": {"name": "Ada", "visits": 1}, "active": True}
    updated = toolz.update_in(profile, ["user", "visits"], lambda value: value + 1, 0)
    updated = toolz.assoc_in(updated, ["user", "name"], "Lin")
    assert toolz.get_in(["user", "name"], updated) == "Lin"
    assert toolz.get_in(["user", "visits"], updated) == 2
    assert profile["user"] == {"name": "Ada", "visits": 1}


@pytest.mark.depends_on("test_merge_and_merge_with_precedence", "test_mapping_filters_select_by_predicate", "test_mapping_transforms_preserve_key_value_relationships")
def test_dictionary_cleaning_workflow_merges_filters_and_maps_values():
    merged = toolz.merge({"a": 1, "b": 2}, {"b": 3, "c": 4})
    filtered = toolz.keyfilter(lambda key: key != "b", merged)
    rendered = toolz.valmap(lambda value: f"v{value}", filtered)
    assert rendered == {"a": "v1", "c": "v4"}


@pytest.mark.depends_on("test_compose_compose_left_and_pipe_order", "test_curry_supports_partial_positional_and_keyword_application")
def test_composed_curry_workflow_builds_parameterized_formatter():
    def add_suffix(prefix, value):
        return f"{prefix}{value}"

    formatter = toolz.curry(add_suffix, "item-")
    render = toolz.compose(str.upper, formatter)
    assert toolz.pipe(7, render) == "ITEM-7"


@pytest.mark.depends_on("test_memoize_reuses_result_without_timing", "test_compose_compose_left_and_pipe_order")
def test_memoized_composition_workflow_counts_only_distinct_inputs():
    calls = []

    def normalize(value):
        calls.append(value)
        return value.strip().lower()

    cached = toolz.memoize(normalize)
    render = toolz.compose(lambda value: value.title(), cached)
    assert render(" Ada ") == "Ada"
    assert render(" Ada ") == "Ada"
    assert calls == [" Ada "]


@pytest.mark.depends_on("test_juxt_returns_parallel_results", "test_do_and_complement_compose_side_effect_and_predicate")
def test_parallel_projection_workflow_logs_and_classifies_values():
    audit = []
    classify = toolz.juxt(len, lambda value: value.startswith("A"))
    project = toolz.compose(
        lambda value: toolz.do(audit.append, value),
        classify,
    )
    assert project("Ada") == (3, True)
    assert audit == [(3, True)]


@pytest.mark.depends_on("test_thread_first_and_thread_last_place_values", "test_partition_and_partition_all_handle_remainders")
def test_threaded_chunk_workflow_transforms_values_before_partitioning():
    result = toolz.thread_last(
        [1, 2, 3, 4],
        (map, lambda value: value * 10),
        (toolz.partition_all, 2),
    )
    assert list(result) == [(10, 20), (30, 40)]


@pytest.mark.depends_on("test_curried_iterable_functions_accept_partial_arguments", "test_pluck_and_sliding_window_project_data")
def test_curried_record_workflow_filters_then_plucks_fields():
    records = [{"id": 1, "ok": True}, {"id": 2, "ok": False}, {"id": 3, "ok": True}]
    active = curried.filter(lambda record: record["ok"], records)
    ids = curried.pluck("id")(active)
    assert list(ids) == [1, 3]


@pytest.mark.depends_on("test_curried_dict_functions_accept_partial_arguments", "test_get_in_reads_nested_sequences_with_default")
def test_curried_nested_update_workflow_reuses_public_partial_forms():
    data = {"stats": {"count": 2}, "name": "Ada"}
    increment = curried.update_in(data)
    updated = increment(["stats", "count"], lambda value: value + 1, 0)
    renamed = curried.assoc_in(updated)(["name"], "Lin")
    assert curried.get_in(["stats", "count"])(renamed) == 3
    assert renamed["name"] == "Lin"


@pytest.mark.depends_on("test_accumulate_supports_default_and_initial", "test_reduceby_groups_and_reduces_with_init")
def test_curried_reduction_workflow_accumulates_each_group():
    values = [1, 2, 3, 4]
    totals = curried.reduceby(lambda value: value % 2, add, values, 0)
    running = curried.accumulate(add)([1, 2, 3])
    assert totals == {1: 4, 0: 6}
    assert list(running) == [1, 3, 6]


@pytest.mark.depends_on("test_curried_compose_and_pipe_workflow", "test_curried_iterable_functions_accept_partial_arguments")
def test_curried_pipeline_workflow_normalizes_and_selects_values():
    normalize = lambda value: value.strip().lower()
    values = [" Ada ", "Lin ", " Ada "]
    normalized = curried.map(normalize)(values)
    unique = curried.unique(normalized)
    assert list(unique) == ["ada", "lin"]


@pytest.mark.depends_on("test_merge_and_merge_with_precedence", "test_frequencies_counts_hashable_values")
def test_merge_with_frequency_workflow_combines_partition_counts():
    left = toolz.frequencies(["a", "a", "b"])
    right = toolz.frequencies(["b", "c", "c"])
    assert toolz.merge_with(sum, left, right) == {"a": 2, "b": 2, "c": 2}


@pytest.mark.depends_on("test_nested_dict_updates_are_immutable", "test_get_in_reads_nested_sequences_with_default")
def test_multi_level_update_workflow_creates_missing_branch_and_reads_it():
    result = toolz.update_in({}, ["settings", "limits", "max"], lambda value: value + 10, 5)
    assert toolz.get_in(["settings", "limits", "max"], result) == 15
    assert toolz.get_in(["settings", "missing"], result, None) is None


@pytest.mark.depends_on("test_groupby_accepts_callable_and_member_key", "test_mapping_transforms_preserve_key_value_relationships")
def test_member_group_workflow_renames_groups_and_projects_rows():
    grouped = toolz.groupby("team", [{"team": "r", "value": 1}, {"team": "b", "value": 2}])
    totals = toolz.valmap(lambda rows: sum(row["value"] for row in rows), grouped)
    renamed = toolz.keymap({"r": "red", "b": "blue"}.get, totals)
    assert renamed == {"red": 1, "blue": 2}


@pytest.mark.depends_on("test_concat_concatv_and_mapcat_flatten_sequences", "test_cons_and_interpose_preserve_order")
def test_token_stream_workflow_adds_prefixes_and_delimiters():
    tokens = toolz.cons("BEGIN", toolz.mapcat(list, ["ab", "cd"]))
    rendered = list(toolz.interpose("|", tokens))
    assert rendered == ["BEGIN", "|", "a", "|", "b", "|", "c", "|", "d"]


@pytest.mark.depends_on("test_partition_and_partition_all_handle_remainders", "test_pluck_and_sliding_window_project_data")
def test_windowed_batch_workflow_computes_adjacent_pair_sums():
    batches = toolz.partition_all(3, [1, 2, 3, 4, 5])
    windows = toolz.mapcat(lambda batch: toolz.sliding_window(2, batch), batches)
    assert list(toolz.map(sum, windows)) == [3, 5, 9]


@pytest.mark.depends_on("test_join_matches_records_by_public_key_functions", "test_groupby_accepts_callable_and_member_key")
def test_join_workflow_enriches_matching_records_then_groups_by_category():
    users = [(1, "Ada"), (2, "Lin"), (3, "Max")]
    events = [(1, "login"), (1, "edit"), (3, "login")]
    joined = toolz.join(0, users, 0, events)
    by_user = toolz.groupby(lambda pair: pair[0][1], joined)
    assert by_user == {
        "Ada": [((1, "Ada"), (1, "login")), ((1, "Ada"), (1, "edit"))],
        "Max": [((3, "Max"), (3, "login"))],
    }


@pytest.mark.depends_on(
    "test_random_sample_is_repeatable_with_explicit_seed",
    "test_merge_sorted_and_topk_order_values",
)
def test_seeded_sampling_workflow_can_be_ranked_deterministically():
    sample = list(toolz.random_sample(0.5, range(10), random_state=7))
    assert sample == list(toolz.random_sample(0.5, range(10), random_state=7))
    assert toolz.topk(2, sample) == tuple(sorted(sample, reverse=True)[:2])


@pytest.mark.depends_on("test_count_works_for_materialized_and_generator", "test_diff_and_peek_helpers_preserve_stream_views")
def test_generator_count_and_replay_workflow_preserves_observed_prefix():
    first, replay = toolz.peek((value for value in range(5)))
    remainder = list(toolz.drop(1, replay))
    assert first == 0
    assert toolz.count(remainder) == 4
    assert list(toolz.take(2, remainder)) == [1, 2]


@pytest.mark.depends_on("test_pluck_and_sliding_window_project_data", "test_merge_sorted_and_topk_order_values")
def test_ranked_record_workflow_plucks_values_and_selects_largest():
    records = [{"name": "A", "score": 4}, {"name": "B", "score": 9}, {"name": "C", "score": 6}]
    ranked = toolz.topk(2, records, key="score")
    assert list(toolz.pluck("name", ranked)) == ["B", "C"]


@pytest.mark.depends_on("test_flip_and_excepts_adapt_callables", "test_identity_apply_and_basic_aliases")
def test_adapted_predicate_workflow_filters_and_recovers_invalid_items():
    parse = toolz.excepts(ValueError, int, lambda _: None)
    values = list(map(parse, ["3", "bad", "4"]))
    divisible = toolz.flip(lambda value, expected: value % expected == 0, 2)
    evens = list(filter(lambda value: value is not None and divisible(value), values))
    assert values == [3, None, 4]
    assert evens == [4]


@pytest.mark.depends_on("test_custom_factories_are_used_for_mapping_results", "test_assoc_and_dissoc_return_copies")
def test_ordered_mapping_workflow_keeps_projection_order_across_updates():
    source = toolz.valmap(lambda value: value * 2, {"first": 1, "second": 2}, factory=dict)
    updated = toolz.assoc(source, "third", 6, factory=dict)
    assert list(updated) == ["first", "second", "third"]
    assert toolz.dissoc(updated, "second") == {"first": 2, "third": 6}


@pytest.mark.depends_on("test_curried_compose_and_pipe_workflow", "test_curried_dict_functions_accept_partial_arguments", "test_curried_iterable_functions_accept_partial_arguments")
def test_curried_end_to_end_workflow_projects_clean_nested_records():
    records = [
        {"name": " Ada ", "score": 4},
        {"name": " Lin ", "score": 8},
        {"name": " Ada ", "score": 9},
    ]
    clean = curried.map(
        lambda row: toolz.assoc(row, "name", row["name"].strip().lower())
    )(records)
    high = curried.filter(lambda row: row["score"] >= 8)(clean)
    names = curried.pluck("name")(high)
    assert list(names) == ["lin", "ada"]


@pytest.mark.depends_on("test_curry_exposes_public_bound_arguments", "test_thread_first_and_thread_last_place_values")
def test_function_adapter_workflow_binds_then_threads_arguments():
    add_prefix = toolz.curry(lambda prefix, value: prefix + value, "id:")
    result = toolz.thread_first("42", add_prefix, str.upper)
    assert result == "ID:42"


@pytest.mark.depends_on("test_reduceby_groups_and_reduces_with_init", "test_get_in_reads_nested_sequences_with_default")
def test_summary_workflow_reduces_rows_into_nested_report():
    rows = [
        {"kind": "a", "amount": 2},
        {"kind": "b", "amount": 3},
        {"kind": "a", "amount": 4},
    ]
    totals = toolz.reduceby("kind", lambda total, row: total + row["amount"], rows, 0)
    report = toolz.assoc_in({}, ["summary", "totals"], totals)
    assert toolz.get_in(["summary", "totals", "a"], report) == 6
    assert report == {"summary": {"totals": {"a": 6, "b": 3}}}
