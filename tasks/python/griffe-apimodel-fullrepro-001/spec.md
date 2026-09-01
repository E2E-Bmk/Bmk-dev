# Griffe semantic workspace and publication API

## Scope

This package models Python source as a semantic object graph and carries that
graph through loading, navigation, snapshots, compatibility analysis, extension
effects, and local artifact publication.  Implementations may choose any
internal layout.  The public laws in this document are authoritative.

Only local source trees, local persistence directories, and local Git
repositories are supported.  Network access, package downloads, private Griffe
modules, terminal styling bytes, exact diagnostic prose, and private on-disk
layouts are outside the contract.

## Public modules and names

The following established names are importable from `griffe`:

- graph objects: `Object`, `Module`, `Class`, `Function`, `Attribute`, `Alias`,
  `Parameter`, `Parameters`, `TypeParameter`, `TypeParameters`, `Kind`,
  `ParameterKind`, and `ModulesCollection`;
- analysis: `load`, `GriffeLoader`, `visit`, and `inspect`;
- text and snapshots: `Docstring`, `Parser`, `parse`, `parse_google`,
  `JSONEncoder`, and `json_decoder`;
- compatibility: `find_breaking_changes`, `Breakage`, `BreakageKind`, and
  `ExplanationStyle`;
- extensions and commands: `Extension`, `Extensions`, `load_extensions`,
  `get_parser`, `dump`, `check`, and `main`.

The durable workflow adds these public names:

- `AnalysisWorkspace`, `WorkspaceRevision`;
- `SnapshotStore`, `SnapshotReceipt`;
- `CompatibilityLedger`, `ComparisonReceipt`;
- `ExtensionPipeline`, `EffectReceipt`;
- `ArtifactPublisher`, `PublicationReceipt`;
- `ReceiptClosure`;
- `OwnershipError`, `IntegrityError`, `ConflictError`, `PrerequisiteError`,
  and `RecoveryError`.

Receipt objects are immutable value objects.  They support equality, stable
string identifiers, dictionary projection through `as_dict()`, and restoration
through the corresponding owner's public read or reopen operation.  Dictionary
key order and private storage fields are not fixed.

The durable constructors and principal methods have these public shapes:

- `AnalysisWorkspace(path)`, with `admit`, `open`, `current`, `history`, and
  `recover`;
- `SnapshotStore(path)`, with `prepare`, `promote`, `read`, and `current`;
- `CompatibilityLedger(path)`, with `prepare`, `commit`, `acknowledge`, `read`,
  `pending`, and `replay`;
- `ExtensionPipeline(path, workspace)`, with `run` and `recover`;
- `ArtifactPublisher(path)`, with `prepare`, `promote`, `acknowledge`, `read`,
  `current`, `pending`, and `recover`;
- `ReceiptClosure.verify(receipts)`.

Paths accept strings and `os.PathLike` values.  Owner constructors create their
local state directory when its parent is writable.

The ordinary API keeps its established call shapes.  In particular,
`Module(name, ...)`, `Class(name, ...)`, `Function(name, parameters=..., returns=..., ...)`,
`Attribute(name, value=..., annotation=..., ...)`, `Parameter(name, annotation=...,
kind=..., default=...)`, and `Parameters(*parameters)` construct graph values.
`ParameterKind` exposes `positional_only`, `positional_or_keyword`,
`var_positional`, `keyword_only`, and `var_keyword`; `Parser` exposes at least
`google`, `sphinx`, and `numpy`; compatibility kinds include
`PARAMETER_CHANGED_REQUIRED` for an optional parameter that becomes required.
These are public symbolic values; their private storage representation is not
fixed.

## Semantic graph

`Module`, `Class`, `Function`, `Attribute`, and `Alias` expose their name,
parent, dotted path, canonical path, kind, and kind predicates.  A function has
ordered parameters and return information.  An attribute has annotation and
value.  A class has bases and members.

Inserting a declared object through item assignment or `set_member` establishes
its parent and path.  Deleting a declared member removes it.  Lookup accepts a
name, dotted path, or tuple of path components.  Missing lookup or deletion
raises `KeyError`.

`Parameters` preserves order.  It supports iteration, length, membership,
integer lookup, and name lookup.  Name lookup treats leading `*` and `**` as
syntax rather than part of the parameter name.  Replacing an existing entry
preserves its position; adding a new named entry appends it; adding a duplicate
through `add` raises `ValueError`.

An unresolved `Alias` preserves its import path and target path.  Resolution
may follow a chain to a final target while retaining the import path as the
alias identity and exposing the final definition as the canonical path.  A
missing target and a cyclic target are public resolution failures.  A failed
chain resolution is atomic: it does not leave a resolved prefix.

Inherited members are aliases that retain their inherited import path and final
defining path.  Declared child members override inherited members.  An
unresolved base contributes no fabricated inherited members.

## Analysis

`visit(module_name, filepath, code, ...)` builds a static module graph from
source text.  It retains the supplied path and public line, import, export,
annotation, docstring, and parent relationships.  An explicit `__all__`
defines the ordered exported names.

`load` accepts an import name, a dotted object request, a module file, or a
package directory.  Explicit search paths are considered in caller order.  A
dotted request returns the same logical object reachable from the containing
package graph.  `GriffeLoader` keeps a caller-visible shared collection so
separately loaded packages can resolve cross-package aliases.

Source analysis is static unless inspection is explicitly requested.  A
missing requested import with inspection disabled raises a public loading
failure and does not install a partial requested module in a caller-supplied
collection.  Existing unrelated members are preserved.

Whether a package's submodules are loaded is always an explicit operation
choice in durable workflows.  No workspace law relies on an undocumented
loader default.

## Docstrings and minimal JSON

`Docstring` cleans Python indentation and trailing whole-value whitespace.
An explicit parser and options take precedence over stored configuration.
Direct parsing is fresh; the `.parsed` projection caches its first result.
Parsed sections expose their public semantic kind and elements.  Exact warning
and rendering prose is not fixed.

Objects provide minimal JSON round-trip behavior through their documented
encoding APIs.  Minimal JSON retains facts required for normal navigation,
aliases, callable parameters, annotations, type parameters, docstrings, and
compatibility analysis.  Full JSON may be richer, but its additional private
field set is not a contract.  Invalid or unsupported top-level data never
returns a partially valid graph.

## Compatibility analysis

`find_breaking_changes(old, new)` compares public graphs.  A breakage exposes
the affected object, its kind, public old/new semantic values when applicable,
details, and explanation projections.  Concrete class and `BreakageKind` agree.
The iterable order is not fixed; consumers compare semantic identities or sets.

Public removal, incompatible object-kind change, public attribute-value change,
removed public base, incompatible positional movement or parameter-kind change,
unsatisfied removal, changed default, optional-to-required transition, and a
new required parameter are incompatible.  Private changes are ignored.  The
same semantic breakage set is found after minimal graph round-trip.

Explanation projections preserve the comparison and breakage identity and are
nonempty.  Their exact wording, color, and line formatting are not fixed.

## Extensions

`Extensions` preserves configured instances and dispatches a named hook in
configuration order.  `load_extensions` accepts documented instances, classes,
import names or paths, and one-entry option mappings.  Invalid input raises a
public extension error.

An extension may mutate a graph only through public graph operations.  Its
effects therefore reach navigation, minimal snapshots, compatibility analysis,
and publication.  A failed hook stops later hooks.

The durable `ExtensionPipeline` adds operation identity and rollback.
`run(revision, extensions, *, operation_id=None)` returns the new
`WorkspaceRevision` and its `EffectReceipt`.  Running the same committed effect
operation again is idempotent.  If a hook fails, none of that operation's
effects become part of the committed workspace generation.  A retry starts from
the last committed graph, keeps prior committed operations, and cannot duplicate
an already recorded effect.  Effect receipts identify the workspace generation
and declared public paths affected; they do not expose private hook call stacks.

## Analysis workspace

`AnalysisWorkspace(path)` owns committed analysis generations in a local
directory.  Reopening the same path restores committed state.  Operations on
different workspace paths are independent.

`admit(package, source_path, *, operation_id=None, include_submodules=False)`
normalizes a logical package input, analyzes it, and returns a
`WorkspaceRevision`.  Source identity depends on the logical package identity
and admitted source bytes, not on the absolute checkout directory.  Relocating
byte-identical source preserves source identity; changing admitted bytes creates
a new source identity.

A package generation increases only when a distinct source identity is
committed.  Repeating an already committed operation returns the same logical
revision.  Competing writers for one package cannot both become the same next
generation: one may commit, while the other receives a public ownership or
conflict result and can recover or retry.  A failed admission never replaces
the last readable committed graph.

`open(package_or_revision)` returns a detached semantic graph for the selected
committed revision.  Mutating the returned graph does not mutate committed
workspace state.  `current(package)` returns the current revision receipt.
`history(package)` returns committed revisions in generation order.
`recover()` completes or rolls back interrupted owner state without inventing a
new source analysis.

## Snapshot store

`SnapshotStore(path)` owns canonical graph snapshots separately from workspace
source admission.  Reopening restores prepared and committed snapshot state.

`prepare(workspace_revision, module, *, operation_id=None)` validates that the
graph matches the declared workspace revision and records canonical snapshot
bytes plus an integrity envelope.  Preparation returns a `SnapshotReceipt` but
does not change the package's current snapshot.

`promote(receipt, *, owner_token)` atomically makes the prepared revision
current when the token still owns the package generation.  Repeating promotion
for the same receipt is idempotent.  A stale owner, foreign receipt, corrupt
snapshot, or integrity mismatch fails without changing the last valid current
snapshot.  `read(receipt_or_package)` returns a detached graph reconstructed
through normal public graph APIs.  `current(package)` identifies the current
snapshot receipt.

Snapshot identity is content-based within the declared workspace revision.
Equivalent graphs prepared for the same revision converge; graph or revision
differences do not.

## Compatibility ledger

`CompatibilityLedger(path)` owns durable comparisons separately from snapshot
storage.  `prepare(old_snapshot, new_snapshot, *, operation_id=None)` requires
two valid committed snapshot receipts, computes the public semantic breakage
set, and returns a `ComparisonReceipt`.  Comparison identity binds both ordered
snapshot revisions and an order-independent digest of the breakage set.

Preparation is not committed visibility.  `commit(receipt, *, owner_token)`
makes the comparison available for read and explanation projections.
`acknowledge(receipt)` closes delivery of that comparison.  A committed but
unacknowledged comparison remains pending and recoverable across reopen.
Repeating prepare, commit, or acknowledgement for the same operation is
idempotent.

`read(receipt)` returns detached comparison data; `pending()` lists committed
unacknowledged comparisons; `replay(receipt)` returns the same comparison and
breakage identities.  Replay does not recompute history from mutable source or
current graphs.

## Artifact publication

`ArtifactPublisher(path)` owns visible export files and publication state.  A
publication may contain several package graph artifacts, a compatibility
report, and one combined manifest.  Exact JSON key order and file ordering are
not fixed.

`prepare(inputs, destination, *, operation_id=None, owner_token)` validates the
declared workspace, snapshot, comparison, and effect receipts; stages all
artifacts; and returns a `PublicationReceipt`.  Prepared bytes are not visible
as the destination's current publication.  The receipt binds the complete
content closure rather than only filenames.

`promote(receipt, *, owner_token)` changes all visible artifacts atomically.
Readers see either the prior complete publication or the new complete
publication.  A stale token, altered prerequisite, corrupt stage, or foreign
receipt fails without changing visible bytes.  A promoted publication is
visible even if the process stops before acknowledgement; it remains pending.

`acknowledge(receipt)` closes the publication.  `recover()` resumes the earliest
incomplete phase, preserves already committed identities, and never republishes
an acknowledged operation.  Repeating a successful phase for the same receipt
is idempotent.  `current(destination)` and `pending()` expose public receipts.
`read(receipt_or_destination)` returns a detached mapping of relative artifact
paths to exact published bytes.

## Receipt closure

`ReceiptClosure.verify(receipts)` validates a public prerequisite graph across
workspace, extension, snapshot, comparison, and publication owners.  A valid
closure is acyclic, uses matching package/revision/content identities, and
contains every prerequisite declared by its terminal receipt.  Order of the
input iterable is irrelevant.

Missing, foreign, corrupt, circular, or superseded prerequisites raise
`PrerequisiteError` or `IntegrityError` without writing owner state.  A closure
that is valid before reopen remains valid after each owner is independently
reopened.

## Commands

`dump` exports one or more package graphs and returns zero on complete success
and nonzero on product failure.  `check` compares a current package with a local
Git reference or admitted older path and similarly returns zero for no public
breakage and nonzero for breakage or setup failure.  The old reference path is
owned independently from the current search path.

`main(args)` and `python -m griffe` dispatch the same public operations.
Invalid command syntax has a nonzero public outcome; no particular Python
exception-delivery mechanism is required.  Diagnostic wording is not fixed.

Workspace-aware command routes accept local owner paths and operation identity,
then use the same workspace, snapshot, compatibility, and publication laws as
the library API.  A successful command and an equivalent library workflow yield
the same graph, comparison, artifact content closure, and receipt identities.

## Errors and safety

Ownership and stale-generation failures use `OwnershipError`; malformed or
tampered persisted facts use `IntegrityError`; incompatible concurrent intent
uses `ConflictError`; missing or foreign receipt dependencies use
`PrerequisiteError`; and an interrupted state that cannot be safely completed
or rolled back uses `RecoveryError`.

Product failures are fail-closed.  They do not delete or replace the last valid
committed graph, snapshot, comparison, or visible publication.  Public read
results and receipt dictionaries are detached values; mutating them does not
change owner state.
