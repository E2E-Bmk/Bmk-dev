package integration

import (
	"errors"
	"sort"
	"testing"

	"go.uber.org/dig"
)

var errTestSentinel = errors.New("member failed")

type groupIn struct {
	dig.In
	Nums []int `group:"nums"`
}

type softIn struct {
	dig.In
	Nums []int `group:"nums,soft"`
}

func sorted(xs []int) []int {
	out := append([]int{}, xs...)
	sort.Ints(out)
	return out
}

func equalInts(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func TestGroupVisibilityFollowsScopes(t *testing.T) {
	c := dig.New()
	c.Provide(func() int { return 1 }, dig.Group("nums"))
	child := c.Scope("child")
	child.Provide(func() int { return 2 }, dig.Group("nums"))
	var fromChild, fromRoot []int
	if err := child.Invoke(func(p groupIn) { fromChild = sorted(p.Nums) }); err != nil {
		t.Fatalf("child invoke: %v", err)
	}
	if err := c.Invoke(func(p groupIn) { fromRoot = sorted(p.Nums) }); err != nil {
		t.Fatalf("root invoke: %v", err)
	}
	if !equalInts(fromChild, []int{1, 2}) {
		t.Fatalf("child saw %v, want [1 2]", fromChild)
	}
	if !equalInts(fromRoot, []int{1}) {
		t.Fatalf("root saw %v, want only its own [1]", fromRoot)
	}
}

func TestGroupValuesMemoizedAcrossDemands(t *testing.T) {
	c := dig.New()
	runs := 0
	c.Provide(func() int { runs++; return runs }, dig.Group("nums"))
	c.Provide(func() int { runs++; return runs }, dig.Group("nums"))
	var first, second []int
	if err := c.Invoke(func(p groupIn) { first = sorted(p.Nums) }); err != nil {
		t.Fatalf("invoke 1: %v", err)
	}
	if err := c.Invoke(func(p groupIn) { second = sorted(p.Nums) }); err != nil {
		t.Fatalf("invoke 2: %v", err)
	}
	if runs != 2 {
		t.Fatalf("group providers ran %d times total, want 2 (once each)", runs)
	}
	if !equalInts(first, second) {
		t.Fatalf("group content changed between demands: %v vs %v", first, second)
	}
}

func TestFlattenAndScalarProvidersMerge(t *testing.T) {
	c := dig.New()
	type flatOut struct {
		dig.Out
		Ns []int `group:"nums,flatten"`
	}
	c.Provide(func() flatOut { return flatOut{Ns: []int{10, 20}} })
	c.Provide(func() int { return 30 }, dig.Group("nums"))
	var got []int
	if err := c.Invoke(func(p groupIn) { got = sorted(p.Nums) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !equalInts(got, []int{10, 20, 30}) {
		t.Fatalf("got %v, want multiset {10,20,30}", got)
	}
}

func TestSoftGroupOnlyReflectsAlreadyBuiltValues(t *testing.T) {
	c := dig.New()
	type memberOut struct {
		dig.Out
		N int `group:"nums"`
	}
	built := 0
	c.Provide(func() (memberOut, string) { built++; return memberOut{N: 42}, "side" })
	var before []int
	if err := c.Invoke(func(p softIn) { before = append([]int{}, p.Nums...) }); err != nil {
		t.Fatalf("soft invoke: %v", err)
	}
	if len(before) != 0 || built != 0 {
		t.Fatalf("soft demand must not trigger providers: got %v, built=%d", before, built)
	}
	// force the provider to run through its other output
	if err := c.Invoke(func(s string) {}); err != nil {
		t.Fatalf("side invoke: %v", err)
	}
	var after []int
	if err := c.Invoke(func(p softIn) { after = append([]int{}, p.Nums...) }); err != nil {
		t.Fatalf("second soft invoke: %v", err)
	}
	if !equalInts(after, []int{42}) {
		t.Fatalf("soft group after side demand = %v, want [42]", after)
	}
}

func TestHardGroupDemandRunsAllProviders(t *testing.T) {
	c := dig.New()
	type memberOut struct {
		dig.Out
		N int `group:"nums"`
	}
	c.Provide(func() (memberOut, string) { return memberOut{N: 7}, "side" })
	c.Provide(func() int { return 8 }, dig.Group("nums"))
	var got []int
	if err := c.Invoke(func(p groupIn) { got = sorted(p.Nums) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !equalInts(got, []int{7, 8}) {
		t.Fatalf("got %v, want multiset {7,8}", got)
	}
}

func TestGroupProviderFailureFailsWholeDemand(t *testing.T) {
	c := dig.New()
	c.Provide(func() int { return 5 }, dig.Group("nums"))
	c.Provide(func() (int, error) { return 0, errTestSentinel }, dig.Group("nums"))
	ran := false
	err := c.Invoke(func(p groupIn) { ran = true })
	wantContains(t, err, "received non-nil error from function")
	wantContains(t, err, `[group="nums"]`)
	if ran {
		t.Fatal("group demand must fail when any member constructor fails")
	}
}

func TestExportedGroupProviderJoinsGroupEverywhere(t *testing.T) {
	c := dig.New()
	s1 := c.Scope("s1")
	s2 := c.Scope("s2")
	s1.Provide(func() int { return 100 }, dig.Group("nums"), dig.Export(true))
	var fromS2 []int
	if err := s2.Invoke(func(p groupIn) { fromS2 = sorted(p.Nums) }); err != nil {
		t.Fatalf("sibling invoke: %v", err)
	}
	if !equalInts(fromS2, []int{100}) {
		t.Fatalf("sibling saw %v, want [100]", fromS2)
	}
}
