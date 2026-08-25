"""Integration layer tests for pelican-sitegen-fullrepro-001.

Each test verifies ≥2 different public API boundaries cooperating.
Composition Dependency: even if all atomic tests pass, these can still fail
because component seams don't align.

Seam types targeted:
  - State consistency (settings → generation output)
  - Protocol handoff (metadata → template context → rendered output)
  - Error propagation (settings + generation error chain)
  - Config interaction (settings affecting multiple outputs)
  - Lifecycle crossing (CLI → settings → generation)
"""
from __future__ import annotations

import pytest

from pelican import Pelican, get_config, parse_arguments
from pelican import signals as package_signals
from pelican.plugins import signals as plugin_signals
from pelican.paginator import Paginator
from pelican.readers import Readers
from pelican.settings import read_settings
from pelican.urlwrappers import Author, Category, Tag
from pelican.utils import slugify

from conftest import (
    ARTICLE_AUTHOR,
    ARTICLE_CATEGORY,
    ARTICLE_SLUG,
    ARTICLE_SUMMARY,
    ARTICLE_TAGS,
    ARTICLE_TITLE,
    ATOM_NS,
    DRAFT_SLUG,
    DRAFT_TITLE,
    HIDDEN_SLUG,
    HIDDEN_TITLE,
    PAGE_BODY,
    PAGE_SLUG,
    PAGE_TITLE,
    SITE_NAME,
    SITE_URL,
    STATIC_ASSET,
    STATIC_CONTENT,
    build_site_tree,
    generation_settings,
    parse_feed_entries,
    read_output,
    wrapper_settings,
)


# ===================================================================
# CVI 1 – Settings consistency (read_settings ↔ get_config)
# Seam: config interaction
# ===================================================================

@pytest.mark.depends_on(
    "test_read_settings_override_replaces_default",
    "test_get_config_produces_settings_mapping",
)
def test_settings_consistency_sitename_via_both_paths():
    """Seam: config interaction — read_settings and get_config produce same SITENAME."""
    """read_settings and get_config must produce the same SITENAME."""
    direct = read_settings(override={"SITENAME": "Orbital Alpha"})
    args = parse_arguments(["content", "-e", 'SITENAME="Orbital Alpha"'])
    via_cli = get_config(args)
    assert direct["SITENAME"] == via_cli["SITENAME"] == "Orbital Alpha"


@pytest.mark.depends_on(
    "test_read_settings_override_replaces_default",
    "test_get_config_sets_relative_urls_true",
)
def test_settings_consistency_relative_urls_via_both_paths():
    """Seam: config interaction — RELATIVE_URLS consistent across settings paths."""
    """RELATIVE_URLS must match across read_settings and get_config."""
    direct = read_settings(override={"RELATIVE_URLS": True})
    args = parse_arguments(["content", "--relative-urls"])
    via_cli = get_config(args)
    assert direct["RELATIVE_URLS"] is True
    assert via_cli["RELATIVE_URLS"] is True


# ===================================================================
# CVI 2 – Article metadata → content object → template context
# Seam: protocol handoff (Readers ↔ Pelican template rendering)
# ===================================================================

@pytest.mark.depends_on("test_readers_extracts_content_and_metadata")
def test_reader_title_matches_generated_article_title(generated_site):
    """Seam: protocol handoff — Readers title matches rendered article template output."""
    """Title from Readers.read_file must equal title in rendered output."""
    readers = Readers(generated_site["settings"])
    result = readers.read_file(
        base_path=str(generated_site["content"]),
        path="articles/mugs.md",
    )
    reader_title = result.metadata["title"]
    rendered = read_output(
        generated_site["output"], f"entries/{ARTICLE_SLUG}.html"
    )
    assert f"ART_TITLE={reader_title}" in rendered


@pytest.mark.depends_on("test_readers_extracts_content_and_metadata")
def test_article_category_propagated_to_template(generated_site):
    """Seam: protocol handoff — article category metadata propagated to template."""
    """Category in source metadata must appear in rendered article template."""
    rendered = read_output(
        generated_site["output"], f"entries/{ARTICLE_SLUG}.html"
    )
    assert f"ART_CAT={ARTICLE_CATEGORY}" in rendered


@pytest.mark.depends_on("test_readers_extracts_content_and_metadata")
def test_article_tags_propagated_to_template(generated_site):
    """Seam: protocol handoff — article tags metadata propagated to template."""
    """Each tag from source metadata must appear in rendered article."""
    rendered = read_output(
        generated_site["output"], f"entries/{ARTICLE_SLUG}.html"
    )
    for tag in ARTICLE_TAGS.split(", "):
        assert f"{tag};" in rendered


# ===================================================================
# CVI 3 – URL/save-path settings ↔ file location ↔ template context
# Seam: state consistency (settings → filesystem → template variable)
# ===================================================================

@pytest.mark.depends_on("test_read_settings_override_replaces_default")
def test_article_save_as_determines_file_and_template_value(generated_site):
    """Seam: state consistency — ARTICLE_SAVE_AS determines file path and template value."""
    """ARTICLE_SAVE_AS must determine file path AND template variable."""
    expected_path = f"entries/{ARTICLE_SLUG}.html"
    assert (generated_site["output"] / expected_path).is_file()
    rendered = read_output(generated_site["output"], expected_path)
    assert f"ART_SAVEAS={expected_path}" in rendered


@pytest.mark.depends_on("test_read_settings_override_replaces_default")
def test_page_save_as_determines_page_location(generated_site):
    """Seam: state consistency — PAGE_SAVE_AS determines page location and template URL."""
    """PAGE_SAVE_AS must determine page file location and template URL."""
    expected = f"pg/{PAGE_SLUG}.html"
    assert (generated_site["output"] / expected).is_file()
    rendered = read_output(generated_site["output"], expected)
    assert f"PG_URL={expected}" in rendered


# ===================================================================
# CVI 4 – Status → index membership + feed membership
# Seam: state consistency (content status → two output projections)
# ===================================================================

def test_published_article_in_index_and_feed(generated_site):
    """CVI-4: published article appears in both index and feed projections."""
    """Published article must appear in BOTH index and feed."""
    index = read_output(generated_site["output"], "index.html")
    assert ARTICLE_TITLE in index

    entries = parse_feed_entries(generated_site["output"])
    titles = [e.findtext(f"{{{ATOM_NS}}}title") for e in entries]
    assert ARTICLE_TITLE in titles


def test_hidden_article_has_file_but_absent_from_index(generated_site):
    """CVI-4: hidden article retains file but absent from index."""
    """Hidden article must retain its file but not appear in index."""
    assert (
        generated_site["output"] / f"entries/{HIDDEN_SLUG}.html"
    ).is_file()
    index = read_output(generated_site["output"], "index.html")
    assert HIDDEN_TITLE not in index


def test_hidden_article_excluded_from_feed(generated_site):
    """CVI-4: hidden article excluded from Atom feed."""
    """Hidden article must not appear in the Atom feed."""
    entries = parse_feed_entries(generated_site["output"])
    titles = [e.findtext(f"{{{ATOM_NS}}}title") for e in entries]
    assert HIDDEN_TITLE not in titles


def test_draft_at_draft_location_excluded_from_index(generated_site):
    """CVI-4: draft at DRAFT_SAVE_AS absent from index."""
    """Draft must be at DRAFT_SAVE_AS and absent from the index."""
    assert (generated_site["output"] / f"wip/{DRAFT_SLUG}.html").is_file()
    index = read_output(generated_site["output"], "index.html")
    assert DRAFT_TITLE not in index


def test_draft_excluded_from_feed(generated_site):
    """CVI-4: draft article excluded from Atom feed."""
    """Draft article must not appear in the Atom feed."""
    entries = parse_feed_entries(generated_site["output"])
    titles = [e.findtext(f"{{{ATOM_NS}}}title") for e in entries]
    assert DRAFT_TITLE not in titles


# ===================================================================
# CVI 5 – Taxonomy slug ↔ collection page path
# Seam: state consistency (wrapper slug → generated file location)
# ===================================================================

@pytest.mark.depends_on("test_category_slug_from_display_name")
def test_category_wrapper_slug_matches_collection_page(generated_site):
    """CVI-5: Category wrapper slug matches generated collection page path."""
    """Category wrapper slug must agree with the generated page path."""
    cat = Category(ARTICLE_CATEGORY, settings=generated_site["settings"])
    expected = f"topics/{cat.slug}.html"
    assert (generated_site["output"] / expected).is_file()


@pytest.mark.depends_on("test_tag_slug_from_display_name")
def test_tag_wrapper_slug_matches_generated_page(generated_site):
    """CVI-5: Tag wrapper slug matches generated tag page path."""
    """Tag wrapper slug must agree with the generated tag page path."""
    first_tag = ARTICLE_TAGS.split(", ")[0]
    tag = Tag(first_tag, settings=generated_site["settings"])
    expected = f"labels/{tag.slug}.html"
    assert (generated_site["output"] / expected).is_file()


@pytest.mark.depends_on("test_author_slug_derived_from_display_name")
def test_author_wrapper_slug_matches_generated_page(generated_site):
    """CVI-5: Author wrapper slug matches generated author page path."""
    """Author wrapper slug must agree with the generated author page path."""
    author = Author(ARTICLE_AUTHOR, settings=generated_site["settings"])
    expected = f"writers/{author.slug}.html"
    assert (generated_site["output"] / expected).is_file()


# ===================================================================
# CVI 6 – Feed entry ↔ article page
# Seam: protocol handoff (feed generator ↔ article generator)
# ===================================================================

def test_feed_entry_title_matches_article_page(generated_site):
    """CVI-6: feed entry title matches article page rendered title."""
    """Feed entry title must match the title rendered in the article page."""
    entries = parse_feed_entries(generated_site["output"])
    feed_title = entries[0].findtext(f"{{{ATOM_NS}}}title")
    rendered = read_output(
        generated_site["output"], f"entries/{ARTICLE_SLUG}.html"
    )
    assert f"ART_TITLE={feed_title}" in rendered


def test_feed_entry_link_includes_siteurl_and_article_url(generated_site):
    """CVI-6: feed entry link combines SITEURL and article URL."""
    """Feed entry link href must be SITEURL + article URL."""
    entries = parse_feed_entries(generated_site["output"])
    link = entries[0].find(f"{{{ATOM_NS}}}link")
    href = link.attrib["href"]
    assert href == f"{SITE_URL}/entries/{ARTICLE_SLUG}.html"


# ===================================================================
# CVI 7 – Static link resolution
# Seam: state consistency (STATIC_PATHS → output tree → {static} href)
# ===================================================================

def test_static_asset_copied_and_link_resolves(generated_site):
    """CVI-7: static asset copied and {static} link resolves in output."""
    """Static asset must be copied AND {static} link must resolve to it."""
    assert (
        read_output(generated_site["output"], f"assets/{STATIC_ASSET}")
        == STATIC_CONTENT
    )
    rendered = read_output(
        generated_site["output"], f"entries/{ARTICLE_SLUG}.html"
    )
    assert f'href="{SITE_URL}/assets/{STATIC_ASSET}"' in rendered


# ===================================================================
# CVI 8 – Pagination consistency
# Seam: state consistency (Paginator properties ↔ Page neighbor flags)
# ===================================================================

@pytest.mark.depends_on(
    "test_paginator_page_range_starts_at_one",
    "test_paginator_first_page_has_next_not_previous",
)
def test_paginator_range_and_neighbors_are_consistent():
    """CVI-8: Paginator page_range, num_pages, and neighbor flags agree."""
    """page_range length, num_pages, and neighbor flags must all agree."""
    p = Paginator(
        "entries", "", list(range(23)), wrapper_settings(), per_page=6
    )
    assert len(p.page_range) == p.num_pages
    for n in p.page_range:
        page = p.page(n)
        assert page.has_previous() == (n > 1)
        assert page.has_next() == (n < p.num_pages)


# ===================================================================
# Settings → generation pipeline
# Seam: config interaction (settings values → rendered template output)
# ===================================================================

@pytest.mark.depends_on("test_read_settings_override_replaces_default")
def test_sitename_setting_appears_in_rendered_article(generated_site):
    """Seam: config interaction — SITENAME setting appears in rendered article."""
    """SITENAME from settings must appear in the article template output."""
    rendered = read_output(
        generated_site["output"], f"entries/{ARTICLE_SLUG}.html"
    )
    assert f"CFG_SITENAME={SITE_NAME}" in rendered


@pytest.mark.depends_on("test_read_settings_override_replaces_default")
def test_siteurl_setting_appears_in_feed_link(generated_site):
    """Seam: config interaction — SITEURL setting appears in feed entry link."""
    """SITEURL from settings must appear in feed entry link href."""
    entries = parse_feed_entries(generated_site["output"])
    link = entries[0].find(f"{{{ATOM_NS}}}link")
    assert SITE_URL in link.attrib["href"]


# ===================================================================
# Source exclusion
# Seam: state consistency (content source ↔ output tree)
# ===================================================================

def test_markdown_source_excluded_from_output(generated_site):
    """Seam: state consistency — source .md files excluded from output tree."""
    """Source .md files must NOT be copied to the output tree."""
    all_files = {
        p.name for p in generated_site["output"].rglob("*") if p.is_file()
    }
    assert "mugs.md" not in all_files


# ===================================================================
# Category feed ↔ taxonomy slug
# Seam: state consistency (Category slug → category feed file path)
# ===================================================================

@pytest.mark.depends_on("test_category_slug_from_display_name")
def test_category_feed_path_uses_category_slug(generated_site):
    """Seam: state consistency — category feed path uses Category slug."""
    """Category feed file path must include the category slug."""
    cat = Category(ARTICLE_CATEGORY, settings=generated_site["settings"])
    expected = f"syndication/{cat.slug}.atom.xml"
    assert (generated_site["output"] / expected).is_file()


# ===================================================================
# Signals identity across import paths
# Seam: protocol handoff (pelican.signals ↔ pelican.plugins.signals)
# ===================================================================

@pytest.mark.depends_on(
    "test_signals_available_from_pelican_package",
    "test_signals_available_from_plugins_package",
)
def test_signal_objects_identical_across_import_paths():
    """Seam: protocol handoff — signal objects identical across import paths."""
    """Signal objects must be the same object from both import paths."""
    assert (
        package_signals.article_generator_finalized
        is plugin_signals.article_generator_finalized
    )
    assert (
        package_signals.content_object_init
        is plugin_signals.content_object_init
    )


# ===================================================================
# slugify ↔ taxonomy wrapper consistency
# Seam: protocol handoff (slugify algorithm ↔ wrapper slug computation)
# ===================================================================

@pytest.mark.depends_on(
    "test_slugify_lowercases_without_preserve_case",
    "test_category_slug_from_display_name",
)
def test_slugify_consistent_with_wrapper_slug():
    """Seam: protocol handoff — slugify output matches taxonomy wrapper slug."""
    """slugify(name) must match Category(name).slug for the same name."""
    settings = wrapper_settings()
    name = "Artisan Pottery"
    manual_slug = slugify(
        name, regex_subs=settings.get("SLUG_REGEX_SUBSTITUTIONS", [])
    )
    cat_slug = Category(name, settings=settings).slug
    assert manual_slug == cat_slug


# ===================================================================
# CLI → settings → generation (lifecycle crossing)
# Seam: lifecycle crossing (parse_arguments → get_config → Pelican.run)
# ===================================================================

@pytest.mark.depends_on(
    "test_parse_arguments_extra_settings_accumulate",
    "test_get_config_produces_settings_mapping",
)
def test_cli_parsed_sitename_drives_generation(tmp_path):
    """Seam: lifecycle crossing — CLI parse_arguments to get_config to Pelican.run pipeline."""
    """parse_arguments → get_config → Pelican.run → SITENAME in output."""
    content, output, theme = build_site_tree(tmp_path)
    args = parse_arguments([str(content), "-e", 'SITENAME="CLI Orbital"'])
    cli_name = get_config(args)["SITENAME"]
    settings = generation_settings(content, output, theme, SITENAME=cli_name)
    Pelican(settings).run()
    rendered = read_output(output, f"entries/{ARTICLE_SLUG}.html")
    assert f"CFG_SITENAME={cli_name}" in rendered


# ===================================================================
# Error propagation: missing content PATH
# Seam: error propagation (read_settings → Pelican failure chain)
# ===================================================================

@pytest.mark.depends_on("test_read_settings_override_replaces_default")
def test_generation_fails_when_content_path_missing(tmp_path):
    """Seam: error propagation — Pelican.run fails when content PATH missing."""
    """Pelican.run() must fail when PATH does not exist."""
    settings = read_settings(
        override={
            "PATH": str(tmp_path / "nonexistent_content"),
            "OUTPUT_PATH": str(tmp_path / "output"),
        }
    )
    with pytest.raises((SystemExit, FileNotFoundError, OSError)):
        Pelican(settings).run()


# ===================================================================
# Page metadata → rendered page (protocol handoff)
# Seam: protocol handoff (page metadata → template rendering)
# ===================================================================

def test_page_metadata_and_body_in_rendered_output(generated_site):
    """Seam: protocol handoff — page metadata and body appear in rendered output."""
    """Page title and body from metadata must appear in rendered output."""
    rendered = read_output(
        generated_site["output"], f"pg/{PAGE_SLUG}.html"
    )
    assert f"PG_TITLE={PAGE_TITLE}" in rendered
    assert PAGE_BODY in rendered
