# Spec2Repo oracle - atomic tests for babel-fullrepro-001

from __future__ import annotations

import copy
import io
from pathlib import Path

import pytest

from babel.messages import Catalog, Message, TranslationError
from babel.messages import catalog, extract, pofile
from babel.messages.catalog import DEFAULT_HEADER, PYTHON_FORMAT
from babel.messages.extract import (
    DEFAULT_KEYWORDS,
    GROUP_NAME,
    default_directory_filter,
    extract as extract_dispatch,
    extract_from_dir,
    extract_from_file,
    extract_javascript,
    extract_nothing,
    extract_python,
    parse_template_string,
)
from babel.messages.frontend import (
    CommandLineInterface,
    ConfigurationError,
    OptionError,
    listify_value,
    parse_keywords,
    parse_mapping,
    parse_mapping_cfg,
)
from babel.messages.mofile import read_mo, write_mo
from babel.messages.pofile import (
    PoFileError,
    denormalize,
    escape,
    generate_po,
    normalize,
    read_po,
    unescape,
    write_po,
)
from babel.messages.setuptools_frontend import check_message_extractors


def test_message_percent_format_flag_is_added():
    """Verifies: BABEL-CAT-003."""
    msg = Message("Hello %(name)s")
    assert msg.python_format is True
    assert "python-format" in msg.flags

def test_message_brace_format_flag_is_added():
    """Verifies: BABEL-CAT-004."""
    msg = Message("Hello {name}")
    assert msg.python_brace_format is True
    assert "python-brace-format" in msg.flags

def test_message_non_format_flags_are_absent():
    """Verifies: BABEL-CAT-003, BABEL-CAT-004."""
    msg = Message("plain text")
    assert msg.python_format is False
    assert msg.python_brace_format is False
    assert "python-format" not in msg.flags
    assert "python-brace-format" not in msg.flags

def test_plural_message_gets_empty_plural_translation_tuple():
    """Verifies: BABEL-CAT-002."""
    msg = Message(("file", "files"))
    assert msg.pluralizable is True
    assert msg.string == ("", "")

def test_message_clone_is_independent_copy():
    """Verifies: BABEL-CAT-006."""
    msg = Message("hello", "bonjour", locations=[("app.py", 1)], flags=["fuzzy"])
    clone = msg.clone()
    clone.locations.append(("other.py", 2))
    clone.flags.add("reviewed")
    assert msg.locations == [("app.py", 1)]
    assert "reviewed" not in msg.flags
    assert clone.is_identical(msg) is False

def test_message_is_identical_rejects_non_message():
    """Verifies: BABEL-CAT-006."""
    with pytest.raises(AssertionError):
        Message("x").is_identical(object())

def test_message_check_returns_translation_errors_for_bad_plural():
    """Verifies: BABEL-CAT-007."""
    catalog = Catalog()
    msg = Message(("file", "files"), ("fichier",))
    errors = msg.check(catalog)
    assert errors
    assert all(isinstance(error, TranslationError) for error in errors)

def test_setup_message_extractors_validation_rejects_non_mapping():
    """Verifies: BABEL-CMD-018."""
    with pytest.raises(Exception):
        check_message_extractors(None, "message_extractors", ["not", "a", "mapping"])
    check_message_extractors(None, "message_extractors", {"src": [("**.py", "python")]})

def test_catalog_accepts_domain_and_metadata_without_locale():
    """Verifies: BABEL-CAT-008."""
    catalog = Catalog(domain="messages", project="Demo", version="1.0", charset="latin-1")
    assert catalog.domain == "messages"
    assert catalog.project == "Demo"
    assert catalog.version == "1.0"
    assert catalog.charset == "latin-1"

def test_catalog_rejects_invalid_locale_type():
    """Verifies: BABEL-CAT-009."""
    with pytest.raises(TypeError):
        Catalog(locale=object())

def test_catalog_add_returns_and_stores_message():
    """Verifies: BABEL-CAT-010, BABEL-CAT-011."""
    catalog = Catalog()
    msg = catalog.add("Hello", "Bonjour", locations=[("app.py", 3)])
    assert catalog.get("Hello") is msg
    assert "Hello" in catalog
    assert len(catalog) == 1

def test_catalog_delete_missing_id_is_noop():
    """Verifies: BABEL-CAT-011."""
    catalog = Catalog()
    catalog.add("Hello")
    catalog.delete("Missing")
    assert len(catalog) == 1
    catalog.delete("Hello")
    assert catalog.get("Hello") is None

def test_catalog_context_keys_are_distinct():
    """Verifies: BABEL-CAT-011."""
    catalog = Catalog()
    catalog.add("Open", "Open", context="adjective")
    catalog.add("Open", "Ouvrir", context="verb")
    assert catalog.get("Open", context="adjective").string == "Open"
    assert catalog.get("Open", context="verb").string == "Ouvrir"

def test_catalog_iteration_starts_with_header_message():
    """Verifies: BABEL-CAT-012."""
    catalog = Catalog(project="Demo", version="1.0", fuzzy=False)
    catalog.add("Hello")
    messages = list(catalog)
    assert messages[0].id == ""
    assert "Project-Id-Version: Demo 1.0" in messages[0].string
    assert messages[1].id == "Hello"

def test_catalog_assignment_merges_message_metadata_without_duplicates():
    """Verifies: BABEL-CAT-013."""
    catalog = Catalog()
    catalog["Hello"] = Message("Hello", locations=[("a.py", 1)], flags=["fuzzy"])
    catalog["Hello"] = Message("Hello", locations=[("a.py", 1), ("b.py", 2)], auto_comments=["note"])
    msg = catalog["Hello"]
    assert msg.locations == [("a.py", 1), ("b.py", 2)]
    assert msg.auto_comments == ["note"]
    assert "fuzzy" in msg.flags

def test_catalog_empty_message_updates_header_state():
    """Verifies: BABEL-CAT-014."""
    catalog = Catalog(fuzzy=False)
    header = Message("", "Project-Id-Version: Demo 2.0\n", flags=["fuzzy"], user_comments=["Custom"])
    catalog[""] = header
    assert catalog.project == "Demo"
    assert catalog.version == "2.0"
    assert catalog.fuzzy is True
    assert "Custom" in catalog.header_comment

def test_catalog_plural_forms_follow_locale():
    """Verifies: BABEL-CAT-008."""
    catalog = Catalog()
    assert catalog.num_plurals == 2
    assert catalog.plural_forms == "nplurals=2; plural=(n != 1);"

def test_catalog_mime_headers_include_default_plural_free_metadata():
    """Verifies: BABEL-CAT-008."""
    catalog = Catalog(project="Demo", version="1.0", fuzzy=False)
    headers = dict(catalog.mime_headers)
    assert headers["Project-Id-Version"] == "Demo 1.0"
    assert headers["Content-Type"] == "text/plain; charset=utf-8"

def test_catalog_is_identical_requires_catalog():
    """Verifies: BABEL-CAT-006."""
    with pytest.raises(AssertionError):
        Catalog().is_identical(object())

def test_escape_and_unescape_po_string_round_trip():
    """Verifies: BABEL-FILE-006."""
    original = 'Say:\n  "hello"\tthere\r\n'
    assert unescape(escape(original)) == original

def test_normalize_and_denormalize_multiline_text():
    """Verifies: BABEL-FILE-006."""
    original = "Line one\nLine two\n"
    normalized = normalize(original, width=None)
    assert normalized.startswith('""')
    assert denormalize(normalized) == original

def test_normalize_width_zero_disables_wrapping():
    """Verifies: BABEL-FILE-006."""
    text = "a long message that stays together"
    assert normalize(text, width=0) == '"a long message that stays together"'

def test_extract_unknown_method_raises_value_error():
    """Verifies: BABEL-EXT-002."""
    with pytest.raises(ValueError):
        list(extract_dispatch("missing_method", io.BytesIO(b"_('x')")))

def test_extract_callable_method_is_used():
    """Verifies: BABEL-EXT-001, BABEL-EXT-002."""
    def custom(fileobj, keywords, comment_tags, options):
        return [(7, "gettext", "Hello", ["note"])]

    assert list(extract_dispatch(custom, io.BytesIO(b""), {"gettext": None})) == [(7, "Hello", ["note"], None)]

def test_extract_python_finds_gettext_call():
    """Verifies: BABEL-EXT-005."""
    source = io.BytesIO(b"print(_('Hello'))\n")
    assert list(extract_python(source, {"_": None}, [], {})) == [(1, "_", "Hello", [])]

def test_extract_python_combines_adjacent_string_literals():
    """Verifies: BABEL-EXT-005."""
    source = io.BytesIO(b"gettext('Hello ' 'world')\n")
    assert list(extract_dispatch("python", source, {"gettext": None})) == [(1, "Hello world", [], None)]

def test_extract_python_handles_plural_keyword_spec():
    """Verifies: BABEL-EXT-005, BABEL-EXT-008."""
    source = io.BytesIO(b"ngettext('file', 'files', count)\n")
    assert list(extract_dispatch("python", source, parse_keywords(["ngettext:1,2"]))) == [(1, ("file", "files"), [], None)]

def test_extract_python_handles_context_keyword_spec():
    """Verifies: BABEL-EXT-005, BABEL-EXT-008."""
    source = io.BytesIO(b"pgettext('button', 'Open')\n")
    assert list(extract_dispatch("python", source, parse_keywords(["pgettext:1c,2"]))) == [(1, "Open", [], "button")]

def test_extract_python_collects_translator_comments():
    """Verifies: BABEL-EXT-005."""
    source = io.BytesIO(b"# NOTE: Used on homepage\n_('Welcome')\n")
    assert list(extract_dispatch("python", source, {"_": None}, ["NOTE:"])) == [(2, "Welcome", ["NOTE: Used on homepage"], None)]

def test_extract_strips_comment_tags_when_requested():
    """Verifies: BABEL-EXT-005."""
    source = io.BytesIO(b"# NOTE: Used on homepage\n_('Welcome')\n")
    assert list(extract_dispatch("python", source, {"_": None}, ["NOTE:"], strip_comment_tags=True)) == [(2, "Welcome", ["Used on homepage"], None)]

def test_extract_python_respects_source_encoding_comment():
    """Verifies: BABEL-EXT-005."""
    source = "# coding: latin-1\n_('caf\xe9')\n".encode("latin-1")
    assert list(extract_dispatch("python", io.BytesIO(source), {"_": None})) == [(2, "café", [], None)]

def test_extract_javascript_finds_gettext_call():
    """Verifies: BABEL-EXT-006."""
    source = io.BytesIO(b"gettext('Hello');\n")
    assert list(extract_javascript(source, {"gettext": None}, [], {})) == [(1, "gettext", "Hello", [])]

def test_extract_javascript_collects_line_comment():
    """Verifies: BABEL-EXT-006."""
    source = io.BytesIO(b"// NOTE: Button label\ngettext('Open');\n")
    assert list(extract_dispatch("javascript", source, {"gettext": None}, ["NOTE:"])) == [(2, "Open", ["NOTE: Button label"], None)]

def test_extract_javascript_template_string_tag():
    """Verifies: BABEL-EXT-006."""
    source = io.BytesIO(b"gettext`Hello`;\n")
    assert list(extract_dispatch("javascript", source, {"gettext": None}, options={"template_string": True})) == [(1, "Hello", [], None)]

def test_extract_javascript_block_comment_is_returned():
    """Verifies: BABEL-EXT-006."""
    source = io.BytesIO(b"/* NOTE: Menu label */\ngettext('Menu');\n")
    assert list(extract_dispatch("javascript", source, {"gettext": None}, ["NOTE:"])) == [(2, "Menu", ["NOTE: Menu label"], None)]

def test_default_directory_filter_skips_hidden_directory(tmp_path):
    """Verifies: BABEL-EXT-003."""
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    assert default_directory_filter(hidden) is False

def test_parse_mapping_cfg_returns_methods_and_options():
    """Verifies: BABEL-EXT-007."""
    cfg = io.StringIO("[extractors]\ncustom = package.module:func\n[custom: **.txt]\nencoding = latin-1\nkeywords = _ gettext\n")
    method_map, options_map = parse_mapping_cfg(cfg)
    assert method_map == [("**.txt", "package.module:func")]
    assert options_map["**.txt"]["encoding"] == "latin-1"
    assert options_map["**.txt"]["keywords"] == {"_": None, "gettext": None}

def test_parse_mapping_deprecated_alias_matches_cfg():
    """Verifies: BABEL-EXT-007."""
    cfg = "[python: **.py]\nencoding = utf-8\n"
    with pytest.warns(DeprecationWarning):
        old = parse_mapping(io.StringIO(cfg))
    new = parse_mapping_cfg(io.StringIO(cfg))
    assert old == new

def test_parse_keywords_handles_context_plural_and_arity():
    """Verifies: BABEL-EXT-008."""
    parsed = parse_keywords(["_", "pgettext:1c,2", "poly:1", "poly:2,2t"])
    assert parsed["_"] is None
    assert parsed["pgettext"] == ((1, "c"), 2)
    assert parsed["poly"][None] == (1,)
    assert parsed["poly"][2] == (2,)

def test_parse_mapping_cfg_rejects_malformed_ini():
    """Verifies: BABEL-EXT-007."""
    with pytest.raises(Exception):
        parse_mapping_cfg(io.StringIO("[python **.py]\n"))

def test_listify_value_splits_strings():
    """Verifies: BABEL-EXT-007."""
    assert listify_value("one two") == ["one", "two"]
    assert listify_value(["one", "two"]) == ["one", "two"]

def test_public_extraction_constants_are_available():
    """Verifies: BABEL-EXT-005."""
    assert "_" in DEFAULT_KEYWORDS
    assert GROUP_NAME == "babel.extractors"

def test_public_constants_have_expected_roles():
    """Verifies: BABEL-CAT-008."""
    assert "PROJECT" in DEFAULT_HEADER
    assert PYTHON_FORMAT.search("%(name)s")

def test_upstream_message_python_format_patterns():
    """Verifies: BABEL-CAT-003."""
    for value in [
        "foo %d bar",
        "foo %s bar",
        "foo %r bar",
        "foo %(name).1f",
        "foo %(name)3.3f",
        "foo %(name)06d",
        "foo %(name)#d",
        "foo %(name)*.*f",
        "foo %()s",
    ]:
        assert catalog.PYTHON_FORMAT.search(value)

def test_upstream_message_translator_comments_are_stored():
    """Verifies: BABEL-CAT-001."""
    msg = catalog.Message("foo", user_comments=["Comment About foo"])
    assert msg.user_comments == ["Comment About foo"]
    msg = catalog.Message("foo", auto_comments=["Comment 1", "Comment 2"])
    assert msg.auto_comments == ["Comment 1", "Comment 2"]

def test_upstream_message_clone_does_not_share_mutable_state():
    """Verifies: BABEL-CAT-006."""
    msg = catalog.Message("foo", locations=[("foo.py", 42)])
    clone = msg.clone()
    clone.locations.append(("bar.py", 42))
    msg.flags.add("fuzzy")
    assert msg.locations == [("foo.py", 42)]
    assert clone.fuzzy is False
    assert msg.fuzzy is True

def test_upstream_catalog_add_returns_message_instance():
    """Verifies: BABEL-CAT-010."""
    cat = catalog.Catalog()
    message = cat.add("foo")
    assert message.id == "foo"
    assert cat["foo"] is message

def test_upstream_catalog_two_messages_with_same_singular_merge():
    """Verifies: BABEL-CAT-013."""
    cat = catalog.Catalog()
    cat.add("foo")
    cat.add(("foo", "foos"))
    assert len(cat) == 1
    assert cat["foo"].pluralizable is True

def test_upstream_catalog_deduplicates_comments_and_locations():
    """Verifies: BABEL-CAT-013."""
    cat = catalog.Catalog()
    cat.add("foo", locations=[("foo.py", 1)], auto_comments=["A"], user_comments=["U"])
    cat.add("foo", locations=[("foo.py", 1), ("bar.py", 2)], auto_comments=["A", "B"], user_comments=["U", "V"])
    assert cat["foo"].locations == [("foo.py", 1), ("bar.py", 2)]
    assert cat["foo"].auto_comments == ["A", "B"]
    assert cat["foo"].user_comments == ["U", "V"]

def test_upstream_catalog_setitem_merges_locations():
    """Verifies: BABEL-CAT-013."""
    cat = catalog.Catalog()
    cat["foo"] = catalog.Message("foo", locations=[("main.py", 1)])
    cat["foo"] = catalog.Message("foo", locations=[("utils.py", 5)])
    assert cat["foo"].locations == [("main.py", 1), ("utils.py", 5)]

def test_upstream_extract_invalid_method_raises():
    """Verifies: BABEL-EXT-002."""
    with pytest.raises(ValueError):
        list(extract.extract("spam", io.BytesIO(b"")))

def test_upstream_extract_allows_callable_method():
    """Verifies: BABEL-EXT-002."""
    def arbitrary_extractor(fileobj, keywords, comment_tags, options):
        return [(1, "_", "Hello", [])]

    rows = list(extract.extract(arbitrary_extractor, io.BytesIO(b"")))
    assert rows == [(1, "Hello", [], None)]

def test_upstream_extract_future_unicode_literal():
    """Verifies: BABEL-EXT-005."""
    buf = io.BytesIO(
        br"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
nbsp = _('\xa0')
"""
    )
    messages = list(extract.extract("python", buf, extract.DEFAULT_KEYWORDS, [], {}))
    assert messages[0][1] == "\xa0"

def test_upstream_extract_python_default_encoding_utf8():
    """Verifies: BABEL-EXT-005."""
    buf = io.BytesIO('_("☃")'.encode("utf-8"))
    messages = list(extract.extract_python(buf, list(extract.DEFAULT_KEYWORDS), [], {}))
    assert messages == [(1, "_", "☃", [])]

def test_upstream_extract_python_multiline_plural_call():
    """Verifies: BABEL-EXT-005."""
    buf = io.BytesIO(
        b"""
msg = ngettext('pylon',
            'pylons', count)
"""
    )
    messages = list(extract.extract_python(buf, ("ngettext",), [], {}))
    assert messages == [(2, "ngettext", ("pylon", "pylons", None), [])]
