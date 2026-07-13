# Requirement Map

| Requirement | Public packet section | Rubric IDs |
| --- | --- | --- |
| `REQ-variables` | Variables and Expressions | `MTEU001`, `MTEU002` |
| `REQ-filters` | Variables and Expressions; Environment registry semantics | `MTEU003`, `MTEU013`, `MTES001`, `MTES002`, `MTES003`, `MTES007`, `MTES009`, `MTES011`, `MTES012` |
| `REQ-conditionals` | Conditionals and Tests | `MTEU004`, `MTEU005` |
| `REQ-tests` | Conditionals and Tests; Environment registry semantics | `MTEU005`, `MTEU013`, `MTES003`, `MTES007` |
| `REQ-loops` | Loops and Scoped Variables | `MTEU006`, `MTES004`, `MTES010` |
| `REQ-scope` | Loops and Scoped Variables; Includes, Imports, and Macros | `MTEU007`, `MTES004`, `MTES010` |
| `REQ-blocks` | Blocks and Inheritance | `MTEU008`, `MTES002` |
| `REQ-environment` | Product Model; Environment API | `MTEU009`, `MTES001`, `MTES003`, `MTES009` |
| `REQ-loader-cache` | Environment API; Global Invariants | `MTEU010`, `MTEU018`, `MTES001`, `MTES003`, `MTES006`, `MTES008`, `MTES009`, `MTES012` |
| `REQ-inheritance` | Blocks and Inheritance | `MTEU011`, `MTES002`, `MTES005`, `MTES006`, `MTES007`, `MTES008`, `MTES010` |
| `REQ-include-import` | Includes, Imports, and Macros | `MTEU012`, `MTES001`, `MTES002`, `MTES004`, `MTES005`, `MTES006`, `MTES008`, `MTES011`, `MTES012` |
| `REQ-globals` | Product Model; Environment API | `MTEU009`, `MTES001`, `MTES002`, `MTES004`, `MTES006`, `MTES009`, `MTES011` |
| `REQ-undefined` | Global Invariants; Error Behavior | `MTEU014`, `MTES007`, `MTES010` |
| `REQ-autoescape` | Global Invariants; Variables and Expressions | `MTEU015`, `MTES005`, `MTES011` |
| `REQ-whitespace` | Global Invariants | `MTEU016`, `MTES008` |
| `REQ-errors` | Error Behavior | `MTEU017`, `MTEU018`, `MTES006`, `MTES012` |

## Redesign Note

Canonical fact source: one `Environment` containing loader sources, compiled-template cache, filter/test registries, globals, undefined policy, whitespace trimming behavior, and autoescape policy.

Derived views: standalone `Template` renders, `Environment.from_string()` renders, named `get_template()` renders, parent template renders through inheritance, included template output, imported macro namespaces, registry lookups, and cache state after source replacement or invalidation.

Expected gap mechanism: a function-by-function implementation can satisfy unit rows by adding variables, loops, filters, tests, blocks, includes, or autoescape locally. The system rows require those features to share environment state after mixed lifecycle operations: cache population followed by source replacement, inherited blocks that include other templates, registry mutation after compilation, macro calls with caller values passed explicitly as scoped arguments, undefined policy across direct/include/inherited views, and error recovery without poisoning cache or registries.

Audit risks and mitigations:

- No private-shape trap: tests use only public constructors, public registries, named templates, renders, and documented exceptions.
- No exact-text trap beyond rendered template semantics: expected strings are produced from explicit template sources, not hidden formatting conventions.
- No arbitrary-order trap: outputs are deterministic strings and do not rely on dictionary iteration.
- Whitespace is tested only where trim markers are present and documented.
- Candidate validation is still required; prior candidate scores belong to the old checklist packet and should not be reused as evidence for this redesign.

## Validation Notes

Reference-compatible implementation against lifecycle v2 rubric: 100.00% unit, 100.00% system.

Fresh candidate runs are still needed to measure whether the redesign creates the intended unit-over-system gap. Target acceptance evidence is at least one fresh candidate with unit score exceeding system score by 15 percentage points or more after failure clustering.
