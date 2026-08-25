# Track A rewrite audit — kong-cli-grammar-fullrepro-001

Upstream suite at v1.16.1: 19 test files, 290 test functions (271 black-box
in package `kong_test`, 18 white-box in package `kong`, plus one
benchmark-only file). Every black-box file imports
`github.com/alecthomas/assert/v2` at module level; `kong_test.go`
additionally imports `github.com/alecthomas/repr` for golden value
rendering. Neither dependency exists in the oracle module, and every kept
function would need its assertion surface rewritten to plain `testing`.

| file | funcs | package decl | decision | reason |
|---|---|---|---|---|
| kong_test.go | 157 | `kong_test` | DISCARD | every assertion via third-party assert/v2 + repr golden rendering; large minority exercise out-of-scope options (`WithHyphenPrefixedParameters`, `IgnoreFields`, `AutoGroup`, `BindFor`, `BindSingletonProvider`, `Visit`, signature helpers) that the spec deliberately excludes; rewrite = full re-authoring |
| mapper_test.go | 40 | `kong_test` | DISCARD | assert/v2-bound; several funcs exercise unspecced mapper extensions (`BoolMapperExt`, `MapperValue`, `KindMapper`, counter float forms) and platform-specific file mappers |
| help_test.go | 19 | `kong_test` | DISCARD | assert/v2-bound whole-screen golden comparisons incl. wrap-width and formatting options the spec does not pin (`ValueFormatter`, `NoAppDescFormat`, terminal-width interplay) |
| resolver_test.go | 18 | `kong_test` | DISCARD | assert/v2-bound; several funcs bind to unspecced resolver hooks (`VarsContributor`, validation callbacks) |
| tag_test.go | 18 | `kong_test` | DISCARD | assert/v2-bound; majority parse `kong.Tag` internals directly (`parseTagString` surface) rather than grammar behaviour |
| signature_test.go | 10 | `kong_test` | DISCARD | exercises the unspecced `Signature` interface |
| model_test.go | 3 | `kong_test` | DISCARD | assert/v2-bound |
| config_test.go | 2 | `kong_test` | DISCARD | assert/v2-bound |
| helpwrap1.18_test.go / helpwrap1.19_test.go | 2 | `kong_test` | DISCARD | go-version-conditional golden wrap output; spec does not define terminal-width wrapping |
| mapper_linux_test.go / mapper_windows_test.go | 3 | `kong_test` | DISCARD | platform-conditional; windows file unbuildable on the scoring platform |
| options_test.go | 9 | `kong` | DISCARD | in-package white-box (reads unexported parser state) |
| defaults_test.go / global_test.go / interpolate_test.go / scanner_test.go / util_test.go | 9 | `kong` | DISCARD | in-package white-box; interpolate/util test unexported helpers directly |
| benchmark_test.go | 0 | `kong` | DISCARD | benchmarks only |

## Summary

```
functions_in_scope: 290
functions_kept (Track A): 0
functions_excluded: 290 (100%)
```

Early trigger fires: all upstream files discarded at Step 1 (100% > 50%
threshold). Proceeding to Track B generation, consistent with the four
prior Go tasks in this batch whose upstream suites were bound to
alecthomas/assert or in-package white-box state (participle, gocmp, cty,
goyaml).

Track B targets are enumerated from the spec: 8 behavior sections, the
Error Semantics table, 8 Cross-View Invariants, and 2 Representative
Workflows, with per-section minimums per the test-filter skill.
