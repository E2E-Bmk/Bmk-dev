# gix-config Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

═══════════════════════════════════ Context Layer ═══════════════════════════════════

## Product Overview

`gix-config` is a Rust library that reads, queries, mutates and rewrites files in the
`git-config` text format while preserving everything it did not deliberately change.
The installable crate name is `gix-config`, and the type callers interact with is `File`.

A `File` is a lossless in-memory model of one configuration text. Parsing it and writing it
back reproduces the original bytes — including comments, indentation, blank lines, quoting
style, legacy section-header spellings and mixed line endings. Editing a single value
rewrites only that value's bytes; every unrelated byte survives untouched. This makes the
library usable for programs that must edit a user's configuration file in place without
reformatting it.

On top of that lossless layer sits a resolution layer that implements the `git-config`
lookup rules: section and value names match case-insensitively while subsection names match
byte-exactly, a name declared more than once forms a multivar, single-value lookups resolve
to the last declaration in file order, and values are normalized (quote-stripped and
unescaped) before being handed to the caller. Typed accessors convert normalized values into
booleans, integers, colors and paths. Every section carries metadata describing where it came
from — a `Source` classification, an optional path, an include level and a trust level — and
every read API has a filtered variant that consults that metadata, so a caller that merged
several configuration files together restricts a lookup to the sources it trusts.

## Non-Goals

- This specification does not define discovery or loading of configuration files from the
  filesystem, from environment variables, or from a repository layout. Construction happens
  from bytes or strings that the caller already holds.
- This specification does not require support for `include` and `includeIf` directives.
  A key named `include.path` must be treated as an ordinary value with no side effects, and
  no conditional-inclusion predicates are evaluated.
- This specification does not define a public syntactic event stream, token type, or
  low-level parser API. The grammar described in this document is an internal concern of the
  implementation; no type describing individual lexical events is publicly reachable.
- This specification does not define a whole-file reformatter that normalizes indentation,
  separator spacing or newline style across an entire document.
- This specification does not require serialization support through `serde`, and does not
  define any `Serialize` or `Deserialize` implementation or any cargo feature enabling one.
- This specification does not define object-hash selection features, reference-name parsing,
  or glob matching.
- This specification does not require thread-safe interior mutability. Shared ownership of
  metadata is by reference-counted handle, and `File` itself is mutated through `&mut self`.

═════════════════════════════════ Orientation Layer ═════════════════════════════════

## Representative Workflows

**Workflow 1 — read a configuration, resolve a multivar, and query typed values.**

```rust
use gix_config::File;

let input = r#"
# a leading comment
[core]
    bare = true
    repositoryformatversion = 0
[remote "origin"]
    url = https://example.invalid/a.git
    fetch = +refs/heads/*:refs/remotes/origin/*
    fetch = +refs/tags/*:refs/tags/*
[remote "upstream"]
    url = https://example.invalid/b.git
"#;

let config = File::try_from(input)?;

// Dotted keys address section, optional subsection, and value name.
assert_eq!(config.string("remote.origin.url").unwrap(), "https://example.invalid/a.git");

// Typed accessors normalize, then convert.
assert_eq!(config.boolean("core.bare")?, Some(true));
assert_eq!(config.integer("core.repositoryformatversion")?, Some(0));

// A name declared twice is a multivar; `strings` returns every declaration in file order.
assert_eq!(config.strings("remote.origin.fetch").unwrap().len(), 2);

// A single-value lookup of a multivar resolves to the last declaration.
assert_eq!(config.string("remote.origin.fetch").unwrap(),
           "+refs/tags/*:refs/tags/*");

// Missing keys are absent, not errors, for the comfort accessors.
assert!(config.string("core.missing").is_none());

// The raw accessors report why a lookup failed.
assert!(matches!(config.raw_value("nosuch.key"),
                 Err(gix_config::lookup::existing::Error::SectionMissing)));

// Sections with the same name are visited in file order.
let names: Vec<_> = config
    .sections_by_name("remote")
    .expect("at least one")
    .map(|s| s.header().subsection_name().unwrap().to_string())
    .collect();
assert_eq!(names, ["origin", "upstream"]);
# Ok::<(), Box<dyn std::error::Error>>(())
```

**Workflow 2 — mutate a configuration in place and write it back losslessly.**

```rust
use gix_config::File;

let mut config = File::try_from("[core]\n\t# keep me\n\tbare = false\n")?;

// Editing an existing value rewrites only that value's bytes.
let previous = config.set_raw_value("core.bare", "true")?;
assert_eq!(previous.unwrap(), "false");
assert_eq!(config.to_string(), "[core]\n\t# keep me\n\tbare = true\n");

// Setting a key in an absent section creates the section.
config.set_raw_value("user.name", "Jane Doe")?;

// Section-level editing reuses the whitespace style already present in the section.
let mut section = config.section_mut("core", None)?;
section.push("editor", Some("vi".into()))?;
assert_eq!(section.value("editor").unwrap(), "vi");

// Values that need protection are quoted and escaped on the way in,
// and unescaped again on the way out.
config.set_raw_value("user.comment", " # not a comment ")?;
assert_eq!(config.raw_value("user.comment")?, " # not a comment ");

// A removed section is a self-contained value that is re-insertable.
let removed = config.remove_section("user", None).expect("present");
config.push_section(removed)?;

// Writing back reproduces every byte the edits did not touch.
let mut out = Vec::new();
config.write_to(&mut out)?;
assert_eq!(out, config.to_bstring());
# Ok::<(), Box<dyn std::error::Error>>(())
```

══════════════════════════════════ Behavior Layer ══════════════════════════════════

## Configuration Text Format

This section defines the text format that a `File` reads and writes. The grammar is
line-oriented; the implementation must accept every construction described here and must
preserve every byte it does not rewrite.

**Section headers.** A section header occupies its own logical line and must take one of
three forms. `[name]` declares a section with no subsection. `[name "subsection"]` declares a
section whose subsection name is the quoted text; the separator between name and subsection
must be whitespace, and the quoted text is unescaped when read. `[name.subsection]` is the
legacy spelling; the separator is a literal `.` and the subsection text is taken raw, without
quoting or unescaping. A header must report `is_legacy() == true` exactly when its separator
is `.`. WHEN a header that has not been renamed is written back, THEN the separator it was
parsed with must be reproduced, so such a legacy header must never be rewritten into the
quoted form and such a quoted header must never be rewritten into the legacy form. WHEN a
header is rewritten by `SectionMut::rename`, `rename_section` or `rename_section_filter`,
THEN the modern quoted form must be emitted regardless of the form the header was parsed
with, so a legacy header `[branch.source]` renamed to the identity it already carries must
serialize as `[branch "source"]`.

**Header validation.** A section name written into a header must consist only of ASCII
alphanumeric characters and `-`; the empty section name is accepted, and so is the empty
subsection name. IF a section name violates this rule, THEN every operation that constructs
or renames a header must return `parse::section::header::Error::InvalidName`.
A subsection name must not contain a newline (`\n`) or a null byte (`\0`), and must otherwise
accept arbitrary bytes including spaces, quotes and backslashes. IF a subsection name
contains either forbidden byte, THEN header construction must return
`parse::section::header::Error::InvalidSubSection`. The free function
`parse::section::header::is_valid_subsection` must return `false` for exactly those inputs.
The separate validated type `parse::section::Name` applies a stricter rule than the header
does: each of its `TryFrom` conversions must additionally reject the empty name, and must
report that rejection as `parse::section::name::Error` rather than as a header error.

**Value names and separators.** Inside a section body, a value line begins with a value name,
followed optionally by `=` and the value. A value name must be non-empty, must consist only
of ASCII alphanumeric characters and `-`, and must begin with an ASCII alphabetic character.
IF a value name violates this rule, THEN every operation that writes a value under that name
must return `parse::section::value_name::Error`. Whitespace before the name, before the `=`,
and after the `=` is insignificant to the meaning of the value and must be preserved
verbatim on write. `=` is the only accepted separator.

**Implicit values.** WHEN a value name appears with no `=` separator, THEN the entry must be
recorded as an implicit value: it exists, it has no value text, and it is distinguishable
from a name assigned the empty string. `value_implicit` must return `Some(None)` for an
implicit entry, `Some(Some(text))` for an entry with a value, and `None` when the name is
absent. `value` must return `None` for an implicit entry.

**Comments.** A comment begins at an unquoted `#` or `;` and runs to the end of the line.
Comments must be preserved verbatim on write, both when they occupy a whole line and when
they trail a value.

**Quoting, escaping and continuation.** A value is a mixture of quoted and unquoted runs; a
value such as `5"hello world"` is legal and must be accepted. Inside a value, the only
recognized escape sequences are `\n`, `\t`, `\b` and `\\`, plus `\"` inside a quoted run.
A `\` at the very end of a line is a line continuation: the newline is consumed and the value
continues on the following line, both inside and outside quotes. Trailing whitespace after an
unquoted value is not part of the value; leading whitespace on a continuation line is part of
the value. WHEN the line following a continuation marker contributes no value text — because
it is empty, because it holds only a comment, or because the input ends there — THEN the
value terminates at the continuation marker, so each of `[core]\n\tk = abc\\\n\n`,
`[core]\n\tk = abc\\\n; comment\n` and `[core]\n\tk = abc\\` declares the single value `abc`.
WHEN the following line does carry text, THEN that text continues the value even when it is
shaped like a new value line, so `[core]\n\tk = abc\\\n\tk = def\n` declares one value whose
text is `abc\tk = def`.

**Frontmatter and byte-order marks.** Value lines that appear before the first section header
must be accepted and preserved. A UTF-8 byte-order mark at the start of the input must be
accepted and must not become part of any name or value.

**Line endings.** Both `\n` and `\r\n` must be accepted, including within one document. A run
of consecutive line endings must be preserved as written.

**Size limit.** WHEN the input handed to construction is larger than `u32::MAX` bytes, THEN
construction must fail with `parse::Error`, whose message is
`Configuration input is {n} bytes large, but at most 4294967295 bytes are supported` for an
input of `{n}` bytes. The distinct type `parse::span::Error` reports the append-time failure
instead: it is returned when a write, an append or a reinsertion would push the backing text
past `u32::MAX` bytes.

## Loading and Construction

This section defines how a `File` comes into existence and what each entry point promises
about metadata and fidelity.

**Empty files.** `File::default()` must return an empty file whose metadata equals
`file::Metadata::api()`. `File::new(meta)` must return an empty file carrying the supplied
metadata. An empty file must serialize to the empty byte string, must report
`num_values() == 0`, and must report `is_void() == true`.

**Parsing from text.** `File::try_from(&str)`, `File::try_from(&BStr)` and
`str::parse::<File>()` must each parse the input and attach `file::Metadata::api()` to every
resulting section. Their error type must be `parse::Error`.

**Parsing with metadata.** `File::from_bytes_no_includes(input, meta, options)` must parse
`input`, attach `meta` to every resulting section, and honour `options`. Its error type must
be `file::init::Error`. `File::from_bytes_owned(input_and_buf, meta, options)` must parse the
current contents of the supplied buffer and must otherwise answer exactly as
`from_bytes_no_includes` does over the same bytes, with the same metadata attachment, the
same honouring of `options` and the same `file::init::Error` error type; the resulting `File`
must borrow nothing from the buffer.

**Lossy loading.** WHERE `options.lossy` is `true`, THEN only value-bearing content must be
retained: comments, whitespace and newlines are discarded. A file loaded this way must still
answer every read query identically to a losslessly loaded file, and must still serialize to
valid configuration text — but the text will not reproduce the input. WHERE `options.lossy`
is `false` (its default), THEN serialization must reproduce the input byte for byte.

**Parse failures.** IF the input is not valid configuration text, THEN construction must
return a `parse::Error`. `line_number()` must return the one-based line on which the failure
occurred, and `remaining_data()` must return the unparsed remainder that caused it. The
`Display` form must be
`Got an unexpected token on line {line} while trying to parse a {parser}: '{data}'`, where a
remainder longer than ten characters is truncated to its first ten characters followed by
` ... ({n} characters omitted)`. The `{parser}` token must be exactly one of the three
literals `section header`, `name` and `value`, naming the construct that was being parsed
when the failure occurred. A size-limit failure must instead display as
`Configuration input is {n} bytes large, but at most 4294967295 bytes are supported`, and
must report `line_number() == 1` and an empty `remaining_data()`.

**Composition.** `File::append(other)` must move every section of `other` to the end of the
receiver, preserving each section's own metadata and its surrounding non-value content, and
must return `&mut Self`. IF the combined text would exceed the supported size, THEN `append`
must return `parse::span::Error`.

## Key Resolution and Section Lookup

This section defines how a caller names something and which declaration answers.

**Dotted keys.** Every method whose name has no `_by` suffix accepts a key through the
`AsKey` trait. A key is split once on its **first** `.` to yield the section name, and the
remainder is split once on its **last** `.`; when the remainder contains no further `.`, the
key has no subsection. `remote.origin.url` therefore resolves to section `remote`, subsection
`origin`, value name `url`; `core.bare` resolves to section `core`, no subsection, value name
`bare`; and `remote.with.dots.url` resolves to subsection `with.dots`. `AsKey::try_as_key`
must return `None` when the input has fewer than two `.`-separated tokens or is not valid
UTF-8, and `AsKey::as_key` must panic in exactly those cases. `AsKey` must be implemented for
`&str`, `&String`, `&BStr`, `&BString`, for `KeyRef<'_>` itself, and blanket-implemented for
`&T where T: AsKey`. Which of the two an accessor uses is itself part of the contract: every
comfort accessor (`string`, `path`, `boolean`, `integer`, `strings`, `integers` and their
`_filter` forms) must split through `try_as_key` and must therefore report an unsplittable
key as absence — `None` for the `Option`-returning families and `Ok(None)` for the
`Result`-returning ones — while every raw accessor, every typed `value*` accessor and every
key-taking mutator must split through `as_key` and must therefore panic on the same input.

**Explicit three-part addressing.** Every method whose name ends in `_by` accepts the section
name, an optional subsection name and the value name as three separate arguments. The
optional subsection is expressed through `AsBStrOpt`, so both `None` and a plain string
literal are accepted at the call site. The `_by` form and the dotted form must be
behaviorally identical once the key is split.

**Case rules.** Section names and value names must match case-insensitively over ASCII.
Subsection names must match byte-exactly, so `[remote "Origin"]` and `[remote "origin"]` are
two different sections. A name's original spelling must be preserved on write regardless of
how it was matched, including for legacy headers.

**Which section answers.** `section(name, subsection)` must return the **last** matching
section in file order. `section_filter(name, subsection, filter)` must consider matching
sections from last to first and return the first one whose metadata satisfies `filter`.
IF no section carries the requested name, THEN both must fail with
`lookup::existing::Error::SectionMissing`. IF sections carry the name but none carries the
requested subsection, THEN both must fail with `lookup::existing::Error::SubSectionMissing`;
requesting no subsection when every section of that name has one must also produce
`SubSectionMissing`. IF matching sections exist but `filter` rejects all of them, THEN
`section_filter` must return `Ok(None)` rather than an error.
`section_by_key` and `section_filter_by_key` accept a two-part key such as `core` or
`remote.origin`, and must fail with `lookup::existing::Error::KeyMissing` when the key cannot
be split at all.

**Enumeration.** `sections()` must yield every section in file order.
`sections_and_ids()` must yield the same sections paired with their identifiers.
`sections_by_name(name)` must return `None` when no section carries the name, and otherwise
an iterator over every section of that name — across all subsections and the
no-subsection case alike — in file order. `sections_by_name_and_filter` must additionally
drop sections whose metadata fails the filter, and must return `None` when the name is
absent. `section_ids(&mut self)` must yield every identifier in file order and takes `&mut
self`.

**Section identity.** Each section carries a `SectionId` that is unique for the lifetime of
the `File` and is never reused after a removal. Identifiers must be monotonically increasing
at allocation time but must not be assumed to reflect file order after mutation, and must not
be assumed to be contiguous. `SectionId::default()` must equal the identifier built from
`usize::MAX`, which no allocated section holds.

**Counting.** `num_values()` must return the total number of value entries across all
sections, counting each declaration of a multivar separately. `is_void()` must return `true`
exactly when the file holds no value entries at all; a file consisting only of empty section
headers must report `is_void() == true`.

## Raw Value Access

This section defines the unconverted-value layer. Every raw accessor must return bytes after
normalization but before any type conversion, and must report absence as an error rather than
as `None`.

**Single values.** `raw_value(key)` must resolve the key and return the value of the **last**
matching declaration: matching sections are considered from last to first, and within a
section the last declaration of the name wins. Implicit entries must be skipped during this
search, so a name that appears only without a separator must not satisfy a single-value
lookup. IF no declaration remains after that search, THEN the call must fail with
`lookup::existing::Error::KeyMissing`. `raw_value_with_section` must return the value paired
with the section it came from. `raw_value_filter` and `raw_value_with_section_filter` must
restrict the search to sections whose metadata satisfies the filter, and must fail with
`KeyMissing` when the filter leaves no candidate.

**Multiple values.** `raw_values(key)` must return every declaration of the name, collected in
file order across every matching section and in declaration order within each section. IF no
declaration exists, THEN the call must fail with `lookup::existing::Error::KeyMissing`; an
empty vector is never returned. `raw_values_with_sections` must pair each value with its
section, and the `_filter` variants must restrict the search by metadata.

**Mutable handles.** `raw_value_mut(key)` must return a `ValueMut` addressing the same
declaration that `raw_value` would have returned, and `raw_values_mut(key)` must return a
`MultiValueMut` addressing the same set that `raw_values` would have returned. Both must fail
with the same errors as their read-only counterparts.

**Assigning to an existing value.** `set_existing_raw_value(key, new_value)` must overwrite
the declaration that `raw_value` resolves to and must return `()`. IF the key does not exist,
THEN it must fail with `set_raw_value::Error::Lookup` wrapping the corresponding
`lookup::existing::Error`; no section and no value is created.

**Assigning with creation.** `set_raw_value(key, new_value)` must overwrite the last matching
declaration when one exists and must return the previous value as `Some`. WHEN no matching
section exists, THEN the section must be created at the end of the file and the value
appended, and the call must return `None`. WHEN the section exists but the value name does
not, THEN the value must be appended to that section and the call must return `None`.
`set_raw_value_filter` must select the section to modify by metadata, creating a new section
when the filter rejects every candidate. IF the value name is not a valid value name, THEN
the call must fail with `set_raw_value::Error::ValueName` and must not create a section — a
rejected assignment must leave the file byte-identical to what it was.

**Assigning a multivar.** `set_existing_raw_multi_value(key, new_values)` must zip the
supplied values against the existing declarations in order: surplus new values are discarded,
and surplus existing declarations are left unmodified. IF the key does not exist, THEN it
must fail with `set_raw_value::Error::Lookup`.

**Escaping on assignment.** Every raw assignment must escape the incoming bytes so that
reading the value back returns exactly what was written. The value must be wrapped in double
quotes exactly when it begins with ASCII whitespace, ends with ASCII whitespace, or contains
`;` or `#`. Independently of quoting, `\n` must be written as `\n`, a tab as `\t`, `"` as
`\"`, and `\` as `\\`.

## Typed Value Access

This section defines conversion from stored bytes to Rust values. Two families exist: a
`Result`-returning family that surfaces conversion errors, and a comfort family that folds
absence into `None`.

**Normalization.** Every value handed to a caller — by any accessor, raw or typed — must first
be normalized. Normalization strips enclosing quote pairs repeatedly while the text is at
least three bytes long, begins with `"`, ends with `"`, and the byte before the trailing quote
is not `\`. The literal input `""` normalizes to the empty string. After quote stripping,
escape sequences are resolved: `\n` becomes a line feed, `\t` becomes a tab, `\b` becomes
byte `0x08`, `\X` becomes `X` for any other `X`, and any remaining unescaped `"` is dropped.
WHEN the text contains neither `\` nor `"`, THEN normalization must return the input
unchanged without allocating. The free function `value::normalize` must expose exactly this
behavior.

**Generic conversion.** `value::<T>(key)` must return the last matching value converted
through `T: TryFrom<BString>`. IF the key is absent, THEN it must fail with
`lookup::Error::ValueMissing`. IF conversion fails, THEN it must fail with
`lookup::Error::FailedConversion` carrying `T::Error`. `values::<T>(key)` must convert every
declaration and fail on the first conversion error. `value_with_section` and
`values_with_sections` must additionally return the originating section.
`try_value::<T>(key)` must return `Ok(None)` when the key is absent and must propagate only
`T::Error`, never a lookup error.

**Comfort accessors.** `string(key)` must return the normalized value as `Option<BString>`,
and `strings(key)` must return every declaration as `Option<Vec<BString>>`; both return
`None` when the key is absent. `path(key)` must return `Option<Path>` without interpolating
it. `boolean(key)` must return `Result<Option<bool>, value::Error>` and `integer(key)` must
return `Result<Option<i64>, value::Error>`; both return `Ok(None)` when the key is absent and
`Err` when a present value fails to convert. `integers(key)` must return
`Result<Option<Vec<i64>>, value::Error>`. Each of the six comfort accessors must additionally
exist in `_by`, `_filter` and `_filter_by` forms, giving twenty-four methods in total.

**Implicit values as booleans.** WHEN a value name is present as an implicit entry, THEN
`boolean` must return `Ok(Some(true))`. This is the only single-value accessor that treats an
implicit entry as carrying a value. The multi-value accessors disagree with the single-value
ones about the same entry: WHEN a value name is present only as an implicit entry, THEN
`string` and `raw_value` must report absence, while `strings` must return a one-element
vector holding the empty string and `SectionRef::values` / `SectionMut::values` must likewise
yield one empty entry. `SectionRef::value` must still return `None` for that entry, and
`value_implicit` must return `Some(None)`.

**Integer suffixes and overflow.** An integer value accepts an optional `k`, `m` or `g`
suffix, matched case-insensitively so that `K`, `M` and `G` are accepted equally, and
multiplying by 1024, 1024², and 1024³ respectively. IF the multiplied result does not
fit in `i64`, THEN `integer` must fail with a `value::Error` whose `message` is
`Integer overflow` and whose `input` is the offending text.

**Booleans.** The accepted true spellings are `yes`, `on` and `true`; the accepted false
spellings are `no`, `off`, `false` and the empty string. Matching over those spellings is
case-insensitive. WHEN the text matches none of them but parses as an `i64`, THEN the
conversion must succeed, yielding `false` for zero and `true` for every non-zero value, so
`1`, `-1` and `0042` are all accepted. IF the text neither matches a spelling nor parses as
an `i64`, THEN conversion must fail with a `value::Error`.

## Section Mutation

This section defines the operations that add, remove, rename and reorder whole sections.
Every operation in it must keep the name lookup structures consistent with file order.

**Obtaining a mutable section.** `section_mut(name, subsection)` must return a `SectionMut`
for the last matching section, failing with `lookup::existing::Error` exactly as `section`
does. `section_mut_by_key` accepts a two-part key. `section_mut_by_id(id)` must return `None`
when no section carries that identifier. `section_mut_filter` and `section_mut_filter_by_key`
must return `Ok(None)` when matching sections exist but the filter rejects all of them.
`section_mut_or_create_new` must return the last matching section when one exists and
otherwise append a new one; `section_mut_or_create_new_filter` must append a new section when
the filter rejects every candidate. Both must fail with
`parse::section::header::Error` when the name or subsection is invalid.

**Creating sections.** `new_section(name, subsection)` must always append a new section, even
when a section of the same name already exists, and must return a `SectionMut` for it. The
new section must be terminated by a newline immediately, so that a section created and left
empty still serializes as a complete header line. The new section must inherit the file's
metadata. IF the name or subsection is invalid, THEN the call must fail with
`parse::section::header::Error` and must not modify the file.

**Removing sections.** `remove_section(name, subsection)` must remove and return the **last**
matching section, or return `None` when no section matches. `remove_section_by_id(id)` must
remove the section with that identifier or return `None`. `remove_section_filter` must remove
the last matching section that satisfies the filter, or return `None`. Removing the final
section that carried a given subsection must also retire that subsection from the lookup
structures, and removing the final section of a name must retire the name, so that a
subsequent lookup of that name reports `SectionMissing` rather than `SubSectionMissing`.

**Reinserting sections.** A removed section is a self-contained owned value. Mutating it
through `Section::to_mut()` and reinserting it with `push_section` must be supported;
`push_section` must append it, must assign it a **fresh** identifier distinct from the one it
had before removal, must leave its metadata unchanged, and must return a `SectionMut` for it.
Unlike `new_section`, `push_section` must not append a newline of its own: the reinserted
section must serialize to exactly the bytes it carried, and any newline that separates it
from what follows must come from the newline repair applied at serialization time.
IF reinsertion would exceed the supported size, THEN `push_section` must fail with
`parse::span::Error`.

**Renaming sections.** `rename_section(name, subsection, new_name, new_subsection)` must
rename **every** matching section, not only the last, and must leave any pre-existing section
already carrying the target name untouched — a rename that produces duplicates must produce
them rather than merging. `rename_section_filter` must rename every matching section that
satisfies the filter. IF the source name is absent, THEN the call must fail with
`rename_section::Error::Lookup`. IF matching sections exist but the filter rejects all of
them, THEN the call must fail with `rename_section::Error::Lookup` wrapping
`lookup::existing::Error::KeyMissing`. IF the new name or new subsection is invalid, THEN the
call must fail with `rename_section::Error::Section` and must leave the file unchanged.
Those three failures must be reported in that fixed precedence: the source lookup is
performed first, the filter-rejected-everything test second, and the new name and new
subsection are validated only after both succeed, so an absent source name must be reported
as `rename_section::Error::Lookup` even when the requested new name is itself invalid.

**Section metadata.** `meta()` must return the file-level metadata, `meta_owned()` must return
a shared handle to it, and `set_meta(meta)` must replace it and return `&mut Self`. Replacing
file-level metadata must not retroactively change the metadata already attached to existing
sections. `SectionMut::set_trust(trust)` must replace the trust level of that one section
alone, leaving other sections that shared the same metadata unaffected.

## Value Mutation

This section defines the three mutable views — a whole section, one value, and a multivar —
and the whitespace rules that govern what they write.

**Whitespace inheritance.** A `SectionMut` derives its writing style from the first value line
already present in the section: the whitespace before the value name, the whitespace before
the `=`, and the whitespace after the `=`. WHEN a section has no value line to learn from,
THEN the defaults must be one tab before the name and one space on each side of the `=`.
`separator_whitespace()` must return the pre-separator and post-separator whitespace as a
pair of options. `leading_whitespace()` must return the whitespace written before value names,
and `set_leading_whitespace(ws)` must replace it. `set_leading_whitespace` must panic when
given text that is not entirely whitespace.

**Newline style.** `File::detect_newline_style()` must return the first line ending found in
the document; a run containing `\r` must be reported as `\r\n` and a run without one as `\n`.
WHEN the document contains no line ending at all, THEN the platform newline must be
returned — `\r\n` on Windows and `\n` elsewhere. `SectionMut::newline()` must return the
newline that handle inserts. Which newline that is depends on where the handle came from:
every `SectionMut` handed out by a `File` — by `section_mut`, `section_mut_by_key`,
`section_mut_by_id`, `section_mut_filter`, `section_mut_filter_by_key`,
`section_mut_or_create_new`, `section_mut_or_create_new_filter`, `new_section`,
`push_section` or `raw_value_mut(…).into_section_mut()` — must use the **document's**
detected style even when the addressed section's own body uses a different one, while
`Section::to_mut()` on a detached owned section must use the style detected in that section's
own body, falling back to the platform newline when it holds none. `push_newline()` must
append one newline and
return `&mut Self`, failing with `parse::span::Error` when the size limit is exceeded.
`set_implicit_newline(on)` must control whether a pushed value is automatically terminated by
a newline, and must return `&mut Self`.

**Editing a section body.** `SectionMut::push(name, value)` must append a value line and
return `&mut Self`; passing `None` as the value must write an implicit entry with no
separator. `push_with_comment(name, value, comment)` must append the same line and then the
comment, in this exact shape: one space, then `#`, then — only WHEN the comment's first byte
is not ASCII whitespace — one further space, then the comment text with every `\n` replaced
by a space and every other byte, `\r` included, written through unchanged. `set(name, value)`
must overwrite the last declaration of the name and
return the previous value as `Some`, or append the value and return `None` when the name is
absent. `remove(name)` must remove the last declaration of the name and return its value, or
return `None`. `remove` must not validate `name`: a name that no declaration carries — whether
because it is absent or because it is not a writable name at all — must yield `None` rather
than an
error. `pop()` must remove the last value line of the section and return its name and
value as a pair, or return `None` when the section holds no value; `pop` must also discard
the whitespace, newline and comment events that belonged to that line. The three differ in
what they hand back: `pop()` must return the value **after** normalization, while `remove()`
and `set()` must return the previous value as the concatenation of its stored value bytes,
**before** normalization and therefore still escaped. IF a value name supplied
to `push`, `push_with_comment` or `set` is invalid, THEN the call must fail with
`file::section::value::Error::ValueName`. IF the write would exceed the supported size, THEN
it must fail with `file::section::value::Error::Span`. A rejected value name must leave the
section untouched: validation must happen before any event is written.

**Renaming through a section.** `SectionMut::rename(name, subsection)` must change that
section's header and return `&mut Self`, failing with `parse::section::header::Error` on an
invalid name or subsection.

**Reading through a mutable section.** `SectionMut` must expose the same read operations as
`SectionRef` — `value`, `value_implicit`, `values`, `value_names`, `contains_value_name`,
`header`, `body`, `id`, `meta` and `to_bstring` — and must additionally offer `section()`,
which hands out a `SectionRef` read-only view of the same section. `SectionMut` must also
expose `num_values` and `is_void` directly; `SectionRef` must not carry those two counters, so
from a `SectionRef` they are reached through `body()`, which does carry them.
`value_names` must yield one entry per value declaration, in declaration order, so a name
declared twice in the same section must appear twice.

**Single value handle.** `ValueMut::get()` must return the current value, failing with
`lookup::existing::Error` when the value has since been deleted. `set(bytes)` and
`set_string(text)` must replace it with the escaped form. `delete()` must remove the value
and must be idempotent: a second `delete()` on the same handle must not panic and must not
remove anything else. `section()` must return a read-only view of the containing section, and
`into_section_mut()` must consume the handle and yield a `SectionMut` for that section with
the borrow lifetime preserved.

**Multivar handle.** `MultiValueMut::get()` must return every addressed value in file order,
normalized, failing with `lookup::existing::Error::KeyMissing` when they have all been
deleted. `len()` must return the number of declarations the handle still addresses and
`is_empty()` must return whether that count is zero.
`set_at(index, bytes)` and `set_string_at(index, text)` must replace one value.
`set_values(iter)` must zip the supplied values against the addressed ones, discarding surplus
inputs and leaving surplus existing values unmodified. `set_all(bytes)` must assign the same
value to every addressed declaration. `delete(index)` must remove one, and `delete_all()`
must remove all of them and must leave the handle addressing nothing, so `len()` afterwards is
`0`. Every mutating method must fail with `parse::span::Error` when the size limit is
exceeded.

**Multivar indices.** The `index` accepted by `set_at`, `set_string_at` and `delete` addresses
the handle's own list of declarations, which is `len()` entries long, and that list shrinks as
entries are deleted. WHEN `delete(index)` succeeds, THEN the entry must be dropped from the
list and every later entry must move down one position, so `delete` is **not** idempotent:
calling `delete(0)` twice on a handle addressing two declarations must remove both of them,
which is the opposite of `ValueMut::delete`. IF `index` is not less than `len()`, THEN
`set_at`, `set_string_at` and `delete` must panic.

## Serialization

This section defines how a `File` becomes bytes again and what fidelity that conversion
promises.

**Entry points.** `to_bstring()` must return the complete document as a byte string.
`write_to(out)` must stream the same bytes to any `std::io::Write`. `Display` must render
what `to_bstring()` produces, and `From<File> for BString` must yield the same bytes.
`SectionRef::write_to(out)` and `SectionRef::to_bstring()` must render one section, header
included; `HeaderRef::to_bstring()` must render only the header line.

**Round-trip fidelity.** WHEN a file was loaded with `lossy` disabled and has not been
mutated, THEN serialization must reproduce the input byte for byte, including comments,
indentation, blank lines, quoting style, header spelling and mixed line endings. WHEN the
file has been mutated, THEN every byte outside the rewritten regions must be unchanged.

**Newline repair.** Serialization inserts newlines that were not in the text so that the
result stays parseable. Every newline inserted this way — at every position, including
between a section and the content that follows it — must be the **document's** detected style,
so a section body written in `\n` inside a document detected as `\r\n` must be separated by
`\r\n`. "Ends in a newline" must be decided by walking the trailing run of events whose text
is entirely ASCII whitespace and asking whether any of them contains the document's newline;
consequently a body whose own trailing newline is `\n` must count as **not** ending in a
newline while the document style is `\r\n`, and one further newline must be inserted after it.
WHEN content precedes the first section and does not end in a newline, THEN one newline must
be emitted before the first section, and WHEN there is no such preceding content at all, THEN
none must be emitted. WHEN written content does not end in a newline and further content
follows, THEN one newline must be emitted between them; an empty section body must count as
not ending in a newline, while content recorded after a section must inherit the preceding
verdict when it is empty. WHEN the last written content does not end in a newline, THEN one
must be appended.

**Filtered writing.** `write_to_filter(out, filter)` must write the body of only those
sections for which `filter` returns `true`, and `write_to(out)` must behave as
`write_to_filter(out, |_| true)`. Rejected sections must be skipped, but the filter must not
suppress the surrounding repair: content preceding the first section must be written
unconditionally, whether or not any section survives, and only the newline repaired **after**
that content is conditional — it must be emitted just WHEN at least one section passes the
filter. IF the previously written section did not end in a newline, THEN the separating
newline must be emitted before the next section is offered to the filter, so a rejected
section still contributes that newline and still leaves the "ends in a newline" verdict at the
value the last accepted section produced. The filter must be offered each section as a
`&SectionRef<'_>` and must be accepted as `FnMut`, and a single section must be allowed to be
offered to it more than once during one write.

**Equality.** `File` implements `PartialEq` and `Eq` over value-bearing content only.
Two files must compare equal when they declare the same number of sections in the same order,
each pair of headers has section names equal case-insensitively and subsection names equal
byte-exactly, and each pair of sections declares the same value names in the same order with
values equal **after** normalization. Value names must compare case-insensitively. Comments,
whitespace, quoting style, header spelling and section identifiers must not affect equality.

## Sources, Metadata and Trust

This section defines where a configuration is said to come from and how that provenance
reaches the read APIs.

**Source classification.** `Source` enumerates ten origins in ascending order of precedence:
`GitInstallation`, `System`, `Git`, `User`, `Local`, `Worktree`, `Env`, `Cli`, `Api`,
`EnvOverride`. Declaration order is precedence order, and `Source` derives `Ord` so that a
later variant compares greater than an earlier one.

**Source categories.** `Source::kind()` must classify each source into a `source::Kind`:
`GitInstallation` into `Kind::GitInstallation`, `System` into `Kind::System`, `Git` and `User`
into `Kind::Global`, `Local` and `Worktree` into `Kind::Repository`, and `Env`, `Cli`, `Api`
and `EnvOverride` into `Kind::Override`. `Kind::sources()` must return the sources belonging
to each category in ascending precedence: `[GitInstallation]`, `[System]`, `[Git, User]`,
`[Local, Worktree]`, and `[Env, Cli, Api]`. `Kind::Override.sources()` must **not** include
`EnvOverride`, even though `EnvOverride.kind()` is `Kind::Override`.

**Storage locations.** `Source::storage_location(env_var)` must compute where a file of that
source would live, consulting the environment only through the supplied closure so that a
caller restricts environment access. For `GitInstallation` and `System`, WHEN `env_var`
returns a value for `GIT_CONFIG_NOSYSTEM` that parses as a true boolean, THEN the result must
be `None`. Otherwise `GitInstallation` must return the installation-provided configuration
path, and `System` must return `GIT_CONFIG_SYSTEM` when set and otherwise the system prefix
joined with `etc/gitconfig`. `Git` must return `GIT_CONFIG_GLOBAL` when set and otherwise the
XDG configuration path for `config`. `User` must return `GIT_CONFIG_GLOBAL` when set and
otherwise `HOME` joined with `.gitconfig`; WHERE `HOME` is unset, THEN on Windows the home
directory reported by the platform must be used in its place and joined with `.gitconfig`,
while on every other platform the result must be `None`. `Local` must return the relative
path `config` and
`Worktree` the relative path `config.worktree`; the caller resolves them against the
appropriate base. `Env`, `Cli`, `Api` and `EnvOverride` must return `None`.

**Metadata.** `file::Metadata` carries a public `path`, `source`, `level` and `trust`.
`Metadata::api()` must return path `None`, source `Source::Api`, level `0` and trust
`gix_sec::Trust::Full`, and `Metadata::default()` must equal it. `From<Source> for Metadata`
must produce the given source with path `None`, level `0` and trust `Trust::Full`.
`Metadata::try_from_path(path, source)` must attach the given `source`, must set `path` to
`Some(path)` and `level` to `0`, and must derive `trust` from the ownership of `path` itself
without following a final symbolic link: `Trust::Full` WHEN the path is owned by the effective
user of the current process, `Trust::Full` also WHEN it is instead owned by the user id named
by the `SUDO_UID` environment variable, and `Trust::Reduced` otherwise. IF the ownership of
the path cannot be determined, THEN the failure must be propagated as `std::io::Error`.
`with(trust)` and `at(path)` must
return the modified metadata by value. `level` records include depth, with `0` meaning
directly loaded.

**Metadata-filtered reads.** Every `_filter` and `_filter_by` accessor must pass each
candidate section's metadata to the supplied predicate and must consider only sections for
which it returns `true`. Filtering must never change which declaration wins among accepted
candidates: the last accepted declaration still answers a single-value lookup, and accepted
declarations still appear in file order for a multi-value lookup.

═══════════════════════════════════ Contract Layer ═══════════════════════════════════

## State Model

The core state of a `File` is an ordered list of sections over a single append-only byte
buffer. Every public view is a projection of that one state, and every mutation must leave
all projections mutually consistent.

**Core state.**

1. *Backing text* — the bytes of the document. Content is only ever appended to it; edits
   redirect the spans that reference it rather than rewriting earlier bytes.
2. *Section order* — the sequence of section identifiers as they appear in the document. This
   is the authority for "file order" everywhere in this specification.
3. *Section table* — identifier to section, where a section is a header, a body of value
   entries, and a metadata handle.
4. *Name index* — section name to the identifiers declaring it, split into the
   no-subsection case and a per-subsection case, each held in file order.
5. *Identifier counter* — monotonically increasing; an identifier retired by removal is
   never reissued.
6. *File metadata* — the metadata attached to sections created after load.

**Public projections.**

| Projection | Reached through | Shows |
|---|---|---|
| Serialized text | `to_bstring`, `write_to`, `write_to_filter`, `Display` | backing text plus repaired newlines |
| Section sequence | `sections`, `sections_and_ids`, `section_ids` | section order |
| Named lookup | `section`, `section_filter`, `sections_by_name`, `*_by_key` | name index, resolved against section order |
| Raw values | `raw_value*`, `raw_values*` | normalized bytes from section bodies |
| Typed values | `value*`, `string*`, `boolean*`, `integer*`, `path*`, `strings*`, `integers*` | raw values after conversion |
| Section view | `SectionRef`, `BodyRef`, `HeaderRef` | one section's header and body |
| Mutable views | `SectionMut`, `ValueMut`, `MultiValueMut` | write access to one section, value, or multivar |
| Provenance | `meta`, `meta_owned`, `SectionRef::meta`, `SectionMut::meta` | metadata handles |
| Equality | `PartialEq` | value-bearing content only |

**Transitions.** Creating or pushing a section extends section order, the section table and
the name index together, and allocates a fresh identifier. Removing a section retracts it
from all three, and retires an emptied subsection bucket and then an emptied name bucket.
Renaming moves identifiers between name-index buckets while leaving section order untouched.
Every value write appends to the backing text and redirects the spans of the rewritten entry —
the value name, the separator run between it and the value, and the value itself, so several
spans at once rather than one; no value write reorders sections or changes any identifier.

## Error Semantics

| Condition | Result |
|---|---|
| Section name absent from the file | `lookup::existing::Error::SectionMissing` |
| Section name present, requested subsection absent | `lookup::existing::Error::SubSectionMissing` |
| Section found, value name has no non-implicit declaration | `lookup::existing::Error::KeyMissing` |
| Two-part section key cannot be split | `lookup::existing::Error::KeyMissing` |
| `rename_section_filter` filter rejects every candidate | `rename_section::Error::Lookup(lookup::existing::Error::KeyMissing)` |
| Value name is empty, non-alphanumeric, or does not start with a letter | `parse::section::value_name::Error` |
| Section name contains anything but ASCII alphanumerics and `-` | `parse::section::header::Error::InvalidName` |
| Section name is empty, in a `parse::section::Name` conversion only | `parse::section::name::Error` |
| Subsection name contains `\n` or `\0` | `parse::section::header::Error::InvalidSubSection` |
| Document would exceed `u32::MAX` bytes through a write, append or reinsertion | `parse::span::Error` |
| Construction input is larger than `u32::MAX` bytes | `parse::Error` |
| Input text is not valid configuration syntax | `parse::Error` |
| Typed conversion of a present value fails | `value::Error` |
| Generic conversion through `value::<T>` fails | `lookup::Error::FailedConversion(T::Error)` |
| Generic lookup through `value::<T>` finds nothing | `lookup::Error::ValueMissing(lookup::existing::Error)` |
| Path ownership cannot be inspected in `Metadata::try_from_path` | `std::io::Error` |
| `AsKey::as_key` on an unsplittable key | panic |
| `MultiValueMut::set_at`, `set_string_at` or `delete` given an index not below `len()` | panic |
| `set_leading_whitespace` given non-whitespace text | panic |

Error message strings are part of the contract. `lookup::existing::Error` renders as
`The requested section does not exist`, `The requested subsection does not exist`, and
`The key does not exist in the requested section`. `parse::section::name::Error` renders as
`Valid names consist of alphanumeric characters or dashes.`, and
`parse::section::value_name::Error` as
`Valid value names consist of alphanumeric characters or dashes, starting with an alphabetic character.`
`parse::section::header::Error` renders as `section names can only be ascii, '-'` and
`sub-section names must not contain newlines or null bytes`. `parse::span::Error` renders as
`configuration data exceeds the supported span size of 4294967295 bytes`. Every enum variant
marked `#[error(transparent)]` in the Import Surface must render its wrapped error verbatim.

## Cross-View Invariants

1. Serializing a losslessly loaded, unmutated file must return exactly the bytes it was
   loaded from, so the serialized-text projection and the input are byte-identical.
2. For every value written through any mutating API, reading it back through the
   corresponding raw accessor must return exactly the bytes that were written: escaping on
   write and normalization on read are mutual inverses over all inputs.
3. For any key present in the file, the value returned by `raw_value` must be identical to
   the last element of the vector returned by `raw_values` for that same key, and the value
   returned by `string` must equal the value returned by `raw_value`.
4. `File::num_values()` must equal the sum of `body().num_values()` over every section yielded
   by `sections()`, and `File::is_void()` must be `true` exactly when that sum is zero — the
   whole-file counters and the per-section counters must never disagree. The same two counters
   read from a `SectionMut` directly must agree with the ones read from that section's
   `body()`.
5. The set of sections yielded by `sections_by_name(n)` must equal the set of sections in
   `sections()` whose header name equals `n` case-insensitively, in the same relative order;
   the name index must never disagree with section order.
6. After `remove_section` removes the last section carrying a name, every subsequent lookup of
   that name must return `SectionMissing` rather than `SubSectionMissing`, and after it removes
   the last section carrying a subsection under a still-present name, lookups of that
   subsection must return `SubSectionMissing`.
7. A section removed and immediately reinserted with `push_section` must serialize to the same
   bytes it serialized to before removal and must retain its metadata, while receiving an
   identifier distinct from the one it previously held and from every other live identifier.
8. Two files that serialize to byte-identical text must compare equal under `PartialEq`, and
   two files that differ only in comments, whitespace, quoting style or header spelling must
   also compare equal — equality is strictly coarser than serialized-text identity.
9. Every mutation performed through a `SectionMut`, `ValueMut` or `MultiValueMut` must be
   visible through the file-level accessors as soon as the handle is dropped, and must leave
   every section identifier and the relative order of all sections unchanged.
10. A `_filter` accessor called with a predicate that always returns `true` must select exactly
    the declarations its unfiltered counterpart selects, but the two do not always share a
    return shape. WHERE the pair returns the same type — the value families `raw_value`,
    `raw_values`, `raw_value_mut`, `raw_values_mut`, `value`, `try_value`, the six comfort
    families and their `_by` forms, together with `sections_by_name` against
    `sections_by_name_and_filter` — THEN the two calls must produce equal results outright.
    WHERE the pair does not — `section` and `section_by_key` return
    `Result<SectionRef, lookup::existing::Error>` while `section_filter` and
    `section_filter_by_key` return `Result<Option<SectionRef>, lookup::existing::Error>`, and
    `section_mut` and `section_mut_by_key` stand in the same relation to `section_mut_filter`
    and `section_mut_filter_by_key` — THEN the always-true call must return `Ok(Some(s))` for
    exactly the `s` the unfiltered call returns `Ok(s)` for, and must return the identical
    `Err` otherwise; `Ok(None)` must never be produced by an always-true predicate.

══════════════════════════════════ Reference Layer ══════════════════════════════════

## Public Interface

This section is a lookup index. Behavior is defined above; the declarations below fix the
shape the caller compiles against. Every signature is normative, including receiver form,
generic bounds, lifetimes and derive sets. Types are named exactly as they must be reachable.

### Import Surface

Every name below is publicly reachable at the path it is written under. These are the paths
a caller imports from; the exact declared shape of each name — signature, receiver form,
generic bounds, lifetimes, variant shape and derive set — is in the API Catalog below.

```rust
use gix_config::{
    AsBStr, AsBStrOpt, AsKey, Boolean, Color, File, Integer, KeyRef, Path, Source,
    color, integer, path,
};
use gix_config::source::Kind;
use gix_config::value::{self, normalize};
```

```rust
use gix_config::file::{
    IntoBStringOpt, Metadata, MultiValueMut, Section, SectionId, SectionMut, SectionRef,
    ValueMut,
};
use gix_config::file::init::{self, Options};
use gix_config::file::section::{self, BodyRef, BodyRefIter, HeaderRef};
use gix_config::file::{rename_section, set_raw_value};
```

```rust
use gix_config::lookup::{self, existing};
use gix_config::parse::{self, span};
use gix_config::parse::section::{Name, header, name, value_name};
use gix_config::parse::section::header::is_valid_subsection;
```

`gix_config::file::init`, `file::rename_section`, `file::set_raw_value`,
`file::section::value`, `lookup::existing`, `parse::span`, `parse::section::name`,
`parse::section::value_name` and `parse::section::header` each export an `Error`; they are
distinct types and are never interchangeable. `Boolean`, `Color`, `Integer`, `Path`,
`color`, `integer`, `path` and `value::Error` are re-exports from the value crate, and
`AsBStr` / `AsBStrOpt` are re-exports from the byte-string utility crate — a caller must be
able to name each of them through `gix_config` at the path shown.

### API Catalog

Every declaration below is normative and exact: receiver form, generic bounds, lifetimes,
argument order and arity, return type, variant shape and derive set. A `/* private */`
marker means the item has fields a caller cannot name. Derives are written on the
declaration, never described in prose — a derive stated only in prose cannot be checked and
a missing one is invisible until link time.

**Roles.**

| Name | Kind | Role |
|---|---|---|
| `File` | struct | The whole configuration document; the entry point for every read and write |
| `Source` | enum | Where a configuration came from, ordered by ascending precedence |
| `source::Kind` | enum | Coarse category grouping several sources |
| `AsKey` | trait | Accepts a dotted key at a call site |
| `KeyRef` | struct | A dotted key split into section, optional subsection and value name |
| `AsBStr` | trait | Accepts any byte-string-like value at a call site |
| `AsBStrOpt` | trait | Accepts an optional subsection name at a call site |
| `file::IntoBStringOpt` | trait | Accepts an owned optional subsection name at a call site |
| `file::Metadata` | struct | Provenance and trust of a section or of the file |
| `file::Section` | struct | A self-contained owned section, detached from any file |
| `file::SectionRef` | struct | Read-only view of one section inside a file |
| `file::SectionMut` | struct | Write access to one section inside a file |
| `file::SectionId` | struct | Stable, never-reused identifier of a section |
| `file::ValueMut` | struct | Write access to one value declaration |
| `file::MultiValueMut` | struct | Write access to every declaration of one multivar |
| `file::section::HeaderRef` | struct | Read-only view of a section header |
| `file::section::BodyRef` | struct | Read-only view of a section body |
| `file::section::BodyRefIter` | struct | Iterator over a body's name and value pairs |
| `file::init::Options` | struct | Controls whether loading is lossless or value-only |
| `file::init::Error` | enum | Failure of `from_bytes_no_includes` |
| `file::rename_section::Error` | enum | Failure of a section rename |
| `file::set_raw_value::Error` | enum | Failure of a raw value assignment |
| `file::section::value::Error` | enum | Failure of a value write through a section |
| `lookup::Error` | enum | Failure of a typed lookup, missing or unconvertible |
| `lookup::existing::Error` | enum | Failure to find a section, subsection or value name |
| `parse::Error` | struct | Failure to parse configuration text |
| `parse::span::Error` | struct | The document exceeded the supported size |
| `parse::section::Name` | struct | A validated, case-insensitive section name |
| `parse::section::name::Error` | struct | A section name failed validation |
| `parse::section::value_name::Error` | struct | A value name failed validation |
| `parse::section::header::Error` | enum | A section header failed validation |
| `parse::section::header::is_valid_subsection` | function | Reports whether a subsection name is writable |
| `value::normalize` | function | Strips quotes and resolves escapes in a stored value |
| `value::Error` | struct | Reports a stored value that failed to convert to the requested type |
| `Boolean`, `Integer`, `Color`, `Path` | structs | Typed views over a normalized value |

#### `gix_config` — crate root

```rust
pub mod file;
pub mod lookup;
pub mod parse;
pub mod source;
pub mod value;

pub use gix_config_value::{Boolean, Color, Integer, Path, color, integer, path};
pub use gix_utils::{AsBStr, AsBStrOpt};

pub trait AsKey: Copy {
    fn as_key(&self) -> KeyRef<'_>;
    fn try_as_key(&self) -> Option<KeyRef<'_>>;
}
// implemented for: &str, &String, &BStr, &BString, KeyRef<'_>, and &T where T: AsKey

#[derive(Debug, PartialEq, Ord, PartialOrd, Eq, Hash, Clone, Copy)]
pub struct KeyRef<'a> {
    pub section_name: &'a str,
    pub subsection_name: Option<&'a bstr::BStr>,
    pub value_name: &'a str,
}
impl KeyRef<'_> {
    pub fn parse_unvalidated(input: &bstr::BStr) -> Option<KeyRef<'_>>;
}

#[derive(Clone, Debug, Default)]
pub struct File { /* private */ }

#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash, Ord, PartialOrd)]
pub enum Source {
    GitInstallation, System, Git, User, Local, Worktree, Env, Cli, Api, EnvOverride,
}
```

#### `gix_config::source`

```rust
// gix_config::source
#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash, Ord, PartialOrd)]
pub enum Kind { GitInstallation, System, Global, Repository, Override }

impl Kind {
    pub fn sources(self) -> &'static [crate::Source];
}
impl crate::Source {
    pub const fn kind(self) -> Kind;
    pub fn storage_location(
        self,
        env_var: &mut dyn FnMut(&str) -> Option<std::ffi::OsString>,
    ) -> Option<std::path::PathBuf>;
}
```

#### `gix_config::lookup`

```rust
// gix_config::lookup
#[derive(Debug, thiserror::Error)]
pub enum Error<E> {
    #[error(transparent)] ValueMissing(#[from] existing::Error),
    #[error(transparent)] FailedConversion(E),
}
pub mod existing {
    #[derive(Debug, thiserror::Error)]
    pub enum Error {
        #[error("The requested section does not exist")]            SectionMissing,
        #[error("The requested subsection does not exist")]         SubSectionMissing,
        #[error("The key does not exist in the requested section")] KeyMissing,
        #[error(transparent)] ValueName(#[from] crate::parse::section::value_name::Error),
    }
}
```

#### `gix_config::value`

```rust
// gix_config::value
pub use gix_config_value::Error;
pub fn normalize(input: &(impl crate::AsBStr + ?Sized)) -> std::borrow::Cow<'_, bstr::BStr>;
```

#### `gix_config::parse` — only the error surface is public.

```rust
// gix_config::parse
#[derive(PartialEq, Debug)]
pub struct Error { /* private */ }
impl Error {
    pub const fn line_number(&self) -> usize;   // one-based
    pub fn remaining_data(&self) -> &[u8];
}
impl std::fmt::Display for Error {}
impl std::error::Error for Error {}

pub mod span {
    #[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, thiserror::Error)]
    #[error("configuration data exceeds the supported span size of {} bytes", u32::MAX)]
    pub struct Error;
}

pub mod section {
    #[derive(Clone, Eq, Debug, Default)]
    pub struct Name(/* private */);
    impl Name {
        pub fn to_owned(&self) -> Name;
    }
    // PartialEq, PartialOrd, Ord and Hash are hand-written, not derived, and all four
    // compare ASCII-case-insensitively.
    impl PartialEq for Name {}
    impl PartialOrd for Name {}
    impl Ord for Name {}
    impl std::hash::Hash for Name {}
    impl TryFrom<&str> for Name          { type Error = name::Error; }
    impl TryFrom<String> for Name        { type Error = name::Error; }
    impl TryFrom<bstr::BString> for Name { type Error = name::Error; }
    impl TryFrom<&bstr::BStr> for Name   { type Error = name::Error; }
    impl std::ops::Deref for Name { type Target = bstr::BStr; }
    impl AsRef<str> for Name {}
    impl std::fmt::Display for Name {}

    pub mod name {
        #[derive(Debug, thiserror::Error, Copy, Clone)]
        #[error("Valid names consist of alphanumeric characters or dashes.")]
        pub struct Error;
    }
    pub mod value_name {
        #[derive(Debug, thiserror::Error, Copy, Clone)]
        #[error("Valid value names consist of alphanumeric characters or dashes, \
                 starting with an alphabetic character.")]
        pub struct Error;
    }
    pub mod header {
        #[derive(Debug, PartialOrd, PartialEq, Eq, thiserror::Error)]
        pub enum Error {
            #[error("section names can only be ascii, '-'")]                      InvalidName,
            #[error("sub-section names must not contain newlines or null bytes")] InvalidSubSection,
            #[error(transparent)] Span(#[from] crate::parse::span::Error),
        }
        pub fn is_valid_subsection(name: impl crate::AsBStr) -> bool;
    }
}
```

#### `gix_config::file` — types and error modules.

```rust
// gix_config::file
pub use mutable::{multi_value::MultiValueMut, section::SectionMut, value::ValueMut};
pub mod init;
pub mod section;

#[derive(Clone, Debug, PartialOrd, PartialEq, Ord, Eq, Hash)]
pub struct Metadata {
    pub path: Option<std::path::PathBuf>,
    pub source: crate::Source,
    pub level: u8,
    pub trust: gix_sec::Trust,
}
impl Metadata {
    pub fn api() -> Self;
    pub fn try_from_path(path: impl Into<std::path::PathBuf>, source: crate::Source)
        -> std::io::Result<Self>;
    pub fn with(self, trust: gix_sec::Trust) -> Self;
    pub fn at(self, path: impl Into<std::path::PathBuf>) -> Self;
}
impl Default for Metadata {}          // == Metadata::api()
impl From<crate::Source> for Metadata {}

#[derive(Clone, Debug)]                                 pub struct Section { /* private */ }
#[derive(Copy, Clone, Debug)]                           pub struct SectionRef<'a> { /* private */ }
#[derive(PartialEq, Eq, Hash, Copy, Clone, PartialOrd, Ord, Debug)]
pub struct SectionId(/* private */);
impl Default for SectionId {}         // the identifier built from usize::MAX

pub trait IntoBStringOpt {
    fn into_bstring_opt(self) -> Option<bstr::BString>;
}
// implemented for: Option<BString>, BString, String, Vec<u8>, [u8; N] (const generic),
// and &T where T: crate::AsBStr + ?Sized

pub mod rename_section {
    #[derive(Debug, thiserror::Error)]
    pub enum Error {
        #[error(transparent)] Lookup(#[from] crate::lookup::existing::Error),
        #[error(transparent)] Section(#[from] crate::parse::section::header::Error),
    }
}
pub mod set_raw_value {
    #[derive(Debug, thiserror::Error)]
    pub enum Error {
        #[error(transparent)] Lookup(#[from] crate::lookup::existing::Error),
        #[error(transparent)] Header(#[from] crate::parse::section::header::Error),
        #[error(transparent)] ValueName(#[from] crate::parse::section::value_name::Error),
        #[error(transparent)] Span(#[from] crate::parse::span::Error),
    }
}
```

#### `gix_config::file::init`

```rust
// gix_config::file::init
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error(transparent)] Parse(#[from] crate::parse::Error),
    #[error(transparent)] Interpolate(#[from] crate::path::interpolate::Error),
    #[error(transparent)] Span(#[from] crate::parse::span::Error),
}

#[derive(Clone, Copy, Default)]
pub struct Options { pub lossy: bool }
```

#### `gix_config::file::section`

```rust
// gix_config::file::section
pub mod value {
    #[derive(Debug, thiserror::Error)]
    pub enum Error {
        #[error(transparent)] ValueName(#[from] crate::parse::section::value_name::Error),
        #[error(transparent)] Span(#[from] crate::parse::span::Error),
    }
}

#[derive(Copy, Clone, Debug)] pub struct HeaderRef<'a> { /* private */ }
impl<'a> HeaderRef<'a> {
    pub fn is_legacy(&self) -> bool;
    pub fn subsection_name(&self) -> Option<&'a bstr::BStr>;
    pub fn name(&self) -> &'a bstr::BStr;
    pub fn to_bstring(&self) -> bstr::BString;
}

#[derive(Copy, Clone, Debug)] pub struct BodyRef<'a> { /* private */ }
impl<'a> BodyRef<'a> {
    pub fn value(&self, value_name: impl AsRef<str>) -> Option<bstr::BString>;
    pub fn value_implicit(&self, value_name: &str) -> Option<Option<bstr::BString>>;
    pub fn values(&self, value_name: &str) -> Vec<bstr::BString>;
    pub fn value_names(&self) -> impl Iterator<Item = String> + '_;
    pub fn contains_value_name(&self, value_name: &str) -> bool;
    pub fn num_values(&self) -> usize;
    pub fn is_void(&self) -> bool;
}
pub struct BodyRefIter<'a> { /* private */ }   // derives nothing
impl<'a> Iterator for BodyRefIter<'a> { type Item = (String, bstr::BString); }
impl<'a> std::iter::FusedIterator for BodyRefIter<'a> {}
impl<'a> IntoIterator for BodyRef<'a> { type Item = (String, bstr::BString);
                                        type IntoIter = BodyRefIter<'a>; }

impl Section {
    pub fn new(
        name: impl AsRef<str>,
        subsection: impl crate::file::IntoBStringOpt,
        meta: impl Into<gix_features::threading::OwnShared<crate::file::Metadata>>,
    ) -> Result<Self, crate::parse::section::header::Error>;
    pub fn to_ref(&self) -> SectionRef<'_>;
    pub fn to_mut(&mut self) -> crate::file::SectionMut<'_>;
}

impl<'file> SectionRef<'file> {
    pub fn to_owned(self) -> Section;
    pub fn header(&self) -> HeaderRef<'file>;
    pub fn id(&self) -> crate::file::SectionId;
    pub fn body(&self) -> BodyRef<'file>;
    pub fn to_bstring(&self) -> bstr::BString;
    pub fn write_to(&self, out: &mut dyn std::io::Write) -> std::io::Result<()>;
    pub fn meta(&self) -> &'file crate::file::Metadata;
    pub fn value(&self, value_name: impl AsRef<str>) -> Option<bstr::BString>;
    pub fn value_implicit(&self, value_name: &str) -> Option<Option<bstr::BString>>;
    pub fn values(&self, value_name: &str) -> Vec<bstr::BString>;
    pub fn value_names(&self) -> impl Iterator<Item = String> + '_;
    pub fn contains_value_name(&self, value_name: &str) -> bool;
}
```

#### `gix_config::File` — construction, trait impls and serialization.

```rust
impl File {
    pub fn new(meta: impl Into<gix_features::threading::OwnShared<file::Metadata>>) -> Self;
    pub fn from_bytes_no_includes(
        input: &[u8],
        meta: impl Into<gix_features::threading::OwnShared<file::Metadata>>,
        options: file::init::Options,
    ) -> Result<Self, file::init::Error>;
    pub fn from_bytes_owned(
        input_and_buf: &mut Vec<u8>,
        meta: impl Into<gix_features::threading::OwnShared<file::Metadata>>,
        options: file::init::Options,
    ) -> Result<Self, file::init::Error>;

    pub fn to_bstring(&self) -> bstr::BString;
    pub fn write_to(&self, out: &mut dyn std::io::Write) -> std::io::Result<()>;
    pub fn write_to_filter(
        &self,
        out: &mut dyn std::io::Write,
        filter: impl FnMut(&file::SectionRef<'_>) -> bool,
    ) -> std::io::Result<()>;
}

impl std::str::FromStr  for File { type Err   = parse::Error; }
impl TryFrom<&str>      for File { type Error = parse::Error; }
impl TryFrom<&bstr::BStr> for File { type Error = parse::Error; }
impl From<File> for bstr::BString {}
impl std::fmt::Display for File {}
impl PartialEq for File {}   // hand-written; see Serialization
impl Eq for File {}
```

#### `gix_config::File` — read-only access.

```rust
impl File {
    pub fn value<T: TryFrom<BString>>(&self, key: impl AsKey) -> Result<T, lookup::Error<T::Error>>;
    pub fn value_by<T: TryFrom<BString>>(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<T, lookup::Error<T::Error>>;
    pub fn value_with_section<T: TryFrom<BString>>(
        &self, key: impl AsKey,
    ) -> Result<(T, file::SectionRef<'_>), lookup::Error<T::Error>>;
    pub fn value_with_section_by<T: TryFrom<BString>>(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<(T, file::SectionRef<'_>), lookup::Error<T::Error>>;
    pub fn try_value<T: TryFrom<BString>>(&self, key: impl AsKey) -> Result<Option<T>, T::Error>;
    pub fn try_value_by<T: TryFrom<BString>>(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Option<T>, T::Error>;
    pub fn values<T: TryFrom<BString>>(&self, key: impl AsKey)
        -> Result<Vec<T>, lookup::Error<T::Error>>;
    pub fn values_by<T: TryFrom<BString>>(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Vec<T>, lookup::Error<T::Error>>;
    pub fn values_with_sections<T: TryFrom<BString>>(
        &self, key: impl AsKey,
    ) -> Result<Vec<(T, file::SectionRef<'_>)>, lookup::Error<T::Error>>;
    pub fn values_with_sections_by<T: TryFrom<BString>>(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Vec<(T, file::SectionRef<'_>)>, lookup::Error<T::Error>>;

    pub fn section(
        &self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
    ) -> Result<file::SectionRef<'_>, lookup::existing::Error>;
    pub fn section_by_key(
        &self, section_key: impl AsBStr,
    ) -> Result<file::SectionRef<'_>, lookup::existing::Error>;
    pub fn section_filter(
        &self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<file::SectionRef<'_>>, lookup::existing::Error>;
    pub fn section_filter_by_key(
        &self, section_key: impl AsBStr, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<file::SectionRef<'_>>, lookup::existing::Error>;
    pub fn sections_by_name(&self, name: impl AsRef<str>)
        -> Option<impl Iterator<Item = file::SectionRef<'_>> + '_>;
    pub fn sections_and_ids_by_name(&self, name: impl AsRef<str>)
        -> Option<impl Iterator<Item = (file::SectionRef<'_>, file::SectionId)> + '_>;
    pub fn sections_by_name_and_filter<'a>(
        &'a self, name: impl AsRef<str>,
        filter: impl FnMut(&file::Metadata) -> bool + 'a,
    ) -> Option<impl Iterator<Item = file::SectionRef<'a>> + 'a>;
    pub fn sections(&self) -> impl Iterator<Item = file::SectionRef<'_>> + '_;
    pub fn sections_and_ids(&self)
        -> impl Iterator<Item = (file::SectionRef<'_>, file::SectionId)> + '_;
    pub fn section_ids(&mut self) -> impl Iterator<Item = file::SectionId> + '_;

    pub fn num_values(&self) -> usize;
    pub fn is_void(&self) -> bool;
    pub fn meta(&self) -> &file::Metadata;
    pub fn set_meta(
        &mut self,
        meta: impl Into<gix_features::threading::OwnShared<file::Metadata>>,
    ) -> &mut Self;
    pub fn meta_owned(&self) -> gix_features::threading::OwnShared<file::Metadata>;
    pub fn detect_newline_style(&self) -> &bstr::BStr;
}
```

#### `gix_config::File` — comfort accessors (six families, four forms each)

```rust
impl File {
    pub fn string(&self, key: impl AsKey) -> Option<BString>;
    pub fn string_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Option<BString>;
    pub fn string_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<BString>;
    pub fn string_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<BString>;

    pub fn path(&self, key: impl AsKey) -> Option<crate::Path>;
    pub fn path_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Option<crate::Path>;
    pub fn path_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<crate::Path>;
    pub fn path_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<crate::Path>;

    pub fn boolean(&self, key: impl AsKey) -> Result<Option<bool>, value::Error>;
    pub fn boolean_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Option<bool>, value::Error>;
    pub fn boolean_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<bool>, value::Error>;
    pub fn boolean_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<bool>, value::Error>;

    pub fn integer(&self, key: impl AsKey) -> Result<Option<i64>, value::Error>;
    pub fn integer_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Option<i64>, value::Error>;
    pub fn integer_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<i64>, value::Error>;
    pub fn integer_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<i64>, value::Error>;

    pub fn strings(&self, key: impl AsKey) -> Option<Vec<BString>>;
    pub fn strings_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Option<Vec<BString>>;
    pub fn strings_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<Vec<BString>>;
    pub fn strings_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<Vec<BString>>;

    pub fn integers(&self, key: impl AsKey) -> Result<Option<Vec<i64>>, value::Error>;
    pub fn integers_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Option<Vec<i64>>, value::Error>;
    pub fn integers_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<Vec<i64>>, value::Error>;
    pub fn integers_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<Vec<i64>>, value::Error>;
}
```

#### `gix_config::File` — raw access.

```rust
impl File {
    pub fn raw_value(&self, key: impl AsKey) -> Result<BString, lookup::existing::Error>;
    pub fn raw_value_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<BString, lookup::existing::Error>;
    pub fn raw_value_with_section(&self, key: impl AsKey)
        -> Result<(BString, file::SectionRef<'_>), lookup::existing::Error>;
    pub fn raw_value_with_section_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<(BString, file::SectionRef<'_>), lookup::existing::Error>;
    pub fn raw_value_with_section_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<(BString, file::SectionRef<'_>), lookup::existing::Error>;
    pub fn raw_value_with_section_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<(BString, file::SectionRef<'_>), lookup::existing::Error>;
    pub fn raw_value_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<BString, lookup::existing::Error>;
    pub fn raw_value_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<BString, lookup::existing::Error>;

    pub fn raw_value_mut(&mut self, key: impl AsKey)
        -> Result<file::ValueMut<'_>, lookup::existing::Error>;
    pub fn raw_value_mut_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<file::ValueMut<'_>, lookup::existing::Error>;
    pub fn raw_value_mut_filter(
        &mut self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<file::ValueMut<'_>, lookup::existing::Error>;
    pub fn raw_value_mut_filter_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<file::ValueMut<'_>, lookup::existing::Error>;

    pub fn raw_values(&self, key: impl AsKey) -> Result<Vec<BString>, lookup::existing::Error>;
    pub fn raw_values_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Vec<BString>, lookup::existing::Error>;
    pub fn raw_values_with_sections(&self, key: impl AsKey)
        -> Result<Vec<(BString, file::SectionRef<'_>)>, lookup::existing::Error>;
    pub fn raw_values_with_sections_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<Vec<(BString, file::SectionRef<'_>)>, lookup::existing::Error>;
    pub fn raw_values_with_sections_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Vec<(BString, file::SectionRef<'_>)>, lookup::existing::Error>;
    pub fn raw_values_with_sections_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Vec<(BString, file::SectionRef<'_>)>, lookup::existing::Error>;
    pub fn raw_values_filter(
        &self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Vec<BString>, lookup::existing::Error>;
    pub fn raw_values_filter_by(
        &self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Vec<BString>, lookup::existing::Error>;

    pub fn raw_values_mut(&mut self, key: impl AsKey)
        -> Result<file::MultiValueMut<'_>, lookup::existing::Error>;
    pub fn raw_values_mut_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>,
    ) -> Result<file::MultiValueMut<'_>, lookup::existing::Error>;
    pub fn raw_values_mut_filter(
        &mut self, key: impl AsKey, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<file::MultiValueMut<'_>, lookup::existing::Error>;
    pub fn raw_values_mut_filter_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<file::MultiValueMut<'_>, lookup::existing::Error>;

    pub fn set_existing_raw_value(
        &mut self, key: impl AsKey, new_value: impl AsBStr,
    ) -> Result<(), file::set_raw_value::Error>;
    pub fn set_existing_raw_value_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, new_value: impl AsBStr,
    ) -> Result<(), file::set_raw_value::Error>;
    pub fn set_raw_value(
        &mut self, key: impl AsKey, new_value: impl AsBStr,
    ) -> Result<Option<BString>, file::set_raw_value::Error>;
    pub fn set_raw_value_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, new_value: impl AsBStr,
    ) -> Result<Option<BString>, file::set_raw_value::Error>;
    pub fn set_raw_value_filter(
        &mut self, key: impl AsKey, new_value: impl AsBStr,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<BString>, file::set_raw_value::Error>;
    pub fn set_raw_value_filter_by(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, new_value: impl AsBStr,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<BString>, file::set_raw_value::Error>;
    pub fn set_existing_raw_multi_value<Iter, Item>(
        &mut self, key: impl AsKey, new_values: Iter,
    ) -> Result<(), file::set_raw_value::Error>
    where Iter: IntoIterator<Item = Item>, Item: AsBStr;
    pub fn set_existing_raw_multi_value_by<Iter, Item>(
        &mut self, section_name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        value_name: impl AsRef<str>, new_values: Iter,
    ) -> Result<(), file::set_raw_value::Error>
    where Iter: IntoIterator<Item = Item>, Item: AsBStr;
}
```

#### `gix_config::File` — section mutation.

```rust
impl File {
    pub fn section_mut(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
    ) -> Result<file::SectionMut<'_>, lookup::existing::Error>;
    pub fn section_mut_by_key(
        &mut self, key: impl AsBStr,
    ) -> Result<file::SectionMut<'_>, lookup::existing::Error>;
    pub fn section_mut_by_id(&mut self, id: file::SectionId) -> Option<file::SectionMut<'_>>;
    pub fn section_mut_or_create_new(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
    ) -> Result<file::SectionMut<'_>, parse::section::header::Error>;
    pub fn section_mut_or_create_new_filter(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<file::SectionMut<'_>, parse::section::header::Error>;
    pub fn section_mut_filter(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<file::SectionMut<'_>>, lookup::existing::Error>;
    pub fn section_mut_filter_by_key(
        &mut self, key: impl AsBStr, filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<Option<file::SectionMut<'_>>, lookup::existing::Error>;

    pub fn new_section(
        &mut self, name: impl AsRef<str>, subsection: impl file::IntoBStringOpt,
    ) -> Result<file::SectionMut<'_>, parse::section::header::Error>;
    pub fn remove_section(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
    ) -> Option<file::Section>;
    pub fn remove_section_by_id(&mut self, id: file::SectionId) -> Option<file::Section>;
    pub fn remove_section_filter(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Option<file::Section>;
    pub fn push_section(
        &mut self, section: file::Section,
    ) -> Result<file::SectionMut<'_>, parse::span::Error>;
    pub fn rename_section(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        new_name: impl AsRef<str>, new_subsection_name: impl file::IntoBStringOpt,
    ) -> Result<(), file::rename_section::Error>;
    pub fn rename_section_filter(
        &mut self, name: impl AsRef<str>, subsection_name: impl AsBStrOpt,
        new_name: impl AsRef<str>, new_subsection_name: impl file::IntoBStringOpt,
        filter: impl FnMut(&file::Metadata) -> bool,
    ) -> Result<(), file::rename_section::Error>;
    pub fn append(&mut self, other: Self) -> Result<&mut Self, parse::span::Error>;
}
```

#### `gix_config::file` — mutable views

```rust
// gix_config::file
#[derive(Debug)] pub struct SectionMut<'a> { /* private */ }
impl SectionMut<'_> {
    pub fn rename(
        &mut self, name: impl AsRef<str>, subsection_name: impl crate::file::IntoBStringOpt,
    ) -> Result<&mut Self, crate::parse::section::header::Error>;
    pub fn push(
        &mut self, value_name: impl AsRef<str>, value: impl crate::AsBStrOpt,
    ) -> Result<&mut Self, crate::file::section::value::Error>;
    pub fn push_with_comment(
        &mut self, value_name: impl AsRef<str>, value: impl crate::AsBStrOpt,
        comment: impl crate::AsBStr,
    ) -> Result<&mut Self, crate::file::section::value::Error>;
    pub fn pop(&mut self) -> Option<(String, bstr::BString)>;
    pub fn set(
        &mut self, value_name: impl AsRef<str>, value: impl crate::AsBStr,
    ) -> Result<Option<bstr::BString>, crate::file::section::value::Error>;
    pub fn set_trust(&mut self, trust: gix_sec::Trust) -> &mut Self;
    pub fn remove(&mut self, value_name: &str) -> Option<bstr::BString>;
    pub fn push_newline(&mut self) -> Result<&mut Self, crate::parse::span::Error>;
    pub fn newline(&self) -> &bstr::BStr;
    pub fn set_implicit_newline(&mut self, on: bool) -> &mut Self;
    pub fn set_leading_whitespace(
        &mut self, whitespace: impl crate::file::IntoBStringOpt,
    ) -> &mut Self;
    pub fn leading_whitespace(&self) -> Option<&bstr::BStr>;
    pub fn section(&self) -> crate::file::SectionRef<'_>;
    pub fn header(&self) -> crate::file::section::HeaderRef<'_>;
    pub fn id(&self) -> crate::file::SectionId;
    pub fn body(&self) -> crate::file::section::BodyRef<'_>;
    pub fn to_bstring(&self) -> bstr::BString;
    pub fn meta(&self) -> &crate::file::Metadata;
    pub fn value(&self, value_name: impl AsRef<str>) -> Option<bstr::BString>;
    pub fn value_implicit(&self, value_name: &str) -> Option<Option<bstr::BString>>;
    pub fn values(&self, value_name: &str) -> Vec<bstr::BString>;
    pub fn value_names(&self) -> impl Iterator<Item = String> + '_;
    pub fn contains_value_name(&self, value_name: &str) -> bool;
    pub fn num_values(&self) -> usize;
    pub fn is_void(&self) -> bool;
    pub fn separator_whitespace(&self) -> (Option<&bstr::BStr>, Option<&bstr::BStr>);
}

#[derive(Debug)] pub struct ValueMut<'borrow> { /* private */ }
impl<'borrow> ValueMut<'borrow> {
    pub fn get(&self) -> Result<bstr::BString, crate::lookup::existing::Error>;
    pub fn set_string(&mut self, input: impl AsRef<str>)
        -> Result<(), crate::parse::span::Error>;
    pub fn set(&mut self, input: impl crate::AsBStr) -> Result<(), crate::parse::span::Error>;
    pub fn delete(&mut self);
    pub fn section(&self) -> crate::file::SectionRef<'_>;
    pub fn into_section_mut(self) -> crate::file::SectionMut<'borrow>;
}

#[derive(Debug)] pub struct MultiValueMut<'borrow> { /* private */ }
impl MultiValueMut<'_> {
    pub fn get(&self) -> Result<Vec<bstr::BString>, crate::lookup::existing::Error>;
    pub fn len(&self) -> usize;
    pub fn is_empty(&self) -> bool;
    pub fn set_string_at(&mut self, index: usize, value: impl AsRef<str>)
        -> Result<(), crate::parse::span::Error>;
    pub fn set_at(&mut self, index: usize, value: impl crate::AsBStr)
        -> Result<(), crate::parse::span::Error>;
    pub fn set_values<Iter, Item>(&mut self, values: Iter)
        -> Result<(), crate::parse::span::Error>
    where Iter: IntoIterator<Item = Item>, Item: crate::AsBStr;
    pub fn set_all(&mut self, input: impl crate::AsBStr)
        -> Result<(), crate::parse::span::Error>;
    pub fn delete(&mut self, index: usize);
    pub fn delete_all(&mut self);
}
```

### CLI Entry Points

There is no executable target for this crate. It builds as a library only, declares no
`[[bin]]` section, and offers no command-line interface. All use is through the Rust API
described above.

════════════════════════════════════ Meta Layer ════════════════════════════════════

## Appendix A: Environment

The working environment runs Rust 1.85 or newer on Linux without network access. The crate
must use edition 2024 and declare `rust-version = "1.85"`.

The following crates are vendored and available to depend on:

| crate | purpose in this contract |
|---|---|
| `gix-config-value` | `Boolean`, `Color`, `Integer`, `Path`, `value::Error`, `path::interpolate` |
| `gix-features` | `threading::OwnShared`, the shared-metadata handle |
| `gix-path` | environment lookups behind `Source::storage_location` |
| `gix-sec` | `Trust` and ownership-derived trust levels |
| `gix-utils` | the re-exported `AsBStr` and `AsBStrOpt` traits (enable its `bstr` feature) |
| `bstr` | `BStr` and `BString` (default features off, `std` on) |
| `thiserror` | error enum derivation |
| `smallvec` | small inline collections |
| `unicode-bom` | byte-order-mark detection |

Reference-name parsing, glob matching and object-hash crates are **not** available and are
not needed: no behavior in this specification depends on them, and no cargo feature must be
declared that would require them.

The crate must build with `#![deny(missing_docs, unsafe_code)]` at the crate root, so every
public item needs a documentation comment and no `unsafe` block is permitted. Declare
packaging metadata in a standard `Cargo.toml` at the project root with the package name
`gix-config`, so the library is buildable and linkable as a dependency.

`File` must stay a compact handle: `std::mem::size_of::<gix_config::File>()` must be at most
`1040` bytes on a 64-bit target. This bounds how the core state of the State Model is laid
out — the backing text, section order, section table, name index, identifier counter and file
metadata must be held behind owned collections and shared handles rather than inline.

## Appendix B: Assessment Notes

Assessment compiles a test suite directly against the delivered crate and runs it. Because
Rust resolves the public API at compile time, a single divergence in a declared signature,
derive set, enum variant, module path or visibility prevents the whole suite from building
and scores every test as failed at once. The Import Surface above is therefore normative in
its exact form — reproduce names, receivers, generic bounds, lifetimes, return types and
derive lists literally, and place each item at the module path shown.

The suite exercises the following dimensions:

1. **Format fidelity** — loading a document and writing it back unchanged, across quoting
   styles, legacy and modern headers, comment placement, blank lines, implicit values,
   continuation lines and mixed line endings.
2. **Resolution semantics** — case handling for section, subsection and value names;
   last-declaration-wins for single-value reads; file order for multi-value reads; and the
   three-way distinction between a missing section, a missing subsection and a missing key.
3. **Typed conversion** — booleans including the implicit-entry case, integers including
   suffixes and overflow, paths, colors, and the generic `TryFrom` path with its two failure
   modes.
4. **Mutation and lossless rewriting** — creating, renaming, removing and reinserting
   sections; setting, appending and deleting values; the exact whitespace and newline that
   each insertion adopts; and the guarantee that untouched bytes stay untouched.
5. **Error identity** — the enum variant returned for each failure condition, and the
   rendered message text for the error types whose messages this document quotes.
6. **Provenance** — source classification and precedence, storage-location computation under
   injected environment variables, and metadata-filtered reads.

Assertions compare rendered configuration text and returned values directly, and no snapshot
files, fixture directories, or golden artifacts are consulted. Beyond the public shape fixed
by the Import Surface and the size bound stated in Appendix A, internal organization is
unconstrained: any module layout, data structure or private helper that satisfies the
contracts above is acceptable.
