# Astroid Stage 3A Rewrite Audit

Generated for `S3A_IMPORT_AUDIT` / `S3A_REWRITE`. File-level import classification is recorded here; function-level fairness/accounting is in `candidate_filter_map.md`.

Rechecked for `spec_v2` / `filter_iter=1`: Track A accounting is unchanged and reused; no upstream nodeid becomes scoreable under the factual spec corrections, so Track B remains the oracle source.

## Summary

- total_files: 63
- retained_files: 63
- discarded_files: 0
- discard_rate: 0/63 (0.00%)
- functions_in_scope: 1591
- shared_helper_files_scanned: tests/__init__.py, tests/resources.py, tests/testdata/** (referenced by upstream tests)
- decision_note: upstream files are retained for function-level accounting, but no raw upstream nodeid is kept because the suite is dominated by non-spec astroid utility modules, internal shapes, exact renderer text, testdata fixtures, or implementation-coupled inference expectations. Track B supplies the scoreable oracle.

## Per-file audit

| file | test_count | import_type | decision | rewrite_result | failure_reason | notes |
|---|---:|---|---|---|---|---|
| tests/benchmarks/test_bench_endtoend.py | 4 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_core_einsumfunc.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_core_fromnumeric.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_core_function_base.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_core_multiarray.py | 5 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_core_numeric.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_core_numerictypes.py | 9 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.brain.brain_numpy_utils |
| tests/brain/numpy/test_core_umath.py | 8 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_ma.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/numpy/test_ndarray.py | 3 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.brain.brain_numpy_utils |
| tests/brain/numpy/test_random_mtrand.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_argparse.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_attr.py | 9 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_brain.py | 142 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.bases, astroid.brain.brain_namedtuple_enum, astroid.const |
| tests/brain/test_builtin.py | 5 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_ctypes.py | 3 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_dataclasses.py | 39 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.util |
| tests/brain/test_dateutil.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_enum.py | 32 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_gi.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_hashlib.py | 3 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.nodes.scoped_nodes |
| tests/brain/test_helpers.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_multiprocessing.py | 4 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_named_tuple.py | 23 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_pathlib.py | 4 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.util |
| tests/brain/test_pytest.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_qt.py | 3 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.bases, astroid.const |
| tests/brain/test_regex.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_signal.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_six.py | 7 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.nodes.scoped_nodes |
| tests/brain/test_ssl.py | 2 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const |
| tests/brain/test_statistics.py | 4 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.util |
| tests/brain/test_threading.py | 4 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.bases |
| tests/brain/test_typing.py | 4 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_typing_extensions.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/brain/test_unittest.py | 1 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/test_builder.py | 59 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.nodes.scoped_nodes |
| tests/test_constraint.py | 40 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.bases, astroid.util |
| tests/test_decorators.py | 3 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: _pytest.recwarn, astroid.decorators |
| tests/test_filter_statements.py | 1 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.filter_statements |
| tests/test_get_relative_base_path.py | 8 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/test_group_exceptions.py | 5 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.context |
| tests/test_helpers.py | 21 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const |
| tests/test_inference.py | 401 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.arguments, astroid.bases, astroid.const, astroid.context, astroid.objects |
| tests/test_inference_calls.py | 24 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.util |
| tests/test_lookup.py | 54 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/test_manager.py | 50 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.interpreter._import, astroid.modutils, astroid.nodes.scoped_nodes |
| tests/test_modutils.py | 62 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.interpreter._import |
| tests/test_nodes.py | 125 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.context, astroid.nodes.node_classes, astroid.nodes.scoped_nodes, tests.testdata.python3.recursion_error |
| tests/test_nodes_lineno.py | 23 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const |
| tests/test_nodes_position.py | 6 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/test_object_model.py | 45 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const |
| tests/test_objects.py | 24 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.objects |
| tests/test_protocols.py | 33 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.util |
| tests/test_python3.py | 26 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/test_raw_building.py | 16 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: _io, astroid.const, astroid.raw_building, tests.testdata.python3.data.fake_module_with_broken_getattr, tests.testdata.python3.data.fake_module_with_collection_getattribute, tests.testdata.python3.data.fake_module_with_warnings |
| tests/test_regrtest.py | 34 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const, astroid.context, astroid.raw_building, astroid.util |
| tests/test_scoped_nodes.py | 165 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.bases, astroid.const, astroid.nodes.scoped_nodes.scoped_nodes |
| tests/test_stdlib.py | 2 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/test_transforms.py | 9 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.brain.brain_dataclasses, astroid.const, tests.testdata.python3.recursion_error |
| tests/test_type_params.py | 9 | non-spec/private import | retain_for_node_filter | per_function_accounting | - | non-spec/private imports: astroid.const |
| tests/test_utils.py | 8 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
| tests/testdata/python3/data/module_dict_items_call/test.py | 0 | clean or public/test dependency | retain_for_node_filter | not_needed | - | top-level imports are public/stdlib/test dependencies; function assertions still require fairness filtering |
