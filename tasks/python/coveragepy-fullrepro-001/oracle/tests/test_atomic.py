from __future__ import annotations

from pathlib import Path

from tests.atomic_support import close_coverage, close_data, sandbox, working_directory


def test_a01_public_surface_and_exception_taxonomy():
    import coverage
    from coverage import Coverage, CoverageData, CoverageException, CoveragePlugin, FileReporter, FileTracer
    from coverage.exceptions import ConfigError, DataError, NoCode, NoDataError, NoSource, NotPython, PluginError

    assert isinstance(coverage.__version__, str) and coverage.__version__
    assert isinstance(coverage.version_info, tuple) and len(coverage.version_info) >= 3
    assert coverage.coverage is Coverage
    assert all(isinstance(value, type) for value in (CoverageData, CoveragePlugin, FileReporter, FileTracer))
    assert all(issubclass(exc, CoverageException) for exc in (ConfigError, DataError, NoDataError, NoSource, NoCode, NotPython, PluginError))
    assert issubclass(NoCode, NoSource)


def test_a02_configuration_free_defaults_are_stable():
    from coverage import Coverage

    cov = Coverage(data_file=None, config_file=False)
    try:
        assert cov.get_option("run:branch") is False
        assert cov.get_option("run:parallel") is False
        assert cov.get_option("report:precision") == 0
        assert cov.get_option("report:skip_covered") is False
    finally:
        close_coverage(cov)


def test_a03_run_and_report_options_round_trip_independently():
    from coverage import Coverage

    cov = Coverage(data_file=None, config_file=False)
    try:
        cov.set_option("run:branch", True)
        cov.set_option("run:parallel", True)
        cov.set_option("report:precision", 3)
        cov.set_option("report:skip_covered", True)
        assert cov.get_option("run:branch") is True
        assert cov.get_option("run:parallel") is True
        assert cov.get_option("report:precision") == 3
        assert cov.get_option("report:skip_covered") is True
    finally:
        close_coverage(cov)


def test_a04_exclude_and_partial_lists_clear_independently():
    from coverage import Coverage

    cov = Coverage(data_file=None, config_file=False)
    try:
        cov.exclude(r"V2_EXCLUDE_[A-Z]+")
        cov.exclude(r"V2_PARTIAL_[A-Z]+", which="partial")
        assert r"V2_EXCLUDE_[A-Z]+" in cov.get_exclude_list("exclude")
        assert r"V2_PARTIAL_[A-Z]+" in cov.get_exclude_list("partial")
        cov.clear_exclude("exclude")
        assert cov.get_exclude_list("exclude") == []
        assert r"V2_PARTIAL_[A-Z]+" in cov.get_exclude_list("partial")
        cov.clear_exclude("partial")
        assert cov.get_exclude_list("partial") == []
    finally:
        close_coverage(cov)


def test_a05_data_filename_views_share_one_canonical_base():
    from coverage import Coverage

    with sandbox() as root:
        project, elsewhere = root / "project", root / "elsewhere"
        project.mkdir()
        elsewhere.mkdir()
        (project / ".coveragerc").write_text("[run]\ndata_file = state/ledger.coverage\n", encoding="utf-8")
        with working_directory(project):
            cov = Coverage(config_file=True)
            cov.get_option("run:data_file")
        try:
            with working_directory(elsewhere):
                data = cov.get_data()
            target = (project / "state" / "ledger.coverage").resolve()
            assert Path(data.base_filename()) == target
            assert Path(data.data_filename()) == target
        finally:
            close_coverage(cov)


def test_a06_line_mode_deduplicates_and_preserves_empty_identity():
    from coverage import CoverageData

    with sandbox() as root:
        measured = str(root / "measured.py")
        empty = str(root / "empty.py")
        unknown = str(root / "unknown.py")
        data = CoverageData(no_disk=True)
        try:
            data.add_lines({measured: [8, 5, 8, 3]})
            data.touch_file(empty)
            assert set(data.lines(measured) or []) == {3, 5, 8}
            assert data.lines(empty) == []
            assert data.lines(unknown) is None
            assert data.has_arcs() is False
        finally:
            close_data(data)


def test_a07_arc_mode_preserves_entry_exit_and_unknown_distinction():
    from coverage import CoverageData

    with sandbox() as root:
        measured = str(root / "flow.py")
        unknown = str(root / "unknown.py")
        data = CoverageData(no_disk=True)
        try:
            data.add_arcs({measured: [(-7, 4), (4, 9), (9, -7), (4, 9)]})
            assert set(data.arcs(measured) or []) == {(-7, 4), (4, 9), (9, -7)}
            assert data.arcs(unknown) is None
            assert data.has_arcs() is True
        finally:
            close_data(data)


def test_a08_one_data_object_rejects_cross_mode_mixing_transactionally():
    import pytest
    from coverage import CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        name = str(root / "mode.py")
        lines = CoverageData(no_disk=True)
        arcs = CoverageData(no_disk=True)
        try:
            lines.add_lines({name: {2, 4}})
            before_lines = lines.dumps()
            with pytest.raises(DataError):
                lines.add_arcs({name: {(-1, 2), (2, -1)}})
            assert lines.dumps() == before_lines
            arcs.add_arcs({name: {(-1, 2), (2, -1)}})
            before_arcs = arcs.dumps()
            with pytest.raises(DataError):
                arcs.add_lines({name: {2}})
            assert arcs.dumps() == before_arcs
        finally:
            close_data(lines, arcs)


def test_a09_exact_context_filters_file_and_payload_views_literally():
    from coverage import CoverageData

    with sandbox() as root:
        literal_file = str(root / "literal.py")
        neighbor_file = str(root / "neighbor.py")
        data = CoverageData(no_disk=True)
        try:
            data.set_context("job[4].done")
            data.add_lines({literal_file: {11, 13}})
            data.set_context("job4Xdone")
            data.add_lines({neighbor_file: {17}})
            data.set_query_context("job[4].done")
            assert data.measured_files() == {literal_file}
            assert set(data.lines(literal_file) or []) == {11, 13}
            assert data.lines(neighbor_file) == []
            assert set(data.contexts_by_lineno(literal_file)) == {11, 13}
        finally:
            close_data(data)


def test_a10_file_tracer_has_named_empty_and_unknown_states():
    from coverage import CoverageData

    with sandbox() as root:
        (root / "aliases").mkdir()
        seed = str(root / "seed.py")
        plain = str(root / "plain.py")
        templated = str((root / "template.src").resolve())
        templated_alias = str(root / "aliases" / ".." / "template.src")
        unknown = str(root / "unknown.py")
        data = CoverageData(no_disk=True)
        try:
            data.add_lines({seed: {1}})
            data.touch_file(plain)
            data.touch_file(templated_alias, plugin_name="render-v2")
            assert data.file_tracer(templated) == "render-v2"
            assert data.file_tracer(templated_alias) == "render-v2"
            assert data.file_tracer(plain) == ""
            assert data.file_tracer(unknown) is None
            assert templated_alias not in data.measured_files()
        finally:
            close_data(data)


def test_a11_tracer_repetition_is_idempotent_and_conflict_preserves_value():
    import pytest
    from coverage import CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        name = str(root / "template.src")
        data = CoverageData(no_disk=True)
        try:
            data.add_lines({str(root / "seed.py"): {1}})
            data.touch_file(name, plugin_name="render-v2")
            data.add_file_tracers({name: "render-v2"})
            with pytest.raises(DataError):
                data.add_file_tracers({name: "other-renderer"})
            assert data.file_tracer(name) == "render-v2"
        finally:
            close_data(data)


def test_a12_batch_touch_requires_mode_and_establishes_empty_files():
    import pytest
    from coverage import CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        first = str(root / "first.py")
        second = str(root / "second.py")
        data = CoverageData(no_disk=True)
        try:
            with pytest.raises(DataError):
                data.touch_files([first, second])
            data.add_lines({str(root / "seed.py"): {1}})
            data.touch_files([second, first])
            assert data.lines(first) == [] and data.lines(second) == []
            assert {first, second} <= data.measured_files()
        finally:
            close_data(data)


def test_a13_purge_retains_identity_and_tracer_but_clears_payload_contexts():
    from coverage import CoverageData

    with sandbox() as root:
        (root / "aliases").mkdir()
        target = str((root / "target.py").resolve())
        target_alias = str(root / "aliases" / ".." / "target.py")
        peer = str(root / "peer.py")
        data = CoverageData(no_disk=True)
        try:
            data.set_context("purge/v2")
            data.add_lines({target: {4, 6}, peer: {9}})
            data.add_file_tracers({target: "render-v2"})
            data.purge_files([target_alias])
            assert target in data.measured_files()
            assert data.lines(target) == [] and data.contexts_by_lineno(target) == {}
            assert data.file_tracer(target) == "render-v2"
            assert data.lines(peer) == [9]
        finally:
            close_data(data)


def test_a14_line_update_merges_file_and_line_unions():
    from coverage import CoverageData

    with sandbox() as root:
        shared, added = str(root / "shared.py"), str(root / "added.py")
        left, right = CoverageData(no_disk=True), CoverageData(no_disk=True)
        try:
            left.add_lines({shared: {2, 5}})
            right.add_lines({shared: {5, 7}, added: {3}})
            left.update(right)
            assert set(left.lines(shared) or []) == {2, 5, 7}
            assert left.lines(added) == [3]
        finally:
            close_data(left, right)


def test_a15_arc_update_merges_entry_exit_and_file_unions():
    from coverage import CoverageData

    with sandbox() as root:
        shared, added = str(root / "shared.py"), str(root / "added.py")
        left, right = CoverageData(no_disk=True), CoverageData(no_disk=True)
        try:
            left.add_arcs({shared: {(-1, 2), (2, -1)}})
            right.add_arcs({shared: {(2, 5), (5, -1)}, added: {(-1, 3), (3, -1)}})
            left.update(right)
            assert set(left.arcs(shared) or []) == {(-1, 2), (2, -1), (2, 5), (5, -1)}
            assert set(left.arcs(added) or []) == {(-1, 3), (3, -1)}
        finally:
            close_data(left, right)


def test_a16_cross_mode_update_leaves_both_operands_unchanged():
    import pytest
    from coverage import CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        lines, arcs = CoverageData(no_disk=True), CoverageData(no_disk=True)
        try:
            lines.add_lines({str(root / "line.py"): {3}})
            arcs.add_arcs({str(root / "arc.py"): {(-1, 4), (4, -1)}})
            line_blob, arc_blob = lines.dumps(), arcs.dumps()
            with pytest.raises(DataError):
                lines.update(arcs)
            assert lines.dumps() == line_blob and arcs.dumps() == arc_blob
        finally:
            close_data(lines, arcs)


def test_a17_dumps_and_loads_round_trip_complete_logical_state():
    from coverage import CoverageData

    with sandbox() as root:
        measured, empty = str(root / "measured.py"), str(root / "empty.py")
        original, restored = CoverageData(no_disk=True), CoverageData(no_disk=True)
        try:
            original.set_context("serialize/v2")
            original.add_lines({measured: {6, 10}})
            original.touch_file(empty, plugin_name="render-v2")
            restored.loads(original.dumps())
            assert restored.measured_files() == {measured, empty}
            assert set(restored.lines(measured) or []) == {6, 10}
            assert restored.lines(empty) == []
            assert restored.measured_contexts() == {"serialize/v2"}
            assert restored.file_tracer(empty) == "render-v2"
        finally:
            close_data(original, restored)


def test_a18_current_is_owned_only_during_normal_collection():
    import sys
    from coverage import Coverage

    with sandbox() as root:
        program = root / "lifecycle.py"
        program.write_text("value = 18\n", encoding="utf-8")
        cov = Coverage(data_file=None, config_file=False, timid=True)
        initial_trace = sys.gettrace()
        try:
            assert Coverage.current() is None
            with cov.collect():
                assert Coverage.current() is cov
                with cov.collect():
                    assert Coverage.current() is cov
                    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
                assert Coverage.current() is cov
            assert Coverage.current() is None
            assert sys.gettrace() is initial_trace
        finally:
            close_coverage(cov)
