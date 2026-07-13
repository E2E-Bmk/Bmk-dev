"""A small dependency-free Markdown parser with a canonical public token tree."""

from __future__ import annotations

import copy
import re
from html import escape as _html_escape
from urllib.parse import quote


def escape_html(value):
    """Escape text for HTML text and attribute contexts."""
    return _html_escape("" if value is None else str(value), quote=True)


_PUNCT = r"\\`*_{}\[\]()#+\-.!_|>~:"
_INLINE_SPECIAL_RE = re.compile(r"(!?\[|`|\\\n|\\| {2,}\n|\n|\*\*|__|\*|_|~~|<)")
_EMAIL_RE = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")
_HR_RE = re.compile(r"^\s{0,3}([-_*])(?:\s*\1){2,}\s*$")
_FENCE_RE = re.compile(r"^\s{0,3}(`{3,})(.*)$")
_ATX_RE = re.compile(r"^\s{0,3}(#{1,6})(?:\s+|$)(.*?)(?:\s+#+\s*)?$")
_UL_RE = re.compile(r"^(\s{0,3})([-+*])\s+(.*)$")
_OL_RE = re.compile(r"^(\s{0,3})(\d+)[.)]\s+(.*)$")


def _compile(pattern):
    return pattern if hasattr(pattern, "match") else re.compile(pattern)


def _plain_inline(tokens):
    pieces = []
    for token in tokens or []:
        ttype = token.get("type")
        if ttype in ("text", "code_span", "soft_break", "line_break"):
            if ttype in ("soft_break", "line_break"):
                pieces.append(" ")
            else:
                pieces.append(token.get("text", ""))
        elif ttype == "image":
            pieces.append(token.get("alt", ""))
        else:
            pieces.append(_plain_inline(token.get("children", [])))
    return "".join(pieces)


def _slugify(text, used):
    slug = re.sub(r"[\s\W_]+", "-", text.lower(), flags=re.ASCII).strip("-")
    if not slug:
        slug = "section"
    base = slug
    index = 2
    while slug in used:
        slug = "%s-%d" % (base, index)
        index += 1
    used.add(slug)
    return slug


class ASTRenderer:
    """Renderer that returns a deep-copy of the public token tree."""

    def render(self, tokens, **_kwargs):
        return copy.deepcopy(tokens)


class HTMLRenderer:
    """Render MiniMarkdown public tokens to HTML."""

    def render(self, tokens, inline_renderers=None, block_renderers=None):
        inline_renderers = inline_renderers or {}
        block_renderers = block_renderers or {}
        return "\n".join(
            self.render_block(token, inline_renderers, block_renderers, in_list=False)
            for token in tokens
        )

    def render_block(self, token, inline_renderers=None, block_renderers=None, in_list=False):
        inline_renderers = inline_renderers or {}
        block_renderers = block_renderers or {}
        ttype = token.get("type")
        inline_method = getattr(self, "render_inline_" + str(ttype), None)
        if inline_method is not None:
            return self.render_inline(token, inline_renderers)
        if ttype in block_renderers:
            return block_renderers[ttype](self, token)
        method = getattr(self, "render_" + ttype, None)
        if method is None:
            if "children" in token:
                return self.render_inlines(token.get("children", []), inline_renderers)
            return escape_html(token.get("text", ""))
        return method(token, inline_renderers, block_renderers, in_list)

    def render_inlines(self, tokens, inline_renderers=None):
        inline_renderers = inline_renderers or {}
        return "".join(self.render_inline(token, inline_renderers) for token in tokens or [])

    def render_inline(self, token, inline_renderers=None):
        inline_renderers = inline_renderers or {}
        ttype = token.get("type")
        if ttype in inline_renderers:
            return inline_renderers[ttype](self, token)
        method = getattr(self, "render_inline_" + ttype, None)
        if method is None:
            if "children" in token:
                return self.render_inlines(token.get("children", []), inline_renderers)
            return escape_html(token.get("text", ""))
        return method(token, inline_renderers)

    def render_paragraph(self, token, inline_renderers, _block_renderers, _in_list):
        return "<p>%s</p>" % self.render_inlines(token.get("children", []), inline_renderers)

    def render_heading(self, token, inline_renderers, _block_renderers, _in_list):
        level = int(token.get("level", 1))
        level = min(6, max(1, level))
        ident = escape_html(token.get("attrs", {}).get("id", ""))
        body = self.render_inlines(token.get("children", []), inline_renderers)
        return '<h%d id="%s">%s</h%d>' % (level, ident, body, level)

    def render_block_code(self, token, _inline_renderers, _block_renderers, _in_list):
        attrs = ""
        if token.get("lang"):
            attrs = ' class="language-%s"' % escape_html(token.get("lang"))
        return "<pre><code%s>%s</code></pre>" % (attrs, escape_html(token.get("text", "")))

    def render_block_quote(self, token, inline_renderers, block_renderers, _in_list):
        body = "\n".join(
            self.render_block(child, inline_renderers, block_renderers, in_list=False)
            for child in token.get("children", [])
        )
        return "<blockquote>%s</blockquote>" % body

    def render_list(self, token, inline_renderers, block_renderers, _in_list):
        tag = "ol" if token.get("ordered") else "ul"
        items = []
        for item in token.get("items", []):
            prefix = ""
            if "checked" in item:
                checked = " checked" if item.get("checked") else ""
                prefix = '<input type="checkbox" disabled%s> ' % checked
            if item.get("blocks"):
                body = "\n".join(
                    self.render_block(child, inline_renderers, block_renderers, in_list=True)
                    for child in item.get("blocks", [])
                )
                if item.get("children") and not body:
                    body = self.render_inlines(item.get("children", []), inline_renderers)
            elif item.get("children"):
                body = self.render_inlines(item.get("children", []), inline_renderers)
            else:
                body = escape_html(item.get("text", ""))
            items.append("<li>%s%s</li>" % (prefix, body))
        return "<%s>%s</%s>" % (tag, "".join(items), tag)

    def render_thematic_break(self, _token, _inline_renderers, _block_renderers, _in_list):
        return "<hr>"

    def render_table(self, token, inline_renderers, _block_renderers, _in_list):
        aligns = token.get("align", [])

        def cell(tag, data, index):
            align = aligns[index] if index < len(aligns) else None
            attr = ' align="%s"' % escape_html(align) if align else ""
            body = self.render_inlines(data.get("children", []), inline_renderers)
            return "<%s%s>%s</%s>" % (tag, attr, body, tag)

        head = "".join(cell("th", cell_token, i) for i, cell_token in enumerate(token.get("header", [])))
        rows = []
        for row in token.get("rows", []):
            rows.append("<tr>%s</tr>" % "".join(cell("td", cell_token, i) for i, cell_token in enumerate(row)))
        return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (head, "".join(rows))

    def render_inline_text(self, token, _inline_renderers):
        return escape_html(token.get("text", ""))

    def render_inline_soft_break(self, _token, _inline_renderers):
        return "\n"

    def render_inline_line_break(self, _token, _inline_renderers):
        return "<br>"

    def render_inline_code_span(self, token, _inline_renderers):
        return "<code>%s</code>" % escape_html(token.get("text", ""))

    def render_inline_emphasis(self, token, inline_renderers):
        return "<em>%s</em>" % self.render_inlines(token.get("children", []), inline_renderers)

    def render_inline_strong(self, token, inline_renderers):
        return "<strong>%s</strong>" % self.render_inlines(token.get("children", []), inline_renderers)

    def render_inline_strikethrough(self, token, inline_renderers):
        return "<del>%s</del>" % self.render_inlines(token.get("children", []), inline_renderers)

    def render_inline_link(self, token, inline_renderers):
        attrs = ' href="%s"' % escape_html(token.get("url", ""))
        if token.get("title") is not None:
            attrs += ' title="%s"' % escape_html(token.get("title"))
        return "<a%s>%s</a>" % (attrs, self.render_inlines(token.get("children", []), inline_renderers))

    def render_inline_image(self, token, _inline_renderers):
        attrs = ' src="%s" alt="%s"' % (escape_html(token.get("url", "")), escape_html(token.get("alt", "")))
        if token.get("title") is not None:
            attrs += ' title="%s"' % escape_html(token.get("title"))
        return "<img%s>" % attrs


class Markdown:
    def __init__(self, renderer=None, plugins=None):
        self.inline_rules = []
        self.block_rules = []
        self.inline_renderers = {}
        self.block_renderers = {}
        self.use_tables = False
        self.use_task_lists = False
        self.renderer = self._coerce_renderer(renderer)
        for plugin in plugins or []:
            self._load_plugin(plugin)

    def __call__(self, text):
        return self.markdown(text)

    def markdown(self, text):
        return self.render(self.parse(text))

    def _coerce_renderer(self, renderer):
        if renderer is None:
            return HTMLRenderer()
        if renderer == "ast":
            return ASTRenderer()
        if isinstance(renderer, (HTMLRenderer, ASTRenderer)):
            return renderer
        raise ValueError("unknown renderer")

    def _load_plugin(self, plugin):
        if callable(plugin):
            plugin(self)
            return
        if plugin == "strikethrough":
            self.register_inline(
                "strikethrough",
                r"~~(.+?)~~",
                lambda m: {"children": self._parse_inlines(m.group(1))},
                lambda renderer, token: "<del>%s</del>" % renderer.render_inlines(
                    token.get("children", []), self.inline_renderers
                ),
            )
            return
        if plugin == "table":
            self.use_tables = True
            return
        if plugin == "task_list":
            self.use_task_lists = True
            return
        raise ValueError("unknown plugin")

    def register_inline(self, name, pattern, parse_func, render_func=None):
        self.inline_rules.append((name, _compile(pattern), parse_func))
        if render_func is not None:
            self.inline_renderers[name] = render_func

    def register_block(self, name, pattern, parse_func, render_func=None):
        self.block_rules.append((name, _compile(pattern), parse_func))
        if render_func is not None:
            self.block_renderers[name] = render_func

    def tokens(self, text):
        return self.parse(text)

    def parse(self, text):
        lines = str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        tokens = self._parse_blocks(lines)
        self._parse_inline_blocks(tokens)
        self._assign_heading_ids(tokens)
        return tokens

    def render(self, tokens, renderer=None):
        chosen = self._coerce_renderer(renderer) if renderer is not None else self.renderer
        if isinstance(chosen, ASTRenderer):
            return chosen.render(tokens)
        return chosen.render(tokens, inline_renderers=self.inline_renderers, block_renderers=self.block_renderers)

    def walk(self, tokens):
        for token in tokens or []:
            yield token
            if token.get("type") == "list":
                for item in token.get("items", []):
                    yield item
                    for child in item.get("children", []):
                        yield from self.walk([child])
                    for child in item.get("blocks", []) or item.get("children_blocks", []):
                        yield from self.walk([child])
            elif token.get("type") == "table":
                for cell in token.get("header", []):
                    yield cell
                    yield from self.walk(cell.get("children", []))
                for row in token.get("rows", []):
                    for cell in row:
                        yield cell
                        yield from self.walk(cell.get("children", []))
            else:
                if token.get("children"):
                    yield from self.walk(token.get("children", []))
                if token.get("blocks"):
                    yield from self.walk(token.get("blocks", []))

    def toc(self, text):
        tokens = self.parse(text)
        return [
            {"level": token.get("level"), "text": token.get("text", ""), "id": token.get("attrs", {}).get("id", "")}
            for token in self.walk(tokens)
            if token.get("type") == "heading"
        ]

    def _parse_blocks(self, lines):
        tokens = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                i += 1
                continue

            custom = self._match_custom_block(line)
            if custom is not None:
                tokens.append(custom)
                i += 1
                continue

            fence = _FENCE_RE.match(line)
            if fence:
                marker = fence.group(1)
                info = fence.group(2).strip()
                lang = info.split()[0] if info else None
                i += 1
                body = []
                while i < len(lines):
                    if re.match(r"^\s{0,3}%s`*\s*$" % re.escape(marker), lines[i]):
                        i += 1
                        break
                    body.append(lines[i])
                    i += 1
                token = {"type": "block_code", "text": "\n".join(body)}
                if lang:
                    token["lang"] = lang
                tokens.append(token)
                continue

            heading = _ATX_RE.match(line)
            if heading:
                tokens.append(
                    {
                        "type": "heading",
                        "level": len(heading.group(1)),
                        "text": heading.group(2).strip(),
                        "children": [],
                        "attrs": {},
                    }
                )
                i += 1
                continue

            if _HR_RE.match(line):
                tokens.append({"type": "thematic_break"})
                i += 1
                continue

            if line.startswith("    "):
                body = []
                while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
                    body.append(lines[i][4:] if lines[i].startswith("    ") else "")
                    i += 1
                tokens.append({"type": "block_code", "text": "\n".join(body).rstrip("\n")})
                continue

            if line.lstrip().startswith(">") and len(line) - len(line.lstrip()) <= 3:
                quote_lines = []
                while i < len(lines):
                    current = lines[i]
                    stripped = current.lstrip()
                    indent = len(current) - len(stripped)
                    if stripped.startswith(">") and indent <= 3:
                        rest = stripped[1:]
                        if rest.startswith(" "):
                            rest = rest[1:]
                        quote_lines.append(rest)
                        i += 1
                    elif current.strip() == "":
                        quote_lines.append("")
                        i += 1
                    else:
                        break
                tokens.append({"type": "block_quote", "children": self._parse_blocks(quote_lines)})
                continue

            list_match = _UL_RE.match(line) or _OL_RE.match(line)
            if list_match:
                token, i = self._parse_list(lines, i, ordered=_OL_RE.match(line) is not None)
                tokens.append(token)
                continue

            if self.use_tables and i + 1 < len(lines) and self._is_table_start(lines[i], lines[i + 1]):
                table, i = self._parse_table(lines, i)
                tokens.append(table)
                continue

            para = []
            while i < len(lines) and lines[i].strip() != "":
                if para and self._starts_block(lines, i, allow_table=False):
                    break
                para.append(lines[i])
                i += 1
            tokens.append({"type": "paragraph", "text": "\n".join(para), "children": []})
        return tokens

    def _match_custom_block(self, line):
        for name, pattern, parse_func in self.block_rules:
            match = pattern.match(line)
            if match:
                fields = parse_func(match) or {}
                token = {"type": name}
                token.update(fields)
                return token
        return None

    def _starts_block(self, lines, index, allow_table=True):
        line = lines[index]
        if line.strip() == "":
            return True
        if _FENCE_RE.match(line) or _ATX_RE.match(line) or _HR_RE.match(line):
            return True
        if line.startswith("    "):
            return True
        if (line.lstrip().startswith(">") and len(line) - len(line.lstrip()) <= 3):
            return True
        if _UL_RE.match(line) or _OL_RE.match(line):
            return True
        if allow_table and self.use_tables and index + 1 < len(lines) and self._is_table_start(lines[index], lines[index + 1]):
            return True
        return self._match_custom_block(line) is not None

    def _parse_list(self, lines, start, ordered=False):
        items = []
        i = start
        matcher = _OL_RE if ordered else _UL_RE
        while i < len(lines):
            match = matcher.match(lines[i])
            if not match:
                break
            marker_indent = len(match.group(1))
            content = match.group(3)
            i += 1
            raw = [content]
            loose = False
            while i < len(lines):
                current = lines[i]
                if current.strip() == "":
                    if i + 1 < len(lines) and (lines[i + 1].startswith(" " * (marker_indent + 2))):
                        loose = True
                        raw.append("")
                        i += 1
                        continue
                    i += 1
                    break
                if matcher.match(current):
                    break
                if _UL_RE.match(current) or _OL_RE.match(current):
                    break
                if current.startswith(" " * (marker_indent + 2)):
                    raw.append(current[marker_indent + 2 :])
                    i += 1
                    continue
                break
            item_text = "\n".join(raw).strip("\n")
            item = {"type": "list_item", "text": item_text}
            if self.use_task_lists:
                task = re.match(r"^\[([ xX])\]\s*(.*)$", item_text, re.S)
                if task:
                    item["checked"] = task.group(1).lower() == "x"
                    item_text = task.group(2)
                    item["text"] = item_text
            if loose or "\n\n" in item_text:
                blocks = self._parse_blocks(item_text.split("\n"))
                item["blocks"] = blocks
            else:
                item["children"] = []
            items.append(item)
        return {"type": "list", "ordered": ordered, "items": items}, i

    def _split_table_row(self, line):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [part.strip() for part in line.split("|")]

    def _is_table_start(self, header, delim):
        if "|" not in header or "|" not in delim:
            return False
        cells = self._split_table_row(delim)
        if not cells:
            return False
        return all(re.match(r"^:?-{3,}:?$", cell.strip()) for cell in cells)

    def _parse_table(self, lines, start):
        headers = self._split_table_row(lines[start])
        delims = self._split_table_row(lines[start + 1])
        align = []
        for cell in delims:
            left, right = cell.startswith(":"), cell.endswith(":")
            align.append("center" if left and right else "left" if left else "right" if right else None)
        i = start + 2
        rows = []
        while i < len(lines) and lines[i].strip() and "|" in lines[i] and not self._starts_non_table_block(lines[i]):
            values = self._split_table_row(lines[i])
            while len(values) < len(headers):
                values.append("")
            rows.append(values[: len(headers)])
            i += 1
        return (
            {
                "type": "table",
                "header": [{"type": "table_cell", "text": cell, "children": []} for cell in headers],
                "align": align[: len(headers)],
                "rows": [
                    [{"type": "table_cell", "text": cell, "children": []} for cell in row]
                    for row in rows
                ],
            },
            i,
        )

    def _starts_non_table_block(self, line):
        return bool(_FENCE_RE.match(line) or _ATX_RE.match(line) or _HR_RE.match(line))

    def _parse_inline_blocks(self, tokens):
        for token in tokens:
            ttype = token.get("type")
            if ttype in ("paragraph", "heading"):
                token["children"] = self._parse_inlines(token.get("text", ""))
                if ttype == "heading":
                    token["text"] = re.sub(r"\s+", " ", _plain_inline(token["children"]).strip())
            elif ttype == "block_quote":
                self._parse_inline_blocks(token.get("children", []))
            elif ttype == "list":
                for item in token.get("items", []):
                    if item.get("blocks"):
                        self._parse_inline_blocks(item.get("blocks", []))
                    else:
                        item["children"] = self._parse_inlines(item.get("text", ""))
            elif ttype == "table":
                for cell in token.get("header", []):
                    cell["children"] = self._parse_inlines(cell.get("text", ""))
                for row in token.get("rows", []):
                    for cell in row:
                        cell["children"] = self._parse_inlines(cell.get("text", ""))
            elif "text" in token and "children" not in token and ttype != "block_code":
                token["children"] = self._parse_inlines(token.get("text", ""))
            elif token.get("children"):
                self._parse_inline_blocks(token.get("children", []))

    def _assign_heading_ids(self, tokens):
        used = set()
        for token in self.walk(tokens):
            if token.get("type") == "heading":
                token.setdefault("attrs", {})["id"] = _slugify(token.get("text", ""), used)

    def _parse_inlines(self, text):
        return self._parse_inline_range(str(text or ""), 0, len(str(text or "")))

    def _parse_inline_range(self, text, start, end):
        tokens = []
        pos = start
        while pos < end:
            custom = self._match_custom_inline(text, pos, end)
            if custom is not None:
                token, new_pos = custom
                tokens.append(token)
                pos = new_pos
                continue

            match = _INLINE_SPECIAL_RE.search(text, pos, end)
            custom_at = self._find_next_custom_inline(text, pos, end)
            next_start = None
            if match is not None:
                next_start = match.start()
            if custom_at is not None and (next_start is None or custom_at.start() < next_start):
                next_start = custom_at.start()
            if next_start is None:
                tokens.append({"type": "text", "text": text[pos:end]})
                break
            if next_start > pos:
                tokens.append({"type": "text", "text": text[pos:next_start]})
            pos = next_start
            custom = self._match_custom_inline(text, pos, end)
            if custom is not None:
                token, new_pos = custom
                tokens.append(token)
                pos = new_pos
                continue

            if text.startswith("\\\n", pos):
                tokens.append({"type": "line_break", "text": "\n"})
                pos += 2
            elif text.startswith("\\", pos):
                if pos + 1 < end and text[pos + 1] in _PUNCT:
                    tokens.append({"type": "text", "text": text[pos + 1]})
                    pos += 2
                else:
                    tokens.append({"type": "text", "text": "\\"})
                    pos += 1
            elif text.startswith("  \n", pos):
                space_end = pos
                while space_end < end and text[space_end] == " ":
                    space_end += 1
                if space_end < end and text[space_end] == "\n" and space_end - pos >= 2:
                    tokens.append({"type": "line_break", "text": "\n"})
                    pos = space_end + 1
                else:
                    tokens.append({"type": "text", "text": text[pos]})
                    pos += 1
            elif text[pos] == "\n":
                tokens.append({"type": "soft_break", "text": "\n"})
                pos += 1
            elif text[pos] == "`":
                token, new_pos = self._parse_code_span(text, pos, end)
                tokens.append(token)
                pos = new_pos
            elif text.startswith("![", pos):
                parsed = self._parse_link_or_image(text, pos, end, image=True)
                if parsed:
                    token, pos = parsed
                    tokens.append(token)
                else:
                    tokens.append({"type": "text", "text": "!"})
                    pos += 1
            elif text.startswith("[", pos):
                parsed = self._parse_link_or_image(text, pos, end, image=False)
                if parsed:
                    token, pos = parsed
                    tokens.append(token)
                else:
                    tokens.append({"type": "text", "text": "["})
                    pos += 1
            elif text[pos] == "<":
                parsed = self._parse_autolink(text, pos, end)
                if parsed:
                    token, pos = parsed
                    tokens.append(token)
                else:
                    tokens.append({"type": "text", "text": "<"})
                    pos += 1
            elif text.startswith("**", pos) or text.startswith("__", pos):
                parsed = self._parse_delimited(text, pos, end, text[pos : pos + 2], "strong")
                if parsed:
                    token, pos = parsed
                    tokens.append(token)
                else:
                    tokens.append({"type": "text", "text": text[pos : pos + 2]})
                    pos += 2
            elif text[pos] in "*_":
                parsed = self._parse_delimited(text, pos, end, text[pos], "emphasis")
                if parsed:
                    token, pos = parsed
                    tokens.append(token)
                else:
                    tokens.append({"type": "text", "text": text[pos]})
                    pos += 1
            elif text.startswith("~~", pos):
                tokens.append({"type": "text", "text": "~~"})
                pos += 2
            else:
                tokens.append({"type": "text", "text": text[pos]})
                pos += 1
        return _merge_text(tokens)

    def _match_custom_inline(self, text, pos, end):
        for name, pattern, parse_func in self.inline_rules:
            match = pattern.match(text, pos, end)
            if match:
                fields = parse_func(match) or {}
                token = {"type": name}
                token.update(fields)
                return token, match.end()
        return None

    def _find_next_custom_inline(self, text, pos, end):
        best = None
        for _name, pattern, _parse_func in self.inline_rules:
            match = pattern.search(text, pos, end)
            if match and (best is None or match.start() < best.start()):
                best = match
        return best

    def _parse_code_span(self, text, pos, end):
        run_end = pos
        while run_end < end and text[run_end] == "`":
            run_end += 1
        marker = text[pos:run_end]
        close = text.find(marker, run_end, end)
        if close < 0:
            return {"type": "text", "text": marker}, run_end
        body = text[run_end:close].replace("\n", " ")
        if body.startswith(" ") and body.endswith(" ") and len(body.strip()) > 0:
            body = body[1:-1]
        return {"type": "code_span", "text": body}, close + len(marker)

    def _parse_delimited(self, text, pos, end, marker, token_type):
        close = self._find_closer(text, pos + len(marker), end, marker)
        if close < 0 or close == pos + len(marker):
            return None
        inner = text[pos + len(marker) : close]
        return {"type": token_type, "children": self._parse_inlines(inner)}, close + len(marker)

    def _find_closer(self, text, start, end, marker):
        i = start
        while True:
            found = text.find(marker, i, end)
            if found < 0:
                return -1
            if found == 0 or text[found - 1] != "\\":
                return found
            i = found + len(marker)

    def _find_label_end(self, text, start, end):
        depth = 0
        i = start
        while i < end:
            char = text[i]
            if char == "\\":
                i += 2
                continue
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _parse_link_or_image(self, text, pos, end, image=False):
        label_start = pos + (2 if image else 1)
        label_end = self._find_label_end(text, pos + (1 if image else 0), end)
        if label_end < 0 or label_end + 1 >= end or text[label_end + 1] != "(":
            return None
        dest_end = self._find_link_dest_end(text, label_end + 2, end)
        if dest_end < 0:
            return None
        inside = text[label_end + 2 : dest_end].strip()
        if not inside:
            return None
        url, title = self._split_link_dest(inside)
        if url is None:
            return None
        label = text[label_start:label_end]
        if image:
            return (
                {
                    "type": "image",
                    "url": url,
                    "title": title,
                    "alt": _plain_inline(self._parse_inlines(label)),
                    "children": self._parse_inlines(label),
                },
                dest_end + 1,
            )
        return (
            {"type": "link", "url": url, "title": title, "children": self._parse_inlines(label)},
            dest_end + 1,
        )

    def _find_link_dest_end(self, text, start, end):
        depth = 1
        i = start
        in_quote = None
        while i < end:
            char = text[i]
            if char == "\\":
                i += 2
                continue
            if in_quote:
                if char == in_quote:
                    in_quote = None
            elif char in ("'", '"'):
                in_quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _split_link_dest(self, inside):
        match = re.match(r'^(<[^>\n]*>|\S+)(?:\s+(".*?"|\'.*?\'))?$', inside, re.S)
        if not match:
            return None, None
        url = match.group(1)
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]
        title = match.group(2)
        if title is not None:
            title = title[1:-1]
        return url, title

    def _parse_autolink(self, text, pos, end):
        close = text.find(">", pos + 1, end)
        if close < 0:
            return None
        body = text[pos + 1 : close]
        if body.startswith(("http://", "https://")):
            return {"type": "link", "url": body, "children": [{"type": "text", "text": body}]}, close + 1
        if _EMAIL_RE.match(body):
            return {"type": "link", "url": "mailto:" + body, "children": [{"type": "text", "text": body}]}, close + 1
        return None


def _merge_text(tokens):
    merged = []
    for token in tokens:
        if token.get("type") == "text" and merged and merged[-1].get("type") == "text":
            merged[-1]["text"] += token.get("text", "")
        else:
            merged.append(token)
    return merged


__all__ = ["Markdown", "HTMLRenderer", "ASTRenderer", "escape_html"]
