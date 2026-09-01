package nutsdbv5gate_test

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"sync"
	"testing"
	"time"

	nutsdb "github.com/nutsdb/nutsdb"
)

const streamBucket = "commit-stream-v5"

func openDatabase(t *testing.T, structures ...nutsdb.DataStructure) (*nutsdb.DB, nutsdb.Options) {
	t.Helper()
	opt := nutsdb.DefaultOptions
	opt.Dir = t.TempDir()
	db, err := nutsdb.Open(opt)
	if err != nil {
		t.Fatal(err)
	}
	if len(structures) != 0 {
		if err := db.Update(func(tx *nutsdb.Tx) error {
			for _, structure := range structures {
				if err := tx.NewBucket(structure, streamBucket); err != nil {
					return err
				}
			}
			return nil
		}); err != nil {
			_ = db.Close()
			t.Fatal(err)
		}
	}
	return db, opt
}

func openStream(t *testing.T, db *nutsdb.DB) *nutsdb.CommitStream {
	t.Helper()
	stream, err := db.CommitStream()
	if err != nil {
		t.Fatal(err)
	}
	if stream == nil {
		t.Fatal("nil commit stream")
	}
	return stream
}

func nextRevision(t *testing.T, stream *nutsdb.CommitStream) nutsdb.CommitRevision {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 1500*time.Millisecond)
	defer cancel()
	revision, err := stream.Next(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if revision == 0 {
		t.Fatal("zero revision")
	}
	return revision
}

func requireCanceledWithoutConsumption(t *testing.T, stream *nutsdb.CommitStream) {
	t.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if revision, err := stream.Next(ctx); revision != 0 || !errors.Is(err, context.Canceled) {
		t.Fatalf("canceled wait: revision=%d err=%v", revision, err)
	}
}

func putValue(t *testing.T, db *nutsdb.DB, key, value string) {
	t.Helper()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		return tx.Put(streamBucket, []byte(key), []byte(value), nutsdb.Persistent)
	}); err != nil {
		t.Fatal(err)
	}
}

func getValue(t *testing.T, db *nutsdb.DB, key string) string {
	t.Helper()
	var value []byte
	if err := db.View(func(tx *nutsdb.Tx) error {
		var err error
		value, err = tx.Get(streamBucket, []byte(key))
		return err
	}); err != nil {
		t.Fatal(err)
	}
	return string(value)
}

func TestNutsDBV5A01(t *testing.T) {
	db, _ := openDatabase(t)
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	if stream, err := db.CommitStream(); stream != nil || !errors.Is(err, nutsdb.ErrDBClosed) {
		t.Fatalf("closed database stream: %#v %v", stream, err)
	}
}

func TestNutsDBV5A02(t *testing.T) {
	var db *nutsdb.DB
	if stream, err := db.CommitStream(); stream != nil || !errors.Is(err, nutsdb.ErrDBClosed) {
		t.Fatalf("nil database stream: %#v %v", stream, err)
	}
}

func TestNutsDBV5A03(t *testing.T) {
	var stream *nutsdb.CommitStream
	if revision, err := stream.Next(context.Background()); revision != 0 || !errors.Is(err, nutsdb.ErrCommitStreamClosed) {
		t.Fatalf("nil stream next: %d %v", revision, err)
	}
}

func TestNutsDBV5A04(t *testing.T) {
	stream := &nutsdb.CommitStream{}
	if revision, err := stream.Next(nil); revision != 0 || !errors.Is(err, nutsdb.ErrInvalidCommitStreamRequest) {
		t.Fatalf("nil context: %d %v", revision, err)
	}
}

func TestNutsDBV5A05(t *testing.T) {
	stream := &nutsdb.CommitStream{}
	if err := stream.Close(); err != nil {
		t.Fatalf("zero stream close: %v", err)
	}
}

func TestNutsDBV5A06(t *testing.T) {
	stream := &nutsdb.CommitStream{}
	if err := stream.Close(); err != nil {
		t.Fatal(err)
	}
	if err := stream.Close(); err != nil {
		t.Fatalf("repeated close: %v", err)
	}
}

func TestNutsDBV5A07(t *testing.T) {
	var earlier nutsdb.CommitRevision = 19
	var later nutsdb.CommitRevision = 23
	if earlier == 0 || later <= earlier {
		t.Fatalf("revision ordering: %d %d", earlier, later)
	}
}

func TestNutsDBV5A08(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "a08", "first")
	if revision := nextRevision(t, stream); revision == 0 {
		t.Fatal("first commit was not published")
	}
}

func TestNutsDBV5A09(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "a09/one", "one")
	putValue(t, db, "a09/two", "two")
	first, second := nextRevision(t, stream), nextRevision(t, stream)
	if second != first+1 {
		t.Fatalf("nonconsecutive commit order: %d %d", first, second)
	}
}

func TestNutsDBV5A10(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.Put(streamBucket, []byte("a10/a"), []byte("A"), nutsdb.Persistent); err != nil {
			return err
		}
		return tx.Put(streamBucket, []byte("a10/b"), []byte("B"), nutsdb.Persistent)
	}); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	requireCanceledWithoutConsumption(t, stream)
}

func TestNutsDBV5A11(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "a11/base", "base")
	first := nextRevision(t, stream)
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Put(streamBucket, []byte("a11/discard"), []byte("x"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	putValue(t, db, "a11/after", "after")
	if second := nextRevision(t, stream); second != first+1 {
		t.Fatalf("rollback advanced revision: %d %d", first, second)
	}
}

func TestNutsDBV5A12(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "a12/base", "base")
	first := nextRevision(t, stream)
	sentinel := errors.New("a12 callback failure")
	err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.Put(streamBucket, []byte("a12/discard"), []byte("x"), nutsdb.Persistent); err != nil {
			return err
		}
		return sentinel
	})
	if !errors.Is(err, sentinel) {
		t.Fatal(err)
	}
	putValue(t, db, "a12/after", "after")
	if second := nextRevision(t, stream); second != first+1 {
		t.Fatalf("failed callback advanced revision: %d %d", first, second)
	}
}

func TestNutsDBV5A13(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "a13/base", "base")
	first := nextRevision(t, stream)
	if err := db.Update(func(*nutsdb.Tx) error { return nil }); err != nil {
		t.Fatal(err)
	}
	putValue(t, db, "a13/after", "after")
	if second := nextRevision(t, stream); second != first+1 {
		t.Fatalf("empty update advanced revision: %d %d", first, second)
	}
	requireCanceledWithoutConsumption(t, stream)
}

func TestNutsDBV5A14(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	requireCanceledWithoutConsumption(t, stream)
	putValue(t, db, "a14", "pending")
	if revision := nextRevision(t, stream); revision == 0 {
		t.Fatal("cancellation consumed future revision")
	}
}

func TestNutsDBV5A15(t *testing.T) {
	db, _ := openDatabase(t)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if revision, err := stream.Next(nil); revision != 0 || !errors.Is(err, nutsdb.ErrInvalidCommitStreamRequest) {
		t.Fatalf("active nil context: %d %v", revision, err)
	}
}

func TestNutsDBV5A16(t *testing.T) {
	db, _ := openDatabase(t)
	defer db.Close()
	stream := openStream(t, db)
	if err := stream.Close(); err != nil {
		t.Fatal(err)
	}
	if revision, err := stream.Next(context.Background()); revision != 0 || !errors.Is(err, nutsdb.ErrCommitStreamClosed) {
		t.Fatalf("next after close: %d %v", revision, err)
	}
}

func TestNutsDBV5I01(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	putValue(t, db, "i01", "btree")
	if got := getValue(t, db, "i01"); got != "btree" {
		t.Fatalf("value %q", got)
	}
}

func TestNutsDBV5I02(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Put(streamBucket, []byte("i02"), []byte("discard"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	err = db.View(func(tx *nutsdb.Tx) error { _, err := tx.Get(streamBucket, []byte("i02")); return err })
	if !errors.Is(err, nutsdb.ErrKeyNotFound) {
		t.Fatalf("rolled back key: %v", err)
	}
}

func TestNutsDBV5I03(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureList)
	defer db.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.LPush(streamBucket, []byte("i03"), []byte("left")); err != nil {
			return err
		}
		return tx.RPush(streamBucket, []byte("i03"), []byte("right"))
	}); err != nil {
		t.Fatal(err)
	}
	if err := db.View(func(tx *nutsdb.Tx) error {
		values, err := tx.LRange(streamBucket, []byte("i03"), 0, -1)
		if err == nil && (len(values) != 2 || string(values[0]) != "left" || string(values[1]) != "right") {
			return fmt.Errorf("list %q", values)
		}
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestNutsDBV5I04(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureSet)
	defer db.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.SAdd(streamBucket, []byte("i04"), []byte("a"), []byte("b")) }); err != nil {
		t.Fatal(err)
	}
	if err := db.View(func(tx *nutsdb.Tx) error {
		count, err := tx.SCard(streamBucket, []byte("i04"))
		if err == nil && count != 2 {
			return fmt.Errorf("set count %d", count)
		}
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestNutsDBV5I05(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureSortedSet)
	defer db.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.ZAdd(streamBucket, []byte("i05"), 7.5, []byte("member")) }); err != nil {
		t.Fatal(err)
	}
	if err := db.View(func(tx *nutsdb.Tx) error {
		score, err := tx.ZScore(streamBucket, []byte("i05"), []byte("member"))
		if err == nil && score != 7.5 {
			return fmt.Errorf("score %v", score)
		}
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestNutsDBV5I06(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree, nutsdb.DataStructureList, nutsdb.DataStructureSet, nutsdb.DataStructureSortedSet)
	defer db.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.Put(streamBucket, []byte("i06-kv"), []byte("v"), nutsdb.Persistent); err != nil {
			return err
		}
		if err := tx.RPush(streamBucket, []byte("i06-list"), []byte("l")); err != nil {
			return err
		}
		if err := tx.SAdd(streamBucket, []byte("i06-set"), []byte("s")); err != nil {
			return err
		}
		return tx.ZAdd(streamBucket, []byte("i06-z"), 2, []byte("z"))
	}); err != nil {
		t.Fatal(err)
	}
	if getValue(t, db, "i06-kv") != "v" {
		t.Fatal("multi-owner value")
	}
}

func TestNutsDBV5I07(t *testing.T) {
	db, opt := openDatabase(t, nutsdb.DataStructureBTree)
	putValue(t, db, "i07", "persisted")
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	reopened, err := nutsdb.Open(opt)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	if got := getValue(t, reopened, "i07"); got != "persisted" {
		t.Fatalf("reopened %q", got)
	}
}

func TestNutsDBV5I08(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "i08", "visible")
	_ = nextRevision(t, stream)
	if got := getValue(t, db, "i08"); got != "visible" {
		t.Fatalf("state %q", got)
	}
}

func TestNutsDBV5I09(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Put(streamBucket, []byte("i09"), []byte("explicit"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	if getValue(t, db, "i09") != "explicit" {
		t.Fatal("explicit commit view")
	}
}

func TestNutsDBV5I10(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureList)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.RPush(streamBucket, []byte("i10"), []byte("one"), []byte("two")) }); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	if err := db.View(func(tx *nutsdb.Tx) error {
		values, err := tx.LRange(streamBucket, []byte("i10"), 0, -1)
		if err == nil && len(values) != 2 {
			return fmt.Errorf("list length %d", len(values))
		}
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestNutsDBV5I11(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureSet)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		return tx.SAdd(streamBucket, []byte("i11"), []byte("x"), []byte("y"), []byte("z"))
	}); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	if err := db.View(func(tx *nutsdb.Tx) error {
		count, err := tx.SCard(streamBucket, []byte("i11"))
		if err == nil && count != 3 {
			return fmt.Errorf("set count %d", count)
		}
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestNutsDBV5I12(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureSortedSet)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.ZAdd(streamBucket, []byte("i12"), 12.25, []byte("member")) }); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	if err := db.View(func(tx *nutsdb.Tx) error {
		score, err := tx.ZScore(streamBucket, []byte("i12"), []byte("member"))
		if err == nil && score != 12.25 {
			return fmt.Errorf("score %v", score)
		}
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestNutsDBV5I13(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree, nutsdb.DataStructureList, nutsdb.DataStructureSet, nutsdb.DataStructureSortedSet)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.Put(streamBucket, []byte("i13-kv"), []byte("v"), nutsdb.Persistent); err != nil {
			return err
		}
		if err := tx.LPush(streamBucket, []byte("i13-list"), []byte("l")); err != nil {
			return err
		}
		if err := tx.SAdd(streamBucket, []byte("i13-set"), []byte("s")); err != nil {
			return err
		}
		return tx.ZAdd(streamBucket, []byte("i13-z"), 13, []byte("z"))
	}); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	requireCanceledWithoutConsumption(t, stream)
}

func TestNutsDBV5I14(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	left, right := openStream(t, db), openStream(t, db)
	defer left.Close()
	defer right.Close()
	putValue(t, db, "i14", "fanout")
	if a, b := nextRevision(t, left), nextRevision(t, right); a != b {
		t.Fatalf("fanout revisions: %d %d", a, b)
	}
}

func TestNutsDBV5I15(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	first, second := openStream(t, db), openStream(t, db)
	defer first.Close()
	defer second.Close()
	putValue(t, db, "i15", "owned")
	one := nextRevision(t, first)
	if two := nextRevision(t, second); two != one {
		t.Fatalf("consumption leaked: %d %d", one, two)
	}
}

func TestNutsDBV5I16(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	closed, live := openStream(t, db), openStream(t, db)
	defer live.Close()
	if err := closed.Close(); err != nil {
		t.Fatal(err)
	}
	putValue(t, db, "i16", "live")
	_ = nextRevision(t, live)
	if revision, err := closed.Next(context.Background()); revision != 0 || !errors.Is(err, nutsdb.ErrCommitStreamClosed) {
		t.Fatalf("closed peer: %d %v", revision, err)
	}
}

func TestNutsDBV5I17(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	slow, fast := openStream(t, db), openStream(t, db)
	defer slow.Close()
	defer fast.Close()
	for index := 0; index < 5; index++ {
		putValue(t, db, fmt.Sprintf("i17/%d", index), "queued")
	}
	for index := 0; index < 5; index++ {
		a, b := nextRevision(t, slow), nextRevision(t, fast)
		if a != b {
			t.Fatalf("queued ownership at %d: %d %d", index, a, b)
		}
	}
}

func TestNutsDBV5I18(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	canceled, peer := openStream(t, db), openStream(t, db)
	defer canceled.Close()
	defer peer.Close()
	requireCanceledWithoutConsumption(t, canceled)
	putValue(t, db, "i18", "after-cancel")
	peerRevision := nextRevision(t, peer)
	if ownRevision := nextRevision(t, canceled); ownRevision != peerRevision {
		t.Fatalf("canceled owner lost revision: %d %d", ownRevision, peerRevision)
	}
}

func TestNutsDBV5I19(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	early := openStream(t, db)
	defer early.Close()
	putValue(t, db, "i19/early", "one")
	first := nextRevision(t, early)
	late := openStream(t, db)
	defer late.Close()
	putValue(t, db, "i19/late", "two")
	second := nextRevision(t, early)
	if lateOnly := nextRevision(t, late); lateOnly != second || second != first+1 {
		t.Fatalf("creation boundary: %d %d %d", first, second, lateOnly)
	}
}

func TestNutsDBV5I20(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	sentinel := errors.New("i20 abort")
	err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.Put(streamBucket, []byte("i20/bad"), []byte("bad"), nutsdb.Persistent); err != nil {
			return err
		}
		return sentinel
	})
	if !errors.Is(err, sentinel) {
		t.Fatal(err)
	}
	putValue(t, db, "i20/good", "good")
	_ = nextRevision(t, stream)
	requireCanceledWithoutConsumption(t, stream)
}

func TestNutsDBV5I21(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	tx, err := db.Begin(true)
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Put(streamBucket, []byte("i21/bad"), []byte("bad"), nutsdb.Persistent); err != nil {
		t.Fatal(err)
	}
	if err := tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	putValue(t, db, "i21/good", "good")
	_ = nextRevision(t, stream)
	requireCanceledWithoutConsumption(t, stream)
}

func TestNutsDBV5I22(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.DeleteBucket(nutsdb.DataStructureBTree, streamBucket) }); err != nil {
		t.Fatal(err)
	}
	_ = nextRevision(t, stream)
	if err := db.View(func(tx *nutsdb.Tx) error { _, err := tx.Get(streamBucket, []byte("missing")); return err }); err == nil {
		t.Fatal("deleted bucket remained readable")
	}
}

func TestNutsDBV5I23(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	if err := db.View(func(tx *nutsdb.Tx) error { _, err := tx.Get(streamBucket, []byte("i23/missing")); return err }); !errors.Is(err, nutsdb.ErrKeyNotFound) {
		t.Fatal(err)
	}
	putValue(t, db, "i23/present", "present")
	_ = nextRevision(t, stream)
	requireCanceledWithoutConsumption(t, stream)
}

func TestNutsDBV5I24(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	putValue(t, db, "i24/one", "one")
	first := nextRevision(t, stream)
	if err := db.Merge(); err != nil && !errors.Is(err, nutsdb.ErrDontNeedMerge) {
		t.Fatal(err)
	}
	putValue(t, db, "i24/two", "two")
	if second := nextRevision(t, stream); second != first+1 {
		t.Fatalf("maintenance advanced stream: %d %d", first, second)
	}
}

func TestNutsDBV5S01(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree, nutsdb.DataStructureList, nutsdb.DataStructureSet)
	defer db.Close()
	streams := []*nutsdb.CommitStream{openStream(t, db), openStream(t, db), openStream(t, db)}
	defer func() {
		for _, stream := range streams {
			_ = stream.Close()
		}
	}()
	if err := db.Update(func(tx *nutsdb.Tx) error {
		return tx.Put(streamBucket, []byte("s01-kv"), []byte("v"), nutsdb.Persistent)
	}); err != nil {
		t.Fatal(err)
	}
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.LPush(streamBucket, []byte("s01-list"), []byte("l")) }); err != nil {
		t.Fatal(err)
	}
	if err := db.Update(func(tx *nutsdb.Tx) error { return tx.SAdd(streamBucket, []byte("s01-set"), []byte("s")) }); err != nil {
		t.Fatal(err)
	}
	for round := 0; round < 3; round++ {
		expected := nextRevision(t, streams[0])
		for owner := 1; owner < len(streams); owner++ {
			if got := nextRevision(t, streams[owner]); got != expected {
				t.Fatalf("round %d owner %d: %d %d", round, owner, expected, got)
			}
		}
	}
}

func TestNutsDBV5S02(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	stream := openStream(t, db)
	putValue(t, db, "s02/one", "one")
	putValue(t, db, "s02/two", "two")
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	first, second := nextRevision(t, stream), nextRevision(t, stream)
	if second != first+1 {
		t.Fatalf("drain order: %d %d", first, second)
	}
	if revision, err := stream.Next(context.Background()); revision != 0 || !errors.Is(err, nutsdb.ErrDBClosed) {
		t.Fatalf("drained terminal: %d %v", revision, err)
	}
}

func TestNutsDBV5S03(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	departing, survivor := openStream(t, db), openStream(t, db)
	defer survivor.Close()
	if err := departing.Close(); err != nil {
		t.Fatal(err)
	}
	putValue(t, db, "s03", "survives")
	_ = nextRevision(t, survivor)
	if getValue(t, db, "s03") != "survives" {
		t.Fatal("stream close changed database")
	}
}

func TestNutsDBV5S04(t *testing.T) {
	db, opt := openDatabase(t, nutsdb.DataStructureBTree)
	old := openStream(t, db)
	putValue(t, db, "s04/before", "before")
	_ = nextRevision(t, old)
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	if revision, err := old.Next(context.Background()); revision != 0 || !errors.Is(err, nutsdb.ErrDBClosed) {
		t.Fatalf("old generation: %d %v", revision, err)
	}
	reopened, err := nutsdb.Open(opt)
	if err != nil {
		t.Fatal(err)
	}
	defer reopened.Close()
	fresh := openStream(t, reopened)
	defer fresh.Close()
	putValue(t, reopened, "s04/after", "after")
	if revision := nextRevision(t, fresh); revision == 0 {
		t.Fatal("fresh generation")
	}
}

func TestNutsDBV5S05(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	const writers = 8
	start := make(chan struct{})
	var wg sync.WaitGroup
	for index := 0; index < writers; index++ {
		index := index
		wg.Add(1)
		go func() { defer wg.Done(); <-start; putValue(t, db, fmt.Sprintf("s05/%02d", index), "concurrent") }()
	}
	close(start)
	wg.Wait()
	var previous nutsdb.CommitRevision
	for index := 0; index < writers; index++ {
		current := nextRevision(t, stream)
		if previous != 0 && current != previous+1 {
			t.Fatalf("concurrent order: %d %d", previous, current)
		}
		previous = current
	}
}

func TestNutsDBV5S06(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	streams := []*nutsdb.CommitStream{openStream(t, db), openStream(t, db), openStream(t, db), openStream(t, db)}
	defer func() {
		for _, stream := range streams {
			_ = stream.Close()
		}
	}()
	for index := 0; index < 6; index++ {
		putValue(t, db, fmt.Sprintf("s06/%d", index), fmt.Sprintf("value-%d", index))
	}
	for index := 0; index < 6; index++ {
		expected := nextRevision(t, streams[0])
		for owner := 1; owner < 4; owner++ {
			if got := nextRevision(t, streams[owner]); got != expected {
				t.Fatalf("owner %d event %d: %d %d", owner, index, got, expected)
			}
		}
	}
}

func TestNutsDBV5S07(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	defer db.Close()
	stream := openStream(t, db)
	defer stream.Close()
	for index := 0; index < 24; index++ {
		putValue(t, db, fmt.Sprintf("s07/%02d", index), fmt.Sprintf("payload-%02d", index))
	}
	var previous nutsdb.CommitRevision
	for index := 0; index < 24; index++ {
		revision := nextRevision(t, stream)
		if previous != 0 && revision != previous+1 {
			t.Fatalf("backlog order at %d: %d %d", index, previous, revision)
		}
		previous = revision
	}
	if getValue(t, db, "s07/23") != "payload-23" {
		t.Fatal("backlog state mismatch")
	}
}

func TestNutsDBV5S08(t *testing.T) {
	db, _ := openDatabase(t, nutsdb.DataStructureBTree)
	first, second := openStream(t, db), openStream(t, db)
	for index := 0; index < 4; index++ {
		putValue(t, db, fmt.Sprintf("s08/%d", index), "queued")
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	for index := 0; index < 4; index++ {
		a, b := nextRevision(t, first), nextRevision(t, second)
		if a != b {
			t.Fatalf("multi-drain %d: %d %d", index, a, b)
		}
	}
	for owner, stream := range []*nutsdb.CommitStream{first, second} {
		if revision, err := stream.Next(context.Background()); revision != 0 || !errors.Is(err, nutsdb.ErrDBClosed) {
			t.Fatalf("owner %d terminal: %d %v", owner, revision, err)
		}
	}
}

var _ = filepath.Separator
