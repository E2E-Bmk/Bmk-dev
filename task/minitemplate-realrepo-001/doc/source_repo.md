# Source Repository

## Identity

- Primary reference: `areebbeigh/minja`
- URL: https://github.com/areebbeigh/minja
- Description: "A basic (and heavily jinja inspired) python template engine intended to teach myself basic compiler design."
- Secondary reference: `grahammitchell/minja` (https://github.com/grahammitchell/minja)
- Pinned commit: (TBD — latest main at time of construction)
- Local checkout: (TBD)
- Source language: Python
- Benchmark case: `minitemplate-realrepo-001`

## Public Evidence Used

- `areebbeigh/minja` README: Jinja-inspired template engine, supports `{{ variables }}`, `{% if %}`, `{% for %}`, `{% block %}`, `{% with %}`, custom functions, autoescape.
- `areebbeigh/minja/minja/__init__.py`: core lexer/parser/renderer implementation showing the tokenization → AST → rendering pipeline.
- `grahammitchell/minja` README: "Kind of like Cookiecutter or Jinja but with 70% fewer features and 90% less code!" — minimal find-and-replace template engine in pure Python 3.
- Jinja2 documentation: reference semantics for variable scoping, filter behavior, template inheritance (used to validate the expected behavior of the benchmark subset).

## Reconstruction Boundary

The candidate does not rebuild the full Jinja2 feature set. The benchmark will ask for a compact Python 3.11 module named `minitemplate.py` that implements a practical subset of template engine features: `{{ }}` variable substitution with dot notation, `{% if/elif/else/endif %}` conditionals, `{% for/endfor %}` loops with `loop.index`, built-in filters (`| upper`, `| lower`, `| default`, `| length`, `| trim`), `{% include %}` with an in-memory loader, `{# #}` comments, and custom filter registration. Hidden scoring should evaluate user-visible behavior: rendered output correctness, variable scoping, filter pipeline order, include resolution, and error recovery.

## Why This Case

A template engine is a classic compiler/parser exercise that exercises distinct benchmark dimensions from the existing cases:

- **pipeline dataflow**: template source → tokenize → parse → AST → render; each stage feeds the next with well-defined interfaces.
- **variable scoping**: loop variables shadow outer context; includes share the parent context; this creates rich `global_invariant` and `state_accumulation` test scenarios.
- **filter chains**: left-to-right application of filters to values tests `operation_order_sensitivity` (upper|lower ≠ lower|upper on mixed case).
- **error recovery**: parse errors, include errors, and undefined variable errors must not corrupt the Template/Environment objects for subsequent operations, testing `error_atomicity`.
- **composition**: for-loops containing includes containing filters within conditionals create natural `boundary_crossing` scenarios.

The fairness risk is manageable: the public packet defines a focused subset (no template inheritance, no macros, no complex expressions, no whitespace control) that is implementable in a single Python file while still exposing the "unit pass / system fail" gap.

This task complements the existing benchmark cases:

| Task | Paradigm | Test format |
| --- | --- | --- |
| `zk-realrepo-001` | CLI — filesystem state | CLI args + stdout/stderr checks |
| `sqlite-utils-realrepo-001` | CLI — SQL database state | CLI args + SQL checks |
| `miniurlutils-realrepo-001` | Library — URL parsing | Python test_code + expected_output |
| `minikv-realrepo-001` | CLI — key-value state | CLI args + stdout/stderr checks |
| `miniredis-realrepo-001` | CLI — data structure state | CLI args + stdout/stderr checks |
| `minitemplate-realrepo-001` | Library — template engine | Python test_code + expected_output |
