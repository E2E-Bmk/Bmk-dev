# Spec2Repo oracle - integration tests for mkdocs-sitebuild-fullrepro-002
import subprocess

import sys

import textwrap

from pathlib import Path

import pytest

import mkdocs

from mkdocs.__main__ import cli

from mkdocs.commands.build import build

from mkdocs.config import load_config

from mkdocs.exceptions import Abort

from mkdocs.plugins import BasePlugin, PluginCollection

import json

import logging

import os

from mkdocs.commands.new import new

from mkdocs.config import config_options as c

from mkdocs.config.base import Config

from mkdocs.contrib.search import SearchPlugin

from mkdocs.contrib.search.search_index import SearchIndex

from mkdocs.exceptions import Abort, ConfigurationError

from mkdocs.plugins import BasePlugin, PluginCollection, event_priority

from mkdocs.structure.files import File, Files, InclusionLevel, get_files

from mkdocs.structure.nav import Link, Section, get_navigation

from mkdocs.structure.pages import Page

from mkdocs.structure.toc import AnchorLink, TableOfContents

from mkdocs.theme import Theme

from mkdocs.utils import (
    CountHandler,
    clean_directory,
    copy_file,
    create_media_urls,
    dirname_to_title,
    get_relative_url,
    is_error_template,
    is_markdown_file,
    normalize_url,
    reduce_list,
    write_file,
)

from mkdocs.utils.meta import get_data

from mkdocs.utils.templates import script_tag_filter, url_filter

from mkdocs.utils.yaml import yaml_load

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


def test_python_module_version_reports_installed_version():
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "mkdocs" in result.stdout.lower()
    assert mkdocs.__version__ in result.stdout


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
    assert (Path(config.site_dir) / "search" / "search_index.json").exists()


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


def test_plugin_lifecycle_events_run_during_build(tmp_path):
    events = []

    class Recorder(BasePlugin):
        def on_pre_build(self, *, config):
            events.append("pre_build")

        def on_post_build(self, *, config):
            events.append("post_build")

    config_file = write_project(tmp_path, "site_name: Plugins\n")
    config = load_config(config_file=str(config_file))
    plugins = PluginCollection()
    plugins["recorder"] = Recorder()
    config.plugins = plugins

    build(config)

    assert events == ["pre_build", "post_build"]


def test_plugin_build_error_hook_observes_build_failure(tmp_path):
    seen = []

    class FailingPlugin(BasePlugin):
        def on_pre_build(self, *, config):
            raise RuntimeError("boom")

        def on_build_error(self, *, error):
            seen.append(type(error).__name__)

    config_file = write_project(tmp_path, "site_name: Error Hook\n")
    config = load_config(config_file=str(config_file))
    plugins = PluginCollection()
    plugins["failing"] = FailingPlugin()
    config.plugins = plugins

    with pytest.raises(RuntimeError):
        build(config)
    assert seen == ["RuntimeError"]


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


def test_full_new_then_build_workflow(tmp_path):
    project = tmp_path / "project"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "new", str(project)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    build_result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-f", str(project / "mkdocs.yml"), "-d", str(project / "public")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert build_result.returncode == 0, build_result.stdout + build_result.stderr
    assert (project / "public" / "index.html").exists()


def test_new_creates_project_config_and_index(tmp_path):
    target = tmp_path / "site"
    new(str(target))

    assert (target / "mkdocs.yml").read_text(encoding="utf-8").strip() == "site_name: My Docs"
    assert "Welcome to MkDocs" in (target / "docs" / "index.md").read_text(encoding="utf-8")


def test_new_preserves_existing_config_and_index(tmp_path):
    target = tmp_path / "existing"
    (target / "docs").mkdir(parents=True)
    (target / "mkdocs.yml").write_text("site_name: Existing\n", encoding="utf-8")
    (target / "docs" / "index.md").write_text("# Existing", encoding="utf-8")

    new(str(target))

    assert (target / "mkdocs.yml").read_text(encoding="utf-8") == "site_name: Existing\n"
    assert (target / "docs" / "index.md").read_text(encoding="utf-8") == "# Existing"


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


def test_yaml_inherit_deep_merges_mappings_and_replaces_lists(tmp_path):
    parent = tmp_path / "parent.yml"
    child = tmp_path / "child.yml"
    parent.write_text("site_name: Parent\nextra:\n  a: 1\nnav:\n  - Home: index.md\n", encoding="utf-8")
    child.write_text("INHERIT: parent.yml\nextra:\n  b: 2\nnav:\n  - Guide: guide.md\n", encoding="utf-8")

    with child.open(encoding="utf-8") as handle:
        data = yaml_load(handle)

    assert data["site_name"] == "Parent"
    assert data["extra"] == {"a": 1, "b": 2}
    assert data["nav"] == [{"Guide": "guide.md"}]


def test_copy_static_files_copies_included_non_markdown(tmp_path):
    docs = tmp_path / "docs"
    site = tmp_path / "site"
    docs.mkdir()
    (docs / "asset.txt").write_text("asset", encoding="utf-8")
    asset = File("asset.txt", str(docs), str(site), True, inclusion=InclusionLevel.INCLUDED)

    Files([asset]).copy_static_files()

    assert (site / "asset.txt").read_text(encoding="utf-8") == "asset"


def test_get_files_prefers_index_over_readme(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Example\n",
        {"index.md": "# Home", "README.md": "# Readme", "guide.md": "# Guide"},
    )

    files = get_files(config)

    assert files.get_file_from_path("index.md") is not None
    assert files.get_file_from_path("README.md") is None
    assert files.get_file_from_path("guide.md") is not None


def test_page_render_rewrites_internal_markdown_links(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Example\nuse_directory_urls: false\n",
        {"index.md": "[Guide](guide.md#intro)", "guide.md": "# Intro"},
    )
    index = File("index.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    guide = File("guide.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    page = Page(None, index, config)

    page.read_source(config)
    page.render(config, Files([index, guide]))

    assert 'href="guide.html#intro"' in page.content


def test_navigation_builds_sections_links_and_pages(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Example\nnav:\n  - Home: index.md\n  - Guide:\n      - Intro: guide.md\n  - Project: https://example.com\n",
        {"index.md": "# Home", "guide.md": "# Guide"},
    )
    files = get_files(config)
    nav = get_navigation(files, config)

    assert len(nav.pages) == 2
    assert nav.homepage.title == "Home"
    assert isinstance(nav.items[1], Section)
    assert isinstance(nav.items[2], Link)
    assert nav.items[2].url == "https://example.com"


def test_pages_omitted_from_explicit_nav_still_get_page_objects(tmp_path):
    config = _loaded_config(
        tmp_path,
        "site_name: Example\nnav:\n  - Home: index.md\n",
        {"index.md": "# Home", "hidden.md": "# Hidden"},
    )
    files = get_files(config)
    nav = get_navigation(files, config)

    hidden = files.get_file_from_path("hidden.md")
    assert hidden.page is not None
    assert hidden.page not in nav.pages


def test_plugin_load_config_validates_schema():
    class DemoPlugin(BasePlugin):
        config_scheme = (("enabled", c.Type(bool, default=True)), ("label", c.Type(str, default="ok")))

    plugin = DemoPlugin()
    errors, warnings = plugin.load_config({"enabled": False})

    assert errors == []
    assert warnings == []
    assert plugin.config["enabled"] is False
    assert plugin.config["label"] == "ok"


def test_plugin_collection_runs_events_in_priority_order():
    calls = []

    class FirstPlugin(BasePlugin):
        @event_priority(50)
        def on_nav(self, nav, *, config, files):
            calls.append("first")
            return nav + ["first"]

    class SecondPlugin(BasePlugin):
        def on_nav(self, nav, *, config, files):
            calls.append("second")
            return nav + ["second"]

    collection = PluginCollection()
    collection["second"] = SecondPlugin()
    collection["first"] = FirstPlugin()

    result = collection.run_event("nav", [], config=None, files=None)

    assert calls == ["first", "second"]
    assert result == ["first", "second"]


def test_search_index_serializes_page_and_section_entries(tmp_path):
    config = _loaded_config(tmp_path)
    file = File("index.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    page = Page("Home", file, config)
    page.content = '<h1 id="intro">Intro</h1><p>Welcome</p>'
    page.toc = TableOfContents([AnchorLink("Intro", "intro", 1)])
    index = SearchIndex(lang=["en"], separator=r"[\s\-]+", min_search_length=3, prebuild_index=False, indexing="full")

    index.add_entry_from_context(page)
    payload = json.loads(index.generate_search_index())

    assert payload["config"]["lang"] == ["en"]
    assert payload["docs"][0]["title"] == "Home"
    assert payload["docs"][1]["location"] == "#intro"
    assert payload["docs"][1]["text"] == "Welcome"


def test_search_index_titles_mode_omits_section_entries(tmp_path):
    config = _loaded_config(tmp_path)
    file = File("index.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    page = Page("Home", file, config)
    page.content = '<h1 id="intro">Intro</h1><p>Welcome</p>'
    page.toc = TableOfContents([AnchorLink("Intro", "intro", 1)])
    index = SearchIndex(lang=["en"], separator=r"[\s\-]+", min_search_length=3, prebuild_index=False, indexing="titles")

    index.add_entry_from_context(page)
    payload = json.loads(index.generate_search_index())

    assert len(payload["docs"]) == 1
    assert payload["docs"][0]["text"] == ""
