"""A small dependency-free archive manager with aptly-like workflows."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path


class ArchiveError(Exception):
    """Raised when an archive operation cannot be completed."""


NAME_RE = re.compile(r"^[a-z0-9_-]+$")
VERSION_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*))*$")
ARCHES = {"amd64", "arm64", "all"}
FIELDS = {"Name", "Version", "Arch", "Depends"}


def _version_key(version: str) -> tuple[int, ...]:
    if not isinstance(version, str) or not VERSION_RE.match(version):
        raise ArchiveError(f"invalid version: {version!r}")
    parts = [int(part) for part in version.split(".")]
    while parts and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _identity(pkg: dict) -> str:
    return f"{pkg['name']}|{pkg['version']}|{pkg['arch']}"


def _identity_from_parts(name: str, version: str, arch: str) -> str:
    return f"{name}|{version}|{arch}"


def _display_identity(ident: str) -> str:
    return ident.replace("|", ":")


def _parse_identity(ident: str) -> tuple[str, str, str]:
    try:
        name, version, arch = ident.split("|", 2)
    except ValueError as exc:
        raise ArchiveError(f"corrupt package identity: {ident!r}") from exc
    return name, version, arch


def _prefix_key(distribution: str, component: str, arch: str) -> str:
    return f"{distribution}|{component}|{arch}"


def _parse_prefix(key: str) -> tuple[str, str, str]:
    try:
        return tuple(key.split("|", 2))  # type: ignore[return-value]
    except ValueError as exc:
        raise ArchiveError(f"corrupt published prefix: {key!r}") from exc


def _normalize_pkg(pkg: dict) -> dict:
    required = {"name", "version", "arch", "checksum", "depends"}
    if set(pkg) != required:
        raise ArchiveError("invalid package record")
    name = pkg["name"]
    version = pkg["version"]
    arch = pkg["arch"]
    checksum = pkg["checksum"]
    depends = pkg["depends"]
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise ArchiveError(f"invalid package name: {name!r}")
    _version_key(version)
    if arch not in ARCHES:
        raise ArchiveError(f"invalid architecture: {arch!r}")
    if not isinstance(checksum, str) or not re.match(r"^[0-9a-f]{64}$", checksum):
        raise ArchiveError("invalid checksum")
    if not isinstance(depends, str):
        raise ArchiveError("invalid dependency field")
    return {
        "name": name,
        "version": version,
        "arch": arch,
        "checksum": checksum,
        "depends": depends,
    }


def _sort_packages(packages) -> list[dict]:
    return [
        copy.deepcopy(pkg)
        for pkg in sorted(
            packages,
            key=lambda p: (p["name"], p["arch"], _version_key(p["version"]), p["version"], p["checksum"]),
        )
    ]


def _index_digest(packages: list[dict]) -> str:
    payload = json.dumps(_sort_packages(packages), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_package(path) -> dict:
    """Parse a simplified package artifact."""

    artifact = Path(path)
    try:
        raw = artifact.read_bytes()
    except OSError as exc:
        raise ArchiveError(f"cannot read package artifact: {artifact}") from exc

    split = raw.find(b"\n\n")
    separator_len = 2
    if split < 0:
        split = raw.find(b"\r\n\r\n")
        separator_len = 4
    if split < 0:
        raise ArchiveError("artifact is missing blank line before payload")

    header_bytes = raw[:split]
    payload = raw[split + separator_len :]
    try:
        header_text = header_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArchiveError("control stanza is not valid UTF-8") from exc

    values: dict[str, str] = {}
    for line in header_text.replace("\r\n", "\n").split("\n"):
        if not line:
            raise ArchiveError("blank line inside control stanza")
        if ":" not in line:
            raise ArchiveError(f"malformed control line: {line!r}")
        key, value = line.split(":", 1)
        value = value.strip()
        if key not in FIELDS:
            raise ArchiveError(f"unknown control field: {key!r}")
        if key in values:
            raise ArchiveError(f"duplicate control field: {key!r}")
        values[key] = value

    missing = FIELDS - set(values)
    if missing:
        raise ArchiveError(f"missing control field: {sorted(missing)[0]}")

    record = {
        "name": values["Name"],
        "version": values["Version"],
        "arch": values["Arch"],
        "depends": values["Depends"],
        "checksum": hashlib.sha256(payload).hexdigest(),
    }
    return _normalize_pkg(record)


class MiniAptly:
    """Manage simplified package repositories, snapshots, publications, and cleanup."""

    def __init__(self, root=None):
        self.root = Path(root) if root is not None else Path(tempfile.mkdtemp(prefix="miniaptly-"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.pool_dir = self.root / "pool"
        self.publish_dir = self.root / "public"
        self.state_path = self.root / "state.json"
        self.pool_dir.mkdir(parents=True, exist_ok=True)
        self.publish_dir.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._write_state(self._empty_state())

    def parse_package(self, path) -> dict:
        return parse_package(path)

    @staticmethod
    def _empty_state() -> dict:
        return {
            "packages": {},
            "repos": {},
            "snapshots": {},
            "published": {},
            "pending": None,
        }

    def _read_state(self) -> dict:
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
        except FileNotFoundError:
            state = self._empty_state()
        except (OSError, json.JSONDecodeError) as exc:
            raise ArchiveError("cannot read archive state") from exc

        for key, default in self._empty_state().items():
            state.setdefault(key, copy.deepcopy(default))
        return state

    def _write_state(self, state: dict) -> None:
        tmp = self.state_path.with_suffix(".json.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump(state, handle, sort_keys=True, indent=2)
            last_error = None
            for _ in range(6):
                try:
                    os.replace(tmp, self.state_path)
                    last_error = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.05)
            if last_error is not None:
                raise last_error
        except OSError as exc:
            raise ArchiveError("cannot write archive state") from exc
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass

    def _require_no_pending(self, state: dict) -> None:
        if state.get("pending") is not None:
            pending = state["pending"]
            raise ArchiveError(f"pending transaction requires recovery: {pending.get('prefix', '')}")

    def _committed_view_state(self, state: dict) -> dict:
        view = copy.deepcopy(state)
        pending = view.get("pending")
        if pending is not None:
            prefix = pending["prefix"]
            previous = pending.get("previous")
            if previous is None:
                view["published"].pop(prefix, None)
            else:
                view["published"][prefix] = previous
        return view

    def _pool_path(self, checksum: str) -> Path:
        return self.pool_dir / checksum

    def _package_records(self, state: dict, identities) -> list[dict]:
        records = []
        for ident in identities:
            if ident not in state["packages"]:
                raise ArchiveError(f"missing package: {_display_identity(ident)}")
            records.append(copy.deepcopy(state["packages"][ident]))
        return _sort_packages(records)

    def _source_identities(self, state: dict, source: str) -> set[str]:
        if source in state["repos"]:
            return set(state["repos"][source])
        if source in state["snapshots"]:
            return set(state["snapshots"][source]["packages"])
        raise ArchiveError(f"unknown source: {source}")

    def add(self, repo: str, package_path) -> dict:
        pkg = parse_package(package_path)
        state = self._read_state()
        self._require_no_pending(state)

        ident = _identity(pkg)
        existing = state["packages"].get(ident)
        if existing is not None and existing["checksum"] != pkg["checksum"]:
            raise ArchiveError("package identity already exists with different checksum")

        new_state = copy.deepcopy(state)
        new_state["repos"].setdefault(repo, [])
        pool_path = self._pool_path(pkg["checksum"])
        if existing is None:
            new_state["packages"][ident] = copy.deepcopy(pkg)
        if not pool_path.exists():
            try:
                shutil.copyfile(package_path, pool_path)
            except OSError as exc:
                raise ArchiveError("cannot import package artifact") from exc
        if ident not in new_state["repos"][repo]:
            new_state["repos"][repo].append(ident)
        self._write_state(new_state)
        return copy.deepcopy(pkg)

    def remove(self, repo: str, name: str, version=None, arch=None) -> list[dict]:
        state = self._read_state()
        self._require_no_pending(state)
        if repo not in state["repos"]:
            raise ArchiveError(f"unknown repo: {repo}")

        removed = []
        remaining = []
        for ident in state["repos"][repo]:
            pkg = state["packages"][ident]
            match = pkg["name"] == name
            match = match and (version is None or pkg["version"] == version)
            match = match and (arch is None or pkg["arch"] == arch)
            if match:
                removed.append(ident)
            else:
                remaining.append(ident)

        new_state = copy.deepcopy(state)
        new_state["repos"][repo] = remaining
        self._write_state(new_state)
        return self._package_records(state, removed)

    def repo_show(self, repo: str) -> list[dict]:
        state = self._read_state()
        if repo not in state["repos"]:
            raise ArchiveError(f"unknown repo: {repo}")
        return self._package_records(state, state["repos"][repo])

    def repo_search(self, repo: str, **predicates) -> list[dict]:
        allowed = {"name", "arch", "min_version"}
        unknown = set(predicates) - allowed
        if unknown:
            raise ArchiveError(f"unknown search predicate: {sorted(unknown)[0]}")
        records = self.repo_show(repo)
        result = []
        for pkg in records:
            if "name" in predicates and pkg["name"] != predicates["name"]:
                continue
            if "arch" in predicates and pkg["arch"] != predicates["arch"]:
                continue
            if "min_version" in predicates and _version_key(pkg["version"]) < _version_key(predicates["min_version"]):
                continue
            result.append(pkg)
        return _sort_packages(result)

    def snapshot_create(self, name: str, source: str) -> dict:
        state = self._read_state()
        self._require_no_pending(state)
        if name in state["snapshots"]:
            raise ArchiveError(f"snapshot already exists: {name}")
        identities = self._source_identities(state, source)
        new_state = copy.deepcopy(state)
        new_state["snapshots"][name] = {
            "name": name,
            "sources": [source],
            "packages": sorted(identities),
            "parents": [source] if source in state["snapshots"] else [],
        }
        self._write_state(new_state)
        return self.snapshot_show(name)

    def snapshot_merge(self, name: str, sources, *, first_wins=False) -> dict:
        state = self._read_state()
        self._require_no_pending(state)
        if name in state["snapshots"]:
            raise ArchiveError(f"snapshot already exists: {name}")
        sources = list(sources)
        if not sources:
            raise ArchiveError("merge requires at least one source snapshot")
        for source in sources:
            if source not in state["snapshots"]:
                raise ArchiveError(f"unknown snapshot: {source}")

        selected: dict[tuple[str, str], str] = {}
        selected_by_identity: dict[str, str] = {}
        for source in sources:
            for ident in state["snapshots"][source]["packages"]:
                pkg = state["packages"][ident]
                if ident in selected_by_identity and selected_by_identity[ident] != pkg["checksum"]:
                    raise ArchiveError("same package identity has conflicting checksums")
                selected_by_identity[ident] = pkg["checksum"]

                key = (pkg["name"], pkg["arch"])
                current_ident = selected.get(key)
                if current_ident is None:
                    selected[key] = ident
                    continue
                current = state["packages"][current_ident]
                if current_ident == ident:
                    continue
                if current["version"] == pkg["version"] and current["checksum"] != pkg["checksum"]:
                    raise ArchiveError("same package identity has conflicting checksums")
                if first_wins:
                    continue
                if _version_key(pkg["version"]) > _version_key(current["version"]):
                    selected[key] = ident

        new_state = copy.deepcopy(state)
        new_state["snapshots"][name] = {
            "name": name,
            "sources": sources,
            "packages": sorted(selected.values()),
            "parents": sources,
        }
        self._write_state(new_state)
        return self.snapshot_show(name)

    def snapshot_filter(self, name: str, source: str, *, name_filter=None, arch=None, min_version=None) -> dict:
        state = self._read_state()
        self._require_no_pending(state)
        if name in state["snapshots"]:
            raise ArchiveError(f"snapshot already exists: {name}")
        if source not in state["snapshots"]:
            raise ArchiveError(f"unknown snapshot: {source}")

        selected = []
        for ident in state["snapshots"][source]["packages"]:
            pkg = state["packages"][ident]
            if name_filter is not None and pkg["name"] != name_filter:
                continue
            if arch is not None and pkg["arch"] != arch:
                continue
            if min_version is not None and _version_key(pkg["version"]) < _version_key(min_version):
                continue
            selected.append(ident)

        new_state = copy.deepcopy(state)
        new_state["snapshots"][name] = {
            "name": name,
            "sources": [source],
            "packages": sorted(selected),
            "parents": [source],
        }
        self._write_state(new_state)
        return self.snapshot_show(name)

    def snapshot_show(self, name: str) -> dict:
        state = self._read_state()
        if name not in state["snapshots"]:
            raise ArchiveError(f"unknown snapshot: {name}")
        snap = state["snapshots"][name]
        return {
            "name": snap["name"],
            "sources": list(snap.get("sources", [])),
            "packages": self._package_records(state, snap["packages"]),
            "parents": list(snap.get("parents", [])),
        }

    def snapshot_diff(self, left: str, right: str) -> dict:
        state = self._read_state()
        if left not in state["snapshots"] or right not in state["snapshots"]:
            raise ArchiveError("unknown snapshot")
        left_by_slot = {}
        for ident in state["snapshots"][left]["packages"]:
            pkg = state["packages"][ident]
            left_by_slot[(pkg["name"], pkg["arch"])] = pkg
        right_by_slot = {}
        for ident in state["snapshots"][right]["packages"]:
            pkg = state["packages"][ident]
            right_by_slot[(pkg["name"], pkg["arch"])] = pkg

        added = []
        removed = []
        changed = []
        for key, pkg in right_by_slot.items():
            if key not in left_by_slot:
                added.append(pkg)
            elif (
                left_by_slot[key]["version"] != pkg["version"]
                or left_by_slot[key]["checksum"] != pkg["checksum"]
                or left_by_slot[key]["depends"] != pkg["depends"]
            ):
                changed.append({"from": copy.deepcopy(left_by_slot[key]), "to": copy.deepcopy(pkg)})
        for key, pkg in left_by_slot.items():
            if key not in right_by_slot:
                removed.append(pkg)

        changed.sort(key=lambda c: (c["from"]["name"], c["from"]["arch"], c["from"]["version"], c["to"]["version"]))
        return {"added": _sort_packages(added), "removed": _sort_packages(removed), "changed": changed}

    def publish(self, snapshot: str, distribution: str, component: str, arch: str) -> dict:
        state = self._read_state()
        self._require_no_pending(state)
        if snapshot not in state["snapshots"]:
            raise ArchiveError(f"unknown snapshot: {snapshot}")
        if arch not in ARCHES:
            raise ArchiveError(f"invalid architecture: {arch}")
        key = _prefix_key(distribution, component, arch)
        if key in state["published"]:
            raise ArchiveError("published prefix already exists")
        return self._publish_transaction(snapshot, distribution, component, arch, fail_at=None, previous=None)

    def publish_switch(self, snapshot: str, distribution: str, component: str, arch: str, *, fail_at=None) -> dict:
        state = self._read_state()
        self._require_no_pending(state)
        if snapshot not in state["snapshots"]:
            raise ArchiveError(f"unknown snapshot: {snapshot}")
        key = _prefix_key(distribution, component, arch)
        if key not in state["published"]:
            raise ArchiveError("published prefix does not exist")
        previous = copy.deepcopy(state["published"][key])
        return self._publish_transaction(snapshot, distribution, component, arch, fail_at=fail_at, previous=previous)

    def _publish_transaction(self, snapshot: str, distribution: str, component: str, arch: str, *, fail_at, previous) -> dict:
        if fail_at not in {None, "after_journal", "after_index", "after_publish_record"}:
            raise ArchiveError(f"unsupported fail_at hook: {fail_at}")
        state = self._read_state()
        package_identities = [
            ident
            for ident in state["snapshots"][snapshot]["packages"]
            if state["packages"][ident]["arch"] in {arch, "all"}
        ]
        packages = self._package_records(state, package_identities)
        key = _prefix_key(distribution, component, arch)
        record = {
            "distribution": distribution,
            "component": component,
            "arch": arch,
            "snapshot": snapshot,
            "packages": packages,
            "index_digest": _index_digest(packages),
        }
        pending = {
            "op": "publish",
            "prefix": key,
            "record": record,
            "previous": previous,
            "stage": "journal",
        }

        new_state = copy.deepcopy(state)
        new_state["pending"] = pending
        self._write_state(new_state)
        if fail_at == "after_journal":
            raise ArchiveError("simulated publish failure after journal")

        self._materialize_index(record)
        staged_state = self._read_state()
        staged_state["pending"]["stage"] = "index"
        self._write_state(staged_state)
        if fail_at == "after_index":
            raise ArchiveError("simulated publish failure after index")

        committed = self._read_state()
        committed["published"][key] = copy.deepcopy(record)
        committed["pending"]["stage"] = "publish_record"
        self._write_state(committed)
        if fail_at == "after_publish_record":
            raise ArchiveError("simulated publish failure after publish record")

        final_state = self._read_state()
        final_state["pending"] = None
        self._write_state(final_state)
        return self.publish_show(distribution, component, arch)

    def _prefix_dir(self, record: dict) -> Path:
        return self.publish_dir / record["distribution"] / record["component"] / record["arch"]

    def _materialize_index(self, record: dict) -> None:
        prefix = self._prefix_dir(record)
        tmp = prefix.with_name(prefix.name + ".tmp")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True, exist_ok=True)
        index_path = tmp / "index.json"
        try:
            with index_path.open("w", encoding="utf-8") as handle:
                json.dump(record["packages"], handle, sort_keys=True, indent=2)
            digest_path = tmp / "index.sha256"
            digest_path.write_text(record["index_digest"], encoding="utf-8")
            if prefix.exists():
                shutil.rmtree(prefix)
            os.replace(tmp, prefix)
        except OSError as exc:
            raise ArchiveError("cannot materialize published index") from exc
        finally:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)

    def publish_show(self, distribution: str, component: str, arch: str) -> dict:
        state = self._committed_view_state(self._read_state())
        key = _prefix_key(distribution, component, arch)
        if key not in state["published"]:
            raise ArchiveError("unknown published prefix")
        return copy.deepcopy(state["published"][key])

    def published_index(self, distribution: str, component: str, arch: str) -> list[dict]:
        return copy.deepcopy(self.publish_show(distribution, component, arch)["packages"])

    def cleanup_dry_run(self) -> dict:
        raw_state = self._read_state()
        state = self._committed_view_state(raw_state)
        keep_reasons = self._checksum_reasons(state)
        blocked_reasons = {}
        pending = raw_state.get("pending")
        if pending is not None:
            for pkg in pending["record"]["packages"]:
                blocked_reasons.setdefault(pkg["checksum"], set()).add(f"pending:{pending['prefix']}")

        all_checksums = {pkg["checksum"] for pkg in state["packages"].values()}
        for path in self.pool_dir.iterdir() if self.pool_dir.exists() else []:
            if path.is_file():
                all_checksums.add(path.name)

        keep = {checksum: sorted(reasons) for checksum, reasons in keep_reasons.items() if reasons}
        blocked = {checksum: sorted(reasons) for checksum, reasons in blocked_reasons.items() if reasons}
        remove = sorted(checksum for checksum in all_checksums if checksum not in keep and checksum not in blocked)
        return {"remove": remove, "keep": keep, "blocked": blocked}

    def cleanup_apply(self) -> dict:
        state = self._read_state()
        self._require_no_pending(state)
        report = self.cleanup_dry_run()
        for checksum in report["remove"]:
            path = self._pool_path(checksum)
            if path.exists():
                try:
                    path.unlink()
                except OSError as exc:
                    raise ArchiveError(f"cannot remove pool artifact: {checksum}") from exc
        report["applied"] = True
        return report

    def _checksum_reasons(self, state: dict) -> dict[str, set[str]]:
        reasons: dict[str, set[str]] = {}

        def mark(ident: str, reason: str) -> None:
            pkg = state["packages"].get(ident)
            if pkg:
                reasons.setdefault(pkg["checksum"], set()).add(reason)

        for repo, identities in state["repos"].items():
            for ident in identities:
                mark(ident, f"repo:{repo}")
        for snapshot, snap in state["snapshots"].items():
            for ident in snap["packages"]:
                mark(ident, f"snapshot:{snapshot}")
        for prefix, record in state["published"].items():
            for pkg in record["packages"]:
                reasons.setdefault(pkg["checksum"], set()).add(f"published:{prefix}")
        return reasons

    def recover(self) -> dict:
        state = self._read_state()
        pending = state.get("pending")
        if pending is None:
            return {"status": "no_pending", "prefix": None}

        prefix = pending["prefix"]
        record = pending["record"]
        previous = pending.get("previous")
        new_state = copy.deepcopy(state)
        if pending.get("stage") == "journal":
            if previous is None:
                new_state["published"].pop(prefix, None)
            else:
                new_state["published"][prefix] = previous
                self._materialize_index(previous)
            new_state["pending"] = None
            self._write_state(new_state)
            return {"status": "rolled_back", "prefix": prefix}

        self._materialize_index(record)
        new_state["published"][prefix] = record
        new_state["pending"] = None
        self._write_state(new_state)
        return {"status": "completed", "prefix": prefix}

    def graph(self) -> list[dict]:
        raw_state = self._read_state()
        state = self._committed_view_state(raw_state)
        edges = []

        def add_edge(from_type, from_name, to_type, to_name, relation):
            edges.append(
                {
                    "from_type": from_type,
                    "from": from_name,
                    "to_type": to_type,
                    "to": to_name,
                    "relation": relation,
                }
            )

        for repo, identities in state["repos"].items():
            for ident in identities:
                add_edge("repo", repo, "package", _display_identity(ident), "contains")
        for snap_name, snap in state["snapshots"].items():
            for source in snap.get("parents", []):
                add_edge("snapshot", snap_name, "snapshot", source, "parent")
            for source in snap.get("sources", []):
                if source in state["repos"]:
                    add_edge("snapshot", snap_name, "repo", source, "source")
                elif source in state["snapshots"] and source not in snap.get("parents", []):
                    add_edge("snapshot", snap_name, "snapshot", source, "source")
            for ident in snap["packages"]:
                add_edge("snapshot", snap_name, "package", _display_identity(ident), "contains")
        for prefix, record in state["published"].items():
            add_edge("published", prefix, "snapshot", record["snapshot"], "publishes")
            for pkg in record["packages"]:
                add_edge("published", prefix, "package", _display_identity(_identity(pkg)), "contains")
        pending = raw_state.get("pending")
        if pending is not None:
            add_edge("pending", pending["prefix"], "snapshot", pending["record"]["snapshot"], "publishes")
            for pkg in pending["record"]["packages"]:
                add_edge("pending", pending["prefix"], "package", _display_identity(_identity(pkg)), "contains")

        return sorted(edges, key=lambda e: (e["from_type"], e["from"], e["to_type"], e["to"], e["relation"]))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MiniAptly archive manager")
    parser.add_argument("--root", default=".", help="archive root")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("repo")
    p_add.add_argument("package")

    p_repo = sub.add_parser("repo-show")
    p_repo.add_argument("repo")

    p_snap = sub.add_parser("snapshot-create")
    p_snap.add_argument("name")
    p_snap.add_argument("source")

    p_show = sub.add_parser("snapshot-show")
    p_show.add_argument("name")

    p_pub = sub.add_parser("publish")
    p_pub.add_argument("snapshot")
    p_pub.add_argument("distribution")
    p_pub.add_argument("component")
    p_pub.add_argument("arch")

    p_ps = sub.add_parser("publish-show")
    p_ps.add_argument("distribution")
    p_ps.add_argument("component")
    p_ps.add_argument("arch")

    sub.add_parser("cleanup-dry-run")
    sub.add_parser("recover")
    sub.add_parser("graph")
    args = parser.parse_args(argv)
    api = MiniAptly(args.root)

    if args.command == "add":
        result = api.add(args.repo, args.package)
    elif args.command == "repo-show":
        result = api.repo_show(args.repo)
    elif args.command == "snapshot-create":
        result = api.snapshot_create(args.name, args.source)
    elif args.command == "snapshot-show":
        result = api.snapshot_show(args.name)
    elif args.command == "publish":
        result = api.publish(args.snapshot, args.distribution, args.component, args.arch)
    elif args.command == "publish-show":
        result = api.publish_show(args.distribution, args.component, args.arch)
    elif args.command == "cleanup-dry-run":
        result = api.cleanup_dry_run()
    elif args.command == "recover":
        result = api.recover()
    elif args.command == "graph":
        result = api.graph()
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
