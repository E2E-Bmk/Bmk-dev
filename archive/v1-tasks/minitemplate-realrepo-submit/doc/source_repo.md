# Source Repo: Jinja

- Repository: `pallets/jinja`
- Benchmark case: `minitemplate-realrepo-submit`
- Source surface: template parsing and rendering with variables, conditionals, loops, blocks, scoped variables, environment compilation, and syntax errors.
- Origin packet: `tyx010/tyx-Bmk-dev`

## Selected Surface

This task uses a compact Python template engine API with `Template`, `Environment`, `TemplateSyntaxError`, variable substitution, if/elif/else, for/else, block sections, and scoped `with` bindings.

## Rationale

The intended compositional contract is that parsed templates can be rendered repeatedly with independent contexts while variables, conditions, loops, blocks, and scoped bindings compose. Validated runs showed the current mini surface is too direct for both Codex and OpenHands + DeepSeek V4.
