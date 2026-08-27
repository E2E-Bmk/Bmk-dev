package ristrettov8gate

import (
	"fmt"
	"reflect"
	"sort"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	ristretto "github.com/dgraph-io/ristretto/v2"
)

func observe4(t *testing.T, root string, values ...any) {
	t.Helper()
	if len(values) != 4 {
		t.Fatalf("%s: observation cardinality = %d", root, len(values))
	}
	for i, value := range values {
		t.Logf("OBS|%s-%02d|%T|%v", root, i+1, value, value)
	}
}

func newStringCache(t *testing.T, configure func(*ristretto.Config[string, string])) *ristretto.Cache[string, string] {
	t.Helper()
	cfg := &ristretto.Config[string, string]{
		NumCounters:        1_024,
		MaxCost:            128,
		BufferItems:        64,
		IgnoreInternalCost: true,
	}
	if configure != nil {
		configure(cfg)
	}
	cache, err := ristretto.NewCache(cfg)
	if err != nil {
		t.Fatalf("NewCache: %v", err)
	}
	t.Cleanup(cache.Close)
	return cache
}

func setWait(t *testing.T, cache *ristretto.Cache[string, string], key, value string, cost int64) {
	t.Helper()
	if !cache.Set(key, value, cost) {
		t.Fatalf("Set(%q) was dropped", key)
	}
	cache.Wait()
	got, ok := cache.Get(key)
	if !ok || got != value {
		t.Fatalf("Get(%q) = %q, %v; want %q, true", key, got, ok, value)
	}
}

func requireFork(t *testing.T, source *ristretto.Cache[string, string]) *ristretto.Cache[string, string] {
	t.Helper()
	child := source.Fork()
	if child == nil {
		t.Fatal("Fork returned nil")
	}
	t.Cleanup(child.Close)
	return child
}

func valueOf(cache *ristretto.Cache[string, string], key string) string {
	value, ok := cache.Get(key)
	if !ok {
		return "<missing>"
	}
	return value
}

func liveKeys(cache *ristretto.Cache[string, string], keys ...string) []string {
	live := make([]string, 0, len(keys))
	for _, key := range keys {
		if _, ok := cache.Get(key); ok {
			live = append(live, key)
		}
	}
	sort.Strings(live)
	return live
}

func flushHistory(t *testing.T, cache *ristretto.Cache[string, string]) {
	t.Helper()
	barrier := cache.Fork()
	if barrier == nil {
		t.Fatal("history barrier fork returned nil")
	}
	barrier.Close()
}

func TestA01NativeRoundTrip(t *testing.T) {
	cache := newStringCache(t, nil)
	setWait(t, cache, "alpha", "one", 2)
	value, ok := cache.Get("alpha")
	observe4(t, "A01", ok, value, cache.MaxCost(), cache.RemainingCost())
}

func TestA02NativeNegativeTTL(t *testing.T) {
	cache := newStringCache(t, nil)
	accepted := cache.SetWithTTL("neg", "value", 1, -time.Second)
	cache.Wait()
	value, ok := cache.Get("neg")
	if accepted || ok {
		t.Fatalf("negative TTL accepted=%v found=%v value=%q", accepted, ok, value)
	}
	observe4(t, "A02", accepted, ok, value, cache.RemainingCost())
}

func TestA03NativeCapacityUpdate(t *testing.T) {
	cache := newStringCache(t, nil)
	before := cache.MaxCost()
	cache.UpdateMaxCost(96)
	after := cache.MaxCost()
	if before == after || after != 96 {
		t.Fatalf("capacity %d -> %d", before, after)
	}
	observe4(t, "A03", before, after, cache.RemainingCost(), before-after)
}

func TestA04NativeUpdateVeto(t *testing.T) {
	cache := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.ShouldUpdate = func(cur, prev string) bool { return cur > prev }
	})
	setWait(t, cache, "k", "z", 1)
	cache.Set("k", "a", 1)
	cache.Wait()
	value, ok := cache.Get("k")
	if !ok || value != "z" {
		t.Fatalf("vetoed update became %q, %v", value, ok)
	}
	observe4(t, "A04", value, ok, cache.RemainingCost(), cache.MaxCost())
}

func TestA05NativeCustomHasher(t *testing.T) {
	var calls atomic.Int64
	cache := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.KeyToHash = func(key string) (uint64, uint64) {
			calls.Add(1)
			return uint64(len(key))*101 + uint64(key[0]), 17
		}
	})
	setWait(t, cache, "hash", "kept", 1)
	value, ok := cache.Get("hash")
	if !ok || calls.Load() < 2 {
		t.Fatalf("custom hasher calls=%d value=%q ok=%v", calls.Load(), value, ok)
	}
	observe4(t, "A05", calls.Load(), value, ok, cache.MaxCost())
}

func TestA06NativeMetrics(t *testing.T) {
	cache := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.Metrics = true })
	setWait(t, cache, "hit", "v", 1)
	cache.Get("hit")
	cache.Get("miss")
	if cache.Metrics.Hits() == 0 || cache.Metrics.Misses() == 0 {
		t.Fatalf("metrics hits=%d misses=%d", cache.Metrics.Hits(), cache.Metrics.Misses())
	}
	observe4(t, "A06", cache.Metrics.Hits(), cache.Metrics.Misses(), cache.Metrics.KeysAdded(), cache.Metrics.Ratio())
}

func TestA07NativeNilSafety(t *testing.T) {
	var cache *ristretto.Cache[string, string]
	value, ok := cache.Get("x")
	accepted := cache.Set("x", "y", 1)
	cache.Del("x")
	if ok || accepted || value != "" {
		t.Fatalf("nil cache value=%q ok=%v accepted=%v", value, ok, accepted)
	}
	observe4(t, "A07", value, ok, accepted, cache.MaxCost())
}

func TestI01NativeWriteDeleteOrder(t *testing.T) {
	cache := newStringCache(t, nil)
	cache.Set("ordered", "queued", 1)
	cache.Del("ordered")
	cache.Wait()
	value, ok := cache.Get("ordered")
	if ok {
		t.Fatalf("deleted queued value survived: %q", value)
	}
	observe4(t, "I01", value, ok, cache.RemainingCost(), cache.MaxCost())
}

func TestI02NativeClearReuse(t *testing.T) {
	cache := newStringCache(t, nil)
	setWait(t, cache, "before", "old", 1)
	cache.Clear()
	setWait(t, cache, "after", "new", 1)
	old, oldOK := cache.Get("before")
	newValue, newOK := cache.Get("after")
	if oldOK || !newOK {
		t.Fatalf("clear reuse old=%q/%v new=%q/%v", old, oldOK, newValue, newOK)
	}
	observe4(t, "I02", oldOK, newOK, newValue, cache.RemainingCost())
}

func TestI03NativeLeaseVisibility(t *testing.T) {
	cache := newStringCache(t, nil)
	if !cache.SetWithTTL("lease", "short", 1, 45*time.Millisecond) {
		t.Fatal("lease set dropped")
	}
	cache.Wait()
	first, firstOK := cache.Get("lease")
	time.Sleep(70 * time.Millisecond)
	second, secondOK := cache.Get("lease")
	if !firstOK || secondOK {
		t.Fatalf("lease first=%q/%v second=%q/%v", first, firstOK, second, secondOK)
	}
	observe4(t, "I03", firstOK, first, secondOK, second)
}

func TestI04NativePressureBound(t *testing.T) {
	cache := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 2 })
	setWait(t, cache, "a", "A", 1)
	setWait(t, cache, "b", "B", 1)
	cache.Set("c", "C", 1)
	cache.Wait()
	if cache.RemainingCost() < 0 {
		t.Fatalf("negative capacity: %d", cache.RemainingCost())
	}
	observe4(t, "I04", liveKeys(cache, "a", "b", "c"), cache.MaxCost(), cache.RemainingCost(), valueOf(cache, "c"))
}

func TestI05NativeValueCost(t *testing.T) {
	var calls atomic.Int64
	cache := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.Cost = func(value string) int64 { calls.Add(1); return int64(len(value)) }
	})
	if !cache.Set("sized", "12345", 0) {
		t.Fatal("costed set dropped")
	}
	cache.Wait()
	if calls.Load() != 1 || cache.RemainingCost() != 123 {
		t.Fatalf("cost calls=%d remaining=%d", calls.Load(), cache.RemainingCost())
	}
	observe4(t, "I05", calls.Load(), valueOf(cache, "sized"), cache.MaxCost(), cache.RemainingCost())
}

func TestI06NativeCallbackLifecycle(t *testing.T) {
	var exits atomic.Int64
	cache := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.OnExit = func(string) { exits.Add(1) }
	})
	setWait(t, cache, "callback", "v", 1)
	cache.Clear()
	if exits.Load() != 1 {
		t.Fatalf("exit callbacks=%d", exits.Load())
	}
	observe4(t, "I06", exits.Load(), valueOf(cache, "callback"), cache.RemainingCost(), cache.MaxCost())
}

func TestI07NativeIndependentCaches(t *testing.T) {
	left := newStringCache(t, nil)
	right := newStringCache(t, nil)
	setWait(t, left, "key", "left", 1)
	setWait(t, right, "key", "right", 1)
	if valueOf(left, "key") == valueOf(right, "key") {
		t.Fatal("independent caches converged unexpectedly")
	}
	observe4(t, "I07", valueOf(left, "key"), valueOf(right, "key"), left.RemainingCost(), right.RemainingCost())
}

func TestA08ForkNilReceiver(t *testing.T) {
	var cache *ristretto.Cache[string, string]
	child := cache.Fork()
	if child != nil {
		child.Close()
		t.Fatal("nil receiver produced a child")
	}
	observe4(t, "A08", child == nil, cache.MaxCost(), valueOf(cache, "x"), cache.RemainingCost())
}

func TestA09ForkClosedReceiver(t *testing.T) {
	cache := newStringCache(t, nil)
	cache.Close()
	child := cache.Fork()
	if child != nil {
		child.Close()
		t.Fatal("closed cache produced a child")
	}
	observe4(t, "A09", child == nil, cache.MaxCost(), cache.RemainingCost(), valueOf(cache, "x"))
}

func TestA10ForkFreshConfiguration(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 73; cfg.Metrics = true })
	child := requireFork(t, source)
	if child.MaxCost() != 73 || child.Metrics == nil {
		t.Fatalf("child capacity=%d metrics=%v", child.MaxCost(), child.Metrics)
	}
	observe4(t, "A10", child.MaxCost(), child.RemainingCost(), child.Metrics.Hits(), child.Metrics.Misses())
}

func TestA11ForkSingleAssociation(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "copied", "payload", 3)
	child := requireFork(t, source)
	value, ok := child.Get("copied")
	if !ok || value != "payload" {
		t.Fatalf("child value=%q ok=%v", value, ok)
	}
	observe4(t, "A11", value, ok, source.RemainingCost(), child.RemainingCost())
}

func TestA12ForkValueCopySemantics(t *testing.T) {
	type record struct{ Name string }
	cfg := &ristretto.Config[string, *record]{NumCounters: 128, MaxCost: 16, BufferItems: 8, IgnoreInternalCost: true}
	source, err := ristretto.NewCache(cfg)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(source.Close)
	item := &record{Name: "before"}
	if !source.Set("ptr", item, 1) {
		t.Fatal("set dropped")
	}
	source.Wait()
	child := source.Fork()
	if child == nil {
		t.Fatal("Fork returned nil")
	}
	t.Cleanup(child.Close)
	got, ok := child.Get("ptr")
	if !ok || got != item {
		t.Fatalf("pointer identity got=%p want=%p", got, item)
	}
	item.Name = "after"
	observe4(t, "A12", ok, got == item, got.Name, source.RemainingCost()-child.RemainingCost())
}

func TestA13ForkLeaseDeadline(t *testing.T) {
	source := newStringCache(t, nil)
	if !source.SetWithTTL("lease", "v", 1, 220*time.Millisecond) {
		t.Fatal("set dropped")
	}
	source.Wait()
	time.Sleep(45 * time.Millisecond)
	child := requireFork(t, source)
	sourceTTL, sourceOK := source.GetTTL("lease")
	childTTL, childOK := child.GetTTL("lease")
	delta := sourceTTL - childTTL
	if delta < 0 {
		delta = -delta
	}
	if !sourceOK || !childOK || sourceTTL >= 210*time.Millisecond || delta > 35*time.Millisecond {
		t.Fatalf("sourceTTL=%v childTTL=%v sourceOK=%v childOK=%v", sourceTTL, childTTL, sourceOK, childOK)
	}
	observe4(t, "A13", sourceOK, childOK, sourceTTL.Milliseconds(), childTTL.Milliseconds())
}

func TestA14ForkCustomHasherContinues(t *testing.T) {
	var calls atomic.Int64
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.KeyToHash = func(key string) (uint64, uint64) { calls.Add(1); return uint64(len(key)) * 313, uint64(key[0]) }
	})
	setWait(t, source, "one", "source", 1)
	child := requireFork(t, source)
	before := calls.Load()
	setWait(t, child, "two-long", "child", 1)
	after := calls.Load()
	if after <= before {
		t.Fatalf("hasher calls before=%d after=%d", before, after)
	}
	observe4(t, "A14", before, after, valueOf(child, "one"), valueOf(child, "two-long"))
}

func TestA15ForkCostFunctionContinues(t *testing.T) {
	var calls atomic.Int64
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.Cost = func(value string) int64 { calls.Add(1); return int64(len(value)) }
	})
	setWait(t, source, "base", "xx", 0)
	child := requireFork(t, source)
	before := calls.Load()
	setWait(t, child, "next", "yyyy", 0)
	after := calls.Load()
	if after != before+1 {
		t.Fatalf("cost calls before=%d after=%d", before, after)
	}
	observe4(t, "A15", before, after, child.MaxCost(), child.RemainingCost())
}

func TestA16ForkFreshMetrics(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.Metrics = true })
	setWait(t, source, "seen", "v", 1)
	source.Get("seen")
	source.Get("absent")
	beforeHits, beforeMisses := source.Metrics.Hits(), source.Metrics.Misses()
	child := requireFork(t, source)
	if child.Metrics.Hits() != 0 || child.Metrics.Misses() != 0 {
		t.Fatalf("inherited metrics hits=%d misses=%d", child.Metrics.Hits(), child.Metrics.Misses())
	}
	if source.Metrics.Hits() != beforeHits || source.Metrics.Misses() != beforeMisses {
		t.Fatal("fork changed source metrics")
	}
	observe4(t, "A16", beforeHits, beforeMisses, child.Metrics.Hits(), child.Metrics.Misses())
}

func TestI08ForkDrainsBufferedWrites(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 256 })
	for i := 0; i < 20; i++ {
		if !source.Set(fmt.Sprintf("k%02d", i), fmt.Sprintf("v%02d", i), 1) {
			t.Fatalf("set %d dropped", i)
		}
	}
	child := requireFork(t, source)
	live := 0
	for i := 0; i < 20; i++ {
		if valueOf(child, fmt.Sprintf("k%02d", i)) == fmt.Sprintf("v%02d", i) {
			live++
		}
	}
	if live != 20 {
		t.Fatalf("child live writes=%d", live)
	}
	observe4(t, "I08", live, valueOf(child, "k00"), valueOf(child, "k19"), child.RemainingCost())
}

func TestI09ForkDrainsBufferedUpdate(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "version", "old", 2)
	if !source.Set("version", "new", 5) {
		t.Fatal("update dropped")
	}
	child := requireFork(t, source)
	if valueOf(child, "version") != "new" {
		t.Fatalf("child value=%q", valueOf(child, "version"))
	}
	observe4(t, "I09", valueOf(source, "version"), valueOf(child, "version"), source.RemainingCost(), child.RemainingCost())
}

func TestI10ForkDrainsBufferedDelete(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "gone", "value", 1)
	source.Del("gone")
	child := requireFork(t, source)
	_, sourceOK := source.Get("gone")
	_, childOK := child.Get("gone")
	if sourceOK || childOK {
		t.Fatalf("deleted association source=%v child=%v", sourceOK, childOK)
	}
	observe4(t, "I10", sourceOK, childOK, source.RemainingCost(), child.RemainingCost())
}

func TestI11ForkCarriesPartialAccessBatch(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.MaxCost = 1
		cfg.BufferItems = 64
	})
	setWait(t, source, "resident", "A", 1)
	for i := 0; i < 20; i++ {
		source.Get("resident")
	}
	child := requireFork(t, source)
	for i := 0; i < 5; i++ {
		child.Get("challenger")
	}
	flushHistory(t, child)
	child.Set("challenger", "X", 1)
	child.Wait()
	resident, residentOK := child.Get("resident")
	challenger, challengerOK := child.Get("challenger")
	if !residentOK || challengerOK {
		t.Fatalf("resident=%q/%v challenger=%q/%v", resident, residentOK, challenger, challengerOK)
	}
	observe4(t, "I11", resident, residentOK, challenger, challengerOK)
}

func TestI12ForkCarriesDrainedAccessHistory(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.MaxCost = 1
		cfg.BufferItems = 4
	})
	setWait(t, source, "hot", "H", 1)
	for i := 0; i < 12; i++ {
		source.Get("hot")
	}
	child := requireFork(t, source)
	for i := 0; i < 4; i++ {
		child.Get("cold")
	}
	flushHistory(t, child)
	child.Set("cold", "C", 1)
	child.Wait()
	if _, ok := child.Get("hot"); !ok {
		t.Fatal("inherited hot item was displaced")
	}
	if _, ok := child.Get("cold"); ok {
		t.Fatal("colder challenger was admitted")
	}
	observe4(t, "I12", liveKeys(child, "hot", "cold"), valueOf(child, "hot"), valueOf(child, "cold"), child.RemainingCost())
}

func TestI13ForkInheritsCapacityGeneration(t *testing.T) {
	source := newStringCache(t, nil)
	source.UpdateMaxCost(11)
	child := requireFork(t, source)
	source.UpdateMaxCost(19)
	if child.MaxCost() != 11 || source.MaxCost() != 19 {
		t.Fatalf("source=%d child=%d", source.MaxCost(), child.MaxCost())
	}
	observe4(t, "I13", source.MaxCost(), child.MaxCost(), source.RemainingCost(), child.RemainingCost())
}

func TestI14ForkSourceMutationIsIndependent(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "base", "shared", 1)
	child := requireFork(t, source)
	setWait(t, source, "source-only", "S", 1)
	_, childHas := child.Get("source-only")
	if childHas {
		t.Fatal("source write leaked into child")
	}
	observe4(t, "I14", valueOf(source, "source-only"), childHas, valueOf(child, "base"), source.RemainingCost()-child.RemainingCost())
}

func TestI15ForkChildMutationIsIndependent(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "base", "shared", 1)
	child := requireFork(t, source)
	setWait(t, child, "child-only", "C", 1)
	_, sourceHas := source.Get("child-only")
	if sourceHas {
		t.Fatal("child write leaked into source")
	}
	observe4(t, "I15", valueOf(child, "child-only"), sourceHas, valueOf(source, "base"), child.RemainingCost()-source.RemainingCost())
}

func TestI16ForkSurvivesSourceClear(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "kept", "child", 1)
	child := requireFork(t, source)
	source.Clear()
	if valueOf(child, "kept") != "child" || valueOf(source, "kept") != "<missing>" {
		t.Fatal("source clear crossed generation")
	}
	observe4(t, "I16", valueOf(source, "kept"), valueOf(child, "kept"), source.RemainingCost(), child.RemainingCost())
}

func TestI17ForkChildClearDoesNotTouchSource(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "kept", "source", 1)
	child := requireFork(t, source)
	child.Clear()
	if valueOf(source, "kept") != "source" || valueOf(child, "kept") != "<missing>" {
		t.Fatal("child clear crossed generation")
	}
	observe4(t, "I17", valueOf(source, "kept"), valueOf(child, "kept"), source.RemainingCost(), child.RemainingCost())
}

func TestI18ForkSurvivesSourceClose(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "seed", "v", 1)
	child := requireFork(t, source)
	source.Close()
	setWait(t, child, "after", "alive", 1)
	if valueOf(child, "seed") != "v" {
		t.Fatal("source close erased child seed")
	}
	observe4(t, "I18", valueOf(source, "seed"), valueOf(child, "seed"), valueOf(child, "after"), child.MaxCost())
}

func TestI19ForkChildCloseDoesNotTouchSource(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "seed", "v", 1)
	child := requireFork(t, source)
	child.Close()
	setWait(t, source, "after", "alive", 1)
	if valueOf(source, "seed") != "v" {
		t.Fatal("child close erased source seed")
	}
	observe4(t, "I19", valueOf(child, "seed"), valueOf(source, "seed"), valueOf(source, "after"), source.MaxCost())
}

func TestI20ForkSiblingsKeepBoundaries(t *testing.T) {
	source := newStringCache(t, nil)
	setWait(t, source, "version", "one", 1)
	first := requireFork(t, source)
	setWait(t, source, "version", "two", 1)
	second := requireFork(t, source)
	if valueOf(first, "version") != "one" || valueOf(second, "version") != "two" {
		t.Fatal("sibling boundaries collapsed")
	}
	observe4(t, "I20", valueOf(source, "version"), valueOf(first, "version"), valueOf(second, "version"), first.RemainingCost()-second.RemainingCost())
}

func TestI21ForkCreationEmitsNoCallbacks(t *testing.T) {
	var evicts, rejects, exits atomic.Int64
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.OnEvict = func(*ristretto.Item[string]) { evicts.Add(1) }
		cfg.OnReject = func(*ristretto.Item[string]) { rejects.Add(1) }
		cfg.OnExit = func(string) { exits.Add(1) }
	})
	setWait(t, source, "owned", "v", 1)
	before := []int64{evicts.Load(), rejects.Load(), exits.Load()}
	child := requireFork(t, source)
	after := []int64{evicts.Load(), rejects.Load(), exits.Load()}
	if !reflect.DeepEqual(before, after) {
		t.Fatalf("callbacks before=%v after=%v", before, after)
	}
	observe4(t, "I21", before, after, valueOf(child, "owned"), child.RemainingCost())
}

func TestI22ForkCallbacksFollowOwner(t *testing.T) {
	var exits atomic.Int64
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.OnExit = func(string) { exits.Add(1) } })
	setWait(t, source, "owned", "v", 1)
	child := requireFork(t, source)
	source.Del("owned")
	source.Wait()
	first := exits.Load()
	if valueOf(child, "owned") != "v" || first != 1 {
		t.Fatalf("after source delete exits=%d child=%q", first, valueOf(child, "owned"))
	}
	child.Del("owned")
	child.Wait()
	second := exits.Load()
	if second != 2 {
		t.Fatalf("after child delete exits=%d", second)
	}
	observe4(t, "I22", first, second, valueOf(source, "owned"), valueOf(child, "owned"))
}

func TestI23ForkLeaseExpiresInBothGenerations(t *testing.T) {
	source := newStringCache(t, nil)
	if !source.SetWithTTL("lease", "v", 1, 85*time.Millisecond) {
		t.Fatal("set dropped")
	}
	source.Wait()
	child := requireFork(t, source)
	time.Sleep(120 * time.Millisecond)
	sourceValue, sourceOK := source.Get("lease")
	childValue, childOK := child.Get("lease")
	if sourceOK || childOK {
		t.Fatalf("expired source=%q/%v child=%q/%v", sourceValue, sourceOK, childValue, childOK)
	}
	observe4(t, "I23", sourceOK, sourceValue, childOK, childValue)
}

func TestI24ForkCarriesReplacementLease(t *testing.T) {
	source := newStringCache(t, nil)
	if !source.SetWithTTL("lease", "temporary", 1, 90*time.Millisecond) {
		t.Fatal("ttl set dropped")
	}
	source.Wait()
	if !source.Set("lease", "permanent", 1) {
		t.Fatal("replacement dropped")
	}
	child := requireFork(t, source)
	ttl, ok := child.GetTTL("lease")
	time.Sleep(120 * time.Millisecond)
	value, live := child.Get("lease")
	if !ok || ttl != 0 || !live || value != "permanent" {
		t.Fatalf("ttl=%v ok=%v value=%q live=%v", ttl, ok, value, live)
	}
	observe4(t, "I24", ttl, ok, value, live)
}

func TestS01ForkLargeCompletedFrontier(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 512 })
	for i := 0; i < 64; i++ {
		if !source.Set(fmt.Sprintf("frontier-%02d", i), fmt.Sprintf("value-%02d", i), 1) {
			t.Fatalf("set %d dropped", i)
		}
	}
	child := requireFork(t, source)
	live := len(liveKeys(child, func() []string {
		keys := make([]string, 64)
		for i := range keys {
			keys[i] = fmt.Sprintf("frontier-%02d", i)
		}
		return keys
	}()...))
	if live != 64 {
		t.Fatalf("frontier live=%d", live)
	}
	observe4(t, "S01", live, valueOf(child, "frontier-00"), valueOf(child, "frontier-63"), child.RemainingCost())
}

func TestS02ForkWaitsForInFlightCost(t *testing.T) {
	entered := make(chan struct{})
	release := make(chan struct{})
	var once sync.Once
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.Cost = func(value string) int64 {
			once.Do(func() { close(entered) })
			<-release
			return int64(len(value))
		}
	})
	if !source.Set("blocked", "payload", 0) {
		t.Fatal("set dropped")
	}
	<-entered
	result := make(chan *ristretto.Cache[string, string], 1)
	go func() { result <- source.Fork() }()
	select {
	case early := <-result:
		close(release)
		if early != nil {
			early.Close()
		}
		t.Fatal("Fork crossed an unfinished cost calculation")
	case <-time.After(35 * time.Millisecond):
	}
	close(release)
	var child *ristretto.Cache[string, string]
	select {
	case child = <-result:
	case <-time.After(2 * time.Second):
		t.Fatal("Fork did not finish after cost release")
	}
	if child == nil {
		t.Fatal("Fork returned nil")
	}
	t.Cleanup(child.Close)
	value, ok := child.Get("blocked")
	if !ok || value != "payload" {
		t.Fatalf("child value=%q ok=%v", value, ok)
	}
	observe4(t, "S02", value, ok, child.RemainingCost(), source.RemainingCost())
}

func TestS03ForkPreservesAdmissionLineage(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 1; cfg.BufferItems = 64 })
	setWait(t, source, "resident", "R", 1)
	for i := 0; i < 24; i++ {
		source.Get("resident")
	}
	child := requireFork(t, source)
	for i := 0; i < 6; i++ {
		child.Get("challenger")
	}
	flushHistory(t, child)
	child.Set("challenger", "C", 1)
	child.Wait()
	resident, residentOK := child.Get("resident")
	challenger, challengerOK := child.Get("challenger")
	if !residentOK || challengerOK {
		t.Fatalf("resident=%q/%v challenger=%q/%v", resident, residentOK, challenger, challengerOK)
	}
	observe4(t, "S03", resident, residentOK, challenger, challengerOK)
}

func TestS04ForkPolicyDivergesIndependently(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 1; cfg.BufferItems = 64 })
	setWait(t, source, "resident", "R", 1)
	child := requireFork(t, source)
	for i := 0; i < 20; i++ {
		source.Get("resident")
	}
	for i := 0; i < 20; i++ {
		child.Get("challenger")
	}
	flushHistory(t, source)
	flushHistory(t, child)
	source.Set("challenger", "C", 1)
	child.Set("challenger", "C", 1)
	source.Wait()
	child.Wait()
	sourceKeys := liveKeys(source, "resident", "challenger")
	childKeys := liveKeys(child, "resident", "challenger")
	if !reflect.DeepEqual(sourceKeys, []string{"resident"}) || !reflect.DeepEqual(childKeys, []string{"challenger"}) {
		t.Fatalf("source=%v child=%v", sourceKeys, childKeys)
	}
	observe4(t, "S04", sourceKeys, childKeys, source.RemainingCost(), child.RemainingCost())
}

func TestS05ForkNestedGenerationLineage(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 1; cfg.BufferItems = 64 })
	setWait(t, source, "ancestor", "A", 1)
	for i := 0; i < 22; i++ {
		source.Get("ancestor")
	}
	first := requireFork(t, source)
	second := requireFork(t, first)
	for i := 0; i < 5; i++ {
		second.Get("new")
	}
	flushHistory(t, second)
	second.Set("new", "N", 1)
	second.Wait()
	if valueOf(second, "ancestor") != "A" || valueOf(second, "new") != "<missing>" {
		t.Fatal("nested fork lost ancestral policy history")
	}
	observe4(t, "S05", valueOf(source, "ancestor"), valueOf(first, "ancestor"), valueOf(second, "ancestor"), valueOf(second, "new"))
}

func TestS06ForkExpirationRecoversCapacity(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 1 })
	if !source.SetWithTTL("old", "O", 1, 65*time.Millisecond) {
		t.Fatal("set dropped")
	}
	source.Wait()
	child := requireFork(t, source)
	time.Sleep(95 * time.Millisecond)
	cleaned := requireFork(t, child)
	if !cleaned.Set("new", "N", 1) {
		t.Fatal("replacement set dropped")
	}
	cleaned.Wait()
	if valueOf(cleaned, "old") != "<missing>" || valueOf(cleaned, "new") != "N" {
		t.Fatal("expired ownership was not recovered")
	}
	observe4(t, "S06", valueOf(cleaned, "old"), valueOf(cleaned, "new"), cleaned.MaxCost(), cleaned.RemainingCost())
}

func TestS07ForkRetainsUpdatePolicy(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) {
		cfg.ShouldUpdate = func(cur, prev string) bool { return len(cur) > len(prev) }
	})
	setWait(t, source, "version", "long", 1)
	child := requireFork(t, source)
	child.Set("version", "x", 1)
	child.Wait()
	rejected := valueOf(child, "version")
	child.Set("version", "longer", 1)
	child.Wait()
	accepted := valueOf(child, "version")
	if rejected != "long" || accepted != "longer" || valueOf(source, "version") != "long" {
		t.Fatal("forked update policy or independence failed")
	}
	observe4(t, "S07", rejected, accepted, valueOf(source, "version"), valueOf(child, "version"))
}

func TestS08ForkConcurrentIndependentContinuation(t *testing.T) {
	source := newStringCache(t, func(cfg *ristretto.Config[string, string]) { cfg.MaxCost = 512 })
	setWait(t, source, "seed", "root", 1)
	child := requireFork(t, source)
	var group sync.WaitGroup
	for i := 0; i < 24; i++ {
		group.Add(2)
		go func(i int) { defer group.Done(); source.Set(fmt.Sprintf("s-%02d", i), "source", 1) }(i)
		go func(i int) { defer group.Done(); child.Set(fmt.Sprintf("c-%02d", i), "child", 1) }(i)
	}
	group.Wait()
	source.Wait()
	child.Wait()
	sourceOwn := len(liveKeys(source, func() []string {
		keys := make([]string, 24)
		for i := range keys {
			keys[i] = fmt.Sprintf("s-%02d", i)
		}
		return keys
	}()...))
	childOwn := len(liveKeys(child, func() []string {
		keys := make([]string, 24)
		for i := range keys {
			keys[i] = fmt.Sprintf("c-%02d", i)
		}
		return keys
	}()...))
	if sourceOwn != 24 || childOwn != 24 || valueOf(source, "c-00") != "<missing>" || valueOf(child, "s-00") != "<missing>" {
		t.Fatalf("sourceOwn=%d childOwn=%d sourceCross=%q childCross=%q", sourceOwn, childOwn, valueOf(source, "c-00"), valueOf(child, "s-00"))
	}
	observe4(t, "S08", sourceOwn, childOwn, valueOf(source, "c-00"), valueOf(child, "s-00"))
}
