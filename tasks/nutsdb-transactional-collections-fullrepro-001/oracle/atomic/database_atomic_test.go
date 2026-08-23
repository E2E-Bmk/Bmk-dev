package atomic

import (
	"bytes"
	"errors"
	"reflect"
	"sort"
	"testing"
	"time"

	nutsdb "github.com/nutsdb/nutsdb"
	compat "nutsdb-oracle/compat"
)

func openDB(t *testing.T, options ...nutsdb.Option) *nutsdb.DB {
	t.Helper()
	base := nutsdb.DefaultOptions
	options = append([]nutsdb.Option{nutsdb.WithDir(t.TempDir()), nutsdb.WithRWMode(nutsdb.FileIO)}, options...)
	db, err := nutsdb.Open(base, options...)
	if err != nil {
		t.Fatalf("open: %v", err)
	}
	t.Cleanup(func() {
		if !db.IsClose() {
			_ = db.Close()
		}
	})
	return db
}

func newKV(t *testing.T, db *nutsdb.DB, bucket string) {
	t.Helper()
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.NewKVBucket(bucket) }); err != nil {
		t.Fatalf("new kv bucket: %v", err)
	}
}

// Verifies: NUTS-DB-001, NUTS-DB-002
func TestOpenCreatesUsableDatabase(t *testing.T) {
	db := openDB(t)
	if db.IsClose() {
		t.Fatal("new database reports closed")
	}
}

// Verifies: NUTS-DB-003
func TestOpenRejectsLockedDirectory(t *testing.T) {
	dir := t.TempDir()
	base := nutsdb.DefaultOptions
	first, err := nutsdb.Open(base, nutsdb.WithDir(dir), nutsdb.WithRWMode(nutsdb.FileIO))
	if err != nil {
		t.Fatal(err)
	}
	defer first.Close()
	_, err = nutsdb.Open(base, nutsdb.WithDir(dir), nutsdb.WithRWMode(nutsdb.FileIO))
	if !errors.Is(err, nutsdb.ErrDirLocked) {
		t.Fatalf("expected ErrDirLocked, got %v", err)
	}
}

// Verifies: NUTS-DB-004
func TestCloseChangesLifecycleState(t *testing.T) {
	db := openDB(t)
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	if !db.IsClose() {
		t.Fatal("closed database reports open")
	}
	if _, err := db.Begin(false); !errors.Is(err, nutsdb.ErrDBClosed) {
		t.Fatalf("begin after close: %v", err)
	}
}

// Verifies: NUTS-DB-005
func TestSecondCloseReturnsSentinel(t *testing.T) {
	db := openDB(t)
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); !errors.Is(err, nutsdb.ErrDBClosed) {
		t.Fatalf("second close: %v", err)
	}
}

// Verifies: NUTS-DB-008
func TestManagedTransactionsRejectNilCallback(t *testing.T) {
	db := openDB(t)
	if err := db.Update(nil); !errors.Is(err, nutsdb.ErrFn) {
		t.Fatalf("update nil: %v", err)
	}
	if err := db.View(nil); !errors.Is(err, nutsdb.ErrFn) {
		t.Fatalf("view nil: %v", err)
	}
}

// Verifies: NUTS-DB-009, NUTS-DB-010
func TestViewReadsAndRejectsWrites(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	err := db.View(func(tx *nutsdb.Tx) error {
		if err := tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent); !errors.Is(err, nutsdb.ErrTxNotWritable) {
			t.Fatalf("write error: %v", err)
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

// Verifies: NUTS-BKT-001, NUTS-BKT-002
func TestTypedBucketConvenienceConstructors(t *testing.T) {
	db := openDB(t)
	err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("kv"); err != nil {
			return err
		}
		if err := tx.NewListBucket("list"); err != nil {
			return err
		}
		if err := tx.NewSetBucket("set"); err != nil {
			return err
		}
		if err := tx.NewSortSetBucket("zset"); err != nil {
			return err
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	err = db.View(func(tx *nutsdb.Tx) error {
		if !tx.ExistBucket(nutsdb.DataStructureBTree, "kv") ||
			!tx.ExistBucket(nutsdb.DataStructureList, "list") ||
			!tx.ExistBucket(nutsdb.DataStructureSet, "set") ||
			!tx.ExistBucket(nutsdb.DataStructureSortedSet, "zset") {
			return errors.New("typed bucket projection mismatch")
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

// Verifies: NUTS-BKT-003
func TestDuplicateBucketReturnsSentinel(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	err := db.Update(func(tx *nutsdb.Tx) error { return tx.NewKVBucket("b") })
	if !errors.Is(err, nutsdb.ErrBucketAlreadyExist) {
		t.Fatalf("duplicate bucket: %v", err)
	}
}

// Verifies: NUTS-BKT-004
func TestDeleteBucketRemovesExistence(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.DeleteBucket(nutsdb.DataStructureBTree, "b") }); err != nil {
		t.Fatal(err)
	}
	if err := db.View(func(tx *nutsdb.Tx) error {
		if tx.ExistBucket(nutsdb.DataStructureBTree, "b") {
			t.Fatal("bucket still exists")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
}

// Verifies: NUTS-KV-001
func TestPutGetRoundTrip(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent) }); err != nil {
		t.Fatal(err)
	}
	if err := db.View(func(tx *nutsdb.Tx) error {
		got, err := compat.Get(tx, "b", []byte("k"))
		if err != nil {
			return err
		}
		if !bytes.Equal(got, []byte("v")) {
			t.Fatalf("value=%q", got)
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
}

// Verifies: NUTS-KV-002
func TestDeleteUpdatesHasAndGet(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent) })
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.Delete("b", []byte("k")) }); err != nil {
		t.Fatal(err)
	}
	_ = db.View(func(tx *nutsdb.Tx) error {
		has, err := tx.Has("b", []byte("k"))
		if err != nil || has {
			t.Fatalf("has=%v err=%v", has, err)
		}
		if _, err := tx.Get("b", []byte("k")); !errors.Is(err, nutsdb.ErrKeyNotFound) {
			t.Fatalf("get=%v", err)
		}
		return nil
	})
}

// Verifies: NUTS-KV-003
func TestEmptyKeyReturnsSentinel(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	err := db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", nil, []byte("v"), nutsdb.Persistent) })
	if !errors.Is(err, nutsdb.ErrKeyEmpty) {
		t.Fatalf("empty key: %v", err)
	}
}

// Verifies: NUTS-KV-004
func TestMissingBucketUsesDirectEntrySentinel(t *testing.T) {
	db := openDB(t)
	err := db.View(func(tx *nutsdb.Tx) error {
		_, err := tx.Get("missing", []byte("k"))
		return err
	})
	if !errors.Is(err, nutsdb.ErrNotFoundBucket) {
		t.Fatalf("missing bucket: %v", err)
	}
}

// Verifies: NUTS-KV-005
func TestPutIfNotExistsPreservesExistingValue(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.PutIfNotExists("b", []byte("k"), []byte("first"), nutsdb.Persistent); err != nil {
			return err
		}
		return tx.PutIfNotExists("b", []byte("k"), []byte("second"), nutsdb.Persistent)
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		v, _ := compat.Get(tx, "b", []byte("k"))
		if string(v) != "first" {
			t.Fatalf("value=%q", v)
		}
		return nil
	})
}

// Verifies: NUTS-KV-006
func TestPutIfExistsRejectsMissingKey(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	err := db.Update(func(tx *nutsdb.Tx) error {
		return tx.PutIfExists("b", []byte("missing"), []byte("v"), nutsdb.Persistent)
	})
	if !errors.Is(err, nutsdb.ErrKeyNotFound) {
		t.Fatalf("missing key: %v", err)
	}
}

// Verifies: NUTS-KV-007, NUTS-KV-009
func TestMSetMGetPreservesRequestOrder(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	if err := db.Update(func(tx *nutsdb.Tx) error {
		return compat.MSet(tx, "b", nutsdb.Persistent, []byte("b"), []byte("2"), []byte("a"), []byte("1"))
	}); err != nil {
		t.Fatal(err)
	}
	_ = db.View(func(tx *nutsdb.Tx) error {
		got, err := compat.MGet(tx, "b", []byte("a"), []byte("b"))
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, [][]byte{[]byte("1"), []byte("2")}) {
			t.Fatalf("values=%q", got)
		}
		return nil
	})
}

// Verifies: NUTS-KV-008
func TestMSetOddArgumentsIsAtomicFailure(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	err := db.Update(func(tx *nutsdb.Tx) error {
		return compat.MSet(tx, "b", nutsdb.Persistent, []byte("a"), []byte("1"), []byte("dangling"))
	})
	if !errors.Is(err, nutsdb.ErrKVArgsLenNotEven) {
		t.Fatalf("odd args: %v", err)
	}
}

// Verifies: NUTS-KV-010
func TestGetSetReturnsPreviousValue(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", []byte("k"), []byte("old"), nutsdb.Persistent) })
	err := db.Update(func(tx *nutsdb.Tx) error {
		old, err := compat.GetSet(tx, "b", []byte("k"), []byte("new"), nutsdb.Persistent)
		if err != nil {
			return err
		}
		if string(old) != "old" {
			t.Fatalf("old=%q", old)
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
}

// Verifies: NUTS-KV-011
func TestAppendAndValueLenAgree(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", []byte("k"), []byte("ab"), nutsdb.Persistent) })
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Append("b", []byte("k"), []byte("cd")) })
	_ = db.View(func(tx *nutsdb.Tx) error {
		v, _ := compat.Get(tx, "b", []byte("k"))
		n, _ := tx.ValueLen("b", []byte("k"))
		if string(v) != "abcd" || n != 4 {
			t.Fatalf("v=%q n=%d", v, n)
		}
		return nil
	})
}

// Verifies: NUTS-KV-012
func TestGetAllKeysValuesShareSortedProjection(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, pair := range [][2]string{{"c", "3"}, {"a", "1"}, {"b", "2"}} {
			if err := tx.Put("b", []byte(pair[0]), []byte(pair[1]), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		keys, values, err := compat.GetAll(tx, "b")
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(keys, [][]byte{[]byte("a"), []byte("b"), []byte("c")}) ||
			!reflect.DeepEqual(values, [][]byte{[]byte("1"), []byte("2"), []byte("3")}) {
			t.Fatalf("keys=%q values=%q", keys, values)
		}
		return nil
	})
}

// Verifies: NUTS-KV-013
func TestMinMaxKeysUseByteOrder(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, k := range []string{"m", "a", "z"} {
			if err := tx.Put("b", []byte(k), []byte(k), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		min, _ := tx.GetMinKey("b")
		max, _ := tx.GetMaxKey("b")
		if string(min) != "a" || string(max) != "z" {
			t.Fatalf("min=%q max=%q", min, max)
		}
		return nil
	})
}

// Verifies: NUTS-SCN-001
func TestPrefixScanAppliesOffsetAndLimit(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, k := range []string{"p1", "p2", "p3", "x"} {
			if err := tx.Put("b", []byte(k), []byte(k), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		got, err := tx.PrefixScan("b", []byte("p"), 1, 2)
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, [][]byte{[]byte("p2"), []byte("p3")}) {
			t.Fatalf("got=%q", got)
		}
		return nil
	})
}

// Verifies: NUTS-SCN-002
func TestPrefixSearchFiltersSuffix(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, k := range []string{"user:12", "user:ab", "user:34"} {
			if err := tx.Put("b", []byte(k), []byte(k), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		got, err := tx.PrefixSearchScan("b", []byte("user:"), "^[0-9]+$", 0, nutsdb.ScanNoLimit)
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, [][]byte{[]byte("user:12"), []byte("user:34")}) {
			t.Fatalf("got=%q", got)
		}
		return nil
	})
}

// Verifies: NUTS-SCN-003
func TestRangeScanUsesClosedInterval(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, k := range []string{"a", "b", "c", "d"} {
			if err := tx.Put("b", []byte(k), []byte(k), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		got, err := tx.RangeScan("b", []byte("b"), []byte("c"))
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, [][]byte{[]byte("b"), []byte("c")}) {
			t.Fatalf("got=%q", got)
		}
		return nil
	})
}

// Verifies: NUTS-SCN-004
func TestEmptyScansReturnSentinels(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.View(func(tx *nutsdb.Tx) error {
		if _, err := tx.PrefixScan("b", []byte("none"), 0, nutsdb.ScanNoLimit); !errors.Is(err, nutsdb.ErrPrefixScan) {
			t.Fatalf("prefix=%v", err)
		}
		if _, err := tx.RangeScan("b", []byte("a"), []byte("z")); !errors.Is(err, nutsdb.ErrRangeScan) {
			t.Fatalf("range=%v", err)
		}
		return nil
	})
}

// Verifies: NUTS-ITR-001, NUTS-ITR-002
func TestIteratorForwardAndReverseOrder(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, k := range []string{"a", "b", "c"} {
			if err := tx.Put("b", []byte(k), []byte(k), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		for _, tc := range []struct {
			rev  bool
			want []string
		}{{false, []string{"a", "b", "c"}}, {true, []string{"c", "b", "a"}}} {
			it := nutsdb.NewIterator(tx, "b", nutsdb.IteratorOptions{Reverse: tc.rev})
			if it == nil {
				t.Fatal("nil iterator")
			}
			var got []string
			for it.Valid() {
				got = append(got, string(it.Key()))
				if _, err := compat.IteratorValue(it); err != nil {
					return err
				}
				it.Next()
			}
			it.Release()
			if !reflect.DeepEqual(got, tc.want) {
				t.Fatalf("rev=%v got=%v", tc.rev, got)
			}
		}
		return nil
	})
}

// Verifies: NUTS-ITR-003, NUTS-ITR-004, NUTS-ITR-005
func TestIteratorSeekRewindAndRelease(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		for _, k := range []string{"a", "c", "e"} {
			if err := tx.Put("b", []byte(k), []byte(k), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		it := nutsdb.NewIterator(tx, "b", nutsdb.IteratorOptions{})
		positioned, err := compat.IteratorMove(it, "Seek", []byte("b"))
		if err != nil || !positioned || string(it.Key()) != "c" {
			t.Fatalf("seek=%q", it.Key())
		}
		positioned, err = compat.IteratorMove(it, "Rewind")
		if err != nil || !positioned || string(it.Key()) != "a" {
			t.Fatalf("rewind=%q", it.Key())
		}
		it.Release()
		if it.Valid() || it.Key() != nil {
			t.Fatal("released iterator valid")
		}
		return nil
	})
}

// Verifies: NUTS-TTL-001
func TestPersistentTTLIsMinusOne(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent) })
	_ = db.View(func(tx *nutsdb.Tx) error {
		ttl, err := tx.GetTTL("b", []byte("k"))
		if err != nil {
			return err
		}
		if ttl != -1 {
			t.Fatalf("ttl=%d", ttl)
		}
		return nil
	})
}

// Verifies: NUTS-TTL-002, NUTS-TTL-003
func TestPersistCancelsExpiration(t *testing.T) {
	db := openDB(t)
	newKV(t, db, "b")
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Put("b", []byte("k"), []byte("v"), 2) })
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Persist("b", []byte("k")) })
	time.Sleep(2200 * time.Millisecond)
	_ = db.View(func(tx *nutsdb.Tx) error {
		v, err := compat.Get(tx, "b", []byte("k"))
		if err != nil {
			return err
		}
		if string(v) != "v" {
			t.Fatal("value changed")
		}
		ttl, _ := tx.GetTTL("b", []byte("k"))
		if ttl != -1 {
			t.Fatalf("ttl=%d", ttl)
		}
		return nil
	})
}

// Verifies: NUTS-LST-001
func TestListPushAndRangeOrder(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewListBucket("l"); err != nil {
			return err
		}
		if err := tx.RPush("l", []byte("k"), []byte("b"), []byte("c")); err != nil {
			return err
		}
		return tx.LPush("l", []byte("k"), []byte("a"))
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		got, err := tx.LRange("l", []byte("k"), 0, -1)
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, [][]byte{[]byte("a"), []byte("b"), []byte("c")}) {
			t.Fatalf("got=%q", got)
		}
		return nil
	})
}

// Verifies: NUTS-SET-001, NUTS-SET-002
func TestSetUniquenessAndMembership(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSetBucket("s"); err != nil {
			return err
		}
		return tx.SAdd("s", []byte("k"), []byte("a"), []byte("a"), []byte("b"))
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		n, err := tx.SCard("s", []byte("k"))
		if err != nil {
			return err
		}
		ok, err := tx.SIsMember("s", []byte("k"), []byte("a"))
		if err != nil {
			return err
		}
		members, err := tx.SMembers("s", []byte("k"))
		if err != nil {
			return err
		}
		sort.Slice(members, func(i, j int) bool { return bytes.Compare(members[i], members[j]) < 0 })
		if n != 2 || !ok || !reflect.DeepEqual(members, [][]byte{[]byte("a"), []byte("b")}) {
			t.Fatalf("n=%d ok=%v members=%q", n, ok, members)
		}
		return nil
	})
}

// Verifies: NUTS-ZST-001, NUTS-ZST-002
func TestSortedSetScoreAndCardinality(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSortSetBucket("z"); err != nil {
			return err
		}
		if err := tx.ZAdd("z", []byte("k"), 1, []byte("a")); err != nil {
			return err
		}
		return tx.ZAdd("z", []byte("k"), 2, []byte("a"))
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		score, err := tx.ZScore("z", []byte("k"), []byte("a"))
		if err != nil {
			return err
		}
		n, err := tx.ZCard("z", []byte("k"))
		if err != nil {
			return err
		}
		if score != 2 || n != 1 {
			t.Fatalf("score=%v n=%d", score, n)
		}
		return nil
	})
}

// Verifies: NUTS-ZST-003
func TestSortedSetRanksAreOneBased(t *testing.T) {
	db := openDB(t)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSortSetBucket("z"); err != nil {
			return err
		}
		for i, v := range []string{"a", "b", "c"} {
			if err := tx.ZAdd("z", []byte("k"), float64(i+1), []byte(v)); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		rank, _ := tx.ZRank("z", []byte("k"), []byte("b"))
		rev, _ := tx.ZRevRank("z", []byte("k"), []byte("b"))
		if rank != 2 || rev != 2 {
			t.Fatalf("rank=%d rev=%d", rank, rev)
		}
		return nil
	})
}

// Verifies: NUTS-KV-004
func TestPublicErrorClassifiers(t *testing.T) {
	if !nutsdb.IsDBClosed(nutsdb.ErrDBClosed) || !nutsdb.IsBucketNotFound(nutsdb.ErrBucketNotFound) ||
		!nutsdb.IsKeyNotFound(nutsdb.ErrKeyNotFound) || !nutsdb.IsKeyEmpty(nutsdb.ErrKeyEmpty) ||
		!nutsdb.IsPrefixScan(nutsdb.ErrPrefixScan) {
		t.Fatal("error classifier mismatch")
	}
}
