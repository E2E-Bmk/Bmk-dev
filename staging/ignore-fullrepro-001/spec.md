<!-- INTERNAL
task_id: ignore-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: docs.rs/ignore 0.4.23 (crate root, gitignore, overrides, types, walk module and item docs), git-scm.com gitignore format description, ripgrep GUIDE section on automatic filtering; reference behavior observed by running the pinned checkout (probe binary, two rounds)
-->

# Ignore Rules and Directory Walking Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`ignore` is a Rust library for matching file paths against ignore rules and
for walking directory trees while honoring those rules. Its core is a single
rule stack in the gitignore pattern dialect — patterns collected from
`.gitignore` files, `.ignore` files, custom ignore files, explicit override
globs, and file-type definitions — evaluated with precise precedence: within
one source the last matching pattern wins, and across sources a fixed rank
order decides which source's verdict applies.

The stack is exposed through two kinds of projection. Matcher types
(`Gitignore`, `Override`, `Types`) answer pure queries — given a path and
whether it is a directory, they return an ignore verdict together with the
pattern that produced it. The walker (`WalkBuilder` and its serial and
parallel iterators) applies the same rules to a real file tree, discovering
ignore files as it descends and yielding exactly the entries the rules
admit. Both projections must agree: a path the matcher stack ignores never
appears in a walk over an equivalent tree.

## Non-Goals

- This specification does not require following symbolic links, symlink
  loop detection, or reporting whether an entry was reached through a
  symlink beyond a `false` answer for ordinary entries.
- This specification does not require reading the user's global git
  configuration: no lookup of `core.excludesFile`, no reading of a global
  ignore file from the home directory or environment, and no
  `gitconfig_excludes_path` helper. The global-gitignore toggle on the
  walker must exist but its rules resolve to nothing in this environment.
- This specification does not require a built-in table of default file-type
  definitions; only explicitly added type definitions matter.
- This specification does not require skipping entries that correspond to
  the process's standard output, same-file-system confinement, or
  device/inode reporting.
- This specification does not require a command-line interface.
- This specification does not define the yield order of a walk when no sort
  callback is installed; only membership is contractual in that case.

## Representative Workflows

**Query a matcher.** Build a gitignore matcher from pattern lines and ask
for verdicts. The verdict carries the pattern that decided it:

```rust
use ignore::gitignore::GitignoreBuilder;

let mut builder = GitignoreBuilder::new("/project");
builder.add_line(None, "*.log").unwrap();
builder.add_line(None, "!keep.log").unwrap();
let matcher = builder.build().unwrap();

assert!(matcher.matched("debug.log", false).is_ignore());
assert!(matcher.matched("keep.log", false).is_whitelist());
assert!(matcher.matched("src/main.rs", false).is_none());
```

**Walk a tree with standard filters.** The walker discovers `.gitignore`
files on its way down and yields the root first:

```rust
use ignore::WalkBuilder;

// Given a directory tree with a `.git` marker and a `.gitignore`
// containing `target/`:
for result in WalkBuilder::new("./project").build() {
    let entry = result.unwrap();
    // Nothing under target/ and no hidden files are yielded.
    println!("{} (depth {})", entry.path().display(), entry.depth());
}
```

**Combine overrides, types, and a parallel walk.** All rule sources feed
one decision, and the parallel walker sees the same set as the serial one:

```rust
use ignore::overrides::OverrideBuilder;
use ignore::types::TypesBuilder;
use ignore::{WalkBuilder, WalkState};

let mut over = OverrideBuilder::new("./project");
over.add("!*.min.js").unwrap();
let mut types = TypesBuilder::new();
types.add("web", "*.js").unwrap();
types.select("web");

let mut builder = WalkBuilder::new("./project");
builder
    .overrides(over.build().unwrap())
    .types(types.build().unwrap());
builder.build_parallel().run(|| {
    Box::new(|result| {
        if let Ok(entry) = result {
            // only *.js files, minus *.min.js, minus ignored ones
            let _ = entry.path();
        }
        WalkState::Continue
    })
});
```

## Ignore Pattern Matching

This section defines the gitignore pattern dialect and the matcher built
from it; every other rule source in the library reuses this machinery.

**Verdicts.** `Match` is a generic enum with three variants: `None` (no
pattern matched), `Ignore(T)` (the path is ignored), and `Whitelist(T)`
(the path is explicitly re-included), where the payload identifies the
deciding pattern. `is_none`, `is_ignore`, and `is_whitelist` test the
variant; `inner` returns the payload reference (`Some` unless `None`);
`invert` swaps `Ignore` and `Whitelist` and leaves `None` unchanged; `map`
transforms the payload; `or` returns the receiver unless it is `None`, in
which case it returns the argument.

**Building a matcher.** `GitignoreBuilder::new` accepts a root directory
path; all matching is relative to that root. `add_line` accepts an optional
source-file path and one pattern line, returning a mutable-builder result
that is an error when the line contains an invalid glob. `add` accepts the
path of a gitignore-format file, reads all its lines, and returns
`Some(Error)` when the file cannot be read or contains invalid patterns
(`None` on success). `case_insensitive` accepts a boolean; when enabled,
patterns added afterward match without regard to letter case. `build`
returns the immutable `Gitignore` matcher or an error. The convenience
constructor `Gitignore::new` accepts the path of a gitignore file and
returns the pair of a matcher (rooted at the file's parent directory) and
an optional error; `Gitignore::empty` returns a matcher with no patterns
whose every query answer is `None`, whose `is_empty` is true and `len` is
zero.

**Pattern dialect.** Each line is one rule, evaluated as follows:

- A line that is empty, whitespace-only, or starts with `#` is skipped and
  adds no pattern. A leading `\#` escapes the hash: the pattern matches a
  name starting with a literal `#`. Unescaped trailing whitespace is
  trimmed; a backslash-escaped trailing space is kept as a literal space.
- A leading `!` marks the pattern as a whitelist rule: a path it matches is
  re-included even if an earlier pattern ignored it.
- A pattern with no `/` (other than an optional trailing one) matches the
  final name component at any depth: `silt.log` matches both `silt.log`
  and `nested/silt.log`.
- A pattern containing a `/` in a non-trailing position is anchored to the
  matcher root: `/topsoil.txt` matches only the root-level `topsoil.txt`;
  `docs/*.tmp` matches `docs/a.tmp` but not `docs/sub/a.tmp` and not
  `other/docs/a.tmp` — a single `*` never crosses a path separator.
- A trailing `/` restricts the pattern to directories: `cache/` matches a
  directory named `cache` at any depth, and does not match a file of the
  same name. Whether a query names a directory is supplied by the caller
  as the `is_dir` argument.
- `**` spans any number of components: `**/deep.txt` matches at every
  depth including the root; `sub/**/leaf.md` matches `sub/leaf.md`,
  `sub/a/leaf.md`, and `sub/a/b/leaf.md`.
- Within one matcher, when several patterns match the same path, the
  pattern added last decides the verdict (last match wins). A whitelist
  pattern followed by a later ignore pattern for the same path yields
  `Ignore`; the reverse order yields `Whitelist`.

**Queries.** `matched` accepts a path and an `is_dir` flag and returns a
`Match` whose payload is a `Glob` describing the deciding pattern. The path
is interpreted relative to the matcher root; an absolute path under the
root is stripped to its root-relative form. `matched_path_or_any_parents`
additionally checks every ancestor directory of the path below the root:
when any ancestor matches an ignore rule (such as a directory-only
pattern), the whole path is reported `Ignore` even though `matched` on the
full path alone returns `None`. `num_ignores` and `num_whitelists` return
the number of ignore and whitelist patterns; `len` returns the total
pattern count and `is_empty` reports whether it is zero; `path` returns
the matcher root.

**Pattern provenance.** The `Glob` payload exposes `original` (the line as
added), `actual` (the compiled glob text), `from` (the source file path
given when the pattern was added, absent for lines added with no source),
`is_only_dir` (trailing-slash rule), and `is_whitelist`.

## Override Globs

This section defines the override matcher: the same pattern dialect with
inverted polarity, used to restrict a walk to caller-chosen globs.

**Building.** `OverrideBuilder::new` accepts a root directory. `add`
accepts one glob line and returns an error for invalid globs;
`case_insensitive` behaves as on the gitignore builder; `build` returns an
`Override`. `Override::empty` returns an override with no globs; `path`,
`is_empty`, `num_ignores`, and `num_whitelists` mirror the gitignore
accessors, with inverted counting: a plain glob counts as a whitelist rule
and a `!`-prefixed glob counts as an ignore rule.

**Matching.** `matched` accepts a path and `is_dir` flag. An empty
override returns `None` for every query. Otherwise polarity is the inverse
of gitignore: a path matching a plain glob returns `Whitelist`; a path
matching a `!`-prefixed glob returns `Ignore`. When no glob matches, the
result depends on the query kind: a directory returns `None` (so walkers
still descend), and a file returns `Ignore` when the override set contains
at least one plain (non-`!`) glob — with only `!` globs present, an
unmatched file returns `None`.

## File Type Filters

This section defines named glob groups and the selection matcher built
from them.

**Definitions.** `TypesBuilder::new` creates an empty builder. `add`
accepts a type name and one glob and returns a unit result; the name must
consist only of Unicode letters and numbers and must not be the reserved
word `all`, otherwise `add` returns an error. Repeated `add` calls with the
same name accumulate globs under one definition. `add_def` accepts a
string-form definition in one of two formats: `{name}:{glob}` (everything
after the first `:` is a single glob, commas included), or
`{name}:include:{comma-separated names}` which defines a composite whose
globs are those of the named existing definitions. `definitions` (on both
builder and built matcher) returns the sorted list of `FileTypeDef` values;
each exposes `name` and `globs`.

**Selection.** `select` marks a named type (or `all`, meaning every defined
type) as selected; `negate` marks a name (or `all`) as negated; `clear`
accepts a name and removes its selections. `build` returns a `Types`
matcher, or an error when a selected or negated name has no definition.
`Types::empty` returns a matcher with no definitions and no selections;
`len` counts selections and `is_empty` reports zero selections.

**Matching.** `matched` accepts a path and `is_dir` flag. With no
selections at all, every query returns `None`. Directories always return
`None`. A file matching a negated type's glob returns `Ignore`; a file
matching a selected type's glob returns `Whitelist`; a file matching
neither returns `Ignore` when at least one selection exists. The payload
`Glob` of a decisive match exposes `file_type_def`, the `FileTypeDef` that
owns the matched glob (absent for the blanket unmatched-file verdict).

## Directory Walking

This section defines the recursive walker: the rule stack applied to a
real tree.

**Construction and iteration.** `WalkBuilder::new` accepts a root path;
`add` appends an additional root, and the walk visits all roots in the
order given. `build` returns `Walk`, an iterator of results, each `Ok` item
a `DirEntry` and each `Err` item an `Error`. The root itself is yielded
first with depth `0`; a root naming a file yields exactly that file. A
nonexistent root yields a single `Err` item whose `is_io` is true.
`DirEntry` exposes `path` (root-joined path), `into_path`, `file_name`,
`depth` (component distance from the root), `file_type` (absent only for
stdin entries), `metadata`, and `path_is_symlink` (false for ordinary
entries). `Walk::new` builds a default walker for one root, equivalent to
building with no customization.

**Default filtering.** With no configuration beyond the root, the walker
must: skip hidden entries (name starting with `.`) including hidden
directories and everything below them; read `.ignore` files; and read
`.gitignore` files and `.git/info/exclude` — but apply the git-sourced
rules only when the walked tree is inside a git repository (a `.git`
directory at or above the walk root). Ignore files are discovered per
directory during descent and their rules apply to everything at or below
that directory. A rule file's own entry is still subject to hidden
filtering (a `.gitignore` file is itself hidden), but its rules apply
regardless of whether the file is yielded.

**Source precedence.** When rule sources disagree about one path, the
verdict comes from the highest-ranking source that has an opinion
(whitelist and ignore both count as opinions):

1. explicit override globs installed with `overrides` (highest),
2. custom ignore files installed with `add_custom_ignore_filename`,
3. `.ignore` files,
4. `.gitignore` files, then `.git/info/exclude`, then global rules
   (lowest of the per-directory sources),
5. ignore files installed with `add_ignore` (lowest overall).

Within each per-directory source, files in deeper directories outrank
files in shallower ones, and within one file the last matching pattern
wins. A whitelist rule in a higher-ranking source (for example `!b.log` in
`.ignore`) re-includes a path that a lower-ranking source (`*.log` in
`.gitignore`) ignores. File-type filters apply to files only, after the
ignore decision. A whitelist rule cannot rescue a file inside an ignored
directory: the walker never descends into a directory whose verdict is
`Ignore`, even though a pure matcher query for the file alone reports
`Whitelist`.

**Toggles.** Each toggle accepts a boolean and returns the builder for
chaining. `hidden` (default enabled) skips hidden entries; disabling it
yields dotfiles and descends into dot-directories. `ignore` (default
enabled) controls `.ignore` files. `git_ignore`, `git_global`, and
`git_exclude` (defaults enabled) control `.gitignore`, global rules, and
`.git/info/exclude` respectively. `require_git` (default enabled) gates
all three git-sourced kinds on the presence of a git repository; with
`require_git` disabled the git-sourced files apply everywhere. `parents`
(default enabled) controls whether ignore files in directories above each
walk root are consulted; disabling it also stops the upward search that
discovers the repository root, so git-sourced rules from above the root no
longer apply. `standard_filters` sets `hidden`, `parents`, `ignore`,
`git_ignore`, `git_global`, and `git_exclude` together to one value.
`ignore_case_insensitive` (default disabled) makes patterns from ignore
files match case-insensitively.

**Extra rule files.** `add_custom_ignore_filename` accepts a file name;
files with that name are read in every directory, ranked above `.ignore`.
`add_ignore` accepts the path of one ignore file whose rules apply to the
entire walk at the lowest precedence; it returns an optional `Error` for
unreadable files or invalid patterns.

**Selection limits.** `max_depth` accepts an optional depth; entries
deeper than the limit are not yielded (the root is depth `0`).
`max_filesize` accepts an optional byte count; regular files larger than
the limit are skipped, directories are never affected. `filter_entry`
accepts a predicate over `DirEntry`; an entry for which the predicate
returns false is not yielded, and when it is a directory nothing below it
is visited. `overrides` installs an `Override` matcher: files whose
override verdict is `Ignore` are skipped (unmatched files are ignored per
the override matching rules above); directories are still descended.
`types` installs a `Types` matcher with the same file-only application.

**Sorting.** `sort_by_file_name` accepts a comparator over file names
(`OsStr`); `sort_by_file_path` accepts a comparator over full paths.
Either makes the serial walk yield each directory's entries in comparator
order, parents before their children. Without a sort callback the yield
order is unspecified and only membership is contractual.

## Parallel Walking

This section defines the multi-threaded projection of the same walk.

**Running.** `build_parallel` returns a `WalkParallel`. Its `run` method
accepts a factory closure, called once per worker thread, that returns a
boxed `FnMut` visitor; the visitor receives each walk result and returns a
`WalkState`. `threads` on the builder sets the worker count, where `0`
selects an automatic default. The set of results delivered across all
visitors must equal the set the serial walk yields for the same
configuration; arrival order is unspecified.

**Flow control.** `WalkState::Continue` proceeds normally.
`WalkState::Skip` — returned for a directory entry — prevents descent into
that directory (the directory itself has already been delivered), and has
no further effect for file entries. `WalkState::Quit` stops the entire
walk as soon as possible; results already in flight are still delivered.

## State Model

One rule stack, five public projections:

- **Gitignore matcher**: pattern lines compiled per source file, queried
  by path + directory flag, reporting verdict and deciding pattern.
- **Override matcher**: the same dialect with inverted polarity and a
  blanket-ignore rule for unmatched files when plain globs exist.
- **Types matcher**: named glob groups with select/negate marks, applying
  to files only.
- **Serial walk**: the stack applied to a tree, discovering per-directory
  rule files during descent, composing sources by rank, yielding entries.
- **Parallel walk**: the same visibility set delivered concurrently with
  per-entry flow control.

Builders own all mutation; built matchers are immutable and every query is
pure. The walker composes matchers per directory; the effective verdict
for a path is a fold over sources in rank order where the first
non-`None` verdict wins.

## Error Semantics

| Condition | Outcome |
|---|---|
| `add_line`/`add` (overrides) with an invalid glob | returns `Err(Error)` |
| `GitignoreBuilder::add` / `add_ignore` with an unreadable file | returns `Some(Error)` |
| `TypesBuilder::add`/`add_def` with a non-alphanumeric name or the name `all` | returns `Err(Error)` |
| `TypesBuilder::build` with a selected or negated name that was never defined | returns `Err(Error)` |
| Walking a nonexistent root | yields exactly one `Err` item; `is_io()` is true |
| Unreadable directory during a walk | yields an `Err` item for it; the walk continues |

`Error` values implement `Display` and expose `is_partial` (aggregate of
several errors), `is_io` (wraps an I/O error), `io_error` (the wrapped
I/O error when present), and `depth` (the directory depth where a walk
error arose, when applicable).

## Cross-View Invariants

1. For any tree and configuration, the set of paths delivered by
   `build_parallel().run(...)` must equal the set yielded by `build()`.
2. For a tree whose only rule file is one root-level `.gitignore` (walked
   with `require_git(false)` and other sources disabled), a file is
   yielded by the walk exactly when a `Gitignore` built from that file
   reports it not-`Ignore` via `matched_path_or_any_parents`.
3. With an `Override` installed, the files yielded by a walk must be
   exactly the walked-and-not-ignored files whose override verdict is not
   `Ignore`; the same correspondence holds for an installed `Types`
   matcher and its `matched` verdicts.
4. `matched_path_or_any_parents(p, is_dir)` must equal the first `Ignore`
   or `Whitelist` verdict of `matched` applied to `p` and then each of its
   ancestor directories from deepest to shallowest, and `None` when no
   level yields a verdict.
5. An `Override` built from a glob list must report, for every matched
   path, exactly the inverted verdict of a `Gitignore` built from the same
   lines rooted at the same directory — with the additional rule that an
   unmatched file becomes `Ignore` when the override set contains a plain
   glob.
6. `standard_filters(false)` must yield the same set as disabling
   `hidden`, `parents`, `ignore`, `git_ignore`, `git_global`, and
   `git_exclude` individually.
7. For every yielded entry, `depth()` must equal the number of path
   components between the walk root and `path()`, and `max_depth(Some(d))`
   must yield exactly the depth-limited subset of the unlimited walk.
8. With a comparator installed via `sort_by_file_name` or
   `sort_by_file_path`, the multiset of yielded paths must be unchanged
   from the unsorted walk, every directory must be yielded before its
   contents, and siblings must appear in comparator order.

## Public Interface

### Import Surface

```rust
// crate root
use ignore::{DirEntry, Error, Match, Walk, WalkBuilder, WalkParallel, WalkState};

// gitignore matching
use ignore::gitignore::{Gitignore, GitignoreBuilder, Glob};

// override globs
use ignore::overrides::{Override, OverrideBuilder};

// file type filters
use ignore::types::{FileTypeDef, Types, TypesBuilder};
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Match` | enum | verdict: `None` / `Ignore(T)` / `Whitelist(T)` with tests, `invert`, `inner`, `map`, `or` |
| `Gitignore` | struct | compiled gitignore matcher; `matched`, `matched_path_or_any_parents`, counters, `path`, `empty`, `new` |
| `GitignoreBuilder` | struct | collects pattern lines and files; `add_line`, `add`, `case_insensitive`, `build` |
| `Glob` (gitignore) | struct | deciding pattern: `original`, `actual`, `from`, `is_only_dir`, `is_whitelist` |
| `Override` | struct | inverted-polarity glob matcher; `matched`, counters, `empty`, `path` |
| `OverrideBuilder` | struct | collects override globs; `add`, `case_insensitive`, `build` |
| `Types` | struct | file-type matcher; `matched`, `definitions`, `empty`, `len` |
| `TypesBuilder` | struct | type definitions and marks; `add`, `add_def`, `select`, `negate`, `clear`, `definitions`, `build` |
| `FileTypeDef` | struct | one named glob group; `name`, `globs` |
| `Glob` (types) | struct | deciding type glob; `file_type_def` |
| `WalkBuilder` | struct | walk configuration: roots, toggles, limits, matchers, sorting |
| `Walk` | struct | serial iterator of `Result<DirEntry, Error>` |
| `WalkParallel` | struct | multi-threaded walk; `run` with per-thread visitors |
| `WalkState` | enum | visitor flow control: `Continue` / `Skip` / `Quit` |
| `DirEntry` | struct | yielded entry: `path`, `into_path`, `file_name`, `depth`, `file_type`, `metadata`, `path_is_symlink` |
| `Error` | enum | failure value; `is_partial`, `is_io`, `io_error`, `depth`, `Display` |

### CLI Entry Points

There is no console script for this package. Programmatic use is through
the Rust crate API.

## Appendix A: Environment

- Language: Rust, edition 2021 (toolchain 1.83; the crate's declared
  minimum supported Rust version must not exceed it).
- The crate must build as `ignore` with its default configuration
  providing every behavior described here; the assessment suite depends on
  the crate as `ignore = { version = "*" }`.
- The `globset`, `walkdir`, `same-file`, `crossbeam-deque`, `regex-automata`,
  `log`, `memchr`, and `bstr` crates are available as primitives; the rule
  stack, precedence composition, matchers, and walkers are the deliverable.
- Tests are run with cargo-nextest; each test runs in its own process.
  Tests create their own temporary directory trees; no test depends on a
  pre-existing git installation or user configuration.
- No network access at test time.

## Appendix B: Assessment Notes

The assessment exercises the public API through its documented behavior.
Dimensions covered:

- Pattern dialect: anchoring, name-component matching, directory-only
  rules, `**` spans, negation, comments and escaping, last-match-wins,
  case-insensitive mode.
- Matcher queries: verdict variants and payload provenance, parent-aware
  matching, counters, empty matchers, builder error paths.
- Override and type matchers: inverted polarity, blanket-ignore rule,
  selection and negation, definition formats and validation errors.
- Serial walks over constructed temporary trees: default filters, git
  gating, per-source precedence including whitelist rescue and its
  directory limit, toggles, custom rule files, depth/size limits,
  predicate pruning, sorting.
- Parallel walks: set equality with serial walks, flow-control states.
- Cross-view consistency: the invariants listed above, exercised jointly
  across matchers and walkers on the same fixtures.

Scoring runs the suite against the delivered crate; each test either
passes or fails, and the score is the fraction passed. Tests use fresh
fixture trees and patterns; memorized outputs from any similarly-named
library will not match.
