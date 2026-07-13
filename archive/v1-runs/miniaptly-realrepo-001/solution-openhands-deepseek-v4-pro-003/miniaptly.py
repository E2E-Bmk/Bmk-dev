"""
MiniAptly - dependency-free Python archive manager.

Inspired by aptly-style package repository workflows. Manages simplified
package artifacts, local repositories, immutable snapshots, published
repository trees, cleanup reachability, recovery, and graph projections.
"""

import hashlib
import json
import os
import re
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ArchiveError(Exception):
    """Base exception for MiniAptly operations."""


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def _parse_version_tuple(version_str):
    """Parse a dot-separated version into a tuple of ints, trailing zeros trimmed."""
    if not re.match(r'^\d+(\.\d+)*$', version_str):
        raise ArchiveError(f"Invalid version format: {version_str}")
    parts = tuple(int(x) for x in version_str.split('.'))
    while len(parts) > 1 and parts[-1] == 0:
        parts = parts[:-1]
    return parts


def _version_less_than(a, b):
    """Compare two version strings using trailing-zero-trimmed tuple ordering."""
    return _parse_version_tuple(a) < _parse_version_tuple(b)


# ---------------------------------------------------------------------------
# Package helpers
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r'^[a-z0-9_-]+$')
_VALID_ARCHES = {'amd64', 'arm64', 'all'}


def _pkg_identity_str(name, version, arch):
    return f"{name}={version}_{arch}"


def _pkg_name_arch_key(name, arch):
    return f"{name}_{arch}"


def _parse_artifact_text(text):
    """Parse artifact text; return (control_dict, payload, checksum)."""
    idx = text.find('\n\n')
    if idx == -1:
        raise ArchiveError("Missing blank line between control stanza and payload")

    control_text = text[:idx]
    payload = text[idx + 2:]  # skip the blank line
    checksum = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    fields = {}
    for line in control_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if ':' not in line:
            raise ArchiveError(f"Malformed control line: {line!r}")
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()
        if key in fields:
            raise ArchiveError(f"Duplicate field '{key}' in control stanza")
        fields[key] = value

    return fields, payload, checksum


def _validate_package_fields(fields):
    """Validate required fields and return a package record dict."""
    name = fields.get('Name', '')
    version = fields.get('Version', '')
    arch = fields.get('Arch', '')
    depends = fields.get('Depends', '')

    if not name:
        raise ArchiveError("Missing Name field")
    if not _NAME_RE.match(name):
        raise ArchiveError(f"Invalid package name: {name!r}")

    if not version:
        raise ArchiveError("Missing Version field")
    try:
        _parse_version_tuple(version)
    except ArchiveError:
        raise
    except Exception:
        raise ArchiveError(f"Invalid version: {version!r}")

    if arch not in _VALID_ARCHES:
        raise ArchiveError(f"Invalid architecture: {arch!r}")

    checksum = fields.get('_checksum', '')
    if not checksum:
        raise ArchiveError("Missing checksum (internal)")

    return {
        'name': name,
        'version': version,
        'arch': arch,
        'checksum': checksum,
        'depends': depends,
    }


def _artifact_to_package_record(text):
    """Parse full artifact text into a package record."""
    fields, payload, checksum = _parse_artifact_text(text)
    fields['_checksum'] = checksum
    return _validate_package_fields(fields)


def _pool_to_package_record(text, checksum):
    """Re-parse pool artifact text into a package record (checksum already known)."""
    fields, _, _ = _parse_artifact_text(text)
    fields['_checksum'] = checksum
    return _validate_package_fields(fields)


def _pkg_sort_key(p):
    return (p['name'], _parse_version_tuple(p['version']), p['arch'])


# ---------------------------------------------------------------------------
# parse_package  (module-level)
# ---------------------------------------------------------------------------

def parse_package(path):
    """Parse a package artifact file; return a package record dict."""
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    return _artifact_to_package_record(text)


# ---------------------------------------------------------------------------
# MiniAptly
# ---------------------------------------------------------------------------

class MiniAptly:
    """Archive manager for simplified package artifacts."""

    def __init__(self, root):
        self.root = Path(root)
        self._ensure_dirs()

    # ── directory scaffolding ──────────────────────────────────────

    def _ensure_dirs(self):
        for sub in ('pool', 'repos', 'snapshots', 'publishes', 'publish_index'):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    # ── path helpers ───────────────────────────────────────────────

    def _pool_path(self, checksum):
        return self.root / 'pool' / checksum

    def _repo_path(self, name):
        return self.root / 'repos' / f"{name}.json"

    def _snapshot_path(self, name):
        return self.root / 'snapshots' / f"{name}.json"

    def _publish_dir(self, distribution, component):
        d = self.root / 'publishes' / distribution / component
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _publish_path(self, distribution, component, arch):
        return self._publish_dir(distribution, component) / f"{arch}.json"

    def _publish_index_path(self, distribution, component, arch):
        d = self.root / 'publish_index' / distribution / component
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{arch}.json"

    def _journal_path(self):
        return self.root / 'journal.json'

    # ── pool operations ───────────────────────────────────────────

    def _pool_read_package(self, checksum):
        path = self._pool_path(checksum)
        if not path.exists():
            raise ArchiveError(f"Pool artifact not found: {checksum}")
        text = path.read_text(encoding='utf-8')
        return _pool_to_package_record(text, checksum)

    def _pool_write(self, checksum, artifact_text):
        path = self._pool_path(checksum)
        if not path.exists():
            path.write_text(artifact_text, encoding='utf-8')

    def _pool_delete(self, checksum):
        path = self._pool_path(checksum)
        if path.exists():
            path.unlink()

    def _pool_all_checksums(self):
        pool_dir = self.root / 'pool'
        if not pool_dir.exists():
            return set()
        return {p.name for p in pool_dir.iterdir() if p.is_file()}

    # ── journal / pending ─────────────────────────────────────────

    def _has_pending(self):
        return self._journal_path().exists()

    def _read_journal(self):
        path = self._journal_path()
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding='utf-8'))

    def _write_journal(self, data):
        self._journal_path().write_text(
            json.dumps(data, indent=2), encoding='utf-8')

    def _clear_journal(self):
        p = self._journal_path()
        if p.exists():
            p.unlink()

    def _check_not_pending(self):
        if self._has_pending():
            raise ArchiveError(
                "A pending transaction exists; run recover() first")

    # ── repo helpers ──────────────────────────────────────────────

    def _repo_load(self, name):
        path = self._repo_path(name)
        if not path.exists():
            raise ArchiveError(f"Repository not found: {name}")
        return json.loads(path.read_text(encoding='utf-8'))

    def _repo_save(self, name, data):
        self._repo_path(name).write_text(
            json.dumps(data, indent=2), encoding='utf-8')

    def _repo_list_packages(self, name):
        """Return list of package records for a repo."""
        data = self._repo_load(name)
        pkgs = []
        for _ident, checksum in data.items():
            try:
                pkgs.append(self._pool_read_package(checksum))
            except ArchiveError:
                pass
        pkgs.sort(key=_pkg_sort_key)
        return pkgs

    # ── snapshot helpers ──────────────────────────────────────────

    def _snap_load(self, name):
        path = self._snapshot_path(name)
        if not path.exists():
            raise ArchiveError(f"Snapshot not found: {name}")
        return json.loads(path.read_text(encoding='utf-8'))

    def _snap_save(self, name, data):
        self._snapshot_path(name).write_text(
            json.dumps(data, indent=2), encoding='utf-8')

    def _resolve_source_packages(self, source):
        """Return identity_str→checksum dict for a source (repo or snapshot)."""
        # Try snapshot first
        sp = self._snapshot_path(source)
        if sp.exists():
            snap = json.loads(sp.read_text(encoding='utf-8'))
            return {
                _pkg_identity_str(p['name'], p['version'], p['arch']): p['checksum']
                for p in snap['packages']
            }
        # Then repo
        rp = self._repo_path(source)
        if rp.exists():
            return json.loads(rp.read_text(encoding='utf-8'))
        raise ArchiveError(f"Source not found: {source}")

    def _resolve_source_full(self, source):
        """Return list of full package records from a source."""
        pkg_map = self._resolve_source_packages(source)
        return [self._pool_read_package(cs) for cs in pkg_map.values()]

    # ── publish helpers ───────────────────────────────────────────

    def _read_publish_metadata(self, distribution, component, arch):
        path = self.root / 'publishes' / distribution / component / f"{arch}.json"
        if not path.exists():
            raise ArchiveError(
                f"Published prefix not found: {distribution}/{component}/{arch}")
        return json.loads(path.read_text(encoding='utf-8'))

    def _read_publish_index(self, distribution, component, arch):
        path = self.root / 'publish_index' / distribution / component / f"{arch}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding='utf-8'))

    def _compute_index_digest(self, packages):
        sorted_pkgs = sorted(packages, key=_pkg_sort_key)
        payload = json.dumps(sorted_pkgs, sort_keys=True)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _filter_by_arch(self, packages, arch):
        """Filter packages for a published index by arch."""
        if arch == 'all':
            return list(packages)
        return [p for p in packages if p['arch'] in (arch, 'all')]

    # ── reachability ──────────────────────────────────────────────

    def _committed_checksums(self):
        """Set of checksums reachable from repos, snapshots, published indexes."""
        cs = set()
        # repos
        repos_dir = self.root / 'repos'
        if repos_dir.exists():
            for f in repos_dir.iterdir():
                if f.suffix == '.json':
                    cs.update(json.loads(f.read_text(encoding='utf-8')).values())
        # snapshots
        snaps_dir = self.root / 'snapshots'
        if snaps_dir.exists():
            for f in snaps_dir.iterdir():
                if f.suffix == '.json':
                    for p in json.loads(f.read_text(encoding='utf-8')).get('packages', []):
                        cs.add(p['checksum'])
        # published indexes
        idx_dir = self.root / 'publish_index'
        if idx_dir.exists():
            for dist_d in idx_dir.iterdir():
                if dist_d.is_dir():
                    for comp_d in dist_d.iterdir():
                        if comp_d.is_dir():
                            for f in comp_d.iterdir():
                                if f.suffix == '.json':
                                    for p in json.loads(f.read_text(encoding='utf-8')):
                                        cs.add(p['checksum'])
        return cs

    def _pending_checksums(self):
        """Set of checksums reachable only from the pending transaction."""
        if not self._has_pending():
            return set()
        journal = self._read_journal()
        target = journal.get('target_snapshot')
        if not target:
            return set()
        sp = self._snapshot_path(target)
        if not sp.exists():
            return set()
        snap = json.loads(sp.read_text(encoding='utf-8'))
        prefix = journal.get('prefix', '')
        parts = prefix.split('/') if prefix else []
        arch = parts[2] if len(parts) == 3 else 'all'
        pkgs = self._filter_by_arch(snap['packages'], arch)
        return {p['checksum'] for p in pkgs}

    def _reachable_checksums(self):
        return self._committed_checksums() | self._pending_checksums()

    # =================================================================
    # Public API
    # =================================================================

    # ── Package / Repo ─────────────────────────────────────────────

    def add(self, repo, package_path):
        """Import a package artifact into a local repository."""
        self._check_not_pending()

        with open(package_path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        pkg = _artifact_to_package_record(text)
        checksum = pkg['checksum']

        rp = self._repo_path(repo)
        if rp.exists():
            data = json.loads(rp.read_text(encoding='utf-8'))
        else:
            data = {}

        ident = _pkg_identity_str(pkg['name'], pkg['version'], pkg['arch'])

        if ident in data:
            existing_cs = data[ident]
            if existing_cs != checksum:
                raise ArchiveError(
                    f"Package {ident} already exists with a different checksum")
            # same identity, same checksum → idempotent
            return

        self._pool_write(checksum, text)
        data[ident] = checksum
        self._repo_save(repo, data)

    def remove(self, repo, name, version=None, arch=None):
        """Remove matching package identities from a local repository."""
        self._check_not_pending()
        data = self._repo_load(repo)

        to_remove = []
        for ident_str, checksum in data.items():
            pkg_name, rest = ident_str.split('=', 1)
            pkg_version, pkg_arch = rest.rsplit('_', 1)
            if pkg_name != name:
                continue
            if version is not None and pkg_version != version:
                continue
            if arch is not None and pkg_arch != arch:
                continue
            to_remove.append(ident_str)

        for i in to_remove:
            del data[i]
        self._repo_save(repo, data)
        # Pool artifacts are NOT deleted — they may be referenced elsewhere.

    def repo_show(self, repo):
        """Return sorted list of package records for a repository."""
        return self._repo_list_packages(repo)

    def repo_search(self, repo, **predicates):
        """Search a repository's packages; supports name, arch, min_version."""
        pkgs = self._repo_list_packages(repo)
        results = []
        for p in pkgs:
            if 'name' in predicates and p['name'] != predicates['name']:
                continue
            if 'arch' in predicates and p['arch'] != predicates['arch']:
                continue
            if 'min_version' in predicates:
                if _version_less_than(p['version'], predicates['min_version']):
                    continue
            results.append(p)
        return results

    # ── Snapshots ──────────────────────────────────────────────────

    def snapshot_create(self, name, source):
        """Create an immutable snapshot from a repository or snapshot."""
        self._check_not_pending()

        sp = self._snapshot_path(name)
        if sp.exists():
            raise ArchiveError(f"Snapshot already exists: {name}")

        packages = self._resolve_source_full(source)

        # Determine parents
        src_sp = self._snapshot_path(source)
        if src_sp.exists():
            src_snap = json.loads(src_sp.read_text(encoding='utf-8'))
            parents = [source] + src_snap.get('parents', [])
        else:
            parents = []

        snap = {
            'name': name,
            'sources': [source],
            'parents': parents,
            'packages': packages,
        }
        self._snap_save(name, snap)

    def snapshot_merge(self, name, sources, *, first_wins=False):
        """Merge multiple snapshots into a new immutable snapshot."""
        self._check_not_pending()

        if self._snapshot_path(name).exists():
            raise ArchiveError(f"Snapshot already exists: {name}")

        merged = {}          # (name, arch) → (version_tuple, checksum, pkg_record)
        all_parents = set()

        for src in sources:
            snap = self._snap_load(src)
            all_parents.add(src)
            for par in snap.get('parents', []):
                all_parents.add(par)

            for p in snap['packages']:
                key = (p['name'], p['arch'])
                vt = _parse_version_tuple(p['version'])

                if key not in merged:
                    merged[key] = (vt, p['checksum'], p)
                    continue

                evt, ecs, existing = merged[key]

                if first_wins:
                    # Keep existing; only fail on checksum conflict at same version
                    if vt == evt and p['checksum'] != ecs:
                        raise ArchiveError(
                            f"Checksum conflict for {p['name']}={p['version']}_{p['arch']}")
                    continue

                # Higher-version-wins (default)
                if vt > evt:
                    merged[key] = (vt, p['checksum'], p)
                elif vt == evt:
                    if p['checksum'] != ecs:
                        raise ArchiveError(
                            f"Checksum conflict for {p['name']}={p['version']}_{p['arch']}")

        packages = [pkg for _vt, _cs, pkg in merged.values()]

        snap = {
            'name': name,
            'sources': list(sources),
            'parents': sorted(all_parents),
            'packages': packages,
        }
        self._snap_save(name, snap)

    def snapshot_filter(self, name, source, *,
                        name_filter=None, arch=None, min_version=None):
        """Create a filtered snapshot from a source."""
        self._check_not_pending()

        if self._snapshot_path(name).exists():
            raise ArchiveError(f"Snapshot already exists: {name}")

        snap = self._snap_load(source)
        filtered = []
        for p in snap['packages']:
            if name_filter is not None and p['name'] != name_filter:
                continue
            if arch is not None and p['arch'] != arch:
                continue
            if min_version is not None:
                if _version_less_than(p['version'], min_version):
                    continue
            filtered.append(p)

        parents = [source] + snap.get('parents', [])

        new_snap = {
            'name': name,
            'sources': [source],
            'parents': parents,
            'packages': filtered,
        }
        self._snap_save(name, new_snap)

    def snapshot_show(self, name):
        """Return the semantic snapshot record."""
        snap = self._snap_load(name)
        return {
            'name': snap['name'],
            'sources': snap['sources'],
            'packages': snap['packages'],
            'parents': snap.get('parents', []),
        }

    def snapshot_diff(self, left, right):
        """Return semantic {added, removed, changed} between two snapshots."""
        ls = self._snap_load(left)
        rs = self._snap_load(right)

        lm = {_pkg_name_arch_key(p['name'], p['arch']): p for p in ls['packages']}
        rm = {_pkg_name_arch_key(p['name'], p['arch']): p for p in rs['packages']}

        lk = set(lm)
        rk = set(rm)

        added = [rm[k] for k in sorted(rk - lk)]
        removed = [lm[k] for k in sorted(lk - rk)]

        changed = []
        for k in sorted(lk & rk):
            lp = lm[k]
            rp = rm[k]
            if lp['checksum'] != rp['checksum'] or lp['version'] != rp['version']:
                changed.append(rp)

        return {'added': added, 'removed': removed, 'changed': changed}

    # ── Publishing ─────────────────────────────────────────────────

    def _do_publish(self, snapshot, distribution, component, arch, fail_at):
        """Core publish logic with optional failure injection."""
        prefix = f"{distribution}/{component}/{arch}"

        snap = self._snap_load(snapshot)
        index_packages = self._filter_by_arch(snap['packages'], arch)
        index_digest = self._compute_index_digest(index_packages)

        # Capture previous state for rollback
        pub_path = self._publish_path(distribution, component, arch)
        previous_snapshot = None
        previous_index_digest = None
        is_new = not pub_path.exists()

        if not is_new:
            pub_data = json.loads(pub_path.read_text(encoding='utf-8'))
            previous_snapshot = pub_data.get('snapshot')
            prev_idx = self._read_publish_index(distribution, component, arch)
            previous_index_digest = self._compute_index_digest(prev_idx)

        # Stage 1: journal
        journal = {
            'prefix': prefix,
            'previous_snapshot': previous_snapshot,
            'target_snapshot': snapshot,
            'previous_index_digest': previous_index_digest,
            'index_digest': index_digest,
            'stage': 'after_journal',
            'is_new': is_new,
        }
        self._write_journal(journal)

        if fail_at == 'after_journal':
            raise ArchiveError(f"Simulated failure after journal: {prefix}")

        # Stage 2: materialize index
        self._write_publish_index(distribution, component, arch, index_packages)
        journal['stage'] = 'after_index'
        self._write_journal(journal)

        if fail_at == 'after_index':
            raise ArchiveError(f"Simulated failure after index: {prefix}")

        # Stage 3: update publish metadata
        pub_record = {
            'distribution': distribution,
            'component': component,
            'arch': arch,
            'snapshot': snapshot,
            'packages': index_packages,
            'index_digest': index_digest,
        }
        self._write_publish_metadata(distribution, component, arch, pub_record)
        journal['stage'] = 'after_publish_record'
        self._write_journal(journal)

        if fail_at == 'after_publish_record':
            raise ArchiveError(f"Simulated failure after publish record: {prefix}")

        # Success — clear journal
        self._clear_journal()

    def _write_publish_index(self, distribution, component, arch, packages):
        path = self._publish_index_path(distribution, component, arch)
        path.write_text(json.dumps(packages, indent=2), encoding='utf-8')

    def _write_publish_metadata(self, distribution, component, arch, data):
        path = self._publish_path(distribution, component, arch)
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def publish(self, snapshot, distribution, component, arch):
        """Materialize a published prefix from a snapshot."""
        self._check_not_pending()

        pub_path = self._publish_path(distribution, component, arch)
        if pub_path.exists():
            raise ArchiveError(
                f"Published prefix already exists: "
                f"{distribution}/{component}/{arch}. Use publish_switch().")

        self._do_publish(snapshot, distribution, component, arch, fail_at=None)

    def publish_switch(self, snapshot, distribution, component, arch,
                       *, fail_at=None):
        """Switch an existing published prefix to a new snapshot."""
        self._check_not_pending()

        pub_path = self._publish_path(distribution, component, arch)
        if not pub_path.exists():
            raise ArchiveError(
                f"Published prefix not found: "
                f"{distribution}/{component}/{arch}. Use publish() first.")

        valid_fail = {None, 'after_journal', 'after_index', 'after_publish_record'}
        if fail_at not in valid_fail:
            raise ArchiveError(f"Invalid fail_at value: {fail_at!r}")

        self._do_publish(snapshot, distribution, component, arch, fail_at=fail_at)

    def publish_show(self, distribution, component, arch):
        """Return the semantic publish record."""
        pub = self._read_publish_metadata(distribution, component, arch)
        return {
            'distribution': pub['distribution'],
            'component': pub['component'],
            'arch': pub['arch'],
            'snapshot': pub['snapshot'],
            'packages': pub.get('packages', []),
            'index_digest': pub.get('index_digest', ''),
        }

    def published_index(self, distribution, component, arch):
        """Return the package records in the materialized published index."""
        return self._read_publish_index(distribution, component, arch)

    # ── Cleanup ────────────────────────────────────────────────────

    def cleanup_dry_run(self):
        """Return checksums that would be removed, kept, or blocked."""
        all_cs = self._pool_all_checksums()
        committed = self._committed_checksums()
        pending = self._pending_checksums()
        reachable = committed | pending

        remove = sorted(all_cs - reachable)
        keep = sorted(all_cs & reachable)

        # Blocked: packages that are only reachable from the pending transaction
        # (not from committed state)
        blocked = []
        only_pending = pending - committed
        for cs in sorted(only_pending):
            blocked.append({
                'checksum': cs,
                'reason': 'reachable only from pending transaction',
            })

        return {'remove': remove, 'keep': keep, 'blocked': blocked}

    def cleanup_apply(self):
        """Remove unreachable pool artifacts and return the cleanup report."""
        self._check_not_pending()

        report = self.cleanup_dry_run()
        for cs in report['remove']:
            self._pool_delete(cs)
        report['applied'] = True
        return report

    # ── Recovery ───────────────────────────────────────────────────

    def recover(self):
        """Recover from a pending transaction. Idempotent."""
        if not self._has_pending():
            return {'status': 'no_pending', 'prefix': ''}

        journal = self._read_journal()
        prefix = journal['prefix']
        parts = prefix.split('/')
        distribution, component, arch = parts[0], parts[1], parts[2]
        stage = journal.get('stage', 'after_journal')

        if stage == 'after_publish_record':
            # Everything is committed; just clear journal
            self._clear_journal()
            return {'status': 'completed', 'prefix': prefix}

        if stage == 'after_index':
            # Index is materialized; complete by writing publish metadata
            target = journal['target_snapshot']
            snap = self._snap_load(target)
            index_packages = self._read_publish_index(
                distribution, component, arch)
            digest = journal.get('index_digest',
                                 self._compute_index_digest(index_packages))

            pub_record = {
                'distribution': distribution,
                'component': component,
                'arch': arch,
                'snapshot': target,
                'packages': index_packages,
                'index_digest': digest,
            }
            self._write_publish_metadata(distribution, component, arch, pub_record)
            self._clear_journal()
            return {'status': 'completed', 'prefix': prefix}

        # stage == 'after_journal': roll back
        is_new = journal.get('is_new', False)
        previous_snapshot = journal.get('previous_snapshot')

        if previous_snapshot:
            # Restore previous published state
            prev_snap = self._snap_load(previous_snapshot)
            prev_index = self._filter_by_arch(prev_snap['packages'], arch)
            prev_digest = journal.get('previous_index_digest',
                                      self._compute_index_digest(prev_index))

            self._write_publish_index(distribution, component, arch, prev_index)
            pub_record = {
                'distribution': distribution,
                'component': component,
                'arch': arch,
                'snapshot': previous_snapshot,
                'packages': prev_index,
                'index_digest': prev_digest,
            }
            self._write_publish_metadata(distribution, component, arch, pub_record)
        elif is_new:
            # New publish that never completed — remove partial state
            pub_path = self.root / 'publishes' / distribution / component / f"{arch}.json"
            if pub_path.exists():
                pub_path.unlink()
            idx_path = self.root / 'publish_index' / distribution / component / f"{arch}.json"
            if idx_path.exists():
                idx_path.unlink()

        self._clear_journal()
        return {'status': 'rolled_back', 'prefix': prefix}

    # ── Graph ──────────────────────────────────────────────────────

    def graph(self):
        """Return semantic edge set across all projections."""
        edges = []

        # Repo → package
        repos_dir = self.root / 'repos'
        if repos_dir.exists():
            for f in repos_dir.iterdir():
                if f.suffix != '.json':
                    continue
                repo_name = f.stem
                data = json.loads(f.read_text(encoding='utf-8'))
                for ident_str in data:
                    edges.append({
                        'from_type': 'repo',
                        'from': repo_name,
                        'to_type': 'package',
                        'to': ident_str,
                        'relation': 'contains',
                    })

        # Snapshot → source, parents, packages
        snaps_dir = self.root / 'snapshots'
        if snaps_dir.exists():
            for f in snaps_dir.iterdir():
                if f.suffix != '.json':
                    continue
                snap_name = f.stem
                snap = json.loads(f.read_text(encoding='utf-8'))

                # sources
                for src in snap.get('sources', []):
                    src_type = 'snapshot' if self._snapshot_path(src).exists() else 'repo'
                    edges.append({
                        'from_type': 'snapshot',
                        'from': snap_name,
                        'to_type': src_type,
                        'to': src,
                        'relation': 'sources',
                    })

                # parents
                for parent in snap.get('parents', []):
                    edges.append({
                        'from_type': 'snapshot',
                        'from': snap_name,
                        'to_type': 'snapshot',
                        'to': parent,
                        'relation': 'parents',
                    })

                # packages
                for p in snap.get('packages', []):
                    ident = _pkg_identity_str(p['name'], p['version'], p['arch'])
                    edges.append({
                        'from_type': 'snapshot',
                        'from': snap_name,
                        'to_type': 'package',
                        'to': ident,
                        'relation': 'contains',
                    })

        # Publish → snapshot
        pubs_dir = self.root / 'publishes'
        if pubs_dir.exists():
            for dist_d in pubs_dir.iterdir():
                if not dist_d.is_dir():
                    continue
                for comp_d in dist_d.iterdir():
                    if not comp_d.is_dir():
                        continue
                    for f in comp_d.iterdir():
                        if f.suffix != '.json':
                            continue
                        pub = json.loads(f.read_text(encoding='utf-8'))
                        prefix = (
                            f"{pub['distribution']}/{pub['component']}"
                            f"/{pub['arch']}"
                        )
                        edges.append({
                            'from_type': 'publish',
                            'from': prefix,
                            'to_type': 'snapshot',
                            'to': pub['snapshot'],
                            'relation': 'sources',
                        })

        return edges
