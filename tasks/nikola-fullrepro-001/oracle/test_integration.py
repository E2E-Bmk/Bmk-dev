"""Integration tests for nikola-fullrepro-001.

Each test crosses at least two public API boundaries.
"""

from __future__ import annotations

import pytest

from nikola.__main__ import main
from nikola.plugin_categories import ShortcodePlugin
from nikola.shortcodes import apply_shortcodes

from conftest import (
    DRAFT_TITLE,
    PAGE_SLUG,
    PAGE_TITLE,
    POST_SLUG,
    POST_TITLE,
    PluginFakeSite,
    built_project,
    chdir,
    expect_failure,
    expect_success,
    load_site_from_project,
    minimal_site,
    read_project_output,
)


# ===================================================================
# CVI 1 – init project readable by later build
# ===================================================================


@pytest.mark.depends_on("test_version_command_runs_without_project_configuration")
def test_init_project_contains_configuration_and_content_roots(built_project):
    """CVI-1: Seam: lifecycle crossing — init creates project state consumed by build."""
    assert (built_project / "conf.py").is_file()
    assert (built_project / "posts").is_dir()
    assert (built_project / "pages").is_dir()
    assert (built_project / "output").is_dir()


# ===================================================================
# CVI 2 – new_post source discoverable after scan
# ===================================================================


@pytest.mark.depends_on("test_write_metadata_nikola_format_contains_declared_fields")
def test_new_post_source_is_discoverable_as_post_object(built_project):
    """CVI-2: Seam: state consistency — CLI-created source appears in site.posts."""
    site = load_site_from_project(built_project)
    titles = {post.title("en") for post in site.posts}
    assert POST_TITLE in titles


# ===================================================================
# CVI 3 – destination_path matches generated output
# ===================================================================


@pytest.mark.depends_on("test_slugify_lowercases_ascii_words")
def test_post_destination_path_matches_generated_output_file(built_project):
    """CVI-3: Seam: state consistency — Post.destination_path matches build output."""
    site = load_site_from_project(built_project)
    post = next(p for p in site.posts if p.title("en") == POST_TITLE)
    generated = built_project / "output" / post.destination_path("en")
    assert generated.is_file()
    assert POST_TITLE in generated.read_text(encoding="utf-8")


# ===================================================================
# CVI 4 – permalink agrees with path handlers
# ===================================================================


@pytest.mark.depends_on("test_translation_candidate_adds_language_before_extension")
def test_post_permalink_uses_registered_path_handlers(built_project):
    """CVI-4: Seam: protocol handoff — permalink and path handler agree for same post."""
    site = load_site_from_project(built_project)
    post = next(p for p in site.posts if p.title("en") == POST_TITLE)
    assert post.permalink("en") == f"/posts/{POST_SLUG}/"


# ===================================================================
# CVI 5 – taxonomy pages reflect post tag metadata
# ===================================================================


@pytest.mark.depends_on("test_bool_from_meta_accepts_true_word")
def test_category_outputs_match_post_tag_metadata(built_project):
    """CVI-5: Seam: state consistency — tag metadata and category pages agree."""
    source = (built_project / "posts" / f"{POST_SLUG}.rst").read_text(encoding="utf-8")
    assert "crafts" in source and "pottery" in source
    assert (built_project / "output" / "categories" / "crafts" / "index.html").is_file()
    assert (built_project / "output" / "categories" / "pottery" / "index.html").is_file()


# ===================================================================
# CVI 6 – RSS excludes draft posts
# ===================================================================


@pytest.mark.depends_on("test_bool_from_meta_accepts_false_word")
def test_rss_feed_excludes_draft_posts(built_project):
    """CVI-6: Seam: config interaction — draft status metadata excludes RSS entries."""
    rss = read_project_output(built_project, "rss.xml")
    assert POST_TITLE in rss
    assert DRAFT_TITLE not in rss


# ===================================================================
# CVI 7 – template context title matches generated HTML
# ===================================================================


@pytest.mark.depends_on("test_apply_shortcodes_replaces_single_shortcode")
def test_generated_post_page_contains_scanned_post_title(built_project):
    """CVI-7: Seam: protocol handoff — scanned post title appears in rendered HTML."""
    site = load_site_from_project(built_project)
    post = next(p for p in site.posts if p.title("en") == POST_TITLE)
    html = read_project_output(built_project, post.destination_path("en"))
    assert post.title("en") in html


# ===================================================================
# CVI 8 – site shortcode registry matches standalone shortcode API
# ===================================================================


@pytest.mark.depends_on("test_apply_shortcodes_replaces_single_shortcode")
def test_site_shortcode_registry_matches_standalone_application():
    """CVI-8: Seam: state consistency — site registry and standalone shortcode API agree."""
    site = minimal_site()
    site.register_shortcode("marker", lambda site, data, lang, post=None: "MARKER")

    via_site, site_deps = site.apply_shortcodes("{{% marker %}}", "fragment.rst", "en", {})
    via_module, module_deps = apply_shortcodes(
        "{{% marker %}}",
        site.shortcode_registry,
        site,
        "fragment.rst",
        True,
        "en",
        {},
    )
    assert via_site == via_module == "MARKER"
    assert site_deps == module_deps == []


# ===================================================================
# CVI 9 – sitemap references generated public URL
# ===================================================================


@pytest.mark.depends_on("test_encodelink_escapes_spaces")
def test_sitemap_lists_generated_post_url(built_project):
    """CVI-9: Seam: state consistency — sitemap URL corresponds to generated post output."""
    sitemap = read_project_output(built_project, "sitemap.xml")
    assert f"posts/{POST_SLUG}" in sitemap
    assert (built_project / "output" / "posts" / POST_SLUG / "index.html").is_file()


# ===================================================================
# CVI 10 – compiler selected for source extension
# ===================================================================


@pytest.mark.depends_on("test_slugify_lowercases_ascii_words")
def test_rst_compiler_selected_for_post_source_extension(built_project):
    """CVI-10: Seam: protocol handoff — scanned post source uses rest compiler."""
    site = load_site_from_project(built_project)
    post = next(p for p in site.posts if p.title("en") == POST_TITLE)
    compiler = site.get_compiler(post.source_path)
    assert compiler.name == "rest"


# ===================================================================
# Build output projections
# ===================================================================


def test_build_writes_index_page(built_project):
    """Seam: lifecycle crossing — build command writes site index output."""
    assert (built_project / "output" / "index.html").is_file()
    assert POST_TITLE in read_project_output(built_project, "index.html")


def test_build_writes_page_output(built_project):
    """Seam: lifecycle crossing — new_page source produces page output."""
    assert (built_project / "output" / "pages" / PAGE_SLUG / "index.html").is_file()
    assert PAGE_TITLE in read_project_output(
        built_project, f"pages/{PAGE_SLUG}/index.html"
    )


def test_build_writes_archive_and_feed_files(built_project):
    """Seam: state consistency — build emits archive, RSS, and sitemap together."""
    assert (built_project / "output" / "archive.html").is_file()
    assert (built_project / "output" / "rss.xml").is_file()
    assert (built_project / "output" / "sitemap.xml").is_file()


# ===================================================================
# Path and link generation
# ===================================================================


def test_custom_path_handler_produces_relative_and_link_paths():
    """Seam: config interaction — registered path handler feeds path() resolution.

    Crosses register_path_handler() (write) and path() (read) boundaries.
    """
    site = minimal_site()
    site.register_path_handler("custom", lambda name, lang: ["custom", lang, name])
    assert site.path("custom", "widget", "en", False) == "custom/en/widget"
    assert site.path("custom", "widget", "es", True) == "/custom/es/widget"


# ===================================================================
# Plugin contracts
# ===================================================================


def test_shortcode_plugin_registers_handler_on_site():
    """Seam: protocol handoff — ShortcodePlugin registers handler on site.shortcodes."""

    class MarkerShortcode(ShortcodePlugin):
        name = "marker"

        def handler(self, site, data, lang, post=None, **kw):
            return "handled"

    fake = PluginFakeSite()
    plugin = MarkerShortcode()
    plugin.set_site(fake)
    assert "marker" in fake.shortcodes
    assert fake.shortcodes["marker"]("site", "", "en") == "handled"


# ===================================================================
# CLI error propagation
# ===================================================================


def test_unknown_command_returns_failure():
    """Seam: error propagation — unknown CLI command returns non-zero status."""
    expect_failure(main(["definitely_unknown_command"]))


def test_build_without_configuration_returns_failure(tmp_path):
    """Seam: error propagation — build requires an existing project configuration."""
    with chdir(tmp_path):
        expect_failure(main(["build"]))


def test_invalid_configuration_file_returns_failure(tmp_path):
    """Seam: error propagation — malformed conf.py prevents successful build."""
    bad_conf = tmp_path / "bad_conf.py"
    bad_conf.write_text("this is not python !!!", encoding="utf-8")
    expect_failure(main(["--conf=" + str(bad_conf), "build"]))


def test_missing_configuration_file_returns_failure(tmp_path):
    """Seam: error propagation — missing conf path prevents successful build."""
    expect_failure(main(["--conf=" + str(tmp_path / "missing.py"), "build"]))


def test_invalid_command_option_returns_failure(built_project):
    """Seam: error propagation — invalid CLI options return non-zero status."""
    with chdir(built_project):
        expect_failure(main(["check", "--not-a-real-option"]))


def test_duplicate_new_post_returns_failure(built_project):
    """Seam: error propagation — duplicate new_post title is rejected."""
    with chdir(built_project):
        expect_failure(main(["new_post", "-t", POST_TITLE]))


# ===================================================================
# Cross-view consistency checks
# ===================================================================


def test_index_feed_and_sitemap_reference_same_post_url(built_project):
    """Seam: state consistency — index, RSS, and sitemap reference the same post URL."""
    index = read_project_output(built_project, "index.html")
    rss = read_project_output(built_project, "rss.xml")
    sitemap = read_project_output(built_project, "sitemap.xml")
    needle = f"posts/{POST_SLUG}"
    assert needle in index
    assert POST_TITLE in rss
    assert needle in sitemap


def test_check_command_accepts_generated_site(built_project):
    """Seam: lifecycle crossing — check validates the generated projection."""
    with chdir(built_project):
        expect_success(main(["check", "--check-links", "--check-files"]))


def test_manual_draft_source_remains_excluded_from_public_index(built_project):
    """Seam: config interaction — draft metadata keeps draft out of public index lists."""
    index = read_project_output(built_project, "index.html")
    assert POST_TITLE in index
    assert DRAFT_TITLE not in index
