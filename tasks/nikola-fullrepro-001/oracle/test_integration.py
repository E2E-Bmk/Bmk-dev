# Spec2Repo oracle - integration and system_e2e tests for nikola-fullrepro-001

# Spec2Repo oracle - generated tests for nikola-fullrepro-001

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _ok(result):
    assert result in (0, None)


def _failed(result):
    assert result not in (0, None)


def _base_translation_config(pattern="{path}.{lang}.{ext}"):
    return {
        "TRANSLATIONS": {"en": "", "es": "/es", "pl": "/pl"},
        "DEFAULT_LANG": "en",
        "TRANSLATIONS_PATTERN": pattern,
    }


def _configured_site():
    from nikola import Nikola

    return Nikola(
        SITE_URL="https://example.invalid/blog/",
        TRANSLATIONS={"en": "", "es": "/es"},
        DEFAULT_LANG="en",
        INDEX_FILE="index.html",
        PRETTY_URLS=True,
    )


class _PluginFakeSite:
    def __init__(self):
        self.debug = False
        self.shortcodes = {}
        self.calls = []

    def register_shortcode(self, name, handler):
        self.calls.append((name, handler))
        self.shortcodes[name] = handler


@pytest.fixture(scope="module")
def local_site(tmp_path_factory):
    from nikola.__main__ import main

    root = tmp_path_factory.mktemp("nikola_site") / "site"
    _ok(main(["init", "--quiet", str(root)]))

    old = os.getcwd()
    os.chdir(root)
    try:
        _ok(main(["new_post", "-t", "Hello World", "--tags=alpha,beta"]))
        _ok(main(["new_page", "-t", "About Us"]))
        _ok(main(["build"]))
    finally:
        os.chdir(old)
    return root

def test_build_creates_output_directory(local_site):
    assert (local_site / "output").is_dir()

def test_build_creates_site_index(local_site):
    assert (local_site / "output" / "index.html").is_file()

def test_build_creates_post_output_page(local_site):
    assert (local_site / "output" / "posts" / "hello-world" / "index.html").is_file()

def test_build_creates_page_output(local_site):
    assert (local_site / "output" / "pages" / "about-us" / "index.html").is_file()

def test_build_creates_archive_output(local_site):
    assert (local_site / "output" / "archive.html").is_file()

def test_build_creates_category_index(local_site):
    assert (local_site / "output" / "categories" / "index.html").is_file()

def test_build_creates_category_pages_for_post_tags(local_site):
    assert (local_site / "output" / "categories" / "alpha" / "index.html").is_file()
    assert (local_site / "output" / "categories" / "beta" / "index.html").is_file()

def test_build_creates_rss_feed(local_site):
    assert (local_site / "output" / "rss.xml").is_file()

def test_build_creates_sitemap(local_site):
    assert (local_site / "output" / "sitemap.xml").is_file()

def test_generated_post_page_contains_post_title(local_site):
    text = (local_site / "output" / "posts" / "hello-world" / "index.html").read_text(encoding="utf-8")
    assert "Hello World" in text

def test_generated_index_links_to_post(local_site):
    text = (local_site / "output" / "index.html").read_text(encoding="utf-8")
    assert "posts/hello-world" in text

def test_generated_rss_mentions_post(local_site):
    text = (local_site / "output" / "rss.xml").read_text(encoding="utf-8")
    assert "Hello World" in text

def test_generated_sitemap_mentions_post_url(local_site):
    text = (local_site / "output" / "sitemap.xml").read_text(encoding="utf-8")
    assert "posts/hello-world" in text

def test_check_command_accepts_generated_site(local_site):
    from nikola.__main__ import main

    old = os.getcwd()
    os.chdir(local_site)
    try:
        _ok(main(["check", "--check-links", "--check-files"]))
    finally:
        os.chdir(old)

def test_version_command_is_configuration_free():
    from nikola.__main__ import main

    _ok(main(["version"]))

def test_help_command_is_configuration_free():
    from nikola.__main__ import main

    _ok(main(["help"]))

def test_unknown_command_returns_failure():
    from nikola.__main__ import main

    _failed(main(["definitely_unknown_command"]))

def test_build_without_configuration_returns_failure(tmp_path):
    from nikola.__main__ import main

    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        _failed(main(["build"]))
    finally:
        os.chdir(old)

def test_surface_top_level_nikola_constructs_configured_site():
    site = _configured_site()

    assert site.config["SITE_URL"] == "https://example.invalid/blog/"
    assert site.config["DEFAULT_LANG"] == "en"

def test_state_model_has_config_content_and_generated_projections(local_site):
    assert (local_site / "conf.py").is_file()
    assert (local_site / "posts").is_dir()
    assert (local_site / "output").is_dir()

def test_state_model_source_title_is_visible_in_generated_projection(local_site):
    source = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    output = (local_site / "output" / "posts" / "hello-world" / "index.html").read_text(encoding="utf-8")
    assert ".. title: Hello World" in source
    assert "Hello World" in output

def test_state_model_tag_metadata_is_visible_in_taxonomy_projection(local_site):
    source = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert "alpha" in source and "beta" in source
    assert (local_site / "output" / "categories" / "alpha" / "index.html").is_file()
    assert (local_site / "output" / "categories" / "beta" / "index.html").is_file()

def test_configuration_file_declares_post_and_page_patterns(local_site):
    conf = (local_site / "conf.py").read_text(encoding="utf-8")
    assert "POSTS" in conf
    assert "PAGES" in conf

def test_post_source_contains_required_metadata_fields(local_site):
    source = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert ".. title: Hello World" in source
    assert ".. slug: hello-world" in source
    assert ".. date:" in source

def test_page_source_contains_page_metadata(local_site):
    pages = list((local_site / "pages").glob("*.rst"))
    assert pages
    text = pages[0].read_text(encoding="utf-8")
    assert ".. title: About Us" in text
    assert ".. slug: about-us" in text

def test_registered_path_handler_returns_configured_path():
    site = _configured_site()

    site.register_path_handler("custom", lambda name, lang: ["custom", lang, name])
    assert site.path("custom", "thing", "en", False) == "custom/en/thing"

def test_registered_path_handler_link_path_has_leading_slash():
    site = _configured_site()

    site.register_path_handler("custom", lambda name, lang: ["custom", lang, name])
    assert site.path("custom", "thing", "es", True) == "/custom/es/thing"

def test_relative_link_between_pretty_url_pages():
    site = _configured_site()

    assert site.rel_link("/posts/a/index.html", "/posts/b/index.html") == "../b/index.html"

def test_taxonomy_outputs_match_post_tags(local_site):
    post = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert "alpha" in post and "beta" in post
    assert (local_site / "output" / "categories" / "alpha" / "index.html").is_file()
    assert (local_site / "output" / "categories" / "beta" / "index.html").is_file()

def test_command_plugin_receives_active_site():
    from nikola.plugin_categories import Command

    fake = _PluginFakeSite()
    plugin = Command()
    plugin.set_site(fake)
    assert plugin.site is fake

def test_task_and_compiler_plugins_receive_same_site_object():
    from nikola.plugin_categories import PageCompiler, Task

    fake = _PluginFakeSite()
    task = Task()
    compiler = PageCompiler()
    task.set_site(fake)
    compiler.set_site(fake)
    assert task.site is fake
    assert compiler.site is fake

def test_shortcode_plugin_registers_handler_on_site():
    from nikola.plugin_categories import ShortcodePlugin

    class HelloShortcode(ShortcodePlugin):
        name = "hello"

        def handler(self, site, data, lang, post=None, **kw):
            return "handled"

    fake = _PluginFakeSite()
    plugin = HelloShortcode()
    plugin.set_site(fake)
    assert "hello" in fake.shortcodes
    assert fake.shortcodes["hello"]("site", "", "en") == "handled"

def test_invalid_config_file_returns_nonzero(tmp_path):
    from nikola.__main__ import main

    bad_conf = tmp_path / "bad_conf.py"
    bad_conf.write_text("this is not python !!!", encoding="utf-8")
    _failed(main(["--conf=" + str(bad_conf), "build"]))

def test_missing_config_file_returns_nonzero(tmp_path):
    from nikola.__main__ import main

    _failed(main(["--conf=" + str(tmp_path / "missing.py"), "build"]))

def test_invalid_command_option_returns_nonzero(local_site):
    from nikola.__main__ import main

    old = os.getcwd()
    os.chdir(local_site)
    try:
        _failed(main(["check", "--not-a-real-option"]))
    finally:
        os.chdir(old)

def test_duplicate_new_post_returns_nonzero(local_site):
    from nikola.__main__ import main

    old = os.getcwd()
    os.chdir(local_site)
    try:
        _failed(main(["new_post", "-t", "Hello World"]))
    finally:
        os.chdir(old)

def test_cross_view_post_source_generates_matching_output_path(local_site):
    assert (local_site / "posts" / "hello-world.rst").is_file()
    assert (local_site / "output" / "posts" / "hello-world" / "index.html").is_file()

def test_cross_view_index_feed_and_sitemap_reference_post(local_site):
    index = (local_site / "output" / "index.html").read_text(encoding="utf-8")
    rss = (local_site / "output" / "rss.xml").read_text(encoding="utf-8")
    sitemap = (local_site / "output" / "sitemap.xml").read_text(encoding="utf-8")
    assert "posts/hello-world" in index
    assert "Hello World" in rss
    assert "posts/hello-world" in sitemap

def test_cross_view_tag_metadata_matches_category_outputs(local_site):
    source = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert "alpha" in source
    assert (local_site / "output" / "categories" / "alpha" / "index.html").is_file()

def test_cross_view_page_source_generates_page_output(local_site):
    pages = list((local_site / "pages").glob("*.rst"))
    assert pages
    assert (local_site / "output" / "pages" / "about-us" / "index.html").is_file()

def test_cross_view_check_accepts_same_generated_projection(local_site):
    from nikola.__main__ import main

    old = os.getcwd()
    os.chdir(local_site)
    try:
        _ok(main(["check", "--check-links", "--check-files"]))
    finally:
        os.chdir(old)

def test_workflow_init_new_post_build_check_created_site(local_site):
    assert (local_site / "conf.py").is_file()
    assert (local_site / "posts" / "hello-world.rst").is_file()
    assert (local_site / "output" / "index.html").is_file()

def test_workflow_register_and_apply_site_shortcode():
    site = _configured_site()
    site.register_shortcode("hello", lambda site, data, lang, post=None: "Hello")

    rendered, deps = site.apply_shortcodes("{{% hello %}}", "post.rst", "en", {})
    assert rendered == "Hello"
    assert deps == []

def test_workflow_register_path_handler_and_resolve_link():
    site = _configured_site()
    site.register_path_handler("custom", lambda name, lang: ["custom", lang, name])

    assert site.path("custom", "thing", "es", True) == "/custom/es/thing"

