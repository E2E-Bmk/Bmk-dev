# Spec Test Map — gojq v1

| Node ID | Clauses | Source | Spec section |
|---|---|---|---|
| `atomic::TestGJQ001ParseIdentity` | `GJQ001`, `GJQ005` | generated | Parsing and Query Values |
| `atomic::TestGJQ002ParseErrorOffsetAndToken` | `GJQ002` | generated | Parsing and Query Values |
| `atomic::TestGJQ003QueryStringRoundTrip` | `GJQ003` | generated | Parsing and Query Values |
| `atomic::TestGJQ004NewIterAndExhaustion` | `GJQ004` | generated | Iterator Contract |
| `atomic::TestGJQ005CommaPipeAndEmpty` | `GJQ005` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ006LiteralAndArrayConstruction` | `GJQ006` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ007ObjectConstructionAlternatives` | `GJQ006` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ008ObjectLookupMissingAndOptional` | `GJQ007` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ009ObjectIterationSortedKeys` | `GJQ007` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ010ArrayIndices` | `GJQ008` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ011ArrayAndUnicodeStringSlices` | `GJQ008` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ012NumericArithmetic` | `GJQ009` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ013PolymorphicAddition` | `GJQ010` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ014InvalidArithmeticEmitsError` | `GJQ009` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ015EqualityAndTotalOrder` | `GJQ011` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ016RecursiveEquality` | `GJQ011` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ017TruthinessAndShortCircuit` | `GJQ012` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ018ConditionalAndSelect` | `GJQ013` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ019MapLengthKeysHas` | `GJQ014` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ020AggregatesAndEmptyConventions` | `GJQ015` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ021MinMaxSortUnique` | `GJQ015` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ022RangeFirstLastLimit` | `GJQ016` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ023UntilAndWhile` | `GJQ016` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ024StringCaseAffixAndTrim` | `GJQ017` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ025SplitJoinExplodeImplodeConversions` | `GJQ017` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ026RegexTestAndMatch` | `GJQ018` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ027RegexCaptureAndScan` | `GJQ018` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ028RegexSubAndGsub` | `GJQ018` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ029PathAndGetPath` | `GJQ019` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ030SetPathAndDelPaths` | `GJQ019` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ031AssignmentsDoNotMutateInput` | `GJQ020`, `GJQ042` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ032Delete` | `GJQ020` | generated | Basic Evaluation and Streaming |
| `atomic::TestGJQ033FunctionsArgumentsAndRecursion` | `GJQ021` | generated | Functions, Variables, and Control Flow |
| `atomic::TestGJQ034ReduceAndForeach` | `GJQ022` | generated | Functions, Variables, and Control Flow |
| `atomic::TestGJQ035TryOptionalAndHalt` | `GJQ023`, `GJQ024` | generated | Functions, Variables, and Control Flow |
| `integration::TestGJQ036CompiledAndDirectExecutionAgree` | `GJQ025` | generated | Compilation and Reuse |
| `integration::TestGJQ037VariablesBindPositionally` | `GJQ028` | generated | Compiler Options |
| `integration::TestGJQ038InvalidVariableNameFailsCompile` | `GJQ028` | generated | Compiler Options |
| `integration::TestGJQ039VariableValueCountErrors` | `GJQ028` | generated | Compiler Options |
| `integration::TestGJQ040CustomFunctionReceivesInputAndArgs` | `GJQ029` | generated | Compiler Options |
| `integration::TestGJQ041CustomFunctionMultipleArities` | `GJQ029` | generated | Compiler Options |
| `integration::TestGJQ042CustomFunctionArityPanicsImmediately` | `GJQ029` | generated | Compiler Options |
| `integration::TestGJQ043CustomValueErrorIsCatchable` | `GJQ023`, `GJQ029` | generated | Functions, Variables, and Control Flow |
| `integration::TestGJQ044CustomIterFunctionStreamsValues` | `GJQ030` | generated | Compiler Options |
| `integration::TestGJQ045IterAndNonIterNameConflictPanics` | `GJQ030` | generated | Compiler Options |
| `integration::TestGJQ046InputDisabledByDefault` | `GJQ031` | generated | Compiler Options |
| `integration::TestGJQ047InputIteratorConsumption` | `GJQ031` | generated | Compiler Options |
| `integration::TestGJQ048EnvironmentLoaderIsolationAndDuplicates` | `GJQ032` | generated | Compiler Options |
| `integration::TestGJQ049CustomModuleAndJSONLoader` | `GJQ033` | generated | Module Loading |
| `integration::TestGJQ050ModuleLoaderErrorPropagates` | `GJQ033` | generated | Module Loading |
| `integration::TestGJQ051FilesystemModuleSearchForms` | `GJQ034` | generated | Module Loading |
| `integration::TestGJQ052FilesystemJSONImportPreservesNumbers` | `GJQ034`, `GJQ035` | generated | Module Loading |
| `integration::TestGJQ053CompareTotalOrderAndCompositeValues` | `GJQ036` | generated | Value Comparison |
| `integration::TestGJQ054CompareNumericRepresentationsNaNAndZero` | `GJQ036`, `GJQ037` | generated | Value Comparison |
| `integration::TestGJQ055MarshalSpecialFloatsAndEscaping` | `GJQ038` | generated | Encoding, Type Names, and Preview |
| `integration::TestGJQ056MarshalSortsKeysAndPreservesNumbers` | `GJQ038`, `GJQ039` | generated | Encoding, Type Names, and Preview |
| `integration::TestGJQ057TypeOfSupportedAndUnsupported` | `GJQ040` | generated | Encoding, Type Names, and Preview |
| `integration::TestGJQ058PreviewPrimitiveAndUTF8Truncation` | `GJQ041` | generated | Encoding, Type Names, and Preview |
| `integration::TestGJQ059RunWithContextCancellation` | `GJQ026` | generated | Compilation and Reuse |
| `integration::TestGJQ060ConcurrentReuseAndIsolation` | `GJQ027`, `GJQ042` | generated | Compilation and Reuse |
