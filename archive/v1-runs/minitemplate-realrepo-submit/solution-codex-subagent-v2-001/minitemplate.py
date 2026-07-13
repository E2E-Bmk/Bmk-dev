"""A compact Jinja-like template engine for the MiniTemplate benchmark."""

from __future__ import annotations

import ast
import html
import re
from types import SimpleNamespace
from typing import Any


class TemplateSyntaxError(Exception):
    pass


class TemplateNotFound(Exception):
    pass


class Undefined:
    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return ""

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        return 0

    def __getattr__(self, _name: str) -> "Undefined":
        return self

    def __getitem__(self, _key: Any) -> "Undefined":
        return self

    def __call__(self, *_args: Any, **_kwargs: Any) -> "Undefined":
        return self


UNDEFINED = Undefined()


class SafeString(str):
    pass


def _is_undefined(value: Any) -> bool:
    return isinstance(value, Undefined)


def _is_safe(value: Any) -> bool:
    return isinstance(value, SafeString)


def _to_string(value: Any) -> str:
    if _is_undefined(value):
        return ""
    return str(value)


def _filter_upper(value: Any) -> str:
    return _to_string(value).upper()


def _filter_lower(value: Any) -> str:
    return _to_string(value).lower()


def _filter_title(value: Any) -> str:
    return _to_string(value).title()


def _filter_length(value: Any) -> int:
    if _is_undefined(value) or value is None:
        return 0
    try:
        return len(value)
    except TypeError:
        return 0


def _filter_join(value: Any, sep: str = "") -> str:
    if _is_undefined(value) or value is None:
        return ""
    return str(sep).join(_to_string(item) for item in value)


def _filter_default(value: Any, default: Any = "", boolean: bool = False) -> Any:
    if _is_undefined(value):
        return default
    if boolean and not value:
        return default
    return value


def _filter_escape(value: Any) -> SafeString:
    return SafeString(html.escape(_to_string(value), quote=True))


def _filter_safe(value: Any) -> SafeString:
    if _is_safe(value):
        return value
    return SafeString(_to_string(value))


def _test_defined(value: Any) -> bool:
    return not _is_undefined(value)


def _test_undefined(value: Any) -> bool:
    return _is_undefined(value)


def _test_odd(value: Any) -> bool:
    try:
        return int(value) % 2 == 1
    except Exception:
        return False


def _test_even(value: Any) -> bool:
    try:
        return int(value) % 2 == 0
    except Exception:
        return False


def _test_iterable(value: Any) -> bool:
    if _is_undefined(value) or value is None:
        return False
    try:
        iter(value)
        return True
    except TypeError:
        return False


class Context:
    def __init__(self, env: "Environment", values: dict[str, Any] | None = None):
        self.env = env
        self.scopes: list[dict[str, Any]] = [dict(env.globals), dict(values or {})]
        self.autoescape_stack = [bool(env.autoescape)]

    @property
    def autoescape(self) -> bool:
        return self.autoescape_stack[-1]

    def push(self, values: dict[str, Any] | None = None) -> None:
        self.scopes.append(dict(values or {}))

    def pop(self) -> None:
        self.scopes.pop()

    def set(self, name: str, value: Any) -> None:
        self.scopes[-1][name] = value

    def resolve(self, name: str) -> Any:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return UNDEFINED

    def flatten(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for scope in self.scopes:
            values.update(scope)
        return values


class Environment:
    def __init__(
        self,
        loader: dict[str, str] | None = None,
        *,
        autoescape: bool = False,
        trim_blocks: bool = False,
        lstrip_blocks: bool = False,
        globals: dict[str, Any] | None = None,
    ):
        self.loader = loader if loader is not None else {}
        self.autoescape = autoescape
        self.trim_blocks = trim_blocks
        self.lstrip_blocks = lstrip_blocks
        self.globals = dict(globals or {})
        self.cache: dict[str, Template] = {}
        self.filters = {
            "upper": _filter_upper,
            "lower": _filter_lower,
            "title": _filter_title,
            "length": _filter_length,
            "join": _filter_join,
            "default": _filter_default,
            "escape": _filter_escape,
            "safe": _filter_safe,
        }
        self.tests = {
            "defined": _test_defined,
            "undefined": _test_undefined,
            "odd": _test_odd,
            "even": _test_even,
            "iterable": _test_iterable,
        }

    def from_string(self, source: str, name: str | None = None) -> "Template":
        return Template(source, env=self, name=name)

    def get_template(self, name: str) -> "Template":
        if name in self.cache:
            return self.cache[name]
        if name not in self.loader:
            raise TemplateNotFound(name)
        template = Template(self.loader[name], env=self, name=name)
        self.cache[name] = template
        return template

    def set_template(self, name: str, source: str) -> None:
        self.loader[name] = source
        self.invalidate(name)

    def invalidate(self, name: str | None = None) -> None:
        if name is None:
            self.cache.clear()
        else:
            self.cache.pop(name, None)


class Template:
    def __init__(self, source: str, env: Environment | None = None, name: str | None = None):
        self.source = source
        self.env = env if env is not None else Environment()
        self.name = name
        parser = Parser(self.env, source)
        self.nodes = parser.parse()
        self.blocks = _collect_blocks(self.nodes)
        self.macros = _collect_macros(self.nodes)
        self.extends_expr = parser.extends_expr

    def render(self, **kwargs: Any) -> str:
        ctx = Context(self.env, kwargs)
        return self._render_with_context(ctx, {})

    def _render_with_context(
        self, ctx: Context, blocks: dict[str, "BlockNode"] | None = None
    ) -> str:
        blocks = dict(blocks or {})
        for node in self.nodes:
            if isinstance(node, MacroNode):
                node.render(ctx, blocks)
        if self.extends_expr is not None:
            for node in self.nodes:
                if isinstance(node, ImportNode):
                    node.render(ctx, blocks)
            merged = dict(self.blocks)
            merged.update(blocks)
            parent_name = _to_string(eval_expr(self.extends_expr, ctx))
            parent = self.env.get_template(parent_name)
            return parent._render_with_context(ctx, merged)
        return "".join(node.render(ctx, blocks) for node in self.nodes)

    def _exported_macros(self, closure: dict[str, Any] | None = None) -> dict[str, "Macro"]:
        return {name: Macro(self, node, closure=closure) for name, node in self.macros.items()}


class TextNode:
    def __init__(self, text: str):
        self.text = text

    def render(self, _ctx: Context, _blocks: dict[str, "BlockNode"]) -> str:
        return self.text


class OutputNode:
    def __init__(self, expr: str):
        self.expr = expr

    def render(self, ctx: Context, _blocks: dict[str, "BlockNode"]) -> str:
        value = eval_expr(self.expr, ctx)
        if _is_undefined(value):
            return ""
        if ctx.autoescape and not _is_safe(value):
            return html.escape(str(value), quote=True)
        return str(value)


class ExtendsNode:
    def __init__(self, expr: str):
        self.expr = expr

    def render(self, _ctx: Context, _blocks: dict[str, "BlockNode"]) -> str:
        return ""


class IncludeNode:
    def __init__(self, expr: str):
        self.expr = expr

    def render(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        name = _to_string(eval_expr(self.expr, ctx))
        template = ctx.env.get_template(name)
        return template._render_with_context(ctx, {})


class ImportNode:
    def __init__(self, expr: str, alias: str):
        self.expr = expr
        self.alias = alias

    def render(self, ctx: Context, _blocks: dict[str, "BlockNode"]) -> str:
        name = _to_string(eval_expr(self.expr, ctx))
        template = ctx.env.get_template(name)
        ctx.set(self.alias, SimpleNamespace(**template._exported_macros(ctx.flatten())))
        return ""


class IfNode:
    def __init__(
        self,
        branches: list[tuple[str, list[Any]]],
        else_body: list[Any] | None = None,
    ):
        self.branches = branches
        self.else_body = else_body or []

    def render(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        for expr, body in self.branches:
            if bool(eval_expr(expr, ctx)):
                return "".join(node.render(ctx, blocks) for node in body)
        return "".join(node.render(ctx, blocks) for node in self.else_body)


class ForNode:
    def __init__(
        self,
        var_name: str,
        expr: str,
        body: list[Any],
        else_body: list[Any] | None = None,
    ):
        self.var_name = var_name
        self.expr = expr
        self.body = body
        self.else_body = else_body or []

    def render(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        value = eval_expr(self.expr, ctx)
        if _is_undefined(value) or value is None:
            items: list[Any] = []
        else:
            try:
                items = list(value)
            except TypeError:
                items = []
        if not items:
            return "".join(node.render(ctx, blocks) for node in self.else_body)
        out: list[str] = []
        length = len(items)
        for index, item in enumerate(items):
            loop = SimpleNamespace(
                index=index + 1,
                index0=index,
                first=index == 0,
                last=index == length - 1,
                length=length,
            )
            ctx.push({self.var_name: item, "loop": loop})
            try:
                out.append("".join(node.render(ctx, blocks) for node in self.body))
            finally:
                ctx.pop()
        return "".join(out)


class WithNode:
    def __init__(self, assignments: list[tuple[str, str]], body: list[Any]):
        self.assignments = assignments
        self.body = body

    def render(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        values = {name: eval_expr(expr, ctx) for name, expr in self.assignments}
        ctx.push(values)
        try:
            return "".join(node.render(ctx, blocks) for node in self.body)
        finally:
            ctx.pop()


class BlockNode:
    def __init__(self, name: str, body: list[Any]):
        self.name = name
        self.body = body

    def render(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        override = blocks.get(self.name)
        if override is not None and override is not self:
            return override._render_body(ctx, blocks)
        return self._render_body(ctx, blocks)

    def _render_body(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        return "".join(node.render(ctx, blocks) for node in self.body)


class MacroNode:
    def __init__(self, name: str, params: list[str], body: list[Any]):
        self.name = name
        self.params = params
        self.body = body

    def render(self, ctx: Context, _blocks: dict[str, "BlockNode"]) -> str:
        ctx.set(self.name, Macro(None, self, ctx.env, closure=ctx.flatten()))
        return ""


class AutoescapeNode:
    def __init__(self, expr: str, body: list[Any]):
        self.expr = expr
        self.body = body

    def render(self, ctx: Context, blocks: dict[str, "BlockNode"]) -> str:
        ctx.autoescape_stack.append(bool(eval_expr(self.expr, ctx)))
        try:
            return "".join(node.render(ctx, blocks) for node in self.body)
        finally:
            ctx.autoescape_stack.pop()


class Macro:
    def __init__(
        self,
        template: Template | None,
        node: MacroNode,
        env: Environment | None = None,
        closure: dict[str, Any] | None = None,
    ):
        self.template = template
        self.node = node
        self.env = env if env is not None else template.env  # type: ignore[union-attr]
        self.closure = dict(closure or {})

    def __call__(self, *args: Any, **kwargs: Any) -> SafeString:
        values = dict(self.closure)
        values.update(dict(zip(self.node.params, args)))
        values.update(kwargs)
        for name in self.node.params:
            values.setdefault(name, UNDEFINED)
        if self.template is not None:
            for name, node in self.template.macros.items():
                values.setdefault(name, Macro(self.template, node, closure=self.closure))
        ctx = Context(self.env, values)
        rendered = "".join(node.render(ctx, {}) for node in self.node.body)
        return SafeString(rendered)


class Parser:
    def __init__(self, env: Environment, source: str):
        self.env = env
        self.tokens = _tokenize(source, env)
        self.pos = 0
        self.extends_expr: str | None = None

    def parse(self) -> list[Any]:
        nodes, stop = self._parse_until(set())
        if stop is not None:
            raise TemplateSyntaxError("unexpected end tag")
        return nodes

    def _parse_until(self, stops: set[str]) -> tuple[list[Any], str | None]:
        nodes: list[Any] = []
        while self.pos < len(self.tokens):
            kind, content = self.tokens[self.pos]
            if kind == "text":
                self.pos += 1
                nodes.append(TextNode(content))
                continue
            if kind == "var":
                self.pos += 1
                if not content:
                    raise TemplateSyntaxError("empty expression")
                nodes.append(OutputNode(content))
                continue

            keyword = content.split(None, 1)[0] if content else ""
            if keyword in stops:
                self.pos += 1
                return nodes, content
            if keyword in {"endif", "endfor", "endwith", "endblock", "endmacro", "endautoescape"}:
                raise TemplateSyntaxError("unexpected end tag")
            self.pos += 1
            nodes.append(self._parse_tag(keyword, content))
        if stops:
            raise TemplateSyntaxError("unclosed block")
        return nodes, None

    def _parse_tag(self, keyword: str, content: str) -> Any:
        rest = content[len(keyword) :].strip()
        if keyword == "if":
            if not rest:
                raise TemplateSyntaxError("empty if")
            branches: list[tuple[str, list[Any]]] = []
            body, stop = self._parse_until({"elif", "else", "endif"})
            branches.append((rest, body))
            else_body: list[Any] = []
            while stop is not None and stop.startswith("elif"):
                expr = stop[4:].strip()
                if not expr:
                    raise TemplateSyntaxError("empty elif")
                body, stop = self._parse_until({"elif", "else", "endif"})
                branches.append((expr, body))
            if stop is not None and stop.startswith("else"):
                else_body, stop = self._parse_until({"endif"})
            if stop is None or not stop.startswith("endif"):
                raise TemplateSyntaxError("unclosed if")
            return IfNode(branches, else_body)

        if keyword == "for":
            match = re.match(r"^([A-Za-z_]\w*)\s+in\s+(.+)$", rest)
            if not match:
                raise TemplateSyntaxError("malformed for")
            body, stop = self._parse_until({"else", "endfor"})
            else_body: list[Any] = []
            if stop is not None and stop.startswith("else"):
                else_body, stop = self._parse_until({"endfor"})
            if stop is None or not stop.startswith("endfor"):
                raise TemplateSyntaxError("unclosed for")
            return ForNode(match.group(1), match.group(2).strip(), body, else_body)

        if keyword == "with":
            assignments = _parse_assignments(rest)
            body, stop = self._parse_until({"endwith"})
            if stop is None:
                raise TemplateSyntaxError("unclosed with")
            return WithNode(assignments, body)

        if keyword == "block":
            if not re.match(r"^[A-Za-z_]\w*$", rest):
                raise TemplateSyntaxError("malformed block")
            body, stop = self._parse_until({"endblock"})
            if stop is None:
                raise TemplateSyntaxError("unclosed block")
            return BlockNode(rest, body)

        if keyword == "extends":
            if not rest:
                raise TemplateSyntaxError("empty extends")
            if self.extends_expr is not None:
                raise TemplateSyntaxError("duplicate extends")
            self.extends_expr = rest
            return ExtendsNode(rest)

        if keyword == "include":
            if not rest:
                raise TemplateSyntaxError("empty include")
            return IncludeNode(rest)

        if keyword == "import":
            match = re.match(r"^(.+?)\s+as\s+([A-Za-z_]\w*)$", rest)
            if not match:
                raise TemplateSyntaxError("malformed import")
            return ImportNode(match.group(1).strip(), match.group(2))

        if keyword == "macro":
            match = re.match(r"^([A-Za-z_]\w*)\s*\((.*)\)$", rest)
            if not match:
                raise TemplateSyntaxError("malformed macro")
            params = []
            param_text = match.group(2).strip()
            if param_text:
                for part in _split_top_level(param_text, ","):
                    part = part.strip()
                    if not re.match(r"^[A-Za-z_]\w*$", part):
                        raise TemplateSyntaxError("malformed macro parameter")
                    params.append(part)
            body, stop = self._parse_until({"endmacro"})
            if stop is None:
                raise TemplateSyntaxError("unclosed macro")
            return MacroNode(match.group(1), params, body)

        if keyword == "autoescape":
            if not rest:
                raise TemplateSyntaxError("empty autoescape")
            body, stop = self._parse_until({"endautoescape"})
            if stop is None:
                raise TemplateSyntaxError("unclosed autoescape")
            return AutoescapeNode(rest, body)

        raise TemplateSyntaxError("unknown tag")


def _collect_blocks(nodes: list[Any]) -> dict[str, BlockNode]:
    blocks: dict[str, BlockNode] = {}
    for node in nodes:
        if isinstance(node, BlockNode):
            blocks[node.name] = node
    return blocks


def _collect_macros(nodes: list[Any]) -> dict[str, MacroNode]:
    macros: dict[str, MacroNode] = {}
    for node in nodes:
        if isinstance(node, MacroNode):
            macros[node.name] = node
    return macros


def _tokenize(source: str, env: Environment) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    trim_next = False
    while pos < len(source):
        var_at = source.find("{{", pos)
        tag_at = source.find("{%", pos)
        starts = [idx for idx in (var_at, tag_at) if idx != -1]
        if not starts:
            text = source[pos:]
            if trim_next:
                text = text.lstrip()
            if text:
                tokens.append(("text", text))
            break
        start = min(starts)
        kind = "var" if start == var_at else "tag"
        text = source[pos:start]
        if trim_next:
            text = text.lstrip()
            trim_next = False
        if kind == "tag" and env.lstrip_blocks:
            text = re.sub(r"(^|\n)[ \t]+$", lambda m: m.group(1), text)
        trim_left = start + 2 < len(source) and source[start + 2] == "-"
        if trim_left:
            text = text.rstrip()
        if text:
            tokens.append(("text", text))

        close = "}}" if kind == "var" else "%}"
        end = source.find(close, start + 2)
        if end == -1:
            raise TemplateSyntaxError("unclosed delimiter")
        content_start = start + 3 if trim_left else start + 2
        trim_right = end > content_start and source[end - 1] == "-"
        content_end = end - 1 if trim_right else end
        content = source[content_start:content_end].strip()
        tokens.append((kind, content))
        pos = end + 2
        if kind == "tag" and (trim_right or env.trim_blocks):
            if source.startswith("\r\n", pos):
                pos += 2
            elif pos < len(source) and source[pos] == "\n":
                pos += 1
        trim_next = trim_right
    return tokens


def _parse_assignments(text: str) -> list[tuple[str, str]]:
    if not text:
        raise TemplateSyntaxError("empty with")
    assignments: list[tuple[str, str]] = []
    for part in _split_top_level(text, ","):
        if "=" not in part:
            raise TemplateSyntaxError("malformed assignment")
        name, expr = part.split("=", 1)
        name = name.strip()
        expr = expr.strip()
        if not re.match(r"^[A-Za-z_]\w*$", name) or not expr:
            raise TemplateSyntaxError("malformed assignment")
        assignments.append((name, expr))
    return assignments


def eval_expr(expr: str, ctx: Context) -> Any:
    expr = expr.strip()
    if not expr:
        return UNDEFINED

    parts = _split_top_level_word(expr, "or")
    if len(parts) > 1:
        result = UNDEFINED
        for part in parts:
            result = eval_expr(part, ctx)
            if result:
                return result
        return result

    parts = _split_top_level_word(expr, "and")
    if len(parts) > 1:
        result = True
        for part in parts:
            result = eval_expr(part, ctx)
            if not result:
                return result
        return result

    if _starts_with_word(expr, "not"):
        return not bool(eval_expr(expr[3:].strip(), ctx))

    test_split = _split_test(expr)
    if test_split is not None:
        left, negate, test_name, args_text = test_split
        value = eval_expr(left, ctx)
        test = ctx.env.tests.get(test_name)
        if test is None:
            return False
        args, kwargs = _parse_call_args(args_text, ctx) if args_text is not None else ([], {})
        result = bool(test(value, *args, **kwargs))
        return not result if negate else result

    comp = _split_comparison(expr)
    if comp is not None:
        left, op, right = comp
        a = eval_expr(left, ctx)
        b = eval_expr(right, ctx)
        try:
            if op == "==":
                return a == b
            if op == "!=":
                return a != b
            if op == "<":
                return a < b
            if op == ">":
                return a > b
            if op == "<=":
                return a <= b
            if op == ">=":
                return a >= b
            if op == "in":
                return a in b
            if op == "not in":
                return a not in b
        except Exception:
            return False

    pipe_parts = _split_top_level(expr, "|")
    if len(pipe_parts) > 1:
        value = _eval_atom(pipe_parts[0].strip(), ctx)
        for part in pipe_parts[1:]:
            value = _apply_filter(value, part.strip(), ctx)
        return value

    return _eval_atom(expr, ctx)


def _eval_atom(expr: str, ctx: Context) -> Any:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        dotted = _eval_dotted_path(expr, ctx)
        if dotted is not None:
            return dotted
        raise TemplateSyntaxError("malformed expression")
    return _eval_ast(tree.body, ctx)


def _eval_dotted_path(expr: str, ctx: Context) -> Any | None:
    if not re.match(r"^[A-Za-z_]\w*(?:\.(?:[A-Za-z_]\w*|\d+))+$", expr):
        return None
    parts = expr.split(".")
    value = ctx.resolve(parts[0])
    for part in parts[1:]:
        value = _resolve_attr(value, part)
    return value


def _eval_ast(node: ast.AST, ctx: Context) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in {"true", "True"}:
            return True
        if node.id in {"false", "False"}:
            return False
        if node.id in {"none", "None", "null"}:
            return None
        return ctx.resolve(node.id)
    if isinstance(node, ast.Attribute):
        return _resolve_attr(_eval_ast(node.value, ctx), node.attr)
    if isinstance(node, ast.Subscript):
        value = _eval_ast(node.value, ctx)
        key = _eval_ast(node.slice, ctx)
        try:
            return value[key]
        except Exception:
            return UNDEFINED
    if isinstance(node, ast.List):
        return [_eval_ast(item, ctx) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_ast(item, ctx) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval_ast(key, ctx): _eval_ast(value, ctx)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not bool(_eval_ast(node.operand, ctx))
    if isinstance(node, ast.BoolOp):
        values = [_eval_ast(value, ctx) for value in node.values]
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in values:
                result = value
                if not value:
                    return value
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in values:
                result = value
                if value:
                    return value
            return result
    if isinstance(node, ast.Compare):
        left = _eval_ast(node.left, ctx)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_ast(comparator, ctx)
            if not _compare_values(left, op, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Call):
        func = _eval_ast(node.func, ctx)
        args = [_eval_ast(arg, ctx) for arg in node.args]
        kwargs = {kw.arg: _eval_ast(kw.value, ctx) for kw in node.keywords if kw.arg}
        if callable(func):
            return func(*args, **kwargs)
        return UNDEFINED
    raise TemplateSyntaxError("unsupported expression")


def _compare_values(left: Any, op: ast.cmpop, right: Any) -> bool:
    try:
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.In):
            return left in right
        if isinstance(op, ast.NotIn):
            return left not in right
    except Exception:
        return False
    return False


def _resolve_attr(value: Any, part: str) -> Any:
    if _is_undefined(value) or value is None:
        return UNDEFINED
    if not part.startswith("_"):
        try:
            return getattr(value, part)
        except Exception:
            pass
    try:
        return value[part]
    except Exception:
        pass
    try:
        index = int(part)
        return value[index]
    except Exception:
        return UNDEFINED


def _apply_filter(value: Any, spec: str, ctx: Context) -> Any:
    name, args_text = _parse_name_call(spec)
    if not name:
        raise TemplateSyntaxError("malformed filter")
    func = ctx.env.filters.get(name)
    if func is None:
        return value
    args, kwargs = _parse_call_args(args_text, ctx) if args_text is not None else ([], {})
    return func(value, *args, **kwargs)


def _parse_name_call(spec: str) -> tuple[str, str | None]:
    spec = spec.strip()
    if spec.endswith(")") and "(" in spec:
        idx = spec.find("(")
        name = spec[:idx].strip()
        return name, spec[idx + 1 : -1]
    return spec, None


def _parse_call_args(text: str, ctx: Context) -> tuple[list[Any], dict[str, Any]]:
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    if not text or not text.strip():
        return args, kwargs
    for part in _split_top_level(text, ","):
        if _has_top_level_equals(part):
            name, expr = part.split("=", 1)
            kwargs[name.strip()] = eval_expr(expr.strip(), ctx)
        else:
            args.append(eval_expr(part.strip(), ctx))
    return args, kwargs


def _has_top_level_equals(text: str) -> bool:
    for i, ch in enumerate(text):
        if ch == "=":
            return True
    return False


def _split_top_level(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    escape = False
    for i, ch in enumerate(text):
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch in "([{":
            depth += 1
            continue
        if ch in ")]}":
            depth -= 1
            continue
        if depth == 0 and ch == sep:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def _split_top_level_word(text: str, word: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch in "([{":
            depth += 1
            i += 1
            continue
        if ch in ")]}":
            depth -= 1
            i += 1
            continue
        if depth == 0 and _word_at(text, i, word):
            parts.append(text[start:i].strip())
            i += len(word)
            start = i
            continue
        i += 1
    if parts:
        parts.append(text[start:].strip())
        return parts
    return [text]


def _starts_with_word(text: str, word: str) -> bool:
    return _word_at(text, 0, word)


def _word_at(text: str, index: int, word: str) -> bool:
    if not text.startswith(word, index):
        return False
    before = text[index - 1] if index > 0 else " "
    after_index = index + len(word)
    after = text[after_index] if after_index < len(text) else " "
    return not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_")


def _split_test(expr: str) -> tuple[str, bool, str, str | None] | None:
    idx = _find_top_level_word(expr, "is")
    if idx == -1:
        return None
    left = expr[:idx].strip()
    rest = expr[idx + 2 :].strip()
    negate = False
    if _starts_with_word(rest, "not"):
        negate = True
        rest = rest[3:].strip()
    name, args_text = _parse_name_call(rest)
    if not left or not name:
        raise TemplateSyntaxError("malformed test")
    return left, negate, name, args_text


def _find_top_level_word(text: str, word: str) -> int:
    depth = 0
    quote: str | None = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch in "([{":
            depth += 1
            i += 1
            continue
        if ch in ")]}":
            depth -= 1
            i += 1
            continue
        if depth == 0 and _word_at(text, i, word):
            return i
        i += 1
    return -1


def _split_comparison(expr: str) -> tuple[str, str, str] | None:
    for op in ("not in", "==", "!=", "<=", ">=", "<", ">", "in"):
        idx = _find_top_level_operator(expr, op)
        if idx != -1:
            left = expr[:idx].strip()
            right = expr[idx + len(op) :].strip()
            if left and right:
                return left, op, right
    return None


def _find_top_level_operator(text: str, op: str) -> int:
    depth = 0
    quote: str | None = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch in "([{":
            depth += 1
            i += 1
            continue
        if ch in ")]}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            if op.isalpha() or " " in op:
                if _word_sequence_at(text, i, op):
                    return i
            elif text.startswith(op, i):
                return i
        i += 1
    return -1


def _word_sequence_at(text: str, index: int, seq: str) -> bool:
    words = seq.split()
    pos = index
    for n, word in enumerate(words):
        if n > 0:
            while pos < len(text) and text[pos].isspace():
                pos += 1
        if not text.startswith(word, pos):
            return False
        before = text[pos - 1] if pos > 0 else " "
        after_index = pos + len(word)
        after = text[after_index] if after_index < len(text) else " "
        if before.isalnum() or before == "_" or after.isalnum() or after == "_":
            return False
        pos = after_index
    return True
