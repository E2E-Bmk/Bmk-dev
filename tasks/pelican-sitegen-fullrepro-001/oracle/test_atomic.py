"""Atomic layer tests for pelican-sitegen-fullrepro-001.

Each test verifies ONE public API entry's ONE behavior.
Independent Solvability: if only that API is correctly implemented, the test passes.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from pelican import get_config, parse_arguments
from pelican.paginator import PaginationRule, Paginator
from pelican.readers import Readers
from pelican.settings import DEFAULT_CONFIG, read_settings
from pelican.urlwrappers import Author, Category, Tag
from pelican.utils import get_date, path_to_url, posixize_path, slugify

from conftest import wrapper_settings


# ===================================================================
# DEFAULT_CONFIG
# ===================================================================

def test_default_config_provides_default_lang_en():
    assert DEFAULT_CONFIG["DEFAULT_LANG"] == "en"


def test_default_config_contains_standard_keys():
    for key in ("DEFAULT_LANG", "SITENAME", "OUTPUT_PATH"):
        assert key in DEFAULT_CONFIG


# ===================================================================
# read_settings
# ===================================================================

def test_read_settings_returns_dict_with_defaults():
    settings = read_settings()
    assert isinstance(settings, dict)
    assert "DEFAULT_LANG" in settings


def test_read_settings_override_replaces_default():
    settings = read_settings(override={"SITENAME": "Replaced Name"})
    assert settings["SITENAME"] == "Replaced Name"


def test_read_settings_preserves_unoverridden_defaults():
    settings = read_settings(override={"SITENAME": "Xyz"})
    assert settings["DEFAULT_LANG"] == "en"


def test_read_settings_normalizes_output_path(tmp_path):
    target = tmp_path / "rendered"
    settings = read_settings(override={"OUTPUT_PATH": str(target)})
    assert Path(settings["OUTPUT_PATH"]).name == "rendered"


# ===================================================================
# parse_arguments
# ===================================================================

def test_parse_arguments_extra_settings_accumulate():
    args = parse_arguments(
        ["content", "-e", 'SITENAME="Accum"', 'CACHE_CONTENT=false']
    )
    assert args.overrides["SITENAME"] == "Accum"
    assert args.overrides["CACHE_CONTENT"] is False


def test_parse_arguments_stores_overrides_in_mapping():
    args = parse_arguments(["content", "-e", 'DEFAULT_PAGINATION=8'])
    assert isinstance(args.overrides, dict)
    assert args.overrides["DEFAULT_PAGINATION"] == 8


def test_parse_arguments_missing_equals_raises_valueerror():
    with pytest.raises(ValueError):
        parse_arguments(["content", "-e", "SITENAME"])


def test_parse_arguments_invalid_json_raises_valueerror():
    with pytest.raises(ValueError):
        parse_arguments(["content", "-e", "CACHE_CONTENT=True"])


def test_parse_arguments_accepts_relative_urls_flag():
    args = parse_arguments(["content", "--relative-urls"])
    assert getattr(args, "relative_urls", False) is True


# ===================================================================
# get_config
# ===================================================================

def test_get_config_produces_settings_mapping():
    args = parse_arguments(["content", "-e", 'SITENAME="Via CLI"'])
    settings = get_config(args)
    assert settings["SITENAME"] == "Via CLI"


def test_get_config_sets_relative_urls_true():
    args = parse_arguments(["content", "--relative-urls"])
    settings = get_config(args)
    assert settings["RELATIVE_URLS"] is True


# ===================================================================
# slugify
# ===================================================================

def test_slugify_lowercases_without_preserve_case():
    result = slugify("Bright Morning", regex_subs=[(r"[-\s]+", "-")])
    assert result == "bright-morning"


def test_slugify_retains_case_with_preserve_case_true():
    result = slugify(
        "Bright Morning", regex_subs=[(r"[-\s]+", "-")], preserve_case=True
    )
    assert result == "Bright-Morning"


def test_slugify_applies_configured_regex_subs():
    result = slugify(
        "Hello, Ceramic World!",
        regex_subs=[(r"[^\w\s-]", ""), (r"[-\s]+", "-")],
    )
    assert result == "hello-ceramic-world"


# ===================================================================
# posixize_path
# ===================================================================

def test_posixize_path_normalizes_backslashes():
    assert (
        posixize_path(os.path.join("alpha", "beta", "gamma.html"))
        == "alpha/beta/gamma.html"
    )


def test_posixize_path_preserves_forward_slashes():
    assert posixize_path("alpha/beta/gamma.html") == "alpha/beta/gamma.html"


# ===================================================================
# path_to_url
# ===================================================================

def test_path_to_url_produces_forward_slashes():
    assert (
        path_to_url("entries/ceramic-mugs-guide.html")
        == "entries/ceramic-mugs-guide.html"
    )


def test_path_to_url_handles_deeply_nested_paths():
    assert path_to_url("a/b/c/d/index.html") == "a/b/c/d/index.html"


# ===================================================================
# get_date
# ===================================================================

def test_get_date_returns_datetime_from_valid_string():
    dt = get_date("2015-08-14 09:30")
    assert dt.year == 2015 and dt.month == 8 and dt.day == 14


def test_get_date_raises_on_unparseable_input():
    with pytest.raises(ValueError):
        get_date("not-a-valid-date-string")


# ===================================================================
# Author
# ===================================================================

def test_author_slug_derived_from_display_name():
    author = Author("Tomoko Nagai", settings=wrapper_settings())
    assert author.slug == "tomoko-nagai"


def test_author_url_uses_settings_pattern():
    author = Author("Tomoko Nagai", settings=wrapper_settings())
    assert author.url == "writers/tomoko-nagai.html"
    assert author.save_as == "writers/tomoko-nagai.html"


def test_author_as_dict_contains_name_and_slug():
    d = Author("Tomoko Nagai", settings=wrapper_settings()).as_dict()
    assert d["name"] == "Tomoko Nagai"
    assert d["slug"] == "tomoko-nagai"


# ===================================================================
# Category
# ===================================================================

def test_category_slug_from_display_name():
    cat = Category("Lifestyle", settings=wrapper_settings())
    assert cat.slug == "lifestyle"


def test_category_url_follows_settings_pattern():
    cat = Category("Urban Crafts", settings=wrapper_settings())
    assert cat.url == "topics/urban-crafts.html"
    assert cat.save_as == "topics/urban-crafts.html"


def test_category_as_dict_contains_name_and_slug():
    d = Category("Urban Crafts", settings=wrapper_settings()).as_dict()
    assert d["name"] == "Urban Crafts"
    assert d["slug"] == "urban-crafts"


# ===================================================================
# Tag
# ===================================================================

def test_tag_slug_from_display_name():
    tag = Tag("ceramics", settings=wrapper_settings())
    assert tag.slug == "ceramics"


def test_tag_url_follows_settings_pattern():
    tag = Tag("Fine Crafts", settings=wrapper_settings())
    assert tag.url == "labels/fine-crafts.html"
    assert tag.save_as == "labels/fine-crafts.html"


def test_tag_as_dict_contains_name_and_slug():
    d = Tag("Fine Crafts", settings=wrapper_settings()).as_dict()
    assert d["name"] == "Fine Crafts"
    assert d["slug"] == "fine-crafts"


# ===================================================================
# Readers
# ===================================================================

def test_readers_extracts_content_and_metadata(tmp_path):
    (tmp_path / "note.md").write_text(
        "Title: Orbital Entry\nDate: 2015-08-14\n\nBody of orbital note.",
        encoding="utf-8",
    )
    settings = read_settings(override={"PATH": str(tmp_path)})
    result = Readers(settings).read_file(
        base_path=str(tmp_path), path="note.md"
    )
    assert result.metadata["title"] == "Orbital Entry"
    assert "Body of orbital note" in result.content


def test_readers_unknown_extension_raises_typeerror(tmp_path):
    (tmp_path / "document.qwxyz").write_text("data", encoding="utf-8")
    readers = Readers(read_settings())
    with pytest.raises(TypeError):
        readers.read_file(base_path=str(tmp_path), path="document.qwxyz")


# ===================================================================
# Paginator
# ===================================================================

def test_paginator_count_equals_total_items():
    p = Paginator("entries", "", list(range(17)), wrapper_settings(), per_page=4)
    assert p.count == 17


def test_paginator_num_pages_is_correct():
    p = Paginator("entries", "", list(range(17)), wrapper_settings(), per_page=4)
    assert p.num_pages == 5


def test_paginator_page_range_starts_at_one():
    p = Paginator("entries", "", list(range(17)), wrapper_settings(), per_page=4)
    assert p.page_range == [1, 2, 3, 4, 5]


def test_paginator_first_page_has_next_not_previous():
    p = Paginator("entries", "", list(range(17)), wrapper_settings(), per_page=4)
    page = p.page(1)
    assert page.has_next() is True
    assert page.has_previous() is False
    assert page.object_list == [0, 1, 2, 3]


def test_paginator_middle_page_has_both_neighbors():
    p = Paginator("entries", "", list(range(17)), wrapper_settings(), per_page=4)
    page = p.page(3)
    assert page.has_next() is True
    assert page.has_previous() is True


# ===================================================================
# PaginationRule
# ===================================================================

def test_pagination_rule_exposes_three_fields():
    rule = PaginationRule(
        3, "{name}/{number}{extension}", "{name}/{number}{extension}"
    )
    assert rule.min_page == 3
    assert rule.URL == "{name}/{number}{extension}"
    assert rule.SAVE_AS == "{name}/{number}{extension}"


# ===================================================================
# signals
# ===================================================================

def test_signals_available_from_pelican_package():
    from pelican import signals

    assert hasattr(signals, "article_generator_finalized")


def test_signals_available_from_plugins_package():
    from pelican.plugins import signals

    assert hasattr(signals, "content_object_init")
