# Deal Specification

## Product Overview

Deal brings design-by-contract checks to ordinary Python callables and classes. Applications attach preconditions, result conditions, exception policies, side-effect markers, and invariants with decorators. The same contract facts drive runtime checks and a stable introspection interface, while process-wide controls turn checks on or off without changing callers.

## Scope

This specification covers:

- synchronous functions, generator functions, and asynchronous functions decorated with runtime contracts;
- contract composition and ordering, dispatch registration, and inheritance from base classes;
- process-wide enable, disable, reset, and permanent-removal transitions;
- the public `deal.introspection` view of contracts and their metadata;
- public contract exception classes and the small runtime helpers used by validators.

## Installable Surface

The package is imported as `deal`. Runtime decorators, state functions, helpers, and public exception classes are available directly from that package. Contract metadata is available from the independently importable `deal.introspection` namespace.

The root package must export `pre`, `post`, `ensure`, `inv`, `raises`, `reason`, `has`, `example`, `chain`, `inherit`, `dispatch`, `safe`, `pure`, `catch`, `implies`, `disable`, `enable`, `reset`, and `introspection`. It must export `ContractError`, `PreContractError`, `PostContractError`, `InvContractError`, `ExampleContractError`, `RaisesContractError`, `ReasonContractError`, `MarkerError`, `OfflineContractError`, `SilentContractError`, and `NoMatchError`.

The `deal.introspection` namespace must export `get_contracts`, `init_all`, `unwrap`, `Contract`, `ValidatedContract`, `Pre`, `Post`, `Ensure`, `Example`, `Raises`, `Reason`, and `Has`. Importing either public namespace must raise no optional-dependency error.

## Product State Model

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

## Public API

### Contract declarations

The value and exception decorators use these signatures:

```python
pre(validator, *, message=None, exception=None)
post(validator, *, message=None, exception=None)
ensure(validator, *, message=None, exception=None)
inv(validator, *, message=None, exception=None)
raises(*exceptions, message=None, exception=None)
reason(event, validator, *, message=None, exception=None)
```

The composition and marker decorators use these signatures:

```python
has(*markers, message=None, exception=None)
example(validator)
chain(*contracts)
inherit(func_or_class)
dispatch(func)
safe(func=None, **kwargs)
pure(func)
```

Each contract decorator must preserve the decorated callable's name, documentation, annotations, and normal argument interface. Passing an `exception` class or instance must select that violation type. Passing `message` must expose that description through introspection; a validator that returns a string on failure must supply the failure description for that call. A failing validator without a custom exception must raise the contract-specific default listed under Error Semantics.

`safe` must support both `@deal.safe` and `@deal.safe()` and must behave as `raises()` with an empty allow-list. `pure` must behave as the combination of `has()` and `safe`; a disallowed side effect or any function exception must therefore raise its corresponding contract violation.

`chain(*contracts)` must return one reusable decorator. When every supplied contract passes, the decorated callable must return its original result. When a supplied contract fails, the composed callable must raise that contract's configured violation without running later phases that depend on success.

`implies(test, then)` must return `then` when `test` is truthy and must return `True` when `test` is falsy. `catch(func, *args, **kwargs)` must return the exact type of an `Exception` raised by the call and must return `None` when the call completes. A `BaseException` outside the `Exception` hierarchy must propagate.

### Process state

The state functions have these signatures:

```python
disable(*, permament=False, warn=True)
enable(warn=True)
reset()
```

The public parameter name is `permament`. `disable()` must turn off enforcement for retained contracts. `enable()` must restore their enforcement. `reset()` must restore the interpreter default: checks enabled in normal mode and disabled in optimized mode.

`disable(permament=True)` must turn off enforcement and must prevent later decorators from attaching contracts. After that transition, `enable()`, `reset()`, and a second permanent-disable request must raise `RuntimeError`.

With `warn=True`, `enable()` must emit `RuntimeWarning` when `LAMBDA_TASK_ROOT` or `GCLOUD_PROJECT` identifies a production environment, and `disable()` must emit `RuntimeWarning` when `PYTEST_CURRENT_TEST` or `CI` identifies a test environment. Passing `warn=False` must suppress these state sanity warnings. Calls that do not meet a warning condition must return `None` without emitting a warning.

### Introspection objects

`get_contracts(func)` returns an iterator of stable wrapper objects. Each `Contract` wrapper must expose `exception`, `exception_type`, and `message`. When a decorator receives an exception class together with a non-empty `message`, `exception` must return an instance of that class initialized with the message. When the decorator receives an exception class with `message=None` or an empty message, `exception` must return the class itself. When the decorator receives an exception instance, `exception` must return that same instance regardless of the configured message. Omitting a custom exception must apply the same class-or-instance rule to the decorator's default exception class. In every case, `exception_type` must return the exception class and `message` must return the separately configured message.

`Pre`, `Post`, `Ensure`, `Example`, and `Reason` must be instances of `ValidatedContract`. Their `validate(*args, **kwargs)` method must return `None` when the supplied values satisfy the validator and must raise the configured exception when they do not. Their `init()` method must initialize deferred contract metadata without executing the decorated function. Their `source` property must return a named validator's function name or a lambda validator's expression body when source text is available, and it must return an empty string when source cannot be recovered.

`Raises.exceptions` must return the declared exception classes as an ordered tuple. `Reason.event` must return the declared triggering exception class. `Has.markers` must return the effective marker names as a `frozenset`. Accessing these properties on wrappers returned by `get_contracts` must not execute the decorated function.

`init_all(func)` must initialize every validated contract found on the callable and must return `None`; a callable with no Deal contracts must also return `None`. `unwrap(func)` must return the original callable for a Deal-wrapped callable and must return its input unchanged when no Deal wrapper is present.

## Runtime Contract Lifecycle

### Validator inputs and outcomes

A normal validator must receive the arguments appropriate to its contract: call arguments for `pre`, only the produced value for `post`, call arguments plus a `result` keyword for `ensure`, and the original call arguments for `reason`. A validator whose sole parameter is named `_` must instead receive an attribute-accessible mapping of the decorated callable's bound arguments, including defaults; `ensure` must include `result` in that mapping.

A truthy validator result must satisfy the contract. A falsy result must raise the configured exception. A string result must fail validation and must become the call-specific description. If argument binding or validator invocation itself is invalid, the underlying Python call error must propagate.

During a recursive call from one contract validator into another decorated callable, Deal must avoid recursively enforcing contracts until the current validation finishes. An exception raised by an already-failing Deal contract must propagate without being converted by an enclosing `raises` declaration.

### Values, results, and ordering

`pre` must validate before the function body. A failed precondition must raise before the body produces side effects or a result. `post` must validate the function's returned value after the body completes. `ensure` must validate the original arguments together with that returned value. Failed result validation must prevent the invalid result from reaching the caller.

Within an ordinary source decorator stack, multiple validators of the same kind must run from the decorator nearest the function upward. If the first such validator fails, its exception must be raised and later same-kind validators must not run. `post` validators must run before `ensure` validators when both kinds are present and the function returns normally.

Contracts passed to `chain(first, second, ...)` must be applied and enforced in argument order for same-kind validators. If `first` and `second` both fail, the failure selected by `first` must reach the caller.

### Generators and asynchronous functions

Calling a decorated generator function must return an iterator without running its validator or body. Starting iteration must run preconditions before the first body step. Every yielded value must pass all `post` and `ensure` validators before reaching the caller; the first invalid yielded value must raise the configured result-contract exception. Function exceptions raised during iteration must follow `raises` and `reason` rules.

Calling a decorated asynchronous function must return an awaitable without running its validator or body. Awaiting it must run preconditions before the body and must run `post` and `ensure` after the awaited body returns. Function exceptions raised while awaiting must follow `raises` and `reason` rules.

`has` guards must remain active while a synchronous or asynchronous body executes and around each generator advancement. A prohibited operation must raise its marker exception before the generator yields or the awaited call returns.

### Exceptions and reasons

`raises(*exceptions)` must allow a function exception only when its exact type occurs in the declared tuple. An allowed exception must propagate unchanged. An undeclared exception, including a subclass of a listed type that is not itself listed, must be chained as the cause of `RaisesContractError` or the configured replacement.

`raises()` and `safe` must reject every function exception. They must not replace a `ContractError` raised by another Deal contract.

`reason(event, validator)` must run the validator only when the function raises exactly `event`. A passing reason must preserve and re-raise the original event. A failing reason must raise `ReasonContractError` or the configured replacement with the original event as its cause. Other exception types, including subclasses not exactly equal to `event`, must propagate without running that reason validator.

When both declarations are present, `raises` must check the exact exception allow-list before a matching `reason` validator runs. An event absent from the allow-list must raise `RaisesContractError` without running its reason. An allowed matching event must proceed to reason validation and must raise `ReasonContractError` when that validator fails.

### Side-effect markers

`has(*markers)` must preserve every marker string for introspection. Custom marker strings must remain metadata and must not invent a runtime guard.

The `io`, `network`, and `socket` markers must permit creation of network sockets during the decorated body. Without any of those markers, a socket attempt must raise `OfflineContractError` or the custom marker exception. This contract covers the local permission boundary; it does not require a remote service to answer.

The `io`, `print`, and `stdout` markers must permit writes to standard output. Without any of those markers, an output write must raise `SilentContractError` or the custom marker exception. The `io` and `stderr` markers must permit writes to standard error; without either marker, an error-stream write must raise `SilentContractError` or the custom marker exception.

Stacking more than one `has` decorator directly on one function must make the outer decorator's marker set effective. Inherited `has` contracts must instead merge base and child marker sets into their union. A prohibited operation after either rule is applied must raise according to the resulting effective markers.

### Class invariants

`inv(validator)` must return a class whose instances remain instances of the original class. It must validate before and after public method execution and after attribute assignment. A failed check must raise `InvContractError` or the configured replacement.

Invariant failure must not roll back mutation. If a method or assignment stores an invalid value before validation fails, the object must retain that value after the exception. Applying multiple invariants must require every validator to pass; the first failing invariant in runtime order must raise its configured exception.

### Dispatch and inheritance

`dispatch(func)` must return a callable dispatcher with a `register(function)` method. Registration must return the registered function so it remains directly callable. The initially decorated function must supply the dispatcher's name, documentation, annotations, and signature, but its body must never execute.

On each dispatch call, registered implementations must be tried in registration order. The first implementation that returns without a direct `PreContractError` from its own preconditions must supply the result. A direct precondition mismatch must advance to the next registration. If all registrations mismatch, the dispatcher must raise `NoMatchError`. A `PreContractError` raised inside a selected implementation's body or a nested call must propagate and must not be treated as a dispatch mismatch.

Dispatch must temporarily enforce the registered implementations' preconditions even when global checks are disabled, then must restore the prior global state after return or failure. A default registration without preconditions must match when reached; a failure raised by that implementation must propagate.

`inherit` must accept either an overriding method or a whole subclass. On first use of an inherited method, Deal must combine contracts from all applicable base implementations with contracts already attached below `@deal.inherit` on the child. Every inherited and child value contract must remain enforceable, and a violation must raise the corresponding configured exception.

For `has`, inheritance must return one effective marker set containing the union of base and child markers. If no base implementation carries contracts, the child method must run with only its own contracts. If neither base nor child carries contracts, the method must behave as the undecorated implementation.

### Runtime metadata

`example(validator)` must attach an `Example` object visible through `get_contracts` and must not execute the example during ordinary function calls. Calling that wrapper's `validate()` must return `None` for a truthy example and must raise `ExampleContractError` for a false example.

`get_contracts` must enumerate attached wrappers in this kind order: all `Pre`, then `Post`, `Ensure`, `Raises`, `Reason`, `Example`, and finally one effective `Has`. Within a kind, it must preserve that kind's runtime order. A callable with no Deal contracts must return an empty iterator.

`get_contracts` must follow ordinary decorator-wrapper links and must expose inherited contracts after inheritance is resolved. It must return only the public wrapper types above and must not require callers to inspect private carrier attributes.

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

## Representative Workflow

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

## Non-Goals

- Property-based case generation, `TestCase`, memory checks, formal verification, and external validator libraries are excluded.
- Static analysis, flake8 integration, source transformation, stubs, Sphinx rendering, and command-specific CLI presentation are excluded.
- Module-load contracts and import hooks are excluded.
- Private modules, private carrier attributes, internal state objects, generated subclass names, cache layout, and wrapper storage are excluded.
- Exact exception strings, `repr` output, traceback trimming, syntax coloring, and diagnostic formatting are excluded.
- Successful communication with a real remote network service is excluded; only local permission or rejection of a socket operation is covered.

## Invocation Protocol

This distribution must not install a `deal` console script. It must support `python -m deal` as the package's tooling entry point, while individual tooling commands remain outside the scope above.

| Invocation outcome | Exit code |
|---|---:|
| Help or a successfully completed supported invocation | 0 |
| Invalid top-level arguments or an unknown command | 2 |
| A supported command reports an operational failure | nonzero |

Importing and using the runtime API must not require invoking the module entry point. An invalid invocation must terminate with status 2 rather than entering a runtime contract workflow.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

The runtime API must work without optional analysis, documentation, property-testing, or validator-adapter packages. It must support Python 3.8 and later.

## Implementation Guidance

Checks exercise public imports, synchronous calls, generator iteration, asynchronous awaiting, state transitions, dispatch and inheritance, side-effect boundaries, and introspection metadata. They compare observable return values, exception classes, warning categories, metadata values, and cross-view consistency. Presentation details and private storage are not checked. Each independently observable requirement contributes to the result.
