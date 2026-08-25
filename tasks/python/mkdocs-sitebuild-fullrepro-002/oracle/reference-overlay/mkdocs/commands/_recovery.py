"""Reference implementation of the recoverable publication contract."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable
from collections.abc import Mapping

from mkdocs.exceptions import BuildError


OWNER_NAMES = ("config", "discovery", "lineage", "publication", "search", "outbox")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    data = value if isinstance(value, bytes) else _canonical(value)
    return hashlib.sha256(data).hexdigest()


def _record(owner: str, body: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": 1, "owner": owner, "body": body, "checksum": _digest(body)}


def _load(state_dir: Path, owner: str) -> dict[str, Any] | None:
    path = state_dir / f"{owner}.json"
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BuildError(f"invalid recovery owner {owner}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("owner") != owner:
        raise BuildError(f"invalid recovery owner {owner}")
    body = value.get("body")
    if not isinstance(body, dict) or value.get("checksum") != _digest(body):
        raise BuildError(f"invalid recovery checksum {owner}")
    return body


def _save(state_dir: Path, owner: str, body: dict[str, Any]) -> None:
    path = state_dir / f"{owner}.json"
    temporary = state_dir / f".{owner}.json.next"
    temporary.write_text(
        json.dumps(_record(owner, body), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def _source_snapshot(docs_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(docs_dir.rglob("*")):
        if path.is_file() and not path.is_symlink():
            result[path.relative_to(docs_dir).as_posix()] = _digest(path.read_bytes())
    return result


def _output_snapshot(site_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not site_dir.exists():
        return result
    for path in sorted(site_dir.rglob("*")):
        if path.is_file() and not path.is_symlink():
            result[path.relative_to(site_dir).as_posix()] = _digest(path.read_bytes())
    return result


def _config_view(config: Any) -> dict[str, Any]:
    theme = getattr(config, "theme", None)
    theme_name = getattr(theme, "name", None)
    if theme_name is None and theme is not None:
        try:
            theme_name = theme["name"]
        except Exception:
            theme_name = None
    return {
        "site_name": str(config.site_name),
        "site_url": config.site_url,
        "use_directory_urls": bool(config.use_directory_urls),
        "nav": config.nav,
        "theme": theme_name,
        "plugins": sorted(str(name) for name in config.plugins),
    }


def _state_path(config: Any, recovery: dict[str, Any]) -> Path:
    raw = recovery.get("state_dir", ".mkdocs-state")
    if not isinstance(raw, str) or not raw:
        raise BuildError("recovery state_dir must be a non-empty path")
    path = Path(raw)
    config_path = getattr(config, "config_file_path", None)
    owner = Path(config_path).resolve().parent if config_path else Path.cwd()
    path = path if path.is_absolute() else owner / path
    path = path.resolve()
    docs = Path(config.docs_dir).resolve()
    site = Path(config.site_dir).resolve()
    if path == docs or docs in path.parents or path == site or site in path.parents:
        raise BuildError("recovery state_dir overlaps a source or destination")
    return path


def _validate_recovery(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise BuildError("extra.recovery must be a mapping")
    allowed = {
        "state_dir", "action", "acknowledge", "expected_visible_generation", "renames",
        "delivery_failure",
    }
    if set(raw) - allowed:
        raise BuildError("unknown recovery setting")
    result = dict(raw)
    action = result.get("action", "publish")
    if action not in {"prepare", "publish"}:
        raise BuildError("invalid recovery action")
    result["action"] = action
    acknowledge = result.get("acknowledge", True)
    if not isinstance(acknowledge, bool):
        raise BuildError("recovery acknowledge must be boolean")
    result["acknowledge"] = acknowledge
    expected = result.get("expected_visible_generation")
    if expected is not None and (not isinstance(expected, int) or isinstance(expected, bool) or expected < 0):
        raise BuildError("expected_visible_generation must be a non-negative integer")
    renames = result.get("renames", {})
    if not isinstance(renames, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in renames.items()):
        raise BuildError("recovery renames must be a string mapping")
    if len(set(renames.values())) != len(renames):
        raise BuildError("recovery rename destinations must be unique")
    result["renames"] = {k.replace("\\", "/"): v.replace("\\", "/") for k, v in renames.items()}
    failure = result.get("delivery_failure")
    if failure is not None and not isinstance(failure, str):
        raise BuildError("delivery_failure must name an event kind")
    return result


def _changes(previous: dict[str, str], current: dict[str, str], renames: dict[str, str]) -> dict[str, list[str]]:
    renamed_old = set(renames)
    renamed_new = set(renames.values())
    if any(old not in previous or new not in current for old, new in renames.items()):
        raise BuildError("declared rename does not match discovered sources")
    if any(new in previous and new not in renamed_old for new in renamed_new):
        raise BuildError("declared rename collides with an active source")
    return {
        "added": sorted(set(current) - set(previous) - renamed_new),
        "modified": sorted(uri for uri in set(current) & set(previous) if current[uri] != previous[uri]),
        "removed": sorted(set(previous) - set(current) - renamed_old),
        "renamed": sorted(f"{old}->{new}" for old, new in renames.items()),
    }


def _lineage(previous: dict[str, Any] | None, snapshot: dict[str, str], changes: dict[str, list[str]], renames: dict[str, str]) -> dict[str, Any]:
    old_pages = dict((previous or {}).get("pages", {}))
    pages: dict[str, dict[str, Any]] = {}
    reverse_rename = {new: old for old, new in renames.items()}
    for uri, digest in sorted(snapshot.items()):
        if Path(uri).suffix.lower() not in {".md", ".markdown"}:
            continue
        source = reverse_rename.get(uri, uri)
        old = old_pages.get(source)
        if old is None and source != uri:
            # A retry of an already prepared rename sees the new URI in the
            # lineage owner while discovery still compares to acknowledged old.
            old = old_pages.get(uri)
        if old is None:
            identity = "page-" + _digest({"first_uri": uri})[:16]
            revision = 1
        else:
            identity = old["id"]
            changed = source != uri or old.get("source_digest") != digest
            revision = int(old["revision"]) + (1 if changed else 0)
        pages[uri] = {"id": identity, "revision": revision, "source_digest": digest}
    retired = sorted(set(old_pages) - set(pages) - set(renames))
    return {"generation": 0, "pages": pages, "retired": retired, "changes": changes}


def _events(generation: int, changes: dict[str, list[str]], config_changed: bool) -> list[dict[str, Any]]:
    pairs: list[tuple[str, str]] = []
    if config_changed:
        pairs.append(("config-changed", "effective-config"))
    for key, kind in (("added", "source-added"), ("modified", "source-modified"), ("removed", "source-removed"), ("renamed", "source-renamed")):
        pairs.extend((kind, uri) for uri in changes[key])
    result = []
    for kind, subject in pairs:
        event_id = "evt-" + _digest({"generation": generation, "kind": kind, "subject": subject})[:20]
        result.append({"id": event_id, "generation": generation, "kind": kind, "subject": subject, "status": "pending", "attempts": 0})
    return result


def _search_body(stage: Path, generation: int, lineage: dict[str, Any]) -> dict[str, Any]:
    artifact = stage / "search" / "search_index.json"
    receipts: list[dict[str, Any]] = []
    artifact_digest = None
    if artifact.is_file():
        artifact_digest = _digest(artifact.read_bytes())
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        for doc in payload.get("docs", []):
            location = str(doc.get("location", ""))
            base = location.split("#", 1)[0].rstrip("/")
            uri = "index.md" if base == "" else f"{base}.md"
            page = lineage["pages"].get(uri)
            if page is None:
                continue
            receipts.append({
                "source_uri": uri,
                "page_id": page["id"],
                "revision": page["revision"],
                "title": doc.get("title"),
                "location": location,
            })
    receipts.sort(key=lambda item: (item["source_uri"], item["location"], str(item["title"])))
    return {"generation": generation, "artifact_sha256": artifact_digest, "receipts": receipts, "acknowledged_generation": 0}


def transactional_build(config: Any, build_func: Callable[..., None], *, serve_url: str | None, dirty: bool) -> None:
    recovery_raw = getattr(config, "extra", {}).get("recovery") if isinstance(getattr(config, "extra", None), Mapping) else None
    if recovery_raw is None:
        build_func(config, serve_url=serve_url, dirty=dirty)
        return
    recovery = _validate_recovery(recovery_raw)
    state_dir = _state_path(config, recovery)
    state_dir.mkdir(parents=True, exist_ok=True)
    owners = {name: _load(state_dir, name) for name in OWNER_NAMES}

    config_view = _config_view(config)
    config_fingerprint = _digest(config_view)
    snapshot = _source_snapshot(Path(config.docs_dir))
    snapshot_fingerprint = _digest(snapshot)
    old_config = owners["config"] or {}
    old_discovery = owners["discovery"] or {}
    old_publication = owners["publication"] or {
        "generation": 0, "prepared_generation": 0, "visible_generation": 0,
        "acknowledged_generation": 0, "visible_files": {}, "stale_fence_count": 0,
    }
    pending_generation = int(old_discovery.get("pending_generation", 0))
    same_pending = pending_generation and old_discovery.get("pending_fingerprint") == _digest({"config": config_fingerprint, "sources": snapshot_fingerprint})
    if pending_generation and not same_pending:
        raise BuildError("a different input generation is still unacknowledged")

    acknowledged_sources = dict(old_discovery.get("acknowledged_sources", {}))
    renames = recovery["renames"]
    changes = _changes(acknowledged_sources, snapshot, renames)
    input_fingerprint = _digest({"config": config_fingerprint, "sources": snapshot_fingerprint})
    previous_input = old_config.get("input_fingerprint")
    maximum = max(int((owners[name] or {}).get("generation", 0)) for name in OWNER_NAMES)
    generation = int(old_config.get("generation", 0)) if input_fingerprint == previous_input else maximum + 1
    if same_pending:
        generation = pending_generation
    if generation <= 0:
        generation = 1

    lineage = _lineage(owners["lineage"], snapshot, changes, renames)
    lineage["generation"] = generation
    config_body = {"generation": generation, "fingerprint": config_fingerprint, "input_fingerprint": input_fingerprint, "effective": config_view}
    discovery_body = {
        "generation": generation, "observed_sources": snapshot, "changes": changes,
        "pending_generation": generation, "pending_fingerprint": input_fingerprint,
        "acknowledged_generation": int(old_discovery.get("acknowledged_generation", 0)),
        "acknowledged_sources": acknowledged_sources,
    }

    stage = state_dir / "stages" / f"g{generation:08d}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.parent.mkdir(parents=True, exist_ok=True)
    original_site = str(config.site_dir)
    config.site_dir = str(stage)
    try:
        build_func(config, serve_url=serve_url, dirty=False)
    finally:
        config.site_dir = original_site

    output_files = _output_snapshot(stage)
    publication_body = dict(old_publication)
    publication_body.update({"generation": generation, "prepared_generation": generation, "prepared_files": output_files})
    expected = recovery.get("expected_visible_generation")
    if recovery["action"] == "publish" and expected is not None and expected != int(old_publication.get("visible_generation", 0)):
        publication_body["stale_fence_count"] = int(old_publication.get("stale_fence_count", 0)) + 1
        _save(state_dir, "publication", publication_body)
        raise BuildError("stale visible generation")

    search_body = _search_body(stage, generation, lineage)
    old_outbox = owners["outbox"] or {"generation": 0, "events": []}
    event_map = {event["id"]: dict(event) for event in old_outbox.get("events", [])}
    config_changed = config_fingerprint != old_config.get("fingerprint")
    for event in _events(generation, changes, config_changed):
        event_map.setdefault(event["id"], event)
    outbox_body = {"generation": generation, "events": sorted(event_map.values(), key=lambda event: event["id"])}

    _save(state_dir, "config", config_body)
    _save(state_dir, "discovery", discovery_body)
    _save(state_dir, "lineage", lineage)
    _save(state_dir, "search", search_body)
    _save(state_dir, "outbox", outbox_body)
    _save(state_dir, "publication", publication_body)

    if recovery["action"] == "prepare":
        return

    visible = Path(original_site)
    replacement = visible.parent / f".{visible.name}.g{generation:08d}.next"
    if replacement.exists():
        shutil.rmtree(replacement)
    shutil.copytree(stage, replacement)
    if visible.exists():
        shutil.rmtree(visible)
    os.replace(replacement, visible)
    publication_body.update({"visible_generation": generation, "visible_files": output_files})
    _save(state_dir, "publication", publication_body)

    failure_kind = recovery.get("delivery_failure")
    failed = False
    for event in outbox_body["events"]:
        if event["status"] == "delivered":
            continue
        event["attempts"] = int(event["attempts"]) + 1
        if failed or event["kind"] == failure_kind:
            failed = True
            continue
        event["status"] = "delivered"
    _save(state_dir, "outbox", outbox_body)
    if failed:
        raise BuildError("recovery event delivery failed")

    if recovery["acknowledge"]:
        discovery_body.update({
            "pending_generation": 0, "pending_fingerprint": None,
            "acknowledged_generation": generation, "acknowledged_sources": snapshot,
        })
        publication_body["acknowledged_generation"] = generation
        search_body["acknowledged_generation"] = generation
        _save(state_dir, "discovery", discovery_body)
        _save(state_dir, "publication", publication_body)
        _save(state_dir, "search", search_body)
