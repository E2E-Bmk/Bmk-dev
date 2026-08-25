# Dependency Ruleset Evaluation and Reporting Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## 1. Product Overview

`dependency-cruiser` is a TypeScript library that takes one already-assembled dependency-graph
result and a rule set, extracts the rule violations already recorded on that graph, classifies and
orders them, and renders the outcome. The unit
of input is a single plain-data object — a graph of modules, the dependencies between them, and the
rule set that was in force — and the library never reads a file, opens a socket, resolves a module
from disk, parses source code, or transpiles anything. Every fact it needs is already present in the
object it is handed.

Given that object, the library answers two questions. First, **which rules does the graph violate?**
It walks every module and every dependency, collects the violation records already recorded on each,
classifies each record's type by looking up the matching rule's flags, and produces a de-duplicated,
ordered list
of violation records together with a count of violations at each severity. Second, **how is that
outcome presented?** It offers a family of reporters — a machine-readable serialization, two
human-readable text renderings, and a comma-separated incidence matrix — each of which turns the
same summarised result into an output string and an exit code.

The two questions share one fact source. The violation list computed for the first is exactly the
list every reporter renders for the second, so the machine-readable serialization and the text
renderings never disagree about what was violated.

## 2. Non-Goals

- This specification does not define how a dependency graph is discovered, resolved, or built from a
  filesystem. The input result is supplied whole; nothing in scope walks directories, resolves
  module specifiers, or reads source files.
- This specification does not define parsing or transpilation of any source language. No abstract
  syntax tree is produced or consumed; the graph arrives pre-built.
- This specification does not require network access at install time, build time, or run time.
- This specification does not define a caching layer, an incremental-analysis mode, or any
  persistence of results between calls.
- This specification does not define a command-line interface, argument parsing, or configuration
  file reading. The rule set is delivered inside the input object, not loaded from disk.
- This specification does not define the graph, dot, mermaid, d2, html, teamcity, metrics, anon,
  baseline, text, or flat renderings, nor any plugin-supplied reporter. Only the json, err,
  err-long, and csv reporters are in scope.
- This specification does not define environment or transpiler detection. The environment block is
  carried through from the input unchanged and is never recomputed.

## 3. Representative Workflows

### 3.1 Gate a build on forbidden dependencies

A caller holds a result object describing a project's module graph, whose rule set forbids any
module under `src/` from importing a module under `test/`. The caller invokes the entry point asking
for the `err` rendering. The library reads the two forbidden-edge violations already recorded on the
boundary-crossing dependencies, and returns an object whose `output` is a text block naming each
offending edge under the
rule's name and severity, and whose `exitCode` equals the number of error-severity violations. The
caller's build script forwards that exit code, so a non-zero code stops the build. When the graph
contains no forbidden edge, the text reads that no violations were found and the exit code is zero.

### 3.2 Compare a machine reading against a human reading

A caller wants both a durable record and a console summary of the same outcome. The caller invokes
the entry point twice on the identical input, once asking for `json` and once for `err`. The `json`
call returns the whole result serialized as an indented string with exit code zero; the `err` call
returns the text summary with an exit code equal to the error count. The violation array embedded in
the serialized result lists exactly the same violations, with the same rule names, severities, and
coordinates, that the text summary renders — the two readings are two presentations of one
summarised result.

### 3.3 Read the incidence matrix

A caller wants a spreadsheet-friendly view of which module depends on which. The caller invokes the
entry point asking for `csv`. The library returns a comma-separated incidence matrix — one header
row of quoted module names and one body row per module — with exit code zero, regardless of how many
violations the graph contains.

## 4. Core Concepts and the Shared Data Model

This section fixes the vocabulary and the field-level shapes that every later section refers to. It
is descriptive: it states what the data looks like, and the behavior sections state what is done
with it.

### 4.1 The input result

**Shape.** The input is one object with a `modules` array and a `summary` object. Each entry of
`modules` names a module by its `source` string and lists its `dependencies`; each dependency names
its resolved target (`resolved`), its unresolved specifier (`module`), and its `dependencyTypes`.
The `summary` object carries the rule set that was in force, under `summary.ruleSetUsed`, the
options that were used, under `summary.optionsUsed`, an `environment` block, and severity counts.

**Purity.** The input object is treated as read-only. The entry point returns a fresh result and
must not mutate the object it was given. Given equal input, the entry point returns equal output.

### 4.2 Severity

**The scale.** A severity is exactly one of `"error"`, `"warn"`, `"info"`, or `"ignore"`. For
ordering, `"error"` precedes `"warn"`, which precedes `"info"`, which precedes `"ignore"`. A
violation whose rule severity is `"ignore"` is counted but is never rendered by a text reporter.

### 4.3 The rule set

**Shape.** The rule set under `summary.ruleSetUsed` has up to three arrays — `forbidden`, `allowed`,
and `required` — and one scalar, `allowedSeverity`. A rule has a `name`, a `severity`, an optional
`comment`, and one or both of a `from` restriction and a `to` restriction. A restriction is a set of
match conditions; a module or dependency satisfies a restriction when it satisfies every condition
present in that restriction, and a condition that is absent imposes nothing.

**`from` conditions.** `path` and `pathNot` are regular-expression strings tested against the source
module's path; `path` requires a match and `pathNot` requires the absence of one. `orphan`,
`pathNot`, and the dependents conditions restrict which module a rule applies to.

**`to` conditions.** `path` and `pathNot` are regular-expression strings tested against the target
module's resolved path. `dependencyTypes` and `dependencyTypesNot` are arrays that match when they
intersect (respectively do not intersect) the dependency's own `dependencyTypes`.
`moreThanOneDependencyType` matches when the dependency carries more than one dependency type after
the types that never matter on their own are removed. `circular` matches when the dependency closes
a cycle; `dynamic`, `exoticRequire`, `preCompilationOnly`, and the license conditions test the like-
named dependency attributes. `reachable` and `reaches` express transitive reachability. `moreUnstable`
matches when the target module's instability exceeds the source module's.

**Group back-references.** When a `from.path` regular expression contains capture groups, a `to`
condition string of the form `$1`, `$2`, … is expanded, before matching, to the corresponding group
captured from the source path. A rule therefore expresses that a module depends only on targets in
its own captured folder.

## 5. Violation Extraction and Type Classification

This section states how one module and one dependency contribute violation records. Extraction is the
first of the two projections and produces the violation records the second projection renders. The
rule set is not re-matched here: each module and dependency arrives with its rule outcome already
recorded on the graph, and the entry point reads that recorded outcome. It never re-tests a `path`,
`pathNot`, `dependencyTypes`, or any other `from`/`to` condition to decide what was violated.

**The recorded inputs.** Each dependency carries a `valid` flag and a `rules` array, and each module
carries the same pair. A `rules` entry is a `{ name, severity }` record naming one rule the module or
dependency broke. When `valid` is `true` the module or dependency contributes no violation; when
`valid` is `false` it contributes one violation record for each element of its `rules` array.

**Dependency violations.** For each module, the entry point must walk the dependencies whose `valid`
is `false` and return, for each `rules` entry on such a dependency, one violation record whose
`rule.name` and `rule.severity` are copied verbatim from that `rules` entry, whose `from` is the
owning module's `source`, and whose `to` is the dependency's `resolved` path. The name and severity
are never recomputed from the rule set. A dependency whose `valid` is `false` but whose `rules` array
is empty returns no violation.

**Module violations.** For each module whose `valid` is `false`, the entry point must return one
violation record for each of the module's `rules` entries, whose `rule.name` and `rule.severity` are
copied verbatim from that entry. A module violation that is not reclassified returns `type: "module"`
with `from` and `to` both equal to the module's `source`; a module whose `valid` is `true` returns no
module violation.

**Type classification.** The rule set carried under `summary.ruleSetUsed` is a table indexed by rule
`name`, consulted only to set a violation's `type`. For a dependency violation the entry point looks
up the matching rule by name and must return `type: "cycle"` when that rule's `to.circular` is set
and the dependency records a `cycle`, must return `type: "instability"` when that rule's `to` declares
`moreUnstable` and both the module and the dependency record an `instability`, and otherwise returns
`type: "dependency"`. For a module violation the entry point must return `type: "reachability"` when
the matching rule's `to.reachable` is set and the module records `reaches` entries defined by that
rule, and otherwise returns `type: "module"`. No `from` condition and no other `to` field is
consulted.

**Failure path.** When a `rules` entry names a rule that the rule-set table does not contain, the
entry point returns the violation with its verbatim `rule.name` and `rule.severity` under the default
`type` for its origin (`"dependency"` or `"module"`), because a missing lookup withholds only the
reclassification and raises nothing. When a module or a dependency carries no `rules` entry, it
contributes no violation. Rejection of a structurally invalid input is a schema concern described in
§9.

## 6. Violation Synthesis and Severity Aggregation

This section states the exact shape of each violation record and how the per-severity counts are
derived. The field grammar here is the heart of the contract: a reporter renders these fields
verbatim, so every optional field must appear exactly when — and only when — its condition holds.

### 6.1 The violation record

**Common fields.** Every violation returns a `rule` object of `{ name, severity }`, a `from` string,
and a `to` string. It returns a `type` that is one of `"dependency"`, `"module"`, `"cycle"`,
`"reachability"`, or `"instability"`; when `type` is absent a reader treats it as `"dependency"`.

**Dependency violations.** A violation about a forbidden or not-in-allowed dependency returns
`type: "dependency"`, `from` equal to the source module's `source`, and `to` equal to the
dependency's resolved path. It returns `dependencyTypes` equal to that dependency's dependency-type
array. It returns `unresolvedTo` equal to the dependency's unresolved specifier when — and only
when — that specifier differs from the resolved path (i.e. the dependency did not resolve to a
concrete module); otherwise `unresolvedTo` is absent.

**Cycle violations.** When the matched rule's `to` restriction includes `circular`, the violation
returns `type: "cycle"` and a `cycle` array. Each element of `cycle` is a `{ name, dependencyTypes }`
pair naming one hop of the circular path, in traversal order, ending at the module that closes the
cycle. `cycle` is present only on cycle violations and is absent on every other type.

**Reachability violations.** When a module-scope reachability rule matches, the violation returns
`type: "reachability"`, `from` equal to the module that owns the rule's `from`, `to` equal to the
reached module, and a `via` array of `{ name, dependencyTypes }` hops describing the path from `from`
to `to`. `via` is present only on reachability violations.

**Instability violations.** When the matched rule's `to` restriction includes `moreUnstable`, the
violation returns `type: "instability"` and a `metrics` object of the shape
`{ from: { instability }, to: { instability } }`, where each `instability` is the numeric instability
of the respective module. `metrics` is present only on instability violations.

**Mutual exclusion.** The four optional coordinate carriers are mutually exclusive by type: a
violation returns at most one of `cycle`, `via`, or `metrics`, and returns `unresolvedTo` only on a
dependency violation. A reader that finds `cycle` present must find `type` equal to `"cycle"`, and
likewise for `via`/`"reachability"` and `metrics`/`"instability"`.

### 6.2 De-duplication and ordering

**De-duplication.** Two violations that agree on `type`, `from`, `to`, `rule.name`, and their
coordinate carriers are the same violation; the returned list contains each distinct violation once.

**Ordering.** The returned violation list is sorted deterministically. Violations are ordered first
by ascending severity rank (`"error"` before `"warn"` before `"info"` before `"ignore"`), then by
`rule.name`, then by `from`, then by `to`, then by `unresolvedTo`, then by `type`, then by the joined
`dependencyTypes`, then by the joined `cycle` names, then by the joined `via` names. Given equal
input, the order is identical on every call.

### 6.3 Severity aggregation

**The counts.** The summary returns four integer counts: `error`, `warn`, `info`, and `ignore`. Each
count returns the number of violations whose `rule.severity` equals the like-named severity. The sum
of the four counts equals the length of the violation list. The summary returns `totalCruised` and
`totalDependenciesCruised` carried through from the input, and returns the violation list itself
under `summary.violations`.

**Environment.** The summary returns an `environment` block equal to the input's `summary.environment`.
Re-evaluation never recomputes the environment; the incoming block is carried through unchanged.

## 7. Reporters

This section states the entry point and the four reporter contracts. A reporter takes the summarised
result and returns an object of `{ output, exitCode }`. The entry point selects the reporter by name.

### 7.1 The entry point

**Signature.** `format` is an async function taking the input result as its first, required argument
and an options object as its optional second argument, and returns a promise of an
`{ output, exitCode }` object. The options object carries the reporter name under `outputType`
(defaulting to `"err"`), the rule set consulted for violation-type classification, and optional graph
filters (`includeOnly`,
`focus`, `exclude`, `collapse`).

**Order of operations.** The entry point normalizes the options, asserts the options are valid,
asserts the input result conforms to the result schema, extracts and classifies the violations
already recorded on the graph to produce a fresh summary and violation list, and then hands the
re-summarized result to the reporter named by `outputType`. The reporter's `{ output, exitCode }` object is what the promise
resolves to.

**Unknown reporter.** When `outputType` names a reporter that is not one of the defined names, the entry point raises before any reporter runs: an output type outside the known set is an invalid option, rejected by the same validation that rejects a malformed options object.

**Failure path.** When the options are invalid, or the input result does not conform to the schema,
the entry point raises before any reporter runs, as described in §9.

### 7.2 The json reporter

**Contract.** The `json` reporter returns `output` equal to the entire summarised result serialized
with `JSON.stringify` using a two-space indent, followed by a trailing newline, and returns `exitCode`
zero. The serialized object includes `summary.violations`, the four severity counts, and every module
of the graph. The exit code is zero whether or not violations exist.

### 7.3 The err reporter

**No violations.** When the result contains no violation whose severity is other than `"ignore"`, the
`err` reporter returns `output` equal to a line reading that no dependency violations were found,
naming the number of modules and dependencies cruised, and returns `exitCode` equal to the summary's
`error` count (which is zero in this case).

**With violations.** Otherwise the reporter returns `output` listing each non-ignored violation and
returns `exitCode` equal to the summary's `error` count. Each violation line names the severity, then
the rule name, then the offending coordinates, rendered by type:

- **A dependency violation** renders as `from → to`.
- **A module violation** renders as the module's `from`.
- **A cycle violation** renders as `from → ` followed by the cycle hop names.
- **A reachability violation** renders as `from → to` followed by the via hop names.
- **An instability violation** renders as `from → to` followed by the two instability percentages.

**Summary line.** After the violation lines the reporter returns a summary line stating the total
number of violations, the error and warning counts in parentheses, and the number of modules and
dependencies cruised.

### 7.4 The err-long reporter

**Contract.** The `err-long` reporter renders exactly as `err` does, and additionally appends, under
each violation, the `comment` of the rule that produced it, looked up by rule name in the rule set.
When the matched rule carries no comment, the appended text is a single dash. Its `exitCode` equals
the summary's `error` count.

### 7.5 The csv reporter

**Contract.** The `csv` reporter returns `output` equal to a comma-separated incidence matrix and
returns `exitCode` zero. The first row is an empty quoted cell, then one quoted module `source` per
column, then a trailing empty quoted cell. Each subsequent row is a module's quoted `source`, then
one quoted incidence value per module column, then a trailing empty quoted cell. The exit code is
zero regardless of violation count.

## 8. State Model

The library is stateless across calls. The entry point holds no state between invocations, writes
nothing outside the object it returns, and mutates neither the input result nor the options object.
Two calls with equal input return equal output, and the order of two calls never affects either
result. There is no session, no handle to close, and no ordering requirement between reporters: the order of
reporter requests never matters, and requesting one never changes what another later returns for the
same input.

## 9. Error Semantics

The entry point distinguishes invalid input, which raises, from a graph that merely contains
violations, which does not.

- **Invalid result.** When the input result does not conform to the result schema, the entry point
  raises an error whose message states that the supplied result is not valid and includes the schema
  reason. No reporter runs.
- **Invalid options.** When the options object is not valid — for example, when a filter regular
  expression such as `collapse` is not a safe, well-formed pattern — the entry point raises before
  any violation is extracted.
- **A graph with violations is not an error condition.** Violations are data: they are returned in
  the summary and rendered by the reporter, and only the text reporters' `exitCode` reflects them,
  through the `error` count. The entry point returns normally.
- **Unknown reporter name is not an error condition.** An unrecognized `outputType` returns the
  re-summarized result unchanged with exit code zero rather than raising.

## 10. Cross-View Invariants

**CVI-1 — The text exit code equals the aggregated error count.** For any input, the `err` and
`err-long` reporters return an `exitCode` that equals the summary's `error` count, which equals the
number of returned violations whose `rule.severity` is `"error"`. A build that forwards the exit code
therefore fails exactly when at least one error-severity violation exists.

**CVI-2 — Machine and human readings render one violation list.** For any input, the violation array
the `json` reporter serializes under `summary.violations` is element-for-element equal to the set of
non-ignored violations the `err` reporter renders as lines, matched on `type`, `from`, `to`,
`rule.name`, `rule.severity`, and the coordinate carriers. The two projections must never disagree
about which rules were violated or how.

**CVI-3 — The severity counts partition the violation list.** For any input, `error + warn + info +
ignore` equals the length of `summary.violations`, and each count equals the number of violations at
the like-named severity. No violation is counted twice and none is omitted from the partition.

**CVI-4 — Ordering is a deterministic function of the input.** For any two calls with equal input,
`summary.violations` is returned in an identical order, and therefore the `json` reporter's `output`
string is byte-for-byte identical across the two calls. Ordering follows §6.2 and depends on no
external state.

**CVI-5 — Coordinate carriers are determined by type.** For any returned violation, `cycle` is
present if and only if `type` is `"cycle"`, `via` is present if and only if `type` is
`"reachability"`, `metrics` is present if and only if `type` is `"instability"`, and `unresolvedTo`
is present only when `type` is `"dependency"` and the dependency did not resolve. A reader infers
the type from which carrier is present, and a reporter renders the carrier the type prescribes.

**CVI-6 — The not-in-allowed name has one origin.** For any input, a violation whose `rule.name` is
`"not-in-allowed"` arises only from a dependency matching no `allowed` rule, carries the rule set's
`allowedSeverity` (defaulting to `"warn"`), and never arises from a `forbidden` or `required` rule.
When the rule set declares no `allowed` array, no such violation is ever present.

**CVI-7 — Summarisation preserves the environment and the totals.** For any input, the returned
`summary.environment` equals the input's `summary.environment`, and `totalCruised` and
`totalDependenciesCruised` equal the input's values. Summarisation changes the violation list and the
severity counts; it never recomputes the environment or the module and dependency totals.

## 11. Public Interface

The implementation is delivered as a Node.js package named `dependency-cruiser`. Callers import the
public names below from the package root module and exercise them directly from TypeScript or
JavaScript. The covered workflows require no command-line entry points and no external services, so
this specification defines no console commands.

### 11.1 Import surface

The package root module exports the function `format` and the type names listed in §11.2. Every name
in §11.2 is importable from the package root; no listed name resolves through a deep path. A name not
listed in §11.2 is not part of this contract.

### 11.2 API catalog

| Name | Kind | Role |
| --- | --- | --- |
| `format` | function | Extracts the violations already recorded on the input graph, classifies each violation's `type` against the matching rule's flags, aggregates severity counts, and renders the result with the named reporter; returns a promise of `{ output, exitCode }`. |
| `IReporterOutput` | interface | The reporter return shape: `output` (string or the result object) and numeric `exitCode`. |
| `IFormatOptions` | interface | The options bag: `outputType`, the effective rule set, and the graph filters. |
| `ICruiseResult` | interface | The input fact source: `modules` and `summary`. |
| `ISummary` | interface | Severity counts, the violation list, the carried-through environment, options, totals, and rule set. |
| `IViolation` | interface | One violation record: `rule`, `from`, `to`, `type`, and the type-specific coordinate carriers. |
| `IRuleSummary` | interface | The violated rule's `name` and `severity`. |
| `IMiniDependency` | interface | One hop of a `cycle` or `via` path: `name` and `dependencyTypes`. |
| `IMetricsSummary` | interface | Instability pair `{ from: { instability }, to: { instability } }`. |
| `IModule` | interface | A module node: `source` and its `dependencies`. |
| `IDependency` | interface | A dependency edge: `resolved`, `module`, and `dependencyTypes`. |
| `IFlattenedRuleSet` | interface | The rule set: `forbidden`, `allowed`, `allowedSeverity`, `required`. |
| `IForbiddenRuleType` | interface | A forbidden rule: `name`, `severity`, `comment`, `from`, `to`. |
| `IAllowedRuleType` | interface | An allowed rule: `from`, `to`. |
| `IRequiredRuleType` | interface | A required rule: `name`, `severity`, `comment`, `from`, `to`. |
| `IFromRestriction` | interface | The `from` match conditions of a rule. |
| `IToRestriction` | interface | The `to` match conditions of a rule. |
| `SeverityType` | type | `"error" \| "warn" \| "info" \| "ignore"`. |
| `ViolationType` | type | `"dependency" \| "module" \| "cycle" \| "reachability" \| "instability"`. |
| `DependencyType` | type | The union of dependency-kind tags a dependency carries. |
| `OutputType` | type | The union of reporter names, including `"json"`, `"err"`, `"err-long"`, and `"csv"`. |

## Appendix A: Environment

**Runtime.** Node.js 22. The implementation must run on that version without a transpilation step
performed by the consumer.

**Third-party runtime dependencies.** There are none. Every behavior in this specification is
expressible with the Node.js standard library alone. The input result is plain data; violation extraction is object traversal and rule-name lookup; the
reporters are string assembly and
`JSON.stringify`. No runtime package is required or permitted on the delivery surface.

**Network.** There is no network access at any point. Nothing is fetched at install time, at build
time, or at run time.

**How the package is consumed — read this twice.** The consuming code is an **ES module**: its
`package.json` declares `"type": "module"`, and it reaches this package with
`import { format } from 'dependency-cruiser'`. Three requirements follow, and each of them has
independently broken an otherwise-correct implementation.

1. **The package must be importable by name from an ES module.** After `npm install` is run from the
   package directory, `import { format } from 'dependency-cruiser'` executed by an ES module must
   resolve and load. Verify that, not `require.resolve`. Under ESM resolution an `exports` map
   **replaces** `main` rather than supplementing it: if `package.json` declares
   `"exports": { ".": { ... } }` and that entry has no `import` condition and no `default` condition,
   the specifier is unresolvable from an ES module no matter what `main` says — while
   `require.resolve` still succeeds. That combination passes a require-based smoke test and fails
   every ESM test file at load time. Declare an `exports` map that includes an `import` (or
   `default`) condition pointing at a file that exists.
2. **The package must ship runnable JavaScript.** If the sources are TypeScript, the package must
   publish compiled output; an `exports`/`main` entry that points at a `.ts` file cannot be loaded.
   Nothing runs a build step on the consumer's behalf between install and import, so a `tsc`
   invocation the author did not arrange will not happen.
3. **The declared entry file must exist after installation.** Whatever `main`, `module`, `exports`,
   or `types` points at must be a real file in the installed tree, not a path that only exists in the
   working copy before packing.

**Input schema.** The entry point validates its first argument against the full cruise-result schema
before any reporter runs, and raises with a message stating the result is not valid when a required
member is missing (the raise is the invalid-result path of §9). Every entry of
`modules[].dependencies` must carry `coreModule`, `exoticallyRequired`, `followable`,
`couldNotResolve`, `circular`, `moduleSystem`, `dynamic`, `dependencyTypes`, `resolved`, `module`,
and `valid`; a dependency missing any of these is rejected. `matchesDoNotFollow` is an optional
dependency member and is not required. `summary.optionsUsed` admits no member the schema does not
list, and a result carrying an unlisted `optionsUsed` member is rejected. A fixture supplied to the
entry point must therefore be schema-valid in full.

**Type declarations.** Consumers written in TypeScript type-check against the package. Declaration
files must accompany the JavaScript and must describe exactly the surface of §11.2, with the
parameter order, arity, types, and optionality stated in §7.1.

**Test tooling.** The environment's test runner is Vitest 2.x. Do not rely on any API introduced in
Vitest 3, and do not pin a Vitest version in the package's own manifest that conflicts with the one
already installed in the environment.

## Appendix B: Assessment Notes

Assertions prefer the machine-readable half of every result. For the summarisation projection, that
means the `type` value, the `from` and `to` strings, the `rule.name` and `rule.severity`, whether
each coordinate carrier (`unresolvedTo`, `cycle`, `via`, `metrics`) is present, and the four severity
counts. For the reporters, that means the exact `exitCode` and the presence of the summary line's
numbers, rather than the precise colour codes or icon glyphs a terminal renderer adds. Exact
console styling is presentation, not contract; the numbers and the structure are the contract.

## Appendix C: Terminology

- **Result** — the single plain-data input object of `modules` and `summary`.
- **Rule set** — the `forbidden`, `allowed`, and `required` rule arrays plus `allowedSeverity`,
  carried in `summary.ruleSetUsed`.
- **Restriction** — the `from` or `to` set of match conditions on a rule.
- **Violation** — one record naming a rule that a module or dependency broke, with its coordinates.
- **Coordinate carrier** — one of the type-specific optional fields `unresolvedTo`, `cycle`, `via`,
  or `metrics`.
- **Reporter** — a function turning the summarised result into `{ output, exitCode }`.
- **Instability** — the numeric measure a `moreUnstable` rule compares between two modules.
