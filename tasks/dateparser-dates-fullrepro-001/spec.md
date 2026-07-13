<!-- INTERNAL
task_id: dateparser-dates-fullrepro-001
spec_version: v2
delta: clarifies no-spaces-time compact digit parsing, TO_TIMEZONE awareness for timezone-bearing input, and past-week RETURN_TIME_SPAN boundary/time semantics; excludes timezone implementation object shape
source_boundary: dateparser/__init__.py; dateparser/date.py public signatures and docstrings; dateparser/search/__init__.py; dateparser/search/search.py public signatures and docstrings; dateparser/conf.py validation surface; docs/usage.rst; docs/settings.rst; docs/dateparser.rst; docs/custom_language_detection.rst; pyproject.toml console script declaration
-->

# dateparser Specification

## Product Overview

dateparser converts human-readable date and time text into Python `datetime.datetime` objects. It accepts absolute dates, relative expressions, timestamps, localized month and weekday names, language and locale hints, and settings that control ambiguous or incomplete input.

The library exposes a convenient one-call parser, a reusable parser object that returns date metadata, and a text search function that extracts date expressions from larger prose. All parsing failures return `None` in the success-return position unless the caller supplied an invalid argument or invalid setting.

## Scope

This specification covers these user-facing behaviors:

- `dateparser.parse()` for single date/time strings.
- `dateparser.date.DateDataParser` and `DateDataParser.get_date_data()` for reusable parsing with period and locale metadata.
- `dateparser.search.search_dates()` for extracting date expressions from text.
- Documented parser settings that affect date order, language order, incomplete dates, relative dates, parser selection, Unicode normalization, timezone handling, strictness, required parts, and search time spans.
- Error semantics for invalid input types, unknown languages/locales, invalid settings, and invalid `DateData` item access.

The covered behavior is intentionally limited to public parsing and search contracts. Raw locale dictionaries, parser-internal token streams, private parser functions, calendar converter classes, and the download console command are outside this scope.

## Installable Surface

The package must be importable as `dateparser`.

The following public imports must be available:

```python
from dateparser import parse, DateDataParser
from dateparser.date import DateData, DateDataParser
from dateparser.search import search_dates
from dateparser.conf import SettingValidationError
```

`dateparser.parse` has this call signature:

```python
parse(
    date_string,
    date_formats=None,
    languages=None,
    locales=None,
    region=None,
    settings=None,
    detect_languages_function=None,
)
```

`DateDataParser` has this constructor signature:

```python
DateDataParser(
    languages=None,
    locales=None,
    region=None,
    try_previous_locales=False,
    use_given_order=False,
    settings=None,
    detect_languages_function=None,
)
```

`DateDataParser.get_date_data` has this call signature:

```python
get_date_data(date_string, date_formats=None)
```

`dateparser.search.search_dates` has this call signature:

```python
search_dates(
    text,
    languages=None,
    settings=None,
    add_detected_language=False,
    detect_languages_function=None,
)
```

The package declares a `dateparser-download` console script for data management. The parsing API does not require callers to use that command.

## Product State Model

The core state is the caller's date text plus three optional sources of parsing context:

- Language context: explicit `languages`, explicit `locales`, a `region`, a custom `detect_languages_function`, parser-level previous-locale memory, and `DEFAULT_LANGUAGES`.
- Interpretation context: settings such as `DATE_ORDER`, `PREFER_LOCALE_DATE_ORDER`, `RELATIVE_BASE`, `PREFER_DAY_OF_MONTH`, `PREFER_MONTH_OF_YEAR`, `PREFER_DATES_FROM`, `REQUIRE_PARTS`, `STRICT_PARSING`, and `PARSERS`.
- Timezone context: timezone text embedded in the date string, `TIMEZONE`, `TO_TIMEZONE`, and `RETURN_AS_TIMEZONE_AWARE`.

The same parse result has three public projections:

- `parse()` returns only the parsed `datetime.datetime` or `None`.
- `DateDataParser.get_date_data()` returns a `DateData` object with `date_obj`, `period`, and `locale`.
- `search_dates()` returns matched substrings paired with parsed datetimes, and returns the detected language when requested.

These projections must agree for the same caller-visible inputs:

- When `DateDataParser.get_date_data()` returns a `DateData` whose `date_obj` is not `None`, `parse()` returns that same datetime for the same date string, date formats, language context, and settings.
- When `DateDataParser.get_date_data()` cannot parse a string, its `date_obj` is `None` and `parse()` returns `None` for the same context.
- When `search_dates()` extracts a substring and parses it, parsing the meaningful date expression from that substring with the same language and settings returns the same datetime.
- When a caller fixes `RELATIVE_BASE`, all public projections that interpret relative or incomplete dates must use that fixed base rather than the current system clock.

## Public API

### `parse`

`parse()` returns a `datetime.datetime` when the input string is recognized under the supplied context. It returns `None` when the input string is syntactically valid as a string but contains no parseable date.

`date_formats` restricts parsing to the supplied `strptime`-style formats before falling through according to the configured parser order. A matching format returns a datetime with the period implied by the missing fields. If no format matches and no configured parser recognizes the text, `parse()` returns `None`.

`languages` must be a list, tuple, or set of language codes when provided. `locales` must be a list, tuple, or set of locale codes when provided. `region` must be a string when provided. Invalid argument types raise `TypeError`. Unknown language or locale codes raise `ValueError`.

`detect_languages_function` is used only when neither `languages` nor `locales` is provided. The function is called with keyword arguments `text` and `confidence_threshold`, and must return language codes. If it returns no usable languages and `DEFAULT_LANGUAGES` is not set, parsing returns `None`.

### `DateData` and `DateDataParser`

`DateData` represents a parse result with three public attributes:

- `date_obj`: the parsed `datetime.datetime`, or `None`.
- `period`: one of `"time"`, `"day"`, `"week"`, `"month"`, or `"year"`.
- `locale`: the locale code that produced the parse, or `None`.

`DateData` supports dictionary-style access for exactly these keys. Reading or writing an unknown key raises `KeyError`.

`DateDataParser.get_date_data()` returns `DateData`. It raises `TypeError` when `date_string` is not a string. Its `date_formats` argument follows the same format behavior as `parse()`.

`DateDataParser` remembers previously successful locales only when constructed with `try_previous_locales=True`. In that mode, later calls must try previously successful locales before normal detection. When `try_previous_locales=False`, each call must resolve locales from the constructor arguments, detection function, settings, and defaults without using previous successes.

`use_given_order=True` requires `languages` or `locales` to be supplied. If it is true without either, construction raises `ValueError`. When enabled, the parser must try supplied languages/locales in caller order. The same ordering rule applies when `settings={"USE_GIVEN_LANGUAGE_ORDER": True}` is passed.

### `search_dates`

`search_dates()` scans prose and returns a list of tuples. Each tuple contains the matched substring and the parsed `datetime.datetime`. It returns `None` when no parseable date expression is found.

When `add_detected_language=True`, each tuple has a third item containing the detected language code.

When `languages` is provided, `search_dates()` must search using those languages and must not invoke `detect_languages_function`. When no languages are provided and `detect_languages_function` is supplied, that function is called with `text` and `confidence_threshold`.

When search language detection cannot identify a candidate language and no default language applies, the public function returns `None`.

## Settings Behavior

### Date Order and Language Order

`DATE_ORDER` controls how numeric dates are interpreted. Supported values are permutations of `D`, `M`, and `Y`, such as `"MDY"`, `"DMY"`, and `"YMD"`. Invalid values raise `SettingValidationError`.

`PREFER_LOCALE_DATE_ORDER` defaults to true. When the caller does not supply `DATE_ORDER`, a detected or supplied locale with its own date order determines numeric date interpretation. When the caller supplies `DATE_ORDER`, that explicit order must be used for numeric date interpretation. `PREFER_LOCALE_DATE_ORDER=False` also requires the caller's configured `DATE_ORDER` to be used.

`USE_GIVEN_LANGUAGE_ORDER` defaults to false. When false, supplied languages/locales are tried in the library's normal language priority order. When true, supplied languages/locales and fallback `DEFAULT_LANGUAGES` must be tried in caller order. This setting affects `parse()` and `DateDataParser`; `search_dates()` uses its own search language detection and must not use this setting to disambiguate numeric dates.

### Incomplete and Relative Dates

`RELATIVE_BASE` supplies the base datetime for relative expressions and incomplete dates. When supplied, relative expressions such as `"tomorrow"`, `"yesterday"`, and `"2 weeks ago"` must be computed from that base.

`PREFER_DAY_OF_MONTH` controls missing day values for month-level dates. It accepts `"current"`, `"first"`, and `"last"`. With `"first"`, missing days resolve to day 1. With `"last"`, missing days resolve to the last day of the month. With `"current"`, missing days use the day from `RELATIVE_BASE` or the current date.

`PREFER_MONTH_OF_YEAR` controls missing month values for year-level dates. It accepts `"current"`, `"first"`, and `"last"`. With `"first"`, missing months resolve to January. With `"last"`, missing months resolve to December. With `"current"`, missing months use the month from `RELATIVE_BASE` or the current date.

`PREFER_DATES_FROM` accepts `"current_period"`, `"past"`, and `"future"`. For incomplete dates that have both a past and future interpretation around the base date, `"past"` chooses a date before or at the base period and `"future"` chooses a date after or at the base period.

`STRICT_PARSING=True` returns `None` for dates that omit any of year, month, or day. `REQUIRE_PARTS` returns `None` unless the parsed date contains every requested part from `["day", "month", "year"]`.

### Parser Selection, Formats, and Normalization

`PARSERS` controls which parser families are attempted and in what order. Supported names are `"timestamp"`, `"negative-timestamp"`, `"relative-time"`, `"custom-formats"`, `"absolute-time"`, and `"no-spaces-time"`. Unknown parser names make the settings invalid and raise `SettingValidationError`.

`"no-spaces-time"` is not enabled by default. When explicitly selected, it parses compact date/time text made only of digits, or digits plus non-digits where the first non-digit is a colon. Six-digit compact dates use one- or two-digit month/day fields followed by a four-digit year; for example, `"121994"` returns `datetime(1994, 1, 2)`. If the compact text cannot be interpreted by this parser and no other configured parser recognizes it, `parse()` returns `None`.

`NORMALIZE` defaults to true. When true, Unicode accents and diacritics are normalized before matching language words. When false, the parser must require the input spelling to match the locale data without that normalization.

`SKIP_TOKENS` is a list of tokens discarded during language detection. It must affect language detection without changing the returned datetime for otherwise equivalent parseable input.

### Timezone Behavior

If the input string contains a timezone abbreviation or UTC offset, parsing must account for that timezone. When no conversion setting is supplied, the parsed wall time is returned with timezone information only when `RETURN_AS_TIMEZONE_AWARE=True` or when the parser's documented behavior for that input keeps timezone information.

`TIMEZONE` localizes the parsed datetime to the named timezone or abbreviation. `TO_TIMEZONE` converts the result to the target timezone after localization. When the input string itself contains timezone information and `TO_TIMEZONE` is supplied, the returned datetime must be timezone-aware and must represent the converted instant in the target timezone. `RETURN_AS_TIMEZONE_AWARE=False` returns a naive datetime when timezone-aware return values are not requested. `RETURN_AS_TIMEZONE_AWARE=True` returns a timezone-aware datetime when the input or settings provide timezone context. Timezone-aware results must expose normal `datetime` timezone behavior such as `tzinfo`, `tzname()`, and `utcoffset()`; they do not require a particular timezone implementation class or provider-specific attribute.

Unix timestamps are interpreted by the `"timestamp"` parser. Negative timestamps are interpreted by the `"negative-timestamp"` parser. `TIMEZONE` and `TO_TIMEZONE` must apply to timestamp results in the same way they apply to other parsed datetimes.

### Search Time Spans

`RETURN_TIME_SPAN=True` makes `search_dates()` detect span expressions such as `"past month"` and append start and end entries for the matched span. `DEFAULT_DAYS_IN_MONTH` controls how many days are used for month-like relative spans.

For `"past week"`, the span is the completed week immediately before the week containing `RELATIVE_BASE`, not a rolling seven-day interval ending at `RELATIVE_BASE`. `DEFAULT_START_OF_WEEK="monday"` makes the completed week run Monday through Sunday. `DEFAULT_START_OF_WEEK="sunday"` makes the completed week run Sunday through Saturday. The generated start and end datetimes preserve the time of day from `RELATIVE_BASE`. When `RELATIVE_BASE` is omitted, the same rules apply using the current datetime as the base.

## Error Semantics

Invalid setting names or invalid setting values raise `SettingValidationError`.

Invalid `languages` type raises `TypeError`. Unknown language codes raise `ValueError`.

Invalid `locales` type raises `TypeError`. Unknown locale codes raise `ValueError`.

Invalid `region` type raises `TypeError`.

`DateDataParser(use_given_order=True)` raises `ValueError` when neither `languages` nor `locales` is supplied.

`DateDataParser.get_date_data()` raises `TypeError` when the date input is not a string.

`DateData` raises `KeyError` for dictionary-style reads or writes using keys other than `date_obj`, `period`, and `locale`.

Unparseable but well-typed date text returns `None` from `parse()` and returns `DateData(date_obj=None, period="day" or the applicable attempted period, locale=None)` from `DateDataParser.get_date_data()`.

## Cross-View Invariants

- `parse(text, settings=s)` must return the same datetime as `DateDataParser(settings=s).get_date_data(text)["date_obj"]` when both calls use the same language, locale, region, format, detection, and settings context.
- `parse()` must return `None` exactly when `DateDataParser.get_date_data()` returns a `DateData` whose `date_obj` is `None` for the same context.
- `DateData.period` must describe the precision of the parsed text: `"day"` for complete dates, `"month"` for missing-day dates, `"year"` for year-only dates, and `"time"` when `RETURN_TIME_AS_PERIOD=True` and the input includes a time component.
- `DateData.locale` must identify the locale that produced the parse when a locale was selected, and must be `None` when no locale can parse the input.
- `search_dates(text, languages=[lang], settings=s)` must return datetimes that agree with parsing the corresponding date expression using `parse(..., languages=[lang], settings=s)`.
- `add_detected_language=True` must add a language code to each search tuple without changing the matched substring or datetime.
- Fixed `RELATIVE_BASE` must make relative and incomplete date results deterministic across `parse()`, `DateDataParser`, and `search_dates()`.
- `TIMEZONE`, `TO_TIMEZONE`, and `RETURN_AS_TIMEZONE_AWARE` must affect top-level parsing and `DateDataParser` consistently for the same input.
- Invalid argument and setting errors must be raised before returning partial parse results.

## Representative Workflows

### Reusing a Parser for Related Inputs

```python
from datetime import datetime
from dateparser.date import DateDataParser

parser = DateDataParser(languages=["de", "nl"])
first = parser.get_date_data("vr jan 24, 2014 12:49")
second = parser.get_date_data("18.10.14 um 22:56 Uhr")
missing = parser.get_date_data("11 July 2012")

assert first["date_obj"] == datetime(2014, 1, 24, 12, 49)
assert first["locale"] == "nl"
assert second["date_obj"] == datetime(2014, 10, 18, 22, 56)
assert second["locale"] == "de"
assert missing["date_obj"] is None
```

### Parsing Search Results with a Fixed Base

```python
from datetime import datetime
from dateparser.search import search_dates

settings = {"RELATIVE_BASE": datetime(2020, 1, 15, 9, 30)}
result = search_dates("Ship it tomorrow and review it on 17 January 2020", languages=["en"], settings=settings)

assert result[0][1] == datetime(2020, 1, 16, 9, 30)
assert result[1][1] == datetime(2020, 1, 17, 0, 0)
```

## Non-Goals

This specification does not require:

- Compatibility with private modules such as parser tokenizers or underscored parsing helpers.
- Exact `repr()` text for `DateData`, timezone objects, or internal parser objects.
- Raw locale dictionary shape, locale loader cache shape, or language data file contents.
- Calendar converter classes for Jalali or Hijri calendars.
- Pickle compatibility of internal timezone classes.
- Downloading or refreshing language data through the `dateparser-download` command.
- Matching exact exception message wording.

## Invocation Protocol

The supported programmatic invocation is importing and calling the Python APIs listed above.

`python -m dateparser` is not supported.

The `dateparser-download` console script is declared by the package. It is outside the parsing contract covered here.

Exit code expectations:

- Successful Python API calls return their documented values and do not set process exit codes.
- Import failures, syntax errors, and uncaught exceptions in user code follow normal Python process behavior.
- The covered parsing API signals user errors through Python exceptions, not process exit codes.

## Evaluation Notes

The scoring checks exercise public parsing behavior from the perspective of a caller using the documented API. They cover successful absolute parsing, relative parsing with fixed bases, incomplete-date settings, language and locale hints, custom language detection, search result shape, timezone conversion, deterministic cross-view agreement, and documented error types.

The checks avoid private parser modules, raw language fixtures, exact exception message text, exact object representations, and system-clock-dependent assertions. Correct implementations are expected to pass by following the public behavior described here, even when their internal parser organization differs from the original package.
