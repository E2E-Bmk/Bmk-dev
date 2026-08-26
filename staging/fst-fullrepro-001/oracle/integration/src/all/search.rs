// Automaton search agreeing with brute-force filtering over the ordered
// key space, and search composing with range bounds.
mod search {
    use fst::automaton::{Str, Subsequence};
    use fst::{Automaton, IntoStreamer, Map, Set, Streamer};

    const CORPUS: [&str; 8] = [
        "crates/engine/core",
        "crates/engine/wal",
        "crates/query/planner",
        "crates/query/runtime",
        "docs/design/wal",
        "docs/guide/query",
        "tools/bench/engine",
        "tools/lint/rules",
    ];

    fn corpus_set() -> Set<Vec<u8>> {
        Set::from_iter(CORPUS.iter()).unwrap()
    }

    /// Brute-force subsequence check mirroring the automaton's contract.
    fn is_subsequence(needle: &str, hay: &str) -> bool {
        let mut want = needle.bytes().peekable();
        for b in hay.bytes() {
            if want.peek() == Some(&b) {
                want.next();
            }
        }
        want.peek().is_none()
    }

    #[test]
    fn generated_subsequence_agrees_with_brute_force() {
        let set = corpus_set();
        for needle in ["ceg", "wal", "qr", "zzz", "dgq"] {
            let expected: Vec<String> = CORPUS
                .iter()
                .filter(|k| is_subsequence(needle, k))
                .map(|k| k.to_string())
                .collect();
            let got = set
                .search(Subsequence::new(needle))
                .into_stream()
                .into_strs()
                .unwrap();
            assert_eq!(got, expected, "needle {:?}", needle);
        }
    }

    #[test]
    fn generated_starts_with_and_range_compose() {
        let set = corpus_set();
        let got = set
            .search(Str::new("crates/").starts_with())
            .gt("crates/engine/core")
            .into_stream()
            .into_strs()
            .unwrap();
        assert_eq!(
            got,
            vec![
                "crates/engine/wal",
                "crates/query/planner",
                "crates/query/runtime"
            ]
        );
        let bounded = set
            .search(Subsequence::new("wal"))
            .lt("docs")
            .into_stream()
            .into_strs()
            .unwrap();
        assert_eq!(bounded, vec!["crates/engine/wal"]);
    }

    #[test]
    fn generated_complement_is_set_difference() {
        let set = corpus_set();
        let matched = set
            .search(Subsequence::new("engine"))
            .into_stream()
            .into_strs()
            .unwrap();
        let complement = set
            .search(Subsequence::new("engine").complement())
            .into_stream()
            .into_strs()
            .unwrap();
        // The two partitions are disjoint and reassemble the full key set.
        let mut merged = matched.clone();
        merged.extend(complement.iter().cloned());
        merged.sort();
        let all = set.stream().into_strs().unwrap();
        assert_eq!(merged, all);
        assert!(matched.iter().all(|k| !complement.contains(k)));
        assert_eq!(matched.len(), 3);
    }

    #[test]
    fn generated_automaton_intersection_union_algebra() {
        let set = corpus_set();
        let a = Subsequence::new("engine");
        let b = Subsequence::new("crates");
        let both = set
            .search(Subsequence::new("engine").intersection(Subsequence::new("crates")))
            .into_stream()
            .into_strs()
            .unwrap();
        let a_hits = set.search(a).into_stream().into_strs().unwrap();
        let b_hits = set.search(b).into_stream().into_strs().unwrap();
        let expected_both: Vec<String> = a_hits
            .iter()
            .filter(|k| b_hits.contains(k))
            .cloned()
            .collect();
        assert_eq!(both, expected_both);

        let either = set
            .search(Subsequence::new("engine").union(Subsequence::new("crates")))
            .into_stream()
            .into_strs()
            .unwrap();
        let mut expected_either: Vec<String> = a_hits.clone();
        for k in &b_hits {
            if !expected_either.contains(k) {
                expected_either.push(k.clone());
            }
        }
        expected_either.sort();
        assert_eq!(either, expected_either);
    }

    /// Accepts keys whose byte length is at most the configured cap;
    /// prunes with `can_match` once the cap is exceeded.
    struct MaxLen(usize);

    impl Automaton for MaxLen {
        type State = usize;

        fn start(&self) -> usize {
            0
        }

        fn is_match(&self, state: &usize) -> bool {
            *state <= self.0
        }

        fn accept(&self, state: &usize, _byte: u8) -> usize {
            state + 1
        }

        fn can_match(&self, state: &usize) -> bool {
            *state <= self.0
        }
    }

    #[test]
    fn generated_custom_automaton_with_bounds() {
        let set = Set::from_iter(vec!["ash", "aspen", "birch", "fir", "oak", "yew"]).unwrap();
        let short = set.search(MaxLen(3)).into_stream().into_strs().unwrap();
        assert_eq!(short, vec!["ash", "fir", "oak", "yew"]);
        let bounded = set
            .search(MaxLen(3))
            .ge("b")
            .lt("yew")
            .into_stream()
            .into_strs()
            .unwrap();
        assert_eq!(bounded, vec!["fir", "oak"]);
    }

    #[test]
    fn generated_map_search_carries_values() {
        let map = Map::from_iter(vec![
            ("route/alpha", 11u64),
            ("route/beta", 22),
            ("track/alpha", 33),
        ])
        .unwrap();
        let mut stream = map.search(Str::new("route/").starts_with()).into_stream();
        let mut got = vec![];
        while let Some((key, value)) = stream.next() {
            got.push((String::from_utf8(key.to_vec()).unwrap(), value));
        }
        assert_eq!(
            got,
            vec![
                ("route/alpha".to_string(), 11),
                ("route/beta".to_string(), 22)
            ]
        );
    }

    #[test]
    fn generated_raw_search_carries_outputs() {
        let fst = fst::raw::Fst::from_iter_map(vec![
            ("lane/1", 100u64),
            ("lane/2", 200),
            ("road/1", 300),
        ])
        .unwrap();
        let mut stream = fst.search(Str::new("lane/").starts_with()).into_stream();
        let mut got = vec![];
        while let Some((key, out)) = stream.next() {
            got.push((String::from_utf8(key.to_vec()).unwrap(), out.value()));
        }
        assert_eq!(
            got,
            vec![("lane/1".to_string(), 100), ("lane/2".to_string(), 200)]
        );
    }
}
