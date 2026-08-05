"""Integration tests for PyMdown Extensions public behavior."""
from __future__ import annotations

import importlib
import xml.etree.ElementTree as etree

import markdown
import pytest

from conftest import PIXEL_PNG_BYTES, render_markdown

@pytest.mark.depends_on("test_installable_extension_strings_load_independently")
def test_extra_bundle_enables_tables_and_footnotes():
    """Seam: config interaction between the extra bundle and bundled Markdown extensions."""

    html = render_markdown(
        "| A | B |\n| - | - |\n| 1 | 2 |\n\nText[^1]\n\n[^1]: footnote",
        ["pymdownx.extra"],
    )
    assert "<table>" in html
    assert 'class="footnote"' in html

@pytest.mark.depends_on(
    "test_installable_extension_strings_load_independently",
    "test_superfences_public_code_formatter_escapes_source_and_attrs",
)
def test_extra_routes_subextension_configuration():
    """CVI-2: bundled configuration reaches the SuperFences subextension."""

    html = render_markdown(
        "```python\nprint('x')\n```",
        ["pymdownx.extra"],
        {"pymdownx.extra": {"pymdownx.superfences": {"css_class": "codebox"}}},
    )
    assert 'class="codebox"' in html

@pytest.mark.depends_on(
    "test_installable_extension_strings_load_independently",
    "test_legacy_tabbed_groups_consecutive_tabs",
)
def test_markdown_instance_reset_clears_tab_group_counter():
    """CVI-3: lifecycle crossing where reset restarts block tab counters."""

    md = markdown.Markdown(extensions=["pymdownx.blocks.tab"])
    first = md.convert("/// tab | One\nA\n///\n\n/// tab | Two\nB\n///")
    md.reset()
    second = md.convert("/// tab | One\nA\n///\n\n/// tab | Two\nB\n///")
    assert '__tabbed_1_1' in first
    assert '__tabbed_1_1' in second
    assert '__tabbed_2_1' not in second

@pytest.mark.depends_on(
    "test_installable_extension_strings_load_independently",
    "test_blocks_validators_accept_precise_public_types",
)
def test_markdown_instance_reset_clears_caption_numbering():
    """CVI-3: lifecycle crossing where reset restarts caption numbering."""

    md = markdown.Markdown(extensions=["pymdownx.blocks.caption"])
    first = md.convert("![a](a.png)\n/// figure-caption\nA\n///")
    md.reset()
    second = md.convert("![b](b.png)\n/// figure-caption\nB\n///")
    assert "Figure 1." in first
    assert "Figure 1." in second
    assert "Figure 2." not in second

@pytest.mark.depends_on("test_magiclink_shorthand_uses_configured_repo_context")
def test_markdown_instance_reset_preserves_extension_configuration():
    """CVI-3: lifecycle crossing where reset preserves MagicLink configuration."""

    md = markdown.Markdown(
        extensions=["pymdownx.magiclink", "pymdownx.saneheaders"],
        extension_configs={"pymdownx.magiclink": {"repo_url_shorthand": True, "user": "docs-team", "repo": "guidepack"}},
    )
    assert "issues/1" in md.convert("#1")
    md.reset()
    assert "issues/2" in md.convert("#2")

@pytest.mark.depends_on("test_emoji_default_generators_honor_options_and_alt_text")
def test_emoji_generator_receives_alias_information():
    """CVI-9: protocol handoff from emoji index lookup into custom generator arguments."""

    import pymdownx.emoji as emoji

    calls = []

    def generator(index, shortname, alias, uc, alt, title, category, options, md):
        calls.append((index, shortname, alias, alt, title))
        return etree.Element("span", {"data-short": shortname, "data-alias": alias or ""})

    html = render_markdown(
        ":basketball_man:",
        ["pymdownx.emoji"],
        {
            "pymdownx.emoji": {
                "emoji_index": emoji.gemoji,
                "emoji_generator": generator,
                "alt": "short",
                "title": "short",
            }
        },
    )
    assert "data-short=\":bouncing_ball_man:\"" in html
    assert "data-alias=\":basketball_man:\"" in html
    assert calls[0][1] == ":bouncing_ball_man:"
    assert calls[0][2] == ":basketball_man:"


@pytest.mark.depends_on(
    "test_superfences_highlight_validator_separates_options_and_attrs",
    "test_superfences_public_code_formatter_escapes_source_and_attrs",
)
def test_superfences_custom_fence_receives_options_and_attrs():
    """CVI-9: protocol handoff from SuperFences option parsing into custom callbacks."""

    calls = []

    def validator(language, inputs, options, attrs, md):
        options["mode"] = inputs["mode"]
        attrs["data-seen"] = "yes"
        return True

    def formatter(source, language, class_name, options, md, **kwargs):
        attrs = kwargs.get("attrs", {})
        calls.append((language, class_name, options["mode"], attrs))
        attr_text = "".join(f' {key}="{value}"' for key, value in sorted(attrs.items()))
        return f'<section class="{class_name}"{attr_text}>{source}</section>'

    html = render_markdown(
        '```demo {mode="fast"}\ncontent\n```',
        ["markdown.extensions.attr_list", "pymdownx.superfences"],
        {"pymdownx.superfences": {"custom_fences": [{"name": "demo", "class": "diagram", "format": formatter, "validator": validator}]}},
    )
    assert '<section class="diagram" data-seen="yes">content</section>' in html
    assert calls == [("demo", "diagram", "fast", {"data-seen": "yes"})]

@pytest.mark.depends_on("test_inlinehilite_exception_from_formatter_propagates")
def test_inlinehilite_custom_inline_receives_language_and_class():
    """CVI-9: protocol handoff from InlineHilite parsing into custom callbacks."""

    calls = []

    def formatter(source, language, class_name, md):
        calls.append((source, language, class_name))
        return f'<span class="{class_name}" data-language="{language}">{source}</span>'

    html = render_markdown(
        "`#!math x^2`",
        ["pymdownx.inlinehilite"],
        {"pymdownx.inlinehilite": {"custom_inline": [{"name": "math", "class": "arithmatex", "format": formatter}]}},
    )
    assert '<span class="arithmatex" data-language="math">x^2</span>' in html
    assert calls == [("x^2", "math", "arithmatex")]


@pytest.mark.depends_on(
    "test_installable_extension_strings_load_independently",
    "test_superfences_public_code_formatter_escapes_source_and_attrs",
)
def test_registration_replacement_with_superfences_and_fenced_code_is_single_output():
    """CVI-1: state consistency between replacement registration and rendered code output."""

    html = render_markdown(
        "```\ncode\n```",
        ["pymdownx.superfences", "markdown.extensions.fenced_code"],
    )
    assert html.count("<pre") == 1
    assert "code" in html

@pytest.mark.depends_on(
    "test_legacy_tabbed_groups_consecutive_tabs",
    "test_blocks_details_open_option_controls_outer_element",
)
def test_legacy_tabbed_and_blocks_tab_share_output_classes():
    """CVI-8: state consistency between legacy tabbed and Blocks tab projections."""

    legacy = render_markdown('=== "One"\n    content', ["pymdownx.tabbed"])
    modern = render_markdown("/// tab | One\ncontent\n///", ["pymdownx.blocks.tab"])
    assert "tabbed-set" in legacy
    assert "tabbed-set" in modern
    assert "<input" in legacy and "<label" in legacy and "tabbed-content" in legacy
    assert "<input" in modern and "<label" in modern and "tabbed-content" in modern


@pytest.mark.depends_on("test_magiclink_shorthand_uses_configured_repo_context")
def test_saneheaders_preserves_issue_like_line_for_magiclink():
    """CVI-6: config interaction between SaneHeaders and MagicLink line parsing."""

    html = render_markdown(
        "#1",
        ["pymdownx.saneheaders", "pymdownx.magiclink"],
        {"pymdownx.magiclink": {"repo_url_shorthand": True, "user": "docs-team", "repo": "guidepack"}},
    )
    assert "<h1>" not in html
    assert "magiclink-issue" in html

@pytest.mark.depends_on(
    "test_snippets_inserted_markdown_is_rendered",
    "test_magiclink_shorthand_uses_configured_repo_context",
    "test_snippets_missing_file_raises_when_check_paths_enabled",
    "test_emoji_default_generators_honor_options_and_alt_text",
    "test_tasklist_custom_clickable_checkbox_shape",
)
def test_representative_documentation_workflow_combines_public_projections(tmp_path):
    """Seam: state consistency across snippets, links, emoji, tasks, tabs, inline code, and TOC."""

    ref = tmp_path / "ref.md"
    ref.write_text("[ref]: https://example.com\n", encoding="utf-8")
    html = render_markdown(
        """
# Guide

--8<-- "ref.md"

See #3 and :smile:.

- [x] done

/// tab | Python
`#!py3 print("ok")`
///
""",
        [
            "markdown.extensions.toc",
            "pymdownx.snippets",
            "pymdownx.magiclink",
            "pymdownx.emoji",
            "pymdownx.tasklist",
            "pymdownx.blocks.tab",
            "pymdownx.inlinehilite",
        ],
        {
            "pymdownx.snippets": {"base_path": [str(tmp_path)]},
            "pymdownx.magiclink": {"repo_url_shorthand": True, "user": "docs-team", "repo": "guidepack"},
            "pymdownx.emoji": {"emoji_generator": importlib.import_module("pymdownx.emoji").to_alt},
        },
    )
    assert 'id="guide"' in html
    assert 'href="https://github.com/docs-team/guidepack/issues/3"' in html
    assert "\U0001f604" in html
    assert "task-list-item" in html
    assert "tabbed-set" in html

@pytest.mark.depends_on(
    "test_snippets_inserted_markdown_is_rendered",
    "test_snippets_missing_file_raises_when_check_paths_enabled",
)
def test_representative_documentation_workflow_missing_snippet_raises(tmp_path):
    """Seam: error propagation from Snippets lookup through Markdown conversion."""

    from pymdownx.snippets import SnippetMissingError

    (tmp_path / "present.md").write_text("**present**", encoding="utf-8")
    md = markdown.Markdown(
        extensions=["pymdownx.snippets"],
        extension_configs={"pymdownx.snippets": {"base_path": [str(tmp_path)], "check_paths": True}},
    )
    assert "<strong>present</strong>" in md.convert('--8<-- "present.md"')
    md.reset()
    with pytest.raises(SnippetMissingError):
        md.convert('--8<-- "missing.md"')

@pytest.mark.depends_on(
    "test_arithmatex_inline_formatter_generic_output",
    "test_inlinehilite_exception_from_formatter_propagates",
    "test_superfences_public_code_formatter_escapes_source_and_attrs",
)
def test_representative_math_workflow_combines_inlinehilite_and_superfences():
    """CVI-9: protocol handoff across Arithmatex, InlineHilite, and SuperFences callbacks."""

    import pymdownx.arithmatex as arithmatex

    html = render_markdown(
        "`#!math x^2`\n\n```math\ny^2\n```",
        ["pymdownx.inlinehilite", "pymdownx.superfences"],
        {
            "pymdownx.inlinehilite": {
                "custom_inline": [{"name": "math", "class": "arithmatex", "format": arithmatex.arithmatex_inline_format(mode="generic")}]
            },
            "pymdownx.superfences": {
                "custom_fences": [{"name": "math", "class": "arithmatex", "format": arithmatex.arithmatex_fenced_format(mode="generic")}]
            },
        },
    )
    assert html.count('class="arithmatex"') >= 2
    assert "x^2" in html and "y^2" in html

@pytest.mark.depends_on(
    "test_highlight_non_pygments_javascript_shape",
    "test_superfences_public_code_formatter_escapes_source_and_attrs",
)
def test_highlight_configuration_shared_with_superfences_non_pygments():
    """CVI-5: config interaction between Highlight settings and SuperFences output."""

    html = render_markdown(
        "```python\nprint(1)\n```",
        ["pymdownx.highlight", "pymdownx.superfences"],
        {"pymdownx.highlight": {"use_pygments": False, "css_class": "codebox", "language_prefix": "lang-"}},
    )
    assert '<pre class="codebox"><code class="lang-python">' in html

@pytest.mark.depends_on("test_highlight_non_pygments_javascript_shape")
def test_inline_plain_text_default_language_uses_highlight_class():
    """CVI-5: config interaction between Highlight settings and InlineHilite output."""

    html = render_markdown(
        "`plain`",
        ["pymdownx.highlight", "pymdownx.inlinehilite"],
        {
            "pymdownx.highlight": {"use_pygments": False, "css_class": "hi"},
            "pymdownx.inlinehilite": {"style_plain_text": "text"},
        },
    )
    assert "<code" in html and "plain</code>" in html
    assert "hi" in html and "language-text" in html

@pytest.mark.depends_on("test_snippets_missing_file_raises_when_check_paths_enabled")
def test_snippets_line_selection_flows_into_markdown_rendering(tmp_path):
    """Seam: protocol handoff from snippet line selection into Markdown rendering."""

    source = tmp_path / "source.md"
    source.write_text("alpha\nbeta\ngamma\ndelta\n", encoding="utf-8")
    html = render_markdown(
        '--8<-- "source.md:2:3"',
        ["pymdownx.snippets"],
        {"pymdownx.snippets": {"base_path": [str(tmp_path)]}},
    )
    assert "beta" in html
    assert "gamma" in html
    assert "alpha" not in html
    assert "delta" not in html


@pytest.mark.depends_on("test_highlight_non_pygments_javascript_shape")
def test_superfences_uses_highlight_code_attr_on_pre_configuration():
    """Seam: config interaction between Highlight and SuperFences non-Pygments output."""

    html = render_markdown(
        "```python\nprint(2)\n```",
        ["pymdownx.superfences", "pymdownx.highlight"],
        {"pymdownx.highlight": {"use_pygments": False, "code_attr_on_pre": True, "css_class": "box"}},
    )
    assert '<pre class="language-python box">' in html
    assert "<code>print(2)</code>" in html


@pytest.mark.depends_on("test_superfences_public_code_formatter_escapes_source_and_attrs")
def test_superfences_nested_blockquote_preserves_quote_and_code_views():
    """Seam: state consistency between blockquote parsing and nested SuperFences output."""

    html = render_markdown("> ```\n> quoted\n> ```", ["pymdownx.superfences"])
    assert "<blockquote>" in html
    assert "<pre" in html
    assert "quoted" in html


@pytest.mark.depends_on("test_tasklist_custom_clickable_checkbox_shape")
def test_tasklist_and_smartsymbols_transform_same_list_item():
    """CVI-4: downstream inline replacements remain active inside task-list item content."""

    html = render_markdown("- [x] ship --> docs", ["pymdownx.tasklist", "pymdownx.smartsymbols"])
    assert "task-list-item" in html
    assert "checked" in html
    assert "&rarr;" in html


@pytest.mark.depends_on(
    "test_keys_custom_separator_and_class",
    "test_quotes_callout_uses_blockquote_public_syntax",
)
def test_keys_and_quotes_extensions_preserve_inline_keyboard_content_in_callout():
    html = render_markdown(
        "> [!TIP]\n> Press ++ctrl+s++ to save.",
        ["pymdownx.quotes", "pymdownx.keys"],
        {"pymdownx.keys": {"separator": "+"}},
    )

    assert "admonition" in html or "quote" in html
    assert "key-control" in html and "key-s" in html
    assert "save" in html


@pytest.mark.depends_on(
    "test_critic_accept_and_reject_modes_select_different_text",
    "test_smartsymbols_replaces_arrows_and_ordinals",
)
def test_critic_and_smartsymbols_compose_without_losing_inline_replacements():
    source = "{++A --> B++} {--21st--}"
    accepted = render_markdown(
        source,
        ["pymdownx.critic", "pymdownx.smartsymbols"],
        {"pymdownx.critic": {"mode": "accept"}},
    )
    rejected = render_markdown(
        source,
        ["pymdownx.critic", "pymdownx.smartsymbols"],
        {"pymdownx.critic": {"mode": "reject"}},
    )

    assert "A" in accepted and "&rarr;" in accepted
    assert "21<sup>st</sup>" not in accepted
    assert "A" not in rejected
    assert "21<sup>st</sup>" in rejected


@pytest.mark.depends_on(
    "test_b64_rewrites_allowed_local_png",
    "test_pathconverter_preserves_fragment_while_rewriting_path",
)
def test_local_asset_rewriters_preserve_semantic_links_and_embed_allowed_images(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "pixel.png").write_bytes(PIXEL_PNG_BYTES)
    (docs / "images").mkdir()
    (docs / "images" / "pic.png").write_bytes(PIXEL_PNG_BYTES)
    html = render_markdown(
        "![pixel](pixel.png)\n\n[diagram](images/pic.png#section)",
        ["pymdownx.b64", "pymdownx.pathconverter"],
        {
            "pymdownx.b64": {"base_path": str(docs)},
            "pymdownx.pathconverter": {
                "base_path": str(docs),
                "relative_path": str(tmp_path / "site"),
            },
        },
    )

    assert "data:image/png;base64," in html
    assert "#section" in html


@pytest.mark.depends_on(
    "test_blocks_attrs_visible_on_outer_element",
    "test_blocks_admonition_renders_title_and_markdown_content",
)
def test_blocks_attribute_and_admonition_extensions_share_nested_markdown_state():
    html = render_markdown(
        "/// admonition | Note\n    attrs: {class: highlighted}\n\n**body**\n///",
        ["pymdownx.blocks.admonition"],
    )

    assert 'class="admonition-title">Note' in html
    assert "<strong>body</strong>" in html
    assert "highlighted" in html


@pytest.mark.depends_on(
    "test_progressbar_level_class_uses_configured_increment",
    "test_tasklist_custom_clickable_checkbox_shape",
)
def test_progressbar_and_tasklist_extensions_keep_distinct_block_projections():
    html = render_markdown(
        "[=35%]\n\n- [x] shipped",
        ["pymdownx.progressbar", "pymdownx.tasklist"],
        {"pymdownx.progressbar": {"progress_increment": 10}, "pymdownx.tasklist": {"custom_checkbox": True}},
    )

    assert "progress-30plus" in html
    assert "task-list-item" in html
    assert "checked" in html
