from __future__ import annotations

import io
import os
from pathlib import Path

from tests.integration_support import (
    close_coverage,
    close_data,
    collect_program,
    exec_source,
    json_total,
    logical_snapshot,
    measured_file,
    run_cli,
    sandbox,
    working_directory,
    write_py,
)


def test_i01_measure_save_reload_and_file_projection_agree():
    from coverage import CoverageData

    with sandbox() as root:
        cov, program = collect_program(root, "alpha = 4\nbeta = alpha + 6\n")
        loaded = CoverageData(basename=str(root / ".coverage"))
        try:
            loaded.read()
            name = measured_file(loaded, "program.py")
            assert Path(name) == program.resolve()
            assert set(loaded.lines(name) or []) == {1, 2}
            assert name in cov.get_data().measured_files()
        finally:
            close_data(loaded)
            close_coverage(cov)


def test_i02_branch_arcs_analysis_and_text_totals_agree():
    with sandbox() as root:
        cov, program = collect_program(
            root,
            "flag = True\nif flag:\n    chosen = 8\nelse:\n    chosen = 13\n",
            branch=True,
        )
        output = io.StringIO()
        try:
            name = measured_file(cov.get_data(), "program.py")
            arcs = set(cov.get_data().arcs(name) or [])
            analysis = cov.analysis2(str(program))
            total = cov.report(file=output, show_missing=True)
            assert any(left < 0 or right < 0 for left, right in arcs)
            assert analysis[3]
            assert 0 < total < 100
            assert "program.py" in output.getvalue()
        finally:
            close_coverage(cov)


def test_i03_dynamic_contexts_survive_disk_and_line_projection():
    from coverage import CoverageData

    with sandbox() as root:
        red = str(root / "red.py")
        blue = str(root / "blue.py")
        target = root / ".coverage"
        data = CoverageData(basename=str(target))
        loaded = CoverageData(basename=str(target))
        try:
            data.set_context("phase/red")
            data.add_lines({red: {2, 4}})
            data.set_context("phase/blue")
            data.add_lines({blue: {4, 6}})
            data.write()
            data.close()
            loaded.read()
            assert loaded.measured_contexts() == {"phase/red", "phase/blue"}
            loaded.set_query_context("phase/red")
            assert loaded.measured_files() == {red}
            assert set(loaded.contexts_by_lineno(red)) == {2, 4}
            assert loaded.lines(blue) == []
            loaded.set_query_contexts(None)
            assert loaded.measured_files() == {red, blue}
        finally:
            close_data(data, loaded)


def test_i04_regex_context_union_and_reset_restore_unfiltered_view():
    from coverage import CoverageData

    with sandbox() as root:
        filename = str(root / "regex.py")
        data = CoverageData(no_disk=True)
        try:
            for context, line in (("task.red", 3), ("task.blue", 5), ("other", 8)):
                data.set_context(context)
                data.add_lines({filename: {line}})
            data.set_query_contexts([r"^task\."])
            assert set(data.lines(filename) or []) == {3, 5}
            assert set(data.contexts_by_lineno(filename)) == {3, 5}
            data.set_query_contexts(None)
            assert set(data.lines(filename) or []) == {3, 5, 8}
        finally:
            close_data(data)


def test_i05_literal_context_controls_files_lines_and_report_after_reload():
    from coverage import Coverage, CoverageData

    with sandbox() as root:
        literal = write_py(root / "literal.py", "value = 5\n")
        neighbor = write_py(root / "neighbor.py", "value = 9\n")
        target = root / ".coverage"
        data = CoverageData(basename=str(target))
        reloaded = CoverageData(basename=str(target))
        cov = Coverage(data_file=str(target), config_file=False)
        try:
            data.set_context("build[2].ok")
            data.add_lines({str(literal.resolve()): {1}})
            data.set_context("build2Xok")
            data.add_lines({str(neighbor.resolve()): {1}})
            data.write()
            data.close()
            reloaded.read()
            reloaded.set_query_context("build[2].ok")
            assert reloaded.measured_files() == {str(literal.resolve())}
            assert reloaded.lines(str(literal.resolve())) == [1]
            cov.load()
            cov.get_data().set_query_context("build[2].ok")
            output = io.StringIO()
            cov.report(file=output)
            text = output.getvalue()
            assert "literal.py" in text and "neighbor.py" not in text
        finally:
            close_data(data, reloaded)
            close_coverage(cov)


def test_i06_touch_tracer_serialization_and_reload_preserve_three_states():
    from coverage import CoverageData

    with sandbox() as root:
        (root / "aliases").mkdir()
        seed, plain, named, unknown = (str((root / name).resolve()) for name in ("seed.py", "plain.py", "named.src", "unknown.py"))
        named_alias = str(root / "aliases" / ".." / "named.src")
        target = root / ".coverage"
        data, loaded = CoverageData(basename=str(target)), CoverageData(basename=str(target))
        try:
            data.add_lines({seed: {1}})
            data.touch_file(plain)
            data.touch_file(named_alias, plugin_name="template-v2")
            data.write()
            data.close()
            loaded.read()
            assert loaded.file_tracer(named) == "template-v2"
            assert named_alias not in loaded.measured_files()
            assert loaded.file_tracer(plain) == ""
            assert loaded.file_tracer(unknown) is None
        finally:
            close_data(data, loaded)


def test_i07_purge_one_file_preserves_peer_across_reload():
    from coverage import CoverageData

    with sandbox() as root:
        (root / "aliases").mkdir()
        target_name, peer = str((root / "target.py").resolve()), str((root / "peer.py").resolve())
        target_alias = str(root / "aliases" / ".." / "target.py")
        target = root / ".coverage"
        data, loaded = CoverageData(basename=str(target)), CoverageData(basename=str(target))
        try:
            data.set_context("generation/v2")
            data.add_lines({target_name: {2, 3}, peer: {7}})
            data.add_file_tracers({target_name: "render-v2", peer: "peer-v2"})
            data.purge_files([target_alias])
            data.write()
            data.close()
            loaded.read()
            assert loaded.lines(target_name) == []
            assert loaded.contexts_by_lineno(target_name) == {}
            assert loaded.file_tracer(target_name) == "render-v2"
            assert loaded.lines(peer) == [7]
            assert loaded.file_tracer(peer) == "peer-v2"
        finally:
            close_data(data, loaded)


def test_i08_line_update_preserves_context_and_tracer_unions():
    from coverage import CoverageData

    with sandbox() as root:
        (root / "aliases").mkdir()
        shared = str((root / "shared.py").resolve())
        shared_alias = str(root / "aliases" / ".." / "shared.py")
        left, right = CoverageData(no_disk=True), CoverageData(no_disk=True)
        try:
            left.set_context("left/v2")
            left.add_lines({shared: {2}})
            left.add_file_tracers({shared: "plugin-v2"})
            right.set_context("right/v2")
            right.add_lines({shared_alias: {5}})
            right.add_file_tracers({shared_alias: "plugin-v2"})
            left.update(right)
            assert set(left.lines(shared) or []) == {2, 5}
            assert left.contexts_by_lineno(shared) == {2: ["left/v2"], 5: ["right/v2"]}
            assert left.file_tracer(shared) == "plugin-v2"
            assert left.measured_files() == {shared}
        finally:
            close_data(left, right)


def test_i09_mapped_tracer_conflict_is_rejected_without_partial_update():
    import pytest
    from coverage import CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        destination = CoverageData(no_disk=True)
        source = CoverageData(no_disk=True)
        collision = str(root / "collision.py")
        try:
            destination.add_lines({str(root / "existing.py"): {1}})
            source.add_lines({str(root / "left.src"): {3}, str(root / "right.src"): {5}})
            source.add_file_tracers({str(root / "left.src"): "left-v2", str(root / "right.src"): "right-v2"})
            before_destination = logical_snapshot(destination)
            before_source = logical_snapshot(source)
            with pytest.raises(DataError):
                destination.update(source, map_path=lambda _name: collision)
            assert logical_snapshot(destination) == before_destination
            assert logical_snapshot(source) == before_source
        finally:
            close_data(destination, source)


def test_i10_arc_update_preserves_contexts_and_entry_exit_structure():
    from coverage import CoverageData

    with sandbox() as root:
        name = str(root / "flow.py")
        left, right = CoverageData(no_disk=True), CoverageData(no_disk=True)
        try:
            left.set_context("left/arc")
            left.add_arcs({name: {(-1, 2), (2, -1)}})
            right.set_context("right/arc")
            right.add_arcs({name: {(2, 4), (4, -1)}})
            left.update(right)
            assert set(left.arcs(name) or []) == {(-1, 2), (2, -1), (2, 4), (4, -1)}
            contexts = left.contexts_by_lineno(name)
            assert "left/arc" in contexts[2] and "right/arc" in contexts[4]
        finally:
            close_data(left, right)


def test_i11_repeating_compatible_update_is_serially_idempotent():
    from coverage import CoverageData

    with sandbox() as root:
        name = str(root / "idempotent.py")
        left = CoverageData(basename=str(root / "left.coverage"))
        right = CoverageData(basename=str(root / "right.coverage"))
        try:
            left.add_lines({name: {2}})
            right.set_context("repeat/v2")
            right.add_lines({name: {4, 6}})
            left.update(right)
            first = logical_snapshot(left)
            left.update(right)
            assert logical_snapshot(left) == first
        finally:
            close_data(left, right)


def test_i12_disk_write_read_erase_preserves_caller_source_file():
    from coverage import CoverageData

    with sandbox() as root:
        source = write_py(root / "caller.py", "caller_value = 12\n")
        original = source.read_bytes()
        target = root / ".coverage"
        data, loaded = CoverageData(basename=str(target)), CoverageData(basename=str(target))
        try:
            data.add_lines({str(source.resolve()): {1}})
            data.write()
            data.close()
            loaded.read()
            assert loaded.lines(str(source.resolve())) == [1]
            loaded.erase()
            assert not target.exists()
            assert source.read_bytes() == original
        finally:
            close_data(data, loaded)


def test_i13_default_combine_consumes_shards_while_keep_retains_them():
    from coverage import Coverage, CoverageData

    with sandbox() as root:
        base = root / ".coverage"
        first_path, second_path = Path(str(base) + ".first"), Path(str(base) + ".second")
        first, second = CoverageData(basename=str(first_path)), CoverageData(basename=str(second_path))
        cov = Coverage(data_file=str(base), config_file=False)
        try:
            first.add_lines({str(root / "first.py"): {2}})
            second.add_lines({str(root / "second.py"): {5}})
            first.write(); second.write(); first.close(); second.close()
            cov.combine(data_paths=[str(root)], strict=True)
            assert not first_path.exists() and not second_path.exists()
            assert len(cov.get_data().measured_files()) == 2
            third_path = Path(str(base) + ".third")
            third = CoverageData(basename=str(third_path))
            third.add_lines({str(root / "third.py"): {8}}); third.write(); third.close()
            cov.combine(data_paths=[str(third_path)], strict=True, keep=True)
            assert third_path.exists()
        finally:
            close_data(first, second)
            close_coverage(cov)


def test_i14_late_mode_conflict_restores_destination_and_all_shards():
    import pytest
    from coverage import Coverage, CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        base = root / ".coverage"
        destination = Coverage(data_file=str(base), config_file=False)
        destination.get_data().add_lines({str(root / "base.py"): {1}})
        valid_path = Path(str(base) + ".a-valid")
        conflict_path = Path(str(base) + ".z-conflict")
        valid, conflict = CoverageData(basename=str(valid_path)), CoverageData(basename=str(conflict_path))
        try:
            valid.add_lines({str(root / "valid.py"): {3}})
            conflict.add_arcs({str(root / "branch.py"): {(-1, 4), (4, -1)}})
            valid.write(); conflict.write(); valid.close(); conflict.close()
            before_destination = logical_snapshot(destination.get_data())
            before_inputs = {valid_path: valid_path.read_bytes(), conflict_path: conflict_path.read_bytes()}
            with pytest.raises(DataError):
                destination.combine(data_paths=[str(root)], strict=True)
            assert logical_snapshot(destination.get_data()) == before_destination
            assert all(path.read_bytes() == content for path, content in before_inputs.items())
        finally:
            close_data(valid, conflict)
            close_coverage(destination)


def test_i15_late_tracer_conflict_restores_destination_and_all_shards():
    import pytest
    from coverage import Coverage, CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        base = root / ".coverage"
        shared = str(root / "shared.py")
        destination = Coverage(data_file=str(base), config_file=False)
        destination.get_data().add_lines({shared: {1}})
        destination.get_data().add_file_tracers({shared: "base-v2"})
        valid_path = Path(str(base) + ".a-valid")
        conflict_path = Path(str(base) + ".z-conflict")
        valid, conflict = CoverageData(basename=str(valid_path)), CoverageData(basename=str(conflict_path))
        try:
            valid.add_lines({str(root / "valid.py"): {2}})
            conflict.add_lines({shared: {5}})
            conflict.add_file_tracers({shared: "other-v2"})
            valid.write(); conflict.write(); valid.close(); conflict.close()
            before_destination = logical_snapshot(destination.get_data())
            before_inputs = {valid_path: valid_path.read_bytes(), conflict_path: conflict_path.read_bytes()}
            with pytest.raises(DataError):
                destination.combine(data_paths=[str(root)], strict=True)
            assert logical_snapshot(destination.get_data()) == before_destination
            assert all(path.read_bytes() == content for path, content in before_inputs.items())
        finally:
            close_data(valid, conflict)
            close_coverage(destination)


def test_i16_parallel_combine_is_independent_of_input_order():
    from coverage import Coverage, CoverageData

    with sandbox() as root:
        (root / "aliases").mkdir()
        shared = str((root / "shared.py").resolve())
        shared_alias = str(root / "aliases" / ".." / "shared.py")
        results = []
        for lane, reverse in (("left", False), ("right", True)):
            lane_root = root / lane
            lane_root.mkdir()
            base = lane_root / ".coverage"
            paths = [Path(str(base) + ".red"), Path(str(base) + ".blue")]
            for index, path in enumerate(paths):
                shard = CoverageData(basename=str(path))
                shard.set_context(f"ctx/{index}")
                shard.add_lines({shared if index == 0 else shared_alias: {index + 2}})
                shard.write(); shard.close()
            cov = Coverage(data_file=str(base), config_file=False)
            try:
                selected = list(reversed(paths)) if reverse else paths
                cov.combine(data_paths=[str(path) for path in selected], strict=True, keep=True)
                snap = logical_snapshot(cov.get_data())
                snap.pop("blob")
                assert snap["files"] == [shared]
                assert snap["payload"] == {shared: [2, 3]}
                results.append(snap)
            finally:
                close_coverage(cov)
        assert results[0] == results[1]


def test_i17_cli_run_and_python_load_share_measured_lines():
    from coverage import CoverageData

    with sandbox() as root:
        write_py(root / "cli_program.py", "first = 3\nsecond = first + 8\n")
        target = root / "cli.data"
        result = run_cli(root, "run", "cli_program.py", extra_env={"COVERAGE_FILE": str(target)})
        assert result.returncode == 0, result.stderr
        data = CoverageData(basename=str(target))
        try:
            data.read()
            name = measured_file(data, "cli_program.py")
            assert set(data.lines(name) or []) == {1, 2}
        finally:
            close_data(data)


def test_i18_cli_text_total_and_json_total_share_measurement():
    with sandbox() as root:
        write_py(root / "totals.py", "first = 1\nsecond = first + 2\n")
        target = root / "totals.data"
        env = {"COVERAGE_FILE": str(target)}
        assert run_cli(root, "run", "totals.py", extra_env=env).returncode == 0
        text = run_cli(root, "report", "--format=total", extra_env=env)
        output = root / "totals.json"
        structured = run_cli(root, "json", "-o", str(output), extra_env=env)
        assert text.returncode == 0 and structured.returncode == 0
        covered, statements, percent = json_total(output)
        assert covered == statements == 2
        assert float(text.stdout.strip()) == percent == 100.0
        before = target.read_bytes()
        run_cli(root, "report", "--format=total", extra_env=env)
        assert target.read_bytes() == before


def test_i19_failed_source_report_preserves_prior_target_and_data():
    import pytest
    from coverage.exceptions import NoSource

    with sandbox() as root:
        cov, program = collect_program(root, "value = 19\n")
        prior = root / "prior-report.json"
        prior.write_bytes(b'{"stable":"report-v2"}\n')
        before_data = cov.get_data().dumps()
        program.unlink()
        try:
            with pytest.raises(NoSource):
                cov.json_report(outfile=str(prior))
            assert prior.read_bytes() == b'{"stable":"report-v2"}\n'
            assert cov.get_data().dumps() == before_data
        finally:
            close_coverage(cov)


def test_i20_absolute_rcfile_is_consistent_when_used_from_its_directory():
    from coverage import CoverageData

    with sandbox() as root:
        project = root / "project"
        source_dir = project / "src"
        source_dir.mkdir(parents=True)
        write_py(source_dir / "main.py", "configured = 20\n")
        rcfile = project / "coverage.ini"
        rcfile.write_text("[run]\ndata_file = state/.coverage\nsource = src\n[json]\noutput = publish/result.json\n", encoding="utf-8")
        launcher = root / "launcher"
        launcher.mkdir()
        run = run_cli(launcher, "run", str((source_dir / "main.py").resolve()), extra_env={"COVERAGE_RCFILE": str(rcfile.resolve())})
        report = run_cli(launcher, "json", extra_env={"COVERAGE_RCFILE": str(rcfile.resolve())})
        assert run.returncode == 0 and report.returncode == 0
        data = CoverageData(basename=str(project / "state" / ".coverage"))
        try:
            data.read()
            measured = Path(measured_file(data, "src/main.py"))
            assert measured.name == "main.py" and measured.parent.name == "src"
            assert (project / "publish" / "result.json").is_file()
        finally:
            close_data(data)


def test_i21_discovered_rcfile_keeps_data_origin_after_cwd_change():
    from coverage import Coverage

    with sandbox() as root:
        project, elsewhere = root / "project", root / "elsewhere"
        project.mkdir(); elsewhere.mkdir()
        program = write_py(project / "module.py", "value = 21\n")
        (project / ".coveragerc").write_text("[run]\ndata_file = state/.coverage\n", encoding="utf-8")
        with working_directory(project):
            cov = Coverage(config_file=True)
        try:
            with working_directory(elsewhere):
                cov.start(); exec_source(program); cov.stop(); cov.save()
            assert (project / "state" / ".coverage").is_file()
            assert not (elsewhere / "state" / ".coverage").exists()
        finally:
            close_coverage(cov)


def test_i22_discovered_relative_source_include_and_omit_share_origin():
    from coverage import Coverage

    with sandbox() as root:
        project, run_dir, report_dir = root / "project", root / "run", root / "report"
        source_dir = project / "src"
        source_dir.mkdir(parents=True); run_dir.mkdir(); report_dir.mkdir()
        keep = write_py(source_dir / "keep.py", "kept = 22\n")
        omitted = write_py(source_dir / "omit_generated.py", "hidden = 22\n")
        (project / ".coveragerc").write_text(
            "[run]\nsource = src\nomit = src/omit_*.py\ndata_file = state/.coverage\n"
            "disable_warnings = module-not-imported,no-data-collected\n"
            "[report]\ninclude = src/*.py\nomit = src/omit_*.py\n",
            encoding="utf-8",
        )
        with working_directory(project):
            cov = Coverage(config_file=True)
        try:
            with working_directory(run_dir):
                cov.start(); exec_source(keep); exec_source(omitted); cov.stop(); cov.save()
            with working_directory(report_dir):
                output = io.StringIO(); cov.report(file=output)
            assert "keep.py" in output.getvalue()
            assert "omit_generated.py" not in output.getvalue()
        finally:
            close_coverage(cov)


def test_i23_environment_expansion_precedes_path_projection():
    from coverage import Coverage

    with sandbox() as root:
        project = root / "project"
        project.mkdir()
        rcfile = project / ".coveragerc"
        rcfile.write_text("[run]\ndata_file = $V2_STATE_DIR/.coverage\n", encoding="utf-8")
        prior = os.environ.get("V2_STATE_DIR")
        os.environ["V2_STATE_DIR"] = "expanded/state"
        cov = None
        try:
            with working_directory(project):
                cov = Coverage(config_file=True)
                cov.get_option("run:data_file")
                cov.get_data().add_lines({str(project / "synthetic.py"): {1}})
                cov.save()
                assert (project / "expanded" / "state" / ".coverage").is_file()
                assert Path(cov.get_data().base_filename()) == (project / "expanded" / "state" / ".coverage").resolve()
        finally:
            if cov is not None:
                close_coverage(cov)
            if prior is None:
                os.environ.pop("V2_STATE_DIR", None)
            else:
                os.environ["V2_STATE_DIR"] = prior


def test_i24_measurement_and_report_cwd_changes_do_not_rebase_rcfile_paths():
    from coverage import Coverage

    with sandbox() as root:
        project, measure_dir, report_dir = root / "project", root / "measure", root / "report"
        project.mkdir(); measure_dir.mkdir(); report_dir.mkdir()
        source_dir = project / "src"; source_dir.mkdir()
        program = write_py(source_dir / "workflow.py", "value = 24\n")
        (project / ".coveragerc").write_text(
            "[run]\ndata_file = artifacts/.coverage\nsource = src\n"
            "disable_warnings = module-not-imported,no-data-collected\n"
            "[json]\noutput = artifacts/report.json\n",
            encoding="utf-8",
        )
        with working_directory(project):
            cov = Coverage(config_file=True)
        try:
            with working_directory(measure_dir):
                cov.start(); exec_source(program); cov.stop(); cov.save()
            with working_directory(report_dir):
                cov.json_report()
            assert (project / "artifacts" / ".coverage").is_file()
            assert (project / "artifacts" / "report.json").is_file()
            assert not (measure_dir / "artifacts").exists()
            assert not (report_dir / "artifacts").exists()
        finally:
            close_coverage(cov)
