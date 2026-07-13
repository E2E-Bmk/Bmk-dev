# XitKit Source Repository Notes

Canonical source repository:
`https://github.com/hoechstleistungshaartrockner/xitkit`

Checked source revision: `2fd55de` on branch `main`.

Local analysis checkout:
`/Users/nixer/项目/benchmark-source-repos/xitkit`

Local paths above are analysis context only. Source evidence below cites
repository-relative paths at commit `2fd55de`.

## Source Summary

XitKit is a command-line task manager for `.xit` and `.md` files using the
`[x]it!` task format. The README describes multiple task states, priority
levels, due dates, tags, multi-line descriptions, groups/headers, filtering,
statistics, batch operations, recurring tasks, and move/write commands
(`README.md:3`, `README.md:7`, `README.md:67`).

The source CLI exposes `show`, `stats`, `add`, `mark`, `move`, `prio`,
`reschedule`, `tag`, and `untag` behavior through Click commands
(`xitkit/__main__.py:49`, `xitkit/__main__.py:164`). The mini-task intentionally
uses a smaller deterministic CLI surface while preserving the source-derived
task parsing, filtering, sorting, stats, writeback, and movement behaviors.

## Source Capability Map

| Capability | Source signal | Mini-task use |
| --- | --- | --- |
| Task syntax and parser behavior | The syntax guide defines valid/invalid checkbox forms, mandatory separators, continuation indentation, priority syntax, due-date syntax, and tag/value syntax (`syntax_guide.txt:4`, `syntax_guide.txt:50`, `syntax_guide.txt:92`, `syntax_guide.txt:129`, `syntax_guide.txt:183`). The parser states it supports statuses, priorities, due dates, tags, multi-line descriptions, and UTF-8 text (`xitkit/fileparser.py:258`). | PRD defines a deterministic `.xit` subset with the same public syntax families. |
| Status extraction | Status characters map to open, checked, ongoing, obsolete, and in-question states (`xitkit/fileparser.py:277`). | PRD exposes `open`, `done`, `ongoing`, `obsolete`, and `question`. |
| Priority extraction | README documents priority indicators using `!`, `!!`, and `!!!` (`README.md:7`). The syntax guide defines priority padding and invalid dot placement (`syntax_guide.txt:92`). | PRD extracts priority as count of `!` and clarifies valid padded tokens. |
| Due-date extraction | README lists flexible due date parsing (`README.md:7`). The syntax guide defines day, month, year, week, quarter, slash delimiter, and invalid mixed delimiter forms (`syntax_guide.txt:129`). | PRD keeps fixed literal date forms and excludes natural-language dates for determinism. |
| Tag extraction | README lists tags as a feature (`README.md:7`). The syntax guide defines unicode tag names, tag values, quoted values, empty values, and invalid missing-value cases (`syntax_guide.txt:183`). | PRD exposes tag parsing plus deterministic CLI tag arguments. |
| Continuation lines | README lists multi-line descriptions (`README.md:7`). The syntax guide requires exactly four-space continuation indentation (`syntax_guide.txt:50`). The parser main loop handles continuation lines (`xitkit/fileparser.py:431`). | PRD requires exactly four-space continuation parsing and writeback preservation. |
| Task ID assignment | The file repository tracks an incrementing current ID and task map (`xitkit/file_repository.py:14`). CLI examples use task IDs for mark, move, reschedule, tag, and untag operations (`README.md:95`). | PRD adapts this into deterministic IDs assigned from 1 by supplied file order and line order. |
| Filtering | The CLI `show` command supports status, priority, tag, due-on, due-by, file, sort, and order options (`xitkit/__main__.py:49`). `TaskFilter` carries status, priority, tags, due-on, and due-by (`xitkit/services.py:25`), and filtering applies those fields (`xitkit/services.py:68`). | PRD exposes intersecting filters through `list`. |
| Sorting | The CLI exposes `--sort priority|due_date` and `--order asc|desc` (`xitkit/__main__.py:73`). Service sorting supports priority and due-date order (`xitkit/services.py:166`). | PRD exposes deterministic `id`, `priority`, and `due` sorting with tie-breaks. |
| Stats | The CLI has a `stats` command (`xitkit/__main__.py:164`). The service counts total tasks, status, priority, file, tags, due dates, and overdue tasks (`xitkit/services.py:110`). | PRD exposes deterministic stats excluding current-date overdue behavior. |
| Add/writeback | README documents `add` examples (`README.md:91`). File repository supports adding tasks to files (`xitkit/file_repository.py:155`). | PRD exposes `add` as canonical parseable writeback. |
| Mark/writeback | README documents `mark` examples for done, ongoing, obsolete, and open (`README.md:95`). Task serialization writes checkbox format (`xitkit/task.py:471`). | PRD exposes `mark` and requires preserving task fields. |
| Tag/untag writeback | README documents `tag` and `untag` commands (`README.md:123`). | PRD exposes deterministic tag mutation and writeback. |
| Reschedule writeback | README documents `reschedule` (`README.md:101`). | PRD exposes deterministic due-date replacement. |
| Cross-file move | README documents moving tasks between files (`README.md:111`). | PRD exposes `move --from FILE --to FILE ID`. |
| Round-trip writeback | Source tests check parse -> checkbox format -> parse preservation (`tests/test_integration.py:203`). Task serialization writes checkbox format (`xitkit/task.py:471`). | PRD requires writeback operations to preserve task fields and continuation lines. |
| Error behavior and atomicity | Source parser validates supported file types (`xitkit/fileparser.py:291`). Writeback is explicit through file repository and task serialization (`xitkit/file_repository.py:76`, `xitkit/task.py:471`). | PRD adapts this into a strict benchmark rule: failed commands modify no files. |

## PRD Reconciliation

| PRD behavior | Source grounding | Classification |
| --- | --- | --- |
| `.xit` task parsing | Source parses `.xit` and `.md`; mini-task keeps only `.xit` for determinism (`xitkit/fileparser.py:291`). | A / B: source-derived, narrowed adaptation |
| Five public statuses | Source status map contains five checkbox states (`xitkit/fileparser.py:277`). | A |
| Invalid task lines ignored | Source parser skips invalid lines rather than raising (`xitkit/fileparser.py:258`). | A |
| Four-space continuation lines | Syntax guide and parser define continuation behavior (`syntax_guide.txt:50`, `xitkit/fileparser.py:431`). | A |
| Priority extraction and padded tokens | Syntax guide defines valid/invalid priority tokens (`syntax_guide.txt:92`). | A |
| Due date normalization | Syntax guide defines day/month/year/week/quarter forms (`syntax_guide.txt:129`). Mini-task fixes deterministic ISO-week and no natural language. | A / B |
| Unicode tags and values | Syntax guide defines unicode tags and values (`syntax_guide.txt:183`). | A |
| JSON output | Source uses Rich terminal output; benchmark uses JSON for stable scoring. | B |
| Deterministic task IDs by supplied file order and line order | Source has repository ID assignment (`xitkit/file_repository.py:14`), but deterministic cross-process ordering is a mini-task adaptation for stable tests. | B |
| `list` filters | Source `show` filters by status, priority, tags, due-on, and due-by (`xitkit/__main__.py:49`, `xitkit/services.py:68`). | A |
| Sorting with tie-break by ID | Source sorts by priority/due date (`xitkit/services.py:166`); explicit ID tie-break is benchmark determinism. | A / B |
| Stats excluding overdue | Source stats include more fields including overdue (`xitkit/services.py:110`); mini-task removes current-date-dependent overdue. | B |
| Canonical writeback order | Source serializes task lines (`xitkit/task.py:471`); exact canonical order is a deterministic mini-task scoring adaptation. | B |
| Add/mark/tag/untag/reschedule | Source README documents these commands (`README.md:91`, `README.md:95`, `README.md:101`, `README.md:123`). | A |
| Cross-file move | Source README documents move (`README.md:111`). | A |
| Round-trip parse/write preservation | Source tests exercise parse -> serialize -> parse behavior (`tests/test_integration.py:203`). | A |
| Failed commands modify no files | Source has error paths but benchmark makes atomicity explicit for fair system testing. | B |
| Rich output, Click internals, interactive mode, recurrence, pomodoro | Excluded from PRD. | C: unsupported for this mini-task |

Classification:

- A: directly source-derived public behavior.
- B: deterministic mini-task adaptation of source behavior.
- C: unsupported or intentionally removed from the mini-task.

## Current Source-Grounding Status

The xitkit handoff is source-faithful in behavior family and deliberately
deterministic where the original project has UI, cache, current-date, or
implementation-specific behavior. The main residual risk is task ID semantics:
source IDs are repository-managed, while the PRD defines stable IDs by supplied
file order and line order. This is an intentional benchmark adaptation and must
remain explicit in the PRD and rubric.
