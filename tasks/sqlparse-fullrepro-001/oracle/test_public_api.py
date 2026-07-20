import io

import pytest

import sqlparse
from sqlparse import tokens as T


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", 0),
        ("   ", 0),
        ("select 1", 1),
        ("select 1;", 1),
        ("select 1; select 2;", 2),
        ("select ';'; select 2", 2),
        ("select 1 -- ;\n; select 2", 2),
        ("/* ; */ select 1; select 2", 2),
    ],
)
def test_parse_statement_count(text, expected):
    assert len(sqlparse.parse(text)) == expected


@pytest.mark.parametrize(
    "text",
    [
        "select 1",
        "SELECT a, b FROM table_name WHERE a = 2",
        "insert into t values (1, 'x')",
        "update t set a = 3 where id = 1",
        "delete from t where id in (1, 2)",
        "select case when a > 1 then 'yes' else 'no' end from t",
        "select count(*) from t group by a order by a desc",
        "with x as (select 1) select * from x",
    ],
)
def test_parse_preserves_sql_text(text):
    assert str(sqlparse.parse(text)[0]) == text


@pytest.mark.parametrize(
    "text, expected",
    [
        ("select 1; select 2;", ["select 1;", "select 2;"]),
        ("select 1; select 2;", ["select 1", "select 2"]),
        ("select ';'; select 2", ["select ';';", "select 2"]),
        ("select 1 -- ;\n; select 2", ["select 1 -- ;\n;", "select 2"]),
        ("", []),
    ],
)
def test_split_statements(text, expected):
    strip = expected and not any(item.endswith(";") for item in expected)
    assert sqlparse.split(text, strip_semicolon=strip) == expected


@pytest.mark.parametrize(
    "text",
    ["select 1", "select 1;", "select ';'", "/* comment */ select 1", "select (1 + 2)"],
)
def test_split_round_trip(text):
    assert "".join(sqlparse.split(text)) == text


@pytest.mark.parametrize(
    "option, expected",
    [
        ({"keyword_case": "upper"}, "SELECT * FROM foo"),
        ({"keyword_case": "lower"}, "select * from foo"),
        ({"keyword_case": "capitalize"}, "Select * From foo"),
        ({"identifier_case": "upper"}, "select * from FOO"),
        ({"identifier_case": "lower"}, "select * from foo"),
        ({"identifier_case": "capitalize"}, "select * from Foo"),
    ],
)
def test_format_case_options(option, expected):
    assert sqlparse.format("select * from foo", **option).strip() == expected


@pytest.mark.parametrize(
    "option",
    [
        {"strip_comments": True},
        {"strip_whitespace": True},
        {"reindent": True},
        {"use_space_around_operators": True},
        {"reindent_aligned": True},
        {"indent_width": 4, "reindent": True},
    ],
)
def test_format_options_return_text(option):
    result = sqlparse.format("select a+1 -- note\nfrom foo", **option)
    assert isinstance(result, str)
    assert "foo" in result


@pytest.mark.parametrize("bad", ["invalid", 3])
def test_invalid_format_options_raise_public_error(bad):
    with pytest.raises(sqlparse.exceptions.SQLParseError):
        sqlparse.format("select 1", keyword_case=bad)


def test_parsestream_accepts_text_stream():
    statements = list(sqlparse.parsestream(io.StringIO("select 1; select 2")))
    assert [str(statement).strip() for statement in statements] == ["select 1;", "select 2"]


@pytest.mark.parametrize("text", ["select 1", "select a from t", "insert into t values (1)"])
def test_tokenize_yields_token_type_and_value(text):
    tokens = list(sqlparse.lexer.tokenize(text))
    assert tokens
    assert all(len(item) == 2 for item in tokens)
    assert "".join(value for _ttype, value in tokens) == text


@pytest.mark.parametrize(
    "text, expected",
    [
        ("a\nb", ["a", "b"]),
        ("a\r\nb", ["a", "b"]),
        ("a\n\nb", ["a", "", "b"]),
        ("a", ["a"]),
    ],
)
def test_split_unquoted_newlines(text, expected):
    assert sqlparse.utils.split_unquoted_newlines(text) == expected


@pytest.mark.parametrize(
    "value, expected",
    [("'name'", "name"), ('"name"', "name"), ("name", "name")],
)
def test_remove_quotes(value, expected):
    assert sqlparse.utils.remove_quotes(value) == expected


def test_public_tokens_are_available():
    assert T.Keyword is not None
    assert T.Name is not None
    assert T.Literal.String.Single is not None
