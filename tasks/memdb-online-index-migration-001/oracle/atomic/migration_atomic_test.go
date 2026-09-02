package memdb_test

import (
	"errors"
	"testing"

	memdb "github.com/hashicorp/go-memdb"
)

// Verifies: MDB-MIG-001
func TestEmptyMigrationIsNoOp(t *testing.T) {
	db := freshDB(t)
	before := db.DBSchema()
	if err := db.MigrateIndexes(); err != nil || db.DBSchema() != before {
		t.Fatalf("error=%v schema changed=%v", err, db.DBSchema() != before)
	}
}

// Verifies: MDB-BACKFILL-001, MDB-BACKFILL-002
func TestAddIndexBackfillsNonUniqueRows(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"}, &row{ID: "2", Email: "a"})
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1", "2")
}

// Verifies: MDB-BACKFILL-003
func TestAddUniqueIndexBackfillsDistinctRows(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"}, &row{ID: "2", Email: "b"})
	idx := stringIndex("email", "Email")
	idx.Unique = true
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "b"), "2")
}

// Verifies: MDB-BACKFILL-004
func TestAddMultiIndexBackfillsEveryKey(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Tags: []string{"a", "b"}})
	idx := &memdb.IndexSchema{Name: "labels", Indexer: &memdb.StringSliceFieldIndex{Field: "Tags"}}
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "labels", "a"), "1")
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "labels", "b"), "1")
}

// Verifies: MDB-BACKFILL-005
func TestAllowMissingSkipsExistingRow(t *testing.T) {
	db := freshDB(t, &row{ID: "1"}, &row{ID: "2", Optional: "yes"})
	idx := stringIndex("optional", "Optional")
	idx.AllowMissing = true
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "optional", "yes"), "2")
}

// Verifies: MDB-ERR-009
func TestRequiredMissingValueReturnsSentinel(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	err := db.AddIndex("items", stringIndex("optional", "Optional"))
	if !errors.Is(err, memdb.ErrIndexMigrationMissingValue) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-010
func TestIndexerFailureReturnsSentinel(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	err := db.AddIndex("items", &memdb.IndexSchema{Name: "email", Indexer: failingIndexer{failID: "1"}})
	if !errors.Is(err, memdb.ErrIndexMigrationIndexer) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-008
func TestUniqueConflictReturnsSentinel(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"}, &row{ID: "2", Email: "a"})
	idx := stringIndex("email", "Email")
	idx.Unique = true
	if err := db.AddIndex("items", idx); !errors.Is(err, memdb.ErrIndexMigrationUniqueConflict) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-010
func TestNilAddedIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{nil}})
	if !errors.Is(err, memdb.ErrIndexMigrationIndexer) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-010
func TestInvalidAddedIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.AddIndex("items", &memdb.IndexSchema{Name: "broken"})
	if !errors.Is(err, memdb.ErrIndexMigrationIndexer) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-002
func TestUnknownTableIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.AddIndex("missing", stringIndex("email", "Email"))
	if !errors.Is(err, memdb.ErrIndexMigrationTableNotFound) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-003
func TestDuplicateTableEntryIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items"}, memdb.IndexMigration{Table: "items"})
	if !errors.Is(err, memdb.ErrIndexMigrationDuplicateTable) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-004
func TestDuplicateAddNameIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("email", "Email"), stringIndex("email", "Group")}})
	if !errors.Is(err, memdb.ErrIndexMigrationDuplicateIndex) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-004
func TestDuplicateDropNameIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color", "color"}})
	if !errors.Is(err, memdb.ErrIndexMigrationDuplicateIndex) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-005
func TestAddExistingIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	if err := db.AddIndex("items", stringIndex("color", "Email")); !errors.Is(err, memdb.ErrIndexExists) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-006
func TestDropAbsentIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	if err := db.DropIndex("items", "missing"); !errors.Is(err, memdb.ErrIndexNotFound) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-007
func TestAddPrimaryIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	if err := db.AddIndex("items", stringIndex("id", "Email")); !errors.Is(err, memdb.ErrIndexMigrationPrimary) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-007
func TestDropPrimaryIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	if err := db.DropIndex("items", "id"); !errors.Is(err, memdb.ErrIndexMigrationPrimary) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-007
func TestReplacePrimaryIndexIsRejected(t *testing.T) {
	db := freshDB(t)
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"id"}, Add: []*memdb.IndexSchema{stringIndex("id", "Email")}})
	if !errors.Is(err, memdb.ErrIndexMigrationPrimary) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-001
func TestSnapshotAddIndexIsRejected(t *testing.T) {
	db := freshDB(t).Snapshot()
	if err := db.AddIndex("items", stringIndex("email", "Email")); !errors.Is(err, memdb.ErrIndexMigrationSnapshot) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-ERR-001
func TestSnapshotDropIndexIsRejected(t *testing.T) {
	db := freshDB(t).Snapshot()
	if err := db.DropIndex("items", "color"); !errors.Is(err, memdb.ErrIndexMigrationSnapshot) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-MIG-004
func TestDropIndexRemovesSchemaName(t *testing.T) {
	db := freshDB(t)
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	if _, ok := db.DBSchema().Tables["items"].Indexes["color"]; ok {
		t.Fatal("color remains")
	}
}

// Verifies: MDB-XVIEW-012
func TestDropIndexPreservesPrimaryRows(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "id", "1"), "1")
}

// Verifies: MDB-MIG-005
func TestReplacementUsesNewDefinition(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "new"})
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{stringIndex("color", "Email")}})
	if err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "color", "new"), "1")
}

// Verifies: MDB-MIG-008
func TestAddedSchemaIsCopied(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	idx := stringIndex("email", "Email")
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	idx.Name = "mutated"
	got := db.DBSchema().Tables["items"].Indexes["email"]
	if got == nil || got.Name != "email" {
		t.Fatal("published schema aliases caller struct")
	}
}

// Verifies: MDB-ROLLBACK-001
func TestFailedMigrationPreservesSchemaIdentity(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	before := db.DBSchema()
	_ = db.AddIndex("items", stringIndex("optional", "Optional"))
	if db.DBSchema() != before {
		t.Fatal("failed migration published schema")
	}
}

// Verifies: MDB-ROLLBACK-002
func TestFailedMigrationPreservesExistingQuery(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "blue"})
	_ = db.AddIndex("items", stringIndex("optional", "Optional"))
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "color", "blue"), "1")
}

// Verifies: MDB-WATCH-003
func TestFailedMigrationDoesNotWakeWatch(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	watch, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
	_ = db.AddIndex("items", stringIndex("optional", "Optional"))
	requireOpen(t, watch)
}

// Verifies: MDB-WATCH-001
func TestSuccessfulAddWakesExistingWatch(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	watch, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireClosed(t, watch)
}

// Verifies: MDB-WATCH-001
func TestSuccessfulDropWakesDroppedIndexWatch(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "blue"})
	iter, _ := db.Txn(false).Get("items", "color", "blue")
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	requireClosed(t, iter.WatchCh())
}

// Verifies: MDB-MVCC-001
func TestOldTransactionRejectsNewIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	old := db.Txn(false)
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	if _, err := safeGet(old, "items", "email", "a"); err == nil {
		t.Fatal("old txn saw new index")
	}
}

// Verifies: MDB-MVCC-002
func TestOldTransactionRetainsDroppedIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "blue"})
	old := db.Txn(false)
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, old, "items", "color", "blue"), "1")
}

// Verifies: MDB-MVCC-003
func TestNewTransactionSeesAddedIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1")
}

// Verifies: MDB-MVCC-004
func TestTransactionSnapshotRetainsOldSchema(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	snap := db.Txn(false).Snapshot()
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	if _, err := safeGet(snap, "items", "email", "a"); err == nil {
		t.Fatal("txn snapshot saw new index")
	}
}

// Verifies: MDB-WATCH-004
func TestEmptyMigrationDoesNotWakeWatch(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	watch, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
	if err := db.MigrateIndexes(); err != nil {
		t.Fatal(err)
	}
	requireOpen(t, watch)
}

// Verifies: MDB-ROLLBACK-003
func TestFailedMigrationDoesNotPublishIndexName(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	_ = db.AddIndex("items", stringIndex("optional", "Optional"))
	if _, ok := db.DBSchema().Tables["items"].Indexes["optional"]; ok {
		t.Fatal("failed index published")
	}
}

// Verifies: MDB-ERR-002
func TestWrappedErrorCarriesTableContext(t *testing.T) {
	db := freshDB(t)
	err := db.DropIndex("missing", "x")
	if !errors.Is(err, memdb.ErrIndexMigrationTableNotFound) || err.Error() == memdb.ErrIndexMigrationTableNotFound.Error() {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-XVIEW-001
func TestAddedIndexAppearsInDBSchema(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	if got := db.DBSchema().Tables["items"].Indexes["email"]; got == nil || got.Name != "email" {
		t.Fatalf("schema index=%#v", got)
	}
}

// Verifies: MDB-BACKFILL-001
func TestAddIndexToEmptyTableSucceeds(t *testing.T) {
	db := freshDB(t)
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "absent"))
}

// Verifies: MDB-XVIEW-012
func TestDropOneIndexPreservesSchemaForOtherIndex(t *testing.T) {
	db := freshDB(t)
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	if _, ok := db.DBSchema().Tables["items"].Indexes["tags"]; !ok {
		t.Fatal("unrelated tags index removed")
	}
}

// Verifies: MDB-BACKFILL-001
func TestAddedLowercaseIndexUsesIndexerEncoding(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "Mixed@Example"})
	idx := &memdb.IndexSchema{Name: "email", Indexer: &memdb.StringFieldIndex{Field: "Email", Lowercase: true}}
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "MIXED@EXAMPLE"), "1")
}

// Verifies: MDB-BACKFILL-001
func TestFirstReadsBackfilledIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	raw, err := db.Txn(false).First("items", "email", "a")
	if err != nil || raw == nil || raw.(*row).ID != "1" {
		t.Fatalf("row=%#v error=%v", raw, err)
	}
}

// Verifies: MDB-WATCH-002
func TestSuccessfulMigrationReturnsAfterWatchNotification(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	watch, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	select {
	case <-watch:
	default:
		t.Fatal("watch remained open after migration returned")
	}
}
