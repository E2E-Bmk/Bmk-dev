repo: beets
source_path: /Users/zijian/Bmk-dev-main/repo-pool/beets-master
commit: unknown - source snapshot has no .git metadata
src_loc: 36252
test_functions: 1677
test_files: 133
dominant_test_styles: unit and integration pytest tests over dbcore/library/query/path formatting, CLI command helpers, plugin behavior, filesystem state, and mocked HTTP/service integrations; no snapshot files detected
public_docs: README.rst; docs/reference/cli.rst; docs/reference/config.rst; docs/reference/query.rst; docs/reference/pathformat.rst; docs/api/database.rst; docs/dev/library.rst; docs/plugins/index.rst and plugin pages
core_fact_source: the beets music library state, centered on SQLite library.db rows for items/albums plus associated media-file paths, tags, configuration, and plugin metadata
derived_views: beet CLI commands such as import/list/modify/move/write/fields/config; Python Library/Item/Album/dbcore query APIs; generated filesystem paths and tag writes; plugin command outputs and exports/playlists/web views
external_deps: runtime deps include confuse, mediafile, jellyfish, lap/numpy, PyYAML, requests, requests-ratelimiter, unidecode; optional plugins touch MusicBrainz/Discogs/Spotify/Tidal/ListenBrainz/Plex/Subsonic and binaries such as ffmpeg/ImageMagick/fpcalc/mp3gain; isolation plan is to prefer core/library/path/query/CLI tests plus plugin tests with requests_mock/responses/monkeypatch/local tmp dirs and filter live service/binary-dependent cases
test_import_audit: clean - grep/AST pre-screen found 0/133 test files (0.0%) with module-level from beets._ or import beets._ imports under test/
docs_test_alignment: aligned - public user, reference, API, and developer docs cover the same CLI, library database, query, path-format, config, and plugin projections exercised by the tests, though Stage 3 should filter tests tied only to beets.test helpers or beetsplug._utils internals
contamination_note: beets@2.12.0 plus unreleased master snapshot, released June 22, 2026, relative to training cutoff: after
decision: keep
reason: beets is a large pure-Python library manager with durable SQLite/filesystem facts, multiple documented public projections, a broad mostly isolated pytest suite, and a clean beets._ private-import pre-screen.
risks: Some tests target developer/internal-adjacent APIs, beets.test helpers, private beetsplug._utils modules, exact CLI/log text, optional plugin extras, external services, or local binaries; Stage 3 will need aggressive filtering toward documented public behavior and mocked/local integrations.
