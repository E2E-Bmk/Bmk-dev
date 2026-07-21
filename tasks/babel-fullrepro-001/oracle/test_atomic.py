from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path

import pytest

from babel.messages.catalog import Catalog, Message


def extract_module():
    from babel.messages import extract

    return extract


def mofile_module():
    from babel.messages import mofile

    return mofile


def pofile_module():
    from babel.messages import pofile

    return pofile


def javascript_messages(
    source: bytes,
    keywords: dict[str, object] | tuple[str, ...] | None = None,
    options: dict[str, object] | None = None,
) -> list[tuple]:
    selected = extract_module().DEFAULT_KEYWORDS if keywords is None else keywords
    return list(
        extract_module().extract(
            "javascript", BytesIO(source), selected, [], options or {}
        )
    )


def po_with_location(line: str, *, abort_invalid: bool = True) -> Catalog:
    source = f'#: {line}\nmsgid "foo"\nmsgstr ""\n'
    return pofile_module().read_po(StringIO(source), abort_invalid=abort_invalid)


def test_message_preserves_translator_comments() -> None:
    message = Message("foo", user_comments=["Comment About `foo`"])
    assert message.user_comments == ["Comment About `foo`"]
    message = Message("foo", auto_comments=["First", "Second"])
    assert message.auto_comments == ["First", "Second"]


def test_message_clone_has_independent_mutable_state() -> None:
    message = Message("foo", locations=[("foo.py", 42)])
    clone = message.clone()
    clone.locations.append(("bar.py", 42))
    message.flags.add("fuzzy")
    assert message.locations == [("foo.py", 42)]
    assert message.fuzzy is True
    assert clone.fuzzy is False


def test_catalog_add_returns_message() -> None:
    message = Catalog().add("foo")
    assert isinstance(message, Message)
    assert message.id == "foo"


def test_catalog_merges_singular_and_plural_with_same_singular_id() -> None:
    catalog = Catalog()
    catalog.add("foo")
    catalog.add(("foo", "foos"))
    assert len(catalog) == 1


def test_catalog_deduplicates_automatic_comments() -> None:
    catalog = Catalog()
    catalog.add("foo", auto_comments=["A comment"])
    catalog.add("foo", auto_comments=["A comment", "Another comment"])
    assert catalog["foo"].auto_comments == ["A comment", "Another comment"]


def test_catalog_deduplicates_user_comments() -> None:
    catalog = Catalog()
    catalog.add("foo", user_comments=["A comment"])
    catalog.add("foo", user_comments=["A comment", "Another comment"])
    assert catalog["foo"].user_comments == ["A comment", "Another comment"]


def test_catalog_deduplicates_locations() -> None:
    catalog = Catalog()
    catalog.add("foo", locations=[("foo.py", 1)])
    catalog.add("foo", locations=[("foo.py", 1)])
    assert catalog["foo"].locations == [("foo.py", 1)]


def test_catalog_assignment_merges_new_comments_and_locations() -> None:
    catalog = Catalog()
    catalog["foo"] = Message("foo", locations=[("main.py", 5)])
    catalog["foo"] = Message(
        "foo", locations=[("main.py", 7)], user_comments=["User comment"]
    )
    catalog["foo"] = Message(
        "foo", locations=[("main.py", 9)], auto_comments=["Automatic comment"]
    )
    assert catalog["foo"].user_comments == ["User comment"]
    assert catalog["foo"].auto_comments == ["Automatic comment"]
    assert catalog["foo"].locations == [("main.py", 5), ("main.py", 7), ("main.py", 9)]


def test_po_plural_count_is_normalized_before_message_check() -> None:
    source = b'''msgid ""
msgstr ""
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "item"
msgid_plural "items"
msgstr[0] "one"
msgstr[1] "many"
msgstr[2] "extra"
'''
    catalog = pofile_module().read_po(BytesIO(source))
    message = catalog["item"]
    assert message.string == ("one", "many")
    assert message.check(catalog) == []


def test_javascript_extracts_simple_gettext_calls() -> None:
    source = b"msg1 = _('simple')\nmsg2 = gettext('simple')\nmsg3 = ngettext('s', 'p', 42)\n"
    assert javascript_messages(source) == [
        (1, "simple", [], None),
        (2, "simple", [], None),
        (3, ("s", "p"), [], None),
    ]


def test_javascript_ignores_dynamic_arguments() -> None:
    source = b'''msg1 = _(dynamic.replace(/"/, "'"))
msg2 = ungettext("Babel", dynamic, 2)
msg3 = ungettext('bunny', 'bunnies', 2)
msg4 = gettext('Rabbit')
msg5 = dngettext(domain, 'Page', 'Pages', 3)
'''
    assert javascript_messages(source) == [
        (3, ("bunny", "bunnies"), [], None),
        (4, "Rabbit", [], None),
        (5, ("Page", "Pages"), [], None),
    ]


def test_javascript_line_comment_is_attached() -> None:
    source = "// NOTE: hello\nmsg = _('Bonjour à tous')\n".encode()
    messages = list(extract_module().extract_javascript(BytesIO(source), ("_",), ["NOTE:"], {}))
    assert messages[0][2:] == ("Bonjour à tous", ["NOTE: hello"])


def test_javascript_multiline_comment_is_attached() -> None:
    source = "/* NOTE: hello\nand bonjour\n  and servus */\nmsg = _('Bonjour à tous')\n".encode()
    messages = list(extract_module().extract_javascript(BytesIO(source), ("_",), ["NOTE:"], {}))
    assert messages[0][2] == "Bonjour à tous"
    assert messages[0][3] == ["NOTE: hello", "and bonjour", "  and servus"]


def test_javascript_function_definition_is_not_a_message() -> None:
    source = b"function gettext(value) { return translations[value] || value; }"
    assert list(extract_module().extract_javascript(BytesIO(source), ("gettext",), [], {})) == []


def test_javascript_only_attaches_adjacent_comments() -> None:
    source = b'''/* NOTE: ignored */
foo()
/* NOTE: first */
_('One')
// NOTE: second
// continuation
_('Two')
// NOTE: ignored too
bar()
_('Three')
'''
    messages = list(extract_module().extract_javascript(BytesIO(source), ("_",), ["NOTE:"], {}))
    assert [message[2] for message in messages] == ["One", "Two", "Three"]
    assert [message[3] for message in messages] == [
        ["NOTE: first"],
        ["NOTE: second", "continuation"],
        [],
    ]


JSX_SOURCE = b'''class Foo {
    render() {
        const value = gettext("hello");
        return (
            <option value="val1">{ i18n._('String1') }</option>
            <option value="val2">{ i18n._('String 2') }</option>
            <option value="val3">{ i18n._('String 3') }</option>
            <option value="val4">{ _('String 4') }</option>
            <option>{ _('String 5') }</option>
        );
    }
'''

JSX_MESSAGES = ["hello", "String1", "String 2", "String 3", "String 4", "String 5"]


def test_javascript_jsx_disabled_does_not_extract_full_jsx_surface() -> None:
    messages = list(extract_module().extract_javascript(BytesIO(JSX_SOURCE), ("_", "gettext"), [], {"jsx": False}))
    assert [message[2] for message in messages] != JSX_MESSAGES


def test_javascript_jsx_enabled_extracts_embedded_calls() -> None:
    messages = list(extract_module().extract_javascript(BytesIO(JSX_SOURCE), ("_", "gettext"), [], {"jsx": True}))
    assert [message[2] for message in messages] == JSX_MESSAGES


def test_javascript_extracts_dotted_keyword() -> None:
    source = b"com.corporate.i18n.formatMessage('Insert coin to continue')"
    messages = javascript_messages(source, {"com.corporate.i18n.formatMessage": None})
    assert messages == [(1, "Insert coin to continue", [], None)]


def test_javascript_extracts_standard_template_literal() -> None:
    messages = javascript_messages(b"gettext(`Very template, wow`)", {"gettext": None})
    assert messages == [(1, "Very template, wow", [], None)]


def test_javascript_extracts_tagged_template_literal() -> None:
    messages = javascript_messages(b"function() { if(foo) i18n`Tag template, wow`; }", {"i18n": None})
    assert messages == [(1, "Tag template, wow", [], None)]


def test_javascript_extracts_call_inside_template_interpolation() -> None:
    source = b"const msg = `${gettext('Hello')} ${user.name}`"
    messages = javascript_messages(source, {"gettext": None}, {"parse_template_string": True})
    assert messages == [(1, "Hello", [], None)]


def test_javascript_template_interpolation_tracks_line_numbers() -> None:
    source = b'''const userName = gettext('Username')
const msg = `${
gettext('Hello')
} ${userName} ${
gettext('Are you having a nice day?')
}`
'''
    messages = javascript_messages(source, {"gettext": None}, {"parse_template_string": True})
    assert messages == [
        (1, "Username", [], None),
        (3, "Hello", [], None),
        (5, "Are you having a nice day?", [], None),
    ]


def test_javascript_extracts_nested_template_interpolations() -> None:
    source = b"const msg = `${gettext('Greetings!')} ${ ok ? `${gettext('Evening')}` : `${gettext('Day')}`}`"
    messages = javascript_messages(source, {"gettext": None}, {"parse_template_string": True})
    assert [message[1] for message in messages] == ["Greetings!", "Evening", "Day"]


def test_javascript_unquotes_unicode_and_hex_escapes() -> None:
    source = rb'''gettext("h\u00ebllo"); gettext("h\xebllo");'''
    assert [message[1] for message in javascript_messages(source, {"gettext": None})] == ["hëllo", "hëllo"]


def test_javascript_accepts_dollar_in_keyword_identifier() -> None:
    messages = javascript_messages(b"dollar$dollar('value')", {"dollar$dollar": None})
    assert messages == [(1, "value", [], None)]


def test_javascript_dotted_name_routes_to_dotted_keyword() -> None:
    messages = javascript_messages(b"foo.bar('value')", {"foo.bar": None})
    assert messages == [(1, "value", [], None)]


def test_javascript_dotted_name_without_call_is_ignored() -> None:
    assert javascript_messages(b"const value = foo.bar", {"foo.bar": None}) == []


def test_javascript_tagged_template_preserves_quotes() -> None:
    messages = javascript_messages(b'''gettext `foo"bar"p`''', {"gettext": None})
    assert messages == [(1, 'foo"bar"p', [], None)]


def test_javascript_nested_jsx_extracts_all_calls() -> None:
    source = b'''<comp data={{active: true}}>
      <option>{ i18n._('String 1') }</option>
      <button text={i18n._('String 2')} />
    </comp>'''
    messages = list(extract_module().extract_javascript(BytesIO(source), ("i18n._",), [], {"jsx": True}))
    assert [message[2] for message in messages] == ["String 1", "String 2"]


def test_mo_reader_preserves_catalog_metadata_and_messages() -> None:
    fixture = Path(__file__).parent / "data" / "messages.mo"
    with fixture.open("rb") as handle:
        catalog = mofile_module().read_mo(handle)
    assert len(catalog) == 2
    assert catalog.project == "TestProject"
    assert catalog.version == "0.1"
    assert catalog["bar"].string == "Stange"
    assert catalog["foobar"].string == ["Fuhstange", "Fuhstangen"]


def test_po_unescape_handles_quotes_and_newlines() -> None:
    escaped = '"Say:\\n  \\"hello, world!\\"\\n"'
    assert pofile_module().unescape(escaped) == 'Say:\n  "hello, world!"\n'


def test_po_unescape_preserves_quoted_backslash_n() -> None:
    assert pofile_module().unescape(r'"\\n"') == "\\n"


def test_po_denormalize_handles_multiline_string_without_empty_prefix() -> None:
    text = '"multi-line\\n"\n" translation"'
    assert pofile_module().denormalize(text) == "multi-line\n translation"
    assert pofile_module().denormalize(f'""\n{text}') == "multi-line\n translation"


def test_po_location_accepts_isolated_filename() -> None:
    assert po_with_location("\u2068file1.po\u2069")["foo"].locations == [("file1.po", None)]


def test_po_location_accepts_mixed_plain_and_isolated_filenames() -> None:
    line = "file1.po \u2068file 2.po\u2069 file3.po"
    assert po_with_location(line)["foo"].locations == [
        ("file1.po", None),
        ("file 2.po", None),
        ("file3.po", None),
    ]


def test_po_location_accepts_line_numbers_after_isolates() -> None:
    line = "file1.po:1 \u2068file 2.po\u2069:2 file3.po:3"
    assert po_with_location(line)["foo"].locations == [
        ("file1.po", 1),
        ("file 2.po", 2),
        ("file3.po", 3),
    ]


def test_po_location_rejects_missing_pop_isolate() -> None:
    with pytest.raises(pofile_module().PoFileError):
        po_with_location("\u2068file 1.po")


def test_po_location_rejects_unmatched_pop_isolate() -> None:
    with pytest.raises(pofile_module().PoFileError):
        po_with_location("file 1.po\u2069")


def test_po_location_rejects_reversed_isolates() -> None:
    with pytest.raises(pofile_module().PoFileError):
        po_with_location("\u2069file 1.po\u2068")


def test_po_location_reads_plain_filename() -> None:
    assert po_with_location("file.po")["foo"].locations == [("file.po", None)]


def test_po_location_reads_underscore_filename() -> None:
    assert po_with_location("file_a.po")["foo"].locations == [("file_a.po", None)]


def test_po_location_reads_dash_filename() -> None:
    assert po_with_location("file-a.po")["foo"].locations == [("file-a.po", None)]


def test_po_location_reads_space_inside_isolates() -> None:
    assert po_with_location("\u2068file a.po\u2069")["foo"].locations == [("file a.po", None)]


def test_po_location_reads_tab_inside_isolates() -> None:
    assert po_with_location("\u2068file\ta.po\u2069")["foo"].locations == [("file\ta.po", None)]


def test_po_reader_rejects_text_then_bytes_iterable() -> None:
    with pytest.raises((TypeError, AttributeError)):
        pofile_module().read_po(['msgid "foo"', b'msgstr "Voh"'])


def test_po_reader_rejects_bytes_then_text_iterable() -> None:
    with pytest.raises((TypeError, AttributeError)):
        pofile_module().read_po([b'msgstr "Voh"', 'msgid "foo"'])


def test_po_reader_treats_blank_language_as_no_locale() -> None:
    source = StringIO('msgid ""\nmsgstr ""\n"Language: \\n"\n')
    assert pofile_module().read_po(source).locale is None


def test_po_reader_keeps_singular_message_without_msgstr_when_not_aborting() -> None:
    catalog = pofile_module().read_po(StringIO('msgid "foo"'))
    assert len(catalog) == 1
    assert catalog["foo"].string == ""


def test_po_reader_keeps_plural_message_without_msgstr_when_not_aborting() -> None:
    catalog = pofile_module().read_po(StringIO('msgid "foo"\nmsgid_plural "foos"'))
    assert len(catalog) == 1
    assert catalog["foo"].string == ("", "")
