//! Shared fixtures and helpers for the `gix-config` oracle suites.
//!
//! This crate declares no tests of its own, so `RustRunner.discover` -- which
//! reads the attribute out of the source of `oracle/atomic` and
//! `oracle/integration` only -- never counts anything here. It exists so both
//! suites hand the same `gix_config::File` values around: one crate instance
//! means one `File` type, and a duplicated helper crate would make the two
//! suites' fixtures mutually incompatible at the type level.
//!
//! Every fixture is an inline string literal. Nothing reads from the
//! filesystem, consults an environment variable, or shells out, so a failure
//! here is always attributable to the candidate rather than to the machine the
//! scorer happened to run on.

#![deny(unsafe_code)]

use bstr::BString;
use gix_config::File;

/// The byte string `s` denotes.
///
/// Configuration values are bytes, not text: a value may hold a NUL, a lone
/// `\xff`, or anything else a file can contain. Comparisons are written
/// against `BString` for that reason, and this is the shorthand that builds
/// one from a literal.
pub fn bstring(s: &str) -> BString {
    s.into()
}

/// Parse `input` as a configuration document, or panic.
///
/// Used where the fixture is a constant of the test rather than the thing
/// under test. A candidate that cannot parse the fixture fails the test
/// through this panic, which is the correct outcome: every one of those tests
/// asserts something about a parsed document.
pub fn file(input: &str) -> File {
    File::try_from(input).expect("fixture is valid configuration text")
}

/// The newline sequence a freshly created document inserts.
///
/// `\n` on unix and `\r\n` on windows. Tests that build a document from
/// nothing and then compare its serialization have to spell the platform's
/// newline somehow, and asking the implementation is the only way to do it
/// that does not hard-code a platform.
pub fn newline() -> String {
    File::default().detect_newline_style().to_string()
}

/// Whether calling `f` unwinds, with the panic message suppressed.
///
/// The specification states outright that two operations panic rather than
/// returning an error -- `AsKey::as_key` on a key with no separator, and
/// `SectionMut::set_leading_whitespace` on bytes that are not whitespace --
/// and a contract that says "this panics" is only checked by a test that
/// observes the unwind.
///
/// Written this way rather than with the `should_panic` attribute for a reason
/// that decides whether the oracle can measure anything at all. `should_panic`
/// passes on *any* panic anywhere in the test, so against a submission whose
/// every method body is `unimplemented!()` such a test passes -- not because
/// the panicking contract holds, but because nothing is implemented. It would
/// score a stub as correct. Confining the guard to the one call whose panic is
/// the contract, and doing every step of the setup outside it, keeps the
/// panics of an unimplemented submission uncaught, where they fail the test.
///
/// The hook is replaced for the duration so a deliberate unwind does not print
/// a backtrace into the report. That is process-global state, which is safe
/// here only because nextest runs each test in its own process.
pub fn panics(f: impl FnOnce()) -> bool {
    let previous = std::panic::take_hook();
    std::panic::set_hook(Box::new(|_| {}));
    let outcome = std::panic::catch_unwind(std::panic::AssertUnwindSafe(f));
    std::panic::set_hook(previous);
    outcome.is_err()
}

/// A section holding five value declarations of five different shapes.
///
/// Upstream calls this `multi_value_section`. The five entries are, in order:
/// an ordinary value, a value whose separator is followed by a space and
/// nothing else, a value whose separator is followed by nothing at all, an
/// implicit entry with no separator, and a value continued across three lines.
/// Together they cover every shape `SectionMut::set`, `remove` and `pop` have
/// to handle, which is why the same fixture serves all three.
///
/// Spelled as concatenated line literals rather than as one raw string on
/// purpose: the `b = ` line ends in a significant space. In a raw string that
/// space is invisible, and any editor or formatter that trims trailing
/// whitespace would silently change what `SectionMut::set` writes back --
/// `b = " a"` becomes `b ="a"` -- turning a fixture edit into a test failure
/// with no visible cause.
pub fn multi_value_section() -> File {
    file(concat!(
        "\n",
        "        [a]\n",
        "            a = v\n",
        "            b = \n",
        "            c=\n",
        "            d\n",
        "            e =a \\\n",
        "       b \\\n",
        "       c",
    ))
}

/// Two `core` sections, the first holding a quoted value, the second two plain
/// ones.
///
/// Upstream's `init_config` in the value-mutation tests. The interesting part
/// is `a=b"100"`: a value with quotes in the middle, so that a test which
/// rewrites or deletes it proves the implementation tracks the value's true
/// extent in the backing buffer rather than the extent of its normalized form.
pub fn value_config() -> File {
    file(
        r#"[core]
            a=b"100"
        [core]
            c=d
            e=f"#,
    )
}

/// Three declarations of the same multivar spread over two sections, each with
/// a different spelling of the separator whitespace.
///
/// Upstream's `init_config` in the multi-value tests. `a = b"100"`, `a =d` and
/// `a= f` differ in where the whitespace sits, so a test that rewrites one
/// declaration shows whether the surrounding layout survived.
pub fn multi_value_config() -> File {
    file(
        r#"[core]
    a = b"100"
    [core]
        a =d
        a= f"#,
    )
}
