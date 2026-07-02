import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from coverage import Coverage, CoverageData
from coverage.exceptions import ConfigError, NoDataError, NoSource


def write_py(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def run_cli(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "coverage", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=run_env,
        timeout=30,
    )


def test_installable_surface_imports_version_and_module_cli(tmp_path):
    import coverage

    assert isinstance(coverage.__version__, str)
    assert hasattr(coverage, "Coverage")
    assert hasattr(coverage, "CoverageData")

    result = run_cli(tmp_path, "--version")

    assert result.returncode == 0
    assert "Coverage.py" in result.stdout


def test_cli_branch_context_json_and_total_report_agree(tmp_path):
    write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    print('yes')\n"
        "else:\n"
        "    print('no')\n",
    )

    run_result = run_cli(tmp_path, "run", "--branch", "--context=cli_ctx", "prog.py")
    assert run_result.returncode == 0
    assert run_result.stdout == "yes\n"

    json_result = run_cli(tmp_path, "json", "--show-contexts", "-o", "ctx.json")
    assert json_result.returncode == 0
    payload = json.loads((tmp_path / "ctx.json").read_text(encoding="utf-8"))
    file_payload = next(iter(payload["files"].values()))
    context_values = [ctx for contexts in file_payload["contexts"].values() for ctx in contexts]
    assert "cli_ctx" in context_values
    assert payload["totals"]["covered_lines"] == 3
    assert payload["totals"]["num_statements"] == 4
    assert payload["totals"]["covered_branches"] == 1
    assert payload["totals"]["missing_branches"] == 1

    total_result = run_cli(tmp_path, "report", "--format=total", "--precision=2")
    assert total_result.returncode == 0
    assert total_result.stdout.strip() == "66.67"


def test_cli_xml_report_exposes_branch_totals_and_missing_branch(tmp_path):
    write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    print('yes')\n"
        "else:\n"
        "    print('no')\n",
    )
    assert run_cli(tmp_path, "run", "--branch", "prog.py").returncode == 0

    xml_result = run_cli(tmp_path, "xml", "-o", "coverage.xml")
    assert xml_result.returncode == 0
    root = ET.parse(tmp_path / "coverage.xml").getroot()
    assert root.attrib["branches-valid"] == "2"
    assert root.attrib["branches-covered"] == "1"
    assert root.attrib["branch-rate"] == "0.5"
    branch_lines = [line.attrib for line in root.findall(".//line") if line.attrib.get("branch") == "true"]
    assert len(branch_lines) == 1
    assert branch_lines[0]["number"] == "2"
    assert branch_lines[0]["hits"] == "1"
    assert branch_lines[0]["condition-coverage"] == "50% (1/2)"
    assert branch_lines[0]["missing-branches"].isdigit()


def test_configured_data_file_is_shared_by_cli_and_coveragedata(tmp_path):
    write_py(tmp_path / "prog.py", "value = 7\nprint(value)\n")
    (tmp_path / ".coveragerc").write_text("[run]\ndata_file = envcov.dat\n", encoding="utf-8")

    run_result = run_cli(tmp_path, "run", "prog.py")
    assert run_result.returncode == 0
    data_file = tmp_path / "envcov.dat"
    assert data_file.exists()

    data = CoverageData(basename=str(data_file))
    data.read()
    assert {Path(name).name for name in data.measured_files()} == {"prog.py"}


def test_programmatic_branch_contexts_survive_serialization(tmp_path):
    program = write_py(
        tmp_path / "prog.py",
        "flag = False\n"
        "if flag:\n"
        "    value = 'yes'\n"
        "else:\n"
        "    value = 'no'\n",
    )
    cov = Coverage(data_file=str(tmp_path / ".coverage"), branch=True, source=[str(tmp_path)], context="api_ctx")
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    measured = next(name for name in data.measured_files() if name.endswith("prog.py"))
    assert data.has_arcs() is True
    assert data.arcs(measured)
    assert "api_ctx" in data.measured_contexts()

    blob = data.dumps()
    loaded = CoverageData(no_disk=True)
    loaded.loads(blob)
    loaded_measured = next(name for name in loaded.measured_files() if name.endswith("prog.py"))
    assert loaded.has_arcs() is True
    assert loaded.arcs(loaded_measured) == data.arcs(measured)


def test_coverage_collect_context_manager_records_lines(tmp_path):
    program = write_py(tmp_path / "prog.py", "a = 1\nb = 2\nc = a + b\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])

    with cov.collect():
        exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.save()

    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    measured = next(name for name in data.measured_files() if name.endswith("prog.py"))
    assert data.has_arcs() is False
    assert data.lines(measured) == [1, 2, 3]


def test_coverage_analysis_and_analysis2_report_missing_lines(tmp_path):
    program = write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    value = 1\n"
        "else:\n"
        "    value = 2\n",
    )
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    filename, statements, missing, missing_text = cov.analysis(str(program))
    analysis2 = cov.analysis2(str(program))

    assert Path(filename).name == "prog.py"
    assert statements == [1, 2, 3, 5]
    assert missing == [5]
    assert missing_text == "5"
    assert analysis2[3] == [5]


def test_exclude_and_clear_exclude_change_missing_line_analysis(tmp_path):
    program = write_py(
        tmp_path / "prog.py",
        "flag = True\n"
        "if flag:\n"
        "    value = 1\n"
        "else:  # pragma: skip-branch\n"
        "    value = 2\n",
    )
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.exclude("pragma: skip-branch")
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    excluded = cov.analysis2(str(program))
    cov.clear_exclude()

    assert excluded[2] == [4, 5]
    assert 5 not in excluded[3]
    assert "pragma: skip-branch" not in cov.get_exclude_list("exclude")


def test_switch_context_filters_coveragedata_queries(tmp_path):
    first = write_py(tmp_path / "first.py", "value = 1\n")
    second = write_py(tmp_path / "second.py", "value = 2\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)], context="static")
    cov.start()
    cov.switch_context("first")
    exec(compile(first.read_text(encoding="utf-8"), str(first), "exec"), {})
    cov.switch_context("second")
    exec(compile(second.read_text(encoding="utf-8"), str(second), "exec"), {})
    cov.stop()
    cov.save()

    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    first_file = next(name for name in data.measured_files() if name.endswith("first.py"))
    second_file = next(name for name in data.measured_files() if name.endswith("second.py"))
    data.set_query_contexts(["first"])
    assert data.lines(first_file) == [1]
    assert data.lines(second_file) == []


def test_include_omit_measurement_controls_measured_files(tmp_path):
    keep = write_py(tmp_path / "keep.py", "value = 'keep'\n")
    skip = write_py(tmp_path / "skip.py", "value = 'skip'\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), include=[str(keep)], omit=[str(skip)])
    cov.start()
    exec(compile(keep.read_text(encoding="utf-8"), str(keep), "exec"), {})
    exec(compile(skip.read_text(encoding="utf-8"), str(skip), "exec"), {})
    cov.stop()
    cov.save()

    measured = {Path(name).name for name in cov.get_data().measured_files()}
    assert measured == {"keep.py"}


def test_programmatic_json_xml_html_and_lcov_reports_share_total(tmp_path):
    program = write_py(tmp_path / "prog.py", "print('hello')\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()

    json_total = cov.json_report(outfile=str(tmp_path / "coverage.json"))
    xml_total = cov.xml_report(outfile=str(tmp_path / "coverage.xml"))
    html_total = cov.html_report(directory=str(tmp_path / "htmlcov"))
    lcov_total = cov.lcov_report(outfile=str(tmp_path / "coverage.lcov"))

    assert json_total == xml_total == html_total == lcov_total == 100.0
    assert (tmp_path / "coverage.json").exists()
    assert (tmp_path / "coverage.xml").exists()
    assert (tmp_path / "htmlcov" / "index.html").exists()
    assert (tmp_path / "coverage.lcov").exists()


def test_combine_keep_preserves_parallel_input_files(tmp_path):
    write_py(tmp_path / "one.py", "print('one')\n")
    write_py(tmp_path / "two.py", "print('two')\n")
    assert run_cli(tmp_path, "run", "--parallel-mode", "one.py").returncode == 0
    assert run_cli(tmp_path, "run", "--parallel-mode", "two.py").returncode == 0
    parallel_files = sorted(tmp_path.glob(".coverage.*"))

    combine = run_cli(tmp_path, "combine", "--keep")
    assert combine.returncode == 0
    data = CoverageData(basename=str(tmp_path / ".coverage"))
    data.read()
    measured = {Path(name).name for name in data.measured_files()}

    assert {path.name for path in parallel_files}.issubset({path.name for path in tmp_path.glob(".coverage.*")})
    assert measured == {"one.py", "two.py"}


def test_cli_erase_removes_coverage_file_and_report_has_no_data(tmp_path):
    write_py(tmp_path / "prog.py", "print('hello')\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0
    assert (tmp_path / ".coverage").exists()

    erase = run_cli(tmp_path, "erase")
    report = run_cli(tmp_path, "report")

    assert erase.returncode == 0
    assert not (tmp_path / ".coverage").exists()
    assert report.returncode != 0


def test_coverage_data_update_merges_line_data_objects(tmp_path):
    first = CoverageData(no_disk=True)
    second = CoverageData(no_disk=True)
    first.add_lines({str(tmp_path / "a.py"): {1, 2}})
    second.add_lines({str(tmp_path / "b.py"): {3}})

    first.update(second)

    measured = {Path(name).name for name in first.measured_files()}
    assert measured == {"a.py", "b.py"}
    assert first.lines(str(tmp_path / "b.py")) == [3]


def test_coverage_data_file_tracer_and_touch_file_roundtrip(tmp_path):
    data_file = tmp_path / ".coverage"
    source = tmp_path / "templated.txt"
    source.write_text("not python", encoding="utf-8")
    data = CoverageData(basename=str(data_file))
    data.add_lines({str(tmp_path / "seed.py"): {1}})
    data.touch_file(str(source), plugin_name="template-plugin")
    data.write()

    loaded = CoverageData(basename=str(data_file))
    loaded.read()

    assert loaded.lines(str(source)) == []
    assert loaded.file_tracer(str(source)) == "template-plugin"


def test_coverage_data_purge_files_removes_measured_file(tmp_path):
    data = CoverageData(no_disk=True)
    first = str(tmp_path / "first.py")
    second = str(tmp_path / "second.py")
    data.add_lines({first: {1}, second: {2}})

    data.purge_files([first])

    assert data.lines(first) == []
    assert data.lines(second) == [2]


def test_invalid_rcfile_reports_config_error_via_cli_and_api(tmp_path):
    bad = tmp_path / ".coveragerc"
    bad.write_text("[run\nbranch = true\n", encoding="utf-8")
    cli = run_cli(tmp_path, "debug", "config")

    def make_coverage():
        Coverage(config_file=str(bad))

    try:
        make_coverage()
    except ConfigError:
        api_error = True
    else:
        api_error = False

    assert cli.returncode != 0
    assert api_error is True


def test_report_without_data_raises_no_data_error(tmp_path):
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])

    try:
        cov.report()
    except NoDataError:
        raised = True
    else:
        raised = False

    assert raised is True


def test_missing_source_file_raises_no_source(tmp_path):
    program = write_py(tmp_path / "gone.py", "print('gone')\n")
    cov = Coverage(data_file=str(tmp_path / ".coverage"), source=[str(tmp_path)])
    cov.start()
    exec(compile(program.read_text(encoding="utf-8"), str(program), "exec"), {})
    cov.stop()
    cov.save()
    program.unlink()

    try:
        cov.report()
    except NoSource:
        raised = True
    else:
        raised = False

    assert raised is True


def test_cli_run_missing_script_fails_nonzero(tmp_path):
    result = run_cli(tmp_path, "run", "missing_script.py")

    assert result.returncode != 0


def test_cli_run_module_passes_program_arguments(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    write_py(package / "__init__.py", "")
    write_py(
        package / "__main__.py",
        "import sys\n"
        "from pathlib import Path\n"
        "Path('args.json').write_text(__import__('json').dumps(sys.argv[1:]), encoding='utf-8')\n",
    )

    result = run_cli(tmp_path, "run", "-m", "pkg", "left", "right", env={"PYTHONPATH": str(tmp_path)})

    assert result.returncode == 0
    assert json.loads((tmp_path / "args.json").read_text(encoding="utf-8")) == ["left", "right"]


def test_cli_debug_data_reports_measured_file(tmp_path):
    write_py(tmp_path / "prog.py", "print('hello')\n")
    assert run_cli(tmp_path, "run", "prog.py").returncode == 0

    debug = run_cli(tmp_path, "debug", "data")

    assert debug.returncode == 0
    assert "prog.py" in debug.stdout


def test_coverage_file_environment_is_used_by_report_command(tmp_path):
    write_py(tmp_path / "prog.py", "print('hello')\n")
    env = {"COVERAGE_FILE": str(tmp_path / "custom.dat")}
    assert run_cli(tmp_path, "run", "prog.py", env=env).returncode == 0

    report = run_cli(tmp_path, "report", "--format=total", env=env)

    assert report.returncode == 0
    assert report.stdout.strip() == "100"
