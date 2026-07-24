# Spec2Repo oracle - integration tests for mkdocs-sitebuild-fullrepro-002
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from mkdocs.commands.build import build, site_directory_contains_stale_files
from mkdocs.config import load_config
from mkdocs.exceptions import Abort, ConfigurationError
from mkdocs.plugins import BasePlugin, PluginCollection, event_priority
from mkdocs.structure.files import File, Files, InclusionLevel, get_files
from mkdocs.structure.nav import Link, Section, get_navigation
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import get_toc
from mkdocs.theme import Theme
from mkdocs.utils import clean_directory, get_build_datetime, get_relative_url, normalize_url

def write_project(tmp_path, config_text="site_name: Example\n", pages=None):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, content in (pages or {"index.md": "# Home"}).items():
        path = docs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    config = tmp_path / "mkdocs.yml"
    config.write_text(textwrap.dedent(config_text).lstrip(), encoding="utf-8")
    return config


def _project(tmp_path, config_text="site_name: Example\n", pages=None):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for name, content in (pages or {"index.md": "# Home"}).items():
        path = docs_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path


def _loaded_config(tmp_path, config_text="site_name: Example\n", pages=None):
    return load_config(config_file=str(_project(tmp_path, config_text, pages)))


def test_project_config_defaults_include_site_and_theme(tmp_path):
    config_file = write_project(tmp_path, "site_name: Defaults\n")

    config = load_config(config_file=str(config_file))

    assert config.site_name == "Defaults"
    assert Path(config.docs_dir).name == "docs"
    assert Path(config.site_dir).name == "site"
    assert config.theme.name == "mkdocs"
    assert "search" in config.plugins


def test_build_api_writes_site_pages_and_search_assets(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Build API
        nav:
          - Home: index.md
          - Guide: guide.md
        """,
        {"index.md": "# Home\nWelcome", "guide.md": "# Guide\nContent"},
    )
    config = load_config(config_file=str(config_file))

    build(config)

    assert (Path(config.site_dir) / "index.html").exists()
    assert (Path(config.site_dir) / "guide" / "index.html").exists()
    search_path = Path(config.site_dir) / "search" / "search_index.json"
    payload = json.loads(search_path.read_text(encoding="utf-8"))
    assert any(doc["title"] == "Home" and "Welcome" in doc["text"] for doc in payload["docs"])
    assert any(doc["title"] == "Guide" and "Content" in doc["text"] for doc in payload["docs"])


def test_build_site_dir_override_keeps_config_and_output_consistent(tmp_path):
    config_file = write_project(tmp_path, "site_name: Override\n", {"index.md": "# Home"})
    custom_site = tmp_path / "published"
    config = load_config(config_file=str(config_file), site_dir=str(custom_site))

    build(config)

    assert Path(config.site_dir) == custom_site
    assert (custom_site / "index.html").exists()
    assert not (tmp_path / "site" / "index.html").exists()


def test_strict_build_aborts_on_warning(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Strict
        nav:
          - Missing: missing.md
        """,
        {"index.md": "# Home"},
    )
    config = load_config(config_file=str(config_file), strict=True)

    with pytest.raises(Abort):
        build(config)


def test_repo_url_and_site_url_shape_page_edit_links(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Links
        site_url: https://example.com/docs/
        repo_url: https://github.com/example/project
        edit_uri: edit/main/docs/
        """,
        {"index.md": "# Home"},
    )
    config = load_config(config_file=str(config_file))

    build(config)
    html = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")

    assert "https://example.com/docs/" in html
    assert "https://github.com/example/project" in html
    assert "edit/main/docs/index.md" in html


def test_custom_theme_directory_overrides_main_template(tmp_path):
    theme_dir = tmp_path / "theme"
    theme_dir.mkdir()
    (theme_dir / "main.html").write_text("CUSTOM {{ page.title }}", encoding="utf-8")
    config_file = write_project(
        tmp_path,
        f"""
        site_name: Custom Theme
        theme:
          name: mkdocs
          custom_dir: {theme_dir.as_posix()}
        """,
        {"index.md": "# Custom Page"},
    )
    config = load_config(config_file=str(config_file))

    build(config)

    assert (Path(config.site_dir) / "index.html").read_text(encoding="utf-8") == "CUSTOM Custom Page"


def test_load_config_applies_keyword_overrides(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: File Name\nsite_dir: configured_site\nuse_directory_urls: true\n",
        pages={"index.md": "# Home"},
    )
    overridden = load_config(config_file=config.config_file_path, site_name="Override", use_directory_urls=False)

    assert overridden.site_name == "Override"
    assert overridden.use_directory_urls is False
    assert Path(overridden.site_dir).name == "configured_site"


def test_load_config_discovers_mkdocs_yml_before_yaml(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Home", encoding="utf-8")
    (tmp_path / "mkdocs.yml").write_text("site_name: Preferred\n", encoding="utf-8")
    (tmp_path / "mkdocs.yaml").write_text("site_name: Secondary\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.site_name == "Preferred"


def test_load_config_missing_default_file_raises_configuration_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigurationError):
        load_config()


def test_get_files_prefers_index_over_readme(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Example\n",
        {"index.md": "# Home", "README.md": "# Readme", "guide.md": "# Guide"},
    )

    build(config)

    homepage = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")
    assert "Home" in homepage
    assert "Readme" not in homepage
    assert (Path(config.site_dir) / "guide" / "index.html").exists()


def test_build_copies_non_markdown_media_to_matching_site_path(tmp_path):
    config_file = write_project(
        tmp_path,
        "site_name: Media\n",
        {"index.md": "# Home", "assets/data.txt": "payload"},
    )
    config = load_config(config_file=str(config_file))

    build(config)

    assert (Path(config.site_dir) / "assets" / "data.txt").read_text(encoding="utf-8") == "payload"


def test_build_copies_and_links_configured_extra_css(tmp_path):
    config_file = write_project(
        tmp_path,
        "site_name: Styles\nextra_css:\n  - styles.css\n",
        {"index.md": "# Home", "styles.css": "body { color: red; }"},
    )
    config = load_config(config_file=str(config_file))

    build(config)
    site = Path(config.site_dir)
    html = (site / "index.html").read_text(encoding="utf-8")

    assert (site / "styles.css").read_text(encoding="utf-8") == "body { color: red; }"
    assert "styles.css" in html


def test_build_rewrites_internal_markdown_link_to_page_url(tmp_path):
    config_file = write_project(
        tmp_path,
        "site_name: Links\n",
        {"index.md": "# Home\n\n[Guide](guide.md)", "guide.md": "# Guide"},
    )
    config = load_config(config_file=str(config_file))

    build(config)
    html = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")

    assert 'href="guide/"' in html


def test_explicit_navigation_labels_are_visible_in_built_pages(tmp_path):
    config_file = write_project(
        tmp_path,
        "site_name: Navigation\nnav:\n  - Start Here: index.md\n  - User Guide: guide.md\n",
        {"index.md": "# Home", "guide.md": "# Guide"},
    )
    config = load_config(config_file=str(config_file))

    build(config)
    html = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")

    assert "Start Here" in html
    assert "User Guide" in html


def test_plugin_pre_and_post_build_events_share_one_build_lifecycle(tmp_path):
    events = []

    class ProbePlugin(BasePlugin):
        def on_pre_build(self, *, config):
            events.append(("pre", config.site_name))

        def on_post_build(self, *, config):
            events.append(("post", config.site_name))

    config_file = write_project(tmp_path, "site_name: Plugin Flow\n")
    config = load_config(config_file=str(config_file))
    config.plugins["probe"] = ProbePlugin()

    build(config)

    assert events == [("pre", "Plugin Flow"), ("post", "Plugin Flow")]


def test_build_clean_removes_stale_output_before_writing_site(tmp_path):
    config = _loaded_config(tmp_path)
    stale = Path(config.site_dir) / "stale.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("old", encoding="utf-8")
    assert site_directory_contains_stale_files(Path(config.site_dir)) is True
    build(config, dirty=False)
    assert not stale.exists()
    assert (Path(config.site_dir) / "index.html").exists()


def test_build_dirty_preserves_existing_output_while_updating_pages(tmp_path):
    config = _loaded_config(tmp_path, pages={"index.md": "# Home"})
    build(config)
    stale = Path(config.site_dir) / "keep.txt"
    stale.write_text("keep", encoding="utf-8")
    (Path(config.docs_dir) / "index.md").write_text("# Updated", encoding="utf-8")
    build(config, dirty=True)
    assert stale.read_text(encoding="utf-8") == "keep"
    assert (Path(config.site_dir) / "index.html").exists()


def test_generated_file_content_views_share_one_replaceable_value(tmp_path):
    observed = {}

    class GeneratedFilePlugin(BasePlugin):
        def on_files(self, files, *, config):
            file = File.generated(config, "virtual/info.txt", content="hello", inclusion=InclusionLevel.INCLUDED)
            observed["initial"] = (file.content_string, file.content_bytes, file.generated_by)
            file.content_bytes = b"updated"
            observed["updated"] = (file.content_string, file.abs_src_path)
            files.append(file)
            return files

    config = _loaded_config(tmp_path)
    config.plugins["generator"] = GeneratedFilePlugin()
    build(config)
    assert observed["initial"] == ("hello", b"hello", "generator")
    assert observed["updated"] == ("updated", None)
    assert (Path(config.site_dir) / "virtual" / "info.txt").read_bytes() == b"updated"


def test_files_collection_lookup_replace_remove_and_filters(tmp_path):
    docs, site = str(tmp_path / "docs"), str(tmp_path / "site")
    page = File("index.md", docs, site, True)
    media = File("asset.bin", docs, site, True)
    files = Files([page, media])
    assert files.get_file_from_path("index.md") is page
    assert list(files.documentation_pages()) == [page]
    assert list(files.media_files()) == [media]
    files.remove(media)
    assert set(files.src_uris) == {"index.md"}
    with pytest.raises(ValueError):
        files.remove(media)


def test_page_reads_front_matter_and_renders_title_toc_and_links(tmp_path):
    config = _loaded_config(
        tmp_path,
        pages={"index.md": "---\ntitle: Metadata Title\nkind: guide\n---\n# Heading\n\n[Part](#part)\n\n## Part"},
    )
    file = File("index.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    files = Files([file])
    page = Page(None, file, config)
    page.read_source(config)
    page.render(config, files)
    assert page.meta == {"title": "Metadata Title", "kind": "guide"}
    assert page.title == "Metadata Title"
    assert "<h2 id=\"part\">" in page.content
    assert [item.id for item in page.toc] == ["heading"]


def test_page_title_falls_back_to_heading_then_filename(tmp_path):
    config = _loaded_config(tmp_path, pages={"guide-page.md": "# Rendered Heading"})
    file = File("guide-page.md", config.docs_dir, config.site_dir, True)
    page = Page(None, file, config)
    page.read_source(config)
    assert page.title == "Rendered Heading"
    no_heading = File.generated(config, "fallback-name.md", content="plain body")
    fallback = Page(None, no_heading, config)
    fallback.read_source(config)
    assert fallback.title == "Fallback name"


def test_navigation_builds_sections_links_pages_and_sequence(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Nav\nnav:\n  - Home: index.md\n  - Guide:\n      - Start: guide.md\n  - External: https://example.com\n",
        {"index.md": "# Home", "guide.md": "# Guide"},
    )
    files = get_files(config)
    nav = get_navigation(files, config)
    assert [page.title for page in nav.pages] == ["Home", "Start"]
    assert isinstance(nav.items[1], Section)
    assert isinstance(nav.items[2], Link)
    assert nav.pages[0].next_page is nav.pages[1]
    assert nav.pages[1].previous_page is nav.pages[0]


def test_omitted_page_is_built_but_absent_from_navigation_pages(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Nav\nnav:\n  - Home: index.md\n",
        {"index.md": "# Home", "extra.md": "# Extra"},
    )
    files = get_files(config)
    nav = get_navigation(files, config)
    assert [page.file.src_uri for page in nav.pages] == ["index.md"]
    assert files.get_file_from_path("extra.md").page is not None
    build(config)
    assert (Path(config.site_dir) / "extra" / "index.html").exists()


def test_section_active_state_propagates_from_child_page(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Active\nnav:\n  - Docs:\n      - Home: index.md\n",
    )
    nav = get_navigation(get_files(config), config)
    section = nav.items[0]
    nav.pages[0].active = True
    assert section.active is True
    assert section.is_section is True


def test_plugin_collection_applies_event_priority_and_replacements():
    events = []

    class Early(BasePlugin):
        @event_priority(10)
        def on_page_markdown(self, markdown, **kwargs):
            events.append("early")
            return markdown + " early"

    class Late(BasePlugin):
        @event_priority(-10)
        def on_page_markdown(self, markdown, **kwargs):
            events.append("late")
            return markdown + " late"

    plugins = PluginCollection()
    plugins["late"] = Late()
    plugins["early"] = Early()
    result = plugins.run_event("page_markdown", "start", page=None, config=None, files=None)
    assert events == ["early", "late"]
    assert result == "start early late"


def test_plugin_none_keeps_value_and_string_replaces_page_markdown(tmp_path):
    class ReplacePlugin(BasePlugin):
        def on_config(self, config):
            return None

        def on_page_markdown(self, markdown, **kwargs):
            return markdown + "\n\nPlugin sentence."

    config = _loaded_config(tmp_path)
    config.plugins["replace"] = ReplacePlugin()
    build(config)
    html = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")
    assert "Plugin sentence." in html


def test_search_index_contains_rendered_page_title_location_and_text(tmp_path):
    config = _loaded_config(tmp_path, pages={"guide.md": "# Guide\nUnique searchable sentence"})
    build(config)
    payload = json.loads((Path(config.site_dir) / "search" / "search_index.json").read_text(encoding="utf-8"))
    item = next(doc for doc in payload["docs"] if doc["title"] == "Guide")
    assert item["location"] == "guide/"
    assert "Unique searchable sentence" in item["text"]


def test_replacing_default_plugins_removes_search_output(tmp_path):
    config = _loaded_config(tmp_path, "site_name: No Search\nplugins: []\n")
    build(config)
    assert not (Path(config.site_dir) / "search" / "search_index.json").exists()


def test_search_titles_indexing_omits_body_text(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Titles\nplugins:\n  - search:\n      indexing: titles\n",
        {"index.md": "# Home\nSecret body phrase\n\n## Section Name"},
    )
    build(config)
    payload = json.loads((Path(config.site_dir) / "search" / "search_index.json").read_text(encoding="utf-8"))
    combined = " ".join(doc.get("text", "") for doc in payload["docs"])
    assert "Secret body phrase" not in combined
    assert any(doc["title"] in {"Home", "Section Name"} for doc in payload["docs"])


def test_directory_url_file_page_link_and_output_views_agree(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: URLs\nuse_directory_urls: true\n",
        {"index.md": "# Home\n[Guide](guide.md)", "guide.md": "# Guide"},
    )
    files = get_files(config)
    nav = get_navigation(files, config)
    guide = files.get_file_from_path("guide.md")
    assert guide.url == "guide/"
    assert next(page for page in nav.pages if page.file is guide).url == "guide/"
    build(config)
    assert 'href="guide/"' in (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")
    assert (Path(config.site_dir) / "guide" / "index.html").exists()


def test_nav_page_template_and_search_share_explicit_title(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Titles\nnav:\n  - Public Guide: guide.md\n",
        {"guide.md": "---\ntitle: Metadata Guide\n---\n# Heading Guide"},
    )
    build(config)
    html = (Path(config.site_dir) / "guide" / "index.html").read_text(encoding="utf-8")
    search = json.loads((Path(config.site_dir) / "search" / "search_index.json").read_text(encoding="utf-8"))
    assert "Public Guide" in html
    assert any(doc["title"] == "Public Guide" for doc in search["docs"])


def test_plugin_replacement_is_shared_by_page_output_and_search(tmp_path):
    class ReplacePlugin(BasePlugin):
        def on_page_markdown(self, markdown, **kwargs):
            return markdown + "\n\nShared plugin phrase"

    config = _loaded_config(tmp_path)
    config.plugins["replace"] = ReplacePlugin()
    build(config)
    html = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")
    search = (Path(config.site_dir) / "search" / "search_index.json").read_text(encoding="utf-8")
    assert "Shared plugin phrase" in html
    assert "Shared plugin phrase" in search


def test_module_help_and_version_are_successful():
    help_result = subprocess.run([sys.executable, "-m", "mkdocs", "--help"], text=True, capture_output=True)
    version_result = subprocess.run([sys.executable, "-m", "mkdocs", "--version"], text=True, capture_output=True)
    assert help_result.returncode == version_result.returncode == 0
    assert "build" in help_result.stdout and "mkdocs" in version_result.stdout.lower()


def test_new_command_creates_project_without_overwriting_existing_page(tmp_path):
    project = tmp_path / "project"
    result = subprocess.run([sys.executable, "-m", "mkdocs", "new", str(project)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "site_name: My Docs" in (project / "mkdocs.yml").read_text(encoding="utf-8")
    page = project / "docs" / "index.md"
    page.write_text("custom", encoding="utf-8")
    second = subprocess.run([sys.executable, "-m", "mkdocs", "new", str(project)], text=True, capture_output=True)
    assert second.returncode == 0
    assert page.read_text(encoding="utf-8") == "custom"


def test_build_command_site_dir_override_writes_requested_output(tmp_path):
    write_project(tmp_path)
    output = tmp_path / "published"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--site-dir", str(output)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert (output / "index.html").exists()


def test_representative_new_then_build_workflow(tmp_path):
    project = tmp_path / "site-project"
    created = subprocess.run([sys.executable, "-m", "mkdocs", "new", str(project)], text=True, capture_output=True)
    built = subprocess.run([sys.executable, "-m", "mkdocs", "build"], cwd=project, text=True, capture_output=True)
    assert created.returncode == built.returncode == 0
    assert (project / "site" / "index.html").exists()
    assert (project / "site" / "search" / "search_index.json").exists()


def test_representative_navigation_theme_and_search_workflow(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Complete\nnav:\n  - Home: index.md\n  - Guide: guide.md\ntheme:\n  name: readthedocs\nplugins:\n  - search:\n      indexing: sections\n",
        {"index.md": "# Home", "guide.md": "# Guide\nSearchable content"},
    )
    build(config)
    site = Path(config.site_dir)
    assert (site / "index.html").exists() and (site / "guide" / "index.html").exists()
    search = json.loads((site / "search" / "search_index.json").read_text(encoding="utf-8"))
    assert any(item["title"] == "Guide" for item in search["docs"])


def test_representative_plugin_build_and_output_workflow(tmp_path):
    events = []

    class WorkflowPlugin(BasePlugin):
        def on_pre_build(self, **kwargs):
            events.append("pre")

        def on_page_markdown(self, markdown, **kwargs):
            return markdown + "\n\nWorkflow plugin output"

        def on_post_build(self, **kwargs):
            events.append("post")

    config = _loaded_config(tmp_path)
    config.plugins["workflow"] = WorkflowPlugin()
    build(config)
    assert events == ["pre", "post"]
    assert "Workflow plugin output" in (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")


