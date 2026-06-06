# Source Repository

## Identity

- Repository: `zk-org/zk`
- URL: https://github.com/zk-org/zk
- Pinned commit: `10d93d5d6419941420e7775d409e530a7de59cbc`
- Local checkout: `G:/research/swe-e2e/sources/zk-org__zk`
- Source language: Go
- Benchmark case: `zk-realrepo-001`

## Public Evidence Used

- `README.md`: product narrative, command-line note-taking assistant, links, tags, templates, search/filtering, automation focus.
- `docs/notes/notebook.md`: notebook identity via `.zk`, config/templates/db anatomy, notebook discovery.
- `docs/notes/note-creation.md`: `zk new`, title/content, automation-friendly path output, stdin initial content.
- `docs/notes/note-filtering.md`: path filters, match strategies, tags, link/backlink exploration, related/mentions, excludes, limits, sort.
- `docs/notes/tags.md`: supported tag syntaxes and tag listing.
- `docs/notes/template.md`: template helpers and JSON formatting concepts.
- `tests/*.tesh`: broad command examples for init, new, list, tag, graph, config, filters, links, formats, and edge cases.
- ProgramBench sample metadata under `samples/ProgramBench/zk-org__zk.10d93d5`: behavior category inspiration, not direct rubric import.

## Reconstruction Boundary

The candidate does not rebuild the Go application or SQLite-backed implementation. The benchmark will ask for a compact Python 3.11 CLI named `zmini.py` that manages Markdown note files in a notebook directory. Hidden scoring should evaluate user-visible lifecycle behavior: initializing notebooks, creating notes, parsing metadata/tags/links, listing/filtering notes, generating graph JSON, and maintaining deterministic outputs.

## Why This Case

This is likely a stronger target-band candidate than `htmlq` because useful behavior crosses durable state and derived relationships:

- filesystem notebook initialization and discovery;
- note creation with generated filenames and templates;
- Markdown/YAML-frontmatter parsing;
- multiple tag syntaxes;
- links, backlinks, recursive traversal, and missing backlink detection;
- list/tag/graph output formats;
- config-driven defaults and path filtering.

The fairness risk is scope. The public packet should define a compact but realistic subset instead of asking for full `zk`. Hidden rubrics should compose stateful workflows without relying on exact original `zk` formatting, SQLite internals, editor integration, LSP behavior, or fuzzy interactive tools.
