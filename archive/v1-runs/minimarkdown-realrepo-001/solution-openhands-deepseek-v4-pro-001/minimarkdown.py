"""
minimarkdown.py - A dependency-free Markdown parser and HTML renderer.

Parses a practical subset of Markdown into tokens, renders to HTML,
and supports an extension system via plugins.

Usage:
    from minimarkdown import Markdown, HTMLRenderer, ASTRenderer, escape_html

    md = Markdown()
    html = md('# Hello **world**')

    md = Markdown(plugins=['strikethrough', 'table'])
    html = md('~~deleted~~')

    ast = Markdown(renderer='ast')('# Hello')
"""

import re
import html as _html

__all__ = ['Markdown', 'HTMLRenderer', 'ASTRenderer', 'escape_html']


# ---------------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------------

def escape_html(text):
    """Escape &, <, >, and double-quote for safe HTML output."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def _token(type_, **kwargs):
    """Create a token dictionary."""
    d = {'type': type_}
    d.update(kwargs)
    return d


# ---------------------------------------------------------------------------
# Inline parser
# ---------------------------------------------------------------------------

_ESCAPABLE = set(r'!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~\\')


class InlineParser:
    """Parse inline Markdown constructs within a block of text."""

    def __init__(self, rules=None):
        self._placeholder_tokens = {}
        self._counter = 0
        self._rules = {} if rules is None else rules

    def _make_ph(self, token):
        key = '\x00%d\x00' % self._counter
        self._placeholder_tokens[key] = token
        self._counter += 1
        return key

    # -- public entry point -----------------------------------------------

    def parse(self, text):
        """Parse *text* into a list of inline token dicts."""
        self._placeholder_tokens = {}
        self._counter = 0
        text = self._process_escapes(text)
        text = self._process_custom_inlines(text)
        text = self._process_code_spans(text)
        text = self._process_autolinks(text)
        tokens = self._parse_links_and_images(text)
        tokens = self._parse_emphasis_in_tokens(tokens)
        tokens = self._process_linebreaks(tokens)
        return self._merge_adjacent_text(tokens)

    # -- escapes ----------------------------------------------------------

    def _process_escapes(self, text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                nxt = text[i + 1]
                if nxt in _ESCAPABLE:
                    # Hard line break: backslash before newline
                    if nxt == '\n':
                        result.append('\x00LB\x00')
                        i += 2
                        continue
                    # Use placeholder so escaped char is not
                    # re-interpreted as emphasis/etc.
                    result.append(self._make_ph(_token('text', text=nxt)))
                    i += 2
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)

    # -- custom inline rules (plugins) ------------------------------------

    def _process_custom_inlines(self, text):
        if not self._rules:
            return text
        result = []
        i = 0
        while i < len(text):
            earliest = None
            for name, (pattern, parse_func, _) in self._rules.items():
                m = pattern.match(text, i)
                if m and (earliest is None or m.start() < earliest[0].start()):
                    earliest = (m, name, parse_func)
            if earliest:
                m, name, parse_func = earliest
                result.append(text[i:m.start()])
                token = parse_func(m)
                if token is not None:
                    result.append(self._make_ph(token))
                else:
                    result.append(text[m.start():m.end()])
                i = m.end()
            else:
                result.append(text[i:])
                break
        return ''.join(result)

    # -- code spans -------------------------------------------------------

    def _process_code_spans(self, text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == '`':
                j = i
                while j < len(text) and text[j] == '`':
                    j += 1
                n_ticks = j - i
                delim = '`' * n_ticks
                close = text.find(delim, j)
                if close != -1:
                    code_text = text[j:close]
                    result.append(self._make_ph(_token('code', text=code_text)))
                    i = close + n_ticks
                else:
                    result.append(delim)
                    i = j
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    # -- autolinks --------------------------------------------------------

    _AUTOLINK_RE = re.compile(
        r'<(https?://[^\s<>]+|'
        r'[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9]'
        r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
        r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>'
    )

    def _process_autolinks(self, text):
        result = []
        last = 0
        for m in self._AUTOLINK_RE.finditer(text):
            result.append(text[last:m.start()])
            url = m.group(1)
            is_email = '@' in url and not url.startswith('http')
            result.append(self._make_ph(_token('autolink', url=url,
                                               is_email=is_email)))
            last = m.end()
        result.append(text[last:])
        return ''.join(result)

    # -- links and images -------------------------------------------------

    def _parse_links_and_images(self, text):
        """Scan for ![...](...) and [...](...) and parse recursively."""
        tokens = []
        i = 0
        n = len(text)
        buf_start = 0

        def flush(end):
            if end > buf_start:
                tokens.append(_token('text', text=text[buf_start:end]))
            return end

        while i < n:
            # placeholder pass-through
            if text[i] == '\x00':
                buf_start = flush(i)
                j = text.find('\x00', i + 1)
                if j != -1:
                    key = text[i:j + 1]
                    if key in self._placeholder_tokens:
                        tokens.append(self._placeholder_tokens[key])
                    i = j + 1
                    buf_start = i
                    continue

            # image  ![alt](url "title")
            if text[i:i + 2] == '![':
                j = self._find_balanced(text, i + 1, '[', ']')
                if j is not None and j + 1 < n and text[j + 1] == '(':
                    k = self._find_balanced(text, j + 1, '(', ')')
                    if k is not None:
                        buf_start = flush(i)
                        alt = text[i + 2:j]
                        url, title = self._split_url_title(text[j + 2:k])
                        alt_tokens = self._parse_links_and_images(alt)
                        tokens.append(_token('image', alt=alt_tokens,
                                             url=url, title=title))
                        i = k + 1
                        buf_start = i
                        continue

            # link  [label](url "title")
            if text[i] == '[':
                j = self._find_balanced(text, i, '[', ']')
                if j is not None and j + 1 < n and text[j + 1] == '(':
                    k = self._find_balanced(text, j + 1, '(', ')')
                    if k is not None:
                        buf_start = flush(i)
                        label = text[i + 1:j]
                        url, title = self._split_url_title(text[j + 2:k])
                        label_tokens = self._parse_links_and_images(label)
                        tokens.append(_token('link', children=label_tokens,
                                             url=url, title=title))
                        i = k + 1
                        buf_start = i
                        continue

            i += 1

        flush(n)
        return tokens

    @staticmethod
    def _find_balanced(text, start, open_c, close_c):
        """Find matching close bracket, handling nesting."""
        depth = 1
        i = start + 1
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                i += 2
                continue
            if text[i] == open_c:
                depth += 1
            elif text[i] == close_c:
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return None

    @staticmethod
    def _split_url_title(raw):
        """Split 'url "title"' into (url, title_or_none)."""
        raw = raw.strip()
        m = re.match(r'^(\S+)\s+"([^"]*)"$', raw)
        if m:
            return m.group(1), m.group(2)
        return raw, None

    # -- emphasis / strong ------------------------------------------------

    def _parse_emphasis_in_tokens(self, tokens):
        """Process emphasis/strong in token list, recursing into children."""
        result = []
        for tok in tokens:
            if tok['type'] == 'text':
                result.extend(self._parse_emphasis_text(tok['text']))
            elif tok['type'] in ('link', 'image'):
                if tok['type'] == 'link':
                    tok['children'] = self._parse_emphasis_in_tokens(
                        tok['children'])
                else:
                    tok['alt'] = self._parse_emphasis_in_tokens(tok['alt'])
                result.append(tok)
            else:
                result.append(tok)
        return result

    def _parse_emphasis_text(self, text):
        """Parse * and _ delimiters for emphasis / strong using a
        simplified delimiter-stack algorithm."""
        # Build a flat segment list
        segments = self._scan_delimiters(text)

        # Process closers against openers
        openers = []  # list of index into segments

        i = 0
        while i < len(segments):
            seg = segments[i]
            if seg['kind'] == 'delim':
                if seg['can_open'] and seg['can_close']:
                    # Both – treat as opener (biased)
                    openers.append(i)
                elif seg['can_open']:
                    openers.append(i)
                elif seg['can_close']:
                    found = False
                    for oi in range(len(openers) - 1, -1, -1):
                        o_idx = openers[oi]
                        o_seg = segments[o_idx]
                        if o_seg['char'] == seg['char']:
                            match_len = min(o_seg['length'], seg['length'])
                            tok_type = 'strong' if match_len >= 2 else 'em'

                            # Content between opener end and closer start
                            inner_text = text[o_seg['end']:seg['start']]
                            inner_tokens = self._parse_emphasis_text(inner_text)

                            token = _token(tok_type, children=inner_tokens)
                            ph = self._make_ph(token)

                            # Replace segments
                            new_seg = {
                                'kind': 'ph', 'key': ph,
                                'start': o_seg['start'], 'end': seg['end']
                            }

                            # Handle remaining chars
                            new_parts = []
                            remain_o = o_seg['length'] - match_len
                            remain_c = seg['length'] - match_len

                            if remain_o > 0:
                                t = o_seg['char'] * remain_o
                                new_parts.insert(0, {
                                    'kind': 'text', 'text': t,
                                    'start': o_seg['start'],
                                    'end': o_seg['start'] + remain_o,
                                })
                                new_seg['start'] = o_seg['start'] + remain_o
                            if remain_c > 0:
                                t = seg['char'] * remain_c
                                new_parts.append({
                                    'kind': 'text', 'text': t,
                                    'start': seg['start'] + match_len,
                                    'end': seg['end'],
                                })

                            segments = (segments[:o_idx] + new_parts +
                                        [new_seg] + segments[i + 1:])
                            openers = [x if x < o_idx else x - o_idx + len(new_parts)
                                       for x in openers[:oi]]
                            found = True
                            i = o_idx + len(new_parts)
                            break
                    if not found:
                        seg['kind'] = 'text'
                        seg['text'] = seg['char'] * seg['length']
                else:
                    seg['kind'] = 'text'
                    seg['text'] = seg['char'] * seg['length']
            i += 1

        # Convert any remaining unmatched delimiters to text
        for seg in segments:
            if seg['kind'] == 'delim':
                seg['kind'] = 'text'
                seg['text'] = seg['char'] * seg['length']

        # Convert segments to tokens
        result = []
        for seg in segments:
            if seg['kind'] == 'text':
                if seg['text']:
                    result.append(_token('text', text=seg['text']))
            elif seg['kind'] == 'ph':
                if seg['key'] in self._placeholder_tokens:
                    result.append(self._placeholder_tokens[seg['key']])
        return result

    def _scan_delimiters(self, text):
        """Build a flat list of segments: text spans and delimiter runs."""
        segments = []
        i = 0
        while i < len(text):
            if text[i] == '\x00':
                j = text.find('\x00', i + 1)
                if j != -1:
                    key = text[i:j + 1]
                    segments.append({
                        'kind': 'ph', 'key': key,
                        'start': i, 'end': j + 1
                    })
                    i = j + 1
                    continue

            if text[i] in '*_':
                ch = text[i]
                j = i
                while j < len(text) and text[j] == ch:
                    j += 1
                length = j - i

                left_flanking = j < len(text) and not text[j].isspace()
                right_flanking = i > 0 and not text[i - 1].isspace()

                if ch == '_':
                    if left_flanking and i > 0 and text[i - 1].isalnum():
                        left_flanking = False
                    if right_flanking and j < len(text) and text[j].isalnum():
                        right_flanking = False

                segments.append({
                    'kind': 'delim',
                    'char': ch,
                    'length': length,
                    'can_open': left_flanking,
                    'can_close': right_flanking,
                    'start': i,
                    'end': j,
                })
                i = j
            else:
                start = i
                while i < len(text) and text[i] not in '*_\x00':
                    i += 1
                if i > start:
                    segments.append({
                        'kind': 'text', 'text': text[start:i],
                        'start': start, 'end': i,
                    })
        return segments

    # -- line breaks ------------------------------------------------------

    def _process_linebreaks(self, tokens):
        """Process hard/soft line breaks in text tokens."""
        result = []
        for tok in tokens:
            if tok['type'] != 'text':
                result.append(tok)
                continue
            text = tok['text']
            # Split on \x00LB\x00 (backslash-newline hard break)
            parts = text.split('\x00LB\x00')
            for pi, part in enumerate(parts):
                if pi > 0:
                    result.append(_token('linebreak', hard=True))
                # Process two-trailing-spaces-then-newline within each part
                self._split_two_space_breaks(part, result)
        return result

    @staticmethod
    def _split_two_space_breaks(text, result):
        """Split text on '  \\n' (two spaces then newline = hard line break)."""
        i = 0
        n = len(text)
        start = 0
        while i < n:
            if text[i:i + 3] == '  \n':
                if start < i:
                    result.append(_token('text', text=text[start:i]))
                result.append(_token('linebreak', hard=True))
                i += 3
                start = i
            else:
                i += 1
        if start < n:
            result.append(_token('text', text=text[start:]))

    # -- utilities --------------------------------------------------------

    def _merge_adjacent_text(self, tokens):
        """Merge adjacent text tokens into single tokens."""
        result = []
        for tok in tokens:
            if tok['type'] == 'text':
                if result and result[-1]['type'] == 'text':
                    result[-1]['text'] += tok['text']
                else:
                    result.append(tok)
            else:
                result.append(tok)
        return result


# ---------------------------------------------------------------------------
# Block parser
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+#+\s*)?$')
_HR_RE = re.compile(r'^\s{0,3}([-*_])\s*\1\s*\1[\1\s]*$')
_FENCE_RE = re.compile(r'^(`{3,})(\w*)\s*$')
_LIST_RE = re.compile(r'^(\s{0,3})([-*+]|\d+\.)\s+(.+)')


class BlockParser:
    """Parse Markdown text into a list of block token dicts."""

    def __init__(self, rules=None):
        self._rules = {} if rules is None else rules

    def parse(self, text):
        """Parse *text* into block tokens."""
        lines = text.split('\n')
        blocks = self._parse_blocks(lines)
        return blocks

    # -- main loop --------------------------------------------------------

    def _parse_blocks(self, lines):
        blocks = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]

            # Blank line
            if not line.strip():
                i += 1
                continue

            # Custom block rules (plugins)
            handled = False
            for name, (pattern, parse_func, _) in self._rules.items():
                m = pattern.match(line)
                if m:
                    result, i = parse_func(m, lines, i, self)
                    if result is not None:
                        if isinstance(result, list):
                            blocks.extend(result)
                        else:
                            blocks.append(result)
                    handled = True
                    break
            if handled:
                continue

            # Fenced code block
            fm = _FENCE_RE.match(line)
            if fm:
                fence = fm.group(1)
                lang = fm.group(2) or None
                i += 1
                code_lines = []
                while i < n:
                    if lines[i].strip() == fence:
                        i += 1
                        break
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(_token('code_block', text='\n'.join(code_lines),
                                     lang=lang))
                continue

            # ATX heading
            hm = _HEADING_RE.match(line)
            if hm:
                level = len(hm.group(1))
                text = hm.group(2).strip()
                blocks.append(_token('heading', level=level, text=text))
                i += 1
                continue

            # Horizontal rule
            if _HR_RE.match(line):
                blocks.append(_token('hr'))
                i += 1
                continue

            # Block quote
            if line.lstrip().startswith('>'):
                quote_lines = []
                while i < n:
                    l = lines[i]
                    if not l.strip():
                        # Peek ahead for quote continuation
                        if i + 1 < n and lines[i + 1].lstrip().startswith('>'):
                            quote_lines.append('')
                            i += 1
                            continue
                        break
                    if not l.lstrip().startswith('>'):
                        break
                    quote_lines.append(re.sub(r'^>\s?', '', l))
                    i += 1
                inner = '\n'.join(quote_lines)
                inner_blocks = self._parse_blocks(inner.split('\n'))
                blocks.append(_token('block_quote', children=inner_blocks))
                continue

            # Indented code block
            if re.match(r'^( {4,}|\t)', line):
                code_lines = []
                while i < n:
                    l = lines[i]
                    if not l.strip():
                        code_lines.append('')
                        i += 1
                        continue
                    m = re.match(r'^( {4,}|\t)', l)
                    if m:
                        code_lines.append(l[m.end():])
                        i += 1
                    else:
                        break
                blocks.append(_token('code_block', text='\n'.join(code_lines)))
                continue

            # List
            lm = _LIST_RE.match(line)
            if lm:
                items, i = self._parse_list(lines, i, n)
                blocks.extend(items)
                continue

            # Paragraph
            para_lines = []
            while i < n:
                l = lines[i]
                if not l.strip():
                    break
                if _is_block_start(l):
                    break
                para_lines.append(l)
                i += 1
            if para_lines:
                text = _join_para_lines(para_lines)
                blocks.append(_token('paragraph', text=text))

        return blocks

    # -- list parsing -----------------------------------------------------

    def _parse_list(self, lines, start, n):
        """Parse a sequence of list items, handling tight/loose."""
        i = start
        items_raw = []  # (ordered, item_raw_text)
        current_ordered = None

        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            lm = _LIST_RE.match(line)
            if not lm:
                break

            marker = lm.group(2)
            is_ordered = marker[0].isdigit()
            if current_ordered is not None and is_ordered != current_ordered:
                break
            current_ordered = is_ordered

            first_line = lm.group(3)
            item_lines = [first_line]
            i += 1

            # Collect continuation lines
            while i < n:
                l = lines[i]
                if not l.strip():
                    # Blank line – could be intra-item or inter-item
                    if i + 1 < n:
                        nxt = lines[i + 1]
                        if (nxt.strip() and
                                not _LIST_RE.match(nxt) and
                                not _is_block_start(nxt)):
                            item_lines.append('')
                            i += 1
                            continue
                    break

                # New list item?
                if _LIST_RE.match(l):
                    next_lm = _LIST_RE.match(l)
                    next_marker = next_lm.group(2)
                    next_ordered = next_marker[0].isdigit()
                    if next_ordered == current_ordered:
                        break

                # Continuation (any indented or regular text)
                item_lines.append(l.strip())
                i += 1

            items_raw.append((is_ordered, '\n'.join(item_lines)))

        if not items_raw:
            return [], i

        # Determine tight vs loose
        is_loose = any('\n\n' in t for _, t in items_raw)

        list_items = []
        for _, raw in items_raw:
            if is_loose:
                child_blocks = self._parse_blocks(raw.split('\n'))
                list_items.append(_token('list_item', children=child_blocks))
            else:
                list_items.append(
                    _token('list_item', children=[_token('paragraph', text=raw)])
                )

        return [_token('list', ordered=current_ordered, tight=not is_loose,
                       children=list_items)], i


def _is_block_start(line):
    """Check if *line* would start a new block type."""
    s = line.strip()
    if not s:
        return True
    if _HEADING_RE.match(s):
        return True
    if _FENCE_RE.match(s):
        return True
    if _HR_RE.match(s):
        return True
    if s.lstrip().startswith('>'):
        return True
    if re.match(r'^( {4,}|\t)', s):
        return True
    if _LIST_RE.match(s):
        return True
    return False


def _join_para_lines(lines):
    """Join paragraph lines, handling hard/soft line breaks."""
    result = []
    for i, line in enumerate(lines):
        if i > 0:
            prev = lines[i - 1]
            if prev.endswith('  '):
                result.append('\n')
            elif prev.endswith('\\'):
                result.append('\n')
            else:
                result.append('\n')
        result.append(line)
    return ''.join(result)


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

class HTMLRenderer:
    """Render token trees to HTML strings."""

    def __init__(self, rules=None):
        self._rules = {} if rules is None else rules

    def render(self, tokens):
        """Render a list of block tokens to HTML."""
        parts = []
        for tok in tokens:
            h = self._render_block(tok)
            if h:
                parts.append(h)
        return '\n'.join(parts)

    def _render_block(self, tok):
        t = tok['type']
        if t == 'heading':
            level = tok['level']
            children = self._render_inlines(
                self._inline_parser.parse(tok['text']))
            return '<h%d>%s</h%d>' % (level, children, level)
        elif t == 'paragraph':
            children = self._render_inlines(
                self._inline_parser.parse(tok['text']))
            return '<p>%s</p>' % children
        elif t == 'code_block':
            code = escape_html(tok['text'])
            lang = tok.get('lang')
            if lang:
                return '<pre><code class="language-%s">%s</code></pre>' % (
                    escape_html(lang), code)
            return '<pre><code>%s</code></pre>' % code
        elif t == 'block_quote':
            inner = self.render(tok['children'])
            return '<blockquote>\n%s\n</blockquote>' % inner
        elif t == 'list':
            tag = 'ol' if tok['ordered'] else 'ul'
            items = []
            for item in tok['children']:
                items.append(self._render_list_item(item, tok['tight']))
            inner = '\n'.join(items)
            return '<%s>\n%s\n</%s>' % (tag, inner, tag)
        elif t == 'list_item':
            return self._render_list_item(tok, True)
        elif t == 'hr':
            return '<hr>'
        elif t in self._rules:
            return self._rules[t](tok, self)
        else:
            return ''

    def _render_list_item(self, tok, tight):
        if tok['type'] == 'task_list_item':
            checked = ' checked' if tok.get('checked') else ''
            cb = '<input type="checkbox" disabled%s>' % checked
            body_parts = [cb + ' ']
            for child in tok['children']:
                if child['type'] == 'paragraph':
                    body_parts.append(self._render_inlines(
                        self._inline_parser.parse(child['text'])))
                else:
                    body_parts.append(self._render_block(child))
            return '<li>%s</li>' % ''.join(body_parts)
        elif tight:
            # Render child paragraph inline (no <p> wrapper)
            body_parts = []
            for child in tok['children']:
                if child['type'] == 'paragraph':
                    body_parts.append(self._render_inlines(
                        self._inline_parser.parse(child['text'])))
                else:
                    body_parts.append(self._render_block(child))
            return '<li>%s</li>' % ''.join(body_parts)
        else:
            inner = self.render(tok['children'])
            return '<li>\n%s\n</li>' % inner

    def _render_inlines(self, tokens):
        """Render inline tokens to HTML."""
        parts = []
        for tok in tokens:
            parts.append(self._render_inline(tok))
        return ''.join(parts)

    def _render_inline(self, tok):
        t = tok['type']
        if t == 'text':
            return escape_html(tok['text'])
        elif t == 'em':
            return '<em>%s</em>' % self._render_inlines(tok['children'])
        elif t == 'strong':
            return '<strong>%s</strong>' % self._render_inlines(
                tok['children'])
        elif t == 'code':
            return '<code>%s</code>' % escape_html(tok['text'])
        elif t == 'link':
            title = ''
            if tok.get('title'):
                title = ' title="%s"' % escape_html(tok['title'])
            return '<a href="%s"%s>%s</a>' % (
                escape_html(tok['url']), title,
                self._render_inlines(tok['children']))
        elif t == 'image':
            title = ''
            if tok.get('title'):
                title = ' title="%s"' % escape_html(tok['title'])
            alt = self._render_inlines(tok['alt'])
            return '<img src="%s" alt="%s"%s>' % (
                escape_html(tok['url']), alt, title)
        elif t == 'linebreak':
            if tok.get('hard'):
                return '<br>\n'
            return '\n'
        elif t == 'autolink':
            url = escape_html(tok['url'])
            if tok['is_email']:
                return '<a href="mailto:%s">%s</a>' % (url, url)
            return '<a href="%s">%s</a>' % (url, url)
        elif t in self._rules:
            return self._rules[t](tok, self)
        else:
            return escape_html(tok.get('text', ''))

    # Connection to inline parser – set by Markdown after construction
    _inline_parser = None


# ---------------------------------------------------------------------------
# AST renderer
# ---------------------------------------------------------------------------

class ASTRenderer:
    """Return token dicts directly (AST output)."""

    def __init__(self, rules=None):
        self._rules = {} if rules is None else rules

    def render(self, tokens):
        return [self._clean_token(t) for t in tokens]

    def _clean_token(self, tok):
        """Return a dict with only public fields (no compiled regex, callbacks, state)."""
        t = tok['type']
        if t == 'heading':
            d = {
                'type': t,
                'level': tok['level'],
                'text': tok['text'],
                'children': [self._clean_token(c) for c in
                             (self._inline_parser.parse(tok['text'])
                              if self._inline_parser else [])]
            }
            return d
        elif t == 'paragraph':
            return {
                'type': t,
                'text': tok['text'],
                'children': [self._clean_token(c) for c in
                             (self._inline_parser.parse(tok['text'])
                              if self._inline_parser else [])]
            }
        elif t in ('em', 'strong', 'link'):
            d = {'type': t, 'children': [self._clean_token(c) for c in
                                         tok.get('children', [])]}
            if t == 'link':
                d['url'] = tok.get('url', '')
                if tok.get('title'):
                    d['title'] = tok['title']
            return d
        elif t == 'image':
            d = {
                'type': t,
                'alt': [self._clean_token(c) for c in tok.get('alt', [])],
                'url': tok.get('url', ''),
            }
            if tok.get('title'):
                d['title'] = tok['title']
            return d
        elif t in ('code_block', 'code'):
            d = {'type': t, 'text': tok.get('text', '')}
            if tok.get('lang'):
                d['lang'] = tok['lang']
            return d
        elif t in ('block_quote', 'list', 'list_item', 'task_list_item'):
            d = {'type': t}
            if t == 'list':
                d['ordered'] = tok.get('ordered', False)
                d['tight'] = tok.get('tight', True)
            if t == 'task_list_item':
                d['checked'] = tok.get('checked', False)
            d['children'] = [self._clean_token(c) for c in
                             tok.get('children', [])]
            return d
        elif t == 'text':
            return {'type': t, 'text': tok.get('text', '')}
        elif t == 'autolink':
            return {'type': t, 'url': tok['url'],
                    'is_email': tok.get('is_email', False)}
        elif t == 'hr':
            return {'type': t}
        elif t == 'linebreak':
            return {'type': t, 'hard': tok.get('hard', False)}
        elif t in self._rules:
            return self._rules[t](tok, self)
        else:
            return {'type': t, 'text': tok.get('text', '')}

    _inline_parser = None


# ---------------------------------------------------------------------------
# Markdown class
# ---------------------------------------------------------------------------

class Markdown:
    """Main Markdown parser and renderer.

    Parameters
    ----------
    renderer:
        - ``None`` (default): render to HTML.
        - ``"ast"`` or an ``ASTRenderer`` instance: return token dicts.
        - ``HTMLRenderer`` instance: use that renderer.
    plugins:
        Iterable of plugin names (``"strikethrough"``, ``"table"``,
        ``"task_list"``) and/or callables that receive this ``Markdown``
        instance.
    """

    def __init__(self, renderer=None, plugins=None):
        self._inline_rules = {}
        self._block_rules = {}
        self._inline_render_rules = {}
        self._block_render_rules = {}
        self._inline_parser = InlineParser(self._inline_rules)
        self._block_parser = BlockParser(self._block_rules)

        # Resolve renderer
        if renderer is None:
            self._renderer = HTMLRenderer(self._inline_render_rules)
        elif renderer == 'ast':
            self._renderer = ASTRenderer(self._inline_render_rules)
        elif isinstance(renderer, ASTRenderer):
            self._renderer = renderer
        elif isinstance(renderer, HTMLRenderer):
            self._renderer = renderer
        else:
            raise ValueError('Unknown renderer: %r' % renderer)

        self._renderer._inline_parser = self._inline_parser

        # Process known plugins and custom callables
        if plugins:
            for p in plugins:
                if callable(p):
                    p(self)
                elif p == 'strikethrough':
                    _install_strikethrough(self)
                elif p == 'table':
                    _install_table(self)
                elif p == 'task_list':
                    _install_task_list(self)
                else:
                    raise ValueError('Unknown plugin: %r' % p)

    # -- public API -------------------------------------------------------

    def __call__(self, text):
        """Parse and render *text*.  Alias for ``markdown(text)``."""
        return self.markdown(text)

    def markdown(self, text):
        """Parse *text* and render to HTML or AST."""
        tokens = self.parse(text)
        return self._renderer.render(tokens)

    def parse(self, text):
        """Return the block token stream for *text* (before final rendering)."""
        return self._block_parser.parse(text)

    def register_inline(self, name, pattern, parse_func, render_func=None):
        """Register an inline syntax rule.

        *pattern* is a compiled regex; *parse_func* receives the match
        object and returns a token dict; *render_func* receives
        ``(token, renderer)`` and returns an HTML string.
        """
        self._inline_rules[name] = (pattern, parse_func, render_func)
        if render_func:
            self._inline_render_rules[name] = render_func

    def register_block(self, name, pattern, parse_func, render_func=None):
        """Register a block syntax rule.

        *pattern* is a compiled regex; *parse_func* receives
        ``(match, lines, index, block_parser)`` and returns
        ``(token_or_list, next_index)``; *render_func* receives
        ``(token, renderer)`` and returns an HTML string.
        """
        self._block_rules[name] = (pattern, parse_func, render_func)
        if render_func:
            self._block_render_rules[name] = render_func


# ---------------------------------------------------------------------------
# Built-in plugins
# ---------------------------------------------------------------------------

# -- strikethrough --------------------------------------------------------

_STRIKE_RE = re.compile(r'~~(.+?)~~')


def _strike_parse(m):
    return _token('strikethrough', children=[_token('text', text=m.group(1))])


def _strike_render(tok, renderer):
    children = renderer._render_inlines(tok['children'])
    return '<del>%s</del>' % children


def _strike_ast(tok, renderer):
    return {
        'type': 'strikethrough',
        'children': [renderer._clean_token(c) for c in tok['children']]
    }


def _install_strikethrough(md):
    md.register_inline('strikethrough', _STRIKE_RE,
                       _strike_parse, _strike_render)


# -- table ----------------------------------------------------------------

_TABLE_LINE_RE = re.compile(r'^\|?.+\|?\s*$')
_TABLE_DELIM_RE = re.compile(r'^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$')


def _parse_table(match, lines, i, block_parser):
    """Parse a GitHub-style pipe table."""
    n = len(lines)
    if i + 1 >= n:
        return None, i

    header_line = lines[i]
    delim_line = lines[i + 1]

    # Validate delimiter row
    if not _TABLE_DELIM_RE.match(delim_line):
        return None, i

    # Parse header
    headers = [c.strip() for c in header_line.strip('|').split('|')]

    # Parse alignments
    delim_cells = [c.strip() for c in delim_line.strip('|').split('|')]
    aligns = []
    for dc in delim_cells:
        left = dc.startswith(':')
        right = dc.endswith(':')
        if left and right:
            aligns.append('center')
        elif right:
            aligns.append('right')
        elif left:
            aligns.append('left')
        else:
            aligns.append(None)

    i += 2

    # Parse body rows
    rows = []
    while i < n:
        l = lines[i]
        if not l.strip():
            break
        if not _TABLE_LINE_RE.match(l):
            break
        cells = [c.strip() for c in l.strip('|').split('|')]
        rows.append(cells)
        i += 1

    if not rows:
        return None, i

    return _token('table', headers=headers, aligns=aligns, rows=rows), i


def _table_render(tok, renderer):
    ip = renderer._inline_parser
    parts = ['<table>']

    # Header
    parts.append('<thead><tr>')
    for h in tok['headers']:
        parts.append('<th>%s</th>' % renderer._render_inlines(ip.parse(h)))
    parts.append('</tr></thead>')

    # Body
    parts.append('<tbody>')
    for row in tok['rows']:
        parts.append('<tr>')
        for ci, cell in enumerate(row):
            align = ''
            if ci < len(tok['aligns']) and tok['aligns'][ci]:
                align = ' align="%s"' % tok['aligns'][ci]
            parts.append('<td%s>%s</td>' % (
                align, renderer._render_inlines(ip.parse(cell))))
        parts.append('</tr>')
    parts.append('</tbody>')

    parts.append('</table>')
    return '\n'.join(parts)


def _table_ast(tok, renderer):
    ip = renderer._inline_parser
    return {
        'type': 'table',
        'headers': tok['headers'],
        'aligns': tok['aligns'],
        'rows': [
            [
                [renderer._clean_token(c) for c in ip.parse(cell)]
                for cell in row
            ]
            for row in tok['rows']
        ]
    }


def _install_table(md):
    md.register_block('table', _TABLE_LINE_RE, _parse_table, _table_render)
    md._inline_render_rules['table'] = _table_render


# -- task list ------------------------------------------------------------

_TASK_RE = re.compile(r'^\s{0,3}([-*+]|\d+\.)\s+\[([ xX])\]\s+(.+)')
_TASK_ITEM_RE = re.compile(r'^\[([ xX])\]\s+(.+)')


def _task_parse(match, lines, i, block_parser):
    """Parse a task list item."""
    n = len(lines)
    items_raw = []
    current_ordered = None

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        tm = _TASK_RE.match(line)
        if not tm:
            break

        marker = tm.group(1)
        is_ordered = marker[0].isdigit()
        if current_ordered is not None and is_ordered != current_ordered:
            break
        current_ordered = is_ordered

        checked = tm.group(2).lower() == 'x'
        first_line = tm.group(3)
        item_lines = [first_line]
        i += 1

        while i < n:
            l = lines[i]
            if not l.strip():
                if i + 1 < n:
                    nxt = lines[i + 1]
                    if (nxt.strip() and not _TASK_RE.match(nxt) and
                            not _is_block_start(nxt)):
                        item_lines.append('')
                        i += 1
                        continue
                break
            if _TASK_RE.match(l):
                tl = _TASK_RE.match(l)
                tlm = tl.group(1)
                tlo = tlm[0].isdigit()
                if tlo == current_ordered:
                    break
            item_lines.append(l.strip())
            i += 1

        items_raw.append((is_ordered, checked, '\n'.join(item_lines)))

    if not items_raw:
        return None, i

    is_loose = any('\n\n' in t for _, _, t in items_raw)

    list_items = []
    for _, checked, raw in items_raw:
        if is_loose:
            child_blocks = block_parser._parse_blocks(raw.split('\n'))
            for cb in child_blocks:
                cb['checked'] = checked
            list_items.append(_token('task_list_item', checked=checked,
                                     children=child_blocks))
        else:
            list_items.append(_token('task_list_item', checked=checked,
                                     children=[_token('paragraph', text=raw)]))

    result = _token('list', ordered=current_ordered, tight=not is_loose,
                    children=list_items)
    return result, i


def _task_render(tok, renderer):
    tag = 'ol' if tok['ordered'] else 'ul'
    ip = renderer._inline_parser
    items_html = []
    for item in tok['children']:
        checked = ' checked' if item.get('checked') else ''
        disabled = ' disabled'
        cb = '<input type="checkbox"%s%s>' % (checked, disabled)
        body = ''
        for child in item['children']:
            if child['type'] == 'paragraph':
                body += renderer._render_inlines(ip.parse(child['text']))
            else:
                body += renderer._render_block(child)
        items_html.append('<li>%s %s</li>' % (cb, body))
    inner = '\n'.join(items_html)
    return '<%s>\n%s\n</%s>' % (tag, inner, tag)


def _task_ast(tok, renderer):
    items = []
    for item in tok['children']:
        d = {'type': 'task_list_item', 'checked': item.get('checked', False)}
        d['children'] = [renderer._clean_token(c) for c in item['children']]
        items.append(d)
    return {
        'type': 'list',
        'ordered': tok.get('ordered', False),
        'tight': tok.get('tight', True),
        'children': items,
    }


def _install_task_list(md):
    md.register_block('task_list', _TASK_RE, _task_parse, _task_render)
