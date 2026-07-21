# markdown-it-py Parsing, Rendering, Plugins, And CLI

## Overview

`markdown-it-py` parses Markdown into token streams, renders HTML, exposes
ordered rule registries for plugins, and provides a file/stdin command
interface. The supported behavior covers the default, `zero`, and
`commonmark` configurations together with custom fence and plugin rules.

## Installable Surface

The solution root provides an importable `markdown_it` package. These imports
are supported:

```python
from markdown_it import MarkdownIt, presets
from markdown_it.cli import parse
from markdown_it.rules_block.fence import make_fence_rule
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
```

`MarkdownIt(config="commonmark", options_update=None, renderer_cls=None)`
accepts a preset name or configuration mapping. Its public methods include
`parse`, `parseInline`, `render`, `renderInline`, `enable`, `disable`, `use`,
`get_all_rules`, `get_active_rules`, and `reset_rules`.

## Parser Configuration And Rule Control

`get_all_rules()` returns every known rule grouped as `core`, `block`,
`inline`, and `inline2`, preserving execution order. The known rules include:

- core: `normalize`, `block`, `inline`, `linkify`, `replacements`,
  `smartquotes`, `text_join`;
- block: `table`, `code`, `fence`, `blockquote`, `hr`, `list`, `reference`,
  `html_block`, `heading`, `lheading`, `paragraph`;
- inline: `text`, `linkify`, `newline`, `escape`, `backticks`,
  `strikethrough`, `emphasis`, `link`, `image`, `autolink`, `html_inline`,
  `entity`;
- inline2: `balance_pairs`, `strikethrough`, `emphasis`, `fragments_join`.

The `zero` preset initially enables paragraph parsing plus core normalization,
block, inline, and text joining, with `text`, `balance_pairs`, and
`fragments_join`. The `commonmark` preset enables CommonMark block and inline
rules but not table, linkify, replacements, smartquotes, or strikethrough.

`enable(name_or_names)` and `disable(name_or_names)` mutate active rules and
return the parser. Unknown names raise unless the documented ignore option is
used. `reset_rules()` is a context manager that restores every rule registry
after the block. Options supplied at construction override preset options;
for example `maxNesting` can replace the `zero` default of 20.

## Inline Parsing And Token Joining

`parseInline(source, env=None)` returns one top-level `inline` token whose
content is the complete source and whose children represent inline content.
Physical newlines become `softbreak` children, including adjacent blank
lines. `renderInline` emits only inline HTML without a paragraph wrapper.

Parsing or rendering an empty string returns an empty token list or empty
string. Passing no environment is equivalent to a fresh empty mapping and
does not leak state between calls.

The `fragments_join` post-rule merges adjacent `text` fragments produced by
inline processing. The core `text_join` rule similarly merges adjacent
`text_special` tokens into normal text while preserving combined content.

## Fence Rule Factory

`make_fence_rule(*, markers=("~", "`"), token_type="fence",
exact_match=False, disallow_marker_in_info=("`",), min_markers=3)` returns a
block rule compatible with
`md.block.ruler`.

A colon-marker rule registered before the normal fence rule recognizes
`:::` blocks, emits the configured token type, records opening markup, info,
and body content, and does not interfere with backtick fences. A closing fence
may be longer than its opener by default; a shorter close does not close.
Unclosed fences consume through end of input.

With `exact_match=True`, only a closing sequence of exactly the opening length
closes the block. Longer and shorter closing sequences remain body content. Exact
matching also supports nested-looking marker text without prematurely closing.

`min_markers` defaults to three and can be increased. Backtick fences reject
backticks in their info string by default. Tilde text is allowed in tilde info.
`disallow_marker_in_info` may reject all configured markers or none. A custom
rule can replace the standard `fence` rule or be registered under an
additional marker without changing unrelated fence behavior.

## Plugin Rule Registration

Each ruler supports `before(existing, name, rule)`,
`after(existing, name, rule)`, and `at(name, rule)`. `MarkdownIt.use(plugin)`
calls the plugin with the parser and returns the parser, allowing inline,
block, and core rules to be inserted or replaced. The resulting rule executes
during normal parsing in the requested order.

`md.inline.add_terminator_char(character)` extends inline terminators. Adding
the same character twice is idempotent and keeps the existing compiled
`terminator_re`; adding a new character rebuilds that regex and the new regex
matches the character.

## Token And Syntax Tree Views

`Token(type, tag, nesting, ...)` exposes `type`, `tag`, `nesting`, `attrs`,
`map`, `level`, `children`, `content`, `markup`, `info`, `meta`, `block`, and
`hidden`. `as_dict()` returns those fields; `from_dict()` recursively restores
child tokens. Attribute helpers behave as follows:

- `attrSet(name, value)` inserts or replaces;
- `attrGet(name)` returns the value or `None`;
- `attrJoin(name, value)` appends with one separating space;
- `attrPush((name, value))` appends an attribute pair;
- legacy `attrIndex(name)` returns the zero-based position or `-1`.

`SyntaxTreeNode(tokens)` builds a root tree. Paired open/close tokens become a
single node, inline children become child nodes, and `to_tokens()` exactly
reconstructs the original token sequence. Token properties pass through to
their node. Nodes support indexing, `.children`, `.type`, `.next_sibling`,
`.previous_sibling`, and depth-first `.walk()`.

## Markdown Rendering Behavior

Default rendering follows CommonMark-compatible HTML. Inputs without a final
newline still render correctly:

| Markdown | HTML |
|---|---|
| `#` | `<h1></h1>\n` |
| `###` | `<h3></h3>\n` |
| `` ` ` `` | `<p><code> </code></p>\n` |
| six backticks | `<pre><code></code></pre>\n` |
| `-` | `<ul>\n<li></li>\n</ul>\n` |
| `1.` | `<ol>\n<li></li>\n</ol>\n` |
| `>` | `<blockquote></blockquote>\n` |
| `---` | `<hr />\n` |
| `<h1></h1>` | `<h1></h1>` |
| `p` | `<p>p</p>\n` |
| `[reference]: /url` | empty string |

Indented code retains a terminating newline inside `<code>`. A blockquote
ending with a bare `>` closes normally.

Reference definitions produce no tokens and populate `env["references"]`
with uppercase labels, title, href, and source-line map. Later duplicate labels
do not replace the first definition; they are appended to
`env["duplicate_refs"]`.

The CommonMark preset expands tabs in indented code according to four-column
tab stops, including lines containing Unicode. The first three canonical tab
examples render as indented code with their remaining tab characters intact.

A configured `highlight(code, lang, attrs)` callback receives the first info
word as `lang` and the remaining spacing-preserved text as `attrs`; its returned
HTML is used as the fence rendering. Ordered-list item tokens expose their
numeric marker in `.info` and `.` in `.markup`, including multi-digit values
and indentation.

## Command-Line Workflows

`markdown_it.cli.parse.main(argv=None)` returns `0` after successful work.
With file paths it renders each UTF-8-decoded file to standard output in order.
Invalid byte sequences are decoded with replacement rather than aborting.
`--stdin` reads standard input. A missing path prints the command error and
raises `SystemExit(1)`.

With no arguments, `main` calls `interactive()` and returns `0`.
`print_heading()` writes the interactive heading. Interactive mode collects
lines, renders on end-of-input, starts another input block, and exits cleanly
on keyboard interruption. Its output includes `markdown-it-py`, the rendered
HTML preceded by a newline, and an exit message.

## Non-Goals

Linkification requiring optional dependencies, third-party plugin packages,
fuzzing utilities, profiling tools, and documentation-site generation are
outside this compatibility surface.
