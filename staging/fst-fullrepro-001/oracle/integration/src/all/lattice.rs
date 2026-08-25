// The set-operation lattice across multiple containers: union,
// intersection, difference, symmetric difference, provenance, predicates.
mod lattice {
    use fst::map::IndexedValue;
    use fst::{Automaton, Map, Set, Streamer};
    use std::collections::BTreeSet;

    fn keys_of<'a, S>(mut stream: S) -> Vec<String>
    where
        S: for<'b> Streamer<'b, Item = &'b [u8]>,
    {
        let mut out = vec![];
        while let Some(key) = stream.next() {
            out.push(String::from_utf8(key.to_vec()).unwrap());
        }
        out
    }

    fn fixture() -> (Set<Vec<u8>>, Set<Vec<u8>>) {
        let a = Set::from_iter(vec!["gale", "gust", "squall", "zephyr"]).unwrap();
        let b = Set::from_iter(vec!["breeze", "gust", "zephyr"]).unwrap();
        (a, b)
    }

    #[test]
    fn generated_two_set_ops_match_brute_force() {
        let (a, b) = fixture();
        let sa: BTreeSet<String> = a.stream().into_strs().unwrap().into_iter().collect();
        let sb: BTreeSet<String> = b.stream().into_strs().unwrap().into_iter().collect();

        let union = keys_of(a.op().add(&b).union());
        let expected: Vec<String> = sa.union(&sb).cloned().collect();
        assert_eq!(union, expected);

        let inter = keys_of(a.op().add(&b).intersection());
        let expected: Vec<String> = sa.intersection(&sb).cloned().collect();
        assert_eq!(inter, expected);

        let diff = keys_of(a.op().add(&b).difference());
        let expected: Vec<String> = sa.difference(&sb).cloned().collect();
        assert_eq!(diff, expected);

        let sym = keys_of(a.op().add(&b).symmetric_difference());
        let expected: Vec<String> = sa.symmetric_difference(&sb).cloned().collect();
        assert_eq!(sym, expected);
    }

    #[test]
    fn generated_three_stream_difference_first_minus_rest() {
        let s1 = Set::from_iter(vec!["ada", "cob", "eel", "fry"]).unwrap();
        let s2 = Set::from_iter(vec!["cob", "fry"]).unwrap();
        let s3 = Set::from_iter(vec!["eel", "fry"]).unwrap();
        let diff = keys_of(s1.op().add(&s2).add(&s3).difference());
        assert_eq!(diff, vec!["ada"]);
    }

    #[test]
    fn generated_three_stream_symmetric_difference_odd_count() {
        let s1 = Set::from_iter(vec!["ada", "cob", "eel", "fry"]).unwrap();
        let s2 = Set::from_iter(vec!["cob", "fry"]).unwrap();
        let s3 = Set::from_iter(vec!["eel", "fry"]).unwrap();
        // ada: 1 stream (odd, kept); cob: 2 (dropped); eel: 2 (dropped);
        // fry: 3 (odd, kept).
        let sym = keys_of(s1.op().add(&s2).add(&s3).symmetric_difference());
        assert_eq!(sym, vec!["ada", "fry"]);
    }

    #[test]
    fn generated_map_union_indexed_value_provenance() {
        let m1 = Map::from_iter(vec![("apex", 10u64), ("base", 20)]).unwrap();
        let m2 = Map::from_iter(vec![("base", 200u64), ("crest", 300)]).unwrap();
        let mut union = m1.op().add(&m2).union();
        let mut got: Vec<(String, Vec<IndexedValue>)> = vec![];
        while let Some((key, ivs)) = union.next() {
            got.push((String::from_utf8(key.to_vec()).unwrap(), ivs.to_vec()));
        }
        assert_eq!(
            got,
            vec![
                (
                    "apex".to_string(),
                    vec![IndexedValue { index: 0, value: 10 }]
                ),
                (
                    "base".to_string(),
                    vec![
                        IndexedValue { index: 0, value: 20 },
                        IndexedValue { index: 1, value: 200 }
                    ]
                ),
                (
                    "crest".to_string(),
                    vec![IndexedValue { index: 1, value: 300 }]
                ),
            ]
        );
    }

    #[test]
    fn generated_map_intersection_provenance_sorted_by_index() {
        let m1 = Map::from_iter(vec![("dim", 1u64), ("lit", 2)]).unwrap();
        let m2 = Map::from_iter(vec![("dim", 7u64), ("dun", 8), ("lit", 9)]).unwrap();
        let m3 = Map::from_iter(vec![("lit", 40u64)]).unwrap();
        let mut inter = m1.op().add(&m2).add(&m3).intersection();
        let mut got: Vec<(String, Vec<(usize, u64)>)> = vec![];
        while let Some((key, ivs)) = inter.next() {
            got.push((
                String::from_utf8(key.to_vec()).unwrap(),
                ivs.iter().map(|iv| (iv.index, iv.value)).collect(),
            ));
        }
        // Only "lit" is present in all three inputs; provenance entries are
        // sorted by input stream index.
        assert_eq!(got, vec![("lit".to_string(), vec![(0, 2), (1, 9), (2, 40)])]);
    }

    #[test]
    fn generated_op_over_range_and_search_streams() {
        let a = Set::from_iter(vec!["kelp01", "kelp02", "kelp03", "wrack01"]).unwrap();
        let b = Set::from_iter(vec!["kelp02", "kelp03", "wrack02"]).unwrap();
        // Operands are sub-streams, not whole containers.
        let inter = keys_of(
            fst::set::OpBuilder::new()
                .add(a.range().lt("wrack01"))
                .add(b.search(fst::automaton::Str::new("kelp").starts_with()))
                .intersection(),
        );
        assert_eq!(inter, vec!["kelp02", "kelp03"]);
    }

    #[test]
    fn generated_push_and_add_equivalent() {
        let (a, b) = fixture();
        let via_add = keys_of(a.op().add(&b).union());
        let mut builder = a.op();
        builder.push(&b);
        let via_push = keys_of(builder.union());
        assert_eq!(via_add, via_push);
    }

    #[test]
    fn generated_subset_superset_disjoint_predicates() {
        let big = Set::from_iter(vec!["ant", "bee", "fly", "moth", "wasp"]).unwrap();
        let small = Set::from_iter(vec!["bee", "moth"]).unwrap();
        let other = Set::from_iter(vec!["crab", "squid"]).unwrap();

        assert!(small.is_subset(big.stream()));
        assert!(!big.is_subset(small.stream()));
        assert!(big.is_superset(small.stream()));
        assert!(!small.is_superset(big.stream()));
        assert!(small.is_disjoint(other.stream()));
        assert!(!small.is_disjoint(big.stream()));
        // Every set is subset and superset of itself, and never disjoint
        // from itself unless empty.
        assert!(small.is_subset(small.stream()));
        assert!(small.is_superset(small.stream()));
        assert!(!small.is_disjoint(small.stream()));
    }

    #[test]
    fn generated_raw_predicates_over_keys() {
        let big = fst::raw::Fst::from_iter_map(vec![("ash", 1u64), ("oak", 2), ("yew", 3)])
            .unwrap();
        let small = fst::raw::Fst::from_iter_map(vec![("oak", 99u64)]).unwrap();
        // Predicates compare keys; values play no part.
        assert!(small.is_subset(small.stream()));
        assert!(big.is_superset(small.stream()));
        assert!(!big.is_disjoint(small.stream()));
    }
}
