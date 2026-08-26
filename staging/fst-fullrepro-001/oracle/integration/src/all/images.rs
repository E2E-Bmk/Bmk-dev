// The byte image as a first-class artifact: round trips, verification,
// malformed input, and interop between container views of one image.
mod images {
    use fst::automaton::Str;
    use fst::raw::Output;
    use fst::{IntoStreamer, Map, Set, Streamer};

    #[test]
    fn generated_image_roundtrip_preserves_projections() {
        let map = Map::from_iter(vec![
            ("comet", 5u64),
            ("meteor", 0),
            ("nebula", 77),
            ("quasar", 12),
        ])
        .unwrap();
        let bytes = map.as_fst().to_vec();
        let reopened = Map::new(bytes).unwrap();

        assert_eq!(reopened.len(), map.len());
        assert_eq!(
            reopened.stream().into_byte_vec(),
            map.stream().into_byte_vec()
        );
        assert_eq!(reopened.get("meteor"), Some(0));
        assert_eq!(reopened.get("pulsar"), None);

        let ranged: Vec<(Vec<u8>, u64)> = reopened
            .range()
            .ge("meteor")
            .lt("quasar")
            .into_stream()
            .into_byte_vec();
        assert_eq!(
            ranged,
            vec![(b"meteor".to_vec(), 0u64), (b"nebula".to_vec(), 77)]
        );

        let mut search = reopened.search(Str::new("nebula")).into_stream();
        assert_eq!(search.next(), Some((&b"nebula"[..], 77u64)));
        assert!(search.next().is_none());
    }

    #[test]
    fn generated_corrupt_image_checksum_mismatch() {
        let set = Set::from_iter(vec!["arch", "butte", "canyon", "hoodoo"]).unwrap();
        assert!(set.as_fst().verify().is_ok());

        let mut corrupted = set.as_fst().to_vec();
        let mid = corrupted.len() / 2;
        corrupted[mid] ^= 0x55;
        // A single flipped interior byte still opens (the header is intact)
        // but verification recomputes the checksum and reports the mismatch.
        match Set::new(corrupted) {
            Ok(opened) => match opened.as_fst().verify() {
                Err(fst::Error::Fst(fst::raw::Error::ChecksumMismatch { expected, got })) => {
                    assert_ne!(expected, got);
                }
                other => panic!("expected ChecksumMismatch, got {:?}", other),
            },
            Err(fst::Error::Fst(fst::raw::Error::Format { .. })) => {
                // Also acceptable: the flip landed on structural bytes.
            }
            Err(other) => panic!("unexpected open error {:?}", other),
        }
    }

    #[test]
    fn generated_format_error_size_payload() {
        for size in [0usize, 1, 4, 11] {
            let junk = vec![0xA5u8; size];
            match Map::new(junk) {
                Err(fst::Error::Fst(fst::raw::Error::Format { size: got })) => {
                    assert_eq!(got, size);
                }
                other => panic!("size {}: expected Format error, got {:?}", size, other),
            }
        }
    }

    #[test]
    fn generated_into_inner_reopen_projections() {
        let set = Set::from_iter(vec!["ember", "flame", "spark"]).unwrap();
        let expected_keys = set.stream().into_strs().unwrap();
        let data: Vec<u8> = set.into_fst().into_inner();
        let reopened = Set::new(data).unwrap();
        assert_eq!(reopened.stream().into_strs().unwrap(), expected_keys);
        assert!(reopened.contains("flame"));
    }

    #[test]
    fn generated_set_map_raw_image_interop() {
        // A set's image reopened as a raw transducer answers every key with
        // the zero output.
        let set = Set::from_iter(vec!["gorse", "heather"]).unwrap();
        let raw = fst::raw::Fst::new(set.as_fst().to_vec()).unwrap();
        assert_eq!(raw.len(), 2);
        assert_eq!(raw.get("gorse"), Some(Output::zero()));
        assert_eq!(raw.get("heather"), Some(Output::zero()));

        // A map's image reopened raw answers with the stored values.
        let map = Map::from_iter(vec![("lichen", 15u64)]).unwrap();
        let raw = fst::raw::Fst::new(map.as_fst().to_vec()).unwrap();
        assert_eq!(raw.get("lichen"), Some(Output::new(15)));
        assert!(raw.verify().is_ok());
    }

    #[test]
    fn generated_verify_survives_roundtrip() {
        let map = Map::from_iter(vec![("aa", 1u64), ("ab", 2), ("ba", 3)]).unwrap();
        assert!(map.as_fst().verify().is_ok());
        let reopened = Map::new(map.as_fst().to_vec()).unwrap();
        assert!(reopened.as_fst().verify().is_ok());
        assert_eq!(reopened.as_fst().size(), map.as_fst().size());
    }
}
