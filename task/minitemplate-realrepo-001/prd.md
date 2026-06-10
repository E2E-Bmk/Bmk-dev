# MiniTemplate Unit/System Public Packet

## Overview

Build `minitemplate.py`, a compact template engine inspired by Jinja2. It parses template source text containing variables, conditionals, loops, filters, includes, and comments, then renders output by substituting real values from a context dictionary.

This task is designed around the distinction between local feature correctness and system correctness. Individual template features should work on their own, but the engine is only complete if variable scoping, filter pipelines, include resolution, loop state, comment stripping, and error recovery remain consistent across composed templates.

The implementation language is Python 3.11. Place `minitemplate.py` at the root of your solution directory. Use only the Python standard library.

Public API:

```python
from minitemplate import Template, Environment

# Simple usage — parse and render in one step
t = Template("Hello {{ name }}!")
print(t.render(name="Alice"))

# Environment usage — with loader for includes and custom filters
env = Environment(loader={"header": "Title: {{ title }}"})
env.add_filter("shout", lambda s: s.upper() + "!")
t = env.from_string("{% include 'header' %}\n{{ msg | shout }}")
print(t.render(title="Home", msg="welcome"))
```

The benchmark does not inspect private implementation details.

## Feature Set

The product has seven feature modules:

1. Variable substitution — `{{ var }}`, dot notation `{{ obj.key }}`, and index access `{{ seq[0] }}`.
2. Conditional blocks — `{% if cond %}`, `{% elif cond %}`, `{% else %}`, `{% endif %}`.
3. Loop blocks — `{% for item in seq %}` / `{% endfor %}`, with `loop.index` and `loop.index0`.
4. Built-in filters — `| upper`, `| lower`, `| default("x")`, `| length`, `| trim`, plus custom filter registration.
5. Template includes — `{% include "name" %}` resolved via an environment loader.
6. Comment handling — `{# ... #}` stripped from output.
7. Error handling — undefined variables, syntax errors, missing includes, circular includes.

These modules are intentionally state-dependent. Variables defined in the render context flow through conditionals, loops, and filters. Include directives pull in sub-templates whose output becomes part of the parent. Loop variables shadow outer context. Filters transform values before they reach conditionals or final output.

## Global Invariants

The following invariants define system correctness:

- Variables resolve to the innermost scope: render kwargs > loop variables > nothing (raises or empty string depending on strict mode).
- Undefined variables in `{% if %}` and `{% elif %}` conditions should be treated as falsy (not error).
- Dot notation `{{ obj.key }}` should first try dict key access, then object attribute access.
- Filter pipelines `{{ val | filter1 | filter2 }}` apply left to right.
- `loop.index` is 1-based, `loop.index0` is 0-based; both are only available inside `{% for %}` bodies.
- Include paths are looked up in the environment loader dict. A missing include key must raise an error.
- Comments `{# ... #}` must be completely stripped from output (not rendered as whitespace).
- Failed template operations (parse error, render error) must not corrupt the Template or Environment object state for subsequent use.
- Re-rendering the same Template instance with different context values must produce independent, correct results.

## Template Syntax

### Variables

```
{{ var }}
{{ obj.key }}
{{ seq[0] }}
```

Render-time keyword arguments become template variables. Dot notation accesses nested dict keys or object attributes (dict takes priority).

### Conditionals

```
{% if user %}
  Hello {{ user }}!
{% elif guest %}
  Welcome guest.
{% else %}
  Please log in.
{% endif %}
```

Truthiness follows Python rules: `None`, `False`, `0`, empty string, empty list, empty dict are falsy; everything else is truthy. Undefined variables in conditions are treated as falsy.

### Loops

```
{% for item in items %}
  {{ loop.index }}: {{ item }}
{% endfor %}
```

Within the loop body, `item` is the current element and `loop` provides `loop.index` (1-based) and `loop.index0` (0-based). The loop variable shadows any outer variable of the same name.

### Filters

```
{{ name | upper }}
{{ bio | default("No bio provided") | trim }}
{{ items | length }}
```

Built-in filters:

| Filter | Behavior |
|--------|----------|
| `upper` | Convert to uppercase string |
| `lower` | Convert to lowercase string |
| `default("x")` | Use default value if input is undefined, None, or empty string |
| `length` | Return length of list/string |
| `trim` | Strip leading and trailing whitespace |

Custom filters are registered via `env.add_filter(name, func)`. Custom filters take precedence over built-in filters of the same name.

### Includes

```
{% include "header" %}
```

The include name is looked up in the Environment's loader (a dict mapping names to template source strings). The included template is parsed and rendered with the same context as the parent. Includes may themselves include other templates. Circular includes must be detected and raise an error.

### Comments

```
{# This is a comment #}
```

Comments are stripped and produce no output.

## API

### `Template(source, *, env=None)`

Parse a template string. The optional `env` is an `Environment` instance for includes and filters.

Methods:
- `render(**context)` — render the template with keyword arguments as variables. Returns the rendered string.

### `Environment(loader=None)`

Create an environment for template resolution.

Parameters:
- `loader` — a dict mapping include names to template source strings.

Methods:
- `from_string(source)` — parse a template string using this environment's loader and filters. Returns a `Template`.
- `add_filter(name, func)` — register a custom filter function. `func` receives one argument (the value) and returns the filtered value. Raises if a built-in filter name is used (unless explicitly intended as an override — overriding is allowed).

## Error Behavior

The following must raise exceptions:

- **Undefined variable**: rendering `{{ missing }}` where `missing` is not in context must raise `UndefinedError` (a subclass of `NameError`).
- **Syntax error**: unclosed `{% if %}` without `{% endif %}`, unclosed `{% for %}` without `{% endfor %}`, or malformed tags must raise `TemplateSyntaxError` (a subclass of `ValueError`).
- **Missing include**: `{% include "nonexistent" %}` where the name is not in the loader must raise `IncludeError` (a subclass of `LookupError`).
- **Circular include**: A chain of includes that loops back to an already-included template must raise `IncludeError`.

Exception types should be importable:

```python
from minitemplate import Template, Environment
from minitemplate import UndefinedError, TemplateSyntaxError, IncludeError
```

The exact error message text is not part of the public API.

## Non-Goals

- No template inheritance (`{% extends %}`, `{% block %}`).
- No macro definitions (`{% macro %}`).
- No raw/verbatim blocks (`{% raw %}`).
- No autoescaping or HTML escaping.
- No complex expressions in `{% if %}` (no `and`/`or`/`not` operators — just single variable or attribute truthiness checks).
- No whitespace control modifiers (`{%-`, `-%}`).
- No async rendering.
- No file system loader — the loader is always an in-memory dict.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time using short Python snippets that import the module, create templates, and print rendered output.
- System tests exercise interactions across at least two feature modules. They inspect rendered strings, exception types, variable scoping, filter pipelines, include chains, and error recovery.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`
