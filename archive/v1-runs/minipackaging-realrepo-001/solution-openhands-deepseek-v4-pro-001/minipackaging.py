"""
minipackaging - A dependency-free Python module for PEP 440 / PEP 508
version, specifier, requirement, and marker parsing and evaluation.

Only the Python standard library is used.
"""

import os
import platform
import re
import sys
from functools import total_ordering


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvalidVersion(ValueError):
    """Raised when a version string cannot be parsed as a PEP 440 version."""


class InvalidSpecifier(ValueError):
    """Raised when a specifier string cannot be parsed."""


class InvalidRequirement(ValueError):
    """Raised when a requirement string cannot be parsed as PEP 508."""


class InvalidMarker(ValueError):
    """Raised when a marker expression cannot be parsed."""


class UndefinedEnvironmentName(ValueError):
    """Raised when a marker references a variable not in the environment."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UNDERSCORE_OR_DASH = re.compile(r'[-_]+')


def _normalize_name(name: str) -> str:
    """Normalize a distribution name: lowercase, underscores to hyphens."""
    return _UNDERSCORE_OR_DASH.sub('-', name).lower()


def _is_version_value(variable: str) -> bool:
    """Return True for environment variable names that hold version strings."""
    return variable in (
        'python_version',
        'python_full_version',
        'implementation_version',
        'platform_version',
    )


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

# Regular expression that mirrors the subset of PEP 440 described in the PRD.
_VERSION_RE = re.compile(
    r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                         # optional epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                # release segments
        (?P<pre>                                         # pre-release
            [-_\.]?
            (?P<pre_l>a|alpha|b|beta|c|rc|pre|preview)
            (?:[-_\.]?(?P<pre_n>[0-9]+))?
        )?
        (?P<post>                                        # post-release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                (?:[-_\.]?(?P<post_n2>[0-9]+))?
            )
        )?
        (?P<dev>                                         # dev release
            [-_\.]?
            (?P<dev_l>dev)
            (?:[-_\.]?(?P<dev_n>[0-9]+))?
        )?
    )
    (?:\+(?P<local>[a-zA-Z0-9]+(?:[-_\.][a-zA-Z0-9]+)*))?  # local
    """,
    re.IGNORECASE | re.VERBOSE,
)

_PRE_NORMALIZE = {
    'a': 'a', 'alpha': 'a',
    'b': 'b', 'beta': 'b',
    'c': 'rc', 'rc': 'rc', 'pre': 'rc', 'preview': 'rc',
}

_POST_NORMALIZE = {'post': 'post', 'rev': 'post', 'r': 'post'}

# Phase ordering for the sort key: dev < pre < final < post
_PHASE_DEV = 0
_PHASE_PRE = 1
_PHASE_FINAL = 2
_PHASE_POST = 3

# Sub-phase ordering within dev releases: final-dev < pre-dev < post-dev
_DEV_SUB_FINAL = 0
_DEV_SUB_PRE = 1
_DEV_SUB_POST = 2

# Pre-release type ordering
_PRE_ORDER = {'a': 0, 'b': 1, 'rc': 2}


@total_ordering
class Version:
    """A PEP 440 version."""

    __slots__ = (
        '_epoch', '_release', '_release_stripped',
        '_is_dev', '_dev', '_is_pre', '_pre_l', '_pre_n',
        '_is_post', '_post', '_local', '_cmp_key',
    )

    def __init__(self, text: str) -> None:
        text = text.strip()
        m = _VERSION_RE.fullmatch(text)
        if not m:
            raise InvalidVersion(f"Invalid version: {text!r}")

        # epoch
        epoch_str = m.group('epoch')
        self._epoch = int(epoch_str) if epoch_str else 0

        # release
        self._release = tuple(int(s) for s in m.group('release').split('.'))

        # strip trailing zeros for equality/ordering
        rel = list(self._release)
        while len(rel) > 1 and rel[-1] == 0:
            rel.pop()
        self._release_stripped = tuple(rel)

        # pre-release
        self._is_pre = False
        self._pre_l = None
        self._pre_n = 0
        if m.group('pre_l'):
            self._is_pre = True
            raw = m.group('pre_l').lower()
            self._pre_l = _PRE_NORMALIZE[raw]
            self._pre_n = int(m.group('pre_n')) if m.group('pre_n') else 0

        # post-release
        self._is_post = False
        self._post = 0
        if m.group('post_n1'):
            self._is_post = True
            self._post = int(m.group('post_n1'))
        elif m.group('post_l'):
            self._is_post = True
            raw = m.group('post_l').lower()
            # post_l is normalized in __str__, here we just track the number
            self._post = int(m.group('post_n2')) if m.group('post_n2') else 0

        # dev release
        self._is_dev = False
        self._dev = 0
        if m.group('dev_l'):
            self._is_dev = True
            self._dev = int(m.group('dev_n')) if m.group('dev_n') else 0

        # local
        self._local = None
        if m.group('local'):
            raw_local = m.group('local')
            parts = re.split(r'[-_\.]', raw_local)
            local_parts = []
            for p in parts:
                p_lower = p.lower()
                try:
                    local_parts.append(int(p_lower))
                except ValueError:
                    local_parts.append(p_lower)
            self._local = local_parts

        # Build comparison key
        self._cmp_key = self._build_cmp_key()

    def _build_cmp_key(self):
        """Build a sortable tuple following PEP 440 ordering."""
        # Release comparison uses the stripped release
        release = self._release_stripped

        # Phase key: (phase_type, ...)
        # Dev releases carry the full pre/post context so 1.0.dev1 < 1.0a1.dev1 < 1.0a1
        if self._is_dev:
            if self._is_pre:
                if self._is_post:
                    phase = (_PHASE_DEV, _DEV_SUB_POST,
                             _PRE_ORDER[self._pre_l], self._pre_n,
                             _PHASE_POST, self._post, self._dev)
                else:
                    phase = (_PHASE_DEV, _DEV_SUB_PRE,
                             _PRE_ORDER[self._pre_l], self._pre_n, self._dev)
            elif self._is_post:
                phase = (_PHASE_DEV, _DEV_SUB_POST,
                         _PHASE_FINAL, 0, _PHASE_POST, self._post, self._dev)
            else:
                phase = (_PHASE_DEV, _DEV_SUB_FINAL, self._dev)
        elif self._is_pre:
            if self._is_post:
                phase = (_PHASE_PRE, _PRE_ORDER[self._pre_l], self._pre_n,
                         _PHASE_POST, self._post)
            else:
                phase = (_PHASE_PRE, _PRE_ORDER[self._pre_l], self._pre_n)
        elif self._is_post:
            phase = (_PHASE_POST, self._post)
        else:
            phase = (_PHASE_FINAL,)

        return (self._epoch, release, phase)

    def _local_cmp_key(self):
        """Key for local label comparison."""
        if self._local is None:
            return ()
        result = []
        for part in self._local:
            if isinstance(part, int):
                result.append((1, part))
            else:
                result.append((0, part))
        return tuple(result)

    @property
    def epoch(self) -> int:
        return self._epoch

    @property
    def release(self) -> tuple:
        """The release segments, with trailing zeros stripped."""
        return self._release_stripped

    @property
    def is_prerelease(self) -> bool:
        return self._is_pre or self._is_dev

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self._cmp_key == other._cmp_key and
                self._local_cmp_key() == other._local_cmp_key())

    def __lt__(self, other: 'Version') -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self._cmp_key != other._cmp_key:
            return self._cmp_key < other._cmp_key
        return self._local_cmp_key() < other._local_cmp_key()

    def __hash__(self) -> int:
        return hash((self._cmp_key, self._local_cmp_key()))

    def __str__(self) -> str:
        parts = []
        if self._epoch != 0:
            parts.append(f'{self._epoch}!')
        # Strip trailing zeros for canonical output per PEP 440.
        parts.append('.'.join(str(s) for s in self._release_stripped))
        if self._is_pre:
            parts.append(f'{self._pre_l}{self._pre_n}')
        if self._is_post:
            parts.append(f'.post{self._post}')
        if self._is_dev:
            parts.append(f'.dev{self._dev}')
        base = ''.join(parts)
        if self._local:
            local_str = '.'.join(
                str(p) for p in self._local
            )
            base = f'{base}+{local_str}'
        return base

    def __repr__(self) -> str:
        return f"Version({str(self)!r})"


# ---------------------------------------------------------------------------
# Specifier / SpecifierSet
# ---------------------------------------------------------------------------

_SPECIFIER_CLAUSE_RE = re.compile(
    r"""
    \s*
    (?P<op>~=|==|!=|<=|>=|<|>)
    \s*
    (?P<version>.+?)
    \s*
    """,
    re.VERBOSE,
)


class _SpecifierClause:
    """A single specifier clause (e.g. ``>= 1.0``)."""

    __slots__ = ('_op', '_version', '_wildcard', '_prereleases')

    def __init__(self, clause_text: str) -> None:
        m = _SPECIFIER_CLAUSE_RE.fullmatch(clause_text.strip())
        if not m:
            raise InvalidSpecifier(f"Invalid specifier clause: {clause_text!r}")

        self._op = m.group('op')
        version_text = m.group('version').strip()

        self._wildcard = False
        if version_text.endswith('.*'):
            self._wildcard = True
            version_text = version_text[:-2].strip()

        if self._op == '~=' and self._wildcard:
            raise InvalidSpecifier("~= does not support wildcard")

        self._version = Version(version_text)

        # Track whether this clause involves prereleases (for prereleases=None logic)
        self._prereleases = self._version.is_prerelease

    @property
    def op(self) -> str:
        return self._op

    @property
    def version(self) -> Version:
        return self._version

    @property
    def has_prerelease(self) -> bool:
        return self._prereleases

    def _upper_bound(self) -> Version:
        """Compute the exclusive upper bound for ~=."""
        release = list(self._version.release)
        if len(release) == 1:
            upper = [release[0] + 1]
        else:
            upper = release[:-1]
            upper[-1] += 1
        upper_ver = '.'.join(str(s) for s in upper)
        if self._version.epoch:
            upper_ver = f'{self._version.epoch}!{upper_ver}'
        return Version(upper_ver)

    def contains(self, version: Version) -> bool:
        """Check if *version* satisfies this clause (no prerelease filtering)."""
        op = self._op
        v = self._version
        t = version

        if self._wildcard:
            # Wildcard: prefix match on raw release (not stripped),
            # so ==1.0.* matches 1.0.x but not 1.x.
            prefix = v._release
            cand = t._release
            if len(cand) < len(prefix):
                cand = cand + (0,) * (len(prefix) - len(cand))
            matches = cand[:len(prefix)] == prefix
            return not matches if op == '!=' else matches

        if op == '==':
            return t == v
        elif op == '!=':
            return t != v
        elif op == '>=':
            return t >= v
        elif op == '<=':
            return t <= v
        elif op == '>':
            return t > v
        elif op == '<':
            return t < v
        elif op == '~=':
            upper = self._upper_bound()
            # For ~= with a prerelease, the lower bound includes that prerelease
            return t >= v and t < upper
        return False

    def __str__(self) -> str:
        op = self._op
        ver = str(self._version)
        if self._wildcard:
            ver += '.*'
        return f'{op}{ver}'


class SpecifierSet:
    """A set of comma-separated PEP 440 specifier clauses."""

    __slots__ = ('_clauses',)

    def __init__(self, text: str = '') -> None:
        text = text.strip()
        if not text:
            self._clauses = ()
            return

        # Split on commas
        raw_clauses = _split_specifiers(text)
        clauses = []
        for raw in raw_clauses:
            raw = raw.strip()
            if raw:
                clauses.append(_SpecifierClause(raw))
        self._clauses = tuple(clauses)

    def contains(self, version, prereleases=None) -> bool:
        """Return True if *version* satisfies all clauses.

        *version* may be a string or a Version object.
        """
        if isinstance(version, str):
            version = Version(version)

        # Determine whether prereleases should be considered.
        if prereleases is False:
            if version.is_prerelease:
                return False
        elif prereleases is None:
            # Allow prereleases only if at least one clause targets them
            if version.is_prerelease and not any(
                c.has_prerelease for c in self._clauses
            ):
                return False
        # prereleases is True: consider normally

        for clause in self._clauses:
            if not clause.contains(version):
                return False
        return True

    def __bool__(self) -> bool:
        return bool(self._clauses)

    def __str__(self) -> str:
        return ','.join(str(c) for c in self._clauses)

    def __repr__(self) -> str:
        return f"SpecifierSet({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpecifierSet):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))


def _split_specifiers(text: str) -> list:
    """Split a specifier string on commas, respecting version content."""
    parts = []
    current = []
    paren_depth = 0
    for ch in text:
        if ch == ',' and paren_depth == 0:
            parts.append(''.join(current))
            current = []
        else:
            if ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth -= 1
            current.append(ch)
    if current:
        parts.append(''.join(current))
    return parts


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$')

_REQUIREMENT_URL_RE = re.compile(
    r"""
    ^\s*
    (?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)
    \s*
    (?:\[(?P<extras>[^\]]+)\])?
    \s*
    @\s*
    (?P<url>[^;]*?)
    \s*
    (?:;(?P<marker>.+))?
    \s*$
    """,
    re.VERBOSE,
)

_REQUIREMENT_SPEC_RE = re.compile(
    r"""
    ^\s*
    (?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)
    \s*
    (?:\[(?P<extras>[^\]]+)\])?
    \s*
    (?P<specifier>
        (?:~=|==|!=|<=|>=|<|>)
        [^;]*
    )?
    \s*
    (?:;(?P<marker>.+))?
    \s*$
    """,
    re.VERBOSE,
)


def _parse_extras(extras_text: str) -> 'set[str]':
    """Parse and normalize extras from [...].

    Raises InvalidRequirement on invalid extra names.
    """
    result = set()
    for extra in extras_text.split(','):
        extra = extra.strip()
        normalized = _normalize_name(extra)
        if not _NAME_RE.match(extra):
            raise InvalidRequirement(
                f"Invalid extra name: {extra!r}"
            )
        result.add(normalized)
    return result


class Requirement:
    """A PEP 508 requirement."""

    __slots__ = ('_name', '_extras', '_specifier', '_url', '_marker',
                 '_marker_text')

    def __init__(self, text: str) -> None:
        original = text.strip()

        # Try URL form first, then specifier form
        m = _REQUIREMENT_URL_RE.fullmatch(original)
        if m:
            self._name = _normalize_name(m.group('name'))
            self._extras = (
                _parse_extras(m.group('extras'))
                if m.group('extras') else set()
            )
            self._url = m.group('url').strip()
            self._specifier = SpecifierSet('')
            self._marker_text = m.group('marker')
            self._marker = (
                Marker(self._marker_text) if self._marker_text else None
            )
            if not self._url:
                raise InvalidRequirement(
                    f"URL cannot be empty: {text!r}"
                )
            return

        m = _REQUIREMENT_SPEC_RE.fullmatch(original)
        if m:
            self._name = _normalize_name(m.group('name'))
            self._extras = (
                _parse_extras(m.group('extras'))
                if m.group('extras') else set()
            )
            spec_text = (
                m.group('specifier').strip()
                if m.group('specifier') else ''
            )
            self._specifier = SpecifierSet(spec_text)
            self._url = None
            self._marker_text = m.group('marker')
            self._marker = (
                Marker(self._marker_text) if self._marker_text else None
            )
            return

        raise InvalidRequirement(f"Invalid requirement: {text!r}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def extras(self) -> 'set[str]':
        return self._extras

    @property
    def specifier(self) -> SpecifierSet:
        return self._specifier

    @property
    def url(self) -> 'str | None':
        return self._url

    @property
    def marker(self) -> 'Marker | None':
        return self._marker

    def __str__(self) -> str:
        parts = [self._name]
        if self._extras:
            sorted_extras = sorted(self._extras)
            parts.append('[' + ','.join(sorted_extras) + ']')

        if self._url is not None:
            parts.append(f'@ {self._url}')
        elif self._specifier:
            parts.append(str(self._specifier))

        if self._marker:
            parts.append(f'; {self._marker}')

        return ' '.join(parts)

    def __repr__(self) -> str:
        return f"Requirement({str(self)!r})"


# ---------------------------------------------------------------------------
# Marker
# ---------------------------------------------------------------------------

_VALID_VARIABLES = frozenset({
    'python_version',
    'python_full_version',
    'os_name',
    'sys_platform',
    'platform_machine',
    'platform_system',
    'platform_release',
    'platform_version',
    'platform_python_implementation',
    'implementation_name',
    'implementation_version',
    'extra',
})

_OPERATORS = frozenset({'==', '!=', '<', '<=', '>', '>=', 'in', 'not in'})


class _MarkerTokenizer:
    """Tokenizes a marker expression string."""

    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0
        self._length = len(text)

    def _peek(self) -> str:
        if self._pos < self._length:
            return self._text[self._pos]
        return ''

    def _advance(self) -> str:
        ch = self._peek()
        if ch:
            self._pos += 1
        return ch

    def _skip_ws(self) -> None:
        while self._pos < self._length and self._text[self._pos] in ' \t':
            self._pos += 1

    def next_token(self) -> 'tuple[str, str] | None':
        """Return (type, value) or None at end."""
        self._skip_ws()
        if self._pos >= self._length:
            return None

        ch = self._text[self._pos]

        # Operators
        if ch == '=' and self._pos + 1 < self._length:
            if self._text[self._pos + 1] == '=':
                self._pos += 2
                return ('OP', '==')
        if ch == '!' and self._pos + 1 < self._length:
            if self._text[self._pos + 1] == '=':
                self._pos += 2
                return ('OP', '!=')
        if ch == '<':
            if self._pos + 1 < self._length and self._text[self._pos + 1] == '=':
                self._pos += 2
                return ('OP', '<=')
            self._pos += 1
            return ('OP', '<')
        if ch == '>':
            if self._pos + 1 < self._length and self._text[self._pos + 1] == '=':
                self._pos += 2
                return ('OP', '>=')
            self._pos += 1
            return ('OP', '>')

        # Parentheses
        if ch == '(':
            self._pos += 1
            return ('LPAREN', '(')
        if ch == ')':
            self._pos += 1
            return ('RPAREN', ')')

        # Quoted string
        if ch in ("'", '"'):
            quote = ch
            self._pos += 1
            start = self._pos
            while self._pos < self._length:
                if self._text[self._pos] == quote:
                    val = self._text[start:self._pos]
                    self._pos += 1
                    return ('STRING', val)
                self._pos += 1
            raise InvalidMarker("Unterminated string literal")

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            start = self._pos
            while self._pos < self._length and (
                self._text[self._pos].isalnum() or self._text[self._pos] == '_'
            ):
                self._pos += 1
            word = self._text[start:self._pos]

            if word == 'and':
                return ('AND', 'and')
            if word == 'or':
                return ('OR', 'or')
            if word == 'in':
                return ('OP', 'in')
            if word == 'not':
                # peek ahead for 'not in'
                saved = self._pos
                self._skip_ws()
                if (self._pos + 1 < self._length and
                        self._text[self._pos:self._pos + 2] == 'in'):
                    self._pos += 2
                    return ('OP', 'not in')
                self._pos = saved
                raise InvalidMarker("'not' must be followed by 'in'")

            # Variable name
            return ('VAR', word)

        raise InvalidMarker(f"Unexpected character: {ch!r}")


class _MarkerParser:
    """Recursive descent parser for marker expressions.

    Grammar:
        expression  = or_expr
        or_expr     = and_expr ('or' and_expr)*
        and_expr    = atom ('and' atom)*
        atom        = '(' or_expr ')' | comparison
        comparison  = variable op value
    """

    def __init__(self, text: str) -> None:
        self._tokens: list[tuple[str, str]] = []
        self._pos = 0
        tokenizer = _MarkerTokenizer(text)
        while True:
            tok = tokenizer.next_token()
            if tok is None:
                break
            self._tokens.append(tok)

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self):
        tok = self._peek()
        if tok:
            self._pos += 1
        return tok

    def parse(self):
        """Return a tuple representing the AST.

        AST forms:
            ('var', name)           - variable reference
            ('str', value)          - string literal
            ('op', op, lhs, rhs)    - comparison
            ('and', lhs, rhs)       - and
            ('or', lhs, rhs)        - or
        """
        if not self._tokens:
            raise InvalidMarker("Empty marker expression")
        node = self._or_expr()
        if self._peek() is not None:
            raise InvalidMarker("Unexpected token after expression")
        return node

    def _or_expr(self):
        node = self._and_expr()
        while self._peek() and self._peek()[0] == 'OR':
            self._advance()
            right = self._and_expr()
            node = ('or', node, right)
        return node

    def _and_expr(self):
        node = self._atom()
        while self._peek() and self._peek()[0] == 'AND':
            self._advance()
            right = self._atom()
            node = ('and', node, right)
        return node

    def _atom(self):
        tok = self._peek()
        if tok is None:
            raise InvalidMarker("Unexpected end of expression")
        if tok[0] == 'LPAREN':
            self._advance()
            node = self._or_expr()
            tok = self._advance()
            if tok is None or tok[0] != 'RPAREN':
                raise InvalidMarker("Missing closing parenthesis")
            return node
        return self._comparison()

    def _comparison(self):
        # Left side: variable or string literal
        lhs_tok = self._advance()
        if lhs_tok is None or lhs_tok[0] not in ('VAR', 'STRING'):
            raise InvalidMarker("Expected variable name or string value")
        lhs = ('var' if lhs_tok[0] == 'VAR' else 'str', lhs_tok[1])

        op_tok = self._advance()
        if op_tok is None or op_tok[0] != 'OP':
            raise InvalidMarker("Expected operator")
        op = op_tok[1]

        # Right side: variable or string literal
        rhs_tok = self._advance()
        if rhs_tok is None or rhs_tok[0] not in ('VAR', 'STRING'):
            raise InvalidMarker("Expected variable name or string value")
        rhs = ('var' if rhs_tok[0] == 'VAR' else 'str', rhs_tok[1])

        return ('op', op, lhs, rhs)


class Marker:
    """A parsed PEP 508 environment marker expression."""

    __slots__ = ('_ast', '_text')

    def __init__(self, text: str) -> None:
        self._text = text.strip()
        parser = _MarkerParser(self._text)
        try:
            self._ast = parser.parse()
        except InvalidMarker:
            raise
        except Exception as e:
            raise InvalidMarker(
                f"Invalid marker: {text!r} ({e})"
            ) from e

    def _resolve_value(self, node, env: dict):
        """Resolve an AST value node (var or str) to its concrete value.

        Returns (value, is_extra) where is_extra indicates the value came
        from the ``extra`` variable.
        """
        if node[0] == 'var':
            name = node[1]
            if name == 'extra':
                return ('', True)
            if name not in env:
                raise UndefinedEnvironmentName(
                    f"Environment variable not defined: {name!r}"
                )
            return (env[name], False)
        return (node[1], False)

    def _evaluate_node(self, node, env: dict, requested_extras) -> bool:
        """Evaluate an AST node."""
        kind = node[0]

        if kind == 'and':
            return (self._evaluate_node(node[1], env, requested_extras) and
                    self._evaluate_node(node[2], env, requested_extras))

        if kind == 'or':
            return (self._evaluate_node(node[1], env, requested_extras) or
                    self._evaluate_node(node[2], env, requested_extras))

        if kind == 'op':
            op = node[1]
            lhs_node = node[2]
            rhs_node = node[3]

            lhs_value, lhs_is_extra = self._resolve_value(lhs_node, env)
            rhs_value, rhs_is_extra = self._resolve_value(rhs_node, env)

            if lhs_is_extra or rhs_is_extra:
                return self._evaluate_with_extra(
                    op, lhs_node, lhs_value, lhs_is_extra,
                    rhs_node, rhs_value, rhs_is_extra,
                    env, requested_extras,
                )

            # Neither side is extra - straightforward comparison
            # Determine if a version-valued variable is involved
            var_name = ''
            if lhs_node[0] == 'var':
                var_name = lhs_node[1]
            elif rhs_node[0] == 'var':
                var_name = rhs_node[1]
            return self._compare(op, lhs_value, rhs_value, var_name)

        raise InvalidMarker(f"Unknown AST node: {kind}")

    def _evaluate_with_extra(self, op, lhs_node, lhs_value, lhs_is_extra,
                              rhs_node, rhs_value, rhs_is_extra,
                              env, requested_extras) -> bool:
        """Evaluate a comparison involving the extra variable.

        The extra value in the marker is normalized for comparison.
        The expression is true if it is true for AT LEAST ONE
        requested extra (or empty string if none requested).
        """
        extras = requested_extras or set()
        if not extras:
            extras = {''}

        for extra in extras:
            norm_extra = _normalize_name(extra) if extra else ''
            if lhs_is_extra:
                e_lhs = norm_extra
                e_rhs = _normalize_name(rhs_value)
            elif rhs_is_extra:
                e_lhs = _normalize_name(lhs_value)
                e_rhs = norm_extra
            else:
                e_lhs = lhs_value
                e_rhs = rhs_value

            # Determine variable for version-valued comparison
            variable = ''
            if not lhs_is_extra and not rhs_is_extra:
                pass
            elif lhs_is_extra:
                variable = rhs_node[1] if rhs_node[0] == 'var' else ''
            else:
                variable = lhs_node[1] if lhs_node[0] == 'var' else ''

            if self._compare(op, e_lhs, e_rhs, variable):
                return True
        return False

    def _compare(self, op: str, lhs: str, rhs: str,
                 variable: str) -> bool:
        """Compare two values using the appropriate comparison strategy.

        When *variable* names a version-valued environment variable,
        attempt version comparison first.
        """
        if variable and _is_version_value(variable):
            try:
                v_lhs = Version(lhs)
                v_rhs = Version(rhs)
                return self._compare_version(op, v_lhs, v_rhs)
            except InvalidVersion:
                pass

        return self._compare_string(op, lhs, rhs)

    @staticmethod
    def _compare_version(op: str, a: Version, b: Version) -> bool:
        if op == '==':
            return a == b
        if op == '!=':
            return a != b
        if op == '<':
            return a < b
        if op == '<=':
            return a <= b
        if op == '>':
            return a > b
        if op == '>=':
            return a >= b
        if op == 'in':
            return str(a) in str(b)
        if op == 'not in':
            return str(a) not in str(b)
        raise InvalidMarker(f"Unknown operator: {op!r}")

    @staticmethod
    def _compare_string(op: str, a: str, b: str) -> bool:
        if op == '==':
            return a == b
        if op == '!=':
            return a != b
        if op == '<':
            return a < b
        if op == '<=':
            return a <= b
        if op == '>':
            return a > b
        if op == '>=':
            return a >= b
        if op == 'in':
            return a in b
        if op == 'not in':
            return a not in b
        raise InvalidMarker(f"Unknown operator: {op!r}")

    def evaluate(self, environment=None, requested_extras=None) -> bool:
        """Evaluate this marker against an environment.

        *environment* defaults to ``default_environment()`` if None.
        *requested_extras* is a set of normalized extra names (or None/empty).
        """
        if environment is None:
            env = dict(default_environment())
        else:
            env = dict(environment)

        return self._evaluate_node(self._ast, env, requested_extras)

    def _format_node(self, node) -> str:
        """Format an AST node back to canonical string form."""
        kind = node[0]

        if kind == 'and':
            left = self._format_node(node[1])
            right = self._format_node(node[2])
            if node[1][0] == 'or':
                left = f'({left})'
            if node[2][0] == 'or':
                right = f'({right})'
            return f'{left} and {right}'

        if kind == 'or':
            left = self._format_node(node[1])
            right = self._format_node(node[2])
            if node[1][0] == 'and':
                left = f'({left})'
            if node[2][0] == 'and':
                right = f'({right})'
            return f'{left} or {right}'

        if kind == 'op':
            op = node[1]
            lhs_node = node[2]
            rhs_node = node[3]

            # Normalize extra values in canonical output
            if lhs_node[0] == 'var' and lhs_node[1] == 'extra':
                lhs = 'extra'
                rhs_val = _normalize_name(rhs_node[1]) if rhs_node[0] == 'str' else rhs_node[1]
                rhs = f'"{rhs_val}"' if rhs_node[0] == 'str' else rhs_val
            elif rhs_node[0] == 'var' and rhs_node[1] == 'extra':
                rhs = 'extra'
                lhs_val = _normalize_name(lhs_node[1]) if lhs_node[0] == 'str' else lhs_node[1]
                lhs = f'"{lhs_val}"' if lhs_node[0] == 'str' else lhs_val
            else:
                lhs = self._format_atom(lhs_node)
                rhs = self._format_atom(rhs_node)

            return f'{lhs} {op} {rhs}'

        raise InvalidMarker(f"Unknown AST node: {kind}")

    def _format_atom(self, node) -> str:
        """Format a single atom (variable or string)."""
        if node[0] == 'var':
            return node[1]
        else:
            return f'"{node[1]}"'

    def __str__(self) -> str:
        return self._format_node(self._ast)

    def __repr__(self) -> str:
        return f"Marker({str(self)!r})"


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

def default_environment() -> dict:
    """Return a dictionary of all supported marker variables (except extra).

    Values are derived from *sys*, *os*, and *platform*.
    """
    return {
        'python_version': '.'.join(
            str(v) for v in sys.version_info[:2]
        ),
        'python_full_version': sys.version.split()[0],
        'os_name': os.name,
        'sys_platform': sys.platform,
        'platform_machine': platform.machine(),
        'platform_system': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'platform_python_implementation': platform.python_implementation(),
        'implementation_name': sys.implementation.name,
        'implementation_version': '.'.join(
            str(v) for v in sys.implementation.version
        ) if hasattr(sys.implementation, 'version') else '0',
    }


# ---------------------------------------------------------------------------
# Requirement Satisfaction
# ---------------------------------------------------------------------------

def is_requirement_satisfied(
    requirement,
    installed_version,
    environment=None,
    requested_extras=None,
    prereleases=None,
) -> bool:
    """Return whether *installed_version* satisfies *requirement*.

    Parameters
    ----------
    requirement : str or Requirement
    installed_version : str or Version
    environment : dict or None (uses default_environment)
    requested_extras : set or None
    prereleases : bool or None
    """
    if isinstance(requirement, str):
        requirement = Requirement(requirement)

    if isinstance(installed_version, str):
        installed_version = Version(installed_version)

    # If the requirement has a marker, evaluate it first.
    if requirement.marker is not None:
        env = (
            dict(environment) if environment is not None
            else dict(default_environment())
        )
        if not requirement.marker.evaluate(
            environment=env,
            requested_extras=requested_extras,
        ):
            # Marker does not apply -> requirement is considered satisfied.
            return True

    # Marker applies or there is no marker: check specifier.
    if requirement.specifier:
        return requirement.specifier.contains(
            installed_version,
            prereleases=prereleases,
        )

    # No specifier: satisfied by any version.
    return True
