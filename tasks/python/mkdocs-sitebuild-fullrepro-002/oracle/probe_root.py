#!/usr/bin/env python3
"""One-root semantic oracle for the MkDocs v14 formal gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
import warnings
from typing import Any, Callable
from collections.abc import Mapping

import yaml

GATE = Path(__file__).resolve().parent
RECORD_CONTRACT = json.loads((GATE / "RECORD-SHAPE-CONTRACT.json").read_text(encoding="utf-8"))
INVALID_EXCEPTIONS = (ImportError, AttributeError, TypeError, NotImplementedError, TimeoutError, OSError)


class Mismatch(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise Mismatch(message)


def mapping_item(value: Any, key: str, label: str) -> Any:
    """Read a mapping only after an explicit shape and presence check."""
    check(isinstance(value, Mapping), f"{label} is not a mapping")
    try:
        present = key in value
    except KeyError as exc:
        raise Mismatch(f"{label} rejected presence check for {key}") from exc
    check(present, f"{label} is missing required key {key}")
    try:
        return value[key]
    except KeyError as exc:
        raise Mismatch(f"{label} lost required key {key}") from exc


def sequence_item(value: Any, index: int, label: str) -> Any:
    """Index a public list only after checking its type and length."""
    check(isinstance(value, list), f"{label} is not a list")
    check(index >= 0 and len(value) > index, f"{label} has no item {index}")
    try:
        return value[index]
    except IndexError as exc:
        raise Mismatch(f"{label} lost item {index}") from exc


def sequence_replace(value: Any, index: int, replacement: Any, label: str) -> None:
    """Replace a public list item only after checking its type and length."""
    check(isinstance(value, list), f"{label} is not a list")
    check(index >= 0 and len(value) > index, f"{label} has no item {index}")
    try:
        value[index] = replacement
    except IndexError as exc:
        raise Mismatch(f"{label} lost item {index}") from exc


def list_value(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    check(isinstance(value, list), f"{label} is not a list")
    if nonempty:
        check(bool(value), f"{label} is unexpectedly empty")
    return value


def mapping_value(value: Any, label: str) -> Mapping[str, Any]:
    check(isinstance(value, Mapping), f"{label} is not a mapping")
    return value


def first_matching(value: Any, predicate: Callable[[Any], bool], label: str) -> Any:
    items = list_value(value, label, nonempty=True)
    matches = [item for item in items if predicate(item)]
    check(bool(matches), f"{label} has no matching item")
    return sequence_item(matches, 0, f"{label} matches")


def semantic_public_callable(name: str, value: Any) -> Any:
    """Translate attributable product KeyError into a scoreable mismatch."""
    if not callable(value) or isinstance(value, type) and name in {"Abort", "BuildError", "ConfigurationError", "MkDocsException", "PluginError", "Link", "Section"}:
        return value

    def invoke(*args: Any, **kwargs: Any) -> Any:
        try:
            return value(*args, **kwargs)
        except KeyError as exc:
            raise Mismatch(f"public MkDocs call {name} raised KeyError: {exc}") from exc

    return invoke


def keyerror_from_candidate(exc: KeyError, candidate_root: Path) -> bool:
    """Return whether a raw KeyError traceback entered the candidate tree."""
    root = candidate_root.resolve()
    traceback_cursor = exc.__traceback__
    while traceback_cursor is not None:
        try:
            source = Path(traceback_cursor.tb_frame.f_code.co_filename).resolve()
        except OSError:
            source = None
        if source is not None and (source == root or source.is_relative_to(root)):
            return True
        traceback_cursor = traceback_cursor.tb_next
    return False


def _resolve_schema(schema: Mapping[str, Any]) -> Mapping[str, Any]:
    definitions = mapping_value(mapping_item(RECORD_CONTRACT, "definitions", "record contract"), "record definitions")
    visited: set[str] = set()
    current = schema
    while "ref" in current:
        reference = mapping_item(current, "ref", "record schema reference")
        check(isinstance(reference, str) and reference not in visited, "invalid record schema reference")
        visited.add(reference)
        current = mapping_value(mapping_item(definitions, reference, "record definitions"), f"record definition {reference}")
    return current


def _matches_json_type(value: Any, type_name: str) -> bool:
    if type_name == "null":
        return value is None
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "positive_integer":
        return isinstance(value, int) and not isinstance(value, bool) and value > 0
    if type_name == "nonnegative_integer":
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    return False


def _validate_shape(value: Any, raw_schema: Any, label: str) -> None:
    schema = _resolve_schema(mapping_value(raw_schema, f"{label} schema"))
    declared = mapping_item(schema, "type", f"{label} schema")
    types = list_value(declared, f"{label} types", nonempty=True) if isinstance(declared, list) else [declared]
    check(all(isinstance(item, str) for item in types), f"{label} has invalid declared types")
    check(any(_matches_json_type(value, item) for item in types), f"{label} has wrong type")
    if "const" in schema:
        check(value == mapping_item(schema, "const", f"{label} schema"), f"{label} has wrong constant value")
    if "enum" in schema:
        allowed = list_value(mapping_item(schema, "enum", f"{label} schema"), f"{label} enum", nonempty=True)
        check(value in allowed, f"{label} has unsupported value")
    if schema.get("nonempty") is True:
        check(bool(value), f"{label} is unexpectedly empty")
    pattern = schema.get("pattern")
    if pattern == "sha256" or pattern == "sha256_or_null" and value is not None:
        check(isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value), f"{label} is not a SHA-256 digest")
    if isinstance(value, dict):
        required = mapping_value(schema.get("required", {}), f"{label} required schema")
        for key, child in required.items():
            _validate_shape(mapping_item(value, key, label), child, f"{label}.{key}")
        if "values" in schema:
            child = mapping_item(schema, "values", f"{label} schema")
            for key, item in value.items():
                check(isinstance(key, str), f"{label} has a non-string key")
                _validate_shape(item, child, f"{label}.{key}")
    if isinstance(value, list) and "items" in schema:
        child = mapping_item(schema, "items", f"{label} schema")
        for index, item in enumerate(value):
            _validate_shape(item, child, f"{label}[{index}]")


def validate_owner_record(owner_name: str, value: Any) -> dict[str, Any]:
    envelope = mapping_item(RECORD_CONTRACT, "envelope", "record contract")
    _validate_shape(value, envelope, owner_name)
    record = mapping_value(value, f"{owner_name} envelope")
    check(mapping_item(record, "owner", f"{owner_name} envelope") == owner_name, f"invalid {owner_name} owner")
    body = mapping_item(record, "body", f"{owner_name} envelope")
    schemas = mapping_value(mapping_item(RECORD_CONTRACT, "body_schemas", "record contract"), "record body schemas")
    _validate_shape(body, mapping_item(schemas, owner_name, "record body schemas"), owner_name)
    expected = digest_bytes(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    check(mapping_item(record, "checksum", f"{owner_name} envelope") == expected, f"invalid {owner_name} checksum")
    return dict(mapping_value(body, f"{owner_name} body"))


def record_value(value: Any, path: str, *keys: str) -> Any:
    current = value
    for key in keys:
        current = mapping_item(current, key, path)
    return current


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8", newline="\n")


def base_docs() -> dict[str, str]:
    return {
        "index.md": "---\ntitle: Harbor Home\n---\n# Home Heading\n\nWelcome cobalt. [Guide](guide.md#topic).\n",
        "guide.md": "# Field Guide\n\nGuide amber.\n\n## Topic\n\nDetails.\n",
        "notes.md": "# Notes\n\nUnlisted notes.\n",
        "assets/site.css": "body { color: rgb(17, 34, 51); }\n",
    }


def project(root: Path, name: str = "project", *, recovery: dict[str, Any] | None = None, plugins: dict[str, Any] | None = None, use_directory_urls: bool = True, strict: bool = False) -> dict[str, Path]:
    base = root / name
    docs = base / "docs"
    site = base / "site"
    state = base / "state"
    for relative, content in base_docs().items():
        write(docs / relative, content)
    recovery_value = {"state_dir": str(state), "action": "publish", "acknowledge": True}
    if recovery:
        recovery_value.update(recovery)
    config = {
        "site_name": "Harbor Manual",
        "site_url": "https://docs.invalid/manual/",
        "docs_dir": str(docs),
        "site_dir": str(site),
        "use_directory_urls": use_directory_urls,
        "nav": [{"Home": "index.md"}, {"Guide": "guide.md"}, {"External": "https://example.invalid/"}],
        "not_in_nav": "notes.md\n",
        "theme": {"name": "mkdocs"},
        "plugins": {"search": None} if plugins is None else plugins,
        "strict": strict,
        "extra": {"recovery": recovery_value},
    }
    config_path = base / "mkdocs.yml"
    write(config_path, yaml.safe_dump(config, sort_keys=False))
    return {"root": base, "docs": docs, "site": site, "state": state, "config": config_path}


def config_value(p: dict[str, Path]) -> dict[str, Any]:
    path = mapping_item(p, "config", "project paths")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return dict(mapping_value(value, "project configuration"))


def update_config(p: dict[str, Path], **recovery: Any) -> None:
    value = config_value(p)
    extra = mapping_value(mapping_item(value, "extra", "project configuration"), "project extra")
    recovery_value = mapping_value(mapping_item(extra, "recovery", "project extra"), "project recovery")
    recovery_value.update(recovery)
    write(mapping_item(p, "config", "project paths"), yaml.safe_dump(value, sort_keys=False))


def update_plugins(p: dict[str, Path], plugins: dict[str, Any]) -> None:
    value = config_value(p)
    check("plugins" in value, "project configuration is missing plugins")
    value.update({"plugins": plugins})
    write(mapping_item(p, "config", "project paths"), yaml.safe_dump(value, sort_keys=False))


def owner(p: dict[str, Path], name: str) -> dict[str, Any]:
    path = mapping_item(p, "state", "project paths") / f"{name}.json"
    check(path.is_file(), f"missing public owner record: {name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Mismatch(f"invalid public owner JSON: {name}") from exc
    return validate_owner_record(name, value)


def imports(candidate: Path) -> dict[str, Any]:
    sys.path.insert(0, str(candidate.resolve()))
    from mkdocs.commands.build import build
    from mkdocs.config import load_config
    from mkdocs.exceptions import Abort, BuildError, ConfigurationError, MkDocsException, PluginError
    from mkdocs.structure.files import File, Files, get_files
    from mkdocs.structure.nav import Link, Section, get_navigation
    from mkdocs.structure.pages import Page
    values = locals()
    public: dict[str, Any] = {}
    for name, value in values.items():
        if name not in {"candidate", "public", "values"}:
            public.update({name: semantic_public_callable(name, value)})
    return public


def build_public(api: dict[str, Any], p: dict[str, Path]) -> Any:
    load_config = mapping_item(api, "load_config", "public API")
    build = mapping_item(api, "build", "public API")
    cfg = load_config(config_file=str(mapping_item(p, "config", "project paths")))
    build(cfg)
    return cfg


def expect_build_failure(api: dict[str, Any], p: dict[str, Path]) -> str:
    try:
        build_public(api, p)
    except mapping_item(api, "MkDocsException", "public API") as exc:
        return type(exc).__name__
    raise Mismatch("build unexpectedly succeeded")


def search_docs(p: dict[str, Path]) -> list[dict[str, Any]]:
    path = mapping_item(p, "site", "project paths") / "search" / "search_index.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Mismatch("public search artifact is not valid JSON") from exc
    docs = mapping_item(payload, "docs", "public search artifact")
    check(isinstance(docs, list), "public search docs is not a list")
    return docs


def external_build(candidate: Path, p: dict[str, Path], receipt: Path, *, expect_success: bool = True) -> dict[str, Any]:
    done = subprocess.run(
        [sys.executable, "-s", "-X", "utf8", "-B", str(GATE / "scenario_driver.py"), "--candidate-root", str(candidate), "--config", str(mapping_item(p, "config", "project paths")), "--output", str(receipt)],
        cwd=GATE, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=45, check=False,
    )
    check(receipt.is_file(), "fresh-process build emitted no receipt")
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("fresh-process driver emitted invalid JSON") from exc
    check(isinstance(value, dict), "fresh-process driver receipt is not an object")
    if expect_success:
        check("ok" in value, "fresh-process driver receipt is missing ok")
        check(done.returncode == 0 and mapping_item(value, "ok", "fresh-process receipt") is True, f"fresh-process build failed: {value}")
    else:
        check("ok" in value and "error_type" in value, "fresh-process failure receipt is incomplete")
        check(done.returncode == 3 and mapping_item(value, "ok", "fresh-process receipt") is False, "fresh-process failure was not finite")
        check(mapping_item(value, "error_type", "fresh-process receipt") not in {"ImportError", "ModuleNotFoundError", "AttributeError", "TypeError", "NotImplementedError"}, f"invalid failure type: {value}")
    return value


def ordinary_project(p: dict[str, Path]) -> None:
    value = config_value(p)
    check("extra" in value, "project configuration is missing extra")
    value.update({"extra": {}})
    write(mapping_item(p, "config", "project paths"), yaml.safe_dump(value, sort_keys=False))


def A01(candidate: Path, root: Path) -> None:
    p = project(root); ordinary_project(p); api = imports(candidate)
    cfg = mapping_item(api, "load_config", "public API")(config_file=str(mapping_item(p, "config", "project paths")), site_name="Override Harbor", site_url=None)
    check(cfg.site_name == "Override Harbor" and cfg.site_url == "https://docs.invalid/manual/" and mapping_item(cfg, "docs_dir", "public Config") == cfg.docs_dir, "typed config law")


def A02(candidate: Path, root: Path) -> None:
    p = project(root, use_directory_urls=False); ordinary_project(p); api = imports(candidate)
    cfg = mapping_item(api, "load_config", "public API")(config_file=str(mapping_item(p, "config", "project paths")))
    index = mapping_item(api, "File", "public API")("index.md", cfg.docs_dir, cfg.site_dir, False)
    guide = mapping_item(api, "File", "public API")("guide.md", cfg.docs_dir, cfg.site_dir, False)
    css = mapping_item(api, "File", "public API")("assets/site.css", cfg.docs_dir, cfg.site_dir, False)
    check((index.dest_uri, index.url, guide.dest_uri, css.is_css()) == ("index.html", "index.html", "guide.html", True), "file projections")


def A03(candidate: Path, root: Path) -> None:
    p = project(root); ordinary_project(p); api = imports(candidate)
    cfg = mapping_item(api, "load_config", "public API")(config_file=str(mapping_item(p, "config", "project paths")))
    first = mapping_item(api, "File", "public API")("index.md", cfg.docs_dir, cfg.site_dir, True)
    css = mapping_item(api, "File", "public API")("assets/site.css", cfg.docs_dir, cfg.site_dir, True)
    files = mapping_item(api, "Files", "public API")([first, css])
    replacement = mapping_item(api, "File", "public API")("index.md", cfg.docs_dir, cfg.site_dir, False)
    files.remove(first); files.append(replacement); files.remove(css)
    uri_map = mapping_value(files.src_uris, "public Files.src_uris")
    check(files.get_file_from_path("index.md") is replacement and css.src_uri not in uri_map and list(uri_map) == ["index.md"], f"collection ownership: {uri_map}")


def A04(candidate: Path, root: Path) -> None:
    p = project(root); ordinary_project(p); api = imports(candidate)
    cfg = mapping_item(api, "load_config", "public API")(config_file=str(mapping_item(p, "config", "project paths")))
    file = mapping_item(api, "File", "public API")("index.md", cfg.docs_dir, cfg.site_dir, True)
    page = mapping_item(api, "Page", "public API")(None, file, cfg); page.read_source(cfg); page.render(cfg, mapping_item(api, "Files", "public API")([file]))
    check(page.title == "Harbor Home" and mapping_item(page.meta, "title", "public Page.meta") == "Harbor Home" and "<h1" in page.content and len(page.toc) == 1, "page lifecycle")


def A05(candidate: Path, root: Path) -> None:
    p = project(root); ordinary_project(p); api = imports(candidate)
    cfg = mapping_item(api, "load_config", "public API")(config_file=str(mapping_item(p, "config", "project paths"))); files = mapping_item(api, "get_files", "public API")(cfg); nav = mapping_item(api, "get_navigation", "public API")(files, cfg)
    pages = list_value(nav.pages, "public Navigation.pages", nonempty=True)
    check(len(pages) >= 2, "public Navigation.pages has fewer than two pages")
    first_page = sequence_item(pages, 0, "public Navigation.pages"); second_page = sequence_item(pages, 1, "public Navigation.pages")
    nav_items = list_value(nav.items, "public Navigation.items", nonempty=True)
    link_type = mapping_item(api, "Link", "public API")
    check(first_page.next_page is second_page and second_page.previous_page is first_page and files.get_file_from_path("index.md") is first_page.file and any(isinstance(item, link_type) for item in nav_items), "navigation graph")


def A06(candidate: Path, root: Path) -> None:
    api = imports(candidate)
    abort = mapping_item(api, "Abort", "public API"); base = mapping_item(api, "MkDocsException", "public API"); build_error = mapping_item(api, "BuildError", "public API"); plugin_error = mapping_item(api, "PluginError", "public API")
    check(issubclass(abort, base) and issubclass(build_error, base) and issubclass(plugin_error, build_error) and abort.exit_code == 1, "exception hierarchy")


def A07(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); body = owner(p, "config")
    check(record_value(body, "config.generation", "generation") == 1 and record_value(body, "config.effective.site_name", "effective", "site_name") == "Harbor Manual" and record_value(body, "config.effective.plugins", "effective", "plugins") == ["search"], "config owner")


def A08(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"acknowledge": False}); api = imports(candidate); build_public(api, p); body = owner(p, "discovery")
    check(record_value(body, "discovery.generation", "generation") == record_value(body, "discovery.pending_generation", "pending_generation") == 1 and record_value(body, "discovery.acknowledged_generation", "acknowledged_generation") == 0 and record_value(body, "discovery.changes.added", "changes", "added") == sorted(base_docs()), "discovery journal")


def A09(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); first_body = owner(p, "lineage"); first_pages = record_value(first_body, "lineage.pages", "pages"); first = mapping_item(first_pages, "guide.md", "lineage.pages")
    write(mapping_item(p, "docs", "project paths") / "guide.md", "# Field Guide\n\nChanged violet.\n"); build_public(api, p); second_body = owner(p, "lineage"); second_pages = record_value(second_body, "lineage.pages", "pages"); second = mapping_item(second_pages, "guide.md", "lineage.pages")
    check(record_value(second, "lineage.pages.*.id", "id") == record_value(first, "lineage.pages.*.id", "id") and record_value(second, "lineage.pages.*.revision", "revision") == record_value(first, "lineage.pages.*.revision", "revision") + 1, "lineage revision")


def A10(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"action": "prepare", "acknowledge": False}); api = imports(candidate); build_public(api, p); first = owner(p, "publication")
    build_public(api, p); second = owner(p, "publication")
    check(not mapping_item(p, "site", "project paths").exists() and record_value(first, "publication.prepared_generation", "prepared_generation") == record_value(second, "publication.prepared_generation", "prepared_generation") == 1 and record_value(first, "publication.visible_generation", "visible_generation") == record_value(second, "publication.visible_generation", "visible_generation") == 0, "prepare visibility")


def A11(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); body = owner(p, "search")
    receipts = list_value(record_value(body, "search.receipts", "receipts"), "search.receipts", nonempty=True)
    home = first_matching(receipts, lambda item: record_value(item, "search.receipts[].source_uri", "source_uri") == "index.md", "search.receipts")
    check(record_value(body, "search.artifact_sha256", "artifact_sha256") == digest_file(mapping_item(p, "site", "project paths") / "search" / "search_index.json") and record_value(home, "search.receipts[].title", "title") == "Home" and record_value(home, "search.receipts[].location", "location") == "" and bool(record_value(home, "search.receipts[].page_id", "page_id")), f"search receipt: {body}")


def A12(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); first = owner(p, "outbox"); build_public(api, p); second = owner(p, "outbox")
    events = list_value(record_value(second, "outbox.events", "events"), "outbox.events", nonempty=True)
    ids = [record_value(event, "outbox.events[].id", "id") for event in events]
    generation = record_value(second, "outbox.generation", "generation")
    check(bool(ids) and len(ids) == len(set(ids)) and all(record_value(event, "outbox.events[].status", "status") == "delivered" and record_value(event, "outbox.events[].attempts", "attempts") == 1 and record_value(event, "outbox.events[].generation", "generation") == generation for event in events) and first == second, "outbox uniqueness")


def I01(candidate: Path, root: Path) -> None:
    p = project(root); ordinary_project(p); api = imports(candidate); cfg = build_public(api, p)
    site = mapping_item(p, "site", "project paths")
    check((site / "index.html").is_file() and (site / "guide" / "index.html").is_file() and cfg.site_dir == str(site), "basic site")


def I02(candidate: Path, root: Path) -> None:
    p = project(root, use_directory_urls=False); ordinary_project(p); api = imports(candidate); build_public(api, p); site = mapping_item(p, "site", "project paths"); html = (site / "index.html").read_text(encoding="utf-8")
    check((site / "guide.html").is_file() and 'href="guide.html#topic"' in html, "URL handoff")


def I03(candidate: Path, root: Path) -> None:
    p = project(root); ordinary_project(p); api = imports(candidate); build_public(api, p); docs = list_value(search_docs(p), "ordinary.search.docs", nonempty=True)
    topic = first_matching(docs, lambda item: mapping_item(item, "title", "ordinary search document") == "Topic", "ordinary.search.docs")
    home = first_matching(docs, lambda item: mapping_item(item, "location", "ordinary search document") == "", "ordinary.search.docs")
    check(mapping_item(home, "title", "ordinary search home document") == "Home" and mapping_item(topic, "location", "ordinary search topic document") == "guide/#topic" and 'id="topic"' in (mapping_item(p, "site", "project paths") / "guide" / "index.html").read_text(encoding="utf-8"), "search/nav/page seam")


def I04(candidate: Path, root: Path) -> None:
    p = project(root, strict=True); ordinary_project(p); write(mapping_item(p, "docs", "project paths") / "index.md", "# Broken\n\n[Missing](absent.md)\n"); api = imports(candidate)
    check(expect_build_failure(api, p) == "Abort", "strict failure boundary")


def I05(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); write(mapping_item(p, "docs", "project paths") / "guide.md", "# Changed Guide\n"); build_public(api, p)
    c, d = owner(p, "config"), owner(p, "discovery")
    check(record_value(c, "config.generation", "generation") == record_value(d, "discovery.generation", "generation") == record_value(d, "discovery.acknowledged_generation", "acknowledged_generation") == 2 and record_value(d, "discovery.changes.modified", "changes", "modified") == ["guide.md"], "shared generation")


def I06(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); first_body = owner(p, "lineage"); first = mapping_item(record_value(first_body, "lineage.pages", "pages"), "guide.md", "lineage.pages"); write(mapping_item(p, "docs", "project paths") / "guide.md", "# Revised Guide\n\nCopper.\n"); build_public(api, p)
    d, l, pub = owner(p, "discovery"), owner(p, "lineage"), owner(p, "publication"); current = mapping_item(record_value(l, "lineage.pages", "pages"), "guide.md", "lineage.pages")
    check(record_value(d, "discovery.changes.modified", "changes", "modified") == ["guide.md"] and record_value(current, "lineage.pages.*.id", "id") == record_value(first, "lineage.pages.*.id", "id") and record_value(current, "lineage.pages.*.revision", "revision") == 2 and record_value(pub, "publication.visible_generation", "visible_generation") == 2, "edit composition")


def I07(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); lineage = owner(p, "lineage"); guide = mapping_item(record_value(lineage, "lineage.pages", "pages"), "guide.md", "lineage.pages"); identity = record_value(guide, "lineage.pages.*.id", "id"); docs = mapping_item(p, "docs", "project paths"); shutil.move(docs / "guide.md", docs / "manual.md")
    value = config_value(p); nav = list_value(mapping_item(value, "nav", "project configuration"), "project navigation", nonempty=True); sequence_replace(nav, 1, {"Guide": "manual.md"}, "project navigation"); extra = mapping_value(mapping_item(value, "extra", "project configuration"), "project extra"); recovery = mapping_value(mapping_item(extra, "recovery", "project extra"), "project recovery"); check("renames" not in recovery or isinstance(mapping_item(recovery, "renames", "project recovery"), dict), "project renames has wrong type"); recovery.update({"renames": {"guide.md": "manual.md"}}); write(mapping_item(p, "config", "project paths"), yaml.safe_dump(value, sort_keys=False)); build_public(api, p)
    current_lineage = owner(p, "lineage"); manual = mapping_item(record_value(current_lineage, "lineage.pages", "pages"), "manual.md", "lineage.pages"); search_receipts = list_value(record_value(owner(p, "search"), "search.receipts", "receipts"), "search.receipts", nonempty=True)
    check(record_value(manual, "lineage.pages.*.id", "id") == identity and record_value(owner(p, "discovery"), "discovery.changes.renamed", "changes", "renamed") == ["guide.md->manual.md"] and any(record_value(item, "search.receipts[].source_uri", "source_uri") == "manual.md" for item in search_receipts), "rename composition")


def I08(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"action": "prepare", "acknowledge": False}); api = imports(candidate); build_public(api, p); update_config(p, action="publish", acknowledge=True); build_public(api, p); pub = owner(p, "publication")
    check(record_value(pub, "publication.prepared_generation", "prepared_generation") == record_value(pub, "publication.visible_generation", "visible_generation") == record_value(pub, "publication.acknowledged_generation", "acknowledged_generation") == 1 and (mapping_item(p, "site", "project paths") / "index.html").is_file(), "prepare publish handoff")


def I09(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"acknowledge": False}); api = imports(candidate); build_public(api, p); update_config(p, acknowledge=True); build_public(api, p)
    d, pub, s, o = (owner(p, name) for name in ("discovery", "publication", "search", "outbox"))
    events = list_value(record_value(o, "outbox.events", "events"), "outbox.events", nonempty=True)
    check(record_value(d, "discovery.pending_generation", "pending_generation") == 0 and record_value(d, "discovery.acknowledged_generation", "acknowledged_generation") == record_value(pub, "publication.acknowledged_generation", "acknowledged_generation") == record_value(s, "search.acknowledged_generation", "acknowledged_generation") == 1 and all(record_value(event, "outbox.events[].status", "status") == "delivered" for event in events), "ack order")


def I10(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); site = mapping_item(p, "site", "project paths"); before = digest_file(site / "index.html"); write(mapping_item(p, "docs", "project paths") / "index.md", "# New Home\n"); update_config(p, expected_visible_generation=0); check(expect_build_failure(api, p) == "BuildError", "fence error"); pub = owner(p, "publication")
    check(record_value(pub, "publication.visible_generation", "visible_generation") == 1 and record_value(pub, "publication.stale_fence_count", "stale_fence_count") == 1 and digest_file(site / "index.html") == before, "stale fence")


def I11(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); write(mapping_item(p, "docs", "project paths") / "guide.md", "# Delivery Change\n"); update_config(p, delivery_failure="source-modified"); check(expect_build_failure(api, p) == "BuildError", "delivery failure"); failed = owner(p, "outbox"); update_config(p, delivery_failure=None); build_public(api, p); done = owner(p, "outbox")
    done_events = list_value(record_value(done, "outbox.events", "events"), "outbox.events", nonempty=True); failed_events = list_value(record_value(failed, "outbox.events", "events"), "outbox.events", nonempty=True)
    target = first_matching(done_events, lambda event: record_value(event, "outbox.events[].kind", "kind") == "source-modified", "outbox.events")
    check(record_value(owner(p, "publication"), "publication.visible_generation", "visible_generation") == 2 and any(record_value(event, "outbox.events[].status", "status") == "pending" for event in failed_events) and record_value(target, "outbox.events[].status", "status") == "delivered" and record_value(target, "outbox.events[].attempts", "attempts") == 2 and len({record_value(event, "outbox.events[].id", "id") for event in done_events}) == len(done_events), "delivery retry")


def I12(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); site = mapping_item(p, "site", "project paths"); state = mapping_item(p, "state", "project paths"); before = digest_file(site / "index.html"); config_path = state / "config.json"; check(config_path.is_file(), "missing config owner before corruption"); config_before = config_path.read_bytes(); write(state / "discovery.json", "{}\n"); check(expect_build_failure(api, p) == "BuildError", "corruption failure")
    check(digest_file(site / "index.html") == before and (state / "config.json").read_bytes() == config_before, "corruption containment")


def I13(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); l, pub, s = (owner(p, name) for name in ("lineage", "publication", "search")); receipts = list_value(record_value(s, "search.receipts", "receipts"), "search.receipts", nonempty=True); receipt = first_matching(receipts, lambda item: record_value(item, "search.receipts[].source_uri", "source_uri") == "guide.md", "search.receipts"); page = mapping_item(record_value(l, "lineage.pages", "pages"), "guide.md", "lineage.pages")
    check(record_value(s, "search.acknowledged_generation", "acknowledged_generation") == record_value(pub, "publication.acknowledged_generation", "acknowledged_generation") == record_value(l, "lineage.generation", "generation") and record_value(receipt, "search.receipts[].page_id", "page_id") == record_value(page, "lineage.pages.*.id", "id") and record_value(receipt, "search.receipts[].revision", "revision") == record_value(page, "lineage.pages.*.revision", "revision"), "search lineage seam")


def I14(candidate: Path, root: Path) -> None:
    p = project(root); api = imports(candidate); build_public(api, p); update_plugins(p, {}); build_public(api, p); c, o = owner(p, "config"), owner(p, "outbox")
    events = list_value(record_value(o, "outbox.events", "events"), "outbox.events", nonempty=True); config_events = [event for event in events if record_value(event, "outbox.events[].kind", "kind") == "config-changed" and record_value(event, "outbox.events[].generation", "generation") == 2]
    check(len(config_events) == 1 and record_value(c, "config.generation", "generation") == 2 and record_value(c, "config.effective.plugins", "effective", "plugins") == [] and record_value(sequence_item(config_events, 0, "generation-two config events"), "outbox.events[].status", "status") == "delivered", "plugin config event")


def S01(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); first_body = owner(p, "lineage"); first = mapping_item(record_value(first_body, "lineage.pages", "pages"), "guide.md", "lineage.pages"); write(mapping_item(p, "docs", "project paths") / "guide.md", "# Reopened Guide\n"); external_build(candidate, p, root / "r2.json"); second_body = owner(p, "lineage"); second = mapping_item(record_value(second_body, "lineage.pages", "pages"), "guide.md", "lineage.pages")
    check(record_value(owner(p, "publication"), "publication.visible_generation", "visible_generation") == 2 and record_value(first, "lineage.pages.*.id", "id") == record_value(second, "lineage.pages.*.id", "id") and record_value(second, "lineage.pages.*.revision", "revision") == 2, "fresh reopen edit")


def S02(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"action": "prepare", "acknowledge": False}); external_build(candidate, p, root / "r1.json"); check(not mapping_item(p, "site", "project paths").exists(), "prepare leaked"); update_config(p, action="publish", acknowledge=True); external_build(candidate, p, root / "r2.json"); pub = owner(p, "publication")
    check(record_value(pub, "publication.prepared_generation", "prepared_generation") == record_value(pub, "publication.visible_generation", "visible_generation") == record_value(owner(p, "search"), "search.acknowledged_generation", "acknowledged_generation") == 1, "fresh publish")


def S03(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); write(mapping_item(p, "docs", "project paths") / "guide.md", "# Retry Guide\n"); update_config(p, delivery_failure="source-modified"); external_build(candidate, p, root / "r2.json", expect_success=False); update_config(p, delivery_failure=None); external_build(candidate, p, root / "r3.json"); events = list_value(record_value(owner(p, "outbox"), "outbox.events", "events"), "outbox.events", nonempty=True); target = first_matching(events, lambda event: record_value(event, "outbox.events[].kind", "kind") == "source-modified", "outbox.events")
    check(record_value(target, "outbox.events[].attempts", "attempts") == 2 and record_value(target, "outbox.events[].status", "status") == "delivered" and record_value(owner(p, "discovery"), "discovery.acknowledged_generation", "acknowledged_generation") == 2, "fresh retry")


def S04(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); docs = mapping_item(p, "docs", "project paths"); site = mapping_item(p, "site", "project paths"); write(docs / "guide.md", "# Writer A\n"); update_config(p, expected_visible_generation=1); external_build(candidate, p, root / "r2.json"); before = digest_file(site / "guide" / "index.html"); write(docs / "guide.md", "# Writer B\n"); update_config(p, expected_visible_generation=1); external_build(candidate, p, root / "r3.json", expect_success=False)
    publication = owner(p, "publication")
    check(record_value(publication, "publication.visible_generation", "visible_generation") == 2 and record_value(publication, "publication.stale_fence_count", "stale_fence_count") == 1 and digest_file(site / "guide" / "index.html") == before, "competing fence")


def S05(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); lineage = owner(p, "lineage"); guide = mapping_item(record_value(lineage, "lineage.pages", "pages"), "guide.md", "lineage.pages"); identity = record_value(guide, "lineage.pages.*.id", "id"); docs = mapping_item(p, "docs", "project paths"); shutil.move(docs / "guide.md", docs / "manual.md"); value = config_value(p); nav = list_value(mapping_item(value, "nav", "project configuration"), "project navigation", nonempty=True); sequence_replace(nav, 1, {"Guide": "manual.md"}, "project navigation"); extra = mapping_value(mapping_item(value, "extra", "project configuration"), "project extra"); recovery = mapping_value(mapping_item(extra, "recovery", "project extra"), "project recovery"); recovery.update({"renames": {"guide.md": "manual.md"}}); write(mapping_item(p, "config", "project paths"), yaml.safe_dump(value, sort_keys=False)); external_build(candidate, p, root / "r2.json"); receipts = list_value(record_value(owner(p, "search"), "search.receipts", "receipts"), "search.receipts", nonempty=True); receipt = first_matching(receipts, lambda item: record_value(item, "search.receipts[].source_uri", "source_uri") == "manual.md", "search.receipts"); current_lineage = owner(p, "lineage"); manual = mapping_item(record_value(current_lineage, "lineage.pages", "pages"), "manual.md", "lineage.pages")
    check(record_value(receipt, "search.receipts[].page_id", "page_id") == identity == record_value(manual, "lineage.pages.*.id", "id") and (mapping_item(p, "site", "project paths") / "manual" / "index.html").is_file(), "rename system")


def S06(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"acknowledge": False}); external_build(candidate, p, root / "r1.json"); guide_path = mapping_item(p, "docs", "project paths") / "guide.md"; write(guide_path, "# Competing\n"); external_build(candidate, p, root / "r2.json", expect_success=False); write(guide_path, mapping_item(base_docs(), "guide.md", "base documents")); update_config(p, acknowledge=True); external_build(candidate, p, root / "r3.json")
    check(record_value(owner(p, "discovery"), "discovery.acknowledged_generation", "acknowledged_generation") == 1 and record_value(owner(p, "publication"), "publication.visible_generation", "visible_generation") == 1, "pending conflict recovery")


def S07(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); discovery_path = mapping_item(p, "state", "project paths") / "discovery.json"; check(discovery_path.is_file(), "missing discovery owner before corruption"); saved = discovery_path.read_bytes(); site = mapping_item(p, "site", "project paths"); before = digest_file(site / "index.html"); write(discovery_path, "{broken\n"); external_build(candidate, p, root / "r2.json", expect_success=False); check(digest_file(site / "index.html") == before, "corrupt reopen changed visibility"); write(discovery_path, saved); external_build(candidate, p, root / "r3.json")
    check(record_value(owner(p, "lineage"), "lineage.generation", "generation") == 1 and record_value(owner(p, "discovery"), "discovery.acknowledged_generation", "acknowledged_generation") == 1, "owner restore")


def S08(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); update_plugins(p, {}); update_config(p, delivery_failure="config-changed"); external_build(candidate, p, root / "r2.json", expect_success=False); update_config(p, delivery_failure=None); external_build(candidate, p, root / "r3.json"); events = list_value(record_value(owner(p, "outbox"), "outbox.events", "events"), "outbox.events", nonempty=True); target = [event for event in events if record_value(event, "outbox.events[].kind", "kind") == "config-changed" and record_value(event, "outbox.events[].generation", "generation") == 2]
    search = owner(p, "search")
    check(len(target) == 1 and record_value(sequence_item(target, 0, "generation-two config events"), "outbox.events[].attempts", "attempts") == 2 and record_value(search, "search.receipts", "receipts") == [] and record_value(search, "search.acknowledged_generation", "acknowledged_generation") == 2, "plugin recovery")


def S09(candidate: Path, root: Path) -> None:
    p = project(root); external_build(candidate, p, root / "r1.json"); site = mapping_item(p, "site", "project paths"); write(site / "stale-owned.txt", "old"); (mapping_item(p, "docs", "project paths") / "notes.md").unlink(); external_build(candidate, p, root / "r2.json"); pub = owner(p, "publication"); search = owner(p, "search")
    receipts = list_value(record_value(search, "search.receipts", "receipts"), "search.receipts")
    check(not (site / "stale-owned.txt").exists() and "stale-owned.txt" not in record_value(pub, "publication.visible_files", "visible_files") and "notes.md" in record_value(owner(p, "discovery"), "discovery.changes.removed", "changes", "removed") and all(record_value(receipt, "search.receipts[].source_uri", "source_uri") != "notes.md" for receipt in receipts), "clean stale recovery")


def S10(candidate: Path, root: Path) -> None:
    p = project(root, recovery={"action": "prepare", "acknowledge": False}); external_build(candidate, p, root / "r1.json"); update_config(p, action="publish", acknowledge=True); external_build(candidate, p, root / "r2.json"); lineage = owner(p, "lineage"); guide = mapping_item(record_value(lineage, "lineage.pages", "pages"), "guide.md", "lineage.pages"); identity = record_value(guide, "lineage.pages.*.id", "id"); docs = mapping_item(p, "docs", "project paths"); shutil.move(docs / "guide.md", docs / "manual.md"); value = config_value(p); nav = list_value(mapping_item(value, "nav", "project configuration"), "project navigation", nonempty=True); sequence_replace(nav, 1, {"Guide": "manual.md"}, "project navigation"); check("plugins" in value, "project configuration is missing plugins"); value.update({"plugins": {}}); extra = mapping_value(mapping_item(value, "extra", "project configuration"), "project extra"); recovery = mapping_value(mapping_item(extra, "recovery", "project extra"), "project recovery"); recovery.update({"renames": {"guide.md": "manual.md"}, "delivery_failure": "source-renamed"}); write(mapping_item(p, "config", "project paths"), yaml.safe_dump(value, sort_keys=False)); external_build(candidate, p, root / "r3.json", expect_success=False); update_config(p, delivery_failure=None); external_build(candidate, p, root / "r4.json"); records = {name: owner(p, name) for name in ("config", "discovery", "lineage", "publication", "search", "outbox")}
    current_lineage = mapping_item(records, "lineage", "owner records"); manual = mapping_item(record_value(current_lineage, "lineage.pages", "pages"), "manual.md", "lineage.pages"); publication = mapping_item(records, "publication", "owner records"); search = mapping_item(records, "search", "owner records"); outbox = mapping_item(records, "outbox", "owner records"); events = list_value(record_value(outbox, "outbox.events", "events"), "outbox.events", nonempty=True)
    generations = {
        record_value(mapping_item(records, "config", "owner records"), "config.generation", "generation"),
        record_value(mapping_item(records, "discovery", "owner records"), "discovery.generation", "generation"),
        record_value(current_lineage, "lineage.generation", "generation"),
        record_value(publication, "publication.generation", "generation"),
        record_value(search, "search.generation", "generation"),
        record_value(outbox, "outbox.generation", "generation"),
    }
    check(generations == {2} and record_value(manual, "lineage.pages.*.id", "id") == identity and record_value(publication, "publication.acknowledged_generation", "acknowledged_generation") == record_value(search, "search.acknowledged_generation", "acknowledged_generation") == 2 and all(record_value(event, "outbox.events[].status", "status") == "delivered" for event in events), f"full recovery workflow: {records}")


ROOTS: dict[str, Callable[[Path, Path], None]] = {name: value for name, value in list(globals().items()) if isinstance(value, type(lambda: None)) and (name.startswith("A") or name.startswith("I") or name.startswith("S")) and name[1:].isdigit()}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", required=True); parser.add_argument("--candidate-root", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    record: dict[str, Any] = {"schema_version": 1, "root": args.root}
    if args.root not in ROOTS:
        record.update({"valid": False, "phase": "collection", "classification": "collection", "error": "unknown root"}); args.output.write_text(json.dumps(record) + "\n", encoding="utf-8"); return 2
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with tempfile.TemporaryDirectory(prefix=f"mkdocs-v14-{args.root}-") as temp:
                root_callable = mapping_item(ROOTS, args.root, "oracle root registry")
                root_callable(args.candidate_root.resolve(), Path(temp))
            if caught:
                raise RuntimeError("warning emitted: " + "; ".join(str(item.message) for item in caught))
        record.update({"valid": True, "phase": "semantic-call", "passed": True, "classification": "pass"}); code = 0
    except Mismatch as exc:
        record.update({"valid": True, "phase": "semantic-call", "passed": False, "classification": "semantic-mismatch", "error": str(exc)}); code = 0
    except KeyError as exc:
        if keyerror_from_candidate(exc, args.candidate_root):
            record.update({"valid": True, "phase": "semantic-call", "passed": False, "classification": "public-product-keyerror", "error_type": "KeyError", "error": str(exc)}); code = 0
        else:
            record.update({"valid": False, "phase": "semantic-call", "classification": "invalid-harness-indexing", "error_type": "KeyError", "error": str(exc), "traceback": traceback.format_exc()}); code = 2
    except INVALID_EXCEPTIONS as exc:
        record.update({"valid": False, "phase": "semantic-call", "classification": "invalid-infrastructure", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}); code = 2
    except BaseException as exc:
        module = type(exc).__module__
        if module.startswith("mkdocs.exceptions"):
            record.update({"valid": True, "phase": "semantic-call", "passed": False, "classification": "public-call-failure", "error_type": type(exc).__name__, "error": str(exc)}); code = 0
        else:
            record.update({"valid": False, "phase": "semantic-call", "classification": "invalid-harness-or-product", "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}); code = 2
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
