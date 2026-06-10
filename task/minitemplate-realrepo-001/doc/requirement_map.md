# MiniTemplate Unit/System Requirement Map

Date: 2026-06-06

Public packet: `prd.md`

Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-feature-set` | Bounded 7-module feature set | Feature Set | Variables, conditionals, loops, filters, includes, comments, errors |
| `REQ-global-invariants` | Cross-feature template invariants | Global Invariants | Variable scoping, dot notation resolution, filter pipeline order, loop shadowing, include context sharing, comment stripping, error isolation |
| `REQ-variables` | Variable substitution | `{{ var }}`, `{{ obj.key }}`, `{{ seq[0] }}` | Simple interpolation, dot notation with dict/obj precedence, index access |
| `REQ-conditionals` | Conditional blocks | `{% if %}`, `{% elif %}`, `{% else %}`, `{% endif %}` | Truthiness-based branching, elif chains, undefined vars treated as falsy |
| `REQ-loops` | Loop blocks | `{% for item in seq %}` / `{% endfor %}`, `loop.index`, `loop.index0` | Iteration over sequences, loop.index (1-based) and loop.index0 (0-based), variable shadowing |
| `REQ-filters` | Built-in and custom filters | `| upper`, `| lower`, `| default`, `| length`, `| trim`, `env.add_filter()` | Transform values in pipeline; custom filters override built-ins; left-to-right application |
| `REQ-includes` | Template includes | `{% include "name" %}` | Sub-template rendered with parent context; resolved via env loader dict; circular detection |
| `REQ-comments` | Comment handling | `{# ... #}` | Comments stripped from output entirely |
| `REQ-errors` | Error handling | `UndefinedError`, `TemplateSyntaxError`, `IncludeError` | Undefined vars raise; syntax errors at parse time raise; missing/circular includes raise; errors don't corrupt |
| `REQ-unit-eval` | Unit testing definition | Evaluation Style | Unit cases test one module with short Python snippets |
| `REQ-system-eval` | System testing definition | Evaluation Style | System cases cross at least two modules and carry `system_dimension` labels |

## Unit Coverage

| Feature module | Unit tests | Requirement refs | Public basis |
| --- | --- | --- | --- |
| Variables | `MTEU001`, `MTEU002`, `MTEU003` | `REQ-variables` | Simple substitution, dot notation, index access |
| Conditionals | `MTEU004`, `MTEU005`, `MTEU006` | `REQ-conditionals` | If with truthy/falsy, if/else, elif chain |
| Loops | `MTEU007`, `MTEU008` | `REQ-loops` | For loop over list, loop.index/loop.index0 |
| Filters | `MTEU009`, `MTEU010`, `MTEU011`, `MTEU012`, `MTEU018` | `REQ-filters` | upper, lower, chain, default, length, trim, custom filter |
| Includes | `MTEU013` | `REQ-includes` | Include with env loader sharing context |
| Comments | `MTEU014` | `REQ-comments` | Comment stripping |
| Errors | `MTEU015`, `MTEU016`, `MTEU017` | `REQ-errors`, `REQ-includes` | UndefinedError subclass, TemplateSyntaxError subclass, IncludeError subclass |

Unit requirement coverage:

- `REQ-variables`: `MTEU001`, `MTEU002`, `MTEU003`
- `REQ-conditionals`: `MTEU004`, `MTEU005`, `MTEU006`
- `REQ-loops`: `MTEU007`, `MTEU008`
- `REQ-filters`: `MTEU009`, `MTEU010`, `MTEU011`, `MTEU012`, `MTEU018`
- `REQ-includes`: `MTEU013`, `MTEU017`
- `REQ-comments`: `MTEU014`
- `REQ-errors`: `MTEU015`, `MTEU016`, `MTEU017`

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `MTES001` | `cross_feature_dataflow` | loops → filters → conditionals | `REQ-loops`, `REQ-filters`, `REQ-conditionals` | Loop values flow through filters then conditionals gate output |
| `MTES002` | `cross_feature_dataflow` | includes → filters → variables | `REQ-includes`, `REQ-filters`, `REQ-variables` | Include receives context; filter applied to context var in parent |
| `MTES003` | `state_accumulation` | conditionals → loops → variables | `REQ-conditionals`, `REQ-loops`, `REQ-variables` | Nested blocks accumulate; parent context var available inside loop when not shadowed |
| `MTES004` | `state_accumulation` | includes → variables (chained) | `REQ-includes`, `REQ-variables` | Chained includes (A→B→C) accumulate output with shared context |
| `MTES005` | `global_invariant` | loops → variables | `REQ-loops`, `REQ-variables` | Loop var shadows outer; outer restored after loop ends |
| `MTES006` | `global_invariant` | variables → conditionals → loops | `REQ-variables`, `REQ-conditionals`, `REQ-loops` | Independent renders produce independent correct output |
| `MTES007` | `error_atomicity` | includes → errors → variables | `REQ-includes`, `REQ-errors`, `REQ-variables` | Failed include doesn't corrupt Environment for later valid renders |
| `MTES008` | `error_atomicity` | loops → variables → errors | `REQ-loops`, `REQ-variables`, `REQ-errors` | Undefined var error in one render doesn't corrupt Template for later render |
| `MTES009` | `operation_order_sensitivity` | filters → variables | `REQ-filters`, `REQ-variables` | upper\|lower ≠ lower\|upper on mixed-case input |
| `MTES010` | `operation_order_sensitivity` | includes → variables | `REQ-includes`, `REQ-variables` | Include order within parent determines output position |
| `MTES011` | `boundary_crossing` | loops → includes → filters → conditionals | `REQ-loops`, `REQ-includes`, `REQ-filters`, `REQ-conditionals` | For→include→custom filter→if compose; all four modules cooperate |
| `MTES012` | `boundary_crossing` | comments → loops → filters → conditionals | `REQ-comments`, `REQ-loops`, `REQ-filters`, `REQ-conditionals` | Comments stripped in all positions: inside for, before if, after if |

System dimension coverage:

- `cross_feature_dataflow`: `MTES001`, `MTES002`
- `state_accumulation`: `MTES003`, `MTES004`
- `global_invariant`: `MTES005`, `MTES006`
- `error_atomicity`: `MTES007`, `MTES008`
- `operation_order_sensitivity`: `MTES009`, `MTES010`
- `boundary_crossing`: `MTES011`, `MTES012`

All 6 required system dimensions are covered with 2 tests each.

## Verification Targets

| Solution | Unit (target) | System (target) | Gap (target) |
| --- | ---: | ---: | ---: |
| Reference | 100.00% | 100.00% | 0.00pp |
| Candidate (expected) | 70-90% | 40-70% | 15-50pp |

Unit score target band: 70-90% (18 unit cases × weight 4 = 72 total). System gap target: ≥15pp below unit.

## Fairness Notes

- Template syntax deliberately uses Jinja2-compatible delimiters (`{{ }}`, `{% %}`, `{# #}`) to leverage models' pre-training familiarity. The benchmark tests behavioral correctness, not syntax recognition.
- Error types (UndefinedError, TemplateSyntaxError, IncludeError) have explicit subclass relationships to Python builtins (NameError, ValueError, LookupError) to allow partial-credit evaluation.
- Undefined variables in `{% if %}` conditions are treated as falsy (not errors), matching Jinja2's behavior and documented in the public packet. This prevents condition-heavy templates from being unnecessarily fragile.
- No template inheritance (`{% extends %}`) is required, keeping the parser complexity manageable. The feature set focuses on composition (includes, filters, loops, conditionals) rather than OOP-style template design.
- The Environment loader is always an in-memory dict, not a filesystem. This eliminates platform-dependent path resolution from the evaluation.
- All test_code snippets use `print()` for output; the scorer compares against `expected_output` as a plain string. Whitespace in output is significant and must match exactly.
