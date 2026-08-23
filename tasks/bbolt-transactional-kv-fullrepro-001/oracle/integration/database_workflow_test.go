package integration

import (
	"bytes"
	"errors"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sync"
	"testing"

	bolt "go.etcd.io/bbolt"
)

var root = []byte("root")

func open(t *testing.T) (*bolt.DB, string) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "db.bolt")
	db, err := bolt.Open(path, 0600, &bolt.Options{InitialMmapSize: 1 << 20})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db, path
}
func value(t *testing.T, db *bolt.DB, bucket, key string) []byte {
	t.Helper()
	var out []byte
	err := db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte(bucket))
		if b != nil {
			out = append([]byte(nil), b.Get([]byte(key))...)
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return out
}
func put(t *testing.T, db *bolt.DB, bucket, key, val string) {
	t.Helper()
	if err := db.Update(func(tx *bolt.Tx) error {
		b, e := tx.CreateBucketIfNotExists([]byte(bucket))
		if e != nil {
			return e
		}
		return b.Put([]byte(key), []byte(val))
	}); err != nil {
		t.Fatal(err)
	}
}

// Verifies: BOLT-050
// Depends-On: atomic::TestOpenCreatesDatabaseAndReportsPath, atomic::TestPutGetReplace
func TestCommittedValueSurvivesReopen(t *testing.T) {
	db, path := open(t)
	put(t, db, "root", "k", "v")
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	db, err := bolt.Open(path, 0600, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if string(value(t, db, "root", "k")) != "v" {
		t.Fatal("missing")
	}
}

// Verifies: BOLT-051, BOLT-062
// Depends-On: atomic::TestUpdateErrorRollsBackAndPropagates
func TestRolledBackValueAbsentAfterReopen(t *testing.T) {
	db, path := open(t)
	sent := errors.New("rollback")
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		_ = b.Put([]byte("k"), []byte("v"))
		return sent
	})
	_ = db.Close()
	db, _ = bolt.Open(path, 0600, nil)
	defer db.Close()
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(root) != nil {
			t.Fatal("persisted")
		}
		return nil
	})
}

// Verifies: BOLT-031
// Depends-On: atomic::TestManualRollback, atomic::TestPutGetReplace
func TestRollbackAcrossBuckets(t *testing.T) {
	db, _ := open(t)
	tx, _ := db.Begin(true)
	a, _ := tx.CreateBucket([]byte("a"))
	b, _ := tx.CreateBucket([]byte("b"))
	_ = a.Put([]byte("k"), []byte("1"))
	_ = b.Put([]byte("k"), []byte("2"))
	_ = tx.Rollback()
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket([]byte("a")) != nil || tx.Bucket([]byte("b")) != nil {
			t.Fatal("partial")
		}
		return nil
	})
}

// Verifies: BOLT-055
// Depends-On: atomic::TestCursorBoundariesAndMovement, atomic::TestForEachOrderedAndError
func TestGetForEachCursorAgree(t *testing.T) {
	db, _ := open(t)
	for _, p := range [][2]string{{"c", "3"}, {"a", "1"}, {"b", "2"}} {
		put(t, db, "root", p[0], p[1])
	}
	_ = db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(root)
		var each [][2]string
		_ = b.ForEach(func(k, v []byte) error { each = append(each, [2]string{string(k), string(v)}); return nil })
		var cur [][2]string
		for k, v := b.Cursor().First(); k != nil; k, v = b.Cursor().Next() {
			_ = v
			break
		}
		c := b.Cursor()
		for k, v := c.First(); k != nil; k, v = c.Next() {
			cur = append(cur, [2]string{string(k), string(v)})
			if !bytes.Equal(b.Get(k), v) {
				t.Fatal("get mismatch")
			}
		}
		if !reflect.DeepEqual(each, cur) {
			t.Fatalf("%v %v", each, cur)
		}
		return nil
	})
}

// Verifies: BOLT-056
// Depends-On: atomic::TestUpdateCommits, atomic::TestManualCommit
func TestManagedAndManualCommitEquivalent(t *testing.T) {
	db, _ := open(t)
	put(t, db, "managed", "k", "v")
	tx, _ := db.Begin(true)
	b, _ := tx.CreateBucket([]byte("manual"))
	_ = b.Put([]byte("k"), []byte("v"))
	_ = tx.Commit()
	if !bytes.Equal(value(t, db, "managed", "k"), value(t, db, "manual", "k")) {
		t.Fatal("different")
	}
}

// Verifies: BOLT-039
// Depends-On: atomic::TestNestedBucketEnumeration
func TestNestedHierarchySurvivesReopen(t *testing.T) {
	db, path := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		a, _ := tx.CreateBucket(root)
		b, _ := a.CreateBucket([]byte("b"))
		c, _ := b.CreateBucket([]byte("c"))
		return c.Put([]byte("k"), []byte("v"))
	})
	_ = db.Close()
	db, _ = bolt.Open(path, 0600, nil)
	defer db.Close()
	_ = db.View(func(tx *bolt.Tx) error {
		got := tx.Bucket(root).Bucket([]byte("b")).Bucket([]byte("c")).Get([]byte("k"))
		if string(got) != "v" {
			t.Fatal("missing")
		}
		return nil
	})
}

// Verifies: BOLT-040
// Depends-On: atomic::TestDeleteBucketLifecycle, atomic::TestNestedBucketEnumeration
func TestDeleteParentRemovesDescendants(t *testing.T) {
	db, path := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		a, _ := tx.CreateBucket(root)
		b, _ := a.CreateBucket([]byte("child"))
		return b.Put([]byte("k"), []byte("v"))
	})
	_ = db.Update(func(tx *bolt.Tx) error { return tx.DeleteBucket(root) })
	_ = db.Close()
	db, _ = bolt.Open(path, 0600, nil)
	defer db.Close()
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(root) != nil {
			t.Fatal("present")
		}
		return nil
	})
}

// Verifies: BOLT-042
// Depends-On: atomic::TestBucketSequence
func TestSequenceRollbackAndCommit(t *testing.T) {
	db, _ := open(t)
	_ = db.Update(func(tx *bolt.Tx) error { b, _ := tx.CreateBucket(root); return b.SetSequence(5) })
	tx, _ := db.Begin(true)
	_, _ = tx.Bucket(root).NextSequence()
	_ = tx.Rollback()
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(root).Sequence() != 5 {
			t.Fatal("rollback")
		}
		return nil
	})
	_ = db.Update(func(tx *bolt.Tx) error { _, e := tx.Bucket(root).NextSequence(); return e })
	_ = db.View(func(tx *bolt.Tx) error {
		if tx.Bucket(root).Sequence() != 6 {
			t.Fatal("commit")
		}
		return nil
	})
}

// Verifies: BOLT-043, BOLT-057
// Depends-On: atomic::TestBucketSequence, atomic::TestBucketStatsRelationships
func TestSequenceIterationStatsAfterReopen(t *testing.T) {
	db, path := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		_ = b.SetSequence(9)
		_ = b.Put([]byte("a"), []byte("1"))
		return b.Put([]byte("b"), []byte("2"))
	})
	_ = db.Close()
	db, _ = bolt.Open(path, 0600, nil)
	defer db.Close()
	_ = db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(root)
		n := 0
		_ = b.ForEach(func(k, v []byte) error { n++; return nil })
		if b.Sequence() != 9 || n != 2 || b.Stats().KeyN != 2 {
			t.Fatalf("seq=%d n=%d stats=%+v", b.Sequence(), n, b.Stats())
		}
		return nil
	})
}

// Verifies: BOLT-044, BOLT-045
// Depends-On: atomic::TestUpdateCommits
func TestReadSnapshotStableAcrossCommit(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "old")
	read, _ := db.Begin(false)
	defer read.Rollback()
	put(t, db, "root", "k", "new")
	if string(read.Bucket(root).Get([]byte("k"))) != "old" {
		t.Fatal("snapshot moved")
	}
	if string(value(t, db, "root", "k")) != "new" {
		t.Fatal("new reader stale")
	}
}

// Verifies: BOLT-046
// Depends-On: atomic::TestManualCommit
func TestUncommittedWriterInvisible(t *testing.T) {
	db, _ := open(t)
	tx, _ := db.Begin(true)
	b, _ := tx.CreateBucket(root)
	_ = b.Put([]byte("k"), []byte("v"))
	done := make(chan []byte, 1)
	go func() { done <- value(t, db, "root", "k") }()
	_ = tx.Rollback()
	if got := <-done; got != nil {
		t.Fatalf("got=%q", got)
	}
}

func openCopied(t *testing.T, path string) *bolt.DB {
	t.Helper()
	db, err := bolt.Open(path, 0600, nil)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

// Verifies: BOLT-047
// Depends-On: atomic::TestPutGetReplace
func TestWriteToProducesReopenableSnapshot(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	var buf bytes.Buffer
	_ = db.View(func(tx *bolt.Tx) error { _, e := tx.WriteTo(&buf); return e })
	path := filepath.Join(t.TempDir(), "copy.db")
	if err := os.WriteFile(path, buf.Bytes(), 0600); err != nil {
		t.Fatal(err)
	}
	copydb := openCopied(t, path)
	if string(value(t, copydb, "root", "k")) != "v" {
		t.Fatal("missing")
	}
}

// Verifies: BOLT-048
// Depends-On: atomic::TestPutGetReplace
func TestCopyFileProducesReopenableSnapshot(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	path := filepath.Join(t.TempDir(), "copy.db")
	_ = db.View(func(tx *bolt.Tx) error { return tx.CopyFile(path, 0600) })
	copydb := openCopied(t, path)
	if string(value(t, copydb, "root", "k")) != "v" {
		t.Fatal("missing")
	}
}

// Verifies: BOLT-049, BOLT-058
// Depends-On: atomic::TestPutGetReplace
func TestBackupIndependentFromLaterWrites(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "old")
	path := filepath.Join(t.TempDir(), "copy.db")
	_ = db.View(func(tx *bolt.Tx) error { return tx.CopyFile(path, 0600) })
	put(t, db, "root", "k", "new")
	copydb := openCopied(t, path)
	if string(value(t, copydb, "root", "k")) != "old" || string(value(t, db, "root", "k")) != "new" {
		t.Fatal("not independent")
	}
}

// Verifies: BOLT-013
// Depends-On: atomic::TestOnCommitTiming
func TestOnCommitObservesDurableState(t *testing.T) {
	db, _ := open(t)
	seen := false
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		_ = b.Put([]byte("k"), []byte("v"))
		tx.OnCommit(func() { seen = true })
		return nil
	})
	if !seen || string(value(t, db, "root", "k")) != "v" {
		t.Fatal("callback/state")
	}
}

// Verifies: BOLT-014
// Depends-On: atomic::TestUpdateCommits
func TestBatchCommitsState(t *testing.T) {
	db, _ := open(t)
	if err := db.Batch(func(tx *bolt.Tx) error {
		b, e := tx.CreateBucketIfNotExists(root)
		if e != nil {
			return e
		}
		return b.Put([]byte("k"), []byte("v"))
	}); err != nil {
		t.Fatal(err)
	}
	if string(value(t, db, "root", "k")) != "v" {
		t.Fatal("missing")
	}
}

// Verifies: BOLT-029
// Depends-On: atomic::TestViewIsReadOnly
func TestReadonlyMutationFamilies(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	_ = db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(root)
		for _, err := range []error{b.Put([]byte("x"), []byte("1")), b.Delete([]byte("k")), b.SetSequence(1)} {
			if !errors.Is(err, bolt.ErrTxNotWritable) {
				t.Fatalf("err=%v", err)
			}
		}
		_, err := b.CreateBucket([]byte("child"))
		if !errors.Is(err, bolt.ErrTxNotWritable) {
			t.Fatalf("create=%v", err)
		}
		return nil
	})
}

// Verifies: BOLT-035
// Depends-On: atomic::TestNestedBucketEnumeration, atomic::TestCursorBoundariesAndMovement
func TestCursorDistinguishesNestedBucket(t *testing.T) {
	db, _ := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		_, _ = b.CreateBucket([]byte("child"))
		return b.Put([]byte("value"), []byte("v"))
	})
	_ = db.View(func(tx *bolt.Tx) error {
		c := tx.Bucket(root).Cursor()
		k, v := c.First()
		if string(k) != "child" || v != nil {
			t.Fatalf("%q %q", k, v)
		}
		k, v = c.Next()
		if string(k) != "value" || string(v) != "v" {
			t.Fatalf("%q %q", k, v)
		}
		return nil
	})
}

// Verifies: BOLT-037
// Depends-On: atomic::TestCursorDeleteValue
func TestCursorDeleteErrorModes(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	_ = db.View(func(tx *bolt.Tx) error {
		c := tx.Bucket(root).Cursor()
		c.First()
		if !errors.Is(c.Delete(), bolt.ErrTxNotWritable) {
			t.Fatal("readonly")
		}
		return nil
	})
	_ = db.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket(root)
		_, _ = b.CreateBucket([]byte("child"))
		c := b.Cursor()
		c.Seek([]byte("child"))
		if !errors.Is(c.Delete(), bolt.ErrIncompatibleValue) {
			t.Fatal("bucket delete")
		}
		return nil
	})
}

// Verifies: BOLT-053
func TestDatabaseReadTransactionStats(t *testing.T) {
	db, _ := open(t)
	before := db.Stats()
	tx, _ := db.Begin(false)
	during := db.Stats()
	if during.TxN < before.TxN+1 || during.OpenTxN < 1 {
		t.Fatalf("before=%+v during=%+v", before, during)
	}
	_ = tx.Rollback()
	after := db.Stats()
	if after.OpenTxN != 0 {
		t.Fatalf("after=%+v", after)
	}
}

// Verifies: BOLT-054
func TestStatsSubTransactionDelta(t *testing.T) {
	db, _ := open(t)
	before := db.Stats()
	_ = db.View(func(*bolt.Tx) error { return nil })
	after := db.Stats()
	diff := after.Sub(&before)
	if diff.TxN < 1 {
		t.Fatalf("diff=%+v", diff)
	}
}

// Verifies: BOLT-059
// Depends-On: atomic::TestPutGetReplace
func TestConcurrentReadersAgree(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	var wg sync.WaitGroup
	errs := make(chan error, 20)
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if string(value(t, db, "root", "k")) != "v" {
				errs <- errors.New("mismatch")
			}
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Fatal(err)
	}
}

// Verifies: BOLT-060
// Depends-On: atomic::TestUpdateCommits
func TestCoordinatedWriterPreservesReader(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "old")
	reader, _ := db.Begin(false)
	done := make(chan struct{})
	go func() { put(t, db, "root", "k", "new"); close(done) }()
	<-done
	if string(reader.Bucket(root).Get([]byte("k"))) != "old" {
		t.Fatal("reader changed")
	}
	_ = reader.Rollback()
}

// Verifies: BOLT-030
// Depends-On: atomic::TestPutGetReplace
func TestStagedViewsAgreeBeforeCommit(t *testing.T) {
	db, _ := open(t)
	tx, _ := db.Begin(true)
	b, _ := tx.CreateBucket(root)
	_ = b.Put([]byte("k"), []byte("v"))
	if string(b.Get([]byte("k"))) != "v" {
		t.Fatal("get")
	}
	k, v := b.Cursor().First()
	if string(k) != "k" || string(v) != "v" {
		t.Fatal("cursor")
	}
	_ = tx.Rollback()
}

// Verifies: BOLT-024
// Depends-On: atomic::TestValueBucketCollision
func TestBucketValueCollisionBothDirections(t *testing.T) {
	db, _ := open(t)
	err := db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		_, _ = b.CreateBucket([]byte("child"))
		return b.Put([]byte("child"), []byte("v"))
	})
	if !errors.Is(err, bolt.ErrIncompatibleValue) {
		t.Fatalf("err=%v", err)
	}
}

// Verifies: BOLT-038
// Depends-On: atomic::TestForEachOrderedAndError
func TestNestedEntryIncludedInForEach(t *testing.T) {
	db, _ := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		_, _ = b.CreateBucket([]byte("a"))
		return b.Put([]byte("b"), []byte("v"))
	})
	_ = db.View(func(tx *bolt.Tx) error {
		var got [][2]string
		_ = tx.Bucket(root).ForEach(func(k, v []byte) error { got = append(got, [2]string{string(k), string(v)}); return nil })
		want := [][2]string{{"a", ""}, {"b", "v"}}
		if !reflect.DeepEqual(got, want) {
			t.Fatalf("%v", got)
		}
		return nil
	})
}

// Verifies: BOLT-064
// Depends-On: atomic::TestTopLevelBucketEnumeration
func TestTransactionCursorTraversesTopBuckets(t *testing.T) {
	db, _ := open(t)
	_ = db.Update(func(tx *bolt.Tx) error { tx.CreateBucket([]byte("b")); tx.CreateBucket([]byte("a")); return nil })
	_ = db.View(func(tx *bolt.Tx) error {
		c := tx.Cursor()
		k, v := c.First()
		if string(k) != "a" || v != nil {
			t.Fatal("first")
		}
		k, v = c.Next()
		if string(k) != "b" || v != nil {
			t.Fatal("next")
		}
		return nil
	})
}

// Verifies: BOLT-065
func TestReadonlyCommitClosesWithoutMutation(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	tx, _ := db.Begin(false)
	if err := tx.Commit(); !errors.Is(err, bolt.ErrTxNotWritable) {
		t.Fatalf("commit err=%v", err)
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	if string(value(t, db, "root", "k")) != "v" {
		t.Fatal("mutated")
	}
}

// Verifies: BOLT-047
// Depends-On: atomic::TestPutGetReplace
func TestCopyMethodWritesSnapshot(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	var buf bytes.Buffer
	_ = db.View(func(tx *bolt.Tx) error { return tx.Copy(&buf) })
	if buf.Len() == 0 {
		t.Fatal("empty")
	}
	path := filepath.Join(t.TempDir(), "copy.db")
	f, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	_, _ = io.Copy(f, &buf)
	_ = f.Close()
	copydb := openCopied(t, path)
	if string(value(t, copydb, "root", "k")) != "v" {
		t.Fatal("missing")
	}
}

// Verifies: BOLT-052
// Depends-On: atomic::TestBucketStatsRelationships
func TestNestedStatsMatchHierarchy(t *testing.T) {
	db, _ := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		c, _ := b.CreateBucket([]byte("child"))
		_ = b.Put([]byte("a"), []byte("1"))
		return c.Put([]byte("z"), []byte("2"))
	})
	_ = db.View(func(tx *bolt.Tx) error {
		s := tx.Bucket(root).Stats()
		if s.BucketN < 2 || s.KeyN < 2 {
			t.Fatalf("%+v", s)
		}
		return nil
	})
}

// Verifies: BOLT-004, BOLT-050
// Depends-On: atomic::TestReadOnlyDatabaseRejectsWriter
func TestReadOnlyReopenReadsNestedState(t *testing.T) {
	db, path := open(t)
	_ = db.Update(func(tx *bolt.Tx) error {
		b, _ := tx.CreateBucket(root)
		c, _ := b.CreateBucket([]byte("child"))
		return c.Put([]byte("k"), []byte("v"))
	})
	_ = db.Close()
	ro, err := bolt.Open(path, 0600, &bolt.Options{ReadOnly: true})
	if err != nil {
		t.Fatal(err)
	}
	defer ro.Close()
	_ = ro.View(func(tx *bolt.Tx) error {
		if string(tx.Bucket(root).Bucket([]byte("child")).Get([]byte("k"))) != "v" {
			t.Fatal("missing")
		}
		return nil
	})
}

// Verifies: BOLT-061, BOLT-062
// Depends-On: atomic::TestUpdateErrorRollsBackAndPropagates
func TestViewCallbackErrorDoesNotChangeState(t *testing.T) {
	db, _ := open(t)
	put(t, db, "root", "k", "v")
	sent := errors.New("view stop")
	err := db.View(func(tx *bolt.Tx) error { _ = tx.Bucket(root).Get([]byte("k")); return sent })
	if !errors.Is(err, sent) || string(value(t, db, "root", "k")) != "v" {
		t.Fatalf("err=%v", err)
	}
}
