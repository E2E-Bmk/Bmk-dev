"""Shared fixtures, helpers, and constants for pelican-sitegen-fullrepro-001 oracle."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pelican.settings import read_settings


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic tests this integration test depends on",
    )


# ---------------------------------------------------------------------------
# Anti-memorization constants (all values differ from upstream test suite)
# ---------------------------------------------------------------------------
SITE_NAME = "Emerald Notes"
SITE_URL = "https://orbital.test"
FEED_PATH = "syndication/main.atom.xml"
CAT_FEED_PATTERN = "syndication/{slug}.atom.xml"

ARTICLE_TITLE = "Ceramic Mugs Guide"
ARTICLE_DATE = "2015-08-14 09:30"
ARTICLE_CATEGORY = "Lifestyle"
ARTICLE_TAGS = "ceramics, crafts"
ARTICLE_SLUG = "ceramic-mugs-guide"
ARTICLE_AUTHOR = "Tomoko Nagai"
ARTICLE_SUMMARY = "A detailed look at handmade ceramics."

HIDDEN_TITLE = "Secret Recipe"
HIDDEN_SLUG = "secret-recipe"

DRAFT_TITLE = "Unfinished Thoughts"
DRAFT_SLUG = "unfinished-thoughts"

PAGE_TITLE = "Contact Us"
PAGE_SLUG = "contact-us"
PAGE_BODY = "Reach us at hello@orbital.test."

STATIC_ASSET = "banner.txt"
STATIC_CONTENT = "BANNER_DATA"

ATOM_NS = "http://www.w3.org/2005/Atom"

# ---------------------------------------------------------------------------
# Jinja2 template strings for custom theme
# ---------------------------------------------------------------------------
ARTICLE_TPL = "\n".join([
    "ART_TITLE={{ article.title }}",
    "ART_URL={{ article.url }}",
    "ART_SAVEAS={{ article.save_as }}",
    "ART_CAT={{ article.category }}",
    "ART_AUTHOR={{ article.author }}",
    "ART_TAGS={% for t in article.tags %}{{ t }};{% endfor %}",
    "ART_SUMMARY={{ article.summary|striptags|trim }}",
    "ART_CONTENT={{ article.content }}",
    "CFG_SITENAME={{ SITENAME }}",
    "CFG_SITEURL={{ SITEURL }}",
])

PAGE_TPL = "\n".join([
    "PG_TITLE={{ page.title }}",
    "PG_URL={{ page.url }}",
    "PG_CONTENT={{ page.content }}",
])

INDEX_TPL = "IDX={% for a in articles %}{{ a.title }};{% endfor %}"
CAT_TPL = "CAT={{ category }}"
TAG_TPL = "TAG={{ tag }}"
AUTH_TPL = "AUTH={{ author }}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def wrapper_settings(**overrides):
    """Minimal settings suitable for taxonomy wrapper and paginator tests."""
    defaults = {
        "AUTHOR_URL": "writers/{slug}.html",
        "AUTHOR_SAVE_AS": "writers/{slug}.html",
        "CATEGORY_URL": "topics/{slug}.html",
        "CATEGORY_SAVE_AS": "topics/{slug}.html",
        "TAG_URL": "labels/{slug}.html",
        "TAG_SAVE_AS": "labels/{slug}.html",
    }
    defaults.update(overrides)
    return read_settings(override=defaults)


def build_site_tree(root):
    """Create directories, templates, and content files for a full test site.

    Returns (content, output, theme) paths.
    """
    content = root / "content"
    output = root / "output"
    theme = root / "theme"
    for d in [
        content / "articles",
        content / "pages",
        content / "assets",
        theme / "templates",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    (theme / "templates" / "article.html").write_text(ARTICLE_TPL, encoding="utf-8")
    (theme / "templates" / "page.html").write_text(PAGE_TPL, encoding="utf-8")
    (theme / "templates" / "index.html").write_text(INDEX_TPL, encoding="utf-8")
    (theme / "templates" / "category.html").write_text(CAT_TPL, encoding="utf-8")
    (theme / "templates" / "tag.html").write_text(TAG_TPL, encoding="utf-8")
    (theme / "templates" / "author.html").write_text(AUTH_TPL, encoding="utf-8")

    (content / "articles" / "mugs.md").write_text(
        f"Title: {ARTICLE_TITLE}\n"
        f"Date: {ARTICLE_DATE}\n"
        f"Category: {ARTICLE_CATEGORY}\n"
        f"Tags: {ARTICLE_TAGS}\n"
        f"Slug: {ARTICLE_SLUG}\n"
        f"Author: {ARTICLE_AUTHOR}\n"
        f"Summary: {ARTICLE_SUMMARY}\n\n"
        f"Exploring [banner]({{static}}/assets/{STATIC_ASSET}) in detail.",
        encoding="utf-8",
    )
    (content / "articles" / "secret.md").write_text(
        f"Title: {HIDDEN_TITLE}\nDate: 2015-08-15\n"
        f"Status: hidden\nSlug: {HIDDEN_SLUG}\n\nSecret content.",
        encoding="utf-8",
    )
    (content / "articles" / "wip.md").write_text(
        f"Title: {DRAFT_TITLE}\nDate: 2015-08-16\n"
        f"Status: draft\nSlug: {DRAFT_SLUG}\n\nWork in progress.",
        encoding="utf-8",
    )
    (content / "pages" / "contact.md").write_text(
        f"Title: {PAGE_TITLE}\nSlug: {PAGE_SLUG}\n\n{PAGE_BODY}",
        encoding="utf-8",
    )
    (content / "assets" / STATIC_ASSET).write_text(
        STATIC_CONTENT, encoding="utf-8"
    )
    return content, output, theme


def generation_settings(content, output, theme, **extra):
    """Build a complete settings dict for site generation."""
    overrides = {
        "PATH": str(content),
        "OUTPUT_PATH": str(output),
        "THEME": str(theme),
        "SITENAME": SITE_NAME,
        "SITEURL": SITE_URL,
        "ARTICLE_PATHS": ["articles"],
        "PAGE_PATHS": ["pages"],
        "STATIC_PATHS": ["assets"],
        "ARTICLE_URL": "entries/{slug}.html",
        "ARTICLE_SAVE_AS": "entries/{slug}.html",
        "DRAFT_URL": "wip/{slug}.html",
        "DRAFT_SAVE_AS": "wip/{slug}.html",
        "PAGE_URL": "pg/{slug}.html",
        "PAGE_SAVE_AS": "pg/{slug}.html",
        "AUTHOR_URL": "writers/{slug}.html",
        "AUTHOR_SAVE_AS": "writers/{slug}.html",
        "CATEGORY_URL": "topics/{slug}.html",
        "CATEGORY_SAVE_AS": "topics/{slug}.html",
        "TAG_URL": "labels/{slug}.html",
        "TAG_SAVE_AS": "labels/{slug}.html",
        "FEED_ALL_ATOM": FEED_PATH,
        "CATEGORY_FEED_ATOM": CAT_FEED_PATTERN,
        "DIRECT_TEMPLATES": ["index"],
        "ARCHIVES_SAVE_AS": "",
        "TAGS_SAVE_AS": "",
        "CATEGORIES_SAVE_AS": "",
        "AUTHORS_SAVE_AS": "",
        "YEAR_ARCHIVE_SAVE_AS": "",
        "MONTH_ARCHIVE_SAVE_AS": "",
        "DAY_ARCHIVE_SAVE_AS": "",
        "TIMEZONE": "UTC",
        "DELETE_OUTPUT_DIRECTORY": True,
    }
    overrides.update(extra)
    return read_settings(override=overrides)


def read_output(output_dir, rel_path):
    """Read text from a generated output file."""
    return (Path(output_dir) / rel_path).read_text(encoding="utf-8")


def parse_feed_entries(output_dir, feed_rel=None):
    """Parse an Atom feed and return its <entry> elements."""
    if feed_rel is None:
        feed_rel = FEED_PATH
    root = ET.fromstring(read_output(output_dir, feed_rel))
    return root.findall(f"{{{ATOM_NS}}}entry")


# ---------------------------------------------------------------------------
# Module-scoped fixture: generated site (used by integration tests)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def generated_site(tmp_path_factory):
    """Generate a complete test site and return paths + settings."""
    from pelican import Pelican

    root = tmp_path_factory.mktemp("pelican_orbital")
    content, output, theme = build_site_tree(root)
    settings = generation_settings(content, output, theme)
    Pelican(settings).run()
    return {
        "root": root,
        "content": content,
        "output": output,
        "theme": theme,
        "settings": settings,
    }
