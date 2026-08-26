# rewrite_audit — postcss-css-ast-engine-fullrepro-001

Upstream test root: /tmp/repos/postcss/test (tag 8.5.26, commit
07b25773f38f77919f2af02ae3e8896b0deb5988). 26 test files, 613 test blocks, 8566 LOC, uvu runner.

## Import classification (file level)

Every one of the 26 test files falls into at least one non-portable class:

| class | evidence | count | action |
|---|---|---|---|
| library internal (bidirectional): `import ... from '../lib/postcss.js'` or other `../lib/*` paths | all node/class/pipeline tests construct trees through the repo source tree, not the published package | 24/26 | discard |
| library internal module under test: `lib/tokenize.js`, `lib/stringifier.js` | tokenize.test.js asserts internal token arrays; stringifier.test.js drives the internal Stringifier class directly — neither is a public export of the package root | 2/26 | discard |
| upstream test infrastructure: external `postcss-parser-tests` corpus package + `test/errors.ts` + `test/types.ts` helpers | parse/stringify corpus files iterate fixture CSS files shipped in a separate npm package that is not a dependency of the oracle environment | 4/26 overlap | discard |
| out-of-scope module: map.test.ts, previous-map.test.ts (source maps), document.test.ts partially (custom-syntax parsers) | behavior this spec excludes as non-goals | 3/26 overlap | discard |

## Rewrite feasibility

- The unit layer's heaviest files (tokenize, stringifier, parse corpus) are bound to internal
  modules and an external fixture corpus; rewriting them against the package root changes what
  each test verifies (Q1: token-array shapes and internal Stringifier dispatch are not public
  behavior).
- The remaining class files import `'../lib/postcss.js'` — mechanically redirectable — but rely
  on uvu's runner and on `test/errors.ts`/`test/types.ts` helpers, and a large share assert
  source-map interactions or exact reason wording that the spec excludes. The salvageable
  behavioral intents (raws capture, round trips, walk semantics, warnings) are fully replaceable
  by generation against the installed release with observed values.
- Zero files import `postcss` by its published name; there is no subset importable against the
  installed package as-is.

rewrite_result: fail for all 26 files.
failure_reason (uniform): module-level imports resolve only inside the upstream repo source tree
(`../lib/*`) or require an external fixture corpus package; two files' behavioral intent is bound
to internal modules the published root does not export.

## Decision

Track A yields 0 portable files (100% discard > 50% early-trigger threshold) → Track B
generated oracle against the installed `postcss@8.5.26` package, same precedent as
immer / yjs / tanstack-table-core.

functions_in_scope (Track A): 0
