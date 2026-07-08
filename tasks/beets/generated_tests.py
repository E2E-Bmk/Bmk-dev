"""Cleaned public-API tests for the beets Stage 3 oracle.

These tests intentionally avoid `beets.test`, private helpers, `beets.util`,
`beets.dbcore.query`, `beets.ui.commands.*`, and built-in plugin internals.
They exercise behavior described by `wip/beets/spec/spec_v1.md` through the
installable public surface only.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from beets import config
from beets.dbcore import AndQuery, FieldQuery, MatchQuery, OrQuery
from beets.library import Album, Item, Library, parse_query_parts, parse_query_string
from beets.plugins import BeetsPlugin, send
from beets.ui import Subcommand, main


def _mark(section: str, layer: str, notes: str):
    return pytest.mark.beets_filter(spec_section=section, layer=layer, notes=notes)


@pytest.fixture(autouse=True)
def isolated_beets_config(tmp_path, monkeypatch):
    beetsdir = tmp_path / "beetsdir"
    musicdir = tmp_path / "music"
    beetsdir.mkdir()
    musicdir.mkdir()
    monkeypatch.setenv("BEETSDIR", str(beetsdir))
    config["library"] = str(tmp_path / "library.db")
    config["directory"] = str(musicdir)
    config["plugins"] = []
    config["pluginpath"] = []
    config["sort_item"] = "artist+"
    config["sort_album"] = "albumartist+"
    config["sort_case_insensitive"] = True


def make_library(tmp_path: Path) -> Library:
    return Library(str(tmp_path / "library.db"), directory=str(tmp_path / "music"))


def make_item(tmp_path: Path, **values) -> Item:
    path = values.pop("path", tmp_path / f"{values.get('title', 'track')}.mp3")
    defaults = {
        "title": "Alpha",
        "artist": "Artist One",
        "artists": ["Artist One", "Guest"],
        "album": "Example Album",
        "albumartist": "Album Artist",
        "year": 2001,
        "track": 1,
        "tracktotal": 2,
        "disc": 1,
        "disctotal": 1,
        "genres": ["Rock"],
        "comments": "public note",
        "path": str(path),
    }
    defaults.update(values)
    return Item(**defaults)


def titles(results):
    return [item.title for item in results]


@_mark("section Public API", "integration", "Library.add stores an Item retrievable by id")
def test_library_add_and_get_item_roundtrip(tmp_path):
    lib = make_library(tmp_path)
    item = make_item(tmp_path, title="Stored")
    item_id = lib.add(item)

    loaded = lib.get_item(item_id)

    assert loaded is not None
    assert loaded.title == "Stored"
    assert loaded.artist == "Artist One"


@_mark("section Cross-View Invariants", "atomic", "attribute and mapping access expose the same model value")
def test_item_attribute_and_mapping_access_are_equivalent(tmp_path):
    item = make_item(tmp_path)

    item["artist"] = "Mapped Artist"
    item.title = "Attribute Title"

    assert item.artist == "Mapped Artist"
    assert item["title"] == "Attribute Title"


@_mark("section Public API", "integration", "flexible attributes persist across store/load")
def test_flexible_attribute_persists_after_store_load(tmp_path):
    lib = make_library(tmp_path)
    item = make_item(tmp_path, mood="bright")
    item_id = lib.add(item)

    loaded = lib.get_item(item_id)

    assert loaded is not None
    assert loaded.mood == "bright"


@_mark("section Public API", "integration", "Library.add_album creates an album and associates items")
def test_add_album_associates_items_and_allows_album_lookup(tmp_path):
    lib = make_library(tmp_path)
    first = make_item(tmp_path, title="One", track=1)
    second = make_item(tmp_path, title="Two", track=2)

    album = lib.add_album([first, second])

    assert album.id is not None
    assert {item.title for item in album.items()} == {"One", "Two"}
    assert lib.get_album(first).id == album.id


@_mark("section Error Semantics", "atomic", "Library.add_album rejects an empty album")
def test_add_album_empty_raises_valueerror(tmp_path):
    lib = make_library(tmp_path)

    with pytest.raises(ValueError):
        lib.add_album([])


@_mark("section Public API", "integration", "Album.store(inherit=True) propagates inheritable fields")
def test_album_store_inherits_album_fields_to_items(tmp_path):
    lib = make_library(tmp_path)
    album = lib.add_album([make_item(tmp_path, title="One"), make_item(tmp_path, title="Two")])

    album.year = 1998
    album.store(inherit=True)

    assert {item.year for item in album.items()} == {1998}


@_mark("section Public API", "integration", "flexible album attributes are visible on album items")
def test_album_store_inherits_flexible_album_attribute(tmp_path):
    lib = make_library(tmp_path)
    item = make_item(tmp_path, title="One")
    album = lib.add_album([item])

    album.release_context = "anniversary"
    album.store(inherit=True)

    loaded = lib.get_item(item.id)
    assert loaded.release_context == "anniversary"


@_mark("section Public API", "atomic", "item lookup falls back to album fields unless disabled")
def test_item_album_fallback_and_with_album_false(tmp_path):
    lib = make_library(tmp_path)
    item = make_item(tmp_path, title="One")
    album = lib.add_album([item])
    album.album_note = "from album"
    album.store(inherit=False)

    loaded = lib.get_item(item.id)

    assert loaded.get("album_note") == "from album"
    assert loaded.get("album_note", with_album=False) is None


@_mark("section Public API", "integration", "Results are lazy, repeatable, truthy, sized, and indexable")
def test_results_are_repeatable_sized_and_indexable(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Alpha"))
    lib.add(make_item(tmp_path, title="Beta"))
    results = lib.items()

    assert bool(results)
    assert len(results) == 2
    assert titles(results) == titles(results)
    assert results[0].title in {"Alpha", "Beta"}


@_mark("section Error Semantics", "atomic", "Results indexing raises IndexError outside the result set")
def test_results_out_of_range_index_raises(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Alpha"))

    with pytest.raises(IndexError):
        lib.items()[4]


@_mark("section Query Language", "integration", "field queries perform substring matching")
def test_library_query_field_substring(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Alpha Song", artist="Alice"))
    lib.add(make_item(tmp_path, title="Beta Song", artist="Bob"))

    assert titles(lib.items("artist:Ali")) == ["Alpha Song"]


@_mark("section Query Language", "integration", "unadorned query terms search default item fields")
def test_unadorned_query_searches_default_fields(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Needle", comments="ordinary"))
    lib.add(make_item(tmp_path, title="Other", comments="needle comment"))

    assert set(titles(lib.items("needle"))) == {"Needle", "Other"}


@_mark("section Query Language", "integration", "exact and case-insensitive exact matching are supported")
def test_exact_and_case_insensitive_exact_query(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Hard Rock", genres=["Rock"]))
    lib.add(make_item(tmp_path, title="Soft Rock", genres=["rock"]))

    assert titles(lib.items("genres:=Rock")) == ["Hard Rock"]
    assert set(titles(lib.items("genres:=~rock"))) == {"Hard Rock", "Soft Rock"}


@_mark("section Query Language", "integration", "regular expressions and numeric ranges match query fields")
def test_regex_and_numeric_range_queries(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Old", artist="Alpha", year=1999))
    lib.add(make_item(tmp_path, title="New", artist="Beta", year=2005))

    assert titles(lib.items("artist::^Al")) == ["Old"]
    assert titles(lib.items("year:1998..2001")) == ["Old"]


@_mark("section Query Language", "integration", "comma-separated query parts form OR groups")
def test_or_group_query_parts(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="One"))
    lib.add(make_item(tmp_path, title="Two"))
    lib.add(make_item(tmp_path, title="Three"))

    assert set(titles(lib.items("title:One , title:Two"))) == {"One", "Two"}


@_mark("section Query Language", "integration", "caret and dash prefixes negate query terms")
def test_negated_query_terms(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Keep"))
    lib.add(make_item(tmp_path, title="Drop"))

    assert titles(lib.items("-title:Drop")) == ["Keep"]
    assert titles(lib.items("^title:Drop")) == ["Keep"]


@_mark("section Query Language", "integration", "multi-valued fields match individual values")
def test_multivalued_field_query_matches_individual_value(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Collab", artists=["Alice", "Bob"]))

    assert titles(lib.items("artists::Bob")) == ["Collab"]


@_mark("section Query Objects", "atomic", "parse_query_string returns a Query usable against an Item")
def test_parse_query_string_returns_matching_query(tmp_path):
    query, sort = parse_query_string("artist:Alice", Item)
    item = make_item(tmp_path, artist="Alice")

    assert query.match(item)
    assert sort is not None


@_mark("section Query Objects", "atomic", "parse_query_parts accepts sort terms alongside query terms")
def test_parse_query_parts_accepts_embedded_sort(tmp_path):
    query, sort = parse_query_parts(["artist:Alice", "year-"], Item)

    assert query.match(make_item(tmp_path, artist="Alice"))
    assert sort is not None


@_mark("section Query Objects", "atomic", "MatchQuery matches scalars and list-valued fields")
def test_match_query_matches_scalar_and_list_values(tmp_path):
    item = make_item(tmp_path, artist="Alice", artists=["Alice", "Bob"])

    assert MatchQuery("artist", "Alice").match(item)
    assert MatchQuery("artists", "Bob").match(item)


@_mark("section Query Objects", "atomic", "AndQuery and OrQuery combine public Query objects")
def test_and_or_query_composition(tmp_path):
    item = make_item(tmp_path, artist="Alice", title="Song")

    assert AndQuery([MatchQuery("artist", "Alice"), MatchQuery("title", "Song")]).match(item)
    assert OrQuery([MatchQuery("artist", "Nobody"), MatchQuery("title", "Song")]).match(item)


@_mark("section Query Objects", "atomic", "FieldQuery can intentionally fall back from SQL matching")
def test_field_query_fast_false_has_no_sql_clause():
    assert FieldQuery("title", "Slow", fast=False).clause() == (None, ())


@_mark("section Cross-View Invariants", "integration", "query sort terms order Library results")
def test_sort_terms_order_library_results(tmp_path):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Early", year=1998))
    lib.add(make_item(tmp_path, title="Late", year=2005))

    assert titles(lib.items("year-")) == ["Late", "Early"]
    assert titles(lib.items("year+")) == ["Early", "Late"]


@_mark("section Path Formats and Templates", "atomic", "destination substitutes metadata in templates")
def test_destination_substitutes_metadata_values(tmp_path):
    lib = make_library(tmp_path)
    config["paths"] = {"singleton": "$album/$artist $title"}
    item = make_item(tmp_path, album="Album", artist="Artist", title="Title")
    lib.add(item)

    dest = item.destination(basedir=os.fsencode(tmp_path / "out"))

    assert os.fsdecode(dest).endswith("Album/Artist Title.mp3")


@_mark("section Path Formats and Templates", "atomic", "destination preserves the filename extension")
def test_destination_preserves_extension(tmp_path):
    lib = make_library(tmp_path)
    config["paths"] = {"singleton": "$title"}
    item = make_item(tmp_path, title="Title", path=tmp_path / "source.flac")
    lib.add(item)

    dest = item.destination(basedir=os.fsencode(tmp_path / "out"))

    assert os.fsdecode(dest).endswith("Title.flac")


@_mark("section Path Formats and Templates", "atomic", "relative_to_libdir returns only the formatted path fragment")
def test_destination_relative_to_library_root(tmp_path):
    lib = make_library(tmp_path)
    config["paths"] = {"singleton": "$artist/$title"}
    item = make_item(tmp_path, title="Title")
    lib.add(item)

    dest = item.destination(relative_to_libdir=True)

    assert os.fsdecode(dest) == "Artist One/Title.mp3"


@_mark("section Path Formats and Templates", "integration", "query-conditioned path formats select the first match")
def test_query_conditioned_path_format_selection(tmp_path):
    lib = make_library(tmp_path)
    config["paths"] = {"comp": "Comp/$title", "default": "Other/$title"}
    item = make_item(tmp_path, title="Title", comp=True)
    lib.add(item)

    dest = item.destination()

    assert os.fsdecode(dest).endswith("Comp/Title.mp3")


@_mark("section Path Formats and Templates", "atomic", "path separators inside fields are sanitized")
def test_destination_sanitizes_path_separators_inside_fields(tmp_path):
    lib = make_library(tmp_path)
    config["paths"] = {"singleton": "$album/$title"}
    item = make_item(tmp_path, album="A/B", title="Title")
    lib.add(item)

    dest = os.fsdecode(item.destination())

    assert "A" in dest and "B" in dest
    assert "A/B/Title" not in dest


@_mark("section Path Formats and Templates", "atomic", "template functions transform values")
def test_template_functions_transform_values(tmp_path):
    item = make_item(tmp_path, artist="Mixed Case", title="Title")

    assert item.evaluate_template("%lower{$artist} - %upper{$title}") == "mixed case - TITLE"


@_mark("section Path Formats and Templates", "atomic", "undefined template fields remain visibly unreplaced")
def test_undefined_template_field_remains_visible(tmp_path):
    item = make_item(tmp_path, title="Title")

    assert "$missing_field" in item.evaluate_template("$title/$missing_field")


@_mark("section Cross-View Invariants", "system_e2e", "file deletion and database removal are the same public removal projection")
def test_item_remove_with_delete_removes_file_and_database_row(tmp_path):
    lib = make_library(tmp_path)
    media = tmp_path / "track.mp3"
    media.write_bytes(b"not real audio, only a file path for deletion")
    item = make_item(tmp_path, title="Delete Me", path=media)
    item_id = lib.add(item)

    item.remove(delete=True)

    assert not media.exists()
    assert lib.get_item(item_id) is None


@_mark("section Cross-View Invariants", "system_e2e", "database-only removal leaves the file in place")
def test_item_remove_without_delete_leaves_file(tmp_path):
    lib = make_library(tmp_path)
    media = tmp_path / "track.mp3"
    media.write_bytes(b"not real audio, only a file path for retention")
    item = make_item(tmp_path, title="Keep File", path=media)
    item_id = lib.add(item)

    item.remove(delete=False)

    assert media.exists()
    assert lib.get_item(item_id) is None


@_mark("section Cross-View Invariants", "system_e2e", "album inheritance is visible through query and formatting projections")
def test_album_inheritance_visible_in_query_and_formatting(tmp_path):
    lib = make_library(tmp_path)
    item = make_item(tmp_path, title="Inherited")
    album = lib.add_album([item])
    album.year = 1984
    album.store(inherit=True)

    loaded = lib.items("year:1984").get()

    assert loaded is not None
    assert loaded.title == "Inherited"
    assert loaded.evaluate_template("$album - $year") == "Example Album - 1984"


@_mark("section Command-Line Behavior", "system_e2e", "CLI list exposes the same library query and template projection")
def test_cli_list_formats_matching_items(tmp_path, capsys):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="CliTitle", artist="CliArtist"))

    main(["-l", str(tmp_path / "library.db"), "-d", str(tmp_path / "music"), "list", "-f", "$artist:$title", "title:CliTitle"])

    captured = capsys.readouterr()
    assert "CliArtist:CliTitle" in captured.out


@_mark("section Command-Line Behavior", "system_e2e", "CLI fields includes flexible attributes stored in the library")
def test_cli_fields_includes_flexible_attribute(tmp_path, capsys):
    lib = make_library(tmp_path)
    lib.add(make_item(tmp_path, title="Flex", public_flex="visible"))

    main(["-l", str(tmp_path / "library.db"), "-d", str(tmp_path / "music"), "fields"])

    captured = capsys.readouterr()
    assert "public_flex" in captured.out


@_mark("section Plugin Behavior", "atomic", "BeetsPlugin.commands defaults to an empty command sequence")
def test_plugin_commands_default_empty_sequence():
    plugin = BeetsPlugin("cleaned")

    assert tuple(plugin.commands()) == ()


@_mark("section Plugin Behavior", "atomic", "Subcommand stores command metadata")
def test_subcommand_exposes_name_aliases_help_and_visibility():
    command = Subcommand("demo", help="demo help", aliases=("d",), hide=True)

    assert command.name == "demo"
    assert command.aliases == ("d",)
    assert command.help == "demo help"
    assert command.hide is True


@_mark("section Plugin Behavior", "atomic", "plugins can expose Subcommand objects from commands()")
def test_plugin_commands_can_return_subcommand_sequence():
    class DemoPlugin(BeetsPlugin):
        def commands(self):
            return (Subcommand("demo-command", help="demo help"),)

    plugin = DemoPlugin("demo_cleaned")
    command = plugin.commands()[0]

    assert command.name == "demo-command"
    assert command.help == "demo help"


@_mark("section Plugin Behavior", "atomic", "plugins can expose query prefix mappings from queries()")
def test_plugin_queries_can_return_public_query_mapping():
    class DemoPlugin(BeetsPlugin):
        def queries(self):
            return {"cleaned": MatchQuery}

    plugin = DemoPlugin("demo_cleaned_field")

    assert plugin.queries() == {"cleaned": MatchQuery}


@_mark("section Plugin Behavior", "atomic", "register_listener prevents duplicate registration of the same function")
def test_plugin_register_listener_deduplicates_same_function():
    plugin = BeetsPlugin("listener_cleaned")
    event = "cleaned_generated_event"

    def listener(**kwargs):
        return kwargs.get("value")

    plugin.register_listener(event, listener)
    plugin.register_listener(event, listener)

    assert send(event, value="observed") == ["observed"]


@_mark("section Plugin Behavior", "atomic", "BeetsPlugin.queries defaults to no query prefixes")
def test_plugin_queries_default_empty_mapping():
    plugin = BeetsPlugin("queries_cleaned")

    assert plugin.queries() == {}
