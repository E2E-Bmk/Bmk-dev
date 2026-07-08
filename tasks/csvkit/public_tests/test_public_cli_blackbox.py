"""Public black-box csvkit tests for the Stage 3 filter oracle.

Collection imports only the documented top-level csvkit module. Command tests
exercise installed script behavior through subprocesses and observable streams.
"""

from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import csvkit

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


def _mark(section: str, layer: str, notes: str):
    return pytest.mark.csvkit_filter(spec_section=section, layer=layer, notes=notes)


def _project_root() -> Path:
    package_file = Path(csvkit.__file__).resolve()
    for parent in package_file.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return package_file.parent.parent


def _entry_point(command: str) -> str:
    pyproject = _project_root() / "pyproject.toml"
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        scripts = data.get("project", {}).get("scripts", {})
        if command in scripts:
            return scripts[command]
    raise AssertionError(f"no script or entry point found for {command}")


def run_cmd(command: str, *args: str, input_text: str | None = None, cwd: Path | None = None):
    root = _project_root()
    script = root / command
    env = os.environ.copy()
    env["LC_ALL"] = env.get("LC_ALL") or "en_US.UTF-8"
    env["PYTHONIOENCODING"] = "utf-8"
    if script.exists():
        argv = [sys.executable, str(script), *args]
    else:
        entry = _entry_point(command)
        module, func = entry.split(":", 1)
        code = (
            "import sys\n"
            f"from {module} import {func} as _entry\n"
            "raise SystemExit(_entry())\n"
        )
        argv = [sys.executable, "-c", code, *args]
    return subprocess.run(
        argv,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd or root),
        env=env,
        check=False,
    )


def ok(command: str, *args: str, input_text: str | None = None, cwd: Path | None = None) -> str:
    proc = run_cmd(command, *args, input_text=input_text, cwd=cwd)
    assert proc.returncode == 0, (command, args, proc.stdout, proc.stderr)
    return proc.stdout


def rows(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


def dict_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


@_mark("## Public API", "atomic", "top-level reader and writer aliases read and write CSV rows")
def test_top_level_reader_writer_aliases_roundtrip():
    buffer = io.StringIO()
    writer = csvkit.writer(buffer)
    writer.writerow(["name", "count"])
    writer.writerow(["alpha", "2"])

    parsed = list(csvkit.reader(io.StringIO(buffer.getvalue())))

    assert parsed == [["name", "count"], ["alpha", "2"]]


@_mark("## Public API", "atomic", "top-level DictReader and DictWriter aliases preserve field names")
def test_top_level_dict_reader_writer_aliases_roundtrip():
    buffer = io.StringIO()
    writer = csvkit.DictWriter(buffer, fieldnames=["name", "count"])
    writer.writeheader()
    writer.writerow({"name": "alpha", "count": "2"})

    parsed = list(csvkit.DictReader(io.StringIO(buffer.getvalue())))

    assert parsed == [{"name": "alpha", "count": "2"}]


@_mark("## Installable Surface", "atomic", "commands expose a successful version flag")
def test_command_version_flag_reports_command_name(tmp_path):
    stdout = ok("csvcut", "--version", cwd=tmp_path)

    assert "csvcut" in stdout
    assert stdout.strip()


@_mark("### `csvcut`", "atomic", "csvcut selects named columns in requested order")
def test_csvcut_selects_named_columns_in_requested_order(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,qty\n1,apple,2\n2,pear,5\n")

    stdout = ok("csvcut", "-c", "name,id", str(data), cwd=tmp_path)

    assert rows(stdout) == [["name", "id"], ["apple", "1"], ["pear", "2"]]


@_mark("### Column Identification", "atomic", "csvcut excludes known columns and ignores unknown excluded names")
def test_csvcut_not_columns_ignores_unknown_exclusions(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,qty\n1,apple,2\n")

    stdout = ok("csvcut", "-C", "missing,qty", str(data), cwd=tmp_path)

    assert rows(stdout) == [["id", "name"], ["1", "apple"]]


@_mark("### Column Identification", "atomic", "csvcut --names lists active column names and positions")
def test_csvcut_names_lists_positions(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,qty\n1,apple,2\n")

    stdout = ok("csvcut", "--names", str(data), cwd=tmp_path)

    parsed = []
    for row in rows(stdout):
        assert len(row) == 1
        position, name = row[0].split(":", 1)
        parsed.append((int(position.strip()), name.strip()))
    assert parsed == [(1, "id"), (2, "name"), (3, "qty")]


@_mark("### Common CSV Input Behavior", "atomic", "headerless input receives generated headers before projection")
def test_csvcut_no_header_row_uses_generated_headers(tmp_path):
    data = write_text(tmp_path / "items.csv", "1,apple,2\n2,pear,5\n")

    stdout = ok("csvcut", "--no-header-row", "-c", "b,a", str(data), cwd=tmp_path)

    assert rows(stdout) == [["b", "a"], ["apple", "1"], ["pear", "2"]]


@_mark("### Common CSV Input Behavior", "atomic", "linenumbers adds a leading output column")
def test_csvcut_linenumbers_adds_ordinary_column(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n2,pear\n")

    stdout = ok("csvcut", "--linenumbers", str(data), cwd=tmp_path)

    assert rows(stdout) == [["line_number", "id", "name"], ["1", "1", "apple"], ["2", "2", "pear"]]


@_mark("### `csvgrep`", "atomic", "csvgrep exact matching filters rows by selected column")
def test_csvgrep_exact_match_filters_selected_column(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,color\n1,apple,red\n2,pear,green\n")

    stdout = ok("csvgrep", "-c", "color", "-m", "red", str(data), cwd=tmp_path)

    assert dict_rows(stdout) == [{"id": "1", "name": "apple", "color": "red"}]


@_mark("### `csvgrep`", "atomic", "csvgrep regex matching filters rows by selected column")
def test_csvgrep_regex_filters_selected_column(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n2,pear\n3,plum\n")

    stdout = ok("csvgrep", "-c", "name", "-r", "^p", str(data), cwd=tmp_path)

    assert [row["name"] for row in dict_rows(stdout)] == ["pear", "plum"]


@_mark("### `csvgrep`", "atomic", "any-match keeps rows where any selected column matches")
def test_csvgrep_any_match_checks_any_selected_column(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,color\n1,apple,red\n2,pear,green\n")

    stdout = ok("csvgrep", "-c", "name,color", "-m", "red", "--any-match", str(data), cwd=tmp_path)

    assert [row["id"] for row in dict_rows(stdout)] == ["1"]


@_mark("### `csvgrep`", "atomic", "invert-match keeps nonmatching rows")
def test_csvgrep_invert_match_keeps_nonmatching_rows(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,color\n1,apple,red\n2,pear,green\n")

    stdout = ok("csvgrep", "-c", "color", "-m", "red", "--invert-match", str(data), cwd=tmp_path)

    assert dict_rows(stdout) == [{"id": "2", "name": "pear", "color": "green"}]


@_mark("### `csvsort`", "atomic", "csvsort sorts by parsed values in selected columns")
def test_csvsort_sorts_numeric_column(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\npear,10\napple,2\nplum,1\n")

    stdout = ok("csvsort", "-c", "qty", str(data), cwd=tmp_path)

    assert [row["name"] for row in dict_rows(stdout)] == ["plum", "apple", "pear"]


@_mark("### `csvsort`", "atomic", "reverse sorts in descending order")
def test_csvsort_reverse_descending(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\npear,10\napple,2\n")

    stdout = ok("csvsort", "-c", "qty", "--reverse", str(data), cwd=tmp_path)

    assert [row["qty"] for row in dict_rows(stdout)] == ["10", "2"]


@_mark("### `csvsort`", "atomic", "ignore-case performs case-insensitive text sorting")
def test_csvsort_ignore_case_for_text(tmp_path):
    data = write_text(tmp_path / "items.csv", "name\nbanana\nApple\ncherry\n")

    stdout = ok("csvsort", "-c", "name", "--ignore-case", str(data), cwd=tmp_path)

    assert [row["name"] for row in dict_rows(stdout)] == ["Apple", "banana", "cherry"]


@_mark("### `csvjoin`", "integration", "default key join is an inner join")
def test_csvjoin_inner_join_on_named_key(tmp_path):
    left = write_text(tmp_path / "left.csv", "id,name\n1,apple\n2,pear\n")
    right = write_text(tmp_path / "right.csv", "id,color\n1,red\n3,purple\n")

    stdout = ok("csvjoin", "-c", "id", str(left), str(right), cwd=tmp_path)

    assert dict_rows(stdout) == [{"id": "1", "name": "apple", "color": "red"}]


@_mark("### `csvjoin`", "integration", "left join preserves left rows")
def test_csvjoin_left_join_preserves_left_rows(tmp_path):
    left = write_text(tmp_path / "left.csv", "id,name\n1,apple\n2,pear\n")
    right = write_text(tmp_path / "right.csv", "id,color\n1,red\n")

    stdout = ok("csvjoin", "-c", "id", "--left", str(left), str(right), cwd=tmp_path)

    assert rows(stdout) == [["id", "name", "color"], ["1", "apple", "red"], ["2", "pear", ""]]


@_mark("### `csvjoin`", "integration", "without columns csvjoin joins files sequentially by row position")
def test_csvjoin_without_columns_joins_by_row_position(tmp_path):
    left = write_text(tmp_path / "left.csv", "id,name\n1,apple\n2,pear\n")
    right = write_text(tmp_path / "right.csv", "color\nred\ngreen\n")

    stdout = ok("csvjoin", str(left), str(right), cwd=tmp_path)

    assert rows(stdout) == [["id", "name", "color"], ["1", "apple", "red"], ["2", "pear", "green"]]


@_mark("### `csvstack`", "integration", "csvstack concatenates rows under one header")
def test_csvstack_concatenates_rows(tmp_path):
    first = write_text(tmp_path / "first.csv", "id,name\n1,apple\n")
    second = write_text(tmp_path / "second.csv", "id,name\n2,pear\n")

    stdout = ok("csvstack", str(first), str(second), cwd=tmp_path)

    assert rows(stdout) == [["id", "name"], ["1", "apple"], ["2", "pear"]]


@_mark("### `csvstack`", "integration", "groups adds grouping values in a named column")
def test_csvstack_groups_adds_grouping_column(tmp_path):
    first = write_text(tmp_path / "first.csv", "id,name\n1,apple\n")
    second = write_text(tmp_path / "second.csv", "id,name\n2,pear\n")

    stdout = ok("csvstack", "--groups", "A,B", "--group-name", "source", str(first), str(second), cwd=tmp_path)

    assert rows(stdout) == [["source", "id", "name"], ["A", "1", "apple"], ["B", "2", "pear"]]


@_mark("### `csvstack`", "integration", "filenames uses input filenames as grouping values")
def test_csvstack_filenames_adds_filename_grouping(tmp_path):
    first = write_text(tmp_path / "first.csv", "id,name\n1,apple\n")
    second = write_text(tmp_path / "second.csv", "id,name\n2,pear\n")

    stdout = ok("csvstack", "--filenames", str(first), str(second), cwd=tmp_path)

    parsed = rows(stdout)
    assert parsed[0] == ["group", "id", "name"]
    assert {Path(row[0]).name for row in parsed[1:]} == {"first.csv", "second.csv"}


@_mark("### `csvformat`", "atomic", "out-delimiter sets the output delimiter")
def test_csvformat_changes_output_delimiter(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n")

    stdout = ok("csvformat", "-D", "|", str(data), cwd=tmp_path)

    assert stdout == "id|name\n1|apple\n"


@_mark("### `csvformat`", "atomic", "skip-header omits the header row")
def test_csvformat_skip_header_omits_header(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n")

    stdout = ok("csvformat", "--skip-header", str(data), cwd=tmp_path)

    assert rows(stdout) == [["1", "apple"]]


@_mark("### `csvformat`", "atomic", "out-tabs writes tab-delimited output")
def test_csvformat_out_tabs_writes_tab_delimited_output(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n")

    stdout = ok("csvformat", "-T", str(data), cwd=tmp_path)

    assert stdout == "id\tname\n1\tapple\n"


@_mark("### `csvjson`", "atomic", "csvjson writes an array of objects")
def test_csvjson_writes_array_of_objects(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n2,pear\n")

    stdout = ok("csvjson", str(data), cwd=tmp_path)

    assert json.loads(stdout) == [{"id": 1, "name": "apple"}, {"id": 2, "name": "pear"}]


@_mark("### `csvjson`", "atomic", "stream writes newline-separated JSON objects")
def test_csvjson_stream_writes_newline_json_objects(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n2,pear\n")

    stdout = ok("csvjson", "--stream", str(data), cwd=tmp_path)

    assert [json.loads(line) for line in stdout.splitlines()] == [
        {"id": 1, "name": "apple"},
        {"id": 2, "name": "pear"},
    ]


@_mark("### `csvjson`", "atomic", "key writes an object keyed by the selected column")
def test_csvjson_key_writes_object_keyed_by_column(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n2,pear\n")

    stdout = ok("csvjson", "--key", "id", str(data), cwd=tmp_path)

    assert json.loads(stdout) == {"1": {"id": 1, "name": "apple"}, "2": {"id": 2, "name": "pear"}}


@_mark("### `csvjson`", "atomic", "lat and lon output GeoJSON point features")
def test_csvjson_lat_lon_outputs_geojson(tmp_path):
    data = write_text(tmp_path / "places.csv", "id,lat,lon\nA,10.5,20.25\n")

    stdout = ok("csvjson", "--lat", "lat", "--lon", "lon", "--key", "id", str(data), cwd=tmp_path)
    payload = json.loads(stdout)

    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["id"] == "A"
    assert payload["features"][0]["geometry"] == {"type": "Point", "coordinates": [20.25, 10.5]}


@_mark("### `csvlook`", "atomic", "csvlook renders a Markdown-compatible table")
def test_csvlook_renders_markdown_table_with_values(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name\n1,apple\n")

    stdout = ok("csvlook", str(data), cwd=tmp_path)

    assert "id" in stdout
    assert "| name " in stdout
    assert "apple" in stdout


@_mark("### `csvstat`", "atomic", "csvstat --json writes structured statistics")
def test_csvstat_json_reports_structured_statistics(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\napple,2\npear,5\napple,3\n")

    stdout = ok("csvstat", "--json", str(data), cwd=tmp_path)
    stats = json.loads(stdout)

    by_name = {item["column_name"]: item for item in stats}
    assert by_name["name"]["unique"] == 2
    assert by_name["qty"]["max"] == 5


@_mark("### `csvstat`", "atomic", "csvstat --csv restricts statistics to selected columns")
def test_csvstat_csv_selected_column_outputs_csv_statistics(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\napple,2\npear,5\n")

    stdout = ok("csvstat", "--csv", "-c", "qty", str(data), cwd=tmp_path)

    parsed = list(csv.DictReader(io.StringIO(stdout)))
    assert [row["column_name"] for row in parsed] == ["qty"]


@_mark("### `csvstat`", "atomic", "a single count statistic for one column writes only the value")
def test_csvstat_count_single_column_writes_only_value(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\napple,2\npear,5\n")

    stdout = ok("csvstat", "--count", "-c", "name", str(data), cwd=tmp_path)

    assert stdout.strip() == "2"


@_mark("### `csvsql`", "atomic", "csvsql without a database writes CREATE TABLE statements")
def test_csvsql_generates_create_table_statement(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\napple,2\n")

    stdout = ok("csvsql", "--tables", "items", str(data), cwd=tmp_path)
    lowered = stdout.lower()

    assert "create table" in lowered
    assert ("create table items" in lowered) or ('create table "items"' in lowered)
    assert "name" in lowered
    assert "qty" in lowered


@_mark("### `csvsql`", "integration", "csvsql query mode loads CSV input and returns rows as CSV")
def test_csvsql_query_mode_filters_loaded_csv(tmp_path):
    data = write_text(tmp_path / "items.csv", "name,qty\napple,2\npear,5\n")

    stdout = ok("csvsql", "--query", "select name from items where qty > 2", str(data), cwd=tmp_path)

    assert rows(stdout) == [["name"], ["pear"]]


@_mark("### `sql2csv`", "atomic", "sql2csv executes query text against the default SQLite connection")
def test_sql2csv_query_text_returns_csv_rows(tmp_path):
    stdout = ok("sql2csv", "--query", "select 1 as id, 'apple' as name", cwd=tmp_path)

    assert rows(stdout) == [["id", "name"], ["1", "apple"]]


@_mark("### `sql2csv`", "atomic", "sql2csv reads SQL from an input file when query is omitted")
def test_sql2csv_reads_query_from_file(tmp_path):
    query = write_text(tmp_path / "query.sql", "select 2 as id, 'pear' as name")

    stdout = ok("sql2csv", str(query), cwd=tmp_path)

    assert rows(stdout) == [["id", "name"], ["2", "pear"]]


@_mark("### `csvclean`", "atomic", "header-normalize-space normalizes header whitespace")
def test_csvclean_header_normalize_space(tmp_path):
    data = write_text(tmp_path / "messy.csv", " item   name , qty \napple,2\n")

    stdout = ok("csvclean", "--header-normalize-space", str(data), cwd=tmp_path)

    assert rows(stdout) == [["item name", "qty"], ["apple", "2"]]


@_mark("### `csvclean`", "atomic", "remove-empty-columns drops columns that contain no values")
def test_csvclean_remove_empty_columns(tmp_path):
    data = write_text(tmp_path / "messy.csv", "name,empty,qty\napple,,2\npear,,5\n")

    stdout = ok("csvclean", "--remove-empty-columns", str(data), cwd=tmp_path)

    assert rows(stdout) == [["name", "qty"], ["apple", "2"], ["pear", "5"]]


@_mark("### `csvclean`", "atomic", "length-mismatch reports errors on stderr and exits nonzero")
def test_csvclean_length_mismatch_reports_structured_stderr(tmp_path):
    data = write_text(tmp_path / "bad.csv", "name,qty\napple,2,extra\npear,5\n")

    proc = run_cmd("csvclean", "--length-mismatch", str(data), cwd=tmp_path)

    assert proc.returncode == 1
    assert rows(proc.stdout) == [["name", "qty"], ["apple", "2", "extra"], ["pear", "5"]]
    err_rows = rows(proc.stderr)
    assert err_rows[0][:2] == ["line_number", "msg"]
    assert err_rows[1][0] == "1"


@_mark("### `in2csv`", "atomic", "JSON array input converts to CSV")
def test_in2csv_converts_json_array_to_csv(tmp_path):
    data = write_text(tmp_path / "items.json", '[{"id": 1, "name": "apple"}, {"id": 2, "name": "pear"}]')

    stdout = ok("in2csv", "--format", "json", str(data), cwd=tmp_path)

    assert rows(stdout) == [["id", "name"], ["1", "apple"], ["2", "pear"]]


@_mark("### `in2csv`", "atomic", "newline-delimited JSON converts one object per line")
def test_in2csv_converts_ndjson_to_csv(tmp_path):
    data = write_text(tmp_path / "items.ndjson", '{"id": 1, "name": "apple"}\n{"id": 2, "name": "pear"}\n')

    stdout = ok("in2csv", "--format", "ndjson", str(data), cwd=tmp_path)

    assert rows(stdout) == [["id", "name"], ["1", "apple"], ["2", "pear"]]


@_mark("### `in2csv`", "atomic", "nested JSON object keys flatten into slash-separated column paths")
def test_in2csv_flattens_nested_json_keys(tmp_path):
    data = write_text(tmp_path / "items.json", '[{"id": 10, "item": {"name": "apple", "qty": 2}}]')

    stdout = ok("in2csv", "--format", "json", str(data), cwd=tmp_path)

    assert rows(stdout) == [["id", "item/name", "item/qty"], ["10", "apple", "2"]]


@_mark("### `in2csv`", "atomic", "fixed-width input uses the public schema option")
def test_in2csv_converts_fixed_width_with_schema(tmp_path):
    data = write_text(tmp_path / "items.txt", "01apple02\n02pear 05\n")
    schema = write_text(tmp_path / "schema.csv", "column,start,length\nid,1,2\nname,3,5\nqty,8,2\n")

    stdout = ok("in2csv", "--format", "fixed", "--schema", str(schema), str(data), cwd=tmp_path)

    assert rows(stdout) == [["id", "name", "qty"], ["01", "apple", "02"], ["02", "pear", "05"]]


@_mark("## Cross-View Invariants", "system_e2e", "CSV output from one command can feed another command and then JSON conversion")
def test_pipeline_cut_grep_then_json_preserves_filtered_table(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,color,qty\n1,apple,red,2\n2,pear,green,5\n3,plum,red,4\n")

    cut = run_cmd("csvcut", "-c", "name,color,qty", str(data), cwd=tmp_path)
    assert cut.returncode == 0
    grep = run_cmd("csvgrep", "-c", "color", "-m", "red", input_text=cut.stdout, cwd=tmp_path)
    assert grep.returncode == 0
    as_json = run_cmd("csvjson", input_text=grep.stdout, cwd=tmp_path)
    assert as_json.returncode == 0

    assert json.loads(as_json.stdout) == [
        {"name": "apple", "color": "red", "qty": 2},
        {"name": "plum", "color": "red", "qty": 4},
    ]


@_mark("## Representative Workflows", "system_e2e", "csvsql inserts CSV into SQLite and sql2csv queries the same database")
def test_csvsql_insert_then_sql2csv_query_roundtrip(tmp_path):
    data = write_text(tmp_path / "items.csv", "id,name,qty\n1,apple,2\n2,pear,5\n")
    db = tmp_path / "items.db"
    db_url = f"sqlite:///{db}"

    insert = run_cmd("csvsql", "--db", db_url, "--tables", "items", "--insert", str(data), cwd=tmp_path)
    assert insert.returncode == 0, (insert.stdout, insert.stderr)
    stdout = ok("sql2csv", "--db", db_url, "--query", "select name from items where qty >= 5", cwd=tmp_path)

    assert rows(stdout) == [["name"], ["pear"]]
