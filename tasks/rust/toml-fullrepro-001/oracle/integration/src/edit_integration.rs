// Rewritten upstream tests: cross-document operations on toml_edit that need
// two parsed documents or reference semantics (integration layer).
// Source: repo-pool/toml-fullrepro-001 crates/toml_edit/tests/testsuite/edit.rs
// (test_inserting_tables_from_different_parsed_docs, sorting_with_references)
// Rewrites: produces_display -> assert_eq against the exact rendered document
// (snapbox Inline::trimmed semantics); sort_by on an Array of references kept
// verbatim (spec EDIT-001: array sorting by key text).

mod edit_integration {
    use toml_edit::{DocumentMut, Table};

    struct Test {
        doc: DocumentMut,
    }

    fn given(input: &str) -> Test {
        let doc = input.parse::<DocumentMut>();
        assert!(doc.is_ok());
        Test { doc: doc.unwrap() }
    }

    impl Test {
        fn running<F>(&mut self, func: F) -> &mut Self
        where
            F: Fn(&mut Table),
        {
            {
                let root = self.doc.as_table_mut();
                func(root);
            }
            self
        }

        #[track_caller]
        fn produces_display(&self, expected: &str) -> &Self {
            assert_eq!(self.doc.to_string(), expected);
            self
        }
    }

    #[test]
    fn test_inserting_tables_from_different_parsed_docs() {
        given("[a]")
            .running(|root| {
                let other = "[b]".parse::<DocumentMut>().unwrap();
                root["b"] = other["b"].clone();
            })
            .produces_display("[a]\n[b]\n");
    }

    #[test]
    fn sorting_with_references() {
        let values = vec!["foo", "qux", "bar"];
        let mut array = toml_edit::Array::from_iter(values);
        array.sort_by(|lhs, rhs| lhs.as_str().cmp(&rhs.as_str()));
    }
}
