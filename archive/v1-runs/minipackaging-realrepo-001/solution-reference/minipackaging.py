import os
import platform
import re
import sys


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


def _norm_name(text):
    if not _NAME_RE.match(text or ""):
        raise ValueError(text)
    return text.replace("_", "-").lower()


def _trim_release(parts):
    parts = list(parts)
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


class Version:
    _base_re = re.compile(r"^\s*(?:(\d+)!)?(\d+(?:\.\d+)*)(.*)\s*$", re.I)

    def __init__(self, text):
        if isinstance(text, Version):
            self.__dict__.update(text.__dict__)
            return
        raw = str(text)
        m = self._base_re.match(raw)
        if not m:
            raise InvalidVersion(raw)
        self.epoch = int(m.group(1) or 0)
        try:
            release = tuple(int(p) for p in m.group(2).split("."))
        except ValueError as exc:
            raise InvalidVersion(raw) from exc
        self.release = _trim_release(release)
        rest = m.group(3) or ""
        self.dev = None
        self.pre = None
        self.post = None
        self.local = None

        if "+" in rest:
            rest, local = rest.split("+", 1)
            if not local:
                raise InvalidVersion(raw)
            bits = re.split(r"[._-]", local.lower())
            if any(not b or not re.match(r"^[a-z0-9]+$", b) for b in bits):
                raise InvalidVersion(raw)
            self.local = tuple(int(b) if b.isdigit() else b for b in bits)

        rest = rest.strip()
        while rest:
            low = rest.lower()
            if low.startswith("."):
                rest = rest[1:]
                continue
            m = re.match(r"^-?(?:post|rev|r)(\d+)$", low)
            if m and self.post is None:
                self.post = int(m.group(1))
                rest = ""
                continue
            m = re.match(r"^\.?(?:dev)(\d+)$", low)
            if m and self.dev is None:
                self.dev = int(m.group(1))
                rest = ""
                continue
            m = re.match(r"^-?(a|alpha|b|beta|rc|c|pre|preview)(\d+)$", low)
            if m and self.pre is None:
                tag = m.group(1)
                tag = "a" if tag in {"a", "alpha"} else "b" if tag in {"b", "beta"} else "rc"
                self.pre = (tag, int(m.group(2)))
                rest = ""
                continue
            raise InvalidVersion(raw)

    def _stage(self):
        if self.dev is not None:
            return (0, self.dev)
        if self.pre is not None:
            order = {"a": 1, "b": 2, "rc": 3}
            return (order[self.pre[0]], self.pre[1])
        if self.post is not None:
            return (5, self.post)
        return (4, 0)

    def _release_cmp(self):
        return self.release

    def _local_key(self):
        if self.local is None:
            return ()
        key = []
        for part in self.local:
            if isinstance(part, int):
                key.append((1, part))
            else:
                key.append((0, part))
        return tuple(key)

    def _key(self):
        return (self.epoch, self._release_cmp(), self._stage(), self._local_key())

    def __str__(self):
        release = ".".join(str(p) for p in self.release)
        out = f"{self.epoch}!" if self.epoch else ""
        out += release
        if self.dev is not None:
            out += f".dev{self.dev}"
        if self.pre is not None:
            out += f"{self.pre[0]}{self.pre[1]}"
        if self.post is not None:
            out += f".post{self.post}"
        if self.local is not None:
            out += "+" + ".".join(str(p) for p in self.local)
        return out

    def __repr__(self):
        return f"Version({str(self)!r})"

    def __eq__(self, other):
        try:
            other = Version(other)
        except InvalidVersion:
            return False
        return self._key() == other._key()

    def __lt__(self, other):
        other = Version(other)
        a_rel, b_rel = list(self.release), list(other.release)
        n = max(len(a_rel), len(b_rel))
        a_rel += [0] * (n - len(a_rel))
        b_rel += [0] * (n - len(b_rel))
        return (self.epoch, tuple(a_rel), self._stage(), self._local_key()) < (
            other.epoch,
            tuple(b_rel),
            other._stage(),
            other._local_key(),
        )

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    def __hash__(self):
        return hash(self._key())

    @property
    def is_prerelease(self):
        return self.dev is not None or self.pre is not None


class SpecifierSet:
    _clause_re = re.compile(r"^(==|!=|>=|<=|>|<|~=)\s*(.+)$")

    def __init__(self, text=""):
        self._clauses = []
        text = str(text or "").strip()
        if not text:
            return
        for raw in text.split(","):
            raw = raw.strip()
            if not raw:
                raise InvalidSpecifier(text)
            m = self._clause_re.match(raw)
            if not m:
                raise InvalidSpecifier(text)
            op, value = m.group(1), m.group(2).strip()
            if op in {"==", "!="} and value.endswith(".*"):
                prefix = value[:-2]
                if not prefix or "*" in prefix:
                    raise InvalidSpecifier(text)
                parts = prefix.split(".")
                if any(not p.isdigit() for p in parts):
                    raise InvalidSpecifier(text)
                self._clauses.append((op, tuple(int(p) for p in parts), True))
            else:
                if "*" in value:
                    raise InvalidSpecifier(text)
                try:
                    self._clauses.append((op, Version(value), False))
                except InvalidVersion as exc:
                    raise InvalidSpecifier(text) from exc

    def __str__(self):
        out = []
        for op, value, wildcard in self._clauses:
            if wildcard:
                out.append(op + ".".join(str(p) for p in value) + ".*")
            else:
                out.append(op + str(value))
        return ",".join(out)

    def _compatible_upper(self, v):
        rel = list(v.release)
        if len(rel) <= 2:
            return Version(str(rel[0] + 1))
        return Version(".".join(str(x) for x in [rel[0], rel[1] + 1]))

    def contains(self, version, prereleases=None):
        v = Version(version)
        if v.is_prerelease and prereleases is not True:
            return False
        for op, target, wildcard in self._clauses:
            if wildcard:
                rel = list(v.release)
                prefix = list(target)
                ok = tuple(rel[: len(prefix)]) == tuple(prefix)
                if op == "==" and not ok:
                    return False
                if op == "!=" and ok:
                    return False
                continue
            if op == "==" and not (v == target):
                return False
            if op == "!=" and not (v != target):
                return False
            if op == ">=" and not (v >= target):
                return False
            if op == "<=" and not (v <= target):
                return False
            if op == ">" and not (v > target):
                return False
            if op == "<" and not (v < target):
                return False
            if op == "~=" and not (v >= target and v < self._compatible_upper(target)):
                return False
        return True

    def _semantic_key(self):
        key = []
        for op, value, wildcard in self._clauses:
            rendered = tuple(value) if wildcard else str(value)
            key.append((op, rendered, wildcard))
        return tuple(sorted(key))

    def __eq__(self, other):
        try:
            other = SpecifierSet(str(other)) if not isinstance(other, SpecifierSet) else other
        except InvalidSpecifier:
            return False
        return self._semantic_key() == other._semantic_key()

    def __hash__(self):
        return hash(self._semantic_key())


class Marker:
    _token_re = re.compile(
        r"\s*(not\s+in|==|!=|<=|>=|<|>|in|and|or|\(|\)|[A-Za-z_][A-Za-z0-9_]*|'[^']*'|\"[^\"]*\")",
        re.I,
    )
    _vars = {
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

    def __init__(self, text):
        self.text = str(text).strip()
        self.tokens = self._tokenize(self.text)
        self.pos = 0
        self.ast = self._parse_or()
        if self.pos != len(self.tokens):
            raise InvalidMarker(text)

    def _tokenize(self, text):
        out = []
        i = 0
        while i < len(text):
            m = self._token_re.match(text, i)
            if not m:
                raise InvalidMarker(text)
            tok = m.group(1)
            i = m.end()
            if tok.lower() in {"and", "or", "in", "not in"}:
                tok = tok.lower()
            out.append(tok)
        return out

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _eat(self, tok=None):
        cur = self._peek()
        if cur is None or (tok is not None and cur != tok):
            raise InvalidMarker(self.text)
        self.pos += 1
        return cur

    def _parse_or(self):
        node = self._parse_and()
        while self._peek() == "or":
            self._eat("or")
            node = ("or", node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_atom()
        while self._peek() == "and":
            self._eat("and")
            node = ("and", node, self._parse_atom())
        return node

    def _parse_atom(self):
        if self._peek() == "(":
            self._eat("(")
            node = self._parse_or()
            self._eat(")")
            return node
        left = self._eat()
        op = self._eat()
        if op not in {"==", "!=", "<", "<=", ">", ">=", "in", "not in"}:
            raise InvalidMarker(self.text)
        right = self._eat()
        return ("cmp", left, op, right)

    def _literal(self, token):
        if token[0] in "\"'" and token[-1] == token[0]:
            return token[1:-1]
        return token

    def _eval_for_extra(self, env, extra):
        env = dict(default_environment() if env is None else env)
        env["extra"] = extra or ""

        def value(tok):
            lit = self._literal(tok)
            if lit != tok:
                return lit
            var = tok.lower()
            if var not in self._vars:
                return tok
            if var not in env:
                raise UndefinedEnvironmentName(var)
            return env[var]

        def cmp(a, op, b):
            av, bv = value(a), value(b)
            if op in {"in", "not in"}:
                res = str(av) in str(bv).split()
                return not res if op == "not in" else res
            if a.lower() == "extra" or b.lower() == "extra":
                if a.lower() == "extra":
                    bv = _norm_name(str(bv))
                    av = _norm_name(str(av)) if av else ""
                if b.lower() == "extra":
                    av = _norm_name(str(av))
                    bv = _norm_name(str(bv)) if bv else ""
            try:
                va, vb = Version(av), Version(bv)
            except InvalidVersion:
                va, vb = str(av), str(bv)
            return {
                "==": va == vb,
                "!=": va != vb,
                "<": va < vb,
                "<=": va <= vb,
                ">": va > vb,
                ">=": va >= vb,
            }[op]

        def walk(node):
            if node[0] == "and":
                return walk(node[1]) and walk(node[2])
            if node[0] == "or":
                return walk(node[1]) or walk(node[2])
            return cmp(node[1], node[2], node[3])

        return walk(self.ast)

    def evaluate(self, environment=None, requested_extras=None):
        extras = {_norm_name(e) for e in (requested_extras or [])}
        if not extras:
            return self._eval_for_extra(environment, "")
        return any(self._eval_for_extra(environment, e) for e in extras)

    def __str__(self):
        return self.text


class Requirement:
    def __init__(self, text):
        self.original = str(text).strip()
        try:
            body, marker_text = self._split_marker(self.original)
            self.marker = Marker(marker_text) if marker_text else None
            if " @ " in body:
                left, url = body.split(" @ ", 1)
                if re.search(r"\s(==|!=|>=|<=|>|<|~=)", url):
                    raise InvalidRequirement(text)
                self.url = url.strip()
                spec = ""
            else:
                self.url = None
                m = re.match(r"^([A-Za-z0-9._-]+(?:\[[^\]]*\])?)(.*)$", body)
                if not m:
                    raise InvalidRequirement(text)
                left, spec = m.group(1), m.group(2).strip()
            m = re.match(r"^([A-Za-z0-9._-]+)(?:\[([^\]]*)\])?$", left.strip())
            if not m:
                raise InvalidRequirement(text)
            self.name = _norm_name(m.group(1))
            self.extras = set()
            if m.group(2):
                for item in m.group(2).split(","):
                    self.extras.add(_norm_name(item.strip()))
            self.specifier = SpecifierSet(spec)
        except (ValueError, InvalidMarker, InvalidSpecifier) as exc:
            if isinstance(exc, InvalidRequirement):
                raise
            raise InvalidRequirement(text) from exc

    def _split_marker(self, text):
        if ";" not in text:
            return text.strip(), None
        body, marker = text.split(";", 1)
        return body.strip(), marker.strip()

    def __str__(self):
        out = self.name
        if self.extras:
            out += "[" + ",".join(sorted(self.extras)) + "]"
        if self.url is not None:
            out += " @ " + self.url
        elif str(self.specifier):
            out += str(self.specifier)
        if self.marker is not None:
            out += "; " + str(self.marker)
        return out

    def _semantic_key(self):
        marker = None if self.marker is None else str(self.marker)
        return (self.name, tuple(sorted(self.extras)), self.url, self.specifier, marker)

    def __eq__(self, other):
        try:
            other = other if isinstance(other, Requirement) else Requirement(str(other))
        except InvalidRequirement:
            return False
        return self._semantic_key() == other._semantic_key()

    def __hash__(self):
        return hash(self._semantic_key())


def default_environment():
    pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
    return {
        "python_version": pyver,
        "python_full_version": platform.python_version(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": sys.implementation.name,
        "implementation_version": platform.python_version(),
    }


def is_requirement_satisfied(
    requirement,
    installed_version,
    environment=None,
    requested_extras=None,
    prereleases=None,
):
    req = requirement if isinstance(requirement, Requirement) else Requirement(requirement)
    if req.marker is not None and not req.marker.evaluate(environment, requested_extras):
        return True
    return req.specifier.contains(installed_version, prereleases=prereleases)


def _resolve_metadata_once(
    roots,
    candidates,
    environment=None,
    requested_extras=None,
    prereleases=None,
):
    rows = []
    for index, candidate in enumerate(list(candidates)):
        name = Requirement(candidate["name"]).name
        rows.append(
            {
                "index": index,
                "name": name,
                "version": Version(candidate["version"]),
                "requires": list(candidate.get("requires", [])),
            }
        )

    constraints = {}
    extras = {}
    requirement_facts = set()
    edge_facts = set()
    processed = {}

    def add_requirement(req, source, parent, marker_applicable=True):
        constraints.setdefault(req.name, []).append(req)
        extras.setdefault(req.name, set()).update(req.extras)
        requirement_facts.add(
            (
                source,
                parent,
                req.name,
                tuple(sorted(req.extras)),
                str(req.specifier),
                req.url,
                None if req.marker is None else str(req.marker),
                bool(marker_applicable),
            )
        )

    def candidate_versions(name):
        return sorted((row["version"] for row in rows if row["name"] == name))

    def specifier_matches(req):
        return [
            (str(version), req.specifier.contains(version, prereleases=prereleases))
            for version in candidate_versions(req.name)
        ]

    def satisfying_rows(name):
        reqs = constraints.get(name, [])
        return [
            row
            for row in rows
            if row["name"] == name
            and all(req.specifier.contains(row["version"], prereleases=prereleases) for req in reqs)
        ]

    for root in list(roots):
        req = root if isinstance(root, Requirement) else Requirement(root)
        applies = req.marker is None or req.marker.evaluate(environment, requested_extras)
        if applies:
            add_requirement(req, "root", None, True)

    while True:
        changed = False
        for name in sorted(constraints):
            options = satisfying_rows(name)
            if not options:
                raise ValueError(name)
            selected = max(options, key=lambda row: row["version"])
            state_key = (str(selected["version"]), tuple(sorted(extras.get(name, set()))))
            if processed.get(name) == state_key:
                continue
            processed[name] = state_key

            parent_extras = set(extras.get(name, set()))
            for text in selected["requires"]:
                dep = Requirement(text)
                applies = dep.marker is None or dep.marker.evaluate(environment, parent_extras)
                if not applies:
                    continue
                edge = (
                    name,
                    dep.name,
                    tuple(sorted(dep.extras)),
                    str(dep.specifier),
                    dep.url,
                    None if dep.marker is None else str(dep.marker),
                    True,
                    tuple(specifier_matches(dep)),
                )
                if edge not in edge_facts:
                    edge_facts.add(edge)
                    add_requirement(dep, name, name, True)
                    changed = True
        if not changed:
            break

    selected = {}
    excluded = {}
    for name in sorted(constraints):
        options = satisfying_rows(name)
        if not options:
            raise ValueError(name)
        pick = max(options, key=lambda row: row["version"])
        selected[name] = str(pick["version"])
        rest = [
            str(row["version"])
            for row in rows
            if row["name"] == name and str(row["version"]) != selected[name]
        ]
        if rest:
            excluded[name] = sorted(rest, key=Version)

    edges = [
        {
            "parent": parent,
            "name": name,
            "extras": list(edge_extras),
            "specifier": specifier,
            "url": url,
            "marker": marker,
            "marker_applicable": marker_applicable,
            "specifier_matches": list(matches),
        }
        for parent, name, edge_extras, specifier, url, marker, marker_applicable, matches in sorted(
            edge_facts
        )
    ]

    dependents = {}
    for edge in edges:
        dependents.setdefault(edge["name"], set()).add(edge["parent"])
    dependents = {name: sorted(parents) for name, parents in sorted(dependents.items())}

    requested = {
        name: sorted(values)
        for name, values in sorted(extras.items())
        if name in constraints
    }

    requirements = [
        {
            "source": source,
            "parent": parent,
            "name": name,
            "extras": list(req_extras),
            "specifier": specifier,
            "url": url,
            "marker": marker,
            "marker_applicable": marker_applicable,
        }
        for source, parent, name, req_extras, specifier, url, marker, marker_applicable in sorted(
            requirement_facts
        )
    ]

    return {
        "selected": selected,
        "edges": edges,
        "dependents": dependents,
        "excluded": excluded,
        "requested_extras": requested,
        "requirements": requirements,
    }


def _copy_candidate(candidate):
    copied = {
        "name": Requirement(candidate["name"]).name,
        "version": str(Version(candidate["version"])),
        "requires": list(candidate.get("requires", [])),
    }
    for req in copied["requires"]:
        Requirement(req)
    return copied


def _candidate_key(candidate):
    copied = _copy_candidate(candidate)
    return copied["name"], str(Version(copied["version"]))


class MetadataIndex:
    def __init__(self, candidates=()):
        self._candidates = {}
        self.revision = 0
        for candidate in list(candidates):
            copied = _copy_candidate(candidate)
            self._candidates[(copied["name"], copied["version"])] = copied

    def _state_list(self):
        return [
            {
                "name": candidate["name"],
                "version": candidate["version"],
                "requires": list(candidate.get("requires", [])),
            }
            for _, candidate in sorted(
                self._candidates.items(), key=lambda item: (item[0][0], Version(item[0][1]))
            )
        ]

    def index(self):
        out = {}
        for (name, version), candidate in sorted(
            self._candidates.items(), key=lambda item: (item[0][0], Version(item[0][1]))
        ):
            out.setdefault(name, []).append(
                {"name": name, "version": version, "requires": list(candidate.get("requires", []))}
            )
        return out

    def add_candidate(self, candidate):
        copied = _copy_candidate(candidate)
        self._candidates[(copied["name"], copied["version"])] = copied
        self.revision += 1
        return {
            "revision": self.revision,
            "added": [copied["name"]],
            "removed": [],
            "updated": [],
            "affected": [copied["name"]],
        }

    def remove_candidate(self, name, version):
        key = (Requirement(name).name, str(Version(version)))
        if key not in self._candidates:
            raise ValueError(key[0])
        del self._candidates[key]
        self.revision += 1
        return {
            "revision": self.revision,
            "added": [],
            "removed": [key[0]],
            "updated": [],
            "affected": [key[0]],
        }

    def apply(self, changes):
        new_candidates = dict(self._candidates)
        added, removed, updated, affected = set(), set(), set(), set()
        for change in list(changes):
            action = change.get("action")
            if action == "add":
                copied = _copy_candidate(change["candidate"])
                new_candidates[(copied["name"], copied["version"])] = copied
                added.add(copied["name"])
                affected.add(copied["name"])
            elif action == "update":
                copied = _copy_candidate(change["candidate"])
                key = (copied["name"], copied["version"])
                if key not in new_candidates:
                    raise ValueError(copied["name"])
                new_candidates[key] = copied
                updated.add(copied["name"])
                affected.add(copied["name"])
            elif action == "remove":
                key = (Requirement(change["name"]).name, str(Version(change["version"])))
                if key not in new_candidates:
                    raise ValueError(key[0])
                del new_candidates[key]
                removed.add(key[0])
                affected.add(key[0])
            else:
                raise ValueError(action)
        self._candidates = new_candidates
        self.revision += 1
        return {
            "revision": self.revision,
            "added": sorted(added),
            "removed": sorted(removed),
            "updated": sorted(updated),
            "affected": sorted(affected),
        }

    def resolve(self, roots, environment=None, requested_extras=None, prereleases=None):
        snapshot = _resolve_metadata_once(
            roots,
            self._state_list(),
            environment=environment,
            requested_extras=requested_extras,
            prereleases=prereleases,
        )
        snapshot["revision"] = self.revision
        snapshot["index"] = self.index()
        return snapshot

    def resolve_lock(self, roots, environment=None, requested_extras=None, prereleases=None):
        snapshot = self.resolve(
            roots,
            environment=environment,
            requested_extras=requested_extras,
            prereleases=prereleases,
        )
        lock = {
            "revision": self.revision,
            "roots": list(roots),
            "environment": dict(environment or {}),
            "requested_extras_input": sorted(_norm_name(extra) for extra in (requested_extras or set())),
            "prereleases": prereleases,
            "candidates": self._state_list(),
            "selected": dict(snapshot.get("selected", {})),
            "excluded": {k: list(v) for k, v in snapshot.get("excluded", {}).items()},
            "edges": [dict(edge) for edge in snapshot.get("edges", [])],
            "dependents": {k: list(v) for k, v in snapshot.get("dependents", {}).items()},
            "requested_extras": {k: list(v) for k, v in snapshot.get("requested_extras", {}).items()},
            "requirements": [dict(req) for req in snapshot.get("requirements", [])],
            "index": self.index(),
        }
        return lock

    def apply_lock(self, lock, environment=None, requested_extras=None, prereleases=None):
        lock_copy = {
            "roots": list(lock.get("roots", [])),
            "environment": dict(lock.get("environment", {})),
            "requested_extras_input": list(lock.get("requested_extras_input", [])),
            "prereleases": lock.get("prereleases"),
            "candidates": [
                {
                    "name": candidate["name"],
                    "version": candidate["version"],
                    "requires": list(candidate.get("requires", [])),
                }
                for candidate in lock.get("candidates", [])
            ],
            "selected": dict(lock.get("selected", {})),
        }
        requested = sorted(_norm_name(extra) for extra in (requested_extras or set()))
        if dict(environment or {}) != lock_copy["environment"]:
            raise ValueError("lock environment mismatch")
        if requested != sorted(lock_copy["requested_extras_input"]):
            raise ValueError("lock extras mismatch")
        if prereleases != lock_copy["prereleases"]:
            raise ValueError("lock prereleases mismatch")

        locked_by_key = {}
        for candidate in lock_copy["candidates"]:
            copied = _copy_candidate(candidate)
            locked_by_key[(copied["name"], copied["version"])] = copied

        for name, version in lock_copy["selected"].items():
            key = (Requirement(name).name, str(Version(version)))
            current = self._candidates.get(key)
            locked = locked_by_key.get(key)
            if current is None or locked is None:
                raise ValueError("locked candidate missing")
            if list(current.get("requires", [])) != list(locked.get("requires", [])):
                raise ValueError("locked candidate changed")

        snapshot = _resolve_metadata_once(
            lock_copy["roots"],
            lock_copy["candidates"],
            environment=lock_copy["environment"],
            requested_extras=set(lock_copy["requested_extras_input"]),
            prereleases=lock_copy["prereleases"],
        )
        if dict(snapshot.get("selected", {})) != lock_copy["selected"]:
            raise ValueError("lock replay mismatch")
        snapshot["revision"] = self.revision
        snapshot["lock_revision"] = int(lock.get("revision", 0))
        snapshot["index"] = self.index()
        return snapshot

    def dependents_of(
        self,
        name,
        roots=None,
        transitive=False,
        environment=None,
        requested_extras=None,
        prereleases=None,
    ):
        target = Requirement(name).name
        if roots is None:
            roots = sorted({candidate["name"] for candidate in self._candidates.values()})
        snapshot = self.resolve(
            roots,
            environment=environment,
            requested_extras=requested_extras,
            prereleases=prereleases,
        )
        direct = set(snapshot.get("dependents", {}).get(target, []))
        if not transitive:
            return sorted(direct)
        seen = set(direct)
        frontier = list(direct)
        while frontier:
            current = frontier.pop()
            for parent in snapshot.get("dependents", {}).get(current, []):
                if parent not in seen:
                    seen.add(parent)
                    frontier.append(parent)
        return sorted(seen)

    def export_state(self):
        return {"revision": self.revision, "candidates": self._state_list()}

    @classmethod
    def import_state(cls, state):
        obj = cls(state.get("candidates", []))
        obj.revision = int(state.get("revision", 0))
        return obj


def resolve_metadata(
    roots,
    candidates,
    environment=None,
    requested_extras=None,
    prereleases=None,
):
    snapshot = MetadataIndex(candidates).resolve(
        roots,
        environment=environment,
        requested_extras=requested_extras,
        prereleases=prereleases,
    )
    snapshot.pop("revision", None)
    snapshot.pop("index", None)
    return snapshot
