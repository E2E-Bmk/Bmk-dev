package integration_test

import (
	"fmt"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	r "github.com/dgraph-io/ristretto/v2"
)

func cache(t *testing.T, max int64, metrics bool, opts func(*r.Config[int, int])) *r.Cache[int, int] {
	t.Helper()
	cfg := &r.Config[int, int]{NumCounters: 10000, MaxCost: max, BufferItems: 64, Metrics: metrics, IgnoreInternalCost: true, TtlTickerDurationInSec: 1}
	if opts != nil {
		opts(cfg)
	}
	c, e := r.NewCache(cfg)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(c.Close)
	return c
}

// Depends-On: TestRST017SetWaitGet, TestRST027IterationVisitsValues
func TestRST036LookupAndIterationAgree(t *testing.T) {
	c := cache(t, 20, false, nil)
	for i := 1; i <= 5; i++ {
		if !c.Set(i, i*10, 1) {
			t.Fatal("drop")
		}
	}
	c.Wait()
	seen := map[int]bool{}
	c.IterValues(func(v int) bool { seen[v] = true; return false })
	for i := 1; i <= 5; i++ {
		v, ok := c.Get(i)
		if !ok || !seen[v] {
			t.Fatal(i, v, ok, seen)
		}
	}
}

// Depends-On: TestRST024PositiveTTLReported, TestRST025ExpiredTTLHidden
func TestRST037TTLViewsAgree(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.SetWithTTL(1, 9, 1, 40*time.Millisecond)
	c.Wait()
	if _, ok := c.Get(1); !ok {
		t.Fatal("missing")
	}
	if _, ok := c.GetTTL(1); !ok {
		t.Fatal("ttl missing")
	}
	time.Sleep(55 * time.Millisecond)
	if _, ok := c.Get(1); ok {
		t.Fatal("present")
	}
	if _, ok := c.GetTTL(1); ok {
		t.Fatal("ttl present")
	}
}

// Depends-On: TestRST024PositiveTTLReported
func TestRST038TTLRefreshExtendsLifetime(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.SetWithTTL(1, 1, 1, 50*time.Millisecond)
	c.Wait()
	time.Sleep(25 * time.Millisecond)
	c.SetWithTTL(1, 2, 1, 70*time.Millisecond)
	c.Wait()
	time.Sleep(40 * time.Millisecond)
	v, ok := c.Get(1)
	if !ok || v != 2 {
		t.Fatal(v, ok)
	}
}

// Depends-On: TestRST023ZeroTTLIsPersistent, TestRST024PositiveTTLReported
func TestRST039TTLUpdateBecomesPersistent(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.SetWithTTL(1, 1, 1, 25*time.Millisecond)
	c.Wait()
	c.Set(1, 2, 1)
	c.Wait()
	time.Sleep(40 * time.Millisecond)
	v, ok := c.Get(1)
	if !ok || v != 2 {
		t.Fatal(v, ok)
	}
	d, ok := c.GetTTL(1)
	if !ok || d != 0 {
		t.Fatal(d, ok)
	}
}

// Depends-On: TestRST023ZeroTTLIsPersistent, TestRST025ExpiredTTLHidden
func TestRST040PersistentUpdateGainsTTL(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.Set(1, 1, 1)
	c.Wait()
	c.SetWithTTL(1, 2, 1, 20*time.Millisecond)
	c.Wait()
	time.Sleep(35 * time.Millisecond)
	if _, ok := c.Get(1); ok {
		t.Fatal("present")
	}
}

// Depends-On: TestRST017SetWaitGet, TestRST020DeleteValue
func TestRST041AcceptedSetThenDeleteOrders(t *testing.T) {
	c := cache(t, 20, false, nil)
	if !c.Set(1, 1, 1) {
		t.Fatal("drop")
	}
	c.Del(1)
	c.Wait()
	if _, ok := c.Get(1); ok {
		t.Fatal("present")
	}
}

// Depends-On: TestRST021ClearValue
func TestRST042ClearThenReuse(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.Set(1, 1, 1)
	c.Wait()
	c.Clear()
	if !c.Set(2, 2, 1) {
		t.Fatal("drop")
	}
	c.Wait()
	if v, ok := c.Get(2); !ok || v != 2 {
		t.Fatal(v, ok)
	}
}

// Depends-On: TestRST013NilSet, TestRST016NilLifecycleSafe
func TestRST043ClosedCacheSurface(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.Set(1, 1, 1)
	c.Wait()
	c.Close()
	if c.Set(2, 2, 1) || c.SetWithTTL(2, 2, 1, time.Second) {
		t.Fatal("accepted")
	}
	if _, ok := c.Get(1); ok {
		t.Fatal("present")
	}
	if _, ok := c.GetTTL(1); ok {
		t.Fatal("ttl")
	}
	c.Del(1)
	c.Clear()
	c.Wait()
	c.UpdateMaxCost(2)
	c.IterValues(func(int) bool { t.Fatal("callback"); return false })
}

// Depends-On: TestRST016NilLifecycleSafe
func TestRST044CloseIdempotent(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.Close()
	c.Close()
	c.Close()
}

// Depends-On: TestRST019UpdateValue
func TestRST045ReplacementCallsExitOnce(t *testing.T) {
	var n atomic.Int32
	c := cache(t, 20, false, func(cfg *r.Config[int, int]) { cfg.OnExit = func(int) { n.Add(1) } })
	c.Set(1, 1, 1)
	c.Wait()
	c.Set(1, 2, 1)
	c.Wait()
	if n.Load() != 1 {
		t.Fatal(n.Load())
	}
}

// Depends-On: TestRST020DeleteValue
func TestRST046DeleteCallsExit(t *testing.T) {
	var removed atomic.Int32
	c := cache(t, 20, false, func(cfg *r.Config[int, int]) {
		cfg.OnExit = func(v int) {
			if v == 1 {
				removed.Add(1)
			}
		}
	})
	c.Set(1, 1, 1)
	c.Wait()
	c.Del(1)
	c.Wait()
	if removed.Load() != 1 {
		t.Fatal(removed.Load())
	}
}

// Depends-On: TestRST021ClearValue
func TestRST047ClearCallsEvictAndExit(t *testing.T) {
	var ev, ex atomic.Int32
	c := cache(t, 20, false, func(cfg *r.Config[int, int]) {
		cfg.OnEvict = func(*r.Item[int]) { ev.Add(1) }
		cfg.OnExit = func(int) { ex.Add(1) }
	})
	c.Set(1, 1, 1)
	c.Set(2, 2, 1)
	c.Wait()
	c.Clear()
	if ev.Load() != 2 || ex.Load() != 2 {
		t.Fatal(ev.Load(), ex.Load())
	}
}

// Depends-On: TestRST017SetWaitGet
func TestRST048CloseReleasesEntries(t *testing.T) {
	var ex atomic.Int32
	c := cache(t, 20, false, func(cfg *r.Config[int, int]) { cfg.OnExit = func(int) { ex.Add(1) } })
	c.Set(1, 1, 1)
	c.Set(2, 2, 1)
	c.Wait()
	c.Close()
	if ex.Load() != 2 {
		t.Fatal(ex.Load())
	}
}

// Depends-On: TestRST033OversizedRejected
func TestRST049CapacityRemainsBounded(t *testing.T) {
	c := cache(t, 3, false, nil)
	for i := 0; i < 10; i++ {
		c.Set(i, i, 1)
		c.Wait()
	}
	if rem := c.RemainingCost(); rem < 0 || rem > 3 {
		t.Fatal(rem)
	}
	count := 0
	c.IterValues(func(int) bool { count++; return false })
	if count > 3 {
		t.Fatal(count)
	}
}

// Depends-On: TestRST010UpdateMaxCostProjection, TestRST011InitialRemainingCost
func TestRST050DynamicCapacityProjection(t *testing.T) {
	c := cache(t, 10, false, nil)
	c.Set(1, 1, 3)
	c.Wait()
	if c.RemainingCost() != 7 {
		t.Fatal(c.RemainingCost())
	}
	c.UpdateMaxCost(20)
	if c.MaxCost() != 20 || c.RemainingCost() != 17 {
		t.Fatal(c.MaxCost(), c.RemainingCost())
	}
}

// Depends-On: TestRST030CostFunctionUsed, TestRST033OversizedRejected
func TestRST051ComputedCostControlsAdmission(t *testing.T) {
	c := cache(t, 5, false, func(cfg *r.Config[int, int]) { cfg.Cost = func(v int) int64 { return int64(v) } })
	c.Set(1, 3, 0)
	c.Wait()
	if _, ok := c.Get(1); !ok {
		t.Fatal("missing")
	}
	c.Set(2, 9, 0)
	c.Wait()
	if _, ok := c.Get(2); ok {
		t.Fatal("oversized admitted")
	}
}

// Depends-On: TestRST029ConflictHashPreventsWrongValue
func TestRST052CustomHashUsedEverywhere(t *testing.T) {
	c := cache(t, 20, false, func(cfg *r.Config[int, int]) {
		cfg.KeyToHash = func(k int) (uint64, uint64) { return uint64(k + 7), uint64(k) }
	})
	c.Set(1, 10, 1)
	c.Set(2, 20, 1)
	c.Wait()
	c.Del(1)
	c.Wait()
	if _, ok := c.Get(1); ok {
		t.Fatal("one present")
	}
	if v, ok := c.Get(2); !ok || v != 20 {
		t.Fatal(v, ok)
	}
}

// Depends-On: TestRST017SetWaitGet
func TestRST053ConcurrentDistinctKeys(t *testing.T) {
	c := cache(t, 2000, false, nil)
	var wg sync.WaitGroup
	for i := 0; i < 200; i++ {
		wg.Add(1)
		go func(i int) { defer wg.Done(); c.Set(i, i*2, 1) }(i)
	}
	wg.Wait()
	c.Wait()
	for i := 0; i < 200; i++ {
		v, ok := c.Get(i)
		if !ok || v != i*2 {
			t.Fatalf("%d %d %v", i, v, ok)
		}
	}
}

// Depends-On: TestRST019UpdateValue
func TestRST054ConcurrentSameKeyIsValidValue(t *testing.T) {
	c := cache(t, 100, false, nil)
	var wg sync.WaitGroup
	for i := 1; i <= 100; i++ {
		wg.Add(1)
		go func(v int) { defer wg.Done(); c.Set(1, v, 1) }(i)
	}
	wg.Wait()
	c.Wait()
	v, ok := c.Get(1)
	if !ok || v < 1 || v > 100 {
		t.Fatal(v, ok)
	}
}

// Depends-On: TestRST017SetWaitGet
func TestRST055ConcurrentReadersStable(t *testing.T) {
	c := cache(t, 100, false, nil)
	c.Set(1, 42, 1)
	c.Wait()
	var bad atomic.Int32
	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				if v, ok := c.Get(1); !ok || v != 42 {
					bad.Add(1)
				}
			}
		}()
	}
	wg.Wait()
	if bad.Load() != 0 {
		t.Fatal(bad.Load())
	}
}

// Depends-On: TestRST017SetWaitGet
func TestRST056WaitPublishesAcceptedBatch(t *testing.T) {
	c := cache(t, 2000, false, nil)
	accepted := map[int]bool{}
	for i := 0; i < 500; i++ {
		if c.Set(i, i, 1) {
			accepted[i] = true
		}
	}
	c.Wait()
	for i := range accepted {
		if v, ok := c.Get(i); !ok || v != i {
			t.Fatalf("%d %d %v", i, v, ok)
		}
	}
}

// Depends-On: TestRST019UpdateValue, TestRST034HitMissRatio
func TestRST057MetricsTrackAddAndUpdate(t *testing.T) {
	c := cache(t, 20, true, nil)
	c.Set(1, 1, 2)
	c.Wait()
	c.Set(1, 2, 3)
	c.Wait()
	if c.Metrics.KeysAdded() != 1 || c.Metrics.KeysUpdated() != 1 || c.Metrics.CostAdded() == 0 {
		t.Fatal(c.Metrics.KeysAdded(), c.Metrics.KeysUpdated(), c.Metrics.CostAdded())
	}
}

// Depends-On: TestRST034HitMissRatio
func TestRST058MetricsStringHasNames(t *testing.T) {
	c := cache(t, 20, true, nil)
	c.Get(1)
	s := strings.ToLower(c.Metrics.String())
	if !strings.Contains(s, "hit") || !strings.Contains(s, "miss") {
		t.Fatal(fmt.Sprintf("%q", s))
	}
}

// Depends-On: TestRST007MetricsDisabledIsNil, TestRST017SetWaitGet
func TestRST059MetricsDisabledCacheStillWorks(t *testing.T) {
	c := cache(t, 20, false, nil)
	if c.Metrics != nil {
		t.Fatal("metrics enabled")
	}
	c.Set(1, 9, 1)
	c.Wait()
	if v, ok := c.Get(1); !ok || v != 9 {
		t.Fatal(v, ok)
	}
}

// Depends-On: TestRST028IterationStopsEarly
func TestRST060ClosedIterationDoesNothing(t *testing.T) {
	c := cache(t, 20, false, nil)
	c.Set(1, 1, 1)
	c.Wait()
	c.Close()
	n := 0
	c.IterValues(func(int) bool { n++; return false })
	if n != 0 {
		t.Fatal(n)
	}
}
