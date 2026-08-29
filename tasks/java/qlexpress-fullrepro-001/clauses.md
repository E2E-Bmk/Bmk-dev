# Clause map — qlexpress-fullrepro-001 spec v1

Each entry maps a stable clause ID to the verbatim behavioral sentence in `spec_v1.md` and its section anchor.

## Representative Workflows

**QLX-WF-001** — `#evaluate-a-rule-and-observe-context-state`

> WHEN a map-backed execution succeeds with `polluteUserContext` enabled, THEN the runner must return the final script value and must write global assignments into the supplied map.

**QLX-WF-002** — `#register-domain-operations-and-inspect-dependencies`

> WHEN a registered function or operator is referenced by a later script, THEN execution must dispatch to that registration and dependency inspection must report only unresolved external variables or functions.

**QLX-WF-003** — `#move-a-precompiled-script-between-equivalent-runners`

> WHEN producer and consumer runners have equivalent imports, extensions, operators, class loading, tracing policy, and security policy, THEN a serializable cache must preserve the script behavior and a loaded cache must be reusable on the runner that loaded it.

## Script Evaluation and Contexts

**QLX-EXEC-001** — `#script-evaluation-and-contexts`

> An `Express4Runner` must be constructed with an `InitOptions` value.

**QLX-EXEC-020** — `#script-evaluation-and-contexts`

> String-script execution must accept a `Map<String,Object>`, a Java object, or an `ExpressContext` together with a `QLOptions` value.

**QLX-EXEC-021** — `#script-evaluation-and-contexts`

> `SerializableParseCache` execution must accept a `Map<String,Object>` or `ExpressContext` together with `QLOptions`.

**QLX-EXEC-022** — `#script-evaluation-and-contexts`

> `LoadedParseCache` execution must accept an `ExpressContext` together with `QLOptions`.

**QLX-EXEC-002** — `#script-evaluation-and-contexts`

> WHEN `execute` receives a `Map<String,Object>`, THEN map keys must resolve as script variables and `QLResult.getResult()` must return the final expression or explicit `return` value.

**QLX-EXEC-003** — `#script-evaluation-and-contexts`

> WHEN `execute` receives a Java object, THEN public fields or accessible bean properties must resolve by name subject to the runner's security strategy.

**QLX-EXEC-004** — `#script-evaluation-and-contexts`

> WHEN `executeWithAliasObjects` receives objects annotated with `QLAlias`, THEN every annotation value must expose that object under the corresponding variable name and unannotated objects must be ignored.

**QLX-EXEC-005** — `#script-evaluation-and-contexts`

> WHEN `execute` receives an `ExpressContext`, THEN the runner must obtain unresolved names through `ExpressContext.get(attachments, variableName)` and must use the returned `Value` as the variable projection.

**QLX-EXEC-006** — `#script-evaluation-and-contexts`

> IF script compilation or execution fails, THEN `execute` must raise the corresponding `QLException` subtype instead of returning a partial `QLResult`.

**QLX-EXEC-007** — `#script-evaluation-and-contexts`

> WHEN `polluteUserContext` is false, THEN assignments made by a map-backed script must remain local to that execution and the caller's map must retain its prior entries and values.

**QLX-EXEC-008** — `#script-evaluation-and-contexts`

> WHEN `polluteUserContext` is true, THEN global assignments must be written into the supplied map while function-local variables must remain local to their function scope.

**QLX-EXEC-009** — `#script-evaluation-and-contexts`

> A `DynamicVariableContext` must resolve names registered through `put(name, valueExpression)` by evaluating the stored expression against the same dynamic context, and it must fall back to its static map when no dynamic expression exists.

**QLX-EXEC-010** — `#script-evaluation-and-contexts`

> IF a required variable, function, field, method, index, constructor, or callable target is invalid, THEN execution must raise `QLRuntimeException` with a stable `QLErrorCodes` name and source diagnostic.

**QLX-EXEC-011** — `#script-evaluation-and-contexts`

> Numeric arithmetic must preserve exact decimal comparison for decimal literals that binary floating point does not represent exactly, and `QLOptions.precise(true)` must perform numeric calculation through `BigDecimal` semantics.

**QLX-EXEC-012** — `#script-evaluation-and-contexts`

> String literals must accept single or double quotes, and `+` must concatenate when either operand follows the engine's string-concatenation rules.

**QLX-EXEC-013** — `#script-evaluation-and-contexts`

> List literals must preserve item order, map literals must preserve key-to-value lookup, indexing must read collection elements, and slice expressions must return the selected contiguous subsequence.

**QLX-EXEC-014** — `#script-evaluation-and-contexts`

> Logical `&&`, `||`, `and`, and `or` must short-circuit by default.

**QLX-EXEC-015** — `#script-evaluation-and-contexts`

> WHEN `shortCircuitDisable` is true, THEN both logical operands must be evaluated.

**QLX-EXEC-016** — `#script-evaluation-and-contexts`

> The language must support typed and untyped variables, assignment and compound assignment, conditionals, `while`, classic `for`, for-each, `break`, `continue`, `return`, `try`/`catch`/`final`, functions, lambdas, list `filter`/`map`, and non-fall-through switch statements or switch expressions.

**QLX-EXEC-017** — `#script-evaluation-and-contexts`

> WHEN strict newline mode is enabled, THEN adjacent statements without semicolons must be separated by a line break.

**QLX-EXEC-018** — `#script-evaluation-and-contexts`

> WHEN strict newline mode is disabled, THEN whitespace must separate adjacent statements without requiring a line break.

**QLX-EXEC-019** — `#script-evaluation-and-contexts`

> IF a condition or loop condition does not produce a boolean, THEN execution must raise `QLRuntimeException` rather than coerce the value.

## Options, Strings, and Templates

**QLX-OPT-001** — `#options-strings-and-templates`

> `InitOptions.DEFAULT_OPTIONS` must use the default class supplier, imports for `java.lang`, `java.util`, `java.math`, `java.util.stream`, and `java.util.function`, isolation security, script interpolation, strict newlines, disabled debug output, disabled private access, and disabled expression tracing.

**QLX-OPT-002** — `#options-strings-and-templates`

> An `InitOptions.Builder` must expose `classSupplier`, `addDefaultImport`, `debug`, `debugInfoConsumer`, `securityStrategy`, `allowPrivateAccess`, `interpolationMode`, `traceExpression`, `selectorStart`, `selectorEnd`, and `strictNewLines`, and `build()` must retain those choices in the resulting options value.

**QLX-OPT-003** — `#options-strings-and-templates`

> WHEN `selectorStart` is supplied, THEN it must accept only `${`, `$[`, `#{`, or `#[`.

**QLX-OPT-004** — `#options-strings-and-templates`

> IF another selector-start token is supplied, THEN the builder must raise `IllegalArgumentException`.

**QLX-OPT-005** — `#options-strings-and-templates`

> WHEN `selectorEnd` is supplied, THEN it must be non-null and non-empty.

**QLX-OPT-006** — `#options-strings-and-templates`

> IF the selector-end precondition fails, THEN the builder must raise `IllegalArgumentException`.

**QLX-OPT-007** — `#options-strings-and-templates`

> `QLOptions.DEFAULT_OPTIONS` must disable precise mode, context pollution, compile caching, null avoidance, expression tracing, and short-circuit disabling.

**QLX-OPT-008** — `#options-strings-and-templates`

> `QLOptions.DEFAULT_OPTIONS` must use no timeout, no array-length limit, and an empty attachments map.

**QLX-OPT-009** — `#options-strings-and-templates`

> A `QLOptions.Builder` must expose `precise`, `polluteUserContext`, `timeoutMillis`, `attachments`, `cache`, `avoidNullPointer`, `maxArrLength`, `traceExpression`, and `shortCircuitDisable`, and `build()` must retain those values.

**QLX-OPT-010** — `#options-strings-and-templates`

> WHEN `attachments` are supplied, THEN `QContext.attachment()` must expose the same key/value data to custom functions, operators, macros, and extension callbacks without creating script variables.

**QLX-OPT-011** — `#options-strings-and-templates`

> WHEN `avoidNullPointer` is true, THEN undefined function or callable targets and null field, method, index, or slice receivers must project as null, while ordered comparisons involving null must return false.

**QLX-OPT-012** — `#options-strings-and-templates`

> WHEN a script attempts to allocate an array longer than a nonnegative `maxArrLength`, THEN execution must raise `QLRuntimeException` with the `EXCEED_MAX_ARR_LENGTH` code.

**QLX-OPT-013** — `#options-strings-and-templates`

> WHEN a positive `timeoutMillis` is exceeded at an engine check point, THEN execution must raise `QLTimeoutException`.

**QLX-OPT-014** — `#options-strings-and-templates`

> WHEN a positive timeout elapses inside a Java callback, THEN timeout state must be checked when control returns to the engine.

**QLX-OPT-015** — `#options-strings-and-templates`

> `InterpolationMode.SCRIPT` must evaluate selector contents as script expressions, `InterpolationMode.VARIABLE` must resolve selector contents as variable names, and `InterpolationMode.DISABLE` must preserve selector text literally.

**QLX-OPT-016** — `#options-strings-and-templates`

> WHEN custom selector delimiters are configured, THEN dynamic strings and dependency inspection must use the configured start and end tokens.

**QLX-OPT-017** — `#options-strings-and-templates`

> WHEN `executeTemplate(template, context, options)` receives a non-null one-line template, THEN it must evaluate the template as dynamic string content using the same context and options while preserving ordinary text and escaped double quotes.

**QLX-OPT-018** — `#options-strings-and-templates`

> WHEN `executeTemplate` receives null, THEN it must return a `QLResult` whose result is the empty string.

**QLX-OPT-019** — `#options-strings-and-templates`

> IF the template contains an unsupported newline or invalid interpolation, THEN `executeTemplate` must raise `QLSyntaxException`.

## Validation and Dependency Inspection

**QLX-VAL-001** — `#validation-and-dependency-inspection`

> `check(script)` must validate syntax without executing the script, and `check(script, checkOptions)` must apply the supplied operator and function-call restrictions.

**QLX-VAL-002** — `#validation-and-dependency-inspection`

> `CheckOptions.DEFAULT_OPTIONS` must allow all operators and function calls, while its builder must expose `operatorCheckStrategy` and `disableFunctionCalls`.

**QLX-VAL-003** — `#validation-and-dependency-inspection`

> `OperatorCheckStrategy.allowAll()` must accept every recognized operator, `whitelist(operators)` must accept only listed operators, and `blacklist(operators)` must reject only listed operators.

**QLX-VAL-004** — `#validation-and-dependency-inspection`

> IF syntax is malformed, a function call is disabled, or an operator is rejected, THEN `check` must raise `QLSyntaxException` with a diagnostic instead of executing any script code.

**QLX-VAL-005** — `#validation-and-dependency-inspection`

> `getOutVarNames(script)` must return externally supplied variable names while excluding variables declared in the script, function parameters, imported classes, and functions.

**QLX-VAL-006** — `#validation-and-dependency-inspection`

> `getOutVarAttrs(script)` must return each externally supplied variable access path as an ordered list of path segments while excluding paths rooted in script-local variables.

**QLX-VAL-007** — `#validation-and-dependency-inspection`

> `getOutFunctions(script)` must return called function names that are not defined by the same script in a visible scope.

**QLX-VAL-008** — `#validation-and-dependency-inspection`

> IF dependency inspection receives malformed script text, THEN it must raise `QLSyntaxException` rather than return a partial dependency set.

## Functions, Operators, Macros, and Aliases

**QLX-EXT-001** — `#functions-operators-macros-and-aliases`

> WHEN `addFunction`, `addVarArgsFunction`, or `addFunctionOfServiceMethod` registers a previously unused name, THEN the operation must return true and later calls by that name must invoke the registered implementation.

**QLX-EXT-002** — `#functions-operators-macros-and-aliases`

> WHEN a function name already exists, THEN the non-replacing registration must return false and retain the first registration.

**QLX-EXT-003** — `#functions-operators-macros-and-aliases`

> A `CustomFunction` must receive the current `QContext` and indexed `Parameters`.

**QLX-EXT-004** — `#functions-operators-macros-and-aliases`

> `Parameters.getValue(index)` must unwrap the corresponding `Value`, and an out-of-range parameter lookup must return null.

**QLX-EXT-005** — `#functions-operators-macros-and-aliases`

> A `LazyArgCustomFunction` must receive lazy argument wrappers at indexes for which `isLazyArg(index)` returns true, and an unevaluated wrapper must not trigger the argument's side effects.

**QLX-EXT-006** — `#functions-operators-macros-and-aliases`

> WHEN `addObjFunction(object)` scans public methods or `addStaticFunction(type)` scans public static methods annotated with `QLFunction`, THEN every annotation value must become a function name and `BatchAddFunctionResult` must separate successful and duplicate registrations through `getSucc()` and `getFail()`.

**QLX-EXT-007** — `#functions-operators-macros-and-aliases`

> IF `addFunctionOfServiceMethod` receives a null service, a null method name, or no matching public method, THEN it must raise `IllegalArgumentException`.

**QLX-EXT-008** — `#functions-operators-macros-and-aliases`

> WHEN `addOperator` or `addOperatorBiFunction` registers a new token, THEN the token must evaluate through the supplied implementation at the configured `QLPrecedences` level.

**QLX-EXT-009** — `#functions-operators-macros-and-aliases`

> WHEN `replaceDefaultOperator` receives an existing built-in token, THEN it must return true and later uncached compilations must use the replacement.

**QLX-EXT-010** — `#functions-operators-macros-and-aliases`

> WHEN the built-in token is absent, THEN `replaceDefaultOperator` must return false.

**QLX-EXT-011** — `#functions-operators-macros-and-aliases`

> WHEN `addExtendFunction` binds a name to a declaring class, THEN scripts must invoke it with member-call syntax and the receiver must precede explicit arguments under the `QLFunctionalVarargs` convention.

**QLX-EXT-012** — `#functions-operators-macros-and-aliases`

> An `ExtensionFunction` must identify its `getName`, `getDeclaringClass`, and `getParameterTypes` projections and must execute through `invoke(receiver, arguments)`; its base `isVarArgs()` projection must return false and `isAccess()` must return true.

**QLX-EXT-013** — `#functions-operators-macros-and-aliases`

> IF a custom function or operator raises `UserDefineException`, THEN execution must translate its `ExceptionType` to the matching public error-code projection.

**QLX-EXT-014** — `#functions-operators-macros-and-aliases`

> IF another callback exception escapes, THEN `QLRuntimeException` must retain it as the cause.

**QLX-EXT-015** — `#functions-operators-macros-and-aliases`

> WHEN `addMacro(name, script)` registers a new macro name, THEN it must return true.

**QLX-EXT-016** — `#functions-operators-macros-and-aliases`

> WHEN the macro name exists, THEN `addMacro` must return false and retain the existing macro.

**QLX-EXT-017** — `#functions-operators-macros-and-aliases`

> `addOrReplaceMacro(name, script)` must replace an existing macro definition, and a macro invocation must replay its script in the caller's scope so its assignments and control flow affect that scope.

**QLX-EXT-018** — `#functions-operators-macros-and-aliases`

> WHEN `addAlias(alias, originToken)` maps a valid alias to a supported keyword, operator, or registered function, THEN it must return true and scripts must treat the alias as the original token.

**QLX-EXT-019** — `#functions-operators-macros-and-aliases`

> IF no alias mapping target exists, THEN `addAlias` must return false.

## Security and Java Interoperation

**QLX-SEC-001** — `#security-and-java-interoperation`

> `QLSecurityStrategy.isolation()` must deny Java field and method access, `open()` must permit all members, `blackList(members)` must permit members outside the set, and `whiteList(members)` must permit only members inside the set.

**QLX-SEC-002** — `#security-and-java-interoperation`

> WHEN a script attempts member access rejected by the active strategy, THEN execution must raise `QLRuntimeException` instead of returning the member value.

**QLX-SEC-003** — `#security-and-java-interoperation`

> `ImportManager.importCls(path)` must describe one class import, `importPack(path)` must describe package lookup, `importInnerCls(path)` must describe nested-class lookup, and `importClsAlias(type, alias)` must bind the supplied class without reloading it by name.

**QLX-SEC-004** — `#security-and-java-interoperation`

> WHEN `importClsAlias` receives null class data, an empty alias, or an alias whose first character is not uppercase, THEN it must raise `IllegalArgumentException`.

**QLX-SEC-005** — `#security-and-java-interoperation`

> A `ClassSupplier` must resolve a qualified class name to a `Class` or null, and `DefaultClassSupplier.getInstance()` must reuse cached successful and unsuccessful lookups.

**QLX-SEC-006** — `#security-and-java-interoperation`

> WHEN an import or custom class supplier resolves a class and the security strategy permits its use, THEN scripts must construct the class or invoke its public static and instance members through the imported name.

## Compilation, Serializable Caches, and Tracing

**QLX-CACHE-001** — `#compilation-serializable-caches-and-tracing`

> WHEN `QLOptions.cache` is true, THEN the runner must reuse the compiled form for equal script text.

**QLX-CACHE-002** — `#compilation-serializable-caches-and-tracing`

> `parseToDefinitionWithCache(script)` must prepopulate the same runner-local cache used by cached execution.

**QLX-CACHE-003** — `#compilation-serializable-caches-and-tracing`

> `clearCompileCache()` must discard runner-local compiled forms so the next cached execution recompiles the script without removing functions, operators, macros, aliases, or initialization policy.

**QLX-CACHE-004** — `#compilation-serializable-caches-and-tracing`

> `parseToSerializableCache(script)` must return a JavaBean graph rooted at `SerializableParseCache` with model version, producer version, original script, script hash, main lambda definition, instructions, constants, sources, and optional trace points sufficient for JSON round trip without a runtime JSON dependency.

**QLX-CACHE-005** — `#compilation-serializable-caches-and-tracing`

> WHEN a compatible `SerializableParseCache` is loaded, THEN `loadSerializableCache` must return a `LoadedParseCache` bound to that runner and repeated execution with different contexts must preserve the original script semantics.

**QLX-CACHE-006** — `#compilation-serializable-caches-and-tracing`

> WHEN a serializable or loaded cache contains function definitions, THEN `addFunctionsDefinedInScript` must install them into the consumer runner and report newly installed and duplicate names separately.

**QLX-CACHE-007** — `#compilation-serializable-caches-and-tracing`

> IF a serializable cache has an unsupported model version, malformed bean graph, unsupported instruction or constant, missing class, or missing operator, THEN loading must raise `SerializableParseCacheException` with the corresponding `QLErrorCodes` value and diagnostic.

**QLX-CACHE-008** — `#compilation-serializable-caches-and-tracing`

> `getExpressionTracePoints(script)` must return pre-execution trees whose nodes expose `TraceType`, token, children, line, column, and character position.

**QLX-CACHE-009** — `#compilation-serializable-caches-and-tracing`

> WHEN both `InitOptions.traceExpression` and `QLOptions.traceExpression` are true, THEN `QLResult.getExpressionTraces()` must return execution trees whose nodes additionally expose value and evaluated state.

**QLX-CACHE-010** — `#compilation-serializable-caches-and-tracing`

> WHEN a trace node is short-circuited, THEN its `isEvaluated()` projection must return false.

**QLX-CACHE-011** — `#compilation-serializable-caches-and-tracing`

> WHEN initialization tracing is disabled or a serialized cache contains no trace points, THEN execution must not fabricate execution traces.

## State Model

**QLX-STATE-001** — `#state-model`

> Runner initialization policy and extension registries must persist across executions until explicitly changed, while per-execution context, timeout, attachments, trace values, and local variables must not leak into later executions.

## Error Semantics

**QLX-ERR-001** — `#error-semantics`

> WHEN a script is malformed or a validation rule rejects it, THEN the operation must raise `QLSyntaxException`.

**QLX-ERR-002** — `#error-semantics`

> WHEN a runtime type, member, index, call, condition, allocation, or arithmetic failure occurs, THEN execution must raise `QLRuntimeException`.

**QLX-ERR-003** — `#error-semantics`

> WHEN a positive timeout is exceeded at an engine check point, THEN execution must raise `QLTimeoutException`.

**QLX-ERR-004** — `#error-semantics`

> WHEN a serializable cache model is invalid or a required binding is missing, THEN loading must raise `SerializableParseCacheException`.

**QLX-ERR-005** — `#error-semantics`

> WHEN a selector delimiter or class alias violates its documented precondition, THEN construction must raise `IllegalArgumentException`.

**QLX-ERR-006** — `#error-semantics`

> WHEN a public service-method registration target is missing, THEN registration must raise `IllegalArgumentException`.

**QLX-ERR-007** — `#error-semantics`

> WHEN the security strategy rejects Java member access, THEN execution must raise `QLRuntimeException`.

**QLX-ERR-008** — `#error-semantics`

> WHEN a callback raises `UserDefineException`, THEN execution must project `INVALID_ARGUMENT` or `BIZ_EXCEPTION` through `QLException`.

**QLX-ERR-009** — `#error-semantics`

> Every `QLException` must expose `getDiagnostic`, `getPos`, `getReason`, `getLineNo`, `getColNo`, `getErrLexeme`, and `getErrorCode`.

**QLX-ERR-010** — `#error-semantics`

> `QLException.getLineNo()` and `getColNo()` must be one-based while `Diagnostic.Range.Position` values must be zero-based.

**QLX-ERR-011** — `#error-semantics`

> WHEN a Java member invocation or callback wraps another throwable, THEN `QLRuntimeException.getCause()` or `getCatchObj()` must retain the originating object where the public error path provides it.

## Cross-View Invariants

**QLX-INV-001** — `#cross-view-invariants`

> The value returned by direct script execution must equal the value returned by executing its compatible `SerializableParseCache` and same-runner `LoadedParseCache` under equivalent runner configuration and context.

**QLX-INV-002** — `#cross-view-invariants`

> Names returned by dependency inspection must be exactly the context variables or externally supplied functions required by execution after script-local definitions, imports, and registrations are accounted for.

**QLX-INV-003** — `#cross-view-invariants`

> WHEN `polluteUserContext` is true, THEN assignments visible in the final result must agree with the corresponding entries written to the caller's map.

**QLX-INV-004** — `#cross-view-invariants`

> WHEN `polluteUserContext` is false, THEN the result must use execution-local assignments without changing the caller's map.

**QLX-INV-005** — `#cross-view-invariants`

> A registered function, operator, extension function, macro, or alias must affect later compilation, direct execution, cached execution, and serializable-cache consumption consistently when the consumer runner has an equivalent registration environment.

**QLX-INV-006** — `#cross-view-invariants`

> A validation failure reported by `check` must prevent the same malformed or restricted script from producing a successful execution result under the same restriction policy.

**QLX-INV-007** — `#cross-view-invariants`

> Trace-point source coordinates, execution-trace nodes, and `QLException` diagnostics must refer to the same original script coordinate system even after serializable-cache round trip.

**QLX-INV-008** — `#cross-view-invariants`

> Clearing the runner-local compile cache must not change script results, dependency inspection, extension registrations, initialization options, or serializable-cache semantics.

**QLX-INV-009** — `#cross-view-invariants`

> Security strategy decisions must agree across object contexts, alias-object contexts, imported classes, extension dispatch, and scripts loaded from compatible precompiled caches.

## Appendix A: Environment

**QLX-ENV-001** — `#appendix-a-environment`

> The project must declare `com.alibaba` as `groupId`, `qlexpress4` as `artifactId`, `4.1.3` as `version`, JAR packaging, and Java source and target level 8 in a standard root `pom.xml`.

**QLX-ENV-002** — `#appendix-a-environment`

> The implementation source must live under `src/main/java`, and runtime resources must live under `src/main/resources` when present.
