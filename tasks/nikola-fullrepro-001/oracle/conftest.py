"""Shared fixtures, helpers, and constants for nikola-fullrepro-001 oracle."""

from __future__ import annotations

import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from nikola import Nikola
from nikola.__main__ import main


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic tests this integration test depends on",
    )


# ---------------------------------------------------------------------------
# Anti-memorization constants (values differ from upstream test suite)
# ---------------------------------------------------------------------------
SITE_URL = "https://orbital.test/blog/"
POST_TITLE = "Ceramic Mugs Guide"
POST_TAGS = "crafts,pottery"
POST_SLUG = "ceramic-mugs-guide"
PAGE_TITLE = "Contact Orbital"
PAGE_SLUG = "contact-orbital"
DRAFT_TITLE = "Hidden Draft"
DRAFT_SLUG = "hidden-draft"


# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------
def expect_success(result):
    """CLI helpers return 0 or None on success."""
    assert result in (0, None)


def expect_failure(result):
    """CLI helpers must not report success."""
    assert result not in (0, None)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------
def translation_config(pattern="{path}.{lang}.{ext}"):
    return {
        "TRANSLATIONS": {"en": "", "es": "/es", "pl": "/pl"},
        "DEFAULT_LANG": "en",
        "TRANSLATIONS_PATTERN": pattern,
    }


def minimal_site(**overrides):
    """Construct a lightweight Nikola site for path and shortcode tests."""
    config = {
        "SITE_URL": SITE_URL,
        "TRANSLATIONS": {"en": "", "es": "/es"},
        "DEFAULT_LANG": "en",
        "INDEX_FILE": "index.html",
        "PRETTY_URLS": True,
    }
    config.update(overrides)
    return Nikola(**config)


class PluginFakeSite:
    """Minimal site stand-in for plugin category tests."""

    def __init__(self):
        self.debug = False
        self.shortcodes = {}
        self.calls = []

    def register_shortcode(self, name, handler):
        self.calls.append((name, handler))
        self.shortcodes[name] = handler


@contextmanager
def chdir(path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def load_site_from_project(project_root: Path) -> Nikola:
    """Load conf.py from a project directory and construct a Nikola site."""
    conf_path = project_root / "conf.py"
    with chdir(project_root):
        spec = importlib.util.spec_from_file_location("conf", str(conf_path))
        conf = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(conf)
        config = {
            key: value
            for key, value in conf.__dict__.items()
            if not key.startswith("__") or key in ("__file__",)
        }
        config["__configuration_filename__"] = str(conf_path)
        config["__cwd__"] = str(project_root)
        site = Nikola(**config)
        site.init_plugins()
        site.scan_posts()
        return site


def read_project_output(project_root: Path, relative_path: str) -> str:
    return (project_root / "output" / relative_path).read_text(encoding="utf-8")


def write_draft_post(project_root: Path) -> Path:
    draft_path = project_root / "posts" / f"{DRAFT_SLUG}.rst"
    draft_path.write_text(
        "\n".join(
            [
                f".. title: {DRAFT_TITLE}",
                f".. slug: {DRAFT_SLUG}",
                ".. date: 2026-01-01 12:00",
                ".. status: draft",
                "",
                "Secret draft body.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return draft_path


# ---------------------------------------------------------------------------
# Module-scoped fixture: initialized and built local project
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built_project(tmp_path_factory):
    """Create, populate, and build a local Nikola project."""
    root = tmp_path_factory.mktemp("nikola_orbital") / "site"
    expect_success(main(["init", "--quiet", str(root)]))

    with chdir(root):
        expect_success(main(["new_post", "-t", POST_TITLE, f"--tags={POST_TAGS}"]))
        expect_success(main(["new_page", "-t", PAGE_TITLE]))
        write_draft_post(root)
        expect_success(main(["build"]))

    return root
