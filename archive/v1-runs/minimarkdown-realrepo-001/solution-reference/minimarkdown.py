import copy
import html
import posixpath
import re


def escape_html(value):
    return html.escape(str(value), quote=True)


def _plain_text(tokens):
    parts = []
    for token in tokens or []:
        kind = token.get("type")
        if kind in {"text", "code_span"}:
            parts.append(token.get("text", ""))
        elif kind in {"soft_break", "softbreak"}:
            parts.append("\n")
        elif kind in {"line_break", "hardbreak"}:
            parts.append("\n")
        elif "children" in token:
            parts.append(_plain_text(token.get("children", [])))
        elif kind == "image":
            parts.append(_plain_text(token.get("children", [])))
    return "".join(parts)


def _slugify_heading(text):
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


class ASTRenderer:
    def render(self, tokens):
        return self._clean(tokens)

    def _clean(self, value):
        if isinstance(value, list):
            return [self._clean(item) for item in value]
        if isinstance(value, dict):
            return {
                key: self._clean(val)
                for key, val in value.items()
                if not callable(val) and not key.startswith("_")
            }
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)


class HTMLRenderer:
    def __init__(self):
        self.custom_renderers = {}

    def register(self, name, render_func):
        self.custom_renderers[name] = render_func

    def render(self, tokens):
        return "\n".join(self.render_block(token) for token in tokens)

    def render_block(self, token):
        kind = token["type"]
        if kind in self.custom_renderers:
            return self._call_custom(kind, token)
        method = getattr(self, "render_" + kind, None)
        if method is None:
            return self.render_inline(token)
        return method(token)

    def render_inlines(self, tokens):
        return "".join(self.render_inline(token) for token in tokens)

    def render_inline(self, token):
        kind = token["type"]
        if kind in self.custom_renderers:
            return self._call_custom(kind, token)
        method = getattr(self, "render_inline_" + kind, None)
        if method is None:
            return escape_html(token.get("text", ""))
        return method(token)

    def _call_custom(self, kind, token):
        func = self.custom_renderers[kind]
        for args in ((self, token), (token,)):
            try:
                return func(*args)
            except TypeError:
                pass
        return func(**token)

    def render_heading(self, token):
        level = int(token.get("level", 1))
        attrs = token.get("attrs") or {}
        ident = attrs.get("id")
        id_attr = f' id="{escape_html(ident)}"' if ident else ""
        return f"<h{level}{id_attr}>{self.render_inlines(token.get('children', []))}</h{level}>"

    def render_paragraph(self, token):
        return f"<p>{self.render_inlines(token.get('children', []))}</p>"

    def render_block_code(self, token):
        text = escape_html(token.get("text", ""))
        lang = token.get("lang")
        if lang:
            return f'<pre><code class="language-{escape_html(lang)}">{text}</code></pre>'
        return f"<pre><code>{text}</code></pre>"

    def render_block_quote(self, token):
        body = self.render(token.get("children", []))
        return f"<blockquote>\n{body}\n</blockquote>"

    def render_thematic_break(self, token):
        return "<hr>"

    def render_list(self, token):
        tag = "ol" if token.get("ordered") else "ul"
        items = "\n".join(self.render_list_item(item) for item in token.get("items", []))
        return f"<{tag}>\n{items}\n</{tag}>"

    def render_list_item(self, token):
        prefix = ""
        if "checked" in token:
            checked = " checked" if token.get("checked") else ""
            prefix = f'<input type="checkbox" disabled{checked}> '
        if token.get("loose"):
            body = self.render(token.get("children", []))
            if body:
                return f"<li>{prefix}{body}</li>"
            return f"<li>{prefix}</li>"
        body = self.render_inlines(token.get("children", []))
        return f"<li>{prefix}{body}</li>"

    def render_table(self, token):
        aligns = token.get("align", [])

        def attr(index):
            value = aligns[index] if index < len(aligns) else None
            return f' align="{value}"' if value else ""

        head_cells = "".join(
            f"<th{attr(i)}>{self.render_inlines(cell.get('children', []))}</th>"
            for i, cell in enumerate(token.get("header", []))
        )
        body_rows = []
        for row in token.get("rows", []):
            cells = "".join(
                f"<td{attr(i)}>{self.render_inlines(cell.get('children', []))}</td>"
                for i, cell in enumerate(row)
            )
            body_rows.append(f"<tr>{cells}</tr>")
        tbody = "\n".join(body_rows)
        return f"<table>\n<thead><tr>{head_cells}</tr></thead>\n<tbody>\n{tbody}\n</tbody>\n</table>"

    def render_inline_text(self, token):
        return escape_html(token.get("text", ""))

    def render_inline_softbreak(self, token):
        return "\n"

    def render_inline_soft_break(self, token):
        return "\n"

    def render_inline_hardbreak(self, token):
        return "<br>\n"

    def render_inline_line_break(self, token):
        return "<br>\n"

    def render_inline_emphasis(self, token):
        return f"<em>{self.render_inlines(token.get('children', []))}</em>"

    def render_inline_strong(self, token):
        return f"<strong>{self.render_inlines(token.get('children', []))}</strong>"

    def render_inline_code_span(self, token):
        return f"<code>{escape_html(token.get('text', ''))}</code>"

    def render_inline_link(self, token):
        href = escape_html(token.get("url", ""))
        title = token.get("title")
        title_attr = f' title="{escape_html(title)}"' if title is not None else ""
        return f'<a href="{href}"{title_attr}>{self.render_inlines(token.get("children", []))}</a>'

    def render_inline_image(self, token):
        src = escape_html(token.get("url", ""))
        alt = escape_html(_plain_text(token.get("children", [])))
        title = token.get("title")
        title_attr = f' title="{escape_html(title)}"' if title is not None else ""
        return f'<img src="{src}" alt="{alt}"{title_attr}>'

    def render_inline_strikethrough(self, token):
        return f"<del>{self.render_inlines(token.get('children', []))}</del>"


class Markdown:
    def __init__(self, renderer=None, plugins=None):
        self.inline_rules = []
        self.block_rules = []
        self.enabled_plugins = set()
        if renderer is None:
            self.renderer = HTMLRenderer()
        elif renderer == "ast":
            self.renderer = ASTRenderer()
        else:
            self.renderer = renderer
        for plugin in plugins or []:
            self._load_plugin(plugin)

    def __call__(self, text):
        return self.markdown(text)

    def markdown(self, text):
        tokens = self.parse(text)
        return self.renderer.render(tokens)

    def tokens(self, text):
        return self.parse(text)

    def render(self, tokens, renderer=None):
        active = self.renderer
        if renderer is not None:
            active = ASTRenderer() if renderer == "ast" else renderer
        return active.render(copy.deepcopy(tokens))

    def parse(self, text):
        tokens = self._parse_blocks(str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"))
        self._attach_heading_ids(tokens)
        return tokens

    def walk(self, tokens):
        if isinstance(tokens, dict):
            yield tokens
            values = tokens.values()
        elif isinstance(tokens, list):
            values = tokens
        else:
            return
        for value in values:
            if isinstance(value, dict):
                yield from self.walk(value)
            elif isinstance(value, list):
                for item in value:
                    yield from self.walk(item)

    def toc(self, text):
        entries = []
        for token in self._walk_blocks(self.parse(text)):
            if token.get("type") == "heading":
                entries.append(
                    {
                        "level": int(token.get("level", 1)),
                        "text": _plain_text(token.get("children", [])),
                        "id": (token.get("attrs") or {}).get("id", ""),
                    }
                )
        return entries

    def _attach_heading_ids(self, tokens):
        seen = {}
        for token in self._walk_blocks(tokens):
            if token.get("type") != "heading":
                continue
            base = _slugify_heading(_plain_text(token.get("children", [])))
            count = seen.get(base, 0) + 1
            seen[base] = count
            ident = base if count == 1 else f"{base}-{count}"
            attrs = dict(token.get("attrs") or {})
            attrs["id"] = ident
            token["attrs"] = attrs

    def _walk_blocks(self, tokens):
        for token in tokens or []:
            yield token
            for child in token.get("children", []) or []:
                if isinstance(child, dict) and child.get("type") in {
                    "heading",
                    "paragraph",
                    "block_code",
                    "block_quote",
                    "list",
                    "table",
                    "thematic_break",
                }:
                    yield from self._walk_blocks([child])
            for item in token.get("items", []) or []:
                yield from self._walk_blocks(item.get("children", []))

    def register_inline(self, name, pattern, parse_func, render_func=None):
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.inline_rules.append((name, compiled, parse_func))
        if render_func is not None and hasattr(self.renderer, "register"):
            self.renderer.register(name, render_func)

    def register_block(self, name, pattern, parse_func, render_func=None):
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.block_rules.append((name, compiled, parse_func))
        if render_func is not None and hasattr(self.renderer, "register"):
            self.renderer.register(name, render_func)

    def _load_plugin(self, plugin):
        if callable(plugin):
            plugin(self)
            return
        if plugin == "strikethrough":
            self.enabled_plugins.add("strikethrough")
            return
        if plugin == "table":
            self.enabled_plugins.add("table")
            return
        if plugin == "task_list":
            self.enabled_plugins.add("task_list")
            return
        raise ValueError(f"unknown plugin: {plugin}")

    def _parse_blocks(self, lines):
        tokens = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                i += 1
                continue
            if "table" in self.enabled_plugins and self._is_table_start(lines, i):
                token, i = self._parse_table(lines, i)
                tokens.append(token)
                continue
            custom = self._try_custom_block(lines, i)
            if custom:
                token, i = custom
                tokens.append(token)
                continue
            match = re.match(r"^(#{1,6})\s+(.*?)(?:\s+#+\s*)?$", line)
            if match:
                tokens.append(
                    {
                        "type": "heading",
                        "level": len(match.group(1)),
                        "text": match.group(2),
                        "children": self._parse_inlines(match.group(2)),
                    }
                )
                i += 1
                continue
            if re.match(r"^\s{0,3}```", line):
                token, i = self._parse_fenced_code(lines, i)
                tokens.append(token)
                continue
            if re.match(r"^(?: {4}|\t)", line):
                token, i = self._parse_indented_code(lines, i)
                tokens.append(token)
                continue
            if self._is_hr(line):
                tokens.append({"type": "thematic_break"})
                i += 1
                continue
            if re.match(r"^\s{0,3}>", line):
                token, i = self._parse_block_quote(lines, i)
                tokens.append(token)
                continue
            if self._list_match(line):
                token, i = self._parse_list(lines, i)
                tokens.append(token)
                continue
            token, i = self._parse_paragraph(lines, i)
            tokens.append(token)
        return tokens

    def _try_custom_block(self, lines, i):
        remaining = "\n".join(lines[i:])
        for name, pattern, parse_func in self.block_rules:
            match = pattern.match(remaining)
            if not match:
                continue
            token = self._call_parse_func(parse_func, match)
            if token is None:
                continue
            consumed = max(1, remaining[: match.end()].count("\n") + 1)
            if isinstance(token, str):
                token = {"type": name, "text": token}
            else:
                token = dict(token)
                token.setdefault("type", name)
            return token, i + consumed
        return None

    def _parse_paragraph(self, lines, i):
        collected = []
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                break
            if collected and self._starts_block(lines, i):
                break
            collected.append(line)
            i += 1
        text = "\n".join(collected)
        return {"type": "paragraph", "text": text, "children": self._parse_inlines(text)}, i

    def _starts_block(self, lines, i):
        line = lines[i]
        return bool(
            re.match(r"^(#{1,6})\s+", line)
            or re.match(r"^\s{0,3}```", line)
            or re.match(r"^(?: {4}|\t)", line)
            or re.match(r"^\s{0,3}>", line)
            or self._list_match(line)
            or self._is_hr(line)
        )

    def _parse_fenced_code(self, lines, i):
        opener = lines[i]
        match = re.match(r"^\s{0,3}(`{3,})\s*([^`]*)$", opener)
        fence = match.group(1)
        lang = match.group(2).strip() or None
        i += 1
        body = []
        while i < len(lines):
            if re.match(r"^\s{0,3}" + re.escape(fence) + r"`*\s*$", lines[i]):
                i += 1
                break
            body.append(lines[i])
            i += 1
        return {"type": "block_code", "text": "\n".join(body), "lang": lang}, i

    def _parse_indented_code(self, lines, i):
        body = []
        while i < len(lines):
            line = lines[i]
            if re.match(r"^(?: {4}|\t)", line):
                body.append(re.sub(r"^(?: {4}|\t)", "", line))
                i += 1
            elif line.strip() == "":
                body.append("")
                i += 1
            else:
                break
        return {"type": "block_code", "text": "\n".join(body), "lang": None}, i

    def _parse_block_quote(self, lines, i):
        inner = []
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                inner.append("")
                i += 1
                continue
            if not re.match(r"^\s{0,3}>", line):
                break
            inner.append(re.sub(r"^\s{0,3}>\s?", "", line))
            i += 1
        return {"type": "block_quote", "children": self._parse_blocks(inner)}, i

    def _list_match(self, line):
        return re.match(r"^\s{0,3}(?:(?P<ul>[-*+])|(?P<ol>\d+\.))\s+(?P<body>.*)$", line)

    def _parse_list(self, lines, i):
        first = self._list_match(lines[i])
        ordered = bool(first.group("ol"))
        items = []
        while i < len(lines):
            match = self._list_match(lines[i])
            if not match or bool(match.group("ol")) != ordered:
                break
            item_lines = [match.group("body")]
            i += 1
            loose = False
            while i < len(lines):
                nxt = lines[i]
                nxt_match = self._list_match(nxt)
                if nxt_match and bool(nxt_match.group("ol")) == ordered:
                    break
                if nxt.strip() == "":
                    if i + 1 < len(lines) and lines[i + 1].startswith((" ", "\t")):
                        loose = True
                        item_lines.append("")
                        i += 1
                        continue
                    break
                if nxt.startswith(("  ", "    ", "\t")):
                    item_lines.append(re.sub(r"^(?: {2,4}|\t)", "", nxt))
                    i += 1
                    continue
                break
            items.append(self._make_list_item(item_lines, loose))
            while i < len(lines) and lines[i].strip() == "":
                if i + 1 < len(lines) and self._list_match(lines[i + 1]):
                    loose = True
                    i += 1
                    break
                break
        return {"type": "list", "ordered": ordered, "items": items}, i

    def _make_list_item(self, item_lines, loose):
        text = "\n".join(item_lines).strip("\n")
        token = {"type": "list_item", "loose": loose}
        if "task_list" in self.enabled_plugins:
            match = re.match(r"^\[( |x|X)\]\s+(.*)$", text, re.S)
            if match:
                token["checked"] = match.group(1).lower() == "x"
                text = match.group(2)
        if loose or "\n\n" in text:
            token["loose"] = True
            token["children"] = self._parse_blocks(text.split("\n"))
        else:
            inline_text = " ".join(part.strip() for part in text.split("\n") if part.strip())
            token["text"] = inline_text
            token["children"] = self._parse_inlines(inline_text)
        return token

    def _is_hr(self, line):
        stripped = line.strip().replace(" ", "")
        return len(stripped) >= 3 and len(set(stripped)) == 1 and stripped[0] in "-_*"

    def _split_table_row(self, line):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [cell.strip() for cell in line.split("|")]

    def _is_table_start(self, lines, i):
        if i + 1 >= len(lines) or "|" not in lines[i]:
            return False
        header = self._split_table_row(lines[i])
        delim = self._split_table_row(lines[i + 1])
        if len(header) < 2 or len(delim) != len(header):
            return False
        return all(re.match(r"^:?-{3,}:?$", cell.strip()) for cell in delim)

    def _parse_table(self, lines, i):
        header_text = self._split_table_row(lines[i])
        delim = self._split_table_row(lines[i + 1])
        aligns = []
        for cell in delim:
            left = cell.startswith(":")
            right = cell.endswith(":")
            aligns.append("center" if left and right else "left" if left else "right" if right else None)
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip() and "|" in lines[i]:
            cells = self._split_table_row(lines[i])
            while len(cells) < len(header_text):
                cells.append("")
            rows.append(cells[: len(header_text)])
            i += 1
        return {
            "type": "table",
            "align": aligns,
            "header": [{"type": "table_cell", "text": cell, "children": self._parse_inlines(cell)} for cell in header_text],
            "rows": [
                [{"type": "table_cell", "text": cell, "children": self._parse_inlines(cell)} for cell in row]
                for row in rows
            ],
        }, i

    def _parse_inlines(self, text):
        text = str(text)
        tokens = []
        i = 0
        while i < len(text):
            custom = self._try_custom_inline(text, i)
            if custom:
                token, end = custom
                self._append_token(tokens, token)
                i = end
                continue
            if text[i] == "\\":
                if i + 1 < len(text) and text[i + 1] == "\n":
                    tokens.append({"type": "line_break"})
                    i += 2
                    continue
                if i + 1 < len(text) and text[i + 1] in r"\`*_{}[]()#+-.!|~<>":
                    self._append_text(tokens, text[i + 1])
                    i += 2
                    continue
            if text[i] == "\n":
                if tokens and tokens[-1]["type"] == "text" and tokens[-1]["text"].endswith("  "):
                    tokens[-1]["text"] = tokens[-1]["text"][:-2]
                    if tokens[-1]["text"] == "":
                        tokens.pop()
                    tokens.append({"type": "line_break"})
                else:
                    tokens.append({"type": "soft_break"})
                i += 1
                continue
            if text[i] == "`":
                end = text.find("`", i + 1)
                if end != -1:
                    tokens.append({"type": "code_span", "text": text[i + 1 : end]})
                    i = end + 1
                    continue
            if text.startswith("![", i):
                parsed = self._parse_link_or_image(text, i, image=True)
                if parsed:
                    token, end = parsed
                    tokens.append(token)
                    i = end
                    continue
            if text.startswith("[", i):
                parsed = self._parse_link_or_image(text, i, image=False)
                if parsed:
                    token, end = parsed
                    tokens.append(token)
                    i = end
                    continue
            if text[i] == "<":
                parsed = self._parse_autolink(text, i)
                if parsed:
                    token, end = parsed
                    tokens.append(token)
                    i = end
                    continue
            if text.startswith("**", i) or text.startswith("__", i):
                marker = text[i : i + 2]
                end = text.find(marker, i + 2)
                if end != -1:
                    body = text[i + 2 : end]
                    tokens.append({"type": "strong", "children": self._parse_inlines(body), "text": body})
                    i = end + 2
                    continue
            if "strikethrough" in self.enabled_plugins and text.startswith("~~", i):
                end = text.find("~~", i + 2)
                if end != -1:
                    body = text[i + 2 : end]
                    tokens.append({"type": "strikethrough", "children": self._parse_inlines(body), "text": body})
                    i = end + 2
                    continue
            if text[i] in "*_":
                marker = text[i]
                if (i + 1 < len(text) and text[i + 1] == marker) or (i > 0 and text[i - 1] == marker):
                    self._append_text(tokens, text[i])
                    i += 1
                    continue
                end = text.find(marker, i + 1)
                if end != -1 and end > i + 1:
                    body = text[i + 1 : end]
                    tokens.append({"type": "emphasis", "children": self._parse_inlines(body), "text": body})
                    i = end + 1
                    continue
            self._append_text(tokens, text[i])
            i += 1
        return tokens

    def _try_custom_inline(self, text, i):
        for name, pattern, parse_func in self.inline_rules:
            match = pattern.match(text, i)
            if not match:
                continue
            token = self._call_parse_func(parse_func, match)
            if token is None:
                continue
            if isinstance(token, str):
                token = {"type": name, "text": token}
            else:
                token = dict(token)
                token.setdefault("type", name)
            return token, match.end()
        return None

    def _call_parse_func(self, parse_func, match):
        for args in ((self, match), (match, self), (match,)):
            try:
                return parse_func(*args)
            except TypeError:
                pass
        return parse_func(match)

    def _parse_link_or_image(self, text, i, image=False):
        label_start = i + 2 if image else i + 1
        label_end = self._find_closing(text, label_start, "[", "]")
        if label_end == -1 or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            return None
        dest_end = self._find_closing(text, label_end + 2, "(", ")")
        if dest_end == -1:
            return None
        label = text[label_start:label_end]
        dest = text[label_end + 2 : dest_end].strip()
        match = re.match(r'^(?P<url>\S+?)(?:\s+"(?P<title>.*)")?$', dest)
        if not match:
            return None
        token = {
            "type": "image" if image else "link",
            "url": match.group("url"),
            "title": match.group("title"),
            "children": self._parse_inlines(label),
            "text": label,
        }
        if token["title"] is None:
            token.pop("title")
        return token, dest_end + 1

    def _find_closing(self, text, start, opener, closer):
        depth = 0
        i = start
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                if depth == 0:
                    return i
                depth -= 1
            i += 1
        return -1

    def _parse_autolink(self, text, i):
        end = text.find(">", i + 1)
        if end == -1:
            return None
        body = text[i + 1 : end]
        if re.match(r"^https?://[^\s<>]+$", body):
            return {"type": "link", "url": body, "children": [{"type": "text", "text": body}]}, end + 1
        if re.match(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$", body):
            return {"type": "link", "url": "mailto:" + body, "children": [{"type": "text", "text": body}]}, end + 1
        return None

    def _append_text(self, tokens, text):
        if text:
            if tokens and tokens[-1]["type"] == "text":
                tokens[-1]["text"] += text
            else:
                tokens.append({"type": "text", "text": text})

    def _append_token(self, tokens, token):
        if token.get("type") == "text":
            self._append_text(tokens, token.get("text", ""))
        else:
            tokens.append(token)


class MarkdownWorkspace:
    def __init__(self, renderer=None, plugins=None):
        self._parser = Markdown(renderer=renderer, plugins=plugins)
        self._sources = {}
        self._trees = {}

    @staticmethod
    def _normalize_path(path):
        value = str(path).replace("\\", "/").strip()
        if not value:
            raise ValueError("document path must be non-empty")
        value = posixpath.normpath(value)
        if value == "." or value == ".." or value.startswith("../"):
            raise ValueError("document path must stay inside the workspace")
        return value

    @staticmethod
    def _normalize_anchor(anchor):
        if anchor in (None, ""):
            return None
        return str(anchor).lstrip("#")

    def update(self, path, text):
        if not isinstance(text, str):
            raise TypeError("document text must be a string")
        doc = self._normalize_path(path)
        tree = self._parser.parse(text)
        self._sources[doc] = text
        self._trees[doc] = tree
        return self

    def remove(self, path):
        doc = self._normalize_path(path)
        self._sources.pop(doc, None)
        self._trees.pop(doc, None)
        return self

    def paths(self):
        return sorted(self._sources)

    def tokens(self, path):
        doc = self._normalize_path(path)
        return copy.deepcopy(self._trees[doc])

    def render(self, path, renderer=None):
        return self._parser.render(self.tokens(path), renderer=renderer)

    def toc(self, path=None):
        docs = [self._normalize_path(path)] if path is not None else self.paths()
        entries = []
        for doc in docs:
            for token in self._parser._walk_blocks(self._trees.get(doc, [])):
                if token.get("type") == "heading":
                    entries.append(
                        {
                            "doc": doc,
                            "level": int(token.get("level", 1)),
                            "text": _plain_text(token.get("children", [])),
                            "id": (token.get("attrs") or {}).get("id", ""),
                        }
                    )
        return entries

    def links(self, path=None):
        docs = [self._normalize_path(path)] if path is not None else self.paths()
        rows = []
        for doc in docs:
            order = 0
            for token in self._parser.walk(self._trees.get(doc, [])):
                if not isinstance(token, dict) or token.get("type") not in {"link", "image"}:
                    continue
                parsed = self._parse_reference(doc, token.get("url", ""))
                if parsed is None:
                    continue
                target_doc, target_anchor = parsed
                rows.append(
                    {
                        "source": doc,
                        "target": target_doc,
                        "anchor": target_anchor,
                        "text": _plain_text(token.get("children", [])),
                        "kind": token.get("type"),
                        "resolved": self._is_resolved(target_doc, target_anchor),
                        "order": order,
                    }
                )
                order += 1
        return rows

    def backlinks(self, path, anchor=None):
        doc = self._normalize_path(path)
        normalized_anchor = self._normalize_anchor(anchor)
        return [
            copy.deepcopy(row)
            for row in self.links()
            if row["target"] == doc
            and (normalized_anchor is None or row.get("anchor") == normalized_anchor)
        ]

    def diagnostics(self):
        rows = []
        for link in self.links():
            if link["resolved"]:
                continue
            missing_type = "missing_document"
            if link["target"] in self._sources and link.get("anchor"):
                missing_type = "missing_anchor"
            rows.append(
                {
                    "type": missing_type,
                    "source": link["source"],
                    "target": link["target"],
                    "anchor": link.get("anchor"),
                    "text": link.get("text", ""),
                }
            )
        return rows

    def graph(self):
        return {
            "documents": self.paths(),
            "headings": self.toc(),
            "links": self.links(),
            "diagnostics": self.diagnostics(),
        }

    def export(self):
        return {
            "version": 1,
            "documents": [
                {"path": path, "source": self._sources[path]}
                for path in self.paths()
            ],
        }

    @classmethod
    def import_snapshot(cls, snapshot, renderer=None, plugins=None):
        workspace = cls(renderer=renderer, plugins=plugins)
        for row in snapshot.get("documents", []):
            workspace.update(row["path"], row.get("source", ""))
        return workspace

    def _parse_reference(self, source_doc, url):
        url = str(url or "")
        if not url or re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I):
            return None
        target, hash_mark, anchor = url.partition("#")
        if not target:
            target_doc = source_doc
        else:
            base = posixpath.dirname(source_doc)
            target_doc = self._normalize_path(posixpath.join(base, target))
        return target_doc, self._normalize_anchor(anchor if hash_mark else None)

    def _is_resolved(self, target_doc, target_anchor):
        if target_doc not in self._sources:
            return False
        if target_anchor is None:
            return True
        return target_anchor in {entry["id"] for entry in self.toc(target_doc)}
