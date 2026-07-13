"""A compact, dependency-free subset of Python packaging semantics."""

from __future__ import annotations

import os
import platform
import re
import sys
from functools import total_ordering


class InvalidVersion(ValueError):
    pass


class InvalidSpecifier(ValueError):
    pass


class InvalidRequirement(ValueError):
    pass


class InvalidMarker(ValueError):
    pass


class UndefinedEnvironmentName(ValueError):
    pass


_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")


def _normalize_name(name: str) -> str:
    if not _NAME_RE.match(name):
        raise ValueError("invalid name")
    return name.replace("_", "-").lower()


def _trim_release(parts: tuple[int, ...]) -> tuple[int, ...]:
    parts = tuple(parts)
    while len(parts) > 1 and parts[-1] == 0:
        parts = parts[:-1]
    return parts


_VERSION_RE = re.compile(
    r"""
    ^\s*
    v?
    (?:(?P<epoch>[0-9]+)!)?
    (?P<release>[0-9]+(?:\.[0-9]+)*)
    (?:
        [-_.]?
        (?P<pre_l>a|alpha|b|beta|rc|c|pre|preview)
        [-_.]?
        (?P<pre_n>[0-9]+)?
    )?
    (?:
        (?:[-_.]?(?P<post_l>post|rev|r)[-_.]?(?P<post_n>[0-9]+)?)
        |
        (?:-(?P<post_n2>[0-9]+))
    )?
    (?:
        [-_.]?
        (?P<dev_l>dev)
        [-_.]?
        (?P<dev_n>[0-9]+)?
    )?
    (?:\+(?P<local>[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*))?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


@total_ordering
class Version:
    def __init__(self, text):
        if isinstance(text, Version):
            self.epoch = text.epoch
            self.release = text.release
            self.pre = text.pre
            self.post = text.post
            self.dev = text.dev
            self.local = text.local
            return

        m = _VERSION_RE.match(str(text))
        if not m:
            raise InvalidVersion("invalid version")

        self.epoch = int(m.group("epoch") or 0)
        self.release = _trim_release(tuple(int(p) for p in m.group("release").split(".")))

        pre_l = m.group("pre_l")
        if pre_l:
            pre_map = {
                "alpha": "a",
                "a": "a",
                "beta": "b",
                "b": "b",
                "rc": "rc",
                "c": "rc",
                "pre": "rc",
                "preview": "rc",
            }
            self.pre = (pre_map[pre_l.lower()], int(m.group("pre_n") or 0))
        else:
            self.pre = None

        post_n = m.group("post_n")
        if post_n is None:
            post_n = m.group("post_n2")
        self.post = int(post_n or 0) if (m.group("post_l") or m.group("post_n2")) else None

        self.dev = int(m.group("dev_n") or 0) if m.group("dev_l") else None

        local = m.group("local")
        if local:
            self.local = tuple(
                str(int(p)) if p.isdigit() else p.lower()
                for p in re.split(r"[-_.]", local)
            )
        else:
            self.local = None

    @property
    def is_prerelease(self) -> bool:
        return self.pre is not None or self.dev is not None

    def _public_key(self):
        if self.dev is not None and self.pre is None and self.post is None:
            suffix = (0, self.dev)
        elif self.pre is not None:
            pre_order = {"a": 0, "b": 1, "rc": 2}[self.pre[0]]
            if self.dev is not None:
                suffix = (1, pre_order, self.pre[1], -1, self.dev)
            else:
                suffix = (1, pre_order, self.pre[1], 0)
        else:
            suffix = (2,)
            if self.post is not None:
                if self.dev is not None:
                    suffix = (3, self.post, -1, self.dev)
                else:
                    suffix = (3, self.post, 0)
        return (self.epoch, self.release, suffix)

    def _local_key(self):
        if self.local is None:
            return ()
        key = []
        for part in self.local:
            if part.isdigit():
                key.append((1, int(part)))
            else:
                key.append((0, part))
        return tuple(key)

    def _cmp_public(self, other: "Version") -> int:
        if self.epoch != other.epoch:
            return -1 if self.epoch < other.epoch else 1

        max_len = max(len(self.release), len(other.release))
        left = self.release + (0,) * (max_len - len(self.release))
        right = other.release + (0,) * (max_len - len(other.release))
        if left != right:
            return -1 if left < right else 1

        ls = self._public_key()[2]
        rs = other._public_key()[2]
        if ls != rs:
            return -1 if ls < rs else 1
        return 0

    def __eq__(self, other):
        try:
            other = Version(other)
        except InvalidVersion:
            return NotImplemented
        return self._cmp_public(other) == 0 and self._local_key() == other._local_key()

    def __lt__(self, other):
        other = Version(other)
        public = self._cmp_public(other)
        if public:
            return public < 0
        return self._local_key() < other._local_key()

    def __hash__(self):
        return hash((self.epoch, self.release, self._public_key()[2], self._local_key()))

    def __str__(self):
        s = ""
        if self.epoch:
            s += f"{self.epoch}!"
        s += ".".join(str(p) for p in self.release)
        if self.pre is not None:
            s += f"{self.pre[0]}{self.pre[1]}"
        if self.post is not None:
            s += f".post{self.post}"
        if self.dev is not None:
            s += f".dev{self.dev}"
        if self.local is not None:
            s += "+" + ".".join(self.local)
        return s

    def __repr__(self):
        return f"<Version('{self}')>"


class _Clause:
    def __init__(self, op: str, version_text: str):
        self.op = op
        self.wildcard = False
        self.version = None
        self.prefix = None

        version_text = version_text.strip()
        if op in {"==", "!="} and version_text.endswith(".*"):
            prefix_text = version_text[:-2]
            if not re.match(r"^(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*$", prefix_text):
                raise InvalidSpecifier("invalid wildcard specifier")
            epoch = 0
            if "!" in prefix_text:
                e, prefix_text = prefix_text.split("!", 1)
                epoch = int(e)
            self.wildcard = True
            self.prefix = (epoch, tuple(int(p) for p in prefix_text.split(".")))
            self.text = f"{op}{version_text.lower()}"
        else:
            self.version = Version(version_text)
            self.text = f"{op}{self.version}"

    def _matches_prefix(self, version: Version) -> bool:
        assert self.prefix is not None
        epoch, prefix = self.prefix
        if version.epoch != epoch:
            return False
        release = version.release + (0,) * max(0, len(prefix) - len(version.release))
        return release[: len(prefix)] == prefix

    def contains(self, version: Version) -> bool:
        if self.wildcard:
            matched = self._matches_prefix(version)
            return matched if self.op == "==" else not matched
        if self.op == "==":
            return version == self.version
        if self.op == "!=":
            return version != self.version
        if self.op == ">=":
            return version >= self.version
        if self.op == "<=":
            return version <= self.version
        if self.op == ">":
            return version > self.version
        if self.op == "<":
            return version < self.version
        if self.op == "~=":
            return version >= self.version and version < _compatible_upper_bound(self.version)
        raise AssertionError("unknown operator")

    def __str__(self):
        return self.text


def _compatible_upper_bound(version: Version) -> Version:
    parts = list(version.release)
    if len(parts) == 1:
        upper = [parts[0] + 1]
    else:
        upper = parts[:-1]
        upper[-1] += 1
    prefix = f"{version.epoch}!" if version.epoch else ""
    return Version(prefix + ".".join(str(p) for p in upper))


class SpecifierSet:
    _CLAUSE_RE = re.compile(r"^(===|==|!=|>=|<=|~=|>|<)\s*(\S+)$")

    def __init__(self, text: str = ""):
        self._clauses = []
        text = "" if text is None else str(text).strip()
        if not text:
            return
        for raw in text.split(","):
            raw = raw.strip()
            if not raw:
                raise InvalidSpecifier("empty specifier clause")
            m = self._CLAUSE_RE.match(raw)
            if not m or m.group(1) == "===":
                raise InvalidSpecifier("invalid specifier")
            try:
                self._clauses.append(_Clause(m.group(1), m.group(2)))
            except InvalidVersion as exc:
                raise InvalidSpecifier("invalid version in specifier") from exc

    def contains(self, version, prereleases=None) -> bool:
        version = Version(version)
        if prereleases is False and version.is_prerelease:
            return False
        if prereleases is not True and version.is_prerelease:
            has_prerelease_bound = any(
                clause.version is not None
                and clause.version.is_prerelease
                and clause.op != "!="
                for clause in self._clauses
            )
            if not has_prerelease_bound:
                return False
        return all(clause.contains(version) for clause in self._clauses)

    def __contains__(self, version):
        return self.contains(version)

    def __bool__(self):
        return bool(self._clauses)

    def __str__(self):
        return ",".join(str(c) for c in self._clauses)

    def __repr__(self):
        return f"<SpecifierSet('{self}')>"


_MARKER_VARIABLES = {
    "python_version",
    "python_full_version",
    "os_name",
    "sys_platform",
    "platform_machine",
    "platform_system",
    "platform_release",
    "platform_version",
    "platform_python_implementation",
    "implementation_name",
    "implementation_version",
    "extra",
}


class _MarkerTokenizer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def tokens(self):
        out = []
        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c.isspace():
                self.pos += 1
                continue
            if c in "()":
                out.append((c, c))
                self.pos += 1
                continue
            if c in "\"'":
                out.append(("STRING", self._string()))
                continue
            two = self.text[self.pos : self.pos + 2]
            if two in {"==", "!=", "<=", ">="}:
                out.append(("OP", two))
                self.pos += 2
                continue
            if c in "<>":
                out.append(("OP", c))
                self.pos += 1
                continue
            m = re.match(r"[A-Za-z0-9_.-]+", self.text[self.pos :])
            if not m:
                raise InvalidMarker("invalid marker token")
            word = m.group(0)
            low = word.lower()
            self.pos += len(word)
            if low in {"and", "or", "in"}:
                out.append((low.upper(), low))
            elif low == "not":
                save = self.pos
                while self.pos < len(self.text) and self.text[self.pos].isspace():
                    self.pos += 1
                m2 = re.match(r"[A-Za-z0-9_.-]+", self.text[self.pos :])
                if m2 and m2.group(0).lower() == "in":
                    self.pos += len(m2.group(0))
                    out.append(("NOT IN", "not in"))
                else:
                    self.pos = save
                    out.append(("IDENT", word))
            else:
                out.append(("IDENT", word))
        out.append(("EOF", ""))
        return out

    def _string(self) -> str:
        quote = self.text[self.pos]
        self.pos += 1
        chars = []
        while self.pos < len(self.text):
            c = self.text[self.pos]
            self.pos += 1
            if c == quote:
                return "".join(chars)
            if c == "\\" and self.pos < len(self.text):
                chars.append(self.text[self.pos])
                self.pos += 1
            else:
                chars.append(c)
        raise InvalidMarker("unterminated string")


class _MarkerParser:
    def __init__(self, text: str):
        self.tokens = _MarkerTokenizer(text).tokens()
        self.pos = 0

    def parse(self):
        node = self._parse_or()
        if self._peek()[0] != "EOF":
            raise InvalidMarker("trailing marker input")
        return node

    def _peek(self):
        return self.tokens[self.pos]

    def _accept(self, *kinds):
        if self._peek()[0] in kinds:
            tok = self._peek()
            self.pos += 1
            return tok
        return None

    def _expect(self, *kinds):
        tok = self._accept(*kinds)
        if not tok:
            raise InvalidMarker("invalid marker syntax")
        return tok

    def _parse_or(self):
        node = self._parse_and()
        while self._accept("OR"):
            node = ("or", node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_atom()
        while self._accept("AND"):
            node = ("and", node, self._parse_atom())
        return node

    def _parse_atom(self):
        if self._accept("("):
            node = self._parse_or()
            self._expect(")")
            return node
        left = self._parse_value()
        op = self._expect("OP", "IN", "NOT IN")[1]
        right = self._parse_value()
        return ("cmp", left, op, right)

    def _parse_value(self):
        tok = self._expect("IDENT", "STRING")
        if tok[0] == "STRING":
            return ("str", tok[1])
        name = tok[1].lower()
        if name not in _MARKER_VARIABLES:
            raise InvalidMarker("unknown marker variable")
        return ("var", name)


def _normalize_extra_value(value: str) -> str:
    try:
        return _normalize_name(value)
    except ValueError:
        return value.replace("_", "-").lower()


def _node_uses_extra(node) -> bool:
    if node[0] == "cmp":
        return node[1] == ("var", "extra") or node[3] == ("var", "extra")
    return _node_uses_extra(node[1]) or _node_uses_extra(node[2])


def _serialize_marker_value(value):
    if value[0] == "var":
        return value[1]
    return "'" + value[1].replace("\\", "\\\\").replace("'", "\\'") + "'"


def _serialize_marker_cmp(left, op, right):
    if left == ("var", "extra") and right[0] == "str":
        right = ("str", _normalize_extra_value(right[1]))
    if right == ("var", "extra") and left[0] == "str":
        left = ("str", _normalize_extra_value(left[1]))
    return f"{_serialize_marker_value(left)} {op} {_serialize_marker_value(right)}"


def _serialize_marker(node, parent_prec=0):
    if node[0] == "cmp":
        s = _serialize_marker_cmp(node[1], node[2], node[3])
        prec = 3
    elif node[0] == "and":
        s = f"{_serialize_marker(node[1], 2)} and {_serialize_marker(node[2], 2)}"
        prec = 2
    else:
        s = f"{_serialize_marker(node[1], 1)} or {_serialize_marker(node[2], 1)}"
        prec = 1
    if prec < parent_prec:
        return f"({s})"
    return s


def _marker_value(value, env):
    if value[0] == "str":
        return value[1]
    name = value[1]
    if name not in env:
        raise UndefinedEnvironmentName("undefined marker environment name")
    return env[name]


def _compare_marker_values(left: str, op: str, right: str) -> bool:
    if op in {"==", "!="}:
        result = left == right
        return result if op == "==" else not result
    if op == "in":
        return left in right
    if op == "not in":
        return left not in right
    try:
        lv = Version(left)
        rv = Version(right)
        if op == "<":
            return lv < rv
        if op == "<=":
            return lv <= rv
        if op == ">":
            return lv > rv
        if op == ">=":
            return lv >= rv
    except InvalidVersion:
        pass
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    raise InvalidMarker("unknown marker operator")


def _eval_marker_node(node, env):
    if node[0] == "and":
        return _eval_marker_node(node[1], env) and _eval_marker_node(node[2], env)
    if node[0] == "or":
        return _eval_marker_node(node[1], env) or _eval_marker_node(node[2], env)
    left = _marker_value(node[1], env)
    right = _marker_value(node[3], env)
    if node[1] == ("var", "extra"):
        left = _normalize_extra_value(left)
    if node[3] == ("var", "extra"):
        right = _normalize_extra_value(right)
    if node[1] == ("var", "extra") and node[3][0] == "str":
        right = _normalize_extra_value(right)
    if node[3] == ("var", "extra") and node[1][0] == "str":
        left = _normalize_extra_value(left)
    return _compare_marker_values(str(left), node[2], str(right))


class Marker:
    def __init__(self, text: str):
        text = str(text).strip()
        if not text:
            raise InvalidMarker("empty marker")
        self._node = _MarkerParser(text).parse()

    def evaluate(self, environment=None, requested_extras=None) -> bool:
        env = default_environment() if environment is None else dict(environment)
        for key, value in list(env.items()):
            if key not in _MARKER_VARIABLES:
                continue
            env[key] = str(value)

        extras = [_normalize_extra_value(e) for e in (requested_extras or [])]
        if _node_uses_extra(self._node):
            if not extras:
                trial = dict(env)
                trial["extra"] = ""
                return _eval_marker_node(self._node, trial)
            for extra in extras:
                trial = dict(env)
                trial["extra"] = extra
                if _eval_marker_node(self._node, trial):
                    return True
            return False
        return _eval_marker_node(self._node, env)

    def __str__(self):
        return _serialize_marker(self._node)

    def __repr__(self):
        return f"<Marker(\"{self}\")>"


def default_environment() -> dict[str, str]:
    implementation_version = platform.python_version()
    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_full_version": platform.python_version(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": getattr(sys.implementation, "name", platform.python_implementation().lower()),
        "implementation_version": implementation_version,
    }


class Requirement:
    def __init__(self, text: str):
        original = str(text)
        req_part, marker_part = _split_once_unquoted(original, ";")
        req_part = req_part.strip()
        if not req_part:
            raise InvalidRequirement("empty requirement")

        self.marker = None
        if marker_part is not None:
            try:
                self.marker = Marker(marker_part.strip())
            except InvalidMarker as exc:
                raise InvalidRequirement("invalid marker") from exc

        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]|[A-Za-z0-9])(.*)$", req_part, re.S)
        if not m:
            raise InvalidRequirement("invalid requirement name")
        try:
            self.name = _normalize_name(m.group(1))
        except ValueError as exc:
            raise InvalidRequirement("invalid requirement name") from exc

        rest = m.group(2).strip()
        self.extras = set()
        if rest.startswith("["):
            end = rest.find("]")
            if end < 0:
                raise InvalidRequirement("unterminated extras")
            extras_text = rest[1:end].strip()
            if not extras_text:
                raise InvalidRequirement("empty extras")
            for extra in extras_text.split(","):
                extra = extra.strip()
                try:
                    self.extras.add(_normalize_name(extra))
                except ValueError as exc:
                    raise InvalidRequirement("invalid extra") from exc
            rest = rest[end + 1 :].strip()

        self.url = None
        spec_text = ""
        if rest.startswith("@"):
            rest = rest[1:].strip()
            if not rest:
                raise InvalidRequirement("empty direct URL")
            self.url = rest
        else:
            if rest.startswith("(") and rest.endswith(")"):
                rest = rest[1:-1].strip()
            spec_text = rest

        if self.url is not None and spec_text:
            raise InvalidRequirement("url and specifier are mutually exclusive")
        try:
            self.specifier = SpecifierSet(spec_text)
        except InvalidSpecifier as exc:
            raise InvalidRequirement("invalid specifier") from exc
        if self.url is None and spec_text and not str(self.specifier):
            raise InvalidRequirement("invalid specifier")

    def __str__(self):
        parts = [self.name]
        if self.extras:
            parts.append("[" + ",".join(sorted(self.extras)) + "]")
        if self.url is not None:
            parts.append(f" @ {self.url}")
        elif str(self.specifier):
            parts.append(str(self.specifier))
        if self.marker is not None:
            parts.append(f"; {self.marker}")
        return "".join(parts)

    def __repr__(self):
        return f"<Requirement('{self}')>"


def _split_once_unquoted(text: str, sep: str):
    quote = None
    escape = False
    for i, c in enumerate(text):
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if quote:
            if c == quote:
                quote = None
            continue
        if c in "\"'":
            quote = c
            continue
        if c == sep:
            return text[:i], text[i + 1 :]
    return text, None


def is_requirement_satisfied(
    requirement,
    installed_version,
    environment=None,
    requested_extras=None,
    prereleases=None,
) -> bool:
    req = requirement if isinstance(requirement, Requirement) else Requirement(requirement)
    version = Version(installed_version)
    if req.marker is not None and not req.marker.evaluate(environment, requested_extras):
        return True
    return req.specifier.contains(version, prereleases=prereleases)


__all__ = [
    "Version",
    "InvalidVersion",
    "SpecifierSet",
    "InvalidSpecifier",
    "Requirement",
    "InvalidRequirement",
    "Marker",
    "InvalidMarker",
    "UndefinedEnvironmentName",
    "default_environment",
    "is_requirement_satisfied",
]
