# Spec2Repo oracle - integration tests for babel-fullrepro-001

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


def po_text(catalog: Catalog, **kwargs) -> str:
    buf = io.BytesIO()
    write_po(buf, catalog, **kwargs)
    return buf.getvalue().decode(catalog.charset)

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_assignment_merges_message_metadata_without_duplicates')
def test_catalog_update_preserves_existing_translation():
    """Verifies: BABEL-CAT-015."""
    template = Catalog()
    template.add("Hello", locations=[("new.py", 5)])
    catalog = Catalog()
    catalog.add("Hello", "Bonjour", locations=[("old.py", 1)])
    catalog.update(template)
    msg = catalog["Hello"]
    assert msg.string == "Bonjour"
    assert msg.locations == [("new.py", 5)]

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_delete_missing_id_is_noop')
def test_catalog_update_moves_removed_message_to_obsolete():
    """Verifies: BABEL-CAT-015."""
    template = Catalog()
    template.add("Present")
    catalog = Catalog()
    catalog.add("Present", "Present")
    catalog.add("Removed", "Supprime")
    catalog.update(template, no_fuzzy_matching=True)
    assert catalog.get("Removed") is None
    assert "Removed" in catalog.obsolete

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_message_clone_is_independent_copy')
def test_catalog_update_fuzzy_matches_changed_id():
    """Verifies: BABEL-CAT-016."""
    template = Catalog()
    template.add("Hello there")
    catalog = Catalog()
    catalog.add("Hello here", "Bonjour")
    catalog.update(template)
    msg = catalog["Hello there"]
    assert msg.string == "Bonjour"
    assert "fuzzy" in msg.flags
    assert msg.previous_id == ["Hello here"]

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_delete_missing_id_is_noop')
def test_catalog_update_can_disable_fuzzy_matching():
    """Verifies: BABEL-CAT-015, BABEL-CAT-016."""
    template = Catalog()
    template.add("Hello there")
    catalog = Catalog()
    catalog.add("Hello here", "Bonjour")
    catalog.update(template, no_fuzzy_matching=True)
    assert catalog["Hello there"].string is None
    assert "Hello here" in catalog.obsolete

@pytest.mark.depends_on('test_catalog_accepts_domain_and_metadata_without_locale', 'test_catalog_empty_message_updates_header_state')
def test_catalog_update_can_copy_template_header_comment():
    """Verifies: BABEL-CAT-015."""
    template = Catalog()
    template.header_comment = "# Template PROJECT"
    catalog = Catalog(project="App")
    catalog.update(template, update_header_comment=True)
    assert "Template" in catalog.header_comment

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_normalize_and_denormalize_multiline_text')
def test_write_po_omits_header_when_requested():
    """Verifies: BABEL-FILE-004."""
    catalog = Catalog()
    catalog.add("Hello")
    text = po_text(catalog, omit_header=True)
    assert "msgid \"Hello\"" in text
    assert "Project-Id-Version" not in text

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_assignment_merges_message_metadata_without_duplicates')
def test_write_po_suppresses_locations_when_requested():
    """Verifies: BABEL-FILE-005."""
    catalog = Catalog()
    catalog.add("Hello", locations=[("app.py", 3)])
    text = po_text(catalog, omit_header=True, no_location=True)
    assert "msgid \"Hello\"" in text
    assert "#:" not in text

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_assignment_merges_message_metadata_without_duplicates')
def test_write_po_can_omit_line_numbers():
    """Verifies: BABEL-FILE-004."""
    catalog = Catalog()
    catalog.add("Hello", locations=[("app.py", 3)])
    text = po_text(catalog, omit_header=True, include_lineno=False)
    assert "#: app.py" in text
    assert "#: app.py:3" not in text

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_normalize_and_denormalize_multiline_text')
def test_write_po_includes_previous_ids_when_requested():
    """Verifies: BABEL-FILE-004."""
    catalog = Catalog()
    catalog.add("New", previous_id="Old")
    text = po_text(catalog, omit_header=True, include_previous=True)
    assert "#| msgid \"Old\"" in text
    assert "msgid \"New\"" in text

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_normalize_and_denormalize_multiline_text')
def test_generate_po_emits_string_fragments():
    """Verifies: BABEL-FILE-004."""
    catalog = Catalog()
    catalog.add("Hello")
    lines = list(generate_po(catalog, omit_header=True))
    assert any(line == 'msgid "Hello"\n' for line in lines)

@pytest.mark.depends_on('test_plural_message_gets_empty_plural_translation_tuple', 'test_catalog_assignment_merges_message_metadata_without_duplicates')
def test_read_po_reads_comments_flags_locations_and_plural():
    """Verifies: BABEL-FILE-001."""
    source = io.StringIO(
        '# user\n#. auto\n#: app.py:4\n#, fuzzy\nmsgid "file"\nmsgid_plural "files"\nmsgstr[0] "fichier"\nmsgstr[1] "fichiers"\n'
    )
    catalog = read_po(source)
    msg = catalog["file"]
    assert msg.user_comments == ["user"]
    assert msg.auto_comments == ["auto"]
    assert msg.locations == [("app.py", 4)]
    assert msg.string == ("fichier", "fichiers")
    assert "fuzzy" in msg.flags

@pytest.mark.depends_on('test_catalog_context_keys_are_distinct', 'test_catalog_add_returns_and_stores_message')
def test_read_po_reads_context_as_lookup_key():
    """Verifies: BABEL-FILE-001."""
    catalog = read_po(io.StringIO('msgctxt "button"\nmsgid "Open"\nmsgstr "Ouvrir"\n'))
    assert catalog.get("Open", context="button").string == "Ouvrir"
    assert catalog.get("Open") is None

@pytest.mark.depends_on('test_catalog_delete_missing_id_is_noop', 'test_catalog_add_returns_and_stores_message')
def test_read_po_obsolete_messages_can_be_kept_or_ignored():
    """Verifies: BABEL-FILE-002."""
    source = '#~ msgid "Old"\n#~ msgstr "Ancien"\n'
    kept = read_po(io.StringIO(source), ignore_obsolete=False)
    ignored = read_po(io.StringIO(source), ignore_obsolete=True)
    assert "Old" in kept.obsolete
    assert ignored.obsolete == {}

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_public_constants_have_expected_roles')
def test_read_po_invalid_input_can_abort():
    """Verifies: BABEL-FILE-003."""
    with pytest.raises(PoFileError):
        read_po(io.StringIO('msgid "missing translation"\n'), abort_invalid=True)

@pytest.mark.depends_on('test_catalog_empty_message_updates_header_state', 'test_catalog_accepts_domain_and_metadata_without_locale')
def test_read_po_header_updates_catalog_metadata():
    """Verifies: BABEL-FILE-001."""
    source = 'msgid ""\nmsgstr "Project-Id-Version: Demo 1.2\\nContent-Type: text/plain; charset=iso-8859-1\\n"\n'
    catalog = read_po(io.StringIO(source))
    assert catalog.project == "Demo"
    assert catalog.version == "1.2"
    assert catalog.charset == "iso-8859-1"

@pytest.mark.depends_on('test_catalog_context_keys_are_distinct', 'test_catalog_assignment_merges_message_metadata_without_duplicates')
def test_po_round_trip_preserves_message_context_and_flags():
    """Verifies: BABEL-FILE-001, BABEL-FILE-004."""
    catalog = Catalog()
    catalog.add("Open", "Ouvrir", context="button", flags=["fuzzy"], locations=[("ui.py", 8)])
    text = po_text(catalog)
    loaded = read_po(io.StringIO(text))
    msg = loaded.get("Open", context="button")
    assert msg.string == "Ouvrir"
    assert "fuzzy" in msg.flags
    assert msg.locations == [("ui.py", 8)]

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_mime_headers_include_default_plural_free_metadata')
def test_mo_round_trip_preserves_singular_message():
    """Verifies: BABEL-FILE-007, BABEL-FILE-008."""
    catalog = Catalog()
    catalog.add("Hello", "Bonjour")
    buf = io.BytesIO()
    write_mo(buf, catalog)
    buf.seek(0)
    loaded = read_mo(buf)
    assert loaded["Hello"].string == "Bonjour"

@pytest.mark.depends_on('test_plural_message_gets_empty_plural_translation_tuple', 'test_catalog_plural_forms_follow_locale')
def test_mo_round_trip_preserves_plural_message():
    """Verifies: BABEL-FILE-007, BABEL-FILE-008."""
    catalog = Catalog()
    catalog.add(("file", "files"), ("fichier", "fichiers"))
    buf = io.BytesIO()
    write_mo(buf, catalog)
    buf.seek(0)
    loaded = read_mo(buf)
    assert tuple(loaded["file"].string) == ("fichier", "fichiers")

@pytest.mark.depends_on('test_catalog_context_keys_are_distinct', 'test_catalog_add_returns_and_stores_message')
def test_mo_round_trip_preserves_context_message():
    """Verifies: BABEL-FILE-007, BABEL-FILE-008."""
    catalog = Catalog()
    catalog.add("Open", "Ouvrir", context="button")
    buf = io.BytesIO()
    write_mo(buf, catalog)
    buf.seek(0)
    loaded = read_mo(buf)
    assert loaded.get("Open", context="button").string == "Ouvrir"

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_public_constants_have_expected_roles')
def test_mo_omits_fuzzy_messages_by_default():
    """Verifies: BABEL-FILE-009."""
    catalog = Catalog()
    catalog.add("Hello", "Bonjour", flags=["fuzzy"])
    buf = io.BytesIO()
    write_mo(buf, catalog, use_fuzzy=False)
    buf.seek(0)
    assert read_mo(buf).get("Hello") is None

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_public_constants_have_expected_roles')
def test_mo_includes_fuzzy_messages_when_requested():
    """Verifies: BABEL-FILE-009."""
    catalog = Catalog()
    catalog.add("Hello", "Bonjour", flags=["fuzzy"])
    buf = io.BytesIO()
    write_mo(buf, catalog, use_fuzzy=True)
    buf.seek(0)
    assert read_mo(buf)["Hello"].string == "Bonjour"

@pytest.mark.depends_on('test_mo_round_trip_preserves_singular_message', 'test_public_constants_have_expected_roles')
def test_mo_invalid_bytes_raise_parsing_exception():
    """Verifies: BABEL-FILE-008."""
    with pytest.raises(Exception):
        read_mo(io.BytesIO(b"not a valid mo file"))

@pytest.mark.depends_on('test_extract_python_finds_gettext_call', 'test_extract_unknown_method_raises_value_error')
def test_extract_from_file_uses_named_method(tmp_path):
    """Verifies: BABEL-EXT-001."""
    path = tmp_path / "app.py"
    path.write_text("_('Hello')\n", encoding="utf-8")
    assert extract_from_file("python", path, {"_": None}) == [(1, "Hello", [], None)]

@pytest.mark.depends_on('test_extract_python_finds_gettext_call', 'test_default_directory_filter_skips_hidden_directory')
def test_extract_from_dir_returns_relative_filenames(tmp_path):
    """Verifies: BABEL-EXT-003, BABEL-EXT-004."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "a.py").write_text("_('A')\n", encoding="utf-8")
    (pkg / "ignored.txt").write_text("_('B')\n", encoding="utf-8")
    assert list(extract_from_dir(pkg, keywords={"_": None})) == [("a.py", 1, "A", [], None)]

@pytest.mark.depends_on('test_extract_python_finds_gettext_call', 'test_parse_mapping_cfg_returns_methods_and_options')
def test_extract_from_dir_callback_receives_file_method_and_options(tmp_path):
    """Verifies: BABEL-EXT-003."""
    (tmp_path / "a.py").write_text("_('A')\n", encoding="utf-8")
    calls = []
    list(extract_from_dir(tmp_path, options_map={"**.py": {"encoding": "utf-8"}}, callback=lambda *args: calls.append(args)))
    assert calls == [("a.py", "python", {"encoding": "utf-8"})]

@pytest.mark.depends_on('test_extract_python_finds_gettext_call', 'test_default_directory_filter_skips_hidden_directory')
def test_extract_from_dir_directory_filter_blocks_subtree(tmp_path):
    """Verifies: BABEL-EXT-003."""
    keep = tmp_path / "keep"
    skip = tmp_path / "skip"
    keep.mkdir()
    skip.mkdir()
    (keep / "a.py").write_text("_('A')\n", encoding="utf-8")
    (skip / "b.py").write_text("_('B')\n", encoding="utf-8")
    rows = list(extract_from_dir(tmp_path, keywords={"_": None}, directory_filter=lambda path: Path(path).name != "skip"))
    assert rows == [("keep/a.py", 1, "A", [], None)]

@pytest.mark.depends_on('test_parse_mapping_cfg_returns_methods_and_options', 'test_public_extraction_constants_are_available')
def test_cli_help_lists_core_commands(capsys):
    """Verifies: BABEL-CMD-001, BABEL-CMD-002."""
    with pytest.raises(SystemExit) as exc:
        CommandLineInterface().run(["pybabel", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "compile" in out and "extract" in out and "init" in out and "update" in out

@pytest.mark.depends_on('test_extract_from_file_uses_named_method', 'test_extract_unknown_method_raises_value_error')
def test_cli_extract_requires_output_file(tmp_path):
    """Verifies: BABEL-CMD-003, BABEL-CMD-004."""
    src = tmp_path / "app.py"
    src.write_text("_('Hello')\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        CommandLineInterface().run(["pybabel", "extract", str(src)])
    assert exc.value.code != 0

@pytest.mark.depends_on('test_extract_from_file_uses_named_method', 'test_write_po_omits_header_when_requested')
def test_cli_extract_writes_pot_file(tmp_path):
    """Verifies: BABEL-CMD-003."""
    src = tmp_path / "app.py"
    pot = tmp_path / "messages.pot"
    src.write_text("_('Hello')\n", encoding="utf-8")
    CommandLineInterface().run(["pybabel", "extract", "-o", str(pot), str(src)])
    text = pot.read_text(encoding="utf-8")
    assert "msgid \"Hello\"" in text

@pytest.mark.depends_on('test_plural_message_gets_empty_plural_translation_tuple', 'test_catalog_add_returns_and_stores_message')
def test_upstream_catalog_update_message_changed_to_plural():
    """Verifies: BABEL-CAT-015, BABEL-CAT-016."""
    cat = catalog.Catalog()
    cat.add("foo", "Voh")
    tmpl = catalog.Catalog()
    tmpl.add(("foo", "foos"))
    cat.update(tmpl)
    assert cat["foo"].string == ("Voh", "")
    assert cat["foo"].fuzzy is True

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_catalog_delete_missing_id_is_noop')
def test_upstream_catalog_update_without_fuzzy_matching_obsoletes_old():
    """Verifies: BABEL-CAT-015."""
    cat = catalog.Catalog()
    cat.add("fo", "Voh")
    cat.add("bar", "Bahr")
    tmpl = catalog.Catalog()
    tmpl.add("foo")
    cat.update(tmpl, no_fuzzy_matching=True)
    assert len(cat.obsolete) == 2
    assert cat["foo"].string is None

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_message_clone_is_independent_copy')
def test_upstream_catalog_update_no_template_mutation():
    """Verifies: BABEL-CAT-015."""
    tmpl = catalog.Catalog()
    tmpl.add("foo")
    cat1 = catalog.Catalog()
    cat1.add("foo", "Voh")
    cat1.update(tmpl)
    cat2 = catalog.Catalog()
    cat2.update(tmpl)
    assert cat2["foo"].string is None
    assert cat2["foo"].fuzzy is False

@pytest.mark.depends_on('test_extract_python_handles_plural_keyword_spec', 'test_extract_python_finds_gettext_call')
def test_upstream_extract_different_signatures_filter_invalid_calls():
    """Verifies: BABEL-EXT-005, BABEL-EXT-008."""
    buf = io.BytesIO(
        b"""
foo = _('foo', 'bar')
n = ngettext('hello', 'there', n=3)
n = ngettext(n=3, *messages)
n = ngettext()
n = ngettext('foo')
"""
    )
    messages = list(extract.extract("python", buf, extract.DEFAULT_KEYWORDS, [], {}))
    assert messages == [(2, "foo", [], None), (3, ("hello", "there"), [], None)]

@pytest.mark.depends_on('test_catalog_assignment_merges_message_metadata_without_duplicates', 'test_write_po_omits_header_when_requested')
def test_upstream_pofile_join_locations():
    """Verifies: BABEL-FILE-004."""
    cat = Catalog()
    cat.add("foo", locations=[("main.py", 1)])
    cat.add("foo", locations=[("utils.py", 3)])
    buf = io.BytesIO()
    pofile.write_po(buf, cat, omit_header=True)
    text = buf.getvalue().decode("utf-8")
    assert "#: main.py:1 utils.py:3" in text
    assert 'msgid "foo"' in text

@pytest.mark.depends_on('test_catalog_assignment_merges_message_metadata_without_duplicates', 'test_write_po_omits_header_when_requested')
def test_upstream_pofile_duplicate_auto_comments_written_once():
    """Verifies: BABEL-FILE-004."""
    cat = Catalog()
    cat.add("foo", auto_comments=["A comment"])
    cat.add("foo", auto_comments=["A comment"])
    buf = io.BytesIO()
    pofile.write_po(buf, cat, omit_header=True)
    text = buf.getvalue().decode("utf-8")
    assert text.count("#. A comment") == 1

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_write_po_omits_header_when_requested')
def test_upstream_pofile_obsolete_message_can_be_ignored():
    """Verifies: BABEL-FILE-004."""
    cat = Catalog()
    cat.add("foo", "Voh", locations=[("main.py", 1)])
    cat.obsolete["bar"] = Message("bar", "Bahr")
    buf = io.BytesIO()
    pofile.write_po(buf, cat, omit_header=True, ignore_obsolete=True)
    text = buf.getvalue().decode("utf-8")
    assert 'msgid "foo"' in text
    assert "bar" not in text

@pytest.mark.depends_on('test_catalog_add_returns_and_stores_message', 'test_write_po_includes_previous_ids_when_requested')
def test_upstream_pofile_previous_msgid_is_included_when_requested():
    """Verifies: BABEL-FILE-004."""
    cat = Catalog()
    cat.add("foo", "Voh", previous_id="fo")
    buf = io.BytesIO()
    pofile.write_po(buf, cat, omit_header=True, include_previous=True)
    assert '#| msgid "fo"' in buf.getvalue().decode("utf-8")
