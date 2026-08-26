// Entry-driven aggregation workflows: frequency counting, grouping,
// and index bookkeeping under the two removal laws.

#[test]
fn generated_word_frequency_pipeline() {
    let text = ["the", "cat", "sat", "on", "the", "mat", "the", "cat"];
    let mut counts: IndexMap<&str, i32> = IndexMap::new();
    for w in text {
        *counts.entry(w).or_insert(0) += 1;
    }
    // first-seen order survives counting
    assert_eq!(
        counts.keys().collect::<Vec<_>>(),
        [&"the", &"cat", &"sat", &"on", &"mat"]
    );
    assert_eq!(counts["the"], 3);
    assert_eq!(counts["cat"], 2);

    // stable sort by count descending: ties keep first-seen order
    counts.sort_by(|_, a, _, b| b.cmp(a));
    assert_eq!(
        counts.keys().collect::<Vec<_>>(),
        [&"the", &"cat", &"sat", &"on", &"mat"]
    );

    // top-2 report and tail view
    let mut top = counts.clone();
    top.truncate(2);
    assert_eq!(top.keys().collect::<Vec<_>>(), [&"the", &"cat"]);
    let tail = counts.get_range(2..5).unwrap();
    assert_eq!(tail.keys().collect::<Vec<_>>(), [&"sat", &"on", &"mat"]);
    assert_eq!(tail.values().copied().sum::<i32>(), 3);
}

#[test]
fn generated_grouping_with_or_default() {
    let items = [
        ("fruit", "apple"),
        ("veg", "leek"),
        ("fruit", "pear"),
        ("grain", "rye"),
        ("veg", "kale"),
    ];
    let mut groups: IndexMap<&str, Vec<&str>> = IndexMap::new();
    for (g, item) in items {
        groups.entry(g).or_default().push(item);
    }
    assert_eq!(
        groups.keys().collect::<Vec<_>>(),
        [&"fruit", &"veg", &"grain"]
    );
    assert_eq!(groups["fruit"], ["apple", "pear"]);
    assert_eq!(groups["veg"], ["leek", "kale"]);

    // and_modify only touches existing groups
    groups.entry("fruit").and_modify(|v| v.push("fig")).or_default();
    groups.entry("dairy").and_modify(|v| v.push("x")).or_default();
    assert_eq!(groups["fruit"].len(), 3);
    assert!(groups["dairy"].is_empty());
    assert_eq!(groups.first().unwrap().0, &"fruit");
    assert_eq!(groups.last().unwrap().0, &"dairy");
}

#[test]
fn generated_index_stability_ledger() {
    let mut ledger: IndexMap<&str, i32> = IndexMap::new();
    let (i_a, _) = ledger.insert_full("acct_a", 100);
    let (i_b, _) = ledger.insert_full("acct_b", 250);
    let (i_c, _) = ledger.insert_full("acct_c", 75);
    assert_eq!((i_a, i_b, i_c), (0, 1, 2));

    // updates never move an account
    assert_eq!(ledger.insert_full("acct_b", 300), (1, Some(250)));

    // swap removal moves exactly one other account
    ledger.insert("acct_d", 10);
    assert_eq!(ledger.swap_remove_full("acct_a"), Some((0, "acct_a", 100)));
    assert_eq!(ledger.get_index_of("acct_d"), Some(0));
    assert_eq!(ledger.get_index_of("acct_b"), Some(1));

    // shift removal keeps every survivor's relative order
    let mut ledger2: IndexMap<&str, i32> =
        [("p", 1), ("q", 2), ("r", 3), ("s", 4)].into_iter().collect();
    ledger2.shift_remove("q");
    assert_eq!(ledger2.get_index_of("p"), Some(0));
    assert_eq!(ledger2.get_index_of("r"), Some(1));
    assert_eq!(ledger2.get_index_of("s"), Some(2));
    for i in 0..ledger2.len() {
        let (k, _) = ledger2.get_index(i).unwrap();
        assert_eq!(ledger2.get_index_of(k), Some(i));
    }
}
