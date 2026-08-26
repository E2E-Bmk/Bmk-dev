# PIPELINE STATE — postcss-css-ast-engine-fullrepro-001

state:      S3_DONE
stage:      3
spec_iter:  0
filter_iter: 0
eval_iter:  0
language:   typescript
functions_in_scope: 0 (Track A empty: 24/26 upstream files import ../lib/*, 2 import internal lib/stringifier.js + lib/tokenize.js, 4 need the external postcss-parser-tests corpus)
functions_kept: 125 (98 atomic / 22 integration / 5 system_e2e)
functions_excluded: 0 (Track A)
oracle_count: 125
updated:    2026-08-26

## History

| # | date | from | to | note |
|---|------|------|----|------|
| 1 | 2026-08-26 | S1_SCREENING | S1_SELECTED | filter_notes complete; keep: postcss@8.5.26 (29.0k stars, 277.9M weekly downloads), 4829 runtime LOC + 3582 d.ts contract, 613 upstream test fns in 26 files; core difficulty = raws-preserving tokenizer/parser/stringifier (byte-exact round-trip) + lazy plugin pipeline, memorized 8.x API carries no parser; upstream tests non-portable (24/26 import ../lib/*, 4 need postcss-parser-tests corpus) -> Track B planned; source maps excluded from scope |
| 2 | 2026-08-26 | S1_SELECTED | S2_SPEC_DRAFT | selection recorded in filter_notes (CANDIDATES.md lives outside this staging flow, consistent with prior 14 staged tasks); scope_plan set (target_subdomain = AST model + parse/stringify + manipulation/traversal + pipeline + errors/positions + list + JSON codec; expected_oracle_max=135) |
| 3 | 2026-08-26 | S2_SPEC_DRAFT | S2_SPEC_CHECK | behavioral probes pp1-pp6 executed against installed 8.5.26: raws capture (before/between/after/semicolon/afterName/important/left-right), {raw,value} caches for commented selector/value + selective invalidation on reassignment, byte-exact round trips (CRLF, BOM, ' ! important'), constructed-node defaults (4-space indent, semicolon inheritance, 'a {}'), bodyless atrule nodes undefined vs [] distinction, insertion validation errors, mutation-safe each, walk filters, NoWorkResult fast path (css returns unparsed input; root throws on invalid), LazyResult sync/async lifecycle, visitor order Once->enter/exit->OnceExit + keyed-'*' Declaration listeners + revisit-on-mutation, creator fn .postcss, prepare(result), warning positions word/index + toString, node.error/positionBy/rangeBy/fromOffset ({line,col}), plugin field on thrown errors, toJSON inputs array + fromJSON revival, document concatenation, list/space/comma/split, selectors setter separator reuse |
| 4 | 2026-08-26 | S2_SPEC_CHECK | S2_SPEC_DONE | spec.md written (six-layer, 10 behavior domains, 7 CVIs, root-entry import surface incl. callable default carrying named exports); clauses.md sidecar with 75 EARS clause IDs; 25-check pass: four can/may sentences rephrased to must/where-form, Non-Goals prefixes compliant, no leakage words, API Catalog Name/Kind/Role only, source-map + custom-syntax + color excluded as non-goals |
| 5 | 2026-08-26 | S2_SPEC_DONE | S3A_IMPORT_AUDIT | candidate body is the whole file (no internal header used, consistent with prior staged tasks) |
| 6 | 2026-08-26 | S3A_IMPORT_AUDIT | S3A_REWRITE | audit: 24/26 upstream test files import '../lib/postcss.js' or other ../lib/* paths; 2 remaining (stringifier/tokenize) import internal modules lib/stringifier.js + lib/tokenize.js; 4 files additionally require the external postcss-parser-tests corpus; zero files import the published package name |
| 7 | 2026-08-26 | S3A_REWRITE | S3B_TRIGGER | rewrite_audit.md written: 26/26 files discarded (100% > 50% early trigger); unit layer partially bound to internal modules (tokenizer/stringifier) and uvu runner; corpus files bound to external fixture package |
| 8 | 2026-08-26 | S3B_TRIGGER | S3B_GENERATE | coverage step adapted per TS precedent (no Python coverage harness for vitest): generation targets derived from spec section quota table + probe evidence pp1-pp6, matching immer/yjs/tanstack precedent |
| 9 | 2026-08-26 | S3B_GENERATE | S3B_REFERENCE | generated 125 tests (98 atomic / 22 integration / 5 system_e2e) across 4 vitest files; pinned release passes 125/125 local vitest; tsc --noEmit clean; 1 spec claim corrected from execution (a stale commented-value raws entry is kept, not deleted, on reassignment - the stringifier ignores it and prints the new value) plus 3 expected-value fixes observed from the reference (string-append formatting inference from adjacent siblings, replaceWith unwrap keeping the first child's raws.before, proxy-wrapped nodes inside listeners compared by print not identity) |
| 10 | 2026-08-26 | S3B_REFERENCE | S3B_DUMMY | inert stub (no-op parse/stringify/factories, empty containers, undefined getters, no-throw processor; covers default export + named factories/classes/list/parse/stringify) fails 125/125; 2 tests strengthened with value assertions after early stub runs exposed vacuous instanceof-only passes (factory nodes, default-export factory helpers) |
| 11 | 2026-08-26 | S3B_DUMMY | S3_DONE | lint LINT_PASS (fresh, newer than all oracle files); static verify STATIC_VALID after balancing brace characters inside broken-CSS string literals with trailing comments (the harness's static discovery tracks describe nesting by raw brace depth, strings included); artifacts written (kept_nodeids 125, taxonomy, spec_test_map 125 covered, reference_score 125/125, depends_on 27/27); atomic positive share 91%, zero no_check; packet staged |
