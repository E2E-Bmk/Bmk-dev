"""Minimarkdown: A dependency-free Markdown parser.

Usage:
    from minimarkdown import Markdown, HTMLRenderer, ASTRenderer, escape_html

    md = Markdown()
    html = md("# Hello **world**")
    ast = Markdown("ast")("# Hello **world**")
    toc = md.toc("# Hello\\n\\n## World")
"""

import html as _html
import re
from copy import deepcopy


# ---------------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------------

def escape_html(text):
    """Escape HTML special characters in *text*, including quotes."""
    if not isinstance(text, str):
        text = str(text)
    return _html.escape(text, quote=True)


# ---------------------------------------------------------------------------
# Heading id generator
# ---------------------------------------------------------------------------

class _HeadingIdGenerator:
    """Generate unique heading IDs, reset per-parse."""

    def __init__(self):
        self._used = {}

    def reset(self):
        self._used.clear()

    def generate(self, plain_text):
        """Generate a unique id from plain heading text."""
        # lower-case ASCII, replace runs of whitespace/punctuation with '-'
        slug = plain_text.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug.strip('-')
        if not slug:
            slug = 'heading'
        base = slug
        if base in self._used:
            self._used[base] += 1
            slug = f'{base}-{self._used[base]}'
        else:
            self._used[base] = 1
        return slug


# ---------------------------------------------------------------------------
# Inline parser
# ---------------------------------------------------------------------------

# Escapes  — backslash before a punctuation character
_ESCAPE_RE = re.compile(r'\\([\\`*_{}\[\]()#+\-.!|~<>])')

# Hard line break: two+ trailing spaces before newline, or backslash before newline
_HARD_BREAK_RE = re.compile(r' {2,}\n|\\\n')

# Soft break: a single newline that is not part of a hard break
# (applied after hard breaks are handled)
_SOFT_BREAK_RE = re.compile(r'\n')

# Autolinks
_AUTOLINK_URL_RE = re.compile(r'<(https?://[^>\s]+)>')
_AUTOLINK_EMAIL_RE = re.compile(r'<([^>\s@]+@[^>\s]+)>')


def _find_code_spans(text):
    """Return list of (start, end) for code spans in *text*.

    A code span is delimited by a run of backticks (1+).  The content
    may contain backticks only in smaller runs than the delimiter.
    """
    spans = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '`':
            # Count opening backticks
            j = i
            while j < n and text[j] == '`':
                j += 1
            open_len = j - i
            # Find matching closing backticks
            close_pos = text.find('`' * open_len, j)
            if close_pos != -1:
                # Make sure there are no extra backticks right after
                if close_pos + open_len < n and text[close_pos + open_len] == '`':
                    # This run is part of a longer run; skip
                    i = j
                    continue
                spans.append((i, close_pos + open_len, open_len))
                i = close_pos + open_len
            else:
                # Unmatched opening backticks — treat as literal
                i = j
        else:
            i += 1
    return spans


def _find_links_images(text):
    """Return list of (start, end, is_image, label, url, title) for links/images."""
    results = []
    # We need to find [label](url) or ![alt](url) patterns
    # But we must not match inside code spans.
    pattern = re.compile(
        r'(!?)\[([^\]]*)\]\(\s*([^\s)]+?)(?:\s+"([^"]*)")?\s*\)'
    )
    for m in pattern.finditer(text):
        results.append((m.start(), m.end(),
                         m.group(1) == '!', m.group(2), m.group(3), m.group(4)))
    return results


class InlineParser:
    """Parse inline Markdown content into token lists."""

    def __init__(self, plugins=None):
        self._plugins = plugins or {}
        self._inline_plugins = {}
        for name, info in self._plugins.items():
            if info.get('kind') == 'inline':
                self._inline_plugins[name] = info

    def parse(self, text):
        """Return a list of inline tokens for *text*."""
        if not text:
            return []
        return self._parse_inline(text)

    def _parse_inline(self, text):
        """Top-level parse: handle code spans, then the rest."""
        tokens = []
        i = 0
        n = len(text)

        while i < n:
            # -- code span --
            if text[i] == '`':
                j = i
                while j < n and text[j] == '`':
                    j += 1
                open_len = j - i
                close_pos = text.find('`' * open_len, j)
                if close_pos != -1:
                    # Check not followed by extra backtick
                    if close_pos + open_len < n and text[close_pos + open_len] == '`':
                        tokens.append({'type': 'text', 'text': '`' * open_len})
                        i = j
                        continue
                    content = text[j:close_pos]
                    tokens.append({'type': 'code_span', 'text': content})
                    i = close_pos + open_len
                    continue
                else:
                    tokens.append({'type': 'text', 'text': '`' * open_len})
                    i = j
                    continue

            # -- hard line break --
            m = _HARD_BREAK_RE.match(text, i)
            if m:
                tokens.append({'type': 'line_break'})
                i = m.end()
                continue

            # -- escape --
            m = _ESCAPE_RE.match(text, i)
            if m:
                tokens.append({'type': 'text', 'text': m.group(1)})
                i = m.end()
                continue

            # -- autolink URL --
            m = _AUTOLINK_URL_RE.match(text, i)
            if m:
                url = m.group(1)
                tokens.append({
                    'type': 'link',
                    'url': url,
                    'children': [{'type': 'text', 'text': url}],
                })
                i = m.end()
                continue

            # -- autolink email --
            m = _AUTOLINK_EMAIL_RE.match(text, i)
            if m:
                email = m.group(1)
                tokens.append({
                    'type': 'link',
                    'url': f'mailto:{email}',
                    'children': [{'type': 'text', 'text': email}],
                })
                i = m.end()
                continue

            # -- link / image --
            m = re.match(r'(!?)\[([^\]]*)\]\(\s*([^\s)]+?)(?:\s+"([^"]*)")?\s*\)', text[i:])
            if m:
                is_image = m.group(1) == '!'
                label = m.group(2)
                url = m.group(3)
                title = m.group(4)
                label_tokens = self._parse_inline(label)
                if is_image:
                    token = {
                        'type': 'image',
                        'url': url,
                        'alt': self._plain_text(label_tokens),
                        'children': label_tokens,
                    }
                else:
                    token = {
                        'type': 'link',
                        'url': url,
                        'children': label_tokens,
                    }
                if title:
                    token['title'] = title
                tokens.append(token)
                i += m.end()
                continue

            # -- plugin inline --
            plugin_matched = False
            for name, info in self._inline_plugins.items():
                pat = info['pattern']
                m = pat.match(text, i)
                if m:
                    token = info['parse_func'](m)
                    if not isinstance(token, dict):
                        token = {'type': name, 'text': m.group(0)}
                    token.setdefault('type', name)
                    # If plugin returned text but no children, parse as inline
                    if token.get('text') and not token.get('children'):
                        token['children'] = self._parse_inline(token['text'])
                    tokens.append(token)
                    i = m.end()
                    plugin_matched = True
                    break
            if plugin_matched:
                continue

            # -- emphasis / strong --
            # Handle *** or ___ (emphasis wrapping strong)
            if i + 2 < n and text[i:i + 3] in ('***', '___'):
                ch = text[i]
                close_end = text.find(ch * 3, i + 3)
                if close_end != -1:
                    # inner is the text between outer delimiters: *(...)**
                    inner_text = text[i + 1:close_end + 2]
                    inner_tokens = self._parse_inline(inner_text)
                    tokens.append({'type': 'emphasis', 'children': inner_tokens})
                    i = close_end + 3
                    continue

            # check for ** or __ (strong)
            if i + 1 < n:
                two = text[i:i + 2]
                if two in ('**', '__'):
                    close = text.find(two, i + 2)
                    if close != -1:
                        inner_text = text[i + 2:close]
                        inner_tokens = self._parse_inline(inner_text)
                        tokens.append({'type': 'strong', 'children': inner_tokens})
                        i = close + 2
                        continue

            # check for * or _ (emphasis)
            if text[i] in '*_':
                ch = text[i]
                j = i + 1
                while j < n:
                    if text[j] == ch and (j == 0 or text[j - 1] != '\\'):
                        inner_text = text[i + 1:j]
                        if inner_text:
                            inner_tokens = self._parse_inline(inner_text)
                            tokens.append({'type': 'emphasis', 'children': inner_tokens})
                            i = j + 1
                            break
                    j += 1
                else:
                    tokens.append({'type': 'text', 'text': ch})
                    i += 1
                continue

            # -- soft break --
            if text[i] == '\n':
                tokens.append({'type': 'soft_break'})
                i += 1
                continue

            # -- literal text --
            tokens.append({'type': 'text', 'text': text[i]})
            i += 1

        return self._merge_text_tokens(tokens)

    @staticmethod
    def _merge_text_tokens(tokens):
        """Merge adjacent text tokens into single tokens."""
        merged = []
        for t in tokens:
            if t['type'] == 'text' and merged and merged[-1]['type'] == 'text':
                merged[-1]['text'] += t['text']
            else:
                merged.append(t)
        return merged

    @staticmethod
    def _plain_text(tokens):
        """Extract plain text from inline tokens (for alt text, heading IDs, TOC)."""
        parts = []
        for t in tokens:
            if t['type'] == 'text':
                parts.append(t['text'])
            elif t['type'] == 'code_span':
                parts.append(t.get('text', ''))
            elif t['type'] == 'line_break':
                parts.append(' ')
            elif t['type'] == 'soft_break':
                parts.append(' ')
            elif t['type'] == 'strikethrough':
                parts.append(InlineParser._plain_text(t.get('children', [])))
            elif 'children' in t:
                parts.append(InlineParser._plain_text(t['children']))
        return ''.join(parts)


# ---------------------------------------------------------------------------
# Block parser
# ---------------------------------------------------------------------------

# ATX heading: 1-6 # followed by space
_ATX_RE = re.compile(r'^(#{1,6})\s+(.*)')

# Fenced code open/close: at least 3 backticks or tildes
_FENCE_RE = re.compile(r'^(```|~~~)(\S*)\s*$')

# Horizontal rule: 3+ of - * or _ with optional spaces
_HR_RE = re.compile(r'^[ \t]*([-*_])\s*\1\s*\1[ \t\1]*$')

# Block quote marker
_BLOCKQUOTE_MARKER_RE = re.compile(r'^>\s?(.*)$')

# List markers
_UNORDERED_LIST_RE = re.compile(r'^(\s*)([-*+])\s+(.*)')
_ORDERED_LIST_RE = re.compile(r'^(\s*)(\d{1,9})\.\s+(.*)')

# Task list checkbox (after list marker)
_TASK_CHECKBOX_RE = re.compile(r'^\[([ xX])\]\s+(.*)')

# Table delimiter row
_TABLE_DELIM_RE = re.compile(r'^\|?[\s:]*-{3,}[\s:]*(?:\|[\s:]*-{3,}[\s:]*)*\|?\s*$')


def _is_blank(line):
    return not line.strip()


def _detect_block_type(line, block_plugins):
    """Return the block type of *line*, or None for paragraph."""
    if _is_blank(line):
        return 'blank'
    if _ATX_RE.match(line):
        return 'heading'
    m = _FENCE_RE.match(line)
    if m and len(m.group(1)) >= 3:
        return 'fenced_code'
    if _HR_RE.match(line):
        return 'thematic_break'
    if line.startswith('>'):
        return 'block_quote'
    if _UNORDERED_LIST_RE.match(line) or _ORDERED_LIST_RE.match(line):
        return 'list'
    if line.startswith('    ') or line.startswith('\t'):
        return 'indented_code'
    for _name, info in block_plugins.items():
        if info.get('parse_func') and info['pattern'].match(line):
            return 'plugin'
    return 'paragraph'


class BlockParser:
    """Parse Markdown text into a list of block tokens.

    Uses a line-index-based approach for clean forward-only parsing.
    """

    def __init__(self, inline_parser, heading_ids, plugins=None):
        self._inline = inline_parser
        self._heading_ids = heading_ids
        self._plugins = plugins or {}
        self._block_plugins = {}
        for name, info in self._plugins.items():
            if info.get('kind') == 'block':
                self._block_plugins[name] = info

    def parse(self, text):
        """Parse text into block tokens."""
        if not text:
            return []
        self._heading_ids.reset()
        lines = text.split('\n')
        result, _ = self._parse_blocks(lines, 0)
        return result

    def _parse_blocks(self, lines, start):
        """Parse lines[start:] into block tokens. Returns (tokens, next_index)."""
        result = []
        i = start
        n = len(lines)

        while i < n:
            line = lines[i]

            # Blank line
            if _is_blank(line):
                i += 1
                continue

            # ATX heading
            m = _ATX_RE.match(line)
            if m:
                level = len(m.group(1))
                heading_text = m.group(2).strip()
                children = self._inline.parse(heading_text)
                plain = InlineParser._plain_text(children)
                hid = self._heading_ids.generate(plain)
                result.append({
                    'type': 'heading',
                    'level': level,
                    'text': plain,
                    'children': children,
                    'attrs': {'id': hid},
                })
                i += 1
                continue

            # Fenced code block
            m = _FENCE_RE.match(line)
            if m and len(m.group(1)) >= 3:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                lang = m.group(2) or None
                code_lines = []
                i += 1
                found_end = False
                while i < n:
                    cl = lines[i].strip()
                    if (cl.startswith(fence_char)
                            and len(cl) >= fence_len
                            and all(c == fence_char for c in cl)):
                        i += 1
                        found_end = True
                        break
                    code_lines.append(lines[i])
                    i += 1
                code_text = '\n'.join(code_lines)
                token = {'type': 'block_code', 'text': code_text}
                if lang:
                    token['lang'] = lang
                result.append(token)
                continue

            # Horizontal rule
            if _HR_RE.match(line):
                result.append({'type': 'thematic_break'})
                i += 1
                continue

            # Block quote
            if line.startswith('>'):
                quote_lines = []
                while i < n and lines[i].startswith('>'):
                    m = _BLOCKQUOTE_MARKER_RE.match(lines[i])
                    if m:
                        quote_lines.append(m.group(1))
                    else:
                        quote_lines.append(lines[i][1:])
                    i += 1
                inner_text = '\n'.join(quote_lines)
                inner_blocks, _ = self._parse_blocks(inner_text.split('\n'), 0)
                result.append({
                    'type': 'block_quote',
                    'children': inner_blocks,
                })
                continue

            # Check plugin block (table, etc.)
            plugin_matched = False
            for name, info in self._block_plugins.items():
                if info.get('parse_func') is None:
                    continue
                pat = info['pattern']
                m = pat.match(line)
                if m:
                    token, consumed = info['parse_func'](m, lines, i)
                    if token is not None:
                        token.setdefault('type', name)
                        result.append(token)
                        i += consumed
                        plugin_matched = True
                        break
            if plugin_matched:
                continue

            # List
            ul_m = _UNORDERED_LIST_RE.match(line)
            ol_m = _ORDERED_LIST_RE.match(line)
            if ul_m or ol_m:
                is_ordered = ol_m is not None
                items, i = self._parse_list(lines, i, is_ordered)
                result.append({
                    'type': 'list',
                    'ordered': is_ordered,
                    'items': items,
                })
                continue

            # Indented code block
            if line.startswith('    ') or line.startswith('\t'):
                code_lines = []
                while i < n and (lines[i].startswith('    ') or
                                 lines[i].startswith('\t') or
                                 _is_blank(lines[i])):
                    if lines[i].startswith('    '):
                        code_lines.append(lines[i][4:])
                    elif lines[i].startswith('\t'):
                        code_lines.append(lines[i][1:])
                    else:
                        code_lines.append('')
                    i += 1
                result.append({
                    'type': 'block_code',
                    'text': '\n'.join(code_lines),
                })
                continue

            # Paragraph
            para_lines = [line]
            i += 1
            while i < n and _detect_block_type(lines[i], self._block_plugins) == 'paragraph':
                para_lines.append(lines[i])
                i += 1
            para_text = '\n'.join(para_lines)
            children = self._inline.parse(para_text)
            result.append({'type': 'paragraph', 'children': children})

        return result, i

    # ------------------------------------------------------------------
    # List parsing
    # ------------------------------------------------------------------

    def _parse_list(self, lines, start, is_ordered):
        """Parse a list starting at lines[start]. Returns (items, next_index)."""
        items = []
        i = start
        n = len(lines)

        # Collect raw items (each item is list of lines)
        raw_items = []

        while i < n:
            line = lines[i]
            if _is_blank(line):
                # Look ahead: is the next non-blank line a list item or continuation?
                j = i + 1
                while j < n and _is_blank(lines[j]):
                    j += 1
                if j >= n:
                    break
                nxt = lines[j]
                ul_m = _UNORDERED_LIST_RE.match(nxt)
                ol_m = _ORDERED_LIST_RE.match(nxt)
                is_list_line = (is_ordered and ol_m is not None) or (
                    not is_ordered and ul_m is not None
                )
                if is_list_line:
                    # blank line between items
                    raw_items.append(None)  # marks a loose separator
                    i = j
                    continue
                else:
                    # Check if continuation (indented)
                    indent = len(nxt) - len(nxt.lstrip())
                    if indent >= 2:
                        raw_items.append(None)  # loose separator + continuation
                        i = j
                        continue
                    else:
                        break

            ul_m = _UNORDERED_LIST_RE.match(line)
            ol_m = _ORDERED_LIST_RE.match(line)
            is_list_line = (is_ordered and ol_m is not None) or (
                not is_ordered and ul_m is not None
            )
            if is_list_line:
                raw_items.append([line])
                i += 1
                continue
            else:
                # Check if this is a continuation line (indented)
                indent = len(line) - len(line.lstrip())
                if indent >= 2 and raw_items:
                    raw_items[-1].append(line) if raw_items[-1] is not None else None
                    i += 1
                    continue
                else:
                    break

        # Determine tight vs loose
        tight = None not in raw_items

        # Parse each raw item into a token dict
        has_checks = 'task_list' in self._plugins
        for raw in raw_items:
            if raw is None:
                continue  # separator marker
            item = self._parse_list_item(raw, has_checks)
            items.append(item)

        return items, i

    def _parse_list_item(self, item_lines, has_checks):
        """Parse a single list item's lines into a token dict."""
        first = item_lines[0]
        ul_m = _UNORDERED_LIST_RE.match(first)
        ol_m = _ORDERED_LIST_RE.match(first)
        if ul_m:
            rest = ul_m.group(3)
        else:
            rest = ol_m.group(3)

        # Check for task checkbox
        checked = None
        if has_checks:
            cb_m = _TASK_CHECKBOX_RE.match(rest)
            if cb_m:
                checked = cb_m.group(1).lower() == 'x'
                rest = cb_m.group(2)

        # Build item content text
        content_lines = [rest]
        for cl in item_lines[1:]:
            # Remove up to 4 spaces of indentation for continuation
            stripped = cl
            if len(cl) - len(cl.lstrip()) >= 2:
                stripped = cl[cl.index(cl[0]) + min(4, len(cl) - len(cl.lstrip())):]
            content_lines.append(stripped)

        text = ' '.join(content_lines).strip()
        children = self._inline.parse(text)

        item = {
            'text': text,
            'children': children,
        }
        if checked is not None:
            item['checked'] = checked
        return item


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------

class HTMLRenderer:
    """Render a token tree to an HTML string."""

    def __init__(self, plugins=None):
        self._plugins = plugins or {}
        self._block_renderers = {}
        self._inline_renderers = {}
        for name, info in self._plugins.items():
            render_func = info.get('render_func')
            if render_func:
                if info.get('kind') == 'block':
                    self._block_renderers[name] = render_func
                elif info.get('kind') == 'inline':
                    self._inline_renderers[name] = render_func

    def render(self, tokens):
        """Render a list of block tokens to HTML."""
        parts = []
        for t in tokens:
            parts.append(self._render_block(t))
        return '\n'.join(parts)

    def render_inlines(self, tokens):
        """Render a list of inline tokens to HTML."""
        parts = []
        for t in tokens:
            parts.append(self._render_inline(t))
        return ''.join(parts)

    def _render_block(self, token):
        t = token['type']
        children = token.get('children', [])

        if t == 'heading':
            level = token['level']
            hid = token.get('attrs', {}).get('id', '')
            content = self.render_inlines(children)
            return f'<h{level} id="{escape_html(hid)}">{content}</h{level}>'

        elif t == 'paragraph':
            content = self.render_inlines(children)
            return f'<p>{content}</p>'

        elif t == 'block_code':
            code_text = escape_html(token.get('text', ''))
            lang = token.get('lang')
            if lang:
                return f'<pre><code class="language-{escape_html(lang)}">{code_text}</code></pre>'
            return f'<pre><code>{code_text}</code></pre>'

        elif t == 'block_quote':
            inner = self.render(children)
            return f'<blockquote>\n{inner}\n</blockquote>'

        elif t == 'list':
            ordered = token.get('ordered', False)
            tag = 'ol' if ordered else 'ul'
            items_html = []
            for item in token.get('items', []):
                items_html.append(self._render_list_item(item))
            inner = '\n'.join(items_html)
            return f'<{tag}>\n{inner}\n</{tag}>'

        elif t == 'thematic_break':
            return '<hr>'

        elif t == 'table':
            return self._render_table(token)

        elif t in self._block_renderers:
            return self._block_renderers[t](self, token)

        else:
            if children:
                return self.render(children)
            return ''

    def _render_list_item(self, item):
        inner = self.render_inlines(item.get('children', []))
        checkbox = ''
        if 'checked' in item:
            attr = ' checked' if item['checked'] else ''
            checkbox = f'<input type="checkbox" disabled{attr}> '
        return f'<li>{checkbox}{inner}</li>'

    def _render_inline(self, token):
        t = token['type']
        children = token.get('children', [])

        if t == 'text':
            return escape_html(token.get('text', ''))

        elif t == 'emphasis':
            return f'<em>{self.render_inlines(children)}</em>'

        elif t == 'strong':
            return f'<strong>{self.render_inlines(children)}</strong>'

        elif t == 'code_span':
            return f'<code>{escape_html(token.get("text", ""))}</code>'

        elif t == 'link':
            url = escape_html(token.get('url', ''))
            title = token.get('title')
            title_attr = f' title="{escape_html(title)}"' if title else ''
            return f'<a href="{url}"{title_attr}>{self.render_inlines(children)}</a>'

        elif t == 'image':
            url = escape_html(token.get('url', ''))
            alt = escape_html(token.get('alt', ''))
            title = token.get('title')
            title_attr = f' title="{escape_html(title)}"' if title else ''
            return f'<img src="{url}" alt="{alt}"{title_attr}>'

        elif t == 'line_break':
            return '<br>\n'

        elif t == 'soft_break':
            return '\n'

        elif t == 'strikethrough':
            return f'<del>{self.render_inlines(children)}</del>'

        elif t in self._inline_renderers:
            return self._inline_renderers[t](self, token)

        else:
            if children:
                return self.render_inlines(children)
            return escape_html(token.get('text', ''))

    def _render_table(self, token):
        header = token.get('header', [])
        aligns = token.get('align', [])
        rows = token.get('rows', [])

        parts = ['<table>']

        if header:
            parts.append('<thead><tr>')
            for ci, cell in enumerate(header):
                align = aligns[ci] if ci < len(aligns) else None
                align_attr = f' align="{align}"' if align else ''
                inner = self.render_inlines(cell.get('children', []))
                parts.append(f'<th{align_attr}>{inner}</th>')
            parts.append('</tr></thead>')

        if rows:
            parts.append('<tbody>')
            for row in rows:
                parts.append('<tr>')
                for ci, cell in enumerate(row):
                    align = aligns[ci] if ci < len(aligns) else None
                    align_attr = f' align="{align}"' if align else ''
                    inner = self.render_inlines(cell.get('children', []))
                    parts.append(f'<td{align_attr}>{inner}</td>')
                parts.append('</tr>')
            parts.append('</tbody>')

        parts.append('</table>')
        return '\n'.join(parts)


class ASTRenderer:
    """Return token dictionaries (deep-copied)."""

    @staticmethod
    def render(tokens):
        """Deep-copy the token tree for safe AST output."""
        return deepcopy(tokens)


# ---------------------------------------------------------------------------
# Plugin definitions
# ---------------------------------------------------------------------------

_STRIKETHROUGH_RE = re.compile(r'~~(.+?)~~')


def _strikethrough_parse(match):
    """Parse strikethrough inner text as inline content."""
    # The parse_func only receives the match; inline parsing happens
    # later, so just return raw text and let the parser handle children.
    return {'type': 'strikethrough', 'text': match.group(1)}


def _strikethrough_render(renderer, token):
    """Render strikethrough with inline-parsed children."""
    children = token.get('children', [])
    inner = renderer.render_inlines(children)
    return f'<del>{inner}</del>'


# Table plugin — parse_func receives (match, lines, index) and
# returns (token_dict_or_None, lines_consumed).

def _table_parse(match, lines, idx):
    """Parse a pipe table starting at lines[idx]."""
    header_text = lines[idx]
    header_cells = _split_table_row(header_text)

    # Need at least a header row + delimiter row
    if idx + 1 >= len(lines):
        return None, 0

    delim_line = lines[idx + 1]
    if not _TABLE_DELIM_RE.match(delim_line):
        return None, 0

    aligns = _parse_table_aligns(delim_line)
    consumed = 2  # header + delimiter

    # Collect body rows
    rows = []
    ri = idx + 2
    while ri < len(lines):
        rl = lines[ri]
        if _is_blank(rl):
            break
        if '|' not in rl:
            break
        rows.append(_split_table_row(rl))
        ri += 1
        consumed += 1

    # Build token (inline parsing deferred)
    header = [{'text': c.strip(), 'children': []} for c in header_cells]
    body = [[{'text': c.strip(), 'children': []} for c in row] for row in rows]

    token = {
        'type': 'table',
        'header': header,
        'align': aligns,
        'rows': body,
    }
    return token, consumed


def _split_table_row(line):
    """Split a table row into cells."""
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [c for c in line.split('|')]


def _parse_table_aligns(delim_line):
    """Parse alignment from delimiter row."""
    cells = _split_table_row(delim_line)
    aligns = []
    for c in cells:
        c = c.strip()
        left = c.startswith(':')
        right = c.endswith(':')
        if left and right:
            aligns.append('center')
        elif right:
            aligns.append('right')
        elif left:
            aligns.append('left')
        else:
            aligns.append(None)
    return aligns


# ---------------------------------------------------------------------------
# Main Markdown class
# ---------------------------------------------------------------------------

class Markdown:
    """Markdown parser and renderer.

    Parameters:
        renderer: ``'ast'``, ``ASTRenderer``, ``HTMLRenderer``, or None (default HTML).
        plugins: iterable of plugin names or callables.
    """

    def __init__(self, renderer=None, plugins=None):
        self._plugins = {}
        self._heading_ids = _HeadingIdGenerator()
        self._inline_parser = InlineParser(self._plugins)
        self._block_parser = BlockParser(
            self._inline_parser, self._heading_ids, self._plugins
        )

        # Resolve renderer
        self._ast_mode = False
        if renderer is None:
            self._renderer = HTMLRenderer(self._plugins)
        elif renderer == 'ast':
            self._renderer = ASTRenderer()
            self._ast_mode = True
        elif isinstance(renderer, ASTRenderer):
            self._renderer = renderer
            self._ast_mode = True
        elif isinstance(renderer, HTMLRenderer):
            self._renderer = renderer
        else:
            raise ValueError(f'Unknown renderer: {renderer}')

        # Activate named plugins
        if plugins:
            for p in plugins:
                if isinstance(p, str):
                    self._activate_named_plugin(p)
                elif callable(p):
                    p(self)
                else:
                    raise ValueError(f'Unknown plugin: {p}')

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def __call__(self, text):
        return self.markdown(text)

    def markdown(self, text):
        """Parse *text* and render to HTML or AST."""
        tokens = self._block_parser.parse(text)
        self._post_process_tokens(tokens)
        return self._renderer.render(tokens)

    def parse(self, text):
        """Parse *text* and return the canonical token tree."""
        tokens = self._block_parser.parse(text)
        self._post_process_tokens(tokens)
        return tokens

    def tokens(self, text):
        """Alias for ``parse()``."""
        return self.parse(text)

    def walk(self, tokens):
        """Iterate over all tokens in a token tree, depth-first."""
        for t in tokens:
            yield t
            for child_list_name in ('children', 'items'):
                if child_list_name in t:
                    yield from self.walk(t[child_list_name])
            for container_name in ('header', 'rows'):
                if container_name in t:
                    for row_or_cell in t[container_name]:
                        if isinstance(row_or_cell, list):
                            for cell in row_or_cell:
                                yield cell
                                if 'children' in cell:
                                    yield from self.walk(cell['children'])
                        else:
                            yield row_or_cell
                            if 'children' in row_or_cell:
                                yield from self.walk(row_or_cell['children'])

    def render(self, tokens, renderer=None):
        """Render an existing token tree."""
        if renderer is None:
            r = self._renderer
        elif renderer == 'ast':
            r = ASTRenderer()
        elif isinstance(renderer, (HTMLRenderer, ASTRenderer)):
            r = renderer
        else:
            r = HTMLRenderer(self._plugins)
        return r.render(tokens)

    def toc(self, text):
        """Return a list of heading TOC entries in document order."""
        tokens = self.parse(text)
        return self._extract_toc(tokens)

    def register_inline(self, name, pattern, parse_func, render_func=None):
        """Register a custom inline plugin rule.

        *parse_func(match)* receives the regex match object and must return
        token fields (at minimum a ``type`` key).

        *render_func(renderer, token)* receives the HTML renderer and token
        dict and must return an HTML string.
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._plugins[name] = {
            'kind': 'inline',
            'pattern': pattern,
            'parse_func': parse_func,
            'render_func': render_func,
        }
        self._inline_parser = InlineParser(self._plugins)
        self._block_parser = BlockParser(
            self._inline_parser, self._heading_ids, self._plugins
        )
        if render_func and not self._ast_mode:
            self._renderer = HTMLRenderer(self._plugins)

    def register_block(self, name, pattern, parse_func, render_func=None):
        """Register a custom block plugin rule.

        *parse_func(match, lines, idx)* receives the regex match, the full
        list of source lines, and the current line index.  It must return
        ``(token_or_None, lines_consumed)``.

        *render_func(renderer, token)* receives the HTML renderer and token
        dict and must return an HTML string.
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._plugins[name] = {
            'kind': 'block',
            'pattern': pattern,
            'parse_func': parse_func,
            'render_func': render_func,
        }
        self._inline_parser = InlineParser(self._plugins)
        self._block_parser = BlockParser(
            self._inline_parser, self._heading_ids, self._plugins
        )
        if render_func and not self._ast_mode:
            self._renderer = HTMLRenderer(self._plugins)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _activate_named_plugin(self, name):
        """Activate a known plugin by name."""
        if name == 'strikethrough':
            self.register_inline(
                'strikethrough',
                _STRIKETHROUGH_RE,
                _strikethrough_parse,
                _strikethrough_render,
            )
        elif name == 'table':
            self.register_block('table', re.compile(r'.*\|.*'), _table_parse, None)
        elif name == 'task_list':
            # task_list modifies list item parsing via the has_checks
            # flag in _parse_list; it does not need its own parse_func.
            self._plugins['task_list'] = {
                'kind': 'block',
                'pattern': re.compile(r'^(?!x)x'),  # never matches
                'parse_func': None,
                'render_func': None,
            }
            self._block_parser = BlockParser(
                self._inline_parser, self._heading_ids, self._plugins
            )
        else:
            raise ValueError(f'Unknown plugin name: {name}')

    def _post_process_tokens(self, tokens):
        """Inline-parse text in table cells and descend into children."""
        for t in tokens:
            if t['type'] == 'table':
                for cell in t.get('header', []):
                    if 'text' in cell and not cell.get('children'):
                        cell['children'] = self._inline_parser.parse(cell['text'])
                for row in t.get('rows', []):
                    for cell in row:
                        if 'text' in cell and not cell.get('children'):
                            cell['children'] = self._inline_parser.parse(cell['text'])
            elif t['type'] == 'block_quote':
                self._post_process_tokens(t.get('children', []))
            if 'children' in t:
                self._post_process_tokens(t['children'])

    def _extract_toc(self, tokens):
        """Extract heading entries for TOC."""
        entries = []
        for t in tokens:
            if t['type'] == 'heading':
                entries.append({
                    'level': t['level'],
                    'text': t['text'],
                    'id': t['attrs']['id'],
                })
            elif t['type'] == 'block_quote':
                entries.extend(self._extract_toc(t.get('children', [])))
        return entries
