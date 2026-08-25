from __future__ import annotations

import io
from pathlib import Path

from tests.system_support import (
    close_coverage,
    close_data,
    directory_snapshot,
    exec_source,
    sandbox,
    trace_identity,
    write_py,
)


def test_s01_late_shard_conflict_restores_complete_combine_transaction():
    import pytest
    from coverage import Coverage, CoverageData
    from coverage.exceptions import DataError

    with sandbox() as root:
        base = root / ".coverage"
        destination = Coverage(data_file=str(base), config_file=False)
        destination.get_data().set_context("base")
        destination.get_data().add_lines({str(root / "base.py"): {1}})
        destination.get_data().add_file_tracers({str(root / "base.py"): "base-tracer"})
        shard_paths = [
            Path(str(base) + ".a-first"),
            Path(str(base) + ".b-second"),
            Path(str(base) + ".z-conflict"),
        ]
        shards = [CoverageData(basename=str(path)) for path in shard_paths]
        try:
            for index, shard in enumerate(shards[:2], start=1):
                filename = str(root / f"valid{index}.py")
                shard.set_context(f"lane/{index}")
                shard.add_lines({filename: {index + 2}})
                shard.add_file_tracers({filename: f"tracer-{index}"})
            shards[2].set_context("lane/conflict")
            shards[2].add_arcs({str(root / "branch.py"): {(-1, 4), (4, -1)}})
            for shard in shards:
                shard.write()
                shard.close()

            destination_before = destination.get_data().dumps()
            files_before = {path: path.read_bytes() for path in shard_paths}
            with pytest.raises(DataError):
                destination.combine(data_paths=[str(root)], strict=True)

            assert destination.get_data().dumps() == destination_before
            assert {path: path.read_bytes() for path in shard_paths} == files_before
        finally:
            close_data(*shards)
            close_coverage(destination)


def test_s02_successful_shards_have_one_context_file_and_report_projection():
    import json
    from coverage import Coverage, CoverageData

    with sandbox() as root:
        base = root / ".coverage"
        (root / "aliases").mkdir()
        programs = [
            write_py(root / "first.py", "first = 2\nsecond = first + 3\n"),
            write_py(root / "second.py", "alpha = 5\nbeta = alpha + 7\n"),
        ]
        shard_paths = [Path(str(base) + ".red"), Path(str(base) + ".blue")]
        shards = [CoverageData(basename=str(path)) for path in shard_paths]
        cov = Coverage(data_file=str(base), source=[str(root)], config_file=False)
        try:
            for index, (shard, program) in enumerate(zip(shards, programs)):
                alias = str(root / "aliases" / ".." / program.name)
                shard.set_context(f"phase/{index}")
                shard.add_lines({alias: {1, 2}})
                shard.touch_file(alias)
                shard.write()
                shard.close()
            cov.combine(data_paths=[str(root)], strict=True)
            output = root / "combined.json"
            total = cov.json_report(outfile=str(output), show_contexts=True)
            payload = json.loads(output.read_text(encoding="utf-8"))

            data = cov.get_data()
            assert data.measured_contexts() == {"phase/0", "phase/1"}
            assert data.measured_files() == {str(program.resolve()) for program in programs}
            assert {Path(name).name for name in payload["files"]} == {"first.py", "second.py"}
            assert payload["totals"]["covered_lines"] == 4
            assert payload["totals"]["num_statements"] == 4
            assert total == 100.0
        finally:
            close_data(*shards)
            close_coverage(cov)


def test_s03_erase_then_fresh_run_has_no_prior_generation_metadata_or_totals():
    from coverage import Coverage

    with sandbox() as root:
        old_file = str(root / "old.py")
        fresh = write_py(root / "fresh.py", "fresh = 3\nresult = fresh * 2\n")
        cov = Coverage(data_file=str(root / ".coverage"), source=[str(root)], config_file=False, timid=True)
        try:
            old_data = cov.get_data()
            old_data.set_context("obsolete/generation")
            old_data.add_lines({old_file: {1, 7}})
            old_data.add_file_tracers({old_file: "obsolete-tracer"})
            cov.save()
            cov.erase()

            with cov.collect():
                exec_source(fresh)
            cov.save()
            output = io.StringIO()
            total = cov.report(file=output)
            data = cov.get_data()
            assert data.measured_contexts() == {""}
            assert {Path(name).name for name in data.measured_files()} == {"fresh.py"}
            assert data.file_tracer(old_file) is None
            assert "old.py" not in output.getvalue()
            assert "fresh.py" in output.getvalue()
            assert total == 100.0
        finally:
            close_coverage(cov)


def test_s04_nested_same_owner_body_failure_unwinds_to_outer_then_baseline():
    from coverage import Coverage

    with sandbox() as root:
        initial_trace = trace_identity()
        program = write_py(root / "ownership.py", "owned = 4\n")
        cov = Coverage(data_file=str(root / ".coverage"), config_file=False, timid=True)
        try:
            with cov.collect():
                assert Coverage.current() is cov
                exec_source(program)
                try:
                    with cov.collect():
                        assert Coverage.current() is cov
                        raise RuntimeError("inner-body-v2")
                except RuntimeError as exc:
                    assert str(exc) == "inner-body-v2"
                assert Coverage.current() is cov
                assert trace_identity() is not initial_trace
            assert Coverage.current() is None
            assert trace_identity() is initial_trace
        finally:
            close_coverage(cov)


def test_s05_failed_nested_generation_allows_clean_later_collection():
    from coverage import Coverage

    with sandbox() as root:
        initial_trace = trace_identity()
        fresh_source = root / "freshsrc"
        fresh_source.mkdir()
        failed = Coverage(data_file=str(root / "failed.coverage"), config_file=False, timid=True)
        fresh = Coverage(data_file=str(root / "fresh.coverage"), source=[str(fresh_source)], config_file=False, timid=True)
        warmup = write_py(root / "failed_generation.py", "started = 5\n")
        program = write_py(fresh_source / "recovery.py", "recovered = 5\nready = recovered + 1\n")
        try:
            try:
                with failed.collect():
                    exec_source(warmup)
                    with failed.collect():
                        raise ValueError("failed-generation-v2")
            except ValueError as exc:
                assert str(exc) == "failed-generation-v2"

            with fresh.collect():
                exec_source(program)
            fresh.save()
            output = io.StringIO()
            assert fresh.report(file=output) == 100.0
            assert "recovery.py" in output.getvalue()
            assert Coverage.current() is None
            assert trace_identity() is initial_trace
        finally:
            close_coverage(fresh)
            close_coverage(failed)


def test_s06_cross_directory_project_uses_one_rcfile_origin_for_all_artifacts():
    import json
    import os
    from coverage import Coverage, CoverageData

    with sandbox() as root:
        project, launch, publish = root / "project", root / "launch", root / "publish"
        source = project / "src"
        source.mkdir(parents=True)
        launch.mkdir()
        publish.mkdir()
        main = write_py(source / "main.py", "configured = 6\nreported = configured + 1\n")
        rcfile = project / ".coveragerc"
        rcfile.write_text(
            "[run]\nsource = src\ndata_file = artifacts/.coverage\n"
            "disable_warnings = module-not-imported,no-data-collected\n"
            "[report]\ninclude = src/*.py\n"
            "[json]\noutput = artifacts/json/coverage.json\n",
            encoding="utf-8",
        )
        previous = Path.cwd()
        cov = None
        data = None
        try:
            os.chdir(project)
            cov = Coverage(config_file=True)
            os.chdir(launch)
            with cov.collect():
                exec_source(main)
            cov.save()
            os.chdir(publish)
            assert cov.json_report() == 100.0

            data = CoverageData(basename=str(project / "artifacts" / ".coverage"))
            data.read()
            payload_path = project / "artifacts" / "json" / "coverage.json"
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            assert {Path(name).name for name in data.measured_files()} == {"main.py"}
            assert {Path(name).name for name in payload["files"]} == {"main.py"}
            assert payload["totals"]["covered_lines"] == 2
            assert not (launch / "artifacts").exists()
            assert not (publish / "artifacts").exists()
        finally:
            os.chdir(previous)
            close_data(data)
            if cov is not None:
                close_coverage(cov)


def test_s07_late_structured_report_failure_preserves_existing_destination():
    import pytest
    from coverage import Coverage
    from coverage.exceptions import NoSource

    with sandbox() as root:
        present = write_py(root / "a_present.py", "present = 7\n")
        missing = write_py(root / "z_missing.py", "missing = 8\n")
        destination = root / "report.json"
        destination.write_bytes(b'{"stable":"generation-v2"}\n')
        cov = Coverage(data_file=None, source=[str(root)], config_file=False)
        try:
            data = cov.get_data()
            data.add_lines({str(present.resolve()): {1}, str(missing.resolve()): {1}})
            before_data = data.dumps()
            before_destination = destination.read_bytes()
            missing.unlink()
            with pytest.raises(NoSource):
                cov.json_report(outfile=str(destination))
            assert destination.read_bytes() == before_destination
            assert data.dumps() == before_data
            assert not list(root.glob(".report.json.*"))
            assert Coverage.current() is None
        finally:
            close_coverage(cov)


def test_s08_successful_html_report_replaces_complete_destination_generation():
    from coverage import Coverage

    with sandbox() as root:
        first = write_py(root / "first.py", "first = 8\n")
        second = write_py(root / "second.py", "second = 9\n")
        destination = root / "htmlcov"
        destination.mkdir()
        write_py(destination / "stale-only.html", "stale-generation-v2")
        write_py(destination / "nested" / "sentinel.txt", "must-be-replaced")
        cov = Coverage(data_file=None, source=[str(root)], config_file=False)
        try:
            data = cov.get_data()
            data.add_lines({str(first.resolve()): {1}, str(second.resolve()): {1}})
            before_data = data.dumps()
            assert cov.html_report(directory=str(destination)) == 100.0
            snapshot = directory_snapshot(destination)
            assert "index.html" in snapshot
            assert "stale-only.html" not in snapshot
            assert "nested/sentinel.txt" not in snapshot
            rendered_pages = [name for name in snapshot if name.endswith(".html") and name != "index.html"]
            assert len(rendered_pages) >= 2
            assert all(snapshot[name] for name in rendered_pages)
            assert data.dumps() == before_data
            assert not list(root.glob(".htmlcov.*"))
        finally:
            close_coverage(cov)
