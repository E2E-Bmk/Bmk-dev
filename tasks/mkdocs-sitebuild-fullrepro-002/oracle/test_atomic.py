# Spec2Repo oracle - atomic tests for mkdocs-sitebuild-fullrepro-002
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


def test_public_package_exposes_version_and_cli_group():
    assert isinstance(mkdocs.__version__, str)
    assert mkdocs.__version__
    assert cli.name == "cli"
    assert "build" in cli.commands
    assert "serve" in cli.commands
    assert "new" in cli.commands


def test_load_config_rejects_missing_docs_dir(tmp_path):
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Missing Docs\n", encoding="utf-8")

    with pytest.raises(Abort):
        load_config(config_file=str(config))


def test_validation_rejects_unknown_theme_name(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Bad Theme
        theme:
          name: definitely-not-a-theme
        """,
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_file))


def test_unknown_config_key_is_warning_and_strict_aborts(tmp_path):
    config_path = _project(tmp_path, "site_name: Example\nunexpected_key: value\n")

    assert load_config(config_file=str(config_path)).site_name == "Example"
    with pytest.raises(Abort):
        load_config(config_file=str(config_path), strict=True)


def test_yaml_env_tag_uses_environment_and_default(monkeypatch):
    monkeypatch.setenv("DOCS_ENV_NAME", "Configured")
    data = yaml_load("name: !ENV DOCS_ENV_NAME\nfallback: !ENV [MISSING_NAME, default-value]\n")

    assert data == {"name": "Configured", "fallback": "default-value"}


def test_docs_dir_and_site_dir_may_not_contain_each_other(tmp_path):
    config_path = _project(tmp_path, "site_name: Example\ndocs_dir: docs\nsite_dir: docs/site\n")

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_config_mapping_and_attribute_access_round_trip():
    class DemoConfig(Config):
        title = c.Type(str)
        enabled = c.Type(bool, default=True)

    conf = DemoConfig()
    conf.load_dict({"title": "Docs"})
    errors, warnings = conf.validate()

    assert errors == []
    assert warnings == []
    assert conf["title"] == "Docs"
    assert conf.title == "Docs"
    assert conf.enabled is True


def test_config_options_validate_choice_list_and_optional():
    choice = c.Choice(("warn", "info"), default="warn")
    items = c.ListOfItems(c.Type(str), default=[])
    optional = c.Optional(c.Type(int))

    assert choice.validate("info") == "info"
    assert items.validate(["a", "b"]) == ["a", "b"]
    assert optional.validate(None) is None
    with pytest.raises(c.ValidationError):
        choice.validate("debug")


def test_file_directory_url_mapping(tmp_path):
    docs = tmp_path / "docs"
    site = tmp_path / "site"
    docs.mkdir()
    file = File("guide/intro.md", str(docs), str(site), True)

    assert file.src_uri == "guide/intro.md"
    assert file.dest_uri == "guide/intro/index.html"
    assert file.url == "guide/intro/"
    assert file.is_documentation_page()


def test_file_no_directory_url_mapping(tmp_path):
    docs = tmp_path / "docs"
    site = tmp_path / "site"
    docs.mkdir()
    file = File("guide/intro.md", str(docs), str(site), False)

    assert file.dest_uri == "guide/intro.html"
    assert file.url == "guide/intro.html"


def test_file_generated_content_and_edit_uri(tmp_path):
    config = _loaded_config(tmp_path)
    generated = []

    class GeneratorPlugin(BasePlugin):
        def on_files(self, files, *, config):
            file = File.generated(config, "generated.txt", content="hello")
            generated.append(file)
            files.append(file)
            return files

    collection = PluginCollection()
    collection["generator"] = GeneratorPlugin()
    config.plugins = collection

    files = collection.run_event("files", Files([]), config=config)
    file = generated[0]

    assert files.get_file_from_path("generated.txt") is file
    assert file.content_string == "hello"
    assert file.content_bytes == b"hello"
    assert file.edit_uri is None
    file.content_bytes = b"changed"
    assert file.content_string == "changed"


def test_file_generated_requires_exactly_one_source(tmp_path):
    config = _loaded_config(tmp_path)

    with pytest.raises(TypeError):
        File.generated(config, "bad.txt")
    with pytest.raises(TypeError):
        File.generated(config, "bad.txt", content="x", abs_src_path=str(tmp_path / "x.txt"))


def test_files_collection_replaces_filters_and_removes(tmp_path):
    docs = tmp_path / "docs"
    site = tmp_path / "site"
    docs.mkdir()
    page = File("index.md", str(docs), str(site), True)
    asset = File("assets/app.js", str(docs), str(site), True)
    files = Files([page])
    files.append(asset)

    assert len(files) == 2
    assert files.get_file_from_path("index.md") is page
    assert files.documentation_pages() == [page]
    assert files.javascript_files() == [asset]
    files.remove(asset)
    assert len(files) == 1
    with pytest.raises(ValueError):
        files.remove(asset)


def test_page_title_from_metadata_outranks_heading(tmp_path):
    config = _loaded_config(tmp_path, pages={"index.md": "---\ntitle: Meta Title\n---\n# Heading"})
    file = File("index.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    page = Page(None, file, config)

    page.read_source(config)
    page.render(config, Files([file]))

    assert page.title == "Meta Title"


def test_page_title_from_heading_and_filename_fallback(tmp_path):
    config = _loaded_config(tmp_path, pages={"guide.md": "# Rendered Heading", "api-reference.md": "Body"})
    heading_file = File("guide.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    heading_page = Page(None, heading_file, config)
    heading_page.read_source(config)
    heading_page.render(config, Files([heading_file]))

    fallback_file = File("api-reference.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    fallback_page = Page(None, fallback_file, config)
    fallback_page.read_source(config)

    assert heading_page.title == "Rendered Heading"
    assert fallback_page.title == "Api reference"


def test_theme_mapping_and_custom_dir_precedence(tmp_path):
    custom_dir = tmp_path / "theme"
    custom_dir.mkdir()
    (custom_dir / "main.html").write_text("custom", encoding="utf-8")
    theme = Theme(name=None, custom_dir=str(custom_dir), static_templates=["extra.html"], color="blue")

    assert theme["color"] == "blue"
    assert str(custom_dir) == theme.dirs[0]
    assert "extra.html" in theme.static_templates


def test_template_filters_normalize_urls_and_scripts(tmp_path):
    config = _loaded_config(tmp_path, pages={"guide/index.md": "# Guide"})
    file = File("guide/index.md", config.docs_dir, config.site_dir, config.use_directory_urls)
    page = Page("Guide", file, config)
    context = {"page": page, "base_url": ""}

    assert url_filter(context, "assets/app.css") == "../assets/app.css"
    assert url_filter(context, "https://example.com/app.css") == "https://example.com/app.css"
    assert script_tag_filter(context, c.ExtraScript().validate("app.mjs")) == '<script src="../app.mjs" type="module"></script>'
    assert script_tag_filter(context, c.ExtraScript().validate({"path": "app.js", "defer": True})) == '<script src="../app.js" defer></script>'


def test_plugin_event_returning_none_preserves_current_value():
    class PreservePlugin(BasePlugin):
        def on_nav(self, nav, *, config, files):
            return None

    collection = PluginCollection()
    collection["preserve"] = PreservePlugin()

    nav = ["current"]
    assert collection.run_event("nav", nav, config=None, files=None) == nav


def test_search_plugin_config_defaults_and_overrides():
    plugin = SearchPlugin()
    errors, warnings = plugin.load_config({"indexing": "titles", "min_search_length": 2})

    assert errors == []
    assert warnings == []
    assert plugin.config["indexing"] == "titles"
    assert plugin.config["min_search_length"] == 2
    assert plugin.config["separator"]


def test_url_helpers_preserve_external_urls_and_normalize_relative_paths(tmp_path):
    config = _loaded_config(tmp_path, pages={"guide/page.md": "# Guide"})
    page = Page("Guide", File("guide/page.md", config.docs_dir, config.site_dir, True), config)

    assert get_relative_url("assets/app.css", "guide/page/index.html") == "../../assets/app.css"
    assert normalize_url("assets/app.css", page=page) == "../../assets/app.css"
    assert normalize_url("https://example.com/app.css", page=page) == "https://example.com/app.css"
    assert create_media_urls(["assets/app.css", "https://example.com/app.css"], page=page)[0] == "../../assets/app.css"


def test_file_and_path_utility_helpers(tmp_path):
    source = tmp_path / "source.txt"
    destination = tmp_path / "nested" / "copied.txt"
    source.write_text("hello", encoding="utf-8")

    copy_file(str(source), str(destination))
    write_file(b"bytes", str(tmp_path / "nested" / "bytes.bin"))

    assert destination.read_text(encoding="utf-8") == "hello"
    assert (tmp_path / "nested" / "bytes.bin").read_bytes() == b"bytes"
    assert is_markdown_file("guide.md")
    assert is_error_template("404.html")
    assert dirname_to_title("api-reference") == "Api reference"
    assert reduce_list(["toc", "tables", "toc"]) == ["toc", "tables"]


def test_clean_directory_preserves_hidden_entries(tmp_path):
    target = tmp_path / "site"
    target.mkdir()
    (target / ".keep").write_text("hidden", encoding="utf-8")
    (target / "old.txt").write_text("old", encoding="utf-8")

    clean_directory(str(target))

    assert (target / ".keep").exists()
    assert not (target / "old.txt").exists()


def test_meta_parser_extracts_yaml_and_multimarkdown_metadata():
    yaml_doc = "---\ntitle: YAML Title\n---\n# Body"
    markdown, meta = get_data(yaml_doc)
    assert markdown.strip() == "# Body"
    assert meta["title"] == "YAML Title"

    mm_doc = "Title: Multi\nAuthor: Example\n\n# Body"
    markdown, meta = get_data(mm_doc)
    assert markdown.strip() == "# Body"
    assert meta == {"title": "Multi", "author": "Example"}


def test_count_handler_counts_records_by_level():
    logger = logging.getLogger("mkdocs.tests.rewritten.counts")
    handler = CountHandler()
    logger.addHandler(handler)
    try:
        logger.warning("one")
        logger.error("two")
        logger.error("three")
    finally:
        logger.removeHandler(handler)

    assert handler.get_counts() == [("ERROR", 2), ("WARNING", 1)]


def test_build_date_helpers_use_source_date_epoch(monkeypatch):
    from mkdocs.utils import get_build_date, get_build_datetime, get_build_timestamp

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")

    assert get_build_date() == "1970-01-01"
    assert get_build_datetime().tzinfo is not None
    assert get_build_timestamp() == 0
