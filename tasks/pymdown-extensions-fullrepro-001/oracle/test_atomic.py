"""Atomic tests for PyMdown Extensions public behavior."""
from __future__ import annotations

import importlib
import markdown
import pytest
import warnings

from conftest import PIXEL_PNG_BYTES, render_markdown

def test_slugify_lower_percent_encoding_callback():
    from pymdownx import slugs

    slug = slugs.slugify(case="lower", percent_encode=True)("\u00c4 Header", "-")
    assert slug == "%C3%A4-header"

def test_slugify_case_modes_are_documented():
    from pymdownx import slugs

    assert slugs.slugify(case="none")("\u00c4 Header", "-") == "\u00c4-Header"
    assert slugs.slugify(case="lower-ascii")("\u00c4 Header", "-") == "Ä-header"
    assert slugs.slugify(case="fold")("Stra\u00dfe Header", "-") == "strasse-header"

def test_legacy_slug_helpers_match_documented_modes():
    from pymdownx import slugs

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert slugs.uslugify("\u00c4 Header", "-") == "\u00e4-header"
        assert slugs.uslugify_encoded("\u00c4 Header", "-") == "%C3%A4-header"
        assert slugs.uslugify_cased("\u00c4 Header", "-") == "\u00c4-Header"
        assert slugs.uslugify_cased_encoded("\u00c4 Header", "-") == "%C3%84-Header"

def test_blocks_validator_rejects_invalid_html_identifier():
    from pymdownx.blocks import block

    assert block.type_html_identifier("valid-name") == "valid-name"
    with pytest.raises(ValueError):
        block.type_html_identifier("3bad")

def test_emoji_indexes_return_documented_structure():
    import pymdownx.emoji as emoji

    for index_factory in (emoji.emojione, emoji.gemoji, emoji.twemoji):
        index = index_factory({}, None)
        assert set(index) == {"name", "emoji", "aliases"}
        assert isinstance(index["name"], str)
        assert ":smile:" in index["emoji"]
        assert isinstance(index["aliases"], dict)

def test_emoji_default_generators_honor_options_and_alt_text():
    import pymdownx.emoji as emoji

    png = emoji.to_png(
        "gemoji",
        ":smile:",
        None,
        "1f604",
        "ALT",
        "TITLE",
        "Smileys & Emotion",
        {"classes": "emoji", "attributes": {"data-kind": "face"}},
        None,
    )
    assert png.tag == "img"
    assert png.attrib["class"] == "emoji"
    assert png.attrib["alt"] == "ALT"
    assert png.attrib["title"] == "TITLE"
    assert png.attrib["data-kind"] == "face"
    assert png.attrib["src"].endswith("/1f604.png")

    sprite = emoji.to_svg_sprite(
        "twemoji",
        ":smile:",
        None,
        "1f604",
        "ALT",
        None,
        "Smileys & Emotion",
        {"classes": "emoji", "image_path": "/sprites.svg"},
        None,
    )
    assert sprite.tag == "svg"
    assert sprite.attrib["class"] == "emoji"
    assert sprite.find("description").text == "ALT"
    assert sprite.find("use").attrib["xlink:href"] == "/sprites.svg#emoji-1f604"

def test_emoji_non_strict_unknown_shortname_remains_literal():
    html = render_markdown(":not_a_real_emoji_name:", ["pymdownx.emoji"])
    assert ":not_a_real_emoji_name:" in html

def test_superfences_public_div_formatter_escapes_source():
    import pymdownx.superfences as superfences

    html = superfences.fence_div_format(
        "<tag>",
        "diagram",
        "mermaid",
        {},
        None,
        classes=["extra"],
        id_value="graph",
        attrs={"data-kind": "flow"},
    )
    assert html.startswith("<div ")
    assert 'id="graph"' in html
    assert 'class="mermaid extra"' in html
    assert 'data-kind="flow"' in html
    assert html.endswith("&lt;tag&gt;</div>")

def test_superfences_public_code_formatter_escapes_source_and_attrs():
    import pymdownx.superfences as superfences

    html = superfences.fence_code_format(
        "<tag>",
        "python",
        "highlight",
        {},
        None,
        classes=["extra"],
        id_value="sample",
        attrs={"data-kind": "demo"},
    )
    assert html.startswith("<pre ")
    assert 'id="sample"' in html
    assert 'class="highlight extra"' in html
    assert 'data-kind="demo"' in html
    assert "<code>&lt;tag&gt;</code>" in html

def test_superfences_highlight_validator_separates_options_and_attrs():
    import pymdownx.superfences as superfences

    md = markdown.Markdown(
        extensions=["pymdownx.highlight", "pymdownx.superfences"],
        extension_configs={"pymdownx.highlight": {"use_pygments": True}},
    )
    md.convert("```python\nprint(1)\n```")
    options = {}
    attrs = {}
    accepted = superfences.highlight_validator(
        "python",
        {"linenums": "1 2", "hl_lines": "1 3", "data-kind": "demo", "bad": "value"},
        options,
        attrs,
        md,
    )
    assert accepted is True
    assert options == {"linenums": "1 2", "hl_lines": "1 3"}
    assert attrs == {"data-kind": "demo", "bad": "value"}

def test_arithmatex_inline_formatter_generic_output():
    import pymdownx.arithmatex as arithmatex

    formatter = arithmatex.arithmatex_inline_format(mode="generic")
    element = formatter("x^2", "math", "arithmatex", None)
    assert element.tag == "span"
    assert element.attrib["class"] == "arithmatex"
    assert r"\(x^2\)" in element.text

def test_arithmatex_fenced_formatter_generic_output():
    import pymdownx.arithmatex as arithmatex

    formatter = arithmatex.arithmatex_fenced_format(mode="generic")
    html = formatter("x^2", "math", "arithmatex", {}, None, classes=[], id_value="", attrs={})
    assert html.startswith('<div class="arithmatex">')
    assert "x^2" in html
    assert r"\[" in html and r"\]" in html

def test_arithmatex_legacy_mathjax_formatter_remains_callable():
    import pymdownx.arithmatex as arithmatex

    with pytest.warns(DeprecationWarning):
        html = arithmatex.fence_mathjax_format("x^2", "math", "arithmatex", {}, None)
    assert 'class="arithmatex"' in html
    assert 'type="math/tex; mode=display"' in html
    assert "x^2" in html

def test_snippets_missing_file_raises_when_check_paths_enabled(tmp_path):
    from pymdownx.snippets import SnippetMissingError

    md = markdown.Markdown(
        extensions=["pymdownx.snippets"],
        extension_configs={"pymdownx.snippets": {"base_path": [str(tmp_path)], "check_paths": True}},
    )
    with pytest.raises(SnippetMissingError):
        md.convert('--8<-- "missing.md"')

def test_superfences_exception_from_formatter_propagates():
    from pymdownx.superfences import SuperFencesException

    def explode(source, language, class_name, options, md, **kwargs):
        raise SuperFencesException("boom")

    md = markdown.Markdown(
        extensions=["pymdownx.superfences"],
        extension_configs={"pymdownx.superfences": {"custom_fences": [{"name": "x", "class": "x", "format": explode}]}},
    )
    with pytest.raises(SuperFencesException):
        md.convert("```x\ncontent\n```")

def test_inlinehilite_exception_from_formatter_propagates():
    from pymdownx.inlinehilite import InlineHiliteException

    def explode(source, language, class_name, md):
        raise InlineHiliteException("boom")

    md = markdown.Markdown(
        extensions=["pymdownx.inlinehilite"],
        extension_configs={"pymdownx.inlinehilite": {"custom_inline": [{"name": "x", "class": "x", "format": explode}]}},
    )
    with pytest.raises(InlineHiliteException):
        md.convert("`#!x content`")

def test_emoji_strict_unknown_shortname_raises_runtime_error():
    md = markdown.Markdown(
        extensions=["pymdownx.emoji"],
        extension_configs={"pymdownx.emoji": {"strict": True}},
    )
    with pytest.raises(RuntimeError):
        md.convert(":not_a_real_emoji_name:")

def test_striphtml_removes_on_attributes_and_comments():
    html = render_markdown(
        '<span onclick="bad()" title="ok">x</span><!-- hidden -->',
        ["pymdownx.striphtml"],
    )
    assert "onclick" not in html
    assert "hidden" not in html
    assert 'title="ok"' in html

def test_highlight_non_pygments_javascript_shape():
    html = render_markdown(
        "    print('x')",
        ["pymdownx.highlight"],
        {"pymdownx.highlight": {"use_pygments": False, "default_lang": "python"}},
    )
    assert '<pre class="highlight"><code class="language-python">' in html
    assert "print('x')" in html

def test_arithmatex_generic_normalizes_dollar_math():
    html = render_markdown(
        "$x^2$",
        ["pymdownx.arithmatex"],
        {"pymdownx.arithmatex": {"generic": True}},
    )
    assert '<span class="arithmatex">' in html
    assert r"\(x^2\)" in html

def test_arithmatex_smart_dollar_avoids_currency_false_positive():
    html = render_markdown("I paid $2.00 and got $3.00 back.", ["pymdownx.arithmatex"])
    assert "math/tex" not in html
    assert "$2.00" in html

def test_tasklist_custom_clickable_checkbox_shape():
    html = render_markdown(
        "- [x] done",
        ["pymdownx.tasklist"],
        {"pymdownx.tasklist": {"custom_checkbox": True, "clickable_checkbox": True}},
    )
    assert 'class="task-list"' in html
    assert 'class="task-list-control"' in html
    assert 'class="task-list-indicator"' in html
    assert "disabled" not in html
    assert "checked" in html

def test_blocks_invalid_option_leaves_source_literal():
    html = render_markdown(
        "/// html | div\n    unknown: value\n\ncontent\n///",
        ["pymdownx.blocks.html"],
    )
    assert "/// html | div" in html
    assert "unknown: value" in html

def test_legacy_details_open_marker_renders_details_open():
    html = render_markdown(
        '???+ note "Title"\n    Body',
        ["pymdownx.details"],
    )
    assert '<details class="note" open="open">' in html
    assert "<summary>Title</summary>" in html

def test_caret_and_tilde_disabled_features_remain_literal():
    caret = render_markdown("^^insert^^ and ^sup^", ["pymdownx.caret"], {"pymdownx.caret": {"insert": False, "superscript": False}})
    tilde = render_markdown("~~delete~~ and ~sub~", ["pymdownx.tilde"], {"pymdownx.tilde": {"delete": False, "subscript": False}})
    assert "^^insert^^" in caret
    assert "^sup^" in caret
    assert "~~delete~~" in tilde
    assert "~sub~" in tilde

def test_generated_html_does_not_include_external_css_for_tasklist():
    html = render_markdown("- [ ] item", ["pymdownx.tasklist"])
    assert "<style" not in html
    assert "task-list" in html

def test_striphtml_does_not_sanitize_tag_names_or_text_content():
    html = render_markdown(
        '<script type="text/plain">safe text</script>',
        ["pymdownx.striphtml"],
    )
    assert "<script" in html
    assert "safe text" in html

def test_magiclink_does_not_verify_remote_repository_existence():
    html = render_markdown(
        "@no-such-user/no-such-repo",
        ["pymdownx.magiclink"],
        {"pymdownx.magiclink": {"repo_url_shorthand": True}},
    )
    assert 'href="https://github.com/no-such-user/no-such-repo"' in html
    assert "magiclink-repository" in html

def test_smartsymbols_disabled_family_remains_literal():
    html = render_markdown("(tm) (c)", ["pymdownx.smartsymbols"], {"pymdownx.smartsymbols": {"trademark": False}})
    assert "(tm)" in html
    assert "&copy;" in html

def test_progressbar_level_class_uses_configured_increment():
    html = render_markdown("[=35%]", ["pymdownx.progressbar"], {"pymdownx.progressbar": {"progress_increment": 10}})
    assert "progress" in html
    assert "progress-30plus" in html

def test_keys_custom_separator_and_class():
    html = render_markdown("++ctrl+alt+delete++", ["pymdownx.keys"], {"pymdownx.keys": {"separator": "|", "class": "kbd"}})
    assert html.count("<kbd") >= 3
    assert 'class="kbd"' in html
    assert "<span>|</span>" in html

def test_quotes_callout_uses_blockquote_public_syntax():
    html = render_markdown("> [!NOTE]\n> body", ["pymdownx.quotes"], {"pymdownx.quotes": {"callouts": True}})
    assert "admonition" in html or "quote" in html
    assert "body" in html

def test_slugify_strips_html_and_uses_custom_separator():
    from pymdownx import slugs

    slug = slugs.slugify(case="lower")("<b>My Header!</b>", "_")
    assert slug == "my_header"


def test_blocks_validators_accept_precise_public_types():
    from pymdownx.blocks import block

    assert block.type_boolean(True) is True
    assert block.type_boolean(False) is False
    assert block.type_integer(7.0) == 7
    assert block.type_number(2.5) == 2.5
    assert block.type_html_classes("alpha beta-2") == ["alpha", "beta-2"]


def test_blocks_validator_combinators_convert_or_reject_values():
    from pymdownx.blocks import block

    assert block.type_string_in(["red", "blue"])("RED") == "red"
    assert block.type_string_delimiter(",")("a, b,,c") == ["a", "b", "c"]
    assert block.type_ternary(None) is None
    assert block.type_ternary(True) is True
    with pytest.raises(ValueError):
        block.type_ranged_integer(2, 5)(6)


def test_smartsymbols_replaces_arrows_and_ordinals():
    html = render_markdown("A --> B and 21st", ["pymdownx.smartsymbols"])
    assert "&rarr;" in html
    assert "21<sup>st</sup>" in html


def test_critic_accept_and_reject_modes_select_different_text():
    accepted = render_markdown(
        "{++add++}{--drop--}{~~old~>new~~}",
        ["pymdownx.critic"],
        {"pymdownx.critic": {"mode": "accept"}},
    )
    rejected = render_markdown(
        "{++add++}{--drop--}{~~old~>new~~}",
        ["pymdownx.critic"],
        {"pymdownx.critic": {"mode": "reject"}},
    )
    assert "addnew" in accepted
    assert "dropold" in rejected


INSTALLABLE_EXTENSIONS = (
    "pymdownx.arithmatex",
    "pymdownx.b64",
    "pymdownx.betterem",
    "pymdownx.blocks.admonition",
    "pymdownx.blocks.caption",
    "pymdownx.blocks.definition",
    "pymdownx.blocks.details",
    "pymdownx.blocks.html",
    "pymdownx.blocks.tab",
    "pymdownx.caret",
    "pymdownx.critic",
    "pymdownx.details",
    "pymdownx.emoji",
    "pymdownx.escapeall",
    "pymdownx.extra",
    "pymdownx.fancylists",
    "pymdownx.highlight",
    "pymdownx.inlinehilite",
    "pymdownx.keys",
    "pymdownx.magiclink",
    "pymdownx.mark",
    "pymdownx.pathconverter",
    "pymdownx.progressbar",
    "pymdownx.quotes",
    "pymdownx.saneheaders",
    "pymdownx.smartsymbols",
    "pymdownx.snippets",
    "pymdownx.striphtml",
    "pymdownx.superfences",
    "pymdownx.tabbed",
    "pymdownx.tasklist",
    "pymdownx.tilde",
)


def test_installable_extension_modules_expose_make_extension():
    for name in INSTALLABLE_EXTENSIONS:
        module = importlib.import_module(name)
        assert isinstance(module.makeExtension(), markdown.extensions.Extension)


def test_installable_extension_strings_load_independently():
    for name in INSTALLABLE_EXTENSIONS:
        assert isinstance(markdown.Markdown(extensions=[name]), markdown.Markdown)


def test_b64_rewrites_allowed_local_png(tmp_path):
    png = tmp_path / "pixel.png"
    png.write_bytes(PIXEL_PNG_BYTES)
    html = render_markdown(
        "![pixel](pixel.png)",
        ["pymdownx.b64"],
        {"pymdownx.b64": {"base_path": str(tmp_path)}},
    )
    assert 'src="data:image/png;base64,' in html
    assert "pixel.png" not in html


def test_b64_leaves_disallowed_parent_path_unchanged(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "outside.png").write_bytes(b"not really png")
    html = render_markdown(
        "![outside](../outside.png)",
        ["pymdownx.b64"],
        {"pymdownx.b64": {"base_path": str(root), "restrict_path": True}},
    )
    assert "../outside.png" in html


def test_pathconverter_preserves_fragment_while_rewriting_path(tmp_path):
    base = tmp_path / "docs"
    out = tmp_path / "site"
    base.mkdir()
    out.mkdir()
    html = render_markdown(
        "[target](images/pic.png#section)",
        ["pymdownx.pathconverter"],
        {"pymdownx.pathconverter": {"base_path": str(base), "relative_path": str(out)}},
    )
    assert "#section" in html
    assert 'href="../docs/images/pic.png#section"' in html


def test_snippets_inserted_markdown_is_rendered(tmp_path):
    (tmp_path / "snippet.md").write_text("**strong**", encoding="utf-8")
    html = render_markdown(
        '--8<-- "snippet.md"',
        ["pymdownx.snippets"],
        {"pymdownx.snippets": {"base_path": [str(tmp_path)]}},
    )
    assert "<strong>strong</strong>" in html


def test_magiclink_shorthand_uses_configured_repo_context():
    html = render_markdown(
        "#7",
        ["pymdownx.magiclink", "pymdownx.saneheaders"],
        {"pymdownx.magiclink": {"repo_url_shorthand": True, "user": "docs-team", "repo": "guidepack"}},
    )
    assert 'href="https://github.com/docs-team/guidepack/issues/7"' in html
    assert "magiclink-issue" in html


def test_blocks_attrs_visible_on_outer_element():
    html = render_markdown(
        "/// html | div\n    attrs: {class: extra, id: sample}\n\ncontent\n///",
        ["pymdownx.blocks.html"],
    )
    assert '<div class="extra" id="sample">' in html
    assert "<p>content</p>" in html


def test_blocks_admonition_renders_title_and_markdown_content():
    html = render_markdown(
        "/// admonition | Remember\n\n**Body**\n///",
        ["pymdownx.blocks.admonition"],
    )
    assert 'class="admonition"' in html
    assert 'class="admonition-title">Remember' in html
    assert "<strong>Body</strong>" in html


def test_blocks_details_open_option_controls_outer_element():
    html = render_markdown(
        "/// details | More\n    open: true\n\nBody\n///",
        ["pymdownx.blocks.details"],
    )
    assert "<details" in html and 'open="open"' in html
    assert "<summary>More</summary>" in html


def test_legacy_tabbed_groups_consecutive_tabs():
    html = render_markdown(
        '=== "One"\n    A\n\n=== "Two"\n    B',
        ["pymdownx.tabbed"],
    )
    assert 'data-tabs="1:2"' in html
    assert html.count('type="radio"') == 2
    assert "One" in html and "Two" in html
