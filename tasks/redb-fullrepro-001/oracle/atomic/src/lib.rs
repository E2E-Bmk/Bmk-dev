use redb::{
    Database, Entry, Error, MultimapTableDefinition, ReadableDatabase, ReadableMultimapTable,
    ReadableTable, ReadableTableMetadata, StorageError, TableDefinition, TableError,
};

const U64: TableDefinition<u64, u64> = TableDefinition::new("u64");
const STR: TableDefinition<&str, &str> = TableDefinition::new("str");
const MM: MultimapTableDefinition<&str, &str> = MultimapTableDefinition::new("mm");

fn db() -> Result<(tempfile::NamedTempFile, Database), Error> {
    let file = tempfile::NamedTempFile::new().unwrap();
    let db = Database::create(file.path())?;
    Ok((file, db))
}

#[test]
fn table_insert_returns_old_value_for_existing_key() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    table.insert(1, &10)?;
    assert_eq!(table.insert(1, &20)?.unwrap().value(), 10);
    Ok(())
}

#[test]
fn table_remove_returns_removed_value_once() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    table.insert(1, &10)?;
    assert_eq!(table.remove(1)?.unwrap().value(), 10);
    assert!(table.remove(1)?.is_none());
    Ok(())
}

#[test]
fn table_first_last_follow_key_order() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(STR)?;
    table.insert("b", "2")?;
    table.insert("a", "1")?;
    table.insert("c", "3")?;
    assert_eq!(table.first()?.unwrap().0.value(), "a");
    assert_eq!(table.last()?.unwrap().0.value(), "c");
    Ok(())
}

#[test]
fn table_range_respects_exclusive_upper_bound() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in 0..5 {
        table.insert(i, &(i * 10))?;
    }
    let keys: std::result::Result<Vec<_>, redb::StorageError> =
        table.range(1..4)?.map(|r| Ok(r?.0.value())).collect();
    assert_eq!(keys?, vec![1, 2, 3]);
    Ok(())
}

#[test]
fn table_iter_is_double_ended() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in 0..3 {
        table.insert(i, &i)?;
    }
    let mut iter = table.iter()?;
    assert_eq!(iter.next().unwrap()?.0.value(), 0);
    assert_eq!(iter.next_back().unwrap()?.0.value(), 2);
    assert_eq!(iter.next().unwrap()?.0.value(), 1);
    assert!(iter.next().is_none());
    Ok(())
}

#[test]
fn retain_keeps_true_entries() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in 0..6 {
        table.insert(i, &i)?;
    }
    table.retain(|k, _| k % 2 == 0)?;
    let keys: std::result::Result<Vec<_>, redb::StorageError> =
        table.iter()?.map(|r| Ok(r?.0.value())).collect();
    assert_eq!(keys?, vec![0, 2, 4]);
    Ok(())
}

#[test]
fn extract_if_removes_yielded_entries() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in 0..4 {
        table.insert(i, &i)?;
    }
    let removed: std::result::Result<Vec<_>, redb::StorageError> =
        table.extract_if(|k, _| k >= 2)?.map(|r| Ok(r?.0.value())).collect();
    assert_eq!(removed?, vec![2, 3]);
    assert_eq!(table.len()?, 2);
    Ok(())
}

#[test]
fn entry_or_insert_uses_vacant_then_occupied_path() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    assert_eq!(table.entry(1)?.or_insert(&10)?.value(), 10);
    match table.entry(1)? {
        Entry::Occupied(e) => assert_eq!(e.get()?.value(), 10),
        Entry::Vacant(_) => panic!("expected occupied"),
    }
    Ok(())
}

#[test]
fn entry_and_modify_changes_existing_value() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    table.insert(1, &10)?;
    table.entry(1)?.and_modify(|v| v.insert(v.value() + 5))?;
    assert_eq!(table.get(1)?.unwrap().value(), 15);
    Ok(())
}

#[test]
fn missing_read_table_is_table_does_not_exist() -> Result<(), Error> {
    let (_file, db) = db()?;
    let read = db.begin_read()?;
    assert!(matches!(read.open_table(U64), Err(TableError::TableDoesNotExist(_))));
    Ok(())
}

#[test]
fn opening_multimap_as_regular_errors() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    tx.open_multimap_table(MM)?;
    assert!(matches!(
        tx.open_table(TableDefinition::<&str, &str>::new("mm")),
        Err(TableError::TableIsMultimap(_))
    ));
    Ok(())
}

#[test]
fn value_too_large_is_rejected() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(TableDefinition::<u64, &[u8]>::new("big"))?;
    let value = vec![0u8; 3 * 1024 * 1024 * 1024usize + 1];
    assert!(matches!(table.insert(1, value.as_slice()), Err(StorageError::ValueTooLarge(_))));
    Ok(())
}

#[test]
fn multimap_insert_returns_false_then_true_for_duplicate() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    assert!(!table.insert("a", "x")?);
    assert!(table.insert("a", "x")?);
    Ok(())
}

#[test]
fn multimap_get_values_are_ordered() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    table.insert("a", "c")?;
    table.insert("a", "a")?;
    table.insert("a", "b")?;
    let values: std::result::Result<Vec<_>, redb::StorageError> =
        table.get("a")?.map(|v| Ok(v?.value().to_string())).collect();
    assert_eq!(values?, vec!["a", "b", "c"]);
    Ok(())
}

#[test]
fn multimap_remove_returns_presence() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    table.insert("a", "x")?;
    assert!(table.remove("a", "x")?);
    assert!(!table.remove("a", "x")?);
    Ok(())
}

#[test]
fn multimap_remove_all_returns_ordered_values() -> Result<(), Error> {
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    table.insert("a", "b")?;
    table.insert("a", "a")?;
    let values: std::result::Result<Vec<_>, redb::StorageError> =
        table.remove_all("a")?.map(|v| Ok(v?.value().to_string())).collect();
    assert_eq!(values?, vec!["a", "b"]);
    assert_eq!(table.get("a")?.len(), 0);
    Ok(())
}

#[test]
fn table_len_and_is_empty_track_insert_remove() -> Result<(), Error> {
    // Verifies: REDB-TAB-004, REDB-TAB-005
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    assert!(table.is_empty()?);
    table.insert(1, &10)?;
    table.insert(2, &20)?;
    assert_eq!(table.len()?, 2);
    table.remove(1)?;
    assert_eq!(table.len()?, 1);
    assert!(!table.is_empty()?);
    Ok(())
}

#[test]
fn table_range_inclusive_bounds_include_endpoints() -> Result<(), Error> {
    // Verifies: REDB-TAB-006, REDB-TAB-007
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in 1..=5 {
        table.insert(i, &(i * 2))?;
    }
    let keys: std::result::Result<Vec<_>, redb::StorageError> =
        table.range(2..=4)?.map(|r| Ok(r?.0.value())).collect();
    assert_eq!(keys?, vec![2, 3, 4]);
    Ok(())
}

#[test]
fn table_range_unbounded_prefix_is_ordered() -> Result<(), Error> {
    // Verifies: REDB-TAB-006, REDB-TAB-007
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in [4, 1, 3, 2] {
        table.insert(i, &i)?;
    }
    let keys: std::result::Result<Vec<_>, redb::StorageError> =
        table.range(..3)?.map(|r| Ok(r?.0.value())).collect();
    assert_eq!(keys?, vec![1, 2]);
    Ok(())
}

#[test]
fn table_pop_first_and_last_remove_extremes() -> Result<(), Error> {
    // Verifies: REDB-TAB-005, REDB-TAB-006
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in [2, 1, 3] {
        table.insert(i, &(i * 10))?;
    }
    assert_eq!(table.pop_first()?.unwrap().0.value(), 1);
    assert_eq!(table.pop_last()?.unwrap().0.value(), 3);
    assert_eq!(table.first()?.unwrap().0.value(), 2);
    Ok(())
}

#[test]
fn occupied_entry_insert_returns_previous_value() -> Result<(), Error> {
    // Verifies: REDB-TAB-004
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    table.insert(9, &90)?;
    match table.entry(9)? {
        Entry::Occupied(mut occupied) => {
            assert_eq!(occupied.insert(&99)?.value(), 90);
            assert_eq!(occupied.get()?.value(), 99);
        }
        Entry::Vacant(_) => panic!("expected occupied"),
    }
    Ok(())
}

#[test]
fn occupied_entry_remove_entry_returns_key_and_value() -> Result<(), Error> {
    // Verifies: REDB-TAB-005
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    table.insert(3, &30)?;
    match table.entry(3)? {
        Entry::Occupied(occupied) => {
            let (key, value) = occupied.remove_entry()?;
            assert_eq!(key, 3);
            assert_eq!(value.value(), 30);
        }
        Entry::Vacant(_) => panic!("expected occupied"),
    }
    assert!(table.get(3)?.is_none());
    Ok(())
}

#[test]
fn vacant_entry_exposes_key_before_insert() -> Result<(), Error> {
    // Verifies: REDB-TAB-004
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    match table.entry(44)? {
        Entry::Vacant(vacant) => {
            assert_eq!(*vacant.key(), 44);
            assert_eq!(vacant.insert(&440)?.value(), 440);
        }
        Entry::Occupied(_) => panic!("expected vacant"),
    }
    assert_eq!(table.get(44)?.unwrap().value(), 440);
    Ok(())
}

#[test]
fn entry_or_insert_with_key_uses_requested_key() -> Result<(), Error> {
    // Verifies: REDB-TAB-004
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    let guard = table.entry(5)?.or_insert_with_key(|key| key * 11)?;
    assert_eq!(guard.value(), 55);
    Ok(())
}

#[test]
fn opening_regular_as_multimap_errors() -> Result<(), Error> {
    // Verifies: REDB-TAB-001, REDB-MM-001
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    tx.open_table(TableDefinition::<&str, &str>::new("plain"))?;
    assert!(matches!(
        tx.open_multimap_table(MultimapTableDefinition::<&str, &str>::new("plain")),
        Err(TableError::TableIsNotMultimap(_))
    ));
    Ok(())
}

#[test]
fn opening_existing_table_with_different_value_type_errors() -> Result<(), Error> {
    // Verifies: REDB-TYP-003
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    tx.open_table(TableDefinition::<u64, u64>::new("typed"))?;
    assert!(matches!(
        tx.open_table(TableDefinition::<u64, &str>::new("typed")),
        Err(TableError::TableTypeMismatch { .. }) | Err(TableError::TypeDefinitionChanged { .. })
    ));
    Ok(())
}

#[test]
fn multimap_len_counts_pairs_not_keys() -> Result<(), Error> {
    // Verifies: REDB-MM-002, REDB-MM-004
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    table.insert("a", "x")?;
    table.insert("a", "y")?;
    table.insert("b", "z")?;
    assert_eq!(table.len()?, 3);
    Ok(())
}

#[test]
fn multimap_iter_orders_keys_and_values() -> Result<(), Error> {
    // Verifies: REDB-MM-004
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    table.insert("b", "2")?;
    table.insert("a", "3")?;
    table.insert("a", "1")?;
    let rows: std::result::Result<Vec<_>, redb::StorageError> = table
        .iter()?
        .map(|row| {
            let (key, values) = row?;
            let values: std::result::Result<Vec<_>, redb::StorageError> =
                values.map(|v| Ok(v?.value().to_string())).collect();
            Ok((key.value().to_string(), values?))
        })
        .collect();
    assert_eq!(rows?, vec![("a".to_string(), vec!["1".to_string(), "3".to_string()]), ("b".to_string(), vec!["2".to_string()])]);
    Ok(())
}

#[test]
fn multimap_range_is_double_ended() -> Result<(), Error> {
    // Verifies: REDB-MM-004
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    for key in ["a", "b", "c"] {
        table.insert(key, "v")?;
    }
    let mut range = table.range("a".."d")?;
    assert_eq!(range.next().unwrap()?.0.value(), "a");
    assert_eq!(range.next_back().unwrap()?.0.value(), "c");
    assert_eq!(range.next().unwrap()?.0.value(), "b");
    assert!(range.next().is_none());
    Ok(())
}

#[test]
fn multimap_remove_all_missing_key_is_empty() -> Result<(), Error> {
    // Verifies: REDB-MM-005
    let (_file, db) = db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_multimap_table(MM)?;
    table.insert("a", "x")?;
    let removed = table.remove_all("missing")?;
    assert_eq!(removed.len(), 0);
    assert!(removed.is_empty());
    drop(removed);
    assert_eq!(table.len()?, 1);
    Ok(())
}

#[test]
fn u64_value_round_trips_through_public_encoding() {
    // Verifies: REDB-TYP-001
    let encoded = <u64 as redb::Value>::as_bytes(&513);
    assert_eq!(<u64 as redb::Value>::from_bytes(encoded.as_ref()), 513);
}
