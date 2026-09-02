package integration_test

import (
	"bytes"
	"errors"
	"fmt"
	"testing"
	"time"

	"github.com/nutsdb/nutsdb"
)

func openDB(t *testing.T) *nutsdb.DB {
	t.Helper()
	db, err := nutsdb.Open(nutsdb.DefaultOptions, nutsdb.WithDir(t.TempDir()))
	if err != nil {
		t.Fatal(err)
	}
	err = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("kv"); err != nil {
			return err
		}
		if err := tx.NewListBucket("lists"); err != nil {
			return err
		}
		if err := tx.NewSetBucket("sets"); err != nil {
			return err
		}
		return tx.NewSortSetBucket("zsets")
	})
	if err != nil {
		_ = db.Close()
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func openWatchDB(t *testing.T) *nutsdb.DB {
	t.Helper()
	opts := nutsdb.DefaultOptions
	opts.EnableWatch = true
	db, err := nutsdb.Open(opts, nutsdb.WithDir(t.TempDir()))
	if err != nil {
		t.Fatal(err)
	}
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.NewKVBucket("kv") }); err != nil {
		_ = db.Close()
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func hasBytes(items [][]byte, target []byte) bool {
	for _, item := range items {
		if bytes.Equal(item, target) {
			return true
		}
	}
	return false
}

func runWorkflow(t *testing.T, n int) {
	db := openDB(t)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()

	key := []byte(fmt.Sprintf("key-%02d", n))
	listKey := []byte(fmt.Sprintf("list-%02d", n))
	setKey := []byte(fmt.Sprintf("set-%02d", n))
	zKey := []byte(fmt.Sprintf("zset-%02d", n))
	prefix := []byte(fmt.Sprintf("prefix-%02d", n))
	middle := []byte(fmt.Sprintf("middle-%02d", n))
	tail := []byte(fmt.Sprintf("tail-%02d", n))

	if err := tx.Put("kv", key, prefix, uint32(60+n)); err != nil {
		t.Fatal(err)
	}
	if err := tx.LPush("lists", listKey, prefix); err != nil {
		t.Fatal(err)
	}
	if err := tx.SAdd("sets", setKey, prefix); err != nil {
		t.Fatal(err)
	}
	if err := tx.ZAdd("zsets", zKey, 1, prefix); err != nil {
		t.Fatal(err)
	}
	outer, err := tx.Savepoint()
	if err != nil {
		t.Fatal(err)
	}

	if err := tx.Put("kv", key, middle, nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.LPush("lists", listKey, middle); err != nil {
		t.Fatal(err)
	}
	if err := tx.SAdd("sets", setKey, middle); err != nil {
		t.Fatal(err)
	}
	if err := tx.ZAdd("zsets", zKey, 2, middle); err != nil {
		t.Fatal(err)
	}
	inner, err := tx.Savepoint()
	if err != nil {
		t.Fatal(err)
	}

	if err := tx.Put("kv", key, tail, nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.LPush("lists", listKey, tail); err != nil {
		t.Fatal(err)
	}
	if err := tx.SAdd("sets", setKey, tail); err != nil {
		t.Fatal(err)
	}
	if err := tx.ZAdd("zsets", zKey, 3, tail); err != nil {
		t.Fatal(err)
	}

	mode := n % 3
	wantKV := tail
	wantList, wantSet, wantZ := 3, 3, 3
	wantTTL := int64(-1)
	switch mode {
	case 0:
		if err := tx.RollbackTo(outer); err != nil {
			t.Fatal(err)
		}
		wantKV, wantList, wantSet, wantZ, wantTTL = prefix, 1, 1, 1, 1
	case 1:
		if err := tx.RollbackTo(inner); err != nil {
			t.Fatal(err)
		}
		if err := tx.ReleaseSavepoint(outer); err != nil {
			t.Fatal(err)
		}
		wantKV, wantList, wantSet, wantZ = middle, 2, 2, 2
	case 2:
		if err := tx.ReleaseSavepoint(inner); err != nil {
			t.Fatal(err)
		}
		if err := tx.ReleaseSavepoint(outer); err != nil {
			t.Fatal(err)
		}
	}

	if n%5 == 0 {
		sp, err := tx.Savepoint()
		if err != nil {
			t.Fatal(err)
		}
		bucket := fmt.Sprintf("discarded-bucket-%02d", n)
		if err := tx.NewKVBucket(bucket); err != nil {
			t.Fatal(err)
		}
		if err := tx.RollbackTo(sp); err != nil {
			t.Fatal(err)
		}
	}
	if n%7 == 0 {
		sp, err := tx.Savepoint()
		if err != nil {
			t.Fatal(err)
		}
		if err := tx.DeleteBucket(nutsdb.DataStructureBTree, "kv"); err != nil {
			t.Fatal(err)
		}
		if err := tx.RollbackTo(sp); err != nil {
			t.Fatal(err)
		}
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}

	err = db.View(func(view *nutsdb.Tx) error {
		got, err := view.Get("kv", key)
		if err != nil {
			return err
		}
		if !bytes.Equal(got, wantKV) {
			return fmt.Errorf("kv=%q want=%q", got, wantKV)
		}
		ttl, err := view.GetTTL("kv", key)
		if err != nil {
			return err
		}
		if wantTTL > 0 && ttl <= 0 {
			return fmt.Errorf("ttl=%d want positive", ttl)
		}
		if wantTTL < 0 && ttl != -1 {
			return fmt.Errorf("ttl=%d want persistent", ttl)
		}
		list, err := view.LRange("lists", listKey, 0, -1)
		if err != nil || len(list) != wantList {
			return fmt.Errorf("list len=%d want=%d err=%v", len(list), wantList, err)
		}
		set, err := view.SMembers("sets", setKey)
		if err != nil || len(set) != wantSet {
			return fmt.Errorf("set len=%d want=%d err=%v", len(set), wantSet, err)
		}
		zset, err := view.ZMembers("zsets", zKey)
		if err != nil || len(zset) != wantZ {
			return fmt.Errorf("zset len=%d want=%d err=%v", len(zset), wantZ, err)
		}
		if !hasBytes(list, wantKV) && mode != 0 {
			return fmt.Errorf("list lacks retained boundary value %q", wantKV)
		}
		if n%5 == 0 && view.ExistBucket(nutsdb.DataStructureBTree, fmt.Sprintf("discarded-bucket-%02d", n)) {
			return fmt.Errorf("discarded bucket persisted")
		}
		if n%7 == 0 && !view.ExistBucket(nutsdb.DataStructureBTree, "kv") {
			return fmt.Errorf("restored bucket missing")
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

// Verifies: NUT-RB-001, NUT-TX-001, NUT-CV-002
// Depends-On: TestRollbackRestoresKVOverwrite, TestRollbackConsumesTarget
func TestWorkflow01(t *testing.T) { runWorkflow(t, 1) }

// Verifies: NUT-RB-003, NUT-CV-003
// Depends-On: TestInnerRollbackLeavesOuter, TestRollbackRestoresList
func TestWorkflow02(t *testing.T) { runWorkflow(t, 2) }

// Verifies: NUT-RB-002, NUT-CV-003
// Depends-On: TestRollbackInvalidatesYounger, TestRollbackRestoresSet
func TestWorkflow03(t *testing.T) { runWorkflow(t, 3) }

// Verifies: NUT-SP-005, NUT-CV-003
// Depends-On: TestReleaseKeepsKV, TestRollbackRestoresSortedSet
func TestWorkflow04(t *testing.T) { runWorkflow(t, 4) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketCreate, TestRollbackDropsBucketDelete
func TestWorkflow05(t *testing.T) { runWorkflow(t, 5) }

// Verifies: NUT-DS-001, NUT-CV-005
// Depends-On: TestRollbackRestoresTTL, TestRollbackRestoresKVOverwrite
func TestWorkflow06(t *testing.T) { runWorkflow(t, 6) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketDelete, TestWriteAfterRollbackTo
func TestWorkflow07(t *testing.T) { runWorkflow(t, 7) }

// Verifies: NUT-RB-003, NUT-CV-001
// Depends-On: TestInnerRollbackLeavesOuter, TestDepthIncrements
func TestWorkflow08(t *testing.T) { runWorkflow(t, 8) }

// Verifies: NUT-RB-001, NUT-CV-002
// Depends-On: TestRollbackRestoresKVOverwrite, TestRollbackRestoresDeletedKV
func TestWorkflow09(t *testing.T) { runWorkflow(t, 9) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketCreate, TestReleasePreservesWrites
func TestWorkflow10(t *testing.T) { runWorkflow(t, 10) }

// Verifies: NUT-TX-001, NUT-CV-003
// Depends-On: TestRollbackRestoresList, TestRollbackRestoresSet
func TestWorkflow11(t *testing.T) { runWorkflow(t, 11) }

// Verifies: NUT-DS-001, NUT-CV-005
// Depends-On: TestRollbackRestoresTTL, TestReleaseKeepsKV
func TestWorkflow12(t *testing.T) { runWorkflow(t, 12) }

// Verifies: NUT-SP-005, NUT-CV-003
// Depends-On: TestReleaseDecrementsDepth, TestRollbackRestoresSortedSet
func TestWorkflow13(t *testing.T) { runWorkflow(t, 13) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketDelete, TestRollbackDropsBucketCreate
func TestWorkflow14(t *testing.T) { runWorkflow(t, 14) }

// Verifies: NUT-RB-002, NUT-TX-001
// Depends-On: TestRollbackInvalidatesYounger, TestRollbackConsumesTarget
func TestWorkflow15(t *testing.T) { runWorkflow(t, 15) }

// Verifies: NUT-RB-003, NUT-CV-003
// Depends-On: TestInnerRollbackLeavesOuter, TestRollbackRestoresList
func TestWorkflow16(t *testing.T) { runWorkflow(t, 16) }

// Verifies: NUT-SP-005, NUT-CV-002
// Depends-On: TestReleaseKeepsKV, TestReleasePreservesWrites
func TestWorkflow17(t *testing.T) { runWorkflow(t, 17) }

// Verifies: NUT-RB-001, NUT-CV-005
// Depends-On: TestRollbackRestoresTTL, TestRollbackRestoresKVOverwrite
func TestWorkflow18(t *testing.T) { runWorkflow(t, 18) }

// Verifies: NUT-TX-001, NUT-CV-003
// Depends-On: TestRollbackRestoresSet, TestRollbackRestoresSortedSet
func TestWorkflow19(t *testing.T) { runWorkflow(t, 19) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketCreate, TestWriteAfterRollbackTo
func TestWorkflow20(t *testing.T) { runWorkflow(t, 20) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketDelete, TestRollbackDropsBucketCreate
func TestWorkflow21(t *testing.T) { runWorkflow(t, 21) }

// Verifies: NUT-RB-003, NUT-CV-001
// Depends-On: TestInnerRollbackLeavesOuter, TestConsumedIDNotReused
func TestWorkflow22(t *testing.T) { runWorkflow(t, 22) }

// Verifies: NUT-SP-005, NUT-TX-001
// Depends-On: TestReleaseKeepsKV, TestReleasedIDInvalid
func TestWorkflow23(t *testing.T) { runWorkflow(t, 23) }

// Verifies: NUT-RB-001, NUT-CV-002
// Depends-On: TestRollbackRestoresKVOverwrite, TestWriteAfterRollbackTo
func TestWorkflow24(t *testing.T) { runWorkflow(t, 24) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketCreate, TestRollbackDropsBucketDelete
func TestWorkflow25(t *testing.T) { runWorkflow(t, 25) }

// Verifies: NUT-RB-003, NUT-CV-003
// Depends-On: TestRollbackRestoresList, TestRollbackRestoresSet
func TestWorkflow26(t *testing.T) { runWorkflow(t, 26) }

// Verifies: NUT-RB-002, NUT-CV-003
// Depends-On: TestRollbackInvalidatesYounger, TestRollbackRestoresSortedSet
func TestWorkflow27(t *testing.T) { runWorkflow(t, 27) }

// Verifies: NUT-DS-003, NUT-CV-004
// Depends-On: TestRollbackDropsBucketDelete, TestWriteAfterRollbackTo
func TestWorkflow28(t *testing.T) { runWorkflow(t, 28) }

// Verifies: NUT-SP-005, NUT-CV-002
// Depends-On: TestReleasePreservesWrites, TestReleaseKeepsKV
func TestWorkflow29(t *testing.T) { runWorkflow(t, 29) }

// Verifies: NUT-RB-001, NUT-TX-001, NUT-CV-005
// Depends-On: TestRollbackRestoresTTL, TestRollbackRestoresKVOverwrite
func TestWorkflow30(t *testing.T) { runWorkflow(t, 30) }

// Verifies: NUT-TX-003, NUT-CV-006
// Depends-On: TestRollbackRestoresKVOverwrite, TestRollbackConsumesTarget
func TestWatchReceivesRetainedValue(t *testing.T) {
	db := openWatchDB(t)
	messages := make(chan *nutsdb.Message, 1)
	watchDone := make(chan error, 1)
	errStop := errors.New("stop after retained event")
	go func() {
		watchDone <- db.Watch("kv", []byte("watched"), func(message *nutsdb.Message) error {
			messages <- message
			return errStop
		})
	}()
	time.Sleep(50 * time.Millisecond)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err := tx.Put("kv", []byte("watched"), []byte("retained"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	sp, err := tx.Savepoint()
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Put("kv", []byte("watched"), []byte("discarded"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.RollbackTo(sp); err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
	select {
	case message := <-messages:
		if message.Key != "watched" || !bytes.Equal(message.Value, []byte("retained")) {
			t.Fatalf("message key=%q value=%q", message.Key, message.Value)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("retained watch event not delivered")
	}
	if err := <-watchDone; !errors.Is(err, errStop) {
		t.Fatalf("watch error=%v", err)
	}
}

// Verifies: NUT-TX-003, NUT-CV-006
// Depends-On: TestRollbackDropsBucketCreate, TestWriteAfterRollbackTo
func TestWatchOmitsDiscardedValue(t *testing.T) {
	db := openWatchDB(t)
	messages := make(chan *nutsdb.Message, 1)
	watchDone := make(chan error, 1)
	go func() {
		watchDone <- db.Watch("kv", []byte("discarded"), func(message *nutsdb.Message) error {
			messages <- message
			return nil
		})
	}()
	time.Sleep(50 * time.Millisecond)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	sp, err := tx.Savepoint()
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Put("kv", []byte("discarded"), []byte("never-visible"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.RollbackTo(sp); err != nil {
		t.Fatal(err)
	}
	if err := tx.Put("kv", []byte("other"), []byte("committed"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
	select {
	case message := <-messages:
		t.Fatalf("discarded event delivered: key=%q value=%q", message.Key, message.Value)
	case <-time.After(350 * time.Millisecond):
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	select {
	case err := <-watchDone:
		if err != nil {
			t.Fatalf("watch close error=%v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("watch did not finish after close")
	}
}
