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
_SUPPORTED_MARKER_VARS = {
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


def _normalize_name(name):
    text = str(name).strip()
    if not _NAME_RE.match(text):
        raise InvalidRequirement("invalid name")
    return text.replace("_", "-").lower()


def _norm_release(parts):
    values = tuple(int(p) for p in parts)
    while len(values) > 1 and values[-1] == 0:
        values = values[:-1]
    return values


def _pad_tuple(left, right):
    size = max(len(left), len(right))
    return left + (0,) * (size - len(left)), right + (0,) * (size - len(right))


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
        raw = str(text).strip()
        if not raw:
            raise InvalidVersion("empty version")
        local = ()
        if "+" in raw:
            raw, local_text = raw.split("+", 1)
            if not local_text:
                raise InvalidVersion("empty local")
            local_parts = re.split(r"[._-]", local_text.lower())
            if any(not p or not re.match(r"^[a-z0-9]+$", p) for p in local_parts):
                raise InvalidVersion("invalid local")
            local = tuple((1, int(p)) if p.isdigit() else (0, p) for p in local_parts)
        public = raw.lower()
        epoch = 0
        if "!" in public:
            epoch_text, public = public.split("!", 1)
            if not epoch_text.isdigit() or not public:
                raise InvalidVersion("invalid epoch")
            epoch = int(epoch_text)
        m = re.match(r"^(\d+(?:\.\d+)*)(.*)$", public)
        if not m:
            raise InvalidVersion("invalid release")
        release_text, rest = m.groups()
        if ".." in release_text:
            raise InvalidVersion("invalid release")
        release = _norm_release(release_text.split("."))
        pre = None
        post = None
        dev = None
        token_re = re.compile(r"^(alpha|beta|preview|pre|post|rev|rc|dev|a|b|c|r)(?:[-_.]?(\d+))?(.*)$")
        while rest:
            if rest[0] in ".-_":
                rest = rest[1:]
            if not rest:
                raise InvalidVersion("dangling separator")
            tm = token_re.match(rest)
            if not tm:
                raise InvalidVersion("invalid suffix")
            token, num_text, rest = tm.groups()
            num = int(num_text) if num_text is not None else 0
            if token in {"a", "alpha"}:
                if pre is not None:
                    raise InvalidVersion("duplicate pre")
                pre = ("a", num)
            elif token in {"b", "beta"}:
                if pre is not None:
                    raise InvalidVersion("duplicate pre")
                pre = ("b", num)
            elif token in {"rc", "c", "pre", "preview"}:
                if pre is not None:
                    raise InvalidVersion("duplicate pre")
                pre = ("rc", num)
            elif token == "dev":
                if dev is not None:
                    raise InvalidVersion("duplicate dev")
                dev = num
            else:
                if post is not None:
                    raise InvalidVersion("duplicate post")
                post = num
        self.epoch = epoch
        self.release = release
        self.pre = pre
        self.post = post
        self.dev = dev
        self.local = local

    @property
    def is_prerelease(self):
        return self.dev is not None or self.pre is not None

    def _stage(self):
        if self.dev is not None:
            return (0, self.dev)
        if self.pre is not None:
            order = {"a": 1, "b": 2, "rc": 3}[self.pre[0]]
            return (order, self.pre[1])
        if self.post is not None:
            return (5, self.post)
        return (4, 0)

    def _cmp_public(self, other):
        left_rel, right_rel = _pad_tuple(self.release, other.release)
        return (self.epoch, left_rel, self._stage()), (other.epoch, right_rel, other._stage())

    def __eq__(self, other):
        try:
            other = Version(other)
        except InvalidVersion:
            return NotImplemented
        left, right = self._cmp_public(other)
        return left == right and self.local == other.local

    def __lt__(self, other):
        other = Version(other)
        left, right = self._cmp_public(other)
        if left != right:
            return left < right
        return self.local < other.local

    def __hash__(self):
        return hash((self.epoch, self.release, self._stage(), self.local))

    def __str__(self):
        out = ""
        if self.epoch:
            out += f"{self.epoch}!"
        out += ".".join(str(p) for p in self.release)
        if self.dev is not None:
            out += f".dev{self.dev}"
        if self.pre is not None:
            out += f"{self.pre[0]}{self.pre[1]}"
        if self.post is not None:
            out += f".post{self.post}"
        if self.local:
            parts = [str(v) for kind, v in self.local]
            out += "+" + ".".join(parts)
        return out

    def __repr__(self):
        return f"Version({str(self)!r})"


def _release_prefix(version, size=None):
    rel = version.release
    if size is not None:
        rel = rel + (0,) * max(0, size - len(rel))
    return rel


class SpecifierSet:
    _clause_re = re.compile(r"^(==|!=|>=|<=|>|<|~=)\s*(\S+)$")

    def __init__(self, text=""):
        self._clauses = []
        raw = "" if text is None else str(text).strip()
        if not raw:
            return
        for part in raw.split(","):
            clause = part.strip()
            if not clause:
                raise InvalidSpecifier("empty clause")
            m = self._clause_re.match(clause)
            if not m:
                raise InvalidSpecifier("invalid clause")
            op, value = m.groups()
            wildcard = False
            prefix = None
            version = None
            if value.endswith(".*"):
                if op not in {"==", "!="}:
                    raise InvalidSpecifier("wildcard operator")
                base = value[:-2]
                if not re.match(r"^\d+(?:\.\d+)*$", base):
                    raise InvalidSpecifier("invalid wildcard")
                wildcard = True
                prefix = tuple(int(p) for p in base.split("."))
                canonical = ".".join(str(p) for p in prefix) + ".*"
            else:
                try:
                    version = Version(value)
                except InvalidVersion as exc:
                    raise InvalidSpecifier(str(exc))
                canonical = str(version)
            if op == "~=":
                if wildcard:
                    raise InvalidSpecifier("wildcard compatible")
                parts = tuple(int(p) for p in re.match(r"^(\d+(?:\.\d+)*)", value).group(1).split("."))
                if len(parts) == 1:
                    upper_parts = (parts[0] + 1,)
                elif len(parts) == 2:
                    upper_parts = (parts[0] + 1,)
                else:
                    upper_parts = parts[:-2] + (parts[-2] + 1,)
                upper = Version(".".join(str(p) for p in upper_parts))
                self._clauses.append((op, version, wildcard, prefix, canonical, upper))
            else:
                self._clauses.append((op, version, wildcard, prefix, canonical, None))

    def __str__(self):
        return ",".join(op + canonical for op, _v, _w, _p, canonical, _u in self._clauses)

    def __eq__(self, other):
        return isinstance(other, SpecifierSet) and self._key() == other._key()

    def __hash__(self):
        return hash(self._key())

    def _key(self):
        return tuple(sorted((op, canonical) for op, _v, _w, _p, canonical, _u in self._clauses))

    def contains(self, version, prereleases=None):
        v = Version(version)
        if prereleases is not True and v.is_prerelease:
            return False
        for op, target, wildcard, prefix, _canonical, upper in self._clauses:
            if wildcard:
                cand = _release_prefix(v, len(prefix))[: len(prefix)]
                matched = cand == prefix
                if op == "==" and not matched:
                    return False
                if op == "!=" and matched:
                    return False
                continue
            if op == "==" and v != target:
                return False
            if op == "!=" and v == target:
                return False
            if op == ">=" and not (v >= target):
                return False
            if op == "<=" and not (v <= target):
                return False
            if op == ">" and not (v > target):
                return False
            if op == "<" and not (v < target):
                return False
            if op == "~=" and not (v >= target and v < upper):
                return False
        return True


class _MarkerTokenizer:
    token_re = re.compile(
        r"\s*(?:(and|or|in|not\b)|([A-Za-z_][A-Za-z0-9_]*)|(==|!=|<=|>=|<|>)|([()])|('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))",
        re.I,
    )

    def __init__(self, text):
        self.tokens = []
        pos = 0
        while pos < len(text):
            m = self.token_re.match(text, pos)
            if not m:
                raise InvalidMarker("invalid marker")
            word, ident, op, paren, string = m.groups()
            pos = m.end()
            if word:
                value = word.lower()
                if value == "not":
                    n = self.token_re.match(text, pos)
                    if not n or not n.group(1) or n.group(1).lower() != "in":
                        raise InvalidMarker("expected in")
                    pos = n.end()
                    self.tokens.append(("op", "not in"))
                elif value == "in":
                    self.tokens.append(("op", "in"))
                else:
                    self.tokens.append((value, value))
            elif ident:
                name = ident.lower()
                if name not in _SUPPORTED_MARKER_VARS:
                    raise InvalidMarker("unknown variable")
                self.tokens.append(("var", name))
            elif op:
                self.tokens.append(("op", op))
            elif paren:
                self.tokens.append((paren, paren))
            else:
                self.tokens.append(("str", string[1:-1]))
        self.tokens.append(("eof", ""))
        self.index = 0

    def peek(self):
        return self.tokens[self.index]

    def pop(self, kind=None):
        tok = self.peek()
        if kind is not None and tok[0] != kind:
            raise InvalidMarker("unexpected token")
        self.index += 1
        return tok


class Marker:
    def __init__(self, text):
        self._text = str(text).strip()
        if not self._text:
            raise InvalidMarker("empty marker")
        parser = _MarkerTokenizer(self._text)
        self._ast = self._parse_or(parser)
        if parser.peek()[0] != "eof":
            raise InvalidMarker("trailing marker")

    def _parse_or(self, parser):
        node = self._parse_and(parser)
        while parser.peek()[0] == "or":
            parser.pop()
            node = ("or", node, self._parse_and(parser))
        return node

    def _parse_and(self, parser):
        node = self._parse_atom(parser)
        while parser.peek()[0] == "and":
            parser.pop()
            node = ("and", node, self._parse_atom(parser))
        return node

    def _parse_atom(self, parser):
        if parser.peek()[0] == "(":
            parser.pop("(")
            node = self._parse_or(parser)
            parser.pop(")")
            return node
        left = parser.pop()
        if left[0] not in {"var", "str"}:
            raise InvalidMarker("expected term")
        op = parser.pop("op")[1]
        right = parser.pop()
        if right[0] not in {"var", "str"}:
            raise InvalidMarker("expected term")
        return ("cmp", left, op, right)

    def __str__(self):
        return self._format(self._ast)

    def __eq__(self, other):
        return isinstance(other, Marker) and self._ast == other._ast

    def __hash__(self):
        return hash(self._ast)

    def _format_term(self, term):
        if term[0] == "var":
            return term[1]
        return '"' + str(term[1]).replace('"', '\\"') + '"'

    def _format(self, node):
        if node[0] == "cmp":
            return f"{self._format_term(node[1])} {node[2]} {self._format_term(node[3])}"
        return f"{self._format(node[1])} {node[0]} {self._format(node[2])}"

    def evaluate(self, environment=None, requested_extras=None):
        env = default_environment() if environment is None else dict(environment)
        extras = sorted({_normalize_name(e) for e in (requested_extras or [])})
        if not extras:
            extras = [""]
        if self._uses_extra(self._ast):
            return any(self._eval(self._ast, env, extra) for extra in extras)
        return self._eval(self._ast, env, "")

    def _uses_extra(self, node):
        if node[0] == "cmp":
            return node[1] == ("var", "extra") or node[3] == ("var", "extra")
        return self._uses_extra(node[1]) or self._uses_extra(node[2])

    def _eval(self, node, env, extra):
        if node[0] == "and":
            return self._eval(node[1], env, extra) and self._eval(node[2], env, extra)
        if node[0] == "or":
            return self._eval(node[1], env, extra) or self._eval(node[2], env, extra)
        left = self._term_value(node[1], env, extra)
        right = self._term_value(node[3], env, extra)
        if node[1] == ("var", "extra") or node[3] == ("var", "extra"):
            left = _normalize_name(left) if left else ""
            right = _normalize_name(right) if right else ""
        return _compare_marker_values(left, node[2], right)

    def _term_value(self, term, env, extra):
        if term[0] == "str":
            return str(term[1])
        name = term[1]
        if name == "extra":
            return extra
        if name not in env:
            raise UndefinedEnvironmentName(name)
        return str(env[name])


def _compare_marker_values(left, op, right):
    if op in {"in", "not in"}:
        result = left in right.split()
        return not result if op == "not in" else result
    if op in {"<", "<=", ">", ">="}:
        try:
            lv, rv = Version(left), Version(right)
            if op == "<":
                return lv < rv
            if op == "<=":
                return lv <= rv
            if op == ">":
                return lv > rv
            return lv >= rv
        except InvalidVersion:
            pass
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    raise InvalidMarker("invalid operator")


class Requirement:
    def __init__(self, text):
        if isinstance(text, Requirement):
            self.name = text.name
            self.extras = set(text.extras)
            self.specifier = SpecifierSet(str(text.specifier))
            self.url = text.url
            self.marker = Marker(str(text.marker)) if text.marker is not None else None
            return
        raw = str(text).strip()
        if not raw:
            raise InvalidRequirement("empty requirement")
        req_part, marker_part = _split_marker(raw)
        self.marker = Marker(marker_part.strip()) if marker_part is not None else None
        try:
            self.name, self.extras, rest = self._parse_name_extras(req_part.strip())
            self.url = None
            spec_text = ""
            if rest.strip().startswith("@"):
                after = rest.strip()[1:].strip()
                if not after:
                    raise InvalidRequirement("missing url")
                if re.search(r"\s(==|!=|>=|<=|~=|>|<)", after):
                    raise InvalidRequirement("url with specifier")
                self.url = after
            else:
                spec_text = rest.strip()
            self.specifier = SpecifierSet(spec_text)
            if self.url is not None and str(self.specifier):
                raise InvalidRequirement("url with specifier")
        except InvalidSpecifier as exc:
            raise InvalidRequirement(str(exc))
        except (InvalidMarker, InvalidRequirement):
            raise
        except Exception as exc:
            raise InvalidRequirement(str(exc))

    def _parse_name_extras(self, text):
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]?)(.*)$", text)
        if not m:
            raise InvalidRequirement("invalid name")
        name = _normalize_name(m.group(1))
        rest = m.group(2)
        extras = set()
        rest_strip = rest.lstrip()
        if rest_strip.startswith("["):
            close = rest_strip.find("]")
            if close == -1:
                raise InvalidRequirement("missing extras close")
            extra_text = rest_strip[1:close].strip()
            if not extra_text:
                raise InvalidRequirement("empty extras")
            for item in extra_text.split(","):
                extras.add(_normalize_name(item.strip()))
            rest = rest_strip[close + 1 :]
        else:
            rest = rest
        return name, extras, rest

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

    def _key(self):
        return (self.name, tuple(sorted(self.extras)), self.specifier._key(), self.url, self.marker)

    def __eq__(self, other):
        return isinstance(other, Requirement) and self._key() == other._key()

    def __hash__(self):
        return hash(self._key())


def _split_marker(text):
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == ";":
            return text[:i], text[i + 1 :]
    return text, None


def default_environment():
    vi = sys.version_info
    return {
        "python_version": f"{vi.major}.{vi.minor}",
        "python_full_version": platform.python_version(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": getattr(sys.implementation, "name", platform.python_implementation().lower()),
        "implementation_version": platform.python_version(),
    }


def is_requirement_satisfied(requirement, installed_version, environment=None, requested_extras=None, prereleases=None):
    req = requirement if isinstance(requirement, Requirement) else Requirement(requirement)
    if req.marker is not None and not req.marker.evaluate(environment, requested_extras):
        return True
    return req.specifier.contains(installed_version, prereleases=prereleases)


def _candidate_record(candidate):
    if not isinstance(candidate, dict) and not hasattr(candidate, "get"):
        raise ValueError("candidate must be mapping")
    try:
        name = _normalize_name(candidate["name"])
        version = Version(candidate["version"])
    except KeyError as exc:
        raise ValueError(str(exc))
    requires = list(candidate.get("requires", []) or [])
    copied_requires = []
    for req in requires:
        Requirement(req)
        copied_requires.append(str(req))
    return {"name": name, "version": str(version), "requires": copied_requires}


def _records_from_candidates(candidates):
    table = {}
    for cand in candidates:
        rec = _candidate_record(cand)
        table[(rec["name"], rec["version"])] = rec
    return list(table.values())


def _group_candidates(records):
    grouped = {}
    for rec in records:
        grouped.setdefault(rec["name"], []).append(rec)
    for values in grouped.values():
        values.sort(key=lambda r: Version(r["version"]))
    return grouped


def _requested_extra_map(requested_extras):
    if requested_extras is None:
        return {}
    if isinstance(requested_extras, dict):
        return { _normalize_name(k): {_normalize_name(e) for e in v} for k, v in requested_extras.items() }
    return {"": {_normalize_name(e) for e in requested_extras}}


def _edge_key(edge):
    return (edge["parent"], edge["name"], tuple(edge["extras"]), edge["specifier"], edge["url"] or "", edge["marker"] or "")


def _fact_key(fact):
    return (fact["source"], fact["parent"] or "", fact["name"], tuple(fact["extras"]), fact["specifier"], fact["url"] or "", fact["marker"] or "")


def resolve_metadata(roots, candidates, environment=None, requested_extras=None, prereleases=None):
    records = _records_from_candidates(candidates)
    return _resolve_records(roots, records, environment, requested_extras, prereleases, locked_versions=None)


def _resolve_records(roots, records, environment=None, requested_extras=None, prereleases=None, locked_versions=None):
    grouped = _group_candidates(records)
    req_extra_input = _requested_extra_map(requested_extras)
    constraints = {}
    requested = {}
    facts = []
    fact_seen = set()
    selected = {}
    selected_rec = {}
    processed_parent_versions = {}

    def add_requirement(req_obj, source, parent, extras_context):
        marker_applicable = True
        if req_obj.marker is not None:
            marker_applicable = req_obj.marker.evaluate(environment, extras_context)
        fact = {
            "source": source,
            "parent": parent,
            "name": req_obj.name,
            "extras": sorted(req_obj.extras),
            "specifier": str(req_obj.specifier),
            "url": req_obj.url,
            "marker": str(req_obj.marker) if req_obj.marker is not None else None,
            "marker_applicable": bool(marker_applicable),
        }
        key = _fact_key(fact)
        if key in fact_seen:
            return False
        fact_seen.add(key)
        facts.append(fact)
        if not marker_applicable:
            return False
        constraints.setdefault(req_obj.name, []).append(req_obj.specifier)
        requested.setdefault(req_obj.name, set()).update(req_obj.extras)
        return True

    root_extras = set(req_extra_input.get("", set()))
    for root in list(roots):
        req = root if isinstance(root, Requirement) else Requirement(root)
        extras_context = set(root_extras) | set(req_extra_input.get(req.name, set())) | set(req.extras)
        add_requirement(req, "root", None, extras_context)
    for name, extras in req_extra_input.items():
        if name:
            requested.setdefault(name, set()).update(extras)

    changed = True
    while changed:
        changed = False
        active_names = sorted(constraints)
        for name in active_names:
            if name not in grouped:
                raise ValueError("no candidates")
            specs = constraints.get(name, [])
            locked = locked_versions.get(name) if locked_versions else None
            viable = []
            for rec in grouped[name]:
                v = Version(rec["version"])
                if locked is not None and str(v) != locked:
                    continue
                if all(spec.contains(v, prereleases=prereleases) for spec in specs):
                    viable.append(rec)
            if not viable:
                raise ValueError("no satisfying candidate")
            best = max(viable, key=lambda r: Version(r["version"]))
            if selected.get(name) != best["version"]:
                selected[name] = best["version"]
                selected_rec[name] = best
                changed = True
            if processed_parent_versions.get(name) == selected[name]:
                continue
            processed_parent_versions[name] = selected[name]
            parent_extras = set(requested.get(name, set()))
            for req_text in list(best.get("requires", [])):
                req = Requirement(req_text)
                if add_requirement(req, name, name, parent_extras):
                    changed = True

    edges = []
    for fact in facts:
        if fact["parent"] is None or not fact["marker_applicable"]:
            continue
        child_versions = grouped.get(fact["name"], [])
        spec = SpecifierSet(fact["specifier"])
        matches = [(rec["version"], bool(spec.contains(rec["version"], prereleases=prereleases))) for rec in child_versions]
        edge = {
            "parent": fact["parent"],
            "name": fact["name"],
            "extras": list(fact["extras"]),
            "specifier": fact["specifier"],
            "url": fact["url"],
            "marker": fact["marker"],
            "marker_applicable": True,
            "specifier_matches": matches,
        }
        edges.append(edge)
    edges.sort(key=_edge_key)

    dependents = {}
    for edge in edges:
        dependents.setdefault(edge["name"], set()).add(edge["parent"])
    dependents = {k: sorted(v) for k, v in sorted(dependents.items())}

    excluded = {}
    for name in sorted(constraints):
        specs = constraints[name]
        versions = []
        for rec in grouped.get(name, []):
            if rec["version"] == selected.get(name):
                continue
            if not all(spec.contains(rec["version"], prereleases=prereleases) for spec in specs):
                versions.append(rec["version"])
            else:
                versions.append(rec["version"])
        if versions:
            excluded[name] = sorted(versions, key=Version)

    req_proj = []
    for fact in facts:
        if fact["marker_applicable"]:
            req_proj.append(dict(fact))
    req_proj.sort(key=_fact_key)

    return {
        "selected": dict(sorted(selected.items())),
        "excluded": excluded,
        "edges": edges,
        "dependents": dependents,
        "requested_extras": {k: sorted(v) for k, v in sorted(requested.items()) if k in constraints or k in selected},
        "requirements": req_proj,
    }


class MetadataIndex:
    def __init__(self, candidates=()):
        self._records = {}
        self.revision = 0
        for cand in candidates or ():
            rec = _candidate_record(cand)
            self._records[(rec["name"], rec["version"])] = rec
        if self._records:
            self.revision = len(self._records)

    def index(self):
        grouped = _group_candidates(self._records.values())
        out = {}
        for name in sorted(grouped):
            out[name] = [{"name": r["name"], "version": r["version"], "requires": list(r.get("requires", []))} for r in grouped[name]]
        return out

    def add_candidate(self, candidate):
        rec = _candidate_record(candidate)
        self._records[(rec["name"], rec["version"])] = rec
        self.revision += 1

    def remove_candidate(self, name, version):
        n = _normalize_name(name)
        v = str(Version(version))
        key = (n, v)
        if key not in self._records:
            raise ValueError("missing candidate")
        del self._records[key]
        self.revision += 1

    def apply(self, changes):
        new_records = {k: {"name": v["name"], "version": v["version"], "requires": list(v["requires"])} for k, v in self._records.items()}
        parsed_changes = list(changes)
        for change in parsed_changes:
            action = change.get("action")
            if action in {"add", "update"}:
                rec = _candidate_record(change.get("candidate", {}))
                key = (rec["name"], rec["version"])
                if action == "update" and key not in new_records:
                    raise ValueError("missing update target")
                new_records[key] = rec
            elif action == "remove":
                n = _normalize_name(change.get("name"))
                v = str(Version(change.get("version")))
                key = (n, v)
                if key not in new_records:
                    raise ValueError("missing remove target")
                del new_records[key]
            else:
                raise ValueError("unknown action")
        self._records = new_records
        self.revision += 1

    def resolve(self, roots, environment=None, requested_extras=None, prereleases=None):
        res = _resolve_records(roots, self._records.values(), environment, requested_extras, prereleases)
        res["revision"] = self.revision
        res["index"] = self.index()
        return res

    def dependents_of(self, name, roots=None, transitive=False, **resolve_options):
        target = _normalize_name(name)
        if roots is None:
            roots = sorted(self.index().keys())
        res = self.resolve(roots, **resolve_options)
        direct = set(res["dependents"].get(target, []))
        if not transitive:
            return sorted(direct)
        all_parents = set(direct)
        queue = list(direct)
        while queue:
            item = queue.pop(0)
            for parent in res["dependents"].get(item, []):
                if parent not in all_parents:
                    all_parents.add(parent)
                    queue.append(parent)
        return sorted(all_parents)

    def resolve_lock(self, roots, environment=None, requested_extras=None, prereleases=None):
        root_list = [str(r if isinstance(r, Requirement) else Requirement(r)) for r in list(roots)]
        res = self.resolve(root_list, environment, requested_extras, prereleases)
        lock = {
            "revision": self.revision,
            "roots": list(root_list),
            "selected": dict(res["selected"]),
            "excluded": {k: list(v) for k, v in res["excluded"].items()},
            "edges": [dict(e) for e in res["edges"]],
            "dependents": {k: list(v) for k, v in res["dependents"].items()},
            "requested_extras": {k: list(v) for k, v in res["requested_extras"].items()},
            "requirements": [dict(r) for r in res["requirements"]],
            "index": self.index(),
        }
        return lock

    def apply_lock(self, lock, environment=None, requested_extras=None, prereleases=None):
        lock_copy = _copy_lock(lock)
        required = {"revision", "roots", "selected", "edges", "dependents", "requested_extras", "requirements", "excluded", "index"}
        if not isinstance(lock_copy, dict) or not required.issubset(lock_copy):
            raise ValueError("invalid lock")
        selected = { _normalize_name(k): str(Version(v)) for k, v in lock_copy["selected"].items() }
        for name, version in selected.items():
            key = (name, version)
            if key not in self._records:
                raise ValueError("locked candidate missing")
            current_requires = list(self._records[key].get("requires", []))
            lock_records = lock_copy["index"].get(name, [])
            matches = [r for r in lock_records if str(Version(r["version"])) == version]
            if not matches or list(matches[0].get("requires", [])) != current_requires:
                raise ValueError("locked metadata changed")
        lock_records = []
        for rows in lock_copy["index"].values():
            for rec in rows:
                lock_records.append(_candidate_record(rec))
        res = _resolve_records(lock_copy["roots"], lock_records, environment, requested_extras, prereleases, locked_versions=selected)
        comparable = ["selected", "edges", "dependents", "requested_extras", "requirements"]
        for key in comparable:
            if res[key] != lock_copy[key]:
                raise ValueError("lock graph mismatch")
        res["revision"] = self.revision
        res["lock_revision"] = lock_copy["revision"]
        res["index"] = self.index()
        return res

    def export_state(self):
        records = []
        for name, rows in self.index().items():
            records.extend({"name": r["name"], "version": r["version"], "requires": list(r["requires"])} for r in rows)
        return {"revision": self.revision, "candidates": records}

    @classmethod
    def import_state(cls, state):
        if not isinstance(state, dict) or "revision" not in state or "candidates" not in state:
            raise ValueError("invalid state")
        idx = cls(state["candidates"])
        idx.revision = int(state["revision"])
        return idx


def _copy_lock(lock):
    if not isinstance(lock, dict):
        raise ValueError("invalid lock")
    out = {}
    for k, v in lock.items():
        if isinstance(v, dict):
            out[k] = {kk: list(vv) if isinstance(vv, list) else dict(vv) if isinstance(vv, dict) else vv for kk, vv in v.items()}
        elif isinstance(v, list):
            out[k] = [dict(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out
