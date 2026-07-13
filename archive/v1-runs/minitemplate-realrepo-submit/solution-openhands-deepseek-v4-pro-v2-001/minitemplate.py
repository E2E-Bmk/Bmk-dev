"""
minitemplate.py — A compact Jinja-like template engine.

Python 3.11, standard library only.
"""
from __future__ import annotations

import html
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

__all__ = [
    "Environment",
    "Template",
    "TemplateSyntaxError",
    "TemplateNotFound",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════════════


class TemplateSyntaxError(Exception):
    """Raised when a template has invalid syntax."""

    pass


class TemplateNotFound(Exception):
    """Raised when a named template is not found."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Lexer — splits template source into segments (text, var-tag, block-tag)
# ═══════════════════════════════════════════════════════════════════════════════


def _tokenize(source: str) -> List[Dict[str, Any]]:
    """Split template source into a flat list of segments.

    Each segment is a dict with:
      type   — 'text', 'var', or 'block'
      content— the inner content string
      trim_before / trim_after — bool, whether whitespace trimming applies
    """
    segments: List[Dict[str, Any]] = []
    i = 0
    n = len(source)

    while i < n:
        if i + 1 >= n:
            segments.append(
                {"type": "text", "content": source[i:], "trim_before": False, "trim_after": False}
            )
            break

        two = source[i : i + 2]

        if two in ("{{", "{%"):
            is_var = two == "{{"
            i += 2

            # trim-before?
            trim_before = i < n and source[i] == "-"
            if trim_before:
                i += 1

            # skip whitespace between opening marker and content
            while i < n and source[i] in " \t":
                i += 1

            content_start = i

            # closing markers
            plain_close = "}}" if is_var else "%}"
            trim_close = "-}}" if is_var else "-%}"

            j = i
            depth = 1
            in_str = False
            str_quote = ""

            while j < n and depth > 0:
                ch = source[j]

                if in_str:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == str_quote:
                        in_str = False
                    j += 1
                    continue

                if ch in "'\"":
                    in_str = True
                    str_quote = ch
                    j += 1
                    continue

                # check for nested opens
                if source[j : j + 2] == "{{":
                    depth += 1
                    j += 2
                    continue
                if source[j : j + 2] == "{%":
                    depth += 1
                    j += 2
                    continue

                # check for trim-close (longer pattern first)
                if j + 2 < n and source[j : j + 3] == trim_close:
                    depth -= 1
                    if depth == 0:
                        trim_after = True
                        i = j + 3
                        break
                    j += 3
                    continue

                # check for plain close
                if source[j : j + 2] == plain_close:
                    depth -= 1
                    if depth == 0:
                        trim_after = False
                        i = j + 2
                        break
                    j += 2
                    continue

                j += 1
            else:
                raise TemplateSyntaxError("Unclosed tag")

            # content between markers (before closing marker, after trimming)
            raw = source[content_start:j].strip()
            segments.append(
                {
                    "type": "var" if is_var else "block",
                    "content": raw,
                    "trim_before": trim_before,
                    "trim_after": trim_after,
                }
            )
        else:
            # text up to next tag
            j = i
            while j < n and source[j : j + 2] not in ("{{", "{%"):
                j += 1
            text = source[i:j]
            if text:
                segments.append(
                    {"type": "text", "content": text, "trim_before": False, "trim_after": False}
                )
            i = j

    # Apply whitespace trimming
    for idx, seg in enumerate(segments):
        if seg["trim_before"] and idx > 0 and segments[idx - 1]["type"] == "text":
            segments[idx - 1]["content"] = segments[idx - 1]["content"].rstrip()
        if seg["trim_after"] and idx + 1 < len(segments) and segments[idx + 1]["type"] == "text":
            segments[idx + 1]["content"] = segments[idx + 1]["content"].lstrip()

    return segments


# ═══════════════════════════════════════════════════════════════════════════════
# Expression tokeniser — tokenises the interior of {{ }} and {% %} blocks
# ═══════════════════════════════════════════════════════════════════════════════

_EXPR_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (==|!=|<=|>=|<|>)          |   # comparison operators
        (not\s+in|in)              |   # membership
        (is\s+not|is)              |   # tests
        (and|or|not)               |   # logical
        (\|\|)                     |   # concat (unused)
        (\|)                       |   # filter pipe
        (\.)                       |   # dot
        (,)                        |   # comma
        (\()                       |   # lparen
        (\))                       |   # rparen
        (\[)                       |   # lbracket
        (\])                       |   # rbracket
        (=)                        |   # equals (for with/assignment)
        (True|False|None)          |   # keywords
        (\d+\.\d+|\d+)            |   # numbers
        (\w+)                      |   # identifiers
        ("(?:[^"\\]|\\.)*")       |   # double-quoted string
        ('(?:[^'\\]|\\.)*')       |   # single-quoted string
    )
    """,
    re.VERBOSE | re.DOTALL,
)


def _tokenize_expr(expr: str) -> List[Tuple[str, str]]:
    """Tokenize an expression string into (type, value) pairs.

    Token types: OP, PIPE, DOT, COMMA, LPAREN, RPAREN, LBRACKET, RBRACKET,
                 EQ, KW, NUM, ID, STR
    """
    tokens: List[Tuple[str, str]] = []
    pos = 0
    while pos < len(expr):
        m = _EXPR_TOKEN_RE.match(expr, pos)
        if not m:
            # skip whitespace
            if expr[pos] in " \t\n\r":
                pos += 1
                continue
            raise TemplateSyntaxError(f"Unexpected character {expr[pos]!r} in expression")
        pos = m.end()
        if m.group(1):
            tokens.append(("OP", m.group(1)))
        elif m.group(2):
            tokens.append(("OP", m.group(2)))
        elif m.group(3):
            tokens.append(("OP", m.group(3)))
        elif m.group(4):
            tokens.append(("OP", m.group(4)))
        elif m.group(6):
            tokens.append(("PIPE", "|"))
        elif m.group(7):
            tokens.append(("DOT", "."))
        elif m.group(8):
            tokens.append(("COMMA", ","))
        elif m.group(9):
            tokens.append(("LPAREN", "("))
        elif m.group(10):
            tokens.append(("RPAREN", ")"))
        elif m.group(11):
            tokens.append(("LBRACKET", "["))
        elif m.group(12):
            tokens.append(("RBRACKET", "]"))
        elif m.group(13):
            tokens.append(("EQ", "="))
        elif m.group(14):
            tokens.append(("KW", m.group(14)))
        elif m.group(15):
            tokens.append(("NUM", m.group(15)))
        elif m.group(16):
            tokens.append(("ID", m.group(16)))
        elif m.group(17):
            tokens.append(("STR", m.group(17)))
        elif m.group(18):
            tokens.append(("STR", m.group(18)))
    return tokens


# ═══════════════════════════════════════════════════════════════════════════════
# AST nodes
# ═══════════════════════════════════════════════════════════════════════════════


class _Node:
    """Base AST node."""

    pass


class _Text(_Node):
    __slots__ = ("text",)

    def __init__(self, text: str):
        self.text = text

    def __repr__(self):
        return f"_Text({self.text!r})"


class _Print(_Node):
    __slots__ = ("expr",)

    def __init__(self, expr: _Expr):
        self.expr = expr

    def __repr__(self):
        return f"_Print({self.expr!r})"


class _If(_Node):
    __slots__ = ("branches", "else_body")

    def __init__(self, branches: List[Tuple[_Expr, List[_Node]]], else_body: Optional[List[_Node]] = None):
        self.branches = branches  # [(test_expr, body_nodes), ...]
        self.else_body = else_body or []


class _For(_Node):
    __slots__ = ("loop_var", "iter_expr", "body", "else_body")

    def __init__(self, loop_var: str, iter_expr: _Expr, body: List[_Node], else_body: Optional[List[_Node]] = None):
        self.loop_var = loop_var
        self.iter_expr = iter_expr
        self.body = body
        self.else_body = else_body or []


class _Block(_Node):
    __slots__ = ("name", "body")

    def __init__(self, name: str, body: List[_Node]):
        self.name = name
        self.body = body


class _Extends(_Node):
    __slots__ = ("parent_name",)

    def __init__(self, parent_name: str):
        self.parent_name = parent_name


class _Include(_Node):
    __slots__ = ("template_name",)

    def __init__(self, template_name: str):
        self.template_name = template_name


class _Import(_Node):
    __slots__ = ("template_name", "namespace")

    def __init__(self, template_name: str, namespace: str):
        self.template_name = template_name
        self.namespace = namespace


class _MacroDef(_Node):
    __slots__ = ("name", "params", "body")

    def __init__(self, name: str, params: List[str], body: List[_Node]):
        self.name = name
        self.params = params
        self.body = body


class _With(_Node):
    __slots__ = ("assignments", "body")

    def __init__(self, assignments: List[Tuple[str, _Expr]], body: List[_Node]):
        self.assignments = assignments  # [(var_name, expr), ...]
        self.body = body


class _Autoescape(_Node):
    __slots__ = ("enabled", "body")

    def __init__(self, enabled: bool, body: List[_Node]):
        self.enabled = enabled
        self.body = body


class _MacroCall(_Node):
    __slots__ = ("macro_expr", "args")

    def __init__(self, macro_expr, args: List[_Expr]):
        self.macro_expr = macro_expr
        self.args = args


# ═══════════════════════════════════════════════════════════════════════════════
# Expression AST
# ═══════════════════════════════════════════════════════════════════════════════


class _Expr:
    """Base expression node."""

    pass


class _Literal(_Expr):
    _empty = object()

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"_Literal({self.value!r})"


class _Name(_Expr):
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"_Name({self.name!r})"


class _GetAttr(_Expr):
    __slots__ = ("obj", "attr")

    def __init__(self, obj: _Expr, attr: str):
        self.obj = obj
        self.attr = attr

    def __repr__(self):
        return f"_GetAttr({self.obj!r}, {self.attr!r})"


class _GetItem(_Expr):
    __slots__ = ("obj", "key")

    def __init__(self, obj: _Expr, key: _Expr):
        self.obj = obj
        self.key = key


class _Filter(_Expr):
    __slots__ = ("expr", "name", "args")

    def __init__(self, expr: _Expr, name: str, args: List[_Expr]):
        self.expr = expr
        self.name = name
        self.args = args

    def __repr__(self):
        return f"_Filter({self.expr!r}, {self.name!r}, {self.args!r})"


class _Test(_Expr):
    __slots__ = ("expr", "name", "negated")

    def __init__(self, expr: _Expr, name: str, negated: bool = False):
        self.expr = expr
        self.name = name
        self.negated = negated


class _BinOp(_Expr):
    __slots__ = ("left", "op", "right")

    def __init__(self, left: _Expr, op: str, right: _Expr):
        self.left = left
        self.op = op
        self.right = right


class _UnaryOp(_Expr):
    __slots__ = ("op", "operand")

    def __init__(self, op: str, operand: _Expr):
        self.op = op
        self.operand = operand


class _Call(_Expr):
    __slots__ = ("func", "args")

    def __init__(self, func: _Expr, args: List[_Expr]):
        self.func = func
        self.args = args


_UNDEFINED = object()
"""Sentinel for undefined values."""


# ═══════════════════════════════════════════════════════════════════════════════
# Expression parser (Pratt-style)
# ═══════════════════════════════════════════════════════════════════════════════

_PREC = {
    "or": 1,
    "and": 2,
    "not": 3,
    "==": 4,
    "!=": 4,
    "<": 4,
    ">": 4,
    "<=": 4,
    ">=": 4,
    "in": 4,
    "not in": 4,
    "is": 4,
    "is not": 4,
    "|": 5,
    ".": 6,
}


def _parse_expr(tokens: List[Tuple[str, str]], pos: int = 0) -> Tuple[_Expr, int]:
    """Parse expression from tokens starting at pos.

    Returns (expr_node, new_position).

    Grammar (precedence low → high):
      expr    → or_expr
      or_expr → and_expr ("or" and_expr)*
      and_expr→ not_expr ("and" not_expr)*
      not_expr→ "not" not_expr | comp_expr
      comp_expr→ filter_expr (COMP_OP filter_expr)*
      filter_expr → primary ("|" ID ("(" args ")")?)*
      primary → literal | ID ( "." ID | "[" expr "]" | "(" args ")" )*
    """
    return _parse_or(tokens, pos)


def _parse_or(tokens, pos):
    left, pos = _parse_and(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == "OP" and tokens[pos][1] == "or":
        pos += 1
        right, pos = _parse_and(tokens, pos)
        left = _BinOp(left, "or", right)
    return left, pos


def _parse_and(tokens, pos):
    left, pos = _parse_not(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == "OP" and tokens[pos][1] == "and":
        pos += 1
        right, pos = _parse_not(tokens, pos)
        left = _BinOp(left, "and", right)
    return left, pos


def _parse_not(tokens, pos):
    if pos < len(tokens) and tokens[pos][0] == "OP" and tokens[pos][1] == "not":
        pos += 1
        operand, pos = _parse_not(tokens, pos)
        return _UnaryOp("not", operand), pos
    return _parse_comp(tokens, pos)


def _parse_comp(tokens, pos):
    left, pos = _parse_filter(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == "OP":
        op = tokens[pos][1]
        if op not in ("==", "!=", "<", ">", "<=", ">=", "in", "not in", "is", "is not"):
            break
        pos += 1
        # special: is/is not have ident, not expr
        if op in ("is", "is not"):
            if pos < len(tokens) and tokens[pos][0] == "ID":
                test_name = tokens[pos][1]
                pos += 1
                negated = op == "is not"
                left = _Test(left, test_name, negated)
            else:
                raise TemplateSyntaxError(f"Expected test name after 'is'")
        else:
            right, pos = _parse_filter(tokens, pos)
            left = _BinOp(left, op, right)
    return left, pos


def _parse_filter(tokens, pos):
    left, pos = _parse_primary(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == "PIPE":
        pos += 1
        if pos < len(tokens) and tokens[pos][0] == "ID":
            filter_name = tokens[pos][1]
            pos += 1
            args: List[_Expr] = []
            if pos < len(tokens) and tokens[pos][0] == "LPAREN":
                pos, args = _parse_args(tokens, pos)
            left = _Filter(left, filter_name, args)
        else:
            raise TemplateSyntaxError("Expected filter name after '|'")
    return left, pos


def _parse_primary(tokens, pos):
    if pos >= len(tokens):
        raise TemplateSyntaxError("Unexpected end of expression")

    tok_type, tok_val = tokens[pos]

    if tok_type == "STR":
        val = tok_val[1:-1]  # strip quotes
        # handle escapes
        val = val.replace('\\"', '"').replace("\\'", "'").replace("\\\\", "\\")
        pos += 1
        node: _Expr = _Literal(val)
    elif tok_type == "NUM":
        pos += 1
        if "." in tok_val:
            node = _Literal(float(tok_val))
        else:
            node = _Literal(int(tok_val))
    elif tok_type == "KW":
        pos += 1
        if tok_val == "True":
            node = _Literal(True)
        elif tok_val == "False":
            node = _Literal(False)
        elif tok_val == "None":
            node = _Literal(None)
        else:
            raise TemplateSyntaxError(f"Unexpected keyword {tok_val!r}")
    elif tok_type == "ID":
        name = tok_val
        pos += 1
        node = _Name(name)
    elif tok_type == "LPAREN":
        pos += 1
        node, pos = _parse_or(tokens, pos)
        if pos < len(tokens) and tokens[pos][0] == "RPAREN":
            pos += 1
        else:
            raise TemplateSyntaxError("Expected ')'")
    else:
        raise TemplateSyntaxError(f"Unexpected token {tok_type} {tok_val!r}")

    # postfix: .attr, [expr], (args)
    while pos < len(tokens):
        tt, tv = tokens[pos]
        if tt == "DOT":
            pos += 1
            if pos < len(tokens) and tokens[pos][0] == "ID":
                node = _GetAttr(node, tokens[pos][1])
                pos += 1
            else:
                raise TemplateSyntaxError("Expected attribute name after '.'")
        elif tt == "LBRACKET":
            pos += 1
            key, pos = _parse_or(tokens, pos)
            node = _GetItem(node, key)
            if pos < len(tokens) and tokens[pos][0] == "RBRACKET":
                pos += 1
            else:
                raise TemplateSyntaxError("Expected ']'")
        elif tt == "LPAREN":
            pos, args = _parse_args(tokens, pos)
            node = _Call(node, args)
        else:
            break

    return node, pos


def _parse_args(tokens, pos):
    """Parse (arg, arg, ...) starting at LPAREN."""
    if pos >= len(tokens) or tokens[pos][0] != "LPAREN":
        raise TemplateSyntaxError("Expected '('")
    pos += 1
    args: List[_Expr] = []
    if pos < len(tokens) and tokens[pos][0] != "RPAREN":
        arg, pos = _parse_or(tokens, pos)
        args.append(arg)
        while pos < len(tokens) and tokens[pos][0] == "COMMA":
            pos += 1
            arg, pos = _parse_or(tokens, pos)
            args.append(arg)
    if pos < len(tokens) and tokens[pos][0] == "RPAREN":
        pos += 1
    else:
        raise TemplateSyntaxError("Expected ')'")
    return pos, args


# ═══════════════════════════════════════════════════════════════════════════════
# Template parser — builds AST from tokenized segments
# ═══════════════════════════════════════════════════════════════════════════════


class _Parser:
    def __init__(self, segments: List[Dict[str, Any]]):
        self._segs = segments
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._segs):
            return self._segs[self._pos]
        return None

    def _advance(self):
        seg = self._segs[self._pos]
        self._pos += 1
        return seg

    def _expect(self, block_cmd: str):
        seg = self._peek()
        if seg is None or seg["type"] != "block" or seg["content"] != block_cmd:
            raise TemplateSyntaxError(f"Expected {block_cmd!r}, got {seg}")
        return self._advance()

    def parse(self) -> List[_Node]:
        nodes: List[_Node] = []
        while self._pos < len(self._segs):
            seg = self._peek()
            if seg is None:
                break
            if seg["type"] == "text":
                self._advance()
                nodes.append(_Text(seg["content"]))
            elif seg["type"] == "var":
                self._advance()
                tokens = _tokenize_expr(seg["content"])
                if not tokens:
                    nodes.append(_Text(""))
                else:
                    expr, _ = _parse_expr(tokens)
                    nodes.append(_Print(expr))
            elif seg["type"] == "block":
                cmd = seg["content"]
                words = cmd.split(None, 1)
                keyword = words[0] if words else ""

                if keyword == "if":
                    nodes.append(self._parse_if())
                elif keyword == "for":
                    nodes.append(self._parse_for())
                elif keyword == "block":
                    nodes.append(self._parse_block())
                elif keyword == "endblock":
                    break  # handled by _parse_block caller
                elif keyword == "extends":
                    nodes.append(self._parse_extends())
                elif keyword == "include":
                    nodes.append(self._parse_include())
                elif keyword == "import":
                    nodes.append(self._parse_import())
                elif keyword == "macro":
                    nodes.append(self._parse_macro())
                elif keyword == "endmacro":
                    break
                elif keyword == "with":
                    nodes.append(self._parse_with())
                elif keyword == "endwith":
                    break
                elif keyword == "autoescape":
                    nodes.append(self._parse_autoescape())
                elif keyword == "endautoescape":
                    break
                elif keyword in ("elif", "else", "endif", "endfor"):
                    break  # caller handles these
                else:
                    raise TemplateSyntaxError(f"Unknown block tag: {keyword!r}")
            else:
                self._advance()

        return nodes

    def _parse_extends(self):
        seg = self._advance()
        parts = seg["content"].split(None, 1)
        if len(parts) < 2:
            raise TemplateSyntaxError("extends requires a template name")
        name_token = _tokenize_expr(parts[1])
        if not name_token or name_token[0][0] != "STR":
            raise TemplateSyntaxError("extends requires a string literal template name")
        return _Extends(name_token[0][1][1:-1])

    def _parse_include(self):
        seg = self._advance()
        parts = seg["content"].split(None, 1)
        if len(parts) < 2:
            raise TemplateSyntaxError("include requires a template name")
        name_token = _tokenize_expr(parts[1])
        if not name_token or name_token[0][0] != "STR":
            raise TemplateSyntaxError("include requires a string literal template name")
        return _Include(name_token[0][1][1:-1])

    def _parse_import(self):
        seg = self._advance()
        m = re.match(r'^import\s+(.*?)\s+as\s+(\w+)\s*$', seg["content"])
        if not m:
            raise TemplateSyntaxError("import syntax: import 'name' as ns")
        src = m.group(1).strip()
        name_token = _tokenize_expr(src)
        if not name_token or name_token[0][0] != "STR":
            raise TemplateSyntaxError("import requires a string literal template name")
        return _Import(name_token[0][1][1:-1], m.group(2))

    def _parse_block(self):
        seg = self._advance()
        parts = seg["content"].split(None, 1)
        if len(parts) < 2:
            raise TemplateSyntaxError("block requires a name")
        block_name = parts[1].strip()
        body = self.parse()
        # consume endblock
        end = self._peek()
        if end and end["type"] == "block" and end["content"] == "endblock":
            self._advance()
        return _Block(block_name, body)

    def _parse_if(self):
        self._advance()  # consume 'if'
        seg = self._segs[self._pos - 1]
        # expression is everything after 'if '
        cond_str = re.sub(r'^if\s+', '', seg["content"])
        cond_tokens = _tokenize_expr(cond_str)
        cond_expr, _ = _parse_expr(cond_tokens)

        body = self.parse()

        branches = [(cond_expr, body)]

        while True:
            seg2 = self._peek()
            if seg2 and seg2["type"] == "block":
                kw = seg2["content"].split(None, 1)[0] if seg2["content"] else ""
                if kw == "elif":
                    self._advance()
                    elif_cond_str = re.sub(r'^elif\s+', '', seg2["content"])
                    elif_tokens = _tokenize_expr(elif_cond_str)
                    elif_expr, _ = _parse_expr(elif_tokens)
                    elif_body = self.parse()
                    branches.append((elif_expr, elif_body))
                    continue
                elif kw == "else":
                    self._advance()
                    else_body = self.parse()
                    # consume endif
                    end = self._peek()
                    if end and end["type"] == "block" and end["content"].startswith("endif"):
                        self._advance()
                    return _If(branches, else_body)
                elif kw == "endif":
                    self._advance()
                    return _If(branches)
            break

        # expect endif
        end = self._peek()
        if end and end["type"] == "block" and end["content"].startswith("endif"):
            self._advance()
        return _If(branches)

    def _parse_for(self):
        seg = self._advance()
        m = re.match(r'^for\s+(\w+)\s+in\s+(.+)$', seg["content"], re.DOTALL)
        if not m:
            raise TemplateSyntaxError("for syntax: for var in expr")
        loop_var = m.group(1)
        iter_tokens = _tokenize_expr(m.group(2))
        iter_expr, _ = _parse_expr(iter_tokens)

        body = self.parse()

        else_body = None
        peek = self._peek()
        if peek and peek["type"] == "block":
            kw = peek["content"].split(None, 1)[0] if peek["content"] else ""
            if kw == "else":
                self._advance()
                else_body = self.parse()
                end = self._peek()
                if end and end["type"] == "block" and end["content"].startswith("endfor"):
                    self._advance()
                return _For(loop_var, iter_expr, body, else_body)
            elif kw == "endfor":
                self._advance()
                return _For(loop_var, iter_expr, body)

        end = self._peek()
        if end and end["type"] == "block" and end["content"].startswith("endfor"):
            self._advance()

        return _For(loop_var, iter_expr, body, else_body)

    def _parse_macro(self):
        seg = self._advance()
        m = re.match(r'^macro\s+(\w+)\s*\((.*?)\)\s*$', seg["content"], re.DOTALL)
        if not m:
            raise TemplateSyntaxError("macro syntax: macro name(params)")
        macro_name = m.group(1)
        params_str = m.group(2).strip()
        params = [p.strip() for p in params_str.split(",") if p.strip()] if params_str else []
        body = self.parse()
        end = self._peek()
        if end and end["type"] == "block" and end["content"] == "endmacro":
            self._advance()
        return _MacroDef(macro_name, params, body)

    def _parse_with(self):
        seg = self._advance()
        m = re.match(r'^with\s+(.+)$', seg["content"], re.DOTALL)
        if not m:
            raise TemplateSyntaxError("with syntax: with var = expr")
        # parse assignments
        assign_str = m.group(1)
        # simple case: single assignment
        eq_match = re.match(r'^(\w+)\s*=\s*(.+)$', assign_str, re.DOTALL)
        if not eq_match:
            raise TemplateSyntaxError("with requires an assignment: var = expr")
        var_name = eq_match.group(1)
        expr_tokens = _tokenize_expr(eq_match.group(2))
        expr, _ = _parse_expr(expr_tokens)
        body = self.parse()
        end = self._peek()
        if end and end["type"] == "block" and end["content"] == "endwith":
            self._advance()
        return _With([(var_name, expr)], body)

    def _parse_autoescape(self):
        seg = self._advance()
        parts = seg["content"].split(None, 1)
        if len(parts) < 2:
            raise TemplateSyntaxError("autoescape requires true or false")
        val = parts[1].strip().lower()
        if val not in ("true", "false"):
            raise TemplateSyntaxError("autoescape requires true or false")
        enabled = val == "true"
        body = self.parse()
        end = self._peek()
        if end and end["type"] == "block" and end["content"] == "endautoescape":
            self._advance()
        return _Autoescape(enabled, body)


def _compile(source: str) -> List[_Node]:
    """Compile a template source string to an AST."""
    segments = _tokenize(source)
    parser = _Parser(segments)
    return parser.parse()


# ═══════════════════════════════════════════════════════════════════════════════
# Built-in filters
# ═══════════════════════════════════════════════════════════════════════════════


def _filter_upper(val: Any) -> str:
    return str(val).upper()


def _filter_lower(val: Any) -> str:
    return str(val).lower()


def _filter_title(val: Any) -> str:
    return str(val).title()


def _filter_length(val: Any) -> int:
    try:
        return len(val)
    except TypeError:
        return 0


def _filter_join(val: Any, sep: str = "") -> str:
    if isinstance(val, str):
        return val
    try:
        return sep.join(str(v) for v in val)
    except TypeError:
        return str(val)


def _filter_default(val: Any, default: Any = "", _is_missing=False) -> Any:
    # _is_missing flag used internally
    if _is_missing or val is _UNDEFINED:
        return default
    if val is None or (isinstance(val, str) and val == ""):
        return default
    # Also check falsiness for undefined-like values
    return val


def _filter_escape(val: Any) -> str:
    return html.escape(str(val))


def _filter_safe(val: Any) -> _SafeString:
    return _SafeString(str(val))


class _SafeString(str):
    """Marker for strings that should not be auto-escaped."""

    pass


BUILTIN_FILTERS: Dict[str, Callable] = {
    "upper": _filter_upper,
    "lower": _filter_lower,
    "title": _filter_title,
    "length": _filter_length,
    "join": _filter_join,
    "default": _filter_default,
    "escape": _filter_escape,
    "safe": _filter_safe,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Built-in tests
# ═══════════════════════════════════════════════════════════════════════════════


def _test_defined(val: Any) -> bool:
    return val is not _UNDEFINED


def _test_undefined(val: Any) -> bool:
    return val is _UNDEFINED


def _test_odd(val: Any) -> bool:
    try:
        return int(val) % 2 != 0
    except (ValueError, TypeError):
        return False


def _test_even(val: Any) -> bool:
    try:
        return int(val) % 2 == 0
    except (ValueError, TypeError):
        return False


def _test_iterable(val: Any) -> bool:
    try:
        iter(val)
        return True
    except TypeError:
        return False


BUILTIN_TESTS: Dict[str, Callable] = {
    "defined": _test_defined,
    "undefined": _test_undefined,
    "odd": _test_odd,
    "even": _test_even,
    "iterable": _test_iterable,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Renderer
# ═══════════════════════════════════════════════════════════════════════════════


class _RenderContext:
    """Mutable rendering state."""

    def __init__(self, variables: Dict[str, Any], env: Environment):
        self.vars = dict(variables)
        self.env = env
        self.autoescape = env.autoescape
        self._blocks: Dict[str, List[_Node]] = {}  # block overrides from child templates

    def push(self, extra: Dict[str, Any]):
        """Create a child context with extra/layered variables."""
        child = _RenderContext({}, self.env)
        child.vars = dict(self.vars)
        child.vars.update(extra)
        child.autoescape = self.autoescape
        child._blocks = self._blocks  # share block overrides
        return child

    def resolve(self, name: str) -> Any:
        """Look up a variable: local vars → env globals → undefined."""
        if name in self.vars:
            return self.vars[name]
        if self.env.globals and name in self.env.globals:
            return self.env.globals[name]
        return _UNDEFINED

    def set_var(self, name: str, value: Any):
        self.vars[name] = value


def _eval_expr(expr: _Expr, ctx: _RenderContext) -> Any:
    """Evaluate an expression node to a Python value."""
    if isinstance(expr, _Literal):
        return expr.value
    elif isinstance(expr, _Name):
        return ctx.resolve(expr.name)
    elif isinstance(expr, _GetAttr):
        obj = _eval_expr(expr.obj, ctx)
        if obj is _UNDEFINED:
            return _UNDEFINED
        # Dotted access: attribute → key → index
        if isinstance(obj, dict):
            return obj.get(expr.attr, _UNDEFINED)
        elif isinstance(obj, (list, tuple)):
            try:
                idx = int(expr.attr)
                return obj[idx]
            except (ValueError, IndexError):
                return _UNDEFINED
        else:
            if hasattr(obj, expr.attr):
                return getattr(obj, expr.attr)
            elif hasattr(obj, "__getitem__"):
                try:
                    return obj[expr.attr]
                except (KeyError, IndexError, TypeError):
                    return _UNDEFINED
            return _UNDEFINED
    elif isinstance(expr, _GetItem):
        obj = _eval_expr(expr.obj, ctx)
        key = _eval_expr(expr.key, ctx)
        if obj is _UNDEFINED:
            return _UNDEFINED
        if isinstance(obj, dict):
            return obj.get(key, _UNDEFINED)
        elif isinstance(obj, (list, tuple, str)):
            try:
                if isinstance(key, int):
                    return obj[key]
                return _UNDEFINED
            except (IndexError, TypeError):
                return _UNDEFINED
        elif hasattr(obj, "__getitem__"):
            try:
                return obj[key]
            except (KeyError, IndexError, TypeError):
                return _UNDEFINED
        return _UNDEFINED
    elif isinstance(expr, _Filter):
        val = _eval_expr(expr.expr, ctx)
        filter_func = ctx.env.filters.get(expr.name)
        if filter_func is None:
            raise TemplateSyntaxError(f"Unknown filter: {expr.name!r}")

        # special: 'default' filter only applies if value is falsy/undefined
        if expr.name == "default":
            is_missing = val is _UNDEFINED
            arg_vals = [_eval_expr(a, ctx) for a in expr.args]
            # We need to check if the value is "empty"
            return _apply_default(val, filter_func, is_missing, arg_vals)

        args = [_eval_expr(a, ctx) for a in expr.args]
        return filter_func(val, *args)
    elif isinstance(expr, _Test):
        val = _eval_expr(expr.expr, ctx)
        test_func = ctx.env.tests.get(expr.name)
        if test_func is None:
            raise TemplateSyntaxError(f"Unknown test: {expr.name!r}")
        result = test_func(val)
        return not result if expr.negated else result
    elif isinstance(expr, _BinOp):
        return _eval_binop(expr, ctx)
    elif isinstance(expr, _UnaryOp):
        operand = _eval_expr(expr.operand, ctx)
        if expr.op == "not":
            return not _is_truthy(operand)
        raise TemplateSyntaxError(f"Unknown unary operator: {expr.op!r}")
    elif isinstance(expr, _Call):
        func = _eval_expr(expr.func, ctx)
        args = [_eval_expr(a, ctx) for a in expr.args]
        if callable(func):
            return func(*args)
        raise TemplateSyntaxError(f"Object is not callable")
    else:
        raise TemplateSyntaxError(f"Unknown expression type: {type(expr)}")


def _apply_default(val, filter_func, is_missing, args):
    """Apply the default filter with proper semantics."""
    if is_missing or val is _UNDEFINED:
        if args:
            return args[0]
        return ""
    # val is defined but might be falsy - original Jinja2 'default' only
    # replaces undefined, but the user might expect it to replace empty strings too.
    # Let's follow the documented example: {{ missing|default("guest") }}
    # where 'missing' is undefined renders "guest".
    # For the PRD, we treat undefined → default value, defined values pass through.
    return val


def _is_truthy(val: Any) -> bool:
    """Determine truthiness. Undefined is falsy."""
    if val is _UNDEFINED:
        return False
    return bool(val)


def _eval_binop(expr: _BinOp, ctx: _RenderContext) -> Any:
    """Evaluate a binary operation."""
    if expr.op in ("and", "or"):
        # short-circuit
        left = _is_truthy(_eval_expr(expr.left, ctx))
        if expr.op == "and":
            if not left:
                return False
            return _is_truthy(_eval_expr(expr.right, ctx))
        else:  # or
            if left:
                return True
            return _is_truthy(_eval_expr(expr.right, ctx))

    left = _eval_expr(expr.left, ctx)
    right = _eval_expr(expr.right, ctx)
    op = expr.op

    if op == "==":
        return _cmp_eq(left, right)
    elif op == "!=":
        return not _cmp_eq(left, right)
    elif op == "in":
        return _cmp_in(left, right)
    elif op == "not in":
        return not _cmp_in(left, right)

    # numeric comparisons
    try:
        if op == "<":
            return left < right
        elif op == ">":
            return left > right
        elif op == "<=":
            return left <= right
        elif op == ">=":
            return left >= right
    except TypeError:
        return False

    raise TemplateSyntaxError(f"Unknown operator: {op!r}")


def _cmp_eq(a, b):
    if a is _UNDEFINED and b is _UNDEFINED:
        return True
    if a is _UNDEFINED or b is _UNDEFINED:
        return False
    return a == b


def _cmp_in(item, container):
    if item is _UNDEFINED:
        return False
    try:
        return item in container
    except TypeError:
        return False


def _render_nodes(
    nodes: List[_Node], ctx: _RenderContext, macros: Dict[str, _MacroDef]
) -> str:
    """Render a list of AST nodes to a string."""
    result: List[str] = []
    for node in nodes:
        _render_node(node, ctx, result, macros)
    return "".join(result)


def _render_node(
    node: _Node, ctx: _RenderContext, output: List[str], macros: Dict[str, _MacroDef]
):
    """Render a single AST node."""
    if isinstance(node, _Text):
        output.append(node.text)
    elif isinstance(node, _Print):
        val = _eval_expr(node.expr, ctx)
        text = _stringify(val)
        if ctx.autoescape and not isinstance(val, _SafeString):
            text = html.escape(text)
        output.append(text)
    elif isinstance(node, _If):
        for test_expr, body in node.branches:
            if _is_truthy(_eval_expr(test_expr, ctx)):
                output.append(_render_nodes(body, ctx, macros))
                return
        if node.else_body:
            output.append(_render_nodes(node.else_body, ctx, macros))
    elif isinstance(node, _For):
        items = _eval_expr(node.iter_expr, ctx)
        if items is _UNDEFINED or not _is_iterable(items):
            if node.else_body:
                output.append(_render_nodes(node.else_body, ctx, macros))
            return
        items_list = list(items) if not isinstance(items, list) else items
        if not items_list:
            if node.else_body:
                output.append(_render_nodes(node.else_body, ctx, macros))
            return
        for item in items_list:
            inner = ctx.push({node.loop_var: item})
            output.append(_render_nodes(node.body, inner, macros))
    elif isinstance(node, _Block):
        block_name = node.name
        if block_name in ctx._blocks:
            # Child override
            output.append(_render_nodes(ctx._blocks[block_name], ctx, macros))
        else:
            output.append(_render_nodes(node.body, ctx, macros))
    elif isinstance(node, _Extends):
        raise TemplateSyntaxError("extends must be handled at load time")
    elif isinstance(node, _Include):
        template_name = node.template_name
        template = ctx.env.get_template(template_name)
        output.append(template._render(ctx.vars, ctx))
    elif isinstance(node, _Import):
        template = ctx.env.get_template(node.template_name)
        # Collect macros from the imported template
        ns_macros: Dict[str, _MacroDef] = {}
        for n in template._ast:
            if isinstance(n, _MacroDef):
                ns_macros[n.name] = n
        ctx.set_var(node.namespace, _MacroNamespace(ns_macros, ctx))
    elif isinstance(node, _MacroDef):
        macros[node.name] = node
    elif isinstance(node, _With):
        assignments = {}
        for var_name, var_expr in node.assignments:
            assignments[var_name] = _eval_expr(var_expr, ctx)
        inner = ctx.push(assignments)
        output.append(_render_nodes(node.body, inner, macros))
    elif isinstance(node, _Autoescape):
        orig_ae = ctx.autoescape
        ctx.autoescape = node.enabled
        output.append(_render_nodes(node.body, ctx, macros))
        ctx.autoescape = orig_ae


class _MacroNamespace:
    """A namespace object containing macros from an imported template."""

    def __init__(self, macros: Dict[str, _MacroDef], ctx: _RenderContext):
        self._macros = macros
        self._ctx = ctx

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._macros:
            macro = self._macros[name]
            return _BoundMacro(macro, self._ctx)
        raise AttributeError(f"Macro {name!r} not found")

    def __getitem__(self, name: str):
        return getattr(self, name)


class _BoundMacro:
    """A callable macro bound to a render context."""

    def __init__(self, macro: _MacroDef, ctx: _RenderContext):
        self._macro = macro
        self._outer_ctx = ctx

    def __call__(self, *args, **kwargs):
        # Map positional arguments to parameter names
        local_vars: Dict[str, Any] = {}
        for i, param in enumerate(self._macro.params):
            if i < len(args):
                local_vars[param] = args[i]
            elif param in kwargs:
                local_vars[param] = kwargs[param]
            else:
                local_vars[param] = _UNDEFINED
        # Macros use environment registries and globals (not caller vars except via args)
        macro_ctx = _RenderContext({}, self._outer_ctx.env)
        macro_ctx.vars = dict(self._outer_ctx.env.globals or {})
        macro_ctx.vars.update(local_vars)
        macro_ctx._blocks = self._outer_ctx._blocks
        all_macros: Dict[str, _MacroDef] = {}
        return _render_nodes(self._macro.body, macro_ctx, all_macros)

    def __str__(self):
        return ""


def _stringify(val: Any) -> str:
    """Convert a value to a string for output."""
    if val is _UNDEFINED:
        return ""
    if val is None:
        return ""
    if isinstance(val, bool):
        return str(val).lower()
    return str(val)


def _is_iterable(val: Any) -> bool:
    """Check if a value is iterable (but not a string-like)."""
    if isinstance(val, str):
        return False
    if val is _UNDEFINED:
        return False
    try:
        iter(val)
        return True
    except TypeError:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Environment
# ═══════════════════════════════════════════════════════════════════════════════


class Environment:
    """The canonical fact source for template rendering.

    Owns the loader, compiled-template cache, filter & test registries,
    globals, and autoescape policy.
    """

    def __init__(
        self,
        loader: Optional[Dict[str, str]] = None,
        *,
        autoescape: bool = False,
        trim_blocks: bool = False,
        lstrip_blocks: bool = False,
        globals: Optional[Dict[str, Any]] = None,
    ):
        self._loader: Optional[Dict[str, str]] = loader
        self.autoescape = autoescape
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks
        self.globals: Dict[str, Any] = dict(globals) if globals else {}
        self.filters: Dict[str, Callable] = dict(BUILTIN_FILTERS)
        self.tests: Dict[str, Callable] = dict(BUILTIN_TESTS)
        self._cache: Dict[str, Template] = {}

    # ── template loading ──────────────────────────────────────────────────

    def get_template(self, name: str) -> Template:
        """Load and compile a named template through the environment loader.

        Raises TemplateNotFound when no source exists for the name.
        """
        if name in self._cache:
            return self._cache[name]

        source = self._load_source(name)
        template = self._compile_named(name, source)
        self._cache[name] = template
        return template

    def from_string(self, source: str, name: Optional[str] = None) -> Template:
        """Compile a source string as a template bound to this environment."""
        ast = _compile(source)
        has_extends = any(isinstance(n, _Extends) for n in ast)
        if has_extends:
            # resolve extends
            ext_node = next(n for n in ast if isinstance(n, _Extends))
            parent = self.get_template(ext_node.parent_name)
            # collect child blocks and macros
            child_blocks = {}
            child_macros = {}
            for n in ast:
                if isinstance(n, _Block):
                    child_blocks[n.name] = n.body
                elif isinstance(n, _MacroDef):
                    child_macros[n.name] = n
            return _InheritedTemplate(parent, child_blocks, child_macros, self, name)
        return _BoundTemplate(ast, self, name)

    def set_template(self, name: str, source: str):
        """Store or replace a template source and invalidate cache entry."""
        if self._loader is None:
            self._loader = {}
        self._loader[name] = source
        self._cache.pop(name, None)

    def invalidate(self, name: Optional[str] = None):
        """Invalidate cache: one template by name, or entire cache."""
        if name is None:
            self._cache.clear()
        else:
            self._cache.pop(name, None)

    def _load_source(self, name: str) -> str:
        if self._loader is None:
            raise TemplateNotFound(f"Template {name!r} not found (no loader)")
        if name not in self._loader:
            raise TemplateNotFound(f"Template {name!r} not found")
        return self._loader[name]

    def _compile_named(self, name: str, source: str) -> Template:
        ast = _compile(source)
        has_extends = any(isinstance(n, _Extends) for n in ast)
        if has_extends:
            ext_node = next(n for n in ast if isinstance(n, _Extends))
            parent = self.get_template(ext_node.parent_name)
            child_blocks = {}
            child_macros = {}
            for n in ast:
                if isinstance(n, _Block):
                    child_blocks[n.name] = n.body
                elif isinstance(n, _MacroDef):
                    child_macros[n.name] = n
            return _InheritedTemplate(parent, child_blocks, child_macros, self, name)
        return _BoundTemplate(ast, self, name)


# ═══════════════════════════════════════════════════════════════════════════════
# Template
# ═══════════════════════════════════════════════════════════════════════════════


class Template:
    """A compiled template."""

    def __init__(self, source: str):
        """Parse a standalone template string.

        Raises TemplateSyntaxError on syntax errors.
        """
        ast = _compile(source)
        # standalone environment
        env = Environment({})
        self._template = _BoundTemplate(ast, env, None)

    def render(self, **kwargs) -> str:
        """Render the template with keyword arguments as variables.

        Returns the rendered string.
        """
        return self._template.render(**kwargs)

    def _render(self, variables: Dict[str, Any], parent_ctx: Optional[_RenderContext] = None) -> str:
        return self._template._render(variables, parent_ctx)


class _BoundTemplate(Template):
    """Internal: a template bound to a specific Environment."""

    def __init__(self, ast: List[_Node], env: Environment, name: Optional[str]):
        # bypass Template.__init__
        self._ast = ast
        self._env = env
        self._name = name

    def render(self, **kwargs) -> str:
        return self._render(kwargs, None)

    def _render(self, variables: Dict[str, Any], parent_ctx: Optional[_RenderContext] = None) -> str:
        ctx = _RenderContext(variables, self._env)
        macros: Dict[str, _MacroDef] = {}

        # If we have inherited blocks, inject them
        if parent_ctx is not None:
            ctx._blocks = parent_ctx._blocks

        return _render_nodes(self._ast, ctx, macros)


class _InheritedTemplate(Template):
    """Internal: a child template using extends."""

    def __init__(
        self,
        parent: Template,
        child_blocks: Dict[str, List[_Node]],
        child_macros: Dict[str, _MacroDef],
        env: Environment,
        name: Optional[str],
    ):
        self._parent = parent
        self._child_blocks = child_blocks
        self._child_macros = child_macros
        self._env = env
        self._name = name

    def render(self, **kwargs) -> str:
        return self._render(kwargs, None)

    def _render(self, variables: Dict[str, Any], parent_ctx: Optional[_RenderContext] = None) -> str:
        ctx = _RenderContext(variables, self._env)
        # Inject child blocks into context
        ctx._blocks = dict(self._child_blocks)

        # Render the parent with our block overrides
        macros: Dict[str, _MacroDef] = {}
        if isinstance(self._parent, _BoundTemplate):
            return _render_nodes(self._parent._ast, ctx, macros)
        elif isinstance(self._parent, _InheritedTemplate):
            # Multi-level inheritance: merge blocks
            merged_blocks = dict(self._parent._child_blocks)
            merged_blocks.update(self._child_blocks)
            ctx._blocks = merged_blocks
            return self._parent._render(variables, ctx)
        else:
            return self._parent._render(variables, ctx)
