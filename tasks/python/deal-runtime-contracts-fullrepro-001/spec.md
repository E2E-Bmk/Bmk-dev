<!-- clauses.md -->
# Public clause anchors for deal-runtime-contracts-fullrepro-001

These anchors index the normative public behavior described in the Deal
specification.

| clause_id | section | clause |
|---|---|---|
| DEAL-IS-001 | Installable Surface | The root package must export `pre`, `post`, `ensure`, `inv`, `raises`, `reason`, `has`, `example`, `chain`, `inherit`, `dispatch`, `safe`, `pure`, `catch`, `implies`, `disable`, `enable`, `reset`, and `introspection`. |
| DEAL-IS-002 | Installable Surface | It must export `ContractError`, `PreContractError`, `PostContractError`, `InvContractError`, `ExampleContractError`, `RaisesContractError`, `ReasonContractError`, `MarkerError`, `OfflineContractError`, `SilentContractError`, and `NoMatchError`. |
| DEAL-IS-003 | Installable Surface | The `deal.introspection` namespace must export `get_contracts`, `init_all`, `unwrap`, `Contract`, `ValidatedContract`, `Pre`, `Post`, `Ensure`, `Example`, `Raises`, `Reason`, and `Has`. |
| DEAL-IS-004 | Installable Surface | Importing either public namespace must raise no optional-dependency error. |
| DEAL-PSM-001 | Product State Model | `deal.introspection` returns the definition's contract kind and configured metadata. 3. |
| DEAL-PSM-002 | Product State Model | The projections must agree on these state rules: |
| DEAL-PSM-003 | Product State Model | - A contract attached while ordinary checks are disabled must remain visible through `get_contracts` and must become active after `enable()`. - A contract attached before `disable()` must remain visible through `get_contracts` while its decorated callable returns unchecked results. - A decoration performed after permanent removal must return a callable with no newly attached Deal contract, so `get_contracts` must return no wrapper for that attempted decoration. - `unwrap` must return the original callable regardless of whether retained contracts are currently enabled or disabled. - Inherited contracts must affect a child method at runtime and must appear on that same bound method through `get_contracts`. - Metadata such as a configured exception, message, allowed exceptions, reason event, and markers must match the behavior configured by the corresponding decorator. |
| DEAL-CD-001 | Contract declarations | Each contract decorator must preserve the decorated callable's name, documentation, annotations, and normal argument interface. |
| DEAL-CD-002 | Contract declarations | Passing an `exception` class or instance must select that violation type. |
| DEAL-CD-003 | Contract declarations | Passing `message` must expose that description through introspection; a validator that returns a string on failure must supply the failure description for that call. |
| DEAL-CD-004 | Contract declarations | A failing validator without a custom exception must raise the contract-specific default listed under Error Semantics. |
| DEAL-CD-005 | Contract declarations | `safe` must support both `@deal.safe` and `@deal.safe()` and must behave as `raises()` with an empty allow-list. |
| DEAL-CD-006 | Contract declarations | `pure` must behave as the combination of `has()` and `safe`; a disallowed side effect or any function exception must therefore raise its corresponding contract violation. |
| DEAL-CD-007 | Contract declarations | `chain(*contracts)` must return one reusable decorator. |
| DEAL-CD-008 | Contract declarations | When every supplied contract passes, the decorated callable must return its original result. |
| DEAL-CD-009 | Contract declarations | When a supplied contract fails, the composed callable must raise that contract's configured violation without running later phases that depend on success. |
| DEAL-CD-010 | Contract declarations | `implies(test, then)` must return `then` when `test` is truthy and must return `True` when `test` is falsy. |
| DEAL-CD-011 | Contract declarations | `catch(func, *args, **kwargs)` must return the exact type of an `Exception` raised by the call and must return `None` when the call completes. |
| DEAL-CD-012 | Contract declarations | A `BaseException` outside the `Exception` hierarchy must propagate. |
| DEAL-PS-001 | Process state | `disable()` must turn off enforcement for retained contracts. |
| DEAL-PS-002 | Process state | `enable()` must restore their enforcement. |
| DEAL-PS-003 | Process state | `reset()` must restore the interpreter default: checks enabled in normal mode and disabled in optimized mode. |
| DEAL-PS-004 | Process state | `disable(permament=True)` must turn off enforcement and must prevent later decorators from attaching contracts. |
| DEAL-PS-005 | Process state | After that transition, `enable()`, `reset()`, and a second permanent-disable request must raise `RuntimeError`. |
| DEAL-PS-006 | Process state | With `warn=True`, `enable()` must emit `RuntimeWarning` when `LAMBDA_TASK_ROOT` or `GCLOUD_PROJECT` identifies a production environment, and `disable()` must emit `RuntimeWarning` when `PYTEST_CURRENT_TEST` or `CI` identifies a test environment. |
| DEAL-PS-007 | Process state | Passing `warn=False` must suppress these state sanity warnings. |
| DEAL-PS-008 | Process state | Calls that do not meet a warning condition must return `None` without emitting a warning. |
| DEAL-IO-001 | Introspection objects | `get_contracts(func)` returns an iterator of stable wrapper objects. |
| DEAL-IO-002 | Introspection objects | Each `Contract` wrapper must expose `exception`, `exception_type`, and `message`. |
| DEAL-IO-003 | Introspection objects | When a decorator receives an exception class together with a non-empty `message`, `exception` must return an instance of that class initialized with the message. |
| DEAL-IO-004 | Introspection objects | When the decorator receives an exception class with `message=None` or an empty message, `exception` must return the class itself. |
| DEAL-IO-005 | Introspection objects | When the decorator receives an exception instance, `exception` must return that same instance regardless of the configured message. |
| DEAL-IO-006 | Introspection objects | Omitting a custom exception must apply the same class-or-instance rule to the decorator's default exception class. |
| DEAL-IO-007 | Introspection objects | In every case, `exception_type` must return the exception class and `message` must return the separately configured message. |
| DEAL-IO-008 | Introspection objects | `Pre`, `Post`, `Ensure`, `Example`, and `Reason` must be instances of `ValidatedContract`. |
| DEAL-IO-009 | Introspection objects | Their `validate(*args, **kwargs)` method must return `None` when the supplied values satisfy the validator and must raise the configured exception when they do not. |
| DEAL-IO-010 | Introspection objects | Their `init()` method must initialize deferred contract metadata without executing the decorated function. |
| DEAL-IO-011 | Introspection objects | Their `source` property must return a named validator's function name or a lambda validator's expression body when source text is available, and it must return an empty string when source cannot be recovered. |
| DEAL-IO-012 | Introspection objects | `Raises.exceptions` must return the declared exception classes as an ordered tuple. |
| DEAL-IO-013 | Introspection objects | `Reason.event` must return the declared triggering exception class. |
| DEAL-IO-014 | Introspection objects | `Has.markers` must return the effective marker names as a `frozenset`. |
| DEAL-IO-015 | Introspection objects | Accessing these properties on wrappers returned by `get_contracts` must not execute the decorated function. |
| DEAL-IO-016 | Introspection objects | `init_all(func)` must initialize every validated contract found on the callable and must return `None`; a callable with no Deal contracts must also return `None`. |
| DEAL-IO-017 | Introspection objects | `unwrap(func)` must return the original callable for a Deal-wrapped callable and must return its input unchanged when no Deal wrapper is present. |
| DEAL-VIAO-001 | Validator inputs and outcomes | A normal validator must receive the arguments appropriate to its contract: call arguments for `pre`, only the produced value for `post`, call arguments plus a `result` keyword for `ensure`, and the original call arguments for `reason`. |
| DEAL-VIAO-002 | Validator inputs and outcomes | A validator whose sole parameter is named `_` must instead receive an attribute-accessible mapping of the decorated callable's bound arguments, including defaults; `ensure` must include `result` in that mapping. |
| DEAL-VIAO-003 | Validator inputs and outcomes | A truthy validator result must satisfy the contract. |
| DEAL-VIAO-004 | Validator inputs and outcomes | A falsy result must raise the configured exception. |
| DEAL-VIAO-005 | Validator inputs and outcomes | A string result must fail validation and must become the call-specific description. |
| DEAL-VIAO-006 | Validator inputs and outcomes | If argument binding or validator invocation itself is invalid, the underlying Python call error must propagate. |
| DEAL-VIAO-007 | Validator inputs and outcomes | During a recursive call from one contract validator into another decorated callable, Deal must avoid recursively enforcing contracts until the current validation finishes. |
| DEAL-VIAO-008 | Validator inputs and outcomes | An exception raised by an already-failing Deal contract must propagate without being converted by an enclosing `raises` declaration. |
| DEAL-VRAO-001 | Values, results, and ordering | `pre` must validate before the function body. |
| DEAL-VRAO-002 | Values, results, and ordering | A failed precondition must raise before the body produces side effects or a result. |
| DEAL-VRAO-003 | Values, results, and ordering | `post` must validate the function's returned value after the body completes. |
| DEAL-VRAO-004 | Values, results, and ordering | `ensure` must validate the original arguments together with that returned value. |
| DEAL-VRAO-005 | Values, results, and ordering | Failed result validation must prevent the invalid result from reaching the caller. |
| DEAL-VRAO-006 | Values, results, and ordering | Within an ordinary source decorator stack, multiple validators of the same kind must run from the decorator nearest the function upward. |
| DEAL-VRAO-007 | Values, results, and ordering | If the first such validator fails, its exception must be raised and later same-kind validators must not run. |
| DEAL-VRAO-008 | Values, results, and ordering | `post` validators must run before `ensure` validators when both kinds are present and the function returns normally. |
| DEAL-VRAO-009 | Values, results, and ordering | Contracts passed to `chain(first, second, ...)` must be applied and enforced in argument order for same-kind validators. |
| DEAL-VRAO-010 | Values, results, and ordering | If `first` and `second` both fail, the failure selected by `first` must reach the caller. |
| DEAL-GAAF-001 | Generators and asynchronous functions | Calling a decorated generator function must return an iterator without running its validator or body. |
| DEAL-GAAF-002 | Generators and asynchronous functions | Starting iteration must run preconditions before the first body step. |
| DEAL-GAAF-003 | Generators and asynchronous functions | Every yielded value must pass all `post` and `ensure` validators before reaching the caller; the first invalid yielded value must raise the configured result-contract exception. |
| DEAL-GAAF-004 | Generators and asynchronous functions | Function exceptions raised during iteration must follow `raises` and `reason` rules. |
| DEAL-GAAF-005 | Generators and asynchronous functions | Calling a decorated asynchronous function must return an awaitable without running its validator or body. |
| DEAL-GAAF-006 | Generators and asynchronous functions | Awaiting it must run preconditions before the body and must run `post` and `ensure` after the awaited body returns. |
| DEAL-GAAF-007 | Generators and asynchronous functions | Function exceptions raised while awaiting must follow `raises` and `reason` rules. |
| DEAL-GAAF-008 | Generators and asynchronous functions | `has` guards must remain active while a synchronous or asynchronous body executes and around each generator advancement. |
| DEAL-GAAF-009 | Generators and asynchronous functions | A prohibited operation must raise its marker exception before the generator yields or the awaited call returns. |
| DEAL-EAR-001 | Exceptions and reasons | `raises(*exceptions)` must allow a function exception only when its exact type occurs in the declared tuple. |
| DEAL-EAR-002 | Exceptions and reasons | An allowed exception must propagate unchanged. |
| DEAL-EAR-003 | Exceptions and reasons | An undeclared exception, including a subclass of a listed type that is not itself listed, must be chained as the cause of `RaisesContractError` or the configured replacement. |
| DEAL-EAR-004 | Exceptions and reasons | `raises()` and `safe` must reject every function exception. |
| DEAL-EAR-005 | Exceptions and reasons | They must not replace a `ContractError` raised by another Deal contract. |
| DEAL-EAR-006 | Exceptions and reasons | `reason(event, validator)` must run the validator only when the function raises exactly `event`. |
| DEAL-EAR-007 | Exceptions and reasons | A passing reason must preserve and re-raise the original event. |
| DEAL-EAR-008 | Exceptions and reasons | A failing reason must raise `ReasonContractError` or the configured replacement with the original event as its cause. |
| DEAL-EAR-009 | Exceptions and reasons | Other exception types, including subclasses not exactly equal to `event`, must propagate without running that reason validator. |
| DEAL-EAR-010 | Exceptions and reasons | When both declarations are present, `raises` must check the exact exception allow-list before a matching `reason` validator runs. |
| DEAL-EAR-011 | Exceptions and reasons | An event absent from the allow-list must raise `RaisesContractError` without running its reason. |
| DEAL-EAR-012 | Exceptions and reasons | An allowed matching event must proceed to reason validation and must raise `ReasonContractError` when that validator fails. |
| DEAL-SEM-001 | Side-effect markers | `has(*markers)` must preserve every marker string for introspection. |
| DEAL-SEM-002 | Side-effect markers | Custom marker strings must remain metadata and must not invent a runtime guard. |
| DEAL-SEM-003 | Side-effect markers | The `io`, `network`, and `socket` markers must permit creation of network sockets during the decorated body. |
| DEAL-SEM-004 | Side-effect markers | Without any of those markers, a socket attempt must raise `OfflineContractError` or the custom marker exception. |
| DEAL-SEM-005 | Side-effect markers | The `io`, `print`, and `stdout` markers must permit writes to standard output. |
| DEAL-SEM-006 | Side-effect markers | Without any of those markers, an output write must raise `SilentContractError` or the custom marker exception. |
| DEAL-SEM-007 | Side-effect markers | The `io` and `stderr` markers must permit writes to standard error; without either marker, an error-stream write must raise `SilentContractError` or the custom marker exception. |
| DEAL-SEM-008 | Side-effect markers | Stacking more than one `has` decorator directly on one function must make the outer decorator's marker set effective. |
| DEAL-SEM-009 | Side-effect markers | Inherited `has` contracts must instead merge base and child marker sets into their union. |
| DEAL-SEM-010 | Side-effect markers | A prohibited operation after either rule is applied must raise according to the resulting effective markers. |
| DEAL-CI-001 | Class invariants | `inv(validator)` must return a class whose instances remain instances of the original class. |
| DEAL-CI-002 | Class invariants | It must validate before and after public method execution and after attribute assignment. |
| DEAL-CI-003 | Class invariants | A failed check must raise `InvContractError` or the configured replacement. |
| DEAL-CI-004 | Class invariants | Invariant failure must not roll back mutation. |
| DEAL-CI-005 | Class invariants | If a method or assignment stores an invalid value before validation fails, the object must retain that value after the exception. |
| DEAL-CI-006 | Class invariants | Applying multiple invariants must require every validator to pass; the first failing invariant in runtime order must raise its configured exception. |
| DEAL-DAI-001 | Dispatch and inheritance | `dispatch(func)` must return a callable dispatcher with a `register(function)` method. |
| DEAL-DAI-002 | Dispatch and inheritance | Registration must return the registered function so it remains directly callable. |
| DEAL-DAI-003 | Dispatch and inheritance | The initially decorated function must supply the dispatcher's name, documentation, annotations, and signature, but its body must never execute. |
| DEAL-DAI-004 | Dispatch and inheritance | On each dispatch call, registered implementations must be tried in registration order. |
| DEAL-DAI-005 | Dispatch and inheritance | The first implementation that returns without a direct `PreContractError` from its own preconditions must supply the result. |
| DEAL-DAI-006 | Dispatch and inheritance | A direct precondition mismatch must advance to the next registration. |
| DEAL-DAI-007 | Dispatch and inheritance | If all registrations mismatch, the dispatcher must raise `NoMatchError`. |
| DEAL-DAI-008 | Dispatch and inheritance | A `PreContractError` raised inside a selected implementation's body or a nested call must propagate and must not be treated as a dispatch mismatch. |
| DEAL-DAI-009 | Dispatch and inheritance | Dispatch must temporarily enforce the registered implementations' preconditions even when global checks are disabled, then must restore the prior global state after return or failure. |
| DEAL-DAI-010 | Dispatch and inheritance | A default registration without preconditions must match when reached; a failure raised by that implementation must propagate. |
| DEAL-DAI-011 | Dispatch and inheritance | `inherit` must accept either an overriding method or a whole subclass. |
| DEAL-DAI-012 | Dispatch and inheritance | On first use of an inherited method, Deal must combine contracts from all applicable base implementations with contracts already attached below `@deal.inherit` on the child. |
| DEAL-DAI-013 | Dispatch and inheritance | Every inherited and child value contract must remain enforceable, and a violation must raise the corresponding configured exception. |
| DEAL-DAI-014 | Dispatch and inheritance | For `has`, inheritance must return one effective marker set containing the union of base and child markers. |
| DEAL-DAI-015 | Dispatch and inheritance | If no base implementation carries contracts, the child method must run with only its own contracts. |
| DEAL-DAI-016 | Dispatch and inheritance | If neither base nor child carries contracts, the method must behave as the undecorated implementation. |
| DEAL-RM-001 | Runtime metadata | `example(validator)` must attach an `Example` object visible through `get_contracts` and must not execute the example during ordinary function calls. |
| DEAL-RM-002 | Runtime metadata | Calling that wrapper's `validate()` must return `None` for a truthy example and must raise `ExampleContractError` for a false example. |
| DEAL-RM-003 | Runtime metadata | `get_contracts` must enumerate attached wrappers in this kind order: all `Pre`, then `Post`, `Ensure`, `Raises`, `Reason`, `Example`, and finally one effective `Has`. |
| DEAL-RM-004 | Runtime metadata | Within a kind, it must preserve that kind's runtime order. |
| DEAL-RM-005 | Runtime metadata | A callable with no Deal contracts must return an empty iterator. |
| DEAL-RM-006 | Runtime metadata | `get_contracts` must follow ordinary decorator-wrapper links and must expose inherited contracts after inheritance is resolved. |
| DEAL-RM-007 | Runtime metadata | It must return only the public wrapper types above and must not require callers to inspect private carrier attributes. |
| DEAL-ES-001 | Error Semantics | All value, example, reason, raises, and marker contract errors must inherit from `ContractError`, and `ContractError` must inherit from `AssertionError`. |
| DEAL-ES-002 | Error Semantics | `NoMatchError` must remain a separate exception used only when dispatch exhausts its registrations. |
| DEAL-ES-003 | Error Semantics | \| Trigger \| Default result \| \|---\|---\| \| `pre` validator is false \| raises `PreContractError` \| \| `post` or `ensure` validator is false \| raises `PostContractError` \| \| `inv` validator is false \| raises `InvContractError` \| \| validated `example` is false \| raises `ExampleContractError` \| \| function raises an exception absent from `raises` \| raises `RaisesContractError` from the original exception \| \| matching `reason` validator is false \| raises `ReasonContractError` from the original exception \| \| network operation lacks a permitting marker \| raises `OfflineContractError` \| \| stdout or stderr write lacks a permitting marker \| raises `SilentContractError` \| \| dispatch exhausts direct precondition mismatches \| raises `NoMatchError` \| \| a permanent state transition forbids a later transition \| raises `RuntimeError` \| |
| DEAL-ES-004 | Error Semantics | Supplying a custom `exception` to a supported decorator must replace its default violation type. |
| DEAL-ES-005 | Error Semantics | Supplying an exception instance must preserve that instance's constructor arguments when the violation is raised. |
| DEAL-CVI-001 | Cross-View Invariants | A decorator visible as `Pre`, `Post`, `Ensure`, `Raises`, `Reason`, `Example`, or `Has` through introspection must enforce the matching runtime behavior whenever process checks are enabled. 2. |
| DEAL-CVI-002 | Cross-View Invariants | A runtime violation configured with an exception class and non-empty message must expose an instance of that class through the wrapper's `exception`, while `exception_type` must return the class; a configured exception instance must remain the same object in `exception`. 3. |
| DEAL-CVI-003 | Cross-View Invariants | Disabling ordinary enforcement must not remove wrappers returned by `get_contracts`, and re-enabling must reactivate those same definitions. 4. |
| DEAL-CVI-004 | Cross-View Invariants | Permanent removal must prevent both runtime enforcement and introspection of contracts attempted afterward. 5. |
| DEAL-CVI-005 | Cross-View Invariants | An inherited contract that rejects a child-method call must appear on that child method through `get_contracts`. 6. |
| DEAL-CVI-006 | Cross-View Invariants | The markers that permit or reject a side effect at runtime must equal the `frozenset` returned by the effective `Has` wrapper. 7. |
| DEAL-CVI-007 | Cross-View Invariants | `unwrap` must return the callable whose body supplies results for the decorated runtime view, without changing process state or metadata enumeration. 8. |
| DEAL-CVI-008 | Cross-View Invariants | `init_all` and wrapper `init()` must prepare validation metadata without calling the decorated body or changing whether the contract is enabled. |
| DEAL-RW-001 | Representative Workflow | The workflow must retain one contract definition across runtime calls, metadata inspection, disabling, and re-enabling. |
| DEAL-RW-002 | Representative Workflow | If any projection loses or changes the definition, the corresponding assertion or exception check must fail. |
| DEAL-IP-001 | Invocation Protocol | This distribution must not install a `deal` console script. |
| DEAL-IP-002 | Invocation Protocol | It must support `python -m deal` as the package's tooling entry point, while individual tooling commands remain outside the scope above. |
| DEAL-IP-003 | Invocation Protocol | Importing and using the runtime API must not require invoking the module entry point. |
| DEAL-IP-004 | Invocation Protocol | An invalid invocation must terminate with status 2 rather than entering a runtime contract workflow. |

<!-- spec.md -->
# Deal Specification

> This document defines the package's public contract. The described system
> may differ from similarly named software in interface design, parameter
> naming, behavioral edge cases, and error semantics. Implementations must
> follow the behavior described here rather than assumptions drawn from other
> codebases.

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

<!-- spec-addendum.md -->
# Deal Lifecycle Addendum

This addendum defines how one contract declaration behaves when it crosses Python call forms and Deal lifecycle boundaries. All behavior below is observable through the public `deal` and `deal.introspection` namespaces.

## Mixed declarations across call forms

A callable may combine `pre`, `post`, `ensure`, `raises`, and `reason` declarations. The same declaration pipeline applies to ordinary functions, coroutine functions, and generator functions.

- Argument conditions receive bound positional, defaulted, and keyword-only values.
- Result conditions run after a completed ordinary or awaited call and before each generated value reaches its caller.
- An allowed exception is propagated unchanged. A matching `reason` condition still applies, and a failed reason keeps the original event as its cause.
- Public metadata lists the effective kinds in the documented kind order regardless of source decorator order or call form.

## Deferred execution and process state

Calling a coroutine function or generator function creates a deferred object without running its body or its declarations. The enabled or disabled state is observed when execution actually begins: when the coroutine is awaited or when the generator is first advanced. Changing state after the deferred object is created but before execution begins therefore affects that execution.

Creating a deferred object does not remove or alter its public metadata.

## Dispatch state isolation

A dispatcher may temporarily enforce registered preconditions while the surrounding process state is disabled. It must restore the prior state after every exit path:

- a registered branch returns successfully;
- no branch matches;
- a selected branch raises a contract error from its body or a nested call.

Only a direct precondition mismatch belonging to the candidate branch permits the dispatcher to continue to the next registration. Errors originating from the selected body propagate to the caller.

## Multigeneration inheritance

Inherited methods compose the effective declarations contributed by applicable ancestors with declarations already attached to the overriding method. This applies across more than one generation and across different declaration kinds. Effective `has` markers are the union of inherited and local markers.

Reading metadata may materialize inherited declarations before the first method call. Once materialized, later calls and later metadata reads must keep the same effective kind sequence and marker set. Materializing one subclass must not change the behavior of a sibling or ancestor implementation.

## One definition across introspection and state changes

`init_all` prepares validated declarations without executing the decorated body or running a validator. `unwrap` continues to return the same original callable before and after initialization, calls, disabling, and re-enabling.

Disabling enforcement does not remove declarations. Their kind order, configured exception metadata, and marker metadata remain observable. Re-enabling uses the retained configuration. When a configured exception object is supplied, metadata retains that object; a resulting violation has its type and constructor arguments.
## Deferred policy after execution starts

The enabled or disabled policy selected when a coroutine begins awaiting or a
generator is first advanced remains the policy for that execution until it
finishes. Changing the process state while the execution is suspended does not
replace the policy already selected by the in-flight coroutine or generator.

This lifecycle rule applies to result declarations as well as argument
declarations. Public metadata remains available and unchanged while a deferred
execution is suspended and after it completes or raises a contract violation.

## Deferred registrations under dispatch

Dispatch preserves the ordinary deferred timing of a registered coroutine or
generator function. Asking the dispatcher for the coroutine or generator
object does not advance the registered body or run its declarations. Those
declarations begin when the returned coroutine is awaited or the returned
generator is first advanced.

The registered callable keeps the same public contract metadata and unwrap
identity before object creation, while the object is pending, and after its
execution. Dispatch metadata and registration do not turn deferred creation
into eager contract evaluation.
