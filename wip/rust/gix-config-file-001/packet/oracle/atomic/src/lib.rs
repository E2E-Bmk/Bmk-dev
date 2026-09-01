//! Atomic layer: one documented behavior per test.
//!
//! Each test drives a single entry point of the declared surface and asserts
//! on what came back. Where a behavior is defined over a family of spellings
//! -- the seven ways an implicit boolean can be followed by whitespace, the
//! ten `Source` variants -- the family is walked inside one test, because the
//! behavior is one clause of the specification and splitting it would report a
//! single misunderstanding as several independent failures.
//!
//! Everything here is derived from the crate's own test suite at the carve
//! commit, rewritten so that no assertion depends on a snapshot file, on a
//! fixture read from disk, on an environment variable, or on a symbol outside
//! the specification's API Catalog. `filter/rewrite_audit.md` records each
//! change and why it was made.

use bstr::{BString, ByteSlice};
use common::{bstring, file, multi_value_section, newline, panics};
use gix_config::{
    color,
    file::{init, Metadata, Section, SectionId},
    integer, lookup,
    parse::section,
    source::Kind,
    value::normalize,
    AsKey, Boolean, Color, File, Integer, KeyRef, Source,
};

type Result = std::result::Result<(), Box<dyn std::error::Error>>;

// ── sources, kinds and storage locations ─────────────────────────────────

#[test]
fn every_source_belongs_to_exactly_one_kind() {
    assert_eq!(Source::GitInstallation.kind(), Kind::GitInstallation);
    assert_eq!(Source::System.kind(), Kind::System);
    assert_eq!(Source::Git.kind(), Kind::Global);
    assert_eq!(Source::User.kind(), Kind::Global);
    assert_eq!(Source::Local.kind(), Kind::Repository);
    assert_eq!(Source::Worktree.kind(), Kind::Repository);
    assert_eq!(Source::Env.kind(), Kind::Override);
    assert_eq!(Source::Cli.kind(), Kind::Override);
    assert_eq!(Source::Api.kind(), Kind::Override);
    assert_eq!(
        Source::EnvOverride.kind(),
        Kind::Override,
        "the override applied after everything else is still an override"
    );
}

#[test]
fn a_kind_lists_its_sources_in_ascending_precedence() {
    assert_eq!(
        Kind::GitInstallation.sources(),
        [Source::GitInstallation].as_slice()
    );
    assert_eq!(Kind::System.sources(), [Source::System].as_slice());
    assert_eq!(Kind::Global.sources(), [Source::Git, Source::User].as_slice());
    assert_eq!(
        Kind::Repository.sources(),
        [Source::Local, Source::Worktree].as_slice()
    );
    assert_eq!(
        Kind::Override.sources(),
        [Source::Env, Source::Cli, Source::Api].as_slice(),
        "`EnvOverride` classifies as an override but is not one of the sources a caller loads"
    );

    for kind in [
        Kind::GitInstallation,
        Kind::System,
        Kind::Global,
        Kind::Repository,
        Kind::Override,
    ] {
        for pair in kind.sources().windows(2) {
            assert!(pair[0] < pair[1], "{pair:?} is listed in ascending precedence");
        }
        for source in kind.sources() {
            assert_eq!(source.kind(), kind, "{source:?} classifies back to {kind:?}");
        }
    }
}

#[test]
fn nosystem_suppresses_the_installation_and_system_locations() {
    for source in [Source::GitInstallation, Source::System] {
        let mut consulted = Vec::new();
        let location = source.storage_location(&mut |name| {
            consulted.push(name.to_owned());
            Some("1".into())
        });
        assert_eq!(location, None, "{source:?} has no location once the guard is set");
        assert_eq!(
            consulted,
            ["GIT_CONFIG_NOSYSTEM"],
            "no further variable is read once the guard answers"
        );
    }
}

#[test]
fn the_system_location_follows_git_config_system() {
    let location = Source::System.storage_location(&mut |name| match name {
        "GIT_CONFIG_NOSYSTEM" => None,
        "GIT_CONFIG_SYSTEM" => Some("alternative".into()),
        unexpected => unreachable!("unexpected variable: {unexpected}"),
    });
    assert_eq!(
        location.expect("the override names a path"),
        std::path::Path::new("alternative")
    );
}

#[test]
fn the_global_location_follows_git_config_global() {
    for source in [Source::Git, Source::User] {
        let mut consulted = Vec::new();
        let location = source.storage_location(&mut |name| {
            consulted.push(name.to_owned());
            Some("alternative".into())
        });
        assert_eq!(
            location.expect("the override names a path"),
            std::path::Path::new("alternative"),
            "{source:?} respects the global override"
        );
        assert_eq!(consulted, ["GIT_CONFIG_GLOBAL"]);
    }
}

#[test]
fn repository_locations_are_relative_and_read_no_variable() {
    let mut unreached = |_: &str| -> Option<std::ffi::OsString> {
        unreachable!("a repository-local location consults no environment variable")
    };
    assert_eq!(
        Source::Local.storage_location(&mut unreached).expect("always set"),
        std::path::Path::new("config"),
        "relative to the common directory"
    );
    assert_eq!(
        Source::Worktree.storage_location(&mut unreached).expect("always set"),
        std::path::Path::new("config.worktree"),
        "relative to the git directory"
    );
}

#[test]
fn override_sources_have_no_persistent_location() {
    for source in [Source::Env, Source::Cli, Source::Api, Source::EnvOverride] {
        assert_eq!(
            source.storage_location(&mut |_| None),
            None,
            "{source:?} is applied in memory and is never stored"
        );
    }
}

// ── metadata ──────────────────────────────────────────────────────────────

#[test]
fn the_default_metadata_is_the_api_metadata() {
    let api = Metadata::api();
    assert_eq!(Metadata::default(), api, "the default is the API metadata");
    assert_eq!(api.source, Source::Api);
    assert_eq!(api.level, 0);
    assert_eq!(api.path, None, "nothing was read from disk");
    assert_eq!(api.trust, gix_sec::Trust::Full, "the caller trusts its own input");
}

#[test]
fn metadata_from_a_source_keeps_the_source_and_trusts_it_fully() {
    for source in [Source::Local, Source::User, Source::Cli] {
        let meta = Metadata::from(source);
        assert_eq!(meta.source, source);
        assert_eq!(meta.path, None);
        assert_eq!(meta.level, 0);
        assert_eq!(meta.trust, gix_sec::Trust::Full);
    }
}

#[test]
fn the_metadata_builders_replace_only_what_they_name() {
    let meta = Metadata::api()
        .with(gix_sec::Trust::Reduced)
        .at("/somewhere/gitconfig");
    assert_eq!(meta.trust, gix_sec::Trust::Reduced);
    assert_eq!(
        meta.path.as_deref(),
        Some(std::path::Path::new("/somewhere/gitconfig"))
    );
    assert_eq!(meta.source, Source::Api, "neither builder touches the source");
    assert_eq!(meta.level, 0, "nor the include level");
}

// ── construction, identity and serialization of the whole document ───────

#[test]
fn a_default_file_is_empty_and_void() {
    let config = File::default();
    assert_eq!(config.num_values(), 0);
    assert!(config.is_void(), "a document with no section at all is void");
    assert_eq!(config.sections().count(), 0);
    assert_eq!(config.to_bstring(), "");
}

#[test]
fn the_file_handle_stays_compact() {
    let actual = std::mem::size_of::<File>();
    assert!(
        actual <= 1040,
        "{actual} <= 1040: the handle must not grow without us noticing"
    );
    let config = file("[core]\n\ta = b\n");
    assert_eq!(
        config.num_values(),
        1,
        "the bound is on the handle, not on the document it gives access to"
    );
}

#[test]
fn the_three_parsing_entry_points_agree() -> Result {
    let text = "[core]\n\ta = b\n";
    let from_str: File = text.parse()?;
    let from_try_from = File::try_from(text)?;
    let from_bytes = File::try_from(text.as_bytes().as_bstr())?;

    assert_eq!(from_str, from_try_from);
    assert_eq!(from_str, from_bytes);
    assert_eq!(from_str.to_string(), text, "and serialize back to the input");
    assert_eq!(BString::from(from_bytes), text);
    Ok(())
}

#[test]
fn a_parse_error_reports_a_one_based_line_number() {
    let error = File::try_from("[core]\n\tkey = value\n[unterminated\n")
        .expect_err("the third line never closes its header");
    assert_eq!(error.line_number(), 3, "line numbers are one-based");
    assert!(
        !error.remaining_data().is_empty(),
        "the unparsed remainder carries the cause"
    );
}

#[test]
fn a_lossy_document_keeps_its_values_and_drops_its_layout() -> Result {
    let input = "; leading comment\n[core]\n\ta = b ; trailing comment\n";
    let mut options = init::Options::default();
    options.lossy = true;

    let lossy = File::from_bytes_no_includes(input.as_bytes(), Metadata::api(), options)?;
    assert_eq!(lossy.string("core.a"), Some(bstring("b")), "values survive");
    assert_eq!(
        lossy.to_bstring(),
        "[core]\na=b\n",
        "comments and the original whitespace do not"
    );
    Ok(())
}

// ── key resolution ────────────────────────────────────────────────────────

#[test]
fn a_dotted_key_splits_at_the_first_and_the_last_separator() {
    let two = KeyRef::parse_unvalidated("core.bare".into()).expect("two tokens are enough");
    assert_eq!(two.section_name, "core");
    assert_eq!(two.subsection_name, None);
    assert_eq!(two.value_name, "bare");

    let three = KeyRef::parse_unvalidated("remote.origin.url".into()).expect("three tokens");
    assert_eq!(three.section_name, "remote");
    assert_eq!(three.subsection_name, Some("origin".into()));
    assert_eq!(three.value_name, "url");

    let dotted = KeyRef::parse_unvalidated("remote.https://example.com/a.b.url".into())
        .expect("a subsection may itself contain separators");
    assert_eq!(dotted.section_name, "remote");
    assert_eq!(
        dotted.subsection_name,
        Some("https://example.com/a.b".into()),
        "everything between the first and the last separator is the subsection"
    );
    assert_eq!(dotted.value_name, "url");
}

#[test]
fn a_key_without_a_separator_has_no_key_form() {
    assert_eq!(
        KeyRef::parse_unvalidated("nodot".into()),
        None,
        "a section name alone does not address a value"
    );
    assert!(AsKey::try_as_key(&"nodot").is_none());
    assert!(
        AsKey::try_as_key(&"core.bare").is_some(),
        "and the same call succeeds once a separator is present"
    );
}

#[test]
fn comfort_accessors_treat_an_unsplittable_key_as_absent() {
    let config = file("[core]\n\tnodot = value\n");
    assert_eq!(config.string("nodot"), None);
    assert_eq!(config.strings("nodot"), None);
    assert!(config.path("nodot").is_none());
    assert_eq!(config.boolean("nodot"), Ok(None));
    assert_eq!(config.integer("nodot"), Ok(None));
    assert_eq!(
        config.string("core.nodot"),
        Some(bstring("value")),
        "the value is reachable once the key names its section"
    );
}

#[test]
fn raw_accessors_panic_on_an_unsplittable_key() {
    let config = file("[core]\n\ta = b\n");
    assert_eq!(
        config.raw_value("core.a").expect("present"),
        "b",
        "a well-formed key resolves"
    );
    assert!(
        panics(|| {
            let _ = config.raw_value("nodot");
        }),
        "the raw layer demands a key it can split and panics when it cannot"
    );
}

// ── section lookup ────────────────────────────────────────────────────────

#[test]
fn legacy_and_quoted_headers_are_distinguished() -> Result {
    let config = File::try_from(
        "[remote.origin]\n\turl = https://example.com\n[remote \"upstream\"]\n\turl = https://example.com\n",
    )?;
    let sections: Vec<_> = config.sections().collect();

    assert!(sections[0].header().is_legacy(), "a dot separates the two names");
    assert!(!sections[1].header().is_legacy(), "a quoted subsection is not legacy");
    assert_eq!(sections[0].header().name(), "remote");
    assert_eq!(sections[0].header().subsection_name(), Some("origin".into()));
    assert_eq!(sections[0].header().to_bstring(), "[remote.origin]");
    assert_eq!(sections[1].header().to_bstring(), "[remote \"upstream\"]");
    Ok(())
}

#[test]
fn section_names_are_case_insensitive() -> Result {
    let config = File::try_from("[core] a=true")?;
    assert_eq!(
        config.value::<Boolean>("core.a")?,
        config.value::<Boolean>("CORE.a")?
    );
    assert!(config.section("CoRe", None).is_ok());
    Ok(())
}

#[test]
fn value_names_are_case_insensitive() -> Result {
    let config = File::try_from("[core]\n        a = true\n        A = false")?;
    assert_eq!(config.values::<Boolean>("core.a")?.len(), 2);
    assert_eq!(
        config.value::<Boolean>("core.a")?,
        config.value::<Boolean>("core.A")?
    );
    Ok(())
}

#[test]
fn section_value_access_is_case_insensitive() -> Result {
    let config = File::try_from("[core]\nMixedCase = one\nMIXEDCASE = two")?;
    let section = config.section("core", None)?;

    assert_eq!(section.values("mixedcase"), vec![bstring("one"), bstring("two")]);
    assert_eq!(
        section.value("mIxEdCaSe"),
        Some(bstring("two")),
        "the last declaration wins"
    );
    assert!(section.contains_value_name("mixedcase"));
    Ok(())
}

#[test]
fn subsection_names_are_matched_byte_exactly() -> Result {
    let config = File::try_from("[remote \"Origin\"] url = upper\n[remote \"origin\"] url = lower\n")?;
    assert_eq!(config.section("remote", Some("Origin".into()))?.value("url"), Some(bstring("upper")));
    assert_eq!(config.section("remote", Some("origin".into()))?.value("url"), Some(bstring("lower")));
    assert!(
        matches!(
            config.section("remote", Some("ORIGIN".into())),
            Err(lookup::existing::Error::SubSectionMissing)
        ),
        "a subsection name differing only in case is a different subsection"
    );
    Ok(())
}

#[test]
fn sections_by_name_ignores_subsections_and_preserves_file_order() -> Result {
    let config = File::try_from(
        "[remote] marker=plain\n\
         [other] marker=unrelated\n\
         [REMOTE \"origin\"] marker=origin\n\
         [remote \"upstream\"] marker=upstream\n\
         [remote] marker=last\n",
    )?;

    let markers: Vec<_> = config
        .sections_by_name("Remote")
        .expect("remote sections exist case-insensitively")
        .map(|section| section.value("marker").expect("each matching section has a marker"))
        .collect();
    assert_eq!(
        markers,
        [
            bstring("plain"),
            bstring("origin"),
            bstring("upstream"),
            bstring("last")
        ],
        "plain and subsection sections are returned in file order"
    );
    assert!(
        config.sections_by_name("missing").is_none(),
        "an unknown name yields no iterator at all"
    );
    Ok(())
}

#[test]
fn a_missing_section_subsection_and_value_are_distinguished() -> Result {
    let config = File::try_from("[core]\na=b\nc=d")?;
    assert!(matches!(
        config.raw_value("foo.a"),
        Err(lookup::existing::Error::SectionMissing)
    ));
    assert!(matches!(
        config.raw_value("core.a.a"),
        Err(lookup::existing::Error::SubSectionMissing)
    ));
    assert!(matches!(
        config.raw_value("core.aaaaaa"),
        Err(lookup::existing::Error::KeyMissing)
    ));
    assert!(matches!(
        File::default().section("missing", None),
        Err(lookup::existing::Error::SectionMissing)
    ));
    Ok(())
}

#[test]
fn values_outside_any_section_are_unreachable() -> Result {
    let config = File::try_from("a=b\n[core]\na=c")?;
    assert!(
        matches!(
            config.raw_value_by("", None, "a"),
            Err(lookup::existing::Error::SectionMissing)
        ),
        "the empty section name addresses nothing"
    );
    assert_eq!(
        config.raw_value("core.a")?,
        "c",
        "only values inside a section are readable"
    );
    Ok(())
}

#[test]
fn the_last_declaration_wins_within_and_across_sections() -> Result {
    assert_eq!(File::try_from("[core]\na=b\na=d")?.raw_value("core.a")?, "d");
    assert_eq!(File::try_from("[core]\na=b\n[core]\na=d")?.raw_value("core.a")?, "d");
    Ok(())
}

#[test]
fn a_subsection_is_a_different_key_than_its_section() -> Result {
    let config = File::try_from("[core]a=b\n[core.a]a=c")?;
    assert_eq!(config.raw_value("core.a")?, "b");
    assert_eq!(config.raw_value("core.a.a")?, "c");
    assert_eq!(config.raw_values("core.a")?, vec![bstring("b")]);
    assert_eq!(config.raw_values("core.a.a")?, vec![bstring("c")]);
    Ok(())
}

#[test]
fn every_declaration_of_a_multivar_is_returned_in_file_order() -> Result {
    let config = File::try_from("[core]\na=b\na=c\n[core]a=d\n[core]g=g")?;
    assert_eq!(
        config.raw_values("core.a")?,
        vec![bstring("b"), bstring("c"), bstring("d")],
        "a section that does not declare the value contributes nothing"
    );
    let single = File::try_from("[core]\na=b\nc=d")?;
    assert_eq!(
        vec![single.raw_value("core.a")?],
        single.raw_values("core.a")?,
        "a single declaration reads the same through both queries"
    );
    Ok(())
}

#[test]
fn an_implicit_declaration_is_skipped_when_resolving_a_raw_value() -> Result {
    let config = File::try_from("[core]\na=first\n[core]\na\n")?;
    let first_section = config.sections().next().expect("first section").id();

    let (value, section) = config.raw_value_with_section("core.a")?;
    assert_eq!(value, "first", "the later implicit declaration carries no value");
    assert_eq!(section.id(), first_section, "the reported section owns the value");

    let (value, section) = config.raw_value_with_section_by("core", None, "a")?;
    assert_eq!(value, "first");
    assert_eq!(section.id(), first_section);
    Ok(())
}

#[test]
fn invalid_value_names_are_reported_by_mutable_lookups() -> Result {
    let mut config = File::try_from("[core]\na=b")?;
    assert!(matches!(
        config.raw_value_mut_by("core", None, "1invalid"),
        Err(lookup::existing::Error::ValueName(_))
    ));
    assert!(matches!(
        config.raw_values_mut_by("core", None, "contains.dot"),
        Err(lookup::existing::Error::ValueName(_))
    ));
    assert!(
        config.raw_value_mut_by("core", None, "a").is_ok(),
        "a well-formed name still resolves"
    );
    Ok(())
}

#[test]
fn a_section_id_is_never_the_default_one() -> Result {
    let mut config = File::try_from("[core]\n\ta = b\n")?;
    let id = config.sections_and_ids().next().expect("one section").1;
    assert_ne!(id, SectionId::default(), "a real section never carries the default id");
    assert!(
        config.section_mut_by_id(SectionId::default()).is_none(),
        "and the default id addresses nothing"
    );
    assert!(config.section_mut_by_id(id).is_some());
    Ok(())
}

#[test]
fn a_section_body_iterates_its_declarations_in_order() -> Result {
    let config = File::try_from("[core]\n\ta = 1\n\tb = 2\n\ta = 3\n")?;
    let section = config.section("core", None)?;
    let body = section.body();

    let pairs: Vec<(String, BString)> = body.into_iter().collect();
    assert_eq!(
        pairs,
        vec![
            ("a".to_string(), bstring("1")),
            ("b".to_string(), bstring("2")),
            ("a".to_string(), bstring("3")),
        ]
    );
    assert_eq!(body.num_values(), 3);
    assert!(!body.is_void());
    assert_eq!(body.values("a"), vec![bstring("1"), bstring("3")]);
    assert_eq!(body.value("a"), Some(bstring("3")), "the last declaration wins");
    assert_eq!(body.value_implicit("a"), Some(Some(bstring("3"))));
    assert!(body.contains_value_name("A"), "value names are case-insensitive");
    assert_eq!(
        body.value_names().collect::<Vec<_>>(),
        ["a", "b", "a"],
        "every declaration is named, repeats included"
    );
    Ok(())
}

#[test]
fn an_implicit_declaration_is_distinguishable_from_an_empty_one() -> Result {
    let config = File::try_from("[core]\n\timplicit\n\texplicit =\n")?;
    let section = config.section("core", None)?;
    assert_eq!(
        section.value_implicit("implicit"),
        Some(None),
        "present, but with no value of its own"
    );
    assert_eq!(
        section.value_implicit("explicit"),
        Some(Some(bstring(""))),
        "present, with an empty value"
    );
    assert_eq!(
        section.value_implicit("absent"),
        None,
        "not present at all"
    );
    Ok(())
}

// ── typed and comfort access ──────────────────────────────────────────────

#[test]
fn an_implicit_entry_is_true_as_a_boolean_and_absent_as_a_string() -> Result {
    for input in [
        "[a]\n\tb \n",
        "[a]\n\tb\t\n",
        "[a]\n\tb  \n",
        "[a]\n\tb \t \n",
        "[a]\n\tb ",
        "[a]\n\tb \r\n",
        "[a]\n\tb\n",
    ] {
        let config = File::try_from(input)?;
        assert_eq!(
            config.boolean("a.b"),
            Ok(Some(true)),
            "there is no separator in {input:?}, so the entry is an implicit boolean"
        );
        assert_eq!(
            config.string("a.b"),
            None,
            "an implicit entry has no value of its own, whatever whitespace follows it"
        );
        assert_eq!(
            config.strings("a.b").expect("present"),
            vec![bstring("")],
            "but it does occupy a slot in the multivar"
        );
    }
    Ok(())
}

#[test]
fn a_separator_makes_a_value_explicitly_empty() -> Result {
    for input in ["[a]\n\tb =\n", "[a]\n\tb = \n", "[a]\n\tb=\"\"\n", "[a]\n\tb ="] {
        let config = File::try_from(input)?;
        assert_eq!(
            config.boolean("a.b"),
            Ok(Some(false)),
            "the separator in {input:?} makes the value explicitly empty, and empty is false"
        );
        assert_eq!(
            config.string("a.b"),
            Some(bstring("")),
            "an explicitly empty value is the empty string"
        );
    }
    Ok(())
}

#[test]
fn an_implicit_declaration_overrides_an_earlier_value_in_the_same_section() -> Result {
    let config = File::try_from("[a]\n\tb = false\n\tb\n")?;
    assert_eq!(
        config.boolean("a.b"),
        Ok(Some(true)),
        "the later implicit declaration is the one that counts"
    );
    Ok(())
}

#[test]
fn an_implicit_declaration_overrides_an_earlier_value_across_sections() -> Result {
    let config = File::try_from("[a]\n\tb = false\n[a]\n\tb\n")?;
    assert_eq!(config.boolean("a.b"), Ok(Some(true)));
    Ok(())
}

#[test]
fn an_implicit_entry_has_no_typed_value() -> Result {
    let config = File::try_from("[core]\n\tbool-implicit\n\tbool-explicit = false\n")?;
    assert!(
        matches!(
            config.value::<Boolean>("core.bool-implicit"),
            Err(lookup::Error::ValueMissing(lookup::existing::Error::KeyMissing))
        ),
        "the typed layer has no text to convert, unlike the boolean comfort accessor"
    );
    assert!(
        !config.value::<Boolean>("core.bool-explicit")?.0,
        "an explicit value converts normally"
    );
    assert!(
        config.boolean("core.bool-implicit")?.expect("present"),
        "while the boolean accessor answers from the entry's mere presence"
    );
    Ok(())
}

#[test]
fn a_boolean_lookup_resolves_the_last_declaration_across_sections() -> Result {
    let config = File::try_from(
        "[core]\n\
         bool-explicit = false\n\
         bool-implicit = false\n\
         [core]\n\
         bool-implicit\n",
    )?;
    assert!(
        !config.value::<Boolean>("core.bool-implicit")?.0,
        "the typed layer skips the implicit entry and finds the earlier false"
    );
    assert!(
        config.boolean("core.bool-implicit")?.expect("present"),
        "the comfort accessor sees the implicit entry and reports true"
    );
    assert!(!config.value::<Boolean>("core.bool-explicit")?.0);
    Ok(())
}

#[test]
fn integers_expose_their_suffix_and_their_decimal_value() -> Result {
    let config = File::try_from("[core]\n\tno-prefix = 10\n\tprefix = 10g\n")?;
    assert_eq!(
        config.value::<Integer>("core.no-prefix")?,
        Integer {
            value: 10,
            suffix: None
        }
    );
    assert_eq!(
        config.value::<Integer>("core.prefix")?,
        Integer {
            value: 10,
            suffix: Some(integer::Suffix::Gibi)
        }
    );
    assert_eq!(config.integer("core.no-prefix")?, Some(10));
    assert_eq!(
        config.integer("core.prefix")?,
        Some(10 * 1024 * 1024 * 1024),
        "the comfort accessor applies the suffix"
    );
    Ok(())
}

#[test]
fn a_color_is_read_across_a_continued_line() -> Result {
    let config = File::try_from("[core]\n\tcolor = brightgreen red \\\n\tbold\n")?;
    assert_eq!(
        config.value::<Color>("core.color")?,
        Color {
            foreground: Some(color::Name::BrightGreen),
            background: Some(color::Name::Red),
            attributes: color::Attribute::BOLD
        }
    );
    Ok(())
}

#[test]
fn a_path_is_returned_without_interpolation() -> Result {
    let config = File::try_from("[core]\n\tlocation = ~/tmp\n\tquoted = \"~/quoted\"\n")?;
    assert_eq!(
        &*config.value::<gix_config::Path>("core.location")?,
        "~/tmp",
        "no interpolation occurs when querying a path"
    );
    assert_eq!(&*config.path("core.location").expect("present"), "~/tmp");
    assert_eq!(
        &*config.path("core.quoted").expect("present"),
        "~/quoted",
        "but the surrounding quotes are removed"
    );
    Ok(())
}

#[test]
fn an_empty_value_is_a_string_and_a_path_but_a_missing_one_is_neither() -> Result {
    let config = File::try_from(
        "[core]\n\
         \tempty-implicit\n\
         \tempty-equals = \n\
         \tempty-explicit = \"\"\n",
    )?;
    assert_eq!(config.string("core.empty-implicit"), None, "presence is at most a boolean");
    assert!(config.path("core.empty-implicit").is_none());
    assert_eq!(config.string("core.empty-equals"), Some(bstring("")));
    assert!(config.path("core.empty-equals").is_some(), "this is an empty path");
    assert_eq!(config.string("core.empty-explicit"), Some(bstring("")));
    assert!(config.path("core.empty-explicit").is_some());
    assert_eq!(config.string("doesn't.exist"), None);
    Ok(())
}

#[test]
fn quoted_and_unquoted_declarations_of_one_name_form_a_single_multivar() -> Result {
    let config = File::try_from(
        "[core]\n\tother-quoted = \"hello\"\n[core]\n\tother-quoted = \"hello world\"\n",
    )?;
    assert_eq!(
        config.string("core.other-quoted").expect("present"),
        bstring("hello world"),
        "the last declaration wins and its quotes are removed"
    );
    assert_eq!(
        config.strings("core.other-quoted").expect("present"),
        vec![bstring("hello"), bstring("hello world")],
        "both declarations are visible in file order"
    );
    Ok(())
}

#[test]
fn a_value_reads_as_the_byte_string_it_denotes() -> Result {
    let config = File::try_from("[core]\n\tother = hello world\n")?;
    assert_eq!(config.value::<BString>("core.other")?, bstring("hello world"));
    assert_eq!(config.string("core.other").expect("present"), "hello world");
    Ok(())
}

#[test]
fn normalize_strips_quotes_and_resolves_escapes() {
    assert_eq!(&*normalize("hello \"world\""), "hello world");
    assert_eq!(&*normalize(r#"hello "world\"""#), r#"hello world""#);
    assert_eq!(&*normalize("\"\""), "", "a pair of quotes denotes the empty value");
    assert_eq!(&*normalize("plain"), "plain", "an unquoted value is unchanged");
    assert_eq!(&*normalize(r"a\nb\tc"), "a\nb\tc");
}

#[test]
fn escape_sequences_inside_a_quoted_value_are_resolved() -> Result {
    let config = File::try_from("[core]\n\tescape-sequence = \"hi\\nho\\n\\tthere\\bi\\\\\\\" \\\"\"\n")?;
    let expected = "hi\nho\n\tthere\x08i\\\" \"";
    assert_eq!(
        config.raw_value("core.escape-sequence")?,
        expected,
        "the raw layer already normalizes; `\\b` is the backspace byte"
    );
    assert_eq!(
        config.string("core.escape-sequence").expect("present"),
        expected,
        "and so does the comfort layer"
    );
    Ok(())
}

#[test]
fn a_continued_value_is_joined_into_one_line() -> Result {
    let config = File::try_from(
        "\n[alias]\n   save = !git status \\\n        && git add -A \\\n        && git commit -m \\\"$1\\\" \\\n        && git push -f \\\n        && git log -1 \\\n        && :            # comment\n    ",
    )?;
    let expected = r#"!git status         && git add -A         && git commit -m "$1"         && git push -f         && git log -1         && :"#;
    assert_eq!(config.raw_value("alias.save")?, expected);
    assert_eq!(config.string("alias.save").expect("present"), expected);
    Ok(())
}

#[test]
fn an_empty_continuation_line_ends_the_value() -> Result {
    for input in [
        "[core]\n\tk = abc\\\n\n",
        "[core]\n\tk = abc\\\n; comment\n",
        "[core]\n\tk = abc\\\n",
        "[core]\n\tk = abc\\",
        "[core]\n\tk = abc\\\n\n[other]\n",
        "[core]\r\n\tk = abc\\\r\n",
    ] {
        let config = File::try_from(input)?;
        assert_eq!(
            config.raw_values("core.k")?,
            vec![bstring("abc")],
            "a continuation line that is empty ends the value, for {input:?}"
        );
    }

    let config = File::try_from("[core]\n\tk = abc\\\n\tk = def\n")?;
    assert_eq!(
        config.raw_value("core.k")?,
        bstring("abc\tk = def"),
        "whereas a non-empty next line continues the first value"
    );
    Ok(())
}

#[test]
fn unescaped_inner_quotes_are_dropped_from_a_continued_value() -> Result {
    let config = File::try_from(
        "\n[alias]\n   save = \"!f() { \\\n           git status; \\\n           git add -A; \\\n           git commit -m \"$1\"; \\\n           git push -f; \\\n           git log -1;  \\\n        }; \\\n        f;  \\\n        unset f\"\n",
    )?;
    let expected = r#"!f() {            git status;            git add -A;            git commit -m $1;            git push -f;            git log -1;          };         f;          unset f"#;
    assert_eq!(config.raw_value("alias.save")?, expected);
    Ok(())
}

#[test]
fn escaped_inner_quotes_stay_in_a_continued_value() -> Result {
    let config = File::try_from(
        "\n[alias]\n   save = \"!f() { \\\n           git status; \\\n           git add -A; \\\n           git commit -m \\\"$1\\\"; \\\n           git push -f; \\\n           git log -1;  \\\n        }; \\\n        f;  \\\n        unset f\"\n",
    )?;
    let expected = r#"!f() {            git status;            git add -A;            git commit -m "$1";            git push -f;            git log -1;          };         f;          unset f"#;
    assert_eq!(config.raw_value("alias.save")?, expected);
    Ok(())
}

#[test]
fn a_value_read_through_a_mutable_view_is_normalized() -> Result {
    for (input, expected) in [
        ("[a] k", ""),
        ("[a] k = hello there ; comment", "hello there"),
        ("[a] k = \" hello\tthere \"; comment", " hello\tthere "),
        ("[a] k = a\\\n  b\\\n  c ; comment", "a  b  c"),
    ] {
        let mut config = File::try_from(input)?;
        assert_eq!(
            config.raw_value_mut_by("a", None, "k")?.get()?,
            expected,
            "{input:?} normalizes to {expected:?}"
        );
    }

    let mut config = File::try_from("[core]\nMixedCase = value")?;
    assert_eq!(
        config.raw_value_mut_by("core", None, "mIxEdCaSe")?.get()?,
        "value",
        "the mutable lookup is case-insensitive too"
    );
    Ok(())
}

// ── section mutation ──────────────────────────────────────────────────────

#[test]
fn a_new_section_is_appended_with_its_own_header() -> Result {
    let mut config = File::default();
    config.new_section("remote", "origin")?;
    config.new_section("branch", "main")?;

    let nl = newline();
    assert_eq!(
        config.to_string(),
        format!("[remote \"origin\"]{nl}[branch \"main\"]{nl}"),
        "a borrowed subsection name is owned by its new section"
    );
    Ok(())
}

#[test]
fn a_new_section_validates_its_name_and_subsection() -> Result {
    let mut config = File::default();
    assert!(matches!(
        config.new_section("not_valid", None),
        Err(section::header::Error::InvalidName)
    ));
    assert!(matches!(
        config.new_section("valid", "a\nb"),
        Err(section::header::Error::InvalidSubSection)
    ));
    assert!(
        !gix_config::parse::section::header::is_valid_subsection("a\nb"),
        "and the predicate agrees about the subsection"
    );
    assert!(gix_config::parse::section::header::is_valid_subsection("a b"));
    assert_eq!(
        config.to_bstring(),
        "",
        "a rejected name creates nothing"
    );
    Ok(())
}

#[test]
fn a_detached_section_can_be_created_and_renamed() -> Result {
    let mut section = Section::new("remote", "origin", Metadata::default())?;
    assert_eq!(section.to_ref().header().name(), "remote");
    assert_eq!(section.to_ref().header().subsection_name(), Some("origin".into()));

    section.to_mut().rename("branch", "main")?;
    assert_eq!(section.to_ref().header().name(), "branch");
    assert_eq!(section.to_ref().header().subsection_name(), Some("main".into()));
    Ok(())
}

#[test]
fn section_mut_does_not_create_a_missing_section() -> Result {
    let mut config = multi_value_section();
    assert!(matches!(
        config.section_mut("foo", None),
        Err(lookup::existing::Error::SectionMissing)
    ));
    assert!(
        config.section_mut("a", None).is_ok(),
        "an existing section is returned"
    );
    Ok(())
}

#[test]
fn section_mut_or_create_new_always_yields_a_section() -> Result {
    let mut config = multi_value_section();
    let section = config.section_mut_or_create_new("name", "subsection")?;
    assert_eq!(section.header().name(), "name");
    assert_eq!(section.header().subsection_name().expect("set"), "subsection");
    Ok(())
}

#[test]
fn a_rejecting_filter_makes_section_mut_or_create_new_add_a_section() -> Result {
    let mut config = multi_value_section();
    let section = config.section_mut_or_create_new_filter("a", None, |_| false)?;
    assert_eq!(section.header().name(), "a");
    assert_eq!(section.header().subsection_name(), None);
    assert_eq!(section.to_bstring(), "[a]\n", "the new section is empty");
    assert_eq!(
        section.meta(),
        &Metadata::api(),
        "a section created through the API carries the API metadata"
    );
    Ok(())
}

#[test]
fn a_section_can_be_addressed_by_its_id() -> Result {
    let mut config = multi_value_section();
    let id = config.sections_and_ids().next().expect("at least one").1;
    let section = config.section_mut_by_id(id).expect("present");
    assert_eq!(section.header().name(), "a");
    assert_eq!(section.header().subsection_name(), None);
    Ok(())
}

#[test]
fn pushing_no_value_omits_the_separator() -> Result {
    let mut config = File::default();
    let mut section = config.section_mut_or_create_new("a", "sub")?;
    section.push("key", None)?;
    let expected = format!("[a \"sub\"]{nl}\tkey{nl}", nl = section.newline());

    assert_eq!(section.value("key"), None, "a single read sees no value");
    assert_eq!(
        section.values("key"),
        vec![bstring("")],
        "a multivar read sees an empty one"
    );
    assert_eq!(config.to_bstring(), expected);
    Ok(())
}

#[test]
fn a_pushed_value_is_quoted_only_when_it_has_to_be() -> Result {
    for (value, expected) in [
        ("a b", "$head\tk = a b$nl"),
        (" a b", "$head\tk = \" a b\"$nl"),
        ("a b\t", "$head\tk = \"a b\\t\"$nl"),
        (";c", "$head\tk = \";c\"$nl"),
        ("#c", "$head\tk = \"#c\"$nl"),
        ("a\nb\n\tc", "$head\tk = a\\nb\\n\\tc$nl"),
    ] {
        let mut config = File::default();
        let mut section = config.new_section("a", None)?;
        section.set_implicit_newline(false);
        section.push("k", Some(value.into()))?;
        let expected = expected
            .replace("$head", &format!("[a]{nl}", nl = section.newline()))
            .replace("$nl", &section.newline().to_string());
        assert_eq!(config.to_bstring(), expected, "for {value:?}");
    }
    Ok(())
}

#[test]
fn a_pushed_comment_is_folded_onto_one_line() -> Result {
    for (comment, expected) in [
        ("", "$head\tk = v #$nl"),
        ("this is v!", "$head\tk = v # this is v!$nl"),
        (" no double space", "$head\tk = v # no double space$nl"),
        ("\tno double whitespace", "$head\tk = v #\tno double whitespace$nl"),
        (
            "one\ntwo\nnewlines are replaced with space",
            "$head\tk = v # one two newlines are replaced with space$nl",
        ),
        (
            "a\rb\r\nlinefeeds aren't special",
            "$head\tk = v # a\rb\r linefeeds aren't special$nl",
        ),
    ] {
        let mut config = File::default();
        let mut section = config.new_section("a", None)?;
        section.set_implicit_newline(false);
        section.push_with_comment("k", Some("v".into()), comment)?;
        let expected = expected
            .replace("$head", &format!("[a]{nl}", nl = section.newline()))
            .replace("$nl", &section.newline().to_string());
        assert_eq!(config.to_bstring(), expected, "for {comment:?}");
    }
    Ok(())
}

#[test]
fn a_mutation_validates_the_value_name_before_changing_anything() -> Result {
    let mut config = File::default();
    let mut section = config.new_section("core", None)?;

    assert!(matches!(
        section.push("not.valid", Some("value".into())),
        Err(gix_config::file::section::value::Error::ValueName(_))
    ));
    assert!(matches!(
        section.push_with_comment("1invalid", Some("value".into()), "comment"),
        Err(gix_config::file::section::value::Error::ValueName(_))
    ));
    assert!(matches!(
        section.set("also invalid", "value"),
        Err(gix_config::file::section::value::Error::ValueName(_))
    ));
    assert_eq!(section.num_values(), 0, "validation happens before mutation");
    Ok(())
}

#[test]
fn value_names_are_handed_out_as_strings() -> Result {
    let mut config = multi_value_section();
    let mut section = config.section_mut("a", None)?;
    let names: Vec<String> = section.value_names().collect();
    assert_eq!(names, ["a", "b", "c", "d", "e"]);

    let (name, value) = section.pop().expect("at least one value");
    let name: String = name;
    assert_eq!(name, "e");
    assert_eq!(value, "a        b        c", "and the value comes back normalized");
    Ok(())
}

#[test]
fn leading_and_separator_whitespace_are_derived_from_the_first_value() -> Result {
    for (input, expected_pre_key, expected_sep) in [
        ("[a]\n\t\tb=c", Some("\t\t"), (None, None)),
        ("[a]\nb= c", None, (None, Some(" "))),
        ("[a]", Some("\t"), (Some(" "), Some(" "))),
        ("[a] b", Some(" "), (None, None)),
        ("[a]\tb = ", Some("\t"), (Some(" "), Some(" "))),
        ("[a]\t\tb =c", Some("\t\t"), (Some(" "), None)),
        (
            "[a]\n\t\t  \n    \t    b =  c",
            Some("    \t    "),
            (Some(" "), Some("  ")),
        ),
    ] {
        let mut config = File::try_from(input)?;
        let section = config.section_mut("a", None)?;
        assert_eq!(
            section.leading_whitespace(),
            expected_pre_key.map(Into::into),
            "{input:?} should find {expected_pre_key:?} before the first value name"
        );
        let (pre_sep, post_sep) = expected_sep;
        assert_eq!(
            section.separator_whitespace(),
            (pre_sep.map(Into::into), post_sep.map(Into::into)),
            "{input:?} should find {expected_sep:?} around the separator"
        );
    }
    Ok(())
}

#[test]
fn any_whitespace_may_be_set_as_a_sections_leading_whitespace() -> Result {
    let mut config = File::default();
    let mut section = config.new_section("core", None)?;

    let nl = section.newline().to_owned();
    section.set_leading_whitespace(format!("{nl}\t"));
    section.push("a", Some("v".into()))?;

    assert_eq!(config.to_string(), format!("[core]{nl}{nl}\ta = v{nl}"));
    Ok(())
}

#[test]
fn setting_non_whitespace_as_leading_whitespace_panics() -> Result {
    let mut config = File::default();
    let mut section = config.new_section("core", None)?;
    assert_eq!(
        section.leading_whitespace(),
        Some("\t").map(Into::into),
        "a section with no values yet indents the first one with a tab"
    );
    assert!(
        panics(|| {
            section.set_leading_whitespace("foo");
        }),
        "the contract is a panic, not an error return"
    );
    Ok(())
}

#[test]
fn a_multivar_view_reports_how_many_declarations_it_covers() -> Result {
    let mut config = common::multi_value_config();
    assert_eq!(config.raw_values_mut_by("core", None, "a")?.len(), 3);
    assert!(!config.raw_values_mut_by("core", None, "a")?.is_empty());
    assert_eq!(
        config.raw_values_mut_by("core", None, "a")?.get()?,
        vec![bstring("b100"), bstring("d"), bstring("f")]
    );
    Ok(())
}

#[test]
fn renaming_a_section_validates_the_new_name() -> Result {
    let mut config = File::try_from("[core] a = b")?;
    let before = config.to_string();
    assert!(matches!(
        config.rename_section("core", None, "new_core", None),
        Err(gix_config::file::rename_section::Error::Section(
            section::header::Error::InvalidName
        ))
    ));
    assert!(matches!(
        config.rename_section("core", None, "new-core", "a\nb"),
        Err(gix_config::file::rename_section::Error::Section(
            section::header::Error::InvalidSubSection
        ))
    ));
    assert_eq!(
        config.to_string(),
        before,
        "a rejected rename leaves the document untouched"
    );
    Ok(())
}

#[test]
fn renaming_an_emptied_lookup_bucket_reports_a_missing_section() -> Result {
    let mut config = File::try_from("[core] key = value\n")?;
    config.remove_section("core", None).expect("section exists");
    assert!(matches!(
        config.rename_section("core", None, "other", None),
        Err(gix_config::file::rename_section::Error::Lookup(
            lookup::existing::Error::SectionMissing
        ))
    ));
    Ok(())
}

#[test]
fn an_invalid_value_name_fails_without_creating_a_section() -> Result {
    let mut config = File::default();
    assert!(matches!(
        config.set_raw_value_by("new", None, "not.valid", "value"),
        Err(gix_config::file::set_raw_value::Error::ValueName(_))
    ));
    assert_eq!(
        config.sections().count(),
        0,
        "validation precedes section creation"
    );
    assert!(config.is_void());
    Ok(())
}

#[test]
fn set_existing_raw_value_never_creates_anything() -> Result {
    let mut config = File::default();
    assert!(
        config.set_existing_raw_value_by("new", None, "key", "value").is_err(),
        "new values are never created by the existing-value setter"
    );
    assert!(config.is_void(), "and nothing was added on the way out");

    let mut config = File::try_from("a=b\n[core]\na=c")?;
    assert!(
        matches!(
            config.set_existing_raw_value_by("", None, "a", "d"),
            Err(gix_config::file::set_raw_value::Error::Lookup(
                lookup::existing::Error::SectionMissing
            ))
        ),
        "and a value outside any section cannot be set either"
    );
    Ok(())
}

#[test]
fn a_short_lived_key_may_address_a_value() -> Result {
    let mut config = File::default();
    let key = String::from("new.key");
    config.set_raw_value(key.as_str(), "value")?;
    drop(key);
    assert_eq!(config.string("new.key").expect("present"), "value");
    Ok(())
}

#[test]
fn a_typed_value_can_be_returned_with_the_section_it_came_from() -> Result {
    let config = File::try_from("[core]\na=1\na=2\n[core]\na=3\n")?;
    let ids: Vec<_> = config.sections().map(|section| section.id()).collect();

    let (value, section) = config.value_with_section::<Integer>("core.a")?;
    assert_eq!(value.value, 3, "the last declaration wins");
    assert_eq!(section.id(), ids[1], "and it lives in the second section");

    let paired: Vec<_> = config
        .values_with_sections::<Integer>("core.a")?
        .into_iter()
        .map(|(value, section)| (value.value, section.id()))
        .collect();
    assert_eq!(paired, [(1, ids[0]), (2, ids[0]), (3, ids[1])]);

    let (value, section) = config.value_with_section_by::<Integer>("core", None, "a")?;
    assert_eq!((value.value, section.id()), (3, ids[1]));
    assert_eq!(
        config.values_with_sections_by::<Integer>("core", None, "a")?.len(),
        3,
        "the explicit-component spelling has the same semantics"
    );
    Ok(())
}

#[test]
fn a_newly_created_document_reports_the_platform_newline() {
    let config = File::default();
    let nl = config.detect_newline_style();
    assert!(
        nl == "\n" || nl == "\r\n",
        "{nl:?} is one of the two newline styles"
    );
    assert_eq!(
        nl,
        newline().as_str(),
        "and it is stable across handles"
    );
}

#[test]
fn a_documents_newline_style_is_the_first_one_it_contains() -> Result {
    assert_eq!(File::try_from("[a]\nx=1\n")?.detect_newline_style(), "\n");
    assert_eq!(File::try_from("[a]\r\nx=1\r\n")?.detect_newline_style(), "\r\n");
    assert_eq!(
        File::try_from("; root\r\n[core]\nkey=value\n")?.detect_newline_style(),
        "\r\n",
        "the first complete newline counts even when it follows a comment"
    );
    Ok(())
}
