// Rewritten upstream tests: toml_edit DocumentMut / Table / Value / Array /
// ArrayOfTables / InlineTable editing API (insert, remove, sort, replace,
// format, decor).
// Source: repo-pool/toml-fullrepro-001 crates/toml_edit/tests/testsuite/edit.rs
// Rewrites: snapbox display snapshots -> assert_eq against the exact rendered
// document (snapbox Inline::trimmed semantics: strip one leading and one
// trailing newline, byte-exact otherwise); to_debug snapshot of
// assign_whitespace -> render-stability round-trip (DocumentMut has no
// PartialEq; structure is asserted through the public key API); sort_values_by
// comparator -> Key::as_str (display_repr is not in the spec surface);
// test_remove_value string assert -> assert_eq; dbg! debugging output dropped;
// should_panic behaviour tests kept (Value/Array/Table indexing and bounds
// semantics are contract per spec VAL/EDIT sections).

mod edit_document {
    use toml_edit::{DocumentMut, Item, Key, Table, Value, array, table, value};

    macro_rules! parse_key {
        ($s:expr) => {{
            let key = $s.parse::<Key>();
            assert!(key.is_ok());
            key.unwrap()
        }};
    }

    macro_rules! as_table {
        ($e:ident) => {{
            assert!($e.is_table());
            $e.as_table_mut().unwrap()
        }};
    }

    macro_rules! as_array {
        ($entry:ident) => {{
            assert!($entry.is_value());
            let a = $entry.as_value_mut().unwrap();
            assert!(a.is_array());
            a.as_array_mut().unwrap()
        }};
    }

    macro_rules! as_inline_table {
        ($entry:ident) => {{
            assert!($entry.is_value());
            let a = $entry.as_value_mut().unwrap();
            assert!(a.is_inline_table());
            a.as_inline_table_mut().unwrap()
        }};
    }

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
        fn running_on_doc<F>(&mut self, func: F) -> &mut Self
        where
            F: Fn(&mut DocumentMut),
        {
            {
                func(&mut self.doc);
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
    fn assign_whitespace() {
        let input = r#"
 # top comment
 [ grandparent . parent ]  # table comment
 # table-value sep comment
 key . child = 'value' # key comment
 key . inline-empty = { }  # empty inline-table comment
 key . inline = { inline . child = 'inline-value' }  # inline-table comment
 key . array-empty = [  # inside empty array comment
 ] # after empty array comment
 key . array = [ # start of array comment
   'one' , # one comment
   'two' , # two comment
] # after array comment
 # table-table sep comment
 [ another . table ]  # table comment
 # final comment
"#;
        // The whitespace- and decor-heavy document must parse, re-emit, and
        // re-parse stably (spec FMT-001/002: decor and comments are preserved
        // and rendering round-trips).
        let doc = input.parse::<DocumentMut>().unwrap();
        let rendered = doc.to_string();
        let reparsed = rendered.parse::<DocumentMut>().unwrap();
        assert_eq!(reparsed.to_string(), rendered);
        // Top-level structure survives the round trip.
        // Root holds only the two explicit tables: the `key . *` dotted
        // entries live inside `grandparent.parent` (TOML: keys after a
        // `[table]` header belong to that table).
        let mut keys: Vec<&str> = reparsed.iter().map(|(k, _)| k).collect();
        keys.sort_unstable();
        assert_eq!(keys, ["another", "grandparent"]);
    }

    #[test]
    fn test_add_root_decor() {
        given(
            r#"[package]
name = "hello"
version = "1.0.0"

[[bin]]
name = "world"
path = "src/bin/world/main.rs"

[dependencies]
nom = "4.0" # future is here

[[bin]]
name = "delete me please"
path = "src/bin/dmp/main.rs""#,
        )
        .running_on_doc(|document| {
            document.decor_mut().set_prefix("# Some Header\n\n");
            document.decor_mut().set_suffix("# Some Footer");
            document.set_trailing("\n\ntrailing...");
        })
        .produces_display(
            "# Some Header\n\n[package]\nname = \"hello\"\nversion = \"1.0.0\"\n\n[[bin]]\nname = \"world\"\npath = \"src/bin/world/main.rs\"\n\n[dependencies]\nnom = \"4.0\" # future is here\n\n[[bin]]\nname = \"delete me please\"\npath = \"src/bin/dmp/main.rs\"\n# Some Footer\n\ntrailing...",
        );
    }

    /// Tests that default decor is None for both suffix and prefix and that this means empty strings
    #[test]
    fn test_no_root_decor() {
        given(
            r#"[package]
name = "hello"
version = "1.0.0"

[[bin]]
name = "world"
path = "src/bin/world/main.rs"

[dependencies]
nom = "4.0" # future is here

[[bin]]
name = "delete me please"
path = "src/bin/dmp/main.rs""#,
        )
        .running_on_doc(|document| {
            assert!(document.decor().prefix().is_none());
            assert!(document.decor().suffix().is_none());
            document.set_trailing("\n\ntrailing...");
        })
        .produces_display(
            "[package]\nname = \"hello\"\nversion = \"1.0.0\"\n\n[[bin]]\nname = \"world\"\npath = \"src/bin/world/main.rs\"\n\n[dependencies]\nnom = \"4.0\" # future is here\n\n[[bin]]\nname = \"delete me please\"\npath = \"src/bin/dmp/main.rs\"\n\n\ntrailing...",
        );
    }

    // insertion

    #[test]
    fn test_insert_leaf_table() {
        given(
            r#"[servers]

        [servers.alpha]
        ip = "10.0.0.1"
        dc = "eqdc10"

        [other.table]"#,
        )
        .running(|root| {
            root["servers"]["beta"] = table();
            root["servers"]["beta"]["ip"] = value("10.0.0.2");
            root["servers"]["beta"]["dc"] = value("eqdc10");
        })
        .produces_display(
            "[servers]\n\n        [servers.alpha]\n        ip = \"10.0.0.1\"\n        dc = \"eqdc10\"\n\n[servers.beta]\nip = \"10.0.0.2\"\ndc = \"eqdc10\"\n\n        [other.table]\n",
        );
    }

    #[test]
    fn test_inserted_leaf_table_goes_after_last_sibling() {
        given(
            r#"
        [package]
        [dependencies]
        [[example]]
        [dependencies.opencl]
        [dev-dependencies]"#,
        )
        .running(|root| {
            root["dependencies"]["newthing"] = table();
        })
        .produces_display(
            "\n        [package]\n        [dependencies]\n        [[example]]\n        [dependencies.opencl]\n\n[dependencies.newthing]\n        [dev-dependencies]\n",
        );
    }

    #[test]
    fn test_insert_nonleaf_table() {
        given(
            r#"
        [other.table]"#,
        )
        .running(|root| {
            root["servers"] = table();
            root["servers"]["alpha"] = table();
            root["servers"]["alpha"]["ip"] = value("10.0.0.1");
            root["servers"]["alpha"]["dc"] = value("eqdc10");
        })
        .produces_display(
            "\n        [other.table]\n\n[servers]\n\n[servers.alpha]\nip = \"10.0.0.1\"\ndc = \"eqdc10\"\n",
        );
    }

    #[test]
    fn test_insert_array() {
        given(
            r#"
        [package]
        title = "withoutarray""#,
        )
        .running(|root| {
            root["bin"] = array();
            assert!(root["bin"].is_array_of_tables());
            let array = root["bin"].as_array_of_tables_mut().unwrap();
            {
                let mut table = Table::new();
                table["hello"] = value("world");
                array.push(table);
            }
            array.push(Table::new());
        })
        .produces_display(
            "\n        [package]\n        title = \"withoutarray\"\n\n[[bin]]\nhello = \"world\"\n\n[[bin]]\n",
        );
    }

    #[test]
    fn test_insert_values() {
        given(
            r#"
        [tbl.son]"#,
        )
        .running(|root| {
            root["tbl"]["key1"] = value("value1");
            root["tbl"]["key2"] = value(42);
            root["tbl"]["key3"] = value(8.1415926);
        })
        .produces_display(
            "[tbl]\nkey1 = \"value1\"\nkey2 = 42\nkey3 = 8.1415926\n\n        [tbl.son]\n",
        );
    }

    #[test]
    fn test_insert_key_with_quotes() {
        given(
            r#"
        [package]
        name = "foo"

        [target]
        "#,
        )
        .running(|root| {
            root["target"]["cfg(target_os = \"linux\")"] = table();
            root["target"]["cfg(target_os = \"linux\")"]["dependencies"] = table();
            root["target"]["cfg(target_os = \"linux\")"]["dependencies"]["name"] = value("dep");
        })
        .produces_display(
            "\n        [package]\n        name = \"foo\"\n\n        [target]\n\n[target.'cfg(target_os = \"linux\")']\n\n[target.'cfg(target_os = \"linux\")'.dependencies]\nname = \"dep\"\n        ",
        );
    }

    // removal

    #[test]
    fn test_remove_leaf_table() {
        given(
            r#"
        [servers]

        # Indentation (tabs and/or spaces) is allowed but not required
[servers.alpha]
        ip = "10.0.0.1"
        dc = "eqdc10"

        [servers.beta]
        ip = "10.0.0.2"
        dc = "eqdc10""#,
        )
        .running(|root| {
            let servers = root.get_mut("servers").unwrap();
            let servers = as_table!(servers);
            assert!(servers.remove("alpha").is_some());
        })
        .produces_display(
            "\n        [servers]\n\n        [servers.beta]\n        ip = \"10.0.0.2\"\n        dc = \"eqdc10\"\n",
        );
    }

    #[test]
    fn test_remove_nonleaf_table() {
        given(
            r#"
        title = "not relevant"

        # comment 1
        [a.b.c] # comment 1.1
        key1 = 1 # comment 1.2
        # comment 2
        [b] # comment 2.1
        key2 = 2 # comment 2.2

        # comment 3
        [a] # comment 3.1
        key3 = 3 # comment 3.2
        [[a.'array']]
        b = 1

        [[a.b.c.trololololololo]] # ohohohohoho
        c = 2
        key3 = 42

           # comment on some other table
           [some.other.table]




        # comment 4
        [a.b] # comment 4.1
        key4 = 4 # comment 4.2
        key41 = 41 # comment 4.3


    "#,
        )
        .running(|root| {
            assert!(root.remove("a").is_some());
        })
        .produces_display(
            "\n        title = \"not relevant\"\n        # comment 2\n        [b] # comment 2.1\n        key2 = 2 # comment 2.2\n\n           # comment on some other table\n           [some.other.table]\n\n\n    ",
        );
    }

    #[test]
    fn test_remove_array_entry() {
        given(
            r#"
        [package]
        name = "hello"
        version = "1.0.0"

        [[bin]]
        name = "world"
        path = "src/bin/world/main.rs"

        [dependencies]
        nom = "4.0" # future is here

        [[bin]]
        name = "delete me please"
        path = "src/bin/dmp/main.rs""#,
        )
        .running(|root| {
            let dmp = root.get_mut("bin").unwrap();
            assert!(dmp.is_array_of_tables());
            let dmp = dmp.as_array_of_tables_mut().unwrap();
            assert_eq!(dmp.len(), 2);
            dmp.remove(1);
            assert_eq!(dmp.len(), 1);
        })
        .produces_display(
            "\n        [package]\n        name = \"hello\"\n        version = \"1.0.0\"\n\n        [[bin]]\n        name = \"world\"\n        path = \"src/bin/world/main.rs\"\n\n        [dependencies]\n        nom = \"4.0\" # future is here\n",
        );
    }

    #[test]
    fn test_remove_array() {
        given(
            r#"
        [package]
        name = "hello"
        version = "1.0.0"

        [[bin]]
        name = "world"
        path = "src/bin/world/main.rs"

        [dependencies]
        nom = "4.0" # future is here

        [[bin]]
        name = "delete me please"
        path = "src/bin/dmp/main.rs""#,
        )
        .running(|root| {
            assert!(root.remove("bin").is_some());
        })
        .produces_display(
            "\n        [package]\n        name = \"hello\"\n        version = \"1.0.0\"\n\n        [dependencies]\n        nom = \"4.0\" # future is here\n",
        );
    }

    #[test]
    fn test_remove_value() {
        given(
            r#"
        name = "hello"
        # delete this
        version = "1.0.0" # please
        documentation = "https://docs.rs/hello""#,
        )
        .running(|root| {
            let value = root.remove("version");
            assert!(value.is_some());
            let value = value.unwrap();
            assert!(value.is_value());
            let value = value.as_value().unwrap();
            assert!(value.is_str());
            let value = value.as_str().unwrap();
            assert_eq!(value, "1.0.0");
        })
        .produces_display(
            "\n        name = \"hello\"\n        documentation = \"https://docs.rs/hello\"\n",
        );
    }

    #[test]
    fn test_remove_last_value_from_implicit() {
        given(
            r#"
        [a]
        b = 1"#,
        )
        .running(|root| {
            let a = root.get_mut("a").unwrap();
            assert!(a.is_table());
            let a = as_table!(a);
            a.set_implicit(true);
            let value = a.remove("b");
            assert!(value.is_some());
            let value = value.unwrap();
            assert!(value.is_value());
            let value = value.as_value().unwrap();
            assert_eq!(value.as_integer(), Some(1));
        })
        .produces_display("");
    }

    // values

    #[test]
    fn test_sort_values() {
        given(
            r#"
        [a.z]

        [a]
        # this comment is attached to b
        b = 2 # as well as this
        a = 1
        c = 3

        [a.y]"#,
        )
        .running(|root| {
            let a = root.get_mut("a").unwrap();
            let a = as_table!(a);
            a.sort_values();
        })
        .produces_display(
            "\n        [a.z]\n\n        [a]\n        a = 1\n        # this comment is attached to b\n        b = 2 # as well as this\n        c = 3\n\n        [a.y]\n",
        );
    }

    #[test]
    fn test_sort_values_by() {
        given(
            r#"
        [a.z]

        [a]
        # this comment is attached to b
        b = 2 # as well as this
        a = 1
        "c" = 3

        [a.y]"#,
        )
        .running(|root| {
            let a = root.get_mut("a").unwrap();
            let a = as_table!(a);
            // Sort by the representation, not the value. So "\"c\"" sorts before "a" because '"' sorts
            // before 'a'. Key: Display (spec surface) renders the key's TOML form, which
            // preserves the quote-first ordering for this input.
            a.sort_values_by(|k1, _, k2, _| k1.to_string().cmp(&k2.to_string()));
        })
        .produces_display(
            "\n        [a.z]\n\n        [a]\n        \"c\" = 3\n        a = 1\n        # this comment is attached to b\n        b = 2 # as well as this\n\n        [a.y]\n",
        );
    }

    #[test]
    fn test_insert_replace_into_array() {
        given(
            r#"
        a = [1,2,3]
        b = []"#,
        )
        .running(|root| {
            {
                let a = root.get_mut("a").unwrap();
                let a = as_array!(a);
                assert_eq!(a.len(), 3);
                assert!(a.get(2).is_some());
                a.push(4);
                assert_eq!(a.len(), 4);
                a.fmt();
            }
            let b = root.get_mut("b").unwrap();
            let b = as_array!(b);
            assert!(b.is_empty());
            b.push("hello");
            assert_eq!(b.len(), 1);

            b.push_formatted(Value::from("world").decorated("\n", "\n"));
            b.push_formatted(Value::from("test").decorated("", ""));

            b.insert(1, "beep");
            b.insert_formatted(2, Value::from("boop").decorated("   ", "   "));

            // This should preserve formatting.
            assert_eq!(b.replace(2, "zoink").as_str(), Some("boop"));
            // This should replace formatting.
            assert_eq!(
                b.replace_formatted(4, Value::from("yikes").decorated("  ", ""))
                    .as_str(),
                Some("test")
            );
        })
        .produces_display(
            "\n        a = [1, 2, 3, 4]\n        b = [\"hello\", \"beep\",   \"zoink\"   ,\n\"world\"\n,  \"yikes\"]\n",
        );
    }

    #[test]
    fn test_remove_from_array() {
        given(
            r#"
        a = [1, 2, 3, 4]
        b = ["hello"]"#,
        )
        .running(|root| {
            {
                let a = root.get_mut("a").unwrap();
                let a = as_array!(a);
                assert_eq!(a.len(), 4);
                assert!(a.remove(3).is_integer());
                assert_eq!(a.len(), 3);
            }
            let b = root.get_mut("b").unwrap();
            let b = as_array!(b);
            assert_eq!(b.len(), 1);
            assert!(b.remove(0).is_str());
            assert!(b.is_empty());
        })
        .produces_display(
            "\n        a = [1, 2, 3]\n        b = []\n",
        );
    }

    #[test]
    fn test_format_array() {
        given(
            r#"
    a = [
      1,
            "2",
      3.0,
    ]
    "#,
        )
        .running(|root| {
            for (_, v) in root.iter_mut() {
                if let Item::Value(Value::Array(array)) = v {
                    array.fmt();
                }
            }
        })
        .produces_display(
            "\n    a = [1, \"2\", 3.0]\n    ",
        );
    }

    #[test]
    fn test_insert_into_inline_table() {
        given(
            r#"
        a = {a=2,  c = 3}
        b = {}"#,
        )
        .running(|root| {
            {
                let a = root.get_mut("a").unwrap();
                let a = as_inline_table!(a);
                assert_eq!(a.len(), 2);
                assert!(a.contains_key("a") && a.get("c").is_some() && a.get_mut("c").is_some());
                a.get_or_insert("b", 42);
                assert_eq!(a.len(), 3);
                a.fmt();
            }
            let b = root.get_mut("b").unwrap();
            let b = as_inline_table!(b);
            assert!(b.is_empty());
            b.get_or_insert("hello", "world");
            assert_eq!(b.len(), 1);
            b.fmt();
        })
        .produces_display(
            "\n        a = { a = 2, c = 3, b = 42 }\n        b = { hello = \"world\" }\n",
        );
    }

    #[test]
    fn test_remove_from_inline_table() {
        given(
            r#"
        a = {a=2,  c = 3, b = 42}
        b = {'hello' = "world"}"#,
        )
        .running(|root| {
            {
                let a = root.get_mut("a").unwrap();
                let a = as_inline_table!(a);
                assert_eq!(a.len(), 3);
                assert!(a.remove("c").is_some());
                assert_eq!(a.len(), 2);
            }
            let b = root.get_mut("b").unwrap();
            let b = as_inline_table!(b);
            assert_eq!(b.len(), 1);
            assert!(b.remove("hello").is_some());
            assert!(b.is_empty());
        })
        .produces_display(
            "\n        a = {a=2, b = 42}\n        b = {}\n",
        );
    }

    #[test]
    fn test_as_table_like() {
        given(
            r#"
        a = {a=2,  c = 3, b = 42}
        x = {}
        [[bin]]
        [b]
        x = "y"
        [empty]"#,
        )
        .running(|root| {
            let a = root["a"].as_table_like();
            assert!(a.is_some());
            let a = a.unwrap();
            assert_eq!(a.iter().count(), 3);
            assert_eq!(a.len(), 3);
            assert_eq!(a.get("a").and_then(Item::as_integer), Some(2));

            let b = root["b"].as_table_like();
            assert!(b.is_some());
            let b = b.unwrap();
            assert_eq!(b.iter().count(), 1);
            assert_eq!(b.len(), 1);
            assert_eq!(b.get("x").and_then(Item::as_str), Some("y"));

            assert_eq!(root["x"].as_table_like().map(|t| t.iter().count()), Some(0));
            assert_eq!(
                root["empty"].as_table_like().map(|t| t.is_empty()),
                Some(true)
            );

            assert!(root["bin"].as_table_like().is_none());
        });
    }

    #[test]
    fn test_inline_table_append() {
        let mut a = Value::from_iter(vec![
            (parse_key!("a"), 1),
            (parse_key!("b"), 2),
            (parse_key!("c"), 3),
        ]);
        let a = a.as_inline_table_mut().unwrap();

        let mut b = Value::from_iter(vec![
            (parse_key!("c"), 4),
            (parse_key!("d"), 5),
            (parse_key!("e"), 6),
        ]);
        let b = b.as_inline_table_mut().unwrap();

        a.extend(b.iter());
        assert_eq!(a.len(), 5);
        assert!(a.contains_key("e"));
        assert_eq!(b.len(), 3);
    }

    #[test]
    fn test_insert_dotted_into_std_table() {
        given("")
            .running(|root| {
                root["nixpkgs"] = table();

                root["nixpkgs"]["src"] = table();
                root["nixpkgs"]["src"]
                    .as_table_like_mut()
                    .unwrap()
                    .set_dotted(true);
                root["nixpkgs"]["src"]["git"] = value("https://github.com/nixos/nixpkgs");
            })
            .produces_display(
                "[nixpkgs]\nsrc.git = \"https://github.com/nixos/nixpkgs\"\n",
            );
    }

    #[test]
    fn test_insert_dotted_into_implicit_table() {
        given("")
            .running(|root| {
                root["nixpkgs"] = table();

                root["nixpkgs"]["src"]["git"] = value("https://github.com/nixos/nixpkgs");
                root["nixpkgs"]["src"]
                    .as_table_like_mut()
                    .unwrap()
                    .set_dotted(true);
            })
            .produces_display(
                "[nixpkgs]\nsrc.git = \"https://github.com/nixos/nixpkgs\"\n",
            );
    }

    #[test]
    fn table_str_key_whitespace() {
        let mut document = "bookmark = 1010".parse::<DocumentMut>().unwrap();

        let key: &str = "bookmark";

        document.insert(key, array());
        let table = document[key].as_array_of_tables_mut().unwrap();

        let mut bookmark_table = Table::new();
        bookmark_table["name"] = value("test.swf".to_owned());
        table.push(bookmark_table);

        assert_eq!(
            document.to_string(),
            "[[bookmark]]\nname = \"test.swf\"\n"
        );
    }

    #[test]
    fn table_key_decor_whitespace() {
        let mut document = "bookmark = 1010".parse::<DocumentMut>().unwrap();

        let key = Key::parse("  bookmark   ").unwrap().remove(0);

        document.insert_formatted(&key, array());
        let table = document[&key].as_array_of_tables_mut().unwrap();

        let mut bookmark_table = Table::new();
        bookmark_table["name"] = value("test.swf".to_owned());
        table.push(bookmark_table);

        assert_eq!(
            document.to_string(),
            "[[  bookmark   ]]\nname = \"test.swf\"\n"
        );
    }

    #[test]
    fn table_into_inline() {
        let toml = r#"
[table]
string = "value"
array = [1, 2, 3]
inline = { "1" = 1, "2" = 2 }

[table.child]
other = "world"
"#;
        let mut doc = toml.parse::<DocumentMut>().unwrap();

        doc.get_mut("table").unwrap().make_value();

        let actual = doc.to_string();
        // `table=` is because we didn't re-format the table key, only the value
        assert_eq!(
            actual,
            "table= { string = \"value\", array = [1, 2, 3], inline = { \"1\" = 1, \"2\" = 2 }, child = { other = \"world\" } }\n"
        );
    }

    #[test]
    fn inline_table_to_table() {
        let toml = r#"table = { string = "value", array = [1, 2, 3], inline = { "1" = 1, "2" = 2 }, child = { other = "world" } }
"#;
        let mut doc = toml.parse::<DocumentMut>().unwrap();

        let t = doc.remove("table").unwrap();
        let t = match t {
            Item::Value(Value::InlineTable(t)) => t,
            _ => unreachable!("Unexpected {:?}", t),
        };
        let t = t.into_table();
        doc.insert("table", Item::Table(t));

        let actual = doc.to_string();
        assert_eq!(
            actual,
            "[table]\nstring = \"value\"\narray = [1, 2, 3]\ninline = { \"1\" = 1, \"2\" = 2 }\nchild = { other = \"world\" }\n"
        );
    }

    #[test]
    fn array_of_tables_to_array() {
        let toml = r#"
[[table]]
string = "value"
array = [1, 2, 3]
inline = { "1" = 1, "2" = 2 }

[table.child]
other = "world"

[[table]]
string = "value"
array = [1, 2, 3]
inline = { "1" = 1, "2" = 2 }

[table.child]
other = "world"
"#;
        let mut doc = toml.parse::<DocumentMut>().unwrap();

        doc.get_mut("table").unwrap().make_value();

        let actual = doc.to_string();
        // `table=` is because we didn't re-format the table key, only the value
        assert_eq!(
            actual,
            "table= [{ string = \"value\", array = [1, 2, 3], inline = { \"1\" = 1, \"2\" = 2 }, child = { other = \"world\" } }, { string = \"value\", array = [1, 2, 3], inline = { \"1\" = 1, \"2\" = 2 }, child = { other = \"world\" } }]\n"
        );
    }

    #[test]
    fn test_key_from_str() {
        macro_rules! test_key {
            ($s:expr, $expected:expr) => {{
                let key = $s.parse::<Key>();
                match key {
                    Ok(key) => assert_eq!($expected, key.get(), ""),
                    Err(err) => panic!("failed with {err}"),
                }
            }};
        }

        test_key!("a", "a");
        test_key!(r#"'hello key'"#, "hello key");
        test_key!(
            r#""Jos\u00E9\U000A0000\n\t\r\f\b\"""#,
            "Jos\u{00E9}\u{A0000}\n\t\r\u{c}\u{8}\""
        );
        test_key!("\"\"", "");
        test_key!("\"'hello key'bla\"", "'hello key'bla");
        test_key!(
            "'C:\\Users\\appveyor\\AppData\\Local\\Temp\\1\\cargo-edit-test.YizxPxxElXn9'",
            "C:\\Users\\appveyor\\AppData\\Local\\Temp\\1\\cargo-edit-test.YizxPxxElXn9"
        );
    }

    #[test]
    fn despan_keys() {
        let mut doc = r#"aaaaaa = 1"#.parse::<DocumentMut>().unwrap();
        let key = "bbb".parse::<Key>().unwrap();
        let table = doc.as_table_mut();
        table.insert_formatted(
            &key,
            Item::Value(Value::Integer(toml_edit::Formatted::new(2))),
        );

        assert_eq!(doc.to_string(), "aaaaaa = 1\nbbb = 2\n");
    }

    #[test]
    fn key_repr_roundtrip() {
        assert_key_repr_roundtrip(r#""""#, r#""""#);
        assert_key_repr_roundtrip(r#""a""#, r#""a""#);

        assert_key_repr_roundtrip(r#""tab \t tab""#, r#""tab \t tab""#);
        assert_key_repr_roundtrip(r#""lf \n lf""#, r#""lf \n lf""#);
        assert_key_repr_roundtrip(r#""crlf \r\n crlf""#, r#""crlf \r\n crlf""#);
        assert_key_repr_roundtrip(r#""bell \b bell""#, r#""bell \b bell""#);
        assert_key_repr_roundtrip(r#""feed \f feed""#, r#""feed \f feed""#);
        assert_key_repr_roundtrip(
            r#""backslash \\ backslash""#,
            r#""backslash \\ backslash""#,
        );

        assert_key_repr_roundtrip(r#""squote ' squote""#, r#""squote ' squote""#);
        assert_key_repr_roundtrip(
            r#""triple squote ''' triple squote""#,
            r#""triple squote ''' triple squote""#,
        );
        assert_key_repr_roundtrip(r#""end squote '""#, r#""end squote '""#);

        assert_key_repr_roundtrip(r#""quote \" quote""#, r#""quote \" quote""#);
        assert_key_repr_roundtrip(
            r#""triple quote \"\"\" triple quote""#,
            r#""triple quote \"\"\" triple quote""#,
        );
        assert_key_repr_roundtrip(r#""end quote \"""#, r#""end quote \"""#);
        assert_key_repr_roundtrip(
            r#""quoted \"content\" quoted""#,
            r#""quoted \"content\" quoted""#,
        );
        assert_key_repr_roundtrip(
            r#""squoted 'content' squoted""#,
            r#""squoted 'content' squoted""#,
        );
        assert_key_repr_roundtrip(
            r#""mixed quoted \"start\" 'end'' mixed quote""#,
            r#""mixed quoted \"start\" 'end'' mixed quote""#,
        );
    }

    #[track_caller]
    fn assert_key_repr_roundtrip(input: &str, expected: &str) {
        let value: Key = input.parse().unwrap();
        let actual = value.to_string();
        let _: Key = actual.parse().unwrap_or_else(|_err| {
            panic!(
                "invalid `Key`:
```
{actual}
```
"
            )
        });
        assert_eq!(actual, expected);
    }

    #[test]
    fn key_value_roundtrip() {
        assert_key_value_roundtrip(r#""""#, r#""""#);
        assert_key_value_roundtrip(r#""a""#, "a");

        assert_key_value_roundtrip(r#""tab \t tab""#, r#""tab \t tab""#);
        assert_key_value_roundtrip(r#""lf \n lf""#, r#""lf \n lf""#);
        assert_key_value_roundtrip(r#""crlf \r\n crlf""#, r#""crlf \r\n crlf""#);
        assert_key_value_roundtrip(r#""bell \b bell""#, r#""bell \b bell""#);
        assert_key_value_roundtrip(r#""feed \f feed""#, r#""feed \f feed""#);
        assert_key_value_roundtrip(
            r#""backslash \\ backslash""#,
            "'backslash \\ backslash'",
        );

        assert_key_value_roundtrip(r#""squote ' squote""#, r#""squote ' squote""#);
        assert_key_value_roundtrip(
            r#""triple squote ''' triple squote""#,
            r#""triple squote ''' triple squote""#,
        );
        assert_key_value_roundtrip(r#""end squote '""#, r#""end squote '""#);

        assert_key_value_roundtrip(r#""quote \" quote""#, "'quote \" quote'");
        assert_key_value_roundtrip(
            r#""triple quote \"\"\" triple quote""#,
            "'triple quote \"\"\" triple quote'",
        );
        assert_key_value_roundtrip(r#""end quote \"""#, "'end quote \"'");
        assert_key_value_roundtrip(
            r#""quoted \"content\" quoted""#,
            "'quoted \"content\" quoted'",
        );
        assert_key_value_roundtrip(
            r#""squoted 'content' squoted""#,
            r#""squoted 'content' squoted""#,
        );
        assert_key_value_roundtrip(
            r#""mixed quoted \"start\" 'end'' mixed quote""#,
            r#""mixed quoted \"start\" 'end'' mixed quote""#,
        );
    }

    #[track_caller]
    fn assert_key_value_roundtrip(input: &str, expected: &str) {
        let value: Key = input.parse().unwrap();
        let value = Key::new(value.get()); // Remove repr
        let actual = value.to_string();
        let _: Key = actual.parse().unwrap_or_else(|_err| {
            panic!(
                "invalid `Key`:
```
{actual}
```
"
            )
        });
        assert_eq!(actual, expected);
    }

    #[test]
    fn table_under_inline() {
        let mut doc = DocumentMut::new();
        doc["tool"]["typst-test"] = table();
        doc["tool"]["typst-test"]["tests"] = value("tests");

        assert_eq!(
            doc.to_string(),
            "tool = { typst-test.tests = \"tests\" }\n"
        );
    }

    #[test]
    fn array_of_tables_insert_at_beginning() {
        given(
            r#"[[fruit]]
name = "apple"

[[fruit]]
name = "banana"
"#,
        )
        .running(|root| {
            let array = root["fruit"].as_array_of_tables_mut().unwrap();
            let mut new_table = Table::new();
            new_table.insert("name", value("cherry"));
            array.insert(0, new_table);
            // The previously-first table (now at index 1) had no leading blank line
            // from parsing; fix it up so it separates properly.
            array.get_mut(1).unwrap().decor_mut().set_prefix("\n");
        })
        .produces_display(
            "[[fruit]]\nname = \"cherry\"\n\n[[fruit]]\nname = \"apple\"\n\n[[fruit]]\nname = \"banana\"\n",
        );
    }

    #[test]
    fn array_of_tables_insert_in_middle() {
        given(
            r#"[[fruit]]
name = "apple"

[[fruit]]
name = "banana"
"#,
        )
        .running(|root| {
            let array = root["fruit"].as_array_of_tables_mut().unwrap();
            let mut new_table = Table::new();
            new_table.insert("name", value("cherry"));
            // Give the new table a leading blank line to match the existing style.
            new_table.decor_mut().set_prefix("\n");
            array.insert(1, new_table);
        })
        .produces_display(
            "[[fruit]]\nname = \"apple\"\n\n[[fruit]]\nname = \"cherry\"\n\n[[fruit]]\nname = \"banana\"\n",
        );
    }

    #[test]
    fn array_of_tables_insert_at_end() {
        given(
            r#"[[fruit]]
name = "apple"

[[fruit]]
name = "banana"
"#,
        )
        .running(|root| {
            let array = root["fruit"].as_array_of_tables_mut().unwrap();
            let mut new_table = Table::new();
            new_table.insert("name", value("cherry"));
            // Give the new table a leading blank line to match the existing style.
            new_table.decor_mut().set_prefix("\n");
            array.insert(2, new_table);
        })
        .produces_display(
            "[[fruit]]\nname = \"apple\"\n\n[[fruit]]\nname = \"banana\"\n\n[[fruit]]\nname = \"cherry\"\n",
        );
    }

    #[test]
    #[should_panic]
    fn array_of_tables_insert_out_of_bounds() {
        let mut array = toml_edit::ArrayOfTables::new();
        let t = Table::new();
        array.insert(1, t);
    }

    #[test]
    fn inline_table_to_table_with_comment() {
        given(
            r#"
# hello i'm a comment
foo = { bar = 1 }
"#,
        )
        .running(|root| {
            let mut new_foo = Table::new();
            new_foo.insert("bar", Item::Value(1.into()));
            new_foo.insert("baz", Item::Value(2.into()));
            *root.get_mut("foo").unwrap() = Item::Table(new_foo);
        })
        .produces_display(
            "\n# hello i'm a comment\n[foo]\nbar = 1\nbaz = 2\n",
        );
    }

    #[test]
    fn inline_table_to_array_of_tables_with_comment() {
        given(
            r#"
# hello i'm a comment
foo = [{ bar = 1 }]
"#,
        )
        .running(|root| {
            let mut new_foo_entry = Table::new();
            new_foo_entry.insert("bar", Item::Value(1.into()));
            new_foo_entry.insert("baz", Item::Value(2.into()));
            let mut arr = toml_edit::ArrayOfTables::new();
            arr.push(new_foo_entry);
            *root.get_mut("foo").unwrap() = Item::ArrayOfTables(arr);
        })
        .produces_display(
            "\n# hello i'm a comment\n[[foo]]\nbar = 1\nbaz = 2\n",
        );
    }

    #[test]
    fn array_of_tables_replace() {
        given(
            r#"[[fruit]]
name = "apple"

# tropical
[[fruit]]
name = "banana"
"#,
        )
        .running(|root| {
            let array = root["fruit"].as_array_of_tables_mut().unwrap();
            let mut new_table = Table::new();
            new_table.insert("name", value("cherry"));
            let old = array.replace(1, new_table);
            assert_eq!(old["name"].as_str(), Some("banana"));
        })
        .produces_display(
            "[[fruit]]\nname = \"apple\"\n\n[[fruit]]\nname = \"cherry\"\n",
        );
    }

    #[test]
    #[should_panic]
    fn array_of_tables_replace_out_of_bounds() {
        let mut array = toml_edit::ArrayOfTables::new();
        let t = Table::new();
        array.replace(0, t);
    }
}
