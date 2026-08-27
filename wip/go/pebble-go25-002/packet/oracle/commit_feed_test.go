package pebblegate_test

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"sort"
	"sync"
	"testing"
	"time"

	pebble "github.com/cockroachdb/pebble/v2"
	"github.com/cockroachdb/pebble/v2/vfs"
)

type dbFixture struct {
	db     *pebble.DB
	fs     vfs.FS
	closed bool
}

func newDBFixture(t *testing.T, configure ...func(*pebble.Options)) *dbFixture {
	t.Helper()
	fs := vfs.NewMem()
	options := &pebble.Options{FS: fs}
	for _, fn := range configure {
		fn(options)
	}
	db, err := pebble.Open("db", options)
	if err != nil {
		t.Fatal(err)
	}
	f := &dbFixture{db: db, fs: fs}
	t.Cleanup(func() {
		if !f.closed {
			_ = f.db.Close()
			f.closed = true
		}
	})
	return f
}

func (f *dbFixture) close(t *testing.T) {
	t.Helper()
	if f.closed {
		return
	}
	if err := f.db.Close(); err != nil {
		t.Fatal(err)
	}
	f.closed = true
}

func subscribe(t *testing.T, db *pebble.DB, ctx context.Context, options pebble.CommitFeedOptions) *pebble.CommitFeed {
	t.Helper()
	feed, err := db.SubscribeCommits(ctx, options)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = feed.Close() })
	return feed
}

func receive(t *testing.T, feed *pebble.CommitFeed) pebble.CommitBatch {
	t.Helper()
	select {
	case event, ok := <-feed.Events():
		if !ok {
			t.Fatalf("feed closed early: %v", feed.Err())
		}
		return event
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for commit event")
		return pebble.CommitBatch{}
	}
}

func requireNoEvent(t *testing.T, feed *pebble.CommitFeed) {
	t.Helper()
	select {
	case event, ok := <-feed.Events():
		if !ok {
			t.Fatalf("feed closed while checking silence: %v", feed.Err())
		}
		t.Fatalf("unexpected commit event: %+v", event)
	case <-time.After(25 * time.Millisecond):
	}
}

func requireClosed(t *testing.T, feed *pebble.CommitFeed) {
	t.Helper()
	select {
	case _, ok := <-feed.Events():
		if ok {
			t.Fatal("expected a closed event channel")
		}
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for feed closure")
	}
}

func put(t *testing.T, db *pebble.DB, key, value string) {
	t.Helper()
	if err := db.Set([]byte(key), []byte(value), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
}

func valueOf(t *testing.T, db *pebble.DB, key string) string {
	t.Helper()
	value, closer, err := db.Get([]byte(key))
	if err != nil {
		t.Fatal(err)
	}
	defer closer.Close()
	return string(value)
}

func keysOf(t *testing.T, db *pebble.DB, options *pebble.IterOptions) []string {
	t.Helper()
	iter, err := db.NewIter(options)
	if err != nil {
		t.Fatal(err)
	}
	defer iter.Close()
	var keys []string
	for valid := iter.First(); valid; valid = iter.Next() {
		keys = append(keys, string(iter.Key()))
	}
	if err := iter.Error(); err != nil {
		t.Fatal(err)
	}
	return keys
}

func operationKinds(event pebble.CommitBatch) []pebble.CommitKind {
	kinds := make([]pebble.CommitKind, len(event.Operations))
	for i := range event.Operations {
		kinds[i] = event.Operations[i].Kind
	}
	return kinds
}

// Native atomic controls: seven stable, unrelated Pebble surfaces.

func TestPebbleV2A01PointWriteRead(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "a", "alpha")
	if got := valueOf(t, f.db, "a"); got != "alpha" {
		t.Fatalf("point read = %q", got)
	}
}

func TestPebbleV2A02PointDelete(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "gone", "value")
	if err := f.db.Delete([]byte("gone"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	if _, closer, err := f.db.Get([]byte("gone")); !errors.Is(err, pebble.ErrNotFound) {
		if closer != nil {
			closer.Close()
		}
		t.Fatalf("deleted lookup error = %v", err)
	}
}

func TestPebbleV2A03BatchCountExcludesLogData(t *testing.T) {
	f := newDBFixture(t)
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Set([]byte("a"), []byte("1"), nil)
	_ = batch.LogData([]byte("opaque"), nil)
	_ = batch.Delete([]byte("b"), nil)
	if batch.Count() != 2 || batch.Empty() {
		t.Fatalf("batch count=%d empty=%v", batch.Count(), batch.Empty())
	}
}

func TestPebbleV2A04SnapshotIsolation(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "k", "old")
	snapshot := f.db.NewSnapshot()
	defer snapshot.Close()
	put(t, f.db, "k", "new")
	value, closer, err := snapshot.Get([]byte("k"))
	if err != nil {
		t.Fatal(err)
	}
	defer closer.Close()
	if string(value) != "old" {
		t.Fatalf("snapshot value = %q", value)
	}
}

func TestPebbleV2A05IteratorBounds(t *testing.T) {
	f := newDBFixture(t)
	for _, key := range []string{"a", "b", "c", "d"} {
		put(t, f.db, key, key)
	}
	got := keysOf(t, f.db, &pebble.IterOptions{LowerBound: []byte("b"), UpperBound: []byte("d")})
	if fmt.Sprint(got) != "[b c]" {
		t.Fatalf("bounded keys = %v", got)
	}
}

func TestPebbleV2A06RangeDeletion(t *testing.T) {
	f := newDBFixture(t)
	for _, key := range []string{"a", "b", "c", "d"} {
		put(t, f.db, key, key)
	}
	if err := f.db.DeleteRange([]byte("b"), []byte("d"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	if got := keysOf(t, f.db, nil); fmt.Sprint(got) != "[a d]" {
		t.Fatalf("keys after range delete = %v", got)
	}
}

func TestPebbleV2A07MergeOperand(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "m", "left")
	if err := f.db.Merge([]byte("m"), []byte("right"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	if got := valueOf(t, f.db, "m"); got != "leftright" {
		t.Fatalf("merged value = %q", got)
	}
}

func TestPebbleV2A08RejectsNonPositiveBuffer(t *testing.T) {
	f := newDBFixture(t)
	_, err := f.db.SubscribeCommits(context.Background(), pebble.CommitFeedOptions{Buffer: 0})
	if !errors.Is(err, pebble.ErrCommitFeedUnavailable) {
		t.Fatalf("zero-buffer error = %v", err)
	}
}

func TestPebbleV2A09RejectsInvertedBounds(t *testing.T) {
	f := newDBFixture(t)
	_, err := f.db.SubscribeCommits(context.Background(), pebble.CommitFeedOptions{
		LowerBound: []byte("z"), UpperBound: []byte("a"), Buffer: 1,
	})
	if !errors.Is(err, pebble.ErrCommitFeedUnavailable) {
		t.Fatalf("inverted-bounds error = %v", err)
	}
}

func TestPebbleV2A10PreservesCancelledContext(t *testing.T) {
	f := newDBFixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := f.db.SubscribeCommits(ctx, pebble.CommitFeedOptions{Buffer: 1})
	if !errors.Is(err, pebble.ErrCommitFeedUnavailable) || !errors.Is(err, context.Canceled) {
		t.Fatalf("cancelled subscription error = %v", err)
	}
}

func TestPebbleV2A11ExplicitCloseIsCleanAndIdempotent(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 1})
	if err := feed.Close(); err != nil {
		t.Fatal(err)
	}
	if err := feed.Close(); err != nil {
		t.Fatal(err)
	}
	requireClosed(t, feed)
	if feed.Err() != nil {
		t.Fatalf("explicit close error = %v", feed.Err())
	}
}

func TestPebbleV2A12ProjectsAndOwnsPointSet(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	key, value := []byte("key"), []byte("value")
	if err := f.db.Set(key, value, pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	key[0], value[0] = 'X', 'Y'
	event := receive(t, feed)
	op := event.Operations[0]
	if op.Kind != pebble.CommitKindSet || string(op.Key) != "key" || string(op.Value) != "value" {
		t.Fatalf("set projection = %+v", op)
	}
}

func TestPebbleV2A13DecodesSizedDeleteValue(t *testing.T) {
	f := newDBFixture(t, func(options *pebble.Options) { options.FormatMajorVersion = pebble.FormatNewest })
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	if err := f.db.DeleteSized([]byte("sized"), 73, pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	op := event.Operations[0]
	if op.Kind != pebble.CommitKindDeleteSized || string(op.Key) != "sized" || op.ValueSize != 73 {
		t.Fatalf("sized-delete projection = %+v", op)
	}
}

func TestPebbleV2A14DecodesRangeKeySet(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	if err := f.db.RangeKeySet([]byte("a"), []byte("f"), []byte("@7"), []byte("rv"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	op := receive(t, feed).Operations[0]
	if op.Kind != pebble.CommitKindRangeKeySet || string(op.Key) != "a" || string(op.End) != "f" || string(op.Suffix) != "@7" || string(op.Value) != "rv" {
		t.Fatalf("range-key set projection = %+v", op)
	}
}

func TestPebbleV2A15CopiesSubscriptionBounds(t *testing.T) {
	f := newDBFixture(t)
	lower, upper := []byte("b"), []byte("d")
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{LowerBound: lower, UpperBound: upper, Buffer: 2})
	lower[0], upper[0] = 'x', 'y'
	put(t, f.db, "c", "inside")
	if op := receive(t, feed).Operations[0]; string(op.Key) != "c" {
		t.Fatalf("copied-bound event = %+v", op)
	}
}

func TestPebbleV2A16FeedIsLiveNotHistorical(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "before", "old")
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	requireNoEvent(t, feed)
	put(t, f.db, "after", "new")
	if op := receive(t, feed).Operations[0]; string(op.Key) != "after" {
		t.Fatalf("live boundary event = %+v", op)
	}
}

// Native composition controls: seven upstream workflows with multiple owners.

func TestPebbleV2I01BatchCommitIsAtomic(t *testing.T) {
	f := newDBFixture(t)
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Set([]byte("left"), []byte("L"), nil)
	_ = batch.Set([]byte("right"), []byte("R"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	if valueOf(t, f.db, "left")+valueOf(t, f.db, "right") != "LR" {
		t.Fatal("batch values were not jointly visible")
	}
}

func TestPebbleV2I02IndexedBatchOverlaysDatabase(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "base", "old")
	batch := f.db.NewIndexedBatch()
	defer batch.Close()
	_ = batch.Set([]byte("base"), []byte("overlay"), nil)
	value, closer, err := batch.Get([]byte("base"))
	if err != nil {
		t.Fatal(err)
	}
	defer closer.Close()
	if string(value) != "overlay" || valueOf(t, f.db, "base") != "old" {
		t.Fatalf("batch=%q db=%q", value, valueOf(t, f.db, "base"))
	}
}

func TestPebbleV2I03SnapshotAndLiveViewDiverge(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "version", "one")
	snapshot := f.db.NewSnapshot()
	defer snapshot.Close()
	put(t, f.db, "version", "two")
	old, closer, err := snapshot.Get([]byte("version"))
	if err != nil {
		t.Fatal(err)
	}
	defer closer.Close()
	if string(old) != "one" || valueOf(t, f.db, "version") != "two" {
		t.Fatalf("snapshot=%q live=%q", old, valueOf(t, f.db, "version"))
	}
}

func TestPebbleV2I04RangeDeleteShapesIteration(t *testing.T) {
	f := newDBFixture(t)
	for _, key := range []string{"a1", "b1", "b2", "c1"} {
		put(t, f.db, key, "v/"+key)
	}
	if err := f.db.DeleteRange([]byte("b"), []byte("c"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	if got := keysOf(t, f.db, nil); fmt.Sprint(got) != "[a1 c1]" {
		t.Fatalf("post-delete iteration = %v", got)
	}
}

func TestPebbleV2I05FlushPreservesLogicalReads(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "durable", "payload")
	if err := f.db.Flush(); err != nil {
		t.Fatal(err)
	}
	if valueOf(t, f.db, "durable") != "payload" || f.db.Metrics().Flush.Count == 0 {
		t.Fatalf("flush/read state = %+v", f.db.Metrics().Flush)
	}
}

func TestPebbleV2I06CheckpointFormsIndependentReadView(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "checkpointed", "v1")
	if err := f.db.Checkpoint("checkpoint", pebble.WithFlushedWAL()); err != nil {
		t.Fatal(err)
	}
	checkpoint, err := pebble.Open("checkpoint", &pebble.Options{FS: f.fs, ReadOnly: true})
	if err != nil {
		t.Fatal(err)
	}
	defer checkpoint.Close()
	put(t, f.db, "later", "v2")
	if valueOf(t, checkpoint, "checkpointed") != "v1" {
		t.Fatal("checkpoint lost committed value")
	}
	if _, closer, err := checkpoint.Get([]byte("later")); !errors.Is(err, pebble.ErrNotFound) {
		if closer != nil {
			closer.Close()
		}
		t.Fatalf("checkpoint observed later write: %v", err)
	}
}

func TestPebbleV2I07ConcurrentWritesIterateInComparerOrder(t *testing.T) {
	f := newDBFixture(t)
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	for i := 7; i >= 0; i-- {
		i := i
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- f.db.Set([]byte(fmt.Sprintf("k%02d", i)), []byte{byte(i)}, pebble.NoSync)
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	keys := keysOf(t, f.db, nil)
	if len(keys) != 8 || !sort.StringsAreSorted(keys) {
		t.Fatalf("concurrent keys = %v", keys)
	}
}

func TestPebbleV2I08PreservesBatchGroupingAndOperationOrder(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 4})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Set([]byte("a"), []byte("1"), nil)
	_ = batch.Merge([]byte("b"), []byte("2"), nil)
	_ = batch.Delete([]byte("c"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	want := []pebble.CommitKind{pebble.CommitKindSet, pebble.CommitKindMerge, pebble.CommitKindDelete}
	if fmt.Sprint(operationKinds(event)) != fmt.Sprint(want) {
		t.Fatalf("batch operation order = %v", operationKinds(event))
	}
}

func TestPebbleV2I09ReportsWholeBatchSequenceInterval(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 4})
	batch := f.db.NewBatch()
	defer batch.Close()
	for _, key := range []string{"x", "y", "z"} {
		_ = batch.Set([]byte(key), []byte(key), nil)
	}
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	if event.SequenceEnd-event.SequenceStart != 2 || len(event.Operations) != 3 {
		t.Fatalf("batch interval = [%d,%d] operations=%d", event.SequenceStart, event.SequenceEnd, len(event.Operations))
	}
}

func TestPebbleV2I10SeparatesIndividualMutationCommits(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 4})
	put(t, f.db, "first", "1")
	put(t, f.db, "second", "2")
	first, second := receive(t, feed), receive(t, feed)
	if len(first.Operations) != 1 || len(second.Operations) != 1 ||
		first.SequenceStart != first.SequenceEnd || second.SequenceStart != second.SequenceEnd ||
		first.SequenceEnd >= second.SequenceStart {
		t.Fatalf("individual intervals = %+v then %+v", first, second)
	}
}

func TestPebbleV2I11FiltersOperationsWithoutShrinkingInterval(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{
		LowerBound: []byte("b"), UpperBound: []byte("d"), Buffer: 4,
	})
	batch := f.db.NewBatch()
	defer batch.Close()
	for _, key := range []string{"a", "c", "e"} {
		_ = batch.Set([]byte(key), []byte("v"+key), nil)
	}
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	if len(event.Operations) != 1 || string(event.Operations[0].Key) != "c" || event.SequenceEnd-event.SequenceStart != 2 {
		t.Fatalf("filtered event = %+v", event)
	}
}

func TestPebbleV2I12RangeOverlapDeliversOriginalSpan(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{
		LowerBound: []byte("b"), UpperBound: []byte("d"), Buffer: 2,
	})
	if err := f.db.DeleteRange([]byte("a"), []byte("c"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	op := receive(t, feed).Operations[0]
	if op.Kind != pebble.CommitKindDeleteRange || string(op.Key) != "a" || string(op.End) != "c" {
		t.Fatalf("overlapping range = %+v", op)
	}
}

func TestPebbleV2I13NonOverlappingRangeLeavesSequenceGap(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{
		LowerBound: []byte("b"), UpperBound: []byte("d"), Buffer: 2,
	})
	if err := f.db.DeleteRange([]byte("e"), []byte("g"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	requireNoEvent(t, feed)
	if err := f.db.DeleteRange([]byte("c"), []byte("f"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	if op := receive(t, feed).Operations[0]; string(op.Key) != "c" || string(op.End) != "f" {
		t.Fatalf("post-gap range = %+v", op)
	}
}

func TestPebbleV2I14FeedsProjectDifferentSubsetsOfSameCommit(t *testing.T) {
	f := newDBFixture(t)
	left := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{LowerBound: []byte("a"), UpperBound: []byte("c"), Buffer: 2})
	right := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{LowerBound: []byte("c"), UpperBound: []byte("z"), Buffer: 2})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Set([]byte("b"), []byte("L"), nil)
	_ = batch.Set([]byte("x"), []byte("R"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	l, r := receive(t, left), receive(t, right)
	if string(l.Operations[0].Key) != "b" || string(r.Operations[0].Key) != "x" ||
		l.SequenceStart != r.SequenceStart || l.SequenceEnd != r.SequenceEnd {
		t.Fatalf("left=%+v right=%+v", l, r)
	}
}

func TestPebbleV2I15FeedsDoNotAliasEachOther(t *testing.T) {
	f := newDBFixture(t)
	first := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	second := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	put(t, f.db, "owned", "payload")
	one, two := receive(t, first), receive(t, second)
	one.Operations[0].Key[0] = 'X'
	one.Operations[0].Value[0] = 'Y'
	if string(two.Operations[0].Key) != "owned" || string(two.Operations[0].Value) != "payload" {
		t.Fatalf("cross-feed alias = %+v", two.Operations[0])
	}
}

func TestPebbleV2I16SubmittedBatchMemoryDoesNotAliasEvent(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	batch := f.db.NewBatch()
	defer batch.Close()
	key, value := []byte("batch-key"), []byte("batch-value")
	_ = batch.Set(key, value, nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	key[0], value[0] = 'X', 'Y'
	op := receive(t, feed).Operations[0]
	if string(op.Key) != "batch-key" || string(op.Value) != "batch-value" {
		t.Fatalf("submitted memory alias = %+v", op)
	}
}

func TestPebbleV2I17ReturnedEventMutationCannotChangeDatabase(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	put(t, f.db, "stable", "database")
	event := receive(t, feed)
	for i := range event.Operations[0].Value {
		event.Operations[0].Value[i] = 'x'
	}
	if got := valueOf(t, f.db, "stable"); got != "database" {
		t.Fatalf("database changed through event: %q", got)
	}
}

func TestPebbleV2I18MergeEventCarriesOperandNotResolvedValue(t *testing.T) {
	f := newDBFixture(t)
	put(t, f.db, "merge", "base/")
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	if err := f.db.Merge([]byte("merge"), []byte("delta"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	op := receive(t, feed).Operations[0]
	if op.Kind != pebble.CommitKindMerge || string(op.Value) != "delta" || valueOf(t, f.db, "merge") != "base/delta" {
		t.Fatalf("merge event=%+v resolved=%q", op, valueOf(t, f.db, "merge"))
	}
}

func TestPebbleV2I19DistinguishesDeleteKinds(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Delete([]byte("ordinary"), nil)
	_ = batch.SingleDelete([]byte("single"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	want := []pebble.CommitKind{pebble.CommitKindDelete, pebble.CommitKindSingleDelete}
	if fmt.Sprint(operationKinds(event)) != fmt.Sprint(want) {
		t.Fatalf("delete kinds = %v", operationKinds(event))
	}
}

func TestPebbleV2I20DistinguishesPointAndRangeKeyDeletion(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.DeleteRange([]byte("a"), []byte("d"), nil)
	_ = batch.RangeKeyDelete([]byte("m"), []byte("z"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	want := []pebble.CommitKind{pebble.CommitKindDeleteRange, pebble.CommitKindRangeKeyDelete}
	if fmt.Sprint(operationKinds(event)) != fmt.Sprint(want) || string(event.Operations[1].End) != "z" {
		t.Fatalf("range delete event = %+v", event)
	}
}

func TestPebbleV2I21ProjectsRangeKeyUnsetSuffix(t *testing.T) {
	f := newDBFixture(t)
	if err := f.db.RangeKeySet([]byte("a"), []byte("z"), []byte("@5"), []byte("seed"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	if err := f.db.RangeKeyUnset([]byte("c"), []byte("q"), []byte("@5"), pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	op := receive(t, feed).Operations[0]
	if op.Kind != pebble.CommitKindRangeKeyUnset || string(op.Key) != "c" || string(op.End) != "q" || string(op.Suffix) != "@5" {
		t.Fatalf("range-key unset = %+v", op)
	}
}

func TestPebbleV2I22OmitsLogDataFromLogicalProjection(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.LogData([]byte("wal-only"), nil)
	_ = batch.Set([]byte("logical"), []byte("visible"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	if len(event.Operations) != 1 || event.Operations[0].Kind != pebble.CommitKindSet || event.SequenceStart != event.SequenceEnd {
		t.Fatalf("log-data projection = %+v", event)
	}
}

func TestPebbleV2I23LaggingFeedDoesNotBlockSibling(t *testing.T) {
	f := newDBFixture(t)
	slow := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 1})
	fast := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 4})
	put(t, f.db, "one", "1")
	put(t, f.db, "two", "2")
	first, second := receive(t, fast), receive(t, fast)
	if string(first.Operations[0].Key) != "one" || string(second.Operations[0].Key) != "two" {
		t.Fatalf("fast feed events = %+v %+v", first, second)
	}
	if buffered := receive(t, slow); string(buffered.Operations[0].Key) != "one" {
		t.Fatalf("slow buffered event = %+v", buffered)
	}
	requireClosed(t, slow)
	if !errors.Is(slow.Err(), pebble.ErrCommitFeedLagged) {
		t.Fatalf("slow terminal error = %v", slow.Err())
	}
}

func TestPebbleV2I24CancellationDoesNotTerminateSibling(t *testing.T) {
	f := newDBFixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	cancelled := subscribe(t, f.db, ctx, pebble.CommitFeedOptions{Buffer: 2})
	sibling := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	cancel()
	requireClosed(t, cancelled)
	put(t, f.db, "survivor", "ok")
	if op := receive(t, sibling).Operations[0]; string(op.Key) != "survivor" || sibling.Err() != nil {
		t.Fatalf("sibling after cancellation = %+v err=%v", op, sibling.Err())
	}
}

func TestPebbleV2S01ConcurrentCommitsFollowVisibleSequenceOrder(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 24})
	var wg sync.WaitGroup
	errs := make(chan error, 12)
	for i := 0; i < 12; i++ {
		i := i
		wg.Add(1)
		go func() {
			defer wg.Done()
			key := fmt.Sprintf("concurrent-%02d", i)
			errs <- f.db.Set([]byte(key), []byte{byte(i)}, pebble.NoSync)
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	seen := make(map[string]bool)
	var last uint64
	for i := 0; i < 12; i++ {
		event := receive(t, feed)
		if i > 0 && event.SequenceStart <= last {
			t.Fatalf("sequence order regressed: %d then %d", last, event.SequenceStart)
		}
		last = event.SequenceEnd
		key := string(event.Operations[0].Key)
		seen[key] = true
		if _, closer, err := f.db.Get([]byte(key)); err != nil {
			t.Fatalf("published key %q not visible: %v", key, err)
		} else {
			closer.Close()
		}
	}
	if len(seen) != 12 {
		t.Fatalf("observed concurrent keys = %v", seen)
	}
}

func TestPebbleV2S02RejectedSyncWriteProducesNoEvent(t *testing.T) {
	f := newDBFixture(t, func(options *pebble.Options) { options.DisableWAL = true })
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 3})
	if err := f.db.Set([]byte("rejected"), []byte("x"), pebble.Sync); err == nil {
		t.Fatal("sync write unexpectedly succeeded with WAL disabled")
	}
	requireNoEvent(t, feed)
	put(t, f.db, "accepted", "y")
	if op := receive(t, feed).Operations[0]; string(op.Key) != "accepted" {
		t.Fatalf("post-rejection event = %+v", op)
	}
}

func TestPebbleV2S03ReceivedBatchIsAlreadyReadable(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 3})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Set([]byte("visible-a"), []byte("A"), nil)
	_ = batch.Set([]byte("visible-b"), []byte("B"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	event := receive(t, feed)
	if !bytes.Equal(event.Operations[0].Value, []byte(valueOf(t, f.db, "visible-a"))) ||
		!bytes.Equal(event.Operations[1].Value, []byte(valueOf(t, f.db, "visible-b"))) {
		t.Fatalf("event/read mismatch = %+v", event)
	}
}

func TestPebbleV2S04FilteredFeedRetainsGapFromGlobalOrder(t *testing.T) {
	f := newDBFixture(t)
	all := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 4})
	filtered := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{
		LowerBound: []byte("c"), UpperBound: []byte("d"), Buffer: 2,
	})
	put(t, f.db, "a", "outside")
	put(t, f.db, "c", "inside")
	globalFirst, globalSecond := receive(t, all), receive(t, all)
	retained := receive(t, filtered)
	if retained.SequenceStart != globalSecond.SequenceStart || retained.SequenceStart <= globalFirst.SequenceEnd ||
		string(retained.Operations[0].Key) != "c" {
		t.Fatalf("global=%+v/%+v filtered=%+v", globalFirst, globalSecond, retained)
	}
}

func TestPebbleV2S05DatabaseCloseDrainsThenReportsErrClosed(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 2})
	put(t, f.db, "buffered", "before-close")
	f.close(t)
	if event := receive(t, feed); string(event.Operations[0].Key) != "buffered" {
		t.Fatalf("buffered close event = %+v", event)
	}
	requireClosed(t, feed)
	if !errors.Is(feed.Err(), pebble.ErrClosed) {
		t.Fatalf("database-close terminal error = %v", feed.Err())
	}
}

func TestPebbleV2S06MaintenanceDoesNotReplayMutations(t *testing.T) {
	f := newDBFixture(t)
	feed := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{Buffer: 4})
	put(t, f.db, "seed", "one")
	_ = receive(t, feed)
	if err := f.db.Flush(); err != nil {
		t.Fatal(err)
	}
	if err := f.db.Compact(context.Background(), []byte("a"), []byte("z"), true); err != nil {
		t.Fatal(err)
	}
	if err := f.db.Checkpoint("maintenance-checkpoint"); err != nil {
		t.Fatal(err)
	}
	requireNoEvent(t, feed)
	put(t, f.db, "fresh", "two")
	if op := receive(t, feed).Operations[0]; string(op.Key) != "fresh" {
		t.Fatalf("maintenance replayed an old mutation: %+v", op)
	}
}

func TestPebbleV2S07CancellationCommitRaceHasCompleteOutcome(t *testing.T) {
	f := newDBFixture(t)
	ctx, cancel := context.WithCancel(context.Background())
	feed := subscribe(t, f.db, ctx, pebble.CommitFeedOptions{Buffer: 2})
	start := make(chan struct{})
	writeErr := make(chan error, 1)
	go func() {
		<-start
		writeErr <- f.db.Set([]byte("race"), []byte("complete"), pebble.NoSync)
	}()
	go func() {
		<-start
		cancel()
	}()
	close(start)
	if err := <-writeErr; err != nil {
		t.Fatal(err)
	}
	var events []pebble.CommitBatch
	deadline := time.After(2 * time.Second)
	for {
		select {
		case event, ok := <-feed.Events():
			if !ok {
				if len(events) > 1 || (len(events) == 1 && (len(events[0].Operations) != 1 || string(events[0].Operations[0].Key) != "race")) {
					t.Fatalf("partial race outcome = %+v", events)
				}
				if valueOf(t, f.db, "race") != "complete" || !errors.Is(feed.Err(), context.Canceled) {
					t.Fatalf("race state value=%q err=%v", valueOf(t, f.db, "race"), feed.Err())
				}
				return
			}
			events = append(events, event)
		case <-deadline:
			t.Fatal("cancellation race did not terminate")
		}
	}
}

func TestPebbleV2S08TwoViewsReconcileBatchRangeAndReads(t *testing.T) {
	f := newDBFixture(t)
	left := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{LowerBound: []byte("a"), UpperBound: []byte("m"), Buffer: 3})
	right := subscribe(t, f.db, context.Background(), pebble.CommitFeedOptions{LowerBound: []byte("m"), UpperBound: []byte("z"), Buffer: 3})
	batch := f.db.NewBatch()
	defer batch.Close()
	_ = batch.Set([]byte("b"), []byte("left"), nil)
	_ = batch.Set([]byte("n"), []byte("right"), nil)
	_ = batch.DeleteRange([]byte("c"), []byte("p"), nil)
	if err := batch.Commit(pebble.NoSync); err != nil {
		t.Fatal(err)
	}
	l, r := receive(t, left), receive(t, right)
	if len(l.Operations) != 2 || len(r.Operations) != 2 ||
		l.Operations[1].Kind != pebble.CommitKindDeleteRange || r.Operations[1].Kind != pebble.CommitKindDeleteRange ||
		l.SequenceStart != r.SequenceStart || valueOf(t, f.db, "b") != "left" {
		t.Fatalf("reconciled views left=%+v right=%+v", l, r)
	}
	if _, closer, err := f.db.Get([]byte("n")); !errors.Is(err, pebble.ErrNotFound) {
		if closer != nil {
			closer.Close()
		}
		t.Fatalf("range deletion did not shape live read: %v", err)
	}
}
