import copy
import json
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit


_PUNCT = r"\\`*_\{\}\[\]\(\)#\+\-\.!|~<>"


def escape_html(value):
    """Escape text for HTML text nodes and attributes."""
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _normalize_newlines(text):
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


def _plain_text(tokens):
    parts = []
    for token in tokens or []:
        typ = token.get("type")
        if typ in ("text", "code_span"):
            parts.append(token.get("text", ""))
        elif typ == "soft_break":
            parts.append("\n")
        elif typ == "line_break":
            parts.append("\n")
        elif typ == "image":
            parts.append(token.get("alt", ""))
        elif "children" in token:
            parts.append(_plain_text(token.get("children", [])))
        elif "text" in token:
            parts.append(token.get("text", ""))
    return "".join(parts)


def _slugify(text):
    text = (text or "").lower()
    out = []
    last_dash = False
    for ch in text:
        if "a" <= ch <= "z" or "0" <= ch <= "9":
            out.append(ch)
            last_dash = False
        else:
            if not last_dash:
                out.append("-")
                last_dash = True
    slug = "".join(out).strip("-")
    return slug or "section"


def _has_scheme(url):
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url or ""))


def _split_link_url(url):
    if url is None:
        return "", None
    raw = url.strip()
    if "#" in raw:
        target, anchor = raw.split("#", 1)
        return target, anchor
    return raw, None


class ASTRenderer:
    def render(self, tokens):
        return copy.deepcopy(tokens)


class HTMLRenderer:
    def __init__(self):
        self.inline_renderers = {}
        self.block_renderers = {}

    def add_inline(self, name, func):
        self.inline_renderers[name] = func

    def add_block(self, name, func):
        self.block_renderers[name] = func

    def render(self, tokens):
        return "\n".join(self.render_block(token) for token in tokens)

    def render_blocks(self, tokens):
        return "\n".join(self.render_block(token) for token in tokens)

    def render_inlines(self, tokens):
        return "".join(self.render_inline(token) for token in (tokens or []))

    def _children_or_text(self, token):
        if token.get("children"):
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))

    def render_block(self, token):
        typ = token.get("type")
        if typ in self.block_renderers:
            return self.block_renderers[typ](self, token)
        method = getattr(self, "render_" + typ, None)
        if method is not None:
            return method(token)
        if "children" in token:
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))

    def render_inline(self, token):
        typ = token.get("type")
        if typ in self.inline_renderers:
            return self.inline_renderers[typ](self, token)
        method = getattr(self, "render_inline_" + typ, None)
        if method is not None:
            return method(token)
        if "children" in token:
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))

    def render_paragraph(self, token):
        return "<p>" + self._children_or_text(token) + "</p>"

    def render_heading(self, token):
        level = max(1, min(6, int(token.get("level", 1))))
        attrs = token.get("attrs") or {}
        ident = escape_html(attrs.get("id", ""))
        return f'<h{level} id="{ident}">' + self._children_or_text(token) + f"</h{level}>"

    def render_block_code(self, token):
        text = escape_html(token.get("text", ""))
        lang = token.get("lang")
        if lang:
            return f'<pre><code class="language-{escape_html(lang)}">{text}</code></pre>'
        return f"<pre><code>{text}</code></pre>"

    def render_block_quote(self, token):
        return "<blockquote>\n" + self.render_blocks(token.get("children", [])) + "\n</blockquote>"

    def render_list(self, token):
        tag = "ol" if token.get("ordered") else "ul"
        items = []
        for item in token.get("items", []):
            pieces = []
            if "checked" in item:
                checked = " checked" if item.get("checked") else ""
                pieces.append(f'<input type="checkbox" disabled{checked}> ')
            if item.get("loose") and item.get("blocks"):
                pieces.append(self.render_blocks(item.get("blocks", [])))
            else:
                pieces.append(self._children_or_text(item))
                if item.get("blocks"):
                    block_html = self.render_blocks(item.get("blocks", []))
                    if block_html:
                        pieces.append("\n" + block_html)
            items.append("<li>" + "".join(pieces) + "</li>")
        return f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>"

    def render_thematic_break(self, token):
        return "<hr>"

    def render_table(self, token):
        def cell_tag(tag, cell, align=None):
            attrs = f' style="text-align: {escape_html(align)}"' if align else ""
            return f"<{tag}{attrs}>" + self._children_or_text(cell) + f"</{tag}>"

        align = token.get("align", [])
        head_cells = [
            cell_tag("th", cell, align[i] if i < len(align) else None)
            for i, cell in enumerate(token.get("header", []))
        ]
        rows = []
        for row in token.get("rows", []):
            rows.append(
                "<tr>"
                + "".join(
                    cell_tag("td", cell, align[i] if i < len(align) else None)
                    for i, cell in enumerate(row)
                )
                + "</tr>"
            )
        body = "<thead><tr>" + "".join(head_cells) + "</tr></thead>"
        if rows:
            body += "\n<tbody>\n" + "\n".join(rows) + "\n</tbody>"
        return "<table>\n" + body + "\n</table>"

    def render_inline_text(self, token):
        return escape_html(token.get("text", ""))

    def render_inline_emphasis(self, token):
        return "<em>" + self.render_inlines(token.get("children", [])) + "</em>"

    def render_inline_strong(self, token):
        return "<strong>" + self.render_inlines(token.get("children", [])) + "</strong>"

    def render_inline_strikethrough(self, token):
        return "<del>" + self.render_inlines(token.get("children", [])) + "</del>"

    def render_inline_code_span(self, token):
        return "<code>" + escape_html(token.get("text", "")) + "</code>"

    def render_inline_link(self, token):
        attrs = f' href="{escape_html(token.get("url", ""))}"'
        if token.get("title") is not None:
            attrs += f' title="{escape_html(token.get("title", ""))}"'
        return "<a" + attrs + ">" + self._children_or_text(token) + "</a>"

    def render_inline_image(self, token):
        attrs = f' src="{escape_html(token.get("url", ""))}" alt="{escape_html(token.get("alt", ""))}"'
        if token.get("title") is not None:
            attrs += f' title="{escape_html(token.get("title", ""))}"'
        return "<img" + attrs + ">"

    def render_inline_line_break(self, token):
        return "<br>\n"

    def render_inline_soft_break(self, token):
        return "\n"


class Markdown:
    def __init__(self, renderer=None, plugins=None):
        self.inline_rules = []
        self.block_rules = []
        self.inline_renderers = {}
        self.block_renderers = {}
        self.enable_table = False
        self.enable_task_list = False
        self.renderer = self._coerce_renderer(renderer)
        for plugin in plugins or []:
            self.use(plugin)

    def __call__(self, text):
        return self.markdown(text)

    def _coerce_renderer(self, renderer):
        if renderer is None:
            renderer = HTMLRenderer()
        elif renderer == "ast":
            renderer = ASTRenderer()
        elif isinstance(renderer, type):
            renderer = renderer()
        if isinstance(renderer, HTMLRenderer):
            for name, func in self.inline_renderers.items():
                renderer.add_inline(name, func)
            for name, func in self.block_renderers.items():
                renderer.add_block(name, func)
        return renderer

    def use(self, plugin):
        if isinstance(plugin, str):
            if plugin == "strikethrough":
                self.register_inline(
                    "strikethrough",
                    r"~~(?=\S)(.+?)(?<=\S)~~",
                    lambda m: {"children": self._parse_inlines(m.group(1))},
                    lambda renderer, token: "<del>" + renderer.render_inlines(token.get("children", [])) + "</del>",
                )
            elif plugin == "table":
                self.enable_table = True
            elif plugin == "task_list":
                self.enable_task_list = True
            else:
                raise ValueError("unknown plugin")
        elif callable(plugin):
            plugin(self)
        else:
            raise ValueError("unknown plugin")

    def register_inline(self, name, pattern, parse_func, render_func=None):
        compiled = re.compile(pattern, re.S)
        self.inline_rules.append((name, compiled, parse_func))
        if render_func is not None:
            self.inline_renderers[name] = render_func
            if isinstance(self.renderer, HTMLRenderer):
                self.renderer.add_inline(name, render_func)

    def register_block(self, name, pattern, parse_func, render_func=None):
        compiled = re.compile(pattern, re.M)
        self.block_rules.append((name, compiled, parse_func))
        if render_func is not None:
            self.block_renderers[name] = render_func
            if isinstance(self.renderer, HTMLRenderer):
                self.renderer.add_block(name, render_func)

    def markdown(self, text):
        return self.render(self.parse(text))

    def parse(self, text):
        tokens = self._parse_blocks(_normalize_newlines(text))
        self._parse_block_inlines(tokens)
        self._assign_heading_ids(tokens)
        return tokens

    def tokens(self, text):
        return self.parse(text)

    def render(self, tokens, renderer=None):
        active = self.renderer if renderer is None else self._coerce_renderer(renderer)
        if isinstance(active, ASTRenderer):
            return active.render(tokens)
        return active.render(tokens)

    def toc(self, text):
        result = []
        for token in self.walk(self.parse(text)):
            if token.get("type") == "heading":
                result.append(
                    {
                        "level": token.get("level"),
                        "text": token.get("text", ""),
                        "id": (token.get("attrs") or {}).get("id", ""),
                    }
                )
        return result

    def walk(self, tokens):
        for token in tokens or []:
            yield token
            typ = token.get("type")
            if typ == "list":
                for item in token.get("items", []):
                    yield item
                    for child in item.get("children", []):
                        yield child
                    for block in item.get("blocks", []):
                        yield from self.walk([block])
            elif typ == "table":
                for cell in token.get("header", []):
                    yield cell
                    for child in cell.get("children", []):
                        yield child
                for row in token.get("rows", []):
                    for cell in row:
                        yield cell
                        for child in cell.get("children", []):
                            yield child
            else:
                if typ == "block_quote":
                    yield from self.walk(token.get("children", []))
                else:
                    for child in token.get("children", []):
                        if isinstance(child, dict) and child.get("type") in {
                            "paragraph",
                            "heading",
                            "block_code",
                            "block_quote",
                            "list",
                            "thematic_break",
                            "table",
                        }:
                            yield from self.walk([child])
                        elif isinstance(child, dict):
                            yield child
                            if child.get("children"):
                                yield from self.walk_inline(child.get("children", []))

    def walk_inline(self, tokens):
        for token in tokens or []:
            yield token
            if token.get("children"):
                yield from self.walk_inline(token.get("children", []))
            if token.get("alt_children"):
                yield from self.walk_inline(token.get("alt_children", []))

    def _parse_blocks(self, text):
        lines = text.split("\n")
        tokens, _ = self._parse_block_lines(lines, 0, len(lines))
        return tokens

    def _parse_block_lines(self, lines, start, end):
        tokens = []
        i = start
        while i < end:
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            block = self._try_custom_block(lines, i, end)
            if block is not None:
                token, i = block
                tokens.append(token)
                continue

            if self.enable_table and i + 1 < end and self._is_table_start(lines[i], lines[i + 1]):
                token, i = self._parse_table(lines, i, end)
                tokens.append(token)
                continue

            m = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t#]*$", line)
            if m:
                tokens.append({"type": "heading", "level": len(m.group(1)), "text": m.group(2).strip()})
                i += 1
                continue

            if self._is_thematic_break(line):
                tokens.append({"type": "thematic_break"})
                i += 1
                continue

            m = re.match(r"^[ \t]*(`{3,})(.*)$", line)
            if m:
                fence = m.group(1)
                lang = m.group(2).strip().split()[0] if m.group(2).strip() else None
                i += 1
                code = []
                while i < end and not re.match(r"^[ \t]*" + re.escape(fence) + r"[ \t]*$", lines[i]):
                    code.append(lines[i])
                    i += 1
                if i < end:
                    i += 1
                token = {"type": "block_code", "text": "\n".join(code)}
                if lang:
                    token["lang"] = lang
                tokens.append(token)
                continue

            if re.match(r"^(    |\t)", line):
                code = []
                while i < end and (re.match(r"^(    |\t)", lines[i]) or not lines[i].strip()):
                    cur = lines[i]
                    if cur.startswith("    "):
                        cur = cur[4:]
                    elif cur.startswith("\t"):
                        cur = cur[1:]
                    code.append(cur)
                    i += 1
                tokens.append({"type": "block_code", "text": "\n".join(code).rstrip("\n")})
                continue

            if re.match(r"^[ \t]{0,3}>", line):
                quote = []
                while i < end and (re.match(r"^[ \t]{0,3}> ?", lines[i]) or not lines[i].strip()):
                    if not lines[i].strip():
                        quote.append("")
                    else:
                        quote.append(re.sub(r"^[ \t]{0,3}> ?", "", lines[i], count=1))
                    i += 1
                children = self._parse_blocks("\n".join(quote))
                tokens.append({"type": "block_quote", "children": children})
                continue

            if self._is_list_marker(line):
                token, i = self._parse_list(lines, i, end)
                tokens.append(token)
                continue

            para = [line]
            i += 1
            while i < end:
                cur = lines[i]
                if not cur.strip():
                    break
                if self._starts_block(cur):
                    break
                if self.enable_table and i + 1 < end and self._is_table_start(cur, lines[i + 1]):
                    break
                para.append(cur)
                i += 1
            tokens.append({"type": "paragraph", "text": "\n".join(para)})
        return tokens, i

    def _try_custom_block(self, lines, i, end):
        if not self.block_rules:
            return None
        rest = "\n".join(lines[i:end])
        for name, pattern, parse_func in self.block_rules:
            match = pattern.match(rest)
            if not match:
                continue
            fields = parse_func(match) or {}
            token = {"type": name}
            token.update(fields)
            consumed = match.group(0).count("\n") + 1
            return token, i + max(1, consumed)
        return None

    def _starts_block(self, line):
        return (
            re.match(r"^(#{1,6})[ \t]+", line)
            or self._is_thematic_break(line)
            or re.match(r"^[ \t]*`{3,}", line)
            or re.match(r"^(    |\t)", line)
            or re.match(r"^[ \t]{0,3}>", line)
            or self._is_list_marker(line)
        )

    def _is_thematic_break(self, line):
        stripped = re.sub(r"\s+", "", line)
        return len(stripped) >= 3 and stripped[0] in "-_*" and all(ch == stripped[0] for ch in stripped)

    def _is_list_marker(self, line):
        return re.match(r"^[ \t]{0,3}(?:[-*+]|\d+[.])[ \t]+", line) is not None

    def _parse_list(self, lines, i, end):
        first = re.match(r"^[ \t]{0,3}((?:[-*+])|(?:\d+[.]))[ \t]+(.*)$", lines[i])
        ordered = first.group(1).endswith(".")
        items = []
        while i < end:
            m = re.match(r"^[ \t]{0,3}((?:[-*+])|(?:\d+[.]))[ \t]+(.*)$", lines[i])
            if not m or m.group(1).endswith(".") != ordered:
                break
            content = [m.group(2)]
            i += 1
            loose = False
            extra_blocks = []
            continuation = []
            while i < end:
                cur = lines[i]
                if not cur.strip():
                    if i + 1 < end and re.match(r"^[ \t]{2,}\S", lines[i + 1]):
                        loose = True
                        continuation.append("")
                        i += 1
                        continue
                    i += 1
                    break
                if re.match(r"^[ \t]{0,3}((?:[-*+])|(?:\d+[.]))[ \t]+", cur):
                    break
                cm = re.match(r"^[ \t]{2,}(.*)$", cur)
                if cm:
                    continuation.append(cm.group(1))
                    i += 1
                    continue
                break
            all_text = "\n".join([x for x in content + continuation if x is not None]).strip("\n")
            item = {"type": "list_item", "text": all_text, "loose": loose}
            if self.enable_task_list:
                tm = re.match(r"^\[([ xX])\][ \t]*(.*)$", all_text, re.S)
                if tm:
                    item["checked"] = tm.group(1).lower() == "x"
                    item["text"] = tm.group(2)
                    all_text = tm.group(2)
            if loose and ("\n\n" in "\n".join(continuation) or len([x for x in continuation if x == ""]) > 0):
                blocks = self._parse_blocks(all_text)
                item["blocks"] = blocks
            else:
                item["children"] = self._parse_inlines(all_text)
            if extra_blocks:
                item.setdefault("blocks", []).extend(extra_blocks)
            items.append(item)
        return {"type": "list", "ordered": ordered, "items": items}, i

    def _is_table_start(self, header, delimiter):
        if "|" not in header or "|" not in delimiter:
            return False
        cells = self._split_table_row(delimiter)
        if not cells:
            return False
        return all(re.match(r"^:?-{3,}:?$", cell.strip()) for cell in cells)

    def _split_table_row(self, line):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [cell.strip() for cell in line.split("|")]

    def _parse_table(self, lines, i, end):
        header_cells = self._split_table_row(lines[i])
        delim_cells = self._split_table_row(lines[i + 1])
        align = []
        for cell in delim_cells:
            s = cell.strip()
            if s.startswith(":") and s.endswith(":"):
                align.append("center")
            elif s.startswith(":"):
                align.append("left")
            elif s.endswith(":"):
                align.append("right")
            else:
                align.append(None)
        rows = []
        i += 2
        while i < end and lines[i].strip() and "|" in lines[i] and not self._starts_block(lines[i]):
            cells = self._split_table_row(lines[i])
            rows.append([{"type": "table_cell", "text": cell} for cell in cells])
            i += 1
        token = {
            "type": "table",
            "header": [{"type": "table_cell", "text": cell} for cell in header_cells],
            "align": align,
            "rows": rows,
        }
        return token, i

    def _parse_block_inlines(self, tokens):
        for token in tokens:
            typ = token.get("type")
            if typ in ("paragraph", "heading"):
                token["children"] = self._parse_inlines(token.get("text", ""))
            elif typ == "block_quote":
                self._parse_block_inlines(token.get("children", []))
            elif typ == "list":
                for item in token.get("items", []):
                    if "children" not in item and "text" in item:
                        item["children"] = self._parse_inlines(item.get("text", ""))
                    if item.get("blocks"):
                        self._parse_block_inlines(item.get("blocks", []))
            elif typ == "table":
                for cell in token.get("header", []):
                    cell["children"] = self._parse_inlines(cell.get("text", ""))
                for row in token.get("rows", []):
                    for cell in row:
                        cell["children"] = self._parse_inlines(cell.get("text", ""))
            elif "text" in token and "children" not in token and typ != "block_code":
                token["children"] = self._parse_inlines(token.get("text", ""))

    def _parse_inlines(self, text):
        text = "" if text is None else str(text)
        tokens = []
        i = 0
        buf = []

        def flush():
            if buf:
                tokens.append({"type": "text", "text": "".join(buf)})
                buf.clear()

        while i < len(text):
            custom = self._match_custom_inline(text, i)
            if custom is not None:
                token, end = custom
                flush()
                tokens.append(token)
                i = end
                continue

            ch = text[i]

            if ch == "\\":
                if i + 1 < len(text) and text[i + 1] == "\n":
                    flush()
                    tokens.append({"type": "line_break"})
                    i += 2
                    continue
                if i + 1 < len(text) and text[i + 1] in _PUNCT:
                    buf.append(text[i + 1])
                    i += 2
                    continue
                buf.append(ch)
                i += 1
                continue

            if ch == "\n":
                if len(buf) >= 2 and buf[-1] == " " and buf[-2] == " ":
                    while buf and buf[-1] == " ":
                        buf.pop()
                    flush()
                    tokens.append({"type": "line_break"})
                else:
                    flush()
                    tokens.append({"type": "soft_break"})
                i += 1
                continue

            if ch == "`":
                run = re.match(r"`+", text[i:]).group(0)
                j = text.find(run, i + len(run))
                if j != -1:
                    flush()
                    tokens.append({"type": "code_span", "text": text[i + len(run) : j]})
                    i = j + len(run)
                    continue

            if text.startswith("![", i):
                parsed = self._parse_link_or_image(text, i, image=True)
                if parsed is not None:
                    flush()
                    token, i = parsed
                    tokens.append(token)
                    continue

            if ch == "[":
                parsed = self._parse_link_or_image(text, i, image=False)
                if parsed is not None:
                    flush()
                    token, i = parsed
                    tokens.append(token)
                    continue

            if ch == "<":
                parsed = self._parse_autolink(text, i)
                if parsed is not None:
                    flush()
                    token, i = parsed
                    tokens.append(token)
                    continue

            if text.startswith("**", i) or text.startswith("__", i):
                marker = text[i : i + 2]
                j = text.find(marker, i + 2)
                if j != -1 and j > i + 2:
                    body = text[i + 2 : j]
                    flush()
                    tokens.append({"type": "strong", "children": self._parse_inlines(body)})
                    i = j + 2
                    continue

            if ch in "*_":
                j = self._find_single_delimiter(text, ch, i + 1)
                if j != -1 and j > i + 1:
                    body = text[i + 1 : j]
                    flush()
                    tokens.append({"type": "emphasis", "children": self._parse_inlines(body)})
                    i = j + 1
                    continue

            buf.append(ch)
            i += 1

        flush()
        return tokens

    def _find_single_delimiter(self, text, marker, start):
        j = start
        while True:
            j = text.find(marker, j)
            if j == -1:
                return -1
            prev_same = j > 0 and text[j - 1] == marker
            next_same = j + 1 < len(text) and text[j + 1] == marker
            if not prev_same and not next_same:
                return j
            j += 1

    def _match_custom_inline(self, text, i):
        if not self.inline_rules:
            return None
        rest = text[i:]
        for name, pattern, parse_func in self.inline_rules:
            match = pattern.match(rest)
            if not match:
                continue
            fields = parse_func(match) or {}
            token = {"type": name}
            token.update(fields)
            return token, i + len(match.group(0))
        return None

    def _find_matching_bracket(self, text, start):
        depth = 0
        i = start
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _parse_link_or_image(self, text, i, image=False):
        label_start = i + 2 if image else i + 1
        close = self._find_matching_bracket(text, i + (1 if image else 0))
        if close == -1 or close + 1 >= len(text) or text[close + 1] != "(":
            return None
        end = text.find(")", close + 2)
        if end == -1:
            return None
        label = text[label_start:close]
        dest = text[close + 2 : end].strip()
        m = re.match(r'^(?P<url>\S+?)(?:[ \t]+(?P<q>["\'])(?P<title>.*)(?P=q))?$', dest)
        if not m:
            return None
        url = m.group("url")
        title = m.group("title")
        if image:
            token = {
                "type": "image",
                "url": url,
                "alt": _plain_text(self._parse_inlines(label)),
                "alt_children": self._parse_inlines(label),
            }
        else:
            token = {"type": "link", "url": url, "children": self._parse_inlines(label)}
        if title is not None:
            token["title"] = title
        return token, end + 1

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

    def _assign_heading_ids(self, tokens):
        seen = {}
        for token in self.walk(tokens):
            if token.get("type") != "heading":
                continue
            plain = _plain_text(token.get("children", []))
            base = _slugify(plain)
            count = seen.get(base, 0) + 1
            seen[base] = count
            ident = base if count == 1 else f"{base}-{count}"
            token["text"] = plain
            token.setdefault("attrs", {})["id"] = ident


class MarkdownWorkspace:
    def __init__(self, renderer=None, plugins=None):
        self.renderer_arg = renderer
        self.plugins = list(plugins or [])
        self.markdown = Markdown(renderer=renderer, plugins=self.plugins)
        self._docs = {}
        self._tokens = {}

    def _normalize_path(self, path):
        if not isinstance(path, str):
            raise ValueError("invalid path")
        path = path.replace("\\", "/").strip()
        if not path:
            raise ValueError("invalid path")
        norm = posixpath.normpath(path)
        if norm == "." or norm.startswith("../") or norm == ".." or posixpath.isabs(norm):
            raise ValueError("invalid path")
        return norm

    def update(self, path, text):
        norm = self._normalize_path(path)
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        parsed = self.markdown.parse(text)
        self._docs[norm] = text
        self._tokens[norm] = parsed

    def remove(self, path):
        norm = self._normalize_path(path)
        self._docs.pop(norm, None)
        self._tokens.pop(norm, None)

    def paths(self):
        return sorted(self._docs)

    def tokens(self, path):
        norm = self._normalize_path(path)
        return copy.deepcopy(self._tokens[norm])

    def render(self, path, renderer=None):
        norm = self._normalize_path(path)
        return self.markdown.render(copy.deepcopy(self._tokens[norm]), renderer=renderer)

    def toc(self, path=None):
        docs = [self._normalize_path(path)] if path is not None else self.paths()
        result = []
        for doc in docs:
            for token in self.markdown.walk(self._tokens.get(doc, [])):
                if token.get("type") == "heading":
                    result.append(
                        {
                            "doc": doc,
                            "level": token.get("level"),
                            "text": token.get("text", ""),
                            "id": (token.get("attrs") or {}).get("id", ""),
                        }
                    )
        return result

    def links(self, path=None):
        docs = [self._normalize_path(path)] if path is not None else self.paths()
        links = []
        order = 0
        headings = {doc: {h["id"] for h in self.toc(doc)} for doc in self.paths()}
        for doc in docs:
            base_dir = posixpath.dirname(doc)
            for token in self.markdown.walk(self._tokens.get(doc, [])):
                if token.get("type") not in ("link", "image"):
                    continue
                url = token.get("url", "")
                if not url or _has_scheme(url):
                    continue
                target_part, anchor = _split_link_url(url)
                if target_part == "":
                    target = doc
                else:
                    clean = urlsplit(target_part)
                    target_path = urlunsplit(("", "", clean.path, "", ""))
                    joined = posixpath.normpath(posixpath.join(base_dir, target_path))
                    if joined == "." or joined.startswith("../") or joined == "..":
                        target = joined
                    else:
                        target = joined
                kind = token.get("type")
                text = token.get("alt", "") if kind == "image" else _plain_text(token.get("children", []))
                resolved = target in self._docs and (anchor is None or anchor in headings.get(target, set()))
                links.append(
                    {
                        "source": doc,
                        "target": target,
                        "anchor": anchor,
                        "text": text,
                        "kind": kind,
                        "resolved": resolved,
                        "order": order,
                    }
                )
                order += 1
        return links

    def backlinks(self, path, anchor=None):
        norm = self._normalize_path(path)
        result = []
        for link in self.links():
            if link["target"] != norm:
                continue
            if anchor is not None and link.get("anchor") != anchor:
                continue
            if link.get("resolved"):
                result.append(link)
        return result

    def diagnostics(self):
        diagnostics = []
        for link in self.links():
            if link["resolved"]:
                continue
            if link["target"] not in self._docs:
                reason = "missing_document"
            else:
                reason = "missing_anchor"
            diag = dict(link)
            diag["type"] = reason
            diag["message"] = reason
            diagnostics.append(diag)
        return diagnostics

    def graph(self):
        return {
            "documents": self.paths(),
            "headings": self.toc(),
            "links": self.links(),
            "diagnostics": self.diagnostics(),
        }

    def export(self):
        return {"documents": [{"path": path, "text": self._docs[path]} for path in self.paths()]}

    @classmethod
    def import_snapshot(cls, snapshot, renderer=None, plugins=None):
        ws = cls(renderer=renderer, plugins=plugins)
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        docs = snapshot.get("documents", snapshot)
        if isinstance(docs, dict):
            iterable = [{"path": path, "text": text} for path, text in docs.items()]
        else:
            iterable = docs
        for item in iterable:
            ws.update(item["path"], item["text"])
        return ws
