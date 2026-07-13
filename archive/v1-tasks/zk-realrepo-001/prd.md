# MiniZK Unit/System Public Packet

## Overview

Build `zmini.py`, a compact command line note-taking assistant for a Markdown notebook. It should support the core workflows of a plain-text Zettelkasten: initialize a notebook, create notes, parse metadata, derive tags and links, list/filter/sort notes, list tags, apply small config defaults, and export a note-link graph.

This task is designed around the distinction between local feature correctness and system correctness. Individual commands should work on their own, but the product is only complete if notebook discovery, note files, parsed metadata, filters, tags, links, graph edges, config defaults, and failure behavior remain consistent across workflows.

The implementation language is Python 3.11. Place `zmini.py` at the root of your solution directory. It must run as:

```console
py -3.11 zmini.py [global flags] <command> [command flags]
```

Data-returning JSON commands must print JSON to stdout. Path/title formats should print one record per line. Failed commands must exit non-zero and print a useful message to stderr. The benchmark does not inspect private implementation details.

## Feature Set

The product has eight feature modules:

1. Notebook lifecycle and discovery.
2. Note creation.
3. Note parsing.
4. Tag parsing, tag filtering, and tag listing.
5. Link resolution and graph export.
6. List filtering, output formats, and sorting.
7. Config defaults and named filters.
8. Error and atomicity behavior.

These modules are intentionally state-dependent. Created note files are later parsed; parsed tags and links feed list filters, tag counts, and graph edges; config changes affect note creation and named filters; graph output and backlink/orphan queries must reflect the same parsed notebook state.

## Global Invariants

The following invariants define system correctness:

- Commands must resolve the same notebook root for a given current directory, `ZK_NOTEBOOK_DIR`, or `--notebook-dir` flag. The global flag has priority over the environment variable.
- Notes under `.zk` are control files and must not appear as user notes.
- Note path outputs should be relative to the notebook root.
- A note's title, tags, links, and word count should be derived consistently wherever the note appears.
- Tag counts must match the set of notes selected from all supported tag syntaxes.
- Link filters, backlink filters, missing-backlink detection, orphan detection, and graph edges must agree on the same resolved link graph.
- Graph edges should only connect selected graph nodes.
- Filtering, sorting, tag listing, and graph export must not mutate notes.
- Duplicate note creation and invalid filters must fail without overwriting or corrupting existing notes.

## Notebook Model

A notebook is a directory containing a `.zk` directory. `zmini.py init [DIR]` creates:

- `DIR/.zk/`
- `DIR/.zk/config.toml`
- `DIR/.zk/templates/`

Commands should find the notebook containing the current working directory by walking upward until `.zk` is found. Users may also set the notebook explicitly with:

- `--notebook-dir DIR`
- `ZK_NOTEBOOK_DIR`

The global flag has priority over the environment variable. Re-running `init` on an existing notebook should not destroy notes.

## Notes

Notes are Markdown files under the notebook root, excluding `.zk`. A note may have:

- a title from YAML frontmatter `title`, otherwise the first Markdown `# Heading`, otherwise the filename stem;
- tags from YAML `tags` or `keywords`, inline `#hashtags`, and colon tags like `:project/research:`;
- links from Markdown links `[text](path.md)` and wiki links `[[path-or-title]]`.

Wiki links should resolve by exact path, filename stem, ID-like prefix, or parsed title where practical. If no note matches, keep the unresolved target string in parsed link data.

## Commands

### `init [DIR]`

Create a notebook. If `DIR` is omitted, initialize the current directory.

### `new`

Create a note.

Supported flags:

- `--title TITLE`: note title.
- `--id ID`: use a provided ID prefix instead of generating one.
- `--dir DIR`: create the note under a subdirectory.
- `--filename NAME`: use an explicit filename.
- `--print-path`: print the created path.
- `--interactive`: read initial body content from stdin.

Default filename should be deterministic: combine ID if supplied, otherwise a generated prefix, with a slugified title and `.md`. If a config filename template is present, render `{{id}}` and `{{slug title}}`. Duplicate output paths must fail without overwriting the existing file.

### `list`

List notes matching filters.

Supported flags:

- `--format short|json|jsonl|path|title`
- `--match QUERY`, repeatable; all matches must hold.
- `--match-strategy exact|re`
- `--tag EXPR`
- `--link-to PATH_OR_ID`
- `--linked-by PATH_OR_ID`
- `--recursive`
- `--max-distance N`
- `--orphan`
- `--missing-backlink`
- `--exclude PATH`, repeatable.
- `--limit N`
- `--sort path|title|created|modified|word-count`, with optional `+` or `-` suffix.
- `--filter NAME`, applying a named config filter.

JSON note objects should include at least `path`, `title`, `tags`, `links`, and `word_count`.

Tag expressions should support practical AND via comma/space, OR via `OR` or `|`, and negation via `NOT` or `-`.

### `tag list`

List tags discovered in the notebook.

Supported flags:

- `--format name|json`
- `--sort name|note-count`, with optional `+` or `-` suffix.

JSON tag objects should include `name` and `note_count`.

### `graph`

Export note-link graph data.

Supported flags:

- `--format json`
- the same path, match, tag, exclude, and named-filter options as `list`

JSON graph output should include `nodes` and `edges`, where each node has `path` and `title`, and each edge has `source` and `target`.

## Config

Read `.zk/config.toml` when present. Keep the supported subset small:

```toml
[note]
default_title = "Untitled"
filename = "{{id}}-{{slug title}}"

[format.markdown]
hashtags = true
colon_tags = true

[filter.work]
tag = "work"
exclude = "archive"
```

Config may define defaults for note title/filename and named filters. A named filter can be applied with `--filter NAME` on `list` or `graph`.

## Error Behavior

Missing notebooks, invalid regexes, invalid commands, missing linked targets when a command requires a concrete target, and duplicate output paths should fail with a non-zero exit code and useful stderr. Ordinary filters with no matches should succeed with empty output.

Failed commands must not corrupt existing notes, config files, parsed notebook state, tag counts, or graph relationships.

## Non-Goals

- No editor integration, LSP, fzf, pager, shell helpers, or SQLite database is required.
- No exact reproduction of original `zk` terminal styling is required.
- No natural-language date parsing is required.
- No full Handlebars template engine is required; only the compact filename/title behavior above is in scope.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time. When a command needs existing notebook state, tests create Markdown files and config directly instead of invoking other product commands.
- System tests exercise interactions across at least two feature modules. They inspect files, stdout/stderr, JSON outputs, tag/link relationships, graph consistency, config behavior, and failed-command atomicity.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
