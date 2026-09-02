package atomic_test

import (
	"bytes"
	"errors"
	"fmt"
	"testing"

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
		db.Close()
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func mustWriteTx(t *testing.T, db *nutsdb.DB) *nutsdb.Tx {
	t.Helper()
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = tx.Rollback() })
	return tx
}

func expectKV(t *testing.T, db *nutsdb.DB, key, want []byte) {
	t.Helper()
	err := db.View(func(tx *nutsdb.Tx) error {
		got, err := tx.Get("kv", key)
		if err != nil {
			return err
		}
		if !bytes.Equal(got, want) {
			return fmt.Errorf("value=%q want=%q", got, want)
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

func checkView(t *testing.T, db *nutsdb.DB, fn func(*nutsdb.Tx) error) {
	t.Helper()
	if err := db.View(fn); err != nil {
		t.Fatal(err)
	}
}

func runAtomic(t *testing.T, n int) {
	db := openDB(t)
	switch n {
	case 1:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		d, err := tx.SavepointDepth()
		if err != nil || d != 0 {
			t.Fatalf("depth=%d err=%v", d, err)
		}
	case 2:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		id, err := tx.Savepoint()
		if err != nil || id == 0 {
			t.Fatalf("id=%d err=%v", id, err)
		}
	case 3:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		a, _ := tx.Savepoint()
		b, _ := tx.Savepoint()
		if b <= a {
			t.Fatalf("ids %d %d", a, b)
		}
	case 4:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		_, _ = tx.Savepoint()
		_, _ = tx.Savepoint()
		d, _ := tx.SavepointDepth()
		if d != 2 {
			t.Fatalf("depth=%d", d)
		}
	case 5:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		id, _ := tx.Savepoint()
		if err := tx.ReleaseSavepoint(id); err != nil {
			t.Fatal(err)
		}
		d, _ := tx.SavepointDepth()
		if d != 0 {
			t.Fatalf("depth=%d", d)
		}
	case 6:
		tx := mustWriteTx(t, db)
		_ = tx.Put("kv", []byte("k"), []byte("v"), nutsdb.Persistent)
		id, _ := tx.Savepoint()
		_ = tx.Put("kv", []byte("x"), []byte("y"), nutsdb.Persistent)
		if err := tx.ReleaseSavepoint(id); err != nil {
			t.Fatal(err)
		}
		if err := tx.Commit(); err != nil {
			t.Fatal(err)
		}
		expectKV(t, db, []byte("x"), []byte("y"))
	case 7:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		if err := tx.RollbackTo(id); err != nil {
			t.Fatal(err)
		}
		d, _ := tx.SavepointDepth()
		if d != 0 {
			t.Fatalf("depth=%d", d)
		}
		_ = tx.Rollback()
	case 8:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.RollbackTo(id)
		if !errors.Is(tx.RollbackTo(id), nutsdb.ErrSavepointNotFound) {
			t.Fatal("consumed id accepted")
		}
		_ = tx.Rollback()
	case 9:
		tx := mustWriteTx(t, db)
		outer, _ := tx.Savepoint()
		inner, _ := tx.Savepoint()
		_ = tx.RollbackTo(outer)
		if !errors.Is(tx.RollbackTo(inner), nutsdb.ErrSavepointNotFound) {
			t.Fatal("younger id accepted")
		}
		_ = tx.Rollback()
	case 10:
		tx := mustWriteTx(t, db)
		outer, _ := tx.Savepoint()
		_, _ = tx.Savepoint()
		if !errors.Is(tx.ReleaseSavepoint(outer), nutsdb.ErrSavepointNotTopmost) {
			t.Fatal("wrong error")
		}
		d, _ := tx.SavepointDepth()
		if d != 2 {
			t.Fatalf("depth=%d", d)
		}
		_ = tx.Rollback()
	case 11:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		if !errors.Is(tx.RollbackTo(999), nutsdb.ErrSavepointNotFound) {
			t.Fatal("wrong error")
		}
	case 12:
		tx := mustWriteTx(t, db)
		defer tx.Rollback()
		if !errors.Is(tx.ReleaseSavepoint(999), nutsdb.ErrSavepointNotFound) {
			t.Fatal("wrong error")
		}
	case 13:
		tx, _ := db.Begin(false)
		defer tx.Rollback()
		if _, err := tx.Savepoint(); !errors.Is(err, nutsdb.ErrTxNotWritable) {
			t.Fatalf("err=%v", err)
		}
		_ = tx.Rollback()
	case 14:
		tx, _ := db.Begin(false)
		defer tx.Rollback()
		if err := tx.RollbackTo(1); !errors.Is(err, nutsdb.ErrTxNotWritable) {
			t.Fatalf("err=%v", err)
		}
		_ = tx.Rollback()
	case 15:
		tx, _ := db.Begin(false)
		defer tx.Rollback()
		if err := tx.ReleaseSavepoint(1); !errors.Is(err, nutsdb.ErrTxNotWritable) {
			t.Fatalf("err=%v", err)
		}
		_ = tx.Rollback()
	case 16:
		tx, _ := db.Begin(false)
		defer tx.Rollback()
		d, err := tx.SavepointDepth()
		if err != nil || d != 0 {
			t.Fatalf("depth=%d err=%v", d, err)
		}
		_ = tx.Rollback()
	case 17:
		tx := mustWriteTx(t, db)
		_ = tx.Commit()
		if _, err := tx.Savepoint(); !errors.Is(err, nutsdb.ErrTxClosed) {
			t.Fatalf("err=%v", err)
		}
	case 18:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.Commit()
		if err := tx.RollbackTo(id); !errors.Is(err, nutsdb.ErrTxClosed) {
			t.Fatalf("err=%v", err)
		}
	case 19:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.Rollback()
		if err := tx.ReleaseSavepoint(id); !errors.Is(err, nutsdb.ErrTxClosed) {
			t.Fatalf("err=%v", err)
		}
	case 20:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.Put("kv", []byte("drop"), []byte("x"), nutsdb.Persistent)
		_ = tx.RollbackTo(id)
		_ = tx.Put("kv", []byte("keep"), []byte("y"), nutsdb.Persistent)
		_ = tx.Commit()
		expectKV(t, db, []byte("keep"), []byte("y"))
	case 21:
		tx := mustWriteTx(t, db)
		_ = tx.Put("kv", []byte("k"), []byte("old"), nutsdb.Persistent)
		id, _ := tx.Savepoint()
		_ = tx.Put("kv", []byte("k"), []byte("new"), nutsdb.Persistent)
		_ = tx.RollbackTo(id)
		got, err := tx.Get("kv", []byte("k"))
		if err != nil || !bytes.Equal(got, []byte("old")) {
			t.Fatalf("got=%q err=%v", got, err)
		}
		_ = tx.Rollback()
	case 22:
		tx := mustWriteTx(t, db)
		_ = tx.Put("kv", []byte("k"), []byte("old"), nutsdb.Persistent)
		id, _ := tx.Savepoint()
		_ = tx.Delete("kv", []byte("k"))
		_ = tx.RollbackTo(id)
		got, err := tx.Get("kv", []byte("k"))
		if err != nil || !bytes.Equal(got, []byte("old")) {
			t.Fatalf("got=%q err=%v", got, err)
		}
		_ = tx.Rollback()
	case 23:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.Put("kv", []byte("k"), []byte("v"), nutsdb.Persistent)
		_ = tx.ReleaseSavepoint(id)
		_ = tx.Commit()
		expectKV(t, db, []byte("k"), []byte("v"))
	case 24:
		tx := mustWriteTx(t, db)
		_ = tx.Put("kv", []byte("k"), []byte("v"), 120)
		id, _ := tx.Savepoint()
		_ = tx.Put("kv", []byte("k"), []byte("v2"), nutsdb.Persistent)
		_ = tx.RollbackTo(id)
		ttl, err := tx.GetTTL("kv", []byte("k"))
		if err != nil || ttl <= 0 {
			t.Fatalf("ttl=%d err=%v", ttl, err)
		}
		_ = tx.Rollback()
	case 25:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.NewKVBucket("temporary")
		_ = tx.RollbackTo(id)
		_ = tx.Commit()
		checkView(t, db, func(v *nutsdb.Tx) error {
			if v.ExistBucket(nutsdb.DataStructureBTree, "temporary") {
				return errors.New("bucket persisted")
			}
			return nil
		})
	case 26:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.DeleteBucket(nutsdb.DataStructureBTree, "kv")
		_ = tx.RollbackTo(id)
		_ = tx.Commit()
		checkView(t, db, func(v *nutsdb.Tx) error {
			if !v.ExistBucket(nutsdb.DataStructureBTree, "kv") {
				return errors.New("bucket deleted")
			}
			return nil
		})
	case 27:
		tx := mustWriteTx(t, db)
		_ = tx.LPush("lists", []byte("k"), []byte("keep"))
		id, _ := tx.Savepoint()
		_ = tx.LPush("lists", []byte("k"), []byte("drop"))
		_ = tx.RollbackTo(id)
		_ = tx.Commit()
		checkView(t, db, func(v *nutsdb.Tx) error {
			got, err := v.LRange("lists", []byte("k"), 0, -1)
			if err != nil || len(got) != 1 || !bytes.Equal(got[0], []byte("keep")) {
				return fmt.Errorf("got=%q err=%v", got, err)
			}
			return nil
		})
	case 28:
		tx := mustWriteTx(t, db)
		_ = tx.SAdd("sets", []byte("k"), []byte("keep"))
		id, _ := tx.Savepoint()
		_ = tx.SAdd("sets", []byte("k"), []byte("drop"))
		_ = tx.RollbackTo(id)
		_ = tx.Commit()
		checkView(t, db, func(v *nutsdb.Tx) error {
			got, err := v.SMembers("sets", []byte("k"))
			if err != nil || len(got) != 1 || !bytes.Equal(got[0], []byte("keep")) {
				return fmt.Errorf("got=%q err=%v", got, err)
			}
			return nil
		})
	case 29:
		tx := mustWriteTx(t, db)
		_ = tx.ZAdd("zsets", []byte("k"), 1, []byte("keep"))
		id, _ := tx.Savepoint()
		_ = tx.ZAdd("zsets", []byte("k"), 2, []byte("drop"))
		_ = tx.RollbackTo(id)
		_ = tx.Commit()
		checkView(t, db, func(v *nutsdb.Tx) error {
			got, err := v.ZMembers("zsets", []byte("k"))
			if err != nil || len(got) != 1 {
				return fmt.Errorf("len=%d err=%v", len(got), err)
			}
			for m := range got {
				if !bytes.Equal(m.Value, []byte("keep")) || m.Score != 1 {
					return fmt.Errorf("member=%q score=%v", m.Value, m.Score)
				}
			}
			return nil
		})
	case 30:
		tx := mustWriteTx(t, db)
		a, _ := tx.Savepoint()
		b, _ := tx.Savepoint()
		_ = tx.RollbackTo(b)
		d, _ := tx.SavepointDepth()
		if d != 1 {
			t.Fatalf("depth=%d", d)
		}
		if err := tx.ReleaseSavepoint(a); err != nil {
			t.Fatal(err)
		}
		_ = tx.Rollback()
	case 31:
		tx := mustWriteTx(t, db)
		a, _ := tx.Savepoint()
		_ = tx.RollbackTo(a)
		b, _ := tx.Savepoint()
		if b <= a {
			t.Fatalf("reused id %d %d", a, b)
		}
		_ = tx.Rollback()
	case 32:
		tx := mustWriteTx(t, db)
		id, _ := tx.Savepoint()
		_ = tx.ReleaseSavepoint(id)
		if !errors.Is(tx.ReleaseSavepoint(id), nutsdb.ErrSavepointNotFound) {
			t.Fatal("released id accepted")
		}
		_ = tx.Rollback()
	}
}

// Verifies: NUT-SP-004
func TestInitialDepth(t *testing.T) { runAtomic(t, 1) }

// Verifies: NUT-SP-001
func TestFirstIDNonZero(t *testing.T) { runAtomic(t, 2) }

// Verifies: NUT-SP-002
func TestIDsIncrease(t *testing.T) { runAtomic(t, 3) }

// Verifies: NUT-SP-004
func TestDepthIncrements(t *testing.T) { runAtomic(t, 4) }

// Verifies: NUT-SP-005, NUT-SP-004
func TestReleaseDecrementsDepth(t *testing.T) { runAtomic(t, 5) }

// Verifies: NUT-SP-005
func TestReleasePreservesWrites(t *testing.T) { runAtomic(t, 6) }

// Verifies: NUT-RB-002, NUT-SP-004
func TestRollbackConsumesTarget(t *testing.T) { runAtomic(t, 7) }

// Verifies: NUT-SP-007
func TestRolledBackIDInvalid(t *testing.T) { runAtomic(t, 8) }

// Verifies: NUT-RB-002
func TestRollbackInvalidatesYounger(t *testing.T) { runAtomic(t, 9) }

// Verifies: NUT-SP-006
func TestReleaseRejectsNonTopmost(t *testing.T) { runAtomic(t, 10) }

// Verifies: NUT-SP-007
func TestRollbackUnknownID(t *testing.T) { runAtomic(t, 11) }

// Verifies: NUT-SP-007
func TestReleaseUnknownID(t *testing.T) { runAtomic(t, 12) }

// Verifies: NUT-TX-004
func TestReadOnlySavepointRejected(t *testing.T) { runAtomic(t, 13) }

// Verifies: NUT-TX-004
func TestReadOnlyRollbackToRejected(t *testing.T) { runAtomic(t, 14) }

// Verifies: NUT-TX-004
func TestReadOnlyReleaseRejected(t *testing.T) { runAtomic(t, 15) }

// Verifies: NUT-SP-004, NUT-TX-004
func TestReadOnlyDepthZero(t *testing.T) { runAtomic(t, 16) }

// Verifies: NUT-TX-002
func TestSavepointAfterCommitClosed(t *testing.T) { runAtomic(t, 17) }

// Verifies: NUT-TX-002
func TestRollbackToAfterCommitClosed(t *testing.T) { runAtomic(t, 18) }

// Verifies: NUT-TX-002
func TestReleaseAfterRollbackClosed(t *testing.T) { runAtomic(t, 19) }

// Verifies: NUT-RB-004
func TestWriteAfterRollbackTo(t *testing.T) { runAtomic(t, 20) }

// Verifies: NUT-RB-001, NUT-DS-001
func TestRollbackRestoresKVOverwrite(t *testing.T) { runAtomic(t, 21) }

// Verifies: NUT-RB-001, NUT-DS-001
func TestRollbackRestoresDeletedKV(t *testing.T) { runAtomic(t, 22) }

// Verifies: NUT-SP-005, NUT-TX-001
func TestReleaseKeepsKV(t *testing.T) { runAtomic(t, 23) }

// Verifies: NUT-DS-001, NUT-CV-005
func TestRollbackRestoresTTL(t *testing.T) { runAtomic(t, 24) }

// Verifies: NUT-DS-003
func TestRollbackDropsBucketCreate(t *testing.T) { runAtomic(t, 25) }

// Verifies: NUT-DS-003
func TestRollbackDropsBucketDelete(t *testing.T) { runAtomic(t, 26) }

// Verifies: NUT-DS-002
func TestRollbackRestoresList(t *testing.T) { runAtomic(t, 27) }

// Verifies: NUT-DS-002
func TestRollbackRestoresSet(t *testing.T) { runAtomic(t, 28) }

// Verifies: NUT-DS-002
func TestRollbackRestoresSortedSet(t *testing.T) { runAtomic(t, 29) }

// Verifies: NUT-RB-003, NUT-CV-001
func TestInnerRollbackLeavesOuter(t *testing.T) { runAtomic(t, 30) }

// Verifies: NUT-SP-003
func TestConsumedIDNotReused(t *testing.T) { runAtomic(t, 31) }

// Verifies: NUT-SP-007
func TestReleasedIDInvalid(t *testing.T) { runAtomic(t, 32) }
