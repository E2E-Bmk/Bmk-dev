# Spec2Repo oracle - integration tests for pelican-sitegen-fullrepro-001
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
