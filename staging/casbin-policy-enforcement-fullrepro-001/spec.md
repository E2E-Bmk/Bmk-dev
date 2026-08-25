# casbin Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`casbin` is an authorization engine for Go. An application hands it two
artifacts — a **model**, a short configuration text that declares what an
access request looks like and what rule decides it, and a **policy**, a list
of rules — and then asks one question repeatedly: is this request allowed?

The model text follows the PERM shape: a request definition names the request
attributes (for example `sub, obj, act`), a policy definition names the rule
attributes, an optional role definition declares inheritance relations, a
policy effect states how per-rule verdicts fold into one decision, and a
matcher is a boolean expression evaluated once per policy rule with the
request and rule bound to `r.*` and `p.*` tokens. Enforcement is therefore a
tiny rule engine: the matcher expression is interpreted against every policy
rule, and the effect rule folds the matches into a single boolean verdict.

The same policy store feeds several other public views: a management API
reads and mutates policy rules; an RBAC API asks questions about the role
graphs that grouping rules induce (including transitive and domain-scoped
queries); and adapters persist the store and rebuild it on load. All views
must stay consistent with each other at every step.

The installable module path is `github.com/casbin/casbin/v3`.

## Non-Goals

- This specification does not require concurrency-safe, cached, distributed,
  or transactional enforcer variants; the single-threaded enforcer is the
  whole scope.
- This specification does not require watchers, dispatchers, or any
  change-notification machinery.
- This specification does not require frontend/JSON serialization helpers or
  logging hooks.
- This specification does not define enforcement over context-carrying
  variants of the API.
- This specification does not require a console interface of any kind.
- This specification does not require matcher-expression features beyond
  those stated in Matcher Language.

## Representative Workflows

**Role-based document access.** One state — a policy store — answers both
enforcement and introspection queries.

```go
m, _ := model.NewModelFromString(`
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
`)
e, _ := casbin.NewEnforcer(m)
e.AddPolicy("admin", "report", "edit")
e.AddGroupingPolicy("alice", "admin")

ok, _ := e.Enforce("alice", "report", "edit")   // true, via the role link
roles, _ := e.GetImplicitRolesForUser("alice")  // ["admin"]
perms, _ := e.GetImplicitPermissionsForUser("alice")
// [["admin" "report" "edit"]]
```

**Explicit deny auditing.** A deny-capable effect rule lets specific rules
veto, and `EnforceEx` names the rule that decided.

```go
// policy_definition: p = sub, obj, act, eft
// policy_effect:     e = some(where (p.eft == allow)) && !some(where (p.eft == deny))
e.AddPolicy("alice", "ledger", "read", "allow")
e.AddPolicy("alice", "ledger", "read", "deny")

ok, _ := e.Enforce("alice", "ledger", "read")   // false: the deny rule vetoes
_, reason, _ := e.EnforceEx("alice", "ledger", "read")
// reason names the matched rule that produced the verdict
```

## Model Definition

A model is created from its configuration text with
`model.NewModelFromString`, which returns the parsed model or an error.
`casbin.NewEnforcer` accepts either a parsed model, or a filesystem path to
the same text (see Persistence).

**Sections.** The text is INI-shaped. Four sections are mandatory:
`[request_definition]` (key `r`), `[policy_definition]` (key `p`),
`[policy_effect]` (key `e`), and `[matchers]` (key `m`).
`[role_definition]` (key `g`) is required only when the matcher or the RBAC
API is used. A text missing mandatory sections must be rejected with an error
mentioning `missing required sections` followed by the missing section names.

**Definitions.** `r` and `p` list comma-separated attribute names; each
becomes a token (`r.sub`, `p.obj`, ...) usable in the matcher. A policy rule
supplies one value per declared `p` attribute. `p.eft` is implicitly
available on every policy definition: when the definition does not declare an
`eft` attribute, every rule's effect reads as `allow`; when it does, the
rule's `eft` value participates in the effect fold. A role definition of the
form `g = _, _` declares a two-place inheritance relation; `g = _, _, _`
scopes the relation by a third place (the domain).

**Effect rules.** The effect expression is one of a fixed repertoire; the
three forms in scope are:

| Effect text | Fold |
|---|---|
| `some(where (p.eft == allow))` | allow when at least one matched rule has effect allow |
| `some(where (p.eft == allow)) && !some(where (p.eft == deny))` | allow when at least one matched rule allows and no matched rule denies |
| `priority(p.eft) \|\| deny` | the first matched rule in policy order decides; no match denies |

With no policy rules at all, every request folds to deny under all three.

## Request Enforcement

`Enforce` takes one value per declared request attribute and returns
`(bool, error)`. For each policy rule, the matcher expression is evaluated
with `r.*` bound to the request values and `p.*` bound to the rule values;
the effect rule then folds the per-rule outcomes into the verdict.

**Request arity.** A request whose value count differs from the request
definition must fail with an error mentioning `invalid request size` and
return false.

**Explanations.** `EnforceEx` behaves like `Enforce` and additionally returns
the matched policy rule (as its value list) that determined the verdict; when
no rule matched, the explanation is empty.

**Batching.** `BatchEnforce` takes a list of requests and returns the list of
their verdicts in the same order.

**Failure of the matcher.** A matcher that references a function that was
never registered must make `Enforce` return false with an error mentioning
`Undefined function` and the function's name.

## Matcher Language

The matcher is a boolean expression over the request and policy tokens.

**Operators.** Equality `==` and inequality `!=` compare strings and numbers;
`&&`, `||`, and `!` are boolean connectives; comparison operators
(`<`, `<=`, `>`, `>=`) apply to numeric values; `in` tests membership of a
value in a parenthesized tuple, for example `r.sub in ("alice", "bob")`.

**Attribute access.** A request value may be an arbitrary Go value; the
matcher may read its exported fields with dotted access (`r.sub.Age > 18`).
This is the ABAC form: the policy rule can stay generic while the request
carries a struct.

**Policy-held rules.** When a policy attribute holds an expression text (for
example a policy definition `p = sub_rule, obj, act` whose rules carry
`r.sub.Age > 18` in the first place), the matcher can evaluate it with
`eval(p.sub_rule)`. The evaluated text sees the same `r.*` bindings as the
matcher itself.

**Role predicate.** With a role definition declared, the matcher may call
`g(r.sub, p.sub)` — true exactly when the first argument inherits the second
through the grouping rules, transitively; with a three-place definition,
`g(r.sub, p.sub, r.dom)` scopes the walk to one domain value.

**Built-in match functions.** These functions of two string arguments are
available in every matcher:

| Function | True when |
|---|---|
| `keyMatch(k1, k2)` | `k2` ends with `/*` and `k1` extends the prefix before the `*` by any suffix, or the strings are equal |
| `keyMatch2(k1, k2)` | `k2` contains `:name` segments, each matching exactly one path segment of `k1` (`/res/:id` matches `/res/42`, not `/res/42/sub`) |
| `regexMatch(k1, k2)` | `k1` matches the regular expression `k2` |
| `globMatch(k1, k2)` | `k1` matches the shell glob `k2`, where `*` does not cross `/` boundaries |
| `ipMatch(ip1, ip2)` | `ip1` is an IP address inside `ip2`, which is an address or CIDR block |

## Role Inheritance

Grouping rules (`g` entries) induce a directed inheritance graph per grouping
key: `AddGroupingPolicy("alice", "admin")` makes `alice` inherit `admin`.
The graph answers matcher `g(...)` calls and the whole RBAC API, always
transitively closed at query time: after linking `alice -> admin` and
`admin -> super`, `alice` inherits both.

**Direct queries.** `GetRolesForUser` returns only directly linked roles;
`GetUsersForRole` returns direct members; `HasRoleForUser` tests a direct
link. `AddRoleForUser` and `DeleteRoleForUser` add and remove one link and
report whether the store changed.

**Implicit queries.** `GetImplicitRolesForUser` returns all inherited roles
in walk order, including transitive ones. `GetPermissionsForUser` returns
only the policy rules whose subject is the user itself, while
`GetImplicitPermissionsForUser` also includes rules whose subject is any
inherited role.

**Permission helpers.** `AddPermissionForUser` appends a policy rule for the
user, `HasPermissionForUser` tests one, and `DeletePermissionsForUser`
removes every policy rule whose subject is the user, reporting whether
anything was removed.

**Domains.** With a three-place role definition, grouping rules carry a
domain: `AddGroupingPolicy("alice", "admin", "tenant1")` links alice to admin
inside tenant1 only. Matcher walks with `g(r.sub, p.sub, r.dom)` must not see
links from other domains. `GetRolesForUserInDomain` and
`GetUsersForRoleInDomain` are the domain-scoped direct queries (returning
plain slices), and `DeleteRoleForUserInDomain` removes one domain-scoped
link.

## Policy Management

The policy store holds one rule list per policy key and per grouping key.
All management calls that mutate return `(bool, error)` where the boolean
reports whether the store changed.

**Single-rule calls.** `AddPolicy` appends a rule and returns false (with a
nil error) when an identical rule already exists. `RemovePolicy` removes a
rule and returns false when it was absent. `HasPolicy` tests membership
without mutating. The grouping twins `AddGroupingPolicy`,
`RemoveGroupingPolicy`, `HasGroupingPolicy`, and `GetGroupingPolicy` behave
identically over the grouping store.

**Batch adds are atomic.** `AddPolicies` adds several rules at once; when any
one of them already exists, no rule is added and the call returns false.

**Updates.** `UpdatePolicy` replaces one existing rule with a new one in
place.

**Reads.** `GetPolicy` returns every policy rule as a list of value lists.
`GetFilteredPolicy(fieldIndex, values...)` returns exactly the rules whose
attributes match the given values starting at the given attribute index (an
empty string matches anything). `RemoveFilteredPolicy` removes that same
selection and reports whether anything was removed.

**Catalogs.** `GetAllSubjects`, `GetAllObjects`, and `GetAllActions` return
the distinct first, second, and third policy attribute values in first-seen
order; `GetAllRoles` returns the distinct inherited-role names appearing in
grouping rules.

## Persistence

An enforcer may be constructed with or without an adapter.

**Construction forms.** `NewEnforcer(m)` with a parsed model starts with an
empty store and no adapter. `NewEnforcer(modelPath, policyPath)` loads the
model text from the first file and the policy from the second through a file
adapter; the policy file is CSV-shaped, one rule per line, key first
(`p, alice, data1, read`). `NewEnforcer(m, adapter)` combines a parsed model
with any adapter value.

**String adapter.** `stringadapter.NewAdapter(text)` (import path
`github.com/casbin/casbin/v3/persist/string-adapter`) holds the same
CSV-shaped rules in memory; its `Line` field carries the current text.

**Load and save.** Construction with an adapter loads the adapter's rules
into the store immediately. `LoadPolicy` re-reads the adapter and replaces
the in-memory store, discarding unsaved mutations. `SavePolicy` writes the
current store back through the adapter; a string adapter's `Line` then
reflects the full store, one rule per line.

## State Model

One enforcer owns three pieces of state:

- **Model**: the parsed definitions, effect rule, and matcher expression,
  fixed at construction (mutable only through the model value itself).
- **Policy store**: the rule lists for every policy and grouping key; the
  single source for enforcement, management reads, RBAC queries, and saves.
- **Role graphs**: the inheritance graphs induced by the grouping rules,
  rebuilt to stay consistent with the store after every mutation and load.

Projections: (1) `Enforce`/`EnforceEx`/`BatchEnforce` evaluate matcher x
effect over the store; (2) management reads return the store's rules
verbatim; (3) RBAC queries walk the role graphs; (4) adapters serialize the
store and rebuild it on load. A mutation through any write call must be
visible through all four projections immediately.

## Error Semantics

Errors are returned, not panicked. Message fragments below are contractual
("mentioning" means the error's rendering includes the fragment).

| Condition | Result |
|---|---|
| Model text lacking a mandatory section | `NewModelFromString` returns an error mentioning `missing required sections` |
| `Enforce` called with a value count different from the request definition | returns false and an error mentioning `invalid request size` |
| Matcher calls a function that does not exist | `Enforce` returns false and an error mentioning `Undefined function` |
| `AddPolicy` of an existing rule | returns `(false, nil)`; store unchanged |
| `RemovePolicy` of an absent rule | returns `(false, nil)`; store unchanged |
| `AddPolicies` where any rule already exists | returns `(false, nil)`; no rule added |
| Enforcement with an empty policy store | returns `(false, nil)` under every in-scope effect rule |

## Cross-View Invariants

1. After any successful mutation (`AddPolicy`, `RemovePolicy`,
   `AddGroupingPolicy`, `UpdatePolicy`, filtered removals, role helpers),
   `GetPolicy`/`GetGroupingPolicy`, `HasPolicy`, enforcement verdicts, and
   RBAC queries must all reflect the new store with no further call.
2. `Enforce` and `EnforceEx` must return the same verdict for the same
   request, and a non-empty `EnforceEx` explanation must be a rule currently
   present in the store whose matcher evaluation is true for the request.
3. `BatchEnforce` must return exactly the verdicts that per-request `Enforce`
   calls would return, in request order.
4. For every user, the set returned by `GetRolesForUser` must be a subset of
   `GetImplicitRolesForUser`, and every rule in `GetPermissionsForUser` must
   also appear in `GetImplicitPermissionsForUser`.
5. A `SavePolicy` followed by `LoadPolicy` must restore exactly the same
   store: same `GetPolicy` rows and same enforcement verdicts. Mutations made
   after a save must vanish after the next `LoadPolicy`.
6. The `g(...)` matcher predicate and the RBAC API must agree: whenever
   enforcement succeeds only through a role link, `GetImplicitRolesForUser`
   must list that role; deleting the link must flip both the verdict and the
   query in the same call.
7. Domain-scoped role links must be invisible to every other domain, through
   the matcher, `GetRolesForUserInDomain`, and `GetUsersForRoleInDomain`
   alike.

## Public Interface

### Import Surface

```go
import (
    "github.com/casbin/casbin/v3"
    "github.com/casbin/casbin/v3/model"
    stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)
```

Exported identifiers on `casbin`: `NewEnforcer`, `Enforcer`.
On `model`: `NewModelFromString`, `Model`.
On `string-adapter`: `NewAdapter`, `Adapter` (with field `Line`).

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `NewEnforcer` | function | Build an enforcer from a model (with optional adapter) or model/policy file paths |
| `Enforcer` | struct | The engine; all methods below |
| `Enforce` | method | Judge one request: `(bool, error)` |
| `EnforceEx` | method | Judge and return the deciding rule: `(bool, []string, error)` |
| `BatchEnforce` | method | Judge a list of requests: `([]bool, error)` |
| `AddPolicy` / `RemovePolicy` / `HasPolicy` | methods | Single policy-rule mutations and membership |
| `AddPolicies` | method | Atomic multi-rule add |
| `UpdatePolicy` | method | Replace one rule |
| `GetPolicy` / `GetFilteredPolicy` / `RemoveFilteredPolicy` | methods | Read or remove rule selections |
| `AddGroupingPolicy` / `RemoveGroupingPolicy` / `HasGroupingPolicy` / `GetGroupingPolicy` | methods | Grouping-rule counterparts |
| `GetAllSubjects` / `GetAllObjects` / `GetAllActions` / `GetAllRoles` | methods | Distinct-value catalogs |
| `GetRolesForUser` / `GetUsersForRole` / `HasRoleForUser` | methods | Direct role queries |
| `AddRoleForUser` / `DeleteRoleForUser` | methods | Direct role link mutations |
| `GetImplicitRolesForUser` / `GetImplicitPermissionsForUser` | methods | Transitive role/permission queries |
| `GetPermissionsForUser` / `AddPermissionForUser` / `HasPermissionForUser` / `DeletePermissionsForUser` | methods | Subject-keyed permission helpers |
| `GetRolesForUserInDomain` / `GetUsersForRoleInDomain` / `DeleteRoleForUserInDomain` | methods | Domain-scoped role queries and removal |
| `LoadPolicy` / `SavePolicy` | methods | Adapter round-trip |
| `model.NewModelFromString` | function | Parse model text |
| `model.Model` | type | Parsed model |
| `stringadapter.NewAdapter` | function | In-memory CSV adapter from text |
| `stringadapter.Adapter` | struct | The adapter; field `Line` holds the text |

### CLI Entry Points

There is no console script for this module. Use is through the Go package
API only.

## Appendix A: Environment

The working environment runs Go 1.21 or newer on Linux. The module under
construction must declare the module path `github.com/casbin/casbin/v3` in
its `go.mod`, with packages at the import paths listed above, so consuming
builds wire it in with a standard `replace` directive. Expression evaluation
and glob matching may use any approach; the module proxy is reachable at
build time for ordinary dependency resolution, but no network access is
available at run time and no external services are required.

## Appendix B: Assessment Notes

Functional coverage is verified by compiled test suites that import the
packages above and exercise the documented public surface only. One suite
checks focused single-behavior contracts (model parsing, matcher operators
and functions, effect folds, single management calls); another checks
multi-step workflows (role graphs across enforcement and introspection,
domain scoping, adapter round-trips, batch atomicity, and agreement among
the four projections). Policy CSV assertions rely only on the rule-per-line
shape stated in Persistence. Error expectations are asserted by message
fragment. Scoring counts each passing test function; partial credit accrues
per test, so a correct subset of behaviors earns its share even when other
areas are incomplete.
