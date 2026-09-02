package atomic_test

import (
	"testing"
	"time"

	r "github.com/dgraph-io/ristretto/v2"
)

func cache(t *testing.T) *r.Cache[string, int] {
	t.Helper()
	c, err := r.NewCache(&r.Config[string, int]{
		NumCounters: 100, MaxCost: 20, BufferItems: 64, IgnoreInternalCost: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(c.Close)
	return c
}

func seed(t *testing.T, c *r.Cache[string, int], key string, value int, cost int64) {
	t.Helper()
	if !c.Set(key, value, cost) {
		t.Fatalf("Set(%q) was dropped", key)
	}
	c.Wait()
}

// Verifies: RAB-BATCH-001
func TestEmptyBatchSucceeds(t *testing.T) {
	got := cache(t).ApplyBatch(nil)
	if !got.Applied || got.FailedIndex != -1 || got.Failure != r.BatchSucceeded || got.Effects != 0 {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-ERR-001
func TestNilCacheRejectsNonEmptyBatch(t *testing.T) {
	var c *r.Cache[string, int]
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}})
	if got.Applied || got.Failure != r.BatchCacheClosed || got.FailedIndex != 0 {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-ERR-001
func TestClosedCacheRejectsBatch(t *testing.T) {
	c := cache(t)
	c.Close()
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}})
	if got.Applied || got.Failure != r.BatchCacheClosed {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-ERR-002
func TestInvalidOperationIsReported(t *testing.T) {
	got := cache(t).ApplyBatch([]r.BatchItem[string, int]{{Operation: 99, Key: "bad"}})
	if got.Failure != r.BatchInvalidOperation || got.FailedIndex != 0 || got.FailedKey != "bad" {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-ERR-003
func TestInvalidGuardIsReported(t *testing.T) {
	got := cache(t).ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "bad", Guard: 99}})
	if got.Failure != r.BatchInvalidGuard || got.FailedIndex != 0 {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-ERR-004
func TestNegativeTTLIsRejected(t *testing.T) {
	got := cache(t).ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", TTL: -time.Nanosecond}})
	if got.Failure != r.BatchInvalidTTL {
		t.Fatalf("unexpected failure: %v", got.Failure)
	}
}

// Verifies: RAB-ERR-005
func TestNegativeCostIsRejected(t *testing.T) {
	got := cache(t).ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Cost: -1}})
	if got.Failure != r.BatchInvalidCost {
		t.Fatalf("unexpected failure: %v", got.Failure)
	}
}

// Verifies: RAB-GUARD-001
func TestRequireAbsentAllowsInsertion(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 7, Cost: 1, Guard: r.BatchRequireAbsent}})
	v, ok := c.Get("a")
	if !got.Applied || !ok || v != 7 {
		t.Fatalf("result=%+v value=%v,%v", got, v, ok)
	}
}

// Verifies: RAB-GUARD-001, RAB-BATCH-004
func TestRequireAbsentRejectsExistingKey(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1, Guard: r.BatchRequireAbsent}})
	v, _ := c.Get("a")
	if got.Failure != r.BatchConditionFailed || v != 1 {
		t.Fatalf("result=%+v value=%d", got, v)
	}
}

// Verifies: RAB-GUARD-002
func TestRequirePresentAllowsReplacement(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1, Guard: r.BatchRequirePresent}})
	v, _ := c.Get("a")
	if !got.Applied || v != 2 {
		t.Fatalf("result=%+v value=%d", got, v)
	}
}

// Verifies: RAB-GUARD-002
func TestRequirePresentRejectsMissingKey(t *testing.T) {
	got := cache(t).ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a", Guard: r.BatchRequirePresent}})
	if got.Failure != r.BatchConditionFailed {
		t.Fatalf("unexpected failure: %v", got.Failure)
	}
}

// Verifies: RAB-BATCH-002
func TestDeleteMissingWithAnyIsSuccessfulNoOp(t *testing.T) {
	got := cache(t).ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}})
	if !got.Applied || got.Effects != 1 {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-BATCH-002
func TestDeleteExistingRemovesValue(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}})
	_, ok := c.Get("a")
	if !got.Applied || ok {
		t.Fatalf("result=%+v found=%v", got, ok)
	}
}

// Verifies: RAB-ORDER-001, RAB-BATCH-003
func TestRepeatedSetUsesLastValue(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{
		{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1},
		{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1, Guard: r.BatchRequirePresent},
	})
	v, _ := c.Get("a")
	if !got.Applied || got.Effects != 1 || v != 2 {
		t.Fatalf("result=%+v value=%d", got, v)
	}
}

// Verifies: RAB-ORDER-001
func TestSetThenDeleteLeavesKeyAbsent(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{
		{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1},
		{Operation: r.BatchDelete, Key: "a", Guard: r.BatchRequirePresent},
	})
	_, ok := c.Get("a")
	if !got.Applied || ok {
		t.Fatalf("result=%+v found=%v", got, ok)
	}
}

// Verifies: RAB-ORDER-001, RAB-GUARD-001
func TestDeleteThenSetObservesVirtualAbsence(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{
		{Operation: r.BatchDelete, Key: "a", Guard: r.BatchRequirePresent},
		{Operation: r.BatchSet, Key: "a", Value: 3, Cost: 1, Guard: r.BatchRequireAbsent},
	})
	v, _ := c.Get("a")
	if !got.Applied || v != 3 {
		t.Fatalf("result=%+v value=%d", got, v)
	}
}

// Verifies: RAB-RESULT-001
func TestFailureIdentifiesFirstInvalidItem(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{
		{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1},
		{Operation: r.BatchSet, Key: "b", TTL: -1},
		{Operation: 99, Key: "c"},
	})
	if got.FailedIndex != 1 || got.FailedKey != "b" || got.Failure != r.BatchInvalidTTL {
		t.Fatalf("unexpected result: %+v", got)
	}
}

// Verifies: RAB-BATCH-004
func TestValidationFailureRollsBackEarlierItems(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{
		{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1},
		{Operation: r.BatchDelete, Key: "missing", Guard: r.BatchRequirePresent},
	})
	_, ok := c.Get("a")
	if got.Applied || got.Failure != r.BatchConditionFailed || got.FailedIndex != 1 || ok {
		t.Fatalf("result=%+v found=%v", got, ok)
	}
}

// Verifies: RAB-COST-001
func TestDynamicCostIsEvaluated(t *testing.T) {
	calls := 0
	c, err := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 20, BufferItems: 64, IgnoreInternalCost: true, Cost: func(v int) int64 { calls++; return int64(v) }})
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 4}})
	if !got.Applied || calls != 1 || c.RemainingCost() != 16 {
		t.Fatalf("result=%+v calls=%d remaining=%d", got, calls, c.RemainingCost())
	}
}

// Verifies: RAB-UPDATE-001
func TestShouldUpdateAllowsSequentialReplacement(t *testing.T) {
	c, err := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 20, BufferItems: 64, IgnoreInternalCost: true, ShouldUpdate: func(cur, prev int) bool { return cur > prev }})
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	seed(t, c, "a", 1, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 1}})
	if v, _ := c.Get("a"); !got.Applied || v != 2 {
		t.Fatalf("result=%+v value=%d", got, v)
	}
}

// Verifies: RAB-UPDATE-001, RAB-BATCH-004
func TestShouldUpdateRejectsWholeBatch(t *testing.T) {
	c, err := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 20, BufferItems: 64, IgnoreInternalCost: true, ShouldUpdate: func(cur, prev int) bool { return cur > prev }})
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	seed(t, c, "a", 5, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "b", Value: 2, Cost: 1}, {Operation: r.BatchSet, Key: "a", Value: 3, Cost: 1}})
	_, b := c.Get("b")
	v, _ := c.Get("a")
	if got.Failure != r.BatchUpdateRejected || b || v != 5 {
		t.Fatalf("result=%+v a=%d b=%v", got, v, b)
	}
}

// Verifies: RAB-CAP-001
func TestBatchMayFillCapacityExactly(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 8}, {Operation: r.BatchSet, Key: "b", Value: 2, Cost: 12}})
	if !got.Applied || c.RemainingCost() != 0 {
		t.Fatalf("result=%+v remaining=%d", got, c.RemainingCost())
	}
}

// Verifies: RAB-CAP-001, RAB-BATCH-004
func TestCapacityOverflowRejectsWholeBatch(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Cost: 11}, {Operation: r.BatchSet, Key: "b", Cost: 10}})
	_, a := c.Get("a")
	_, b := c.Get("b")
	if got.Failure != r.BatchCapacityExceeded || a || b {
		t.Fatalf("result=%+v a=%v b=%v", got, a, b)
	}
}

// Verifies: RAB-CAP-002
func TestReplacementUsesNetCostDelta(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 15)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 2, Cost: 18}})
	if !got.Applied || c.RemainingCost() != 2 {
		t.Fatalf("result=%+v remaining=%d", got, c.RemainingCost())
	}
}

// Verifies: RAB-CAP-002, RAB-ORDER-001
func TestDeleteFreesCapacityForLaterItem(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 18)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchDelete, Key: "a"}, {Operation: r.BatchSet, Key: "b", Value: 2, Cost: 20}})
	_, a := c.Get("a")
	b, bok := c.Get("b")
	if !got.Applied || a || !bok || b != 2 {
		t.Fatalf("result=%+v a=%v b=%d,%v", got, a, b, bok)
	}
}

// Verifies: RAB-TTL-001
func TestPositiveTTLSetsExpiringEntry(t *testing.T) {
	c := cache(t)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1, TTL: time.Second}})
	ttl, ok := c.GetTTL("a")
	if !got.Applied || !ok || ttl <= 0 || ttl > time.Second {
		t.Fatalf("result=%+v ttl=%v,%v", got, ttl, ok)
	}
}

// Verifies: RAB-TTL-001
func TestZeroTTLCreatesPermanentEntry(t *testing.T) {
	c := cache(t)
	c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "a", Value: 1, Cost: 1}})
	ttl, ok := c.GetTTL("a")
	if !ok || ttl != 0 {
		t.Fatalf("ttl=%v found=%v", ttl, ok)
	}
}

// Verifies: RAB-SNAP-001
func TestGetManyPreservesInputOrder(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 1)
	seed(t, c, "b", 2, 1)
	got := c.GetMany([]string{"b", "missing", "a"})
	if len(got) != 3 || got[0].Key != "b" || got[0].Value != 2 || !got[0].Found || got[1].Found || got[2].Value != 1 {
		t.Fatalf("unexpected snapshot: %+v", got)
	}
}

// Verifies: RAB-SNAP-001
func TestGetManyPreservesDuplicatePositions(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 4, 1)
	got := c.GetMany([]string{"a", "a"})
	if len(got) != 2 || !got[0].Found || !got[1].Found || got[0].Value != 4 || got[1].Value != 4 {
		t.Fatalf("unexpected snapshot: %+v", got)
	}
}

// Verifies: RAB-SNAP-002
func TestGetManyReportsRemainingTTL(t *testing.T) {
	c := cache(t)
	c.SetWithTTL("a", 1, 1, time.Second)
	c.Wait()
	got := c.GetMany([]string{"a"})
	if !got[0].Found || got[0].RemainingTTL <= 0 || got[0].RemainingTTL > time.Second {
		t.Fatalf("unexpected snapshot: %+v", got)
	}
}

// Verifies: RAB-SNAP-002
func TestGetManyPermanentAndMissingTTLAreZero(t *testing.T) {
	c := cache(t)
	seed(t, c, "a", 1, 1)
	got := c.GetMany([]string{"a", "b"})
	if !got[0].Found || got[0].Key != "a" || got[0].Value != 1 || got[0].RemainingTTL != 0 || got[1].Key != "b" || got[1].RemainingTTL != 0 || got[1].Found {
		t.Fatalf("unexpected snapshot: %+v", got)
	}
}

// Verifies: RAB-HASH-001, RAB-BATCH-004
func TestHashConflictRejectsBatch(t *testing.T) {
	c, err := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 20, BufferItems: 64, IgnoreInternalCost: true, KeyToHash: func(k string) (uint64, uint64) {
		if k == "a" {
			return 1, 10
		}
		return 1, 20
	}})
	if err != nil {
		t.Fatal(err)
	}
	defer c.Close()
	seed(t, c, "a", 1, 1)
	got := c.ApplyBatch([]r.BatchItem[string, int]{{Operation: r.BatchSet, Key: "b", Value: 2, Cost: 1}})
	v, ok := c.Get("a")
	if got.Failure != r.BatchHashConflict || !ok || v != 1 {
		t.Fatalf("result=%+v a=%d,%v", got, v, ok)
	}
}
