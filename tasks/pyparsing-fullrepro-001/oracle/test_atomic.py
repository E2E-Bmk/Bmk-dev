import pytest
import pyparsing as pp

@pytest.mark.parametrize('test_label, loc, input_string, expected_output', [('First column, no newline', 0, 'abcdef', 1), ('Second column, no newline', 1, 'abcdef', 2), ('First column after newline', 4, 'abc\ndef', 1), ('Second column after newline', 5, 'abc\ndef', 2), ('Column after multiple newlines', 9, 'abc\ndef\nghi', 2), ('Location at start of string', 0, 'abcdef', 1), ('Location at end of string', 5, 'abcdef', 6), ('Column after newline at end', 3, 'abc\n', 4), ('Tab character in the string', 4, 'a\tbcd\tef', 5), ('Multiple lines with tab', 8, 'a\tb\nc\td', 5)])
def test_col(test_label: str, loc: int, input_string: str, expected_output: int):
    from pyparsing.util import col
    print(test_label)
    assert col(loc, input_string) == expected_output

@pytest.mark.parametrize('test_label, loc, input_string, expected_output', [('Single line, no newlines', 0, 'abcdef', 'abcdef'), ('First line in multi-line string', 2, 'abc\ndef', 'abc'), ('Second line in multi-line string', 5, 'abc\ndef', 'def'), ('Location at start of second line', 4, 'abc\ndef', 'def'), ('Empty string', 0, '', ''), ('Location at newline character', 3, 'abc\ndef', 'abc'), ('Last line without trailing newline', 7, 'abc\ndef\nghi', 'def'), ('Single line with newline at end', 2, 'abc\n', 'abc'), ('Multi-line with multiple newlines', 6, 'line1\nline2\nline3', 'line2'), ('Multi-line with trailing newline', 11, 'line1\nline2\nline3\n', 'line2')])
def test_line(test_label: str, loc: int, input_string: str, expected_output: str):
    from pyparsing import line
    print(test_label)
    assert line(loc, input_string) == expected_output

@pytest.mark.parametrize('test_label, loc, input_string, expected_output', [('Single line, no newlines', 0, 'abcdef', 1), ('First line in multi-line string', 2, 'abc\ndef', 1), ('Second line in multi-line string', 5, 'abc\ndef', 2), ('Location at start of second line', 4, 'abc\ndef', 2), ('Multiple newlines, third line', 10, 'abc\ndef\nghi', 3), ('Empty string', 0, '', 1), ('Location at newline character', 3, 'abc\ndef', 1), ('Last line without trailing newline', 7, 'abc\ndef\nghi', 2), ('Single line with newline at end', 4, 'abc\n', 2), ('Multi-line with trailing newline', 12, 'line1\nline2\nline3\n', 3), ('Location in middle of a tabbed string', 7, 'a\tb\nc\td', 2)])
def test_lineno(test_label: str, loc: int, input_string: str, expected_output: int):
    from pyparsing import lineno
    assert lineno(loc, input_string) == expected_output

def test_html_entities() -> None:
    from pyparsing import common_html_entity

    entity_strings = ["&amp;", "&gt;", "&lt;", "&nbsp;", "&quot;"]
    parsed = common_html_entity()[...].parse_string(" ".join(entity_strings), parse_all=True)
    assert len(parsed) == len(entity_strings)
