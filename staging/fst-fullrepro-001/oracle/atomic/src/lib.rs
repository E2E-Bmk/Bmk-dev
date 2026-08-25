// Oracle atomic tests for the finite state transducer library task.
#![cfg(test)]
#![allow(clippy::all)]

use fst::automaton::{Str, Subsequence};
use fst::raw::{Builder as RawBuilder, Fst, Output};
use fst::{Automaton, IntoStreamer, Map, MapBuilder, Set, SetBuilder, Streamer};

// Fresh fixture vocabulary (not shared with any upstream test suite).
const MINERALS: [&str; 5] = ["basalt", "gneiss", "pumice", "quartz", "shale"];

fn set_keys(set: &Set<Vec<u8>>) -> Vec<String> {
    set.stream().into_strs().unwrap()
}

// ---------------------------------------------------------------------------
// Building transducers
// ---------------------------------------------------------------------------

#[test]
fn generated_set_from_iter_membership_and_len() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    assert_eq!(set.len(), 5);
    assert!(!set.is_empty());
    assert!(set.contains("pumice"));
    assert!(set.contains("basalt"));
    assert!(!set.contains("marble"));
    assert!(!set.contains(""));
}

#[test]
fn generated_map_from_iter_get_and_len() {
    let map = Map::from_iter(vec![("elm", 12u64), ("fir", 3), ("oak", 40)]).unwrap();
    assert_eq!(map.len(), 3);
    assert_eq!(map.get("fir"), Some(3));
    assert_eq!(map.get("oak"), Some(40));
    assert_eq!(map.get("ash"), None);
}

#[test]
fn generated_set_builder_memory_into_set() {
    let mut b = SetBuilder::memory();
    b.insert("delta").unwrap();
    b.insert("echo").unwrap();
    b.insert("foxtrot").unwrap();
    let set = b.into_set();
    assert_eq!(set.len(), 3);
    assert_eq!(set_keys(&set), vec!["delta", "echo", "foxtrot"]);
}

#[test]
fn generated_map_builder_memory_into_map() {
    let mut b = MapBuilder::memory();
    b.insert("north", 1u64).unwrap();
    b.insert("south", 2).unwrap();
    b.insert("west", 9).unwrap();
    let map = b.into_map();
    assert_eq!(map.len(), 3);
    assert_eq!(map.get("south"), Some(2));
    assert_eq!(map.get("west"), Some(9));
}

#[test]
fn generated_raw_builder_add_zero_outputs() {
    let mut b = RawBuilder::memory();
    b.add("iron").unwrap();
    b.add("zinc").unwrap();
    let fst = b.into_fst();
    assert_eq!(fst.len(), 2);
    assert_eq!(fst.get("iron"), Some(Output::zero()));
    assert_eq!(fst.get("zinc"), Some(Output::new(0)));
    assert_eq!(fst.get("lead"), None);
}

#[test]
fn generated_raw_builder_insert_values() {
    let mut b = RawBuilder::memory();
    b.insert("amber", 17u64).unwrap();
    b.insert("coral", 0).unwrap();
    b.insert("jade", 250).unwrap();
    let fst = b.into_fst();
    assert_eq!(fst.get("amber"), Some(Output::new(17)));
    assert_eq!(fst.get("coral"), Some(Output::new(0)));
    assert_eq!(fst.get("jade"), Some(Output::new(250)));
}

#[test]
fn generated_raw_from_iter_set_zero_values() {
    let fst = Fst::from_iter_set(vec!["ash", "beech", "cedar"]).unwrap();
    assert_eq!(fst.len(), 3);
    let mut stream = fst.stream();
    let mut items = vec![];
    while let Some((key, out)) = stream.next() {
        items.push((String::from_utf8(key.to_vec()).unwrap(), out.value()));
    }
    assert_eq!(
        items,
        vec![
            ("ash".to_string(), 0),
            ("beech".to_string(), 0),
            ("cedar".to_string(), 0)
        ]
    );
}

#[test]
fn generated_raw_from_iter_map_values() {
    let fst = Fst::from_iter_map(vec![("gale", 5u64), ("mist", 11), ("rain", 2)]).unwrap();
    assert_eq!(fst.get("gale"), Some(Output::new(5)));
    assert_eq!(fst.get("mist"), Some(Output::new(11)));
    assert_eq!(fst.get("rain"), Some(Output::new(2)));
    assert_eq!(fst.get("snow"), None);
}

#[test]
fn generated_set_builder_out_of_order_payload() {
    let mut b = SetBuilder::memory();
    b.insert("mango").unwrap();
    let err = b.insert("kiwi").unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::OutOfOrder { previous, got }) => {
            assert_eq!(previous, b"mango".to_vec());
            assert_eq!(got, b"kiwi".to_vec());
        }
        other => panic!("expected OutOfOrder, got {:?}", other),
    }
}

#[test]
fn generated_map_builder_duplicate_key_payload() {
    let mut b = MapBuilder::memory();
    b.insert("pond", 4u64).unwrap();
    let err = b.insert("pond", 8).unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::DuplicateKey { got }) => {
            assert_eq!(got, b"pond".to_vec());
        }
        other => panic!("expected DuplicateKey, got {:?}", other),
    }
}

#[test]
fn generated_set_builder_duplicate_is_noop() {
    let mut b = SetBuilder::memory();
    b.insert("reed").unwrap();
    assert!(b.insert("reed").is_ok());
    b.insert("sage").unwrap();
    let set = b.into_set();
    assert_eq!(set.len(), 2);
    assert_eq!(set_keys(&set), vec!["reed", "sage"]);
}

#[test]
fn generated_raw_builder_add_duplicate_noop_insert_errors() {
    let mut adds = RawBuilder::memory();
    adds.add("moss").unwrap();
    assert!(adds.add("moss").is_ok());
    let fst = adds.into_fst();
    assert_eq!(fst.len(), 1);

    let mut inserts = RawBuilder::memory();
    inserts.insert("moss", 1u64).unwrap();
    let err = inserts.insert("moss", 2).unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::DuplicateKey { got }) => {
            assert_eq!(got, b"moss".to_vec());
        }
        other => panic!("expected DuplicateKey, got {:?}", other),
    }
}

#[test]
fn generated_set_from_iter_duplicate_is_noop() {
    let set = Set::from_iter(vec!["dune", "dune", "peak"]).unwrap();
    assert_eq!(set.len(), 2);
    assert_eq!(set_keys(&set), vec!["dune", "peak"]);
}

#[test]
fn generated_map_from_iter_duplicate_errors() {
    let err = Map::from_iter(vec![("bay", 1u64), ("bay", 2)]).unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::DuplicateKey { got }) => {
            assert_eq!(got, b"bay".to_vec());
        }
        other => panic!("expected DuplicateKey, got {:?}", other),
    }
}

#[test]
fn generated_set_from_iter_out_of_order_errors() {
    let err = Set::from_iter(vec!["stone", "clay"]).unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::OutOfOrder { previous, got }) => {
            assert_eq!(previous, b"stone".to_vec());
            assert_eq!(got, b"clay".to_vec());
        }
        other => panic!("expected OutOfOrder, got {:?}", other),
    }
}

#[test]
fn generated_writer_backed_set_builder_finish_reopen() {
    let mut buf: Vec<u8> = Vec::new();
    {
        let mut b = SetBuilder::new(&mut buf).unwrap();
        b.insert("larch").unwrap();
        b.insert("rowan").unwrap();
        b.finish().unwrap();
    }
    let set = Set::new(buf).unwrap();
    assert_eq!(set.len(), 2);
    assert!(set.contains("larch"));
    assert!(set.contains("rowan"));
}

#[test]
fn generated_builder_bytes_written_grows() {
    let mut b = SetBuilder::new(Vec::new()).unwrap();
    let start = b.bytes_written();
    b.insert("aqueduct").unwrap();
    b.insert("basilica").unwrap();
    b.insert("colonnade").unwrap();
    b.insert("forum").unwrap();
    let later = b.bytes_written();
    assert!(later >= start);
    let written = b.into_inner().unwrap();
    assert!(written.len() as u64 >= later);
}

#[test]
fn generated_builder_get_ref_borrows_writer() {
    let mut b = SetBuilder::new(Vec::new()).unwrap();
    b.insert("heron").unwrap();
    b.insert("plover").unwrap();
    // get_ref observes the writer without finishing construction; whatever
    // has reached the writer so far is a prefix of the finished image.
    let mid: Vec<u8> = b.get_ref().clone();
    assert!(b.bytes_written() >= mid.len() as u64);
    let full = b.into_inner().unwrap();
    assert!(full.starts_with(&mid));
    assert!(full.len() > mid.len() || !mid.is_empty());
    let set = Set::new(full).unwrap();
    assert_eq!(set.len(), 2);
}

#[test]
fn generated_builder_into_inner_reopen() {
    let mut b = MapBuilder::new(Vec::new()).unwrap();
    b.insert("cove", 31u64).unwrap();
    b.insert("reef", 7).unwrap();
    let bytes = b.into_inner().unwrap();
    let map = Map::new(bytes).unwrap();
    assert_eq!(map.get("cove"), Some(31));
    assert_eq!(map.get("reef"), Some(7));
}

#[test]
fn generated_set_extend_iter() {
    let mut b = SetBuilder::memory();
    b.extend_iter(vec!["alpha", "beta", "gamma"]).unwrap();
    let set = b.into_set();
    assert_eq!(set_keys(&set), vec!["alpha", "beta", "gamma"]);
}

#[test]
fn generated_map_builder_writer_finish_reopen() {
    let mut buf: Vec<u8> = Vec::new();
    {
        let mut b = MapBuilder::new(&mut buf).unwrap();
        b.insert("dell", 100u64).unwrap();
        b.insert("glen", 200).unwrap();
        b.finish().unwrap();
    }
    let map = Map::new(buf).unwrap();
    assert_eq!(map.len(), 2);
    assert_eq!(map.get("dell"), Some(100));
    assert_eq!(map.get("glen"), Some(200));
}

#[test]
fn generated_open_garbage_bytes_format_error() {
    let garbage = vec![9u8, 8, 7, 6, 5, 4, 3];
    let err = Set::new(garbage).unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::Format { size }) => assert_eq!(size, 7),
        other => panic!("expected Format, got {:?}", other),
    }
}

#[test]
fn generated_empty_builder_yields_empty_container() {
    let set = SetBuilder::memory().into_set();
    assert_eq!(set.len(), 0);
    assert!(set.is_empty());
    assert!(!set.contains("anything"));
    assert!(!set.contains(""));
    let mut stream = set.stream();
    assert!(stream.next().is_none());

    let map = MapBuilder::memory().into_map();
    assert!(map.is_empty());
    assert_eq!(map.get(""), None);
}

// ---------------------------------------------------------------------------
// Querying containers
// ---------------------------------------------------------------------------

#[test]
fn generated_set_contains_bytes_and_strs() {
    let set = Set::from_iter(vec![b"ab".to_vec(), b"cd".to_vec()]).unwrap();
    assert!(set.contains("ab"));
    assert!(set.contains(b"cd"));
    assert!(set.contains(b"cd".to_vec()));
    assert!(!set.contains("abc"));
    assert!(!set.contains("a"));
}

#[test]
fn generated_map_get_zero_value_distinct_from_absent() {
    let map = Map::from_iter(vec![("hollow", 0u64), ("ridge", 6)]).unwrap();
    assert_eq!(map.get("hollow"), Some(0));
    assert_eq!(map.get("ridge"), Some(6));
    assert_eq!(map.get("crest"), None);
    assert!(map.contains_key("hollow"));
    assert!(!map.contains_key("crest"));
}

#[test]
fn generated_raw_contains_key() {
    let fst = Fst::from_iter_map(vec![("ore", 44u64)]).unwrap();
    assert!(fst.contains_key("ore"));
    assert!(!fst.contains_key("or"));
    assert!(!fst.contains_key("orebody"));
}

#[test]
fn generated_len_and_is_empty_all_containers() {
    let set = Set::from_iter(vec!["one"]).unwrap();
    let map = Map::from_iter(vec![("one", 1u64)]).unwrap();
    let fst = Fst::from_iter_set(vec!["one"]).unwrap();
    assert_eq!((set.len(), map.len(), fst.len()), (1, 1, 1));
    assert!(!set.is_empty() && !map.is_empty() && !fst.is_empty());

    let empty = Set::from_iter(Vec::<&str>::new()).unwrap();
    assert_eq!(empty.len(), 0);
    assert!(empty.is_empty());
}

#[test]
fn generated_raw_size_equals_image_len() {
    let fst = Fst::from_iter_set(vec!["arc", "bow"]).unwrap();
    assert_eq!(fst.size(), fst.as_bytes().len());
    assert!(fst.size() > 0);
}

#[test]
fn generated_output_new_zero_value_is_zero() {
    assert_eq!(Output::zero(), Output::new(0));
    assert!(Output::zero().is_zero());
    assert!(!Output::new(3).is_zero());
    assert_eq!(Output::new(58).value(), 58);
}

#[test]
fn generated_output_cat_sums() {
    assert_eq!(Output::new(19).cat(Output::new(23)), Output::new(42));
    assert_eq!(Output::new(7).cat(Output::zero()), Output::new(7));
}

#[test]
fn generated_output_prefix_minimum() {
    assert_eq!(Output::new(31).prefix(Output::new(8)), Output::new(8));
    assert_eq!(Output::new(4).prefix(Output::new(12)), Output::new(4));
    assert_eq!(Output::zero().prefix(Output::new(5)), Output::zero());
}

#[test]
fn generated_output_sub_difference() {
    assert_eq!(Output::new(50).sub(Output::new(20)), Output::new(30));
    assert_eq!(Output::new(9).sub(Output::new(9)), Output::zero());
    assert_eq!(Output::new(9).sub(Output::zero()), Output::new(9));
}

#[test]
fn generated_output_sub_underflow_panics() {
    // Positive direction first, then the panic contract on underflow.
    assert_eq!(Output::new(3).sub(Output::new(2)), Output::new(1));
    let outcome = std::panic::catch_unwind(|| Output::new(2).sub(Output::new(3)));
    assert!(outcome.is_err());
}

#[test]
fn generated_raw_get_key_monotonic_lookup() {
    let fst = Fst::from_iter_map(vec![("ant", 3u64), ("bee", 7), ("cow", 12)]).unwrap();
    assert_eq!(fst.get_key(3), Some(b"ant".to_vec()));
    assert_eq!(fst.get_key(7), Some(b"bee".to_vec()));
    assert_eq!(fst.get_key(12), Some(b"cow".to_vec()));
}

#[test]
fn generated_raw_get_key_absent_none() {
    let fst = Fst::from_iter_map(vec![("ant", 3u64), ("bee", 7)]).unwrap();
    assert_eq!(fst.get_key(5), None);
    assert_eq!(fst.get_key(100), None);
}

// ---------------------------------------------------------------------------
// Streaming and ranges
// ---------------------------------------------------------------------------

#[test]
fn generated_set_stream_ascending_order() {
    // Insertion helper sorts nothing: keys arrive pre-sorted, stream returns
    // the same ascending byte-lexicographic order.
    let set = Set::from_iter(vec!["Ash", "Zed", "ash", "zed"]).unwrap();
    assert_eq!(set_keys(&set), vec!["Ash", "Zed", "ash", "zed"]);
}

#[test]
fn generated_map_stream_pairs_in_key_order() {
    let map = Map::from_iter(vec![("brook", 30u64), ("creek", 10), ("river", 20)]).unwrap();
    let mut stream = map.stream();
    let mut pairs = vec![];
    while let Some((key, value)) = stream.next() {
        pairs.push((String::from_utf8(key.to_vec()).unwrap(), value));
    }
    assert_eq!(
        pairs,
        vec![
            ("brook".to_string(), 30),
            ("creek".to_string(), 10),
            ("river".to_string(), 20)
        ]
    );
}

#[test]
fn generated_map_keys_projection() {
    let map = Map::from_iter(vec![("ebb", 9u64), ("flow", 1)]).unwrap();
    let mut keys = map.keys();
    let mut got = vec![];
    while let Some(key) = keys.next() {
        got.push(key.to_vec());
    }
    assert_eq!(got, vec![b"ebb".to_vec(), b"flow".to_vec()]);
}

#[test]
fn generated_map_values_projection() {
    let map = Map::from_iter(vec![("ebb", 9u64), ("flow", 1), ("tide", 88)]).unwrap();
    let mut values = map.values();
    let mut got = vec![];
    while let Some(v) = values.next() {
        got.push(v);
    }
    // Values arrive in key order, not sorted by value.
    assert_eq!(got, vec![9, 1, 88]);
}

#[test]
fn generated_set_into_strs_collects() {
    let set = Set::from_iter(vec!["lava", "tuff"]).unwrap();
    assert_eq!(
        set.stream().into_strs().unwrap(),
        vec!["lava".to_string(), "tuff".to_string()]
    );
}

#[test]
fn generated_set_into_bytes_collects() {
    let set = Set::from_iter(vec![vec![0x02u8, 0x01], vec![0x02, 0x02]]).unwrap();
    assert_eq!(
        set.stream().into_bytes(),
        vec![vec![0x02u8, 0x01], vec![0x02, 0x02]]
    );
}

#[test]
fn generated_set_into_strs_non_utf8_error() {
    let set = Set::from_iter(vec![vec![0x61u8], vec![0xFF, 0x01]]).unwrap();
    let err = set.stream().into_strs().unwrap_err();
    match err {
        fst::Error::Fst(fst::raw::Error::FromUtf8(_)) => {}
        other => panic!("expected FromUtf8, got {:?}", other),
    }
}

#[test]
fn generated_map_stream_collection_helpers() {
    let pairs = vec![("fen", 14u64), ("mire", 3)];
    let map = Map::from_iter(pairs.clone()).unwrap();
    assert_eq!(
        map.stream().into_byte_vec(),
        vec![(b"fen".to_vec(), 14u64), (b"mire".to_vec(), 3)]
    );
    assert_eq!(
        map.stream().into_str_vec().unwrap(),
        vec![("fen".to_string(), 14u64), ("mire".to_string(), 3)]
    );
    assert_eq!(
        map.stream().into_str_keys().unwrap(),
        vec!["fen".to_string(), "mire".to_string()]
    );
    assert_eq!(
        map.stream().into_byte_keys(),
        vec![b"fen".to_vec(), b"mire".to_vec()]
    );
    assert_eq!(map.stream().into_values(), vec![14u64, 3]);
}

#[test]
fn generated_map_str_helpers_non_utf8_error() {
    let map = Map::from_iter(vec![(vec![0x64u8], 1u64), (vec![0xFE, 0x02], 2)]).unwrap();
    assert!(matches!(
        map.stream().into_str_vec(),
        Err(fst::Error::Fst(fst::raw::Error::FromUtf8(_)))
    ));
    assert!(matches!(
        map.stream().into_str_keys(),
        Err(fst::Error::Fst(fst::raw::Error::FromUtf8(_)))
    ));
    // Byte-level helpers still succeed on the same map.
    assert_eq!(map.stream().into_values(), vec![1u64, 2]);
}

#[test]
fn generated_stream_next_none_at_exhaustion() {
    let set = Set::from_iter(vec!["only"]).unwrap();
    let mut stream = set.stream();
    assert_eq!(stream.next(), Some(&b"only"[..]));
    assert!(stream.next().is_none());
    assert!(stream.next().is_none());
}

#[test]
fn generated_ref_container_into_stream() {
    let set = Set::from_iter(vec!["ivy", "oak"]).unwrap();
    let mut stream = (&set).into_stream();
    let mut got = vec![];
    while let Some(key) = stream.next() {
        got.push(key.to_vec());
    }
    assert_eq!(got, vec![b"ivy".to_vec(), b"oak".to_vec()]);
}

#[test]
fn generated_range_ge_le_inclusive() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let got = set
        .range()
        .ge("gneiss")
        .le("quartz")
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(got, vec!["gneiss", "pumice", "quartz"]);
}

#[test]
fn generated_range_gt_lt_exclusive() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let got = set
        .range()
        .gt("basalt")
        .lt("quartz")
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(got, vec!["gneiss", "pumice"]);
}

#[test]
fn generated_range_unbounded_equals_full_stream() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let ranged = set.range().into_stream().into_strs().unwrap();
    assert_eq!(ranged, set_keys(&set));
}

#[test]
fn generated_range_empty_selection() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let mut stream = set.range().gt("shale").into_stream();
    assert!(stream.next().is_none());
    let none = set
        .range()
        .ge("m")
        .lt("m")
        .into_stream()
        .into_strs()
        .unwrap();
    assert!(none.is_empty());
}

#[test]
fn generated_range_bound_replacement_last_wins() {
    let set = Set::from_iter(vec!["a", "b", "c", "d", "e"]).unwrap();
    // The second ge replaces the first.
    let got = set
        .range()
        .ge("a")
        .ge("c")
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(got, vec!["c", "d", "e"]);
    // Replacement also loosens: last call wins even when wider.
    let wide = set
        .range()
        .lt("b")
        .lt("e")
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(wide, vec!["a", "b", "c", "d"]);
}

#[test]
fn generated_map_range_carries_values() {
    let map = Map::from_iter(vec![("apse", 4u64), ("nave", 9), ("spire", 61)]).unwrap();
    let mut stream = map.range().ge("nave").into_stream();
    let mut got = vec![];
    while let Some((key, value)) = stream.next() {
        got.push((String::from_utf8(key.to_vec()).unwrap(), value));
    }
    assert_eq!(got, vec![("nave".to_string(), 9), ("spire".to_string(), 61)]);
}

// ---------------------------------------------------------------------------
// Automaton search
// ---------------------------------------------------------------------------

#[test]
fn generated_str_matches_exactly_one_key() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let hits = set
        .search(Str::new("pumice"))
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(hits, vec!["pumice"]);
    let miss = set
        .search(Str::new("pumic"))
        .into_stream()
        .into_strs()
        .unwrap();
    assert!(miss.is_empty());
}

#[test]
fn generated_str_empty_matches_only_empty_key() {
    let without = Set::from_iter(vec!["x"]).unwrap();
    assert!(without
        .search(Str::new(""))
        .into_stream()
        .into_strs()
        .unwrap()
        .is_empty());
    let with = Set::from_iter(vec!["", "x"]).unwrap();
    assert_eq!(
        with.search(Str::new("")).into_stream().into_strs().unwrap(),
        vec![""]
    );
}

#[test]
fn generated_subsequence_gaps_allowed() {
    let set = Set::from_iter(vec!["carton", "craton", "crouton", "torc"]).unwrap();
    // 'c','r','t' in order with gaps; "torc" has no 'r' after its 'c'.
    let hits = set
        .search(Subsequence::new("crt"))
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(hits, vec!["carton", "craton", "crouton"]);
}

#[test]
fn generated_subsequence_empty_matches_every_key() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let hits = set
        .search(Subsequence::new(""))
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(hits, set_keys(&set));
}

#[test]
fn generated_always_match_yields_all() {
    let set = Set::from_iter(vec!["ash", "elm"]).unwrap();
    let hits = set
        .search(fst::automaton::AlwaysMatch)
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(hits, vec!["ash", "elm"]);
}

#[test]
fn generated_starts_with_prefix_filter() {
    let set = Set::from_iter(vec!["lime", "limestone", "limit", "loam"]).unwrap();
    let hits = set
        .search(Str::new("lime").starts_with())
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(hits, vec!["lime", "limestone"]);
}

#[test]
fn generated_complement_inverts() {
    let set = Set::from_iter(MINERALS.iter()).unwrap();
    let hits = set
        .search(Str::new("gneiss").complement())
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(hits, vec!["basalt", "pumice", "quartz", "shale"]);
}

#[test]
fn generated_intersection_union_combinators() {
    let set = Set::from_iter(vec!["flint", "granite", "gravel"]).unwrap();
    let both = set
        .search(Subsequence::new("gr").intersection(Subsequence::new("vl")))
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(both, vec!["gravel"]);
    let either = set
        .search(Str::new("flint").union(Str::new("gravel")))
        .into_stream()
        .into_strs()
        .unwrap();
    assert_eq!(either, vec!["flint", "gravel"]);
}

/// A caller-defined automaton exercising the trait contract with the
/// default `can_match`/`will_always_match` implementations: accepts keys
/// of even byte length.
struct EvenLength;

impl Automaton for EvenLength {
    type State = usize;

    fn start(&self) -> usize {
        0
    }

    fn is_match(&self, state: &usize) -> bool {
        state % 2 == 0
    }

    fn accept(&self, state: &usize, _byte: u8) -> usize {
        state + 1
    }
}

#[test]
fn generated_custom_automaton_even_length() {
    let set = Set::from_iter(vec!["at", "atoll", "atom", "bayou", "reef"]).unwrap();
    let hits = set.search(EvenLength).into_stream().into_strs().unwrap();
    assert_eq!(hits, vec!["at", "atom", "reef"]);
}

// ---------------------------------------------------------------------------
// Set operations (single-builder edge)
// ---------------------------------------------------------------------------

#[test]
fn generated_empty_op_builder_union_empty() {
    let mut union = fst::set::OpBuilder::new().union();
    assert!(union.next().is_none());
}

// ---------------------------------------------------------------------------
// Raw transducers and byte images
// ---------------------------------------------------------------------------

#[test]
fn generated_as_bytes_to_vec_agree() {
    let fst = Fst::from_iter_set(vec!["gorge", "mesa"]).unwrap();
    assert_eq!(fst.as_bytes().to_vec(), fst.to_vec());
    assert_eq!(fst.as_bytes().len(), fst.size());
}

#[test]
fn generated_raw_as_inner_into_inner() {
    let fst = Fst::from_iter_set(vec!["cairn"]).unwrap();
    let borrowed: &Vec<u8> = fst.as_inner();
    assert_eq!(borrowed.len(), fst.size());
    let owned = fst.into_inner();
    let reopened = Fst::new(owned).unwrap();
    assert!(reopened.contains_key("cairn"));
}

#[test]
fn generated_verify_ok_on_built_images() {
    let set = Set::from_iter(vec!["fjord", "sound"]).unwrap();
    assert!(set.as_fst().verify().is_ok());
    let empty = SetBuilder::memory().into_set();
    assert!(empty.as_fst().verify().is_ok());
}

// ---------------------------------------------------------------------------
// Error semantics
// ---------------------------------------------------------------------------

#[test]
fn generated_error_display_and_source() {
    let err = Set::from_iter(vec!["b", "a"]).unwrap_err();
    // Display renders a non-empty message; source() reaches the wrapped
    // domain error through the std trait.
    assert!(!format!("{}", err).is_empty());
    assert!(!format!("{:?}", err).is_empty());
    let dyn_err: &dyn std::error::Error = &err;
    assert!(dyn_err.source().is_some());
}

#[test]
fn generated_error_from_io_variant() {
    let io_err = std::io::Error::new(std::io::ErrorKind::Other, "sink closed");
    let err: fst::Error = fst::Error::from(io_err);
    match err {
        fst::Error::Io(_) => {}
        other => panic!("expected Io variant, got {:?}", other),
    }
    let raw_err = fst::raw::Error::ChecksumMissing;
    let err: fst::Error = fst::Error::from(raw_err);
    match err {
        fst::Error::Fst(fst::raw::Error::ChecksumMissing) => {}
        other => panic!("expected Fst(ChecksumMissing), got {:?}", other),
    }
}

#[test]
fn generated_result_alias_round_trip() {
    fn build(keys: &[&str]) -> fst::Result<Set<Vec<u8>>> {
        Set::from_iter(keys.iter())
    }
    assert!(build(&["k1", "k2"]).is_ok());
    assert!(build(&["k2", "k1"]).is_err());
}
