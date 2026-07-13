"""A compact Jinja-like template engine used by the benchmark reference."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Iterable


class TemplateSyntaxError(Exception):
    """Raised when a template cannot be parsed."""


class TemplateNotFound(Exception):
    """Raised when an environment cannot load a named template."""


class Undefined:
    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return ""


UNDEFINED = Undefined()


class Markup(str):
    """String subclass that bypasses autoescape."""


class MacroNamespace:
    def __init__(self, macros: dict[str, "Macro"]) -> None:
        self._macros = macros

    def __getattr__(self, name: str) -> "Macro":
        try:
            return self._macros[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, name: str) -> "Macro":
        return self._macros[name]


class _Context:
    def __init__(self, values: dict[str, Any], env: "Environment", autoescape: bool | None = None) -> None:
        self.env = env
        self.autoescape = env.autoescape if autoescape is None else autoescape
        self._scopes: list[dict[str, Any]] = [dict(env.globals), dict(values)]

    def push(self, values: dict[str, Any]) -> None:
        self._scopes.append(values)

    def pop(self) -> None:
        self._scopes.pop()

    def overlay(self, values: dict[str, Any]) -> "_Context":
        child = _Context({}, self.env, self.autoescape)
        child._scopes = [*self._scopes, values]
        return child

    def get(self, name: str) -> Any:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return UNDEFINED

    def set(self, name: str, value: Any) -> None:
        self._scopes[-1][name] = value


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    pos = 0
    trim_next_left = False
    pattern = re.compile(r"({[{%]-?)(.*?)(-?[}%]})", re.S)
    for match in pattern.finditer(source):
        text = source[pos : match.start()]
        if trim_next_left:
            text = re.sub(r"^[ \t\r\n]+", "", text)
            trim_next_left = False
        if match.group(1).endswith("-"):
            text = re.sub(r"[ \t\r\n]+$", "", text)
        if text:
            tokens.append(_Token("text", text))
        opener = match.group(1)
        closer = match.group(3)
        kind = "var" if opener.startswith("{{") else "tag"
        tokens.append(_Token(kind, match.group(2).strip()))
        trim_next_left = closer.startswith("-")
        pos = match.end()
    tail = source[pos:]
    if trim_next_left:
        tail = re.sub(r"^[ \t\r\n]+", "", tail)
    if tail:
        tokens.append(_Token("text", tail))
    if "{{" in source[pos:] or "{%" in source[pos:]:
        raise TemplateSyntaxError("unclosed tag")
    return tokens


class _Node:
    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class _Text(_Node):
    value: str

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        return self.value


@dataclass(frozen=True)
class _Var(_Node):
    expr: str

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        value = _eval_expr(self.expr, ctx)
        if value is UNDEFINED or value is None:
            return ""
        if ctx.autoescape and not isinstance(value, Markup):
            return html.escape(str(value), quote=True)
        return str(value)


@dataclass(frozen=True)
class _If(_Node):
    branches: tuple[tuple[str, tuple[_Node, ...]], ...]
    else_body: tuple[_Node, ...] | None

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        for expr, body in self.branches:
            if bool(_eval_expr(expr, ctx)):
                return _render_nodes(body, ctx, blocks)
        return _render_nodes(self.else_body or (), ctx, blocks)


@dataclass(frozen=True)
class _For(_Node):
    name: str
    expr: str
    body: tuple[_Node, ...]
    else_body: tuple[_Node, ...] | None

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        seq = _eval_expr(self.expr, ctx)
        try:
            items = [] if seq is UNDEFINED or seq is None else list(seq)
        except TypeError:
            items = []
        if not items:
            return _render_nodes(self.else_body or (), ctx, blocks)
        parts: list[str] = []
        for item in items:
            ctx.push({self.name: item})
            try:
                parts.append(_render_nodes(self.body, ctx, blocks))
            finally:
                ctx.pop()
        return "".join(parts)


@dataclass(frozen=True)
class _With(_Node):
    name: str
    expr: str
    body: tuple[_Node, ...]

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        ctx.push({self.name: _eval_expr(self.expr, ctx)})
        try:
            return _render_nodes(self.body, ctx, blocks)
        finally:
            ctx.pop()


@dataclass(frozen=True)
class _Block(_Node):
    name: str
    body: tuple[_Node, ...]

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        override = (blocks or {}).get(self.name)
        if override is not None and override is not self:
            return _render_nodes(override.body, ctx, blocks)
        return _render_nodes(self.body, ctx, blocks)


@dataclass(frozen=True)
class _Extends(_Node):
    expr: str

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        return ""


@dataclass(frozen=True)
class _Include(_Node):
    expr: str

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        name = _eval_expr(self.expr, ctx)
        return ctx.env.get_template(str(name))._render_with_context(ctx, blocks)


@dataclass(frozen=True)
class _Import(_Node):
    expr: str
    alias: str

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        name = _eval_expr(self.expr, ctx)
        ctx.set(self.alias, ctx.env.get_template(str(name)).make_module(ctx))
        return ""


@dataclass(frozen=True)
class _Macro(_Node):
    name: str
    args: tuple[str, ...]
    body: tuple[_Node, ...]

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        ctx.set(self.name, Macro(self, ctx))
        return ""


@dataclass(frozen=True)
class _AutoEscape(_Node):
    enabled: bool
    body: tuple[_Node, ...]

    def render(self, ctx: _Context, blocks: dict[str, "_Block"] | None = None) -> str:
        old = ctx.autoescape
        ctx.autoescape = self.enabled
        try:
            return _render_nodes(self.body, ctx, blocks)
        finally:
            ctx.autoescape = old


class Macro:
    def __init__(self, node: _Macro, ctx: _Context) -> None:
        self.node = node
        self.ctx = ctx

    def __call__(self, *args: Any) -> Markup:
        values = {name: args[index] if index < len(args) else UNDEFINED for index, name in enumerate(self.node.args)}
        return Markup(_render_nodes(self.node.body, self.ctx.overlay(values), None))


class _Parser:
    def __init__(self, source: str) -> None:
        self.tokens = _tokenize(source)
        self.pos = 0

    def parse(self) -> tuple[_Node, ...]:
        nodes, end = self._parse_until(set())
        if end is not None:
            raise TemplateSyntaxError("unexpected closing tag")
        return nodes

    def _parse_until(self, stop_words: set[str]) -> tuple[tuple[_Node, ...], str | None]:
        nodes: list[_Node] = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token.kind == "text":
                nodes.append(_Text(token.value))
                self.pos += 1
                continue
            if token.kind == "var":
                if not token.value:
                    raise TemplateSyntaxError("empty variable expression")
                nodes.append(_Var(token.value))
                self.pos += 1
                continue
            word = token.value.split(None, 1)[0] if token.value else ""
            if word in stop_words:
                return tuple(nodes), token.value
            nodes.append(self._parse_tag(token.value))
        return tuple(nodes), None

    def _parse_tag(self, tag: str) -> _Node:
        if not tag:
            raise TemplateSyntaxError("empty tag")
        if tag.startswith("if "):
            return self._parse_if(tag[3:].strip())
        if tag.startswith("for "):
            return self._parse_for(tag[4:].strip())
        if tag.startswith("with "):
            return self._parse_with(tag[5:].strip())
        if tag.startswith("block "):
            return self._parse_block(tag[6:].strip())
        if tag.startswith("extends "):
            self.pos += 1
            return _Extends(tag[8:].strip())
        if tag.startswith("include "):
            self.pos += 1
            return _Include(tag[8:].strip())
        if tag.startswith("import "):
            match = re.fullmatch(r"(.+)\s+as\s+([A-Za-z_]\w*)", tag[7:].strip())
            if not match:
                raise TemplateSyntaxError("malformed import tag")
            self.pos += 1
            return _Import(match.group(1).strip(), match.group(2))
        if tag.startswith("macro "):
            return self._parse_macro(tag[6:].strip())
        if tag.startswith("autoescape "):
            return self._parse_autoescape(tag[11:].strip())
        raise TemplateSyntaxError("unknown tag")

    def _parse_if(self, expr: str) -> _If:
        if not expr:
            raise TemplateSyntaxError("if requires condition")
        self.pos += 1
        branches: list[tuple[str, tuple[_Node, ...]]] = []
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
        if end != "endif":
            raise TemplateSyntaxError("if missing endif")
        self.pos += 1
        return _If(tuple(branches), else_body)

    def _parse_for(self, expr: str) -> _For:
        match = re.fullmatch(r"([A-Za-z_]\w*)\s+in\s+(.+)", expr)
        if not match:
            raise TemplateSyntaxError("malformed for tag")
        self.pos += 1
        body, end = self._parse_until({"else", "endfor"})
        else_body = None
        if end == "else":
            self.pos += 1
            else_body, end = self._parse_until({"endfor"})
        if end != "endfor":
            raise TemplateSyntaxError("for missing endfor")
        self.pos += 1
        return _For(match.group(1), match.group(2).strip(), body, else_body)

    def _parse_with(self, expr: str) -> _With:
        match = re.fullmatch(r"([A-Za-z_]\w*)\s*=\s*(.+)", expr)
        if not match:
            raise TemplateSyntaxError("malformed with tag")
        self.pos += 1
        body, end = self._parse_until({"endwith"})
        if end != "endwith":
            raise TemplateSyntaxError("with missing endwith")
        self.pos += 1
        return _With(match.group(1), match.group(2).strip(), body)

    def _parse_block(self, name: str) -> _Block:
        if not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise TemplateSyntaxError("invalid block name")
        self.pos += 1
        body, end = self._parse_until({"endblock"})
        if end != "endblock":
            raise TemplateSyntaxError("block missing endblock")
        self.pos += 1
        return _Block(name, body)

    def _parse_macro(self, expr: str) -> _Macro:
        match = re.fullmatch(r"([A-Za-z_]\w*)\((.*?)\)", expr)
        if not match:
            raise TemplateSyntaxError("malformed macro tag")
        args = tuple(arg.strip() for arg in match.group(2).split(",") if arg.strip())
        if not all(re.fullmatch(r"[A-Za-z_]\w*", arg) for arg in args):
            raise TemplateSyntaxError("invalid macro argument")
        self.pos += 1
        body, end = self._parse_until({"endmacro"})
        if end != "endmacro":
            raise TemplateSyntaxError("macro missing endmacro")
        self.pos += 1
        return _Macro(match.group(1), args, body)

    def _parse_autoescape(self, expr: str) -> _AutoEscape:
        lowered = expr.lower()
        if lowered not in {"true", "false", "on", "off"}:
            raise TemplateSyntaxError("autoescape expects true or false")
        self.pos += 1
        body, end = self._parse_until({"endautoescape"})
        if end != "endautoescape":
            raise TemplateSyntaxError("autoescape missing endautoescape")
        self.pos += 1
        return _AutoEscape(lowered in {"true", "on"}, body)


_COMPARE_RE = re.compile(r"^(.+?)\s+(not\s+in|in|==|!=|<=|>=|<|>)\s+(.+)$")
_TEST_RE = re.compile(r"^(.+?)\s+is\s+(not\s+)?([A-Za-z_]\w*)(?:\((.*)\))?$")
_CALL_RE = re.compile(r"^(.+)\((.*)\)$")
_STRING_RE = re.compile(r"""^(['"])(.*)\1$""", re.S)
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)$")


def _eval_expr(expr: str, ctx: _Context) -> Any:
    expr = expr.strip()
    parts = _split_top_level(expr, "|")
    value = _eval_core(parts[0], ctx)
    for filt in parts[1:]:
        name, args = _parse_callish(filt)
        func = ctx.env.filters.get(name)
        if func is None:
            raise TemplateSyntaxError(f"unknown filter {name}")
        value = func(value, *[_eval_expr(arg, ctx) for arg in args])
    return value


def _eval_core(expr: str, ctx: _Context) -> Any:
    test_match = _TEST_RE.match(expr)
    if test_match:
        value = _eval_expr(test_match.group(1), ctx)
        test = ctx.env.tests.get(test_match.group(3))
        if test is None:
            raise TemplateSyntaxError("unknown test")
        args = [_eval_expr(arg, ctx) for arg in _split_args(test_match.group(4) or "")]
        result = bool(test(value, *args))
        return not result if test_match.group(2) else result

    compare = _COMPARE_RE.match(expr)
    if compare:
        left = _eval_expr(compare.group(1), ctx)
        right = _eval_expr(compare.group(3), ctx)
        op = compare.group(2)
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

    call = _CALL_RE.match(expr)
    if call and _is_balanced_call(expr):
        func = _eval_atom(call.group(1).strip(), ctx)
        args = [_eval_expr(arg, ctx) for arg in _split_args(call.group(2))]
        if callable(func):
            return func(*args)
        return UNDEFINED
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
    string = _STRING_RE.match(expr)
    if string:
        return string.group(2)
    if _INT_RE.match(expr):
        return int(expr)
    if _FLOAT_RE.match(expr):
        return float(expr)

    parts = _split_dotted(expr)
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
        return getattr(value, part)
    except Exception:
        pass
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


def _split_top_level(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    quote = ""
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
        elif char in {"'", '"'}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == sep and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return parts


def _split_args(text: str) -> list[str]:
    if not text.strip():
        return []
    return _split_top_level(text, ",")


def _split_dotted(text: str) -> list[str]:
    return _split_top_level(text, ".")


def _parse_callish(text: str) -> tuple[str, list[str]]:
    text = text.strip()
    match = re.fullmatch(r"([A-Za-z_]\w*)(?:\((.*)\))?", text)
    if not match:
        raise TemplateSyntaxError("malformed filter or test")
    return match.group(1), _split_args(match.group(2) or "")


def _is_balanced_call(text: str) -> bool:
    return text.endswith(")") and "(" in text


def _render_nodes(nodes: Iterable[_Node], ctx: _Context, blocks: dict[str, _Block] | None = None) -> str:
    return "".join(node.render(ctx, blocks) for node in nodes)


def _collect_blocks(nodes: Iterable[_Node]) -> dict[str, _Block]:
    found: dict[str, _Block] = {}
    for node in nodes:
        if isinstance(node, _Block):
            found[node.name] = node
    return found


def _collect_macros(nodes: Iterable[_Node], ctx: _Context) -> dict[str, Macro]:
    macros: dict[str, Macro] = {}
    for node in nodes:
        if isinstance(node, _Macro):
            macros[node.name] = Macro(node, ctx)
    return macros


class Template:
    def __init__(self, source: str, environment: "Environment | None" = None, name: str | None = None) -> None:
        self.source = source
        self.environment = environment or Environment()
        self.name = name
        self._nodes = _Parser(source).parse()

    def render(self, **kwargs: Any) -> str:
        return self._render_with_context(_Context(kwargs, self.environment), None)

    def make_module(self, parent_ctx: _Context | None = None) -> MacroNamespace:
        ctx = parent_ctx.overlay({}) if parent_ctx is not None else _Context({}, self.environment)
        return MacroNamespace(_collect_macros(self._nodes, ctx))

    def _render_with_context(self, ctx: _Context, blocks: dict[str, _Block] | None = None) -> str:
        own_blocks = _collect_blocks(self._nodes)
        merged_blocks = {**own_blocks, **(blocks or {})}
        extends = next((node for node in self._nodes if isinstance(node, _Extends)), None)
        for macro_name, macro in _collect_macros(self._nodes, ctx).items():
            ctx.set(macro_name, macro)
        if extends is not None:
            parent_name = _eval_expr(extends.expr, ctx)
            return ctx.env.get_template(str(parent_name))._render_with_context(ctx, merged_blocks)
        visible_nodes = [node for node in self._nodes if not isinstance(node, _Extends)]
        return _render_nodes(visible_nodes, ctx, merged_blocks)


class Environment:
    def __init__(
        self,
        loader: dict[str, str] | Any | None = None,
        *,
        autoescape: bool = False,
        trim_blocks: bool = False,
        lstrip_blocks: bool = False,
        globals: dict[str, Any] | None = None,
    ) -> None:
        self.loader = loader if loader is not None else {}
        self.autoescape = autoescape
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks
        self.globals: dict[str, Any] = dict(globals or {})
        self.filters = {
            "upper": lambda value: "" if value is UNDEFINED else str(value).upper(),
            "lower": lambda value: "" if value is UNDEFINED else str(value).lower(),
            "title": lambda value: "" if value is UNDEFINED else str(value).title(),
            "length": lambda value: 0 if value is UNDEFINED or value is None else len(value),
            "join": lambda value, sep="": str(sep).join(str(item) for item in (value or [])),
            "default": lambda value, default="": default if value is UNDEFINED or value is None or value == "" else value,
            "escape": lambda value: Markup(html.escape("" if value is UNDEFINED or value is None else str(value), quote=True)),
            "safe": lambda value: Markup("" if value is UNDEFINED or value is None else str(value)),
        }
        self.tests = {
            "defined": lambda value: value is not UNDEFINED,
            "undefined": lambda value: value is UNDEFINED,
            "odd": lambda value: int(value) % 2 == 1,
            "even": lambda value: int(value) % 2 == 0,
            "iterable": lambda value: value is not UNDEFINED and hasattr(value, "__iter__"),
        }
        self._cache: dict[str, Template] = {}

    def from_string(self, source: str, name: str | None = None) -> Template:
        return Template(source, self, name)

    def get_template(self, name: str) -> Template:
        if name in self._cache:
            return self._cache[name]
        source = self._load_source(name)
        template = Template(source, self, name)
        self._cache[name] = template
        return template

    def set_template(self, name: str, source: str) -> None:
        if not isinstance(self.loader, dict):
            raise TypeError("set_template requires a dict loader")
        self.loader[name] = source
        self.invalidate(name)

    def invalidate(self, name: str | None = None) -> None:
        if name is None:
            self._cache.clear()
        else:
            self._cache.pop(name, None)

    def _load_source(self, name: str) -> str:
        if isinstance(self.loader, dict):
            try:
                return self.loader[name]
            except KeyError as exc:
                raise TemplateNotFound(name) from exc
        if hasattr(self.loader, "get_source"):
            return self.loader.get_source(name)
        raise TemplateNotFound(name)
