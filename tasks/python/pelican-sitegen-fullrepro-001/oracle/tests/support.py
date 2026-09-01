from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Any, Callable


def native_api() -> SimpleNamespace:
    try:
        from pelican import Pelican, get_config, parse_arguments, signals
        from pelican.paginator import PaginationRule, Paginator
        from pelican.plugins import signals as plugin_signals
        from pelican.readers import Readers
        from pelican.settings import DEFAULT_CONFIG, read_settings
        from pelican.urlwrappers import Author, Category, Tag
        from pelican.utils import get_date, path_to_url, posixize_path, slugify
    except (ImportError, AttributeError) as exc:
        raise AssertionError(f"required Pelican public surface is absent: {type(exc).__name__}") from None
    return SimpleNamespace(**locals())


def workflow_api() -> SimpleNamespace:
    try:
        from pelican.publication import (
            AcknowledgementError,
            ArtifactPublisher,
            ContentStore,
            IdentityIndex,
            OwnershipError,
            PublicationError,
            PublicationLedger,
            RecoveryError,
            SignalOutbox,
            StaleGenerationError,
            ThemeRenderer,
        )
    except (ImportError, AttributeError) as exc:
        raise AssertionError(f"durable publication surface is absent: {type(exc).__name__}") from None
    return SimpleNamespace(**locals())


def temporary_root(prefix: str = "pelican-v6-"):
    return tempfile.TemporaryDirectory(prefix=prefix)


def records(version: int = 1) -> list[dict[str, Any]]:
    quartz_slug = "quartz-notes" if version == 1 else "quartz-field-guide"
    quartz_title = "Quartz Notes" if version == 1 else "Quartz Field Guide"
    return [
        {
            "source_id": "quartz",
            "title": quartz_title,
            "slug": quartz_slug,
            "body": f"quartz body {version}",
            "status": "published",
            "category": "Minerals",
            "tags": ["Field", "Minerals"],
            "date": f"2031-04-0{version + 1}",
        },
        {
            "source_id": "opal",
            "title": "Opal Dispatch",
            "slug": "opal-dispatch",
            "body": f"opal body {version}",
            "status": "published",
            "category": "Minerals",
            "tags": ["Field"],
            "date": "2031-04-01",
        },
    ]


def identity_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return list(snapshot["identities"])


def render_one(root: Path, generation: int, identity_snapshot: dict[str, Any], *, body: str = "Body") -> tuple[Any, dict[str, Any], list[dict[str, Any]]]:
    api = workflow_api()
    renderer = api.ThemeRenderer(root / "theme")
    lease = renderer.lease(generation, "linen", identity_snapshot)
    identity = identity_rows(identity_snapshot)[0]
    artifact = renderer.render(lease["token"], identity["identity"], body, context_generation=generation)
    committed = renderer.commit(lease["token"])
    return renderer, artifact, committed


def acknowledged_publication(root: Path, generation: int, artifacts: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any]]:
    api = workflow_api()
    publisher = api.ArtifactPublisher(root / "publisher")
    prepared = publisher.prepare(generation, artifacts or {f"articles/g{generation}.html": f"generation {generation}"})
    visible = publisher.promote(prepared["token"])
    acknowledged = publisher.acknowledge(visible["generation"], visible["digest"])
    return publisher, acknowledged


def expect_error(error_type: type[BaseException], operation: Callable[[], Any]) -> BaseException:
    try:
        operation()
    except error_type as exc:
        return exc
    raise AssertionError(f"expected {error_type.__name__}")


def entries_for(records_value: list[dict[str, Any]], identities: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    slugs: dict[str, str] = {}
    if identities is not None:
        slugs = {row["source_id"]: row["slug"] for row in identities["identities"]}
    return [
        {
            "source_id": row["source_id"],
            "title": row["title"],
            "url": f"articles/{slugs.get(row['source_id'], row['slug'])}.html",
            "status": row.get("status", "published"),
            "date": row.get("date", ""),
        }
        for row in records_value
    ]
