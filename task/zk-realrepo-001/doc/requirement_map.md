# MiniZK Unit/System Requirement Map

Date: 2026-06-03

Public packet: `candidate_task_unit_system/public_packet.md`

Rubric: `scoring/rubrics_unit_system_v1.json`

Scorer: `scoring/score_zmini.py`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-feature-set` | Bounded 8-module feature set | Feature Set | Notebook, note creation/parsing, tags, links/graph, list/filter/sort, config, errors |
| `REQ-global-invariants` | Cross-feature notebook invariants | Global Invariants | Discovery, parsed metadata, tag counts, link graph, graph node/edge consistency, failure safety |
| `REQ-notebook` | Notebook lifecycle and discovery | Notebook Model | `init` creates `.zk`; commands discover notebook via cwd, env, or global flag |
| `REQ-new-note` | Note creation | `new` | Creates deterministic Markdown files from title/id/dir/filename/stdin without overwriting duplicates |
| `REQ-note-parse` | Title/body/word-count parsing | Notes | Frontmatter title, heading fallback, filename fallback, and word count are exposed in note objects |
| `REQ-tags` | Tag parsing/filtering/listing | Notes, `list`, `tag list` | YAML tags/keywords, hashtags, colon tags, tag expressions, and tag counts |
| `REQ-links-graph` | Link resolution and graph export | Notes, `list`, `graph` | Markdown/wiki links resolve by path/stem/id/title and feed filters and graph edges |
| `REQ-list-filters` | List filters, output formats, sorting | `list` | Match, regex, tags, link filters, exclude, limit, sort, path/title/JSON outputs |
| `REQ-config` | Config defaults and named filters | Config | Note defaults/templates and named filters affect `new`, `list`, and `graph` |
| `REQ-errors` | Error and atomicity behavior | Error Behavior | Missing notebooks, invalid regexes, duplicates, and invalid commands fail nonzero without corrupting state |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit cases test one module with direct notebook/file/config setup |
| `REQ-system-eval` | System testing definition | Evaluation Style | System cases cross at least two modules and carry `system_dimension` labels |

## Unit Coverage

| Feature module | Unit tests | Requirement refs | Public basis |
| --- | --- | --- | --- |
| Notebook lifecycle/discovery | `ZKU001`, `ZKU002` | `REQ-notebook` | Init creates control files; cwd/env/global flag discovery works with precedence |
| Note creation | `ZKU003`, `ZKU004` | `REQ-new-note`, `REQ-errors` | Explicit note creation and duplicate-path non-overwrite behavior |
| Note parsing | `ZKU005`, `ZKU006` | `REQ-note-parse`, `REQ-tags`, `REQ-links-graph` | Frontmatter, headings, tags, links, and word count appear in JSON note objects |
| Tag semantics | `ZKU007`, `ZKU008` | `REQ-tags`, `REQ-list-filters` | Tag sources, tag counts, and OR/NOT tag filters |
| Link and graph semantics | `ZKU009`, `ZKU010`, `ZKU014` | `REQ-links-graph`, `REQ-list-filters` | Direct link filters, recursive traversal, graph nodes and edges |
| List filtering/sorting | `ZKU011`, `ZKU012`, `ZKU013` | `REQ-list-filters`, `REQ-note-parse` | Match/exclude/limit and path/word-count sorting |
| Config | `ZKU017`, `ZKU018` | `REQ-config`, `REQ-list-filters`, `REQ-new-note` | Named filters and note filename/title defaults |
| Errors | `ZKU015`, `ZKU016` | `REQ-errors` | Invalid regex and missing notebook fail nonzero with useful stderr |

Unit requirement coverage:

- `REQ-notebook`: `ZKU001`, `ZKU002`
- `REQ-new-note`: `ZKU003`, `ZKU004`, `ZKU018`
- `REQ-note-parse`: `ZKU005`, `ZKU006`, `ZKU013`
- `REQ-tags`: `ZKU005`, `ZKU007`, `ZKU008`
- `REQ-links-graph`: `ZKU005`, `ZKU009`, `ZKU010`, `ZKU014`
- `REQ-list-filters`: `ZKU008`, `ZKU010`, `ZKU011`, `ZKU012`, `ZKU013`, `ZKU017`
- `REQ-config`: `ZKU017`, `ZKU018`
- `REQ-errors`: `ZKU004`, `ZKU015`, `ZKU016`

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `ZKS001` | `cross_feature_dataflow` | new -> tag list -> graph | `REQ-new-note`, `REQ-tags`, `REQ-links-graph` | Created notes become parsed tag and graph state |
| `ZKS002` | `boundary_crossing` | tags -> list filters -> graph filters | `REQ-tags`, `REQ-list-filters`, `REQ-links-graph` | Frontmatter/hashtags/colon tags and OR/NOT filters compose with graph selection |
| `ZKS003` | `global_invariant` | link traversal -> orphan/missing-backlink -> graph | `REQ-links-graph`, `REQ-list-filters`, `REQ-global-invariants` | Link filters and graph outputs agree on one resolved link graph |
| `ZKS004` | `state_accumulation` | config -> excludes -> recursive links | `REQ-config`, `REQ-list-filters`, `REQ-links-graph` | Named filters and transitive link traversal compose over persisted files |
| `ZKS005` | `boundary_crossing` | new -> parsing -> filtering -> sorting | `REQ-new-note`, `REQ-note-parse`, `REQ-list-filters` | Created notes with different bodies are filtered and sorted by parsed word count |
| `ZKS006` | `error_atomicity` | new -> duplicate failure -> graph | `REQ-new-note`, `REQ-errors`, `REQ-links-graph` | Duplicate creation fails without damaging existing graph state |
| `ZKS007` | `cross_feature_dataflow` | parsing -> wiki title resolution -> graph | `REQ-note-parse`, `REQ-links-graph` | Parsed titles feed wiki-link resolution and graph edges |
| `ZKS008` | `global_invariant` | tags -> tag counts -> note-count sort | `REQ-tags`, `REQ-list-filters`, `REQ-global-invariants` | Tag counts and sorting reflect all parsed tag sources |
| `ZKS009` | `state_accumulation` | notebook precedence -> config -> list | `REQ-notebook`, `REQ-config`, `REQ-list-filters` | Notebook selection and named filters choose the correct persisted state |
| `ZKS010` | `boundary_crossing` | regex -> tag expr -> exclude -> limit -> sort | `REQ-tags`, `REQ-list-filters` | Multiple nontrivial list-filter boundaries compose in one output |
| `ZKS011` | `operation_order_sensitivity` | new source -> new target -> list/graph | `REQ-new-note`, `REQ-note-parse`, `REQ-links-graph`, `REQ-list-filters` | Wiki links created before their target resolve against the later complete notebook state |
| `ZKS012` | `operation_order_sensitivity` | tags -> sort -> limit | `REQ-tags`, `REQ-list-filters`, `REQ-note-parse` | Limit is applied after final title sorting, not before |

System dimension coverage:

- `cross_feature_dataflow`: `ZKS001`, `ZKS007`
- `state_accumulation`: `ZKS004`, `ZKS009`
- `global_invariant`: `ZKS003`, `ZKS008`
- `error_atomicity`: `ZKS006`
- `boundary_crossing`: `ZKS002`, `ZKS005`, `ZKS010`
- `operation_order_sensitivity`: `ZKS011`, `ZKS012`

The v1 ZK system set now covers all 6 requested system dimensions. The operation-order cases focus on final notebook state and filter-pipeline order, both visible from the public packet.

## Reference And Model Verification

| Solution | Unit | System | Gap | Report |
| --- | ---: | ---: | ---: | --- |
| Reference | 100.00% | 100.00% | 0.00pp | `score_report_reference_unit_system_v1.json` |
| Codex subagent | 83.33% | 58.33% | 25.00pp | `score_report_codex_subagent_001_unit_system_v1.json` |
| OpenHands + DeepSeek V4 Pro | 83.33% | 41.67% | 41.67pp | `score_report_openhands_deepseek_v4_pro_001_unit_system_v1.json` |

## Fairness Notes

- The scorer now creates temporary notebooks under the run directory rather than the OS Temp directory, because the local Temp parent contained a `.zk` folder that could make missing-notebook tests falsely pass.
- Invalid-regex stderr matching accepts both explicit `regex`/`pattern`/`invalid` wording and Python's useful `unterminated character set` message.
- Config has direct unit coverage in v1 through `ZKU017` and `ZKU018`, so the public `Config` section is not tested only at system level.
- ZK v1 meets the revised unit/system claim for this task: two non-reference candidate runs show unit scores in the 70-90% target band and system scores at least 23.33pp lower.
