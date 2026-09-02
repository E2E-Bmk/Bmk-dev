package memdb_test

import (
	"errors"
	"sync"
	"testing"
	"time"

	memdb "github.com/hashicorp/go-memdb"
)

// Verifies: MDB-MIG-002, MDB-XVIEW-001
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestBatchAddsTwoIndexesAtomically(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a", Group: "g"})
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("email", "Email"), stringIndex("group", "Group")}})
	if err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1")
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "group", "g"), "1")
}

// Verifies: MDB-MIG-003, MDB-XVIEW-009
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestBatchMigratesTwoTables(t *testing.T) {
	db := twoTableDB(t)
	err := db.MigrateIndexes(
		memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("email", "Email")}},
		memdb.IndexMigration{Table: "other", Add: []*memdb.IndexSchema{stringIndex("email", "Email")}},
	)
	if err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "items@example"), "i1")
	requireIDs(t, queryIDs(t, db.Txn(false), "other", "email", "other@example"), "o1")
}

// Verifies: MDB-ROLLBACK-004
// Depends-On: TestUniqueConflictReturnsSentinel, TestFailedMigrationPreservesSchemaIdentity
func TestBatchConflictRollsBackEarlierAddition(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "same", Group: "g1"}, &row{ID: "2", Email: "same", Group: "g2"})
	unique := stringIndex("email", "Email")
	unique.Unique = true
	before := db.DBSchema()
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("group", "Group"), unique}})
	if !errors.Is(err, memdb.ErrIndexMigrationUniqueConflict) || db.DBSchema() != before {
		t.Fatalf("error=%v changed=%v", err, db.DBSchema() != before)
	}
	if _, ok := db.DBSchema().Tables["items"].Indexes["group"]; ok {
		t.Fatal("partial batch published")
	}
}

// Verifies: MDB-ROLLBACK-004
// Depends-On: TestIndexerFailureReturnsSentinel, TestFailedMigrationDoesNotPublishIndexName
func TestBatchIndexerErrorRollsBackEarlierAddition(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a", Group: "g"})
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("group", "Group"), {Name: "bad", Indexer: failingIndexer{failID: "1"}}}})
	if !errors.Is(err, memdb.ErrIndexMigrationIndexer) {
		t.Fatalf("error=%v", err)
	}
	if _, ok := db.DBSchema().Tables["items"].Indexes["group"]; ok {
		t.Fatal("partial batch published")
	}
}

// Verifies: MDB-MVCC-005, MDB-XVIEW-006
// Depends-On: TestReplacementUsesNewDefinition, TestOldTransactionRetainsDroppedIndex
func TestReplacementKeepsOldTransactionDefinition(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "new"})
	old := db.Txn(false)
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{stringIndex("color", "Email")}})
	if err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, old, "items", "color", "old"), "1")
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "color", "new"), "1")
}

// Verifies: MDB-MVCC-006
// Depends-On: TestReplacementUsesNewDefinition, TestTransactionSnapshotRetainsOldSchema
func TestReplacementKeepsOldDatabaseSnapshot(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "new"})
	old := db.Snapshot()
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{stringIndex("color", "Email")}})
	if err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, old.Txn(false), "items", "color", "old"), "1")
}

// Verifies: MDB-MVCC-006
// Depends-On: TestOldTransactionRejectsNewIndex, TestSnapshotAddIndexIsRejected
func TestPreMigrationSnapshotRejectsAddedIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	snap := db.Snapshot()
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	if _, err := safeGet(snap.Txn(false), "items", "email", "a"); err == nil {
		t.Fatal("old snapshot saw new index")
	}
}

// Verifies: MDB-MVCC-006
// Depends-On: TestOldTransactionRetainsDroppedIndex, TestDropIndexPreservesPrimaryRows
func TestPreMigrationSnapshotRetainsDroppedIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "blue"})
	snap := db.Snapshot()
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, snap.Txn(false), "items", "color", "blue"), "1")
}

// Verifies: MDB-CONC-001
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestWriterHeldBeforeMigrationCommitsIntoBackfill(t *testing.T) {
	db := freshDB(t)
	writer := db.Txn(true)
	defer writer.Abort()
	if err := writer.Insert("items", &row{ID: "1", Color: "c", Tags: []string{"t"}, Email: "a"}); err != nil {
		t.Fatal(err)
	}
	done := make(chan error, 1)
	go func() { done <- db.AddIndex("items", stringIndex("email", "Email")) }()
	requireBlocked(t, done)
	writer.Commit()
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1")
}

// Verifies: MDB-CONC-002, MDB-XVIEW-011
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestWriterRequestedDuringBackfillUsesNewIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "old"})
	started := make(chan struct{})
	release := make(chan struct{})
	migrationDone := make(chan error, 1)
	go func() {
		migrationDone <- db.AddIndex("items", &memdb.IndexSchema{Name: "email", Indexer: &blockingIndexer{started: started, release: release}})
	}()
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("backfill did not start")
	}
	writerDone := make(chan error, 1)
	go func() {
		tx := db.Txn(true)
		defer tx.Abort()
		err := tx.Insert("items", &row{ID: "2", Color: "c", Tags: []string{"t"}, Email: "new"})
		if err == nil {
			tx.Commit()
		}
		writerDone <- err
	}()
	requireBlocked(t, writerDone)
	close(release)
	if err := <-migrationDone; err != nil {
		t.Fatal(err)
	}
	if err := <-writerDone; err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "new"), "2")
}

// Verifies: MDB-CONC-003
// Depends-On: TestFailedMigrationPreservesExistingQuery, TestRequiredMissingValueReturnsSentinel
func TestWriterAfterFailedMigrationUsesOldSchema(t *testing.T) {
	db := freshDB(t, &row{ID: "1"})
	_ = db.AddIndex("items", stringIndex("optional", "Optional"))
	insertRows(t, db, "items", &row{ID: "2"})
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "id", "2"), "2")
}

// Verifies: MDB-XVIEW-003
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestPostMigrationUpdateMovesNewIndexKey(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	tx := db.Txn(true)
	if err := tx.Insert("items", &row{ID: "1", Color: "c", Tags: []string{"t"}, Email: "b"}); err != nil {
		t.Fatal(err)
	}
	tx.Commit()
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"))
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "b"), "1")
}

// Verifies: MDB-XVIEW-003
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestDropIndexPreservesPrimaryRows
func TestPostMigrationDeleteRemovesNewIndexKey(t *testing.T) {
	r := &row{ID: "1", Email: "a"}
	db := freshDB(t, r)
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	tx := db.Txn(true)
	if err := tx.Delete("items", r); err != nil {
		t.Fatal(err)
	}
	tx.Commit()
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"))
}

// Verifies: MDB-XVIEW-003, MDB-XVIEW-006
// Depends-On: TestReplacementUsesNewDefinition, TestNewTransactionSeesAddedIndex
func TestPostReplacementUpdateUsesReplacementDefinition(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "a"})
	_ = db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{stringIndex("color", "Email")}})
	tx := db.Txn(true)
	if err := tx.Insert("items", &row{ID: "1", Color: "ignored", Tags: []string{"t"}, Email: "b"}); err != nil {
		t.Fatal(err)
	}
	tx.Commit()
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "color", "b"), "1")
}

// Verifies: MDB-WATCH-002, MDB-XVIEW-008
// Depends-On: TestSuccessfulAddWakesExistingWatch, TestNewTransactionSeesAddedIndex
func TestWatchWakeObservesPublishedSchema(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	watch, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
	observed := make(chan error, 1)
	go func() {
		select {
		case <-watch:
			_, err := db.Txn(false).First("items", "email", "a")
			observed <- err
		case <-time.After(testTimeout):
			observed <- errors.New("watch timeout")
		}
	}()
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	if err := <-observed; err != nil {
		t.Fatal(err)
	}
}

// Verifies: MDB-WATCH-005, MDB-XVIEW-009
// Depends-On: TestSuccessfulAddWakesExistingWatch, TestEmptyMigrationDoesNotWakeWatch
func TestUnaffectedTableWatchRemainsOpen(t *testing.T) {
	db := twoTableDB(t)
	watch, _, _ := db.Txn(false).FirstWatch("other", "id", "o1")
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireOpen(t, watch)
}

// Verifies: MDB-WATCH-001
// Depends-On: TestSuccessfulAddWakesExistingWatch, TestSuccessfulDropWakesDroppedIndexWatch
func TestSuccessfulBatchWakesEveryAffectedTable(t *testing.T) {
	db := twoTableDB(t)
	wi, _, _ := db.Txn(false).FirstWatch("items", "id", "i1")
	wo, _, _ := db.Txn(false).FirstWatch("other", "id", "o1")
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("email", "Email")}}, memdb.IndexMigration{Table: "other", Add: []*memdb.IndexSchema{stringIndex("email", "Email")}})
	if err != nil {
		t.Fatal(err)
	}
	requireClosed(t, wi)
	requireClosed(t, wo)
}

// Verifies: MDB-WATCH-003, MDB-ROLLBACK-004
// Depends-On: TestFailedMigrationDoesNotWakeWatch, TestUniqueConflictReturnsSentinel
func TestFailedBatchWakesNoAffectedTable(t *testing.T) {
	db := twoTableDB(t)
	wi, _, _ := db.Txn(false).FirstWatch("items", "id", "i1")
	wo, _, _ := db.Txn(false).FirstWatch("other", "id", "o1")
	bad := stringIndex("missing", "Optional")
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("email", "Email")}}, memdb.IndexMigration{Table: "other", Add: []*memdb.IndexSchema{bad}})
	if !errors.Is(err, memdb.ErrIndexMigrationMissingValue) {
		t.Fatalf("error=%v", err)
	}
	requireOpen(t, wi)
	requireOpen(t, wo)
}

// Verifies: MDB-WATCH-006, MDB-MVCC-002
// Depends-On: TestSuccessfulDropWakesDroppedIndexWatch, TestOldTransactionRetainsDroppedIndex
func TestWokenOldTransactionRemainsReadable(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "blue"})
	old := db.Txn(false)
	iter, _ := old.Get("items", "color", "blue")
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	requireClosed(t, iter.WatchCh())
	requireIDs(t, queryIDs(t, old, "items", "color", "blue"), "1")
}

// Verifies: MDB-BACKFILL-006
// Depends-On: TestAddMultiIndexBackfillsEveryKey, TestAddUniqueIndexBackfillsDistinctRows
func TestUniqueMultiDuplicateWithinOneObjectIsAllowed(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Group: "g"})
	idx := &memdb.IndexSchema{Name: "group", Unique: true, Indexer: duplicateMultiIndexer{}}
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "group", "g"), "1")
}

// Verifies: MDB-BACKFILL-003
// Depends-On: TestUniqueConflictReturnsSentinel, TestAddMultiIndexBackfillsEveryKey
func TestUniqueMultiCollisionAcrossRowsRollsBack(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Group: "g"}, &row{ID: "2", Group: "g"})
	idx := &memdb.IndexSchema{Name: "group", Unique: true, Indexer: duplicateMultiIndexer{}}
	if err := db.AddIndex("items", idx); !errors.Is(err, memdb.ErrIndexMigrationUniqueConflict) {
		t.Fatalf("error=%v", err)
	}
}

// Verifies: MDB-BACKFILL-002
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestUniqueConflictReturnsSentinel
func TestNonUniqueBackfillKeepsAllCollidingRows(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Group: "g"}, &row{ID: "2", Group: "g"}, &row{ID: "3", Group: "g"})
	if err := db.AddIndex("items", stringIndex("group", "Group")); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "group", "g"), "1", "2", "3")
}

// Verifies: MDB-CONC-004
// Depends-On: TestAllowMissingSkipsExistingRow, TestNewTransactionSeesAddedIndex
func TestPostMigrationWriterMayOmitAllowMissingIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Optional: "yes"})
	idx := stringIndex("optional", "Optional")
	idx.AllowMissing = true
	if err := db.AddIndex("items", idx); err != nil {
		t.Fatal(err)
	}
	insertRows(t, db, "items", &row{ID: "2"})
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "id", "2"), "2")
}

// Verifies: MDB-CONC-004, MDB-XVIEW-003
// Depends-On: TestRequiredMissingValueReturnsSentinel, TestDropIndexPreservesPrimaryRows
func TestPostMigrationRequiredMissingInsertCanAbortCleanly(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Optional: "yes"})
	if err := db.AddIndex("items", stringIndex("optional", "Optional")); err != nil {
		t.Fatal(err)
	}
	tx := db.Txn(true)
	err := tx.Insert("items", &row{ID: "2", Color: "c", Tags: []string{"t"}})
	if err == nil {
		t.Fatal("missing insert succeeded")
	}
	tx.Abort()
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "id", "2"))
}

// Verifies: MDB-CONC-005, MDB-MVCC-001
// Depends-On: TestOldTransactionRejectsNewIndex, TestEmptyMigrationIsNoOp
func TestReadersStartOnOldGenerationDuringBackfill(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	started := make(chan struct{})
	release := make(chan struct{})
	done := make(chan error, 1)
	go func() {
		done <- db.AddIndex("items", &memdb.IndexSchema{Name: "email", Indexer: &blockingIndexer{started: started, release: release}})
	}()
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("not started")
	}
	for n := 0; n < 5; n++ {
		if _, err := safeGet(db.Txn(false), "items", "email", "a"); err == nil {
			t.Fatal("reader saw unpublished schema")
		}
	}
	close(release)
	if err := <-done; err != nil {
		t.Fatal(err)
	}
}

// Verifies: MDB-XVIEW-001
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestPublishedSchemaAndRootAgree(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	if _, ok := db.DBSchema().Tables["items"].Indexes["email"]; !ok {
		t.Fatal("schema missing")
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1")
}

// Verifies: MDB-XVIEW-012
// Depends-On: TestDropIndexPreservesPrimaryRows, TestOldTransactionRetainsDroppedIndex
func TestDropPreservesOtherSecondaryIndex(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "blue", Tags: []string{"keep"}})
	if err := db.DropIndex("items", "color"); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "tags", "keep"), "1")
}

// Verifies: MDB-WATCH-001, MDB-XVIEW-006
// Depends-On: TestSuccessfulDropWakesDroppedIndexWatch, TestReplacementUsesNewDefinition
func TestReplacementWakesOldDefinitionWatch(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "new"})
	iter, _ := db.Txn(false).Get("items", "color", "old")
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{stringIndex("color", "Email")}})
	if err != nil {
		t.Fatal(err)
	}
	requireClosed(t, iter.WatchCh())
}

// Verifies: MDB-MVCC-007
// Depends-On: TestOldTransactionRejectsNewIndex, TestReplacementUsesNewDefinition
func TestSequentialGenerationsRemainDistinct(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a", Group: "g"})
	g0 := db.Txn(false)
	_ = db.AddIndex("items", stringIndex("email", "Email"))
	g1 := db.Txn(false)
	_ = db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"email"}, Add: []*memdb.IndexSchema{stringIndex("email", "Group")}})
	if _, err := safeGet(g0, "items", "email", "a"); err == nil {
		t.Fatal("g0 saw add")
	}
	requireIDs(t, queryIDs(t, g1, "items", "email", "a"), "1")
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "g"), "1")
}

// Verifies: MDB-ROLLBACK-005, MDB-XVIEW-006
// Depends-On: TestReplacementUsesNewDefinition, TestIndexerFailureReturnsSentinel
func TestFailedReplacementPreservesOldDefinition(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "a"})
	before := db.DBSchema()
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{{Name: "color", Indexer: failingIndexer{failID: "1"}}}})
	if !errors.Is(err, memdb.ErrIndexMigrationIndexer) || db.DBSchema() != before {
		t.Fatalf("error=%v changed=%v", err, db.DBSchema() != before)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "color", "old"), "1")
}

// Verifies: MDB-MIG-006, MDB-XVIEW-012
// Depends-On: TestDropIndexPreservesPrimaryRows, TestAddIndexBackfillsNonUniqueRows
func TestSameTableAddAndDropPublishesOneCompleteGeneration(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "old", Email: "a"})
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Drop: []string{"color"}, Add: []*memdb.IndexSchema{stringIndex("email", "Email")}})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.Txn(false).Get("items", "color", "old"); err == nil {
		t.Fatal("drop absent")
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1")
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "id", "1"), "1")
}

// Verifies: MDB-CONC-006
// Depends-On: TestAddIndexBackfillsNonUniqueRows, TestNewTransactionSeesAddedIndex
func TestConcurrentMigrationsSerialize(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a", Group: "g"})
	started := make(chan struct{})
	release := make(chan struct{})
	first := make(chan error, 1)
	second := make(chan error, 1)
	go func() {
		first <- db.AddIndex("items", &memdb.IndexSchema{Name: "email", Indexer: &blockingIndexer{started: started, release: release}})
	}()
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("first not started")
	}
	go func() { second <- db.AddIndex("items", stringIndex("group", "Group")) }()
	requireBlocked(t, second)
	close(release)
	if err := <-first; err != nil {
		t.Fatal(err)
	}
	if err := <-second; err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "email", "a"), "1")
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "group", "g"), "1")
}

// Verifies: MDB-CONC-007
// Depends-On: TestFailedMigrationPreservesSchemaIdentity, TestNewTransactionSeesAddedIndex
func TestMigrationFailureReleasesWaitingWriter(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Optional: ""})
	started := make(chan struct{})
	release := make(chan struct{})
	idx := &blockingIndexer{started: started, release: release}
	done := make(chan error, 1)
	go func() { done <- db.AddIndex("items", &memdb.IndexSchema{Name: "email", Indexer: idx}) }()
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("not started")
	}
	writer := make(chan error, 1)
	go func() {
		tx := db.Txn(true)
		defer tx.Abort()
		err := tx.Insert("items", &row{ID: "2", Color: "c", Tags: []string{"t"}, Email: "b"})
		if err == nil {
			tx.Commit()
		}
		writer <- err
	}()
	requireBlocked(t, writer)
	close(release)
	if err := <-done; !errors.Is(err, memdb.ErrIndexMigrationMissingValue) {
		t.Fatalf("migration error=%v", err)
	}
	if err := <-writer; err != nil {
		t.Fatal(err)
	}
}

// Verifies: MDB-XVIEW-007, MDB-WATCH-003
// Depends-On: TestFailedMigrationDoesNotWakeWatch, TestFailedMigrationPreservesExistingQuery
func TestFailedMultiTableBatchPreservesBothViews(t *testing.T) {
	db := twoTableDB(t)
	before := db.DBSchema()
	wi, _, _ := db.Txn(false).FirstWatch("items", "id", "i1")
	wo, _, _ := db.Txn(false).FirstWatch("other", "id", "o1")
	err := db.MigrateIndexes(memdb.IndexMigration{Table: "items", Add: []*memdb.IndexSchema{stringIndex("email", "Email")}}, memdb.IndexMigration{Table: "other", Add: []*memdb.IndexSchema{stringIndex("optional", "Optional")}})
	if !errors.Is(err, memdb.ErrIndexMigrationMissingValue) || db.DBSchema() != before {
		t.Fatalf("error=%v", err)
	}
	requireOpen(t, wi)
	requireOpen(t, wo)
	requireIDs(t, queryIDs(t, db.Txn(false), "items", "id", "i1"), "i1")
	requireIDs(t, queryIDs(t, db.Txn(false), "other", "id", "o1"), "o1")
}

// Verifies: MDB-MVCC-008
// Depends-On: TestTransactionSnapshotRetainsOldSchema, TestAddIndexBackfillsNonUniqueRows
func TestTxnSnapshotPreservesStagedRowsAndOldSchema(t *testing.T) {
	db := freshDB(t)
	writer := db.Txn(true)
	if err := writer.Insert("items", &row{ID: "1", Color: "c", Tags: []string{"t"}, Email: "a"}); err != nil {
		t.Fatal(err)
	}
	snap := writer.Snapshot()
	writer.Commit()
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireIDs(t, queryIDs(t, snap, "items", "id", "1"), "1")
	if _, err := safeGet(snap, "items", "email", "a"); err == nil {
		t.Fatal("snapshot saw later schema")
	}
}

// Verifies: MDB-WATCH-007
// Depends-On: TestSuccessfulAddWakesExistingWatch, TestEmptyMigrationDoesNotWakeWatch
func TestSuccessWakesAllOldIndexesInAffectedTable(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Color: "c", Email: "a", Tags: []string{"t"}})
	idw, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
	ci, _ := db.Txn(false).Get("items", "color", "c")
	ti, _ := db.Txn(false).Get("items", "tags", "t")
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	requireClosed(t, idw)
	requireClosed(t, ci.WatchCh())
	requireClosed(t, ti.WatchCh())
}

// Verifies: MDB-CONC-008, MDB-XVIEW-008
// Depends-On: TestSuccessfulAddWakesExistingWatch, TestNewTransactionSeesAddedIndex
func TestConcurrentWatchersObserveCompletePublication(t *testing.T) {
	db := freshDB(t, &row{ID: "1", Email: "a"})
	const n = 8
	errs := make(chan error, n)
	var ready sync.WaitGroup
	ready.Add(n)
	for i := 0; i < n; i++ {
		watch, _, _ := db.Txn(false).FirstWatch("items", "id", "1")
		go func(ch <-chan struct{}) {
			ready.Done()
			select {
			case <-ch:
				raw, err := db.Txn(false).First("items", "email", "a")
				if err == nil && raw == nil {
					err = errors.New("missing backfill")
				}
				errs <- err
			case <-time.After(testTimeout):
				errs <- errors.New("timeout")
			}
		}(watch)
	}
	ready.Wait()
	if err := db.AddIndex("items", stringIndex("email", "Email")); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < n; i++ {
		if err := <-errs; err != nil {
			t.Fatal(err)
		}
	}
}
