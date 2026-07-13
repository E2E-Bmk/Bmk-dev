# MiniJinja Lifecycle Public Packet

## Overview

Build `minitemplate.py`, a compact Jinja-like template engine. It should render variables, conditionals, loops, scoped assignments, blocks, inheritance, includes, macro imports, filters, tests, globals, undefined values, whitespace trim markers, and optional HTML autoescaping.

The task is centered on a single shared `Environment`. The environment owns template loading, compiled-template caching, filter and test registries, globals, and autoescape policy. A correct implementation should not treat `Template`, includes, imports, inheritance, and registry lookup as unrelated features. They are different projections of the same environment state.

The implementation language is Python 3.11. Place `minitemplate.py` at the root of your solution directory. Use only the Python standard library.

Public API:

```python
from minitemplate import Environment, Template, TemplateSyntaxError, TemplateNotFound

env = Environment(
    {
        "base.html": "Hello {% block body %}{{ name }}{% endblock %}",
        "page.html": "{% extends \"base.html\" %}{% block body %}{{ name|upper }}{% endblock %}",
    },
    globals={"site_name": "Docs"},
)

print(env.get_template("page.html").render(name="Ada"))  # Hello ADA
print(Template("Hi {{ name }}").render(name="Bob"))      # Hi Bob
```

The benchmark does not inspect private implementation details. Hidden tests compare public render results, exception types where documented, and semantic consistency across environment-driven lifecycle operations.

## Product Model

`Environment` is the canonical fact source. It contains:

- the loader mapping template names to source strings;
- the compiled template cache;
- filter and test registries;
- global variables;
- autoescape policy.

Derived views include direct `Template` renders, `Environment.from_string()` renders, `Environment.get_template()` renders, included templates, imported macro namespaces, inherited block output, and cached template reuse after invalidation.

## Global Invariants

- All templates created by one `Environment` must read the same loader, cache, filters, tests, globals, undefined policy, whitespace control, and autoescape policy.
- `Environment.get_template(name)` loads by template name and may cache compiled templates, but `Environment.set_template(name, source)` and `Environment.invalidate(name)` must make later renders observe the updated source.
- A failed load or parse must not poison the environment cache, registries, globals, or later valid renders.
- `Template(source)` is a convenience for a standalone environment; `Environment.from_string(source)` returns a template bound to that environment.
- A template can be rendered repeatedly with independent call contexts. Loop variables, macro arguments, block overrides, and `{% with %}` variables must not leak into outer or later renders.
- Inheritance resolves block overrides through the environment. A child template with `{% extends "base.html" %}` renders the parent template while overriding blocks defined by name.
- Includes and imports load through the same environment as the caller. Included templates see caller variables and environment globals. Imported macros use the environment registries and globals, and caller-specific values should be passed as explicit macro arguments. Macro arguments remain scoped to the macro call.
- Filters and tests are looked up at render time from `env.filters` and `env.tests`. Mutating those registries affects later renders made through the same environment.
- Undefined variables render as empty strings, are falsy in conditions, are detectable by `is undefined` / `is defined`, and do not raise merely because they are missing.
- Autoescape is an environment policy. When enabled, variable output is HTML-escaped unless a value is marked safe by the `safe` filter or the render is inside `{% autoescape false %}`.
- Whitespace trim markers `{{-`, `-}}`, `{%-`, and `-%}` trim adjacent whitespace around the marked expression or tag. Exact internal whitespace outside documented trim behavior is not part of the API.

## Template Syntax

### Variables and Expressions

```
{{ name }}
{{ user.name }}
{{ d.key }}
{{ name|upper }}
{{ missing|default("guest") }}
```

Render-time keyword arguments become template variables. Dot notation tries attribute access, key access, then integer index access. Supported literal atoms are strings, integers, floats, booleans, and `None`.

Built-in filters: `upper`, `lower`, `title`, `length`, `join`, `default`, `escape`, and `safe`. Users may add or replace entries in `env.filters`.

### Conditionals and Tests

```
{% if user is defined %}
  Hello {{ user }}.
{% elif count > 0 %}
  Counted.
{% else %}
  Empty.
{% endif %}
```

Supported comparison operators: `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, and `not in`. Built-in tests: `defined`, `undefined`, `odd`, `even`, and `iterable`. Users may add or replace entries in `env.tests`.

### Loops and Scoped Variables

```
{% for item in items %}
  {{ item }}
{% else %}
  empty
{% endfor %}

{% with label = "draft" %}{{ label }}{% endwith %}
```

The loop variable and `with` binding shadow outer variables only inside their blocks.

### Blocks and Inheritance

```
{% extends "base.html" %}
{% block title %}Child title{% endblock %}
```

Blocks render their own body in a standalone template. In a child template, blocks with the same name override the parent block at the location where the parent renders that block.

### Includes, Imports, and Macros

```
{% include "nav.html" %}

{% import "forms.html" as forms %}
{{ forms.input(name) }}

{% macro input(value) %}<input value="{{ value }}">{% endmacro %}
```

Includes render another template in the caller context. Imports bind a namespace containing macros from another template. Macro calls render their body with macro arguments scoped to that call; imported macros do not implicitly capture caller-local render variables unless they are passed as arguments.

### Environment API

#### `Environment(loader=None, *, autoescape=False, trim_blocks=False, lstrip_blocks=False, globals=None)`

Create an environment. `loader` may be a `dict[str, str]` mapping names to source strings. `globals` seeds variables visible to all templates rendered through the environment.

#### `Environment.from_string(source, name=None)`

Compile a source string as a template bound to the environment.

#### `Environment.get_template(name)`

Load and compile a named template through the environment loader. Raises `TemplateNotFound` when no source exists for the name.

#### `Environment.set_template(name, source)`

For dictionary loaders, store or replace a template source and invalidate that template's cache entry.

#### `Environment.invalidate(name=None)`

Invalidate one cached template by name, or clear the whole template cache when `name` is omitted.

### `class Template`

#### `Template(source)`

Parse a standalone template string. Raises `TemplateSyntaxError` on syntax errors.

#### `Template.render(**kwargs)`

Render the template with keyword arguments as variables. Returns the rendered string.

## Error Behavior

- Malformed templates must raise `TemplateSyntaxError` at parse/load time.
- Missing named templates must raise `TemplateNotFound`.
- The exact exception message text is not part of the public API.
- After an error, subsequent valid template creation, loading, registry mutation, and rendering must still work.

## Non-Goals

- No file-system loader is required.
- No asynchronous rendering.
- No custom delimiters.
- No arithmetic expressions beyond the documented literals, comparisons, filters, tests, calls, and dotted access.
- No `super()`, `set`, `call`, template comments, or full Jinja compatibility.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one public primitive at a time.
- System tests exercise lifecycle invariants across the shared `Environment` and its derived render views.

System tests are labeled by dimension: `projection_consistency`, `cache_lifecycle`, `inheritance_lifecycle`, `registry_lifecycle`, `scope_lifecycle`, `error_atomicity`, and `policy_projection`.
