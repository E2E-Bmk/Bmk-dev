// Construction paths converging on one image: one-shot, memory builder,
// writer-backed builder, extend forms.
mod build_paths {
    use fst::{Map, MapBuilder, Set, SetBuilder};

    const KEYS: [&str; 6] = ["boron", "carbon", "helium", "neon", "radon", "xenon"];

    #[test]
    fn generated_all_set_paths_identical_images() {
        let one_shot = Set::from_iter(KEYS.iter()).unwrap();

        let mut mem = SetBuilder::memory();
        for k in KEYS.iter() {
            mem.insert(k).unwrap();
        }
        let memory_built = mem.into_set();

        let mut buf: Vec<u8> = Vec::new();
        {
            let mut w = SetBuilder::new(&mut buf).unwrap();
            for k in KEYS.iter() {
                w.insert(k).unwrap();
            }
            w.finish().unwrap();
        }
        let reopened = Set::new(buf).unwrap();

        assert_eq!(
            one_shot.as_fst().as_bytes(),
            memory_built.as_fst().as_bytes()
        );
        assert_eq!(one_shot.as_fst().as_bytes(), reopened.as_fst().as_bytes());
        assert_eq!(one_shot.len(), 6);
    }

    #[test]
    fn generated_all_map_paths_identical_images() {
        let pairs: Vec<(&str, u64)> =
            vec![("dawn", 4), ("dusk", 19), ("noon", 12), ("night", 0)];
        let mut sorted = pairs.clone();
        sorted.sort();

        let one_shot = Map::from_iter(sorted.clone()).unwrap();

        let mut mem = MapBuilder::memory();
        for (k, v) in sorted.iter() {
            mem.insert(k, *v).unwrap();
        }
        let memory_built = mem.into_map();

        let mut w = MapBuilder::new(Vec::new()).unwrap();
        for (k, v) in sorted.iter() {
            w.insert(k, *v).unwrap();
        }
        let bytes = w.into_inner().unwrap();
        let reopened = Map::new(bytes).unwrap();

        assert_eq!(
            one_shot.as_fst().as_bytes(),
            memory_built.as_fst().as_bytes()
        );
        assert_eq!(one_shot.as_fst().as_bytes(), reopened.as_fst().as_bytes());
        for (k, v) in sorted.iter() {
            assert_eq!(reopened.get(k), Some(*v));
        }
    }

    #[test]
    fn generated_extend_iter_matches_manual_inserts() {
        let mut by_extend = SetBuilder::memory();
        by_extend.extend_iter(KEYS.iter()).unwrap();
        let extended = by_extend.into_set();

        let manual = Set::from_iter(KEYS.iter()).unwrap();
        assert_eq!(extended.as_fst().as_bytes(), manual.as_fst().as_bytes());
    }

    #[test]
    fn generated_extend_stream_copies_source_set() {
        let source = Set::from_iter(vec!["ferry", "sloop", "yawl"]).unwrap();
        let mut b = SetBuilder::memory();
        b.extend_stream(source.stream()).unwrap();
        let copy = b.into_set();
        assert_eq!(copy.len(), source.len());
        assert_eq!(
            copy.stream().into_strs().unwrap(),
            source.stream().into_strs().unwrap()
        );
        assert_eq!(copy.as_fst().as_bytes(), source.as_fst().as_bytes());
    }

    #[test]
    fn generated_map_extend_stream_carries_values() {
        let source = Map::from_iter(vec![("silt", 3u64), ("loess", 8), ("till", 0)])
            .unwrap_err();
        // "silt" > "loess": one-shot construction enforces order even before
        // any stream copying happens.
        match source {
            fst::Error::Fst(fst::raw::Error::OutOfOrder { .. }) => {}
            other => panic!("expected OutOfOrder, got {:?}", other),
        }

        let source = Map::from_iter(vec![("loess", 8u64), ("silt", 3), ("till", 0)]).unwrap();
        let mut b = MapBuilder::memory();
        b.extend_stream(source.stream()).unwrap();
        let copy = b.into_map();
        assert_eq!(copy.get("loess"), Some(8));
        assert_eq!(copy.get("silt"), Some(3));
        assert_eq!(copy.get("till"), Some(0));
        assert_eq!(copy.as_fst().as_bytes(), source.as_fst().as_bytes());
    }

    #[test]
    fn generated_mixed_insert_and_extend_equal_one_shot() {
        let mut b = SetBuilder::memory();
        b.insert("boron").unwrap();
        b.extend_iter(vec!["carbon", "helium"]).unwrap();
        b.insert("neon").unwrap();
        b.extend_iter(vec!["radon", "xenon"]).unwrap();
        let mixed = b.into_set();
        let one_shot = Set::from_iter(KEYS.iter()).unwrap();
        assert_eq!(mixed.as_fst().as_bytes(), one_shot.as_fst().as_bytes());
    }

    #[test]
    fn generated_finish_and_into_inner_same_image() {
        let build = |finish_in_place: bool| -> Vec<u8> {
            if finish_in_place {
                let mut buf: Vec<u8> = Vec::new();
                let mut b = SetBuilder::new(&mut buf).unwrap();
                b.insert("ait").unwrap();
                b.insert("eyot").unwrap();
                b.finish().unwrap();
                buf
            } else {
                let mut b = SetBuilder::new(Vec::new()).unwrap();
                b.insert("ait").unwrap();
                b.insert("eyot").unwrap();
                b.into_inner().unwrap()
            }
        };
        let via_finish = build(true);
        let via_into_inner = build(false);
        assert_eq!(via_finish, via_into_inner);
        let set = Set::new(via_finish).unwrap();
        assert_eq!(set.stream().into_strs().unwrap(), vec!["ait", "eyot"]);
    }
}
