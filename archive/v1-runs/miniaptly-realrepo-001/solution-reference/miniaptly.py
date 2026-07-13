import hashlib
import json
import re
from pathlib import Path


class ArchiveError(Exception):
    pass


_NAME_RE = re.compile(r"^[a-z0-9_-]+$")
_ARCHES = {"amd64", "arm64", "all"}


def _version_key(version):
    parts = version.split(".")
    if not parts or any(not p.isdigit() for p in parts):
        raise ArchiveError("invalid version")
    nums = tuple(int(p) for p in parts)
    while nums and nums[-1] == 0:
        nums = nums[:-1]
    return nums or (0,)


def _identity(record):
    return (record["name"], record["version"], record["arch"])


def _identity_text(record):
    return f"{record['name']}={record['version']}@{record['arch']}"


def _sorted_records(records):
    return [
        dict(r)
        for r in sorted(
            records,
            key=lambda r: (r["name"], _version_key(r["version"]), r["arch"], r["checksum"]),
        )
    ]


def _index_digest(records):
    payload = json.dumps(_sorted_records(records), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_package(path):
    raw = Path(path).read_bytes()
    if b"\n\n" not in raw:
        raise ArchiveError("package missing payload separator")
    head, payload = raw.split(b"\n\n", 1)
    fields = {}
    for line in head.decode("utf-8").splitlines():
        if ":" not in line:
            raise ArchiveError("malformed control line")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    for required in ("Name", "Version", "Arch", "Depends"):
        if required not in fields:
            raise ArchiveError(f"missing {required}")
    name = fields["Name"]
    arch = fields["Arch"]
    _version_key(fields["Version"])
    if not _NAME_RE.match(name) or arch not in _ARCHES:
        raise ArchiveError("invalid package identity")
    depends = [part.strip() for part in fields["Depends"].split(",") if part.strip()]
    return {
        "name": name,
        "version": fields["Version"],
        "arch": arch,
        "checksum": hashlib.sha256(payload).hexdigest(),
        "depends": depends,
    }


class MiniAptly:
    def __init__(self):
        self.repos = {}
        self.snapshots = {}
        self.published = {}
        self.pool = {}
        self.pending = None

    def parse_package(self, path):
        return parse_package(path)

    def _ensure_no_pending(self):
        if self.pending is not None:
            raise ArchiveError("pending recovery required")

    def _record_package(self, record):
        current = self.pool.get(record["checksum"])
        if current is None:
            self.pool[record["checksum"]] = dict(record)

    def _snapshot_packages(self, name):
        if name not in self.snapshots:
            raise ArchiveError("unknown snapshot")
        return {tuple(k.split("|")): dict(v) for k, v in self.snapshots[name]["packages"].items()}

    def _source_packages(self, source):
        if source in self.repos:
            return {tuple(k.split("|")): dict(v) for k, v in self.repos[source].items()}
        if source in self.snapshots:
            return self._snapshot_packages(source)
        raise ArchiveError("unknown source")

    @staticmethod
    def _key(record):
        return "|".join(_identity(record))

    def add(self, repo, package_path):
        self._ensure_no_pending()
        record = parse_package(package_path)
        store = self.repos.setdefault(repo, {})
        key = self._key(record)
        existing = store.get(key)
        if existing and existing["checksum"] != record["checksum"]:
            raise ArchiveError("conflicting package identity")
        store[key] = dict(record)
        self._record_package(record)
        return dict(record)

    def remove(self, repo, name, version=None, arch=None):
        self._ensure_no_pending()
        store = self.repos.setdefault(repo, {})
        removed = []
        for key, record in list(store.items()):
            if record["name"] != name:
                continue
            if version is not None and record["version"] != version:
                continue
            if arch is not None and record["arch"] != arch:
                continue
            removed.append(store.pop(key))
        return _sorted_records(removed)

    def repo_show(self, repo):
        return _sorted_records(self.repos.get(repo, {}).values())

    def repo_search(self, repo, name=None, arch=None, min_version=None):
        rows = []
        min_key = _version_key(min_version) if min_version is not None else None
        for record in self.repos.get(repo, {}).values():
            if name is not None and record["name"] != name:
                continue
            if arch is not None and record["arch"] != arch:
                continue
            if min_key is not None and _version_key(record["version"]) < min_key:
                continue
            rows.append(record)
        return _sorted_records(rows)

    def snapshot_create(self, name, source):
        self._ensure_no_pending()
        if name in self.snapshots:
            raise ArchiveError("snapshot exists")
        packages = self._source_packages(source)
        self.snapshots[name] = {
            "name": name,
            "sources": [source],
            "parents": [source] if source in self.snapshots else [],
            "packages": {"|".join(k): dict(v) for k, v in packages.items()},
        }
        return self.snapshot_show(name)

    def snapshot_merge(self, name, sources, *, first_wins=False):
        self._ensure_no_pending()
        if name in self.snapshots:
            raise ArchiveError("snapshot exists")
        selected = {}
        by_name_arch = {}
        for source in sources:
            for record in self._snapshot_packages(source).values():
                ident = _identity(record)
                ident_key = self._key(record)
                if ident_key in selected and selected[ident_key]["checksum"] != record["checksum"]:
                    raise ArchiveError("conflicting package checksum")
                pair = (record["name"], record["arch"])
                current_key = by_name_arch.get(pair)
                if current_key is None:
                    by_name_arch[pair] = ident
                    selected[ident_key] = dict(record)
                    continue
                current = selected["|".join(current_key)]
                if first_wins:
                    continue
                if _version_key(record["version"]) > _version_key(current["version"]):
                    selected.pop("|".join(current_key), None)
                    by_name_arch[pair] = ident
                    selected[ident_key] = dict(record)
        self.snapshots[name] = {
            "name": name,
            "sources": list(sources),
            "parents": list(sources),
            "packages": {k: dict(v) for k, v in selected.items()},
        }
        return self.snapshot_show(name)

    def snapshot_filter(self, name, source, *, name_filter=None, arch=None, min_version=None):
        self._ensure_no_pending()
        if name in self.snapshots:
            raise ArchiveError("snapshot exists")
        min_key = _version_key(min_version) if min_version is not None else None
        selected = {}
        for key, record in self._snapshot_packages(source).items():
            if name_filter is not None and record["name"] != name_filter:
                continue
            if arch is not None and record["arch"] != arch:
                continue
            if min_key is not None and _version_key(record["version"]) < min_key:
                continue
            selected["|".join(key)] = dict(record)
        self.snapshots[name] = {
            "name": name,
            "sources": [source],
            "parents": [source],
            "packages": selected,
        }
        return self.snapshot_show(name)

    def snapshot_show(self, name):
        snap = self.snapshots[name]
        return {
            "name": snap["name"],
            "sources": list(snap["sources"]),
            "parents": list(snap["parents"]),
            "packages": _sorted_records(snap["packages"].values()),
        }

    def snapshot_diff(self, left, right):
        left_rows = {(r["name"], r["arch"]): r for r in self._snapshot_packages(left).values()}
        right_rows = {(r["name"], r["arch"]): r for r in self._snapshot_packages(right).values()}
        added = []
        removed = []
        changed = []
        for key, record in right_rows.items():
            if key not in left_rows:
                added.append(record)
            else:
                before = left_rows[key]
                if before["version"] != record["version"] or before["checksum"] != record["checksum"]:
                    changed.append({"before": dict(before), "after": dict(record)})
        for key, record in left_rows.items():
            if key not in right_rows:
                removed.append(record)
        return {
            "added": _sorted_records(added),
            "removed": _sorted_records(removed),
            "changed": sorted(changed, key=lambda c: (c["after"]["name"], c["after"]["arch"])),
        }

    def _publish_record(self, snapshot, distribution, component, arch):
        packages = [
            dict(record)
            for record in self._snapshot_packages(snapshot).values()
            if record["arch"] in {arch, "all"}
        ]
        packages = _sorted_records(packages)
        return {
            "distribution": distribution,
            "component": component,
            "arch": arch,
            "snapshot": snapshot,
            "packages": packages,
            "index_digest": _index_digest(packages),
        }

    def publish(self, snapshot, distribution, component, arch):
        self._ensure_no_pending()
        record = self._publish_record(snapshot, distribution, component, arch)
        self.published[(distribution, component, arch)] = record
        return dict(record)

    def publish_switch(self, snapshot, distribution, component, arch, *, fail_at=None):
        self._ensure_no_pending()
        key = (distribution, component, arch)
        if key not in self.published:
            raise ArchiveError("unknown published prefix")
        record = self._publish_record(snapshot, distribution, component, arch)
        if fail_at is not None:
            if fail_at not in {"after_journal", "after_index", "after_publish_record"}:
                raise ArchiveError("unknown fail_at")
            self.pending = {
                "kind": "publish_switch",
                "prefix": key,
                "record": record,
                "fail_at": fail_at,
            }
            raise ArchiveError("simulated publish failure")
        self.published[key] = record
        return dict(record)

    def publish_show(self, distribution, component, arch):
        return dict(self.published[(distribution, component, arch)])

    def published_index(self, distribution, component, arch):
        return _sorted_records(self.published[(distribution, component, arch)]["packages"])

    def cleanup_dry_run(self):
        reasons = {checksum: [] for checksum in self.pool}
        for repo, rows in self.repos.items():
            for record in rows.values():
                reasons[record["checksum"]].append(f"repo:{repo}")
        for snap, data in self.snapshots.items():
            for record in data["packages"].values():
                reasons[record["checksum"]].append(f"snapshot:{snap}")
        for key, data in self.published.items():
            prefix = "/".join(key)
            for record in data["packages"]:
                reasons[record["checksum"]].append(f"published:{prefix}")
        if self.pending is not None:
            prefix = "/".join(self.pending["prefix"])
            for record in self.pending["record"]["packages"]:
                reasons[record["checksum"]].append(f"pending:{prefix}")
        remove = sorted(c for c, rs in reasons.items() if not rs)
        keep = {
            c: sorted(set(rs))
            for c, rs in sorted(reasons.items())
            if rs
        }
        blocked = {}
        if self.pending is not None:
            blocked["pending_transaction"] = "/".join(self.pending["prefix"])
        return {"remove": remove, "keep": keep, "blocked": blocked}

    def cleanup_apply(self):
        self._ensure_no_pending()
        report = self.cleanup_dry_run()
        for checksum in report["remove"]:
            self.pool.pop(checksum, None)
        report = self.cleanup_dry_run()
        report["applied"] = True
        return report

    def recover(self):
        if self.pending is None:
            return {"status": "no_pending", "prefix": None}
        pending = self.pending
        self.published[pending["prefix"]] = pending["record"]
        self.pending = None
        return {"status": "completed", "prefix": "/".join(pending["prefix"])}

    def graph(self):
        edges = []
        for repo, rows in self.repos.items():
            for record in rows.values():
                edges.append({
                    "from_type": "repo",
                    "from": repo,
                    "to_type": "package",
                    "to": _identity_text(record),
                    "relation": "contains",
                })
        for snap, data in self.snapshots.items():
            for parent in data["parents"]:
                edges.append({
                    "from_type": "snapshot",
                    "from": snap,
                    "to_type": "snapshot",
                    "to": parent,
                    "relation": "derived_from",
                })
            for source in data["sources"]:
                if source in self.repos:
                    edges.append({
                        "from_type": "snapshot",
                        "from": snap,
                        "to_type": "repo",
                        "to": source,
                        "relation": "created_from",
                    })
            for record in data["packages"].values():
                edges.append({
                    "from_type": "snapshot",
                    "from": snap,
                    "to_type": "package",
                    "to": _identity_text(record),
                    "relation": "contains",
                })
        for prefix, record in self.published.items():
            prefix_text = "/".join(prefix)
            edges.append({
                "from_type": "published",
                "from": prefix_text,
                "to_type": "snapshot",
                "to": record["snapshot"],
                "relation": "publishes",
            })
            for pkg in record["packages"]:
                edges.append({
                    "from_type": "published",
                    "from": prefix_text,
                    "to_type": "package",
                    "to": _identity_text(pkg),
                    "relation": "indexes",
                })
        return sorted(edges, key=lambda e: (e["from_type"], e["from"], e["relation"], e["to_type"], e["to"]))
