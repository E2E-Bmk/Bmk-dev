# Pelican Durable Publication Pipeline

## Purpose

Pelican can expose a durable publication workflow for applications that need to
coordinate content discovery, public identity, rendering, filesystem
publication, feeds, pagination, and signal delivery across restarts.  The
workflow lives in `pelican.publication` and complements Pelican's existing
configuration, URL, taxonomy, and pagination APIs.

Every workflow object is opened on its own directory.  Reopening the same
directory reconstructs committed public state.  Different directories are
independent.  Methods either complete their documented transition or leave the
last committed state observable; callers never need to inspect private files.

## Existing Pelican contracts

The package continues to expose the following imports.  These locations are
part of the compatibility contract; applications may import them exactly as
shown.

```python
from pelican import Pelican, get_config, parse_arguments, signals
from pelican.paginator import PaginationRule, Paginator
from pelican.plugins import signals as plugin_signals
from pelican.readers import Readers
from pelican.settings import DEFAULT_CONFIG, read_settings
from pelican.urlwrappers import Author, Category, Tag
from pelican.utils import get_date, path_to_url, posixize_path, slugify
```

The supported call forms used by this subsystem are:

```python
parse_arguments(argv=None)
get_config(args)
read_settings(path=None, override=None)
slugify(value, regex_subs=(), preserve_case=False, use_unicode=False)
posixize_path(rel_path)
path_to_url(path)
get_date(string)
Author(name, settings)
Category(name, settings)
Tag(name, settings)
Paginator(name, url, object_list, settings, per_page=None)
PaginationRule(min_page, URL, SAVE_AS)
```

`parse_arguments()` returns an argument namespace and `get_config()` returns
its typed configuration mapping.  `read_settings()` returns a completed
mapping: built-in defaults are retained beneath values loaded from `path`, and
the `override` mapping has highest precedence (for example, an override for
`SITENAME` replaces the file value).  The built-in defaults include
`DEFAULT_LANG` equal to `"en"`, `RELATIVE_URLS` equal to `False`, and an
`OUTPUT_PATH` entry.
The `-e NAME=value` command-line form parses JSON-like scalar values before
they are passed through `get_config()`.

With no substitutions, `slugify()` applies its case policy but otherwise
preserves text such as spaces; `regex_subs` are ordered `(pattern,
replacement)` pairs applied before case conversion.  `posixize_path()` and
`path_to_url()` return forward-slash strings.  `get_date()` returns a
`datetime.datetime` for supported public date strings and rejects an invalid
calendar value rather than silently inventing a date.

`Author`, `Category`, and `Tag` expose `name`, `slug`, `url`, and `save_as`;
`as_dict()` includes at least `name` and `slug`.  URL and save projections come
from the corresponding completed settings namespace.  `Paginator` is
one-based, preserves input order, exposes `count`, `num_pages`, `page_range`,
and `page(number).object_list`.  `PaginationRule` exposes `min_page`, `URL`,
and `SAVE_AS`, keeping URL and save projections distinct.  Core and plugin
signal modules share the same signal objects, including
`article_generator_finalized` and `content_object_init`.

## Public module and failures

`pelican.publication` exports these classes:

```python
ContentStore(path)
IdentityIndex(path)
ThemeRenderer(path)
ArtifactPublisher(path)
PublicationLedger(path)
SignalOutbox(path)
```

It also exports `PublicationError`, `StaleGenerationError`, `OwnershipError`,
`AcknowledgementError`, and `RecoveryError`.  The four specialized errors are
subclasses of `PublicationError`.

Paths passed to workflow constructors may be strings or path-like objects.
Public snapshots and receipts are ordinary dictionaries and lists containing
JSON-compatible values.  Returned collections are detached copies: changing a
receipt or snapshot does not mutate durable state.

### Workflow call signatures

The complete public call surface is:

```python
ContentStore.ingest(records, *, expected_generation=None)
ContentStore.current()
ContentStore.acknowledge(generation, digest)

IdentityIndex.project(generation, records)
IdentityIndex.snapshot()
IdentityIndex.resolve(slug)

ThemeRenderer.lease(generation, theme, identities)
ThemeRenderer.render(token, content_id, body, *, context_generation)
ThemeRenderer.commit(token)
ThemeRenderer.snapshot()

ArtifactPublisher.prepare(generation, artifacts)
ArtifactPublisher.promote(token)
ArtifactPublisher.acknowledge(generation, digest)
ArtifactPublisher.recover()
ArtifactPublisher.snapshot()
ArtifactPublisher.read(relative_path)

PublicationLedger.stage(generation, entries, *, page_size)
PublicationLedger.commit(token, publication_receipt)
PublicationLedger.view()

SignalOutbox.enqueue(
    generation, event_id, payload, *, publication_receipt
)
SignalOutbox.claim(worker)
SignalOutbox.fail(token, worker)
SignalOutbox.ack(token, worker)
SignalOutbox.pending()
SignalOutbox.delivered()
```

### Public record shapes

Fields listed here are guaranteed.  Implementations may add other
JSON-compatible informational fields, but callers never need them for the
documented protocol.

- A content receipt contains `generation` (integer), `digest` (64-character
  hexadecimal string), `count` (integer), and `acknowledged` (boolean).
  `current()` returns those fields plus `records`, the canonical ordered list
  of record mappings.
- An identity snapshot contains `generation` and `identities`.  Each identity
  row contains `identity`, `source_id`, `slug`, `aliases`, `category`, and
  `tags`.  `project()` returns this same snapshot shape, and `resolve()`
  returns one identity row or `None`.
- A theme lease contains `token`, `generation`, and `state`; a new lease has
  state `live`.  A rendered artifact contains `path`, `text`, `generation`,
  and `identity`.  `commit()` returns the ordered list of rendered artifacts;
  `snapshot()` contains `generation` and `committed`.
- A prepare receipt contains `token`, `generation`, `digest`, `state`,
  `visible`, and `acknowledged`.  Its state is `prepared` and it is not
  visible or acknowledged.  Promotion and acknowledgement receipts contain
  `generation`, `digest`, `visible`, and `acknowledged`.  A publisher snapshot
  contains `state` and `visible`, where `visible` is the current publication
  receipt or `None`.
- A staged ledger view contains `token`, `generation`, `feed`, and `pages`.
  A committed view omits `token` and contains `generation`, `feed`, and
  `pages`.  Every page row contains `number` and `items`.
- An outbox event contains `event_id`, `token`, `generation`, `payload`,
  `attempt`, `state`, `worker`, and `delivered_by`.  `claim()` returns such a
  row or `None`; `fail()` and `ack()` return the updated row.  `pending()` and
  `delivered()` return ordered lists of event rows.

The error hierarchy is intended to prevent storage-shaped exceptions from
leaking through the public protocol.  Bad public input and unsafe paths raise
`PublicationError`; stale generations or fenced contexts raise
`StaleGenerationError`; unknown, reused, or wrongly-owned tokens and worker
claims raise `OwnershipError`; missing or mismatched acknowledgements raise
`AcknowledgementError`; and unreadable or inconsistent durable state raises
`RecoveryError`.  In particular, normal calls do not expose `KeyError`,
`IndexError`, or storage-layout errors in place of these public failures.

## Content generations

`ContentStore.ingest(records, *, expected_generation=None)` accepts an iterable
of mappings.  Each record has a non-empty `source_id` and may carry `title`,
`slug`, `body`, `status`, `category`, `tags`, and other JSON-compatible public
metadata.  Source identifiers are unique within a generation.  An accepted
ingest canonicalizes records by source identifier, advances the committed
generation by exactly one, and returns a receipt containing the generation,
content digest, record count, and acknowledgement state.

When `expected_generation` is supplied it names the currently committed
generation, not the generation being created.  A mismatch raises
`StaleGenerationError` without consuming a generation.  `current()` returns
the current receipt and records.  `acknowledge(generation, digest)` accepts only
the exact current pair, is idempotent for that pair, and rejects stale or
mismatched acknowledgements with `AcknowledgementError`.  Acknowledgement is
durable across reopen.

## Identity lineage

`IdentityIndex.project(generation, records)` commits public identity for a
newer content generation.  Every source identifier owns a stable identity.
Its current slug comes from an explicit slug when present, otherwise from the
title through Pelican's public slug policy.  Changing a slug preserves the
previous slug as an alias for that same identity.  Category and tag memberships
are projected in separate namespaces even when their text is equal.

Generations must increase strictly.  A stale projection raises
`StaleGenerationError` without changing current identities or aliases.
`snapshot()` exposes the current generation and identities.  `resolve(slug)`
resolves both current slugs and retained aliases, returning `None` for an
unknown slug.  Lineage and namespace membership survive reopen.

## Theme leases and stale-context fencing

`ThemeRenderer.lease(generation, theme, identities)` opens a render lease for a
strictly newer generation and returns an opaque token.  Opening a newer lease
fences every older uncommitted lease.  `render(token, content_id, body, *,
context_generation)` returns an artifact mapping with a public path, rendered
text, generation, and identity.  The token, content identity, and context
generation must all belong to the same live lease; otherwise
`StaleGenerationError` or `OwnershipError` is raised.

`commit(token)` closes the lease and returns its ordered artifacts.  A token is
single-use after commit.  The current generation and lease state are durable,
so reopening cannot make a stale token live again.  Rendering is deterministic
for the same committed public inputs.  The built-in renderer's public text
projection is the theme name, identity, and body joined in that order by `|`;
its public path is `articles/{current-slug}.html`.  Private token text and
storage layout are unspecified.

## Artifact prepare, visibility, acknowledgement, and recovery

`ArtifactPublisher.prepare(generation, artifacts)` stages a mapping of safe
relative output paths to text or bytes and returns a prepare receipt.  Absolute
paths and paths containing a parent traversal raise `PublicationError`.
Preparing does not change the visible output tree.

`promote(token)` atomically makes exactly that prepared tree visible and
returns a publication receipt containing its generation, digest, visibility,
and acknowledgement state.  A token belongs to one publisher and is
single-use.  `acknowledge(generation, digest)` accepts only the currently
visible publication, is idempotent, and returns an acknowledged receipt.

`recover()` is idempotent.  After interruption in the prepared state it
discards the uncommitted stage and preserves the prior visible tree.  After
promotion it retains the promoted tree and retires obsolete recovery material,
whether or not acknowledgement had completed.  `snapshot()` reports the
durable journal state and visible publication; `read(relative_path)` reads a
visible artifact as bytes or returns `None` when it is absent.  Recovery of an
interrupted prepare reports state `recovered-prepared`; recovery of an
unacknowledged promotion reports `recovered-promoted`; an acknowledged
publication continues to report `acknowledged`.

## Feed and pagination ledger

`PublicationLedger.stage(generation, entries, *, page_size)` builds a candidate
publication view without making it current.  Entries are mappings containing
at least `source_id`, `title`, and `url`.  Only entries whose status is absent
or `published` enter the feed.  Feed order is descending public `date`, with
`source_id` as the deterministic tie breaker.  Pages preserve that feed order,
use one-based page numbers, and never contain more than the positive
`page_size`.  The returned stage token is opaque.

`commit(token, publication_receipt)` requires an acknowledged, visible
publication receipt for the same generation.  Wrong generation, missing
acknowledgement, a stale stage, or token reuse raises the corresponding public
error without changing the committed view.  `view()` returns the committed
generation, feed, and pages.  Staging state and the committed view survive
reopen, and a newer commit replaces rather than merges the prior view.

## Signal delivery outbox

`SignalOutbox.enqueue(generation, event_id, payload, *, publication_receipt)`
requires an acknowledged publication receipt for the same generation.  Event
identifiers are unique: enqueueing the same identifier again returns the same
event token and never creates a second delivery.  `claim(worker)` returns the
oldest pending event with an attempt number and binds it to that non-empty
worker, or returns `None` when no event is available.

`fail(token, worker)` releases a matching claim for retry.  The next claim has
a larger attempt number.  `ack(token, worker)` completes only the matching
claim and makes the event visible through `delivered()`.  Wrong workers or
tokens raise `OwnershipError`.  Acknowledgement is idempotent for the same
worker and event.  `pending()` and `delivered()` return ordered detached
snapshots.  Reopening turns interrupted claims back into pending work while
preserving attempt counts and completed exactly-once delivery.

## Cross-owner publication law

A complete publication uses one content generation throughout: ingest commits
the source facts; identity projection binds stable public names; a theme lease
renders those identities; artifact promotion makes the rendered tree visible;
an acknowledged publication authorizes the feed/page ledger and signal outbox.

No downstream owner may infer acknowledgement from visible files, accept a
receipt from another generation, or silently recompute history from only the
latest values.  Failures before publication acknowledgement cannot advance the
feed ledger or enqueue a delivery.  Retry after reopen begins from the last
committed state, retains identity aliases, fences stale render contexts, and
does not duplicate delivered events.

## Typical application flow

The owners exchange only the records described above.  For example, an
application may ingest records, project identities from `current()["records"]`,
pass the identity snapshot directly to `lease()`, and use the returned
`lease["token"]` for every render and for `commit()`.  It then prepares a path
to text/bytes mapping, promotes `prepared["token"]`, and acknowledges the
returned generation and digest.  That acknowledged publication receipt is
passed unchanged to both `PublicationLedger.commit()` and
`SignalOutbox.enqueue()`.

```python
content = store.ingest([
    {"source_id": "ember", "title": "Ember Almanac", "body": "..."}
])
identities = index.project(content["generation"], store.current()["records"])
lease = renderer.lease(content["generation"], "harbor", identities)
artifact = renderer.render(
    lease["token"], identities["identities"][0]["identity"], "body",
    context_generation=content["generation"],
)
renderer.commit(lease["token"])
prepared = publisher.prepare(
    content["generation"], {artifact["path"]: artifact["text"]}
)
visible = publisher.promote(prepared["token"])
publication = publisher.acknowledge(
    visible["generation"], visible["digest"]
)
```

The returned mappings are the public handoff objects.  Tokens themselves are
opaque strings: callers store and return them but do not parse them.

## Non-goals

The contract does not prescribe private file names, JSON layout, lock
implementation, token spelling, HTML framework, network transport, worker
process management, or a template language.  It does not require compatibility
with private Pelican internals.  Concurrency performance and distributed
storage are outside scope; durable single-host behavior and public ownership
rules are in scope.
