# spec_test_map — kong-cli-grammar-fullrepro-001

oracle_version: 2026-08-25T2
oracle_source: generated_only (Track B; see filter/rewrite_audit.md)

Size note: the kept set is 149 base test functions, just under the ~150
guidance. The spec covers the entire retained surface in behavioral
language: all eight behavior sections were written before generation, and
every row below maps to explicit spec text (no test relies on inference
beyond stated contracts). Error-message assertions quote shapes stated in
Error Semantics verbatim.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::TestNewRejectsNonStructPointer | atomic | failure_path | section Grammar Construction — entry points (non-struct rejection) | covered | |
| atomic::TestMustPanicsOnGrammarError | atomic | failure_path | section Grammar Construction — entry points (Must panics) | covered | |
| atomic::TestFieldClassification | atomic | positive | section Grammar Construction — field classification | covered | |
| atomic::TestAnonymousEmbedFlattened | atomic | positive | section Grammar Construction — field classification (anonymous embed) | covered | |
| atomic::TestPluginsContributeFlags | atomic | positive | section Grammar Construction — field classification (Plugins) | covered | |
| atomic::TestKebabCaseNaming | atomic | positive | section Grammar Construction — naming (case-boundary hyphenation) | covered | |
| atomic::TestNameTagOverride | atomic | positive | section Grammar Construction — naming (name tag override) | covered | |
| atomic::TestFlagNamerOption | atomic | positive | section Grammar Construction — naming (FlagNamer option) | covered | |
| atomic::TestCommandAliasParses | atomic | positive | section Grammar Construction — naming (aliases) | covered | |
| atomic::TestDuplicateShortFlagError | atomic | failure_path | section Grammar Construction — structure tags (duplicate short) | covered | |
| atomic::TestArgumentBranch | atomic | positive | section Grammar Construction — commands and argument branches | covered | |
| atomic::TestArgumentBranchMissingChildError | atomic | failure_path | section Grammar Construction — commands and argument branches (missing same-named child) | covered | |
| atomic::TestRequiredAfterOptionalPositionalError | atomic | failure_path | section Grammar Construction — positional ordering | covered | |
| atomic::TestDynamicCommandOption | atomic | positive | section Grammar Construction — dynamic commands | covered | |
| atomic::TestAutomaticHelpFlag | atomic | positive | section Grammar Construction — dynamic commands and the automatic help flag | covered | |
| atomic::TestNoDefaultHelp | atomic | failure_path | section Grammar Construction — the automatic help flag (NoDefaultHelp) | covered | |
| atomic::TestEnumRequiresDefaultOrRequired | atomic | failure_path | section Grammar Construction — grammar-level validation at build time (enum) | covered | |
| atomic::TestNegatableNonBoolError | atomic | failure_path | section Grammar Construction — grammar-level validation at build time (negatable) | covered | |
| atomic::TestUndefinedInterpolationVarError | atomic | failure_path | section Grammar Construction — grammar-level validation at build time (undefined variable) | covered | |
| atomic::TestHelpDefaultLayout | atomic | positive | section Help Rendering and Diagnostics — default layout | covered | |
| atomic::TestHelpExitsZero | atomic | positive | section Help Rendering and Diagnostics — default layout (exit 0 on stdout) | covered | |
| atomic::TestHelpPlaceholders | atomic | positive | section Help Rendering and Diagnostics — default layout (placeholders) | covered | |
| atomic::TestHelpEnvAnnotation | atomic | positive | section Help Rendering and Diagnostics — default layout (env annotation) | covered | |
| atomic::TestHelpHiddenOmitted | atomic | positive | section Help Rendering and Diagnostics — groups, aliases, and hiding (hidden entries) | covered | |
| atomic::TestHelpFlagGroups | atomic | positive | section Help Rendering and Diagnostics — groups, aliases, and hiding (flag groups) | covered | |
| atomic::TestHelpExplicitCommandGroups | atomic | positive | section Help Rendering and Diagnostics — groups, aliases, and hiding (explicit command groups) | covered | |
| atomic::TestHelpCompactAliases | atomic | positive | section Help Rendering and Diagnostics — alternate layouts (compact aliases) | covered | |
| atomic::TestHelpTreeLayout | atomic | positive | section Help Rendering and Diagnostics — alternate layouts (tree) | covered | |
| atomic::TestContextSensitiveHelp | atomic | positive | section Help Rendering and Diagnostics — context-sensitive help | covered | |
| atomic::TestHelpProviderDetail | atomic | positive | section Help Rendering and Diagnostics — context-sensitive help (Help() detail) | covered | |
| atomic::TestUsageOnError | atomic | positive | section Help Rendering and Diagnostics — usage on error | covered | |
| atomic::TestShortUsageOnError | atomic | positive | section Help Rendering and Diagnostics — usage on error (short form) | covered | |
| atomic::TestMessageHelpers | atomic | positive | section Help Rendering and Diagnostics — message helpers | covered | |
| atomic::TestPrintUsage | atomic | positive | section Help Rendering and Diagnostics — usage on error (PrintUsage) | covered | |
| atomic::TestBuiltinScalarDecoding | atomic | positive | section Value Mapping — built-in decoding (scalars) | covered | |
| atomic::TestDurationDecoding | atomic | positive | section Value Mapping — built-in decoding (duration) | covered | |
| atomic::TestTimeDefaultsToRFC3339 | atomic | positive | section Value Mapping — built-in decoding (time defaults to RFC 3339) | covered | |
| atomic::TestTimeFormatTag | atomic | positive | section Value Mapping — built-in decoding (format tag) | covered | |
| atomic::TestMalformedNumberErrors | atomic | failure_path | section Value Mapping — built-in decoding (malformed int and float) | covered | |
| atomic::TestPathTypeExpansion | atomic | positive | section Value Mapping — special types and type tags (path) | covered | |
| atomic::TestFileContentFlag | atomic | positive | section Value Mapping — special types and type tags (FileContentFlag) | covered | |
| atomic::TestConfigFlagLoadsResolver | atomic | positive | section Value Mapping — special types and type tags (ConfigFlag) | covered | |
| atomic::TestVersionFlag | atomic | positive | section Value Mapping — special types and type tags (VersionFlag) | covered | |
| atomic::TestNamedMapper | atomic | positive | section Value Mapping — custom mappers (NamedMapper) | covered | |
| atomic::TestTypeMapper | atomic | positive | section Value Mapping — custom mappers (TypeMapper) | covered | |
| atomic::TestMapperDecodeContext | atomic | positive | section Value Mapping — custom mappers (DecodeContext and scanner) | covered | |
| atomic::TestNegativeNumberAfterShortFlag | atomic | positive | section Value Mapping — custom mappers (negative number after short flag) | covered | |
| atomic::TestEnumFlagViolation | atomic | positive | section Value Mapping — enums (flag form) | covered | |
| atomic::TestEnumPositionalViolation | atomic | positive | section Value Mapping — enums (positional form) | covered | |
| atomic::TestModelNodeFields | atomic | positive | section Model Introspection and the Parse Context — the model (node fields and types) | covered | |
| atomic::TestModelNodeQueries | atomic | positive | section Model Introspection and the Parse Context — the model (node queries) | covered | |
| atomic::TestModelFlagFields | atomic | positive | section Model Introspection and the Parse Context — the model (flag metadata) | covered | |
| atomic::TestContextQueries | atomic | positive | section Model Introspection and the Parse Context — the context (queries after a parse) | covered | |
| atomic::TestContextEmpty | atomic | positive | section Model Introspection and the Parse Context — the context (Empty) | covered | |
| atomic::TestParseErrorShape | atomic | positive | section Model Introspection and the Parse Context — the context (ParseError carries Context, ExitCode, Unwrap) | covered | |
| atomic::TestStagedParsing | atomic | positive | section Model Introspection and the Parse Context — staged parsing | covered | |
| atomic::TestKongPublicFields | atomic | positive | section Model Introspection and the Parse Context — the model (Kong struct fields) | covered | |
| atomic::TestLongFlagValueForms | atomic | positive | section Parsing and Binding — flag syntaxes (long forms) | covered | |
| atomic::TestShortFlagValueForms | atomic | positive | section Parsing and Binding — flag syntaxes (short forms) | covered | |
| atomic::TestShortEqualsIsNotSeparator | atomic | failure_path | section Parsing and Binding — flag syntaxes (= is not a short separator) | covered | |
| atomic::TestCombinedShortFlags | atomic | positive | section Parsing and Binding — flag syntaxes (combined shorts) | covered | |
| atomic::TestBooleanFlagSemantics | atomic | positive | section Parsing and Binding — boolean flags | covered | |
| atomic::TestBooleanDetachedValueNotConsumed | atomic | failure_path | section Parsing and Binding — boolean flags (detached value not consumed) | covered | |
| atomic::TestNegatableFlag | atomic | positive | section Parsing and Binding — boolean flags (negatable) | covered | |
| atomic::TestCustomNegationName | atomic | positive | section Parsing and Binding — boolean flags (custom negation name) | covered | |
| atomic::TestDashDashTerminator | atomic | positive | section Parsing and Binding — terminator and passthrough (--) | covered | |
| atomic::TestPassthroughPositional | atomic | positive | section Parsing and Binding — terminator and passthrough (passthrough positional) | covered | |
| atomic::TestAncestorFlagAfterCommand | atomic | positive | section Parsing and Binding — flag scope (ancestor flags after entry) | covered | |
| atomic::TestDescendantFlagBeforeCommandRejected | atomic | failure_path | section Parsing and Binding — flag scope (descendant flag before its command) | covered | |
| atomic::TestNonLeafSelectionErrors | atomic | failure_path | section Parsing and Binding — command selection (leaf requirement) | covered | |
| atomic::TestCommandStringForms | atomic | positive | section Parsing and Binding — command selection (Command strings) | covered | |
| atomic::TestDefaultCommand | atomic | positive | section Parsing and Binding — default commands (default:"1") | covered | |
| atomic::TestDefaultCommandWithArgs | atomic | positive | section Parsing and Binding — default commands (withargs) | covered | |
| atomic::TestSliceAccumulationAndSeparator | atomic | positive | section Parsing and Binding — collections and counters (slices) | covered | |
| atomic::TestDefaultSeparators | atomic | positive | section Parsing and Binding — collections and counters (default separators) | covered | |
| atomic::TestMapFlagCustomSeparator | atomic | positive | section Parsing and Binding — collections and counters (maps) | covered | |
| atomic::TestCounterFlag | atomic | positive | section Parsing and Binding — collections and counters (counter) | covered | |
| atomic::TestPointerFieldAllocation | atomic | positive | section Parsing and Binding — collections and counters (pointer allocation) | covered | |
| atomic::TestMissingPositionalError | atomic | failure_path | section Parsing and Binding — positional completion (missing) | covered | |
| atomic::TestExcessPositionalError | atomic | failure_path | section Parsing and Binding — positional completion (excess) | covered | |
| atomic::TestOptionalPositionalDefault | atomic | positive | section Parsing and Binding — positional completion (optional default) | covered | |
| atomic::TestSplitAndJoinEscaped | atomic | positive | section Parsing and Binding — collections and counters (escaped separators) | covered | |
| atomic::TestDefaultTag | atomic | positive | section Defaults, Environment Variables and Resolvers — defaults | covered | |
| atomic::TestApplyDefaultsFunction | atomic | positive | section Defaults, Environment Variables and Resolvers — defaults (ApplyDefaults function) | covered | |
| atomic::TestEnvTagPrecedence | atomic | positive | section Defaults, Environment Variables and Resolvers — environment variables (env beats default, command line beats env) | covered | |
| atomic::TestEnvMultiFallback | atomic | positive | section Defaults, Environment Variables and Resolvers — environment variables (multi-variable fallback) | covered | |
| atomic::TestDefaultEnvarsOption | atomic | positive | section Defaults, Environment Variables and Resolvers — environment variables (DefaultEnvars) | covered | |
| atomic::TestEnvPrefixComposition | atomic | positive | section Defaults, Environment Variables and Resolvers — environment variables (envprefix composition) | covered | |
| atomic::TestVarsInterpolation | atomic | positive | section Defaults, Environment Variables and Resolvers — variable interpolation | covered | |
| atomic::TestInterpolationFallback | atomic | positive | section Defaults, Environment Variables and Resolvers — variable interpolation (fallback form) | covered | |
| atomic::TestHasInterpolatedVar | atomic | positive | section Defaults, Environment Variables and Resolvers — variable interpolation (HasInterpolatedVar) | covered | |
| atomic::TestCustomResolver | atomic | positive | section Defaults, Environment Variables and Resolvers — resolvers (custom ResolverFunc) | covered | |
| atomic::TestJSONResolverKeyVariants | atomic | positive | section Defaults, Environment Variables and Resolvers — JSON configuration (key variants) | covered | |
| atomic::TestConfigurationOption | atomic | positive | section Defaults, Environment Variables and Resolvers — JSON configuration (Configuration option and LoadConfig) | covered | |
| atomic::TestClearResolversKeepsEnv | atomic | positive | section Defaults, Environment Variables and Resolvers — resolvers (ClearResolvers does not affect env bindings) | covered | |
| atomic::TestRequiredSatisfiedByResolver | atomic | positive | section Defaults, Environment Variables and Resolvers — precedence (required satisfied by resolver) | covered | |
| atomic::TestResolverBeatsEnvironment | atomic | positive | section Defaults, Environment Variables and Resolvers — precedence (resolver beats environment) | covered | |
| atomic::TestHookOrder | atomic | positive | section Hooks, Bindings and Command Execution — lifecycle hooks (order) | covered | |
| atomic::TestHookErrorAbortsParse | atomic | failure_path | section Hooks, Bindings and Command Execution — lifecycle hooks (error aborts parse) | covered | |
| atomic::TestAfterRunHook | atomic | positive | section Hooks, Bindings and Command Execution — lifecycle hooks (AfterRun) | covered | |
| atomic::TestRunChainLeafToRoot | atomic | positive | section Hooks, Bindings and Command Execution — run dispatch (leaf-to-root chain) | covered | |
| atomic::TestRunNoMethodError | atomic | failure_path | section Hooks, Bindings and Command Execution — run dispatch (no method anywhere) | covered | |
| atomic::TestContextAutoBound | atomic | positive | section Hooks, Bindings and Command Execution — bindings (context auto-bound) | covered | |
| atomic::TestBindOptionAndRunArguments | atomic | positive | section Hooks, Bindings and Command Execution — bindings (Bind option and Run arguments) | covered | |
| atomic::TestBindToInterface | atomic | positive | section Hooks, Bindings and Command Execution — bindings (BindTo interface) | covered | |
| atomic::TestBindToProvider | atomic | positive | section Hooks, Bindings and Command Execution — bindings (BindToProvider) | covered | |
| atomic::TestMissingBindingError | atomic | failure_path | section Hooks, Bindings and Command Execution — bindings (missing binding error) | covered | |
| atomic::TestExitCoderHonoured | atomic | positive | section Hooks, Bindings and Command Execution — errors from commands (ExitCoder honoured by FatalIfErrorf) | covered | |
| atomic::TestMissingRequiredFlag | atomic | failure_path | section Validation and Flag Groups — required and missing values | covered | |
| atomic::TestMissingMultipleRequiredFlags | atomic | failure_path | section Validation and Flag Groups — required and missing values (multiple joined with commas) | covered | |
| atomic::TestXorConflict | atomic | positive | section Validation and Flag Groups — exclusive and inclusive groups (xor conflict) | covered | |
| atomic::TestAndGroupPartial | atomic | positive | section Validation and Flag Groups — exclusive and inclusive groups (and partial) | covered | |
| atomic::TestRequiredXorAbsent | atomic | failure_path | section Validation and Flag Groups — exclusive and inclusive groups (required xor absent) | covered | |
| atomic::TestUnknownFlag | atomic | failure_path | section Validation and Flag Groups — unknown input | covered | |
| atomic::TestUnknownFlagSuggestion | atomic | failure_path | section Validation and Flag Groups — unknown input (flag suggestion) | covered | |
| atomic::TestUnknownCommandSuggestion | atomic | failure_path | section Validation and Flag Groups — unknown input (command suggestion) | covered | |
| integration::TestHelpMatchesParseableSurface | integration | positive | section Cross-View Invariants 1 (help lists exactly the parseable surface) | covered | |
| integration::TestModelFlagsAllParseable | integration | positive | section Cross-View Invariants 1 (model flags render and parse consistently for every declared flag) | covered | |
| integration::TestCommandAgreesWithSummary | integration | positive | section Cross-View Invariants 2 (Command agrees with the model summary) | covered | |
| integration::TestModelContextStructAgreement | integration | positive | section Cross-View Invariants 3 (model flags, context flags, and bound struct agree) | covered | |
| integration::TestPrecedenceChainObservable | integration | positive | section Cross-View Invariants 4 (precedence chain with all four sources) | covered | |
| integration::TestValueSetReflectsSource | integration | positive | section Cross-View Invariants 4 (Value.Set reflects the winning source) | covered | |
| integration::TestStagedEqualsOneShotSuccess | integration | positive | section Cross-View Invariants 5 (staged parsing equals one-shot parsing, success path) | covered | |
| integration::TestStagedEqualsOneShotFailure | integration | failure_path | section Cross-View Invariants 5 (staged parsing equals one-shot parsing, failure path) | covered | |
| integration::TestBuildTimeRejectionTotal | integration | positive | section Cross-View Invariants 6 (build-time rejection is total) | covered | |
| integration::TestInterpolationUniform | integration | positive | section Cross-View Invariants 7 (interpolation is uniform across default, help, and enum) | covered | |
| integration::TestErrorsUseHelpRendering | integration | positive | section Cross-View Invariants 8 (errors name flags as help renders them) | covered | |
| integration::TestExpectedChildrenMatchModel | integration | failure_path | section Cross-View Invariants 2 and 8 (expected-children error names the same children the model exposes) | covered | |
| integration::TestDefaultEnvarsHelpAndResolution | integration | positive | section Cross-View Invariants 1 and Help Rendering (DefaultEnvars annotation matches the variable actually read) | covered | |
| integration::TestRequiredSatisfiedThroughEachSource | integration | positive | section Cross-View Invariants 4 and Validation (required satisfied through each source in turn) | covered | |
| integration::TestFlagNamerConsistentAcrossViews | integration | positive | section Cross-View Invariants 6 and Grammar Construction (a valid grammar parses every declared projection consistently after FlagNamer renaming) | covered | |
| integration::TestUsageOnErrorFullFlow | integration | positive | section Help Rendering and Diagnostics (usage on error) with the ParseError contract from Model Introspection and the Parse Context | covered | |
| integration::TestParseErrorContextPrintsUsage | integration | positive | section Model Introspection and the Parse Context (ParseError.Context drives PrintUsage after a failure) | covered | |
| integration::TestMapperWithDefaultsAndEnums | integration | positive | section Value Mapping (custom mappers) composed with Defaults and enum validation in one grammar | covered | |
| integration::TestDefaultCommandPipeline | integration | positive | section Parsing and Binding (default commands) with Context.Empty and execution | covered | |
| integration::TestGroupConstraintsAcrossViews | integration | positive | section Validation and Flag Groups (xor/and) rendered consistently in help and enforced at parse (Cross-View Invariants 8) | covered | |
| integration::TestRunChainWithProviderBindings | integration | positive | section Hooks, Bindings and Command Execution (providers and parent struct bindings along the run chain) | covered | |
| integration::TestVersionFlagPipeline | integration | positive | section Value Mapping (VersionFlag) leaves the rest of the grammar untouched (Cross-View Invariants 6) | covered | |
| integration::TestAlternateHelpLayoutsSameGrammar | integration | positive | section Help Rendering and Diagnostics (alternate layouts) driven by one grammar (Cross-View Invariants 1) | covered | |
| integration::TestFlagScopeAcrossTree | integration | positive | section Parsing and Binding (scope) and Grammar Construction across a deep tree: each level's flags become available exactly at that level | covered | |
| integration::TestFileUtilityWorkflow | integration | positive | section Representative Workflows (file utility) spanning Grammar Construction, Parsing and Binding, and Hooks, Bindings and Command Execution | covered | |
| integration::TestServerResolutionWorkflow | integration | positive | section Representative Workflows (server resolution) spanning Defaults, Environment Variables and Resolvers and Value Mapping | covered | |
| integration::TestArgumentBranchWorkflow | integration | positive | section Grammar Construction (argument branches) with Parsing and Binding and Model Introspection | covered | |
| integration::TestEmbeddedPrefixWorkflow | integration | positive | section Grammar Construction (embed, prefix, envprefix) across parsing, environment resolution, and help rendering | covered | |
| integration::TestPluginsWorkflow | integration | positive | section Grammar Construction (Plugins) with parsing and help | covered | |
| integration::TestDynamicCommandWorkflow | integration | positive | section Grammar Construction (DynamicCommand) with execution and help | covered | |
| integration::TestConfigFlagWorkflow | integration | positive | section Value Mapping (ConfigFlag) with Defaults, Environment Variables and Resolvers precedence | covered | |
| integration::TestHooksObserveResolution | integration | positive | section Hooks, Bindings and Command Execution (hooks observe the resolution pipeline) | covered | |
| integration::TestPassthroughIntoRun | integration | positive | section Parsing and Binding (passthrough) delivered into command execution | covered | |

Total: 149 | kept (covered): 149 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 149

Layers: atomic 116, integration 33. Assertion kinds: positive 122, failure_path 27, atomic positive share 91/116 = 78%.
