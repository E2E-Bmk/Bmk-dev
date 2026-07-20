from __future__ import annotations

# Rewritten from tests/test_port/test_no_end_newline.py at the pinned source revision.
from markdown_it import MarkdownIt


def assert_render(source: str, expected: str) -> None:
    assert MarkdownIt().render(source) == expected


def test_no_end_newline_empty_h1() -> None:
    assert_render("#", "<h1></h1>\n")


def test_no_end_newline_empty_h3() -> None:
    assert_render("###", "<h3></h3>\n")


def test_no_end_newline_inline_code_space() -> None:
    assert_render("` `", "<p><code> </code></p>\n")


def test_no_end_newline_empty_fence() -> None:
    assert_render("``````", "<pre><code></code></pre>\n")


def test_no_end_newline_empty_unordered_item() -> None:
    assert_render("-", "<ul>\n<li></li>\n</ul>\n")


def test_no_end_newline_empty_ordered_item() -> None:
    assert_render("1.", "<ol>\n<li></li>\n</ol>\n")


def test_no_end_newline_empty_blockquote() -> None:
    assert_render(">", "<blockquote></blockquote>\n")


def test_no_end_newline_horizontal_rule() -> None:
    assert_render("---", "<hr />\n")


def test_no_end_newline_html_block() -> None:
    assert_render("<h1></h1>", "<h1></h1>")


def test_no_end_newline_paragraph() -> None:
    assert_render("p", "<p>p</p>\n")


def test_no_end_newline_reference_definition() -> None:
    assert_render("[reference]: /url", "")


def test_no_end_newline_indented_code() -> None:
    assert_render(
        "    indented code block",
        "<pre><code>indented code block\n</code></pre>\n",
    )


def test_no_end_newline_blockquote_after_text() -> None:
    assert_render(
        "> test\n>",
        "<blockquote>\n<p>test</p>\n</blockquote>\n",
    )
