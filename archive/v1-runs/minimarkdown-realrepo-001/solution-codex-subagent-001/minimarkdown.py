"""A tiny dependency-free Markdown parser and renderer.

This module intentionally implements a practical Markdown subset rather than
the full CommonMark specification.  The public API is compatible with the task
packet: Markdown, HTMLRenderer, ASTRenderer, and escape_html.
"""

from __future__ import annotations

import copy
import re
from html import escape as _html_escape
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


PUNCTUATION = r"\`*_{}[]()#+-.!|>~"


def escape_html(value: Any, quote: bool = True) -> str:
    """Escape text for HTML text and attribute contexts."""

    return _html_escape("" if value is None else str(value), quote=quote)


Token = Dict[str, Any]
InlineParserFunc = Callable[["Markdown", re.Match[str]], Optional[Tuple[Token, int]]]
BlockParserFunc = Callable[["Markdown", Sequence[str], int, re.Match[str]], Optional[Tuple[Token, int]]]
RenderFunc = Callable[..., str]


class HTMLRenderer:
    """Render parsed token dictionaries to HTML."""

    def __init__(self) -> None:
        self.renderers: Dict[str, Callable[[Token], str]] = {
            "text": self.render_text,
            "softbreak": self.render_softbreak,
            "hardbreak": self.render_hardbreak,
            "paragraph": self.render_paragraph,
            "heading": self.render_heading,
            "emphasis": self.render_emphasis,
            "strong": self.render_strong,
            "codespan": self.render_codespan,
            "code_block": self.render_code_block,
            "blockquote": self.render_blockquote,
            "list": self.render_list,
            "list_item": self.render_list_item,
            "link": self.render_link,
            "image": self.render_image,
            "thematic_break": self.render_thematic_break,
        }

    def register(self, name: str, render_func: RenderFunc) -> None:
        self.renderers[name] = lambda token: render_func(self, token)

    def render(self, tokens: Sequence[Token]) -> str:
        return "\n".join(self.render_token(token) for token in tokens)

    def render_token(self, token: Token) -> str:
        renderer = self.renderers.get(token.get("type", ""))
        if renderer is not None:
            return renderer(token)
        if "children" in token:
            return self.render_inlines(token.get("children", []))
        return escape_html(token.get("text", ""))

    def render_inlines(self, tokens: Sequence[Token]) -> str:
        return "".join(self.render_token(token) for token in tokens)

    def render_blocks(self, tokens: Sequence[Token]) -> str:
        return "\n".join(self.render_token(token) for token in tokens)

    def render_text(self, token: Token) -> str:
        return escape_html(token.get("text", ""))

    def render_softbreak(self, token: Token) -> str:
        return "\n"

    def render_hardbreak(self, token: Token) -> str:
        return "<br>"

    def render_paragraph(self, token: Token) -> str:
        return "<p>" + self.render_inlines(token.get("children", [])) + "</p>"

    def render_heading(self, token: Token) -> str:
        level = max(1, min(6, int(token.get("level", 1))))
        return f"<h{level}>" + self.render_inlines(token.get("children", [])) + f"</h{level}>"

    def render_emphasis(self, token: Token) -> str:
        return "<em>" + self.render_inlines(token.get("children", [])) + "</em>"

    def render_strong(self, token: Token) -> str:
        return "<strong>" + self.render_inlines(token.get("children", [])) + "</strong>"

    def render_codespan(self, token: Token) -> str:
        return "<code>" + escape_html(token.get("text", "")) + "</code>"

    def render_code_block(self, token: Token) -> str:
        lang = token.get("lang") or ""
        attrs = ""
        if lang:
            attrs = f' class="language-{escape_html(lang)}"'
        return f"<pre><code{attrs}>" + escape_html(token.get("text", "")) + "</code></pre>"

    def render_blockquote(self, token: Token) -> str:
        return "<blockquote>\n" + self.render_blocks(token.get("children", [])) + "\n</blockquote>"

    def render_list(self, token: Token) -> str:
        tag = "ol" if token.get("ordered") else "ul"
        body = "\n".join(self.render_token(item) for item in token.get("items", []))
        return f"<{tag}>\n{body}\n</{tag}>"

    def render_list_item(self, token: Token) -> str:
        children = token.get("children", [])
        if children and children[0].get("type") == "paragraph" and children[0].get("tight"):
            body = self.render_inlines(children[0].get("children", []))
            rest = self.render_blocks(children[1:])
            if rest:
                body += "\n" + rest
        else:
            body = self.render_blocks(children)
        return "<li>" + body + "</li>"

    def render_link(self, token: Token) -> str:
        attrs = f' href="{escape_html(token.get("url", ""))}"'
        if token.get("title") is not None:
            attrs += f' title="{escape_html(token.get("title", ""))}"'
        return "<a" + attrs + ">" + self.render_inlines(token.get("children", [])) + "</a>"

    def render_image(self, token: Token) -> str:
        attrs = (
            f' src="{escape_html(token.get("url", ""))}"'
            f' alt="{escape_html(token.get("alt", ""))}"'
        )
        if token.get("title") is not None:
            attrs += f' title="{escape_html(token.get("title", ""))}"'
        return "<img" + attrs + ">"

    def render_thematic_break(self, token: Token) -> str:
        return "<hr>"


class ASTRenderer:
    """Return public token dictionaries without parser or renderer internals."""

    def render(self, tokens: Sequence[Token]) -> List[Token]:
        return [self._clean(token) for token in tokens]

    def register(self, name: str, render_func: RenderFunc) -> None:
        return None

    def _clean(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._clean(item)
                for key, item in value.items()
                if not key.startswith("_") and not callable(item) and not isinstance(item, re.Pattern)
            }
        if isinstance(value, list):
            return [self._clean(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._clean(item) for item in value)
        return copy.deepcopy(value)


class Markdown:
    """Parse a small Markdown subset into HTML or AST tokens."""

    def __init__(self, renderer: Any = None, plugins: Optional[Iterable[Any]] = None) -> None:
        if renderer is None:
            self.renderer: Any = HTMLRenderer()
        elif renderer == "ast":
            self.renderer = ASTRenderer()
        elif isinstance(renderer, (HTMLRenderer, ASTRenderer)):
            self.renderer = renderer
        else:
            self.renderer = renderer

        self.inline_rules: List[Tuple[str, re.Pattern[str], InlineParserFunc]] = []
        self.block_rules: List[Tuple[str, re.Pattern[str], BlockParserFunc]] = []
        self.inline_renderers: Dict[str, RenderFunc] = {}
        self.block_renderers: Dict[str, RenderFunc] = {}
        self._task_list_enabled = False
        self._setup_rules()

        if plugins:
            for plugin in plugins:
                self.use(plugin)

    def __call__(self, text: str) -> Any:
        tokens = self.parse(text)
        return self.renderer.render(tokens)

    def use(self, plugin: Any) -> None:
        if isinstance(plugin, str):
            if plugin == "strikethrough":
                plugin_strikethrough(self)
            elif plugin == "table":
                plugin_table(self)
            elif plugin == "task_list":
                plugin_task_list(self)
            else:
                raise ValueError("unknown plugin")
        elif callable(plugin):
            plugin(self)
        else:
            raise ValueError("invalid plugin")

    def _setup_rules(self) -> None:
        self.register_block("table", r"^ {0,3}\|?.*\|.*$", _parse_table_block, _render_table)
        # Table is registered but disabled until the plugin moves it into use.
        self.block_rules.clear()

    def register_inline(
        self,
        name: str,
        pattern: str,
        parse_func: InlineParserFunc,
        render_func: Optional[RenderFunc] = None,
    ) -> None:
        self.inline_rules.append((name, re.compile(pattern, re.S), parse_func))
        if render_func is not None:
            self.inline_renderers[name] = render_func
            if hasattr(self.renderer, "register"):
                self.renderer.register(name, render_func)

    def register_block(
        self,
        name: str,
        pattern: str,
        parse_func: BlockParserFunc,
        render_func: Optional[RenderFunc] = None,
    ) -> None:
        self.block_rules.append((name, re.compile(pattern), parse_func))
        if render_func is not None:
            self.block_renderers[name] = render_func
            if hasattr(self.renderer, "register"):
                self.renderer.register(name, render_func)

    def parse(self, text: str) -> List[Token]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        return self._parse_blocks(normalized.split("\n"))

    def _parse_blocks(self, lines: Sequence[str]) -> List[Token]:
        tokens: List[Token] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.strip() == "":
                index += 1
                continue

            for _name, pattern, parse_func in self.block_rules:
                match = pattern.match(line)
                if match:
                    parsed = parse_func(self, lines, index, match)
                    if parsed is not None:
                        token, index = parsed
                        tokens.append(self._finalize_block_token(token))
                        break
            else:
                parsed = (
                    self._parse_fenced_code(lines, index)
                    or self._parse_indented_code(lines, index)
                    or self._parse_heading(lines, index)
                    or self._parse_thematic_break(lines, index)
                    or self._parse_blockquote(lines, index)
                    or self._parse_list(lines, index)
                    or self._parse_paragraph(lines, index)
                )
                token, index = parsed
                tokens.append(self._finalize_block_token(token))
                continue
            continue
        return tokens

    def _finalize_block_token(self, token: Token) -> Token:
        token_type = token.get("type")
        if token_type in {"paragraph", "heading", "table_cell"} and "children" not in token:
            token["children"] = self.parse_inlines(token.get("text", ""))
        if token_type == "list_item":
            token["children"] = [self._finalize_block_token(child) for child in token.get("children", [])]
        if token_type == "list":
            token["items"] = [self._finalize_block_token(item) for item in token.get("items", [])]
        if token_type == "blockquote":
            token["children"] = [self._finalize_block_token(child) for child in token.get("children", [])]
        if token_type == "table":
            for row in token.get("header", []):
                if "children" not in row:
                    row["children"] = self.parse_inlines(row.get("text", ""))
            for row in token.get("rows", []):
                for cell in row:
                    if "children" not in cell:
                        cell["children"] = self.parse_inlines(cell.get("text", ""))
        return token

    def _is_block_start(self, line: str) -> bool:
        if line.strip() == "":
            return True
        if re.match(r"^( {0,3})(#{1,6})(?:\s+|$)", line):
            return True
        if re.match(r"^( {0,3})(`{3,})(.*)$", line):
            return True
        stripped = line.strip()
        if (
            re.match(r"^(?:-\s*){3,}$", stripped)
            or re.match(r"^(?:_\s*){3,}$", stripped)
            or re.match(r"^(?:\*\s*){3,}$", stripped)
        ):
            return True
        if re.match(r"^( {0,3})>\s?", line):
            return True
        if re.match(r"^( {0,3})([-*+]|\d+[.])\s+", line):
            return True
        for _name, pattern, _parse in self.block_rules:
            if pattern.match(line):
                return True
        return False

    def _parse_fenced_code(self, lines: Sequence[str], index: int) -> Optional[Tuple[Token, int]]:
        match = re.match(r"^( {0,3})(`{3,})([^\n`]*)$", lines[index])
        if not match:
            return None
        fence = match.group(2)
        lang = match.group(3).strip() or None
        content: List[str] = []
        index += 1
        closing = re.compile(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
        while index < len(lines):
            if closing.match(lines[index]):
                index += 1
                break
            content.append(lines[index])
            index += 1
        return {"type": "code_block", "text": "\n".join(content), "lang": lang}, index

    def _parse_indented_code(self, lines: Sequence[str], index: int) -> Optional[Tuple[Token, int]]:
        if not (lines[index].startswith("    ") or lines[index].startswith("\t")):
            return None
        content: List[str] = []
        while index < len(lines):
            line = lines[index]
            if line.startswith("    "):
                content.append(line[4:])
            elif line.startswith("\t"):
                content.append(line[1:])
            elif line.strip() == "":
                content.append("")
            else:
                break
            index += 1
        while content and content[-1] == "":
            content.pop()
        return {"type": "code_block", "text": "\n".join(content), "lang": None}, index

    def _parse_heading(self, lines: Sequence[str], index: int) -> Optional[Tuple[Token, int]]:
        match = re.match(r"^ {0,3}(#{1,6})(?:\s+|$)(.*?)\s*#*\s*$", lines[index])
        if not match:
            return None
        return {
            "type": "heading",
            "level": len(match.group(1)),
            "text": match.group(2).strip(),
        }, index + 1

    def _parse_thematic_break(self, lines: Sequence[str], index: int) -> Optional[Tuple[Token, int]]:
        stripped = lines[index].strip()
        if re.match(r"^(?:-\s*){3,}$", stripped) or re.match(r"^(?:_\s*){3,}$", stripped) or re.match(r"^(?:\*\s*){3,}$", stripped):
            return {"type": "thematic_break"}, index + 1
        return None

    def _parse_blockquote(self, lines: Sequence[str], index: int) -> Optional[Tuple[Token, int]]:
        if not re.match(r"^ {0,3}>\s?", lines[index]):
            return None
        inner: List[str] = []
        while index < len(lines):
            line = lines[index]
            if re.match(r"^ {0,3}>\s?", line):
                inner.append(re.sub(r"^ {0,3}>\s?", "", line, count=1))
                index += 1
            elif line.strip() == "":
                inner.append("")
                index += 1
            else:
                break
        return {"type": "blockquote", "children": self._parse_blocks(inner)}, index

    def _parse_list(self, lines: Sequence[str], index: int) -> Optional[Tuple[Token, int]]:
        first = re.match(r"^( {0,3})([-*+]|\d+[.])\s+(.*)$", lines[index])
        if not first:
            return None
        ordered = first.group(2).endswith(".")
        items: List[Token] = []
        loose = False

        while index < len(lines):
            start = re.match(r"^( {0,3})([-*+]|\d+[.])\s+(.*)$", lines[index])
            if not start or start.group(2).endswith(".") != ordered:
                break
            marker_indent = len(start.group(1))
            content_indent = marker_indent + len(start.group(2)) + 1
            item_lines = [start.group(3)]
            index += 1
            item_had_blank = False

            while index < len(lines):
                line = lines[index]
                if line.strip() == "":
                    item_had_blank = True
                    item_lines.append("")
                    index += 1
                    continue
                next_marker = re.match(r"^( {0,3})([-*+]|\d+[.])\s+(.*)$", line)
                if next_marker and len(next_marker.group(1)) <= marker_indent and next_marker.group(2).endswith(".") == ordered:
                    break
                indent = _indent_width(line)
                if indent > marker_indent:
                    remove = min(content_indent, len(line) - len(line.lstrip(" ")))
                    item_lines.append(line[remove:])
                    index += 1
                    continue
                break

            while item_lines and item_lines[-1] == "":
                item_lines.pop()
            if item_had_blank:
                loose = True
            item = self._make_list_item(item_lines, loose=item_had_blank)
            items.append(item)

        if loose:
            for item in items:
                item["loose"] = True
        return {"type": "list", "ordered": ordered, "items": items}, index

    def _make_list_item(self, item_lines: Sequence[str], loose: bool = False) -> Token:
        checked: Optional[bool] = None
        lines = list(item_lines)
        if self._task_list_enabled and lines:
            match = re.match(r"^\s*\[([ xX])\]\s+(.*)$", lines[0])
            if match:
                checked = match.group(1).lower() == "x"
                lines[0] = match.group(2)

        children = self._parse_blocks(lines) if lines else []
        if not loose and len(children) == 1 and children[0].get("type") == "paragraph":
            children[0]["tight"] = True
        item: Token = {"type": "list_item", "children": children, "loose": loose}
        if checked is not None:
            item["checked"] = checked
        return item

    def _parse_paragraph(self, lines: Sequence[str], index: int) -> Tuple[Token, int]:
        collected: List[str] = []
        while index < len(lines):
            line = lines[index]
            if line.strip() == "":
                break
            if collected and self._is_block_start(line):
                break
            collected.append(line)
            index += 1
        return {"type": "paragraph", "text": "\n".join(collected)}, index

    def parse_inlines(self, text: str) -> List[Token]:
        tokens: List[Token] = []
        buffer: List[str] = []
        index = 0

        def flush() -> None:
            if buffer:
                tokens.append({"type": "text", "text": "".join(buffer)})
                buffer.clear()

        while index < len(text):
            for _name, pattern, parse_func in self.inline_rules:
                match = pattern.match(text, index)
                if match:
                    parsed = parse_func(self, match)
                    if parsed is not None:
                        token, new_index = parsed
                        flush()
                        tokens.append(token)
                        index = new_index
                        break
            else:
                parsed_inline = (
                    self._parse_escape(text, index)
                    or self._parse_linebreak(text, index)
                    or self._parse_codespan(text, index)
                    or self._parse_autolink(text, index)
                    or self._parse_link_or_image(text, index)
                    or self._parse_emphasis(text, index)
                )
                if parsed_inline is not None:
                    token, index = parsed_inline
                    flush()
                    tokens.append(token)
                else:
                    buffer.append(text[index])
                    index += 1
                continue
            continue
        flush()
        return _merge_text_tokens(tokens)

    def _parse_escape(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        if text[index] != "\\" or index + 1 >= len(text):
            return None
        nxt = text[index + 1]
        if nxt == "\n":
            return {"type": "hardbreak"}, index + 2
        if nxt in PUNCTUATION:
            return {"type": "text", "text": nxt}, index + 2
        return None

    def _parse_linebreak(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        if text[index] == "\n":
            return {"type": "softbreak"}, index + 1
        if text.startswith("  \n", index):
            return {"type": "hardbreak"}, index + 3
        return None

    def _parse_codespan(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        if text[index] != "`":
            return None
        count = _run_length(text, index, "`")
        close = text.find("`" * count, index + count)
        if close == -1:
            return None
        raw = text[index + count : close]
        if "\n" in raw:
            raw = re.sub(r"\s+", " ", raw)
        if raw.startswith(" ") and raw.endswith(" ") and len(raw.strip()) > 0:
            raw = raw[1:-1]
        return {"type": "codespan", "text": raw}, close + count

    def _parse_autolink(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        if text[index] != "<":
            return None
        end = text.find(">", index + 1)
        if end == -1:
            return None
        inner = text[index + 1 : end]
        if re.match(r"^https?://[^\s<>]+$", inner):
            return {"type": "link", "url": inner, "children": [{"type": "text", "text": inner}]}, end + 1
        if re.match(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", inner):
            return {"type": "link", "url": "mailto:" + inner, "children": [{"type": "text", "text": inner}]}, end + 1
        return None

    def _parse_link_or_image(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        image = text.startswith("![", index)
        if not image and text[index] != "[":
            return None
        label_start = index + (2 if image else 1)
        label_end = _find_balanced_bracket(text, label_start)
        if label_end == -1 or label_end + 1 >= len(text) or text[label_end + 1] != "(":
            return None
        dest = _parse_link_destination(text, label_end + 2)
        if dest is None:
            return None
        url, title, end_index = dest
        label = text[label_start:label_end]
        if image:
            alt_plain = _plain_text(self.parse_inlines(label))
            return {"type": "image", "url": url, "title": title, "alt": alt_plain, "children": self.parse_inlines(label)}, end_index
        return {"type": "link", "url": url, "title": title, "children": self.parse_inlines(label)}, end_index

    def _parse_emphasis(self, text: str, index: int) -> Optional[Tuple[Token, int]]:
        char = text[index]
        if char not in "*_":
            return None
        count = _run_length(text, index, char)
        if count >= 2:
            close = _find_closing_delim(text, index + 2, char * 2)
            if close != -1 and close > index + 2:
                inner = text[index + 2 : close]
                return {"type": "strong", "children": self.parse_inlines(inner)}, close + 2
        close = _find_closing_delim(text, index + 1, char)
        if close != -1 and close > index + 1:
            inner = text[index + 1 : close]
            return {"type": "emphasis", "children": self.parse_inlines(inner)}, close + 1
        return None


def _indent_width(line: str) -> int:
    width = 0
    for char in line:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4
        else:
            break
    return width


def _run_length(text: str, index: int, char: str) -> int:
    end = index
    while end < len(text) and text[end] == char:
        end += 1
    return end - index


def _find_closing_delim(text: str, start: int, delim: str) -> int:
    index = start
    while True:
        found = text.find(delim, index)
        if found == -1:
            return -1
        if found > 0 and text[found - 1] == "\\":
            index = found + 1
            continue
        if len(delim) == 1:
            if (found > 0 and text[found - 1] == delim) or (
                found + 1 < len(text) and text[found + 1] == delim
            ):
                index = found + 1
                continue
        return found


def _find_balanced_bracket(text: str, start: int) -> int:
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            if depth == 0:
                return index
            depth -= 1
        index += 1
    return -1


def _parse_link_destination(text: str, start: int) -> Optional[Tuple[str, Optional[str], int]]:
    index = start
    length = len(text)
    while index < length and text[index].isspace() and text[index] != "\n":
        index += 1
    if index >= length:
        return None
    if text[index] == "<":
        end = text.find(">", index + 1)
        if end == -1:
            return None
        url = text[index + 1 : end]
        index = end + 1
    else:
        url_start = index
        paren_depth = 0
        while index < length:
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char == "(":
                paren_depth += 1
            elif char == ")":
                if paren_depth == 0:
                    break
                paren_depth -= 1
            elif char.isspace():
                break
            index += 1
        url = text[url_start:index]
    while index < length and text[index].isspace() and text[index] != "\n":
        index += 1
    title: Optional[str] = None
    if index < length and text[index] in "\"'":
        quote = text[index]
        title_start = index + 1
        title_end = text.find(quote, title_start)
        if title_end == -1:
            return None
        title = text[title_start:title_end]
        index = title_end + 1
        while index < length and text[index].isspace() and text[index] != "\n":
            index += 1
    if index < length and text[index] == ")":
        return url, title, index + 1
    return None


def _merge_text_tokens(tokens: Sequence[Token]) -> List[Token]:
    merged: List[Token] = []
    for token in tokens:
        if token.get("type") == "text" and merged and merged[-1].get("type") == "text":
            merged[-1]["text"] += token.get("text", "")
        else:
            merged.append(token)
    return merged


def _plain_text(tokens: Sequence[Token]) -> str:
    parts: List[str] = []
    for token in tokens:
        if token.get("type") == "text":
            parts.append(token.get("text", ""))
        elif token.get("type") == "softbreak":
            parts.append("\n")
        elif token.get("type") == "hardbreak":
            parts.append("\n")
        elif token.get("type") == "codespan":
            parts.append(token.get("text", ""))
        elif "children" in token:
            parts.append(_plain_text(token.get("children", [])))
        elif "alt" in token:
            parts.append(token.get("alt", ""))
    return "".join(parts)


def plugin_strikethrough(markdown: Markdown) -> None:
    def parse_strike(md: Markdown, match: re.Match[str]) -> Optional[Tuple[Token, int]]:
        inner = match.group(1)
        if not inner:
            return None
        return {"type": "strikethrough", "children": md.parse_inlines(inner)}, match.end()

    def render_strike(renderer: HTMLRenderer, token: Token) -> str:
        return "<del>" + renderer.render_inlines(token.get("children", [])) + "</del>"

    markdown.register_inline("strikethrough", r"~~(.+?)~~", parse_strike, render_strike)


def plugin_task_list(markdown: Markdown) -> None:
    markdown._task_list_enabled = True

    def render_item(renderer: HTMLRenderer, token: Token) -> str:
        children = token.get("children", [])
        prefix = ""
        if "checked" in token:
            checked = " checked" if token.get("checked") else ""
            prefix = f'<input type="checkbox" disabled{checked}> '
        if children and children[0].get("type") == "paragraph" and children[0].get("tight"):
            first = copy.deepcopy(children[0])
            first_children = first.get("children", [])
            first["children"] = [{"type": "text", "text": ""}] + first_children
            body = prefix + renderer.render_inlines(first.get("children", [])[1:])
            rest = renderer.render_blocks(children[1:])
            return "<li>" + body + (("\n" + rest) if rest else "") + "</li>"
        return "<li>" + prefix + renderer.render_blocks(children) + "</li>"

    if isinstance(markdown.renderer, HTMLRenderer):
        markdown.renderer.renderers["list_item"] = lambda token: render_item(markdown.renderer, token)


def plugin_table(markdown: Markdown) -> None:
    markdown.register_block("table", r"^ {0,3}\|?.*\|.*$", _parse_table_block, _render_table)


def _split_table_row(line: str) -> List[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells: List[str] = []
    current: List[str] = []
    escaped = False
    for char in stripped:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _parse_alignments(line: str) -> Optional[List[Optional[str]]]:
    cells = _split_table_row(line)
    aligns: List[Optional[str]] = []
    for cell in cells:
        compact = cell.replace(" ", "")
        if not re.match(r"^:?-+:?$", compact):
            return None
        left = compact.startswith(":")
        right = compact.endswith(":")
        if left and right:
            aligns.append("center")
        elif left:
            aligns.append("left")
        elif right:
            aligns.append("right")
        else:
            aligns.append(None)
    return aligns


def _parse_table_block(
    markdown: Markdown,
    lines: Sequence[str],
    index: int,
    match: re.Match[str],
) -> Optional[Tuple[Token, int]]:
    if index + 1 >= len(lines):
        return None
    header = _split_table_row(lines[index])
    aligns = _parse_alignments(lines[index + 1])
    if aligns is None or len(header) < 1:
        return None
    if len(aligns) < len(header):
        aligns += [None] * (len(header) - len(aligns))
    rows: List[List[Token]] = []
    next_index = index + 2
    while next_index < len(lines):
        line = lines[next_index]
        if line.strip() == "" or "|" not in line:
            break
        cells = _split_table_row(line)
        while len(cells) < len(header):
            cells.append("")
        rows.append([
            {"type": "table_cell", "text": cells[col], "align": aligns[col] if col < len(aligns) else None}
            for col in range(len(header))
        ])
        next_index += 1
    return {
        "type": "table",
        "header": [
            {"type": "table_cell", "text": header[col], "align": aligns[col] if col < len(aligns) else None}
            for col in range(len(header))
        ],
        "align": aligns[: len(header)],
        "rows": rows,
    }, next_index


def _render_table(renderer: HTMLRenderer, token: Token) -> str:
    def attrs(cell: Token) -> str:
        align = cell.get("align")
        return f' align="{escape_html(align)}"' if align else ""

    def render_cell(tag: str, cell: Token) -> str:
        return f"<{tag}{attrs(cell)}>" + renderer.render_inlines(cell.get("children", [])) + f"</{tag}>"

    header = "".join(render_cell("th", cell) for cell in token.get("header", []))
    body_rows = []
    for row in token.get("rows", []):
        body_rows.append("<tr>" + "".join(render_cell("td", cell) for cell in row) + "</tr>")
    return (
        "<table>\n<thead>\n<tr>"
        + header
        + "</tr>\n</thead>\n<tbody>\n"
        + "\n".join(body_rows)
        + "\n</tbody>\n</table>"
    )


__all__ = ["Markdown", "HTMLRenderer", "ASTRenderer", "escape_html"]
