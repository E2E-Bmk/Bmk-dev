# Spec2Repo oracle - atomic tests for deal

import asyncio
import inspect
import socket
from typing import get_type_hints
import pytest
import deal
import importlib
import subprocess
import sys
import deal.introspection as introspection

@pytest.fixture(autouse=True)
def _restore_deal_state():
    deal.reset()
    yield
    deal.reset()


def test_preserve_type_annotations():
    @deal.pre(lambda x: x > 0)
    def func(x: int) -> int:
        return x

    assert get_type_hints(func) == {'x': int, 'return': int}


def test_preserve_docstring():
    @deal.post(lambda result: result > 0)
    def func(x):
        """kept documentation"""
        return x

    assert inspect.getdoc(func) == 'kept documentation'


def test_implies():
    assert deal.implies(False, object()) is True
    marker = object()
    assert deal.implies(True, marker) is marker


def test_catch():
    def divide(x, y):
        return x / y

    assert deal.catch(divide, 4, 2) is None
    assert deal.catch(divide, 1, y=0) is ZeroDivisionError


def test_unwrap():
    def func(x):
        return x * 2

    wrapped = deal.pre(lambda x: x > 0)(func)
    assert deal.introspection.unwrap(wrapped) is func
    assert deal.introspection.unwrap(func) is func


def test_get_contracts__raises():
    @deal.raises(ZeroDivisionError, ValueError)
    def func():
        return None

    contract = next(deal.introspection.get_contracts(func))
    assert isinstance(contract, deal.introspection.Raises)
    assert contract.exceptions == (ZeroDivisionError, ValueError)


def test_get_contracts__reason():
    @deal.reason(ValueError, lambda x: x > 0)
    def func(x):
        return x

    contract = next(deal.introspection.get_contracts(func))
    assert isinstance(contract, deal.introspection.Reason)
    assert contract.event is ValueError


def test_simple_signature():
    @deal.ensure(lambda _: _.left > 0 and _.result > _.left)
    def func(left, step=1):
        return left + step

    assert func(2) == 3
    with pytest.raises(deal.PostContractError):
        func(2, -1)


def test_example_is_not_triggered_in_runtime():
    @deal.example(lambda: False)
    def func():
        return True

    assert func() is True


def test_return_value_fulfils_contract():
    func = deal.post(lambda result: result > 0)(lambda x: -x)
    assert func(-4) == 4
    with pytest.raises(deal.PostContractError):
        func(4)


def test_pre_contract_fulfilled():
    func = deal.pre(lambda x: x > 0)(lambda x: x)
    assert func(2) == 2
    with pytest.raises(deal.PreContractError):
        func(-2)


def test_method_decoration_name_is_correct():
    @deal.pre(lambda x: x > 0)
    def some_function(x):
        return x

    assert some_function.__name__ == 'some_function'


def test_safe():
    func = deal.safe(lambda x: 1 / x)
    assert func(2) == 0.5
    with pytest.raises(deal.RaisesContractError):
        func(0)


def test_generated_root_runtime_exports_are_usable():
    names = (
        "pre",
        "post",
        "ensure",
        "inv",
        "raises",
        "reason",
        "has",
        "example",
        "chain",
        "inherit",
        "dispatch",
        "safe",
        "pure",
        "catch",
        "implies",
        "disable",
        "enable",
        "reset",
    )
    assert all(callable(getattr(deal, name)) for name in names)
    assert deal.implies(False, object()) is True
    assert deal.implies(True, 7) == 7
    assert deal.catch(lambda: None) is None
    assert deal.catch(lambda: (_ for _ in ()).throw(ValueError())) is ValueError


def test_generated_root_exception_exports_match_decorator_failures():
    deal.reset()
    try:
        @deal.pre(lambda value: value > 0)
        def positive(value):
            return value

        @deal.post(lambda result: result > 0)
        def negative():
            return -1

        with pytest.raises(deal.PreContractError) as pre_failure:
            positive(0)
        assert type(pre_failure.value) is deal.PreContractError

        with pytest.raises(deal.PostContractError) as post_failure:
            negative()
        assert type(post_failure.value) is deal.PostContractError
    finally:
        deal.reset()
