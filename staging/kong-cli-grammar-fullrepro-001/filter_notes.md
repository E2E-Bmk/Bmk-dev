# Stage 1 evidence brief — kong-cli-grammar-fullrepro-001

```
repo: alecthomas/kong
source_path: https://github.com/alecthomas/kong
commit: 0678fd30af8be8bae6dc9f9c6f143cc549450be2 (tag v1.16.1)
src_loc: 6332 (25 non-test .go files, single package, no vendored/generated code)
test_functions: 290 (271 black-box in package kong_test across 12 files;
  18 white-box in package kong across 7 files; 1 benchmark file)
test_files: 19
dominant_test_styles: table-driven unit assertions via alecthomas/assert/v2;
  help_test.go compares rendered help against expected multi-line strings
  (observable output, spec-able, not internal snapshots)
public_docs: README.md (775 lines: full struct-tag DSL reference, hooks,
  resolvers, mappers, variable interpolation, help customization); godoc
core_fact_source: the grammar model — an Application node tree (commands,
  flags, positionals, groups) derived entirely from Go struct tags at
  kong.New time
derived_views:
  1. parsing — argv tokens bound onto the caller's struct via Context
     (Parse/Resolve/Apply/Run), incl. defaults, enums, required/xor/and
     groups, negatable flags, passthrough, interpolation
  2. help rendering — --help / HelpOptions projection of the same node tree
     (usage line, grouped flags, command tree, envar/default annotations)
  3. model introspection — public Model/Node/Flag/Value API over the tree
  4. resolution — Resolver chain (env vars, JSON config, custom) feeding
     the same values the parser binds
  5. lifecycle callbacks — BeforeReset/BeforeResolve/BeforeApply/AfterApply
     hooks and Run(...) dispatch bound to the selected node
external_deps: none at runtime (go.mod test-only: alecthomas/assert/v2,
  alecthomas/repr); no network, no CGO
test_import_audit: clean — no internal-package imports anywhere; black-box
  files import only github.com/alecthomas/kong + third-party assert/v2
  (assert dep forces Track B-style rewrite if kept, same as participle)
docs_test_alignment: aligned — README documents the same tag DSL, help and
  resolver behaviours the test suite exercises
contamination_note: alecthomas/kong@v1.16.1, released 2026-08-09, relative
  to training cutoff: after (repo well-known earlier; v1.16.x behaviours
  incl. recent tag additions are post-cutoff)
decision: keep
reason: rule-engine over a repo-specific struct-tag mini-language with 5
  public projections of one node tree, zero runtime deps, deterministic
  suite, post-cutoff pin.
risks: CLI-parsing domain is adjacent to high-saturation argparse patterns —
  mitigated because the observable behaviour under test is kong's own tag
  grammar (xor/and groups, embed/prefix, negatable, passthrough modes,
  interpolation, hook ordering), not generic flag parsing; help output
  assertions must quote exact rendering, which the README + probes pin down.
scope_plan: N/A (src_loc 6332 < 15000, test_functions 290 < 300)
```

## Difficulty shapes (selection rationale)

- **Reimplementation of a format rule:** struct tags (`cmd`, `arg`, `enum`,
  `xor`, `and`, `group`, `embed`, `prefix`, `negatable`, `passthrough`,
  `${var}` interpolation) compile into a grammar; a delivery must derive
  binding, validation and help semantics from the DSL, not call into it.
- **Integration spanning >=3 projections:** one struct definition must agree
  across parse results, help text, model introspection and resolver input.
- **Equivalence judgement (partial):** flag matching involves aliases,
  negation prefixes, group exclusivity and levenshtein suggestions where a
  false accept is as wrong as a false reject.

## source_boundary

Candidate-visible artifact is spec.md only. The spec is written from
README.md, godoc and black-box probe programs against the pinned v1.16.1;
no upstream test text is quoted. Oracle tests are benchmark-owned (Track A/B
decision recorded in filter/rewrite_audit.md at Stage 3).
