// Cross-view invariants: one key set observed through point queries, full
// streams, ranges, searches, ops, and the raw view.
mod cross_view {
    use fst::automaton::Subsequence;
    use fst::raw::Output;
    use fst::{Automaton, IntoStreamer, Map, Set, SetBuilder, Streamer};

    const HERBS: [&str; 7] = [
        "angelica", "borage", "chervil", "fennel", "lovage", "sorrel", "tarragon",
    ];

    #[test]
    fn generated_stream_count_matches_len_and_membership() {
        let set = Set::from_iter(HERBS.iter()).unwrap();
        let mut stream = set.stream();
        let mut count = 0;
        while let Some(key) = stream.next() {
            assert!(set.contains(key));
            count += 1;
        }
        assert_eq!(count, set.len());

        let map = Map::from_iter(HERBS.iter().zip(0u64..).map(|(k, v)| (k, v * 3))).unwrap();
        let mut stream = map.stream();
        let mut count = 0;
        while let Some((key, value)) = stream.next() {
            assert_eq!(map.get(key), Some(value));
            count += 1;
        }
        assert_eq!(count, map.len());
    }

    #[test]
    fn generated_range_matrix_agrees_with_filter() {
        let set = Set::from_iter(HERBS.iter()).unwrap();
        let all = set.stream().into_strs().unwrap();
        let lo = "chervil";
        let hi = "sorrel";

        let cases: Vec<(Vec<String>, Vec<String>)> = vec![
            (
                set.range().ge(lo).into_stream().into_strs().unwrap(),
                all.iter().filter(|k| k.as_str() >= lo).cloned().collect(),
            ),
            (
                set.range().gt(lo).into_stream().into_strs().unwrap(),
                all.iter().filter(|k| k.as_str() > lo).cloned().collect(),
            ),
            (
                set.range().le(hi).into_stream().into_strs().unwrap(),
                all.iter().filter(|k| k.as_str() <= hi).cloned().collect(),
            ),
            (
                set.range().lt(hi).into_stream().into_strs().unwrap(),
                all.iter().filter(|k| k.as_str() < hi).cloned().collect(),
            ),
            (
                set.range()
                    .gt(lo)
                    .le(hi)
                    .into_stream()
                    .into_strs()
                    .unwrap(),
                all.iter()
                    .filter(|k| k.as_str() > lo && k.as_str() <= hi)
                    .cloned()
                    .collect(),
            ),
        ];
        for (got, expected) in cases {
            assert_eq!(got, expected);
        }
    }

    #[test]
    fn generated_map_and_raw_view_agree() {
        let map = Map::from_iter(vec![("dell", 40u64), ("holt", 0), ("shaw", 9)]).unwrap();
        let fst = map.as_fst();
        for (key, value) in [("dell", 40u64), ("holt", 0), ("shaw", 9)] {
            assert_eq!(map.get(key), Some(value));
            assert_eq!(fst.get(key), Some(Output::new(value)));
        }
        assert_eq!(map.get("dale"), None);
        assert_eq!(fst.get("dale"), None);
        assert_eq!(map.len(), fst.len());
    }

    #[test]
    fn generated_set_into_fst_projections_agree() {
        let set = Set::from_iter(vec!["glade", "grove"]).unwrap();
        let expected_keys = set.stream().into_strs().unwrap();
        let fst = set.into_fst();
        assert_eq!(fst.len(), 2);
        let mut stream = fst.stream();
        let mut keys = vec![];
        while let Some((key, out)) = stream.next() {
            assert!(out.is_zero());
            keys.push(String::from_utf8(key.to_vec()).unwrap());
        }
        assert_eq!(keys, expected_keys);
        assert!(fst.contains_key("glade"));
    }

    #[test]
    fn generated_union_extend_stream_workflow() {
        // Merge two indexes into a third container through the op layer,
        // then verify the merged container answers as the union of both.
        let january = Set::from_iter(vec!["log/03", "log/07", "log/19"]).unwrap();
        let february = Set::from_iter(vec!["log/07", "log/12"]).unwrap();

        let mut merged_builder = SetBuilder::memory();
        merged_builder
            .extend_stream(january.op().add(&february).union())
            .unwrap();
        let merged = merged_builder.into_set();

        assert_eq!(merged.len(), 4);
        assert_eq!(
            merged.stream().into_strs().unwrap(),
            vec!["log/03", "log/07", "log/12", "log/19"]
        );
        for key in january.stream().into_strs().unwrap() {
            assert!(merged.contains(key));
        }
        for key in february.stream().into_strs().unwrap() {
            assert!(merged.contains(key));
        }
        // The merged image equals the one-shot construction of the same keys.
        let one_shot =
            Set::from_iter(vec!["log/03", "log/07", "log/12", "log/19"]).unwrap();
        assert_eq!(merged.as_fst().as_bytes(), one_shot.as_fst().as_bytes());
    }

    #[test]
    fn generated_map_keys_values_stream_zip_agree() {
        let map = Map::from_iter(vec![("ait", 14u64), ("holm", 2), ("skerry", 33)]).unwrap();
        let mut keys = vec![];
        let mut key_stream = map.keys();
        while let Some(k) = key_stream.next() {
            keys.push(k.to_vec());
        }
        let mut values = vec![];
        let mut value_stream = map.values();
        while let Some(v) = value_stream.next() {
            values.push(v);
        }
        let pairs: Vec<(Vec<u8>, u64)> = map.stream().into_byte_vec();
        assert_eq!(pairs.len(), keys.len());
        assert_eq!(pairs.len(), values.len());
        for (i, (k, v)) in pairs.iter().enumerate() {
            assert_eq!(&keys[i], k);
            assert_eq!(values[i], *v);
        }
    }

    #[test]
    fn generated_get_key_roundtrip_whole_map() {
        // Monotonically increasing values in key order: reverse lookup
        // recovers every key, and misses answer None.
        let pairs: Vec<(&str, u64)> = vec![("east", 2), ("north", 11), ("south", 30), ("west", 41)];
        let map = Map::from_iter(pairs.clone()).unwrap();
        let fst = map.as_fst();
        for (key, value) in &pairs {
            assert_eq!(fst.get_key(*value), Some(key.as_bytes().to_vec()));
        }
        for absent in [0u64, 3, 12, 40, 99] {
            assert_eq!(fst.get_key(absent), None);
        }
    }

    #[test]
    fn generated_search_and_ops_are_consistent_views() {
        // CVI: filtering by automaton then unioning the complement restores
        // the full stream, across two independent projections of one image.
        let set = Set::from_iter(HERBS.iter()).unwrap();
        let aut = Subsequence::new("el");
        let hits = set.search(aut).into_stream();
        let misses = set
            .search(Subsequence::new("el").complement())
            .into_stream();
        let mut rebuilt = SetBuilder::memory();
        rebuilt
            .extend_stream(fst::set::OpBuilder::new().add(hits).add(misses).union())
            .unwrap();
        let rebuilt = rebuilt.into_set();
        assert_eq!(
            rebuilt.stream().into_strs().unwrap(),
            set.stream().into_strs().unwrap()
        );
        assert_eq!(rebuilt.as_fst().as_bytes(), set.as_fst().as_bytes());
    }
}
