# spec_test_map — rrule-recurrence-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::datetime builds a Date carrying the given UTC calendar components | atomic | positive | section Dates And The UTC Convention | covered | RRULE-DTC-002 |
| atomic::Frequency is a numeric enum from YEARLY=0 to SECONDLY=6 with reverse lookup | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-001 |
| atomic::RRule mirrors the frequency values and lists FREQUENCIES in value order | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-001 |
| atomic::ALL_WEEKDAYS lists the two-letter tokens Monday-first | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-003 |
| atomic::weekday constants use Monday=0 numbering and stringify as tokens | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-003 |
| atomic::getJsWeekday converts to JavaScript Sunday=0 numbering | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-003 |
| atomic::Weekday.fromStr parses tokens and equals compares weekday and ordinal | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-003 |
| atomic::nth produces an ordinal weekday with signed token rendering | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-004 |
| atomic::equals distinguishes ordinal from plain weekdays | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-003, RRULE-DEF-004 |
| atomic::a zero ordinal is rejected | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-003 |
| atomic::origOptions echoes exactly the caller-supplied options | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-001 |
| atomic::options fills every recognized key with defaults | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-002 |
| atomic::freq defaults to YEARLY when omitted | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-001 |
| atomic::byweekday accepts Weekday, integer and token forms and normalizes to numbers | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-002, RRULE-NRM-003 |
| atomic::ordinal weekday entries split into bynweekday pairs | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-003 |
| atomic::bymonthday splits positive and negative values | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-004 |
| atomic::a yearly rule derives month and month-day from its start date | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-005 |
| atomic::monthly and weekly rules derive their missing date-level constraint from dtstart | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-005 |
| atomic::time-of-day components derive from dtstart for daily and coarser rules | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-005 |
| atomic::wkst normalizes Weekday to its number and keeps integers | atomic | positive | section Defining A Recurrence | covered | RRULE-NRM-006 |
| atomic::an invalid dtstart is rejected at construction | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-001 |
| atomic::clone returns an equivalent independent rule | atomic | positive | section Defining A Recurrence | covered | RRULE-DEF-005 |
| atomic::all returns the full ascending occurrence list | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-001 |
| atomic::all stops at the first occurrence for which the iterator returns false | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-002 |
| atomic::between excludes both endpoints by default | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-003 |
| atomic::between includes endpoint occurrences when inc is true | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-003 |
| atomic::an inverted between window yields an empty array | atomic | positive | section Occurrence Enumeration + section Error Semantics | covered | RRULE-ENM-003, RRULE-ERR-012 |
| atomic::before returns the latest occurrence strictly before, or at with inc | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-004 |
| atomic::after returns the earliest occurrence strictly after, or at with inc | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-004 |
| atomic::before and after return null when nothing qualifies | atomic | positive | section Occurrence Enumeration + section Error Semantics | covered | RRULE-ENM-004, RRULE-ERR-013 |
| atomic::count returns the total number of occurrences | atomic | positive | section Occurrence Enumeration | covered | RRULE-ENM-005 |
| atomic::non-Date arguments to windowed queries are rejected | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-008 |
| atomic::a frequency outside the enumeration is rejected at construction | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-006 |
| atomic::a zero bysetpos is rejected at construction | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-007 |
| atomic::interval strides whole frequency periods | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-001 |
| atomic::finer-grained by-rules multiply occurrences within each period | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-002 |
| atomic::negative bymonthday counts back from the end of the month | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-003 |
| atomic::byyearday supports negative indices and honors leap years | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-003 |
| atomic::byweekno selects ISO week numbers | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-004 |
| atomic::a positive ordinal weekday picks the n-th matching weekday of the month | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-005 |
| atomic::a negative ordinal weekday counts from the end of a bymonth-constrained year | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-005 |
| atomic::bysetpos -1 selects the last candidate of each period | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-006 |
| atomic::bysetpos mixes positions from both ends of the candidate list | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-006 |
| atomic::hourly and secondly frequencies stride at their own granularity | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-008 |
| atomic::an occurrence equal to until is included and nothing after it | atomic | positive | section Expansion Semantics | covered | RRULE-EXP-009 |
| atomic::a monthly rule pinned to the 31st skips shorter months | atomic | positive | section Expansion Semantics + section Defining A Recurrence | covered | RRULE-EXP-002, RRULE-NRM-005 |
| atomic::toString emits DTSTART and only caller-supplied rule properties | atomic | positive | section RFC String Projection | covered | RRULE-STR-001 |
| atomic::explicitly supplied default values still serialize | atomic | positive | section RFC String Projection | covered | RRULE-STR-002 |
| atomic::ordinal weekdays, negative month days and numeric wkst serialize as tokens | atomic | positive | section RFC String Projection | covered | RRULE-STR-003 |
| atomic::optionsToString serializes an options object directly | atomic | positive | section RFC String Projection | covered | RRULE-STR-004 |
| atomic::a rule constructed without dtstart emits no DTSTART line | atomic | positive | section RFC String Projection | covered | RRULE-STR-001 |
| atomic::parseString reads a bare property list into partial options | atomic | positive | section RFC String Projection | covered | RRULE-STR-005 |
| atomic::parseString reads DTSTART and RRULE lines and date-only UNTIL as UTC midnight | atomic | positive | section RFC String Projection | covered | RRULE-STR-005, RRULE-STR-006 |
| atomic::unknown properties and malformed timestamps are rejected | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-004, RRULE-ERR-005 |
| atomic::rrulestr picks RRule or RRuleSet from the input shape | atomic | positive | section RFC String Projection | covered | RRULE-STR-007, RRULE-STR-008 |
| atomic::rrulestr merges its dtstart option into rules lacking DTSTART | atomic | positive | section RFC String Projection | covered | RRULE-STR-008 |
| atomic::toText renders frequency, weekday list and count | atomic | positive | section Natural Language Projection | covered | RRULE-NLP-001 |
| atomic::toText covers interval, month-day, week-number and until families | atomic | positive | section Natural Language Projection | covered | RRULE-NLP-001, RRULE-NLP-002 |
| atomic::parseText maps a phrase to partial options and null when uninterpretable | atomic | positive | section Natural Language Projection + section Error Semantics | covered | RRULE-NLP-003, RRULE-ERR-011 |
| atomic::fromText builds a weekday rule from a phrase | atomic | positive | section Natural Language Projection | covered | RRULE-NLP-004 |
| atomic::accessors reflect added sources | atomic | positive | section Recurrence Sets | covered | RRULE-SET-001 |
| atomic::wrongly typed sources are rejected | atomic | failure_path | section Error Semantics | covered | RRULE-ERR-009, RRULE-ERR-010 |
| atomic::a dates-only set enumerates in ascending order | atomic | positive | section Recurrence Sets | covered | RRULE-SET-002 |
| atomic::valueOf lists the iCalendar lines of every source | atomic | positive | section Recurrence Sets | covered | RRULE-SET-003 |
| integration::fromString(toString) reproduces the occurrence sequence of a weekday rule | integration | positive | section Cross-View Invariants | covered | RRULE-CVI-001; CVI-001 |
| integration::fromString(toString) survives ordinal weekdays and set positions | integration | positive | section Cross-View Invariants + section Expansion Semantics | covered | RRULE-CVI-001, RRULE-EXP-006; CVI-001 |
| integration::optionsToString(parseString(s)) reproduces a bare rule string | integration | positive | section RFC String Projection | covered | RRULE-STR-004, RRULE-STR-005; Seam: parseString->optionsToString |
| integration::a parsed rule enumerates directly from its string definition | integration | positive | section RFC String Projection + section Occurrence Enumeration | covered | RRULE-STR-005, RRULE-ENM-001; Seam: parse->expansion |
| integration::an until-bounded rule keeps its inclusive bound across the string view | integration | positive | section Cross-View Invariants + section Expansion Semantics | covered | RRULE-CVI-001, RRULE-EXP-009; CVI-001 |
| integration::derived dtstart defaults survive the string view without being serialized | integration | positive | section Defining A Recurrence + section RFC String Projection + section Cross-View Invariants | covered | RRULE-NRM-005, RRULE-STR-001, RRULE-CVI-001; CVI-001 |
| integration::wkst changes the emitted sequence of a biweekly multi-weekday rule | integration | positive | section Expansion Semantics + section Defining A Recurrence | covered | RRULE-EXP-007, RRULE-NRM-006; Seam: normalization->weekly expansion |
| integration::windowed queries agree with the full expansion | integration | positive | section Cross-View Invariants | covered | RRULE-CVI-003; CVI-003 |
| integration::origOptions and options never disagree on caller-supplied values | integration | positive | section Cross-View Invariants + section Defining A Recurrence | covered | RRULE-CVI-002, RRULE-NRM-001, RRULE-NRM-002; CVI-002 |
| integration::clone preserves every projection of a rule | integration | positive | section Cross-View Invariants + section Defining A Recurrence | covered | RRULE-CVI-007, RRULE-DEF-005; CVI-007 |
| integration::unbounded rules stream through the iterator callback | integration | positive | section Occurrence Enumeration + section Expansion Semantics | covered | RRULE-ENM-002, RRULE-EXP-001; Seam: unbounded generation->callback |
| integration::a fully convertible rule survives toText/parseText with the same recurrence | integration | positive | section Cross-View Invariants + section Natural Language Projection | covered | RRULE-CVI-005, RRULE-NLP-003; CVI-005 |
| integration::fromText(toText) preserves the recurrence properties of an interval rule | integration | positive | section Cross-View Invariants + section Natural Language Projection | covered | RRULE-CVI-005, RRULE-NLP-004; CVI-005 |
| integration::a phrase-driven rule enumerates and serializes consistently | integration | positive | section Natural Language Projection + section Expansion Semantics + section Cross-View Invariants | covered | RRULE-NLP-003, RRULE-EXP-001, RRULE-CVI-001; CVI-001 |
| integration::a set merges rule occurrences with rdates and drops exdates | integration | positive | section Recurrence Sets | covered | RRULE-SET-002; Seam: rrule+rdate+exdate->all |
| integration::an exclusion rule removes every instant it generates | integration | positive | section Recurrence Sets | covered | RRULE-SET-002; Seam: rrule+exrule->all |
| integration::duplicate instants from different sources appear once | integration | positive | section Recurrence Sets + section Cross-View Invariants | covered | RRULE-SET-002, RRULE-CVI-004; CVI-004 |
| integration::windowed queries on a set follow single-rule inclusivity semantics | integration | positive | section Recurrence Sets + section Occurrence Enumeration | covered | RRULE-SET-002, RRULE-ENM-003, RRULE-ENM-004; Seam: set->between/before/after |
| integration::count on a set equals the merged sequence length | integration | positive | section Cross-View Invariants + section Recurrence Sets | covered | RRULE-CVI-003, RRULE-SET-002; CVI-003 |
| integration::set clones are independent of later mutation | integration | positive | section Cross-View Invariants + section Recurrence Sets | covered | RRULE-CVI-007, RRULE-SET-001; CVI-007 |
| integration::rrulestr rebuilds a set from its own toString including exclusion rules | integration | positive | section Cross-View Invariants + section RFC String Projection + section Recurrence Sets | covered | RRULE-CVI-004, RRULE-STR-007, RRULE-SET-003; CVI-004 |
| integration::a multi-line recurrence text parses to the same merged stream it serializes | integration | positive | section Cross-View Invariants + section RFC String Projection | covered | RRULE-CVI-004, RRULE-STR-007; CVI-004 |
| integration::build, persist, restore and query a rule across every view | integration | positive | section Cross-View Invariants + section Natural Language Projection | covered | RRULE-CVI-001, RRULE-CVI-003, RRULE-NLP-001; CVI-001 |
| integration::a quarterly schedule set merges weekly and month-end rules and round-trips | integration | positive | section Cross-View Invariants + section Expansion Semantics + section Recurrence Sets | covered | RRULE-CVI-004, RRULE-EXP-006, RRULE-SET-002; CVI-004 |
| integration::a phrase becomes a persisted schedule whose restored form matches all views | integration | positive | section Cross-View Invariants + section Natural Language Projection | covered | RRULE-CVI-001, RRULE-CVI-005, RRULE-NLP-003; CVI-001 |
| integration::exception management workflow: cancel and reschedule occurrences, then persist | integration | positive | section Cross-View Invariants + section Recurrence Sets | covered | RRULE-CVI-004, RRULE-SET-002, RRULE-SET-003; CVI-004 |

Total: 90 | kept (covered): 90 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 90

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
