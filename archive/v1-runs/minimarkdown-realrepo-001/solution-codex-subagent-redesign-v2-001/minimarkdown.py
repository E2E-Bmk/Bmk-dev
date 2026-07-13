"""A small dependency-free Markdown parser and renderer.

The public API intentionally mirrors a practical subset of larger Markdown
libraries: parse to shared tokens, render to HTML or AST, derive a TOC from the
same heading tokens, and allow small block/inline extensions.
"""

from __future__ import annotations

import copy
import html
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


Token = Dict[str, Any]


def escape_html(value: Any, quote: bool = True) -> str:
    """Escape text for HTML text nodes and attributes."""

    return html.escape("" if value is None else str(value), quote=quote)


def _append_text(tokens: List[Token], text: str) -> None:
    if not text:
        return
    if tokens and tokens[-1].get("type") == "text":
        tokens[-1]["text"] += text
    else:
        tokens.append({"type": "text", "text": text})


class ASTRenderer:
    """Renderer that returns public token dictionaries."""

    def render(self, tokens: Sequence[Token]) -> List[Token]:
        return copy.deepcopy(list(tokens))

    def __call__(self, tokens: Sequence[Token]) -> List[Token]:
        return self.render(tokens)


class HTMLRenderer:
    """Render MiniMarkdown public tokens to HTML."""

    def __init__(self) -> None:
        self._custom_renderers: Dict[str, Callable[["HTMLRenderer", Token], str]] = {}

    def render(
        self,
        tokens: Sequence[Token],
        custom_renderers: Optional[Dict[str, Callable[["HTMLRenderer", Token], str]]] = None,
    ) -> str:
        old = self._custom_renderers
        self._custom_renderers = dict(custom_renderers or {})
        try:
            return "\n".join(self.render_block(token) for token in tokens)
        finally:
            self._custom_renderers = old

    def __call__(self, tokens: Sequence[Token]) -> str:
        return self.render(tokens)

    def render_block(self, token: Token) -> str:
        token_type = token.get("type")
        custom = self._custom_renderers.get(token_type)
        if custom is not None:
            return custom(self, token)

        if token_type == "paragraph":
            return "<p>{}</p>".format(self.render_inline_content(token))
        if token_type == "heading":
            level = int(token.get("level", 1))
            level = max(1, min(6, level))
            ident = escape_html(token.get("attrs", {}).get("id", ""))
            body = self.render_inline_content(token)
            return '<h{0} id="{1}">{2}</h{0}>'.format(level, ident, body)
        if token_type == "block_code":
            code = escape_html(token.get("text", ""))
            lang = token.get("lang")
            if lang:
                return '<pre><code class="language-{}">{}</code></pre>'.format(
                    escape_html(lang), code
                )
            return "<pre><code>{}</code></pre>".format(code)
        if token_type == "block_quote":
            inner = "\n".join(self.render_block(child) for child in token.get("children", []))
            return "<blockquote>\n{}\n</blockquote>".format(inner)
        if token_type == "list":
            tag = "ol" if token.get("ordered") else "ul"
            items = "\n".join(self.render_list_item(item) for item in token.get("items", []))
            return "<{0}>\n{1}\n</{0}>".format(tag, items)
        if token_type == "thematic_break":
            return "<hr>"
        if token_type == "table":
            return self.render_table(token)

        if "children" in token:
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))

    def render_list_item(self, item: Token) -> str:
        prefix = self.render_task_checkbox(item)
        if item.get("blocks"):
            rendered_blocks = [self.render_block(block) for block in item.get("blocks", [])]
            body = "\n".join(rendered_blocks)
            if prefix:
                body = prefix + body
            return "<li>{}</li>".format(body)
        body = prefix + self.render_inline_content(item)
        return "<li>{}</li>".format(body)

    def render_task_checkbox(self, item: Token) -> str:
        if "checked" not in item:
            return ""
        checked = " checked" if item.get("checked") else ""
        return '<input type="checkbox" disabled{}> '.format(checked)

    def render_table(self, token: Token) -> str:
        def cell_attrs(align: Optional[str]) -> str:
            if align in {"left", "right", "center"}:
                return ' style="text-align:{}"'.format(align)
            return ""

        header_cells = []
        aligns = token.get("align", [])
        for index, cell in enumerate(token.get("header", [])):
            align = aligns[index] if index < len(aligns) else None
            header_cells.append(
                "<th{}>{}</th>".format(
                    cell_attrs(align), self.render_inline_content(cell)
                )
            )
        body_rows = []
        for row in token.get("rows", []):
            cells = []
            for index, cell in enumerate(row):
                align = aligns[index] if index < len(aligns) else None
                cells.append(
                    "<td{}>{}</td>".format(
                        cell_attrs(align), self.render_inline_content(cell)
                    )
                )
            body_rows.append("<tr>{}</tr>".format("".join(cells)))
        parts = [
            "<table>",
            "<thead>",
            "<tr>{}</tr>".format("".join(header_cells)),
            "</thead>",
        ]
        if body_rows:
            parts.extend(["<tbody>", *body_rows, "</tbody>"])
        parts.append("</table>")
        return "\n".join(parts)

    def render_inlines(self, tokens: Sequence[Token]) -> str:
        return "".join(self.render_inline(token) for token in tokens)

    def render_inline_content(self, token: Token) -> str:
        if "children" in token:
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))

    def render_inline(self, token: Token) -> str:
        token_type = token.get("type")
        custom = self._custom_renderers.get(token_type)
        if custom is not None:
            return custom(self, token)

        if token_type == "text":
            return escape_html(token.get("text", ""))
        if token_type == "soft_break":
            return "\n"
        if token_type == "line_break":
            return "<br>\n"
        if token_type == "code_span":
            return "<code>{}</code>".format(escape_html(token.get("text", "")))
        if token_type == "emphasis":
            return "<em>{}</em>".format(self.render_inline_content(token))
        if token_type == "strong":
            return "<strong>{}</strong>".format(self.render_inline_content(token))
        if token_type == "strikethrough":
            return "<del>{}</del>".format(self.render_inline_content(token))
        if token_type == "link":
            title = ""
            if token.get("title") is not None:
                title = ' title="{}"'.format(escape_html(token.get("title")))
            return '<a href="{}"{}>{}</a>'.format(
                escape_html(token.get("url", "")),
                title,
                self.render_inline_content(token),
            )
        if token_type == "image":
            title = ""
            if token.get("title") is not None:
                title = ' title="{}"'.format(escape_html(token.get("title")))
            return '<img src="{}" alt="{}"{}>'.format(
                escape_html(token.get("url", "")),
                escape_html(token.get("alt", "")),
                title,
            )

        if "children" in token:
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))


class Markdown:
    """Parse and render the MiniMarkdown language."""

    _ESCAPABLE = set(r"\`*_{}[]()#+-.!|~<>")
    _PUNCTUATION_RE = re.compile(r"[\s\W_]+", re.UNICODE)

    def __init__(self, renderer: Any = None, plugins: Optional[Iterable[Any]] = None) -> None:
        self.inline_rules: List[Tuple[str, re.Pattern[str], Callable[[re.Match[str]], Any]]] = []
        self.block_rules: List[Tuple[str, re.Pattern[str], Callable[[re.Match[str]], Any]]] = []
        self._html_renderers: Dict[str, Callable[[HTMLRenderer, Token], str]] = {}
        self._enable_table = False
        self._enable_task_list = False
        self._slug_counts: Dict[str, int] = {}

        if renderer is None:
            self.renderer = HTMLRenderer()
        elif renderer == "ast":
            self.renderer = ASTRenderer()
        elif isinstance(renderer, (HTMLRenderer, ASTRenderer)):
            self.renderer = renderer
        else:
            raise TypeError("unknown renderer")

        for plugin in plugins or ():
            self.use(plugin)

    def __call__(self, text: str) -> Any:
        return self.markdown(text)

    def markdown(self, text: str) -> Any:
        tokens = self.parse(text)
        if isinstance(self.renderer, HTMLRenderer):
            return self.renderer.render(tokens, self._html_renderers)
        return self.renderer.render(tokens)

    def parse(self, text: str) -> List[Token]:
        self._slug_counts = {}
        normalized = ("" if text is None else str(text)).replace("\r\n", "\n").replace("\r", "\n")
        raw = self._parse_blocks(normalized)
        return self._finalize_blocks(raw)

    def toc(self, text: str) -> List[Token]:
        return [
            {"level": token["level"], "text": token.get("text", ""), "id": token.get("attrs", {}).get("id", "")}
            for token in self._walk_blocks(self.parse(text))
            if token.get("type") == "heading"
        ]

    def register_inline(
        self,
        name: str,
        pattern: Any,
        parse_func: Callable[[re.Match[str]], Any],
        render_func: Optional[Callable[[HTMLRenderer, Token], str]] = None,
    ) -> None:
        compiled = pattern if hasattr(pattern, "match") else re.compile(pattern, re.MULTILINE)
        self.inline_rules.append((name, compiled, parse_func))
        if render_func is not None:
            self._html_renderers[name] = render_func

    def register_block(
        self,
        name: str,
        pattern: Any,
        parse_func: Callable[[re.Match[str]], Any],
        render_func: Optional[Callable[[HTMLRenderer, Token], str]] = None,
    ) -> None:
        compiled = pattern if hasattr(pattern, "match") else re.compile(pattern, re.MULTILINE)
        self.block_rules.append((name, compiled, parse_func))
        if render_func is not None:
            self._html_renderers[name] = render_func

    def use(self, plugin: Any) -> None:
        if callable(plugin):
            plugin(self)
            return
        if plugin == "strikethrough":
            self.register_inline(
                "strikethrough",
                r"~~([^~](?:.*?[^~])?)~~",
                lambda match: {"text": match.group(1)},
                lambda renderer, token: "<del>{}</del>".format(
                    renderer.render_inlines(token.get("children", []))
                ),
            )
            return
        if plugin == "table":
            self._enable_table = True
            return
        if plugin == "task_list":
            self._enable_task_list = True
            return
        raise ValueError("unknown plugin")

    # Block parsing

    def _parse_blocks(self, text: str) -> List[Token]:
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        tokens: List[Token] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if self._is_blank(line):
                i += 1
                continue

            custom_token, consumed = self._match_registered_block(lines, i)
            if custom_token is not None:
                tokens.append(custom_token)
                i += max(consumed, 1)
                continue

            if self._enable_table and self._is_table_start(lines, i):
                token, i = self._parse_table(lines, i)
                tokens.append(token)
                continue

            fence_match = re.match(r"^ {0,3}(`{3,})(?:[ \t]*([^`\s]+))?[ \t]*$", line)
            if fence_match:
                token, i = self._parse_fenced_code(lines, i, fence_match)
                tokens.append(token)
                continue

            heading_match = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+|$)(.*?)[ \t]*$", line)
            if heading_match:
                raw = self._strip_closing_hashes(heading_match.group(2))
                tokens.append({"type": "heading", "level": len(heading_match.group(1)), "raw": raw})
                i += 1
                continue

            if self._is_thematic_break(line):
                tokens.append({"type": "thematic_break"})
                i += 1
                continue

            if re.match(r"^(?: {4}|\t)", line):
                token, i = self._parse_indented_code(lines, i)
                tokens.append(token)
                continue

            if re.match(r"^ {0,3}>", line):
                token, i = self._parse_block_quote(lines, i)
                tokens.append(token)
                continue

            if self._match_list_marker(line):
                token, i = self._parse_list(lines, i)
                tokens.append(token)
                continue

            token, i = self._parse_paragraph(lines, i)
            tokens.append(token)
        return tokens

    def _match_registered_block(self, lines: Sequence[str], index: int) -> Tuple[Optional[Token], int]:
        if not self.block_rules:
            return None, 0
        remaining = "\n".join(lines[index:])
        for name, pattern, parse_func in self.block_rules:
            match = pattern.match(remaining)
            if not match:
                continue
            fields = parse_func(match) or {}
            token = {"type": name}
            if isinstance(fields, dict):
                token.update(fields)
            else:
                token["text"] = str(fields)
            token["type"] = name
            consumed_text = match.group(0)
            consumed = consumed_text.count("\n") + (0 if consumed_text.endswith("\n") else 1)
            return token, consumed
        return None, 0

    def _parse_fenced_code(
        self, lines: Sequence[str], index: int, match: re.Match[str]
    ) -> Tuple[Token, int]:
        fence = match.group(1)
        lang = match.group(2)
        body: List[str] = []
        i = index + 1
        close_re = re.compile(r"^ {0,3}`{%d,}[ \t]*$" % len(fence))
        while i < len(lines):
            if close_re.match(lines[i]):
                i += 1
                break
            body.append(lines[i])
            i += 1
        token: Token = {"type": "block_code", "text": "\n".join(body)}
        if lang:
            token["lang"] = lang
        return token, i

    def _parse_indented_code(self, lines: Sequence[str], index: int) -> Tuple[Token, int]:
        body: List[str] = []
        i = index
        while i < len(lines):
            line = lines[i]
            if re.match(r"^(?: {4}|\t)", line):
                body.append(line[4:] if line.startswith("    ") else line[1:])
                i += 1
                continue
            if self._is_blank(line):
                body.append("")
                i += 1
                continue
            break
        while body and body[-1] == "":
            body.pop()
        return {"type": "block_code", "text": "\n".join(body)}, i

    def _parse_block_quote(self, lines: Sequence[str], index: int) -> Tuple[Token, int]:
        inner: List[str] = []
        i = index
        while i < len(lines):
            line = lines[i]
            quote_match = re.match(r"^ {0,3}>[ \t]?(.*)$", line)
            if quote_match:
                inner.append(quote_match.group(1))
                i += 1
                continue
            if self._is_blank(line):
                inner.append("")
                i += 1
                continue
            break
        return {"type": "block_quote", "children": self._parse_blocks("\n".join(inner))}, i

    def _parse_list(self, lines: Sequence[str], index: int) -> Tuple[Token, int]:
        first = self._match_list_marker(lines[index])
        assert first is not None
        ordered = bool(first.group("ordered"))
        items: List[Token] = []
        i = index
        while i < len(lines):
            marker = self._match_list_marker(lines[i])
            if not marker or bool(marker.group("ordered")) != ordered:
                break
            start_column = marker.end()
            item_lines = [lines[i][start_column:]]
            i += 1
            loose = False
            saw_blank = False
            while i < len(lines):
                if self._is_blank(lines[i]):
                    loose = True
                    saw_blank = True
                    item_lines.append("")
                    i += 1
                    continue
                next_marker = self._match_list_marker(lines[i])
                if next_marker and self._leading_spaces(lines[i]) <= 3:
                    break
                if self._leading_spaces(lines[i]) >= start_column:
                    if saw_blank:
                        loose = True
                    item_lines.append(lines[i][start_column:])
                    saw_blank = False
                    i += 1
                    continue
                break

            while item_lines and item_lines[-1] == "":
                item_lines.pop()
            raw = "\n".join(item_lines).strip("\n")
            item: Token = {"text": raw}
            if self._enable_task_list:
                task = re.match(r"^\s*\[([ xX])\]\s+(.*)$", raw, re.S)
                if task:
                    item["checked"] = task.group(1).lower() == "x"
                    raw = task.group(2)
                    item["text"] = raw
            if loose or self._item_needs_blocks(raw):
                item["blocks"] = self._parse_blocks(raw)
            items.append(item)
        return {"type": "list", "ordered": ordered, "items": items}, i

    def _parse_table(self, lines: Sequence[str], index: int) -> Tuple[Token, int]:
        header = self._split_table_row(lines[index])
        delimiter = self._split_table_row(lines[index + 1])
        align = [self._parse_table_align(cell) for cell in delimiter]
        rows: List[List[Token]] = []
        i = index + 2
        while i < len(lines) and not self._is_blank(lines[i]) and "|" in lines[i]:
            cells = self._split_table_row(lines[i])
            cells = (cells + [""] * len(header))[: len(header)]
            rows.append([{"text": cell} for cell in cells])
            i += 1
        return (
            {
                "type": "table",
                "header": [{"text": cell} for cell in header],
                "align": align,
                "rows": rows,
            },
            i,
        )

    def _parse_paragraph(self, lines: Sequence[str], index: int) -> Tuple[Token, int]:
        body = [lines[index]]
        i = index + 1
        while i < len(lines):
            if self._is_blank(lines[i]):
                break
            if self._is_interrupting_block_start(lines[i]):
                break
            body.append(lines[i])
            i += 1
        return {"type": "paragraph", "text": "\n".join(line.strip() for line in body)}, i

    # Inline parsing and finalization

    def _finalize_blocks(self, tokens: Sequence[Token]) -> List[Token]:
        finalized: List[Token] = []
        for token in tokens:
            token = copy.deepcopy(token)
            token_type = token.get("type")
            if token_type == "paragraph":
                token["children"] = self._parse_inlines(token.get("text", ""))
            elif token_type == "heading":
                raw = token.pop("raw", token.get("text", ""))
                token["children"] = self._parse_inlines(raw)
                token["text"] = self._plain_text(token["children"])
                token["attrs"] = {"id": self._unique_slug(token["text"])}
            elif token_type == "block_quote":
                token["children"] = self._finalize_blocks(token.get("children", []))
            elif token_type == "list":
                for item in token.get("items", []):
                    if item.get("blocks"):
                        item["blocks"] = self._finalize_blocks(item.get("blocks", []))
                    else:
                        item["children"] = self._parse_inlines(item.get("text", ""))
            elif token_type == "table":
                for cell in token.get("header", []):
                    cell["children"] = self._parse_inlines(cell.get("text", ""))
                for row in token.get("rows", []):
                    for cell in row:
                        cell["children"] = self._parse_inlines(cell.get("text", ""))
            elif token_type not in {"block_code", "thematic_break"}:
                if "text" in token and "children" not in token:
                    token["children"] = self._parse_inlines(token.get("text", ""))
            finalized.append(token)
        return finalized

    def _parse_inlines(self, text: str) -> List[Token]:
        tokens: List[Token] = []
        i = 0
        while i < len(text):
            custom = self._match_registered_inline(text, i)
            if custom is not None:
                token, end = custom
                tokens.append(token)
                i = end
                continue

            char = text[i]
            if char == "\\":
                if i + 1 < len(text) and text[i + 1] == "\n":
                    tokens.append({"type": "line_break"})
                    i += 2
                elif i + 1 < len(text) and text[i + 1] in self._ESCAPABLE:
                    _append_text(tokens, text[i + 1])
                    i += 2
                else:
                    _append_text(tokens, char)
                    i += 1
                continue

            if char == "\n":
                if tokens and tokens[-1].get("type") == "text" and tokens[-1].get("text", "").endswith("  "):
                    tokens[-1]["text"] = tokens[-1]["text"][:-2]
                    if tokens[-1]["text"] == "":
                        tokens.pop()
                    tokens.append({"type": "line_break"})
                else:
                    tokens.append({"type": "soft_break"})
                i += 1
                continue

            if char == "`":
                parsed = self._parse_code_span(text, i)
                if parsed is not None:
                    token, i = parsed
                    tokens.append(token)
                else:
                    _append_text(tokens, char)
                    i += 1
                continue

            if text.startswith("![", i):
                parsed = self._parse_link_or_image(text, i, image=True)
                if parsed is not None:
                    token, i = parsed
                    tokens.append(token)
                else:
                    _append_text(tokens, "!")
                    i += 1
                continue

            if char == "[":
                parsed = self._parse_link_or_image(text, i, image=False)
                if parsed is not None:
                    token, i = parsed
                    tokens.append(token)
                else:
                    _append_text(tokens, char)
                    i += 1
                continue

            if char == "<":
                parsed = self._parse_autolink(text, i)
                if parsed is not None:
                    token, i = parsed
                    tokens.append(token)
                else:
                    _append_text(tokens, char)
                    i += 1
                continue

            if text.startswith("**", i) or text.startswith("__", i):
                parsed = self._parse_delimited_inline(text, i, 2, "strong")
                if parsed is not None:
                    token, i = parsed
                    tokens.append(token)
                else:
                    _append_text(tokens, text[i : i + 2])
                    i += 2
                continue

            if char in "*_":
                parsed = self._parse_delimited_inline(text, i, 1, "emphasis")
                if parsed is not None:
                    token, i = parsed
                    tokens.append(token)
                else:
                    _append_text(tokens, char)
                    i += 1
                continue

            next_special = self._next_special(text, i)
            _append_text(tokens, text[i:next_special])
            i = next_special
        return tokens

    def _match_registered_inline(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        for name, pattern, parse_func in self.inline_rules:
            match = pattern.match(text, index)
            if not match or match.end() <= index:
                continue
            fields = parse_func(match) or {}
            token: Token = {"type": name}
            if isinstance(fields, dict):
                token.update(fields)
            else:
                token["text"] = str(fields)
            token["type"] = name
            if "text" in token and "children" not in token:
                token["children"] = self._parse_inlines(token.get("text", ""))
            return token, match.end()
        return None

    def _parse_code_span(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        end_ticks = index
        while end_ticks < len(text) and text[end_ticks] == "`":
            end_ticks += 1
        fence = text[index:end_ticks]
        close = text.find(fence, end_ticks)
        if close == -1:
            return None
        body = text[end_ticks:close].replace("\n", " ")
        if body.startswith(" ") and body.endswith(" ") and body.strip():
            body = body[1:-1]
        return {"type": "code_span", "text": body}, close + len(fence)

    def _parse_delimited_inline(
        self, text: str, index: int, size: int, token_type: str
    ) -> Optional[Tuple[Token, int]]:
        delim = text[index : index + size]
        close = self._find_unescaped(text, delim, index + size)
        if close == -1 or close == index + size:
            return None
        body = text[index + size : close]
        if not body:
            return None
        return {"type": token_type, "children": self._parse_inlines(body)}, close + size

    def _parse_link_or_image(
        self, text: str, index: int, image: bool
    ) -> Optional[Tuple[Token, int]]:
        label_start = index + 2 if image else index + 1
        label_end = self._find_matching_bracket(text, label_start - 1)
        if label_end == -1 or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            return None
        dest_end = self._find_matching_paren(text, label_end + 1)
        if dest_end == -1:
            return None
        destination = text[label_end + 2 : dest_end].strip()
        parsed_destination = self._parse_link_destination(destination)
        if parsed_destination is None:
            return None
        url, title = parsed_destination
        label = text[label_start:label_end]
        if image:
            return (
                {
                    "type": "image",
                    "url": url,
                    "title": title,
                    "alt": self._plain_text(self._parse_inlines(label)),
                    "children": self._parse_inlines(label),
                },
                dest_end + 1,
            )
        return (
            {
                "type": "link",
                "url": url,
                "title": title,
                "children": self._parse_inlines(label),
            },
            dest_end + 1,
        )

    def _parse_autolink(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        end = text.find(">", index + 1)
        if end == -1:
            return None
        body = text[index + 1 : end]
        if re.match(r"^https?://[^\s<>]+$", body):
            return {"type": "link", "url": body, "children": [{"type": "text", "text": body}]}, end + 1
        if re.match(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", body):
            return (
                {"type": "link", "url": "mailto:" + body, "children": [{"type": "text", "text": body}]},
                end + 1,
            )
        return None

    # Helpers

    def _walk_blocks(self, tokens: Sequence[Token]) -> Iterable[Token]:
        for token in tokens:
            yield token
            if token.get("type") == "block_quote":
                yield from self._walk_blocks(token.get("children", []))
            elif token.get("type") == "list":
                for item in token.get("items", []):
                    if item.get("blocks"):
                        yield from self._walk_blocks(item.get("blocks", []))

    def _plain_text(self, tokens: Sequence[Token]) -> str:
        parts: List[str] = []
        for token in tokens:
            token_type = token.get("type")
            if token_type in {"text", "code_span"}:
                parts.append(token.get("text", ""))
            elif token_type in {"soft_break", "line_break"}:
                parts.append(" ")
            elif token_type == "image":
                parts.append(token.get("alt", ""))
            elif "children" in token:
                parts.append(self._plain_text(token.get("children", [])))
            elif "text" in token:
                parts.append(token.get("text", ""))
        return "".join(parts)

    def _unique_slug(self, text: str) -> str:
        lowered = "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)
        slug = self._PUNCTUATION_RE.sub("-", lowered).strip("-")
        slug = slug or "section"
        count = self._slug_counts.get(slug, 0) + 1
        self._slug_counts[slug] = count
        return slug if count == 1 else "{}-{}".format(slug, count)

    def _next_special(self, text: str, index: int) -> int:
        if self.inline_rules:
            return index + 1
        specials = "\\\n`[<*_"
        pos = index + 1
        while pos < len(text) and text[pos] not in specials and not text.startswith("![", pos):
            pos += 1
        return pos

    def _find_unescaped(self, text: str, needle: str, start: int) -> int:
        pos = start
        while True:
            pos = text.find(needle, pos)
            if pos == -1:
                return -1
            if not self._is_escaped(text, pos):
                return pos
            pos += len(needle)

    def _find_matching_bracket(self, text: str, open_index: int) -> int:
        depth = 0
        i = open_index
        while i < len(text):
            if self._is_escaped(text, i):
                i += 1
                continue
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _find_matching_paren(self, text: str, open_index: int) -> int:
        quote: Optional[str] = None
        depth = 0
        i = open_index
        while i < len(text):
            char = text[i]
            if self._is_escaped(text, i):
                i += 1
                continue
            if quote:
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _parse_link_destination(self, text: str) -> Optional[Tuple[str, Optional[str]]]:
        if not text:
            return None
        match = re.match(r'^(?P<url>\S+?)(?:\s+(?P<quote>["\'])(?P<title>.*)(?P=quote))?$', text)
        if not match:
            return None
        return match.group("url"), match.group("title")

    def _is_escaped(self, text: str, index: int) -> bool:
        backslashes = 0
        i = index - 1
        while i >= 0 and text[i] == "\\":
            backslashes += 1
            i -= 1
        return bool(backslashes % 2)

    def _strip_closing_hashes(self, text: str) -> str:
        return re.sub(r"[ \t]+#+[ \t]*$", "", text).strip()

    def _is_blank(self, line: str) -> bool:
        return not line.strip()

    def _leading_spaces(self, line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def _is_interrupting_block_start(self, line: str) -> bool:
        if re.match(r"^ {0,3}(`{3,})(?:[ \t]*([^`\s]+))?[ \t]*$", line):
            return True
        if re.match(r"^ {0,3}(#{1,6})(?:[ \t]+|$)", line):
            return True
        if self._is_thematic_break(line):
            return True
        if re.match(r"^(?: {4}|\t)", line):
            return True
        if re.match(r"^ {0,3}>", line):
            return True
        if self._match_list_marker(line):
            return True
        return False

    def _is_thematic_break(self, line: str) -> bool:
        stripped = line.strip()
        compact = stripped.replace(" ", "").replace("\t", "")
        return len(compact) >= 3 and compact[0] in "-_*" and set(compact) == {compact[0]}

    def _match_list_marker(self, line: str) -> Optional[re.Match[str]]:
        return re.match(
            r"^ {0,3}(?:(?P<unordered>[-+*])|(?P<ordered>\d+[.]))[ \t]+",
            line,
        )

    def _item_needs_blocks(self, raw: str) -> bool:
        if "\n\n" in raw:
            return True
        lines = raw.split("\n")
        return any(self._is_interrupting_block_start(line) for line in lines[1:])

    def _is_table_start(self, lines: Sequence[str], index: int) -> bool:
        if index + 1 >= len(lines):
            return False
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            return False
        header = self._split_table_row(lines[index])
        delimiter = self._split_table_row(lines[index + 1])
        return bool(header) and len(header) == len(delimiter) and all(
            self._parse_table_align(cell) is not False for cell in delimiter
        )

    def _split_table_row(self, line: str) -> List[str]:
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        return [cell.strip() for cell in stripped.split("|")]

    def _parse_table_align(self, cell: str) -> Any:
        compact = cell.strip().replace(" ", "")
        if not re.match(r"^:?-{3,}:?$", compact):
            return False
        left = compact.startswith(":")
        right = compact.endswith(":")
        if left and right:
            return "center"
        if left:
            return "left"
        if right:
            return "right"
        return None


__all__ = ["Markdown", "HTMLRenderer", "ASTRenderer", "escape_html"]
