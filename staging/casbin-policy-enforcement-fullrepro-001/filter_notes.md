# Stage 1 evidence brief — casbin-policy-enforcement-fullrepro-001

```
repo: casbin/casbin
source_path: https://github.com/casbin/casbin (local: dev/repo-pool/casbin)
commit: e9df34e092f925e0031f7db4e062f2fbddf3dc86 (tag v3.11.0, released 2026-08-04)
src_loc: 14187 total non-test Go LOC (root enforcers + model + persist + rbac +
  effector + util + config + constant + errors, examples excluded); scoped
  subdomain (root Enforcer + model + persist string/file adapters + rbac
  default-role-manager + effector + util matchers) ~ 7700
test_functions: 233 top-level Test funcs (root 199 + model + util)
test_files: 36 at root + model/util/persist test files
dominant_test_styles: white-box (package casbin) table-driven testEnforce
  helpers over examples/*.conf + examples/*.csv fixtures; benchmark files;
  a few JSON/frontend snapshot tests
public_docs: casbin.org/docs (PERM metamodel, matcher function table, effector
  semantics, RBAC/domain API reference), README.md, pkg.go.dev/github.com/
  casbin/casbin/v3 GoDoc
core_fact_source: one in-memory authorization state: a PERM model (request/
  policy/role definitions, matcher expression, effect rule) + policy/grouping
  rule store + role-inheritance graphs (per grouping token, optionally
  domain-scoped, with pattern-matching functions)
derived_views: (1) Enforce/EnforceEx verdicts (matcher evaluation x effector
  fold, with matched-rule explanation); (2) management API reads (GetPolicy,
  GetFilteredPolicy, HasPolicy, counts) after Add/Remove/Update mutations;
  (3) RBAC introspection (GetRolesForUser, GetUsersForRole, GetImplicit*,
  GetPermissionsForUser, domain variants) projected off the same grouping
  rules; (4) persistence round-trip (SavePolicy/LoadPolicy through adapters)
  rebuilding the same state; (5) error surface for malformed models/requests
external_deps: github.com/casbin/govaluate (expression eval),
  github.com/bmatcuk/doublestar/v4 (globMatch), github.com/google/uuid — all
  pure Go, no network, fetched from module proxy at build time
test_import_audit: HIGH_RISK for direct lift — root tests are in-package
  (package casbin) and lean on examples/ fixture files and unexported helpers
  (testEnforce and friends assert via t.Helper wrappers). Track B expected;
  fixture-free construction is available publicly (model.NewModelFromString,
  persist/string-adapter, AddPolicy API).
docs_test_alignment: aligned — casbin.org documents exactly the projections
  the tests exercise (model syntax, matcher functions, effect rules, RBAC API)
contamination_note: casbin/v3@v3.11.0, released 2026-08-04, relative to
  training cutoff: likely after for the /v3 module path; casbin/v2 semantics
  are long public — difficulty must come from precise matcher/effector/rbac
  graph semantics, not API obscurity
decision: keep
reason: config-driven authorization rule engine: a PERM matcher mini-language
  reinterpreted at enforce time over a role graph with domain scoping and
  pattern matchers, folded by pluggable effect rules, with >= 4 public
  projections of one policy state.
risks: (a) upstream tests not liftable (in-package + fixtures) -> Track B
  generation cost; (b) large surface (cached/synced/distributed/transactional
  enforcers, watchers, dispatcher, frontend) — scope strictly to the core
  Enforcer; (c) matcher language is powered by govaluate — spec must describe
  observable expression behavior, not govaluate internals; (d) RBAC pattern
  matching (keyMatch2 role patterns) has subtle activation rules — every spec
  claim needs a reference probe.
scope_plan: target_subdomain=core Enforcer over PERM model state (model
  parsing, Enforce/EnforceEx with matcher functions + in operator + ABAC
  attribute access, effect rules incl. deny-override/priority, management API,
  RBAC API incl. domains + implicit queries, string/file adapter round-trip),
  expected_oracle_max=95; out of scope: cached/synced/distributed/
  transactional/context enforcers, watchers, dispatcher, frontend JSON, logging,
  detector, transactions.
```

## Difficulty shapes observed (selection rationale, not oracle targets)

- **Reimplementation of a format rule**: the PERM model text (INI sections
  request_definition/policy_definition/role_definition/policy_effect/matchers)
  is parsed into an evaluatable rule; matcher expressions re-interpret
  r.sub/r.obj/r.act and p.* tokens per request with function calls
  (keyMatch/keyMatch2/regexMatch/globMatch/ipMatch) and operator semantics.
- **A lazily resolved reference graph**: grouping rules (g, g2, domain-scoped)
  build role-inheritance graphs whose transitive closure answers both Enforce
  matcher calls g(r.sub, p.sub) and introspection (GetImplicitRolesForUser),
  including pattern-matching role links.
- **An equivalence judgement fold**: the effector folds per-policy matcher
  verdicts under allow-override / deny-override / allow-and-deny / priority
  rules where a false allow is as wrong as a missed deny.
- **>= 3 public projections of one state**: enforcement verdicts, management
  reads after mutations, RBAC implicit queries, and adapter round-trips must
  all agree on the same policy store.

## Selection record

| repo | status | metric | detail |
|------|--------|--------|--------|
| go-chi/chi | REJECTED | router pkg 1785 LOC < 3000 | middleware/ is an unrelated utility collection; core alone under gate |
| casbin/casbin | SELECTED | 14.2k LOC, 233 test funcs | PERM rule engine; role graphs, effectors, 4+ projections; Track B expected |
