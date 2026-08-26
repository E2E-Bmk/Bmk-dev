# spec_test_map — mvdansh-shell-syntax-fullrepro-001

oracle_version: 2026-08-25T1
oracle_source: generated_only (Track B; see filter/rewrite_audit.md)

Size note: the kept set is 170 base test functions, matching the
`expected_oracle_max=170` recorded at Stage 1 for this two-package scope
(`syntax` + `syntax/typedjson`: five parse entry points, printer with
seven options, JSON interchange, walker, and four word utilities). Every
row maps to explicit spec text; error-message assertions quote shapes
stated in Error Semantics verbatim. Three spec claims were corrected
during generation because probing disproved the drafted wording (CVI 1
option scope, CVI 3 decodable roots, CVI 4/heredoc extents) — the spec
was fixed to state the true observed behaviour before the corresponding
tests were kept; no symbol was added to the surface.

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::TestLangVariantValuesAndStrings | atomic | positive | section Language Variants — the variant enumeration | covered | |
| atomic::TestLangVariantSetAccepted | atomic | positive | section Language Variants — selecting by name | covered | |
| atomic::TestLangVariantSetUnknown | atomic | failure_path | section Error Semantics (unknown variant name) | covered | |
| atomic::TestPosixRejectsArrays | atomic | failure_path | section Language Variants — variant gating + Error Semantics (LangError) | covered | |
| atomic::TestPosixRejectsExtGlob | atomic | failure_path | section Language Variants — variant gating | covered | |
| atomic::TestPosixRejectsFunctionKeyword | atomic | failure_path | section Language Variants — variant gating | covered | |
| atomic::TestPosixParsesDoubleBracketAsCommand | atomic | positive | section Language Variants — variant gating (POSIX reinterpretation) | covered | |
| atomic::TestPosixParsesLetAsCommand | atomic | positive | section Language Variants — variant gating (POSIX reinterpretation) | covered | |
| atomic::TestMkshCaseResumeKorn | atomic | positive | section The Syntax Tree — control flow (case operators, mksh) | covered | |
| atomic::TestBashRejectsResumeKorn | atomic | failure_path | section Language Variants — variant gating | covered | |
| atomic::TestBatsTestDecl | atomic | positive | section Language Variants — Bats | covered | |
| atomic::TestBashRejectsAtTest | atomic | failure_path | section Language Variants — Bats (gating outside Bats) | covered | |
| atomic::TestVariantLangAutoPanics | atomic | failure_path | section Language Variants — auto detection is not a parser mode + Error Semantics | covered | |
| atomic::TestParseBasicPositions | atomic | positive | section Parsing Shell Programs — Parse; The Syntax Tree — positions | covered | |
| atomic::TestMultiLinePositions | atomic | positive | section The Syntax Tree — positions (line/col across lines) | covered | |
| atomic::TestColumnsCountBytes | atomic | positive | section The Syntax Tree — positions (columns count bytes) | covered | |
| atomic::TestFileNameRecorded | atomic | positive | section The Syntax Tree — files and statements (Name) | covered | |
| atomic::TestEmptyInput | atomic | positive | section Parsing Shell Programs — Parse (empty input) | covered | |
| atomic::TestParserReuse | atomic | positive | section Parsing Shell Programs — construction and options (reuse) | covered | |
| atomic::TestSemicolonPosition | atomic | positive | section Parsing Shell Programs — statements and separators | covered | |
| atomic::TestBackgroundAndNegated | atomic | positive | section The Syntax Tree — files and statements (Background, Negated) | covered | |
| atomic::TestCoprocessMksh | atomic | positive | section Parsing Shell Programs — statements and separators (mksh coprocess) | covered | |
| atomic::TestPipeAllBash | atomic | positive | section The Syntax Tree — control flow (binary commands, pipe-all) | covered | |
| atomic::TestRedirsAttach | atomic | positive | section The Syntax Tree — redirections | covered | |
| atomic::TestCommentsDiscardedByDefault | atomic | positive | section Parsing Shell Programs — comments | covered | |
| atomic::TestKeepCommentsAttach | atomic | positive | section Parsing Shell Programs — comments (KeepComments) | covered | |
| atomic::TestKeepCommentsDirectApplication | atomic | positive | section Parsing Shell Programs — comments (option as direct function) | covered | |
| atomic::TestHeredocBody | atomic | positive | section Parsing Shell Programs — here-documents | covered | |
| atomic::TestHeredocQuotedDelim | atomic | positive | section Parsing Shell Programs — here-documents (quoted delimiter) | covered | |
| atomic::TestDashHeredocKeepsTabs | atomic | positive | section Parsing Shell Programs — here-documents (dash form) | covered | |
| atomic::TestHereString | atomic | positive | section Parsing Shell Programs — here-documents (here-string) | covered | |
| atomic::TestUnclosedHeredocError | atomic | failure_path | section Parsing Shell Programs — here-documents + Error Semantics | covered | |
| atomic::TestStmtEndCoversHeredoc | atomic | positive | section Parsing Shell Programs — here-documents (statement End, trailing heredoc) | covered | |
| atomic::TestParseErrorFormatWithName | atomic | failure_path | section Error Semantics (ParseError rendering with name) | covered | |
| atomic::TestParseErrorFormatNoName | atomic | failure_path | section Error Semantics (ParseError rendering, empty name) | covered | |
| atomic::TestStopAtWord | atomic | positive | section Parsing Shell Programs — stopping early | covered | |
| atomic::TestStopAtQuotedNotStopped | atomic | positive | section Parsing Shell Programs — stopping early (quoted form not stopped) | covered | |
| atomic::TestRecoverErrorsSubshell | atomic | positive | section Parsing Shell Programs — error recovery | covered | |
| atomic::TestRecoverZeroFails | atomic | failure_path | section Parsing Shell Programs — error recovery (zero budget) | covered | |
| atomic::TestKeywordOutOfPlaceErrors | atomic | failure_path | section Error Semantics (keyword out of place) | covered | |
| atomic::TestUnclosedConstructsIncomplete | atomic | failure_path | section Error Semantics (incomplete input) | covered | |
| atomic::TestStmtsSeqIteration | atomic | positive | section Incremental and Fragment Parsing — statement iteration | covered | |
| atomic::TestStmtsSeqError | atomic | failure_path | section Incremental and Fragment Parsing — statement iteration (error pair) | covered | |
| atomic::TestStmtsCallbackStopEarly | atomic | positive | section Incremental and Fragment Parsing — statement iteration (early stop) | covered | |
| atomic::TestWordsSeqMultiline | atomic | positive | section Incremental and Fragment Parsing — word iteration | covered | |
| atomic::TestWordsSeqNonWordError | atomic | failure_path | section Error Semantics (non-word token in WordsSeq) | covered | |
| atomic::TestDocumentParsesExpansion | atomic | positive | section Incremental and Fragment Parsing — fragment entry points (Document) | covered | |
| atomic::TestArithmeticFragment | atomic | positive | section Incremental and Fragment Parsing — fragment entry points (Arithmetic) | covered | |
| atomic::TestArithmeticFragmentError | atomic | failure_path | section Incremental and Fragment Parsing — fragment entry points (malformed) | covered | |
| atomic::TestInteractiveSeqBatches | atomic | positive | section Incremental and Fragment Parsing — interactive parsing | covered | |
| atomic::TestInteractiveCallbackStop | atomic | positive | section Incremental and Fragment Parsing — interactive parsing (stop) | covered | |
| atomic::TestIsIncompleteClassification | atomic | positive | section Incremental and Fragment Parsing — incomplete input classification | covered | |
| atomic::TestWordLitConcatenation | atomic | positive | section The Syntax Tree — words and word parts (Lit, concatenation) | covered | |
| atomic::TestCallExprAssignsArgs | atomic | positive | section The Syntax Tree — simple commands and assignments | covered | |
| atomic::TestAssignForms | atomic | positive | section The Syntax Tree — simple commands and assignments (Append, Naked) | covered | |
| atomic::TestStandaloneIndexedAssign | atomic | positive | section The Syntax Tree — simple commands and assignments (Index) | covered | |
| atomic::TestInlineIndexedAssignError | atomic | failure_path | section The Syntax Tree — simple commands and assignments (inline array restriction) | covered | |
| atomic::TestArrayExpr | atomic | positive | section The Syntax Tree — simple commands and assignments (ArrayExpr) | covered | |
| atomic::TestSglQuotedDollar | atomic | positive | section The Syntax Tree — words and word parts (SglQuoted, Dollar) | covered | |
| atomic::TestDblQuotedDollarAndParts | atomic | positive | section The Syntax Tree — words and word parts (DblQuoted) | covered | |
| atomic::TestCmdSubstBackquotes | atomic | positive | section The Syntax Tree — words and word parts (CmdSubst, backquotes) | covered | |
| atomic::TestMkshCmdSubstForms | atomic | positive | section The Syntax Tree — words and word parts (mksh TempFile/ReplyVar) | covered | |
| atomic::TestArithmExpBracket | atomic | positive | section The Syntax Tree — words and word parts (ArithmExp forms) | covered | |
| atomic::TestProcSubst | atomic | positive | section The Syntax Tree — words and word parts (ProcSubst) | covered | |
| atomic::TestExtGlobNode | atomic | positive | section The Syntax Tree — words and word parts (ExtGlob) | covered | |
| atomic::TestParamExpBasics | atomic | positive | section The Syntax Tree — parameter expansions (Short, Length, Excl) | covered | |
| atomic::TestParamExpExpansionOp | atomic | positive | section The Syntax Tree — parameter expansions (Exp operators) | covered | |
| atomic::TestParamExpReplace | atomic | positive | section The Syntax Tree — parameter expansions (Repl) | covered | |
| atomic::TestParamExpSlice | atomic | positive | section The Syntax Tree — parameter expansions (Slice) | covered | |
| atomic::TestParamExpNames | atomic | positive | section The Syntax Tree — parameter expansions (Names) | covered | |
| atomic::TestParamExpIndex | atomic | positive | section The Syntax Tree — parameter expansions (Index) | covered | |
| atomic::TestParamExpBadOpError | atomic | failure_path | section The Syntax Tree — parameter expansions + Error Semantics | covered | |
| atomic::TestIfElifElseChain | atomic | positive | section The Syntax Tree — control flow (IfClause chain) | covered | |
| atomic::TestWhileUntil | atomic | positive | section The Syntax Tree — control flow (WhileClause, Until) | covered | |
| atomic::TestForWordIter | atomic | positive | section The Syntax Tree — control flow (ForClause, WordIter) | covered | |
| atomic::TestCStyleLoop | atomic | positive | section The Syntax Tree — control flow (CStyleLoop) | covered | |
| atomic::TestSelectClause | atomic | positive | section The Syntax Tree — control flow (Select) | covered | |
| atomic::TestCaseItems | atomic | positive | section The Syntax Tree — control flow (CaseClause items and operators) | covered | |
| atomic::TestBlockSubshell | atomic | positive | section The Syntax Tree — control flow (Block, Subshell) | covered | |
| atomic::TestBinaryCmdOps | atomic | positive | section The Syntax Tree — control flow (BinaryCmd operators) | covered | |
| atomic::TestFuncDeclForms | atomic | positive | section The Syntax Tree — functions and declarations (FuncDecl forms) | covered | |
| atomic::TestDeclClause | atomic | positive | section The Syntax Tree — functions and declarations (DeclClause) | covered | |
| atomic::TestLetClause | atomic | positive | section The Syntax Tree — functions and declarations (LetClause) | covered | |
| atomic::TestTimeClause | atomic | positive | section The Syntax Tree — control flow (TimeClause) | covered | |
| atomic::TestCoprocClause | atomic | positive | section The Syntax Tree — control flow (CoprocClause) | covered | |
| atomic::TestTestClauseRightAssociative | atomic | positive | section The Syntax Tree — test expressions (associativity) | covered | |
| atomic::TestTestClauseOperators | atomic | positive | section The Syntax Tree — test expressions (operators) | covered | |
| atomic::TestArithmCmdAndTernary | atomic | positive | section The Syntax Tree — arithmetic (ArithmCmd, ternary) | covered | |
| atomic::TestArithmAssignRequiresName | atomic | failure_path | section The Syntax Tree — arithmetic + Error Semantics | covered | |
| atomic::TestEscapedNewlineLit | atomic | positive | section The Syntax Tree — words and word parts (escaped newline in Lit) | covered | |
| atomic::TestValidName | atomic | positive | section The Syntax Tree — keyword and name classification (ValidName) | covered | |
| atomic::TestIsKeyword | atomic | positive | section The Syntax Tree — keyword and name classification (IsKeyword) | covered | |
| atomic::TestNewPosAccessors | atomic | positive | section The Syntax Tree — positions (NewPos accessors) | covered | |
| atomic::TestZeroLinePosInvalid | atomic | positive | section The Syntax Tree — positions (IsValid) | covered | |
| atomic::TestPosString | atomic | positive | section The Syntax Tree — positions (String) | covered | |
| atomic::TestPosAfter | atomic | positive | section The Syntax Tree — positions (After) | covered | |
| atomic::TestStmtPositionField | atomic | positive | section The Syntax Tree — files and statements (Position field) | covered | |
| atomic::TestPrintCanonicalSpacing | atomic | positive | section Canonical Printing — canonical style (spacing) | covered | |
| atomic::TestPrintKeywordSpacing | atomic | positive | section Canonical Printing — canonical style (keywords) | covered | |
| atomic::TestPrintBlankLineCollapse | atomic | positive | section Canonical Printing — canonical style (blank line runs) | covered | |
| atomic::TestPrintBackquoteConversion | atomic | positive | section Canonical Printing — canonical style (backquotes to dollar form) | covered | |
| atomic::TestPrintSubshellBraces | atomic | positive | section Canonical Printing — canonical style (subshell and block spacing) | covered | |
| atomic::TestPrintMultilineBlock | atomic | positive | section Canonical Printing — canonical style (multi-line bodies indent) | covered | |
| atomic::TestPrintPipelineContinuation | atomic | positive | section Canonical Printing — canonical style (pipeline continuation) | covered | |
| atomic::TestPrintCommentSpacing | atomic | positive | section Canonical Printing — canonical style (comment spacing) | covered | |
| atomic::TestPrintTrailingNewlineOnlyForFile | atomic | positive | section Canonical Printing — construction and supported nodes (trailing newline) | covered | |
| atomic::TestPrintUnsupportedNodeError | atomic | failure_path | section Error Semantics (unsupported node type) | covered | |
| atomic::TestIndentSpaces | atomic | positive | section Canonical Printing — Indent | covered | |
| atomic::TestBinaryNextLine | atomic | positive | section Canonical Printing — BinaryNextLine | covered | |
| atomic::TestSwitchCaseIndent | atomic | positive | section Canonical Printing — SwitchCaseIndent | covered | |
| atomic::TestSpaceRedirects | atomic | positive | section Canonical Printing — SpaceRedirects | covered | |
| atomic::TestFunctionNextLine | atomic | positive | section Canonical Printing — FunctionNextLine | covered | |
| atomic::TestMinifyRules | atomic | positive | section Canonical Printing — Minify | covered | |
| atomic::TestMinifyDropsComments | atomic | positive | section Canonical Printing — Minify (comments dropped) | covered | |
| atomic::TestSingleLineJoins | atomic | positive | section Canonical Printing — SingleLine | covered | |
| atomic::TestSingleLineHeredoc | atomic | positive | section Canonical Printing — SingleLine (heredoc exception) | covered | |
| atomic::TestPrintNegationBackground | atomic | positive | section Canonical Printing — canonical style (negation, trailing ampersand) | covered | |
| atomic::TestPrintHeredocVerbatim | atomic | positive | section Canonical Printing — canonical style (heredoc bodies verbatim) | covered | |
| atomic::TestPrintOptionDirectApplication | atomic | positive | section Canonical Printing — construction and supported nodes (options as functions) | covered | |
| atomic::TestWalkOrder | atomic | positive | section Word Utilities and Rewrites — Walk (order) | covered | |
| atomic::TestWalkPruning | atomic | positive | section Word Utilities and Rewrites — Walk (pruning on false) | covered | |
| atomic::TestQuoteUnchanged | atomic | positive | section Word Utilities and Rewrites — Quote (no quoting needed) | covered | |
| atomic::TestQuoteSingleQuotes | atomic | positive | section Word Utilities and Rewrites — Quote (single-quote form) | covered | |
| atomic::TestQuoteEmpty | atomic | positive | section Word Utilities and Rewrites — Quote (empty string) | covered | |
| atomic::TestQuoteDoubleQuotes | atomic | positive | section Word Utilities and Rewrites — Quote (double-quote form) | covered | |
| atomic::TestQuoteDollarEscapes | atomic | positive | section Word Utilities and Rewrites — Quote (dollar-escape form) | covered | |
| atomic::TestQuoteNullByteError | atomic | failure_path | section Error Semantics (Quote with NUL) | covered | |
| atomic::TestQuotePosixEscapesError | atomic | failure_path | section Error Semantics (Quote POSIX escapes) | covered | |
| atomic::TestSplitBracesValid | atomic | positive | section Word Utilities and Rewrites — SplitBraces | covered | |
| atomic::TestSplitBracesSequence | atomic | positive | section Word Utilities and Rewrites — SplitBraces (sequence expression) | covered | |
| atomic::TestSplitBracesMalformed | atomic | positive | section Word Utilities and Rewrites — SplitBraces (malformed fragments) | covered | |
| atomic::TestSplitBracesNoBraces | atomic | positive | section Word Utilities and Rewrites — SplitBraces (no brace character) | covered | |
| atomic::TestSimplifyRules | atomic | positive | section Word Utilities and Rewrites — Simplify | covered | |
| atomic::TestSimplifyNoChange | atomic | positive | section Word Utilities and Rewrites — Simplify (no change reported) | covered | |
| atomic::TestOperatorStrings | atomic | positive | section Public Interface — Import Surface (operator String methods) | covered | |
| atomic::TestEncodeTypeKeyFirst | atomic | positive | section Typed JSON Interchange — encoding (Type key first) | covered | |
| atomic::TestEncodeNoTypeOnFixedFields | atomic | positive | section Typed JSON Interchange — encoding (fixed-type fields untagged) | covered | |
| atomic::TestEncodePosObjects | atomic | positive | section Typed JSON Interchange — encoding (position objects) | covered | |
| atomic::TestEncodeOmitsZeroFields | atomic | positive | section Typed JSON Interchange — encoding (zero fields omitted) | covered | |
| atomic::TestEncodeIndent | atomic | positive | section Typed JSON Interchange — encoding (EncodeOptions.Indent) | covered | |
| atomic::TestEncodeNonFileRoot | atomic | positive | section Typed JSON Interchange — encoding (non-File root) | covered | |
| atomic::TestDecodeRoundTrip | atomic | positive | section Typed JSON Interchange — decoding | covered | |
| atomic::TestDecodeUnknownTypeError | atomic | failure_path | section Error Semantics (unknown Type value) | covered | |
| atomic::TestDecodeWhitespaceTolerant | atomic | positive | section Typed JSON Interchange — decoding (whitespace irrelevant) | covered | |
| integration::TestRoundTripFixpointBash | integration | positive | section Cross-View Invariants — invariant 1 | covered | |
| integration::TestRoundTripFixpointPOSIX | integration | positive | section Cross-View Invariants — invariant 1 | covered | |
| integration::TestRoundTripFixpointMksh | integration | positive | section Cross-View Invariants — invariant 1 | covered | |
| integration::TestRoundTripFixpointBats | integration | positive | section Cross-View Invariants — invariant 1 | covered | |
| integration::TestRoundTripLayoutOptions | integration | positive | section Cross-View Invariants — invariant 1 (layout option sets) | covered | |
| integration::TestMinifyReparsesAndStabilises | integration | positive | section Cross-View Invariants — invariant 8 | covered | |
| integration::TestKeepCommentsFixpoint | integration | positive | section Cross-View Invariants — invariant 1 + Parsing Shell Programs — comments | covered | |
| integration::TestSimplifyThenRoundTrip | integration | positive | section Word Utilities and Rewrites — Simplify + Cross-View Invariants — invariant 1 | covered | |
| integration::TestNodeExtentsOrdered | integration | positive | section Cross-View Invariants — invariant 2 | covered | |
| integration::TestHeredocExtentBeyondStatement | integration | positive | section Parsing Shell Programs — here-documents (statement End vs heredoc body) | covered | |
| integration::TestPositionsAgreeWithSource | integration | positive | section Cross-View Invariants — invariant 2 | covered | |
| integration::TestWalkVisitCounts | integration | positive | section Cross-View Invariants — invariant 4 | covered | |
| integration::TestPosAfterAgreesWithOffsets | integration | positive | section The Syntax Tree — positions (After) + Cross-View Invariants — invariant 2 | covered | |
| integration::TestJSONRoundTripBashCorpus | integration | positive | section Cross-View Invariants — invariant 3 | covered | |
| integration::TestJSONRoundTripOtherDialects | integration | positive | section Cross-View Invariants — invariant 3 | covered | |
| integration::TestJSONRoundTripSubtrees | integration | positive | section Cross-View Invariants — invariant 3 (interface roots) | covered | |
| integration::TestJSONStructuralRootsDoNotDecode | integration | failure_path | section Typed JSON Interchange — decoding (structural roots) + Error Semantics | covered | |
| integration::TestJSONIndentedEncodeDecodesEqual | integration | positive | section Typed JSON Interchange — encoding + decoding (whitespace irrelevant) | covered | |
| integration::TestQuoteParseAgreementBash | integration | positive | section Cross-View Invariants — invariant 5 | covered | |
| integration::TestQuoteParseAgreementMksh | integration | positive | section Cross-View Invariants — invariant 5 | covered | |
| integration::TestQuoteContentPreserved | integration | positive | section Cross-View Invariants — invariant 5 (content equality) | covered | |
| integration::TestParseErrorRenderingAgreesWithPosition | integration | failure_path | section Cross-View Invariants — invariant 6 | covered | |
| integration::TestFileNameThreading | integration | positive | section Cross-View Invariants — invariant 6 (name threading) | covered | |
| integration::TestIncompleteAcrossEntryPoints | integration | failure_path | section Cross-View Invariants — invariant 7 | covered | |
| integration::TestStmtsSeqAgreesWithParse | integration | positive | section Incremental and Fragment Parsing — statement iteration + Cross-View Invariants — invariant 1 | covered | |
| integration::TestInteractiveSeqAgreesWithParse | integration | positive | section Incremental and Fragment Parsing — interactive parsing + Cross-View Invariants — invariant 1 | covered | |

Total: 170 | kept (covered): 170 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 170

Layers: atomic 144, integration 26. Assertion kinds: positive 144, failure_path 26, atomic positive share 121/144 = 84%.
