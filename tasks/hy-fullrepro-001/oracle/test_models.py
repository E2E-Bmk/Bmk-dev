from __future__ import annotations

# Rewritten from tests/test_models.py at the pinned source revision.
import pytest
from hy.models import Dict, Expression, FComponent, FString, Integer, Keyword, List, Set, String, Symbol, Tuple, as_model, replace_hy_obj

def test_symbol_or_keyword():
    for x in ('foo', 'foo-bar', 'foo_bar', '✈é😂⁂'):
        assert str(Symbol(x)) == x
        assert Keyword(x).name == x
    for x in ('', ':foo', '5', '#foo'):
        with pytest.raises(ValueError):
            Symbol(x)
        assert Keyword(x).name == x
    for x in ('foo bar', 'fib()'):
        with pytest.raises(ValueError):
            Symbol(x)
        with pytest.raises(ValueError):
            Keyword(x)

def test_wrap_int():
    wrapped = as_model(0)
    assert type(wrapped) == Integer

def test_wrap_tuple():
    wrapped = as_model((Integer(0),))
    assert type(wrapped) == Tuple
    assert type(wrapped[0]) == Integer
    assert wrapped == Tuple([Integer(0)])

def test_wrap_nested_expr():
    """Test conversion of Expressions with embedded non-HyObjects."""
    wrapped = as_model(Expression([0]))
    assert type(wrapped) == Expression
    assert type(wrapped[0]) == Integer
    assert wrapped == Expression([Integer(0)])

def test_replace_int():
    replaced = replace_hy_obj(0, Integer(13))
    assert replaced == Integer(0)

def test_invalid_bracket_strings():
    for (string, brackets) in [(']foo]', 'foo'), ('something ]f] else', 'f')]:
        with pytest.raises(ValueError):
            String(string, brackets)
    for (nodes, brackets) in [([String('hello'), String('world ]foo]')], 'foo'), ([String('something'), FComponent([String('world')]), String(']f]')], 'f'), ([String('something'), FComponent([Integer(1), String(']f]')])], 'f')]:
        with pytest.raises(ValueError):
            FString(nodes, brackets=brackets)

def test_replace_str():
    replaced = replace_hy_obj('foo', String('bar'))
    assert replaced == String('foo')

def test_replace_tuple():
    replaced = replace_hy_obj((0,), Integer(13))
    assert type(replaced) == Tuple
    assert type(replaced[0]) == Integer
    assert replaced == Tuple([Integer(0)])

def test_list_add():
    """Check that adding two Lists generates a List"""
    a = List([1, 2, 3])
    b = List([3, 4, 5])
    c = a + b
    assert c == List([1, 2, 3, 3, 4, 5])
    assert type(c) is List

def test_list_slice():
    """Check that slicing a List produces a List"""
    a = List([1, 2, 3, 4])
    sl1 = a[1:]
    sl5 = a[5:]
    assert type(sl1) == List
    assert sl1 == List([2, 3, 4])
    assert type(sl5) == List
    assert sl5 == List([])

def test_hydict_methods():
    hydict = Dict(['a', 1, 'z', 9, 'b', 2, 'a', 3, 'c', 4])
    assert hydict.items() == [('a', 1), ('z', 9), ('b', 2), ('a', 3), ('c', 4)]
    assert hydict.keys() == ['a', 'z', 'b', 'a', 'c']
    assert hydict.values() == [1, 9, 2, 3, 4]

def test_set():
    assert list(Set([3, 1, 2, 2])) == [3, 1, 2, 2]
