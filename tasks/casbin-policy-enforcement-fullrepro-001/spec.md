# Casbin Policy Enforcement Specification

This specification defines a compatible Go implementation of the retained policy-enforcement surface from `github.com/casbin/casbin/v3`. It is intentionally behavioral: internal data structures, evaluator design, role-manager implementation, and file layout are not prescribed.

## Product Overview

The module loads a Casbin model, stores authorization and grouping rules, evaluates access requests, exposes policy-management and RBAC projections, and persists policies through string or file adapters. A conforming implementation must keep enforcement, policy queries, role queries, mutation results, and persisted policy state consistent.

## Non-Goals

Cached, synchronized, contextual, distributed, transactional, watcher, dispatcher, detector, conditional-role, custom-function, custom-role-manager, filtered-adapter, incremental-load, logging, CLI, and HTTP APIs are outside scope. Exact error text, log output, unexported fields, concrete role-manager types, and iteration order where this specification says order is irrelevant are not requirements.

## Representative Workflows

### ACL from model text

1. Build a model with request fields `sub, obj, act`, policy fields `sub, obj, act`, an allow effect, and equality-based matching.
2. Construct an enforcer from that model and no adapter.
3. Add policy rules.
4. Enforce allowed, denied, and malformed requests.
5. Query, update, filter, and remove the same rules.

### RBAC and domains

1. Build an RBAC model whose matcher uses `g`.
2. Add direct and transitive role links and permissions.
3. Compare direct and implicit role and permission projections with enforcement.
4. Repeat with a three-field grouping definition containing a domain.

### Adapter round trip

1. Load rules from a string or policy file into an enforcer.
2. Mutate policy in memory with automatic persistence disabled.
3. Save and load through the same adapter kind.
4. Confirm that enforcement and public policy projections survive the round trip.

## Model Construction and Parsing

`model.NewModel` must return an empty, usable model. `Model.AddDef(sec, key, value)` must add a non-empty definition and return true; an empty value must return false without adding the definition.

The retained sections are request definition `r`, policy definition `p`, role definition `g`, policy effect `e`, and matcher `m`. A model built with `AddDef` must be behaviorally equivalent to a model containing the same definitions parsed by `model.NewModelFromString`.

`NewModelFromString` must parse INI-like model text with the standard section names `[request_definition]`, `[policy_definition]`, `[role_definition]`, `[policy_effect]`, and `[matchers]`. It must reject malformed text and text missing any required request, policy, effect, or matcher section. It must accept omission of the role section when the model does not reference role matching.

Multiple named request, policy, role, effect, and matcher definitions are permitted by suffixing their names, such as `p2` or `m2`; retained named-policy methods operate on the requested policy type.

## Construction and Loading

`casbin.NewEnforcer` must support a `model.Model` alone, a `model.Model` with a compatible adapter, a model-file path alone, and model-file plus policy-file paths. A model-only enforcer begins with no policy. A constructor given an adapter or policy path must load its policy before returning.

If model parsing, model-file reading, policy-file reading, or adapter loading fails, construction must return a non-nil error and no usable enforcer. Unsupported constructor argument counts or retained-type combinations must return an error rather than silently choosing a different interpretation.

`ClearPolicy` must remove authorization and grouping rules from memory. On an enforcer constructed with an adapter, `LoadPolicy` must replace the current in-memory policy with the adapter's current contents and rebuild role links. On an enforcer constructed with a save-capable adapter, `SavePolicy` must replace the adapter's stored representation with the current authorization and grouping rules; an adapter save failure must be returned.

`EnableAutoSave(false)` must make later policy mutations affect memory without invoking incremental adapter mutation. Re-enabling it must make later mutations call the adapter when the adapter supports the requested operation.

## Enforcement

`Enforce` must bind request arguments to the active request definition, evaluate the active matcher for each policy rule, combine matching rule effects using the active policy effect, and return the decision. Too few or too many request values, a matcher evaluation failure, or an incompatible request value must return a non-nil error.

Equality, inequality, ordered comparison, boolean conjunction/disjunction, parentheses, and field selection on map or exported struct values must work in matchers. Boolean conjunction and disjunction must short-circuit. The built-in `keyMatch`, `keyMatch2`, `regexMatch`, and `globMatch` functions must implement their conventional Casbin matcher behavior.

The allow-override effect `some(where (p.eft == allow))` must allow exactly when at least one matching allow rule exists. A model with a policy `eft` field and deny-override effect `!some(where (p.eft == deny))` must deny when any matching deny rule exists and otherwise allow. A priority effect must choose the effect of the matching rule with the smallest numeric priority.

If enforcement is disabled with `EnableEnforce(false)`, every well-formed request must return true without consulting policy. Re-enabling enforcement must restore decisions from the unchanged model and policy.

`EnforceWithMatcher` must evaluate the supplied matcher for that call without replacing the model's stored matcher. A later `Enforce` call must still use the original matcher.

`EnforceEx` must return the same boolean decision as `Enforce`. When allowed by a matching policy rule, it must also return that complete rule; when no rule explains an allow decision, the explanation must be empty. A denied decision must not fabricate an unrelated rule.

`BatchEnforce` must return one decision per input request in input order and must agree with calling `Enforce` separately for each request. If one request is invalid, the call must return an error rather than a truncated successful result.

## Authorization Policy Management

`GetPolicy` is the default-ptype projection of `GetNamedPolicy("p")`. Returned rows must contain complete rules. Mutating the returned outer or inner slices must not mutate stored policy.

`GetFilteredPolicy(fieldIndex, values...)` and the named variant must retain rules whose consecutive fields beginning at a valid `fieldIndex` equal every non-empty filter value. An empty filter value is a wildcard. Callers must supply a non-negative index whose requested filter span fits the retained policy definition.

`HasPolicy`, `AddPolicy`, and `RemovePolicy` must accept either one `[]string` rule or the rule's individual string fields. `HasPolicy` must report exact-row membership.

Adding a missing rule must return true and expose it to queries and enforcement. Adding an existing rule must return false and must not create a duplicate. Removing an existing exact rule must return true and remove it; removing a missing rule must return false without changing other rules.

`AddPolicies` is atomic with respect to stored duplicates: if any input rule already exists in stored policy, it must return false and add none of the input rules. Repeated equal rows within an otherwise new input are retained at most once. `AddPoliciesEx` must add every distinct missing input rule and skip duplicates.

`UpdatePolicy(old, new)` must return true and replace the exact old row when old exists. If old is absent, it must return false and preserve policy.

`RemoveFilteredPolicy` must use the same matching rules as `GetFilteredPolicy`, remove all matches, and return true exactly when at least one row was removed.

Named policy methods must isolate policy types: reading or mutating `p2` must not change `p`, and default methods must continue to address `p`.

## Grouping Policy and RBAC

Grouping-policy query, membership, add, and remove methods must follow the same exact-row and duplicate semantics as their authorization-policy counterparts, using default type `g`.

`GetRolesForUser` and `GetUsersForRole` must return direct links only. `HasRoleForUser` must test direct role membership only and must be false for a relationship reachable only through another role. Result ordering is not prescribed, but results must contain no duplicates.

`AddRoleForUser` and `DeleteRoleForUser` must update grouping policy, role projections, and enforcement as one observable change. They must return true only when the requested relationship changed. `BuildRoleLinks` must rebuild role projections from current grouping rules without changing those rules.

`GetImplicitRolesForUser` must return every reachable role through one or more grouping links, without duplicates. Cyclic role graphs must terminate. A direct-role query must remain direct even when implicit roles exist.

`GetPermissionsForUser` must return only authorization rows whose subject is exactly the supplied user or role. `GetImplicitPermissionsForUser` must additionally include rows assigned to every role reachable from that user. Duplicate permission rows must not be introduced by multiple role paths.

`HasPermissionForUser` tests direct policy membership for the subject plus supplied permission fields. `AddPermissionForUser` and `DeletePermissionForUser` must have the same changed/not-changed boolean semantics as exact policy add and remove.

## Domain RBAC

A domain RBAC model uses a grouping definition with three fields and a matcher that supplies the request domain to `g`. Role links from one domain must not authorize, appear in direct-domain projections, or appear in domain permission projections for another domain.

`AddRoleForUserInDomain` and `DeleteRoleForUserInDomain` must add or remove the exact `(user, role, domain)` grouping rule and return true only when state changed.

`GetRolesForUserInDomain` and `GetUsersForRoleInDomain` must return direct links in the selected domain only. `GetPermissionsForUserInDomain` must include direct user permissions and permissions inherited through roles in that domain, and no permissions from another domain.

`GetAllUsersByDomain` must include each subject associated with that domain by either policy or grouping rules exactly once, and must exclude role names that are only the target of grouping rules. Result ordering is not prescribed.

## String Adapter

`stringadapter.NewAdapter(line)` must retain the supplied policy text in exported field `Line`. `LoadPolicy` must parse non-empty newline-separated CSV policy rows, ignoring blank lines. Loading an empty `Line` must return an error.

`SavePolicy` must replace `Line` with all current authorization and grouping rows in valid CSV form without requiring a terminal newline. Loading the resulting `Line` into an equivalent fresh model must reproduce the same policy sets and enforcement decisions.

The retained string adapter does not incrementally add or filtered-remove rules: `AddPolicy` and `RemoveFilteredPolicy` must return errors. `RemovePolicy` must clear `Line` and return nil.

## File Adapter

`fileadapter.NewAdapter(path)` must bind the adapter to that path. `LoadPolicy` must read newline-separated CSV rows, trimming surrounding whitespace and ignoring blank lines. An empty path or unreadable path must return an error.

`SavePolicy` must create or truncate the target file and write all current authorization and grouping rows in loadable CSV form. Saving and then loading into an equivalent fresh model must reproduce the same policy sets and enforcement decisions.

The retained file adapter does not support incremental mutation: `AddPolicy`, `RemovePolicy`, and `RemoveFilteredPolicy` must return errors and must not rewrite the file.

## State Model

An enforcer's observable state consists of its model definitions, authorization rules by policy type, grouping rules by grouping type, role-link projection, enforcement-enabled flag, auto-save flag, and adapter association. Failed reads or rejected duplicate/no-op mutations must preserve all observable state.

Distinct enforcers created from equivalent model values must not share later policy mutations. Data returned by policy and RBAC queries is caller-owned.

## Error Semantics

All malformed model text, missing required definitions, missing or unreadable files, invalid request arity, invalid matcher evaluation, and unsupported adapter operation cases described above must return non-nil errors. Exact text and concrete error type are not prescribed unless the public catalog exposes a sentinel, and this task exposes none.

Public calls covered by this specification must not panic for malformed model text, missing files, invalid request arity, valid policy filters, duplicate rules, absent rules, empty policy sets, or cyclic roles.

## Cross-View Invariants

- A rule visible through `GetPolicy` must affect `HasPolicy` and enforcement according to the active model.
- After a successful policy mutation, exact membership, filtered projections, enforcement, and later save output must agree.
- After a successful grouping mutation, grouping policy, direct roles, implicit roles, implicit permissions, and enforcement must agree.
- Domain-aware enforcement and all domain projections must agree and remain isolated across domains.
- `ClearPolicy` followed by `LoadPolicy` must restore exactly the adapter's stored rules, not stale in-memory rules.
- A save/load round trip through either retained adapter must preserve policy sets and enforcement decisions, independent of row iteration order.
- A failed mutation, failed adapter operation, or invalid request must not corrupt a later valid enforcement or query.
- Concurrent read-only enforcement calls on one unchanged enforcer must produce the same decisions as sequential calls and must not race through caller-visible state.

## Public Interface

### Import Surface

The required imports and complete retained symbol catalog are defined in `public_api_surface.md`. That file is part of the public packet and is normative for signatures. Extra API is permitted but acceptance tests will not require it.

### API Catalog

The retained catalog covers `casbin.Enforcer`, model construction, core enforcement and management methods, RBAC and domain RBAC methods, and the string and file adapters. No unlisted package is required. Concrete struct fields are implementation-defined except for `stringadapter.Adapter.Line`.


### Normative Symbol Catalog

### Public API Surface — Casbin Policy Enforcement

This task targets module `github.com/casbin/casbin/v3` and package `casbin`, with the two explicitly listed adapter packages. The catalog below is the maximum public surface required by the specification and acceptance checks.

#### Required imports

```go
import (
	casbin "github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
	fileadapter "github.com/casbin/casbin/v3/persist/file-adapter"
	stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)
```

Additional internal packages are permitted. Acceptance tests must not import any path other than the four paths above and Go's standard library.

#### Constructors and model construction

```go
type Enforcer struct { /* implementation-defined */ }

func NewEnforcer(params ...interface{}) (*Enforcer, error)

type Model map[string]model.AssertionMap

func model.NewModel() model.Model
func model.NewModelFromString(text string) (model.Model, error)
func (m model.Model) AddDef(sec, key, value string) bool
```

The catalog intentionally permits `NewEnforcer` only in these forms: no arguments; one `model.Model`; two strings containing a model-file path and policy-file path; and a `model.Model` plus a compatible adapter. Other argument combinations are outside scope.

#### Enforcement and lifecycle

```go
func (e *Enforcer) Enforce(rvals ...interface{}) (bool, error)
func (e *Enforcer) EnforceWithMatcher(matcher string, rvals ...interface{}) (bool, error)
func (e *Enforcer) EnforceEx(rvals ...interface{}) (bool, []string, error)
func (e *Enforcer) BatchEnforce(requests [][]interface{}) ([]bool, error)
func (e *Enforcer) EnableEnforce(enable bool)
func (e *Enforcer) EnableAutoSave(autoSave bool)
func (e *Enforcer) BuildRoleLinks() error
func (e *Enforcer) ClearPolicy()
func (e *Enforcer) LoadPolicy() error
func (e *Enforcer) SavePolicy() error
```

#### Authorization-policy management

```go
func (e *Enforcer) GetPolicy() ([][]string, error)
func (e *Enforcer) GetNamedPolicy(ptype string) ([][]string, error)
func (e *Enforcer) GetFilteredPolicy(fieldIndex int, fieldValues ...string) ([][]string, error)
func (e *Enforcer) GetFilteredNamedPolicy(ptype string, fieldIndex int, fieldValues ...string) ([][]string, error)
func (e *Enforcer) HasPolicy(params ...interface{}) (bool, error)
func (e *Enforcer) HasNamedPolicy(ptype string, params ...interface{}) (bool, error)
func (e *Enforcer) AddPolicy(params ...interface{}) (bool, error)
func (e *Enforcer) AddPolicies(rules [][]string) (bool, error)
func (e *Enforcer) AddPoliciesEx(rules [][]string) (bool, error)
func (e *Enforcer) AddNamedPolicy(ptype string, params ...interface{}) (bool, error)
func (e *Enforcer) RemovePolicy(params ...interface{}) (bool, error)
func (e *Enforcer) RemoveFilteredPolicy(fieldIndex int, fieldValues ...string) (bool, error)
func (e *Enforcer) UpdatePolicy(oldPolicy, newPolicy []string) (bool, error)
```

For variadic rule methods, both `method("a", "b", "c")` and `method([]string{"a", "b", "c"})` are retained call shapes.

#### Grouping policy and RBAC

```go
func (e *Enforcer) GetGroupingPolicy() ([][]string, error)
func (e *Enforcer) HasGroupingPolicy(params ...interface{}) (bool, error)
func (e *Enforcer) AddGroupingPolicy(params ...interface{}) (bool, error)
func (e *Enforcer) RemoveGroupingPolicy(params ...interface{}) (bool, error)

func (e *Enforcer) GetRolesForUser(name string, domain ...string) ([]string, error)
func (e *Enforcer) GetUsersForRole(name string, domain ...string) ([]string, error)
func (e *Enforcer) HasRoleForUser(name, role string, domain ...string) (bool, error)
func (e *Enforcer) AddRoleForUser(user, role string, domain ...string) (bool, error)
func (e *Enforcer) DeleteRoleForUser(user, role string, domain ...string) (bool, error)
func (e *Enforcer) GetImplicitRolesForUser(name string, domain ...string) ([]string, error)

func (e *Enforcer) GetPermissionsForUser(user string, domain ...string) ([][]string, error)
func (e *Enforcer) GetImplicitPermissionsForUser(user string, domain ...string) ([][]string, error)
func (e *Enforcer) HasPermissionForUser(user string, permission ...string) (bool, error)
func (e *Enforcer) AddPermissionForUser(user string, permission ...string) (bool, error)
func (e *Enforcer) DeletePermissionForUser(user string, permission ...string) (bool, error)
```

#### Domain RBAC

```go
func (e *Enforcer) GetUsersForRoleInDomain(name, domain string) []string
func (e *Enforcer) GetRolesForUserInDomain(name, domain string) []string
func (e *Enforcer) GetPermissionsForUserInDomain(user, domain string) [][]string
func (e *Enforcer) AddRoleForUserInDomain(user, role, domain string) (bool, error)
func (e *Enforcer) DeleteRoleForUserInDomain(user, role, domain string) (bool, error)
func (e *Enforcer) GetAllUsersByDomain(domain string) ([]string, error)
```

#### String adapter

```go
type stringadapter.Adapter struct {
	Line string
}

func stringadapter.NewAdapter(line string) *stringadapter.Adapter
func (a *stringadapter.Adapter) LoadPolicy(m model.Model) error
func (a *stringadapter.Adapter) SavePolicy(m model.Model) error
func (a *stringadapter.Adapter) AddPolicy(sec, ptype string, rule []string) error
func (a *stringadapter.Adapter) RemovePolicy(sec, ptype string, rule []string) error
func (a *stringadapter.Adapter) RemoveFilteredPolicy(sec, ptype string, fieldIndex int, fieldValues ...string) error
```

#### File adapter

```go
type fileadapter.Adapter struct { /* implementation-defined */ }

func fileadapter.NewAdapter(filePath string) *fileadapter.Adapter
func (a *fileadapter.Adapter) LoadPolicy(m model.Model) error
func (a *fileadapter.Adapter) SavePolicy(m model.Model) error
func (a *fileadapter.Adapter) AddPolicy(sec, ptype string, rule []string) error
func (a *fileadapter.Adapter) RemovePolicy(sec, ptype string, rule []string) error
func (a *fileadapter.Adapter) RemoveFilteredPolicy(sec, ptype string, fieldIndex int, fieldValues ...string) error
```

#### Explicit exclusions

The task does not require cached, synced, distributed, transactional, contextual, watcher, dispatcher, detector, conditional-role, custom-function, custom role-manager, filtered-adapter, incremental-load, priority-sort, constraint, logging, CLI, or HTTP behavior. It does not require any package that is not listed under Required imports.

Exact error strings, log output, map iteration order, internal assertion layout, concrete role-manager types, and concrete `Enforcer` fields are not observable requirements.

#### Evaluation design notes

- Test behavior only through this catalog.
- Treat policy and role query results as ordered only where the specification explicitly says so; otherwise compare them as sets of rows.
- Use temporary directories for file-adapter workflows.
- Do not access unexported fields, use reflection to recover hidden state, or import the reference implementation through an alternate path.
- No single missing optional branch should prevent unrelated tests from compiling or reporting.


## Appendix A: Environment

The submission must be a Go module with module path `github.com/casbin/casbin/v3`. It must build and test on Linux with the repository's configured Go version. Evaluation is offline; an implementation must vendor, replace, or avoid every non-standard-library dependency needed by its submitted source.

Filesystem tests use fresh temporary directories. Tests do not depend on wall-clock timing, network access, locale, host usernames, or absolute paths.

## Appendix B: Assessment Notes

Acceptance tests exercise only public imports and symbols listed in `public_api_surface.md`. Policy and role results are compared as sets except where this specification explicitly preserves input order. Tests do not inspect private fields, private packages, source layout, exact error strings, or log output.
