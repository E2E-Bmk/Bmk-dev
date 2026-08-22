// Rewritten upstream tests: serde_spanned::Spanned through toml::de.
// Source: repo-pool/toml-fullrepro-001 crates/toml/tests/serde/spanned.rs
// Rewrites: snapbox/to_debug asserts -> assert_eq on ranges and byte slices
// (byte-span contract is spec-pinned); serde_untagged custom Deserialize replaced
// with a plain serde visitor (serde_untagged is not a permitted dependency);
// `foo_outer.span() == 0..0` (document-level span shape) dropped as undocumented;
// deny_unknown_fields exact error text relaxed to error-type check.

mod toml_serde_spanned {

use std::collections::BTreeMap;
use std::fmt::Debug;

use serde::Deserialize;
use serde::de::{Deserializer, MapAccess};

use toml::Spanned;

#[test]
fn spanned_test_spanned_field() {
    #[derive(Deserialize, Debug)]
    struct Foo<T> {
        foo: Spanned<T>,
    }

    #[derive(Deserialize, Debug)]
    struct BareFoo<T> {
        foo: T,
    }

    #[track_caller]
    fn good<T>(input: &str, expected: &str, span: std::ops::Range<usize>)
    where
        T: serde::de::DeserializeOwned + Debug + PartialEq,
    {
        let foo: Foo<T> = crate::from_str(input).unwrap();
        assert_eq!(&input[foo.foo.span()], expected);
        assert_eq!(foo.foo.span(), span);

        // Test for Spanned<> at the top level
        let foo_outer: Spanned<BareFoo<T>> = crate::from_str(input).unwrap();
        assert_eq!(&foo_outer.get_ref().foo, foo.foo.get_ref());
    }

    good::<String>("foo = \"foo\"", "\"foo\"", 6..11);
    good::<u32>("foo = 42", "42", 6..8);
    // leading plus
    good::<u32>("foo = +42", "+42", 6..9);
    // table
    good::<BTreeMap<String, u32>>(
        "foo = {\"foo\" = 42, \"bar\" = 42}",
        "{\"foo\" = 42, \"bar\" = 42}",
        6..30,
    );
    // array
    good::<Vec<u32>>("foo = [0, 1, 2, 3, 4]", "[0, 1, 2, 3, 4]", 6..21);
    // datetime
    good::<String>(
        "foo = \"1997-09-09T09:09:09Z\"",
        "\"1997-09-09T09:09:09Z\"",
        6..28,
    );

    let good_datetimes = [
        ("1997-09-09T09:09:09Z", "1997-09-09T09:09:09Z", 6..26),
        ("1997-09-09T09:09:09+09:09", "1997-09-09T09:09:09+09:09", 6..31),
        ("1997-09-09T09:09:09-09:09", "1997-09-09T09:09:09-09:09", 6..31),
        ("1997-09-09T09:09:09", "1997-09-09T09:09:09", 6..25),
        ("1997-09-09", "1997-09-09", 6..16),
        ("09:09:09", "09:09:09", 6..14),
        ("1997-09-09T09:09:09.09Z", "1997-09-09T09:09:09.09Z", 6..29),
        ("1997-09-09T09:09:09.09+09:09", "1997-09-09T09:09:09.09+09:09", 6..34),
        ("1997-09-09T09:09:09.09-09:09", "1997-09-09T09:09:09.09-09:09", 6..34),
        ("1997-09-09T09:09:09.09", "1997-09-09T09:09:09.09", 6..28),
        ("09:09:09.09", "09:09:09.09", 6..17),
    ];
    for (value, expected, span) in good_datetimes {
        let input = format!("foo = {value}");
        good::<crate::Datetime>(&input, expected, span);
    }
    // ending at something other than the absolute end
    good::<u32>("foo = 42\nnoise = true", "42", 6..8);
}

#[test]
fn spanned_test_inner_spanned_table() {
    #[derive(Deserialize, Debug)]
    struct Foo {
        foo: Spanned<BTreeMap<Spanned<String>, Spanned<String>>>,
    }

    #[track_caller]
    fn good(input: &str, zero: bool) {
        let foo: Foo = crate::from_str(input).unwrap();

        if zero {
            assert_eq!(foo.foo.span().start, 0, "invalid `foo.foo.span().start`");
            assert_eq!(foo.foo.span().end, 5, "invalid `foo.foo.span().end`");
        } else {
            assert_eq!(
                foo.foo.span().start,
                input.find('{').unwrap(),
                "invalid `foo.foo.span().start`"
            );
            assert_eq!(
                foo.foo.span().end,
                input.find('}').unwrap() + 1,
                "invalid `foo.foo.span().end`"
            );
        }
        for (k, v) in foo.foo.as_ref().iter() {
            assert_eq!(
                &input[k.span().start..k.span().end],
                k.as_ref(),
                "invalid key"
            );
            assert_eq!(
                &input[(v.span().start + 1)..(v.span().end - 1)],
                v.as_ref(),
                "invalid value"
            );
        }
    }

    good(
        "\
        [foo]
        a = 'b'
        bar = 'baz'
        c = 'd'
        e = \"f\"
    ",
        true,
    );

    good(
        "
        foo = { a = 'b', bar = 'baz', c = 'd', e = \"f\" }",
        false,
    );
}

#[test]
fn spanned_test_outer_spanned_table() {
    #[derive(Debug, Deserialize)]
    struct Foo {
        foo: BTreeMap<Spanned<String>, Spanned<String>>,
    }

    fn good(s: &str, foo: &Foo) {
        for (k, v) in foo.foo.iter() {
            assert_eq!(&s[k.span().start..k.span().end], k.as_ref());
            assert_eq!(&s[(v.span().start + 1)..(v.span().end - 1)], v.as_ref());
        }
    }

    let input = "
        [foo]
        a = 'b'
        bar = 'baz'
        c = 'd'
        e = \"f\"
    ";
    let foo: Foo = crate::from_str(input).unwrap();
    good(input, &foo);

    let input = "
        foo = { a = 'b', bar = 'baz', c = 'd', e = \"f\" }
    ";
    let foo: Foo = crate::from_str(input).unwrap();
    good(input, &foo);
}

#[test]
fn spanned_test_spanned_nested() {
    #[derive(Debug, Deserialize)]
    struct Foo {
        foo: BTreeMap<Spanned<String>, BTreeMap<Spanned<String>, Spanned<String>>>,
    }

    fn good(s: &str, foo: &Foo) {
        for (k, v) in foo.foo.iter() {
            assert_eq!(&s[k.span().start..k.span().end], k.as_ref());
            for (n_k, n_v) in v.iter() {
                assert_eq!(&s[n_k.span().start..n_k.span().end], n_k.as_ref());
                assert_eq!(
                    &s[(n_v.span().start + 1)..(n_v.span().end - 1)],
                    n_v.as_ref()
                );
            }
        }
    }

    let input = "
        [foo.a]
        a = 'b'
        c = 'd'
        e = \"f\"
        [foo.bar]
        baz = 'true'
    ";
    let foo: Foo = crate::from_str(input).unwrap();
    good(input, &foo);

    let input = "
        [foo]
        foo = { a = 'b', bar = 'baz', c = 'd', e = \"f\" }
        bazz = {}
        g = { h = 'i' }
    ";
    let foo: Foo = crate::from_str(input).unwrap();
    good(input, &foo);
}

#[test]
fn spanned_test_spanned_array() {
    #[derive(Debug, Deserialize)]
    struct Foo {
        foo: Vec<Spanned<BTreeMap<Spanned<String>, Spanned<String>>>>,
    }

    let toml = "\
        [[foo]]
        a = 'b'
        bar = 'baz'
        c = 'd'
        e = \"f\"
        [[foo]]
        a = 'c'
        bar = 'baz'
        c = 'g'
        e = \"h\"
    ";
    let foo_list: Foo = crate::from_str(toml).unwrap();

    for (foo, expected) in foo_list.foo.iter().zip([0..7, 84..91]) {
        assert_eq!(foo.span(), expected);
        for (k, v) in foo.as_ref().iter() {
            assert_eq!(&toml[k.span().start..k.span().end], k.as_ref());
            assert_eq!(&toml[(v.span().start + 1)..(v.span().end - 1)], v.as_ref());
        }
    }
}

#[test]
fn spanned_implicit_tables() {
    #[derive(Debug)]
    #[allow(dead_code)]
    enum SpannedValue {
        String(String),
        Map(Vec<(Spanned<String>, Spanned<Self>)>),
    }

    impl SpannedValue {
        fn get(&self, key: &str) -> Option<&(Spanned<String>, Spanned<Self>)> {
            let Self::Map(map) = self else {
                return None;
            };

            map.iter().find(|(k, _v)| k.get_ref() == key)
        }
    }

    impl<'de> Deserialize<'de> for SpannedValue {
        fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
        where
            D: Deserializer<'de>,
        {
            struct SpannedValueVisitor;

            impl<'de> serde::de::Visitor<'de> for SpannedValueVisitor {
                type Value = SpannedValue;

                fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                    formatter.write_str("a string or a map")
                }

                fn visit_str<E>(self, s: &str) -> Result<Self::Value, E>
                where
                    E: serde::de::Error,
                {
                    Ok(SpannedValue::String(s.into()))
                }

                fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
                where
                    A: MapAccess<'de>,
                {
                    let mut result = Vec::new();

                    while let Some((k, v)) = map.next_entry()? {
                        result.push((k, v));
                    }

                    Ok(SpannedValue::Map(result))
                }
            }

            deserializer.deserialize_any(SpannedValueVisitor)
        }
    }

    const INPUT: &str = r#"
[foo.bar]
alice.bob = { one.two = "qux" }
"#;

    let result = crate::from_str::<SpannedValue>(INPUT).unwrap();

    let foo = result.get("foo").unwrap();
    assert_eq!(&INPUT[foo.0.span()], "foo");
    assert_eq!(&INPUT[foo.1.span()], "foo");
    let bar = foo.1.get_ref().get("bar").unwrap();
    assert_eq!(&INPUT[bar.0.span()], "bar");
    assert_eq!(&INPUT[bar.1.span()], "[foo.bar]");
    let alice = bar.1.get_ref().get("alice").unwrap();
    assert_eq!(&INPUT[alice.0.span()], "alice");
    assert_eq!(&INPUT[alice.1.span()], "alice");
    let bob = alice.1.get_ref().get("bob").unwrap();
    assert_eq!(&INPUT[bob.0.span()], "bob");
    assert_eq!(&INPUT[bob.1.span()], "{ one.two = \"qux\" }");
    let one = bob.1.get_ref().get("one").unwrap();
    assert_eq!(&INPUT[one.0.span()], "one");
    assert_eq!(&INPUT[one.1.span()], "one");
    let two = one.1.get_ref().get("two").unwrap();
    assert_eq!(&INPUT[two.0.span()], "two");
    assert_eq!(&INPUT[two.1.span()], "\"qux\"");
}

#[test]
fn spanned_deny_unknown_fields() {
    #[derive(Debug, serde::Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Example {
        #[allow(dead_code)]
        real: u32,
    }

    let error = crate::from_str::<Example>(
        r#"# my comment
# bla bla bla
fake = 1"#,
    );
    assert!(error.is_err());
}

}
