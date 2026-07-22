"""
Atomic-layer tests for mkdocs.

Each test verifies **one** public API entry's **one** behaviour.
Independent-solvability: if only the tested API is correctly implemented
(everything else is a stub), the test must pass.
"""

import os
import re
import pytest
from datetime import datetime, timezone
from pathlib import Path

from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.structure.pages import Page
from mkdocs.structure.nav import Section, Link
from mkdocs.structure.toc import AnchorLink, TableOfContents, get_toc
from mkdocs.exceptions import (
    MkDocsException,
    Abort,
    ConfigurationError,
    BuildError,
    PluginError,
)
from mkdocs.plugins import BasePlugin, PluginCollection, get_plugin_logger
from mkdocs.utils import (
    get_build_datetime,
    get_build_date,
    get_build_timestamp,
    copy_file,
    write_file,
    clean_directory,
    is_markdown_file,
    get_relative_url,
    normalize_url,
)
from mkdocs.commands.build import site_directory_contains_stale_files
from mkdocs.config import load_config
from mkdocs.theme import Theme

from conftest import make_file, create_project, load_cfg, SITE_NAME


# ═══════════════════════════════════════════════════════════════
# Source Files – File mapping
# ═══════════════════════════════════════════════════════════════


def test_file_src_uri_forward_slashes(tmp_path):
    """src_uri must always use forward slashes."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "guide").mkdir()
    (docs / "guide" / "intro.md").write_text("# Intro\n", encoding="utf-8")
    f = make_file("guide/intro.md", docs, site)
    assert f.src_uri == "guide/intro.md"
    assert "\\" not in f.src_uri


def test_file_dest_uri_directory_urls_enabled(tmp_path):
    """With directory URLs, a Markdown file maps to dir/index.html."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "tutorial.md").write_text("", encoding="utf-8")
    f = make_file("tutorial.md", docs, site, use_directory_urls=True)
    assert f.dest_uri == "tutorial/index.html"


def test_file_dest_uri_directory_urls_disabled(tmp_path):
    """Without directory URLs, a Markdown file maps to .html."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "tutorial.md").write_text("", encoding="utf-8")
    f = make_file("tutorial.md", docs, site, use_directory_urls=False)
    assert f.dest_uri == "tutorial.html"


def test_file_url_directory_urls_trailing_slash(tmp_path):
    """File.url for a Markdown page with dir URLs ends with '/'."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "faq.md").write_text("", encoding="utf-8")
    f = make_file("faq.md", docs, site, use_directory_urls=True)
    assert f.url == "faq/"


def test_file_index_maps_to_dot_slash_url(tmp_path):
    """Root index.md must map to index.html with URL './' (dir URLs on)."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "index.md").write_text("", encoding="utf-8")
    f = make_file("index.md", docs, site, use_directory_urls=True)
    assert f.dest_uri == "index.html"
    assert f.url == "./"


def test_file_non_markdown_keeps_original_dest(tmp_path):
    """Non-Markdown files keep their original dest_uri unchanged."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "logo.png").write_bytes(b"\x89PNG")
    f = make_file("logo.png", docs, site, use_directory_urls=True)
    assert f.dest_uri == "logo.png"
    assert f.url == "logo.png"


# ═══════════════════════════════════════════════════════════════
# Source Files – Classification
# ═══════════════════════════════════════════════════════════════


def test_file_is_documentation_page_for_md(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "notes.md").write_text("", encoding="utf-8")
    f = make_file("notes.md", docs, site)
    assert f.is_documentation_page() is True


def test_file_is_documentation_page_for_mdown(tmp_path):
    """All recognized Markdown extensions must classify as documentation."""
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "notes.mdown").write_text("", encoding="utf-8")
    f = make_file("notes.mdown", docs, site)
    assert f.is_documentation_page() is True


def test_file_is_media_file_for_png(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "banner.png").write_bytes(b"\x89PNG")
    f = make_file("banner.png", docs, site)
    assert f.is_media_file() is True
    assert f.is_documentation_page() is False


def test_file_is_css_for_stylesheet(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "custom.css").write_text("body{}", encoding="utf-8")
    f = make_file("custom.css", docs, site)
    assert f.is_css() is True


def test_file_is_javascript_for_script(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "app.js").write_text("// js", encoding="utf-8")
    f = make_file("app.js", docs, site)
    assert f.is_javascript() is True


# ═══════════════════════════════════════════════════════════════
# Source Files – Generated files
# ═══════════════════════════════════════════════════════════════


def test_file_generated_with_content_string(tmp_path):
    """File.generated with content creates a virtual doc page."""
    site = tmp_path / "s"
    site.mkdir()
    f = File.generated(str(site), "virtual/page.md", content="# Virtual\n")
    assert f.src_uri == "virtual/page.md"
    assert f.is_documentation_page() is True


def test_file_generated_no_args_raises_type_error(tmp_path):
    """Neither content nor abs_src_path → TypeError."""
    site = tmp_path / "s"
    site.mkdir()
    with pytest.raises(TypeError):
        File.generated(str(site), "nope.md")


def test_file_generated_both_args_raises_type_error(tmp_path):
    """Both content and abs_src_path → TypeError."""
    site = tmp_path / "s"
    site.mkdir()
    ext = tmp_path / "external.md"
    ext.write_text("ext", encoding="utf-8")
    with pytest.raises(TypeError):
        File.generated(str(site), "both.md", content="txt", abs_src_path=str(ext))


# ═══════════════════════════════════════════════════════════════
# Source Files – Content access
# ═══════════════════════════════════════════════════════════════


def test_file_content_string_reads_utf8(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "greet.md").write_text("Héllo wörld\n", encoding="utf-8")
    f = make_file("greet.md", docs, site)
    assert "Héllo wörld" in f.content_string


def test_file_content_bytes_reads_raw(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "data.bin").write_bytes(b"\xde\xad\xbe\xef")
    f = make_file("data.bin", docs, site)
    assert f.content_bytes == b"\xde\xad\xbe\xef"


# ═══════════════════════════════════════════════════════════════
# Source Files – Edit URI
# ═══════════════════════════════════════════════════════════════


def test_file_edit_uri_defaults_to_src_uri(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "article.md").write_text("", encoding="utf-8")
    f = make_file("article.md", docs, site)
    assert f.edit_uri == "article.md"


def test_file_edit_uri_none_for_generated(tmp_path):
    site = tmp_path / "s"
    site.mkdir()
    f = File.generated(str(site), "gen/report.md", content="# R\n")
    assert f.edit_uri is None


# ═══════════════════════════════════════════════════════════════
# Source Files – Files collection
# ═══════════════════════════════════════════════════════════════


def test_files_collection_length_and_iter(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    for name in ("a.md", "b.md"):
        (docs / name).write_text("", encoding="utf-8")
    f1 = make_file("a.md", docs, site)
    f2 = make_file("b.md", docs, site)
    fs = Files([f1, f2])
    assert len(fs) == 2
    uris = [f.src_uri for f in fs]
    assert "a.md" in uris and "b.md" in uris


def test_files_get_file_from_path_found(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "target.md").write_text("", encoding="utf-8")
    f = make_file("target.md", docs, site)
    fs = Files([f])
    assert fs.get_file_from_path("target.md") is f


def test_files_get_file_from_path_missing_returns_none(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "only.md").write_text("", encoding="utf-8")
    f = make_file("only.md", docs, site)
    fs = Files([f])
    assert fs.get_file_from_path("absent.md") is None


def test_files_remove_absent_raises_value_error(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "present.md").write_text("", encoding="utf-8")
    (docs / "other.md").write_text("", encoding="utf-8")
    f1 = make_file("present.md", docs, site)
    f2 = make_file("other.md", docs, site)
    fs = Files([f1])
    with pytest.raises(ValueError):
        fs.remove(f2)


def test_files_append_adds_file(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    for name in ("first.md", "second.md"):
        (docs / name).write_text("", encoding="utf-8")
    f1 = make_file("first.md", docs, site)
    f2 = make_file("second.md", docs, site)
    fs = Files([f1])
    fs.append(f2)
    assert len(fs) == 2
    assert fs.get_file_from_path("second.md") is f2


def test_files_documentation_pages_only_markdown(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    (docs / "page.md").write_text("", encoding="utf-8")
    (docs / "style.css").write_text("body{}", encoding="utf-8")
    f_md = make_file("page.md", docs, site)
    f_css = make_file("style.css", docs, site)
    fs = Files([f_md, f_css])
    doc_pages = list(fs.documentation_pages())
    assert len(doc_pages) == 1
    assert doc_pages[0].src_uri == "page.md"


def test_files_src_uris_property(tmp_path):
    docs, site = tmp_path / "d", tmp_path / "s"
    docs.mkdir()
    site.mkdir()
    for name in ("alpha.md", "beta.md"):
        (docs / name).write_text("", encoding="utf-8")
    f1 = make_file("alpha.md", docs, site)
    f2 = make_file("beta.md", docs, site)
    fs = Files([f1, f2])
    uris = fs.src_uris
    assert "alpha.md" in uris
    assert "beta.md" in uris


# ═══════════════════════════════════════════════════════════════
# Source Files – InclusionLevel
# ═══════════════════════════════════════════════════════════════


def test_inclusion_level_enum_members():
    assert hasattr(InclusionLevel, "EXCLUDED")
    assert hasattr(InclusionLevel, "DRAFT")
    assert hasattr(InclusionLevel, "NOT_IN_NAV")
    assert hasattr(InclusionLevel, "UNDEFINED")
    assert hasattr(InclusionLevel, "INCLUDED")
    assert InclusionLevel.EXCLUDED != InclusionLevel.INCLUDED


# ═══════════════════════════════════════════════════════════════
# Pages – read_source & metadata
# ═══════════════════════════════════════════════════════════════


def test_page_read_source_populates_markdown(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "# Welcome\n\nBody text here.\n", encoding="utf-8"
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    page.read_source(cfg)
    assert "Body text here." in page.markdown


def test_page_meta_from_yaml_front_matter(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "---\ntitle: Custom Heading\nauthor: Tester\n---\n# Fallback\n\nContent.\n",
        encoding="utf-8",
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    page.read_source(cfg)
    assert page.meta.get("author") == "Tester"


# ═══════════════════════════════════════════════════════════════
# Pages – title resolution
# ═══════════════════════════════════════════════════════════════


def test_page_title_from_nav_label(tmp_path):
    """Nav label has highest priority for title resolution."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "---\ntitle: Meta Title\n---\n# Heading Title\n", encoding="utf-8"
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title="Nav Override", file=f, config=cfg)
    page.read_source(cfg)
    assert page.title == "Nav Override"


def test_page_title_from_metadata(tmp_path):
    """Metadata title used when nav label is absent."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "---\ntitle: Metadata Title\n---\n\nNo heading here.\n", encoding="utf-8"
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    page.read_source(cfg)
    assert page.title == "Metadata Title"


# ═══════════════════════════════════════════════════════════════
# Pages – rendering
# ═══════════════════════════════════════════════════════════════


def test_page_render_produces_html_content(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "# Greeting\n\nHello **universe**.\n", encoding="utf-8"
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    page.read_source(cfg)
    page.render(cfg, Files([f]))
    assert "<strong>universe</strong>" in page.content


def test_page_render_before_read_raises_runtime_error(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text("# Placeholder\n", encoding="utf-8")
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    with pytest.raises(RuntimeError):
        page.render(cfg, Files([f]))


def test_page_toc_populated_after_render(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.md").write_text(
        "# Top Level\n\n## Second Level\n\nParagraph.\n", encoding="utf-8"
    )
    site = tmp_path / "s"
    site.mkdir()
    cfg = load_cfg(tmp_path)
    f = make_file("index.md", docs, site)
    page = Page(title=None, file=f, config=cfg)
    page.read_source(cfg)
    page.render(cfg, Files([f]))
    toc_items = list(page.toc)
    assert len(toc_items) >= 1


# ═══════════════════════════════════════════════════════════════
# Table of Contents
# ═══════════════════════════════════════════════════════════════


def test_anchor_link_url_is_hash_plus_id():
    link = AnchorLink(title="Overview", id="overview-section", level=2)
    assert link.url == "#overview-section"
    assert link.title == "Overview"
    assert link.id == "overview-section"
    assert link.level == 2


def test_table_of_contents_iterable_and_length():
    tokens = [
        {
            "level": 1,
            "id": "main-topic",
            "name": "Main Topic",
            "children": [
                {"level": 2, "id": "subtopic", "name": "Subtopic", "children": []},
            ],
        }
    ]
    toc = get_toc(tokens)
    items = list(toc)
    assert len(toc) >= 1
    assert items[0].id == "main-topic"
    assert len(items[0].children) == 1


# ═══════════════════════════════════════════════════════════════
# Navigation – Section & Link
# ═══════════════════════════════════════════════════════════════


def test_section_is_section_true():
    section = Section(title="User Guide", children=[])
    assert section.is_section is True
    assert section.is_page is False
    assert section.is_link is False
    assert isinstance(section.children, list)


def test_link_is_link_true_active_false():
    link = Link(title="Source Code", path="https://git.example.test/repo")
    assert link.is_link is True
    assert link.is_page is False
    assert link.is_section is False
    assert link.active is False
    assert link.children is None


# ═══════════════════════════════════════════════════════════════
# Themes
# ═══════════════════════════════════════════════════════════════


def test_theme_construction_with_builtin_name():
    theme = Theme(name="mkdocs")
    assert len(theme.dirs) >= 1


def test_theme_get_env_has_main_template():
    theme = Theme(name="mkdocs")
    env = theme.get_env()
    templates = env.list_templates()
    assert "main.html" in templates


def test_theme_custom_dir_first_in_dirs(tmp_path):
    """custom_dir must appear first in Theme.dirs."""
    custom = tmp_path / "my_overrides"
    custom.mkdir()
    theme = Theme(name="mkdocs", custom_dir=str(custom))
    assert Path(theme.dirs[0]) == custom


# ═══════════════════════════════════════════════════════════════
# Plugins
# ═══════════════════════════════════════════════════════════════


def test_plugin_collection_run_event_returns_item():
    """No handlers → item passes through unchanged."""
    pc = PluginCollection()
    result = pc.run_event("page_markdown", item="# Unchanged\n")
    assert result == "# Unchanged\n"


def test_get_plugin_logger_has_prefixed_name():
    logger = get_plugin_logger("alpha_plugin")
    assert "alpha_plugin" in logger.name


# ═══════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════


def test_abort_inherits_system_exit():
    assert issubclass(Abort, SystemExit)
    err = Abort("halt build")
    assert isinstance(err, SystemExit)
    assert "halt build" in str(err)


def test_abort_inherits_mkdocs_exception():
    assert issubclass(Abort, MkDocsException)
    err = Abort("config abort")
    assert isinstance(err, MkDocsException)
    assert "config abort" in str(err)


def test_configuration_error_is_exception():
    err = ConfigurationError("bad config")
    assert isinstance(err, Exception)
    assert "bad config" in str(err)


def test_build_error_is_exception():
    err = BuildError("build broke")
    assert isinstance(err, Exception)
    assert "build broke" in str(err)


def test_plugin_error_inherits_build_error():
    assert issubclass(PluginError, BuildError)
    err = PluginError("plugin issue")
    assert isinstance(err, BuildError)
    assert "plugin issue" in str(err)


# ═══════════════════════════════════════════════════════════════
# Config – Error Semantics
# ═══════════════════════════════════════════════════════════════


def test_load_config_missing_default_raises_configuration_error(tmp_path, monkeypatch):
    """No mkdocs.yml or mkdocs.yaml in cwd → ConfigurationError."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigurationError):
        load_config()


def test_load_config_yaml_parse_error_raises_configuration_error(tmp_path):
    cfg_path = tmp_path / "mkdocs.yml"
    cfg_path.write_text("{unclosed", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(config_file=str(cfg_path))


def test_load_config_missing_inherit_raises_configuration_error(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# X\n", encoding="utf-8")
    cfg_path = tmp_path / "mkdocs.yml"
    cfg_path.write_text(
        f"INHERIT: absent_parent.yml\nsite_name: {SITE_NAME}\n", encoding="utf-8"
    )
    with pytest.raises(ConfigurationError):
        load_config(config_file=str(cfg_path))


def test_load_config_invalid_theme_raises_abort(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# X\n", encoding="utf-8")
    cfg_path = tmp_path / "mkdocs.yml"
    cfg_path.write_text(
        f"site_name: {SITE_NAME}\ntheme:\n  name: nonexistent_theme_xyz\n",
        encoding="utf-8",
    )
    with pytest.raises(Abort):
        load_config(config_file=str(cfg_path))


def test_load_config_custom_dir_nonexistent_raises_abort(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# X\n", encoding="utf-8")
    cfg_path = tmp_path / "mkdocs.yml"
    cfg_path.write_text(
        f"site_name: {SITE_NAME}\ntheme:\n  name: mkdocs\n  custom_dir: ghost_dir\n",
        encoding="utf-8",
    )
    with pytest.raises(Abort):
        load_config(config_file=str(cfg_path))


def test_load_config_docs_site_containment_raises_abort(tmp_path):
    """docs_dir inside site_dir (or vice versa) must raise Abort."""
    nested = tmp_path / "output" / "pages"
    nested.mkdir(parents=True)
    (nested / "index.md").write_text("# X\n", encoding="utf-8")
    cfg_path = tmp_path / "mkdocs.yml"
    cfg_path.write_text(
        f"site_name: {SITE_NAME}\ndocs_dir: output/pages\nsite_dir: output\n",
        encoding="utf-8",
    )
    with pytest.raises(Abort):
        load_config(config_file=str(cfg_path))


# ═══════════════════════════════════════════════════════════════
# Config – features
# ═══════════════════════════════════════════════════════════════


def test_load_config_mapping_and_attribute_access(tmp_path):
    cfg = load_cfg(tmp_path)
    assert cfg["site_name"] == SITE_NAME


def test_load_config_default_markdown_extensions(tmp_path):
    """Default extensions must include toc, tables, fenced_code."""
    cfg = load_cfg(tmp_path)
    ext_strs = [str(e) for e in cfg["markdown_extensions"]]
    joined = " ".join(ext_strs)
    assert "toc" in joined
    assert "tables" in joined
    assert "fenced_code" in joined


def test_load_config_keyword_override_replaces_value(tmp_path):
    """Keyword overrides must replace file values (None ignored)."""
    create_project(tmp_path)
    cfg = load_config(
        config_file=str(tmp_path / "mkdocs.yml"),
        site_name="Override Name",
    )
    assert cfg["site_name"] == "Override Name"


# ═══════════════════════════════════════════════════════════════
# Utilities – date helpers
# ═══════════════════════════════════════════════════════════════


def test_get_build_datetime_aware_utc():
    dt = get_build_datetime()
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_get_build_date_format_yyyy_mm_dd():
    d = get_build_date()
    assert isinstance(d, str)
    assert re.match(r"\d{4}-\d{2}-\d{2}$", d)


def test_get_build_timestamp_numeric():
    ts = get_build_timestamp()
    assert isinstance(ts, (int, float))
    assert ts > 0


def test_get_build_datetime_source_date_epoch(monkeypatch):
    """SOURCE_DATE_EPOCH must override the build time."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    dt = get_build_datetime()
    assert int(dt.timestamp()) == 1700000000


# ═══════════════════════════════════════════════════════════════
# Utilities – file helpers
# ═══════════════════════════════════════════════════════════════


def test_copy_file_creates_parent_directories(tmp_path):
    src = tmp_path / "source.txt"
    src.write_text("sample content", encoding="utf-8")
    dest = str(tmp_path / "deep" / "nested" / "copy.txt")
    copy_file(str(src), dest)
    assert Path(dest).exists()
    assert Path(dest).read_text(encoding="utf-8") == "sample content"


def test_clean_directory_preserves_dot_entries(tmp_path):
    d = tmp_path / "target"
    d.mkdir()
    (d / "visible.txt").write_text("data", encoding="utf-8")
    (d / ".hidden").write_text("secret", encoding="utf-8")
    (d / "subdir").mkdir()
    (d / "subdir" / "nested.txt").write_text("nested", encoding="utf-8")

    clean_directory(str(d))

    assert d.exists()
    assert not (d / "visible.txt").exists()
    assert not (d / "subdir").exists()
    assert (d / ".hidden").exists()


# ═══════════════════════════════════════════════════════════════
# Utilities – URL helpers
# ═══════════════════════════════════════════════════════════════


def test_is_markdown_file_various_extensions():
    assert is_markdown_file("doc.md") is True
    assert is_markdown_file("doc.markdown") is True
    assert is_markdown_file("doc.mdown") is True
    assert is_markdown_file("doc.mkdn") is True
    assert is_markdown_file("doc.mkd") is True


def test_is_markdown_file_rejects_non_markdown():
    assert is_markdown_file("doc.txt") is False
    assert is_markdown_file("doc.html") is False
    assert is_markdown_file("doc.rst") is False


def test_get_relative_url_basic_computation():
    assert get_relative_url("alpha/beta/", ".") == "alpha/beta/"


def test_get_relative_url_traverses_up():
    result = get_relative_url(".", "sub/page/")
    assert result == "../../"


def test_normalize_url_leaves_absolute_unchanged():
    assert normalize_url("https://example.com/page") == "https://example.com/page"
    assert normalize_url("#fragment") == "#fragment"
    assert normalize_url("/abs/path") == "/abs/path"


# ═══════════════════════════════════════════════════════════════
# Utilities – site stale check
# ═══════════════════════════════════════════════════════════════


def test_site_stale_files_nonempty_true(tmp_path):
    d = tmp_path / "site"
    d.mkdir()
    (d / "index.html").write_text("<html></html>", encoding="utf-8")
    assert site_directory_contains_stale_files(str(d)) is True


def test_site_stale_files_empty_false(tmp_path):
    d = tmp_path / "empty_site"
    assert site_directory_contains_stale_files(str(d)) is False
    d.mkdir()
    assert site_directory_contains_stale_files(str(d)) is False
