# MkDocs recoverable site publication

## Scope

This contract defines a local, recoverable MkDocs build mode.  It keeps the
ordinary public MkDocs configuration, file, page, navigation, plugin, search,
and `mkdocs.commands.build.build` interfaces.  Recovery is enabled by a
`recovery` mapping inside `extra`; builds without that mapping retain ordinary
MkDocs behavior.

The mode is intended for build agents that may stop after preparation,
publication, or event delivery and later reopen the same project.  Its durable
records are public operational artifacts.  Implementations may choose any
internal algorithms, databases, or caches that preserve the laws below.

## Public compatibility surface

### Configuration and build calls

Normal local builds import `load_config` from `mkdocs.config` and `build` from
`mkdocs.commands.build`.  Their supported signatures and returns are
`load_config(config_file=None, *, config_file_path=None, **kwargs) -> config`
and `build(config, *, serve_url=None, dirty=False) -> None`.  The configuration
input may be a path, an open file object, or `None`.  Configuration values are
available through both string-key mapping access and attribute access; the
mapping supports normal iteration, length, and truth testing, while numeric
indexing is not implied.  Passing `None` as an optional keyword override leaves
a value loaded from the configuration file in place.

### Files and file collections

The public file imports are `File`, `Files`, and `get_files` from
`mkdocs.structure.files`.  The supported constructor is `File(path, src_dir,
dest_dir, use_directory_urls, *, dest_uri=None, inclusion=...)`.  A `File`
exposes normalized `src_uri`, `dest_uri`, `url`, `src_dir`, `dest_dir`, and
`page` attributes, together with source/destination path projections and the
usual predicates such as `is_css()`.  It is an object, not an indexable or
iterable container.  Constructing a `Page` for a file sets the same Page
instance as `file.page`.

`Files(files)` accepts an iterable of `File` instances.  It is mutable,
iterable in collection order, sized by `len(files)`, and truth-tested from that
length; it is not a positional sequence and does not promise integer indexing.
`append(file)` and `remove(file)` return `None`.  `src_uris` is a mapping whose
normalized URI keys map to the collection's `File` objects, so membership and
iteration operate on URI keys.  `get_file_from_path(path)` returns the identical
stored `File` or `None`.  `documentation_pages()`, `static_pages()`,
`media_files()`, `javascript_files()`, and `css_files()` return finite ordered
sequences.  `get_files(config)` returns a `Files` collection.

### Pages and tables of contents

`Page` is imported from `mkdocs.structure.pages`.  Its supported lifecycle is
`Page(title, file, config)`, `read_source(config) -> None`, followed by
`render(config, files) -> None`.  Before reading, content-derived values may be
empty.  Reading populates the page's Markdown and mutable metadata mapping;
rendering populates HTML `content`, the resolved public `title`, and `toc`.
The page exposes `file`, `url`, `parent`, `previous_page`, `next_page`, and the
ordinary navigation flags.  A page itself is not a collection and has no
length or indexing protocol.

After render, `page.toc` is a table-of-contents collection: it is iterable,
supports `len(page.toc)`, and its truth value follows whether its length is
zero.  Random indexing of the TOC object is not required; callers may convert
it to a list.  Iteration yields anchor entries with public `title`, `id`,
`level`, `url`, and `children` attributes, where `children` is an ordered list
of further anchor entries.  An empty rendered outline has length zero.

### Navigation objects

`Link`, `Section`, and `get_navigation` are imported from
`mkdocs.structure.nav`.  Their supported calls are `Link(title, url)`,
`Section(title, children)`, and `get_navigation(files, config) -> navigation`.
The returned navigation object is iterable over its top-level `items`, supports
`len(navigation)` and ordinary truth testing, and is not itself required to be
integer-indexable.  Its `items` attribute is an ordered, iterable, sized,
indexable list of top-level Page, Section, or Link objects.  Its `pages`
attribute is an ordered, iterable, sized, indexable flat list containing only
the Page objects in navigation order.

Sections expose `title`, ordered `children`, `parent`, `active`, and their
section/page/link flags.  Links expose `title`, `url`, `parent`, and their
link/page/section flags.  Navigation construction preserves Page/File identity,
assigns parentage, sets adjacent pages through `previous_page` and `next_page`,
and retains external links as `Link` objects.  Ordinary build output, page
links, navigation URLs, and search locations follow the same
`use_directory_urls` policy.

### Resource and warning discipline

Public configuration loading, file-content access, `Page.read_source`, page
rendering, navigation construction, and `build` must release every file handle
they open before the call returns or raises.  They do not rely on garbage
collection to close configuration, Markdown, template, search, or durable
record streams.  Valid ordinary and recovery calls emit no Python warnings,
including `ResourceWarning`, and remain valid when warnings are collected or
promoted to errors.  This obligation also applies to failure paths and repeated
fresh-process reopen/retry lifecycles.

The standard public error module exports `MkDocsException`, `Abort`,
`ConfigurationError`, `BuildError`, and `PluginError`.  `Abort` and
`BuildError` derive from `MkDocsException`, `PluginError` derives from
`BuildError`, and `Abort.exit_code` is `1`.  Configuration and build callers
may catch the common base class; strict validation failures use `Abort`, while
the recovery failures described below use `BuildError` or a compatible more
specific public subclass.

## Recovery configuration

`extra.recovery.state_dir` names the durable state directory.  A relative value
is owned by the configuration file's directory.  State must not be placed
inside `docs_dir` or `site_dir`.  `action` is `prepare` or `publish`, with
`publish` as the default.  `acknowledge` defaults to true.  An optional
`expected_visible_generation` fences publication.  An optional `renames`
mapping declares source-identity transfers from an old source URI to a new
source URI.  An optional `delivery_failure` names an event kind whose delivery
must remain pending for that invocation.

Unknown recovery settings or invalid values fail as a public MkDocs build
error.  Paths and source identities use normalized forward-slash relative
forms.  Configuration mappings supplied by a caller are not mutated.

## Generations and configuration ownership

A project has monotonically increasing positive generations.  The effective
recovery-relevant configuration and the discovered source snapshot jointly
identify a generation.  Repeating a build with the same effective inputs
reuses the generation; changing either advances it exactly once.  Reopening in
a fresh process continues from durable state rather than restarting the count.

The configuration owner records a normalized projection that includes site
identity, URL mode, navigation, theme selection, and configured plugin names.
Semantically equivalent mapping order does not create a new generation.
Changing the destination alone changes publication ownership but does not
change source lineage identifiers.

## Discovery and acknowledgement

The discovery owner records every regular source file by normalized URI and
content digest.  Each new generation records sorted added, modified, and
removed sets relative to the last acknowledged snapshot.  A successful
acknowledgement advances the acknowledged source snapshot.

Only one unacknowledged input generation may be active.  Repeating that exact
generation may publish, deliver, or acknowledge it.  A different input while
it remains unacknowledged fails at the build boundary and does not replace the
pending facts.

## Page identity lineage

Every discovered Markdown page has a durable opaque identity and a positive
revision.  Ordinary edits preserve the identity and advance the revision.
Unchanged pages preserve both.  Removal retires the active identity.  A valid
declared rename transfers the old identity to the new URI and advances its
revision; it may not collide with a still-active source or claim one old URI
for multiple destinations.

Navigation, publication, and search receipts for a page generation refer to
the same source URI, lineage identity, and revision.  The concrete identity
encoding is not prescribed.

## Preparation and publication

Every generation is built into a generation-owned preparation area before it
can become visible.  `action: prepare` creates or refreshes that prepared
snapshot but leaves the visible destination and its generation unchanged.
Preparing the same inputs repeatedly is idempotent.

`action: publish` makes one complete prepared generation visible.  When an
expected visible generation is supplied, it must equal the currently visible
generation (zero means no prior publication).  A stale expectation fails
without changing visible bytes or the visible generation and is recorded as a
fenced attempt.  Publication never combines files from two generations.

A successful clean publication removes destination files that are absent from
the prepared generation.  It does not delete the recovery state directory or
unrelated sibling paths.

## Search receipts

When search is enabled, the search owner records the public search artifact's
digest and semantic document receipts.  Each receipt contains the source URI,
page lineage identity, revision, public title, and location for the same
generation.  When search is disabled, the owner records an empty receipt set
and no invented search artifact.

A published but unacknowledged generation may be visible, but it is not an
acknowledged search generation.  Search acknowledgement advances only with the
same generation's source and publication acknowledgement.

## Event outbox and recovery

Input changes create generation-owned public events for configuration change
and source addition, modification, removal, or declared rename as applicable.
Each logical event has one stable identifier.  Delivery is exactly once:
retrying a pending event increments its attempt count but never creates a
second logical event or redelivers an already delivered event.

If delivery fails after publication, visible publication remains visible, the
failed event and all later undelivered events remain pending, and the build
reports failure.  A later invocation with identical inputs resumes that
generation.  Once all events are delivered, acknowledgement may complete.

## Durable owner records

The state directory exposes separate records named `config.json`,
`discovery.json`, `lineage.json`, `publication.json`, `search.json`, and
`outbox.json`.  These files are a public JSON inspection and recovery surface,
not an implementation-private cache.  Every record is a JSON object with four
required members: `schema_version` is the integer `1`; `owner` is the matching
lower-case owner name; `body` is an object with the owner-specific shape below;
and `checksum` is a lower-case, 64-character SHA-256 hex digest.  The checksum
is computed from the UTF-8 JSON encoding of `body` with object keys sorted and
with no insignificant whitespace.  Additional forward-compatible members may
be present, but the required members, nesting, and types may not be omitted or
changed.

Every owner body has a required positive-integer `generation`.  Generation
fields that represent a not-yet-existing visible, pending, or acknowledged
generation use the non-negative integer `0`; they are never absent.  URI and
output-file maps below are JSON objects from normalized relative path strings
to lower-case, 64-character SHA-256 content digests.  Change and retirement
arrays contain strings in sorted order.

- The `config` body requires `generation`, `fingerprint`,
  `input_fingerprint`, and `effective`.  Both fingerprints are SHA-256 strings.
  `effective` is an object requiring `site_name` (string), `site_url` (string
  or null), `use_directory_urls` (boolean), `nav` (array or null), `theme`
  (string or null), and `plugins` (an array of plugin-name strings).  Plugin
  names are normalized into sorted order; in particular, the ordinary search
  configuration is represented as `["search"]`, while disabled plugins are
  represented as an empty array.
- The `discovery` body requires `generation`, `observed_sources`, `changes`,
  `pending_generation`, `pending_fingerprint`, `acknowledged_generation`, and
  `acknowledged_sources`.  `observed_sources` and `acknowledged_sources` are URI
  digest maps.  `pending_fingerprint` is a SHA-256 string while a generation is
  pending and null otherwise.  `changes` is an object requiring the four
  string arrays `added`, `modified`, `removed`, and `renamed`; each rename is
  written as the normalized `old-uri->new-uri` pair.
- The `lineage` body requires `generation`, `pages`, `retired`, and `changes`.
  `pages` is an object keyed by active Markdown source URI.  Every page value
  is an object requiring a non-empty string `id`, a positive-integer
  `revision`, and a SHA-256 `source_digest`.  `retired` is a string array, and
  `changes` has the same required four-array shape as discovery changes.
- The `publication` body requires `generation`, `prepared_generation`,
  `visible_generation`, `acknowledged_generation`, `prepared_files`,
  `visible_files`, and `stale_fence_count`.  The generation and fence-count
  fields are non-negative integers except for the body's positive current
  `generation`; the two file members are output-path digest maps.
- The `search` body requires `generation`, `artifact_sha256`, `receipts`, and
  `acknowledged_generation`.  `artifact_sha256` is a SHA-256 string when a
  search artifact exists and null when search is disabled.  `receipts` is an
  array, possibly empty, whose objects each require `source_uri` (string),
  `page_id` (non-empty string), `revision` (positive integer), `title` (string
  or null), and `location` (string).
- The `outbox` body requires `generation` and `events`.  `events` is an array,
  possibly empty, whose objects each require `id` (non-empty string),
  `generation` (positive integer), `kind` (one of `config-changed`,
  `source-added`, `source-modified`, `source-removed`, or `source-renamed`),
  `subject` (string), `status` (`pending` or `delivered`), and `attempts`
  (non-negative integer).

The arrays allowed to be empty remain present as arrays.  Callers therefore
distinguish an empty semantic result from a missing or wrongly typed field.
Updates are replacement-safe: readers see either the previous valid record or
the next valid record.

Missing records are allowed only before the first recovery build.  Corruption,
owner mismatch, or checksum mismatch in any existing record fails publicly at
the build call.  Such failure does not silently recompute history and does not
change visible publication or other valid owner records.

## Failure boundary

Configuration, source, navigation, theme, plugin, rendering, fencing, durable
state, and delivery errors are public MkDocs build failures.  A failed call
does not report post-build success.  Correcting the responsible public input
or restoring the damaged owner permits a later build at the recovery scope
defined above.

The contract does not require network access, a live server, filesystem
watchers, sleeps, mtime races, private plugin dispatch, a particular database,
or exact HTML/search serialization.  Exact log prose, temporary filenames,
JSON whitespace, and iteration order outside explicitly sorted change sets are
not semantic.

## Cross-owner laws

- A generation number refers to one normalized configuration and one source
  snapshot across all owner records.
- A page receipt uses the same URI, lineage identity, and revision in lineage,
  publication, search, and source-change events.
- Visibility advances only through publication; acknowledgement advances only
  after publication and successful outbox delivery.
- A stale writer, an unacknowledged competing input, or a corrupted owner
  cannot be repaired by eagerly recomputing history.
- Reopen, retry, and correction preserve already acknowledged identities,
  generations, delivered-event uniqueness, and visible destination ownership.
