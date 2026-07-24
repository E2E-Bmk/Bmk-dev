"""Atomic public-API behavioral tests for deal.

Each test exercises a single public API entry point and a single behavior.
Tests that cross decorator ↔ introspection or decorator ↔ state-control
boundaries belong in test_integration.py.
"""
import asyncio
import inspect
import socket
from typing import get_type_hints

import pytest
import deal


# ── pre decorator ─────────────────────────────────────────────────

def test_pre_rejects_invalid_argument():
    func = deal.pre(lambda x: x > 0)(lambda x: x)
    assert func(2) == 2
    with pytest.raises(deal.PreContractError):
        func(-2)


def test_pre_string_result_becomes_violation_description():
    @deal.pre(lambda x: "must be positive" if x <= 0 else True)
    def guarded(x):
        return x

    assert guarded(5) == 5
    with pytest.raises(deal.PreContractError):
        guarded(-3)


def test_pre_preserves_function_name():
    @deal.pre(lambda x: x > 0)
    def some_function(x):
        return x

    assert some_function.__name__ == "some_function"


def test_pre_preserves_type_annotations():
    @deal.pre(lambda x: x > 0)
    def func(x: int) -> int:
        return x

    assert get_type_hints(func) == {"x": int, "return": int}


def test_pre_on_class_method():
    class Number:
        @deal.pre(lambda self, x: x > 0)
        def double(self, x):
            return x * 2

    assert Number().double(2) == 4
    with pytest.raises(deal.PreContractError):
        Number().double(-2)


def test_pre_stacking_same_kind_ordering():
    @deal.pre(lambda x: x > 0)
    @deal.pre(lambda x: x < 10)
    def func(x):
        return x

    assert func(5) == 5
    with pytest.raises(deal.PreContractError):
        func(-1)
    with pytest.raises(deal.PreContractError):
        func(20)


# ── post decorator ────────────────────────────────────────────────

def test_post_rejects_invalid_return_value():
    func = deal.post(lambda result: result > 0)(lambda x: -x)
    assert func(-4) == 4
    with pytest.raises(deal.PostContractError):
        func(4)


def test_post_preserves_docstring():
    @deal.post(lambda result: result > 0)
    def func(x):
        """kept documentation"""
        return x

    assert inspect.getdoc(func) == "kept documentation"


def test_post_on_generator_validates_each_yield():
    @deal.post(lambda value: value < 5)
    def values():
        yield 1
        yield 6

    iterator = values()
    assert next(iterator) == 1
    with pytest.raises(deal.PostContractError):
        next(iterator)


# ── ensure decorator ──────────────────────────────────────────────

def test_ensure_validates_arguments_and_result():
    @deal.ensure(lambda a, b, result: a > 0 and b > 0 and result != "same")
    def func(a, b):
        return "same" if a == b else "different"

    assert func(1, 2) == "different"
    with pytest.raises(deal.PostContractError):
        func(1, 1)


def test_ensure_underscore_shorthand_includes_result():
    @deal.ensure(lambda _: _.left > 0 and _.result > _.left)
    def func(left, step=1):
        return left + step

    assert func(2) == 3
    with pytest.raises(deal.PostContractError):
        func(2, -1)


# ── inv decorator ─────────────────────────────────────────────────

def test_inv_rejects_invalid_attribute_assignment():
    @deal.inv(lambda obj: obj.value > 0)
    class Value:
        value = 2

        def set(self, new):
            self.value = new

    item = Value()
    with pytest.raises(deal.InvContractError):
        item.set(-2)
    assert item.value == -2


def test_inv_multiple_invariants_check_all():
    @deal.inv(lambda obj: obj.value > 0)
    @deal.inv(lambda obj: obj.value < 10)
    class Value:
        value = 2

    item = Value()
    with pytest.raises(deal.InvContractError):
        item.value = -1
    with pytest.raises(deal.InvContractError):
        item.value = 20


def test_inv_with_slots():
    @deal.inv(lambda obj: obj.value > 0)
    class Value:
        __slots__ = ("value",)

        def __init__(self):
            self.value = 2

    item = Value()
    item.value = 4
    assert item.value == 4
    with pytest.raises(deal.InvContractError):
        item.value = -2


# ── raises decorator ─────────────────────────────────────────────

def test_raises_allows_declared_exception():
    @deal.raises(ZeroDivisionError)
    def func(x):
        return 1 / x

    assert func(2) == 0.5
    with pytest.raises(ZeroDivisionError):
        func(0)


def test_raises_wraps_undeclared_exception():
    @deal.raises(KeyError)
    def wrong(x):
        return 1 / x

    with pytest.raises(deal.RaisesContractError) as exc_info:
        wrong(0)
    assert isinstance(exc_info.value.__cause__, ZeroDivisionError)


# ── reason decorator ──────────────────────────────────────────────

def test_reason_passing_preserves_original_exception():
    @deal.reason(ValueError, lambda code: code > 0)
    def checked(code):
        raise ValueError("test")

    with pytest.raises(ValueError):
        checked(5)


def test_reason_failing_raises_reason_contract_error():
    @deal.reason(ValueError, lambda code: code > 0)
    def reject(code):
        raise ValueError()

    with pytest.raises(deal.ReasonContractError) as caught:
        reject(-1)
    assert type(caught.value.__cause__) is ValueError


# ── has decorator ─────────────────────────────────────────────────

def test_has_empty_blocks_socket():
    @deal.has()
    def func():
        socket.socket()

    with pytest.raises(deal.OfflineContractError):
        func()


def test_has_custom_exception_replaces_default():
    class CustomError(Exception):
        pass

    @deal.has(exception=CustomError)
    def func():
        socket.socket()

    with pytest.raises(CustomError):
        func()


def test_has_empty_blocks_stdout():
    @deal.has()
    def func(write):
        if write:
            print("blocked")

    func(False)
    with pytest.raises(deal.SilentContractError):
        func(True)


# ── safe and pure ─────────────────────────────────────────────────

def test_safe_rejects_every_exception():
    func = deal.safe(lambda x: 1 / x)
    assert func(2) == 0.5
    with pytest.raises(deal.RaisesContractError):
        func(0)


# ── example decorator ────────────────────────────────────────────

def test_example_is_not_triggered_in_runtime():
    @deal.example(lambda: False)
    def func():
        return True

    assert func() is True


def test_example_does_not_break_generator():
    @deal.example(lambda: False)
    def func():
        yield True

    assert list(func()) == [True]


def test_example_does_not_break_async():
    @deal.example(lambda: False)
    async def func():
        return True

    assert asyncio.run(func()) is True


# ── Helper functions ──────────────────────────────────────────────

def test_implies():
    assert deal.implies(False, object()) is True
    marker = object()
    assert deal.implies(True, marker) is marker


def test_catch():
    def divide(x, y):
        return x / y

    assert deal.catch(divide, 4, 2) is None
    assert deal.catch(divide, 1, y=0) is ZeroDivisionError


# ── Import surface ───────────────────────────────────────────────

def test_root_runtime_exports_are_callable():
    names = (
        "pre", "post", "ensure", "inv", "raises", "reason", "has",
        "example", "chain", "inherit", "dispatch", "safe", "pure",
        "catch", "implies", "disable", "enable", "reset",
    )
    assert all(callable(getattr(deal, name)) for name in names)


def test_root_exception_hierarchy():
    assert issubclass(deal.ContractError, AssertionError)
    assert issubclass(deal.PreContractError, deal.ContractError)
    assert issubclass(deal.PostContractError, deal.ContractError)
    assert issubclass(deal.InvContractError, deal.ContractError)
    assert issubclass(deal.RaisesContractError, deal.ContractError)
    assert issubclass(deal.ReasonContractError, deal.ContractError)
    assert issubclass(deal.OfflineContractError, deal.ContractError)
    assert issubclass(deal.SilentContractError, deal.ContractError)
    assert not issubclass(deal.NoMatchError, deal.ContractError)
