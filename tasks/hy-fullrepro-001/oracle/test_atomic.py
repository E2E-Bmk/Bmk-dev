from __future__ import annotations

# Rewritten from tests/test_reader.py at the pinned source revision.
import traceback
from math import isnan
import pytest
from hy import PrematureEndOfInput
from hy.models import Complex, Dict, Expression, Float, Integer, List, String, Symbol
from hy.reader import read_many
from hy.reader.exceptions import LexException

def tokenize(*args, **kwargs):
    return list(read_many(*args, **kwargs))

def peoi():
    return pytest.raises(PrematureEndOfInput)

def lexe():
    return pytest.raises(LexException)

def check_ex(einfo, expected):
    assert [x.rstrip() for x in traceback.format_exception_only(einfo.type, einfo.value)] == expected

def test_lex_exception():
    """Ensure tokenize throws a fit on a partial input"""
    with peoi():
        tokenize('(foo')
    with peoi():
        tokenize('{foo bar')
    with peoi():
        tokenize('(defn foo [bar]')
    with peoi():
        tokenize('(foo "bar')

def test_unbalanced_exception():
    """Ensure the tokenization fails on unbalanced expressions"""
    with lexe():
        tokenize('(bar))')
    with lexe():
        tokenize('(baz [quux]])')

def test_lex_single_quote_err():
    with lexe() as execinfo:
        tokenize("' ")
    assert type(execinfo.value) is PrematureEndOfInput
    assert execinfo.value.msg == 'Premature end of input while attempting to parse one form'

def test_lex_expression_symbols():
    """Make sure that expressions produce symbols"""
    objs = tokenize('(foo bar)')
    assert objs == [Expression([Symbol('foo'), Symbol('bar')])]

def test_symbol_and_sugar():
    s = Symbol

    def e(*x):
        return Expression(x)
    for (char, head) in (("'", 'quote'), ('`', 'quasiquote'), ('~', 'unquote'), ('~@', 'unquote-splice')):
        for string in (f'a{s1}{char}{s2}b' for s1 in ('', ' ') for s2 in ('', ' ')):
            assert tokenize(string) == [s('a'), e(s(head), s('b'))]
    assert tokenize('a~ @b') == tokenize('a ~ @b') == [s('a'), e(s('unquote'), s('@b'))]

def test_lex_expression_strings():
    """Test that expressions can produce strings"""
    objs = tokenize('(foo "bar")')
    assert objs == [Expression([Symbol('foo'), String('bar')])]

def test_lex_expression_integer():
    """Make sure expressions can produce integers"""
    objs = tokenize('(foo 2)')
    assert objs == [Expression([Symbol('foo'), Integer(2)])]

def test_lex_symbols():
    """Make sure that symbols are valid expressions"""
    objs = tokenize('foo ')
    assert objs == [Symbol('foo')]

def test_lex_strings():
    """Make sure that strings are valid expressions"""
    objs = tokenize('"foo"')
    assert objs == [String('foo')]
    objs = tokenize('\n"a\\\nbc"\n')
    assert objs == [String('abc')]

def test_lex_strings_exception():
    """Make sure tokenize throws when codec can't decode some bytes"""
    with lexe() as execinfo:
        tokenize('"\\x8"')
    check_ex(execinfo, ['  File "<string>", line 1', '    "\\x8"', '        ^', "hy.reader.exceptions.LexException: 'unicodeescape' codec can't decode bytes in position 0-2: truncated \\xXX escape"])

def test_lex_bracket_strings():
    objs = tokenize('#[my delim[hello world]my delim]')
    assert objs == [String('hello world')]
    assert objs[0].brackets == 'my delim'
    objs = tokenize('#[[squid]]')
    assert objs == [String('squid')]
    assert objs[0].brackets == ''

def test_lex_integers():
    assert tokenize('42') == [Integer(42)]
    assert tokenize('0x80') == [Integer(128)]
    assert tokenize('0o1232') == [Integer(666)]
    assert tokenize('0b1011101') == [Integer(93)]

def test_lex_expression_float():
    """Make sure expressions can produce floats"""
    objs = tokenize('(foo 2.)')
    assert objs == [Expression([Symbol('foo'), Float(2.0)])]
    objs = tokenize('(foo -0.5)')
    assert objs == [Expression([Symbol('foo'), Float(-0.5)])]
    objs = tokenize('(foo 1.e7)')
    assert objs == [Expression([Symbol('foo'), Float(10000000.0)])]

def test_lex_big_float():
    assert tokenize('1e900') == [Float(1e309)]
    assert tokenize('1e900-1e900j') == [Complex(1e309, -1e309)]

def test_lex_nan_and_inf():
    assert isnan(tokenize('NaN')[0])
    assert tokenize('Nan') == [Symbol('Nan')]
    assert tokenize('nan') == [Symbol('nan')]
    assert tokenize('NAN') == [Symbol('NAN')]
    assert tokenize('Inf') == [Float(float('inf'))]
    assert tokenize('inf') == [Symbol('inf')]
    assert tokenize('INF') == [Symbol('INF')]
    assert tokenize('-Inf') == [Float(float('-inf'))]
    assert tokenize('-inf') == [Symbol('-inf')]
    assert tokenize('-INF') == [Symbol('-INF')]

def test_lex_expression_complex():
    """Make sure expressions can produce complex"""

    def t(x):
        return tokenize('(foo {})'.format(x))

    def f(x):
        return [Expression([Symbol('foo'), x])]
    assert t('2j') == f(Complex(2j))
    assert t('2J') == f(Complex(2j))
    assert t('2.j') == f(Complex(2j))
    assert t('2.J') == f(Complex(2j))
    assert t('-0.5j') == f(Complex(-0.5j))
    assert t('1.e7j') == f(Complex(10000000j))
    assert t('1.e7J') == f(Complex(10000000j))
    assert t('j') == f(Symbol('j'))
    assert t('J') == f(Symbol('J'))
    assert isnan(t('NaNj')[0][1].imag)
    assert t('nanj') == f(Symbol('nanj'))
    assert t('Inf+Infj') == f(Complex(complex(float('inf'), float('inf'))))
    assert t('Inf-Infj') == f(Complex(complex(float('inf'), float('-inf'))))
    assert t('Inf-INFj') == f(Symbol('Inf-INFj'))
    assert isnan(t('NaNJ')[0][1].imag)
    assert t('nanJ') == f(Symbol('nanJ'))
    assert t('InfJ') == f(Complex(complex(0, float('inf'))))
    assert t('iNfJ') == f(Symbol('iNfJ'))
    assert t('Inf-INFJ') == f(Symbol('Inf-INFJ'))

def test_lex_digit_separators():
    assert tokenize('1_000_000') == [Integer(1000000)]
    assert tokenize('1,000,000') == [Integer(1000000)]
    assert tokenize('1,000_000') == [Integer(1000000)]
    assert tokenize('1_000,000') == [Integer(1000000)]
    assert tokenize('_42') == [Symbol('_42')]
    assert tokenize('0x_af') == [Integer(175)]
    assert tokenize('0x,af') == [Integer(175)]
    assert tokenize('0_xaf') == [Integer(175)]
    assert tokenize('0b_010') == [Integer(2)]
    assert tokenize('0b,010') == [Integer(2)]
    assert tokenize('0o_373') == [Integer(251)]
    assert tokenize('0o,373') == [Integer(251)]
    assert tokenize('1_2._3,4') == [Float(12.34)]
    assert tokenize('1_2e_3,4') == [Float(1.2e+35)]
    assert tokenize('1,0_00j,') == [Complex(1000j)]
    assert tokenize('1,,,,___,____,,__,,2__,,,__') == [Integer(12)]
    assert tokenize('_1,,,,___,____,,__,,2__,,,__') == [Symbol('_1,,,,___,____,,__,,2__,,,__')]
    assert tokenize('1,,,,___,____,,__,,2__,q,__') == [Symbol('1,,,,___,____,,__,,2__,q,__')]

def test_leading_zero():
    assert tokenize('0') == [Integer(0)]
    assert tokenize('0000') == [Integer(0)]
    assert tokenize('010') == [Integer(10)]
    assert tokenize('000010') == [Integer(10)]
    assert tokenize('000010.00') == [Float(10)]
    assert tokenize('010+000010j') == [Complex(10 + 10j)]

def test_dotted_identifiers():
    t = tokenize
    assert t('foo.bar') == t('(. foo bar)')
    assert t('foo.bar.baz') == t('(. foo bar baz)')
    assert t('.foo') == t('(. None foo)')
    assert t('.foo.bar.baz') == t('(. None foo bar baz)')
    assert t('..foo') == t('(.. None foo)')
    assert t('..foo.bar.baz') == t('(.. None foo bar baz)')

def test_lex_bad_attrs():
    with lexe() as execinfo:
        tokenize('1.foo')
    check_ex(execinfo, ['  File "<string>", line 1', '    1.foo', '        ^', 'hy.reader.exceptions.LexException: The parts of a dotted identifier must be symbols'])
    with lexe():
        tokenize('0.foo')
    with lexe():
        tokenize('1.5.foo')
    with lexe():
        tokenize('1e3.foo')
    with lexe():
        tokenize('5j.foo')
    with lexe():
        tokenize('3+5j.foo')
    with lexe():
        tokenize('3.1+5.1j.foo')
    assert tokenize('j.foo')
    with lexe():
        tokenize(':hello.foo')

def test_lists():
    assert tokenize('[1 2 3 4]') == [List(map(Integer, (1, 2, 3, 4)))]

def test_lex_column_counting():
    entry = tokenize('(foo (one two))')[0]
    assert entry.start_line == 1
    assert entry.start_column == 1
    assert entry.end_line == 1
    assert entry.end_column == 15
    symbol = entry[0]
    assert symbol.start_line == 1
    assert symbol.start_column == 2
    assert symbol.end_line == 1
    assert symbol.end_column == 4
    inner_expr = entry[1]
    assert inner_expr.start_line == 1
    assert inner_expr.start_column == 6
    assert inner_expr.end_line == 1
    assert inner_expr.end_column == 14

def test_lex_column_counting_with_literal_newline():
    (string, symbol) = tokenize('"apple\nblueberry" abc')
    assert string.start_line == 1
    assert string.start_column == 1
    assert string.end_line == 2
    assert string.end_column == 10
    assert symbol.start_line == 2
    assert symbol.start_column == 12
    assert symbol.end_line == 2
    assert symbol.end_column == 14

def test_lex_line_counting_multi():
    """Make sure we can do multi-line tokenization"""
    entries = tokenize('\n(foo (one two))\n(foo bar)\n')
    entry = entries[0]
    assert entry.start_line == 2
    assert entry.start_column == 1
    assert entry.end_line == 2
    assert entry.end_column == 15
    entry = entries[1]
    assert entry.start_line == 3
    assert entry.start_column == 1
    assert entry.end_line == 3
    assert entry.end_column == 9

def test_dicts():
    """Ensure that we can tokenize a dict."""
    objs = tokenize('{foo bar bar baz}')
    assert objs == [Dict([Symbol('foo'), Symbol('bar'), Symbol('bar'), Symbol('baz')])]
    objs = tokenize('(bar {foo bar bar baz})')
    assert objs == [Expression([Symbol('bar'), Dict([Symbol('foo'), Symbol('bar'), Symbol('bar'), Symbol('baz')])])]
    objs = tokenize('{(foo bar) (baz quux)}')
    assert objs == [Dict([Expression([Symbol('foo'), Symbol('bar')]), Expression([Symbol('baz'), Symbol('quux')])])]
