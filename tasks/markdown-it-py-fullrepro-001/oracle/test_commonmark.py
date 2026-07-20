from __future__ import annotations

# Rewritten from the first three entries in tests/test_cmark_spec/commonmark.json.
from markdown_it import MarkdownIt


def assert_commonmark(source: str, expected: str) -> None:
    assert MarkdownIt("commonmark").render(source) == expected


def test_commonmark_tab_example_1() -> None:
    assert_commonmark(
        "\tfoo\tbaz\t\tbim\n",
        "<pre><code>foo\tbaz\t\tbim\n</code></pre>\n",
    )


def test_commonmark_tab_example_2() -> None:
    assert_commonmark(
        "  \tfoo\tbaz\t\tbim\n",
        "<pre><code>foo\tbaz\t\tbim\n</code></pre>\n",
    )


def test_commonmark_tab_example_3() -> None:
    assert_commonmark(
        "    a\ta\n    ὐ\ta\n",
        "<pre><code>a\ta\nὐ\ta\n</code></pre>\n",
    )
