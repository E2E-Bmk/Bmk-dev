"""
Integration-layer tests for mkdocs.

Each test verifies ≥2 different public API boundaries cooperating.
Composition-dependency: even if every atomic test passes, these tests
can still fail because component seams don't align.
"""

import json
import pytest
from pathlib import Path

from mkdocs.config import load_config
from mkdocs.commands.build import build
from mkdocs.structure.files import File, Files, InclusionLevel, get_files
from mkdocs.structure.pages import Page
from mkdocs.structure.nav import Navigation, Section, Link, get_navigation
from mkdocs.structure.toc import AnchorLink
from mkdocs.exceptions import Abort, ConfigurationError
from mkdocs.plugins import BasePlugin, PluginCollection, event_priority
from mkdocs.theme import Theme

from conftest import make_file, create_project, load_cfg, SITE_NAME, REPO_URL


# ═══════════════════════════════════════════════════════════════
# CVI-1  site_dir agreement
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_load_config_mapping_and_attribute_access")
def test_build_output_written_to_effective_site_dir(tmp_path):
    """CVI-1: build output written to config-effective site_dir."""
    """Build must write into the config-effective site_dir."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Alpha Start\n\nContent.\n"},
        cfg_yaml="site_dir: custom_output",
    )
    build(cfg)
    site = Path(cfg["site_dir"])
    assert (site / "index.html").exists()


# ═══════════════════════════════════════════════════════════════
# CVI-2  use_directory_urls consistency
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on(
    "test_file_dest_uri_directory_urls_enabled",
    "test_page_render_produces_html_content",
)
def test_file_and_page_url_agree_directory_urls_on(tmp_path):
    """CVI-2: File.url and Page.url agree when directory URLs enabled."""
    """File.url and Page.url must agree when directory URLs are enabled."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Home\n", "guide.md": "# Guide\n"},
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)
    for page in nav.pages:
        assert page.url == page.file.url


@pytest.mark.depends_on("test_file_dest_uri_directory_urls_disabled")
def test_file_and_page_url_agree_directory_urls_off(tmp_path):
    """CVI-2: File.url and Page.url agree when directory URLs disabled."""
    """File.url and Page.url must agree when directory URLs are disabled."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Home\n", "reference.md": "# Ref\n"},
        cfg_yaml="use_directory_urls: false",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)
    for page in nav.pages:
        assert page.url == page.file.url


# ═══════════════════════════════════════════════════════════════
# CVI-3  nav-page object sharing
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_files_get_file_from_path_found")
def test_nav_page_same_object_as_file_page(tmp_path):
    """CVI-3: nav-referenced page is same object as file.page."""
    """A nav-referenced page must be the same object as file.page."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Home\n", "about.md": "# About\n"},
        cfg_yaml="nav:\n  - Home: index.md\n  - About: about.md",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)

    about_file = files.get_file_from_path("about.md")
    about_in_nav = [p for p in nav.pages if p.file.src_uri == "about.md"][0]
    assert about_file.page is about_in_nav


@pytest.mark.depends_on("test_files_get_file_from_path_found")
def test_previous_next_links_follow_nav_pages(tmp_path):
    """CVI-3: prev/next links follow Navigation.pages ordering."""
    """prev/next links must follow Navigation.pages ordering."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Home\n",
            "setup.md": "# Setup\n",
            "usage.md": "# Usage\n",
        },
        cfg_yaml="nav:\n  - Home: index.md\n  - Setup: setup.md\n  - Usage: usage.md",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)

    pages = nav.pages
    assert len(pages) == 3
    assert pages[0].next_page is pages[1]
    assert pages[1].previous_page is pages[0]
    assert pages[1].next_page is pages[2]
    assert pages[2].previous_page is pages[1]


# ═══════════════════════════════════════════════════════════════
# CVI-4  omitted pages
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_files_get_file_from_path_found")
def test_omitted_page_absent_from_nav_pages(tmp_path):
    """CVI-4: pages omitted from nav absent from Navigation.pages."""
    """Pages not in explicit nav must be absent from Navigation.pages."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Home\n",
            "listed.md": "# Listed\n",
            "unlisted.md": "# Unlisted\n",
        },
        cfg_yaml="nav:\n  - Home: index.md\n  - Listed: listed.md",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)

    nav_uris = {p.file.src_uri for p in nav.pages}
    assert "index.md" in nav_uris
    assert "listed.md" in nav_uris
    assert "unlisted.md" not in nav_uris


@pytest.mark.depends_on("test_files_get_file_from_path_found")
def test_omitted_page_no_previous_next(tmp_path):
    """CVI-4: omitted pages have no previous or next page links."""
    """Omitted pages must not have previous or next page links."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Home\n",
            "visible.md": "# Visible\n",
            "ghost.md": "# Ghost\n",
        },
        cfg_yaml="nav:\n  - Home: index.md\n  - Visible: visible.md",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)

    ghost_file = files.get_file_from_path("ghost.md")
    assert ghost_file.page is not None
    assert ghost_file.page.previous_page is None
    assert ghost_file.page.next_page is None


# ═══════════════════════════════════════════════════════════════
# CVI-5  exclusion consistency
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_inclusion_level_enum_members")
def test_excluded_file_absent_from_nav(tmp_path):
    """CVI-5: EXCLUDED files absent from navigation pages."""
    """EXCLUDED files must not appear in navigation."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Home\n",
            "public.md": "# Public\n",
            "secret.md": "# Secret\n",
        },
    )
    files = get_files(cfg)
    secret = files.get_file_from_path("secret.md")
    if secret is not None:
        secret.inclusion = InclusionLevel.EXCLUDED
    nav = get_navigation(files, cfg)

    nav_uris = {p.file.src_uri for p in nav.pages}
    assert "secret.md" not in nav_uris


# ═══════════════════════════════════════════════════════════════
# CVI-6  title consistency
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_page_title_from_nav_label")
def test_page_title_matches_nav_label_across_views(tmp_path):
    """CVI-6: nav label propagates as Page.title across file and nav views."""
    """Nav label must propagate as Page.title across file and nav views."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Something\n",
            "help.md": "# Anything\n",
        },
        cfg_yaml="nav:\n  - Home: index.md\n  - Help Section: help.md",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)

    help_page = [p for p in nav.pages if p.file.src_uri == "help.md"][0]
    assert help_page.title == "Help Section"
    assert files.get_file_from_path("help.md").page.title == "Help Section"


@pytest.mark.depends_on("test_page_render_produces_html_content")
def test_page_title_consistent_in_search_index(tmp_path):
    """CVI-6: search index entry titles match resolved page titles."""
    """Search index entry titles must match resolved page titles."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Portal Home\n\nWelcome.\n",
            "quickstart.md": "# Getting Started\n\nBegin.\n",
        },
    )
    build(cfg)

    search_path = Path(cfg["site_dir"]) / "search" / "search_index.json"
    assert search_path.exists()
    with open(search_path, encoding="utf-8") as fh:
        index = json.load(fh)

    titles = {doc["title"] for doc in index["docs"]}
    assert "Portal Home" in titles
    assert "Getting Started" in titles


# ═══════════════════════════════════════════════════════════════
# CVI-7  edit links
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on(
    "test_file_edit_uri_defaults_to_src_uri",
    "test_load_config_mapping_and_attribute_access",
)
def test_edit_url_from_repo_url_and_edit_uri(tmp_path):
    """CVI-7: Page.edit_url combines repo_url, edit_uri, and File.edit_uri."""
    """Page.edit_url must combine repo_url, edit_uri, and File.edit_uri."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Home\n", "guide.md": "# Guide\n"},
        cfg_yaml=f"repo_url: {REPO_URL}\nedit_uri: edit/main/docs/",
    )
    files = get_files(cfg)
    nav = get_navigation(files, cfg)

    guide = [p for p in nav.pages if p.file.src_uri == "guide.md"][0]
    guide.read_source(cfg)
    assert guide.edit_url is not None
    assert "guide.md" in guide.edit_url
    assert REPO_URL.rstrip("/") in guide.edit_url or "example.test" in guide.edit_url


# ═══════════════════════════════════════════════════════════════
# CVI-8  metadata removal
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on(
    "test_page_read_source_populates_markdown",
    "test_page_meta_from_yaml_front_matter",
)
def test_metadata_stripped_from_markdown_meta_preserved(tmp_path):
    """CVI-8: front matter stripped from markdown but preserved in meta."""
    """Front matter must be removed from markdown but available in meta."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "---\ntitle: My Title\nstatus: draft\n---\n# Heading\n\nBody.\n",
        encoding="utf-8",
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    page.read_source(cfg)

    assert "---" not in page.markdown
    assert "status:" not in page.markdown
    assert page.meta["status"] == "draft"
    assert page.meta["title"] == "My Title"


# ═══════════════════════════════════════════════════════════════
# CVI-9  base_url / url filter consistency
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_page_render_produces_html_content")
def test_rendered_links_consistent_with_page_urls(tmp_path):
    """CVI-9: internal Markdown links rewritten to correct relative URLs."""
    """Internal Markdown links must be rewritten to correct relative URLs."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Home\n\nGo to [FAQ](faq.md).\n",
            "faq.md": "# FAQ\n\nBack to [Home](index.md).\n",
        },
    )
    build(cfg)

    site = Path(cfg["site_dir"])
    home_html = (site / "index.html").read_text(encoding="utf-8")
    faq_html = (site / "faq" / "index.html").read_text(encoding="utf-8")

    assert 'href="faq/"' in home_html
    assert 'href="../"' in faq_html or 'href=".."' in faq_html


# ═══════════════════════════════════════════════════════════════
# CVI-10  search index
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_page_render_produces_html_content")
def test_search_index_written_under_site_dir(tmp_path):
    """CVI-10: default search plugin writes search_index.json under site_dir."""
    """Default search plugin must write search_index.json under site_dir."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Main Page\n\nSome content.\n"},
    )
    build(cfg)

    search_path = Path(cfg["site_dir"]) / "search" / "search_index.json"
    assert search_path.exists()

    with open(search_path, encoding="utf-8") as fh:
        index = json.load(fh)
    assert "docs" in index
    assert len(index["docs"]) >= 1


@pytest.mark.depends_on("test_page_render_produces_html_content")
def test_search_index_location_matches_page_url(tmp_path):
    """CVI-10: search entry location matches page URL."""
    """Each search entry location must match its page's URL."""
    cfg = load_cfg(
        tmp_path,
        pages={
            "index.md": "# Start\n",
            "reference.md": "# Reference Guide\n\nDetails.\n",
        },
    )
    build(cfg)

    search_path = Path(cfg["site_dir"]) / "search" / "search_index.json"
    with open(search_path, encoding="utf-8") as fh:
        index = json.load(fh)

    locations = {doc["location"] for doc in index["docs"]}
    assert any("reference" in loc for loc in locations)


# ═══════════════════════════════════════════════════════════════
# CVI-11  plugin event returns
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_plugin_collection_run_event_returns_item")
def test_plugin_event_return_replaces_item():
    """CVI-11: plugin handler return value replaces current event item."""
    """A handler returning a value must replace the current item."""

    class AppendPlugin(BasePlugin):
        def on_page_markdown(self, markdown, **kwargs):
            return markdown + "\n> appended"

    pc = PluginCollection()
    pc["appender"] = AppendPlugin()
    result = pc.run_event("page_markdown", item="# Original\n")
    assert "appended" in result
    assert result.startswith("# Original\n")


@pytest.mark.depends_on("test_plugin_collection_run_event_returns_item")
def test_plugin_event_none_preserves_item():
    """CVI-11: plugin handler returning None preserves current item."""
    """A handler returning None must preserve the current item."""

    class NoopPlugin(BasePlugin):
        def on_page_markdown(self, markdown, **kwargs):
            return None

    pc = PluginCollection()
    pc["noop"] = NoopPlugin()
    result = pc.run_event("page_markdown", item="# Keep This\n")
    assert result == "# Keep This\n"


# ═══════════════════════════════════════════════════════════════
# CVI-12  strict mode
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_load_config_mapping_and_attribute_access")
def test_strict_mode_unknown_key_raises_abort(tmp_path):
    """CVI-12: strict mode converts unknown config key warnings to Abort."""
    """In strict mode, unknown config keys must convert warnings → Abort."""
    create_project(
        tmp_path,
        cfg_yaml="strict: true\nzz_unknown_key_alpha: 42",
    )
    with pytest.raises(Abort):
        load_config(config_file=str(tmp_path / "mkdocs.yml"))


# ═══════════════════════════════════════════════════════════════
# Additional seams – render rewrites links via Files
# (state-consistency seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on(
    "test_page_render_produces_html_content",
    "test_files_get_file_from_path_found",
)
def test_render_rewrites_internal_links_via_files(tmp_path):
    """Seam: state consistency — render rewrites internal links via Files collection."""
    """Render must rewrite Markdown links to known files as relative URLs."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text("# Home\n\n[More](details.md)\n", encoding="utf-8")
    (docs / "details.md").write_text("# Details\n", encoding="utf-8")
    site = tmp_path / "s"
    site.mkdir()

    cfg = load_cfg(tmp_path)
    f_idx = make_file("index.md", docs, site)
    f_det = make_file("details.md", docs, site)
    files = Files([f_idx, f_det])

    page = Page(title=None, file=f_idx, config=cfg)
    page.read_source(cfg)
    page.render(cfg, files)

    assert "details" in page.content


# ═══════════════════════════════════════════════════════════════
# Additional seams – generated file in collection
# (protocol-handoff seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on(
    "test_file_generated_with_content_string",
    "test_files_append_adds_file",
)
def test_generated_file_added_to_files_and_discoverable(tmp_path):
    """Seam: protocol handoff — generated File appended to Files becomes discoverable."""
    """A generated File, once appended to Files, must be discoverable."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "index.md").write_text("", encoding="utf-8")

    f_real = make_file("index.md", docs, site)
    f_gen = File.generated(str(site), "extra/generated.md", content="# Gen\n")

    fs = Files([f_real])
    fs.append(f_gen)

    assert fs.get_file_from_path("extra/generated.md") is f_gen
    doc_uris = [f.src_uri for f in fs.documentation_pages()]
    assert "extra/generated.md" in doc_uris


# ═══════════════════════════════════════════════════════════════
# Additional seams – INHERIT config merge
# (config-interaction seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_load_config_mapping_and_attribute_access")
def test_inherit_config_deep_merges_mappings(tmp_path):
    """Seam: config interaction — INHERIT deep-merges parent config with child overrides."""
    """INHERIT must deep-merge parent config; child site_name wins."""
    parent = tmp_path / "base.yml"
    parent.write_text(
        "site_name: Parent Site\ntheme:\n  name: mkdocs\n", encoding="utf-8"
    )

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# X\n", encoding="utf-8")

    child = tmp_path / "mkdocs.yml"
    child.write_text(
        "INHERIT: base.yml\nsite_name: Child Override\n", encoding="utf-8"
    )

    cfg = load_config(config_file=str(child))
    assert cfg["site_name"] == "Child Override"
    env = cfg["theme"].get_env()
    assert "main.html" in env.list_templates()


# ═══════════════════════════════════════════════════════════════
# Additional seams – !ENV tag
# (config-interaction seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_load_config_mapping_and_attribute_access")
def test_env_tag_value_propagates_to_config(tmp_path, monkeypatch):
    """Seam: config interaction — !ENV tag reads environment variable into config."""
    """!ENV tag must read environment variable into config value."""
    monkeypatch.setenv("ALPHA_SITE_URL", "https://alpha.example.test/docs/")
    cfg = load_cfg(tmp_path, cfg_yaml="site_url: !ENV ALPHA_SITE_URL")
    assert cfg["site_url"] == "https://alpha.example.test/docs/"


# ═══════════════════════════════════════════════════════════════
# Additional seams – default search active
# (lifecycle seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_page_render_produces_html_content")
def test_default_search_active_produces_index(tmp_path):
    """Seam: lifecycle crossing — default search plugin produces index during build."""
    """Default plugins include search; it must produce a search index."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Welcome\n\nSearchable content.\n"},
    )
    build(cfg)

    search_file = Path(cfg["site_dir"]) / "search" / "search_index.json"
    assert search_file.exists()

    with open(search_file, encoding="utf-8") as fh:
        data = json.load(fh)
    assert len(data.get("docs", [])) >= 1


@pytest.mark.depends_on("test_load_config_mapping_and_attribute_access")
def test_explicit_empty_plugins_disables_search(tmp_path):
    """Seam: config interaction — explicit empty plugins list disables default search."""
    """An explicit empty plugins list must disable the default search."""
    cfg = load_cfg(
        tmp_path,
        pages={"index.md": "# Home\n"},
        cfg_yaml="plugins: []",
    )
    build(cfg)

    search_file = Path(cfg["site_dir"]) / "search" / "search_index.json"
    assert not search_file.exists()


# ═══════════════════════════════════════════════════════════════
# Additional seams – event_priority ordering
# (protocol-handoff seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_plugin_collection_run_event_returns_item")
def test_event_priority_ordering_with_collection():
    """Seam: protocol handoff — event_priority ordering controls handler execution order."""
    """Higher-priority handlers must run first regardless of insertion order."""

    class LowPlugin(BasePlugin):
        def on_page_markdown(self, markdown, **kwargs):
            return markdown + " low"

    class HighPlugin(BasePlugin):
        @event_priority(100)
        def on_page_markdown(self, markdown, **kwargs):
            return markdown + " high"

    pc = PluginCollection()
    pc["low_first"] = LowPlugin()
    pc["high_second"] = HighPlugin()

    result = pc.run_event("page_markdown", item="start")
    assert result == "start high low"


# ═══════════════════════════════════════════════════════════════
# Additional seams – theme custom_dir override
# (state-consistency seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_theme_custom_dir_first_in_dirs")
def test_theme_custom_dir_overrides_packaged_template(tmp_path):
    """Seam: state consistency — theme custom_dir shadows packaged template."""
    """A template in custom_dir must shadow the packaged one."""
    custom = tmp_path / "overrides"
    custom.mkdir()
    (custom / "main.html").write_text(
        "<!-- custom main -->\n{% block content %}{% endblock %}", encoding="utf-8"
    )
    theme = Theme(name="mkdocs", custom_dir=str(custom))
    env = theme.get_env()
    tpl = env.get_template("main.html")
    source = tpl.render()
    assert "custom main" in source


# ═══════════════════════════════════════════════════════════════
# Additional seams – docs_dir/site_dir containment
# (error-propagation seam)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.depends_on("test_load_config_docs_site_containment_raises_abort")
def test_site_dir_inside_docs_dir_also_raises_abort(tmp_path):
    """Seam: error propagation — site_dir inside docs_dir triggers Abort."""
    """site_dir inside docs_dir must also trigger Abort."""
    docs = tmp_path / "content"
    docs.mkdir()
    (docs / "index.md").write_text("# X\n", encoding="utf-8")
    site = docs / "build"
    site.mkdir()

    cfg_path = tmp_path / "mkdocs.yml"
    cfg_path.write_text(
        f"site_name: {SITE_NAME}\ndocs_dir: content\nsite_dir: content/build\n",
        encoding="utf-8",
    )
    with pytest.raises(Abort):
        load_config(config_file=str(cfg_path))
