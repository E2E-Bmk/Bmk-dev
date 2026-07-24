"""Integration tests for deal.

Each test exercises ≥2 public API boundaries (decorator ↔ introspection,
decorator ↔ state control, composition decorators, etc.) or validates
cross-view invariants.
"""
import asyncio
import importlib
import subprocess
import sys

import pytest
import deal
import deal.introspection as introspection


# ── CVI-1: decorator visible through introspection ────────────────

@pytest.mark.depends_on("test_pre_rejects_invalid_argument")
def test_get_contracts_pre_metadata():
    """CVI-1: pre contract visible through introspection metadata."""
    def validator(x):
        return x > 0

    @deal.pre(validator)
    def func(x):
        return x * 2

    contract = next(introspection.get_contracts(func))
    assert isinstance(contract, introspection.Pre)
    assert contract.validate(2) is None
    with pytest.raises(deal.PreContractError):
        contract.validate(-1)
    assert contract.exception is deal.PreContractError
    assert contract.exception_type is deal.PreContractError
    assert contract.source == "validator"


@pytest.mark.depends_on("test_raises_allows_declared_exception")
def test_get_contracts_raises_metadata():
    """CVI-1: raises contract visible through introspection metadata."""
    @deal.raises(ZeroDivisionError, ValueError)
    def func():
        return None

    contract = next(introspection.get_contracts(func))
    assert isinstance(contract, introspection.Raises)
    assert contract.exceptions == (ZeroDivisionError, ValueError)


@pytest.mark.depends_on("test_reason_failing_raises_reason_contract_error")
def test_get_contracts_reason_metadata():
    """CVI-1: reason contract visible through introspection metadata."""
    @deal.reason(ValueError, lambda x: x > 0)
    def func(x):
        return x

    contract = next(introspection.get_contracts(func))
    assert isinstance(contract, introspection.Reason)
    assert contract.event is ValueError


@pytest.mark.depends_on("test_has_empty_blocks_socket")
def test_get_contracts_has_metadata():
    """CVI-1: has contract visible through introspection metadata."""
    @deal.has("io", "database")
    def func():
        return None

    contract = next(introspection.get_contracts(func))
    assert isinstance(contract, introspection.Has)
    assert contract.markers == frozenset({"io", "database"})
    assert contract.exception_type is deal.MarkerError


def test_get_contracts_multiple_kinds_in_order():
    """CVI-1: multiple contract kinds exposed in decoration order."""
    @deal.pre(lambda x: x > 0)
    @deal.post(lambda result: result > 1)
    @deal.ensure(lambda x, result: result > x)
    def func(x):
        return x * 2

    contracts = list(introspection.get_contracts(func))
    assert [type(item) for item in contracts] == [
        introspection.Pre, introspection.Post, introspection.Ensure,
    ]


def test_get_contracts_example_validate():
    """CVI-1: example contract validate exposed through introspection."""
    @deal.example(lambda: func(3) == 6)
    def func(x):
        return x * 2

    contract = next(introspection.get_contracts(func))
    assert isinstance(contract, introspection.Example)
    assert contract.validate() is None


# ── CVI-2: custom exception visible through wrapper ──────────────

@pytest.mark.depends_on("test_pre_rejects_invalid_argument")
def test_custom_exception_and_message_visible_in_metadata():
    """CVI-2: custom exception and message visible in metadata."""
    @deal.pre(lambda x: x > 0, exception=ValueError, message="positive")
    def func(x):
        return x

    contract = next(introspection.get_contracts(func))
    assert type(contract.exception) is ValueError
    assert contract.exception_type is ValueError
    assert contract.message == "positive"
    with pytest.raises(ValueError):
        func(0)


# ── CVI-7: unwrap returns original ───────────────────────────────

@pytest.mark.depends_on("test_pre_rejects_invalid_argument")
def test_unwrap_returns_original():
    """CVI-7: unwrap returns original undecorated function."""
    def func(x):
        return x * 2

    wrapped = deal.pre(lambda x: x > 0)(func)
    assert introspection.unwrap(wrapped) is func
    assert introspection.unwrap(func) is func


# ── chain composition ────────────────────────────────────────────

def test_chained_contract_decorator():
    """Seam: lifecycle crossing — chained pre contracts compose on one function."""
    @deal.chain(deal.pre(lambda x: x != 1), deal.pre(lambda x: x != 2))
    def func(x):
        return x * 4

    assert func(3) == 12
    with pytest.raises(deal.PreContractError):
        func(1)
    with pytest.raises(deal.PreContractError):
        func(2)


# ── pure composition: has() + safe ────────────────────────────────

def test_pure_blocks_stdout_and_exceptions():
    """Seam: error propagation — pure blocks stdout and undeclared exceptions."""
    @deal.pure
    def func(write):
        if write:
            print("blocked")

    func(False)
    with pytest.raises(deal.SilentContractError):
        func(True)

    func2 = deal.pure(lambda x: 1 / x)
    assert func2(2) == 0.5
    with pytest.raises(deal.RaisesContractError):
        func2(0)


# ── dispatch ──────────────────────────────────────────────────────

def test_dispatch_selects_by_precondition():
    """Seam: protocol handoff — dispatch selects branch by precondition."""
    @deal.dispatch
    def choose(x):
        """choose a branch"""

    @choose.register
    @deal.pre(lambda x: x < 0)
    def negative(x):
        return "negative"

    @choose.register
    @deal.pre(lambda x: x >= 0)
    def nonnegative(x):
        return "nonnegative"

    assert choose(-1) == "negative"
    assert choose(0) == "nonnegative"


def test_dispatch_no_match_raises():
    """Seam: error propagation — dispatch with no match raises NoMatchError."""
    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x > 10)
    def large(x):
        return x

    with pytest.raises(deal.NoMatchError):
        choose(1)


def test_dispatch_default_registration():
    """Seam: protocol handoff — dispatch default registration catches unmatched calls."""
    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x < 0)
    def negative(x):
        return "negative"

    @choose.register
    def fallback(x):
        return "default"

    assert choose(5) == "default"


def test_dispatch_propagates_pre_contract_error_from_body():
    """Seam: error propagation — dispatch propagates pre contract error from body."""
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
    """Seam: config interaction — dispatch works while contracts disabled."""
    @deal.dispatch
    def choose(x):
        pass

    @choose.register
    @deal.pre(lambda x: x < 0)
    def negative(x):
        return "negative"

    @choose.register
    @deal.pre(lambda x: x >= 0)
    def positive(x):
        return "positive"

    deal.disable(warn=False)
    assert choose(-1) == "negative"
    assert choose(1) == "positive"


# ── Recursive contract avoidance ──────────────────────────────────

def test_recursive_contracts_do_not_recurse():
    """Seam: error propagation — mutually referencing contracts do not recurse."""
    @deal.ensure(lambda a, b, result: add(result, b) == a)
    def subtract(a, b):
        return a - b

    @deal.ensure(lambda a, b, result: subtract(result, b) == a)
    def add(a, b):
        return a + b

    assert subtract(5, 3) == 2
    assert add(2, 3) == 5


# ── inherit ──────────────────────────────────────────────────────

def test_inherit_one_parent():
    """Seam: lifecycle crossing — inherit applies parent precondition to child method."""
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
    """Seam: lifecycle crossing — inherit merges multiple parent preconditions."""
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


# ── CVI-5: inherited contract visible through get_contracts ──────

def test_inherit_class_exposes_contracts_through_introspection():
    """CVI-5: inherited class contracts visible through introspection."""
    class Base:
        @deal.has("base")
        def method(self):
            raise NotImplementedError

    @deal.inherit
    class Child(Base):
        def method(self):
            return 2

    contract = next(introspection.get_contracts(Child().method))
    assert contract.markers == frozenset({"base"})


def test_inherit_func_exposes_contracts_through_introspection():
    """CVI-5: inherited method contracts visible through introspection."""
    class Base:
        @deal.pre(lambda self, x: x > 0)
        def method(self, x):
            raise NotImplementedError

    class Child(Base):
        @deal.inherit
        def method(self, x):
            return x * 2

    contracts = list(introspection.get_contracts(Child().method))
    assert len(contracts) == 1
    assert isinstance(contracts[0], introspection.Pre)


# ── CVI-6: has markers runtime == introspection markers ──────────

def test_has_inherit_and_merge_markers():
    """CVI-6: inherit merges has markers in introspection view."""
    class Base:
        @deal.has("stdout")
        def method(self):
            raise NotImplementedError

    @deal.inherit
    class Child(Base):
        @deal.has("stderr")
        def method(self):
            return None

    contract = next(introspection.get_contracts(Child().method))
    assert contract.markers == frozenset({"stdout", "stderr"})


# ── CVI-3: disable/enable preserves metadata ─────────────────────

def test_contract_state_switch_sync():
    """CVI-3: disable and enable toggles sync contract enforcement."""
    @deal.pre(lambda x: x > 0)
    def func(x):
        return x

    deal.disable(warn=False)
    assert func(-1) == -1
    deal.enable(warn=False)
    with pytest.raises(deal.PreContractError):
        func(-1)


def test_contract_state_switch_async():
    """CVI-3: disable and enable toggles async contract enforcement."""
    @deal.pre(lambda x: x > 0)
    async def func(x):
        return x * 2

    deal.disable(warn=False)
    assert asyncio.run(func(-2)) == -4
    deal.enable(warn=False)
    with pytest.raises(deal.PreContractError):
        asyncio.run(func(-2))


def test_contract_state_switch_generator():
    """CVI-3: disable and enable toggles generator contract enforcement."""
    @deal.post(lambda x: x > 0)
    def func():
        yield -1

    deal.disable(warn=False)
    assert list(func()) == [-1]
    deal.enable(warn=False)
    with pytest.raises(deal.PostContractError):
        list(func())


# ── CVI-3: disabled decoration reappears after enable ─────────────

def test_disabled_decoration_reappears_in_all_views():
    """CVI-3: disabled decoration reappears after enable in all views."""
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


# ── CVI-7: retained contract + unwrap survive disable ─────────────

def test_retained_contract_and_unwrap_survive_disable():
    """CVI-7: retained contracts and unwrap survive disable."""
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


# ── CVI-5: inherited precondition matches bound metadata ─────────

def test_inherited_precondition_matches_bound_metadata():
    """CVI-5: inherited precondition matches bound method metadata."""
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


# ── Introspection namespace ──────────────────────────────────────

def test_introspection_namespace_operates_independently():
    """Seam: protocol handoff — introspection namespace operates independently."""
    namespace = importlib.import_module("deal.introspection")
    names = (
        "get_contracts", "init_all", "unwrap", "Contract",
        "ValidatedContract", "Pre", "Post", "Ensure",
        "Example", "Raises", "Reason", "Has",
    )
    assert all(hasattr(namespace, name) for name in names)

    def original(value):
        return value

    decorated = deal.pre(lambda value: value > 0)(original)
    contracts = list(namespace.get_contracts(decorated))
    assert len(contracts) == 1
    assert type(contracts[0]) is namespace.Pre
    assert namespace.unwrap(decorated) is original


# ── Custom exception class + instance projection ─────────────────

def test_custom_exception_class_and_instance_control_violation():
    """Seam: error propagation — custom exception class and instance control violations."""
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

    with pytest.raises(ClassViolation):
        class_guarded(0)
    with pytest.raises(InstanceViolation):
        instance_guarded(1)


# ── Representative workflow: sync fee lifecycle ──────────────────

def test_sync_fee_lifecycle_workflow():
    """Seam: lifecycle crossing — sync fee contracts survive disable and re-enable."""
    @deal.pre(lambda amount: amount > 0)
    @deal.ensure(lambda amount, result: result < amount)
    def apply_fee(amount):
        return amount - 1

    assert apply_fee(5) == 4
    contracts = list(introspection.get_contracts(apply_fee))
    assert [type(c) for c in contracts] == [introspection.Pre, introspection.Ensure]

    deal.disable(warn=False)
    assert apply_fee(-2) == -3
    retained = list(introspection.get_contracts(apply_fee))
    assert [type(c) for c in retained] == [introspection.Pre, introspection.Ensure]

    deal.enable(warn=False)
    with pytest.raises(deal.PreContractError):
        apply_fee(-2)


# ── Representative workflow: exception policy lifecycle ──────────

def test_exception_policy_lifecycle_workflow():
    """Seam: lifecycle crossing — raises policy survives disable and re-enable."""
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
    assert contracts[0].exceptions == (ValueError,)

    deal.disable(warn=False)
    with pytest.raises(KeyError):
        choose_failure("key")
    retained = list(introspection.get_contracts(choose_failure))
    assert retained[0].exceptions == (ValueError,)

    deal.enable(warn=False)
    with pytest.raises(deal.RaisesContractError) as caught:
        choose_failure("key")
    assert type(caught.value.__cause__) is KeyError


# ── CVI-4: permanent disable ─────────────────────────────────────

def test_permanent_transitions_raise_runtime_error():
    """CVI-4: permanent disable blocks further state transitions."""
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
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0
