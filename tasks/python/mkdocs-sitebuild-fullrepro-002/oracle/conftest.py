"""Shared fixtures, helpers, and constants for mkdocs oracle tests."""

import pytest
import textwrap
from pathlib import Path


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): declares atomic tests this integration test depends on",
    )


SITE_NAME = "AlphaDocs"
REPO_URL = "https://git.example.test/alpha/docs-repo/"


def make_file(src_path, docs_dir, site_dir, use_directory_urls=True, **kwargs):
    """Create a mkdocs File instance."""
    from mkdocs.structure.files import File

    return File(src_path, str(docs_dir), str(site_dir), use_directory_urls, **kwargs)


def create_project(base, pages=None, cfg_yaml=""):
    """
    Populate *base* with a ``docs/`` tree and ``mkdocs.yml``.

    *pages* maps relative doc paths to their text content.
    *cfg_yaml* is appended after the ``site_name`` line.
    Returns the base Path.
    """
    base = Path(base)
    docs = base / "docs"
    docs.mkdir(exist_ok=True)
    if pages is None:
        pages = {"index.md": "# Landing\n\nWelcome to AlphaDocs.\n"}
    for name, content in pages.items():
        p = docs / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    yaml_content = f"site_name: {SITE_NAME}\n"
    if cfg_yaml:
        yaml_content += textwrap.dedent(cfg_yaml).strip() + "\n"
    (base / "mkdocs.yml").write_text(yaml_content, encoding="utf-8")
    return base


def load_cfg(base, cfg_yaml="", pages=None):
    """Create a minimal project under *base* and return the loaded config."""
    from mkdocs.config import load_config

    create_project(base, pages=pages, cfg_yaml=cfg_yaml)
    return load_config(config_file=str(Path(base) / "mkdocs.yml"))
