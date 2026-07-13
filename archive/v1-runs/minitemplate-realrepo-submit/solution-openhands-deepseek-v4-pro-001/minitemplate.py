"""minitemplate — a text template engine.

Supports: variable substitution {{ }}, conditionals {% if %}, loops {% for %},
block definitions {% block %}, and variable assignment {% with %}.
"""

__all__ = ['Template', 'Environment', 'TemplateSyntaxError']


class TemplateSyntaxError(Exception):
    """Raised at parse time for malformed templates."""
    pass


# ---------------------------------------------------------------------------
# Value resolution and expression evaluation
# ---------------------------------------------------------------------------

def _resolve_var(expr, context):
    """Resolve a dotted variable expression against *context*."""
    parts = [p.strip() for p in expr.split('.')]
    val = context
    for part in parts:
        if val is None:
            return None
        if isinstance(val, dict):
            val = val.get(part)
            continue
        # 1. attribute access
        try:
            val = getattr(val, part)
            continue
        except (AttributeError, TypeError):
            pass
        # 2. key/index access (as‑is)
        try:
            val = val[part]
            continue
        except (KeyError, IndexError, TypeError):
            pass
        # 3. integer index
        try:
            idx = int(part)
            val = val[idx]
            continue
        except (ValueError, KeyError, IndexError, TypeError):
            pass
        return None
    return val


def _resolve_value(expr, context):
    """Resolve an expression: try variable first, then literal."""
    expr = expr.strip()
    val = _resolve_var(expr, context)
    if val is not None:
        return val
    # int literal
    try:
        return int(expr)
    except (ValueError, TypeError):
        pass
    # float literal
    try:
        return float(expr)
    except (ValueError, TypeError):
        pass
    # string literal
    if len(expr) >= 2:
        if (expr[0] == '"' and expr[-1] == '"'):
            return expr[1:-1]
        if (expr[0] == "'" and expr[-1] == "'"):
            return expr[1:-1]
    # Not a variable, not a literal — undefined
    return None


def _evaluate_condition(expr, context):
    """Evaluate a conditional expression in the given context.
    
    Undefined variables are treated as falsy.
    """
    expr = expr.strip()

    # 'not in' before 'in' (prefix overlap)
    if ' not in ' in expr:
        left, right = expr.split(' not in ', 1)
        left_val = _resolve_value(left.strip(), context)
        right_val = _resolve_value(right.strip(), context)
        try:
            return left_val not in right_val
        except TypeError:
            return True

    if ' in ' in expr:
        left, right = expr.split(' in ', 1)
        left_val = _resolve_value(left.strip(), context)
        right_val = _resolve_value(right.strip(), context)
        try:
            return left_val in right_val
        except TypeError:
            return False

    # Comparison operators – check longer forms first
    for op in ('>=', '<=', '!=', '==', '>', '<'):
        if op in expr:
            left, right = expr.split(op, 1)
            left_val = _resolve_value(left.strip(), context)
            right_val = _resolve_value(right.strip(), context)
            try:
                if op == '==':
                    return left_val == right_val
                if op == '!=':
                    return left_val != right_val
                if op == '>':
                    return left_val > right_val
                if op == '<':
                    return left_val < right_val
                if op == '>=':
                    return left_val >= right_val
                if op == '<=':
                    return left_val <= right_val
            except TypeError:
                return op == '!='   # a != b is True when incomparable
        # (break not needed — we return inside the if)

    # Truthiness check
    val = _resolve_value(expr, context)
    return bool(val)


# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------

class _Node:
    """Base class for template AST nodes."""
    pass


class _TextNode(_Node):
    __slots__ = ('text',)

    def __init__(self, text):
        self.text = text

    def render(self, output, context):
        output.append(self.text)


class _VarNode(_Node):
    __slots__ = ('expr',)

    def __init__(self, expr):
        self.expr = expr

    def render(self, output, context):
        val = _resolve_var(self.expr, context)
        if val is not None:
            output.append(str(val))


class _IfNode(_Node):
    __slots__ = ('conditions', 'bodies', 'else_body')

    def __init__(self, conditions, bodies, else_body):
        self.conditions = conditions          # list of condition strings
        self.bodies = bodies                  # list of list-of-_Node
        self.else_body = else_body or []      # list of _Node

    def render(self, output, context):
        for cond_expr, body in zip(self.conditions, self.bodies):
            if _evaluate_condition(cond_expr, context):
                for node in body:
                    node.render(output, context)
                return
        for node in self.else_body:
            node.render(output, context)


class _ForNode(_Node):
    __slots__ = ('loop_var', 'seq_expr', 'body', 'else_body')

    def __init__(self, loop_var, seq_expr, body, else_body):
        self.loop_var = loop_var
        self.seq_expr = seq_expr
        self.body = body
        self.else_body = else_body or []

    def render(self, output, context):
        seq = _resolve_var(self.seq_expr, context)
        if seq is None:
            seq = []
        try:
            items = list(seq)
        except TypeError:
            items = [seq] if seq else []
        if not items:
            for node in self.else_body:
                node.render(output, context)
            return
        for item in items:
            inner = dict(context)
            inner[self.loop_var] = item
            for node in self.body:
                node.render(output, inner)


class _BlockNode(_Node):
    __slots__ = ('name', 'body')

    def __init__(self, name, body):
        self.name = name
        self.body = body

    def render(self, output, context):
        for node in self.body:
            node.render(output, context)


class _WithNode(_Node):
    __slots__ = ('var_name', 'value_expr', 'body')

    def __init__(self, var_name, value_expr, body):
        self.var_name = var_name
        self.value_expr = value_expr
        self.body = body

    def render(self, output, context):
        val = _resolve_value(self.value_expr, context)
        inner = dict(context)
        inner[self.var_name] = val
        for node in self.body:
            node.render(output, inner)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class _Parser:
    """Recursive‑descent parser for MiniTemplate syntax."""

    def __init__(self, source):
        self.tokens = self._tokenize(source)
        self.pos = 0
        self.len_tokens = len(self.tokens)

    # -- tokenizer ---------------------------------------------------------

    @staticmethod
    def _tokenize(source):
        tokens = []
        i = 0
        n = len(source)
        while i < n:
            if source[i:i + 2] == '{{':
                j = source.find('}}', i + 2)
                if j == -1:
                    raise TemplateSyntaxError("Unclosed '{{'")
                tokens.append(('var', source[i + 2:j].strip()))
                i = j + 2
            elif source[i:i + 2] == '{%':
                j = source.find('%}', i + 2)
                if j == -1:
                    raise TemplateSyntaxError("Unclosed '{%'")
                tokens.append(('tag', source[i + 2:j].strip()))
                i = j + 2
            else:
                j = source.find('{{', i)
                k = source.find('{%', i)
                nxt = n
                if j != -1:
                    nxt = min(nxt, j)
                if k != -1:
                    nxt = min(nxt, k)
                tokens.append(('text', source[i:nxt]))
                i = nxt
        return tokens

    # -- helpers -----------------------------------------------------------

    def _peek_tag(self):
        """Return the raw tag string at the current position, or None."""
        if self.pos >= self.len_tokens:
            return None
        tt, tv = self.tokens[self.pos]
        if tt != 'tag':
            return None
        return tv.strip()

    @staticmethod
    def _tag_name(tag):
        """Return the command name (first word) of *tag*."""
        parts = tag.split(None, 1)
        return parts[0] if parts else tag

    # -- top‑level entry ---------------------------------------------------

    def parse(self):
        self.pos = 0
        return self._parse_content(None)

    # -- content parsing ---------------------------------------------------

    def _parse_content(self, stop_commands):
        """Parse until a tag whose command is in *stop_commands* is seen.

        Returns a list of _Node.  Does **not** consume the stop tag.
        """
        nodes = []
        while self.pos < self.len_tokens:
            tt, tv = self.tokens[self.pos]

            if tt == 'text':
                nodes.append(_TextNode(tv))
                self.pos += 1
            elif tt == 'var':
                nodes.append(_VarNode(tv))
                self.pos += 1
            elif tt == 'tag':
                tag = tv.strip()
                cmd = self._tag_name(tag)

                if stop_commands and cmd in stop_commands:
                    return nodes

                if cmd == 'if':
                    nodes.append(self._parse_if())
                elif cmd == 'for':
                    nodes.append(self._parse_for())
                elif cmd == 'block':
                    nodes.append(self._parse_block())
                elif cmd == 'with':
                    nodes.append(self._parse_with())
                else:
                    raise TemplateSyntaxError(
                        f"Unexpected tag '{{% {tag} %}}'"
                    )
        if stop_commands:
            raise TemplateSyntaxError(
                f"Missing end tag: expected one of {stop_commands}"
            )
        return nodes

    # -- if / elif / else / endif ------------------------------------------

    def _parse_if(self):
        tag = self.tokens[self.pos][1].strip()
        parts = tag.split(None, 1)
        if len(parts) < 2:
            raise TemplateSyntaxError(f"Invalid tag '{{% {tag} %}}'")
        cond_raw = parts[1]
        self.pos += 1

        conditions = [cond_raw]
        bodies = [self._parse_content({'elif', 'else', 'endif'})]
        else_body = []

        while self.pos < self.len_tokens:
            tag = self._peek_tag()
            if tag is None:
                raise TemplateSyntaxError("Missing 'endif'")
            cmd = self._tag_name(tag)

            if cmd == 'elif':
                parts = tag.split(None, 1)
                if len(parts) < 2:
                    raise TemplateSyntaxError(f"Invalid tag '{{% {tag} %}}'")
                self.pos += 1
                conditions.append(parts[1])
                bodies.append(self._parse_content({'elif', 'else', 'endif'}))
            elif cmd == 'else':
                self.pos += 1
                else_body = self._parse_content({'endif'})
                if self.pos >= self.len_tokens:
                    raise TemplateSyntaxError("Missing 'endif' after 'else'")
                tag = self._peek_tag()
                if tag is None or self._tag_name(tag) != 'endif':
                    raise TemplateSyntaxError("Missing 'endif' after 'else'")
                self.pos += 1
                return _IfNode(conditions, bodies, else_body)
            elif cmd == 'endif':
                self.pos += 1
                return _IfNode(conditions, bodies, else_body)
            else:
                raise TemplateSyntaxError(
                    f"Unexpected tag '{{% {tag} %}}' in if block"
                )

        raise TemplateSyntaxError("Missing 'endif'")

    # -- for / else / endfor -----------------------------------------------

    def _parse_for(self):
        tag = self.tokens[self.pos][1].strip()
        rest = tag[4:].strip()          # strip 'for '
        if ' in ' not in rest:
            raise TemplateSyntaxError(f"Invalid tag '{{% {tag} %}}'")
        loop_var, seq_expr = rest.split(' in ', 1)
        self.pos += 1

        body = self._parse_content({'else', 'endfor'})
        else_body = []

        if self.pos >= self.len_tokens:
            raise TemplateSyntaxError("Missing 'endfor'")
        tag = self._peek_tag()
        if tag is None:
            raise TemplateSyntaxError("Missing 'endfor'")
        cmd = self._tag_name(tag)

        if cmd == 'else':
            self.pos += 1
            else_body = self._parse_content({'endfor'})
            if self.pos >= self.len_tokens:
                raise TemplateSyntaxError("Missing 'endfor' after 'else'")
            tag = self._peek_tag()
            if tag is None or self._tag_name(tag) != 'endfor':
                raise TemplateSyntaxError("Missing 'endfor' after 'else'")
            self.pos += 1
        elif cmd == 'endfor':
            self.pos += 1
        else:
            raise TemplateSyntaxError(
                f"Unexpected tag '{{% {tag} %}}' in for block"
            )

        return _ForNode(loop_var.strip(), seq_expr.strip(), body, else_body)

    # -- block / endblock --------------------------------------------------

    def _parse_block(self):
        tag = self.tokens[self.pos][1].strip()
        name = tag[6:].strip()          # strip 'block '
        self.pos += 1

        body = self._parse_content({'endblock'})

        if self.pos >= self.len_tokens:
            raise TemplateSyntaxError("Missing 'endblock'")
        tag = self._peek_tag()
        if tag is None or self._tag_name(tag) != 'endblock':
            raise TemplateSyntaxError("Missing 'endblock'")
        self.pos += 1
        return _BlockNode(name, body)

    # -- with / endwith ----------------------------------------------------

    def _parse_with(self):
        tag = self.tokens[self.pos][1].strip()
        rest = tag[5:].strip()          # strip 'with '
        if '=' not in rest:
            raise TemplateSyntaxError(f"Invalid tag '{{% {tag} %}}'")
        var_name, value_expr = rest.split('=', 1)
        self.pos += 1

        body = self._parse_content({'endwith'})

        if self.pos >= self.len_tokens:
            raise TemplateSyntaxError("Missing 'endwith'")
        tag = self._peek_tag()
        if tag is None or self._tag_name(tag) != 'endwith':
            raise TemplateSyntaxError("Missing 'endwith'")
        self.pos += 1
        return _WithNode(var_name.strip(), value_expr.strip(), body)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class Template:
    """A compiled template that can be rendered multiple times."""

    __slots__ = ('source', 'nodes')

    def __init__(self, source):
        self.source = source
        parser = _Parser(source)
        self.nodes = parser.parse()

    def render(self, **kwargs):
        """Render the template with keyword arguments as variables.

        Undefined variables are rendered as empty strings.
        Returns the rendered string.
        """
        output = []
        context = dict(kwargs)
        for node in self.nodes:
            node.render(output, context)
        return ''.join(output)


class Environment:
    """Template environment for advanced usage."""

    def __init__(self):
        pass

    def from_string(self, source):
        """Compile a template string into a :class:`Template`."""
        return Template(source)
