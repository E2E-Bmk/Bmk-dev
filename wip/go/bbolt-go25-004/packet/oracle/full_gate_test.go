package savepointv4gate_test

import (
	"bytes"
	"errors"
	"fmt"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	bbolt "go.etcd.io/bbolt"
)

func openDB(t *testing.T, path string) *bbolt.DB {
	t.Helper()
	db, err := bbolt.Open(path, 0o600, &bbolt.Options{InitialMmapSize: 32 * 1024 * 1024})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func newDB(t *testing.T) (*bbolt.DB, string) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "case.db")
	return openDB(t, path), path
}

func mustUpdate(t *testing.T, db *bbolt.DB, fn func(*bbolt.Tx)) {
	t.Helper()
	if err := db.Update(func(tx *bbolt.Tx) error { fn(tx); return nil }); err != nil {
		t.Fatal(err)
	}
}

func mustBucket(t *testing.T, tx *bbolt.Tx, name string) *bbolt.Bucket {
	t.Helper()
	bucket := tx.Bucket([]byte(name))
	if bucket == nil {
		t.Fatalf("missing bucket %q", name)
	}
	return bucket
}

func put(t *testing.T, bucket *bbolt.Bucket, key, value string) {
	t.Helper()
	if err := bucket.Put([]byte(key), []byte(value)); err != nil {
		t.Fatal(err)
	}
}

func point(t *testing.T, tx *bbolt.Tx) *bbolt.Savepoint {
	t.Helper()
	sp, err := tx.Savepoint()
	if err != nil {
		t.Fatal(err)
	}
	return sp
}

func clean(t *testing.T, db *bbolt.DB) {
	t.Helper()
	if err := db.View(func(tx *bbolt.Tx) error {
		for err := range tx.Check() {
			if err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
}

func logical(t *testing.T, db *bbolt.DB) string {
	t.Helper()
	var out strings.Builder
	err := db.View(func(tx *bbolt.Tx) error {
		return tx.ForEach(func(name []byte, bucket *bbolt.Bucket) error {
			fmt.Fprintf(&out, "T:%x{", name)
			if err := logicalBucket(&out, bucket); err != nil {
				return err
			}
			out.WriteByte('}')
			return nil
		})
	})
	if err != nil {
		t.Fatal(err)
	}
	return out.String()
}

func logicalBucket(out *strings.Builder, bucket *bbolt.Bucket) error {
	fmt.Fprintf(out, "Q:%d;", bucket.Sequence())
	cursor := bucket.Cursor()
	for key, value := cursor.First(); key != nil; key, value = cursor.Next() {
		if value != nil {
			fmt.Fprintf(out, "V:%x=%x;", key, value)
			continue
		}
		fmt.Fprintf(out, "B:%x{", key)
		if err := logicalBucket(out, bucket.Bucket(key)); err != nil {
			return err
		}
		out.WriteString("};")
	}
	return nil
}

func beginWrite(t *testing.T, db *bbolt.DB) *bbolt.Tx {
	t.Helper()
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = tx.Rollback() })
	return tx
}

func seedBasic(t *testing.T, db *bbolt.DB) {
	t.Helper()
	mustUpdate(t, db, func(tx *bbolt.Tx) {
		root, err := tx.CreateBucket([]byte("root"))
		if err != nil {
			t.Fatal(err)
		}
		put(t, root, "a", "one")
		put(t, root, "c", "three")
	})
}

func TestA01CapturesScalarBytes(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	b := mustBucket(t, tx, "root")
	sp := point(t, tx)
	put(t, b, "a", "changed")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := string(mustBucket(t, tx, "root").Get([]byte("a"))); got != "one" { t.Fatalf("got %q", got) }
	if err := tx.Rollback(); err != nil { t.Fatal(err) }
}

func TestA02CapturesBucketSequence(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	b := mustBucket(t, tx, "root")
	if err := b.SetSequence(17); err != nil { t.Fatal(err) }
	sp := point(t, tx)
	if err := b.SetSequence(99); err != nil { t.Fatal(err) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := mustBucket(t, tx, "root").Sequence(); got != 17 { t.Fatalf("sequence %d", got) }
	_ = tx.Rollback()
}

func TestA03RollbackRemovesLaterWrites(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	put(t, mustBucket(t, tx, "root"), "later", "discard")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := mustBucket(t, tx, "root").Get([]byte("later")); got != nil { t.Fatalf("later=%q", got) }
	_ = tx.Rollback()
}

func TestA04RollbackRestoresDeletedState(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	if err := mustBucket(t, tx, "root").Delete([]byte("a")); err != nil { t.Fatal(err) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := string(mustBucket(t, tx, "root").Get([]byte("a"))); got != "one" { t.Fatalf("got %q", got) }
	_ = tx.Rollback()
}

func TestA05RollbackInvalidatesDescendants(t *testing.T) {
	db, _ := newDB(t)
	tx := beginWrite(t, db)
	if _, err := tx.CreateBucket([]byte("root")); err != nil { t.Fatal(err) }
	outer := point(t, tx)
	inner := point(t, tx)
	if err := tx.RollbackTo(outer); err != nil { t.Fatal(err) }
	if err := tx.RollbackTo(inner); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("got %v", err) }
	_ = tx.Rollback()
}

func TestA06RollbackTargetRemainsReusable(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	put(t, mustBucket(t, tx, "root"), "branch", "one")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	put(t, mustBucket(t, tx, "root"), "branch", "two")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := mustBucket(t, tx, "root").Get([]byte("branch")); got != nil { t.Fatalf("branch=%q", got) }
	_ = tx.Rollback()
}

func TestA07RestoresValueBucketKind(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); child, _ := b.CreateBucket([]byte("kind")); put(t, child, "k", "v") })
	tx := beginWrite(t, db)
	sp := point(t, tx)
	b := mustBucket(t, tx, "root")
	if err := b.DeleteBucket([]byte("kind")); err != nil { t.Fatal(err) }
	put(t, b, "kind", "scalar")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	b = mustBucket(t, tx, "root")
	if b.Get([]byte("kind")) != nil || b.Bucket([]byte("kind")) == nil { t.Fatal("entry kind not restored") }
	_ = tx.Rollback()
}

func TestA08RestoresOverflowValue(t *testing.T) {
	db, _ := newDB(t)
	large := bytes.Repeat([]byte("x"), 96*1024)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); if err := b.Put([]byte("large"), large); err != nil { t.Fatal(err) } })
	tx := beginWrite(t, db)
	sp := point(t, tx)
	if err := mustBucket(t, tx, "root").Put([]byte("large"), []byte("short")); err != nil { t.Fatal(err) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := mustBucket(t, tx, "root").Get([]byte("large")); !bytes.Equal(got, large) { t.Fatalf("length %d", len(got)) }
	_ = tx.Rollback()
}

func TestA09RollbackDiscardsLaterCommitHandler(t *testing.T) {
	db, _ := newDB(t)
	tx := beginWrite(t, db)
	if _, err := tx.CreateBucket([]byte("root")); err != nil { t.Fatal(err) }
	sp := point(t, tx)
	var called atomic.Int32
	tx.OnCommit(func() { called.Add(1) })
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	if called.Load() != 0 { t.Fatalf("handler called %d", called.Load()) }
}

func TestA10NativeBeginWritable(t *testing.T) {
	db, _ := newDB(t)
	tx := beginWrite(t, db)
	if !tx.Writable() { t.Fatal("not writable") }
	_ = tx.Rollback()
}

func TestA11NativePutCopiesBytes(t *testing.T) {
	db, _ := newDB(t)
	key, value := []byte("key"), []byte("value")
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); if err := b.Put(key, value); err != nil { t.Fatal(err) } })
	key[0], value[0] = 'X', 'X'
	if got := logical(t, db); !strings.Contains(got, "6b6579=76616c7565") { t.Fatalf("state %s", got) }
}

func TestA12NativeFullRollback(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	put(t, mustBucket(t, tx, "root"), "x", "y")
	if err := tx.Rollback(); err != nil { t.Fatal(err) }
	if strings.Contains(logical(t, db), "V:78=79") { t.Fatal("rollback published") }
}

func TestA13NativeCursorOrdering(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	if err := db.View(func(tx *bbolt.Tx) error { c := mustBucket(t, tx, "root").Cursor(); k, _ := c.First(); if string(k) != "a" { t.Fatalf("first %q", k) }; k, _ = c.Last(); if string(k) != "c" { t.Fatalf("last %q", k) }; return nil }); err != nil { t.Fatal(err) }
}

func TestA14NativeSequencePersistence(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); _ = b.SetSequence(41) })
	if err := db.View(func(tx *bbolt.Tx) error { if got := mustBucket(t, tx, "root").Sequence(); got != 41 { t.Fatalf("%d", got) }; return nil }); err != nil { t.Fatal(err) }
}

func TestA15NativeMoveBucket(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { a, _ := tx.CreateBucket([]byte("a")); b, _ := tx.CreateBucket([]byte("b")); child, _ := a.CreateBucket([]byte("child")); put(t, child, "k", "v"); if err := tx.MoveBucket([]byte("child"), a, b); err != nil { t.Fatal(err) } })
	if got := logical(t, db); !strings.Contains(got, "T:62") || !strings.Contains(got, "B:6368696c64") { t.Fatalf("%s", got) }
}

func TestA16NativeTxCheck(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	clean(t, db)
}

func TestI01NestedTopologySnapshot(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) {
		r, _ := tx.CreateBucket([]byte("root"))
		a, _ := r.CreateBucket([]byte("a"))
		b, _ := a.CreateBucket([]byte("b"))
		put(t, b, "leaf", "before")
	})
	tx := beginWrite(t, db)
	sp := point(t, tx)
	r := mustBucket(t, tx, "root")
	if err := r.DeleteBucket([]byte("a")); err != nil { t.Fatal(err) }
	x, _ := r.CreateBucket([]byte("x")); put(t, x, "leaf", "after")
	changes, err := tx.ChangesSince(sp); if err != nil { t.Fatal(err) }
	var deleted, created bool
	for _, change := range changes { deleted = deleted || change.Kind == bbolt.ChangeBucketDeleted; created = created || change.Kind == bbolt.ChangeBucketCreated }
	if !deleted || !created { t.Fatalf("changes=%+v", changes) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	r = mustBucket(t, tx, "root")
	if r.Bucket([]byte("x")) != nil || string(r.Bucket([]byte("a")).Bucket([]byte("b")).Get([]byte("leaf"))) != "before" { t.Fatal("topology mismatch") }
	_ = tx.Rollback()
}

func TestI02SnapshotOwnsCallerBytes(t *testing.T) {
	db, _ := newDB(t)
	tx := beginWrite(t, db)
	b, _ := tx.CreateBucket([]byte("root"))
	key, value := []byte("owned-key"), []byte("owned-value")
	if err := b.Put(key, value); err != nil { t.Fatal(err) }
	sp := point(t, tx)
	key[0], value[0] = 'X', 'X'
	put(t, b, "owned-key", "branch")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := string(mustBucket(t, tx, "root").Get([]byte("owned-key"))); got != "owned-value" { t.Fatalf("%q", got) }
	_ = tx.Rollback()
}

func TestI03MultipleTopLevelBucketsRestore(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { for _, name := range []string{"a", "m", "z"} { b, _ := tx.CreateBucket([]byte(name)); put(t, b, "k", name) } })
	want := logical(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	if err := tx.DeleteBucket([]byte("a")); err != nil { t.Fatal(err) }
	put(t, mustBucket(t, tx, "m"), "k", "changed")
	q, _ := tx.CreateBucket([]byte("q")); put(t, q, "k", "q")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	if got := logical(t, db); got != want { t.Fatalf("got %s want %s", got, want) }
}

func TestI04CreateDeleteCycleRestores(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	b := mustBucket(t, tx, "root")
	sp := point(t, tx)
	if err := b.Delete([]byte("a")); err != nil { t.Fatal(err) }
	put(t, b, "new", "one")
	if err := b.Delete([]byte("new")); err != nil { t.Fatal(err) }
	put(t, b, "a", "two")
	changes, err := tx.ChangesSince(sp)
	if err != nil || len(changes) != 1 || changes[0].Kind != bbolt.ChangeValuePut || string(changes[0].Key) != "a" || string(changes[0].Before) != "one" || string(changes[0].After) != "two" { t.Fatalf("%v changes=%+v", err, changes) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	b = mustBucket(t, tx, "root")
	if string(b.Get([]byte("a"))) != "one" || b.Get([]byte("new")) != nil { t.Fatal("cycle leaked") }
	_ = tx.Rollback()
}

func TestI05SequenceNextSequenceRestores(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); _ = b.SetSequence(8) })
	tx := beginWrite(t, db)
	b := mustBucket(t, tx, "root")
	sp := point(t, tx)
	if got, err := b.NextSequence(); err != nil || got != 9 { t.Fatalf("%d %v", got, err) }
	if got, err := b.NextSequence(); err != nil || got != 10 { t.Fatalf("%d %v", got, err) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	b = mustBucket(t, tx, "root")
	if got, err := b.NextSequence(); err != nil || got != 9 { t.Fatalf("%d %v", got, err) }
	_ = tx.Rollback()
}

func TestI06CursorViewsConvergeAfterRollback(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); for _, k := range []string{"aa", "cc", "ee"} { put(t, b, k, "v-"+k) } })
	tx := beginWrite(t, db)
	sp := point(t, tx)
	b := mustBucket(t, tx, "root")
	_ = b.Delete([]byte("cc")); put(t, b, "bb", "branch"); put(t, b, "zz", "branch")
	changes, err := tx.ChangesSince(sp)
	if err != nil || len(changes) != 3 || string(changes[0].Key) != "bb" || changes[1].Kind != bbolt.ChangeValueDeleted || string(changes[2].Key) != "zz" { t.Fatalf("%v changes=%+v", err, changes) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	c := mustBucket(t, tx, "root").Cursor()
	k, _ := c.First(); if string(k) != "aa" { t.Fatalf("first %q", k) }
	k, _ = c.Seek([]byte("bb")); if string(k) != "cc" { t.Fatalf("seek %q", k) }
	k, _ = c.Last(); if string(k) != "ee" { t.Fatalf("last %q", k) }
	k, _ = c.Prev(); if string(k) != "cc" { t.Fatalf("prev %q", k) }
	_ = tx.Rollback()
}

func TestI07ReleaseRetainsCurrentBranch(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	put(t, mustBucket(t, tx, "root"), "branch", "kept")
	changes, err := tx.ChangesSince(sp)
	if err != nil || len(changes) != 1 || changes[0].Kind != bbolt.ChangeValuePut || string(changes[0].Key) != "branch" { t.Fatalf("%v changes=%+v", err, changes) }
	if err := tx.Release(sp); err != nil { t.Fatal(err) }
	if err := tx.RollbackTo(sp); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	if !strings.Contains(logical(t, db), "V:6272616e6368=6b657074") { t.Fatal("released work missing") }
}

func TestI08ReleaseAncestorInvalidatesDescendants(t *testing.T) {
	db, _ := newDB(t)
	tx := beginWrite(t, db)
	b, _ := tx.CreateBucket([]byte("root"))
	outer := point(t, tx)
	put(t, b, "x", "1")
	inner := point(t, tx)
	put(t, b, "y", "2")
	if err := tx.Release(outer); err != nil { t.Fatal(err) }
	if err := tx.Release(inner); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if err := tx.RollbackTo(outer); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if string(b.Get([]byte("x"))) != "1" || string(b.Get([]byte("y"))) != "2" { t.Fatal("release changed data") }
	_ = tx.Rollback()
}

func TestI09ForeignAndInvalidTokensAreNonMutating(t *testing.T) {
	db1, _ := newDB(t)
	db2, _ := newDB(t)
	tx1 := beginWrite(t, db1); b1, _ := tx1.CreateBucket([]byte("root")); put(t, b1, "k", "one"); sp1 := point(t, tx1)
	tx2 := beginWrite(t, db2); b2, _ := tx2.CreateBucket([]byte("root")); put(t, b2, "k", "two"); before := string(b2.Get([]byte("k"))); sp2 := point(t, tx2)
	if err := tx2.RollbackTo(sp1); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if err := tx2.Release(nil); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if changes, err := tx2.ChangesSince(sp2); err != nil || len(changes) != 0 { t.Fatalf("%v changes=%+v", err, changes) }
	if got := string(b2.Get([]byte("k"))); got != before { t.Fatalf("changed to %q", got) }
	_ = tx2.Rollback(); _ = tx1.Rollback()
}

func TestI10MoveAcrossParentsRollsBack(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { a, _ := tx.CreateBucket([]byte("a")); _, _ = tx.CreateBucket([]byte("b")); child, _ := a.CreateBucket([]byte("child")); put(t, child, "k", "v") })
	tx := beginWrite(t, db)
	sp := point(t, tx)
	if err := tx.MoveBucket([]byte("child"), tx.Bucket([]byte("a")), tx.Bucket([]byte("b"))); err != nil { t.Fatal(err) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if tx.Bucket([]byte("a")).Bucket([]byte("child")) == nil || tx.Bucket([]byte("b")).Bucket([]byte("child")) != nil { t.Fatal("move not reversed") }
	_ = tx.Rollback()
}

func TestI11DeleteRecreateTopologyRollsBack(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); c, _ := b.CreateBucket([]byte("node")); put(t, c, "old", "v") })
	tx := beginWrite(t, db)
	sp := point(t, tx)
	b := mustBucket(t, tx, "root")
	_ = b.DeleteBucket([]byte("node")); c, _ := b.CreateBucket([]byte("node")); put(t, c, "new", "v")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	c = mustBucket(t, tx, "root").Bucket([]byte("node"))
	if string(c.Get([]byte("old"))) != "v" || c.Get([]byte("new")) != nil { t.Fatal("recreate leaked") }
	_ = tx.Rollback()
}

func TestI12NestedKindTransitionsRollBack(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); put(t, b, "scalar", "v"); c, _ := b.CreateBucket([]byte("nested")); put(t, c, "leaf", "v") })
	tx := beginWrite(t, db); sp := point(t, tx); b := mustBucket(t, tx, "root")
	_ = b.Delete([]byte("scalar")); s, _ := b.CreateBucket([]byte("scalar")); put(t, s, "inside", "x")
	_ = b.DeleteBucket([]byte("nested")); put(t, b, "nested", "flat")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	b = mustBucket(t, tx, "root")
	if string(b.Get([]byte("scalar"))) != "v" || b.Bucket([]byte("scalar")) != nil || b.Get([]byte("nested")) != nil || b.Bucket([]byte("nested")) == nil { t.Fatal("kind transition leaked") }
	_ = tx.Rollback()
}

func TestI13PageSplitBranchRollsBackCleanly(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db)
	tx := beginWrite(t, db); sp := point(t, tx); b := mustBucket(t, tx, "root")
	for i := 0; i < 1800; i++ { put(t, b, fmt.Sprintf("split-%04d", i), strings.Repeat("x", 120)) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	clean(t, db)
	if strings.Contains(logical(t, db), "split-") { t.Fatal("split branch leaked") }
}

func TestI14RebalanceBranchRollsBackCleanly(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); for i := 0; i < 1200; i++ { put(t, b, fmt.Sprintf("k%04d", i), strings.Repeat("v", 80)) } })
	tx := beginWrite(t, db); sp := point(t, tx); b := mustBucket(t, tx, "root")
	for i := 50; i < 1150; i++ { if err := b.Delete([]byte(fmt.Sprintf("k%04d", i))); err != nil { t.Fatal(err) } }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	clean(t, db)
	if !strings.Contains(logical(t, db), "6b30363030") { t.Fatal("deleted state not restored") }
}

func TestI15LargeNestedBranchCommitsAfterRollback(t *testing.T) {
	db, path := newDB(t)
	large := bytes.Repeat([]byte("a"), 128*1024)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); c, _ := b.CreateBucket([]byte("nested")); if err := c.Put([]byte("blob"), large); err != nil { t.Fatal(err) } })
	tx := beginWrite(t, db); sp := point(t, tx); c := mustBucket(t, tx, "root").Bucket([]byte("nested"))
	_ = c.Put([]byte("blob"), bytes.Repeat([]byte("b"), 160*1024)); put(t, c, "branch", "drop")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	c = mustBucket(t, tx, "root").Bucket([]byte("nested")); put(t, c, "final", "keep")
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	if err := db.Close(); err != nil { t.Fatal(err) }; db = openDB(t, path)
	if err := db.View(func(tx *bbolt.Tx) error { c := mustBucket(t, tx, "root").Bucket([]byte("nested")); if !bytes.Equal(c.Get([]byte("blob")), large) || c.Get([]byte("branch")) != nil || string(c.Get([]byte("final"))) != "keep" { t.Fatal("final branch wrong") }; return nil }); err != nil { t.Fatal(err) }
	clean(t, db)
}

func TestI16EarlierCommitHandlersSurvive(t *testing.T) {
	db, _ := newDB(t); tx := beginWrite(t, db); _, _ = tx.CreateBucket([]byte("root"))
	var before, after atomic.Int32
	tx.OnCommit(func() { before.Add(1) }); sp := point(t, tx); tx.OnCommit(func() { after.Add(1) })
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	if before.Load() != 1 || after.Load() != 0 { t.Fatalf("before=%d after=%d", before.Load(), after.Load()) }
	tx = beginWrite(t, db); before.Store(0); after.Store(0)
	tx.OnCommit(func() { before.Add(1) }); sp = point(t, tx); tx.OnCommit(func() { after.Add(1) })
	if err := tx.Release(sp); err != nil { t.Fatal(err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }
	if before.Load() != 1 || after.Load() != 1 { t.Fatalf("released before=%d after=%d", before.Load(), after.Load()) }
}

func TestI17ReadonlyAndClosedErrors(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db)
	if err := db.View(func(tx *bbolt.Tx) error { if _, err := tx.Savepoint(); !errors.Is(err, bbolt.ErrTxNotWritable) { t.Fatalf("%v", err) }; if err := tx.RollbackTo(nil); !errors.Is(err, bbolt.ErrTxNotWritable) { t.Fatalf("%v", err) }; return nil }); err != nil { t.Fatal(err) }
	tx := beginWrite(t, db); sp := point(t, tx); if err := tx.Rollback(); err != nil { t.Fatal(err) }
	if _, err := tx.Savepoint(); !errors.Is(err, bbolt.ErrTxClosed) { t.Fatalf("%v", err) }
	if err := tx.RollbackTo(sp); !errors.Is(err, bbolt.ErrTxClosed) { t.Fatalf("%v", err) }
}

func TestI18ManagedUpdateSupportsSavepoint(t *testing.T) {
	db, _ := newDB(t)
	if err := db.Update(func(tx *bbolt.Tx) error { b, _ := tx.CreateBucket([]byte("root")); put(t, b, "base", "v"); sp, err := tx.Savepoint(); if err != nil { return err }; put(t, b, "drop", "v"); changes, err := tx.ChangesSince(sp); if err != nil || len(changes) != 1 || string(changes[0].Key) != "drop" { return fmt.Errorf("changes: %v %+v", err, changes) }; if err := tx.RollbackTo(sp); err != nil { return err }; b = tx.Bucket([]byte("root")); put(t, b, "final", "v"); return nil }); err != nil { t.Fatal(err) }
	state := logical(t, db); if strings.Contains(state, "64726f70") || !strings.Contains(state, "66696e616c") { t.Fatalf("%s", state) }
}

func TestI19FullRollbackDominatesSavepoints(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); before := logical(t, db)
	tx := beginWrite(t, db); sp := point(t, tx); var called atomic.Int32; tx.OnCommit(func() { called.Add(1) }); put(t, mustBucket(t, tx, "root"), "drop", "v")
	if err := tx.Rollback(); err != nil { t.Fatal(err) }
	if called.Load() != 0 || logical(t, db) != before { t.Fatal("full rollback failed") }
	if err := tx.Release(sp); !errors.Is(err, bbolt.ErrTxClosed) { t.Fatalf("%v", err) }
}

func TestI20NativeUpdateViewReopen(t *testing.T) {
	db, path := newDB(t); seedBasic(t, db); want := logical(t, db)
	if err := db.Close(); err != nil { t.Fatal(err) }; db = openDB(t, path)
	if got := logical(t, db); got != want { t.Fatalf("%s != %s", got, want) }
}

func TestI21NativeRetainedReaderSnapshot(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db)
	reader, err := db.Begin(false); if err != nil { t.Fatal(err) }
	mustUpdate(t, db, func(tx *bbolt.Tx) { put(t, mustBucket(t, tx, "root"), "a", "new") })
	if got := string(reader.Bucket([]byte("root")).Get([]byte("a"))); got != "one" { t.Fatalf("retained %q", got) }
	if err := reader.Rollback(); err != nil { t.Fatal(err) }
	if got := logical(t, db); !strings.Contains(got, "6e6577") { t.Fatalf("fresh %s", got) }
}

func TestI22NativeHotBackupReopens(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); backup := filepath.Join(t.TempDir(), "backup.db")
	if err := db.View(func(tx *bbolt.Tx) error { return tx.CopyFile(backup, 0o600) }); err != nil { t.Fatal(err) }
	copyDB := openDB(t, backup); if logical(t, copyDB) != logical(t, db) { t.Fatal("backup mismatch") }; clean(t, copyDB)
}

func TestI23NativeMoveBucketCommitReopen(t *testing.T) {
	db, path := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { a, _ := tx.CreateBucket([]byte("a")); b, _ := tx.CreateBucket([]byte("b")); c, _ := a.CreateBucket([]byte("child")); put(t, c, "k", "v"); if err := tx.MoveBucket([]byte("child"), a, b); err != nil { t.Fatal(err) } })
	if err := db.Close(); err != nil { t.Fatal(err) }; db = openDB(t, path)
	if err := db.View(func(tx *bbolt.Tx) error { if tx.Bucket([]byte("a")).Bucket([]byte("child")) != nil || tx.Bucket([]byte("b")).Bucket([]byte("child")) == nil { t.Fatal("move missing") }; return nil }); err != nil { t.Fatal(err) }
}

func TestI24NativeStatsAndConsistency(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); _ = db.Stats(); clean(t, db)
	if err := db.View(func(tx *bbolt.Tx) error { if mustBucket(t, tx, "root").Stats().KeyN != 2 { t.Fatalf("keys %d", mustBucket(t, tx, "root").Stats().KeyN) }; return nil }); err != nil { t.Fatal(err) }
}

func TestS01NestedSavepointBranchCommitReopen(t *testing.T) {
	db, path := newDB(t); seedBasic(t, db); tx := beginWrite(t, db); b := mustBucket(t, tx, "root")
	put(t, b, "pre", "keep"); outer := point(t, tx); put(t, b, "outer", "drop"); middle := point(t, tx); put(t, b, "middle", "drop"); inner := point(t, tx); put(t, b, "inner", "drop")
	changes, err := tx.ChangesSince(outer); if err != nil || len(changes) != 3 { t.Fatalf("%v changes=%+v", err, changes) }
	if err := tx.RollbackTo(middle); err != nil { t.Fatal(err) }; if err := tx.RollbackTo(inner); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	b = mustBucket(t, tx, "root"); put(t, b, "middle-final", "drop-with-outer"); if err := tx.RollbackTo(outer); err != nil { t.Fatal(err) }; if err := tx.RollbackTo(middle); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	b = mustBucket(t, tx, "root"); put(t, b, "final", "keep"); if err := tx.Commit(); err != nil { t.Fatal(err) }
	_ = db.Close(); db = openDB(t, path); state := logical(t, db)
	if !strings.Contains(state, "707265") || !strings.Contains(state, "66696e616c") || strings.Contains(state, "6f75746572") || strings.Contains(state, "6d6964646c65") || strings.Contains(state, "696e6e6572") { t.Fatalf("%s", state) }
	clean(t, db)
}

func TestS02TopologySequenceOverflowBranch(t *testing.T) {
	db, _ := newDB(t); large := bytes.Repeat([]byte("p"), 100*1024)
	mustUpdate(t, db, func(tx *bbolt.Tx) { a, _ := tx.CreateBucket([]byte("a")); b, _ := tx.CreateBucket([]byte("b")); c, _ := a.CreateBucket([]byte("child")); _ = c.SetSequence(77); _ = c.Put([]byte("blob"), large); put(t, b, "stable", "yes") })
	want := logical(t, db); tx := beginWrite(t, db); sp := point(t, tx)
	if err := tx.MoveBucket([]byte("child"), tx.Bucket([]byte("a")), tx.Bucket([]byte("b"))); err != nil { t.Fatal(err) }; c := tx.Bucket([]byte("b")).Bucket([]byte("child")); _ = c.SetSequence(900); _ = c.Put([]byte("blob"), bytes.Repeat([]byte("q"), 130*1024)); put(t, c, "branch", "drop")
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }; if err := tx.Commit(); err != nil { t.Fatal(err) }
	if got := logical(t, db); got != want { t.Fatalf("got %s want %s", got, want) }; clean(t, db)
}

func TestS03RollbackRebranchReleaseLineage(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); tx := beginWrite(t, db); outer := point(t, tx); put(t, mustBucket(t, tx, "root"), "first", "drop"); dead := point(t, tx); put(t, mustBucket(t, tx, "root"), "dead", "drop")
	if err := tx.RollbackTo(outer); err != nil { t.Fatal(err) }; if err := tx.Release(dead); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	put(t, mustBucket(t, tx, "root"), "second", "keep"); branch := point(t, tx); put(t, mustBucket(t, tx, "root"), "third", "keep"); if err := tx.Release(branch); err != nil { t.Fatal(err) }; if err := tx.RollbackTo(branch); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }; state := logical(t, db)
	if strings.Contains(state, "6669727374") || strings.Contains(state, "64656164") || !strings.Contains(state, "7365636f6e64") || !strings.Contains(state, "7468697264") { t.Fatalf("%s", state) }
}

func TestS04PageChurnMoveRollbackCheck(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { a, _ := tx.CreateBucket([]byte("a")); _, _ = tx.CreateBucket([]byte("b")); c, _ := a.CreateBucket([]byte("child")); for i := 0; i < 900; i++ { put(t, c, fmt.Sprintf("k%04d", i), strings.Repeat("v", 100)) } })
	tx := beginWrite(t, db); sp := point(t, tx); a, b := tx.Bucket([]byte("a")), tx.Bucket([]byte("b")); c := a.Bucket([]byte("child")); for i := 100; i < 800; i++ { _ = c.Delete([]byte(fmt.Sprintf("k%04d", i))) }; if err := tx.MoveBucket([]byte("child"), a, b); err != nil { t.Fatal(err) }; for i := 0; i < 500; i++ { put(t, b.Bucket([]byte("child")), fmt.Sprintf("z%04d", i), "branch") }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }; if err := tx.Commit(); err != nil { t.Fatal(err) }; clean(t, db)
	if err := db.View(func(tx *bbolt.Tx) error { c := tx.Bucket([]byte("a")).Bucket([]byte("child")); if c == nil || tx.Bucket([]byte("b")).Bucket([]byte("child")) != nil || c.Get([]byte("k0450")) == nil || c.Get([]byte("z0001")) != nil { t.Fatal("churn branch mismatch") }; return nil }); err != nil { t.Fatal(err) }
}

func TestS05ReaderCommitBackupCompactAgreement(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); old, err := db.Begin(false); if err != nil { t.Fatal(err) }
	tx := beginWrite(t, db); sp := point(t, tx); put(t, mustBucket(t, tx, "root"), "a", "discarded"); put(t, mustBucket(t, tx, "root"), "drop", "branch"); if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }; put(t, mustBucket(t, tx, "root"), "a", "final"); put(t, mustBucket(t, tx, "root"), "keep", "yes"); if err := tx.Commit(); err != nil { t.Fatal(err) }
	if got := string(old.Bucket([]byte("root")).Get([]byte("a"))); got != "one" { t.Fatalf("old %q", got) }; _ = old.Rollback(); want := logical(t, db)
	backupPath := filepath.Join(t.TempDir(), "backup.db"); if err := db.View(func(tx *bbolt.Tx) error { return tx.CopyFile(backupPath, 0o600) }); err != nil { t.Fatal(err) }; backup := openDB(t, backupPath)
	compactPath := filepath.Join(t.TempDir(), "compact.db"); compact := openDB(t, compactPath); if err := bbolt.Compact(compact, db, 64*1024); err != nil { t.Fatal(err) }
	if logical(t, backup) != want || logical(t, compact) != want { t.Fatal("derived views diverged") }; clean(t, db); clean(t, backup); clean(t, compact)
}

func TestS06ManagedFailureHandlerLifecycle(t *testing.T) {
	db, _ := newDB(t); sentinel := errors.New("stop"); var early, late atomic.Int32
	err := db.Update(func(tx *bbolt.Tx) error { b, _ := tx.CreateBucket([]byte("root")); tx.OnCommit(func() { early.Add(1) }); sp, e := tx.Savepoint(); if e != nil { return e }; tx.OnCommit(func() { late.Add(1) }); put(t, b, "branch", "discard"); if e := tx.RollbackTo(sp); e != nil { return e }; b = tx.Bucket([]byte("root")); put(t, b, "after", "also-discard"); return sentinel })
	if !errors.Is(err, sentinel) || early.Load() != 0 || late.Load() != 0 || logical(t, db) != "" { t.Fatalf("err=%v early=%d late=%d state=%s", err, early.Load(), late.Load(), logical(t, db)) }
	if err := db.Update(func(tx *bbolt.Tx) error { b, _ := tx.CreateBucket([]byte("root")); sp, e := tx.Savepoint(); if e != nil { return e }; put(t, b, "drop", "x"); if e := tx.RollbackTo(sp); e != nil { return e }; b = tx.Bucket([]byte("root")); put(t, b, "keep", "y"); return nil }); err != nil { t.Fatal(err) }
	if state := logical(t, db); strings.Contains(state, "64726f70") || !strings.Contains(state, "6b656570") { t.Fatalf("%s", state) }
}

func TestS07NativeCompactPreservesLogicalState(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); mustUpdate(t, db, func(tx *bbolt.Tx) { b := mustBucket(t, tx, "root"); _ = b.SetSequence(88); for i := 0; i < 500; i++ { put(t, b, fmt.Sprintf("k%04d", i), "v") } }); want := logical(t, db)
	compact := openDB(t, filepath.Join(t.TempDir(), "compact.db")); if err := bbolt.Compact(compact, db, 64*1024); err != nil { t.Fatal(err) }; if got := logical(t, compact); got != want { t.Fatalf("%s != %s", got, want) }; clean(t, compact)
}

func TestS08NativeWriterLockAndRecovery(t *testing.T) {
	db, path := newDB(t); seedBasic(t, db)
	second, err := bbolt.Open(path, 0o600, &bbolt.Options{Timeout: 20 * time.Millisecond}); if second != nil { _ = second.Close() }; if !errors.Is(err, bbolt.ErrTimeout) { t.Fatalf("%v", err) }
	if got := logical(t, db); got == "" { t.Fatal("owner unusable") }; if err := db.Close(); err != nil { t.Fatal(err) }
	reopened := openDB(t, path); if logical(t, reopened) == "" { t.Fatal("reopen empty") }
}

func TestA07ChangesSinceScalar(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	put(t, mustBucket(t, tx, "root"), "a", "two")
	changes, err := tx.ChangesSince(sp)
	if err != nil { t.Fatal(err) }
	if len(changes) != 1 { t.Fatalf("changes=%+v", changes) }
	change := changes[0]
	if change.Kind != bbolt.ChangeValuePut || len(change.Path) != 1 || string(change.Path[0]) != "root" || string(change.Key) != "a" || string(change.Before) != "one" || string(change.After) != "two" { t.Fatalf("change=%+v", change) }
	_ = tx.Rollback()
}

func TestA08ChangesSinceSequence(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	b := mustBucket(t, tx, "root")
	if err := b.SetSequence(4); err != nil { t.Fatal(err) }
	sp := point(t, tx)
	if err := b.SetSequence(19); err != nil { t.Fatal(err) }
	changes, err := tx.ChangesSince(sp)
	if err != nil { t.Fatal(err) }
	if len(changes) != 1 || changes[0].Kind != bbolt.ChangeSequenceSet || len(changes[0].Path) != 1 || string(changes[0].Path[0]) != "root" || changes[0].BeforeSequence != 4 || changes[0].AfterSequence != 19 { t.Fatalf("changes=%+v", changes) }
	_ = tx.Rollback()
}

func TestI10ChangesOwnReportedBytes(t *testing.T) {
	db, _ := newDB(t)
	seedBasic(t, db)
	tx := beginWrite(t, db)
	sp := point(t, tx)
	put(t, mustBucket(t, tx, "root"), "a", "branch")
	changes, err := tx.ChangesSince(sp)
	if err != nil || len(changes) != 1 { t.Fatalf("%v %+v", err, changes) }
	changes[0].Path[0][0] = 'X'; changes[0].Key[0] = 'X'; changes[0].Before[0] = 'X'; changes[0].After[0] = 'X'
	put(t, mustBucket(t, tx, "root"), "a", "second")
	again, err := tx.ChangesSince(sp)
	if err != nil || len(again) != 1 { t.Fatalf("%v %+v", err, again) }
	if string(again[0].Path[0]) != "root" || string(again[0].Key) != "a" || string(again[0].Before) != "one" || string(again[0].After) != "second" { t.Fatalf("again=%+v", again[0]) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	if got := string(mustBucket(t, tx, "root").Get([]byte("a"))); got != "one" { t.Fatalf("%q", got) }
	_ = tx.Rollback()
}

func TestI11ChangesDescribeNestedTopology(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { _, _ = tx.CreateBucket([]byte("root")) })
	tx := beginWrite(t, db); sp := point(t, tx); root := mustBucket(t, tx, "root"); child, _ := root.CreateBucket([]byte("child")); _ = child.SetSequence(7); put(t, child, "leaf", "value")
	changes, err := tx.ChangesSince(sp); if err != nil { t.Fatal(err) }
	if len(changes) != 3 { t.Fatalf("changes=%+v", changes) }
	if changes[0].Kind != bbolt.ChangeBucketCreated || string(changes[0].Path[0]) != "root" || string(changes[0].Key) != "child" { t.Fatalf("create=%+v", changes[0]) }
	if changes[1].Kind != bbolt.ChangeSequenceSet || len(changes[1].Path) != 2 || string(changes[1].Path[1]) != "child" || changes[1].AfterSequence != 7 { t.Fatalf("sequence=%+v", changes[1]) }
	if changes[2].Kind != bbolt.ChangeValuePut || string(changes[2].Path[1]) != "child" || string(changes[2].Key) != "leaf" || string(changes[2].After) != "value" { t.Fatalf("value=%+v", changes[2]) }
	_ = tx.Rollback()
}

func TestI12ChangesDescribeKindTransition(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { b, _ := tx.CreateBucket([]byte("root")); put(t, b, "node", "scalar") })
	tx := beginWrite(t, db); sp := point(t, tx); root := mustBucket(t, tx, "root"); _ = root.Delete([]byte("node")); child, _ := root.CreateBucket([]byte("node")); put(t, child, "inside", "nested")
	changes, err := tx.ChangesSince(sp); if err != nil { t.Fatal(err) }
	if len(changes) != 3 || changes[0].Kind != bbolt.ChangeValueDeleted || changes[1].Kind != bbolt.ChangeBucketCreated || changes[2].Kind != bbolt.ChangeValuePut { t.Fatalf("changes=%+v", changes) }
	if string(changes[0].Before) != "scalar" || string(changes[1].Key) != "node" || len(changes[2].Path) != 2 || string(changes[2].Path[1]) != "node" { t.Fatalf("changes=%+v", changes) }
	_ = tx.Rollback()
}

func TestI13ChangesDescribeBucketMove(t *testing.T) {
	db, _ := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { a, _ := tx.CreateBucket([]byte("a")); _, _ = tx.CreateBucket([]byte("b")); child, _ := a.CreateBucket([]byte("child")); _ = child.SetSequence(5); put(t, child, "k", "v") })
	tx := beginWrite(t, db); sp := point(t, tx); if err := tx.MoveBucket([]byte("child"), tx.Bucket([]byte("a")), tx.Bucket([]byte("b"))); err != nil { t.Fatal(err) }
	changes, err := tx.ChangesSince(sp); if err != nil { t.Fatal(err) }
	var deleted, created bool
	for _, change := range changes { if change.Kind == bbolt.ChangeBucketDeleted && len(change.Path) == 1 && string(change.Path[0]) == "a" { deleted = true }; if change.Kind == bbolt.ChangeBucketCreated && len(change.Path) == 1 && string(change.Path[0]) == "b" { created = true } }
	if !deleted || !created || len(changes) != 6 { t.Fatalf("changes=%+v", changes) }
	_ = tx.Rollback()
}

func TestI14ChangesFollowRebranch(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); tx := beginWrite(t, db); sp := point(t, tx)
	put(t, mustBucket(t, tx, "root"), "old-branch", "discard")
	changes, err := tx.ChangesSince(sp); if err != nil || len(changes) != 1 { t.Fatalf("%v %+v", err, changes) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }
	changes, err = tx.ChangesSince(sp); if err != nil || len(changes) != 0 { t.Fatalf("%v %+v", err, changes) }
	put(t, mustBucket(t, tx, "root"), "new-branch", "keep")
	changes, err = tx.ChangesSince(sp); if err != nil || len(changes) != 1 || string(changes[0].Key) != "new-branch" { t.Fatalf("%v %+v", err, changes) }
	_ = tx.Rollback()
}

func TestI15ChangesInvalidPointIsNonMutating(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); tx := beginWrite(t, db); sp := point(t, tx); put(t, mustBucket(t, tx, "root"), "keep", "branch"); if err := tx.Release(sp); err != nil { t.Fatal(err) }
	before := string(mustBucket(t, tx, "root").Get([]byte("keep")))
	if _, err := tx.ChangesSince(sp); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if _, err := tx.ChangesSince(nil); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	if got := string(mustBucket(t, tx, "root").Get([]byte("keep"))); got != before { t.Fatalf("%q", got) }
	_ = tx.Rollback()
}

func TestS04ChangeProjectionAcrossLineage(t *testing.T) {
	db, _ := newDB(t); seedBasic(t, db); tx := beginWrite(t, db); outer := point(t, tx); put(t, mustBucket(t, tx, "root"), "first", "discard"); inner := point(t, tx); put(t, mustBucket(t, tx, "root"), "second", "discard")
	outerChanges, err := tx.ChangesSince(outer); if err != nil || len(outerChanges) != 2 { t.Fatalf("%v %+v", err, outerChanges) }
	innerChanges, err := tx.ChangesSince(inner); if err != nil || len(innerChanges) != 1 || string(innerChanges[0].Key) != "second" { t.Fatalf("%v %+v", err, innerChanges) }
	if err := tx.RollbackTo(outer); err != nil { t.Fatal(err) }; if _, err := tx.ChangesSince(inner); !errors.Is(err, bbolt.ErrInvalidSavepoint) { t.Fatalf("%v", err) }
	put(t, mustBucket(t, tx, "root"), "third", "keep"); branch := point(t, tx); put(t, mustBucket(t, tx, "root"), "fourth", "keep"); if err := tx.Release(branch); err != nil { t.Fatal(err) }
	changes, err := tx.ChangesSince(outer); if err != nil || len(changes) != 2 || string(changes[0].Key) != "fourth" && string(changes[1].Key) != "fourth" { t.Fatalf("%v %+v", err, changes) }
	_ = tx.Rollback()
}

func TestS05ChangeProjectionCommitAgreement(t *testing.T) {
	db, path := newDB(t)
	mustUpdate(t, db, func(tx *bbolt.Tx) { root, _ := tx.CreateBucket([]byte("root")); old, _ := root.CreateBucket([]byte("old")); put(t, old, "k", "v"); _ = root.SetSequence(2) })
	tx := beginWrite(t, db); sp := point(t, tx); root := mustBucket(t, tx, "root"); _ = root.SetSequence(99); _ = root.DeleteBucket([]byte("old")); transient, _ := root.CreateBucket([]byte("transient")); put(t, transient, "drop", "x")
	if changes, err := tx.ChangesSince(sp); err != nil || len(changes) < 5 { t.Fatalf("%v %+v", err, changes) }
	if err := tx.RollbackTo(sp); err != nil { t.Fatal(err) }; root = mustBucket(t, tx, "root"); _ = root.SetSequence(7); final, _ := root.CreateBucket([]byte("final")); put(t, final, "k", "done")
	changes, err := tx.ChangesSince(sp); if err != nil || len(changes) != 3 { t.Fatalf("%v %+v", err, changes) }
	if changes[0].Kind != bbolt.ChangeSequenceSet || changes[1].Kind != bbolt.ChangeBucketCreated || changes[2].Kind != bbolt.ChangeValuePut { t.Fatalf("changes=%+v", changes) }
	if err := tx.Commit(); err != nil { t.Fatal(err) }; _ = db.Close(); db = openDB(t, path); state := logical(t, db)
	if !strings.Contains(state, "Q:7") || !strings.Contains(state, "66696e616c") || !strings.Contains(state, "646f6e65") || strings.Contains(state, "7472616e7369656e74") { t.Fatalf("%s", state) }; clean(t, db)
}
