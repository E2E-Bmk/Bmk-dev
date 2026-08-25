//! Integration layer: behaviors that only exist end to end.
//!
//! Every test here chains at least two declared operations -- parse, mutate,
//! serialize, re-parse -- and asserts on the result of the chain. That is the
//! only way to check the properties the specification states about the
//! document as a whole: that unmodified text is reproduced byte for byte, that
//! a value written back can be read back, that a rename reaches every header
//! it should and no header it should not.
//!
//! Each test names the atomic behaviors it builds on in a `DependsOn` comment.
//! When an atomic test and the integration tests above it fail together, the
//! atomic one is the report to read.

use bstr::{ByteSlice, ByteVec};
use common::{bstring, file, multi_value_config, multi_value_section, value_config};
use gix_config::{
    file::{init, Metadata},
    File, Source,
};

type Result = std::result::Result<(), Box<dyn std::error::Error>>;

// ── the document reproduces itself ───────────────────────────────────────

// DependsOn: the_three_parsing_entry_points_agree
// A document that was parsed and not modified must serialize back to exactly
// the bytes it came from -- not an equivalent document, the same bytes. The
// four shapes below are the ones that make that hard: an input that is nothing
// but blank lines, one with a deep indentation the implementation never chose,
// one whose entries have no separator at all, and one whose separators have no
// surrounding whitespace. An implementation that reformats on the way out
// fails at least one of them.
#[test]
fn an_unmodified_document_serializes_back_byte_for_byte() -> Result {
    let blank = "\n\n    ";
    assert_eq!(File::try_from(blank)?.to_string(), blank);

    let indented = r#"
        [user]
            email = code@eddie.sh
        [core]
            autocrlf = input
        [url "ssh://git@github.com/"]
            insteadOf = "github://"
        [pull]
            ff = only
    "#;
    assert_eq!(File::try_from(indented)?.to_string(), indented);

    let implicits = r#"
        [user]
            email
            name
        [core]
            autocrlf
    "#;
    assert_eq!(File::try_from(implicits)?.to_string(), implicits);

    let tight = r#"
        [core]
            autocrlf=input
        [commit]
            gpgsign=true
        [pull]
            ff = only
    "#;
    assert_eq!(File::try_from(tight)?.to_string(), tight);
    Ok(())
}

// DependsOn: legacy_and_quoted_headers_are_distinguished
// Sections with no values at all, with comments before, beside and after them,
// and with trailing whitespace on the header line. All of that is layout the
// implementation never generated and cannot regenerate, so reproducing it
// proves the original text is being carried rather than rebuilt.
#[test]
fn empty_sections_and_their_comments_survive_a_roundtrip() -> Result {
    let bare = "\n        [a]\n    [b]\n        [c] \n        \n            [d]\n";
    assert_eq!(File::try_from(bare)?.to_bstring(), bare);

    let commented = "; pre-a\n        [a] # side a\n        ; post a  \n    [b] ; side b\n        [c] ; side c\n        ; post c\n            [d] # side d\n";
    assert_eq!(File::try_from(commented)?.to_bstring(), commented);
    Ok(())
}

// DependsOn: the_three_parsing_entry_points_agree
// Appending one document to another has to be indistinguishable from
// concatenating their texts. Checked against a fixture full of comments,
// because a comment belongs to no section and is exactly what an implementation
// that reassembles the document from its sections would lose.
#[test]
fn appending_a_document_is_the_same_as_concatenating_its_text() -> Result {
    let input = "; pre-a\n        [a] # side a\n        ; post a  \n    [b] ; side b\n";
    let mut config = File::try_from(input)?;
    let mut doubled = config.to_bstring();
    assert_eq!(doubled, input);

    let clone = doubled.clone();
    doubled.push_str(&clone);
    assert_eq!(
        config.append(config.clone())?.to_string(),
        doubled,
        "data-structure duplication is string duplication"
    );
    Ok(())
}

// DependsOn: a_lossy_document_keeps_its_values_and_drops_its_layout
// The document that exercises everything at once: comments in every position,
// a subsection name containing escaped quotes and backslashes, implicit and
// empty entries, a continued colour value, and a shell alias continued over
// eight lines with quotes inside it. Parsed losslessly it must come back
// unchanged; parsed lossily it must still hold the same values, which is what
// comparing the re-parsed lossy text against the lossless document checks.
#[test]
fn a_document_using_every_feature_roundtrips_losslessly_and_lossily() -> Result {
    let input = r#"
        [core]
            repositoryformatversion = 0
            filemode = true
            bare = false

        [remote "origin"]
            url = git@github.com:GitoxideLabs/gitoxide.git
            fetch = +refs/heads/*:refs/remotes/origin/*

        [test]  # other comment
            other-quoted = "hello" ; comment
            implicit
            implicit-equal =
            implicit-equal-trailing-ws=

        ; more comments
        # another one

        [test "sub-section \"special\" C:\\root"] ; section comment
            bool-explicit = false
            bool-implicit
            integer-no-prefix = 10 ; a value comment
            integer-prefix = 10g
            color = brightgreen red \
            bold
            other = hello world
            other-quoted = "hello world"
            location = ~/tmp
            location-quoted = "~/quoted"
            escaped = \n\thi\b
            escaped-quoted = "\n\thi\b"

        [alias]
            save = "!f() { \
               git status; \
               git add "-A"; \
               git commit -m \"$1\"; \
               git push -f; \
               git log -1;  \
            }; \
            f;  \
            unset f" ; here we go
    "#;
    let config = File::try_from(input)?;
    assert_eq!(config.to_bstring(), input);

    let mut options = init::Options::default();
    options.lossy = true;
    let lossy = File::from_bytes_owned(&mut input.as_bytes().into(), Metadata::api(), options)?;
    let lossy: File = lossy.to_string().parse()?;
    assert_eq!(
        lossy, config,
        "a lossy document still serializes to text carrying every value"
    );
    Ok(())
}

// DependsOn: section_names_are_case_insensitive
// Equality is defined over what the document means, so it has to fold the case
// of section and value names -- and it has to stop there, because a quoted
// subsection name is compared byte for byte. Two documents differing only in
// subsection case are different documents.
#[test]
fn equality_folds_name_case_but_not_subsection_case() -> Result {
    let mixed_case = File::try_from("[Core]\nMixedCase = value\n[Remote \"Origin\"]\nURL = location\n")?;
    let equivalent = File::try_from("[core]\nmixedcase = value\n[remote \"Origin\"]\nurl = location\n")?;
    assert_eq!(mixed_case, equivalent, "section and value names fold");

    let different_subsection = File::try_from("[core]\nmixedcase = value\n[remote \"origin\"]\nurl = location\n")?;
    assert_ne!(
        mixed_case, different_subsection,
        "a quoted subsection name does not"
    );
    Ok(())
}

// DependsOn: legacy_and_quoted_headers_are_distinguished
// A subsection name is escaped in the file and decoded for lookup, and the two
// spellings differ. Lookup must use the decoded name; serialization must
// reproduce the raw one. Holding both at once is the whole point.
#[test]
fn a_subsections_raw_spelling_survives_a_lookup_by_its_decoded_name() -> Result {
    let input = "[remote \"single \\t \\0\"]\n";
    let config = File::try_from(input)?;
    let section = config
        .section("remote", Some("single t 0".into()))
        .expect("the decoded name is what lookup takes");

    assert_eq!(section.header().subsection_name(), Some("single t 0".into()));
    assert_eq!(
        config.to_bstring(),
        input,
        "while serialization reproduces the raw spelling"
    );
    Ok(())
}

// DependsOn: a_documents_newline_style_is_the_first_one_it_contains
// The newline style is detected once for the document and then used for
// everything inserted into it. Here the only CRLF in the file is on the
// comment line before the first section, and the section body that follows
// uses LF -- so a new section appended afterwards still has to be written with
// CRLF, both around its header and inside its body.
#[test]
fn a_newline_style_detected_before_the_first_section_is_used_for_insertions() -> Result {
    let mut config = File::try_from("; root\r\n[core]\nkey=value\n")?;
    assert_eq!(config.detect_newline_style(), "\r\n");

    config.new_section("new", None)?.push("key", Some("value".into()))?;
    assert_eq!(
        config.to_bstring(),
        "; root\r\n[core]\nkey=value\n\r\n[new]\r\n\tkey = value\r\n",
        "the detected style governs the new section boundary and its body"
    );
    Ok(())
}

// DependsOn: metadata_from_a_source_keeps_the_source_and_trusts_it_fully
// Sections take the document's metadata at the moment they are created, so
// changing that metadata between two insertions labels them differently.
// Filtered writing then selects on the label: only the section built while the
// metadata said `Local` is written out, headers and all.
#[test]
fn filtered_writing_selects_sections_by_the_metadata_they_were_created_with() -> Result {
    let mut config = File::new(Metadata::api());
    config.set_raw_value_by("a", None, "b", "c")?;

    config.set_meta(Metadata::from(Source::Local));
    config
        .new_section("a", "local")?
        .push("b", Some("c".into()))?
        .push("c", Some("d".into()))?;

    config.set_meta(Metadata::from(Source::User));
    config
        .new_section("a", "user")?
        .push("b", Some("c".into()))?
        .push("c", Some("d".into()))?;

    let mut buf = Vec::<u8>::new();
    config.write_to_filter(&mut buf, |section| section.meta().source == Source::Local)?;
    let nl = config.detect_newline_style();
    assert_eq!(buf.to_str_lossy(), format!("[a \"local\"]{nl}\tb = c{nl}\tc = d{nl}"));

    let mut everything = Vec::<u8>::new();
    config.write_to(&mut everything)?;
    assert_eq!(
        everything,
        config.to_bstring(),
        "and accepting every section writes what the document serializes to"
    );
    Ok(())
}

// DependsOn: the_default_metadata_is_the_api_metadata
// The companion to the filtered-writing test, checked at the point of
// creation: a section built before `set_meta` carries the old metadata and one
// built after carries the new, which is what makes the filter above able to
// tell them apart at all.
#[test]
fn a_section_takes_the_documents_metadata_at_the_moment_it_is_created() -> Result {
    let mut config = File::default();
    assert_eq!(config.meta(), &Metadata::api());
    assert_eq!(
        config.new_section("new", None)?.meta(),
        &Metadata::api(),
        "a section inherits the document's metadata"
    );

    let reduced = Metadata {
        path: None,
        source: Source::Local,
        level: 0,
        trust: gix_sec::Trust::Reduced,
    };
    config.set_meta(reduced.clone());
    assert_eq!(
        config.new_section("new", None)?.meta(),
        &reduced,
        "and picks up a later change"
    );
    Ok(())
}

// ── writing values back ───────────────────────────────────────────────────

// DependsOn: a_short_lived_key_may_address_a_value
// Setting a value has to escape it well enough that re-parsing the document
// yields the same bytes back. These eight are the shapes where naive writing
// breaks: whitespace at either end is lost unless quoted, a comment character
// turns the rest of the line into a comment, an embedded newline ends the
// entry, and quotes and backslashes need escaping to survive at all.
#[test]
fn a_value_written_back_reparses_to_itself_for_every_difficult_shape() -> Result {
    for value in [
        "hello world",
        "\ta",
        " a",
        "a\t",
        "a ",
        r#""hello"\"there"\\\b\x"#,
        "a\nb   \n\t   c",
        ";hello ",
        " # hello",
    ] {
        let mut config = file("[a]\nk=c\nk=d");
        config.set_raw_value_by("a", None, "k", value)?;
        assert_eq!(config.raw_value("a.k")?, value, "readable before serializing");

        let text = config.to_string();
        let reparsed: File = text.parse()?;
        assert_eq!(
            reparsed.raw_value("a.k")?,
            value,
            "and after: {text:?} should still hold {value:?}"
        );
    }
    Ok(())
}

// DependsOn: an_invalid_value_name_fails_without_creating_a_section
// The plain setter creates whatever it needs. A missing section is created, a
// missing subsection too, and the value is then readable through the comfort
// accessors under the key it was addressed by.
#[test]
fn setting_a_value_creates_the_section_and_subsection_it_needs() -> Result {
    let mut config = File::default();
    config.set_raw_value_by("new", None, "key", "value")?;
    config.set_raw_value_by("new", "subsection", "key", "subsection-value")?;

    assert_eq!(config.string("new.key").expect("present"), "value");
    assert_eq!(
        config
            .string_by("new", Some("subsection".into()), "key")
            .expect("present"),
        "subsection-value"
    );
    assert_eq!(config.sections().count(), 2, "one section per subsection");
    Ok(())
}

// DependsOn: set_existing_raw_value_never_creates_anything
// The existing-value setter rewrites the declaration that a read would have
// resolved to -- the last one -- and leaves the others in place. Checked
// across the same difficult shapes, and through a re-parse, because the
// rewrite happens inside a document that already has three declarations of the
// name spread over two sections.
#[test]
fn rewriting_an_existing_value_replaces_the_one_a_read_would_resolve_to() -> Result {
    for value in ["hello world", " a", "a\t", r#""hello"\"there"\\\b\x"#, "a\nb   \n\t   c", ";hello "] {
        let mut config = file("[a]k=b\n[a]\nk=c\nk=d");
        config.set_existing_raw_value_by("a", None, "k", value)?;
        assert_eq!(config.raw_value("a.k")?, value);

        let text = config.to_string();
        let reparsed: File = text.parse()?;
        assert_eq!(reparsed.raw_value("a.k")?, value, "{text:?}");
        assert_eq!(
            reparsed.raw_values("a.k")?.len(),
            3,
            "the other two declarations are still there"
        );
    }
    Ok(())
}

// DependsOn: a_value_read_through_a_mutable_view_is_normalized
// A mutable view can be taken on an entry written in any of seven ways -- with
// a value, with an empty value, with a bare separator, with no separator at
// all -- and setting through it must produce a document that re-parses to the
// value that was set. The empty and whitespace-only cases are the ones that
// force quoting to appear where the original had none.
#[test]
fn setting_through_a_mutable_view_works_from_every_starting_shape() -> Result {
    let nl = common::newline();
    for expected in [
        "",
        "\t ",
        " v",
        "hello world",
        "\ta",
        "a ",
        r#""hello"\"there"\\\b\x"#,
        "a\nb   \n\t   c",
        ";hello ",
        " # hello",
        "value then seemingly # comment",
    ] {
        for input in [
            "[a] k = v",
            "[a] k = ",
            "[a] k =",
            "[a] k =$nl",
            "[a] k ",
            "[a] k$nl",
            "[a] k",
        ] {
            let mut config: File = input.replace("$nl", &nl).parse()?;
            let mut value = config.raw_value_mut_by("a", None, "k")?;
            value.set_string(expected)?;
            assert_eq!(value.get()?, expected, "readable through the view");

            let text = config.to_string();
            let reparsed: File = text.parse()?;
            assert_eq!(
                reparsed.raw_value("a.k")?,
                expected,
                "{input:?} set to {expected:?} serialized to {text:?}"
            );
        }
    }
    Ok(())
}

// DependsOn: an_empty_continuation_line_ends_the_value
// A standalone comment after a continuation marker ends the value rather than
// continuing it. That comment is not part of the entry, so replacing the value
// must leave it untouched on its own line -- checked for both comment
// characters and both newline styles, since the continuation, the comment and
// the newline interact.
#[test]
fn a_comment_that_ends_a_continued_value_survives_the_values_replacement() -> Result {
    for newline in ["\n", "\r\n"] {
        for comment in ["# comment", "; comment"] {
            let mut config: File =
                format!("[a]{newline}k=one\\{newline}{comment}{newline}next=value").parse()?;
            let mut value = config.raw_value_mut_by("a", None, "k")?;
            assert_eq!(value.get()?, "one", "the comment ended the continued value");
            value.set_string("replacement")?;
            assert_eq!(
                config.to_string(),
                format!("[a]{newline}k=replacement{newline}{comment}{newline}next=value{newline}"),
                "the comment stayed on its own line"
            );
        }
    }
    Ok(())
}

// DependsOn: escape_sequences_inside_a_quoted_value_are_resolved
// The mirror image of the previous test: inside quotes the same characters are
// ordinary content, so they belong to the value across a continuation and must
// come back out of a rewrite still quoted -- otherwise the document that was
// just written would parse as a value with a comment attached.
#[test]
fn quoted_comment_characters_stay_value_content_across_a_rewrite() -> Result {
    let mut config: File = "[a]\nk=\"one\\\n#not;comments\"\nnext=value".parse()?;
    let mut value = config.raw_value_mut_by("a", None, "k")?;
    let normalized = value.get()?;
    assert_eq!(normalized, "one#not;comments");

    value.set(normalized)?;
    assert_eq!(
        config.to_string(),
        "[a]\nk=\"one#not;comments\"\nnext=value\n",
        "the rewrite re-quotes what would otherwise become a comment"
    );
    Ok(())
}

// DependsOn: a_value_read_through_a_mutable_view_is_normalized
// Rewriting one entry must disturb nothing else -- not the indentation of the
// other entries, not the second section, not even the value's own separator
// spelling. The fixture's first value is `b"100"`, whose quotes sit in the
// middle, so an implementation tracking the wrong extent overwrites too much
// or too little.
#[test]
fn rewriting_one_value_leaves_every_other_byte_in_place() -> Result {
    let mut config = value_config();

    config.raw_value_mut_by("core", None, "a")?.set_string("hello world")?;
    assert_eq!(
        config.to_string(),
        "[core]\n            a=hello world\n        [core]\n            c=d\n            e=f\n"
    );

    config.raw_value_mut_by("core", None, "e")?.set_string(String::new())?;
    assert_eq!(
        config.to_string(),
        "[core]\n            a=hello world\n        [core]\n            c=d\n            e=\n",
        "setting the empty string keeps the entry and empties it"
    );
    Ok(())
}

// DependsOn: a_value_read_through_a_mutable_view_is_normalized
// Deleting an entry removes the entry, not the line it sat on: the leading
// whitespace stays behind. Repeating the deletion changes nothing further, so
// a caller that cannot tell whether it already deleted is safe to try again.
#[test]
fn deleting_a_value_leaves_its_indentation_and_is_idempotent() -> Result {
    let mut config = value_config();
    config.raw_value_mut_by("core", None, "a")?.delete();
    assert_eq!(
        config.to_string(),
        "[core]\n            \n        [core]\n            c=d\n            e=f\n"
    );

    config.raw_value_mut_by("core", None, "c")?.delete();
    assert_eq!(
        config.to_string(),
        "[core]\n            \n        [core]\n            \n            e=f\n"
    );

    let mut config = value_config();
    {
        let mut value = config.raw_value_mut_by("core", None, "a")?;
        for _ in 0..3 {
            value.delete();
        }
    }
    assert_eq!(
        config.to_string(),
        "[core]\n            \n        [core]\n            c=d\n            e=f\n",
        "deleting three times reads the same as deleting once"
    );
    Ok(())
}

// DependsOn: a_value_read_through_a_mutable_view_is_normalized
// A view whose entry was deleted has nothing to read, but it is not spent:
// setting through it re-creates the entry where it used to be, with the
// original separator spelling and in the original position, rather than
// appending a new one at the end of the section.
#[test]
fn a_view_outlives_the_deletion_of_its_value_and_can_recreate_it() -> Result {
    let mut config = value_config();
    {
        let mut value = config.raw_value_mut_by("core", None, "a")?;
        value.delete();
        assert!(value.get().is_err(), "there is nothing to read any more");
        value.set_string("hello world")?;
    }
    assert_eq!(
        config.to_string(),
        "[core]\n            a=hello world\n        [core]\n            c=d\n            e=f\n",
        "the entry is back in the place the deleted one occupied"
    );
    assert_eq!(config.string("core.a"), Some(bstring("hello world")));
    Ok(())
}

// DependsOn: a_continued_value_is_joined_into_one_line
// A value continued over three lines is one entry, so deleting it has to take
// all three lines with it. Deleting only the first would leave two orphaned
// fragments that re-parse as garbage.
#[test]
fn deleting_a_continued_value_removes_all_of_its_lines() -> Result {
    let mut config: File = "[core]\n            a=b\"100\"\\\nc\\\nb\n        [core]\n            c=d\n            e=f"
        .parse()?;
    let mut value = config.raw_value_mut_by("core", None, "a")?;
    assert_eq!(value.get()?, "b100cb");
    value.delete();
    assert_eq!(
        config.to_string(),
        "[core]\n            \n        [core]\n            c=d\n            e=f\n"
    );
    Ok(())
}

// ── multivars ─────────────────────────────────────────────────────────────

// DependsOn: a_multivar_view_reports_how_many_declarations_it_covers
// A multivar view spans declarations in more than one section, and each of
// them may itself be continued over several lines. Reading through the view
// normalizes every one; deleting them all leaves nothing to read.
#[test]
fn a_multivar_view_reads_continued_declarations_from_several_sections() -> Result {
    let mut config: File =
        "[core]\n            a=b\\\n\"100\"\n        [core]\n            a=d\\\n\"b  \"\\\nc\n            a=f\\\n   a"
            .parse()?;

    let mut values = config.raw_values_mut_by("core", None, "a")?;
    assert_eq!(
        &*values.get()?,
        vec![bstring("b100"), bstring("db  c"), bstring("f   a")]
    );

    values.delete_all();
    assert!(values.get().is_err(), "an emptied multivar has nothing to read");
    Ok(())
}

// DependsOn: every_declaration_of_a_multivar_is_returned_in_file_order
// Assigning one value to every declaration has to escape it once per
// declaration, and the three declarations here are spelled with three
// different separator layouts. Re-parsing is what makes the check real: it
// says the written text means what was assigned, not merely that it looks
// plausible.
#[test]
fn assigning_to_a_whole_multivar_escapes_each_declaration() -> Result {
    for value in ["a b", " a b", "a b\t", ";c", "#c", "a\nb\n\tc"] {
        let mut config = multi_value_config();
        config.raw_values_mut_by("core", None, "a")?.set_all(value)?;

        let text = config.to_string();
        let reparsed: File = text.parse()?;
        assert_eq!(
            reparsed.raw_values("core.a")?,
            vec![bstring(value), bstring(value), bstring(value)],
            "{text:?}"
        );
    }
    Ok(())
}

// DependsOn: a_multivar_view_reports_how_many_declarations_it_covers
// Indices into a multivar count declarations in file order across sections, so
// index 0 is in the first section and index 2 in the second. Writing to one
// must leave the other two exactly as they were spelled, quotes included.
#[test]
fn writing_to_one_index_of_a_multivar_leaves_the_others_untouched() -> Result {
    let mut config = multi_value_config();
    config
        .raw_values_mut_by("core", None, "a")?
        .set_string_at(0, "Hello")?;
    assert_eq!(
        config.to_string(),
        "[core]\n    a = Hello\n    [core]\n        a =d\n        a= f\n"
    );

    let mut config = multi_value_config();
    config
        .raw_values_mut_by("core", None, "a")?
        .set_string_at(2, "Hello")?;
    assert_eq!(
        config.to_string(),
        "[core]\n    a = b\"100\"\n    [core]\n        a =d\n        a= Hello\n",
        "the first declaration keeps its quotes"
    );
    Ok(())
}

// DependsOn: a_multivar_view_reports_how_many_declarations_it_covers
// Assigning to the whole multivar rewrites all three declarations in place.
// The empty case is the interesting one: an entry set to the empty string
// keeps its separator, so it stays an explicitly-empty value rather than
// becoming an implicit one, which would flip how it reads as a boolean.
#[test]
fn assigning_to_a_whole_multivar_rewrites_every_declaration_in_place() -> Result {
    let mut config = multi_value_config();
    config.raw_values_mut_by("core", None, "a")?.set_all("Hello")?;
    assert_eq!(
        config.to_string(),
        "[core]\n    a = Hello\n    [core]\n        a= Hello\n        a =Hello\n"
    );

    let mut config = multi_value_config();
    config.raw_values_mut_by("core", None, "a")?.set_all("")?;
    assert_eq!(
        config.to_string(),
        "[core]\n    a = \n    [core]\n        a= \n        a =\n"
    );
    let emptied: File = config.to_string().parse()?;
    assert_eq!(
        emptied.boolean("core.a"),
        Ok(Some(false)),
        "the separators survived, so the values are empty rather than implicit"
    );
    Ok(())
}

// DependsOn: a_multivar_view_reports_how_many_declarations_it_covers
// Deleting by index renumbers what remains: after removing index 0 the view
// covers two declarations, and index 1 now addresses the one that used to be
// at index 2. Deleting the whole multivar twice is not an error.
#[test]
fn deleting_from_a_multivar_renumbers_the_remaining_declarations() -> Result {
    let mut config = multi_value_config();
    {
        let mut values = config.raw_values_mut_by("core", None, "a")?;
        values.delete(0);
        assert_eq!(
            config.to_string(),
            "[core]\n    \n    [core]\n        a =d\n        a= f\n"
        );
    }
    {
        let mut values = config.raw_values_mut_by("core", None, "a")?;
        assert_eq!(values.len(), 2, "the view now covers what is left");
        values.delete(1);
    }
    assert_eq!(
        config.to_string(),
        "[core]\n    \n    [core]\n        a =d\n        ",
        "index 1 addressed the declaration that had been at index 2"
    );

    let mut config = multi_value_config();
    let mut values = config.raw_values_mut_by("core", None, "a")?;
    values.delete_all();
    values.delete_all();
    assert!(values.get().is_err());
    assert_eq!(
        config.to_string(),
        "[core]\n    \n    [core]\n        \n        "
    );
    Ok(())
}

// DependsOn: an_implicit_declaration_is_skipped_when_resolving_a_raw_value
// A filter restricts which sections a mutation may land in. Rejecting the last
// section makes the write fall back to the earlier one, and the two spellings
// of the same call -- by key and by components -- have to agree about that.
#[test]
fn a_filtered_mutation_lands_in_the_last_accepted_section() -> Result {
    let mut config = File::try_from("[core]\na=first\n[core]\na=second\n")?;

    let mut reject_last_section = true;
    config
        .raw_value_mut_filter("core.a", |_| !std::mem::take(&mut reject_last_section))?
        .set("changed")?;
    assert_eq!(config.raw_values("core.a")?, ["changed", "second"]);

    config
        .raw_value_mut_filter_by(String::from("core"), None, String::from("a"), |_| true)?
        .set("last")?;
    assert_eq!(
        config.raw_values("core.a")?,
        ["changed", "last"],
        "the component variant accepts owned components and the same semantics"
    );
    assert_eq!(config.to_string(), "[core]\na=changed\n[core]\na=last\n");
    Ok(())
}

// DependsOn: an_implicit_declaration_is_skipped_when_resolving_a_raw_value
// The read-side counterpart: a filtered read reports both the value and the
// section it came from, and rejecting the last section moves both answers to
// the earlier one.
#[test]
fn a_filtered_read_reports_the_value_and_the_section_it_came_from() -> Result {
    let config = File::try_from("[core]\na=first\n[core]\na=second\n")?;
    let first = config.sections().next().expect("first section").id();

    let mut reject_last_section = true;
    let (value, section) =
        config.raw_value_with_section_filter("core.a", |_| !std::mem::take(&mut reject_last_section))?;
    assert_eq!(value, "first");
    assert_eq!(section.id(), first, "the section the filter accepted");
    Ok(())
}

// DependsOn: every_declaration_of_a_multivar_is_returned_in_file_order
// Reading a multivar with its sections pairs each declaration with the section
// that holds it, in file order -- two from the first section, one from the
// second. A filter applied to the same query keeps only the declarations from
// accepted sections, which is how a caller restricts a lookup to, say, values
// that came from the repository rather than from the user.
#[test]
fn every_declaration_can_be_paired_with_the_section_that_holds_it() -> Result {
    let config = File::try_from("[core]\na=b\na=c\n[core]a=d")?;
    let ids: Vec<_> = config.sections().map(|section| section.id()).collect();

    let paired: Vec<_> = config
        .raw_values_with_sections("core.a")?
        .into_iter()
        .map(|(value, section)| (value, section.id()))
        .collect();
    assert_eq!(
        paired,
        [
            (bstring("b"), ids[0]),
            (bstring("c"), ids[0]),
            (bstring("d"), ids[1]),
        ]
    );
    assert_eq!(config.raw_values_with_sections_by("core", None, "a")?.len(), 3);

    let mut reject_first_section = true;
    let filtered: Vec<_> = config
        .raw_values_with_sections_filter("core.a", |_| !std::mem::take(&mut reject_first_section))?
        .into_iter()
        .map(|(value, section)| (value, section.id()))
        .collect();
    assert_eq!(
        filtered,
        [(bstring("d"), ids[1])],
        "only declarations from accepted sections are returned"
    );
    assert_eq!(
        config
            .raw_values_with_sections_filter_by("core", None, "a", |_| true)?
            .len(),
        3
    );
    Ok(())
}

// ── renaming and removing sections ────────────────────────────────────────

// DependsOn: renaming_a_section_validates_the_new_name
// Renaming addresses a name-and-subsection pair, not a single section, so
// every section carrying that pair is renamed. Sections already carrying the
// target name are left alone rather than merged into, which is why the result
// has three sections spelled `dest` in three different places.
#[test]
fn renaming_a_section_renames_every_match_and_preserves_collisions() -> Result {
    let mut config = File::try_from(
        "[branch \"source\"] key = one\n\
         [some \"gar\"] key = unrelated\n\
         [branch \"dest\"] key = existing\n\
         [branch \"source\"] key = two\n",
    )?;

    config.rename_section("branch", "source", "branch", "dest")?;
    assert_eq!(
        config.to_string(),
        "[branch \"dest\"]\n key = one\n\
         [some \"gar\"]\n key = unrelated\n\
         [branch \"dest\"]\n key = existing\n\
         [branch \"dest\"]\n key = two\n",
        "a rewritten header is followed by the document's newline"
    );
    assert_eq!(
        config
            .sections_by_name("branch")
            .expect("three sections")
            .count(),
        3
    );
    assert!(
        config.section("branch", "source").is_err(),
        "nothing answers to the old identity any more"
    );
    Ok(())
}

// DependsOn: metadata_from_a_source_keeps_the_source_and_trusts_it_fully
// The filtered rename selects among the matching sections by their metadata.
// Marking the first and third with a reduced trust level and filtering on that
// renames exactly those two and leaves the middle one alone. A filter that
// accepts nothing is an error rather than a silent no-op, and it must not have
// changed the document on its way to that error.
#[test]
fn a_rename_filter_selects_which_matching_sections_are_renamed() -> Result {
    let mut config = File::try_from(
        "[branch \"source\"] key = one\n\
         [branch \"source\"] key = two\n\
         [branch \"source\"] key = three\n",
    )?;
    let ids: Vec<_> = config
        .sections_and_ids_by_name("branch")
        .expect("branch sections exist")
        .map(|(_, id)| id)
        .collect();
    config
        .section_mut_by_id(ids[0])
        .expect("first section")
        .set_trust(gix_sec::Trust::Reduced);
    config
        .section_mut_by_id(ids[2])
        .expect("third section")
        .set_trust(gix_sec::Trust::Reduced);

    config.rename_section_filter("branch", "source", "branch", "dest", |meta| {
        meta.trust == gix_sec::Trust::Reduced
    })?;
    assert_eq!(
        config.to_string(),
        "[branch \"dest\"]\n key = one\n\
         [branch \"source\"]\n key = two\n\
         [branch \"dest\"]\n key = three\n"
    );

    let unchanged = config.to_string();
    assert!(
        matches!(
            config.rename_section_filter("branch", "source", "branch", "other", |_| false),
            Err(gix_config::file::rename_section::Error::Lookup(
                gix_config::lookup::existing::Error::KeyMissing
            ))
        ),
        "matching nothing is an error"
    );
    assert_eq!(config.to_string(), unchanged, "and changes nothing");
    Ok(())
}

// DependsOn: legacy_and_quoted_headers_are_distinguished
// Renaming a section to the identity it already has is not a no-op at the text
// level: the headers are rewritten, and rewriting only ever produces the
// quoted spelling. Two legacy dotted headers therefore come back quoted.
#[test]
fn renaming_to_the_same_identity_rewrites_legacy_headers() -> Result {
    let mut config = File::try_from("[branch.source] one = 1\n[branch.source] two = 2\n")?;
    assert!(
        config.sections().all(|section| section.header().is_legacy()),
        "both headers start out in the legacy spelling"
    );

    config.rename_section("branch", "source", "branch", "source")?;
    assert_eq!(
        config.to_string(),
        "[branch \"source\"]\n one = 1\n[branch \"source\"]\n two = 2\n"
    );
    assert!(
        config.sections().all(|section| !section.header().is_legacy()),
        "we only ever write the quoted spelling"
    );
    assert_eq!(config.string("branch.source.one").expect("present"), "1");
    Ok(())
}

// DependsOn: a_section_can_be_addressed_by_its_id
// Renaming through a section handle addresses one section unambiguously, even
// when three others share its name or its target name. Afterwards the renamed
// section is reachable under the new identity and its former namesake is still
// reachable under the old one, so the lookup index was updated rather than
// rebuilt from scratch.
#[test]
fn renaming_one_section_by_id_leaves_its_namesakes_alone() -> Result {
    let mut config = File::try_from(
        "[target \"same\"] key = first\n\
         [source \"old\"] key = selected\n\
         [target \"same\"] key = middle\n\
         [source \"old\"] key = last\n",
    )?;
    let selected = config
        .sections_and_ids_by_name("source")
        .expect("source sections exist")
        .next()
        .expect("at least one")
        .1;

    config
        .section_mut_by_id(selected)
        .expect("selected section")
        .rename("target", "same")?;

    assert_eq!(
        config.to_string(),
        "[target \"same\"]\n key = first\n\
         [target \"same\"]\n key = selected\n\
         [target \"same\"]\n key = middle\n\
         [source \"old\"]\n key = last\n"
    );
    assert_eq!(
        config.section("source", Some("old".as_bytes().as_bstr()))?.value("key"),
        Some(bstring("last")),
        "the other section of that name is still there"
    );
    assert_eq!(
        config
            .sections_by_name("target")
            .expect("three sections")
            .count(),
        3
    );
    Ok(())
}

// DependsOn: renaming_a_section_validates_the_new_name
// A rename that fails validation must fail completely: the section keeps its
// old identity and its values, and no section appears under the sanitized form
// of the rejected name.
#[test]
fn a_rejected_rename_leaves_an_attached_section_exactly_as_it_was() -> Result {
    let mut config = File::try_from("[core] key = value\n")?;
    let before = config.to_string();
    assert!(config.section_mut("core", None)?.rename("not_valid", None).is_err());

    assert_eq!(
        config.section("core", None)?.value("key"),
        Some(bstring("value")),
        "no change was performed"
    );
    assert!(
        config.section("not-valid", None).is_err(),
        "and the name is not present in a repaired spelling either"
    );
    assert_eq!(config.to_string(), before);
    Ok(())
}

// DependsOn: a_section_id_is_never_the_default_one
// A section can be detached from the document, mutated while detached, and put
// back. Reinsertion assigns a fresh identifier -- the old one is spent -- and
// the mutation made while detached is visible through every lookup afterwards.
#[test]
fn a_removed_section_can_be_mutated_while_detached_and_pushed_back() -> Result {
    let mut config = File::try_from("[core]\na = b\n")?;
    let mut section = config.remove_section("core", None).expect("section is present");
    let removed_id = section.to_ref().id();

    section.to_mut().set("detached", "changed")?;
    assert_eq!(section.to_ref().value("detached"), Some(bstring("changed")));

    let inserted_id = config.push_section(section)?.id();
    assert_ne!(inserted_id, removed_id, "reinsertion assigns a fresh identifier");
    assert_eq!(config.section("core", None)?.value("detached"), Some(bstring("changed")));
    assert_eq!(config.string("core.detached"), Some(bstring("changed")));
    assert_eq!(config.string("core.a"), Some(bstring("b")), "and the old value stayed");
    Ok(())
}

// DependsOn: a_new_section_is_appended_with_its_own_header
// Removing a section and immediately putting it back must leave the document
// serializing to what it did before. It is the sharpest statement of the rule
// that reinsertion adds no newline of its own: a section that already ends in
// one would otherwise grow a blank line every time it made the round trip.
#[test]
fn a_section_removed_and_reinserted_serializes_to_what_it_did_before() -> Result {
    let mut config = File::try_from("[core]\n\ta = b\n[other]\n\tc = d\n")?;
    let before = config.to_bstring();

    let section = config.remove_section("core", None).expect("present");
    config.push_section(section)?;

    assert_eq!(
        config.to_bstring(),
        "[other]\n\tc = d\n[core]\n\ta = b\n",
        "the section moved to the end, byte for byte"
    );
    assert_eq!(
        config.to_bstring().len(),
        before.len(),
        "and nothing was added or lost on the way"
    );
    assert_eq!(config.string("core.a"), Some(bstring("b")));
    Ok(())
}

// DependsOn: a_default_file_is_empty_and_void
// Removing every section by identifier empties the document completely -- not
// just of values, but of sections, so that it reports itself as void again.
// Both ways of enumerating identifiers have to reach the same set.
#[test]
fn removing_every_section_by_id_empties_the_document() -> Result {
    let text = "[core] \na = b\nb=c\n\n[core \"name\"]\nd = 1\ne = 2";

    let mut config = File::try_from(text)?;
    for id in config
        .sections_and_ids_by_name("core")
        .expect("two sections present")
        .map(|(_, id)| id)
        .collect::<Vec<_>>()
    {
        assert!(config.remove_section_by_id(id).is_some());
    }
    assert!(config.is_void());
    assert_eq!(config.sections().count(), 0);

    let mut config = File::try_from(text)?;
    for id in config.sections_and_ids().map(|(_, id)| id).collect::<Vec<_>>() {
        assert!(config.remove_section_by_id(id).is_some());
    }
    assert!(config.is_void());
    assert_eq!(config.sections().count(), 0);
    Ok(())
}

// DependsOn: a_missing_section_subsection_and_value_are_distinguished
// Removing the plain `core` section leaves its subsections in place, so the
// name is still known and the failure to find it changes shape: a missing
// subsection, not a missing section. Only when the last subsection goes does
// the name itself disappear.
#[test]
fn removing_a_section_retires_only_its_own_lookup_bucket() -> Result {
    let mut config = File::try_from(
        "[core] key=plain\n\
         [core \"a\"] key=a\n\
         [core \"b\"] key=b\n",
    )?;

    config.remove_section("core", None).expect("plain section exists");
    assert!(
        matches!(
            config.section("core", None),
            Err(gix_config::lookup::existing::Error::SubSectionMissing)
        ),
        "the name survives through its siblings"
    );
    assert_eq!(config.section("core", "a")?.value("key"), Some(bstring("a")));

    config.remove_section("core", "a").expect("first subsection exists");
    assert_eq!(config.section("core", "b")?.value("key"), Some(bstring("b")));

    config.remove_section("core", "b").expect("final subsection exists");
    assert!(matches!(
        config.section("core", "b"),
        Err(gix_config::lookup::existing::Error::SectionMissing)
    ));
    Ok(())
}

// DependsOn: section_mut_or_create_new_always_yields_a_section
// Removal is idempotent -- trying again on an already-removed section returns
// nothing rather than failing -- and it retires the name completely, so the
// same identity can be created afresh afterwards. Checked through both the
// plain and the filtered remover, which differ only in how they choose among
// candidates.
#[test]
fn a_removed_section_can_be_created_again_under_the_same_name() -> Result {
    for filtered in [false, true] {
        let mut config = File::try_from("[core] \na = b\nb=c\n\n[core \"name\"]\nd = 1\ne = 2")?;
        assert_eq!(config.sections().count(), 2);

        let mut remove = |name: &str, sub: Option<&str>| {
            let sub = sub.map(|s| s.as_bytes().as_bstr());
            if filtered {
                config.remove_section_filter(name, sub, |_| true)
            } else {
                config.remove_section(name, sub)
            }
        };

        let removed = remove("core", None).expect("the plain section");
        assert_eq!(removed.to_ref().header().name(), "core");
        assert_eq!(removed.to_ref().header().subsection_name(), None);

        let removed = remove("core", Some("name")).expect("the subsection");
        assert_eq!(removed.to_ref().header().subsection_name(), Some("name".into()));

        assert!(remove("core", None).is_none(), "trying again is not an error");
        assert!(remove("core", Some("name")).is_none());

        assert_eq!(config.sections().count(), 0);
        config.section_mut_or_create_new("core", None)?;
        config.section_mut_or_create_new("core", "name")?;
        assert_eq!(config.sections().count(), 2, "the identities are free again");
    }
    Ok(())
}

// ── mutating a section's values ───────────────────────────────────────────

// DependsOn: value_names_are_handed_out_as_strings
// Removing the five entries one at a time hands back each previous value in
// turn -- including the empty ones and the value continued over three lines,
// which is returned normalized. What is left is the header and the whitespace
// around it, so the section is emptied but not void.
#[test]
fn removing_every_value_leaves_the_section_and_its_whitespace() -> Result {
    let mut config = multi_value_section();
    let mut section = config.section_mut("a", None)?;
    assert_eq!(section.num_values(), 5);
    assert_eq!(section.value_names().count(), 5);

    let previous = ["v", "", "", "", "a        b        c"];
    let mut remaining = section.num_values();
    for (name, expected) in ('a'..='e').zip(previous) {
        let removed = section.remove(&name.to_string());
        remaining -= 1;
        assert_eq!(removed.expect("present"), expected);
        assert_eq!(section.num_values(), remaining);
    }

    assert!(!section.is_void(), "the whitespace is still there");
    assert_eq!(config.to_string(), "\n        [a]\n");
    Ok(())
}

// DependsOn: value_names_are_handed_out_as_strings
// Popping reaches the same end state from the other direction, taking the last
// entry each time instead of a named one, and reaching it through the
// two-part-key spelling of the section lookup.
#[test]
fn popping_every_value_leaves_the_section_and_its_whitespace() -> Result {
    let mut config = multi_value_section();
    let mut section = config.section_mut_by_key("a")?;
    assert_eq!(section.num_values(), 5);

    for name in ['a', 'b', 'c', 'd', 'e'] {
        assert!(section.contains_value_name(&name.to_string()));
    }

    let mut remaining = section.num_values();
    for _ in 0..5 {
        assert!(section.pop().is_some());
        remaining -= 1;
        assert_eq!(section.num_values(), remaining);
    }
    assert!(!section.is_void());
    assert_eq!(config.to_string(), "\n        [a]\n");
    Ok(())
}

// DependsOn: a_pushed_value_is_quoted_only_when_it_has_to_be
// Replacing a value in place returns what was there and keeps the entry's own
// separator spelling: the entry written `c=` stays written without spaces
// around the separator, and the one written `d` with no separator at all gains
// none. Each new value is escaped according to what it contains, so the
// document still re-parses to the values that were assigned.
#[test]
fn replacing_values_keeps_each_entrys_separator_and_escapes_the_new_value() -> Result {
    let mut config = multi_value_section();
    let mut section = config.section_mut("a", None)?;
    let new_values = ["", " a", "b\t", "; comment", "a\n\tc  d\\ \"x\""];
    let previous = ["v", "", "", "", "a        b        c"];
    assert_eq!(section.num_values(), new_values.len());

    for (name, (new_value, expected_previous)) in ('a'..='e').zip(new_values.into_iter().zip(previous)) {
        let replaced = section.set(&name.to_string(), new_value)?;
        assert_eq!(replaced.expect("every name was present"), expected_previous);
    }

    assert_eq!(
        config.to_string(),
        "\n        [a]\n            a = \n            b = \" a\"\n            c=\"b\\t\"\n            d\"; comment\"\n            e =a\\n\\tc  d\\\\ \\\"x\\\"\n"
    );
    assert_eq!(
        config.section_mut("a", None)?.set("new-one", "value")?,
        None,
        "a name that was not there replaces nothing"
    );

    assert_eq!(
        config.section("a", None)?.values("e"),
        vec![bstring("a\n\tc  d\\ \"x\"")],
        "and the escaped replacement reads back through the document"
    );
    Ok(())
}

// DependsOn: a_pushed_value_is_quoted_only_when_it_has_to_be
// A value pushed with a comment has to re-parse to the value alone: the
// comment is not part of it. Together with the entry that has no value at all,
// this checks that what was written can be read back through the ordinary
// accessors rather than only through the text.
#[test]
fn pushed_entries_and_their_comments_reparse_to_the_values_alone() -> Result {
    let mut config = File::default();
    {
        let mut section = config.new_section("a", "sub")?;
        section.push_with_comment("commented", Some("value".into()), "why it is set")?;
        section.push("implicit", None)?;
        section.push("quoted", Some(" needs quoting ".into()))?;
    }

    let reparsed: File = config.to_string().parse()?;
    assert_eq!(
        reparsed.string_by("a", Some("sub".into()), "commented").expect("present"),
        "value",
        "the comment is not part of the value"
    );
    assert_eq!(
        reparsed.boolean_by("a", Some("sub".into()), "implicit"),
        Ok(Some(true)),
        "an entry pushed without a value is implicit"
    );
    assert_eq!(
        reparsed.string_by("a", Some("sub".into()), "quoted").expect("present"),
        " needs quoting ",
        "the surrounding whitespace survived because it was quoted"
    );
    Ok(())
}
