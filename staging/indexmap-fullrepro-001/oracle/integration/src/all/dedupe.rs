// Set-pipeline workflows: streaming dedup, ordered tag algebra,
// recency reordering, and roster merges under the identity laws.

#[test]
fn generated_event_stream_dedup() {
    let stream = [3, 7, 3, 1, 7, 9, 1];
    let mut seen: IndexSet<i32> = IndexSet::new();
    let mut fresh = Vec::new();
    for e in stream {
        if seen.insert(e) {
            fresh.push(e);
        }
    }
    // first occurrences, in arrival order
    assert_eq!(fresh, [3, 7, 1, 9]);
    assert_eq!(seen.iter().collect::<Vec<_>>(), [&3, &7, &1, &9]);

    // process the oldest two as a batch
    let batch: Vec<_> = seen.drain(0..2).collect();
    assert_eq!(batch, [3, 7]);
    assert_eq!(seen.iter().collect::<Vec<_>>(), [&1, &9]);

    // take the newest off the back
    assert_eq!(seen.pop(), Some(9));
    assert_eq!(seen.len(), 1);
    assert!(seen.contains(&1));
}

#[test]
fn generated_tag_algebra_report() {
    let doc1: IndexSet<&str> = ["rust", "maps", "order"].into_iter().collect();
    let doc2: IndexSet<&str> = ["order", "hash", "rust"].into_iter().collect();

    let shared: Vec<_> = doc1.intersection(&doc2).copied().collect();
    assert_eq!(shared, ["rust", "order"]); // doc1's order
    let only1: Vec<_> = doc1.difference(&doc2).copied().collect();
    assert_eq!(only1, ["maps"]);

    let all: IndexSet<&str> = &doc1 | &doc2;
    assert_eq!(
        all.iter().collect::<Vec<_>>(),
        [&"rust", &"maps", &"order", &"hash"]
    );
    let exclusive: IndexSet<&str> = &doc1 ^ &doc2;
    assert_eq!(exclusive.iter().collect::<Vec<_>>(), [&"maps", &"hash"]);

    let shared_set: IndexSet<&str> = shared.into_iter().collect();
    assert!(shared_set.is_subset(&doc1));
    assert!(doc1.is_superset(&shared_set));
    assert!(!doc1.is_disjoint(&doc2));

    // operators agree with the collected lazy iterators, order included
    let collected: IndexSet<&str> = doc1.union(&doc2).copied().collect();
    assert_eq!(all, collected);
    assert_eq!(all.as_slice(), collected.as_slice());
}

#[test]
fn generated_lru_like_promotion() {
    let mut lru: IndexSet<&str> = ["a", "b", "c"].into_iter().collect();

    // hit "a": promote to the most-recent end
    let i = lru.get_index_of("a").unwrap();
    lru.move_index(i, lru.len() - 1);
    assert_eq!(lru.iter().collect::<Vec<_>>(), [&"b", &"c", &"a"]);

    // new page arrives
    assert!(lru.insert("d"));
    assert_eq!(lru.iter().collect::<Vec<_>>(), [&"b", &"c", &"a", &"d"]);

    // hit "c": promote again
    let i = lru.get_index_of("c").unwrap();
    lru.move_index(i, lru.len() - 1);
    assert_eq!(lru.iter().collect::<Vec<_>>(), [&"b", &"a", &"d", &"c"]);

    // evict from the least-recent front, twice
    assert_eq!(lru.shift_remove_index(0), Some("b"));
    assert_eq!(lru.shift_remove_index(0), Some("a"));
    assert_eq!(lru.iter().collect::<Vec<_>>(), [&"d", &"c"]);
    assert!(lru.contains("c"));
}

#[test]
fn generated_roster_merge_with_identity() {
    let mut master: IndexSet<Ver> = [ver(1, 1), ver(2, 1)].into_iter().collect();
    let mut incoming: IndexSet<Ver> = [ver(2, 9), ver(3, 9)].into_iter().collect();

    // append: the duplicate id keeps the ORIGINAL instance and position
    master.append(&mut incoming);
    assert!(incoming.is_empty());
    assert_eq!(master.len(), 3);
    assert_eq!(master.get(&ver(2, 0)).unwrap().tag, 1);
    assert_eq!(master.get_index_of(&ver(3, 0)), Some(2));

    // explicit upgrade with replace: the new instance wins, in place
    let old = master.replace(ver(2, 9)).unwrap();
    assert_eq!(old.tag, 1);
    assert_eq!(master.get(&ver(2, 0)).unwrap().tag, 9);
    assert_eq!(master.get_index_of(&ver(2, 0)), Some(1));

    // retire id 1 preserving roster order
    assert!(master.shift_remove(&ver(1, 0)));
    assert_eq!(master.get_index_of(&ver(2, 0)), Some(0));
    assert_eq!(master.get_index_of(&ver(3, 0)), Some(1));
}
