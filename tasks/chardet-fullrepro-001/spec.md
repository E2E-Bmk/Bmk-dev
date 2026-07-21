# Chardet Specification

## Product Overview

Chardet identifies the character encoding, confidence, language, and MIME type of byte sequences. It supports one-shot detection, ranked candidate detection, incremental streaming, encoding-era filters, compatibility naming, binary-file signatures, and a command-line interface.

Every public detection route uses the same result model. Text results name an encoding and use MIME type `text/plain` or a more specific text type. Binary results use `encoding=None` and identify a known MIME type when a magic signature is recognized.

## Scope

This document covers:

- `detect` and `detect_all` result shape and option behavior;
- ASCII, UTF-8, BOM, null-byte, control-byte, binary-signature, and CJK behavior;
- encoding eras, compatibility names, legacy-name remapping, confidence thresholds, and byte limits;
- `UniversalDetector` streaming parity and compatibility options;
- `chardetect` file, standard-input, version, and minimal-output workflows.

Statistical model files, registry internals, private pipeline stages, accuracy corpora, thread performance studies, and private helper modules are outside this scope.

## Installable Surface

The distribution is installed and imported as:

```python
import chardet
from chardet import EncodingEra, LanguageFilter, UniversalDetector
```

The top-level package exports `detect`, `detect_all`, `UniversalDetector`, `EncodingEra`, `LanguageFilter`, `DetectionDict`, `DetectionResult`, `DEFAULT_MAX_BYTES`, `MINIMUM_THRESHOLD`, and `__version__`.

The distribution provides the `chardetect` console command. `python -m chardet.cli` invokes the same command behavior.

## Product State Model

Detection state has four public projections:

- Best-result projection: `detect(data, ...)` returns one result dictionary.
- Ranked projection: `detect_all(data, ...)` returns result dictionaries in descending confidence order.
- Streaming projection: `UniversalDetector.feed` and `close` expose the best result for accumulated bytes.
- Command projection: `chardetect` renders the best result for a file or standard input.

For the same bytes and options, `detect(data)` must equal `detect_all(data)[0]`. Feeding those bytes to a fresh `UniversalDetector` and closing it must return the same best result. The command must render the encoding returned by the Python API. Naming and era options must be applied consistently to all three Python routes.

## Basic Detection

```python
detect(
    byte_str,
    should_rename_legacy=False,
    encoding_era=EncodingEra.ALL,
    chunk_size=...,
    max_bytes=DEFAULT_MAX_BYTES,
    *,
    prefer_superset=False,
    compat_names=True,
    include_encodings=None,
    exclude_encodings=None,
    no_match_encoding="cp1252",
    empty_input_encoding="utf-8",
)
```

`byte_str` accepts `bytes` and `bytearray`. The result is a dictionary with exactly four keys:

- `encoding`: the selected encoding name, or `None` for binary data;
- `confidence`: a float from 0.0 through 1.0;
- `language`: an ISO-style language identifier or `None`;
- `mime_type`: the detected MIME type or `None`.

Plain ASCII returns encoding `ascii`, confidence `1.0`, and MIME type `text/plain`. UTF-8 multibyte text returns `utf-8`. Empty input returns the configurable empty-input encoding, which defaults to `utf-8`, with confidence `0.10` and MIME type `text/plain`.

`max_bytes` limits the inspected prefix. Data after that prefix must not change the result. It must be a positive integer and must not be a boolean.

## ASCII And Binary Boundaries

ASCII text may contain common whitespace bytes. Printable bytes from 0x20 through 0x7E remain ASCII. Any high byte prevents the ASCII result.

Null-separated ASCII remains text when null bytes are no more than 5 percent of the inspected bytes. Such text returns `ascii` with confidence `0.99`; this includes NUL-separated paths and exactly one NUL among 20 bytes. A null fraction above 5 percent prevents the ASCII result.

Binary classification treats tab, line feed, and carriage return as text controls. Other control bytes and NUL bytes are binary when they exceed 1 percent of the inspected bytes. Exactly one control byte among 100 bytes remains text; two among 100 produce `encoding=None` and MIME type `application/octet-stream`. Binary bytes after `max_bytes` are ignored.

Recognized magic signatures take precedence over character statistics. GIF, JPEG, and MP4 signatures return `encoding=None`, confidence `1.0`, and MIME types `image/gif`, `image/jpeg`, and `video/mp4` respectively. Unknown binary content returns `encoding=None` with `application/octet-stream`.

## BOM Handling

Complete byte-order marks have confidence `1.0` and take precedence over statistical detection:

- UTF-8 BOM returns compatibility name `UTF-8-SIG`.
- UTF-16 little- and big-endian BOMs return `UTF-16`.
- UTF-32 little- and big-endian BOMs return `UTF-32`.

UTF-32 little-endian begins with the UTF-16 little-endian prefix and must be considered first. A bare four-byte UTF-32 little-endian BOM is valid. A UTF-32-looking prefix whose remaining payload is not a multiple of four falls back to UTF-16 when the bytes also form a valid UTF-16 little-endian prefix. The corresponding malformed big-endian form has no UTF-16 fallback and proceeds through normal binary handling.

One or two initial bytes of a UTF-8 BOM are incomplete and must not return `UTF-8-SIG`.

## Encoding Options And Ranking

`EncodingEra` is an `IntFlag` with `MODERN_WEB`, `LEGACY_ISO`, `LEGACY_MAC`, `LEGACY_REGIONAL`, `DOS`, `MAINFRAME`, and their union `ALL`. Eras may be combined with bitwise OR. The default is `ALL`. A restricted era removes encodings outside that set; for example, `MODERN_WEB` must not return legacy `ISO-8859-7` for Greek data for which `ALL` selects that encoding.

With `compat_names=True`, names use the chardet compatibility spelling, including `EUC-JP`, `UTF-8-SIG`, `UTF-16`, and `UTF-32`. With `compat_names=False`, raw codec names such as `euc_jis_2004`, `shift_jis_2004`, and `cp932` are returned.

`prefer_superset=True` maps subset encodings to preferred supersets. The deprecated `should_rename_legacy=True` has the same result and emits `DeprecationWarning`. For ASCII, the remapped compatibility name is `Windows-1252`; with the option false, it remains `ascii`.

```python
detect_all(
    byte_str,
    ignore_threshold=False,
    should_rename_legacy=False,
    encoding_era=EncodingEra.ALL,
    chunk_size=...,
    max_bytes=DEFAULT_MAX_BYTES,
    **keyword_options,
)
```

`detect_all` returns a non-empty list sorted by descending confidence. Each item has the same four keys as `detect`. With `ignore_threshold=False`, candidates at or below `MINIMUM_THRESHOLD` (`0.20`) are removed. If that would remove every result, the unfiltered best result remains available. With `ignore_threshold=True`, low-confidence candidates are retained.

## Streaming Detection

`UniversalDetector` accepts the same era, byte-limit, naming, include/exclude, and fallback options as `detect`. `feed(bytes)` accumulates input up to `max_bytes`. `close()` finalizes and returns a four-key result dictionary; repeated access through `result` returns that state. `reset()` permits reuse.

`should_rename_legacy` and `compat_names` affect streaming results exactly as they affect one-shot results. `lang_filter` remains accepted for compatibility but does not alter candidates. `LanguageFilter.ALL` emits no warning; any other value emits one `DeprecationWarning` mentioning `lang_filter`.

## CJK Candidate Gating

Western text must not become a CJK result solely because some byte pairs are valid in a CJK codec. EBCDIC text must not be labeled `gb18030`, Latin text must not be labeled `cp932`, and MacRoman German text must not be labeled as a CJK encoding.

Real Japanese Shift-JIS text remains `shift_jis_2004` or `cp932` in raw-name mode. Real Chinese GB18030 and Korean EUC-KR text must retain an appropriate CJK candidate rather than being removed by the Western-text guard.

## Command Line

`chardetect FILE` and `python -m chardet.cli FILE` read at most `DEFAULT_MAX_BYTES`, exit with status 0 on success, and print the filename, encoding, and confidence. UTF-8 files include `utf-8`; ASCII files include `ascii`.

With no file argument, the command reads standard input and labels the normal output as `stdin`. `--minimal` prints only the encoding name followed by a newline. `--version` prints `chardet VERSION`, where the version begins with a digit, and exits with status 0.

The public command also accepts `-e/--encoding-era`, `-i/--include-encodings`, `-x/--exclude-encodings`, `--no-match-encoding`, `--empty-input-encoding`, and `-l/--language`.

## Error Semantics

- `max_bytes` values that are non-positive or boolean raise `ValueError` from one-shot, ranked, and streaming construction routes.
- A non-`ALL` `lang_filter` emits `DeprecationWarning`; `LanguageFilter.ALL` does not.
- `should_rename_legacy=True` is accepted and emits `DeprecationWarning` while applying preferred-superset naming.
- Calling `feed` after `close` without `reset` raises `ValueError`.
- Error message wording is not part of this contract except that compatibility warnings identify the deprecated option.

## Cross-View Invariants

- `detect(data)` must equal `detect_all(data)[0]` for identical options.
- A fresh streaming detector fed the same bytes must close with the same result as `detect`.
- Binary MIME recognition must be independent of encoding-era filtering.
- Compatibility naming and preferred-superset naming must agree across one-shot, ranked, and streaming routes.
- `max_bytes` must select the same inspected prefix across all routes.
- Complete BOMs must override statistical and ASCII results in every route.
- The command-line encoding must match the best Python result for the same bytes.
- Every result dictionary must retain the same four-key shape regardless of encoding, binary status, or confidence.

## Representative Workflow

```python
import chardet
from chardet import EncodingEra, UniversalDetector

data = "Héllo wörld".encode("utf-8")
best = chardet.detect(data, encoding_era=EncodingEra.MODERN_WEB)
ranked = chardet.detect_all(data, encoding_era=EncodingEra.MODERN_WEB)
assert ranked[0] == best

stream = UniversalDetector(encoding_era=EncodingEra.MODERN_WEB)
stream.feed(data[:4])
stream.feed(data[4:])
assert stream.close() == best
```

## Non-Goals

Private pipeline modules, private helper return types, model tables, source layout, corpus files, build accelerators, network access, and exact diagnostic wording are not public requirements.

## Invocation Protocol

| Invocation | Supported |
|---|---|
| Python imports shown above | yes |
| `chardetect ...` | yes |
| `python -m chardet.cli ...` | yes |
| `python -m chardet ...` | not required by this surface |

Successful file and standard-input detection exits with status 0. Argument parsing and complete input failure use non-zero status.

## Environment

Runtime dependencies and packaged model data must be declared through `requirements.txt`, `pyproject.toml`, and normal Python package-data configuration. The implementation may use packages available from PyPI.
