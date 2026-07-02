# Gate D Audit - cookiecutter-fullrepro-001

## Step 0 - Data Collection

H2/H3 sections:
- Product Overview
- Non-Goals
- Public Interfaces
- CLI
- Python API
- Public Modules
- Template Structure
- cookiecutter.json Variable Types
- String Variables
- Choice Variables
- Boolean Variables
- Dictionary Variables
- Private Variables (Single Underscore Prefix)
- Private Rendered Variables (Double Underscore Prefix)
- `__prompts__` Key
- Templated Default Values
- `_copy_without_render` Key
- `_extensions` Key
- `templates` Key (Nested Config, v2.5+)
- `template` Key (Nested Config, v2.2 Old Format)
- Context Building Pipeline
- Rendering and File Generation
- Hooks
- Replay
- User Configuration
- Template Directories and Archives
- `--directory` Option
- Zip Archives
- Password-Protected Zip Files
- Built-in Template Extensions
- `cookiecutter.extensions.JsonifyExtension`
- `cookiecutter.extensions.RandomStringExtension`
- `cookiecutter.extensions.SlugifyExtension`
- `cookiecutter.extensions.TimeExtension`
- `cookiecutter.extensions.UUIDExtension`
- Custom Extensions via `_extensions`
- Local Extensions
- Exceptions
- Logging
- Cross-View Invariants
- Evaluation Notes

Covered counts by section:
- Product Overview: 0
- Non-Goals: 0
- Public Interfaces: 1
- CLI: 35
- Python API: 4
- Public Modules: 6
- Template Structure: 3
- cookiecutter.json Variable Types: 3
- String Variables: 8
- Choice Variables: 8
- Boolean Variables: 2
- Dictionary Variables: 9
- Private Variables (Single Underscore Prefix): 1
- Private Rendered Variables (Double Underscore Prefix): 2
- `__prompts__` Key: 17
- Templated Default Values: 1
- `_copy_without_render` Key: 1
- `_extensions` Key: 2
- `templates` Key (Nested Config, v2.5+): 2
- `template` Key (Nested Config, v2.2 Old Format): 1
- Context Building Pipeline: 18
- Rendering and File Generation: 37
- Hooks: 25
- Replay: 1
- User Configuration: 13
- Template Directories and Archives: 4
- `--directory` Option: 1
- Zip Archives: 1
- Password-Protected Zip Files: 1
- Built-in Template Extensions: 3
- `cookiecutter.extensions.JsonifyExtension`: 1
- `cookiecutter.extensions.RandomStringExtension`: 1
- `cookiecutter.extensions.SlugifyExtension`: 1
- `cookiecutter.extensions.TimeExtension`: 8
- `cookiecutter.extensions.UUIDExtension`: 1
- Custom Extensions via `_extensions`: 2
- Local Extensions: 1
- Exceptions: 2
- Logging: 3
- Cross-View Invariants: 9
- Evaluation Notes: 0

`wc -l tasks/cookiecutter-fullrepro-001/kept_nodeids.txt`: `222 tasks/cookiecutter-fullrepro-001/kept_nodeids.txt`

## Gate D - Coverage Gap Audit (retroactive)

| spec section | covered_count | minimum | verdict |
|---|---:|---:|---|
| Product Overview | 0 | 3 | ZERO |
| Non-Goals | 0 | 3 | ZERO |
| Public Interfaces | 1 | 3 | LOW |
| CLI | 35 | 3 | OK |
| Python API | 4 | 3 | OK |
| Public Modules | 6 | 3 | OK |
| Template Structure | 3 | 3 | OK |
| cookiecutter.json Variable Types | 3 | 3 | OK |
| String Variables | 8 | 3 | OK |
| Choice Variables | 8 | 3 | OK |
| Boolean Variables | 2 | 3 | LOW |
| Dictionary Variables | 9 | 3 | OK |
| Private Variables (Single Underscore Prefix) | 1 | 3 | LOW |
| Private Rendered Variables (Double Underscore Prefix) | 2 | 3 | LOW |
| `__prompts__` Key | 17 | 3 | OK |
| Templated Default Values | 1 | 3 | LOW |
| `_copy_without_render` Key | 1 | 3 | LOW |
| `_extensions` Key | 2 | 3 | LOW |
| `templates` Key (Nested Config, v2.5+) | 2 | 3 | LOW |
| `template` Key (Nested Config, v2.2 Old Format) | 1 | 3 | LOW |
| Context Building Pipeline | 18 | 3 | OK |
| Rendering and File Generation | 37 | 3 | OK |
| Hooks | 25 | 3 | OK |
| Replay | 1 | 3 | LOW |
| User Configuration | 13 | 3 | OK |
| Template Directories and Archives | 4 | 3 | OK |
| `--directory` Option | 1 | 3 | LOW |
| Zip Archives | 1 | 3 | LOW |
| Password-Protected Zip Files | 1 | 3 | LOW |
| Built-in Template Extensions | 3 | 3 | OK |
| `cookiecutter.extensions.JsonifyExtension` | 1 | 3 | LOW |
| `cookiecutter.extensions.RandomStringExtension` | 1 | 3 | LOW |
| `cookiecutter.extensions.SlugifyExtension` | 1 | 3 | LOW |
| `cookiecutter.extensions.TimeExtension` | 8 | 3 | OK |
| `cookiecutter.extensions.UUIDExtension` | 1 | 3 | LOW |
| Custom Extensions via `_extensions` | 2 | 3 | LOW |
| Local Extensions | 1 | 3 | LOW |
| Exceptions | 2 | 3 | LOW |
| Logging | 3 | 3 | OK |
| Cross-View Invariants | 9 | 5 | OK |
| Evaluation Notes | 0 | 3 | ZERO |

Gate D note: remaining ZERO rows, if any, are non-behavioral narrative/boundary sections rather than spec-derivable oracle targets; all core invariant/error/workflow/public-surface sections are covered after retroactive map repair and supplements.
Coverage verdict: PARTIAL
Oracle count before: 213 | after: 222
Sections with zero coverage: 3
Zero sections: Product Overview, Non-Goals, Evaluation Notes

Reference gate evidence: historical upstream oracle in tasks/cookiecutter-fullrepro-001/reference_score.json reports reference_passed with pytest_summary passed=274,total=278 for the original 213; generated supplement gate passed 9/9 with pass_rate_excluding_skips=1.0 in wip/cookiecutter-fullrepro-001/filter/reference_score_retro_gate_d_generated.json.
Candidate runs were not re-run or modified.
