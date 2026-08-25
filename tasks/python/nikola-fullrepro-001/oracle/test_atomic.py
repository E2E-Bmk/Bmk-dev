"""Atomic tests for nikola-fullrepro-001.

Each test verifies ONE public API entry point and ONE behavior point.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from nikola.plugin_categories import Command, PageCompiler
from nikola.shortcodes import ParsingError, apply_shortcodes, extract_shortcodes
from nikola.utils import (
    TranslatableSetting,
    LocaleBorg,
    bool_from_meta,
    config_changed,
    create_redirect,
    encodelink,
    get_translation_candidate,
    load_data,
    slugify,
    unslugify,
    write_metadata,
)

from conftest import (
    PluginFakeSite,
    expect_success,
    minimal_site,
    translation_config,
)


# ===================================================================
# Package metadata
# ===================================================================


def test_package_version_is_nonempty_string():
    import nikola

    assert isinstance(nikola.__version__, str)
    assert len(nikola.__version__) >= 3


def test_debug_flags_follow_environment_variables():
    env = os.environ.copy()
    env.update(
        {
            "NIKOLA_DEBUG": "1",
            "NIKOLA_TEMPLATES_TRACE": "1",
            "NIKOLA_SHOW_TRACEBACKS": "1",
        }
    )
    code = (
        "import nikola; "
        "print(nikola.DEBUG, nikola.TEMPLATES_TRACE, nikola.SHOW_TRACEBACKS)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout.strip() == "True True True"


# ===================================================================
# slugify
# ===================================================================


def test_slugify_lowercases_ascii_words():
    assert slugify("Bright Morning!") == "bright-morning"


def test_slugify_transliterates_diacritics():
    assert slugify("Zażółć gęślą jaźń") == "zazolc-gesla-jazn"


def test_slugify_removes_unsafe_punctuation():
    assert slugify("A/B:C? D") == "abc-d"


# ===================================================================
# unslugify
# ===================================================================


def test_unslugify_restores_simple_slug():
    assert unslugify("bright-morning") == "Bright morning"


def test_unslugify_restores_multiple_segments():
    assert unslugify("alpha-beta-gamma") == "Alpha beta gamma"


# ===================================================================
# encodelink
# ===================================================================


def test_encodelink_escapes_spaces():
    assert encodelink("hello world.html") == "hello%20world.html"


def test_encodelink_escapes_unicode():
    assert encodelink("ümlaut and space.html") == "%C3%BCmlaut%20and%20space.html"


def test_encodelink_preserves_existing_percent_encoding():
    assert encodelink("already%20encoded.html") == "already%20encoded.html"


# ===================================================================
# get_translation_candidate
# ===================================================================


def test_translation_candidate_adds_language_before_extension():
    assert (
        get_translation_candidate(translation_config(), "article.rst", "es")
        == "article.es.rst"
    )


def test_translation_candidate_removes_language_for_default():
    assert (
        get_translation_candidate(translation_config(), "article.es.rst", "en")
        == "article.rst"
    )


def test_translation_candidate_supports_extension_language_pattern():
    cfg = translation_config("{path}.{ext}.{lang}")
    assert get_translation_candidate(cfg, "article.rst", "es") == "article.rst.es"


def test_translation_candidate_reverses_extension_language_pattern():
    cfg = translation_config("{path}.{ext}.{lang}")
    assert get_translation_candidate(cfg, "article.rst.es", "en") == "article.rst"


def test_translation_candidate_preserves_directory_and_compound_extension():
    assert (
        get_translation_candidate(
            translation_config(),
            "cache/posts/fancy.post.html",
            "es",
        )
        == "cache/posts/fancy.post.es.html"
    )


# ===================================================================
# bool_from_meta
# ===================================================================


def test_bool_from_meta_accepts_true_word():
    assert bool_from_meta({"draft": "true"}, "draft", fallback=False) is True


def test_bool_from_meta_accepts_yes_word():
    assert bool_from_meta({"draft": "yes"}, "draft", fallback=False) is True


def test_bool_from_meta_accepts_one_string():
    assert bool_from_meta({"draft": "1"}, "draft", fallback=False) is True


def test_bool_from_meta_accepts_false_word():
    assert bool_from_meta({"draft": "false"}, "draft", fallback=True) is False


def test_bool_from_meta_accepts_no_word():
    assert bool_from_meta({"draft": "no"}, "draft", fallback=True) is False


def test_bool_from_meta_accepts_zero_string():
    assert bool_from_meta({"draft": "0"}, "draft", fallback=True) is False


def test_bool_from_meta_uses_blank_for_missing_key():
    assert bool_from_meta({}, "draft", fallback="fallback", blank="blank") == "blank"


def test_bool_from_meta_uses_fallback_for_unknown_text():
    assert (
        bool_from_meta({"draft": "unknown"}, "draft", fallback="fallback", blank="blank")
        == "fallback"
    )


# ===================================================================
# write_metadata / create_redirect / load_data
# ===================================================================


def test_write_metadata_nikola_format_contains_declared_fields():
    data = write_metadata(
        {"title": "Orbital Notes", "slug": "orbital-notes", "a": "1", "b": "2"},
        "nikola",
    )
    assert ".. title: Orbital Notes" in data
    assert ".. slug: orbital-notes" in data
    assert ".. a: 1" in data
    assert data.endswith("\n\n")


def test_create_redirect_writes_target_url(tmp_path):
    target = tmp_path / "from.html"
    create_redirect(str(target), "https://orbital.test/destination")
    text = target.read_text(encoding="utf-8")
    assert "Redirecting" in text
    assert "https://orbital.test/destination" in text


def test_load_data_reads_json_mapping(tmp_path):
    source = tmp_path / "data.json"
    source.write_text('{"alpha": 1, "beta": [2]}', encoding="utf-8")
    assert load_data(str(source)) == {"alpha": 1, "beta": [2]}


# ===================================================================
# Shortcode helpers
# ===================================================================


def test_apply_shortcodes_replaces_single_shortcode():
    def marker(site, data, lang, post=None, **kw):
        return "MARKER"

    rendered, deps = apply_shortcodes(
        "Prefix {{% marker %}} suffix",
        {"marker": marker},
        None,
        "fragment.rst",
        True,
        "en",
        {},
    )
    assert rendered == "Prefix MARKER suffix"
    assert deps == []


def test_apply_shortcodes_passes_body_to_shortcode():
    def echo(site, data, lang, post=None, **kw):
        return "ECHO[" + (data or "") + "]"

    rendered, deps = apply_shortcodes(
        "Start {{% echo %}}payload{{% /echo %}} end",
        {"echo": echo},
        None,
        "fragment.rst",
        True,
        "en",
        {},
    )
    assert rendered == "Start ECHO[payload] end"
    assert deps == []


def test_extract_shortcodes_replaces_shortcode_with_token():
    rendered, replacements = extract_shortcodes("Before {{% marker %}} after")
    assert rendered.startswith("Before SHORTCODE")
    assert rendered.endswith("REPLACEMENT after")
    assert list(replacements.values()) == ["{{% marker %}}"]


def test_unknown_shortcode_with_exceptions_enabled_returns_empty_output():
    rendered, deps = apply_shortcodes(
        "{{% missing %}}",
        {},
        None,
        "fragment.rst",
        True,
        "en",
        {},
    )
    assert rendered == ""
    assert deps == []


def test_malformed_shortcode_raises_parsing_error():
    with pytest.raises(ParsingError):
        apply_shortcodes("{{%", {}, None, "broken.rst", True, "en", {})


# ===================================================================
# TranslatableSetting / config_changed
# ===================================================================


def test_translatable_setting_returns_language_specific_values():
    LocaleBorg.initialize({"en": "en", "es": "es"}, "en")
    setting = TranslatableSetting(
        "TITLE",
        {"en": "Orbital Notes", "es": "Notas Orbitales"},
        {},
    )
    assert setting("en") == "Orbital Notes"
    assert setting("es") == "Notas Orbitales"


def test_config_changed_stores_identifier_and_config_snapshot():
    first = config_changed({"SITE_URL": "https://orbital.test/"}, "orbital-site")
    second = config_changed({"SITE_URL": "https://changed.test/"}, "orbital-site")
    assert first.identifier == "_config_changed:orbital-site"
    assert first.config["SITE_URL"] == "https://orbital.test/"
    assert second.config["SITE_URL"] == "https://changed.test/"
    assert first != second


# ===================================================================
# Configuration-free CLI commands
# ===================================================================


def test_version_command_runs_without_project_configuration():
    from nikola.__main__ import main

    expect_success(main(["version"]))


def test_help_command_runs_without_project_configuration():
    from nikola.__main__ import main

    expect_success(main(["help"]))


# ===================================================================
# Path resolution and link generation
# ===================================================================


def test_relative_link_computes_pretty_url_navigation():
    site = minimal_site()
    assert site.rel_link("/posts/a/index.html", "/posts/b/index.html") == "../b/index.html"


def test_unknown_path_kind_returns_empty_path():
    site = minimal_site()
    assert site.path("missing_kind", "value", "en", False) == ""


# ===================================================================
# Site configuration projection
# ===================================================================


def test_site_constructor_exposes_config_values():
    site = minimal_site()
    assert site.config["SITE_URL"] == "https://orbital.test/blog/"
    assert site.config["DEFAULT_LANG"] == "en"


# ===================================================================
# Plugin category set_site contract
# ===================================================================


def test_command_plugin_receives_active_site():
    fake = PluginFakeSite()
    plugin = Command()
    plugin.set_site(fake)
    assert plugin.site is fake


def test_pagecompiler_plugin_receives_active_site():
    fake = PluginFakeSite()
    plugin = PageCompiler()
    plugin.set_site(fake)
    assert plugin.site is fake
