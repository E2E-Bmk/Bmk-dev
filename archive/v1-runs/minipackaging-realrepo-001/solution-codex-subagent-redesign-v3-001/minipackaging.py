"""A compact, dependency-free subset of Python packaging metadata tools."""

from __future__ import annotations

import functools
import os
import platform
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


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
_PRE_TAGS = {
    "a": "a",
    "alpha": "a",
    "b": "b",
    "beta": "b",
    "rc": "rc",
    "c": "rc",
    "pre": "rc",
    "preview": "rc",
}
_POST_TAGS = {"post", "rev", "r"}
_PRE_ORDER = {"a": 0, "b": 1, "rc": 2}


def _canonical_name(text: str) -> str:
    text = str(text)
    if not _NAME_RE.match(text):
        raise ValueError("invalid name")
    return re.sub(r"[-_.]+", "-", text).lower()


def _split_quoted(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    quote: str | None = None
    start = 0
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == sep:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


@functools.total_ordering
class Version:
    """Supported PEP 440-style version object."""

    def __init__(self, text: str | "Version"):
        if isinstance(text, Version):
            self._copy_from(text)
            return
        original = str(text)
        s = original.strip().lower()
        if not s:
            raise InvalidVersion(original)

        main, plus, local_text = s.partition("+")
        if plus and not local_text:
            raise InvalidVersion(original)
        if "+" in local_text:
            raise InvalidVersion(original)

        epoch = 0
        if "!" in main:
            epoch_text, main = main.split("!", 1)
            if not epoch_text.isdigit() or not main:
                raise InvalidVersion(original)
            epoch = int(epoch_text)

        m = re.match(r"^(\d+(?:\.\d+)*)", main)
        if not m:
            raise InvalidVersion(original)
        raw_release = tuple(int(p) for p in m.group(1).split("."))
        rest = main[m.end() :]

        pre: tuple[str, int] | None = None
        post: int | None = None
        dev: int | None = None
        while rest:
            matched = False
            for kind, pattern in (
                ("pre", r"^[._-]?(a|alpha|b|beta|rc|c|pre|preview)[._-]?(\d*)"),
                ("post", r"^[._-]?(post|rev|r)[._-]?(\d*)"),
                ("dev", r"^[._-]?dev[._-]?(\d*)"),
            ):
                mm = re.match(pattern, rest, re.I)
                if not mm:
                    continue
                if kind == "pre":
                    if pre is not None or post is not None:
                        raise InvalidVersion(original)
                    pre = (_PRE_TAGS[mm.group(1).lower()], int(mm.group(2) or 0))
                elif kind == "post":
                    if post is not None:
                        raise InvalidVersion(original)
                    post = int(mm.group(2) or 0)
                else:
                    if dev is not None:
                        raise InvalidVersion(original)
                    dev = int(mm.group(1) or 0)
                rest = rest[mm.end() :]
                matched = True
                break
            if not matched:
                raise InvalidVersion(original)

        local: tuple[int | str, ...] = ()
        if plus:
            parts = re.split(r"[._-]", local_text)
            if any(not p or not re.match(r"^[a-z0-9]+$", p) for p in parts):
                raise InvalidVersion(original)
            local = tuple(int(p) if p.isdigit() else p for p in parts)

        release = self._trim_release(raw_release)
        self.epoch = epoch
        self.release = release
        self._raw_release = raw_release
        self.pre = pre
        self.post = post
        self.dev = dev
        self.local = local
        self._str = self._format()

    @staticmethod
    def _trim_release(release: tuple[int, ...]) -> tuple[int, ...]:
        items = list(release)
        while len(items) > 1 and items[-1] == 0:
            items.pop()
        return tuple(items)

    def _copy_from(self, other: "Version") -> None:
        self.epoch = other.epoch
        self.release = other.release
        self._raw_release = other._raw_release
        self.pre = other.pre
        self.post = other.post
        self.dev = other.dev
        self.local = other.local
        self._str = other._str

    @property
    def is_prerelease(self) -> bool:
        return self.pre is not None or self.dev is not None

    def _public_key(self) -> tuple[Any, ...]:
        return (self.epoch, self.release, self.pre, self.post, self.dev)

    def _phase_key(self) -> tuple[Any, ...]:
        if self.pre is not None:
            if self.post is not None:
                dev_part = (0, self.dev) if self.dev is not None else (1,)
                return (1, _PRE_ORDER[self.pre[0]], self.pre[1], 2, self.post, *dev_part)
            dev_part = (0, self.dev) if self.dev is not None else (1,)
            return (1, _PRE_ORDER[self.pre[0]], self.pre[1], *dev_part)
        if self.post is not None:
            dev_part = (0, self.dev) if self.dev is not None else (1,)
            return (3, self.post, *dev_part)
        if self.dev is not None:
            return (0, self.dev)
        return (2,)

    @staticmethod
    def _cmp_release(left: tuple[int, ...], right: tuple[int, ...]) -> int:
        size = max(len(left), len(right))
        lpad = left + (0,) * (size - len(left))
        rpad = right + (0,) * (size - len(right))
        return (lpad > rpad) - (lpad < rpad)

    @staticmethod
    def _local_key(local: tuple[int | str, ...]) -> tuple[Any, ...]:
        if not local:
            return ((-1, ""),)
        out = []
        for item in local:
            if isinstance(item, int):
                out.append((1, item))
            else:
                out.append((0, item))
        return tuple(out)

    def _compare(self, other: str | "Version", *, ignore_local: bool = False) -> int:
        other = other if isinstance(other, Version) else Version(other)
        if self.epoch != other.epoch:
            return (self.epoch > other.epoch) - (self.epoch < other.epoch)
        rel = self._cmp_release(self.release, other.release)
        if rel:
            return rel
        lphase, rphase = self._phase_key(), other._phase_key()
        if lphase != rphase:
            return (lphase > rphase) - (lphase < rphase)
        if ignore_local:
            return 0
        llocal, rlocal = self._local_key(self.local), self._local_key(other.local)
        return (llocal > rlocal) - (llocal < rlocal)

    def public_equals(self, other: str | "Version") -> bool:
        return self._compare(other, ignore_local=True) == 0

    def _format(self) -> str:
        parts = []
        if self.epoch:
            parts.append(f"{self.epoch}!")
        parts.append(".".join(str(x) for x in self.release))
        if self.pre is not None:
            parts.append(f"{self.pre[0]}{self.pre[1]}")
        if self.post is not None:
            parts.append(f".post{self.post}")
        if self.dev is not None:
            parts.append(f".dev{self.dev}")
        if self.local:
            local = ".".join(str(x) for x in self.local)
            parts.append(f"+{local}")
        return "".join(parts)

    def __str__(self) -> str:
        return self._str

    def __repr__(self) -> str:
        return f"Version({self._str!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Version, str)):
            return NotImplemented
        try:
            return self._compare(other) == 0
        except InvalidVersion:
            return False

    def __lt__(self, other: str | "Version") -> bool:
        return self._compare(other) < 0

    def __hash__(self) -> int:
        return hash((self.epoch, self.release, self._phase_key(), self.local))


@dataclass(frozen=True)
class _Clause:
    op: str
    version: Version | None = None
    wildcard: tuple[int, ...] | None = None
    raw_release_len: int = 0

    def __str__(self) -> str:
        if self.wildcard is not None:
            return f"{self.op}{'.'.join(str(x) for x in self.wildcard)}.*"
        if self.op == "~=":
            return f"{self.op}{self._format_compatible_version()}"
        return f"{self.op}{self.version}"

    def _format_compatible_version(self) -> str:
        assert self.version is not None
        parts = []
        if self.version.epoch:
            parts.append(f"{self.version.epoch}!")
        parts.append(".".join(str(x) for x in self.version._raw_release))
        if self.version.pre is not None:
            parts.append(f"{self.version.pre[0]}{self.version.pre[1]}")
        if self.version.post is not None:
            parts.append(f".post{self.version.post}")
        if self.version.dev is not None:
            parts.append(f".dev{self.version.dev}")
        if self.version.local:
            parts.append("+" + ".".join(str(x) for x in self.version.local))
        return "".join(parts)

    def key(self) -> tuple[Any, ...]:
        if self.wildcard is not None:
            return (self.op, "wildcard", self.wildcard)
        assert self.version is not None
        return (
            self.op,
            self.version.epoch,
            self.version.release,
            self.version.pre,
            self.version.post,
            self.version.dev,
            self.version.local,
            self.raw_release_len if self.op == "~=" else None,
        )


class SpecifierSet:
    def __init__(self, text: str | "SpecifierSet" = ""):
        if isinstance(text, SpecifierSet):
            self._clauses = list(text._clauses)
            return
        self._clauses: list[_Clause] = []
        s = str(text).strip()
        if not s:
            return
        for part in s.split(","):
            clause = part.strip()
            if not clause:
                raise InvalidSpecifier(text)
            m = re.match(r"^(===|~=|==|!=|<=|>=|<|>)\s*(\S+)$", clause)
            if not m or m.group(1) == "===":
                raise InvalidSpecifier(text)
            op, version_text = m.group(1), m.group(2)
            if version_text.endswith(".*"):
                if op not in {"==", "!="}:
                    raise InvalidSpecifier(text)
                prefix_text = version_text[:-2]
                if not re.match(r"^\d+(?:\.\d+)*$", prefix_text):
                    raise InvalidSpecifier(text)
                prefix = tuple(int(p) for p in prefix_text.split("."))
                self._clauses.append(_Clause(op, wildcard=prefix))
                continue
            try:
                version = Version(version_text)
            except InvalidVersion as exc:
                raise InvalidSpecifier(text) from exc
            if op == "~=" and len(version._raw_release) < 2:
                raise InvalidSpecifier(text)
            self._clauses.append(_Clause(op, version=version, raw_release_len=len(version._raw_release)))

    def __str__(self) -> str:
        return ",".join(str(c) for c in self._clauses)

    def __repr__(self) -> str:
        return f"SpecifierSet({str(self)!r})"

    def _has_prerelease_clause(self) -> bool:
        return any(c.version is not None and c.version.is_prerelease for c in self._clauses)

    def _compatible_upper(self, clause: _Clause) -> Version:
        assert clause.version is not None
        parts = list(clause.version._raw_release)
        if len(parts) == 2:
            upper = [parts[0] + 1]
        else:
            upper = parts[:]
            upper[-2] += 1
            upper = upper[:-1]
        return Version(".".join(str(x) for x in upper))

    @staticmethod
    def _release_prefix(version: Version, prefix: tuple[int, ...]) -> bool:
        release = version.release + (0,) * max(0, len(prefix) - len(version.release))
        return release[: len(prefix)] == prefix

    @staticmethod
    def _cmp_for_spec(candidate: Version, spec_version: Version) -> int:
        ignore_local = not spec_version.local
        return candidate._compare(spec_version, ignore_local=ignore_local)

    def _match_clause(self, candidate: Version, clause: _Clause) -> bool:
        if clause.wildcard is not None:
            matched = self._release_prefix(candidate, clause.wildcard)
            return matched if clause.op == "==" else not matched
        assert clause.version is not None
        cmp = self._cmp_for_spec(candidate, clause.version)
        if clause.op == "==":
            return cmp == 0
        if clause.op == "!=":
            return cmp != 0
        if clause.op == ">=":
            return cmp >= 0
        if clause.op == "<=":
            return cmp <= 0
        if clause.op == ">":
            return cmp > 0
        if clause.op == "<":
            return cmp < 0
        if clause.op == "~=":
            return cmp >= 0 and candidate._compare(self._compatible_upper(clause), ignore_local=True) < 0
        raise AssertionError(clause.op)

    def contains(self, version: str | Version, prereleases: bool | None = None) -> bool:
        candidate = version if isinstance(version, Version) else Version(version)
        if candidate.is_prerelease:
            if prereleases is False:
                return False
            if prereleases is None and not self._has_prerelease_clause():
                return False
        return all(self._match_clause(candidate, c) for c in self._clauses)

    def semantic_key(self) -> tuple[Any, ...]:
        return tuple(sorted({c.key() for c in self._clauses}))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpecifierSet):
            try:
                other = SpecifierSet(str(other))
            except Exception:
                return False
        return self.semantic_key() == other.semantic_key()

    def __hash__(self) -> int:
        return hash(self.semantic_key())


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
_VERSION_MARKER_VARIABLES = {
    "python_version",
    "python_full_version",
    "implementation_version",
    "platform_release",
    "platform_version",
}


@dataclass(frozen=True)
class _MarkerValue:
    kind: str
    value: str


@dataclass(frozen=True)
class _MarkerCompare:
    left: Any
    op: str
    right: Any


@dataclass(frozen=True)
class _MarkerBool:
    op: str
    items: tuple[Any, ...]


class _MarkerParser:
    def __init__(self, text: str):
        self.text = text
        self.tokens = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch.isspace():
                i += 1
                continue
            if ch in "()":
                out.append((ch, ch))
                i += 1
                continue
            if ch in "'\"":
                quote = ch
                j = i + 1
                value = []
                while j < len(text) and text[j] != quote:
                    value.append(text[j])
                    j += 1
                if j >= len(text):
                    raise InvalidMarker(text)
                out.append(("STRING", "".join(value)))
                i = j + 1
                continue
            for op in ("<=", ">=", "==", "!=", "<", ">"):
                if text.startswith(op, i):
                    out.append(("OP", op))
                    i += len(op)
                    break
            else:
                m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i:])
                if not m:
                    raise InvalidMarker(text)
                word = m.group(0)
                low = word.lower()
                if low == "not":
                    rest = text[i + len(word) :]
                    mm = re.match(r"\s+in\b", rest, re.I)
                    if not mm:
                        raise InvalidMarker(text)
                    out.append(("OP", "not in"))
                    i += len(word) + mm.end()
                elif low == "in":
                    out.append(("OP", "in"))
                    i += len(word)
                elif low in {"and", "or"}:
                    out.append((low.upper(), low))
                    i += len(word)
                else:
                    out.append(("IDENT", low))
                    i += len(word)
        return out

    def peek(self) -> tuple[str, str] | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def accept(self, typ: str, value: str | None = None) -> str | None:
        tok = self.peek()
        if tok and tok[0] == typ and (value is None or tok[1] == value):
            self.pos += 1
            return tok[1]
        return None

    def expect(self, typ: str) -> str:
        tok = self.peek()
        if not tok or tok[0] != typ:
            raise InvalidMarker(self.text)
        self.pos += 1
        return tok[1]

    def parse(self) -> Any:
        expr = self.parse_or()
        if self.peek() is not None:
            raise InvalidMarker(self.text)
        return expr

    def parse_or(self) -> Any:
        items = [self.parse_and()]
        while self.accept("OR") is not None:
            items.append(self.parse_and())
        return items[0] if len(items) == 1 else _MarkerBool("or", tuple(items))

    def parse_and(self) -> Any:
        items = [self.parse_atom()]
        while self.accept("AND") is not None:
            items.append(self.parse_atom())
        return items[0] if len(items) == 1 else _MarkerBool("and", tuple(items))

    def parse_atom(self) -> Any:
        if self.accept("(") is not None:
            expr = self.parse_or()
            if self.accept(")") is None:
                raise InvalidMarker(self.text)
            return expr
        left = self.parse_value()
        op = self.expect("OP")
        right = self.parse_value()
        return _MarkerCompare(left, op, right)

    def parse_value(self) -> _MarkerValue:
        tok = self.peek()
        if not tok:
            raise InvalidMarker(self.text)
        if tok[0] == "IDENT":
            self.pos += 1
            if tok[1] not in _MARKER_VARIABLES:
                raise InvalidMarker(self.text)
            return _MarkerValue("var", tok[1])
        if tok[0] == "STRING":
            self.pos += 1
            return _MarkerValue("str", tok[1])
        raise InvalidMarker(self.text)


class Marker:
    def __init__(self, text: str | "Marker"):
        if isinstance(text, Marker):
            self._ast = text._ast
            self._str = text._str
            self._uses_extra = text._uses_extra
            return
        s = str(text).strip()
        if not s:
            raise InvalidMarker(text)
        self._ast = _MarkerParser(s).parse()
        self._uses_extra = self._contains_extra(self._ast)
        self._str = self._format(self._ast, 0)

    def _contains_extra(self, node: Any) -> bool:
        if isinstance(node, _MarkerValue):
            return node.kind == "var" and node.value == "extra"
        if isinstance(node, _MarkerCompare):
            return self._contains_extra(node.left) or self._contains_extra(node.right)
        if isinstance(node, _MarkerBool):
            return any(self._contains_extra(i) for i in node.items)
        return False

    def _format_value(self, value: _MarkerValue, other: _MarkerValue | None = None) -> str:
        if value.kind == "var":
            return value.value
        lit = value.value
        if other and other.kind == "var" and other.value == "extra":
            try:
                lit = _canonical_name(lit)
            except ValueError:
                lit = lit.lower()
        return repr(lit)

    def _format(self, node: Any, parent_prec: int) -> str:
        if isinstance(node, _MarkerCompare):
            return f"{self._format_value(node.left, node.right)} {node.op} {self._format_value(node.right, node.left)}"
        if isinstance(node, _MarkerBool):
            prec = 1 if node.op == "or" else 2
            text = f" {node.op} ".join(self._format(item, prec) for item in node.items)
            if prec < parent_prec:
                return f"({text})"
            return text
        raise AssertionError(node)

    def __str__(self) -> str:
        return self._str

    def __repr__(self) -> str:
        return f"Marker({self._str!r})"

    def _value(self, value: _MarkerValue, env: Mapping[str, str]) -> tuple[str, str | None]:
        if value.kind == "str":
            return value.value, None
        if value.value == "extra":
            return env.get("extra", ""), "extra"
        if value.value not in env:
            raise UndefinedEnvironmentName(value.value)
        return env[value.value], value.value

    def _compare(self, left: _MarkerValue, op: str, right: _MarkerValue, env: Mapping[str, str]) -> bool:
        lval, lvar = self._value(left, env)
        rval, rvar = self._value(right, env)
        extra_cmp = lvar == "extra" or rvar == "extra"
        if extra_cmp:
            lval_norm = _canonical_name(lval) if lval else ""
            if op in {"in", "not in"} and rvar != "extra":
                choices = [_canonical_name(p.strip()) for p in re.split(r"[, ]+", rval) if p.strip()]
                result = lval_norm in choices if choices else lval_norm in rval.lower()
            else:
                rval_norm = _canonical_name(rval) if rval else ""
                result = lval_norm == rval_norm
                if op == "!=":
                    return not result
                if op not in {"==", "!="}:
                    result = lval_norm in rval_norm if op == "in" else lval_norm not in rval_norm
            if op == "not in":
                return not result
            if op == "!=":
                return not result
            return result

        if op in {"<", "<=", ">", ">=", "==", "!="} and (
            lvar in _VERSION_MARKER_VARIABLES or rvar in _VERSION_MARKER_VARIABLES
        ):
            try:
                lv = Version(lval)
                rv = Version(rval)
                cmp = lv._compare(rv)
                result = {
                    "<": cmp < 0,
                    "<=": cmp <= 0,
                    ">": cmp > 0,
                    ">=": cmp >= 0,
                    "==": cmp == 0,
                    "!=": cmp != 0,
                }[op]
                return result
            except InvalidVersion:
                pass
        if op == "==":
            return lval == rval
        if op == "!=":
            return lval != rval
        if op == "<":
            return lval < rval
        if op == "<=":
            return lval <= rval
        if op == ">":
            return lval > rval
        if op == ">=":
            return lval >= rval
        if op == "in":
            return lval in rval
        if op == "not in":
            return lval not in rval
        raise AssertionError(op)

    def _eval(self, node: Any, env: Mapping[str, str]) -> bool:
        if isinstance(node, _MarkerCompare):
            return self._compare(node.left, node.op, node.right, env)
        if isinstance(node, _MarkerBool):
            if node.op == "and":
                return all(self._eval(item, env) for item in node.items)
            return any(self._eval(item, env) for item in node.items)
        raise AssertionError(node)

    def evaluate(
        self,
        environment: Mapping[str, str] | None = None,
        requested_extras: Iterable[str] | None = None,
    ) -> bool:
        env = dict(default_environment() if environment is None else environment)
        for key, value in list(env.items()):
            env[key] = str(value)
        if not self._uses_extra:
            return self._eval(self._ast, env)
        extras = [_canonical_name(e) for e in (requested_extras or [])]
        if not extras:
            env["extra"] = ""
            return self._eval(self._ast, env)
        for extra in sorted(set(extras)):
            local_env = dict(env)
            local_env["extra"] = extra
            if self._eval(self._ast, local_env):
                return True
        return False

    def semantic_key(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Marker):
            try:
                other = Marker(str(other))
            except Exception:
                return False
        return self.semantic_key() == other.semantic_key()

    def __hash__(self) -> int:
        return hash(self.semantic_key())


class Requirement:
    def __init__(self, text: str | "Requirement"):
        if isinstance(text, Requirement):
            self.name = text.name
            self.extras = set(text.extras)
            self.specifier = SpecifierSet(text.specifier)
            self.url = text.url
            self.marker = Marker(text.marker) if text.marker is not None else None
            return
        original = str(text)
        left, marker_text = self._split_marker(original)
        left = left.strip()
        if not left:
            raise InvalidRequirement(original)

        m = re.match(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)", left)
        if not m:
            raise InvalidRequirement(original)
        try:
            self.name = _canonical_name(m.group(1))
        except ValueError as exc:
            raise InvalidRequirement(original) from exc
        rest = left[m.end() :].strip()

        self.extras: set[str] = set()
        if rest.startswith("["):
            end = rest.find("]")
            if end == -1:
                raise InvalidRequirement(original)
            extras_text = rest[1:end].strip()
            if not extras_text:
                raise InvalidRequirement(original)
            for extra in extras_text.split(","):
                try:
                    self.extras.add(_canonical_name(extra.strip()))
                except ValueError as exc:
                    raise InvalidRequirement(original) from exc
            rest = rest[end + 1 :].strip()

        self.url: str | None = None
        self.specifier = SpecifierSet("")
        if rest:
            if rest.startswith("@"):
                self.url = rest[1:].strip()
                if not self.url:
                    raise InvalidRequirement(original)
                if re.search(r"\s(~=|==|!=|<=|>=|<|>)\s*\S+", self.url):
                    raise InvalidRequirement(original)
            else:
                if "@" in rest:
                    raise InvalidRequirement(original)
                if rest.startswith("(") and rest.endswith(")"):
                    rest = rest[1:-1].strip()
                try:
                    self.specifier = SpecifierSet(rest)
                except InvalidSpecifier as exc:
                    raise InvalidRequirement(original) from exc

        self.marker = None
        if marker_text is not None:
            try:
                self.marker = Marker(marker_text)
            except InvalidMarker as exc:
                raise InvalidRequirement(original) from exc

    def _split_marker(self, text: str) -> tuple[str, str | None]:
        quote: str | None = None
        depth = 0
        for i, ch in enumerate(text):
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "'\"":
                quote = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            elif ch == ";" and depth == 0:
                return text[:i], text[i + 1 :].strip()
        return text, None

    def __str__(self) -> str:
        out = self.name
        if self.extras:
            out += "[" + ",".join(sorted(self.extras)) + "]"
        if str(self.specifier):
            out += str(self.specifier)
        if self.url is not None:
            out += f" @ {self.url}"
        if self.marker is not None:
            out += f"; {self.marker}"
        return out

    def __repr__(self) -> str:
        return f"Requirement({str(self)!r})"

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.name,
            tuple(sorted(self.extras)),
            self.specifier.semantic_key(),
            self.url,
            self.marker.semantic_key() if self.marker is not None else None,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Requirement):
            try:
                other = Requirement(str(other))
            except Exception:
                return False
        return self.semantic_key() == other.semantic_key()

    def __hash__(self) -> int:
        return hash(self.semantic_key())


def default_environment() -> dict[str, str]:
    version = sys.version_info
    return {
        "python_version": f"{version.major}.{version.minor}",
        "python_full_version": platform.python_version(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": getattr(sys.implementation, "name", platform.python_implementation().lower()),
        "implementation_version": ".".join(str(x) for x in sys.implementation.version[:3]),
    }


def is_requirement_satisfied(
    requirement: str | Requirement,
    installed_version: str | Version,
    environment: Mapping[str, str] | None = None,
    requested_extras: Iterable[str] | None = None,
    prereleases: bool | None = None,
) -> bool:
    req = requirement if isinstance(requirement, Requirement) else Requirement(requirement)
    if req.marker is not None and not req.marker.evaluate(environment, requested_extras):
        return True
    version = installed_version if isinstance(installed_version, Version) else Version(installed_version)
    return req.specifier.contains(version, prereleases=prereleases)


@dataclass(frozen=True)
class _Candidate:
    name: str
    version: Version
    requires: tuple[str, ...]
    order: int


@dataclass(frozen=True)
class _Fact:
    source: str
    parent: str | None
    req: Requirement

    def key(self) -> tuple[Any, ...]:
        return (self.source, self.parent, self.req.semantic_key())


def _requirement_applicable(
    req: Requirement,
    environment: Mapping[str, str] | None,
    requested_extras: Iterable[str] | None,
) -> bool:
    return req.marker is None or req.marker.evaluate(environment, requested_extras)


def _fact_sort_key(fact: _Fact) -> tuple[Any, ...]:
    return (
        fact.parent is not None,
        fact.source,
        fact.parent or "",
        fact.req.name,
        tuple(sorted(fact.req.extras)),
        str(fact.req.specifier),
        fact.req.url or "",
        str(fact.req.marker) if fact.req.marker else "",
    )


def _dedupe_facts(facts: Iterable[_Fact]) -> list[_Fact]:
    seen: set[tuple[Any, ...]] = set()
    out: list[_Fact] = []
    for fact in sorted(facts, key=_fact_sort_key):
        key = fact.key()
        if key not in seen:
            seen.add(key)
            out.append(fact)
    return out


def _requested_extras_from_facts(facts: Iterable[_Fact]) -> dict[str, set[str]]:
    requested: dict[str, set[str]] = {}
    for fact in facts:
        requested.setdefault(fact.req.name, set()).update(fact.req.extras)
    return requested


def _select_candidates(
    facts: Iterable[_Fact],
    candidate_map: Mapping[str, list[_Candidate]],
    prereleases: bool | None,
) -> dict[str, _Candidate]:
    by_name: dict[str, list[SpecifierSet]] = {}
    for fact in facts:
        by_name.setdefault(fact.req.name, []).append(fact.req.specifier)
    selected: dict[str, _Candidate] = {}
    for name in sorted(by_name):
        candidates = candidate_map.get(name, [])
        if not candidates:
            raise ValueError(f"no candidate for {name}")
        matches = [
            cand
            for cand in candidates
            if all(spec.contains(cand.version, prereleases=prereleases) for spec in by_name[name])
        ]
        if not matches:
            raise ValueError(f"no satisfying candidate for {name}")
        selected[name] = max(matches, key=lambda c: (c.version, -c.order))
    return selected


def resolve_metadata(
    roots: Iterable[str | Requirement],
    candidates: Iterable[Mapping[str, Any]],
    environment: Mapping[str, str] | None = None,
    requested_extras: Iterable[str] | None = None,
    prereleases: bool | None = None,
) -> dict[str, Any]:
    env = dict(default_environment() if environment is None else environment)
    top_extras = tuple(_canonical_name(e) for e in (requested_extras or ()))

    root_reqs = [r if isinstance(r, Requirement) else Requirement(r) for r in list(roots)]
    root_facts = [
        _Fact("root", None, Requirement(req))
        for req in root_reqs
        if _requirement_applicable(req, env, top_extras)
    ]

    candidate_groups: dict[str, dict[Version, tuple[int, set[str]]]] = {}
    for i, mapping in enumerate(list(candidates)):
        try:
            name = _canonical_name(str(mapping["name"]))
            version = Version(mapping["version"])
        except KeyError as exc:
            raise ValueError("candidate missing required field") from exc
        requires_value = mapping.get("requires", ())
        requires = tuple(str(r) for r in list(requires_value))
        version_groups = candidate_groups.setdefault(name, {})
        if version in version_groups:
            order, existing_requires = version_groups[version]
            existing_requires.update(requires)
            version_groups[version] = (min(order, i), existing_requires)
        else:
            version_groups[version] = (i, set(requires))

    candidate_map: dict[str, list[_Candidate]] = {}
    for name, versions in candidate_groups.items():
        candidate_map[name] = sorted(
            [
                _Candidate(name, version, tuple(sorted(requires)), order)
                for version, (order, requires) in versions.items()
            ],
            key=lambda c: (c.version, c.order),
        )

    facts = _dedupe_facts(root_facts)
    selected: dict[str, _Candidate] = {}
    for _ in range(1000):
        requested_by_name = _requested_extras_from_facts(facts)
        selected = _select_candidates(facts, candidate_map, prereleases) if facts else {}
        next_facts: list[_Fact] = list(root_facts)
        for parent in sorted(selected):
            parent_candidate = selected[parent]
            parent_extras = requested_by_name.get(parent, set())
            for requirement_text in parent_candidate.requires:
                req = Requirement(requirement_text)
                if _requirement_applicable(req, env, parent_extras):
                    next_facts.append(_Fact(parent, parent, req))
        deduped = _dedupe_facts(next_facts)
        if [f.key() for f in deduped] == [f.key() for f in facts]:
            facts = deduped
            break
        facts = deduped
    else:
        raise ValueError("metadata resolution did not converge")

    requested_by_name = _requested_extras_from_facts(facts)
    selected = _select_candidates(facts, candidate_map, prereleases) if facts else {}
    active_names = sorted({fact.req.name for fact in facts})
    selected_out = {name: str(selected[name].version) for name in sorted(selected)}

    excluded: dict[str, list[str]] = {}
    for name in active_names:
        omitted = sorted({cand.version for cand in candidate_map.get(name, []) if cand != selected.get(name)})
        if omitted:
            excluded[name] = [str(v) for v in omitted]

    def specifier_matches(req: Requirement) -> list[tuple[str, bool]]:
        versions = sorted({c.version for c in candidate_map.get(req.name, [])})
        return [(str(v), req.specifier.contains(v, prereleases=prereleases)) for v in versions]

    dep_facts = [f for f in facts if f.parent is not None]
    edges = [
        {
            "parent": fact.parent,
            "name": fact.req.name,
            "extras": sorted(fact.req.extras),
            "specifier": str(fact.req.specifier),
            "url": fact.req.url,
            "marker": str(fact.req.marker) if fact.req.marker else None,
            "marker_applicable": True,
            "specifier_matches": specifier_matches(fact.req),
        }
        for fact in sorted(dep_facts, key=_fact_sort_key)
    ]

    dependents_sets: dict[str, set[str]] = {}
    for edge in edges:
        dependents_sets.setdefault(edge["name"], set()).add(edge["parent"])
    dependents = {name: sorted(parents) for name, parents in sorted(dependents_sets.items())}

    requested_out = {
        name: sorted(requested_by_name.get(name, set()))
        for name in sorted(set(active_names) | set(selected))
    }

    requirements = [
        {
            "source": fact.source,
            "parent": fact.parent,
            "name": fact.req.name,
            "extras": sorted(fact.req.extras),
            "specifier": str(fact.req.specifier),
            "url": fact.req.url,
            "marker": str(fact.req.marker) if fact.req.marker else None,
            "marker_applicable": True,
        }
        for fact in sorted(facts, key=_fact_sort_key)
    ]

    return {
        "selected": selected_out,
        "excluded": excluded,
        "edges": edges,
        "dependents": dependents,
        "requested_extras": requested_out,
        "requirements": requirements,
    }


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
    "resolve_metadata",
]
