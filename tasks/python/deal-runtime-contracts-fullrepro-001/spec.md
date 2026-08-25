# Deal Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Deal brings design-by-contract checks to ordinary Python callables and classes. Applications attach preconditions, result conditions, exception policies, side-effect markers, and invariants with decorators. The same contract facts drive runtime checks and a stable introspection interface, while process-wide controls turn checks on or off without changing callers.

## Non-Goals

- Property-based case generation, `TestCase`, memory checks, formal verification, and external validator libraries are excluded.
- Static analysis, flake8 integration, source transformation, stubs, Sphinx rendering, and command-specific CLI presentation are excluded.
- Module-load contracts and import hooks are excluded.
- Private modules, private carrier attributes, internal state objects, generated subclass names, cache layout, and wrapper storage are excluded.
- Exact exception strings, `repr` output, traceback trimming, syntax coloring, and diagnostic formatting are excluded.
- Successful communication with a real remote network service is excluded; only local permission or rejection of a socket operation is covered.

## Representative Workflows

```python
import deal

@deal.pre(lambda amount: amount > 0)
@deal.ensure(lambda amount, result: result < amount)
def apply_fee(amount):
    return amount - 1

assert apply_fee(5) == 4
contracts = list(deal.introspection.get_contracts(apply_fee))
assert [type(item) for item in contracts] == [
    deal.introspection.Pre,
    deal.introspection.Ensure,
]

deal.disable(warn=False)
assert apply_fee(-2) == -3
assert len(list(deal.introspection.get_contracts(apply_fee))) == 2

deal.enable(warn=False)
try:
    apply_fee(-2)
except deal.PreContractError:
    pass
else:
    raise AssertionError("the precondition was not restored")
```

The workflow must retain one contract definition across runtime calls, metadata inspection, disabling, and re-enabling. If any projection loses or changes the definition, the corresponding assertion or exception check must fail.

```python
import deal

@deal.has("network")
@deal.raises(ConnectionError)
@deal.reason(ConnectionError, lambda _: _.retry < 3)
def fetch(url, retry=0):
    raise ConnectionError("timeout")

contracts = list(deal.introspection.get_contracts(fetch))
kinds = [type(c) for c in contracts]
assert deal.introspection.Has in kinds
assert deal.introspection.Raises in kinds
assert deal.introspection.Reason in kinds

has_contract = next(c for c in contracts if isinstance(c, deal.introspection.Has))
assert "network" in has_contract.markers

original = deal.introspection.unwrap(fetch)
assert original is not fetch
assert original.__name__ == "fetch"
```

## Validator Inputs and Outcomes

Validators are the callable predicates that define contract conditions, and their inputs and return values determine enforcement behavior.

**Argument binding.** A normal validator must receive the arguments appropriate to its contract: call arguments for `pre`, only the produced value for `post`, call arguments plus a `result` keyword for `ensure`, and the original call arguments for `reason`.

**Underscore shorthand.** A validator whose sole parameter is named `_` must instead receive an attribute-accessible mapping of the decorated callable's bound arguments, including defaults. For `ensure`, that mapping must include `result`.

**Validation outcomes.** A truthy validator result must satisfy the contract. A falsy result must raise the configured exception. A string result must fail validation and must become the call-specific description.

**Recursive contract avoidance.** During a recursive call from one contract validator into another decorated callable, Deal must avoid recursively enforcing contracts until the current validation finishes.

**Decorator transparency.** Decorated callables must preserve the original function's `__name__`, docstring, and type annotations.

## Values, Results, and Ordering

Contract decorators control when validation occurs and in what order multiple validators execute.

**Pre-condition timing.** `pre` must validate before the function body. A failed precondition must raise before the body produces side effects or a result.

**Post-condition timing.** `post` must validate the function's returned value after the body completes. `ensure` must validate the original arguments together with that returned value. Failed result validation must prevent the invalid result from reaching the caller.

**Same-kind ordering.** Within an ordinary source decorator stack, multiple validators of the same kind must run from the decorator nearest the function upward. If the first validator fails, its exception must be raised and later same-kind validators must not run. `post` validators must run before `ensure` validators when both kinds are present.

**Chain ordering.** Contracts passed to `chain(first, second, ...)` must be applied and enforced in argument order for same-kind validators.

**Custom exception and message.** Supplying `exception` to a supported decorator must replace its default violation type. Supplying `message` must set the violation's descriptive text. Supplying an exception instance must preserve that instance as the raised object.

## Generators and Asynchronous Functions

Contract decorators must handle generator and async functions with appropriate lifecycle integration.

**Generator decoration.** Calling a decorated generator function must return an iterator without running validators. Starting iteration must run preconditions before the first body step. Every yielded value must pass all `post` and `ensure` validators before reaching the caller. Function exceptions during iteration must follow `raises` and `reason` rules.

**Async decoration.** Calling a decorated asynchronous function must return an awaitable without running validators. Awaiting it must run preconditions before the body and must run `post` and `ensure` after the awaited body returns. Function exceptions while awaiting must follow `raises` and `reason` rules.

**Side-effect guards in generators and async.** `has` guards must remain active while a synchronous or asynchronous body executes and around each generator advancement.

## Exceptions and Reasons

Exception policy decorators control which exceptions a function may raise and validate conditions when specific exceptions occur.

**Raises policy.** `raises(*exceptions)` must allow a function exception only when its exact type occurs in the declared tuple. An allowed exception must propagate unchanged. An undeclared exception must be chained as the cause of `RaisesContractError`. `raises()` with no arguments and `safe` must reject every function exception. They must not replace a `ContractError` raised by another Deal contract.

**Reason validation.** `reason(event, validator)` must run the validator only when the function raises exactly the `event` type. A passing reason must preserve and re-raise the original event. A failing reason must raise `ReasonContractError` with the original event as its cause.

**Raises-then-reason ordering.** When both `raises` and `reason` are present, `raises` must check the exception allow-list first. An event absent from the allow-list must raise `RaisesContractError` without running any reason. An allowed matching event must proceed to reason validation.

## Side-Effect Markers

`has` decorators declare permitted side effects and enforce runtime guards against disallowed operations.

**Marker storage.** `has(*markers)` must preserve every marker string for introspection. Custom marker strings must remain metadata and must not invent a runtime guard.

**Network guard.** The `io`, `network`, and `socket` markers must permit creation of network sockets during the decorated body. Without any of those markers, a socket attempt must raise `OfflineContractError` or the custom marker exception.

**Output guard.** The `io`, `print`, and `stdout` markers must permit writes to standard output. The `io` and `stderr` markers must permit writes to standard error. Without the appropriate marker, output writes must raise `SilentContractError` or the custom marker exception.

**Stacking and inheritance.** Stacking more than one `has` decorator directly on one function must make the outer decorator's marker set effective. Inherited `has` contracts must merge base and child marker sets into their union.

**Custom exception.** Supplying `exception` to `has()` must replace the default marker exception type for that decorator's guard.

## Class Invariants

`inv` decorators attach invariants that must hold before and after public method execution and after attribute assignment.

**Instance compatibility.** `inv(validator)` must return a class whose instances remain instances of the original class, including classes with `__slots__`.

**Validation timing.** The invariant must validate before and after public method execution and after attribute assignment. A failed check must raise `InvContractError` or the configured replacement.

**Mutation persistence.** Invariant failure must not roll back mutation. If a method or assignment stores an invalid value before validation fails, the object must retain that value after the exception.

**Multiple invariants.** Applying multiple invariants must require every validator to pass. The first failing invariant must raise its configured exception.

## Dispatch and Inheritance

Dispatch enables multi-method selection by precondition, and inheritance propagates contracts from base classes.

**Dispatch creation.** `dispatch(func)` must return a callable dispatcher with a `register(function)` method. Registration must return the registered function so it remains directly callable.

**Dispatch selection.** On each dispatch call, registered implementations must be tried in registration order. The first implementation that returns without a direct `PreContractError` from its own preconditions must supply the result. If all registrations mismatch, the dispatcher must raise `NoMatchError`.

**Error propagation in dispatch.** A `PreContractError` raised inside a selected implementation's body or a nested call must propagate and must not be treated as a dispatch mismatch.

**Dispatch with disabled contracts.** Dispatch must temporarily enforce the registered implementations' preconditions even when global checks are disabled, then must restore the prior global state after return or failure.

**Default registration.** A registration without preconditions must match when reached; a failure raised by that implementation must propagate.

**Inheritance.** `inherit` must accept either an overriding method or a whole subclass. On first use of an inherited method, Deal must combine contracts from all applicable base implementations with contracts already attached on the child. For `has`, inheritance must return one effective marker set containing the union of base and child markers.

## Runtime Metadata and State Control

Introspection provides read access to attached contracts, while state functions control global enforcement.

**Example decorator.** `example(validator)` must attach an `Example` object visible through `get_contracts` and must not execute the example during ordinary function calls or generator/async iteration. Calling that wrapper's `validate()` must return `None` for a truthy example and must raise `ExampleContractError` for a false example.

**Contract enumeration.** `get_contracts` must enumerate attached wrappers in this kind order: all `Pre`, then `Post`, `Ensure`, `Raises`, `Reason`, `Example`, and finally one effective `Has`. Within a kind, it must preserve runtime order. A callable with no Deal contracts must return an empty iterator. `get_contracts` must follow decorator-wrapper links and must expose inherited contracts after inheritance is resolved.

**Wrapper attributes.** Each wrapper returned by `get_contracts` must expose `exception_type` (the exception class), `exception` (the configured exception class or instance), and `source` (a string identifying the validator). `Raises` wrappers must expose `exceptions` as a tuple of allowed exception types. `Reason` wrappers must expose `event` as the matched exception type. `Has` wrappers must expose `markers` as a `frozenset` of marker strings. `ValidatedContract` wrappers must expose a `validate()` method. Wrappers with a configured `message` must expose it as a string attribute.

**Unwrap.** `unwrap` must return the original callable regardless of whether retained contracts are currently enabled or disabled.

**Init.** `init_all` and wrapper `init()` must prepare validation metadata without calling the decorated body or changing whether the contract is enabled.

**Disable and enable.** `disable(warn=False)` must turn off contract enforcement. `enable(warn=False)` must restore contract enforcement. `reset()` must restore the interpreter-default contract state. The `warn` parameter controls whether a deprecation or state warning is emitted.

**Permanent disable.** `disable(permament=True, warn=False)` must permanently disable contract enforcement. After a permanent transition, calling `enable()`, `reset()`, or `disable(permament=True)` must raise `RuntimeError`. Contracts decorated after permanent disable must not enforce their validators and must not appear through `get_contracts`.

## State Model

Deal exposes one contract definition through three public projections:

1. The decorated callable or class enforces the definition when process state enables checks.
2. `deal.introspection` returns the definition's contract kind and configured metadata.
3. `enable`, `disable`, and `reset` control whether already-decorated callables enforce their retained definitions.

The projections must agree on these state rules:

- A contract attached while ordinary checks are disabled must remain visible through `get_contracts` and must become active after `enable()`.
- A contract attached before `disable()` must remain visible through `get_contracts` while its decorated callable returns unchecked results.
- A decoration performed after permanent removal must return a callable with no newly attached Deal contract, so `get_contracts` must return no wrapper for that attempted decoration.
- `unwrap` must return the original callable regardless of whether retained contracts are currently enabled or disabled.
- Inherited contracts must affect a child method at runtime and must appear on that same bound method through `get_contracts`.
- Metadata such as a configured exception, message, allowed exceptions, reason event, and markers must match the behavior configured by the corresponding decorator.

## Error Semantics

All value, example, reason, raises, and marker contract errors must inherit from `ContractError`, and `ContractError` must inherit from `AssertionError`. `NoMatchError` must remain a separate exception used only when dispatch exhausts its registrations.

| Trigger | Default result |
|---|---|
| `pre` validator is false | raises `PreContractError` |
| `post` or `ensure` validator is false | raises `PostContractError` |
| `inv` validator is false | raises `InvContractError` |
| validated `example` is false | raises `ExampleContractError` |
| function raises an exception absent from `raises` | raises `RaisesContractError` from the original exception |
| matching `reason` validator is false | raises `ReasonContractError` from the original exception |
| network operation lacks a permitting marker | raises `OfflineContractError` |
| stdout or stderr write lacks a permitting marker | raises `SilentContractError` |
| dispatch exhausts direct precondition mismatches | raises `NoMatchError` |
| a permanent state transition forbids a later transition | raises `RuntimeError` |

Supplying a custom `exception` to a supported decorator must replace its default violation type. Supplying an exception instance must preserve that instance's constructor arguments when the violation is raised. Exact exception text, traceback presentation, color, and representation are not part of this contract.

## Cross-View Invariants

1. A decorator visible as `Pre`, `Post`, `Ensure`, `Raises`, `Reason`, `Example`, or `Has` through introspection must enforce the matching runtime behavior whenever process checks are enabled.
2. A runtime violation configured with an exception class and non-empty message must expose an instance of that class through the wrapper's `exception`, while `exception_type` must return the class; a configured exception instance must remain the same object in `exception`.
3. Disabling ordinary enforcement must not remove wrappers returned by `get_contracts`, and re-enabling must reactivate those same definitions.
4. Permanent removal must prevent both runtime enforcement and introspection of contracts attempted afterward.
5. An inherited contract that rejects a child-method call must appear on that child method through `get_contracts`.
6. The markers that permit or reject a side effect at runtime must equal the `frozenset` returned by the effective `Has` wrapper.
7. `unwrap` must return the callable whose body supplies results for the decorated runtime view, without changing process state or metadata enumeration.
8. `init_all` and wrapper `init()` must prepare validation metadata without calling the decorated body or changing whether the contract is enabled.

## Public Interface

### Import Surface

The package is imported as `deal`. Runtime decorators, state functions, helpers, and public exception classes are available directly from that package. Contract metadata is available from the independently importable `deal.introspection` namespace.

```python
from deal import (
    pre, post, ensure, inv, raises, reason, has, example, chain, inherit,
    dispatch, safe, pure, catch, implies, disable, enable, reset, introspection,
    ContractError, PreContractError, PostContractError, InvContractError,
    ExampleContractError, RaisesContractError, ReasonContractError, MarkerError,
    OfflineContractError, SilentContractError, NoMatchError,
)
from deal.introspection import (
    get_contracts, init_all, unwrap, Contract, ValidatedContract,
    Pre, Post, Ensure, Example, Raises, Reason, Has,
)
```

Importing either public namespace must raise no optional-dependency error.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| pre | decorator | Precondition validator |
| post | decorator | Return-value validator |
| ensure | decorator | Combined argument-and-result validator |
| inv | decorator | Class invariant validator |
| raises | decorator | Exception allow-list declaration |
| reason | decorator | Exception-conditional validator |
| has | decorator | Side-effect marker declaration |
| example | decorator | Attach a validatable example |
| chain | function | Compose multiple contract decorators into one |
| inherit | decorator | Inherit contracts from base classes |
| dispatch | decorator | Multi-dispatch by precondition matching |
| safe | decorator | Shorthand for raises() with empty allow-list |
| pure | decorator | Combination of has() and safe |
| catch | function | Return exception type from a call or None |
| implies | function | Conditional logical helper for validators |
| disable | function | Turn off contract enforcement |
| enable | function | Restore contract enforcement |
| reset | function | Restore interpreter-default contract state |
| get_contracts | function | Enumerate attached contract wrappers |
| init_all | function | Initialize deferred contract metadata |
| unwrap | function | Return original callable without Deal wrappers |
| Contract | class | Base contract wrapper type |
| ValidatedContract | class | Contract wrapper with validate method |
| Pre | class | Precondition introspection wrapper |
| Post | class | Post-condition introspection wrapper |
| Ensure | class | Ensure introspection wrapper |
| Example | class | Example introspection wrapper |
| Raises | class | Raises introspection wrapper |
| Reason | class | Reason introspection wrapper |
| Has | class | Side-effect marker introspection wrapper |
| ContractError | exception | Base class for contract violations |
| PreContractError | exception | Precondition violation |
| PostContractError | exception | Post-condition or ensure violation |
| InvContractError | exception | Invariant violation |
| ExampleContractError | exception | Example validation failure |
| RaisesContractError | exception | Undeclared exception violation |
| ReasonContractError | exception | Reason validation failure |
| MarkerError | exception | Base marker violation |
| OfflineContractError | exception | Network operation without permitting marker |
| SilentContractError | exception | Output write without permitting marker |
| NoMatchError | exception | Dispatch exhausted all registrations |

### CLI Entry Points

This distribution must not install a `deal` console script. It must support `python -m deal` as the package's tooling entry point, while individual tooling commands remain outside the scope above.

| Invocation outcome | Exit code |
|---|---:|
| Help or a successfully completed supported invocation | 0 |
| Invalid top-level arguments or an unknown command | 2 |
| A supported command reports an operational failure | nonzero |

Importing and using the runtime API must not require invoking the module entry point. An invalid invocation must terminate with status 2 rather than entering a runtime contract workflow.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

The runtime API must work without optional analysis, documentation, property-testing, or validator-adapter packages. It must support Python 3.8 and later.

## Appendix B: Assessment Notes

Checks exercise public imports, synchronous calls, generator iteration, asynchronous awaiting, state transitions, dispatch and inheritance, side-effect boundaries, and introspection metadata. They compare observable return values, exception classes, warning categories, metadata values, and cross-view consistency. Presentation details and private storage are not checked. Each independently observable requirement contributes to the result.
