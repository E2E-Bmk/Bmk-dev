# Spec2Repo oracle - integration tests for deal

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


def test_chained_contract_decorator():
    @deal.chain(deal.pre(lambda x: x != 1), deal.pre(lambda x: x != 2))
    def func(x):
        return x * 4

    assert func(3) == 12
    with pytest.raises(deal.PreContractError):
        func(1)
    with pytest.raises(deal.PreContractError):
        func(2)


def test_get_contracts__pre():
    def validator(x):
        return x > 0

    @deal.pre(validator)
    def func(x):
        return x * 2

    contract = next(deal.introspection.get_contracts(func))
    assert isinstance(contract, deal.introspection.Pre)
    assert contract.validate(2) is None
    with pytest.raises(deal.PreContractError):
        contract.validate(-1)
    assert contract.exception is deal.PreContractError
    assert contract.exception_type is deal.PreContractError
    assert contract.source == 'validator'


def test_custom_exception_and_message():
    @deal.pre(lambda x: x > 0, exception=ValueError, message='positive')
    def func(x):
        return x

    contract = next(deal.introspection.get_contracts(func))
    assert type(contract.exception) is ValueError
    assert contract.exception_type is ValueError
    assert contract.message == 'positive'
    with pytest.raises(ValueError):
        func(0)


def test_get_contracts__has():
    @deal.has('io', 'database')
    def func():
        return None

    contract = next(deal.introspection.get_contracts(func))
    assert isinstance(contract, deal.introspection.Has)
    assert contract.markers == frozenset({'io', 'database'})
    assert contract.exception_type is deal.MarkerError


def test_get_contracts__multiple():
    @deal.pre(lambda x: x > 0)
    @deal.post(lambda result: result > 1)
    @deal.ensure(lambda x, result: result > x)
    def func(x):
        return x * 2

    contracts = list(deal.introspection.get_contracts(func))
    assert [type(item) for item in contracts] == [
        deal.introspection.Pre,
        deal.introspection.Post,
        deal.introspection.Ensure,
    ]


def test_get_contracts__example():
    @deal.example(lambda: func(3) == 6)
    def func(x):
        return x * 2

    contract = next(deal.introspection.get_contracts(func))
    assert isinstance(contract, deal.introspection.Example)
    assert contract.validate() is None


def test_get_contracts__inherit_class():
    class Base:
        @deal.has('base')
        def method(self):
            raise NotImplementedError

    @deal.inherit
    class Child(Base):
        def method(self):
            return 2

    contract = next(deal.introspection.get_contracts(Child().method))
    assert contract.markers == frozenset({'base'})


def test_get_contracts__inherit_func():
    class Base:
        @deal.pre(lambda self, x: x > 0)
        def method(self, x):
            raise NotImplementedError

    class Child(Base):
        @deal.inherit
        def method(self, x):
            return x * 2

    contracts = list(deal.introspection.get_contracts(Child().method))
    assert len(contracts) == 1
    assert isinstance(contracts[0], deal.introspection.Pre)


def test_match():
    @deal.dispatch
    def choose(x):
        """choose a branch"""

    @choose.register
    @deal.pre(lambda x: x < 0)
    def negative(x):
        return 'negative'

    @choose.register
    @deal.pre(lambda x: x >= 0)
    def nonnegative(x):
        return 'nonnegative'

    assert choose(-1) == 'negative'
    assert choose(0) == 'nonnegative'


def test_no_match():
    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x > 10)
    def large(x):
        return x

    with pytest.raises(deal.NoMatchError):
        choose(1)


def test_match_default():
    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x < 0)
    def negative(x):
        return 'negative'

    @choose.register
    def fallback(x):
        return 'default'

    assert choose(5) == 'default'


def test_propagate_pre_contract_error():
    @deal.pre(lambda x: x > 0)
    def nested(x):
        return x

    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x < 5)
    def selected(x):
        return nested(x)

    with pytest.raises(deal.PreContractError):
        choose(-1)


def test_dispatch_works_with_disabled_contracts():
    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x < 0)
    def negative(x):
        return 'negative'

    @choose.register
    @deal.pre(lambda x: x >= 0)
    def positive(x):
        return 'positive'

    deal.disable(warn=False)
    assert choose(-1) == 'negative'
    assert choose(1) == 'positive'


def test_parameters_and_result_fulfill_constact():
    @deal.ensure(lambda a, b, result: a > 0 and b > 0 and result != 'same')
    def func(a, b):
        return 'same' if a == b else 'different'

    assert func(1, 2) == 'different'
    with pytest.raises(deal.PostContractError):
        func(1, 1)


def test_recursive_contracts_ok():
    @deal.ensure(lambda a, b, result: add(result, b) == a)
    def subtract(a, b):
        return a - b

    @deal.ensure(lambda a, b, result: subtract(result, b) == a)
    def add(a, b):
        return a + b

    assert subtract(5, 3) == 2
    assert add(2, 3) == 5


def test_example_does_not_break_iterator():
    @deal.example(lambda: False)
    def func():
        yield True

    assert list(func()) == [True]


def test_example_does_not_break_async():
    @deal.example(lambda: False)
    async def func():
        return True

    assert asyncio.run(func()) is True


def test_inherit_one_parent():
    class Base:
        @deal.pre(lambda self, x: x == 3)
        def method(self, x):
            raise NotImplementedError

    class Child(Base):
        @deal.inherit
        def method(self, x):
            return x * 2

    assert Child().method(3) == 6
    with pytest.raises(deal.PreContractError):
        Child().method(4)


def test_inherit_multiple_parents():
    class Base:
        @deal.pre(lambda self, x: x > 0)
        def method(self, x):
            raise NotImplementedError

    class Middle(Base):
        @deal.pre(lambda self, x: x < 5)
        def method(self, x):
            raise NotImplementedError

    class Child(Middle):
        @deal.inherit
        def method(self, x):
            return x * 2

    assert Child().method(3) == 6
    with pytest.raises(deal.PreContractError):
        Child().method(-1)
    with pytest.raises(deal.PreContractError):
        Child().method(8)


def test_has_inherit_and_merge():
    class Base:
        @deal.has('stdout')
        def method(self):
            raise NotImplementedError

    @deal.inherit
    class Child(Base):
        @deal.has('stderr')
        def method(self):
            return None

    contract = next(deal.introspection.get_contracts(Child().method))
    assert contract.markers == frozenset({'stdout', 'stderr'})


def test_setting_wrong_args_by_method_raises_error():
    @deal.inv(lambda obj: obj.value > 0)
    class Value:
        value = 2

        def set(self, new):
            self.value = new

    item = Value()
    with pytest.raises(deal.InvContractError):
        item.set(-2)
    assert item.value == -2


def test_chain_contracts_both_fulfill():
    @deal.inv(lambda obj: obj.value > 0)
    @deal.inv(lambda obj: obj.value < 10)
    class Value:
        value = 2

    item = Value()
    with pytest.raises(deal.InvContractError):
        item.value = -1
    with pytest.raises(deal.InvContractError):
        item.value = 20


def test_patch_class_with_slots():
    @deal.inv(lambda obj: obj.value > 0)
    class Value:
        __slots__ = ('value',)

        def __init__(self):
            self.value = 2

    item = Value()
    item.value = 4
    assert item.value == 4
    with pytest.raises(deal.InvContractError):
        item.value = -2


def test_raises_exception():
    @deal.has()
    def func():
        socket.socket()

    with pytest.raises(deal.OfflineContractError):
        func()


def test_raises_specified_exception():
    class CustomError(Exception):
        pass

    @deal.has(exception=CustomError)
    def func():
        socket.socket()

    with pytest.raises(CustomError):
        func()


def test_decorating_generator():
    @deal.post(lambda value: value < 5)
    def values():
        yield 1
        yield 6

    iterator = values()
    assert next(iterator) == 1
    with pytest.raises(deal.PostContractError):
        next(iterator)


def test_chain_all_contracts_fulfilled():
    @deal.pre(lambda x: x > 0)
    @deal.pre(lambda x: x < 10)
    def func(x):
        return x

    assert func(5) == 5
    with pytest.raises(deal.PreContractError):
        func(-1)
    with pytest.raises(deal.PreContractError):
        func(20)


def test_class_method_decorator_raises_error_on_contract_fail():
    class Number:
        @deal.pre(lambda self, x: x > 0)
        def double(self, x):
            return x * 2

    assert Number().double(2) == 4
    with pytest.raises(deal.PreContractError):
        Number().double(-2)


def test_pure_silent():
    @deal.pure
    def func(write):
        if write:
            print('blocked')

    func(False)
    with pytest.raises(deal.SilentContractError):
        func(True)


def test_pure_safe():
    func = deal.pure(lambda x: 1 / x)
    assert func(2) == 0.5
    with pytest.raises(deal.RaisesContractError):
        func(0)


def test_raises_expects_function_to_raise_error():
    @deal.raises(ZeroDivisionError)
    def func(x):
        return 1 / x

    assert func(2) == 0.5
    with pytest.raises(ZeroDivisionError):
        func(0)

    @deal.raises(KeyError)
    def wrong(x):
        return 1 / x

    with pytest.raises(deal.RaisesContractError) as exc_info:
        wrong(0)
    assert isinstance(exc_info.value.__cause__, ZeroDivisionError)


def test_not_allow_print():
    @deal.has()
    def func(write):
        if write:
            print('blocked')

    func(False)
    with pytest.raises(deal.SilentContractError):
        func(True)


def test_contract_state_switch_custom_param():
    @deal.pre(lambda x: x > 0)
    def func(x):
        return x

    deal.disable(warn=False)
    assert func(-1) == -1
    deal.enable(warn=False)
    with pytest.raises(deal.PreContractError):
        func(-1)


def test_contract_state_switch_default_param_async():
    @deal.pre(lambda x: x > 0)
    async def func(x):
        return x * 2

    deal.disable(warn=False)
    assert asyncio.run(func(-2)) == -4
    deal.enable(warn=False)
    with pytest.raises(deal.PreContractError):
        asyncio.run(func(-2))


def test_contract_state_switch_default_param_generator():
    @deal.post(lambda x: x > 0)
    def func():
        yield -1

    deal.disable(warn=False)
    assert list(func()) == [-1]
    deal.enable(warn=False)
    with pytest.raises(deal.PostContractError):
        list(func())


def test_generated_introspection_namespace_operates_independently():
    namespace = importlib.import_module("deal.introspection")
    names = (
        "get_contracts",
        "init_all",
        "unwrap",
        "Contract",
        "ValidatedContract",
        "Pre",
        "Post",
        "Ensure",
        "Example",
        "Raises",
        "Reason",
        "Has",
    )
    assert all(hasattr(namespace, name) for name in names)

    def original(value):
        return value

    decorated = deal.pre(lambda value: value > 0)(original)
    contracts = list(namespace.get_contracts(decorated))
    assert len(contracts) == 1
    assert type(contracts[0]) is namespace.Pre
    assert namespace.unwrap(decorated) is original


def test_generated_disabled_decoration_reappears_in_all_views():
    deal.reset()
    try:
        deal.disable(warn=False)

        @deal.pre(lambda value: value > 0, exception=LookupError)
        def guarded(value):
            return value

        contracts = list(introspection.get_contracts(guarded))
        assert guarded(-3) == -3
        assert len(contracts) == 1
        assert type(contracts[0]) is introspection.Pre
        assert contracts[0].exception is LookupError
        assert contracts[0].exception_type is LookupError

        deal.enable(warn=False)
        with pytest.raises(LookupError):
            guarded(-3)
    finally:
        deal.reset()


def test_generated_retained_contract_and_unwrap_survive_disable():
    deal.reset()
    try:
        def original(value):
            return value - 1

        guarded = deal.post(lambda result: result >= 0)(original)
        contract = list(introspection.get_contracts(guarded))[0]
        assert guarded(2) == 1
        assert introspection.unwrap(guarded) is original

        deal.disable(warn=False)
        assert guarded(0) == -1
        retained = list(introspection.get_contracts(guarded))
        assert len(retained) == 1
        assert type(retained[0]) is type(contract)
        assert retained[0].exception_type is contract.exception_type
        assert introspection.unwrap(guarded) is original
    finally:
        deal.reset()


def test_generated_inherited_precondition_matches_bound_metadata():
    deal.reset()
    try:
        class Base:
            @deal.pre(lambda self, value: value > 0)
            def scale(self, value):
                return value

        class Child(Base):
            @deal.inherit
            def scale(self, value):
                return value * 3

        item = Child()
        assert item.scale(2) == 6
        contracts = list(introspection.get_contracts(item.scale))
        assert len(contracts) == 1
        assert type(contracts[0]) is introspection.Pre
        with pytest.raises(deal.PreContractError):
            item.scale(-1)
    finally:
        deal.reset()


def test_generated_sync_fee_lifecycle_workflow():
    deal.reset()
    try:
        @deal.pre(lambda amount: amount > 0)
        @deal.ensure(lambda amount, result: result < amount)
        def apply_fee(amount):
            return amount - 1

        assert apply_fee(5) == 4
        contracts = list(introspection.get_contracts(apply_fee))
        assert [type(contract) for contract in contracts] == [
            introspection.Pre,
            introspection.Ensure,
        ]

        deal.disable(warn=False)
        assert apply_fee(-2) == -3
        retained = list(introspection.get_contracts(apply_fee))
        assert [type(contract) for contract in retained] == [
            introspection.Pre,
            introspection.Ensure,
        ]

        deal.enable(warn=False)
        with pytest.raises(deal.PreContractError):
            apply_fee(-2)
    finally:
        deal.reset()


def test_generated_async_result_lifecycle_workflow():
    deal.reset()
    try:
        @deal.post(lambda result: result > 0)
        async def read_value(value):
            return value

        assert asyncio.run(read_value(4)) == 4
        contracts = list(introspection.get_contracts(read_value))
        assert len(contracts) == 1
        assert type(contracts[0]) is introspection.Post

        deal.disable(warn=False)
        assert asyncio.run(read_value(-4)) == -4
        retained = list(introspection.get_contracts(read_value))
        assert len(retained) == 1
        assert type(retained[0]) is introspection.Post

        deal.enable(warn=False)
        with pytest.raises(deal.PostContractError):
            asyncio.run(read_value(-4))
    finally:
        deal.reset()


def test_generated_exception_policy_lifecycle_workflow():
    deal.reset()
    try:
        @deal.raises(ValueError)
        def choose_failure(kind):
            if kind == "value":
                raise ValueError()
            if kind == "key":
                raise KeyError()
            return 8

        assert choose_failure("none") == 8
        contracts = list(introspection.get_contracts(choose_failure))
        assert len(contracts) == 1
        assert type(contracts[0]) is introspection.Raises
        assert contracts[0].exceptions == (ValueError,)

        deal.disable(warn=False)
        with pytest.raises(KeyError):
            choose_failure("key")
        retained = list(introspection.get_contracts(choose_failure))
        assert len(retained) == 1
        assert type(retained[0]) is introspection.Raises
        assert retained[0].exceptions == (ValueError,)

        deal.enable(warn=False)
        with pytest.raises(deal.RaisesContractError) as caught:
            choose_failure("key")
        assert type(caught.value.__cause__) is KeyError
    finally:
        deal.reset()


def test_generated_custom_exception_class_and_instance_control_violation_type():
    deal.reset()
    try:
        class ClassViolation(Exception):
            pass

        class InstanceViolation(Exception):
            pass

        configured_instance = InstanceViolation(9)

        @deal.pre(lambda value: value > 0, exception=ClassViolation)
        def class_guarded(value):
            return value

        @deal.ensure(
            lambda value, result: result > value,
            exception=configured_instance,
        )
        def instance_guarded(value):
            return value

        with pytest.raises(ClassViolation) as class_failure:
            class_guarded(0)
        assert type(class_failure.value) is ClassViolation

        with pytest.raises(InstanceViolation) as instance_failure:
            instance_guarded(1)
        assert type(instance_failure.value) is InstanceViolation
    finally:
        deal.reset()


def test_generated_reason_violation_preserves_cause_type():
    @deal.reason(ValueError, lambda code: code > 0)
    def reject(code):
        raise ValueError()

    with pytest.raises(deal.ReasonContractError) as caught:
        reject(-1)
    assert type(caught.value.__cause__) is ValueError


def test_generated_permanent_transitions_raise_runtime_error_in_child():
    program = """
import deal
import deal.introspection as introspection

deal.disable(permament=True, warn=False)

for transition in (
    lambda: deal.enable(warn=False),
    deal.reset,
    lambda: deal.disable(permament=True, warn=False),
):
    try:
        transition()
    except RuntimeError:
        pass
    else:
        raise AssertionError

@deal.pre(lambda value: value > 0)
def unguarded(value):
    return value

assert unguarded(-1) == -1
assert list(introspection.get_contracts(unguarded)) == []
"""
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
