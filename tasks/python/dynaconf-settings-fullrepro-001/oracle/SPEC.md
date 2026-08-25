# Dynaconf durable settings and publication behavioral specification

## Authority and product boundary

This document defines observable behavior of an installable Python distribution
and package named `dynaconf`, including its installed `dynaconf` console
command. The supported boundary is a local settings engine: settings objects,
TOML/JSON/Python files, process environment values, named environments,
conversion, validation, public mutation, fresh values, post-load hooks, history
and inspection, durable ownership, source lineage, acknowledged artifact
publication, and the local console workflows described here.

Internal layout, storage, parsers, caches, registries, normalization stages,
and algorithms are implementation choices. Behavior outside this document is
not required, and no requirement depends on private imports or attributes.

## Public surface and terminology

The package exposes the ordinary settings surface below, plus the durable
resource classes documented later in this specification:

```python
from dynaconf import (
    Dynaconf,
    LazySettings,
    settings,
    Validator,
    ValidationError,
    add_converter,
    post_hook,
    inspect_settings,
    get_history,
    SettingsSnapshot,
    PublicationReceipt,
    ArtifactPublisher,
    PublicationCoordinator,
    ProtocolReceipt,
    PublicationConflict,
    StaleLineageError,
)
```

`Dynaconf` and `LazySettings` are the same constructible class. `settings` is
an instance of it. `Validator`, `SettingsSnapshot`, `PublicationReceipt`, and
`ArtifactPublisher`, `PublicationCoordinator`, and `ProtocolReceipt` are
classes; `ValidationError`, `PublicationConflict`, and `StaleLineageError` are
exception classes; and the other helpers are callable. Installed metadata reports version
`3.3.0.dev0` and one non-empty console entry named `dynaconf`.

A **user value** is a setting rather than an engine option such as a name
ending in `_FOR_DYNACONF`. An **active environment** is the value reported by
`current_env`. A **source contribution** is a public history item with at least
a loader classification and value. A **derived view** is returned by
`from_env`. Structured observations compare Python values or parsed JSON, not
incidental mapping order, formatting, colors, banners, or warning text.

Settings objects are used through construction, attribute/item/callable
access, `get`, `set`, `update`, `as_dict`, `load_file`, `setenv`, `using_env`,
`from_env`, `current_env`, `snapshot`, `transaction`, `bind_file`,
`reload_generation`, `run_hooks`, `publish_artifacts`, `validators`, configured
fresh-value behavior, `get_history`, and `inspect_settings`.

A successful lifecycle or publication operation returns a
`PublicationReceipt`. It exposes a committed generation, a Boolean `committed`
result, and the public resource names covered by that operation. The resource
collection describes semantic ownership and does not prescribe temporary
filenames or internal staging layout.

## Owned generations and snapshots

`snapshot()` returns a `SettingsSnapshot` for the receiving object's current
committed generation. A snapshot exposes `current_env`, `generation`, a
non-empty identity, `get`, and `as_dict`. Its value graph is independent: later
writes, reloads, environment changes, dependent-file changes, or sibling
operations cannot rewrite it through shared mutable objects. Snapshot identity
distinguishes successive snapshots owned by one settings object; its spelling
and process-global uniqueness are not prescribed.

`transaction(validate=True)` is a context manager for one settings owner.
Operations in the body may read the staged view. Normal exit validates the
complete staged generation when requested and publishes it once. A body,
default, cast, or validation exception restores values, environment, source
contributions, inspection, and history to the generation at entry and
preserves the original exception. Successful exit advances the owner's
committed generation once; failed publication does not.

These objects are not a global transaction service. They own local settings
state and do not coordinate remote stores or unrelated settings instances.

## Core settings and projections

Independently constructed settings objects own their runtime user state. A
write to one does not appear in another merely because both exist in the same
process, and unrelated objects do not use module-level `settings` as a hidden
write channel.

Top-level names are case-insensitive in ordinary attribute and item access.
Nested mappings support dotted lookup. If a nested path and a literal key
containing a dot both exist, `dotted_lookup=True` selects the path and
`dotted_lookup=False` selects the literal key. Callable access and `get` use
the same value semantics; `get` returns its supplied default for an absent
name. A controlled absent attribute raises `AttributeError`.

`set` and `update` create or replace public values. Dotted mutation addresses
the named nested path without deleting unrelated siblings unless the caller
replaces their containing branch. `as_dict()` reflects the same current user
state as other public access forms and omits engine configuration keys. Once a
write has been published, public projections describe the same current value,
including when later validation reports that it is invalid. Exact nested-key
letter case in raw dictionary output is not prescribed where case-insensitive
public access agrees.

## File sources, optional discovery, and source order

TOML, JSON, and Python settings files contribute structured values. JSON
objects and arrays preserve their decoded structure. Python files export
uppercase settings names and do not turn lowercase helpers or imports into
user values.

Ordered settings-file sequences apply in supplied order. Comma and semicolon
sequence spellings preserve that order. Earlier unique values remain; later
scalar contributions win collisions unless an explicit merge rule applies.

Source stages relate as follows:

- constructor `preload` precedes regular `settings_files`;
- an adjacent local companion for a named regular file follows the base file;
- relative `dynaconf_include` resolves from its declaring settings directory
  and contributes after that file when a path matches;
- constructor `includes` follow regular file processing; and
- selected process-environment contributions override ordinary file values for
  the same final name.

Unique successful contributions remain visible, and public history reports
semantic contributions that participated rather than synthesizing a list only
from the final value.

File selection may use optional filenames or glob-like declarations. A
declaration that matches no file is ignored and does not prevent the declaring
source from loading, even when general silent-error handling is disabled. If a
path matches a malformed source and non-silent loading is requested, the
format's parsing exception propagates. Correcting that matched source permits a
later construction to load it normally without rewriting the declaring file or
restarting the process.

Construction and explicit loading are scoped to the receiving object. File
creation, rewrite, or removal does not silently mutate unrelated objects. An
existing object keeps established state until a documented fresh access,
explicit `load_file`, environment switch, or other public reload action.
Failure in one construction does not poison a healthy sibling.

`load_file(path=...)` applies successfully read values to the receiving object
without discarding unrelated runtime state. With environment selection disabled
for that call, top-level values remain top-level and named environment sections
remain structured mappings. Successfully published file values have public
source contributions. A non-silent matched parsing failure propagates and does
not make the object permanently unusable. Previously accepted state remains
under ordinary public semantics, and a corrected explicit load may be retried.
The complete supplied path declaration is one publication attempt. Success
returns a committed receipt for the declaration. If any matched source fails,
values from earlier members of that attempt are not published; an unmatched
optional declaration may still return a successful empty publication receipt.

## Named environments and derived views

With separated environments enabled, the selected environment is layered over
`default`, and `global` values are available. Unique applicable values remain,
the selected environment wins collisions, and values belonging only to an
unselected environment do not leak. An ordered environment sequence applies in
listed order, with later members winning collisions.

`setenv(name)` persistently changes the receiving object's active environment.
A single entered `using_env(name)` context selects that environment and returns
to the environment active at entry after normal or exceptional exit. Nested
`using_env` contexts form an owned last-in-first-out stack. After persistent
selection A, outer selection B, and inner selection C, the inner exit exposes B
and the later outer exit restores A, including when either body raises. A scope
belongs to the receiving settings object and the execution context that entered
it: another settings instance or thread cannot observe, pop, or overwrite that
scope. An explicit `setenv` made inside a scope changes that scope's selected
environment but does not erase the exact view saved for outer restoration.
Independently constructed older or newer siblings keep their own active
environments and values throughout this lifecycle.

Entering `using_env` returns the receiving settings owner as the lease value,
so operations through the lease and through the original reference address the
same scoped owner.

`from_env(name)` returns an independently usable view without changing the
parent's active environment. Ordinary derivation follows named/default
layering. With `keep=True`, the named environment overlays the current view so
current-only values remain and the named environment wins collisions. Runtime
writes and validator registrations subsequently made on one derived view do
not write into its parent or an independently derived sibling. Related objects
follow documented snapshot/reload behavior rather than sharing one mutable
user dictionary.

## Process-environment policy and casting

`envvar_prefix` selects process names. A comma-separated prefix list accepts
each named prefix and ignores similar unlisted prefixes.
`envvar_prefix=False` permits controlled unprefixed names. With
`ignore_unknown_envvars=True`, a prefixed name is accepted only when its
settings name is already known from ordinary state; a rewritten source may
make it known to a newly loaded object without retroactively changing an old
object.

When present, `ENVVAR_PREFIX_FOR_DYNACONF` is the effective prefix selector for
a new construction, including a construction that also supplies
`envvar_prefix`. After that controlled process selector is removed, a newly
constructed object again uses its constructor prefix, or the ordinary default
when the constructor omits one. Existing objects keep values and selection
already established; cleanup does not retroactively rewrite them.

With `sysenv_fallback=True`, `get` may obtain an otherwise absent name from an
unprefixed process value. With a list, only named fallbacks are eligible. A
normal stored setting wins over the same fallback name. Fallback does not
bulk-load all process names as stored settings.

Ordinary environment scalar text follows natural scalar parsing.
`auto_cast=False` prevents explicit converter-marker interpretation in
environment values, leaving marker text literal; it does not require ordinary
numeric text to become a string. Casting policy is object-scoped and never
modifies process-environment bytes.

Environment nested keys and merge controls compose with file values.
Dictionary merge preserves unrelated and deeper leaves; list insertion retains
existing members around the inserted value; nested deletion removes only its
leaf. Control markers do not become user data. Attribute, dotted, dictionary,
history, and inspection projections describe the same current result.

## Converters, aliases, and dependent values

Built-in tokens support integer, float, Boolean, JSON, null, literal string,
and documented string transformations: upper, lower, title, capitalize, strip
variants, split, casefold, and swapcase. Public values expose the converted
Python value and type rather than parser markers.

`add_converter` registers a uniquely named callable converter. Composed
operations evaluate inner public operations before the outer callable, and the
callable's returned type is preserved. No internal registry form is prescribed.

`@get NAME` obtains another current public value without changing its type. A
missing alias may use its fallback, and a composed cast applies to that
fallback. Alias and source remain independently readable.

`@read_file` reads UTF-8 text from its absolute or settings-directory relative
path when evaluated. Without a fallback, a missing dependency raises
`FileNotFoundError`; exact text is unconstrained. Present -> missing -> restored
therefore produces value -> exception -> new value when reevaluated rather than
a permanent positive or negative cache. Unrelated state and independently
constructed siblings remain usable. A sibling's dependent value follows its
own public evaluation and may observe current dependency bytes when accessed.

`bind_file(name, path, converter=None, fallback=...)` establishes an owned live
dependency for a public setting name. Each public access reads the dependency's
current UTF-8 bytes and applies the optional callable converter. A missing path
raises `FileNotFoundError` unless the binding supplies a fallback. Bindings are
object-scoped; failure or fallback does not poison later access, and restoring
the path is sufficient for a later access to observe its new bytes.

## Validation publication and correction

`Validator` supports required/must-exist and prohibited-existence rules, type,
equality/order, membership/containment, prefix/suffix, and length relations.
Clear satisfying values validate; violations raise `ValidationError`. A
callable condition receives the current value. A `when=Validator(...)` guard
is reevaluated against current settings: nonmatch suppresses its rule and match
activates it.

Validator objects combined with `|` succeed when either constituent succeeds;
objects combined with `&` succeed only when both do. Composition is reevaluated
from current state rather than retaining a prior outcome.

A static default supplies a missing value. A present non-`None` value remains.
Present `None` receives the default only under `apply_default_on_none`. A
callable default receives current settings and its validator, may read the
active environment, and is evaluated during validation rather than
registration. Its result belongs to that settings context, not a process cache.

Validator casts receive the current value and run in registration order within
one validation transaction. Defaults, casts, and all validated keys are staged
against one coherent settings view. If every applicable rule succeeds, all
staged values become visible together. If any rule, default, or cast raises,
the complete public state, history, derived projections, and active environment
are restored to their pre-validation generation. The object and healthy
siblings remain usable, and corrected input or callable behavior may be retried.

`validators.validate()` reports a current violation with `ValidationError`.
`validate_all()` evaluates independently invalid names and exposes public
`details` for current violations. Revalidation replaces the current error set:
correcting one value removes its obsolete detail; correcting all permits
success. Results are not an append-only error cache.

With update validation enabled, mutation and validation form one publication
boundary. `set` and `update` stage the complete attempted change, including
dotted siblings, defaults, and casts. Success publishes the whole validated
generation. Failure publishes none of it and restores values, history,
inspection, and derived views exactly to their prior public generation. No
caller can observe a mixture of old values and an earlier successful prefix of
the failed update.

A later corrected mutation may succeed on the same object and becomes current.
History records committed generations rather than staged invalid values.
Failure does not contaminate another object.

Dotted validated writes follow the same stage-validate-commit rule while
unrelated nested siblings remain under normal mutation semantics. Validator
collections belong to settings-object ownership: a derived view may inherit
applicable rules, but later registration/evaluation in one view does not
silently mutate unrelated sibling values or outcomes.

The explicit `transaction` context is the public composition boundary for
multi-operation publication. It is also valid for callers that disable
per-operation validation and request one validation on context exit.

## Fresh values and recovery

A name in `fresh_vars` reloads from configured sources when publicly accessed.
Rewriting a valid source changes the next access without reconstructing the
object. A malformed non-silent fresh reload propagates its parsing exception,
does not publish any portion of the attempted generation and leaves every
previously accepted value, source contribution, active environment, and runtime
write visible as before. Correcting the source is sufficient for the next fresh
access to build and publish a new generation; no explicit cache reset,
reconstruction, or process restart is required.

Source parsing, validation, converter, or hook failure does not install a
process-wide negative cache, mutate unrelated siblings, or require restart.
Failed parsing, validation, conversion, or hook execution never installs a
partially fresh public generation. Recovery retries from the last complete
generation plus current source bytes.

`reload_generation(env=None, silent=...)` executes a full reload as one owned
generation and returns its publication receipt. A parsing, conversion,
validation, or hook exception restores the prior complete generation. Corrected
inputs permit the same settings owner to retry without reconstruction. Reload
does not rewrite an older `SettingsSnapshot` or an unrelated object.

## Post-load hooks, merge policy, and cleanup

Post-load hooks run after applicable sources are available. Supported public
forms are constructor `post_hooks`, a settings-directory
`dynaconf_hooks.py` with `post(settings)`, and a Python settings function
decorated with `post_hook`. Hooks receive current public settings and return
mappings applied to that view.

When all three forms apply, settings-directory discovery contributes before
constructor hooks, and decorated Python-settings hooks contribute after them.
Each hook sees the staged state produced by preceding applicable sources and hooks.
Ordered entries within the constructor hook collection preserve their order.

A plain nested mapping returned by a hook replaces its target branch under
ordinary replacement semantics. To preserve unrelated existing siblings while
adding nested values, the returned mapping uses the public `dynaconf_merge`
marker in that branch or at the result level. The marker requests merge and
does not remain as user data. Thus replacement and marked merge are distinct
public behaviors rather than an unconditional hook merge.

Different settings directories may contain identically named discovered hook
modules with different behavior. Constructing from one directory does not
force another to reuse the first behavior, and returning to the first yields
its behavior again.

A complete applicable hook sequence has one commit boundary. Each hook sees the
staged values returned by preceding hooks in deterministic documented order,
but callers see those values only after all hooks succeed. A hook exception
propagates through construction/load, restores the receiving object's complete
pre-hook generation, and preserves that original exception even if cleanup also
fails. Temporary cwd, imports, execution state, staged mappings, and resources
are cleaned after success and failure. A healthy object remains usable, and a
corrected later run may succeed without stale hook or negative-cache state. No
requirement depends on private import-cache entries.

`run_hooks(hooks)` applies an explicitly supplied iterable of public hook
callables as one pipeline transaction. Each callable receives the staged
settings owner and may return a mapping for the next callable. Success returns
a committed receipt. A late exception restores all earlier pipeline mappings,
preserves the original exception, and permits a corrected later pipeline.

## History and inspection consistency

`get_history(settings_object, key=...)` reports public contributions for the
current value, including applicable file, process-environment, and runtime-set
operations. Loader classifications distinguish semantic source kinds. Exact
private filenames, caller frames, internal record order, and undocumented
fields are unconstrained.

`inspect_settings(settings_object, key=...)` reports the same current value and
compatible history. With JSON dumping and `to_file`, it returns a report and
writes UTF-8 JSON. Parsed written output agrees with the returned report for
the controlled current value and semantic contributions.

Inspection reports include the current committed `generation` and a Boolean
`committed` status. Public history items for the report identify the same
generation and committed status. Exact private sequence numbers, internal
journal entries, and uncommitted staging observations remain outside scope.

History and inspection reflect only committed writes. When validation raises,
they remain aligned with the restored prior generation. When file, environment,
runtime mutation, and reload contribute successfully in sequence, all public
projections agree on the final current value and applicable contributions.

## Installed console and generated artifacts

The installed command starts without ambient settings for general help and
semantic version reporting. A configured object may be selected by an
importable `module.settings` path. For the same object, `get`, explicit
environment selection, JSON `list`, and JSON inspection agree with library
value/history/inspection semantics. Each command is a fresh process; an
environment selected in one command is not sticky in the next.

The `init` workflow supports JSON settings and secrets artifacts from public
variables/secrets input. Confirmed success stages the complete `settings.json`,
`.secrets.json`, and suitable secrets ignore entry, then atomically replaces the
destination generation. Library and configured console access agree on the new
values only after complete publication. A refusal or failure at any stage
leaves every pre-existing artifact byte-for-byte unchanged and exposes no
temporary file as a public artifact.

JSON inspection and other public `to_file` exports use the same staging rule:
the returned report and final UTF-8 file describe one complete settings
generation, secret values remain excluded wherever the public command promises
redaction, and render or replacement failure preserves the prior destination.
A corrected fresh destination is not served stale values. Decorative output and
prompt wording are unconstrained.

`ArtifactPublisher` provides the same staging law to library callers.
`publish(destination, settings, secrets, before_commit=None)` owns the related
`settings.json`, `.secrets.json`, and secrets-ignore entry as one bundle.
`publish_report(destination, report, before_commit=None)` owns one UTF-8 JSON
report. `settings.publish_artifacts` is the settings-bound form of bundle
publication. A supplied pre-commit callback observes staged resources and may
abort publication by raising. On any pre-commit, render, or replace failure,
every previously public byte remains unchanged and staging resources are
retired. Success returns a committed publication receipt.

## Durable settings ownership

`DurableSettingsStore(directory)` owns a persistent configuration generation
in a caller-supplied directory. A new store begins at generation zero with an
empty value mapping. `snapshot()` returns an owned JSON-compatible projection
containing the current generation, values, and fencing generation; mutating
that projection never writes through to the store.

`claim(owner, adopt_stale=False)` obtains the exclusive writer lease and
returns a lease object with an immutable `receipt`. A receipt identifies its
owner, opaque token, monotonically increasing fence, current configuration
generation, and whether it adopted a stale owner. A live owner prevents a
second claim, including from another store object. A process that terminates
without releasing leaves a stale lease: it is never adopted implicitly, but a
caller may request explicit adoption. Adoption retains committed values and
generation while advancing the fence. Releasing a valid lease permits a new
claim, which also advances the fence.

`lease.commit(values, expected_generation=None)` atomically replaces the
complete JSON-compatible mapping and advances the configuration generation
once. The returned immutable receipt carries the lease token, fence,
generation, and canonical payload digest. If an expected generation is
supplied it acts as compare-and-set: mismatch publishes nothing. A released,
replaced, or pre-adoption token is fenced and cannot commit. These failures
raise `OwnershipError` or `StaleFenceError` as appropriate and preserve the
last committed state.

The store is process durable. A fresh store object or fresh Python process
opening the same directory observes committed values, generation, and fence.
Lease metadata is ownership state, not configuration data.

## Append-only source lineage and watching

`LineageJournal(path)` owns an append-only UTF-8 event history. `append`
records a source identity and operation with an optional JSON-compatible
payload and accepted flag. Events receive gap-free, monotonically increasing
sequence numbers and expose source, operation, canonical payload digest, and
acceptance. Reopening the journal preserves its bytes and continues the
sequence. `cursor` is the latest sequence and `changes(after)` returns only
later events in order.

`project()` materializes the most recent accepted facts per source. Accepted
upserts replace that source's fact and accepted deletes remove it. Rejected
observations remain visible in lineage but never erase or replace the last
good projection.

`SourceWatcher(journal, sources)` watches caller-supplied local JSON resources.
`poll()` observes each resource independently and appends an upsert, delete, or
rejection when its bytes or existence state changes. Repeated polling of
unchanged state emits nothing. Invalid UTF-8 or malformed JSON is a rejected
revision; correcting the same resource later produces a normal accepted
revision. Delete and recreate are distinct lifecycle events. Multiple source
identities never overwrite one another's lineage.

## Acknowledged artifact transport

`ArtifactTransport(outbox_directory, sink_directory)` implements a durable
local outbox. `stage(key, payload, generation=...)` serializes a
JSON-compatible payload canonically, returns an immutable delivery receipt,
and records a pending delivery. The token is stable for the same key,
generation, and payload. Keys may name nested paths under the sink.

Publication has three explicit phases. `deliver(token)` atomically places the
payload at its sink key but keeps the outbox item pending. `ack(token)` is
allowed only after delivery and retires the pending item as acknowledged.
Acknowledgement is idempotent, including after the transport is reopened.
`rollback(token)` is allowed only while pending; it restores the bytes that
preceded this delivery, or removes a newly created target. An acknowledged
delivery cannot roll back. Unknown tokens and invalid transitions raise
`ProtocolError` without changing artifacts.

`pending()` returns pending tokens in deterministic order. A fresh transport
object recovers pending items, may deliver or roll them back, and never
mistakes bytes at the sink for an acknowledgement. Different artifact keys
have independent acknowledgement and rollback lifecycles.

## Cross-resource workflows

These owners compose without collapsing their transaction boundaries. A
watcher projection may be committed under a fenced durable lease. A committed
store snapshot may then be staged and acknowledged as an artifact whose
generation agrees with the store receipt. A process restart may independently
reopen journal, store, and transport and resume from their public cursors,
generations, and pending set.

A failure in one owner does not silently rewrite another. Rejected source
bytes preserve the last good projection, a stale writer cannot replace the
store, and an unacknowledged artifact may roll back without being mistaken for
an accepted publication. Recovery is explicit at each boundary.

## Recoverable cross-owner publication

`PublicationCoordinator(protocol_directory, *, store_root, lineage_path,
outbox_root, sink_root)` joins four caller-owned durable resources without
collapsing them into one in-memory transaction. Its protocol directory contains
the durable transaction and recovery ledger; reopening the coordinator, or
opening it in another Python process, reconstructs every public phase.

`prepare(owner, *, source_cursor, expected_generation, values, key,
idempotency_key)` creates one fenced prepared publication. Preparation requires
the supplied lineage cursor and store generation to still be current, changes
neither the store nor sink, and returns an immutable `ProtocolReceipt`. The
receipt exposes an opaque token, owner, increasing fence, source cursor, base
and resulting generations, artifact key, state, and canonical value digest.
Repeating the same active request is idempotent. A different active publisher,
changed payload under the request identity, stale cursor, or changed generation
raises `PublicationConflict` or `StaleLineageError` without partial visibility.

`commit(token)` rechecks both prepared boundaries, advances the store by one
tentative generation, and durably stages its complete snapshot in the outbox.
`deliver(token)` makes that snapshot visible at the sink but leaves it pending.
`acknowledge(token)` accepts only a delivered artifact whose generation and
canonical values still match preparation, then durably acknowledges it and
retires protocol ownership. Repeating an already completed phase is idempotent;
skipping a phase is an error.

`recover(token, owner=...)` may reopen a prepared, committed, or delivered
publication. Recovery advances the fence and permanently retires the earlier
publisher. A prepared publication is retired without visibility. A committed
or delivered but unacknowledged publication restores preceding artifact bytes
and writes a new compensating store generation containing preceding values.
Accepted generations and protocol-ledger entries are never deleted or
renumbered. Recovery is idempotent; acknowledgement remains final.

`status(token)` reports durable phase state and `events(after=0)` returns the
append-only protocol events after the supplied offset. Duplicate delivery or
acknowledgement does not append another transition. `reconcile(owner, *, key,
idempotency_key)` publishes the current materialized lineage from the current
store generation through every phase, converging temporarily divergent views
without rewriting accepted source history.

Correct workflows remain valid when prepare, commit, delivery,
acknowledgement, recovery, and reconciliation are performed in fresh processes.
Concurrent publishers, stale watcher cursors, duplicate delivery, publisher
replacement, and post-commit/pre-ack crashes resolve from durable receipts and
fences rather than hidden coordinator memory.

## Isolation, encoding, and implementation freedom

Controlled local inputs yield deterministic public results. Temporary cwd,
process-environment edits, imported settings/hook modules, converter names, and
files are scoped and restored after normal and exceptional exits. Returning to
an earlier settings state by explicit public selection after an intervening
state yields its public behavior rather than leaked middle-state behavior.

Text written by described workflows is valid UTF-8 where textual. Exact path
spelling, dictionary order, wrapping, colors, decorative Unicode, warnings,
and exception messages are unconstrained.

Implementations may be eager or lazy, mutable or persistent, centralized or
modular, and may cache internally. They must preserve object isolation, source
order, optional discovery, explicit malformed-source failure,
stage-validate-commit semantics, documented automatic fresh recovery, hook replacement and
marked merge, truthful provenance, environment/prefix behavior, hook scoping,
and library/console agreement.

## Out of scope

Redis, Vault, cloud services, live network access, Django, Flask, and remote
includes are outside scope. The durable ownership contract covers cooperating
local Python processes but does not require a daemon or network coordinator.
YAML, INI, `.env`, optional serializers, CLI write/validate,
browser opening, shell completion, exact help prose, overwrite prompt wording,
banners, colors, warnings, exact exception messages, and private diagnostics
are also outside scope.
