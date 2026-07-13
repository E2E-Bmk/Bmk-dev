import re
import ast

class TemplateSyntaxError(Exception):
    """Raised for malformed templates."""
    pass


class _Undefined:
    """Singleton sentinel for undefined variables."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self):
        return False

    def __str__(self):
        return ''

    def __repr__(self):
        return 'Undefined'


UNDEFINED = _Undefined()


# ---- Expression AST nodes ----

class Literal:
    """A literal value (string, number, bool, None)."""
    def __init__(self, value):
        self.value = value

    def evaluate(self, context):
        return self.value


class Name:
    """A variable name lookup."""
    def __init__(self, name):
        self.name = name

    def evaluate(self, context):
        for scope in reversed(context):
            if self.name in scope:
                return scope[self.name]
        return UNDEFINED


class Getattr:
    """Dotted access: obj.attr -> getattr first, then key/index."""
    def __init__(self, base, attr):
        self.base = base
        self.attr = attr

    def evaluate(self, context):
        base_val = self.base.evaluate(context)
        if isinstance(base_val, _Undefined):
            return UNDEFINED
        # first try attribute access
        try:
            return getattr(base_val, self.attr)
        except AttributeError:
            # then try key/index access
            try:
                return base_val[self.attr]
            except (KeyError, IndexError, TypeError):
                return UNDEFINED


class Compare:
    """Comparison expression: left OP right."""
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def evaluate(self, context):
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        if isinstance(left_val, _Undefined) or isinstance(right_val, _Undefined):
            return False
        try:
            if self.op == '==':
                return left_val == right_val
            elif self.op == '!=':
                return left_val != right_val
            elif self.op == '<':
                return left_val < right_val
            elif self.op == '>':
                return left_val > right_val
            elif self.op == '<=':
                return left_val <= right_val
            elif self.op == '>=':
                return left_val >= right_val
            elif self.op == 'in':
                return left_val in right_val
            elif self.op == 'not in':
                return left_val not in right_val
            else:
                return False
        except TypeError:
            return False


class NotExpr:
    """Unary 'not' expression."""
    def __init__(self, operand):
        self.operand = operand

    def evaluate(self, context):
        val = self.operand.evaluate(context)
        return not truth(val)


class Group:
    """Parenthesised expression."""
    def __init__(self, expr):
        self.expr = expr

    def evaluate(self, context):
        return self.expr.evaluate(context)


def truth(val):
    """Return bool value, treating UNDEFINED as False."""
    if isinstance(val, _Undefined):
        return False
    return bool(val)


# ---- Expression tokenisation and parsing ----

_token_re = re.compile(r"""
    \s* (?:
        (?P<string>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*") |
        (?P<number>\d+\.?\d*|\.\d+) |
        (?P<name>[a-zA-Z_][a-zA-Z0-9_]*) |
        (?P<op>==|!=|<=|>=|<|>) |
        (?P<paren>[()]) |
        (?P<dot>\.) |
        (?P<invalid>\S)
    )
""", re.VERBOSE)


def tokenize_expr(s: str):
    """Return list of (type, value) tokens for an expression string."""
    tokens = []
    for m in _token_re.finditer(s):
        if m.lastgroup == 'string':
            val = ast.literal_eval(m.group('string'))
            tokens.append(('STRING', val))
        elif m.lastgroup == 'number':
            num_str = m.group('number')
            val = float(num_str) if '.' in num_str else int(num_str)
            tokens.append(('NUMBER', val))
        elif m.lastgroup == 'name':
            name = m.group('name')
            low = name.lower()
            if low == 'true':
                tokens.append(('TRUE', True))
            elif low == 'false':
                tokens.append(('FALSE', False))
            elif low == 'none':
                tokens.append(('NONE', None))
            elif low == 'not':
                tokens.append(('NOT', 'not'))
            elif low == 'in':
                tokens.append(('IN', 'in'))
            else:
                tokens.append(('NAME', name))
        elif m.lastgroup == 'op':
            tokens.append(('OP', m.group('op')))
        elif m.lastgroup == 'paren':
            paren = m.group('paren')
            typ = 'LPAREN' if paren == '(' else 'RPAREN'
            tokens.append((typ, paren))
        elif m.lastgroup == 'dot':
            tokens.append(('DOT', '.'))
        elif m.lastgroup == 'invalid':
            raise TemplateSyntaxError(f"Unexpected character '{m.group('invalid')}'")
    # merge adjacent NOT IN into NOT_IN
    merged = []
    i = 0
    while i < len(tokens):
        if (tokens[i][0] == 'NOT' and i + 1 < len(tokens)
                and tokens[i + 1][0] == 'IN'):
            merged.append(('NOT_IN', 'not in'))
            i += 2
        else:
            merged.append(tokens[i])
            i += 1
    return merged


class ExpressionParser:
    """Recursive-descent parser for the condition/expression grammar."""
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ('EOF', None)

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, typ, value=None):
        tok = self.advance()
        if tok[0] != typ:
            raise TemplateSyntaxError(f"Expected {typ}, got {tok[0]}")
        if value is not None and tok[1] != value:
            raise TemplateSyntaxError(f"Expected {value}")
        return tok

    def parse(self):
        return self.comparison()

    def comparison(self):
        left = self.unary()
        tok = self.peek()
        if tok[0] in ('OP', 'IN', 'NOT_IN'):
            op_tok = self.advance()
            op = op_tok[1]
            right = self.unary()
            return Compare(left, op, right)
        return left

    def unary(self):
        tok = self.peek()
        if tok[0] == 'NOT':
            self.advance()
            operand = self.unary()
            return NotExpr(operand)
        return self.primary()

    def primary(self):
        tok = self.peek()
        if tok[0] == 'NAME':
            name = tok[1]
            self.advance()
            expr = Name(name)
            while self.peek()[0] == 'DOT':
                self.advance()                 # consume dot
                attr_tok = self.expect('NAME') # attribute must be a name
                expr = Getattr(expr, attr_tok[1])
            return expr
        elif tok[0] in ('STRING', 'NUMBER', 'TRUE', 'FALSE', 'NONE'):
            val = tok[1]
            self.advance()
            return Literal(val)
        elif tok[0] == 'LPAREN':
            self.advance()
            expr = self.parse()
            self.expect('RPAREN')
            return Group(expr)
        else:
            raise TemplateSyntaxError(f"Unexpected token {tok}")


def parse_expr(text: str):
    """Parse an expression string and return the AST root."""
    text = text.strip()
    if not text:
        # empty expression -> literal empty string (used for empty {{ }})
        return Literal('')
    tokens = tokenize_expr(text)
    parser = ExpressionParser(tokens)
    return parser.parse()


# ---- Template AST nodes ----

class TextNode:
    """Plain text content."""
    def __init__(self, text):
        self.text = text

    def render(self, context, output):
        output.append(self.text)


class VariableNode:
    """{{ expression }}"""
    def __init__(self, expr_ast):
        self.expr = expr_ast

    def render(self, context, output):
        val = self.expr.evaluate(context)
        if not isinstance(val, _Undefined):
            output.append(str(val))


class IfNode:
    """{% if %}..{% elif %}..{% else %}..{% endif %}"""
    def __init__(self, branches):
        # branches: list of (condition_ast_or_None, body_nodes)
        self.branches = branches

    def render(self, context, output):
        for cond, body in self.branches:
            if cond is None or truth(cond.evaluate(context)):
                for node in body:
                    node.render(context, output)
                break


class ForNode:
    """{% for var in expr %}..{% else %}..{% endfor %}"""
    def __init__(self, loop_var, seq_expr_ast, body, else_body):
        self.loop_var = loop_var
        self.seq_expr = seq_expr_ast
        self.body = body
        self.else_body = else_body

    def render(self, context, output):
        seq_val = self.seq_expr.evaluate(context)
        if isinstance(seq_val, _Undefined):
            iterator = iter([])
        else:
            try:
                iterator = iter(seq_val)
            except TypeError:
                iterator = iter([])
        has_items = False
        for item in iterator:
            has_items = True
            context.append({self.loop_var: item})
            for node in self.body:
                node.render(context, output)
            context.pop()
        if not has_items and self.else_body:
            for node in self.else_body:
                node.render(context, output)


class BlockNode:
    """{% block name %}..{% endblock %}"""
    def __init__(self, name, body):
        self.name = name
        self.body = body

    def render(self, context, output):
        for node in self.body:
            node.render(context, output)


class WithNode:
    """{% with var = expr %}..{% endwith %}"""
    def __init__(self, var_name, value_expr_ast, body):
        self.var_name = var_name
        self.value_expr = value_expr_ast
        self.body = body

    def render(self, context, output):
        val = self.value_expr.evaluate(context)
        context.append({self.var_name: val})
        for node in self.body:
            node.render(context, output)
        context.pop()


# ---- Template class ----

class Template:
    """A compiled template. Created from a source string."""

    def __init__(self, source):
        self.nodes = self._parse(source)

    def render(self, **kwargs):
        """Render template with context variables passed as keyword arguments."""
        context = [kwargs]
        output = []
        for node in self.nodes:
            node.render(context, output)
        return ''.join(output)

    # ----- parsing -----
    def _tokenize_template(self, source):
        tag_re = re.compile(r'\{\{(.+?)\}\}|{%(.+?)%}', re.DOTALL)
        tokens = []
        last_end = 0
        for m in tag_re.finditer(source):
            start = m.start()
            if start > last_end:
                tokens.append(('text', source[last_end:start]))
            if m.group(1) is not None:
                tokens.append(('var', m.group(1).strip()))
            else:
                tokens.append(('tag', m.group(2).strip()))
            last_end = m.end()
        if last_end < len(source):
            tokens.append(('text', source[last_end:]))
        return tokens

    def _parse(self, source):
        tokens = self._tokenize_template(source)
        nodes, idx = self._parse_nodes(tokens, 0, ())
        if idx != len(tokens):
            raise TemplateSyntaxError("Unexpected tokens at end of template")
        return nodes

    def _parse_nodes(self, tokens, start_idx, stop_tags):
        idx = start_idx
        nodes = []
        while idx < len(tokens):
            tok_type, content = tokens[idx]
            if tok_type == 'text':
                nodes.append(TextNode(content))
                idx += 1
            elif tok_type == 'var':
                # empty variable tag just outputs nothing
                if content == '':
                    nodes.append(TextNode(''))
                else:
                    expr_ast = parse_expr(content)
                    nodes.append(VariableNode(expr_ast))
                idx += 1
            elif tok_type == 'tag':
                command = content.strip()
                parts = command.split(None, 1)
                tag_word = parts[0] if parts else ''

                # stop if we hit a tag that our caller handles
                if tag_word in stop_tags:
                    return nodes, idx   # do not consume this tag

                if tag_word == 'if':
                    if len(parts) < 2 or not parts[1].strip():
                        raise TemplateSyntaxError("if tag requires a condition")
                    cond_ast = parse_expr(parts[1].strip())
                    body, idx = self._parse_nodes(
                        tokens, idx + 1, stop_tags=('elif', 'else', 'endif')
                    )
                    branches = [(cond_ast, body)]
                    while idx < len(tokens):
                        tok2 = tokens[idx]
                        if tok2[0] != 'tag':
                            raise TemplateSyntaxError("Expected elif/else/endif")
                        cmd2 = tok2[1].strip()
                        parts2 = cmd2.split(None, 1)
                        tw2 = parts2[0] if parts2 else ''
                        if tw2 == 'elif':
                            if len(parts2) < 2 or not parts2[1].strip():
                                raise TemplateSyntaxError("elif tag requires a condition")
                            elif_cond = parse_expr(parts2[1].strip())
                            body2, idx = self._parse_nodes(
                                tokens, idx + 1, stop_tags=('elif', 'else', 'endif')
                            )
                            branches.append((elif_cond, body2))
                        elif tw2 == 'else':
                            body2, idx = self._parse_nodes(
                                tokens, idx + 1, stop_tags=('endif',)
                            )
                            branches.append((None, body2))
                        elif tw2 == 'endif':
                            idx += 1
                            break
                        else:
                            raise TemplateSyntaxError("Expected elif/else/endif")
                    else:
                        raise TemplateSyntaxError("Unclosed if block – missing endif")
                    nodes.append(IfNode(branches))

                elif tag_word == 'for':
                    rest = parts[1].strip() if len(parts) > 1 else ''
                    match = re.match(r'(\w+)\s+in\s+(.+)', rest, re.DOTALL)
                    if not match:
                        raise TemplateSyntaxError("Invalid for syntax: expected 'for var in expr'")
                    loop_var = match.group(1)
                    seq_expr_text = match.group(2).strip()
                    seq_ast = parse_expr(seq_expr_text)
                    body, idx = self._parse_nodes(
                        tokens, idx + 1, stop_tags=('else', 'endfor')
                    )
                    else_body = None
                    if idx >= len(tokens):
                        raise TemplateSyntaxError("Unclosed for block – missing endfor")
                    tok2 = tokens[idx]
                    if tok2[0] != 'tag':
                        raise TemplateSyntaxError("Expected else/endfor")
                    cmd2 = tok2[1].strip()
                    tw2 = cmd2.split()[0] if cmd2.split() else ''
                    if tw2 == 'else':
                        else_body, idx = self._parse_nodes(
                            tokens, idx + 1, stop_tags=('endfor',)
                        )
                        if (idx >= len(tokens) or tokens[idx][0] != 'tag' or
                                tokens[idx][1].strip().split()[0] != 'endfor'):
                            raise TemplateSyntaxError("Expected endfor after else")
                        idx += 1  # consume endfor
                    elif tw2 == 'endfor':
                        idx += 1
                    else:
                        raise TemplateSyntaxError("Expected else/endfor")
                    nodes.append(ForNode(loop_var, seq_ast, body, else_body))

                elif tag_word == 'block':
                    if len(parts) < 2 or not parts[1].strip():
                        raise TemplateSyntaxError("block tag requires a name")
                    block_name = parts[1].strip()
                    body, idx = self._parse_nodes(
                        tokens, idx + 1, stop_tags=('endblock',)
                    )
                    if (idx >= len(tokens) or tokens[idx][0] != 'tag' or
                            tokens[idx][1].strip().split()[0] != 'endblock'):
                        raise TemplateSyntaxError("Expected endblock")
                    idx += 1
                    nodes.append(BlockNode(block_name, body))

                elif tag_word == 'with':
                    rest = parts[1].strip() if len(parts) > 1 else ''
                    if '=' not in rest:
                        raise TemplateSyntaxError("with tag requires assignment")
                    var_part, expr_part = rest.split('=', 1)
                    var_name = var_part.strip()
                    if not var_name.isidentifier():
                        raise TemplateSyntaxError(f"Invalid variable name '{var_name}'")
                    value_expr_text = expr_part.strip()
                    if not value_expr_text:
                        raise TemplateSyntaxError("with tag requires a value expression")
                    value_ast = parse_expr(value_expr_text)
                    body, idx = self._parse_nodes(
                        tokens, idx + 1, stop_tags=('endwith',)
                    )
                    if (idx >= len(tokens) or tokens[idx][0] != 'tag' or
                            tokens[idx][1].strip().split()[0] != 'endwith'):
                        raise TemplateSyntaxError("Expected endwith")
                    idx += 1
                    nodes.append(WithNode(var_name, value_ast, body))

                else:
                    raise TemplateSyntaxError(f"Unknown tag '{tag_word}'")
            else:
                raise TemplateSyntaxError("Internal tokenisation error")
        return nodes, idx


# ---- Environment class ----

class Environment:
    """Optional environment that can compile templates."""

    def from_string(self, source):
        """Compile a template string and return a Template instance."""
        return Template(source)
