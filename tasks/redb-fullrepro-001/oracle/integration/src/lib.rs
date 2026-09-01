use redb::{
    CommitError, Database, Durability, Error, MultimapTableDefinition, ReadableDatabase,
    ReadableMultimapTable, ReadableTable, ReadableTableMetadata, TableDefinition,
    TableHandle, MultimapTableHandle,
};

const U64: TableDefinition<u64, u64> = TableDefinition::new("u64");
const STR: TableDefinition<&str, &str> = TableDefinition::new("str");
const MM: MultimapTableDefinition<&str, &str> = MultimapTableDefinition::new("mm");

fn file_db() -> Result<(tempfile::NamedTempFile, Database), Error> {
    let file = tempfile::NamedTempFile::new().unwrap();
    let db = Database::create(file.path())?;
    Ok((file, db))
}

#[test]
fn committed_value_survives_reopen() -> Result<(), Error> {
    let (file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(7, &70)?;
    tx.commit()?;
    drop(db);
    let reopened = Database::open(file.path())?;
    assert_eq!(reopened.begin_read()?.open_table(U64)?.get(7)?.unwrap().value(), 70);
    Ok(())
}

#[test]
fn abort_discards_created_table() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &1)?;
    tx.abort()?;
    assert!(db.begin_read()?.open_table(U64).is_err());
    Ok(())
}

#[test]
fn read_snapshot_ignores_later_commit() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let before = db.begin_read()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &1)?;
    tx.commit()?;
    assert!(before.open_table(U64).is_err());
    assert_eq!(db.begin_read()?.open_table(U64)?.get(1)?.unwrap().value(), 1);
    Ok(())
}

#[test]
fn rename_changes_listing_and_open_name() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(STR)?.insert("a", "b")?;
    tx.rename_table(STR, TableDefinition::<&str, &str>::new("renamed"))?;
    let names: Vec<_> = tx.list_tables()?.map(|h| h.name().to_string()).collect();
    assert_eq!(names, vec!["renamed"]);
    tx.commit()?;
    let read = db.begin_read()?;
    assert!(read.open_table(STR).is_err());
    assert_eq!(read.open_table(TableDefinition::<&str, &str>::new("renamed"))?.get("a")?.unwrap().value(), "b");
    Ok(())
}

#[test]
fn delete_removes_table_after_commit() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &1)?;
    assert!(tx.delete_table(U64)?);
    tx.commit()?;
    assert!(db.begin_read()?.open_table(U64).is_err());
    Ok(())
}

#[test]
fn persistent_savepoint_restores_table_state() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let mut tx = db.begin_write()?;
    let savepoint = tx.ephemeral_savepoint()?;
    tx.open_table(U64)?.insert(1, &1)?;
    tx.restore_savepoint(&savepoint)?;
    tx.commit()?;
    assert!(db.begin_read()?.open_table(U64).is_err());
    Ok(())
}

#[test]
fn persistent_savepoint_ids_are_listed_and_deleted() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    let id = tx.persistent_savepoint()?;
    assert_eq!(tx.list_persistent_savepoints()?.collect::<Vec<_>>(), vec![id]);
    assert!(tx.delete_persistent_savepoint(id)?);
    assert!(tx.list_persistent_savepoints()?.collect::<Vec<_>>().is_empty());
    Ok(())
}

#[test]
fn durability_none_commit_is_visible_before_reopen() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let mut tx = db.begin_write()?;
    tx.set_durability(Durability::None)?;
    tx.open_table(U64)?.insert(1, &1)?;
    tx.commit()?;
    assert_eq!(db.begin_read()?.open_table(U64)?.get(1)?.unwrap().value(), 1);
    Ok(())
}

#[test]
fn predicate_panic_poisons_transaction() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    {
        let mut table = tx.open_table(U64)?;
        table.insert(1, &1)?;
        let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let _ = table.retain(|_, _| -> bool { panic!("predicate"); });
        }));
    }
    assert!(matches!(tx.commit(), Err(CommitError::TransactionPoisoned)));
    Ok(())
}

#[test]
fn owned_guard_keeps_read_snapshot_alive() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &1)?;
    tx.commit()?;
    let read = db.begin_read()?;
    let table = read.open_table(U64)?;
    let guard = table.get_owned(1)?.unwrap();
    drop(table);
    drop(read);
    assert_eq!(guard.value(), 1);
    Ok(())
}

#[test]
fn owned_range_keeps_read_snapshot_alive() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    for i in 0..3 {
        tx.open_table(U64)?.insert(i, &i)?;
    }
    tx.commit()?;
    let read = db.begin_read()?;
    let table = read.open_table(U64)?;
    let range = table.range_owned(0..3)?;
    drop(table);
    drop(read);
    let values: std::result::Result<Vec<_>, redb::StorageError> =
        range.map(|r| Ok(r?.1.value())).collect();
    assert_eq!(values?, vec![0, 1, 2]);
    Ok(())
}

#[test]
fn multimap_reopen_preserves_all_pairs() -> Result<(), Error> {
    let (file, db) = file_db()?;
    let tx = db.begin_write()?;
    {
        let mut table = tx.open_multimap_table(MM)?;
        table.insert("a", "x")?;
        table.insert("a", "y")?;
    }
    tx.commit()?;
    drop(db);
    let reopened = Database::open(file.path())?;
    let read = reopened.begin_read()?;
    let table = read.open_multimap_table(MM)?;
    let values: std::result::Result<Vec<_>, redb::StorageError> =
        table.get("a")?.map(|v| Ok(v?.value().to_string())).collect();
    assert_eq!(values?, vec!["x", "y"]);
    Ok(())
}

#[test]
fn table_and_multimap_lists_are_separate() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(STR)?;
    tx.open_multimap_table(MM)?;
    assert_eq!(tx.list_tables()?.map(|h| h.name().to_string()).collect::<Vec<_>>(), vec!["str"]);
    assert_eq!(tx.list_multimap_tables()?.map(|h| h.name().to_string()).collect::<Vec<_>>(), vec!["mm"]);
    Ok(())
}

#[test]
fn stats_and_iteration_agree_on_len() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    let mut table = tx.open_table(U64)?;
    for i in 0..8 {
        table.insert(i, &i)?;
    }
    assert_eq!(table.len()?, 8);
    assert_eq!(table.iter()?.count(), 8);
    assert!(table.stats()?.stored_bytes() >= 8);
    Ok(())
}

/// Verifies: REDB-DB-002, REDB-DB-003, REDB-TXN-002
#[test]
fn create_existing_database_preserves_committed_table() -> Result<(), Error> {
    let (file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(10, &100)?;
    tx.commit()?;
    drop(db);
    let reopened = Database::create(file.path())?;
    assert_eq!(reopened.begin_read()?.open_table(U64)?.get(10)?.unwrap().value(), 100);
    Ok(())
}

/// Verifies: REDB-TXN-003, REDB-DB-003
#[test]
fn dropped_write_transaction_discards_changes_across_reopen() -> Result<(), Error> {
    let (file, db) = file_db()?;
    {
        let tx = db.begin_write()?;
        tx.open_table(U64)?.insert(1, &1)?;
    }
    assert!(db.begin_read()?.open_table(U64).is_err());
    drop(db);
    let reopened = Database::open(file.path())?;
    assert!(reopened.begin_read()?.open_table(U64).is_err());
    Ok(())
}

/// Verifies: REDB-TXN-005, REDB-TAB-004, REDB-TAB-005
#[test]
fn old_snapshot_keeps_removed_value_after_later_commit() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &10)?;
    tx.commit()?;
    let old = db.begin_read()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.remove(1)?;
    tx.commit()?;
    assert_eq!(old.open_table(U64)?.get(1)?.unwrap().value(), 10);
    assert!(db.begin_read()?.open_table(U64)?.get(1)?.is_none());
    Ok(())
}

/// Verifies: REDB-SVP-001, REDB-SVP-003, REDB-TXN-002
#[test]
fn savepoint_restore_after_update_reverts_to_original_value() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let seed = db.begin_write()?;
    seed.open_table(U64)?.insert(1, &10)?;
    seed.commit()?;
    let mut tx = db.begin_write()?;
    let savepoint = tx.ephemeral_savepoint()?;
    tx.open_table(U64)?.insert(1, &20)?;
    tx.restore_savepoint(&savepoint)?;
    tx.commit()?;
    assert_eq!(db.begin_read()?.open_table(U64)?.get(1)?.unwrap().value(), 10);
    Ok(())
}

/// Verifies: REDB-SVP-002
#[test]
fn savepoint_after_table_mutation_is_invalid() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &1)?;
    assert!(matches!(tx.ephemeral_savepoint(), Err(redb::SavepointError::InvalidSavepoint)));
    Ok(())
}

/// Verifies: REDB-SVP-004, REDB-TAB-002, REDB-TAB-003
#[test]
fn rename_to_same_name_preserves_table_and_data() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(STR)?.insert("k", "v")?;
    tx.rename_table(STR, STR)?;
    tx.commit()?;
    let read = db.begin_read()?;
    assert_eq!(read.open_table(STR)?.get("k")?.unwrap().value(), "v");
    Ok(())
}

/// Verifies: REDB-SVP-004, REDB-MM-004
#[test]
fn rename_multimap_preserves_pairs_and_listing() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_multimap_table(MM)?.insert("k", "v")?;
    let renamed = MultimapTableDefinition::<&str, &str>::new("mm2");
    tx.rename_multimap_table(MM, renamed)?;
    assert_eq!(tx.list_multimap_tables()?.map(|h| h.name().to_string()).collect::<Vec<_>>(), vec!["mm2"]);
    tx.commit()?;
    let read = db.begin_read()?;
    assert!(read.open_multimap_table(MM).is_err());
    assert_eq!(read.open_multimap_table(renamed)?.get("k")?.next().unwrap()?.value(), "v");
    Ok(())
}

/// Verifies: REDB-SVP-004
#[test]
fn rename_table_to_existing_name_errors_and_preserves_both_tables() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    let a = TableDefinition::<u64, u64>::new("a");
    let b = TableDefinition::<u64, u64>::new("b");
    tx.open_table(a)?.insert(1, &10)?;
    tx.open_table(b)?.insert(2, &20)?;
    assert!(matches!(tx.rename_table(a, b), Err(redb::TableError::TableExists(_))));
    tx.commit()?;
    let read = db.begin_read()?;
    assert_eq!(read.open_table(a)?.get(1)?.unwrap().value(), 10);
    assert_eq!(read.open_table(b)?.get(2)?.unwrap().value(), 20);
    Ok(())
}

/// Verifies: REDB-TAB-005, REDB-TXN-002
#[test]
fn delete_table_reports_false_for_missing_then_true_for_existing() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    assert!(!tx.delete_table(U64)?);
    tx.open_table(U64)?.insert(1, &1)?;
    assert!(tx.delete_table(U64)?);
    tx.commit()?;
    assert!(db.begin_read()?.open_table(U64).is_err());
    Ok(())
}

/// Verifies: REDB-MM-005, REDB-TXN-002, REDB-DB-003
#[test]
fn multimap_remove_all_then_reopen_keeps_other_keys() -> Result<(), Error> {
    let (file, db) = file_db()?;
    let tx = db.begin_write()?;
    {
        let mut table = tx.open_multimap_table(MM)?;
        table.insert("a", "x")?;
        table.insert("a", "y")?;
        table.insert("b", "z")?;
        table.remove_all("a")?;
    }
    tx.commit()?;
    drop(db);
    let reopened = Database::open(file.path())?;
    let table = reopened.begin_read()?.open_multimap_table(MM)?;
    assert!(table.get("a")?.is_empty());
    assert_eq!(table.get("b")?.next().unwrap()?.value(), "z");
    Ok(())
}

/// Verifies: REDB-GRD-001, REDB-TXN-005
#[test]
fn owned_guard_keeps_old_value_after_later_update() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &1)?;
    tx.commit()?;
    let read = db.begin_read()?;
    let guard = read.open_table(U64)?.get_owned(1)?.unwrap();
    let tx = db.begin_write()?;
    tx.open_table(U64)?.insert(1, &2)?;
    tx.commit()?;
    assert_eq!(guard.value(), 1);
    assert_eq!(db.begin_read()?.open_table(U64)?.get(1)?.unwrap().value(), 2);
    Ok(())
}

/// Verifies: REDB-GRD-002, REDB-TAB-007
#[test]
fn owned_range_is_double_ended_after_transaction_drop() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    for i in 1..=4 {
        tx.open_table(U64)?.insert(i, &i)?;
    }
    tx.commit()?;
    let read = db.begin_read()?;
    let table = read.open_table(U64)?;
    let mut range = table.range_owned(1..=4)?;
    drop(table);
    drop(read);
    assert_eq!(range.next().unwrap()?.0.value(), 1);
    assert_eq!(range.next_back().unwrap()?.0.value(), 4);
    Ok(())
}

/// Verifies: REDB-TYP-003, REDB-TXN-002
#[test]
fn type_mismatch_is_enforced_after_commit() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    tx.open_table(TableDefinition::<u64, u64>::new("typed"))?.insert(1, &1)?;
    tx.commit()?;
    let read = db.begin_read()?;
    assert!(read.open_table(TableDefinition::<u64, &str>::new("typed")).is_err());
    Ok(())
}

/// Verifies: REDB-TAB-006, REDB-TAB-007, REDB-TXN-002
#[test]
fn committed_range_matches_reopened_range() -> Result<(), Error> {
    let (file, db) = file_db()?;
    let tx = db.begin_write()?;
    for i in 0..6 {
        tx.open_table(U64)?.insert(i, &(i * 10))?;
    }
    tx.commit()?;
    drop(db);
    let reopened = Database::open(file.path())?;
    let values: std::result::Result<Vec<_>, redb::StorageError> = reopened
        .begin_read()?
        .open_table(U64)?
        .range(2..5)?
        .map(|r| Ok(r?.1.value()))
        .collect();
    assert_eq!(values?, vec![20, 30, 40]);
    Ok(())
}

/// Verifies: REDB-MM-004, REDB-GRD-002
#[test]
fn owned_multimap_range_survives_read_handle_drop() -> Result<(), Error> {
    let (_file, db) = file_db()?;
    let tx = db.begin_write()?;
    {
        let mut table = tx.open_multimap_table(MM)?;
        table.insert("a", "1")?;
        table.insert("b", "2")?;
    }
    tx.commit()?;
    let read = db.begin_read()?;
    let table = read.open_multimap_table(MM)?;
    let mut range = table.range_owned("a".."z")?;
    drop(table);
    drop(read);
    let mut first = range.next().unwrap()?;
    assert_eq!(first.0.value(), "a");
    assert_eq!(first.1.next().unwrap()?.value(), "1");
    Ok(())
}
