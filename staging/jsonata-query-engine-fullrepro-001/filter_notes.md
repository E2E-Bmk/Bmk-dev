repo: jsonata-js/jsonata
source_path: https://github.com/jsonata-js/jsonata (wip/repo-cache/jsonata-src)
commit: 6c7e95fdbf4405a1e741852a7cd8cd985b4305bb (npm gitHead for jsonata@2.2.2)
language: typescript
src_loc: 7678 (src/*.js: jsonata.js evaluator, parser.js TDOP parser, functions.js library, datetime.js picture engine, signature.js validator, utils.js; ships complete jsonata.d.ts)
test_functions: ~1659 expression cases in 1291 JSON case files across 102 groups (test/test-suite) + 4 mocha driver/implementation files
test_files: 102 JSON groups + test/run-test-suite.js, implementation-tests.js, parser-recovery.js, parser-pluggable-regex.js, async-function.js
dominant_test_styles: data-driven value-equality cases (expr + data -> expected result or expected error code); mocha implementation tests for bindings/callbacks
public_docs: https://docs.jsonata.org (language reference: paths, operators, sequences, function library, datetime picture strings, error codes), README, exerciser
core_fact_source: one compiled expression per source string - a parsed AST plus a static environment (built-in function library, user bindings via assign/registerFunction) that evaluation projects over arbitrary JSON inputs with JSONata sequence semantics
derived_views: (1) compilation projection (jsonata(expr): parse errors as structured {code, position, token}); 
  (2) evaluation projection (async evaluate: path navigation, predicates, wildcards/descendants, flattening/singleton sequence rules, empty-vs-undefined results);
  (3) operator algebra (arithmetic/comparison/boolean/concat/range/in, conditional, coalescing, chain ~>);
  (4) constructors and reshaping (array/object constructors, grouping {}, order-by ^, transform |...|);
  (5) function library projection ($string/$number/$substring/$split/$join/$map/$filter/$reduce/$sift/$each/$sort/$distinct/$merge/$keys/$lookup/$spread/$count/$sum/$max/$min/$average/$boolean/$exists/$type/$match/$replace/$contains with regex, $fromMillis/$toMillis picture strings);
  (6) lambda/closure projection (user-defined functions, recursion, higher-order composition, signature strings with coercion/errors);
  (7) bindings projection (expression.assign, registerFunction, $ variables at evaluate time);
  (8) AST projection (expression.ast() node shapes);
  (9) error semantics (documented error codes with position/token, compile-time vs runtime)
external_deps: none at runtime; upstream tests use mocha+chai only
test_import_audit: HIGH_RISK for direct reuse - all drivers require('../src/jsonata') relative source paths, and the JSON case corpus needs the upstream driver harness (datasets directory, timelimit/depth options) -> Track B generated oracle importing only 'jsonata'
docs_test_alignment: aligned - docs.jsonata.org documents the same language surface (including error codes) that the JSON corpus exercises
contamination_note: jsonata@2.2.2, released 2026-07-16, relative to training cutoff: language stable since 2016 and likely represented in training data; difficulty rests on sequence-semantics edge rules (singleton coercion, empty results, flattening), function signature coercion, structured error codes/positions, and datetime picture rules rather than API novelty
decision: keep
reason: full query-language reimplementation (TDOP parser + sequence-semantics evaluator + 60+ function library + signature validator) with >=3-projection integration (parse/evaluate/bindings/AST/errors) and equivalence-grade value semantics; exactly the language-rule-reimplementation shape that resists pattern matching.
risks: (1) upstream tests non-portable (relative requires + JSON corpus driver) -> generated_only oracle, every expected value observed by executing 2.2.2;
  (2) corpus is huge (1659 cases) -> scope to representative behaviors per language area, expected_oracle_max=100;
  (3) exact error-message wording varies -> assert only code/position/token fields the docs declare;
  (4) datetime picture engine is a large sub-language -> restrict to probed picture components and ISO defaults;
  (5) async evaluate returns Promises -> all oracle tests await results.
scope_plan: target_subdomain=compilation and structured parse errors, path navigation (fields, predicates, wildcards, descendants, singleton/flattening sequence rules), operators (arithmetic, comparison, in, range, concat, and/or, conditional, default/coalescing, chain ~>), constructors (array/object, grouping with key collision error, order-by ^), variables and blocks, lambdas/closures/recursion/higher-order functions, function signatures (coercion + T0410-family errors), core function library (string/number/aggregation/array/object/boolean + regex $match/$replace/$split/$contains), $fromMillis/$toMillis basics, expression.assign/registerFunction bindings, evaluate-time bindings object, expression.ast() shapes, runtime error codes (T-series) with position; expected_oracle_max=100
excluded: async callback API beyond one promise check, $eval of remote/URL, environment timeboxing options (timeout/stack/depth limits), parser recovery mode (options.recover) and pluggable RegexEngine, tupleStream/@ # focus-and-index bind advanced forms beyond probed basics, full XPath datetime picture matrix, jsonata exerciser/CLI
