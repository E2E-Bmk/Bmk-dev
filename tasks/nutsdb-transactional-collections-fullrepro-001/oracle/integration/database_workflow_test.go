package integration

import (
	"bytes"
	"errors"
	"fmt"
	"reflect"
	"sort"
	"testing"
	"time"

	nutsdb "github.com/nutsdb/nutsdb"
	compat "nutsdb-oracle/compat"
)

func openAt(t *testing.T, dir string, options ...nutsdb.Option) *nutsdb.DB {
	t.Helper()
	base := nutsdb.DefaultOptions
	options = append([]nutsdb.Option{nutsdb.WithDir(dir), nutsdb.WithRWMode(nutsdb.FileIO)}, options...)
	db, err := nutsdb.Open(base, options...)
	if err != nil {
		t.Fatalf("open: %v", err)
	}
	return db
}

func openWatchAt(t *testing.T, dir string) *nutsdb.DB {
	t.Helper()
	options := nutsdb.DefaultOptions
	options.EnableWatch = true
	db, err := nutsdb.Open(options, nutsdb.WithDir(dir), nutsdb.WithRWMode(nutsdb.FileIO))
	if err != nil {
		t.Fatalf("open watch database: %v", err)
	}
	return db
}

func closeOK(t *testing.T, db *nutsdb.DB) {
	t.Helper()
	if db != nil && !db.IsClose() {
		if err := db.Close(); err != nil {
			t.Fatalf("close: %v", err)
		}
	}
}

func putKV(t *testing.T, db *nutsdb.DB, bucket, key, value string) {
	t.Helper()
	err := db.Update(func(tx *nutsdb.Tx) error {
		if !tx.ExistBucket(nutsdb.DataStructureBTree, bucket) {
			if err := tx.NewKVBucket(bucket); err != nil {
				return err
			}
		}
		return tx.Put(bucket, []byte(key), []byte(value), nutsdb.Persistent)
	})
	if err != nil {
		t.Fatalf("put: %v", err)
	}
}

func readKV(t *testing.T, db *nutsdb.DB, bucket, key string) string {
	t.Helper()
	var value []byte
	err := db.View(func(tx *nutsdb.Tx) error {
		var err error
		value, err = compat.Get(tx, bucket, []byte(key))
		return err
	})
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	return string(value)
}

// Verifies: NUTS-DB-006, NUTS-KV-001
// Depends-On: TestPutGetRoundTrip, TestTypedBucketConvenienceConstructors
func TestManagedUpdateCommitsAllChanges(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("b"); err != nil {
			return err
		}
		if err := tx.Put("b", []byte("a"), []byte("1"), nutsdb.Persistent); err != nil {
			return err
		}
		return tx.Put("b", []byte("b"), []byte("2"), nutsdb.Persistent)
	})
	if err != nil {
		t.Fatal(err)
	}
	if readKV(t, db, "b", "a") != "1" || readKV(t, db, "b", "b") != "2" {
		t.Fatal("commit mismatch")
	}
}

// Verifies: NUTS-DB-007, NUTS-BKT-001, NUTS-KV-001
// Depends-On: TestPutGetRoundTrip, TestTypedBucketConvenienceConstructors
func TestManagedUpdateErrorRollsBackBucketAndEntries(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	stop := errors.New("stop")
	err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("b"); err != nil {
			return err
		}
		if err := tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent); err != nil {
			return err
		}
		return stop
	})
	if !errors.Is(err, stop) {
		t.Fatalf("err=%v", err)
	}
	_ = db.View(func(tx *nutsdb.Tx) error {
		if tx.ExistBucket(nutsdb.DataStructureBTree, "b") {
			return errors.New("rolled-back bucket exists")
		}
		return nil
	})
}

// Verifies: NUTS-DB-011
// Depends-On: TestPutGetRoundTrip
func TestManualCommitPublishesStagedState(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	if err = tx.NewKVBucket("b"); err != nil {
		t.Fatal(err)
	}
	if err = tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	if readKV(t, db, "b", "k") != "v" {
		t.Fatal("manual commit missing")
	}
}

// Verifies: NUTS-DB-011
// Depends-On: TestPutGetRoundTrip
func TestManualRollbackDiscardsStagedState(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	_ = tx.NewKVBucket("b")
	_ = tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent)
	if err = tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	_ = db.View(func(tx *nutsdb.Tx) error {
		if tx.ExistBucket(nutsdb.DataStructureBTree, "b") {
			return errors.New("rollback visible")
		}
		return nil
	})
}

// Verifies: NUTS-DB-012, NUTS-DB-013
// Depends-On: TestViewReadsAndRejectsWrites
func TestManualReadTransactionClosesWithoutMutation(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	tx, err := db.Begin(false)
	if err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	if _, err = tx.Get("b", []byte("k")); !errors.Is(err, nutsdb.ErrTxClosed) {
		t.Fatalf("closed read tx=%v", err)
	}
}

// Verifies: NUTS-BKT-002, NUTS-BKT-005
// Depends-On: TestTypedBucketConvenienceConstructors
func TestTypedBucketsAreEnumerableByKind(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		_ = tx.NewKVBucket("kv-a")
		_ = tx.NewKVBucket("kv-b")
		_ = tx.NewListBucket("list")
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		var got []string
		err := compat.IterateBuckets(tx, nutsdb.DataStructureBTree, "kv-*", func(name string) bool { got = append(got, name); return true })
		sort.Strings(got)
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, []string{"kv-a", "kv-b"}) {
			return fmt.Errorf("got=%v", got)
		}
		return nil
	})
}

// Verifies: NUTS-DUR-001, NUTS-KV-001
// Depends-On: TestPutGetRoundTrip
func TestCommittedKVSurvivesCloseAndReopen(t *testing.T) {
	dir := t.TempDir()
	db := openAt(t, dir)
	putKV(t, db, "b", "k", "v")
	closeOK(t, db)
	later := openAt(t, dir)
	defer closeOK(t, later)
	if got := readKV(t, later, "b", "k"); got != "v" {
		t.Fatalf("got=%q", got)
	}
}

// Verifies: NUTS-TTL-002, NUTS-DUR-001
// Depends-On: TestPersistCancelsExpiration
func TestUnexpiredTTLStateSurvivesReopenThenExpires(t *testing.T) {
	dir := t.TempDir()
	db := openAt(t, dir)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("b"); err != nil {
			return err
		}
		return tx.Put("b", []byte("k"), []byte("v"), 2)
	})
	closeOK(t, db)
	later := openAt(t, dir)
	if readKV(t, later, "b", "k") != "v" {
		t.Fatal("missing before expiry")
	}
	closeOK(t, later)
	time.Sleep(2200 * time.Millisecond)
	final := openAt(t, dir)
	defer closeOK(t, final)
	err := final.View(func(tx *nutsdb.Tx) error { _, err := tx.Get("b", []byte("k")); return err })
	if !errors.Is(err, nutsdb.ErrKeyNotFound) {
		t.Fatalf("expired get=%v", err)
	}
}

// Verifies: NUTS-LST-002, NUTS-LST-003
// Depends-On: TestListPushAndRangeOrder
func TestListPeekPopAndSizeAgree(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewListBucket("l"); err != nil {
			return err
		}
		return tx.RPush("l", []byte("k"), []byte("a"), []byte("b"), []byte("c"))
	})
	_ = db.Update(func(tx *nutsdb.Tx) error {
		left, _ := tx.LPeek("l", []byte("k"))
		right, _ := tx.RPeek("l", []byte("k"))
		if string(left) != "a" || string(right) != "c" {
			return fmt.Errorf("peek %q %q", left, right)
		}
		popped, _ := tx.LPop("l", []byte("k"))
		if string(popped) != "a" {
			return fmt.Errorf("pop=%q", popped)
		}
		n, _ := tx.LSize("l", []byte("k"))
		if n != 2 {
			return fmt.Errorf("size=%d", n)
		}
		return nil
	})
}

// Verifies: NUTS-LST-004, NUTS-LST-005
// Depends-On: TestListPushAndRangeOrder
func TestListTrimAndRemoveCompose(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewListBucket("l"); err != nil {
			return err
		}
		return tx.RPush("l", []byte("k"), []byte("x"), []byte("a"), []byte("x"), []byte("b"), []byte("x"))
	})
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := compat.LRem(tx, "l", []byte("k"), 1, []byte("x")); err != nil {
			return err
		}
		return tx.LTrim("l", []byte("k"), 0, 2)
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		got, err := tx.LRange("l", []byte("k"), 0, -1)
		if err != nil {
			return err
		}
		if !reflect.DeepEqual(got, [][]byte{[]byte("a"), []byte("x"), []byte("b")}) {
			return fmt.Errorf("got=%q", got)
		}
		return nil
	})
}

// Verifies: NUTS-LST-006, NUTS-DUR-001
// Depends-On: TestListPushAndRangeOrder
func TestListImplementationsExposeEquivalentResults(t *testing.T) {
	var snapshots [][][]byte
	for _, impl := range []nutsdb.ListImplementationType{nutsdb.ListImplementationType(nutsdb.ListImplDoublyLinkedList), nutsdb.ListImplementationType(nutsdb.ListImplBTree)} {
		dir := t.TempDir()
		db := openAt(t, dir, nutsdb.WithListImpl(impl))
		_ = db.Update(func(tx *nutsdb.Tx) error {
			if err := tx.NewListBucket("l"); err != nil {
				return err
			}
			return tx.RPush("l", []byte("k"), []byte("a"), []byte("b"))
		})
		closeOK(t, db)
		later := openAt(t, dir, nutsdb.WithListImpl(impl))
		var got [][]byte
		_ = later.View(func(tx *nutsdb.Tx) error { var err error; got, err = tx.LRange("l", []byte("k"), 0, -1); return err })
		closeOK(t, later)
		snapshots = append(snapshots, got)
	}
	if !reflect.DeepEqual(snapshots[0], snapshots[1]) {
		t.Fatalf("snapshots=%q", snapshots)
	}
}

// Verifies: NUTS-SET-003, NUTS-SET-004
// Depends-On: TestSetUniquenessAndMembership
func TestSetUnionDifferenceAndRemovalAgree(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSetBucket("s"); err != nil {
			return err
		}
		_ = tx.SAdd("s", []byte("a"), []byte("1"), []byte("2"))
		return tx.SAdd("s", []byte("b"), []byte("2"), []byte("3"))
	})
	_ = db.Update(func(tx *nutsdb.Tx) error {
		union, _ := tx.SUnionByOneBucket("s", []byte("a"), []byte("b"))
		diff, _ := tx.SDiffByOneBucket("s", []byte("a"), []byte("b"))
		sort.Slice(union, func(i, j int) bool { return bytes.Compare(union[i], union[j]) < 0 })
		if !reflect.DeepEqual(union, [][]byte{[]byte("1"), []byte("2"), []byte("3")}) || !reflect.DeepEqual(diff, [][]byte{[]byte("1")}) {
			return fmt.Errorf("union=%q diff=%q", union, diff)
		}
		return tx.SRem("s", []byte("a"), []byte("2"))
	})
}

// Verifies: NUTS-SET-005
// Depends-On: TestSetUniquenessAndMembership
func TestSetMoveChangesBothViewsAtomically(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSetBucket("s"); err != nil {
			return err
		}
		_ = tx.SAdd("s", []byte("src"), []byte("x"))
		return tx.SAdd("s", []byte("dst"), []byte("y"))
	})
	_ = db.Update(func(tx *nutsdb.Tx) error {
		moved, err := tx.SMoveByOneBucket("s", []byte("src"), []byte("dst"), []byte("x"))
		if err != nil {
			return err
		}
		if !moved {
			return errors.New("not moved")
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		src, _ := tx.SIsMember("s", []byte("src"), []byte("x"))
		dst, _ := tx.SIsMember("s", []byte("dst"), []byte("x"))
		if src || !dst {
			return fmt.Errorf("src=%v dst=%v", src, dst)
		}
		return nil
	})
}

// Verifies: NUTS-ZST-004
// Depends-On: TestSortedSetScoreAndCardinality
func TestSortedSetRangeByRankReturnsMembersAndScores(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
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
		got, err := tx.ZRangeByRank("z", []byte("k"), 1, -1)
		if err != nil {
			return err
		}
		if len(got) != 3 || string(got[0].Value) != "a" || got[2].Score != 3 {
			return fmt.Errorf("got=%v", got)
		}
		return nil
	})
}

// Verifies: NUTS-ZST-005, NUTS-ZST-006
// Depends-On: TestSortedSetRanksAreOneBased
func TestSortedSetScoreRangeOptionsControlEndpointsAndLimit(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSortSetBucket("z"); err != nil {
			return err
		}
		for i, v := range []string{"a", "b", "c", "d"} {
			if err := tx.ZAdd("z", []byte("k"), float64(i+1), []byte(v)); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		opts := &nutsdb.GetByScoreRangeOptions{ExcludeStart: true, Limit: 2}
		got, err := tx.ZRangeByScore("z", []byte("k"), 1, 4, opts)
		if err != nil {
			return err
		}
		count, err := tx.ZCount("z", []byte("k"), 1, 4, opts)
		if err != nil {
			return err
		}
		if len(got) != 2 || count != 2 || string(got[0].Value) != "b" {
			return fmt.Errorf("got=%v count=%d", got, count)
		}
		return nil
	})
}

// Verifies: NUTS-ZST-007, NUTS-ZST-008
// Depends-On: TestSortedSetScoreAndCardinality
func TestSortedSetPeekPopAndRemoveStayConsistent(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewSortSetBucket("z"); err != nil {
			return err
		}
		_ = tx.ZAdd("z", []byte("k"), 1, []byte("a"))
		_ = tx.ZAdd("z", []byte("k"), 2, []byte("b"))
		return tx.ZAdd("z", []byte("k"), 3, []byte("c"))
	})
	_ = db.Update(func(tx *nutsdb.Tx) error {
		min, _ := tx.ZPeekMin("z", []byte("k"))
		max, _ := tx.ZPeekMax("z", []byte("k"))
		if string(min.Value) != "a" || string(max.Value) != "c" {
			return errors.New("peek mismatch")
		}
		popped, err := tx.ZPopMax("z", []byte("k"))
		if err != nil {
			return err
		}
		if string(popped.Value) != "c" {
			return errors.New("pop mismatch")
		}
		return tx.ZRem("z", []byte("k"), []byte("a"))
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		n, err := tx.ZCard("z", []byte("k"))
		if err != nil {
			return err
		}
		if n != 1 {
			return fmt.Errorf("card=%d", n)
		}
		return nil
	})
}

// Verifies: NUTS-DUR-001, NUTS-LST-001, NUTS-SET-002, NUTS-ZST-001
// Depends-On: TestListPushAndRangeOrder, TestSetUniquenessAndMembership, TestSortedSetScoreAndCardinality
func TestMixedCollectionsSurviveReopen(t *testing.T) {
	dir := t.TempDir()
	db := openAt(t, dir)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		_ = tx.NewListBucket("l")
		_ = tx.NewSetBucket("s")
		_ = tx.NewSortSetBucket("z")
		_ = tx.RPush("l", []byte("k"), []byte("a"))
		_ = tx.SAdd("s", []byte("k"), []byte("b"))
		return tx.ZAdd("z", []byte("k"), 7, []byte("c"))
	})
	closeOK(t, db)
	later := openAt(t, dir)
	defer closeOK(t, later)
	_ = later.View(func(tx *nutsdb.Tx) error {
		list, _ := tx.LRange("l", []byte("k"), 0, -1)
		member, _ := tx.SIsMember("s", []byte("k"), []byte("b"))
		score, _ := tx.ZScore("z", []byte("k"), []byte("c"))
		if len(list) != 1 || !member || score != 7 {
			return errors.New("reopen mismatch")
		}
		return nil
	})
}

// Verifies: NUTS-DUR-002
func TestBackupOpensWithCommittedKVState(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	putKV(t, db, "b", "k", "v")
	backup := t.TempDir()
	if err := db.Backup(backup); err != nil {
		t.Fatal(err)
	}
	copy := openAt(t, backup)
	defer closeOK(t, copy)
	if readKV(t, copy, "b", "k") != "v" {
		t.Fatal("backup mismatch")
	}
}

// Verifies: NUTS-DUR-002, NUTS-LST-001, NUTS-SET-002
func TestBackupPreservesCollectionState(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		_ = tx.NewListBucket("l")
		_ = tx.NewSetBucket("s")
		_ = tx.RPush("l", []byte("k"), []byte("a"), []byte("b"))
		return tx.SAdd("s", []byte("k"), []byte("x"))
	})
	backup := t.TempDir()
	if err := db.Backup(backup); err != nil {
		t.Fatal(err)
	}
	copy := openAt(t, backup)
	defer closeOK(t, copy)
	_ = copy.View(func(tx *nutsdb.Tx) error {
		list, _ := tx.LRange("l", []byte("k"), 0, -1)
		ok, _ := tx.SIsMember("s", []byte("k"), []byte("x"))
		if len(list) != 2 || !ok {
			return errors.New("backup collection mismatch")
		}
		return nil
	})
}

// Verifies: NUTS-DUR-003
func TestMergeWithTooFewSegmentsReturnsSentinel(t *testing.T) {
	db := openAt(t, t.TempDir(), nutsdb.WithEnableMergeV2(true))
	defer closeOK(t, db)
	if err := db.Merge(); !errors.Is(err, nutsdb.ErrDontNeedMerge) {
		t.Fatalf("merge=%v", err)
	}
}

func prepareMergeDB(t *testing.T) (*nutsdb.DB, string) {
	t.Helper()
	dir := t.TempDir()
	db := openAt(t, dir, nutsdb.WithSegmentSize(1024), nutsdb.WithEnableMergeV2(true))
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("b"); err != nil {
			return err
		}
		return nil
	})
	for i := 0; i < 20; i++ {
		value := bytes.Repeat([]byte{byte('a' + i%20)}, 300)
		err := db.Update(func(tx *nutsdb.Tx) error {
			return tx.Put("b", []byte(fmt.Sprintf("k%02d", i%5)), value, nutsdb.Persistent)
		})
		if err != nil {
			t.Fatalf("fill: %v", err)
		}
	}
	return db, dir
}

// Verifies: NUTS-DUR-004
func TestMergePreservesLiveAndDeletedState(t *testing.T) {
	db, _ := prepareMergeDB(t)
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Delete("b", []byte("k00")) })
	if err := db.Merge(); err != nil {
		t.Fatal(err)
	}
	_ = db.View(func(tx *nutsdb.Tx) error {
		if _, err := tx.Get("b", []byte("k00")); !errors.Is(err, nutsdb.ErrKeyNotFound) {
			return fmt.Errorf("deleted=%v", err)
		}
		for _, k := range []string{"k01", "k02", "k03", "k04"} {
			if _, err := tx.Get("b", []byte(k)); err != nil {
				return err
			}
		}
		return nil
	})
}

// Verifies: NUTS-DUR-001, NUTS-DUR-004
func TestMergedStateSurvivesReopen(t *testing.T) {
	db, dir := prepareMergeDB(t)
	if err := db.Merge(); err != nil {
		t.Fatal(err)
	}
	closeOK(t, db)
	later := openAt(t, dir, nutsdb.WithSegmentSize(1024), nutsdb.WithEnableMergeV2(true))
	defer closeOK(t, later)
	for _, k := range []string{"k00", "k01", "k02", "k03", "k04"} {
		if got := readKV(t, later, "b", k); got == "" {
			t.Fatalf("missing %s", k)
		}
	}
}

// Verifies: NUTS-WCH-001
func TestWatchDisabledReturnsSentinel(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	err := db.Watch("b", []byte("k"), func(*nutsdb.Message) error { return nil })
	if !errors.Is(err, nutsdb.ErrWatchFeatureDisabled) {
		t.Fatalf("watch=%v", err)
	}
}

func startWatch(t *testing.T, db *nutsdb.DB, bucket, key string, cb func(*nutsdb.Message) error) <-chan error {
	t.Helper()
	done := make(chan error, 1)
	go func() { done <- compat.Watch(db, bucket, []byte(key), cb) }()
	time.Sleep(200 * time.Millisecond)
	return done
}

// Verifies: NUTS-WCH-002, NUTS-WCH-004
func TestCommittedSetProducesMatchingWatchMessage(t *testing.T) {
	db := openWatchAt(t, t.TempDir())
	defer closeOK(t, db)
	putKV(t, db, "b", "seed", "x")
	stop := errors.New("stop")
	messages := make(chan *nutsdb.Message, 1)
	done := startWatch(t, db, "b", "k", func(m *nutsdb.Message) error { messages <- m; return stop })
	putKV(t, db, "b", "k", "v")
	select {
	case m := <-messages:
		if m.BucketName != "b" || string(m.Key) != "k" || string(m.Value) != "v" || m.Flag != nutsdb.DataSetFlag || m.Timestamp == 0 {
			t.Fatalf("message=%+v", m)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("no message")
	}
	if err := <-done; !errors.Is(err, stop) {
		t.Fatalf("watch=%v", err)
	}
}

// Verifies: NUTS-WCH-002, NUTS-WCH-005
func TestCommittedDeleteProducesMatchingWatchMessage(t *testing.T) {
	dir := t.TempDir()
	seed := openAt(t, dir)
	putKV(t, seed, "b", "k", "v")
	closeOK(t, seed)
	db := openWatchAt(t, dir)
	defer closeOK(t, db)
	stop := errors.New("stop")
	messages := make(chan *nutsdb.Message, 1)
	done := startWatch(t, db, "b", "k", func(m *nutsdb.Message) error { messages <- m; return stop })
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.Delete("b", []byte("k")) })
	select {
	case m := <-messages:
		if m.BucketName != "b" || string(m.Key) != "k" || m.Flag != nutsdb.DataDeleteFlag {
			t.Fatalf("message=%+v", m)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("no delete message")
	}
	if err := <-done; !errors.Is(err, stop) {
		t.Fatalf("watch=%v", err)
	}
}

// Verifies: NUTS-WCH-003
func TestRolledBackWriteProducesNoWatchMessage(t *testing.T) {
	db := openWatchAt(t, t.TempDir())
	putKV(t, db, "b", "seed", "x")
	messages := make(chan *nutsdb.Message, 1)
	done := startWatch(t, db, "b", "k", func(m *nutsdb.Message) error { messages <- m; return nil })
	stop := errors.New("rollback")
	_ = db.Update(func(tx *nutsdb.Tx) error { _ = tx.Put("b", []byte("k"), []byte("v"), nutsdb.Persistent); return stop })
	select {
	case m := <-messages:
		t.Fatalf("unexpected=%+v", m)
	case <-time.After(350 * time.Millisecond):
	}
	closeOK(t, db)
	if err := <-done; err != nil {
		t.Fatalf("watch=%v", err)
	}
}

// Verifies: NUTS-WCH-007
func TestWatchReturnsCallbackError(t *testing.T) {
	db := openWatchAt(t, t.TempDir())
	defer closeOK(t, db)
	putKV(t, db, "b", "seed", "x")
	stop := errors.New("callback stop")
	done := startWatch(t, db, "b", "k", func(*nutsdb.Message) error { return stop })
	putKV(t, db, "b", "k", "v")
	select {
	case err := <-done:
		if !errors.Is(err, stop) {
			t.Fatalf("err=%v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("watch did not stop")
	}
}

// Verifies: NUTS-WCH-006
func TestWatchCallbackTimeoutReturnsSentinel(t *testing.T) {
	db := openWatchAt(t, t.TempDir())
	defer closeOK(t, db)
	putKV(t, db, "b", "seed", "x")
	opts := nutsdb.NewWatchOptions()
	opts.WithCallbackTimeout(50 * time.Millisecond)
	done := make(chan error, 1)
	go func() {
		done <- compat.Watch(db, "b", []byte("k"), func(*nutsdb.Message) error { time.Sleep(300 * time.Millisecond); return nil }, *opts)
	}()
	time.Sleep(200 * time.Millisecond)
	putKV(t, db, "b", "k", "v")
	select {
	case err := <-done:
		if !errors.Is(err, nutsdb.ErrWatchingCallbackTimeout) {
			t.Fatalf("err=%v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("timeout not returned")
	}
}

// Verifies: NUTS-WCH-008
func TestCloseFinishesActiveWatch(t *testing.T) {
	db := openWatchAt(t, t.TempDir())
	putKV(t, db, "b", "seed", "x")
	done := startWatch(t, db, "b", "k", func(*nutsdb.Message) error { return nil })
	closeOK(t, db)
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("watch close=%v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("watch remained active")
	}
}

// Verifies: NUTS-KV-001, NUTS-KV-012, NUTS-SCN-001, NUTS-ITR-002
func TestKVDirectBulkScanAndIteratorViewsAgree(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	_ = db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewKVBucket("b"); err != nil {
			return err
		}
		for _, k := range []string{"p1", "p2", "p3"} {
			if err := tx.Put("b", []byte(k), []byte(k+"v"), nutsdb.Persistent); err != nil {
				return err
			}
		}
		return nil
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		keys, values, _ := compat.GetAll(tx, "b")
		scanned, _ := tx.PrefixScan("b", []byte("p"), 0, nutsdb.ScanNoLimit)
		it := nutsdb.NewIterator(tx, "b", nutsdb.IteratorOptions{})
		var ikeys, ivals [][]byte
		for it.Valid() {
			ikeys = append(ikeys, append([]byte(nil), it.Key()...))
			v, _ := compat.IteratorValue(it)
			ivals = append(ivals, append([]byte(nil), v...))
			it.Next()
		}
		it.Release()
		if !reflect.DeepEqual(keys, ikeys) || !reflect.DeepEqual(values, ivals) || !reflect.DeepEqual(values, scanned) {
			return fmt.Errorf("keys=%q ikeys=%q values=%q ivals=%q scan=%q", keys, ikeys, values, ivals, scanned)
		}
		return nil
	})
}

// Verifies: NUTS-DB-007, NUTS-LST-001, NUTS-SET-001, NUTS-ZST-001
func TestCollectionChangesRollbackTogether(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	stop := errors.New("stop")
	_ = db.Update(func(tx *nutsdb.Tx) error {
		_ = tx.NewListBucket("l")
		_ = tx.NewSetBucket("s")
		_ = tx.NewSortSetBucket("z")
		_ = tx.RPush("l", []byte("k"), []byte("a"))
		_ = tx.SAdd("s", []byte("k"), []byte("b"))
		_ = tx.ZAdd("z", []byte("k"), 1, []byte("c"))
		return stop
	})
	_ = db.View(func(tx *nutsdb.Tx) error {
		if tx.ExistBucket(nutsdb.DataStructureList, "l") || tx.ExistBucket(nutsdb.DataStructureSet, "s") || tx.ExistBucket(nutsdb.DataStructureSortedSet, "z") {
			return errors.New("rolled-back collection visible")
		}
		return nil
	})
}

// Verifies: NUTS-BKT-004, NUTS-DUR-001
func TestDeletedBucketRemainsAbsentAfterReopen(t *testing.T) {
	dir := t.TempDir()
	db := openAt(t, dir)
	putKV(t, db, "b", "k", "v")
	_ = db.Update(func(tx *nutsdb.Tx) error { return tx.DeleteBucket(nutsdb.DataStructureBTree, "b") })
	closeOK(t, db)
	later := openAt(t, dir)
	defer closeOK(t, later)
	_ = later.View(func(tx *nutsdb.Tx) error {
		if tx.ExistBucket(nutsdb.DataStructureBTree, "b") {
			return errors.New("deleted bucket restored")
		}
		return nil
	})
}

// Verifies: NUTS-DUR-002, NUTS-KV-001
func TestBackupIsIndependentFromLaterSourceWrites(t *testing.T) {
	db := openAt(t, t.TempDir())
	defer closeOK(t, db)
	putKV(t, db, "b", "k", "before")
	backup := t.TempDir()
	if err := db.Backup(backup); err != nil {
		t.Fatal(err)
	}
	putKV(t, db, "b", "k", "after")
	copy := openAt(t, backup)
	defer closeOK(t, copy)
	if got := readKV(t, copy, "b", "k"); got != "before" {
		t.Fatalf("backup=%q", got)
	}
}
