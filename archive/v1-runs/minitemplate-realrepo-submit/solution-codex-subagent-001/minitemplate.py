"""A small text template engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class TemplateSyntaxError(Exception):
    """Raised when a template cannot be parsed."""


class _Undefined:
    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return ""


UNDEFINED = _Undefined()


@dataclass(frozen=True)
class _Text:
    value: str

    def render(self, ctx: "_Context") -> str:
        return self.value


@dataclass(frozen=True)
class _Var:
    expr: str

    def render(self, ctx: "_Context") -> str:
        value = _eval_expr(self.expr, ctx)
        if value is UNDEFINED or value is None:
            return ""
        return str(value)


@dataclass(frozen=True)
class _If:
    branches: tuple[tuple[str, tuple[Any, ...]], ...]
    else_body: tuple[Any, ...] | None

    def render(self, ctx: "_Context") -> str:
        for expr, body in self.branches:
            if bool(_eval_expr(expr, ctx)):
                return _render_nodes(body, ctx)
        if self.else_body is not None:
            return _render_nodes(self.else_body, ctx)
        return ""


@dataclass(frozen=True)
class _For:
    name: str
    expr: str
    body: tuple[Any, ...]
    else_body: tuple[Any, ...] | None

    def render(self, ctx: "_Context") -> str:
        seq = _eval_expr(self.expr, ctx)
        if seq is UNDEFINED or seq is None:
            items = []
        else:
            try:
                items = list(seq)
            except TypeError:
                items = []

        if not items:
            return _render_nodes(self.else_body or (), ctx)

        parts: list[str] = []
        for item in items:
            ctx.push({self.name: item})
            try:
                parts.append(_render_nodes(self.body, ctx))
            finally:
                ctx.pop()
        return "".join(parts)


@dataclass(frozen=True)
class _Block:
    name: str
    body: tuple[Any, ...]

    def render(self, ctx: "_Context") -> str:
        return _render_nodes(self.body, ctx)


@dataclass(frozen=True)
class _With:
    name: str
    expr: str
    body: tuple[Any, ...]

    def render(self, ctx: "_Context") -> str:
        ctx.push({self.name: _eval_expr(self.expr, ctx)})
        try:
            return _render_nodes(self.body, ctx)
        finally:
            ctx.pop()


class _Context:
    def __init__(self, values: dict[str, Any]) -> None:
        self._scopes: list[dict[str, Any]] = [dict(values)]

    def push(self, values: dict[str, Any]) -> None:
        self._scopes.append(values)

    def pop(self) -> None:
        self._scopes.pop()

    def get(self, name: str) -> Any:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return UNDEFINED


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    pos = 0
    while pos < len(source):
        var_pos = source.find("{{", pos)
        tag_pos = source.find("{%", pos)
        starts = [p for p in (var_pos, tag_pos) if p != -1]
        if not starts:
            tokens.append(_Token("text", source[pos:]))
            break

        start = min(starts)
        if start > pos:
            tokens.append(_Token("text", source[pos:start]))

        if source.startswith("{{", start):
            end = source.find("}}", start + 2)
            if end == -1:
                raise TemplateSyntaxError("unclosed variable tag")
            tokens.append(_Token("var", source[start + 2 : end].strip()))
            pos = end + 2
        else:
            end = source.find("%}", start + 2)
            if end == -1:
                raise TemplateSyntaxError("unclosed block tag")
            tokens.append(_Token("tag", source[start + 2 : end].strip()))
            pos = end + 2
    return tokens


class _Parser:
    def __init__(self, source: str) -> None:
        self.tokens = _tokenize(source)
        self.pos = 0

    def parse(self) -> tuple[Any, ...]:
        nodes, end = self._parse_until(set())
        if end is not None:
            raise TemplateSyntaxError("unexpected closing tag")
        return nodes

    def _parse_until(self, stop_words: set[str]) -> tuple[tuple[Any, ...], str | None]:
        nodes: list[Any] = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token.kind == "text":
                nodes.append(_Text(token.value))
                self.pos += 1
            elif token.kind == "var":
                if not token.value:
                    raise TemplateSyntaxError("empty variable expression")
                nodes.append(_Var(token.value))
                self.pos += 1
            else:
                word = token.value.split(None, 1)[0] if token.value else ""
                if word in stop_words:
                    return tuple(nodes), token.value
                nodes.append(self._parse_tag(token.value))
        return tuple(nodes), None

    def _parse_tag(self, tag: str) -> Any:
        if not tag:
            raise TemplateSyntaxError("empty tag")
        if tag.startswith("if "):
            return self._parse_if(tag[3:].strip())
        if tag.startswith("for "):
            return self._parse_for(tag[4:].strip())
        if tag.startswith("block "):
            return self._parse_block(tag[6:].strip())
        if tag.startswith("with "):
            return self._parse_with(tag[5:].strip())
        raise TemplateSyntaxError("unknown tag")

    def _parse_if(self, expr: str) -> _If:
        if not expr:
            raise TemplateSyntaxError("if requires condition")
        self.pos += 1
        branches: list[tuple[str, tuple[Any, ...]]] = []
        body, end = self._parse_until({"elif", "else", "endif"})
        branches.append((expr, body))

        while end and end.startswith("elif "):
            expr = end[5:].strip()
            if not expr:
                raise TemplateSyntaxError("elif requires condition")
            self.pos += 1
            body, end = self._parse_until({"elif", "else", "endif"})
            branches.append((expr, body))

        else_body = None
        if end == "else":
            self.pos += 1
            else_body, end = self._parse_until({"endif"})
        elif end and end.startswith("else "):
            raise TemplateSyntaxError("else takes no expression")

        if end != "endif":
            raise TemplateSyntaxError("if missing endif")
        self.pos += 1
        return _If(tuple(branches), else_body)

    def _parse_for(self, expr: str) -> _For:
        match = re.fullmatch(r"([A-Za-z_]\w*)\s+in\s+(.+)", expr)
        if not match:
            raise TemplateSyntaxError("malformed for tag")
        name, seq_expr = match.group(1), match.group(2).strip()
        self.pos += 1
        body, end = self._parse_until({"else", "endfor"})

        else_body = None
        if end == "else":
            self.pos += 1
            else_body, end = self._parse_until({"endfor"})
        elif end and end.startswith("else "):
            raise TemplateSyntaxError("else takes no expression")

        if end != "endfor":
            raise TemplateSyntaxError("for missing endfor")
        self.pos += 1
        return _For(name, seq_expr, body, else_body)

    def _parse_block(self, name: str) -> _Block:
        if not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise TemplateSyntaxError("invalid block name")
        self.pos += 1
        body, end = self._parse_until({"endblock"})
        if end != "endblock":
            raise TemplateSyntaxError("block missing endblock")
        self.pos += 1
        return _Block(name, body)

    def _parse_with(self, expr: str) -> _With:
        match = re.fullmatch(r"([A-Za-z_]\w*)\s*=\s*(.+)", expr)
        if not match:
            raise TemplateSyntaxError("malformed with tag")
        name, value_expr = match.group(1), match.group(2).strip()
        self.pos += 1
        body, end = self._parse_until({"endwith"})
        if end != "endwith":
            raise TemplateSyntaxError("with missing endwith")
        self.pos += 1
        return _With(name, value_expr, body)


_COMPARE_RE = re.compile(r"^(.+?)\s+(not\s+in|in|==|!=|<=|>=|<|>)\s+(.+)$")
_STRING_RE = re.compile(r"""^(['"])(.*)\1$""", re.S)
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)$")


def _eval_expr(expr: str, ctx: _Context) -> Any:
    expr = expr.strip()
    match = _COMPARE_RE.match(expr)
    if match:
        left = _eval_atom(match.group(1).strip(), ctx)
        op = match.group(2)
        right = _eval_atom(match.group(3).strip(), ctx)
        try:
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right
            if op == "in":
                return left in right
            if op == "not in":
                return left not in right
        except Exception:
            return False
    return _eval_atom(expr, ctx)


def _eval_atom(expr: str, ctx: _Context) -> Any:
    expr = expr.strip()
    if not expr:
        return UNDEFINED
    if expr in {"True", "true"}:
        return True
    if expr in {"False", "false"}:
        return False
    if expr in {"None", "none", "null"}:
        return None

    string_match = _STRING_RE.match(expr)
    if string_match:
        return string_match.group(2)
    if _INT_RE.match(expr):
        return int(expr)
    if _FLOAT_RE.match(expr):
        return float(expr)

    parts = expr.split(".")
    value = ctx.get(parts[0])
    for part in parts[1:]:
        value = _resolve_part(value, part)
        if value is UNDEFINED:
            break
    return value


def _resolve_part(value: Any, part: str) -> Any:
    if value is UNDEFINED or value is None:
        return UNDEFINED

    try:
        attr = getattr(value, part)
    except Exception:
        attr = UNDEFINED
    if attr is not UNDEFINED:
        return attr

    try:
        return value[part]
    except Exception:
        pass

    if _INT_RE.match(part):
        try:
            return value[int(part)]
        except Exception:
            pass
    return UNDEFINED


def _render_nodes(nodes: tuple[Any, ...], ctx: _Context) -> str:
    return "".join(node.render(ctx) for node in nodes)


class Template:
    def __init__(self, source: str) -> None:
        self.source = source
        self._nodes = _Parser(source).parse()

    def render(self, **kwargs: Any) -> str:
        return _render_nodes(self._nodes, _Context(kwargs))


class Environment:
    def from_string(self, source: str) -> Template:
        return Template(source)
