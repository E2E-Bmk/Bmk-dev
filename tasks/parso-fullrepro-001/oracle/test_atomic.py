from pathlib import Path

import pytest

import parso
from parso import ParserSyntaxError, load_grammar, parse
from parso.file_io import FileIO, KnownContentFileIO
from parso.utils import python_bytes_to_unicode, split_lines


@pytest.mark.parametrize(
    "code",
    [
        "",
        " ",
        "x",
        "x = 1\n",
        "5  * 3",
        "# comment\nvalue",
        "def function(a=1):\n    return a\n",
        "class Example:\n    pass\n",
        "a\r\nb\r\n",
        "    F\"\"\"",
        "    F\"\"\"\n",
        "f'''s{\n   str.uppe\n'''\n",
    ],
    ids=["empty", "space", "name", "assignment", "operators", "comment", "function", "class", "crlf", "unfinished-string", "unfinished-string-newline", "unfinished-fstring"],
)
def test_parse_round_trips_exact_code(code):
    assert parse(code).get_code() == code


@pytest.mark.parametrize(
    ("code", "end_pos"),
    [
        ("a", (1, 1)),
        ("a\n", (2, 0)),
        ("a\nb", (2, 1)),
        ("a\n#comment\n", (3, 0)),
        ("a#comment", (1, 9)),
        ("def a():\n pass", (2, 5)),
    ],
    ids=["single", "terminal-newline", "two-lines", "comment-line", "inline-comment", "suite"],
)
def test_module_end_positions(code, end_pos):
    module = parse(code)
    assert module.start_pos == (1, 0)
    assert module.end_pos == end_pos


def test_tree_shape_and_parent_links():
    module = parse("def add(x, y):\n    return x + y\n")
    function = module.children[0]
    assert module.type == "file_input"
    assert function.type == "funcdef"
    assert function.parent is module
    assert function.children[1].type == "name"
    assert function.children[1].value == "add"
    assert function.children[1].parent is function
    assert module.parent is None


def test_leaf_navigation_preserves_source_order():
    module = parse("alpha + beta")
    alpha = module.get_first_leaf()
    plus = alpha.get_next_leaf()
    beta = plus.get_next_leaf()
    endmarker = module.get_last_leaf()
    assert (alpha.value, plus.value, beta.value, endmarker.value) == ("alpha", "+", "beta", "")
    assert beta.get_previous_leaf() is plus
    assert plus.get_previous_leaf() is alpha
    assert endmarker.get_previous_leaf() is beta


def test_leaf_prefixes_and_positions():
    module = parse("  alpha  + beta")
    indentation_error = module.get_first_leaf()
    alpha = indentation_error.get_next_leaf()
    plus = alpha.get_next_leaf()
    beta = plus.get_next_leaf()
    assert indentation_error.type == "error_leaf"
    assert indentation_error.start_pos == (1, 2)
    assert alpha.prefix == "  "
    assert alpha.start_pos == (1, 2)
    assert alpha.end_pos == (1, 7)
    assert plus.prefix == "  "
    assert beta.prefix == " "
    assert beta.end_pos == (1, 15)


@pytest.mark.parametrize(
    ("indent", "line_prefix"),
    [(None, None), (0, ""), (2, "  "), ("\t", "\t")],
    ids=["compact", "zero", "spaces", "tab"],
)
def test_tree_dump_indentation(indent, line_prefix):
    dumped = parse("lambda x, y: x + y").dump(indent=indent)
    assert dumped.startswith("Module([")
    assert "Lambda([" in dumped
    assert "Name('x', (1, 7), prefix=' ')" in dumped
    assert "Operator('+', (1, 15), prefix=' ')" in dumped
    if line_prefix is None:
        assert "\n" not in dumped
    else:
        assert f"\n{line_prefix}Lambda([" in dumped


def test_tree_dump_rejects_invalid_indent():
    with pytest.raises(TypeError):
        parse("x").dump(indent=1.5)


def test_intermediate_node_and_leaf_dump():
    function = parse("def foo(): pass").children[0]
    keyword = function.children[0]
    assert function.dump().startswith("Function([")
    assert keyword.dump() == "Keyword('def', (1, 0))"


@pytest.mark.parametrize(
    "code",
    ['f"{1}"', 'f"""{1}"""', 'f"{foo} {bar}"', 'f"{{{1}}}"', 'f"{x:{y}}"', 'f"{a=}"'],
    ids=["simple", "triple", "two-expressions", "escaped-braces", "nested-format", "debug"],
)
def test_valid_fstrings_are_fstring_nodes(code):
    module = load_grammar(version="3.8").parse(code, error_recovery=False)
    assert module.children[0].type == "fstring"
    assert module.get_code() == code


@pytest.mark.parametrize(
    "code",
    ['f"}"', 'f"{"', 'f"{}"', 'f"{!}"', 'f"{1!{a}}"'],
    ids=["close-brace", "open-brace", "empty", "empty-conversion", "nested-conversion"],
)
def test_invalid_fstrings_raise_without_recovery(code):
    grammar = load_grammar(version="3.8")
    with pytest.raises(ParserSyntaxError):
        grammar.parse(code, error_recovery=False)
    assert grammar.parse(code, error_recovery=True).get_code() == code


@pytest.mark.parametrize("version", ["3.6", "3.7", "3.8", "4.0"], ids=["36", "37", "38", "future"])
def test_load_grammar_accepts_compatible_versions(version):
    grammar = load_grammar(version=version)
    assert grammar.parse("x = 1").get_code() == "x = 1"


def test_load_grammar_rejects_unsupported_old_version():
    with pytest.raises(NotImplementedError):
        load_grammar(version="1.5")


@pytest.mark.parametrize("version", ["1.", "a", "#", "1.3.4.5"], ids=["trailing-dot", "letter", "symbol", "too-many-parts"])
def test_load_grammar_rejects_malformed_version(version):
    with pytest.raises(ValueError):
        load_grammar(version=version)


def test_load_grammar_rejects_non_string_version():
    with pytest.raises(TypeError):
        load_grammar(version=3.8)


def test_parse_rejects_undecodable_bytes():
    with pytest.raises(UnicodeDecodeError):
        parse(b"\xe4")


@pytest.mark.parametrize(
    ("value", "keepends", "expected"),
    [
        ("", False, [""]),
        ("a\nb", False, ["a", "b"]),
        ("a\r\nb\r", False, ["a", "b", ""]),
        ("a\nb\n", True, ["a\n", "b\n", ""]),
        ("a\fb", False, ["a\fb"]),
    ],
    ids=["empty", "lf", "mixed", "keepends", "form-feed"],
)
def test_split_lines_python_semantics(value, keepends, expected):
    assert split_lines(value, keepends=keepends) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("already unicode", "already unicode"),
        (b"plain ascii", "plain ascii"),
        (b"# coding: latin-1\nvalue='\xe4'", "# coding: latin-1\nvalue='\xe4'"),
        (b"\xef\xbb\xbfvalue = 1", "\ufeffvalue = 1"),
    ],
    ids=["str", "ascii", "encoding-cookie", "bom"],
)
def test_python_bytes_to_unicode(value, expected):
    assert python_bytes_to_unicode(value) == expected


def test_file_io_reads_bytes_and_reports_timestamp(tmp_path):
    path = tmp_path / "module.py"
    path.write_bytes(b"value = 1\n")
    file_io = FileIO(path)
    assert file_io.path == path
    assert file_io.read() == b"value = 1\n"
    assert isinstance(file_io.get_last_modified(), float)
    assert "FileIO" in repr(file_io)


def test_file_io_missing_timestamp_is_none(tmp_path):
    assert FileIO(tmp_path / "missing.py").get_last_modified() is None


def test_known_content_file_io_returns_supplied_content(tmp_path):
    path = Path(tmp_path / "virtual.py")
    file_io = KnownContentFileIO(path, "virtual = True")
    assert file_io.path == path
    assert file_io.read() == "virtual = True"
