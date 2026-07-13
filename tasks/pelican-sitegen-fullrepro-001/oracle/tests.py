from __future__ import annotations

import re
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

import pelican
from pelican import Pelican, get_config, parse_arguments
from pelican import signals as package_signals
from pelican.plugins import signals as plugin_signals
from pelican.paginator import PaginationRule, Paginator
from pelican.readers import Readers
from pelican.settings import DEFAULT_CONFIG, read_settings
from pelican.urlwrappers import Author, Category, Tag
from pelican.utils import get_date, path_to_url, posixize_path, slugify


@pytest.fixture(scope="module")
def generated_site(tmp_path_factory):
    root = tmp_path_factory.mktemp("pelican_public_site")
    content = root / "content"
    output = root / "output"
    theme = root / "theme"
    (content / "articles").mkdir(parents=True)
    (content / "pages").mkdir()
    (content / "images").mkdir()
    (theme / "templates").mkdir(parents=True)

    (theme / "templates" / "article.html").write_text(
        "\n".join(
            [
                "ARTICLE_TITLE={{ article.title }}",
                "ARTICLE_URL={{ article.url }}",
                "ARTICLE_SAVE_AS={{ article.save_as }}",
                "ARTICLE_CATEGORY={{ article.category }}",
                "ARTICLE_AUTHOR={{ article.author }}",
                "ARTICLE_TAGS={% for tag in article.tags %}{{ tag }};{% endfor %}",
                "ARTICLE_SUMMARY={{ article.summary|striptags }}",
                "ARTICLE_BODY={{ article.content }}",
                "SITE={{ SITENAME }} {{ SITEURL }}",
            ]
        ),
        encoding="utf-8",
    )
    (theme / "templates" / "page.html").write_text(
        "PAGE_TITLE={{ page.title }}\nPAGE_URL={{ page.url }}\nPAGE_BODY={{ page.content }}",
        encoding="utf-8",
    )
    (theme / "templates" / "index.html").write_text(
        "INDEX_ARTICLES={% for article in articles %}{{ article.title }};{% endfor %}",
        encoding="utf-8",
    )

    (content / "articles" / "keyboard.md").write_text(
        "\n".join(
            [
                "Title: Keyboard Review",
                "Date: 2010-12-03 10:20",
                "Modified: 2010-12-04 12:30",
                "Category: Review",
                "Tags: hardware, keyboards",
                "Slug: keyboard-review",
                "Authors: Ada Lovelace, Grace Hopper",
                "Summary: Short summary here.",
                "",
                "Following [logo]({static}/images/logo.txt) review.",
            ]
        ),
        encoding="utf-8",
    )
    (content / "articles" / "hidden.md").write_text(
        "Title: Hidden Note\nDate: 2010-12-04\nStatus: hidden\nSlug: hidden-note\n\nHidden body.",
        encoding="utf-8",
    )
    (content / "articles" / "draft.md").write_text(
        "Title: Draft Note\nDate: 2010-12-05\nStatus: draft\nSlug: draft-note\n\nDraft body.",
        encoding="utf-8",
    )
    (content / "pages" / "about.md").write_text(
        "Title: About\nSlug: about\n\nAbout page body.",
        encoding="utf-8",
    )
    (content / "images" / "logo.txt").write_text("LOGO", encoding="utf-8")

    settings = read_settings(
        override={
            "PATH": str(content),
            "OUTPUT_PATH": str(output),
            "THEME": str(theme),
            "SITENAME": "My Site",
            "SITEURL": "https://example.test",
            "ARTICLE_PATHS": ["articles"],
            "PAGE_PATHS": ["pages"],
            "STATIC_PATHS": ["images"],
            "ARTICLE_URL": "posts/{slug}.html",
            "ARTICLE_SAVE_AS": "posts/{slug}.html",
            "DRAFT_URL": "drafts/{slug}.html",
            "DRAFT_SAVE_AS": "drafts/{slug}.html",
            "PAGE_URL": "pages/{slug}.html",
            "PAGE_SAVE_AS": "pages/{slug}.html",
            "AUTHOR_SAVE_AS": "author/{slug}.html",
            "CATEGORY_SAVE_AS": "category/{slug}.html",
            "TAG_SAVE_AS": "tag/{slug}.html",
            "FEED_ALL_ATOM": "feeds/all.atom.xml",
            "CATEGORY_FEED_ATOM": "feeds/{slug}.atom.xml",
            "TIMEZONE": "UTC",
            "DELETE_OUTPUT_DIRECTORY": True,
        }
    )
    Pelican(settings).run()
    return {"root": root, "content": content, "output": output, "settings": settings}


def text(site, relative):
    return (site["output"] / relative).read_text(encoding="utf-8")


def feed_entries(site):
    root = ET.fromstring(text(site, "feeds/all.atom.xml"))
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    return root.findall("atom:entry", ns)


def public_settings():
    return read_settings(
        override={
            "AUTHOR_URL": "author/{slug}.html",
            "AUTHOR_SAVE_AS": "author/{slug}.html",
            "CATEGORY_URL": "category/{slug}.html",
            "CATEGORY_SAVE_AS": "category/{slug}.html",
            "TAG_URL": "tag/{slug}.html",
            "TAG_SAVE_AS": "tag/{slug}.html",
        }
    )


def test_01_default_settings_include_default_language():
    assert DEFAULT_CONFIG["DEFAULT_LANG"] == "en"


def test_02_pelican_package_exposes_version_string():
    assert isinstance(pelican.__version__, str) and re.match(r"\d+\.\d+", pelican.__version__)


def test_03_pelican_package_exports_main_classes():
    assert pelican.Pelican is Pelican


def test_04_read_settings_applies_explicit_override():
    assert read_settings(override={"SITENAME": "Override Site"})["SITENAME"] == "Override Site"


def test_05_read_settings_keeps_unspecified_defaults():
    settings = read_settings(override={"SITENAME": "Override Site"})
    assert settings["DEFAULT_LANG"] == DEFAULT_CONFIG["DEFAULT_LANG"]


def test_06_read_settings_normalizes_output_path_override(tmp_path):
    settings = read_settings(override={"OUTPUT_PATH": str(tmp_path / "public")})
    assert Path(settings["OUTPUT_PATH"]).name == "public"


def test_07_parse_arguments_decodes_json_extra_settings():
    args = parse_arguments(["content", "-e", 'SITENAME="CLI Site"', "RELATIVE_URLS=true"])
    assert args.overrides == {"SITENAME": "CLI Site", "RELATIVE_URLS": True}


def test_08_parse_arguments_accepts_multiple_extra_settings():
    args = parse_arguments(["content", "-e", 'SITENAME="CLI Site"', "CACHE_CONTENT=true"])
    assert args.overrides["CACHE_CONTENT"] is True


def test_09_parse_arguments_rejects_missing_equals():
    with pytest.raises(ValueError):
        parse_arguments(["content", "-e", "SITENAME"])


def test_10_parse_arguments_rejects_non_json_value():
    with pytest.raises(ValueError):
        parse_arguments(["content", "-e", "CACHE_CONTENT=True"])


def test_11_get_config_turns_cli_overrides_into_settings():
    args = parse_arguments(["content", "-e", 'SITENAME="CLI Site"'])
    assert get_config(args)["SITENAME"] == "CLI Site"


def test_12_get_config_respects_relative_urls_flag():
    args = parse_arguments(["content", "--relative-urls"])
    assert get_config(args)["RELATIVE_URLS"] is True


def test_13_slugify_uses_regex_substitutions_for_url_parts():
    value = slugify("Hello, Static Site!", regex_subs=[(r"[^\w\s-]", ""), (r"[-\s]+", "-")])
    assert value == "hello-static-site"


def test_14_slugify_can_preserve_case():
    assert slugify("Hello World", regex_subs=[(r"[-\s]+", "-")], preserve_case=True) == "Hello-World"


def test_15_posixize_path_uses_forward_slashes():
    assert posixize_path(os.path.join("nested", "path", "file.html")) == "nested/path/file.html"


def test_16_path_to_url_keeps_forward_slash_urls():
    assert path_to_url("nested/path/index.html") == "nested/path/index.html"


def test_17_get_date_parses_pelican_datetime_metadata():
    assert str(get_date("2010-12-03 10:20")) == "2010-12-03 10:20:00"


def test_18_author_slug_url_and_save_path_agree():
    author = Author("Ada Lovelace", settings=public_settings())
    assert (author.slug, author.url, author.save_as) == (
        "ada-lovelace",
        "author/ada-lovelace.html",
        "author/ada-lovelace.html",
    )


def test_19_category_slug_url_and_save_path_agree():
    category = Category("Hardware Reviews", settings=public_settings())
    assert (category.slug, category.url, category.save_as) == (
        "hardware-reviews",
        "category/hardware-reviews.html",
        "category/hardware-reviews.html",
    )


def test_20_tag_slug_url_and_save_path_agree():
    tag = Tag("Key Boards", settings=public_settings())
    assert (tag.slug, tag.url, tag.save_as) == ("key-boards", "tag/key-boards.html", "tag/key-boards.html")


def test_21_urlwrapper_as_dict_exposes_name_and_slug():
    assert Author("Grace Hopper", settings=public_settings()).as_dict()["slug"] == "grace-hopper"


def test_22_readers_read_markdown_content_and_metadata(tmp_path):
    source = tmp_path / "article.md"
    source.write_text("Title: Reader Title\nDate: 2010-12-03\n\nReader body.", encoding="utf-8")
    settings = read_settings(override={"PATH": str(tmp_path)})
    page = Readers(settings).read_file(base_path=str(tmp_path), path="article.md")
    assert page.metadata["title"] == "Reader Title"
    assert "Reader body" in page.content


def test_23_reader_reports_unknown_extension_as_unsupported():
    readers = Readers(read_settings())
    with pytest.raises(TypeError):
        readers.read_file(base_path=".", path="article.unknownextension")


def test_24_public_signal_namespaces_share_generation_signal():
    assert package_signals.article_generator_finalized is plugin_signals.article_generator_finalized


def test_25_plugin_signal_namespace_exposes_content_object_signal():
    assert plugin_signals.content_object_init is package_signals.content_object_init


def test_26_paginator_reports_count_and_page_range():
    paginator = Paginator("index.html", "", list(range(5)), public_settings(), per_page=2)
    assert (paginator.count, paginator.num_pages, paginator.page_range) == (5, 3, [1, 2, 3])


def test_27_paginator_first_page_has_next_only():
    page = Paginator("index.html", "", list(range(5)), public_settings(), per_page=2).page(1)
    assert page.object_list == [0, 1] and page.has_next() and not page.has_previous()


def test_28_paginator_middle_page_has_neighbors():
    page = Paginator("index.html", "", list(range(5)), public_settings(), per_page=2).page(2)
    assert page.object_list == [2, 3] and page.has_next() and page.has_previous()


def test_29_pagination_rule_is_public_three_field_tuple():
    rule = PaginationRule(2, "{name}{number}{extension}", "{name}{number}{extension}")
    assert (rule.min_page, rule.URL, rule.SAVE_AS) == (2, "{name}{number}{extension}", "{name}{number}{extension}")


def test_30_generated_article_uses_configured_save_path(generated_site):
    assert (generated_site["output"] / "posts/keyboard-review.html").is_file()


def test_31_article_template_receives_title_metadata(generated_site):
    assert "ARTICLE_TITLE=Keyboard Review" in text(generated_site, "posts/keyboard-review.html")


def test_32_article_template_receives_url_metadata(generated_site):
    assert "ARTICLE_URL=posts/keyboard-review.html" in text(generated_site, "posts/keyboard-review.html")


def test_33_article_template_receives_save_as_metadata(generated_site):
    assert "ARTICLE_SAVE_AS=posts/keyboard-review.html" in text(generated_site, "posts/keyboard-review.html")


def test_34_article_template_receives_category_metadata(generated_site):
    assert "ARTICLE_CATEGORY=Review" in text(generated_site, "posts/keyboard-review.html")


def test_35_article_template_receives_author_metadata(generated_site):
    assert "ARTICLE_AUTHOR=Ada Lovelace" in text(generated_site, "posts/keyboard-review.html")


def test_36_article_template_receives_tag_metadata(generated_site):
    assert "ARTICLE_TAGS=hardware;keyboards;" in text(generated_site, "posts/keyboard-review.html")


def test_37_article_template_receives_summary_metadata(generated_site):
    assert "ARTICLE_SUMMARY=Short summary here." in text(generated_site, "posts/keyboard-review.html")


def test_38_static_link_renders_to_site_url(generated_site):
    assert 'href="https://example.test/images/logo.txt"' in text(generated_site, "posts/keyboard-review.html")


def test_39_static_file_is_copied_to_output(generated_site):
    assert text(generated_site, "images/logo.txt") == "LOGO"


def test_40_index_contains_published_article(generated_site):
    assert "INDEX_ARTICLES=Keyboard Review;" in text(generated_site, "index.html")


def test_41_hidden_article_has_output_file(generated_site):
    assert (generated_site["output"] / "posts/hidden-note.html").is_file()


def test_42_hidden_article_is_not_listed_on_index(generated_site):
    assert "Hidden Note" not in text(generated_site, "index.html")


def test_43_draft_article_uses_draft_output_location(generated_site):
    assert (generated_site["output"] / "drafts/draft-note.html").is_file()


def test_44_draft_article_is_not_listed_on_index(generated_site):
    assert "Draft Note" not in text(generated_site, "index.html")


def test_45_page_uses_page_url_and_save_path(generated_site):
    assert "PAGE_URL=pages/about.html" in text(generated_site, "pages/about.html")


def test_46_page_template_receives_page_body(generated_site):
    assert "About page body." in text(generated_site, "pages/about.html")


def test_47_category_page_is_generated_for_article_category(generated_site):
    assert (generated_site["output"] / "category/review.html").is_file()


def test_48_tag_pages_are_generated_for_each_tag(generated_site):
    assert (generated_site["output"] / "tag/hardware.html").is_file()
    assert (generated_site["output"] / "tag/keyboards.html").is_file()


def test_49_author_pages_are_generated_for_each_author(generated_site):
    assert (generated_site["output"] / "author/ada-lovelace.html").is_file()
    assert (generated_site["output"] / "author/grace-hopper.html").is_file()


def test_50_all_articles_feed_is_generated(generated_site):
    assert (generated_site["output"] / "feeds/all.atom.xml").is_file()


def test_51_feed_entry_uses_same_article_title_as_page(generated_site):
    entry = feed_entries(generated_site)[0]
    assert entry.findtext("{http://www.w3.org/2005/Atom}title") == "Keyboard Review"


def test_52_feed_entry_uses_same_article_url_as_page(generated_site):
    entry = feed_entries(generated_site)[0]
    link = entry.find("{http://www.w3.org/2005/Atom}link")
    assert link is not None and link.attrib["href"] == "https://example.test/posts/keyboard-review.html"


def test_53_feed_excludes_hidden_and_draft_articles(generated_site):
    titles = [entry.findtext("{http://www.w3.org/2005/Atom}title") for entry in feed_entries(generated_site)]
    assert titles == ["Keyboard Review"]


def test_54_category_feed_uses_category_slug(generated_site):
    assert (generated_site["output"] / "feeds/review.atom.xml").is_file()


def test_55_generated_output_contains_no_source_markdown_files(generated_site):
    generated = {p.name for p in generated_site["output"].rglob("*") if p.is_file()}
    assert "keyboard.md" not in generated


def test_56_cli_and_programmatic_settings_describe_same_site_name():
    args = parse_arguments(["content", "-e", 'SITENAME="My Site"'])
    assert get_config(args)["SITENAME"] == read_settings(override={"SITENAME": "My Site"})["SITENAME"]
