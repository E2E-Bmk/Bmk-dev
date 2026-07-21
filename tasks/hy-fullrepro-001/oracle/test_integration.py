from __future__ import annotations

# Rewritten from tests/compilers/test_ast.py at the pinned source revision.
import sys
import pytest
from hy.compiler import hy_compile
from hy.errors import HyError, HyLanguageError
from hy.reader import read_many

def can_compile(expr, import_stdlib=False, iff=True):
    return hy_compile(read_many(expr), __name__, import_stdlib=import_stdlib) if iff else cant_compile(expr)

def cant_compile(expr):
    with pytest.raises(HyError) as excinfo:
        hy_compile(read_many(expr), __name__)
    assert issubclass(excinfo.type, HyLanguageError)
    assert excinfo.value.msg
    return excinfo.value

def test_ast_bad_type():
    """Make sure AST breakage can happen"""

    class C:
        pass
    with pytest.raises(TypeError):
        hy_compile(C(), __name__, filename='<string>', source='')

def test_empty_expr():
    """Empty expressions should be illegal at the top level."""
    cant_compile('(print ())')
    can_compile("(print '())")

def test_dot_unpacking():
    can_compile('(.meth obj #* args az)')
    cant_compile('(.meth #* args az)')
    cant_compile('(. foo #* bar baz)')
    can_compile('(.meth obj #** args az)')
    can_compile('(.meth #** args obj)')
    cant_compile('(. foo #** bar baz)')

def test_ast_bad_if():
    cant_compile('(if)')
    cant_compile('(if foobar)')
    cant_compile('(if 1 2 3 4 5)')

def test_ast_valid_if():
    can_compile('(if foo bar baz)')

def test_ast_bad_while():
    cant_compile('(while)')

def test_ast_good_do():
    can_compile('(do)')
    can_compile('(do 1)')

def test_ast_good_raise():
    can_compile('(raise)')
    can_compile('(raise Exception)')
    can_compile('(raise e)')

def test_ast_raise_from():
    can_compile('(raise Exception :from NameError)')

def test_ast_bad_raise():
    cant_compile('(raise Exception Exception)')

def test_ast_good_try():
    can_compile('(try 1 (except []) (else 1))')
    can_compile('(try 1 (finally 1))')
    can_compile('(try 1 (except []) (finally 1))')
    can_compile('(try 1 (except [x]) (except [y]) (finally 1))')
    can_compile('(try 1 (except []) (else 1) (finally 1))')
    can_compile('(try 1 (except [x]) (except [y]) (else 1) (finally 1))')
    can_compile(iff=sys.version_info >= (3, 11), expr='(try 1 (except* [x]))')
    can_compile(iff=sys.version_info >= (3, 11), expr='(try 1 (except* [x]) (else 1) (finally 1))')

def test_ast_bad_try():
    cant_compile('(try (do) (else 1) (else 2))')
    cant_compile('(try 1 (else 1) (except []))')
    cant_compile('(try 1 (finally 1) (except []))')
    cant_compile('(try 1 (except []) (finally 1) (else 1))')
    cant_compile('(try 1 (except* [x]) (except [x]))')
    cant_compile('(try 1 (except [x]) (except* [x]))')

def test_ast_good_except():
    can_compile('(try 1 (except []))')
    can_compile('(try 1 (except [Foobar]))')
    can_compile('(try 1 (except [[]]))')
    can_compile('(try 1 (except [x FooBar]))')
    can_compile('(try 1 (except [x [FooBar BarFoo]]))')
    can_compile('(try 1 (except [x [FooBar BarFoo]]))')

def test_ast_bad_except():
    cant_compile('(except 1)')
    cant_compile('(try 1 (except))')
    cant_compile('(try 1 (except 1))')
    cant_compile('(try 1 (except [1 3]))')
    cant_compile('(try 1 (except [(f) [IOError ValueError]]))')
    cant_compile('(try 1 (except [x [FooBar] BarBar]))')

def test_ast_good_assert():
    can_compile('(assert 1)')
    can_compile('(assert 1 "Assert label")')
    can_compile('(assert 1 (+ "spam " "eggs"))')
    can_compile('(assert 1 12345)')
    can_compile('(assert 1 None)')
    can_compile('(assert 1 (+ 2 "incoming eggsception"))')
