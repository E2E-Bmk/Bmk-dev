# QLExpress4 Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`qlexpress4` is an embeddable Java expression and rule engine that compiles scripts, evaluates them against caller-supplied state, and exposes results, dependency inspection, extension dispatch, diagnostics, traces, and reusable compiled forms. The Maven artifact is `com.alibaba:qlexpress4`.

The central fact source is a script compiled by an `Express4Runner` together with runner initialization policy, per-execution options, registered functions/operators/macros, and an execution context. Its public projections are the returned `QLResult`, optional context write-back, dependency sets, trace trees, validation errors, compile-cache reuse, and serializable precompiled cache objects.

## Non-Goals

- This specification does not require Spring, PF4J, OSGi, remote class loading, network access, or external services.
- This specification does not require scripts in open security mode to perform file, process, reflection, network, or other security-sensitive I/O.
- This specification does not define generated lexer/parser types, syntax-tree visitors, VM instructions, internal scopes, internal operator classes, or compile-cache field layout.
- This specification does not require token-stream snapshots, exact debug text, exact exception messages, or exact pretty-print whitespace.
- This specification does not define private-field access behavior or internal member-resolution algorithms.
- This specification does not require a command-line entry point or Maven plugin goal.

## Representative Workflows

### Evaluate a Rule and Observe Context State

```java
import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.InitOptions;
import com.alibaba.qlexpress4.QLOptions;
import com.alibaba.qlexpress4.QLResult;
import java.util.HashMap;
import java.util.Map;

Express4Runner runner = new Express4Runner(InitOptions.DEFAULT_OPTIONS);
Map<String, Object> context = new HashMap<>();
context.put("price", 25);
context.put("count", 4);

QLResult result = runner.execute(
    "total = price * count; total",
    context,
    QLOptions.builder().polluteUserContext(true).build());

Object value = result.getResult();
Object writtenBack = context.get("total");
```

WHEN a map-backed execution succeeds with `polluteUserContext` enabled, THEN the runner must return the final script value and must write global assignments into the supplied map.

### Register Domain Operations and Inspect Dependencies

```java
import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.InitOptions;
import com.alibaba.qlexpress4.QLOptions;
import com.alibaba.qlexpress4.QLPrecedences;
import java.util.Collections;
import java.util.Set;

Express4Runner runner = new Express4Runner(InitOptions.DEFAULT_OPTIONS);
runner.addVarArgsFunction("join", values -> values[0] + ":" + values[1]);
runner.addOperator("plusTax", (left, right) ->
    ((Number) left.get()).doubleValue() + ((Number) right.get()).doubleValue(),
    QLPrecedences.ADD);

Object value = runner.execute(
    "join(customer, amount plusTax tax)",
    Collections.singletonMap("customer", "A"),
    QLOptions.DEFAULT_OPTIONS).getResult();
Set<String> variables = runner.getOutVarNames("join(customer, amount plusTax tax)");
```

WHEN a registered function or operator is referenced by a later script, THEN execution must dispatch to that registration and dependency inspection must report only unresolved external variables or functions.

### Move a Precompiled Script Between Equivalent Runners

```java
import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.InitOptions;
import com.alibaba.qlexpress4.QLOptions;
import com.alibaba.qlexpress4.api.parsecache.LoadedParseCache;
import com.alibaba.qlexpress4.api.parsecache.SerializableParseCache;
import com.alibaba.qlexpress4.runtime.context.MapExpressContext;
import java.util.Collections;

Express4Runner producer = new Express4Runner(InitOptions.DEFAULT_OPTIONS);
SerializableParseCache dto = producer.parseToSerializableCache("x * 2 + 1");

Express4Runner consumer = new Express4Runner(InitOptions.DEFAULT_OPTIONS);
LoadedParseCache loaded = consumer.loadSerializableCache(dto);
Object value = consumer.execute(
    loaded,
    new MapExpressContext(Collections.singletonMap("x", 3)),
    QLOptions.DEFAULT_OPTIONS).getResult();
```

WHEN producer and consumer runners have equivalent imports, extensions, operators, class loading, tracing policy, and security policy, THEN a serializable cache must preserve the script behavior and a loaded cache must be reusable on the runner that loaded it.

## Script Evaluation and Contexts

This section defines how scripts consume caller state, compute results, and project assignment effects.

**Execution inputs and results.** An `Express4Runner` must be constructed with an `InitOptions` value.

String-script execution must accept a `Map<String,Object>`, a Java object, or an `ExpressContext` together with a `QLOptions` value.

`SerializableParseCache` execution must accept a `Map<String,Object>` or `ExpressContext` together with `QLOptions`.

`LoadedParseCache` execution must accept an `ExpressContext` together with `QLOptions`.

WHEN `execute` receives a `Map<String,Object>`, THEN map keys must resolve as script variables and `QLResult.getResult()` must return the final expression or explicit `return` value.

WHEN `execute` receives a Java object, THEN public fields or accessible bean properties must resolve by name subject to the runner's security strategy.

WHEN `executeWithAliasObjects` receives objects annotated with `QLAlias`, THEN every annotation value must expose that object under the corresponding variable name and unannotated objects must be ignored.

WHEN `execute` receives an `ExpressContext`, THEN the runner must obtain unresolved names through `ExpressContext.get(attachments, variableName)` and must use the returned `Value` as the variable projection.

IF script compilation or execution fails, THEN `execute` must raise the corresponding `QLException` subtype instead of returning a partial `QLResult`.

**Context mutation and dynamic values.** WHEN `polluteUserContext` is false, THEN assignments made by a map-backed script must remain local to that execution and the caller's map must retain its prior entries and values.

WHEN `polluteUserContext` is true, THEN global assignments must be written into the supplied map while function-local variables must remain local to their function scope.

A `DynamicVariableContext` must resolve names registered through `put(name, valueExpression)` by evaluating the stored expression against the same dynamic context, and it must fall back to its static map when no dynamic expression exists.

IF a required variable, function, field, method, index, constructor, or callable target is invalid, THEN execution must raise `QLRuntimeException` with a stable `QLErrorCodes` name and source diagnostic.

**Expression and statement rules.** Numeric arithmetic must preserve exact decimal comparison for decimal literals that binary floating point does not represent exactly, and `QLOptions.precise(true)` must perform numeric calculation through `BigDecimal` semantics.

String literals must accept single or double quotes, and `+` must concatenate when either operand follows the engine's string-concatenation rules.

List literals must preserve item order, map literals must preserve key-to-value lookup, indexing must read collection elements, and slice expressions must return the selected contiguous subsequence.

Logical `&&`, `||`, `and`, and `or` must short-circuit by default.

WHEN `shortCircuitDisable` is true, THEN both logical operands must be evaluated.

The language must support typed and untyped variables, assignment and compound assignment, conditionals, `while`, classic `for`, for-each, `break`, `continue`, `return`, `try`/`catch`/`final`, functions, lambdas, list `filter`/`map`, and non-fall-through switch statements or switch expressions.

WHEN strict newline mode is enabled, THEN adjacent statements without semicolons must be separated by a line break.

WHEN strict newline mode is disabled, THEN whitespace must separate adjacent statements without requiring a line break.

IF a condition or loop condition does not produce a boolean, THEN execution must raise `QLRuntimeException` rather than coerce the value.

## Options, Strings, and Templates

This section defines construction-time and per-run policy that changes observable parsing and execution behavior.

**Initialization policy.** `InitOptions.DEFAULT_OPTIONS` must use the default class supplier, imports for `java.lang`, `java.util`, `java.math`, `java.util.stream`, and `java.util.function`, isolation security, script interpolation, strict newlines, disabled debug output, disabled private access, and disabled expression tracing.

An `InitOptions.Builder` must expose `classSupplier`, `addDefaultImport`, `debug`, `debugInfoConsumer`, `securityStrategy`, `allowPrivateAccess`, `interpolationMode`, `traceExpression`, `selectorStart`, `selectorEnd`, and `strictNewLines`, and `build()` must retain those choices in the resulting options value.

WHEN `selectorStart` is supplied, THEN it must accept only `${`, `$[`, `#{`, or `#[`.

IF another selector-start token is supplied, THEN the builder must raise `IllegalArgumentException`.

WHEN `selectorEnd` is supplied, THEN it must be non-null and non-empty.

IF the selector-end precondition fails, THEN the builder must raise `IllegalArgumentException`.

**Execution policy.** `QLOptions.DEFAULT_OPTIONS` must disable precise mode, context pollution, compile caching, null avoidance, expression tracing, and short-circuit disabling.

`QLOptions.DEFAULT_OPTIONS` must use no timeout, no array-length limit, and an empty attachments map.

A `QLOptions.Builder` must expose `precise`, `polluteUserContext`, `timeoutMillis`, `attachments`, `cache`, `avoidNullPointer`, `maxArrLength`, `traceExpression`, and `shortCircuitDisable`, and `build()` must retain those values.

WHEN `attachments` are supplied, THEN `QContext.attachment()` must expose the same key/value data to custom functions, operators, macros, and extension callbacks without creating script variables.

WHEN `avoidNullPointer` is true, THEN undefined function or callable targets and null field, method, index, or slice receivers must project as null, while ordered comparisons involving null must return false.

WHEN a script attempts to allocate an array longer than a nonnegative `maxArrLength`, THEN execution must raise `QLRuntimeException` with the `EXCEED_MAX_ARR_LENGTH` code.

WHEN a positive `timeoutMillis` is exceeded at an engine check point, THEN execution must raise `QLTimeoutException`.

WHEN a positive timeout elapses inside a Java callback, THEN timeout state must be checked when control returns to the engine.

**Interpolation and templates.** `InterpolationMode.SCRIPT` must evaluate selector contents as script expressions, `InterpolationMode.VARIABLE` must resolve selector contents as variable names, and `InterpolationMode.DISABLE` must preserve selector text literally.

WHEN custom selector delimiters are configured, THEN dynamic strings and dependency inspection must use the configured start and end tokens.

WHEN `executeTemplate(template, context, options)` receives a non-null one-line template, THEN it must evaluate the template as dynamic string content using the same context and options while preserving ordinary text and escaped double quotes.

WHEN `executeTemplate` receives null, THEN it must return a `QLResult` whose result is the empty string.

IF the template contains an unsupported newline or invalid interpolation, THEN `executeTemplate` must raise `QLSyntaxException`.

## Validation and Dependency Inspection

This section defines parse-only checks and the public views of names supplied by a caller.

**Validation.** `check(script)` must validate syntax without executing the script, and `check(script, checkOptions)` must apply the supplied operator and function-call restrictions.

`CheckOptions.DEFAULT_OPTIONS` must allow all operators and function calls, while its builder must expose `operatorCheckStrategy` and `disableFunctionCalls`.

`OperatorCheckStrategy.allowAll()` must accept every recognized operator, `whitelist(operators)` must accept only listed operators, and `blacklist(operators)` must reject only listed operators.

IF syntax is malformed, a function call is disabled, or an operator is rejected, THEN `check` must raise `QLSyntaxException` with a diagnostic instead of executing any script code.

**Dependency views.** `getOutVarNames(script)` must return externally supplied variable names while excluding variables declared in the script, function parameters, imported classes, and functions.

`getOutVarAttrs(script)` must return each externally supplied variable access path as an ordered list of path segments while excluding paths rooted in script-local variables.

`getOutFunctions(script)` must return called function names that are not defined by the same script in a visible scope.

IF dependency inspection receives malformed script text, THEN it must raise `QLSyntaxException` rather than return a partial dependency set.

## Functions, Operators, Macros, and Aliases

This section defines runner-scoped extensions and how their registrations participate in later compilation and execution.

**Functions.** WHEN `addFunction`, `addVarArgsFunction`, or `addFunctionOfServiceMethod` registers a previously unused name, THEN the operation must return true and later calls by that name must invoke the registered implementation.

WHEN a function name already exists, THEN the non-replacing registration must return false and retain the first registration.

A `CustomFunction` must receive the current `QContext` and indexed `Parameters`.

`Parameters.getValue(index)` must unwrap the corresponding `Value`, and an out-of-range parameter lookup must return null.

A `LazyArgCustomFunction` must receive lazy argument wrappers at indexes for which `isLazyArg(index)` returns true, and an unevaluated wrapper must not trigger the argument's side effects.

WHEN `addObjFunction(object)` scans public methods or `addStaticFunction(type)` scans public static methods annotated with `QLFunction`, THEN every annotation value must become a function name and `BatchAddFunctionResult` must separate successful and duplicate registrations through `getSucc()` and `getFail()`.

IF `addFunctionOfServiceMethod` receives a null service, a null method name, or no matching public method, THEN it must raise `IllegalArgumentException`.

**Operators and extension functions.** WHEN `addOperator` or `addOperatorBiFunction` registers a new token, THEN the token must evaluate through the supplied implementation at the configured `QLPrecedences` level.

WHEN `replaceDefaultOperator` receives an existing built-in token, THEN it must return true and later uncached compilations must use the replacement.

WHEN the built-in token is absent, THEN `replaceDefaultOperator` must return false.

WHEN `addExtendFunction` binds a name to a declaring class, THEN scripts must invoke it with member-call syntax and the receiver must precede explicit arguments under the `QLFunctionalVarargs` convention.

An `ExtensionFunction` must identify its `getName`, `getDeclaringClass`, and `getParameterTypes` projections and must execute through `invoke(receiver, arguments)`; its base `isVarArgs()` projection must return false and `isAccess()` must return true.

IF a custom function or operator raises `UserDefineException`, THEN execution must translate its `ExceptionType` to the matching public error-code projection.

IF another callback exception escapes, THEN `QLRuntimeException` must retain it as the cause.

**Macros and aliases.** WHEN `addMacro(name, script)` registers a new macro name, THEN it must return true.

WHEN the macro name exists, THEN `addMacro` must return false and retain the existing macro.

`addOrReplaceMacro(name, script)` must replace an existing macro definition, and a macro invocation must replay its script in the caller's scope so its assignments and control flow affect that scope.

WHEN `addAlias(alias, originToken)` maps a valid alias to a supported keyword, operator, or registered function, THEN it must return true and scripts must treat the alias as the original token.

IF no alias mapping target exists, THEN `addAlias` must return false.

## Security and Java Interoperation

This section defines controlled access to Java classes and members from scripts.

**Security strategies.** `QLSecurityStrategy.isolation()` must deny Java field and method access, `open()` must permit all members, `blackList(members)` must permit members outside the set, and `whiteList(members)` must permit only members inside the set.

WHEN a script attempts member access rejected by the active strategy, THEN execution must raise `QLRuntimeException` instead of returning the member value.

**Imports and class loading.** `ImportManager.importCls(path)` must describe one class import, `importPack(path)` must describe package lookup, `importInnerCls(path)` must describe nested-class lookup, and `importClsAlias(type, alias)` must bind the supplied class without reloading it by name.

WHEN `importClsAlias` receives null class data, an empty alias, or an alias whose first character is not uppercase, THEN it must raise `IllegalArgumentException`.

A `ClassSupplier` must resolve a qualified class name to a `Class` or null, and `DefaultClassSupplier.getInstance()` must reuse cached successful and unsuccessful lookups.

WHEN an import or custom class supplier resolves a class and the security strategy permits its use, THEN scripts must construct the class or invoke its public static and instance members through the imported name.

## Compilation, Serializable Caches, and Tracing

This section defines reusable compilation projections and the relationship between compile-time trace points and execution-time traces.

**Runner-local compilation.** WHEN `QLOptions.cache` is true, THEN the runner must reuse the compiled form for equal script text.

`parseToDefinitionWithCache(script)` must prepopulate the same runner-local cache used by cached execution.

`clearCompileCache()` must discard runner-local compiled forms so the next cached execution recompiles the script without removing functions, operators, macros, aliases, or initialization policy.

**Serializable precompilation.** `parseToSerializableCache(script)` must return a JavaBean graph rooted at `SerializableParseCache` with model version, producer version, original script, script hash, main lambda definition, instructions, constants, sources, and optional trace points sufficient for JSON round trip without a runtime JSON dependency.

WHEN a compatible `SerializableParseCache` is loaded, THEN `loadSerializableCache` must return a `LoadedParseCache` bound to that runner and repeated execution with different contexts must preserve the original script semantics.

WHEN a serializable or loaded cache contains function definitions, THEN `addFunctionsDefinedInScript` must install them into the consumer runner and report newly installed and duplicate names separately.

IF a serializable cache has an unsupported model version, malformed bean graph, unsupported instruction or constant, missing class, or missing operator, THEN loading must raise `SerializableParseCacheException` with the corresponding `QLErrorCodes` value and diagnostic.

**Tracing.** `getExpressionTracePoints(script)` must return pre-execution trees whose nodes expose `TraceType`, token, children, line, column, and character position.

WHEN both `InitOptions.traceExpression` and `QLOptions.traceExpression` are true, THEN `QLResult.getExpressionTraces()` must return execution trees whose nodes additionally expose value and evaluated state.

WHEN a trace node is short-circuited, THEN its `isEvaluated()` projection must return false.

WHEN initialization tracing is disabled or a serialized cache contains no trace points, THEN execution must not fabricate execution traces.

## State Model

The core state is runner configuration plus runner-scoped extension registries, macro definitions, aliases, and an optional compile cache. Per-execution state consists of the script or precompiled form, context, options, runtime scopes, result, diagnostics, and trace values.

The public projections are:

1. `QLResult.getResult()` and `getExpressionTraces()`.
2. Caller map write-back or `ExpressContext` resolution.
3. Dependency sets from `getOutVarNames`, `getOutVarAttrs`, and `getOutFunctions`.
4. Registration results from booleans and `BatchAddFunctionResult`.
5. `QLException` and its `Diagnostic`, `Range`, `Position`, error code, lexeme, reason, and one-based convenience coordinates.
6. Runner-local cache reuse and the serializable/loaded cache projections.

Runner initialization policy and extension registries must persist across executions until explicitly changed, while per-execution context, timeout, attachments, trace values, and local variables must not leak into later executions.

## Error Semantics

| Condition | Required result |
|---|---|
| Malformed script or rejected validation rule | WHEN a script is malformed or a validation rule rejects it, THEN the operation must raise `QLSyntaxException`. |
| Runtime type, member, index, call, condition, allocation, or arithmetic failure | WHEN a runtime type, member, index, call, condition, allocation, or arithmetic failure occurs, THEN execution must raise `QLRuntimeException`. |
| Positive timeout exceeded at an engine check point | WHEN a positive timeout is exceeded at an engine check point, THEN execution must raise `QLTimeoutException`. |
| Invalid serializable cache model or missing binding | WHEN a serializable cache model is invalid or a required binding is missing, THEN loading must raise `SerializableParseCacheException`. |
| Invalid selector delimiter or class alias | WHEN a selector delimiter or class alias violates its documented precondition, THEN construction must raise `IllegalArgumentException`. |
| Missing public service method registration target | WHEN a public service-method registration target is missing, THEN registration must raise `IllegalArgumentException`. |
| Rejected Java member access | WHEN the security strategy rejects Java member access, THEN execution must raise `QLRuntimeException`. |
| Callback raises `UserDefineException` | WHEN a callback raises `UserDefineException`, THEN execution must project `INVALID_ARGUMENT` or `BIZ_EXCEPTION` through `QLException`. |

Every `QLException` must expose `getDiagnostic`, `getPos`, `getReason`, `getLineNo`, `getColNo`, `getErrLexeme`, and `getErrorCode`.

`QLException.getLineNo()` and `getColNo()` must be one-based while `Diagnostic.Range.Position` values must be zero-based.

WHEN a Java member invocation or callback wraps another throwable, THEN `QLRuntimeException.getCause()` or `getCatchObj()` must retain the originating object where the public error path provides it.

## Cross-View Invariants

1. The value returned by direct script execution must equal the value returned by executing its compatible `SerializableParseCache` and same-runner `LoadedParseCache` under equivalent runner configuration and context.
2. Names returned by dependency inspection must be exactly the context variables or externally supplied functions required by execution after script-local definitions, imports, and registrations are accounted for.
3. WHEN `polluteUserContext` is true, THEN assignments visible in the final result must agree with the corresponding entries written to the caller's map.
4. WHEN `polluteUserContext` is false, THEN the result must use execution-local assignments without changing the caller's map.
5. A registered function, operator, extension function, macro, or alias must affect later compilation, direct execution, cached execution, and serializable-cache consumption consistently when the consumer runner has an equivalent registration environment.
6. A validation failure reported by `check` must prevent the same malformed or restricted script from producing a successful execution result under the same restriction policy.
7. Trace-point source coordinates, execution-trace nodes, and `QLException` diagnostics must refer to the same original script coordinate system even after serializable-cache round trip.
8. Clearing the runner-local compile cache must not change script results, dependency inspection, extension registrations, initialization options, or serializable-cache semantics.
9. Security strategy decisions must agree across object contexts, alias-object contexts, imported classes, extension dispatch, and scripts loaded from compatible precompiled caches.

## Public Interface

### Import Surface

```java
import com.alibaba.qlexpress4.CheckOptions;
import com.alibaba.qlexpress4.ClassSupplier;
import com.alibaba.qlexpress4.DefaultClassSupplier;
import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.InitOptions;
import com.alibaba.qlexpress4.QLOptions;
import com.alibaba.qlexpress4.QLPrecedences;
import com.alibaba.qlexpress4.QLResult;
```

```java
import com.alibaba.qlexpress4.annotation.QLAlias;
import com.alibaba.qlexpress4.annotation.QLFunction;
import com.alibaba.qlexpress4.api.BatchAddFunctionResult;
import com.alibaba.qlexpress4.api.QLFunctionalVarargs;
import com.alibaba.qlexpress4.aparser.ImportManager;
import com.alibaba.qlexpress4.aparser.InterpolationMode;
import com.alibaba.qlexpress4.operator.OperatorCheckStrategy;
import com.alibaba.qlexpress4.security.QLSecurityStrategy;
```

```java
import com.alibaba.qlexpress4.runtime.Parameters;
import com.alibaba.qlexpress4.runtime.QContext;
import com.alibaba.qlexpress4.runtime.Value;
import com.alibaba.qlexpress4.runtime.context.DynamicVariableContext;
import com.alibaba.qlexpress4.runtime.context.ExpressContext;
import com.alibaba.qlexpress4.runtime.context.MapExpressContext;
import com.alibaba.qlexpress4.runtime.function.CustomFunction;
import com.alibaba.qlexpress4.runtime.function.ExtensionFunction;
import com.alibaba.qlexpress4.runtime.function.LazyArgCustomFunction;
import com.alibaba.qlexpress4.runtime.operator.CustomBinaryOperator;
import com.alibaba.qlexpress4.runtime.trace.ExpressionTrace;
import com.alibaba.qlexpress4.runtime.trace.TracePointTree;
import com.alibaba.qlexpress4.runtime.trace.TraceType;
```

```java
import com.alibaba.qlexpress4.api.parsecache.LoadedParseCache;
import com.alibaba.qlexpress4.api.parsecache.SerializableCatchEntry;
import com.alibaba.qlexpress4.api.parsecache.SerializableConstant;
import com.alibaba.qlexpress4.api.parsecache.SerializableInstruction;
import com.alibaba.qlexpress4.api.parsecache.SerializableLambdaDefinition;
import com.alibaba.qlexpress4.api.parsecache.SerializableParam;
import com.alibaba.qlexpress4.api.parsecache.SerializableParseCache;
import com.alibaba.qlexpress4.api.parsecache.SerializableParseCacheException;
import com.alibaba.qlexpress4.api.parsecache.SerializableSource;
import com.alibaba.qlexpress4.api.parsecache.SerializableTracePoint;
```

```java
import com.alibaba.qlexpress4.exception.QLErrorCodes;
import com.alibaba.qlexpress4.exception.QLException;
import com.alibaba.qlexpress4.exception.QLRuntimeException;
import com.alibaba.qlexpress4.exception.QLSyntaxException;
import com.alibaba.qlexpress4.exception.QLTimeoutException;
import com.alibaba.qlexpress4.exception.UserDefineException;
import com.alibaba.qlexpress4.exception.lsp.Diagnostic;
import com.alibaba.qlexpress4.exception.lsp.Position;
import com.alibaba.qlexpress4.exception.lsp.Range;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Express4Runner` | class | Runner for validation, dependency inspection, extension registration, compilation, and execution. |
| `InitOptions` | class | Runner initialization policy with a fluent builder and default value. |
| `QLOptions` | class | Per-execution policy with a fluent builder and default value. |
| `CheckOptions` | class | Parse-only restriction policy with a fluent builder and default value. |
| `QLResult` | class | Execution result and optional expression-trace projection. |
| `QLPrecedences` | class | Named integer precedence constants for custom operators. |
| `ClassSupplier` | interface | Qualified-class resolver used by imports and Java interoperation. |
| `DefaultClassSupplier` | class | Cached default class resolver singleton. |
| `QLFunctionalVarargs` | interface | Varargs callback shared by functions, operators, and extension functions. |
| `BatchAddFunctionResult` | class | Successful and duplicate function-registration names. |
| `QLAlias` | annotation | Runtime aliases for public types, fields, and methods. |
| `QLFunction` | annotation | Runtime names for public Java methods registered as script functions. |
| `ImportManager` | class | Factories for class, package, nested-class, and class-alias imports. |
| `InterpolationMode` | enum | Script-expression, variable-name, or disabled interpolation policy. |
| `OperatorCheckStrategy` | interface | Allow-all, whitelist, and blacklist operator-validation policy. |
| `QLSecurityStrategy` | interface | Isolation, open, member-blacklist, and member-whitelist policy. |
| `ExpressContext` | interface | Attachment-aware variable-resolution contract. |
| `DynamicVariableContext` | class | Context combining a static map with expression-backed dynamic variables. |
| `MapExpressContext` | class | `ExpressContext` backed by a mutable map. |
| `CustomFunction` | interface | Context-aware indexed-parameter callback. |
| `LazyArgCustomFunction` | interface | Custom function that selects lazy argument indexes. |
| `ExtensionFunction` | abstract class | Java-member-shaped callback exposed through script member syntax. |
| `CustomBinaryOperator` | interface | Binary callback over left and right `Value` operands. |
| `QContext` | interface | Current execution context exposed to custom functions. |
| `Parameters` | interface | Indexed callback parameters with boxed and unboxed access. |
| `Value` | interface | Boxed runtime value and type projection. |
| `ExpressionTrace` | class | Execution trace node with source, value, evaluated state, and children. |
| `TracePointTree` | class | Pre-execution expression tree with source coordinates. |
| `TraceType` | enum | Public trace-node category vocabulary. |
| `SerializableParseCache` | class | JSON-friendly root for a portable precompiled script. |
| `LoadedParseCache` | class | Runner-bound reusable compiled form loaded from a serializable cache. |
| `SerializableLambdaDefinition` | class | Bean carrier for lambda metadata, parameters, and instructions. |
| `SerializableInstruction` | class | Bean carrier for opcode, operands, and source location. |
| `SerializableConstant` | class | Bean carrier for typed constant data. |
| `SerializableTracePoint` | class | Bean carrier for trace-node structure and source location. |
| `SerializableSource` | class | Bean carrier for instruction source coordinates and lexeme. |
| `SerializableParam` | class | Bean carrier for parameter name and class name. |
| `SerializableCatchEntry` | class | Bean carrier for catch-table metadata. |
| `SerializableParseCacheException` | exception | Cache-model validation and binding error. |
| `QLException` | exception | Base script exception with structured diagnostics. |
| `QLSyntaxException` | exception | Compilation or validation syntax error. |
| `QLRuntimeException` | exception | Runtime script error with optional caught object. |
| `QLTimeoutException` | exception | Runtime timeout error. |
| `UserDefineException` | exception | Callback-defined invalid-argument or business failure. |
| `QLErrorCodes` | enum | Stable public error-code names. |
| `Diagnostic` | class | Error position, range, lexeme, code, reason, and snippet projection. |
| `Range` | class | Start and end diagnostic positions. |
| `Position` | class | Zero-based line and character coordinates. |

### Public Member Index

| Type | Public members in scope |
|---|---|
| `Express4Runner` | constructor; `getFunction`; documented `execute` overloads; `executeTemplate`; `executeWithAliasObjects`; `getOutVarNames`; `getOutVarAttrs`; `getOutFunctions`; `getExpressionTracePoints`; `check`; `addMacro`; `addOrReplaceMacro`; `addFunction`; `addVarArgsFunction`; `addFunctionOfServiceMethod`; `addFunctionsDefinedInScript`; `addObjFunction`; `addStaticFunction`; `addExtendFunction`; `parseToSerializableCache`; `loadSerializableCache`; `parseToDefinitionWithCache`; `clearCompileCache`; `addOperatorBiFunction`; `addOperator`; `replaceDefaultOperator`; `addAlias`. |
| `InitOptions` | `DEFAULT_OPTIONS`; `builder`; `getDefaultImport`; `getClassSupplier`; `isDebug`; `getDebugInfoConsumer`; `getSecurityStrategy`; `isAllowPrivateAccess`; `getInterpolationMode`; `isTraceExpression`; `getSelectorStart`; `getSelectorEnd`; `isStrictNewLines`; builder setters named in the behavior section; `build`. |
| `QLOptions` | `DEFAULT_OPTIONS`; `builder`; `isPrecise`; `isPolluteUserContext`; `getTimeoutMillis`; `getAttachments`; `isCache`; `isAvoidNullPointer`; `getMaxArrLength`; `checkArrLen`; `isTraceExpression`; `isShortCircuitDisable`; builder setters named in the behavior section; `build`. |
| `CheckOptions` | `DEFAULT_OPTIONS`; `builder`; `getCheckStrategy`; `isDisableFunctionCalls`; builder setters; `build`. |
| `QLResult` | constructor; `getResult`; `getExpressionTraces`. |
| `BatchAddFunctionResult` | constructor; `getSucc`; `getFail`. |
| `QLPrecedences` | `ASSIGN`; `TERNARY`; `OR`; `AND`; `BIT_OR`; `XOR`; `BIT_AND`; `EQUAL`; `COMPARE`; `BIT_MOVE`; `IN_LIKE`; `ADD`; `MULTI`; `UNARY`; `UNARY_SUFFIX`; `GROUP`. |
| `ClassSupplier` and `DefaultClassSupplier` | `loadCls`; `getInstance`. |
| `QLAlias` and `QLFunction` | `value`. |
| `ImportManager` | `importCls`; `importPack`; `importInnerCls`; `importClsAlias`; `QLImport` accessors. |
| `OperatorCheckStrategy` | `allowAll`; `whitelist`; `blacklist`; `isAllowed`; `getOperators`. |
| `QLSecurityStrategy` | `open`; `isolation`; `blackList`; `whiteList`; `check`. |
| `ExpressContext` | `EMPTY_CONTEXT`; `get`. |
| `DynamicVariableContext` | documented constructors; `put`; `get`. |
| `MapExpressContext` | map constructor; `get`. |
| Callback interfaces | `QLFunctionalVarargs.call`; `CustomFunction.call`; `LazyArgCustomFunction.isLazyArg`; `ExtensionFunction.getParameterTypes`; `isVarArgs`; `isAccess`; `setAccessible`; `getName`; `getDeclaringClass`; `invoke`; `CustomBinaryOperator.execute`; `QContext.attachment`; `Parameters.get`; `getValue`; `size`; `Value.get`; `getType`; `getTypeName`. |
| Trace types | constructors and getters; `ExpressionTrace.isEvaluated`; `toPrettyString`; `TraceType` values `OPERATOR`, `FUNCTION`, `METHOD`, `FIELD`, `LIST`, `MAP`, `IF`, `SWITCH`, `RETURN`, `BLOCK`, `VARIABLE`, `VALUE`, `DEFINE_FUNCTION`, `DEFINE_MACRO`, `PRIMARY`, and `STATEMENT`. |
| Cache bean family | public no-argument constructors where present and bean getters/setters for the fields described in Serializable Precompilation. |
| `LoadedParseCache` | metadata getters; `hasTracePoints`; `getSourceCache`; `isBoundTo`. |
| `QLException` family | diagnostic accessors described in Error Semantics; `QLRuntimeException.getCatchObj`; `UserDefineException.getType`; `QLErrorCodes.getErrorMsg` and the error-code values named in the behavior and error sections. |
| LSP diagnostic types | constructors and getters for all cataloged fields. |

### CLI Entry Points

There is no console script, executable main class, or Maven plugin goal for this artifact. Programmatic use is through Java imports and the Maven dependency.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. Maven 3 resolves locally cached build and test artifacts. The target library has no production third-party dependency; assessment tests receive JUnit 4 from the private test project.

The project must declare `com.alibaba` as `groupId`, `qlexpress4` as `artifactId`, `4.1.3` as `version`, JAR packaging, and Java source and target level 8 in a standard root `pom.xml`.

The implementation source must live under `src/main/java`, and runtime resources must live under `src/main/resources` when present.

## Appendix B: Assessment Notes

Assessment exercises the documented public Java surface through Maven tests. Coverage spans script and template evaluation, context projection and mutation, options, dependency inspection, validation restrictions, functions/operators/macros/aliases, security policy, diagnostics, tracing, compile-cache behavior, serializable-cache round trips, and cross-view consistency. The maximum retained assessment set is 120 deterministic cases. Private structure, generated parser symbols, exact message text, debug wording, external framework adapters, and security-sensitive I/O are not assessed.
