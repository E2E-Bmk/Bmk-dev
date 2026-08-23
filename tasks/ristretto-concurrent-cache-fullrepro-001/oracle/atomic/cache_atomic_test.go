package atomic_test

import (
	"math"
	"sort"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	r "github.com/dgraph-io/ristretto/v2"
)

func cache(t *testing.T, max int64, metrics bool) *r.Cache[string, int] {
	t.Helper()
	c, err := r.NewCache(&r.Config[string, int]{NumCounters: 1000, MaxCost: max, BufferItems: 64, Metrics: metrics, IgnoreInternalCost: true, TtlTickerDurationInSec: 1})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(c.Close)
	return c
}

func TestRST001RejectsZeroCounters(t *testing.T) {
	_, e := r.NewCache(&r.Config[string, int]{MaxCost: 1, BufferItems: 1})
	if e == nil {
		t.Fatal("want error")
	}
}
func TestRST002RejectsNegativeCounters(t *testing.T) {
	_, e := r.NewCache(&r.Config[string, int]{NumCounters: -1, MaxCost: 1, BufferItems: 1})
	if e == nil {
		t.Fatal("want error")
	}
}
func TestRST003RejectsZeroMaxCost(t *testing.T) {
	_, e := r.NewCache(&r.Config[string, int]{NumCounters: 1, BufferItems: 1})
	if e == nil {
		t.Fatal("want error")
	}
}
func TestRST004RejectsNegativeMaxCost(t *testing.T) {
	_, e := r.NewCache(&r.Config[string, int]{NumCounters: 1, MaxCost: -1, BufferItems: 1})
	if e == nil {
		t.Fatal("want error")
	}
}
func TestRST005RejectsZeroBuffer(t *testing.T) {
	_, e := r.NewCache(&r.Config[string, int]{NumCounters: 1, MaxCost: 1})
	if e == nil {
		t.Fatal("want error")
	}
}
func TestRST006RejectsNegativeBuffer(t *testing.T) {
	_, e := r.NewCache(&r.Config[string, int]{NumCounters: 1, MaxCost: 1, BufferItems: -1})
	if e == nil {
		t.Fatal("want error")
	}
}
func TestRST007MetricsDisabledIsNil(t *testing.T) {
	if cache(t, 10, false).Metrics != nil {
		t.Fatal("metrics enabled")
	}
}
func TestRST008MetricsEnabledIsNonNil(t *testing.T) {
	if cache(t, 10, true).Metrics == nil {
		t.Fatal("metrics nil")
	}
}
func TestRST009MaxCostProjection(t *testing.T) {
	if v := cache(t, 17, false).MaxCost(); v != 17 {
		t.Fatal(v)
	}
}
func TestRST010UpdateMaxCostProjection(t *testing.T) {
	c := cache(t, 17, false)
	c.UpdateMaxCost(23)
	if c.MaxCost() != 23 {
		t.Fatal(c.MaxCost())
	}
}
func TestRST011InitialRemainingCost(t *testing.T) {
	if v := cache(t, 17, false).RemainingCost(); v != 17 {
		t.Fatal(v)
	}
}
func TestRST012NilGet(t *testing.T) {
	var c *r.Cache[string, int]
	if v, ok := c.Get("x"); ok || v != 0 {
		t.Fatal(v, ok)
	}
}
func TestRST013NilSet(t *testing.T) {
	var c *r.Cache[string, int]
	if c.Set("x", 1, 1) {
		t.Fatal("accepted")
	}
}
func TestRST014NilSetTTL(t *testing.T) {
	var c *r.Cache[string, int]
	if c.SetWithTTL("x", 1, 1, time.Second) {
		t.Fatal("accepted")
	}
}
func TestRST015NilGetTTL(t *testing.T) {
	var c *r.Cache[string, int]
	if d, ok := c.GetTTL("x"); ok || d != 0 {
		t.Fatal(d, ok)
	}
}
func TestRST016NilLifecycleSafe(t *testing.T) {
	var c *r.Cache[string, int]
	c.Wait()
	c.Del("x")
	c.Clear()
	c.UpdateMaxCost(2)
	c.IterValues(func(int) bool { return false })
	c.Close()
}
func TestRST017SetWaitGet(t *testing.T) {
	c := cache(t, 10, false)
	if !c.Set("a", 7, 1) {
		t.Fatal("drop")
	}
	c.Wait()
	if v, ok := c.Get("a"); !ok || v != 7 {
		t.Fatal(v, ok)
	}
}
func TestRST018MissingGet(t *testing.T) {
	c := cache(t, 10, false)
	if v, ok := c.Get("missing"); ok || v != 0 {
		t.Fatal(v, ok)
	}
}
func TestRST019UpdateValue(t *testing.T) {
	c := cache(t, 10, false)
	c.Set("a", 1, 1)
	c.Wait()
	c.Set("a", 2, 1)
	c.Wait()
	if v, ok := c.Get("a"); !ok || v != 2 {
		t.Fatal(v, ok)
	}
}
func TestRST020DeleteValue(t *testing.T) {
	c := cache(t, 10, false)
	c.Set("a", 1, 1)
	c.Wait()
	c.Del("a")
	c.Wait()
	if _, ok := c.Get("a"); ok {
		t.Fatal("present")
	}
}
func TestRST021ClearValue(t *testing.T) {
	c := cache(t, 10, false)
	c.Set("a", 1, 1)
	c.Wait()
	c.Clear()
	if _, ok := c.Get("a"); ok {
		t.Fatal("present")
	}
}
func TestRST022NegativeTTLNoOp(t *testing.T) {
	c := cache(t, 10, false)
	if c.SetWithTTL("a", 1, 1, -time.Second) {
		t.Fatal("accepted")
	}
	c.Wait()
	if _, ok := c.Get("a"); ok {
		t.Fatal("present")
	}
}
func TestRST023ZeroTTLIsPersistent(t *testing.T) {
	c := cache(t, 10, false)
	c.SetWithTTL("a", 1, 1, 0)
	c.Wait()
	d, ok := c.GetTTL("a")
	if !ok || d != 0 {
		t.Fatal(d, ok)
	}
}
func TestRST024PositiveTTLReported(t *testing.T) {
	c := cache(t, 10, false)
	c.SetWithTTL("a", 1, 1, time.Second)
	c.Wait()
	d, ok := c.GetTTL("a")
	if !ok || d <= 0 || d > time.Second {
		t.Fatal(d, ok)
	}
}
func TestRST025ExpiredTTLHidden(t *testing.T) {
	c := cache(t, 10, false)
	c.SetWithTTL("a", 1, 1, 20*time.Millisecond)
	c.Wait()
	time.Sleep(35 * time.Millisecond)
	if _, ok := c.Get("a"); ok {
		t.Fatal("present")
	}
	if _, ok := c.GetTTL("a"); ok {
		t.Fatal("ttl present")
	}
}
func TestRST026NilPointerValueIsHit(t *testing.T) {
	c, e := r.NewCache(&r.Config[string, *int]{NumCounters: 100, MaxCost: 10, BufferItems: 64, IgnoreInternalCost: true})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	c.Set("x", nil, 1)
	c.Wait()
	v, ok := c.Get("x")
	if !ok || v != nil {
		t.Fatal(v, ok)
	}
}
func TestRST027IterationVisitsValues(t *testing.T) {
	c := cache(t, 10, false)
	c.Set("a", 1, 1)
	c.Set("b", 2, 1)
	c.Set("c", 3, 1)
	c.Wait()
	var vs []int
	c.IterValues(func(v int) bool { vs = append(vs, v); return false })
	sort.Ints(vs)
	if len(vs) != 3 || vs[0] != 1 || vs[2] != 3 {
		t.Fatal(vs)
	}
}
func TestRST028IterationStopsEarly(t *testing.T) {
	c := cache(t, 10, false)
	c.Set("a", 1, 1)
	c.Set("b", 2, 1)
	c.Wait()
	n := 0
	c.IterValues(func(int) bool { n++; return true })
	if n != 1 {
		t.Fatal(n)
	}
}
func TestRST029ConflictHashPreventsWrongValue(t *testing.T) {
	c, e := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 10, BufferItems: 64, IgnoreInternalCost: true, KeyToHash: func(k string) (uint64, uint64) {
		if k == "a" {
			return 1, 1
		}
		return 1, 2
	}})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	c.Set("a", 10, 1)
	c.Set("b", 20, 1)
	c.Wait()
	a, oa := c.Get("a")
	b, ob := c.Get("b")
	if !oa || a != 10 || (ob && b != 20) {
		t.Fatal(a, oa, b, ob)
	}
}
func TestRST030CostFunctionUsed(t *testing.T) {
	var calls atomic.Int32
	c, e := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 10, BufferItems: 64, IgnoreInternalCost: true, Cost: func(v int) int64 { calls.Add(1); return int64(v) }})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	c.Set("a", 3, 0)
	c.Wait()
	if calls.Load() != 1 || c.RemainingCost() != 7 {
		t.Fatal(calls.Load(), c.RemainingCost())
	}
}
func TestRST031ShouldUpdateFalse(t *testing.T) {
	c, e := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 10, BufferItems: 64, IgnoreInternalCost: true, ShouldUpdate: func(cur, prev int) bool { return false }})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	c.Set("a", 1, 1)
	c.Wait()
	c.Set("a", 2, 1)
	c.Wait()
	v, _ := c.Get("a")
	if v != 1 {
		t.Fatal(v)
	}
}
func TestRST032ShouldUpdateTrue(t *testing.T) {
	c, e := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 10, BufferItems: 64, IgnoreInternalCost: true, ShouldUpdate: func(cur, prev int) bool { return true }})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	c.Set("a", 1, 1)
	c.Wait()
	c.Set("a", 2, 1)
	c.Wait()
	v, _ := c.Get("a")
	if v != 2 {
		t.Fatal(v)
	}
}
func TestRST033OversizedRejected(t *testing.T) {
	var reject, exit atomic.Int32
	c, e := r.NewCache(&r.Config[string, int]{NumCounters: 100, MaxCost: 2, BufferItems: 64, IgnoreInternalCost: true, OnReject: func(*r.Item[int]) { reject.Add(1) }, OnExit: func(int) { exit.Add(1) }})
	if e != nil {
		t.Fatal(e)
	}
	defer c.Close()
	c.Set("a", 1, 3)
	c.Wait()
	if _, ok := c.Get("a"); ok {
		t.Fatal("present")
	}
	if reject.Load() != 1 || exit.Load() != 1 {
		t.Fatal(reject.Load(), exit.Load())
	}
}
func TestRST034HitMissRatio(t *testing.T) {
	c := cache(t, 10, true)
	c.Set("a", 1, 1)
	c.Wait()
	c.Get("a")
	c.Get("x")
	if c.Metrics.Hits() != 1 || c.Metrics.Misses() != 1 || math.Abs(c.Metrics.Ratio()-.5) > .0001 {
		t.Fatal(c.Metrics.Hits(), c.Metrics.Misses(), c.Metrics.Ratio())
	}
}
func TestRST035MetricsClear(t *testing.T) {
	c := cache(t, 10, true)
	c.Get("x")
	c.Metrics.Clear()
	if c.Metrics.Misses() != 0 || c.Metrics.Ratio() != 0 || strings.TrimSpace(c.Metrics.String()) == "" {
		t.Fatal("metrics clear")
	}
}
