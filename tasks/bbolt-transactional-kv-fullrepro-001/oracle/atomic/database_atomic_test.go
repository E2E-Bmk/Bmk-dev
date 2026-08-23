package atomic

import (
	"bytes"
	"errors"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	bolt "go.etcd.io/bbolt"
)

var bucketName = []byte("items")

func openDB(t *testing.T) *bolt.DB {
	t.Helper()
	db, err := bolt.Open(filepath.Join(t.TempDir(), "db.bolt"), 0600, nil)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func seed(t *testing.T, db *bolt.DB, pairs map[string]string) {
	t.Helper()
	if err := db.Update(func(tx *bolt.Tx) error {
		b, err := tx.CreateBucketIfNotExists(bucketName)
		if err != nil {
			return err
		}
		for k, v := range pairs {
			if err := b.Put([]byte(k), []byte(v)); err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
}

// Verifies: BOLT-001
func TestOpenCreatesDatabaseAndReportsPath(t *testing.T) {
	path := filepath.Join(t.TempDir(), "new.db")
	db, err := bolt.Open(path, 0600, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if db.Path() != path {
		t.Fatalf("path=%q", db.Path())
	}
}

// Verifies: BOLT-002
func TestCloseTwiceSucceeds(t *testing.T) {
	db := openDB(t)
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-002
func TestClosedDatabaseRejectsView(t *testing.T) {
	db := openDB(t)
	_ = db.Close()
	err := db.View(func(*bolt.Tx) error { return nil })
	if !errors.Is(err, bolt.ErrDatabaseNotOpen) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-003
func TestConflictingOpenTimesOut(t *testing.T) {
	path := filepath.Join(t.TempDir(), "lock.db")
	db, err := bolt.Open(path, 0600, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	other, err := bolt.Open(path, 0600, &bolt.Options{Timeout: 25 * time.Millisecond})
	if other != nil {
		other.Close()
	}
	if !errors.Is(err, bolt.ErrTimeout) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-004
func TestReadOnlyDatabaseRejectsWriter(t *testing.T) {
	path := filepath.Join(t.TempDir(), "ro.db")
	db, err := bolt.Open(path, 0600, nil)
	if err != nil {
		t.Fatal(err)
	}
	seed(t, db, map[string]string{"a": "1"})
	db.Close()
	ro, err := bolt.Open(path, 0600, &bolt.Options{ReadOnly: true, Timeout: time.Second})
	if err != nil {
		t.Fatal(err)
	}
	defer ro.Close()
	if !ro.IsReadOnly() {
		t.Fatal("not readonly")
	}
	tx, err := ro.Begin(true)
	if tx != nil || !errors.Is(err, bolt.ErrDatabaseReadOnly) {
		t.Fatalf("tx=%v err=%v", tx, err)
	}
}

// Verifies: BOLT-005
func TestSyncOpenDatabase(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"a": "1"})
	if err := db.Sync(); err != nil {
		t.Fatal(err)
	}
}

// Verifies: BOLT-006
func TestUpdateCommits(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"a": "1"})
	if err := db.View(func(tx *bolt.Tx) error {
		if string(tx.Bucket(bucketName).Get([]byte("a"))) != "1" {
			t.Fatal("missing")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
}

// Verifies: BOLT-006, BOLT-061
func TestUpdateErrorRollsBackAndPropagates(t *testing.T) {
	db := openDB(t)
	sent := errors.New("stop")
	err := db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(bucketName)
		_ = b.Put([]byte("a"), []byte("1"))
		return sent
	})
	if !errors.Is(err, sent) {
		t.Fatalf("err=%v", err)
	}
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(bucketName) != nil {
			t.Fatal("committed")
		}
		return nil
	})
}

// Verifies: BOLT-007
func TestViewIsReadOnly(t *testing.T) {
	db := openDB(t)
	seed(t, db, nil)
	err := db.View(func(tx *bolt.Tx) error { return tx.Bucket(bucketName).Put([]byte("a"), []byte("1")) })
	if !errors.Is(err, bolt.ErrTxNotWritable) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-008
func TestManualCommit(t *testing.T) {
	db := openDB(t)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	b, _ := tx.CreateBucket(bucketName)
	_ = b.Put([]byte("a"), []byte("1"))
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	_ = db.View(func(tx *bolt.Tx) error {
		if string(tx.Bucket(bucketName).Get([]byte("a"))) != "1" {
			t.Fatal("missing")
		}
		return nil
	})
}

// Verifies: BOLT-009
func TestManualRollback(t *testing.T) {
	db := openDB(t)
	tx, _ := db.Begin(true)
	tx.CreateBucket(bucketName)
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(bucketName) != nil {
			t.Fatal("persisted")
		}
		return nil
	})
}

// Verifies: BOLT-010
func TestTransactionClosedSentinel(t *testing.T) {
	db := openDB(t)
	tx, _ := db.Begin(true)
	_ = tx.Rollback()
	if !errors.Is(tx.Rollback(), bolt.ErrTxClosed) {
		t.Fatal("rollback")
	}
	if !errors.Is(tx.Commit(), bolt.ErrTxClosed) {
		t.Fatal("commit")
	}
}

// Verifies: BOLT-011, BOLT-063
func TestTransactionProperties(t *testing.T) {
	db := openDB(t)
	tx, _ := db.Begin(true)
	defer tx.Rollback()
	if !tx.Writable() || tx.DB() != db || tx.ID() <= 0 || tx.Size() < 0 {
		t.Fatalf("id=%d size=%d", tx.ID(), tx.Size())
	}
}

// Verifies: BOLT-012
func TestWritableTransactionIDsIncrease(t *testing.T) {
	db := openDB(t)
	tx1, _ := db.Begin(true)
	id1 := tx1.ID()
	_ = tx1.Commit()
	tx2, _ := db.Begin(true)
	id2 := tx2.ID()
	_ = tx2.Rollback()
	if id2 <= id1 {
		t.Fatalf("%d %d", id1, id2)
	}
}

// Verifies: BOLT-013
func TestOnCommitTiming(t *testing.T) {
	db := openDB(t)
	calls := 0
	tx, _ := db.Begin(true)
	tx.OnCommit(func() { calls++ })
	if calls != 0 {
		t.Fatal("early")
	}
	_ = tx.Commit()
	if calls != 1 {
		t.Fatalf("calls=%d", calls)
	}
	tx, _ = db.Begin(true)
	tx.OnCommit(func() { calls++ })
	_ = tx.Rollback()
	if calls != 1 {
		t.Fatal("rollback callback")
	}
}

// Verifies: BOLT-015
func TestCreateBucketDuplicate(t *testing.T) {
	db := openDB(t)
	err := db.Update(func(tx *bolt.Tx) error {
		if _, e := tx.CreateBucket(bucketName); e != nil {
			return e
		}
		_, e := tx.CreateBucket(bucketName)
		return e
	})
	if !errors.Is(err, bolt.ErrBucketExists) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-016
func TestCreateBucketIfNotExistsReuses(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		a, e := tx.CreateBucketIfNotExists(bucketName)
		if e != nil {
			return e
		}
		b, e := tx.CreateBucketIfNotExists(bucketName)
		if e != nil {
			return e
		}
		if a == nil || b == nil {
			t.Fatal("nil")
		}
		return nil
	})
}

// Verifies: BOLT-017
func TestBlankBucketNameRejected(t *testing.T) {
	db := openDB(t)
	err := db.Update(func(tx *bolt.Tx) error { _, e := tx.CreateBucket(nil); return e })
	if !errors.Is(err, bolt.ErrBucketNameRequired) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-018, BOLT-019
func TestDeleteBucketLifecycle(t *testing.T) {
	db := openDB(t)
	seed(t, db, nil)
	if err := db.Update(func(tx *bolt.Tx) error { return tx.DeleteBucket(bucketName) }); err != nil {
		t.Fatal(err)
	}
	err := db.Update(func(tx *bolt.Tx) error { return tx.DeleteBucket(bucketName) })
	if !errors.Is(err, bolt.ErrBucketNotFound) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-020
func TestTopLevelBucketEnumeration(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error { tx.CreateBucket([]byte("b")); tx.CreateBucket([]byte("a")); return nil })
	var got []string
	_ = db.View(func(tx *bolt.Tx) error {
		return tx.ForEach(func(k []byte, b *bolt.Bucket) error { got = append(got, string(k)); return nil })
	})
	if !reflect.DeepEqual(got, []string{"a", "b"}) {
		t.Fatal(got)
	}
}

// Verifies: BOLT-021, BOLT-022
func TestNestedBucketEnumeration(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		p, _ := tx.CreateBucket(bucketName)
		p.CreateBucket([]byte("z"))
		p.CreateBucket([]byte("a"))
		return nil
	})
	var got []string
	_ = db.View(func(tx *bolt.Tx) error {
		return tx.Bucket(bucketName).ForEachBucket(func(k []byte) error { got = append(got, string(k)); return nil })
	})
	if !reflect.DeepEqual(got, []string{"a", "z"}) {
		t.Fatal(got)
	}
}

// Verifies: BOLT-023
func TestBucketOwnerProperties(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(bucketName)
		if b.Tx() != tx || !b.Writable() {
			t.Fatal("owner")
		}
		return nil
	})
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(bucketName).Writable() {
			t.Fatal("readonly")
		}
		return nil
	})
}

// Verifies: BOLT-024
func TestValueBucketCollision(t *testing.T) {
	db := openDB(t)
	err := db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(bucketName)
		_ = b.Put([]byte("x"), []byte("v"))
		_, e := b.CreateBucket([]byte("x"))
		return e
	})
	if !errors.Is(err, bolt.ErrIncompatibleValue) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-025
func TestPutGetReplace(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(bucketName)
		_ = b.Put([]byte("k"), []byte("one"))
		_ = b.Put([]byte("k"), []byte("two"))
		if string(b.Get([]byte("k"))) != "two" {
			t.Fatal("replace")
		}
		return nil
	})
}

// Verifies: BOLT-026
func TestEmptyKeyRejected(t *testing.T) {
	db := openDB(t)
	seed(t, db, nil)
	err := db.Update(func(tx *bolt.Tx) error { return tx.Bucket(bucketName).Put(nil, []byte("v")) })
	if !errors.Is(err, bolt.ErrKeyRequired) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-027
func TestEmptyValueDistinctFromMissing(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"empty": ""})
	_ = db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(bucketName)
		if b.Get([]byte("empty")) == nil {
			t.Fatal("empty missing")
		}
		if b.Get([]byte("absent")) != nil {
			t.Fatal("absent")
		}
		return nil
	})
}

// Verifies: BOLT-028
func TestDeleteValueAndAbsent(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"a": "1"})
	_ = db.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket(bucketName)
		if err := b.Delete([]byte("a")); err != nil {
			return err
		}
		return b.Delete([]byte("absent"))
	})
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(bucketName).Get([]byte("a")) != nil {
			t.Fatal("present")
		}
		return nil
	})
}

// Verifies: BOLT-032, BOLT-033
func TestCursorBoundariesAndMovement(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"b": "2", "a": "1", "c": "3"})
	_ = db.View(func(tx *bolt.Tx) error {
		c := tx.Bucket(bucketName).Cursor()
		k, _ := c.First()
		if string(k) != "a" {
			t.Fatal(string(k))
		}
		k, _ = c.Next()
		if string(k) != "b" {
			t.Fatal(string(k))
		}
		k, _ = c.Last()
		if string(k) != "c" {
			t.Fatal(string(k))
		}
		k, _ = c.Prev()
		if string(k) != "b" {
			t.Fatal(string(k))
		}
		return nil
	})
}

// Verifies: BOLT-034
func TestCursorSeek(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"a": "1", "c": "3", "e": "5"})
	_ = db.View(func(tx *bolt.Tx) error {
		k, v := tx.Bucket(bucketName).Cursor().Seek([]byte("b"))
		if string(k) != "c" || string(v) != "3" {
			t.Fatalf("%q %q", k, v)
		}
		return nil
	})
}

// Verifies: BOLT-036
func TestCursorDeleteValue(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"a": "1", "b": "2"})
	_ = db.Update(func(tx *bolt.Tx) error { c := tx.Bucket(bucketName).Cursor(); c.First(); return c.Delete() })
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(bucketName).Get([]byte("a")) != nil {
			t.Fatal("not deleted")
		}
		return nil
	})
}

// Verifies: BOLT-038
func TestForEachOrderedAndError(t *testing.T) {
	db := openDB(t)
	seed(t, db, map[string]string{"b": "2", "a": "1"})
	sent := errors.New("stop")
	var got []string
	err := db.View(func(tx *bolt.Tx) error {
		return tx.Bucket(bucketName).ForEach(func(k, v []byte) error {
			got = append(got, string(k))
			if bytes.Equal(k, []byte("b")) {
				return sent
			}
			return nil
		})
	})
	if !errors.Is(err, sent) || !reflect.DeepEqual(got, []string{"a", "b"}) {
		t.Fatalf("%v %v", got, err)
	}
}

// Verifies: BOLT-041
func TestBucketSequence(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(bucketName)
		if err := b.SetSequence(40); err != nil {
			return err
		}
		n, err := b.NextSequence()
		if err != nil {
			return err
		}
		if n != 41 || b.Sequence() != 41 {
			t.Fatalf("n=%d seq=%d", n, b.Sequence())
		}
		return nil
	})
}

// Verifies: BOLT-052
func TestBucketStatsRelationships(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(bucketName)
		_ = b.Put([]byte("a"), []byte("1"))
		_, _ = b.CreateBucket([]byte("child"))
		return nil
	})
	_ = db.View(func(tx *bolt.Tx) error {
		s := tx.Bucket(bucketName).Stats()
		if s.KeyN < 2 || s.BucketN < 2 {
			t.Fatalf("%+v", s)
		}
		return nil
	})
}
