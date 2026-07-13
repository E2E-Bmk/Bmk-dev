# Mini Xit Requirement Map

Public packet: `prd.md`

Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public basis |
| --- | --- | --- |
| `REQ-parse-status` | Parse valid `.xit` checkbox statuses and ignore invalid task lines | Task File Format |
| `REQ-parse-description` | Preserve task text and four-space continuation descriptions | Task File Format |
| `REQ-parse-priority` | Extract `!` priority tokens and normalize priority level | Extracted Fields |
| `REQ-parse-due` | Extract and normalize supported due-date forms | Extracted Fields |
| `REQ-parse-tags` | Extract tag names and optional values | Extracted Fields |
| `REQ-list` | Emit stable JSON task records with deterministic IDs | `list` |
| `REQ-filter` | Compose status, tag, priority, due-on, and due-by filters | `list` |
| `REQ-sort` | Sort by id, priority, or due with deterministic tie-breaking | `list` |
| `REQ-stats` | Report counts by status, priority, file, tags, and due dates | `stats` |
| `REQ-write-add` | Append parseable tasks | `add` |
| `REQ-write-update` | Modify selected tasks without losing other fields | `mark`, `tag`, `untag`, `reschedule` |
| `REQ-move` | Move a task across files while preserving fields | `move` |
| `REQ-error-atomic` | Failed commands modify no files | Error Behavior |
| `REQ-system-invariants` | Parsed records, filters, sorted views, stats, and file state agree | Goal, Commands |

## Unit Coverage

| Test | Feature | Requirement refs |
| --- | --- | --- |
| `XITU001` | status parsing | `REQ-parse-status`, `REQ-list` |
| `XITU002` | invalid task lines ignored | `REQ-parse-status`, `REQ-list` |
| `XITU003` | priority extraction | `REQ-parse-priority`, `REQ-list` |
| `XITU004` | due-date normalization | `REQ-parse-due`, `REQ-list` |
| `XITU005` | tag and value extraction | `REQ-parse-tags`, `REQ-list` |
| `XITU006` | continuation description parsing | `REQ-parse-description`, `REQ-list` |
| `XITU007` | status filter | `REQ-filter` |
| `XITU008` | tag filter intersection | `REQ-filter`, `REQ-parse-tags` |
| `XITU009` | priority-min filter | `REQ-filter`, `REQ-parse-priority` |
| `XITU010` | due-on and due-by filters | `REQ-filter`, `REQ-parse-due` |
| `XITU011` | priority sorting | `REQ-sort`, `REQ-parse-priority` |
| `XITU012` | due sorting | `REQ-sort`, `REQ-parse-due` |
| `XITU013` | stats counts | `REQ-stats` |
| `XITU014` | add writeback | `REQ-write-add`, `REQ-list` |
| `XITU015` | mark writeback | `REQ-write-update`, `REQ-list` |
| `XITU016` | tag and untag writeback | `REQ-write-update`, `REQ-parse-tags` |

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs |
| --- | --- | --- | --- |
| `XITS001` | `cross_feature_dataflow` | parse -> filter -> sort -> stats | `REQ-list`, `REQ-filter`, `REQ-sort`, `REQ-stats`, `REQ-system-invariants` |
| `XITS002` | `writeback_consistency` | add -> list -> stats -> file state | `REQ-write-add`, `REQ-list`, `REQ-stats`, `REQ-system-invariants` |
| `XITS003` | `writeback_consistency` | mark -> filtered list -> stats -> file state | `REQ-write-update`, `REQ-filter`, `REQ-stats`, `REQ-system-invariants` |
| `XITS004` | `derived_view_consistency` | tag/untag -> tag filters -> stats | `REQ-write-update`, `REQ-filter`, `REQ-stats`, `REQ-system-invariants` |
| `XITS005` | `operation_order_sensitivity` | reschedule -> due filter -> due sort -> file state | `REQ-write-update`, `REQ-filter`, `REQ-sort`, `REQ-system-invariants` |
| `XITS006` | `cross_file_consistency` | move -> source list -> target list -> multi-file stats | `REQ-move`, `REQ-list`, `REQ-stats`, `REQ-system-invariants` |
| `XITS007` | `stable_identity` | multi-file id assignment -> move by id -> relist | `REQ-list`, `REQ-move`, `REQ-system-invariants` |
| `XITS008` | `roundtrip_preservation` | continuation parse -> mark -> move -> parse | `REQ-parse-description`, `REQ-write-update`, `REQ-move` |
| `XITS009` | `date_lifecycle` | add/reschedule normalized dates -> filters/stats | `REQ-parse-due`, `REQ-write-add`, `REQ-write-update`, `REQ-filter`, `REQ-stats` |
| `XITS010` | `error_atomicity` | invalid update -> list/stats/file unchanged | `REQ-error-atomic`, `REQ-list`, `REQ-stats` |
| `XITS011` | `global_invariant` | mixed filters over same parsed state -> stats unchanged | `REQ-filter`, `REQ-stats`, `REQ-system-invariants` |
| `XITS012` | `roundtrip_preservation` | multiple writes -> parse -> sorted/filter views | `REQ-write-add`, `REQ-write-update`, `REQ-sort`, `REQ-filter`, `REQ-system-invariants` |

## Fairness Notes

- Tests use only CLI output, exit code, and `.xit` file contents explicitly
  defined by the PRD.
- The rubric must not inspect internal parser classes, caches, repository
  singletons, Rich formatting, Click callbacks, or source module names.
- Date behavior uses fixed literal dates only; natural-language dates and
  current-day behavior are out of scope.
- JSON object ordering must not matter to a scorer; array order matters only
  where the PRD defines sorting.
