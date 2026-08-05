# dateparser Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

dateparser converts human-readable date and time text into Python `datetime.datetime` objects. It accepts absolute dates, relative expressions, timestamps, localized month and weekday names, language and locale hints, and settings that control ambiguous or incomplete input.

The library exposes a convenient one-call parser, a reusable parser object that returns date metadata, and a text search function that extracts date expressions from larger prose. All parsing failures return `None` in the success-return position unless the caller supplied an invalid argument or invalid setting.

## Non-Goals

This specification does not require:

- Compatibility with private modules such as parser tokenizers or underscored parsing helpers.
- Exact `repr()` text for `DateData`, timezone objects, or internal parser objects.
- Raw locale dictionary shape, locale loader cache shape, or language data file contents.
- Calendar converter classes for Jalali or Hijri calendars.
- Pickle compatibility of internal timezone classes.
- Downloading or refreshing language data through the `dateparser-download` command.
- Matching exact exception message wording.

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

## Date Order and Language Handling

Date order and language selection determine how ambiguous numeric dates and multilingual text are interpreted.

**Date order.** `DATE_ORDER` controls how numeric dates are interpreted. Supported values are permutations of `D`, `M`, and `Y`, such as `"MDY"`, `"DMY"`, and `"YMD"`. Invalid values must raise `SettingValidationError`. When a caller supplies an explicit `DATE_ORDER`, that order must be used for numeric date interpretation regardless of detected locale.

**Locale date order.** `PREFER_LOCALE_DATE_ORDER` defaults to true. When the caller does not supply `DATE_ORDER`, a detected or supplied locale with its own date order must determine numeric date interpretation. When `PREFER_LOCALE_DATE_ORDER` is false, the caller's configured `DATE_ORDER` must be used.

**Language order.** `USE_GIVEN_LANGUAGE_ORDER` defaults to false. When false, supplied languages/locales are tried in the library's normal language priority order. When true, supplied languages/locales and fallback `DEFAULT_LANGUAGES` must be tried in caller order. This setting affects `parse()` and `DateDataParser`.

**Default languages.** `DEFAULT_LANGUAGES` provides fallback languages when no explicit languages are supplied and automatic detection fails.

**Custom language detection.** `detect_languages_function` supplies a custom callable for language detection. When `languages` are supplied, the custom detector must not be called. When `languages` are not supplied, the detector must be called with the text and a confidence threshold of `0.5`.

**Language restriction.** When `DateDataParser` is constructed with `languages=["de", "nl"]`, only those languages must be tried. Input in an unlisted language (e.g., English when only German and Dutch are specified) must return a `DateData` with `date_obj=None` and `locale=None`.

**Locale memory.** When `try_previous_locales=True`, the parser must remember previously successful locales and try them first on subsequent calls.

## Incomplete and Relative Dates

Settings control how ambiguous, incomplete, and relative date expressions are resolved.

**Relative base.** `RELATIVE_BASE` supplies the base datetime for relative expressions and incomplete dates. Expressions such as `"tomorrow"`, `"yesterday"`, `"2 weeks ago"`, `"in 3 days"`, `"in 2 hours"`, and `"30 minutes ago"` must be computed from that base, preserving the base's time-of-day components.

**Preferred day of month.** `PREFER_DAY_OF_MONTH` controls missing day values. It accepts `"current"`, `"first"`, and `"last"`. With `"first"`, missing days must resolve to day 1. With `"last"`, missing days must resolve to the last day of the month.

**Preferred month of year.** `PREFER_MONTH_OF_YEAR` controls missing month values. It accepts `"current"`, `"first"`, and `"last"`. With `"first"`, missing months must resolve to January. With `"last"`, missing months must resolve to December.

**Date direction preference.** `PREFER_DATES_FROM` accepts `"current_period"`, `"past"`, and `"future"`. For incomplete dates that have both a past and future interpretation, `"past"` must choose a date before or at the base period and `"future"` must choose a date after or at the base period.

**Strict parsing.** `STRICT_PARSING=True` must return `None` for dates that omit any of year, month, or day. `REQUIRE_PARTS` must return `None` unless the parsed date contains every requested part from `["day", "month", "year"]`.

## Parser Selection, Formats, and Normalization

Settings control which parser families are used and how input text is normalized before matching.

**Custom date formats.** When `date_formats` is supplied to `parse()` or `get_date_data()`, those strftime-style format strings must be tried for matching. A format like `"%Y/%d/%m"` must parse dates with swapped day/month fields.

**Parser list.** `PARSERS` controls which parser families are attempted and in what order. Supported names are `"timestamp"`, `"negative-timestamp"`, `"relative-time"`, `"custom-formats"`, `"absolute-time"`, and `"no-spaces-time"`. Unknown parser names must raise `SettingValidationError`.

**No-spaces-time parser.** `"no-spaces-time"` is not enabled by default. When explicitly selected, it must parse compact date/time text; for example, `"121994"` must return `datetime(1994, 1, 2)`.

**Negative timestamps.** The `"negative-timestamp"` parser must interpret negative numeric strings as pre-epoch UTC datetimes.

**Unicode normalization.** `NORMALIZE` defaults to true. When true, Unicode accents and diacritics must be normalized before matching. When false, input spelling must match locale data without normalization. For example, unaccented French `"decembre"` must parse when `NORMALIZE=True` and must fail when `NORMALIZE=False`.

**Skip tokens.** `SKIP_TOKENS` is a list of tokens discarded during language detection. It must affect language detection without changing the returned datetime for otherwise equivalent parseable input.

**Return time as period.** `RETURN_TIME_AS_PERIOD=True` must cause `DateData.period` to report `"time"` when the input includes a time component.

## Timezone Behavior

Timezone settings control how parsed datetimes are localized and converted.

**Input timezone.** When the input string contains a timezone abbreviation or UTC offset, parsing must account for that timezone.

**Timezone localization.** `TIMEZONE` localizes the parsed datetime to the named timezone or abbreviation. `TO_TIMEZONE` converts the result to the target timezone after localization. When both are supplied, the returned datetime must represent the converted instant in the target timezone.

**Timezone awareness control.** `RETURN_AS_TIMEZONE_AWARE=False` must return a naive datetime. `RETURN_AS_TIMEZONE_AWARE=True` must return a timezone-aware datetime when the input or settings provide timezone context. Timezone-aware results must expose `tzinfo`, `tzname()`, and `utcoffset()`.

**Timestamp timezone.** `TIMEZONE` and `TO_TIMEZONE` must apply to timestamp results in the same way they apply to other parsed datetimes.

## Search and Time Spans

`search_dates` extracts date expressions from prose text and returns matched substrings paired with parsed datetimes.

**Basic search.** `search_dates(text, languages=[...])` must find date expressions in the text and return them as `(matched_substring, datetime)` tuples in order. Multiple dates in a single text must all be extracted.

**Detected language.** When `add_detected_language=True`, each result tuple must include a third element with the language code. The matched substring and datetime must remain unchanged.

**Relative search.** When `RELATIVE_BASE` is supplied, relative expressions such as `"tomorrow"` must be computed from that base.

**Time spans.** `RETURN_TIME_SPAN=True` must detect span expressions such as `"past month"` and append start and end entries. `DEFAULT_DAYS_IN_MONTH` controls month-like relative span length.

**Past week spans.** For `"past week"`, the span must be the completed week immediately before the week containing `RELATIVE_BASE`. `DEFAULT_START_OF_WEEK="monday"` must make the completed week run Monday through Sunday. `DEFAULT_START_OF_WEEK="sunday"` must make it run Sunday through Saturday. Start and end datetimes must preserve the time of day from `RELATIVE_BASE`.

## State Model

The core state is the caller's date text plus three optional sources of parsing context:

- Language context: explicit `languages`, explicit `locales`, a `region`, a custom `detect_languages_function`, parser-level previous-locale memory, and `DEFAULT_LANGUAGES`.
- Interpretation context: settings such as `DATE_ORDER`, `PREFER_LOCALE_DATE_ORDER`, `RELATIVE_BASE`, `PREFER_DAY_OF_MONTH`, `PREFER_MONTH_OF_YEAR`, `PREFER_DATES_FROM`, `REQUIRE_PARTS`, `STRICT_PARSING`, and `PARSERS`.
- Timezone context: timezone text embedded in the date string, `TIMEZONE`, `TO_TIMEZONE`, and `RETURN_AS_TIMEZONE_AWARE`.

The same parse result has three public projections:

- `parse()` returns only the parsed `datetime.datetime` or `None`.
- `DateDataParser.get_date_data()` returns a `DateData` object with `date_obj`, `period`, and `locale`.
- `search_dates()` returns matched substrings paired with parsed datetimes, and returns the detected language when requested.

These projections must agree for the same caller-visible inputs:

- When `DateDataParser.get_date_data()` returns a `DateData` whose `date_obj` is not `None`, `parse()` must return that same datetime for the same date string, date formats, language context, and settings.
- When `DateDataParser.get_date_data()` cannot parse a string, its `date_obj` must be `None` and `parse()` must return `None` for the same context.
- When `search_dates()` extracts a substring and parses it, parsing the meaningful date expression from that substring with the same language and settings must return the same datetime.
- When a caller fixes `RELATIVE_BASE`, all public projections that interpret relative or incomplete dates must use that fixed base rather than the current system clock.

## Error Semantics

Invalid setting names or invalid setting values must raise `SettingValidationError`.

Invalid `languages` type must raise `TypeError`. Unknown language codes must raise `ValueError`.

Invalid `locales` type must raise `TypeError`. Unknown locale codes must raise `ValueError`.

Invalid `region` type must raise `TypeError`.

`DateDataParser(use_given_order=True)` must raise `ValueError` when neither `languages` nor `locales` is supplied.

`DateDataParser.get_date_data()` must raise `TypeError` when the date input is not a string.

`DateData` must raise `KeyError` for dictionary-style reads or writes using keys other than `date_obj`, `period`, and `locale`.

Unparseable but well-typed date text must return `None` from `parse()` and must return `DateData(date_obj=None, period="day" or the applicable attempted period, locale=None)` from `DateDataParser.get_date_data()`.

## Cross-View Invariants

1. `parse(text, settings=s)` must return the same datetime as `DateDataParser(settings=s).get_date_data(text)["date_obj"]` when both calls use the same language, locale, region, format, detection, and settings context.
2. `parse()` must return `None` exactly when `DateDataParser.get_date_data()` returns a `DateData` whose `date_obj` is `None` for the same context.
3. `DateData.period` must describe the precision of the parsed text: `"day"` for complete dates, `"month"` for missing-day dates, `"year"` for year-only dates, and `"time"` when `RETURN_TIME_AS_PERIOD=True` and the input includes a time component.
4. `DateData.locale` must identify the locale that produced the parse when a locale was selected, and must be `None` when no locale can parse the input.
5. `search_dates(text, languages=[lang], settings=s)` must return datetimes that agree with parsing the corresponding date expression using `parse(..., languages=[lang], settings=s)`.
6. `add_detected_language=True` must add a language code to each search tuple without changing the matched substring or datetime.
7. Fixed `RELATIVE_BASE` must make relative and incomplete date results deterministic across `parse()`, `DateDataParser`, and `search_dates()`.
8. `TIMEZONE`, `TO_TIMEZONE`, and `RETURN_AS_TIMEZONE_AWARE` must affect top-level parsing and `DateDataParser` consistently for the same input.
9. Invalid argument and setting errors must be raised before returning partial parse results.

## Public Interface

### Import Surface

The package must be importable as `dateparser`.

The following public imports must be available:

```python
from dateparser import parse, DateDataParser
from dateparser.date import DateData, DateDataParser
from dateparser.search import search_dates
from dateparser.conf import SettingValidationError
```

The package declares a `dateparser-download` console script for data management. The parsing API does not require callers to use that command.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| parse | function | Parse human-readable date text into a datetime |
| DateDataParser | class | Reusable parser returning date metadata |
| DateData | class | Parse result with date_obj, period, and locale |
| search_dates | function | Extract date expressions from prose text |
| SettingValidationError | exception | Raised for invalid setting names or values |

### CLI Entry Points

The supported programmatic invocation is importing and calling the Python APIs listed above.

`python -m dateparser` is not supported.

The `dateparser-download` console script is declared by the package. It is outside the parsing contract covered here.

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

The three parsing entry points should share one interpretation of language, date-order, relative-base, and timezone settings. A reusable parser may cache caller-visible locale preferences, but that cache must not change the results promised for an equivalent one-shot parse.

Internal parser modules, raw language-data layout, exception wording, object representations, and the choice of timezone provider are implementation details. Only the public values, exceptions, and cross-view relationships described above are stable contracts.
