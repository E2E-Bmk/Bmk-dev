from textwrap import dedent

import pytest

import parso
from parso import ParserSyntaxError, load_grammar, parse
from parso.file_io import KnownContentFileIO


def test_error_recovery_preserves_valid_statements_around_error():
    module = parse("with x: f.\na")
    with_statement = module.children[0]
    assert with_statement.type == "with_stmt"
    error = with_statement.children[-1]
    assert error.type == "error_node"
    assert error.get_code(include_prefix=False) == "f."
    assert module.children[2].type == "name"
    assert module.children[2].value == "a"
    assert module.get_code() == "with x: f.\na"


@pytest.mark.parametrize("version", ["3.6", "3.7", "3.8"], ids=["36", "37", "38"])
def test_incomplete_one_line_function_recovers(version):
    module = parse("def x(): f.", version=version)
    function = module.children[0]
    assert function.type == "funcdef"
    assert function.children[-1].type == "error_node"
    assert module.get_code() == "def x(): f."


def test_invalid_token_is_retained_as_error_leaf():
    module = parse("a + ? + b")
    error_node, question, plus_b, endmarker = module.children
    assert error_node.get_code() == "a +"
    assert question.type == "error_leaf"
    assert question.value == "?"
    assert plus_b.get_code() == " + b"
    assert module.get_code() == "a + ? + b"


def test_inline_else_error_recovery_keeps_all_text():
    code = "if x: f.\nelse: g("
    module = parse(code)
    assert module.children[0].type == "if_stmt"
    assert module.children[0].children[-1].type == "error_node"
    assert module.children[2].type == "error_leaf"
    assert module.children[2].value == "else"
    assert module.get_code() == code


def test_bad_dedent_has_error_leaf_and_round_trips():
    code = "class C:\n  f\n g\n"
    module = load_grammar(version="3.8").parse(code)
    suite = module.children[0].children[-1]
    assert suite.children[2].type == "error_leaf"
    assert suite.children[2].token_type == "ERROR_DEDENT"
    assert module.get_code() == code


@pytest.mark.parametrize(
    ("code", "expected_message"),
    [
        ("foo +\n", "invalid syntax"),
        ("continue\n", "not properly in loop"),
        ("if True\n    pass\n", "invalid syntax"),
    ],
    ids=["operator", "continue", "missing-colon"],
)
def test_grammar_iter_errors_reports_syntax_issues(code, expected_message):
    grammar = load_grammar(version="3.8")
    module = grammar.parse(code)
    issues = list(grammar.iter_errors(module))
    assert issues
    assert expected_message in issues[0].message
    assert isinstance(issues[0].start_pos, tuple)


def test_grammar_iter_errors_is_empty_for_valid_module():
    grammar = load_grammar(version="3.8")
    assert list(grammar.iter_errors(grammar.parse("value = 1\n"))) == []


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("a", "b"),
        ("def func():\n    pass\na", "def func():\n    pass\nb"),
        ("if True:\n    value = 1\n", "if True:\n    value = 2\nelse:\n    value = 3\n"),
        ("class A:\n    pass\n", "class A:\n    def method(self):\n        return 1\n"),
        ("value = (1,\n", "value = (1, 2)\n"),
        ("@decorator\ndef func():\n    pass", "@decorator\ndef func():\n    return 1\n"),
    ],
    ids=["name", "function-tail", "if-else", "class-body", "parentheses", "decorator"],
)
def test_incremental_parse_updates_cached_module(tmp_path, before, after):
    path = tmp_path / "module.py"
    cache_path = tmp_path / "cache"
    first = parse(before, path=path, cache=True, diff_cache=True, cache_path=cache_path)
    second = parse(after, path=path, cache=True, diff_cache=True, cache_path=cache_path)
    fresh = parse(after)
    assert second is first
    assert second.get_code() == after
    assert second.get_code() == fresh.get_code()
    assert second.start_pos == fresh.start_pos
    assert second.end_pos == fresh.end_pos


def test_incremental_change_and_undo(tmp_path):
    path = tmp_path / "module.py"
    cache_path = tmp_path / "cache"
    original = "def func():\n    pass\na\n"
    changed = "def func():\n    pass\nb\n"
    module = parse(original, path=path, cache=True, diff_cache=True, cache_path=cache_path)
    assert parse(changed, path=path, cache=True, diff_cache=True, cache_path=cache_path) is module
    assert module.get_code() == changed
    assert parse(original, path=path, cache=True, diff_cache=True, cache_path=cache_path) is module
    assert module.get_code() == original


def test_parse_from_path_and_file_io(tmp_path):
    path = tmp_path / "module.py"
    path.write_bytes(b"from_path = True\n")
    from_path = parse(path=path)
    virtual = KnownContentFileIO(tmp_path / "virtual.py", "from_memory = True\n")
    from_memory = load_grammar().parse(file_io=virtual)
    assert from_path.get_code() == "from_path = True\n"
    assert from_memory.get_code() == "from_memory = True\n"


def test_parser_requires_an_input_source():
    with pytest.raises(TypeError):
        load_grammar().parse()


def test_non_file_start_symbol_requires_recovery_disabled():
    grammar = load_grammar(version="3.8")
    with pytest.raises(NotImplementedError):
        grammar.parse("x + 1", start_symbol="eval_input")
    module = grammar.parse("x + 1", start_symbol="eval_input", error_recovery=False)
    assert module.get_code() == "x + 1"


def test_parser_syntax_error_exposes_position_and_message():
    grammar = load_grammar(version="3.8")
    with pytest.raises(ParserSyntaxError) as raised:
        grammar.parse("def broken(:\n", error_recovery=False)
    assert raised.value.error_leaf.start_pos == (1, 11)
    assert "SyntaxError" in str(raised.value)


def test_dump_contains_enough_information_to_compare_tree_views():
    code = dedent(
        """\
        def add(x, y):
            return x + y
        """
    )
    module = parso.parse(code)
    dumped = module.dump(indent=2)
    assert "Function([" in dumped
    assert "Name('add', (1, 4), prefix=' ')" in dumped
    assert "ReturnStmt([" in dumped
    assert "Name('x', (2, 11), prefix=' ')" in dumped
    assert module.get_code() == code
