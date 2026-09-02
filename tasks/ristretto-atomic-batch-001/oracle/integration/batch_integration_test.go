package integration_test

import (
	"sort"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	r "github.com/dgraph-io/ristretto/v2"
)

func newCache(t *testing.T, mutate func(*r.Config[string, int])) *r.Cache[string, int] {
	t.Helper()
	cfg := &r.Config[string, int]{NumCounters: 1000, MaxCost: 100, BufferItems: 64, IgnoreInternalCost: true}
	if mutate != nil {
		mutate(cfg)
	}
	c, err := r.NewCache(cfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(c.Close)
	return c
}

func put(t *testing.T, c *r.Cache[string, int], key string, value int, cost int64) {
	t.Helper()
	if !c.Set(key, value, cost) {
		t.Fatalf("set %q dropped", key)
	}
	c.Wait()
}

func mustValue(t *testing.T, c *r.Cache[string, int], key string, want int) {
	t.Helper()
	got, ok := c.Get(key)
	if !ok || got != want {
		t.Fatalf("%q = %d,%v; want %d,true", key, got, ok, want)
	}
}

// Verifies: RAB-BATCH-003, RAB-CVI-001
// Seam: config interaction
// Depends-On: TestDeleteExistingRemovesValue, TestRequireAbsentAllowsInsertion
func TestMixedCommitAppearsThroughOrdinaryGets(t *testing.T) {
	c := newCache(t, nil)
	put(t, c, "old", 1, 3)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "old"}, {Operation: r.BatchSet, Key: "new", Value: 2, Cost: 4}})
	_, old := c.Get("old")
	v, ok := c.Get("new")
	if !res.Applied || old || !ok || v != 2 {
		t.Fatalf("result=%+v old=%v new=%d,%v", res, old, v, ok)
	}
}

// Verifies: RAB-BATCH-005, RAB-CVI-001
// Seam: lifecycle crossing
// Depends-On: TestRequirePresentAllowsReplacement
func TestAcceptedSetBeforeBatchIsDrainedFirst(t *testing.T) {
	c := newCache(t, nil)
	if !c.Set("a", 1, 1) {
		t.Fatal("set dropped")
	}
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1, Guard: r.BatchRequirePresent}})
	mustValue(t, c, "a", 2)
	if !res.Applied {
		t.Fatalf("unexpected result: %+v", res)
	}
}

// Verifies: RAB-BATCH-005, RAB-CVI-001
// Seam: config interaction
// Depends-On: TestRepeatedSetUsesLastValue
func TestOrdinarySetAfterBatchUsesCommittedState(t *testing.T) {
	c := newCache(t, nil)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}})
	if !res.Applied {
		t.Fatalf("result=%+v", res)
	}
	if !c.Set("a", 3, 1) {
		t.Fatal("update dropped")
	}
	c.Wait()
	mustValue(t, c, "a", 3)
}

// Verifies: RAB-SNAP-001, RAB-CVI-002
// Seam: config interaction
// Depends-On: TestGetManyPreservesInputOrder, TestRepeatedSetUsesLastValue
func TestSnapshotMatchesCommittedMultiKeyState(t *testing.T) {
	c := newCache(t, nil)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}, {Operation: r.BatchSet, Key: "b", Value: 2, Cost: 1}})
	got := c.GetMany([]string{"a", "b", "c"})
	if !got[0].Found || got[0].Value != 1 || !got[1].Found || got[1].Value != 2 || got[2].Found {
		t.Fatalf("snapshot=%+v", got)
	}
}

// Verifies: RAB-BATCH-003, RAB-CVI-003
// Seam: config interaction
// Depends-On: TestDeleteExistingRemovesValue, TestRepeatedSetUsesLastValue
func TestIterationMatchesBatchFinalState(t *testing.T) {
	c := newCache(t, nil)
	put(t, c, "old", 9, 1)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "old"}, {Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}, {Operation: r.BatchSet, Key: "b", Value: 2, Cost: 1}})
	var values []int
	c.IterValues(func(v int) bool { values = append(values, v); return false })
	sort.Ints(values)
	if len(values) != 2 || values[0] != 1 || values[1] != 2 {
		t.Fatalf("values=%v", values)
	}
}

// Verifies: RAB-CAP-002, RAB-CVI-004
// Seam: config interaction
// Depends-On: TestReplacementUsesNetCostDelta, TestDeleteFreesCapacityForLaterItem
func TestRemainingCostTracksMixedBatch(t *testing.T) {
	c := newCache(t, nil)
	put(t, c, "a", 1, 10)
	put(t, c, "b", 2, 20)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}, {Operation: r.BatchSet, Key: "b", Value: 3, Cost: 25}, {Operation: r.BatchSet, Key: "c", Value: 4, Cost: 15}})
	if c.RemainingCost() != 60 {
		t.Fatalf("remaining=%d", c.RemainingCost())
	}
}

// Verifies: RAB-TTL-001, RAB-CVI-005
// Seam: config interaction
// Depends-On: TestPositiveTTLSetsExpiringEntry, TestGetManyReportsRemainingTTL
func TestTTLViewsAgreeAfterCommit(t *testing.T) {
	c := newCache(t, nil)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1, TTL: 2 * time.Second}})
	ttl, ok := c.GetTTL("a")
	many := c.GetMany([]string{"a"})
	if !ok || !many[0].Found || ttl <= 0 || many[0].RemainingTTL <= 0 || ttl-many[0].RemainingTTL > 100*time.Millisecond {
		t.Fatalf("ttl=%v snapshot=%+v", ttl, many)
	}
}

// Verifies: RAB-CALLBACK-001, RAB-CVI-006
// Seam: state consistency
// Depends-On: TestRequirePresentAllowsReplacement
func TestReplacementCallsOnExitOnce(t *testing.T) {
	var mu sync.Mutex
	var exited []int
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.OnExit = func(v int) { mu.Lock(); exited = append(exited, v); mu.Unlock() }
	})
	put(t, c, "a", 1, 1)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}})
	mu.Lock()
	defer mu.Unlock()
	if len(exited) != 1 || exited[0] != 1 {
		t.Fatalf("exited=%v", exited)
	}
}

// Verifies: RAB-CALLBACK-001, RAB-CVI-006
// Seam: state consistency
// Depends-On: TestDeleteExistingRemovesValue
func TestDeleteCallsOnExitOnce(t *testing.T) {
	var exited atomic.Int64
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.OnExit = func(v int) {
			if v == 7 {
				exited.Add(1)
			}
		}
	})
	put(t, c, "a", 7, 1)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}})
	if exited.Load() != 1 {
		t.Fatalf("exit count=%d", exited.Load())
	}
}

// Verifies: RAB-CALLBACK-002, RAB-BATCH-004
// Seam: config interaction
// Depends-On: TestValidationFailureRollsBackEarlierItems
func TestGuardFailureProducesNoBatchCallbacks(t *testing.T) {
	var exits atomic.Int64
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.OnExit = func(int) { exits.Add(1) } })
	put(t, c, "a", 1, 1)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}, {Operation: r.BatchDelete, Key: "missing", Guard: r.BatchRequirePresent}})
	value, found := c.Get("a")
	if res.Failure != r.BatchConditionFailed || res.FailedIndex != 1 || exits.Load() != 0 || !found || value != 1 {
		t.Fatalf("result=%+v exit count=%d value=%d,%v", res, exits.Load(), value, found)
	}
}

// Verifies: RAB-CALLBACK-002, RAB-CAP-001
// Seam: config interaction
// Depends-On: TestCapacityOverflowRejectsWholeBatch
func TestCapacityFailureProducesNoCallbacks(t *testing.T) {
	var exits, rejects atomic.Int64
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.MaxCost = 5
		cfg.OnExit = func(int) { exits.Add(1) }
		cfg.OnReject = func(*r.Item[int]) { rejects.Add(1) }
	})
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 6}})
	if res.Failure != r.BatchCapacityExceeded || exits.Load() != 0 || rejects.Load() != 0 {
		t.Fatalf("result=%+v exits=%d rejects=%d", res, exits.Load(), rejects.Load())
	}
}

// Verifies: RAB-ORDER-002, RAB-CALLBACK-001
// Seam: config interaction
// Depends-On: TestRepeatedSetUsesLastValue
func TestRepeatedReplacementExitsOnlyOriginalValue(t *testing.T) {
	var exited []int
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.OnExit = func(v int) { exited = append(exited, v) } })
	put(t, c, "a", 1, 1)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}, {Operation: r.BatchSet, Key: "a", Value: 3, Cost: 1}})
	if len(exited) != 1 || exited[0] != 1 {
		t.Fatalf("exited=%v", exited)
	}
}

// Verifies: RAB-ORDER-002, RAB-CALLBACK-001
// Seam: config interaction
// Depends-On: TestSetThenDeleteLeavesKeyAbsent
func TestNewThenDeletedKeyProducesNoExit(t *testing.T) {
	var exits atomic.Int64
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.OnExit = func(int) { exits.Add(1) } })
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}, {Operation: r.BatchDelete, Key: "a"}})
	_, found := c.Get("a")
	if !res.Applied || res.Effects != 1 || exits.Load() != 0 || found {
		t.Fatalf("result=%+v exit count=%d found=%v", res, exits.Load(), found)
	}
}

// Verifies: RAB-ORDER-002, RAB-CALLBACK-001
// Seam: config interaction
// Depends-On: TestDeleteThenSetObservesVirtualAbsence
func TestDeleteThenSetExitsOriginalOnce(t *testing.T) {
	var exited []int
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.OnExit = func(v int) { exited = append(exited, v) } })
	put(t, c, "a", 1, 1)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}, {Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}})
	if len(exited) != 1 || exited[0] != 1 {
		t.Fatalf("exited=%v", exited)
	}
}

// Verifies: RAB-METRIC-001, RAB-CVI-007
// Seam: config interaction
// Depends-On: TestRequireAbsentAllowsInsertion
func TestMetricsCountCommittedNewKeys(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.Metrics = true })
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}, {Operation: r.BatchSet, Key: "b", Value: 2, Cost: 1}})
	if c.Metrics.KeysAdded() != 2 {
		t.Fatalf("keys added=%d", c.Metrics.KeysAdded())
	}
}

// Verifies: RAB-METRIC-001, RAB-CVI-007
// Seam: config interaction
// Depends-On: TestRequirePresentAllowsReplacement
func TestMetricsCountCommittedUpdates(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.Metrics = true })
	put(t, c, "a", 1, 1)
	before := c.Metrics.KeysUpdated()
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}})
	if c.Metrics.KeysUpdated() != before+1 {
		t.Fatalf("before=%d after=%d", before, c.Metrics.KeysUpdated())
	}
}

// Verifies: RAB-METRIC-002, RAB-SNAP-001
// Seam: config interaction
// Depends-On: TestGetManyPreservesInputOrder
func TestSnapshotContributesHitAndMissMetrics(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.Metrics = true })
	put(t, c, "a", 1, 1)
	h, m := c.Metrics.Hits(), c.Metrics.Misses()
	c.GetMany([]string{"a", "a", "x"})
	if c.Metrics.Hits() != h+2 || c.Metrics.Misses() != m+1 {
		t.Fatalf("hits=%d misses=%d", c.Metrics.Hits()-h, c.Metrics.Misses()-m)
	}
}

// Verifies: RAB-METRIC-001, RAB-BATCH-004
// Seam: config interaction
// Depends-On: TestCapacityOverflowRejectsWholeBatch
func TestRejectedBatchDoesNotCountWrites(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.Metrics = true; cfg.MaxCost = 3 })
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 4}})
	if res.Failure != r.BatchCapacityExceeded || c.Metrics.KeysAdded() != 0 || c.Metrics.KeysUpdated() != 0 {
		t.Fatalf("result=%+v added=%d updated=%d", res, c.Metrics.KeysAdded(), c.Metrics.KeysUpdated())
	}
}

// Verifies: RAB-TTL-002, RAB-CVI-005
// Seam: config interaction
// Depends-On: TestPositiveTTLSetsExpiringEntry, TestGetManyReportsRemainingTTL
func TestExpiredValueIsMissingFromBothReadViews(t *testing.T) {
	c := newCache(t, nil)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1, TTL: 20 * time.Millisecond}})
	if !res.Applied {
		t.Fatalf("result=%+v", res)
	}
	time.Sleep(35 * time.Millisecond)
	_, one := c.Get("a")
	many := c.GetMany([]string{"a"})
	if one || many[0].Found {
		t.Fatalf("get=%v snapshot=%+v", one, many)
	}
}

// Verifies: RAB-TTL-002, RAB-GUARD-001
// Seam: lifecycle crossing
// Depends-On: TestRequireAbsentAllowsInsertion, TestPositiveTTLSetsExpiringEntry
func TestExpiredKeySatisfiesAbsentGuard(t *testing.T) {
	c := newCache(t, nil)
	c.SetWithTTL("a", 1, 1, 15*time.Millisecond)
	c.Wait()
	time.Sleep(30 * time.Millisecond)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1, Guard: r.BatchRequireAbsent}})
	mustValue(t, c, "a", 2)
	if !res.Applied {
		t.Fatalf("result=%+v", res)
	}
}

// Verifies: RAB-TTL-002, RAB-GUARD-002
// Seam: lifecycle crossing
// Depends-On: TestRequirePresentRejectsMissingKey, TestPositiveTTLSetsExpiringEntry
func TestExpiredKeyFailsPresentGuardWithoutReplacement(t *testing.T) {
	c := newCache(t, nil)
	c.SetWithTTL("a", 1, 1, 15*time.Millisecond)
	c.Wait()
	time.Sleep(30 * time.Millisecond)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1, Guard: r.BatchRequirePresent}})
	_, ok := c.Get("a")
	if res.Failure != r.BatchConditionFailed || ok {
		t.Fatalf("result=%+v found=%v", res, ok)
	}
}

// Verifies: RAB-SNAP-001, RAB-CVI-002
// Seam: config interaction
// Depends-On: TestGetManyPreservesInputOrder
func TestZeroValueRemainsDistinguishableFromMissing(t *testing.T) {
	c := newCache(t, nil)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "zero", Value: 0, Cost: 1}})
	got := c.GetMany([]string{"zero", "missing"})
	if !got[0].Found || got[0].Value != 0 || got[1].Found {
		t.Fatalf("snapshot=%+v", got)
	}
}

// Verifies: RAB-HASH-001, RAB-CVI-001
// Seam: config interaction
// Depends-On: TestHashConflictRejectsBatch
func TestCustomHashDistinctPrimariesCommitNormally(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.KeyToHash = func(k string) (uint64, uint64) { return uint64(k[0]), uint64(len(k)) }
	})
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}, {Operation: r.BatchSet, Key: "b", Value: 2, Cost: 1}})
	if !res.Applied {
		t.Fatalf("result=%+v", res)
	}
	mustValue(t, c, "a", 1)
	mustValue(t, c, "b", 2)
}

// Verifies: RAB-HASH-001, RAB-BATCH-004
// Seam: config interaction
// Depends-On: TestHashConflictRejectsBatch, TestValidationFailureRollsBackEarlierItems
func TestHashConflictInLaterItemRollsBackEarlierItem(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.KeyToHash = func(k string) (uint64, uint64) {
			if k == "x" {
				return 9, 1
			}
			return 9, 2
		}
	})
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "x", Value: 1, Cost: 1}, {Operation: r.BatchSet, Key: "y", Value: 2, Cost: 1}})
	_, ok := c.Get("x")
	if res.Failure != r.BatchHashConflict || ok {
		t.Fatalf("result=%+v x=%v", res, ok)
	}
}

// Verifies: RAB-ATOMIC-001, RAB-SNAP-001
// Seam: config interaction
// Depends-On: TestGetManyPreservesInputOrder, TestDeleteExistingRemovesValue
func TestConcurrentSnapshotsNeverSeePartialCommit(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.MaxCost = 500 })
	for i := 0; i < 20; i++ {
		put(t, c, "old"+string(rune('A'+i)), i, 1)
	}
	keys := make([]string, 0, 40)
	ops := make([]r.BatchItem[string, int], 0, 40)
	for i := 0; i < 20; i++ {
		k := "old" + string(rune('A'+i))
		keys = append(keys, k)
		ops = append(ops, r.BatchItem[string, int]{Operation: r.BatchDelete, Key: k})
	}
	for i := 0; i < 20; i++ {
		k := "new" + string(rune('A'+i))
		keys = append(keys, k)
		ops = append(ops, r.BatchItem[string, int]{Operation: r.BatchSet, Key: k, Value: i, Cost: 1})
	}
	done := make(chan struct{})
	errs := make(chan int, 1)
	go func() {
		defer close(done)
		for j := 0; j < 100; j++ {
			snap := c.GetMany(keys)
			found := 0
			for _, v := range snap {
				if v.Found {
					found++
				}
			}
			if found != 20 {
				errs <- found
				return
			}
		}
	}()
	res := c.ApplyBatch(ops)
	<-done
	select {
	case n := <-errs:
		t.Fatalf("partial snapshot with %d found", n)
	default:
	}
	if !res.Applied {
		t.Fatalf("result=%+v", res)
	}
}

// Verifies: RAB-ATOMIC-002
// Seam: config interaction
// Depends-On: TestRequireAbsentAllowsInsertion
func TestConcurrentDisjointBatchesAllCommit(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.MaxCost = 500 })
	var wg sync.WaitGroup
	failures := make(chan r.BatchResult[string], 16)
	for i := 0; i < 16; i++ {
		i := i
		wg.Add(1)
		go func() {
			defer wg.Done()
			key := string(rune('a' + i))
			res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: key, Value: i, Cost: 1, Guard: r.BatchRequireAbsent}})
			if !res.Applied {
				failures <- res
			}
		}()
	}
	wg.Wait()
	close(failures)
	for f := range failures {
		t.Fatalf("failure=%+v", f)
	}
	for i := 0; i < 16; i++ {
		mustValue(t, c, string(rune('a'+i)), i)
	}
}

// Verifies: RAB-ATOMIC-001, RAB-BATCH-005
// Seam: config interaction
// Depends-On: TestDynamicCostIsEvaluated, TestRepeatedSetUsesLastValue
func TestOrdinarySetWaitsForOpenBatchBoundary(t *testing.T) {
	entered := make(chan struct{})
	release := make(chan struct{})
	released := false
	defer func() {
		if !released {
			close(release)
		}
	}()
	var once sync.Once
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.Cost = func(v int) int64 {
			if v == 10 {
				once.Do(func() { close(entered) })
				<-release
			}
			return 1
		}
	})
	batchDone := make(chan struct{})
	go func() {
		c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "batch", Value: 10}})
		close(batchDone)
	}()
	select {
	case <-entered:
	case <-time.After(250 * time.Millisecond):
		t.Fatal("batch did not enter dynamic cost evaluation")
	}
	setDone := make(chan struct{})
	go func() { c.Set("ordinary", 20, 1); close(setDone) }()
	select {
	case <-setDone:
		t.Fatal("ordinary Set crossed open batch boundary")
	case <-time.After(20 * time.Millisecond):
	}
	close(release)
	released = true
	<-batchDone
	<-setDone
	c.Wait()
	mustValue(t, c, "batch", 10)
	mustValue(t, c, "ordinary", 20)
}

// Verifies: RAB-UPDATE-001, RAB-ORDER-001
// Seam: config interaction
// Depends-On: TestShouldUpdateAllowsSequentialReplacement, TestRepeatedSetUsesLastValue
func TestShouldUpdateSeesPriorVirtualValue(t *testing.T) {
	var pairs [][2]int
	c := newCache(t, func(cfg *r.Config[string, int]) {
		cfg.ShouldUpdate = func(cur, prev int) bool { pairs = append(pairs, [2]int{cur, prev}); return cur > prev }
	})
	put(t, c, "a", 1, 1)
	pairs = nil
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}, {Operation: r.BatchSet, Key: "a", Value: 3, Cost: 1}})
	if !res.Applied || len(pairs) != 2 || pairs[0] != [2]int{2, 1} || pairs[1] != [2]int{3, 2} {
		t.Fatalf("result=%+v pairs=%v", res, pairs)
	}
}

// Verifies: RAB-UPDATE-001, RAB-BATCH-004
// Seam: config interaction
// Depends-On: TestShouldUpdateRejectsWholeBatch, TestRepeatedSetUsesLastValue
func TestVirtualUpdateRejectionRestoresOriginal(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.ShouldUpdate = func(cur, prev int) bool { return cur > prev } })
	put(t, c, "a", 1, 1)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 3, Cost: 1}, {Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}})
	mustValue(t, c, "a", 1)
	if res.Failure != r.BatchUpdateRejected {
		t.Fatalf("result=%+v", res)
	}
}

// Verifies: RAB-CAP-002, RAB-ORDER-001
// Seam: config interaction
// Depends-On: TestDeleteFreesCapacityForLaterItem, TestReplacementUsesNetCostDelta
func TestCapacityUsesAllFinalPerKeyEffects(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.MaxCost = 30 })
	put(t, c, "a", 1, 10)
	put(t, c, "b", 2, 10)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}, {Operation: r.BatchSet, Key: "b", Value: 3, Cost: 20}, {Operation: r.BatchSet, Key: "c", Value: 4, Cost: 10}})
	if !res.Applied || c.RemainingCost() != 0 {
		t.Fatalf("result=%+v remaining=%d", res, c.RemainingCost())
	}
}

// Verifies: RAB-RESULT-002, RAB-ORDER-002
// Seam: config interaction
// Depends-On: TestRepeatedSetUsesLastValue
func TestEffectsCountsDistinctTouchedHashes(t *testing.T) {
	c := newCache(t, nil)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}, {Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}, {Operation: r.BatchDelete, Key: "b"}})
	if !res.Applied || res.Effects != 2 {
		t.Fatalf("result=%+v", res)
	}
}

// Verifies: RAB-RESULT-001, RAB-RESULT-002
// Seam: config interaction
// Depends-On: TestEmptyBatchSucceeds
func TestSuccessfulResultClearsFailureFields(t *testing.T) {
	c := newCache(t, nil)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}})
	if !res.Applied || res.FailedIndex != -1 || res.FailedKey != "" || res.Failure != r.BatchSucceeded || res.Effects != 1 {
		t.Fatalf("result=%+v", res)
	}
}

// Verifies: RAB-SNAP-003
// Seam: lifecycle crossing
// Depends-On: TestGetManyPreservesInputOrder
func TestClosedSnapshotPreservesRequestedShape(t *testing.T) {
	c := newCache(t, nil)
	c.Close()
	got := c.GetMany([]string{"a", "b"})
	if len(got) != 2 || got[0].Key != "a" || got[1].Key != "b" || got[0].Found || got[1].Found {
		t.Fatalf("snapshot=%+v", got)
	}
}

// Verifies: RAB-SNAP-003
// Seam: lifecycle crossing
// Depends-On: TestGetManyPreservesInputOrder
func TestNilSnapshotPreservesRequestedShape(t *testing.T) {
	var c *r.Cache[string, int]
	got := c.GetMany([]string{"a", "a"})
	if len(got) != 2 || got[0].Key != "a" || got[1].Key != "a" || got[0].Found || got[1].Found {
		t.Fatalf("snapshot=%+v", got)
	}
}

// Verifies: RAB-API-001, RAB-CVI-001
// Seam: config interaction
// Depends-On: TestRequireAbsentAllowsInsertion
func TestBatchSupportsNonStringKeyType(t *testing.T) {
	c, err := r.NewCache(&r.Config[int, string]{NumCounters: 100, MaxCost: 10, BufferItems: 64, IgnoreInternalCost: true})
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	res := c.ApplyBatch([]r.BatchItem[int, string]{{Operation: r.BatchSet, Key: 7, Value: "seven", Cost: 1}})
	got := c.GetMany([]int{7})
	if !res.Applied || !got[0].Found || got[0].Value != "seven" {
		t.Fatalf("result=%+v snapshot=%+v", res, got)
	}
}

// Verifies: RAB-ATOMIC-001, RAB-CAP-001
// Seam: config interaction
// Depends-On: TestBatchMayFillCapacityExactly, TestRequireAbsentAllowsInsertion
func TestLargeBatchCommitsAsSingleCapacityDecision(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.MaxCost = 200 })
	ops := make([]r.BatchItem[string, int], 100)
	keys := make([]string, 100)
	for i := range ops {
		keys[i] = time.Duration(i).String()
		ops[i] = r.BatchItem[string, int]{Operation: r.BatchSet, Key: keys[i], Value: i, Cost: 2}
	}
	res := c.ApplyBatch(ops)
	got := c.GetMany(keys)
	found := 0
	for _, v := range got {
		if v.Found {
			found++
		}
	}
	if !res.Applied || res.Effects != 100 || found != 100 || c.RemainingCost() != 0 {
		t.Fatalf("result=%+v found=%d remaining=%d", res, found, c.RemainingCost())
	}
}

// Verifies: RAB-BATCH-004, RAB-CVI-004
// Seam: config interaction
// Depends-On: TestCapacityOverflowRejectsWholeBatch, TestReplacementUsesNetCostDelta
func TestRejectedReplacementLeavesCapacityAndValueUnchanged(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.MaxCost = 10 })
	put(t, c, "a", 1, 4)
	before := c.RemainingCost()
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 11}})
	mustValue(t, c, "a", 1)
	if res.Failure != r.BatchCapacityExceeded || c.RemainingCost() != before {
		t.Fatalf("result=%+v before=%d after=%d", res, before, c.RemainingCost())
	}
}

// Verifies: RAB-GUARD-001, RAB-ORDER-001, RAB-BATCH-004
// Seam: config interaction
// Depends-On: TestDeleteThenSetObservesVirtualAbsence, TestValidationFailureRollsBackEarlierItems
func TestLaterGuardFailureRestoresMultipleOriginalKeys(t *testing.T) {
	c := newCache(t, nil)
	put(t, c, "a", 1, 1)
	put(t, c, "b", 2, 1)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}, {Operation: r.BatchSet, Key: "b", Value: 3, Cost: 1}, {Operation: r.BatchSet, Key: "b", Value: 4, Cost: 1, Guard: r.BatchRequireAbsent}})
	mustValue(t, c, "a", 1)
	mustValue(t, c, "b", 2)
	if res.Failure != r.BatchConditionFailed || res.FailedIndex != 2 {
		t.Fatalf("result=%+v", res)
	}
}

// Verifies: RAB-TTL-001, RAB-ORDER-001
// Seam: config interaction
// Depends-On: TestPositiveTTLSetsExpiringEntry, TestRepeatedSetUsesLastValue
func TestLastRepeatedSetDeterminesTTL(t *testing.T) {
	c := newCache(t, nil)
	res := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1, TTL: time.Second}, {Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}})
	ttl, ok := c.GetTTL("a")
	if !res.Applied || !ok || ttl != 0 {
		t.Fatalf("result=%+v ttl=%v,%v", res, ttl, ok)
	}
}

// Verifies: RAB-SNAP-001, RAB-METRIC-002
// Seam: config interaction
// Depends-On: TestGetManyPreservesDuplicatePositions, TestGetManyPreservesInputOrder
func TestRepeatedSnapshotKeysCountIndependently(t *testing.T) {
	c := newCache(t, func(cfg *r.Config[string, int]) { cfg.Metrics = true })
	put(t, c, "a", 1, 1)
	h := c.Metrics.Hits()
	got := c.GetMany([]string{"a", "a", "a"})
	if len(got) != 3 || c.Metrics.Hits() != h+3 {
		t.Fatalf("snapshot=%+v hit delta=%d", got, c.Metrics.Hits()-h)
	}
}
