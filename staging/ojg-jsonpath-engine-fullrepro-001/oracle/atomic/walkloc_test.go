package atomic

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Walking, Locating, and Path Matching — Walk visits all nodes.
func TestWalkAllNodes(t *testing.T) {
	d := []any{[]any{1, 2}, "z"}
	var paths []string
	var values []any
	jp.Walk(d, func(path jp.Expr, value any) {
		paths = append(paths, path.String())
		values = append(values, value)
	})
	eqStrs(t, "paths in order", []string{"$", "$[0]", "$[0][0]", "$[0][1]", "$[1]"}, paths)
	eq(t, "leaf value", 1, values[2])
	eq(t, "scalar value", "z", values[4])
}

// Verifies: Walking, Locating, and Path Matching — justLeaves filtering.
func TestWalkJustLeaves(t *testing.T) {
	d := []any{[]any{1, 2}, "z"}
	var paths []string
	jp.Walk(d, func(path jp.Expr, value any) {
		paths = append(paths, path.String())
	}, true)
	eqStrs(t, "leaves only", []string{"$[0][0]", "$[0][1]", "$[1]"}, paths)
}

// Verifies: Walking, Locating, and Path Matching — empty containers yield no leaves.
func TestWalkEmptyContainers(t *testing.T) {
	var count int
	jp.Walk(map[string]any{"e": map[string]any{}, "s": []any{}}, func(path jp.Expr, value any) {
		count++
	}, true)
	eq(t, "no leaf callbacks", 0, count)
	// anchor: the same data walked without justLeaves visits containers
	var all int
	jp.Walk(map[string]any{"e": map[string]any{}, "s": []any{}}, func(path jp.Expr, value any) {
		all++
	})
	eq(t, "containers visited", 3, all)
}

// Verifies: Walking, Locating, and Path Matching — map children order-free.
func TestWalkMapSet(t *testing.T) {
	d := map[string]any{"m": map[string]any{"k": 1}, "l": []any{true}}
	var paths []string
	jp.Walk(d, func(path jp.Expr, value any) {
		paths = append(paths, path.String())
	})
	eqStrSet(t, "path set", []string{"$", "$.m", "$.m.k", "$.l", "$.l[0]"}, paths)
}

// Verifies: Walking, Locating, and Path Matching — Expr.Walk matches only.
func TestExprWalk(t *testing.T) {
	var paths []string
	var lasts []any
	var chains []int
	mustParse(t, "$.inv[*].qty").Walk(store(), func(path jp.Expr, nodes []any) {
		paths = append(paths, path.String())
		lasts = append(lasts, nodes[len(nodes)-1])
		chains = append(chains, len(nodes))
	})
	eqStrs(t, "paths without root", []string{"inv[0].qty", "inv[1].qty", "inv[2].qty"}, paths)
	eqVals(t, "matched values", []any{3, 0, 9}, lasts)
	eq(t, "chain length", 4, chains[0])
}

// Verifies: Walking, Locating, and Path Matching — Locate normalized paths.
func TestLocateBasics(t *testing.T) {
	d := map[string]any{"a": []any{[]any{10, 20}, []any{30}}}
	eqStrs(t, "wildcards", []string{"$.a[0][0]", "$.a[0][1]", "$.a[1][0]"},
		locStrs(mustParse(t, "$.a[*][*]").Locate(d, 0)))
	eqStrs(t, "slice", []string{"$.a[0][0]", "$.a[1][0]"},
		locStrs(mustParse(t, "$.a[0:2][0]").Locate(d, 0)))
	eqStrs(t, "union", []string{"$.a[0][0]", "$.a[0][1]"},
		locStrs(mustParse(t, "$['a'][0][0,1]").Locate(d, 0)))
}

// Verifies: Walking, Locating, and Path Matching — Locate max and rootedness.
func TestLocateMaxAndRoot(t *testing.T) {
	d := map[string]any{"a": []any{[]any{10, 20}, []any{30}}}
	eq(t, "max caps", 2, len(mustParse(t, "$.a[*][*]").Locate(d, 2)))
	eq(t, "zero unlimited", 3, len(mustParse(t, "$.a[*][*]").Locate(d, 0)))
	eq(t, "negative unlimited", 3, len(mustParse(t, "$.a[*][*]").Locate(d, -1)))
	eqStrs(t, "unrooted expression", []string{"a[0]"}, locStrs(mustParse(t, "a[0]").Locate(d, 0)))
	eqVals(t, "no match", nil, func() []any {
		locs := mustParse(t, "$.zz").Locate(d, 0)
		out := make([]any, 0, len(locs))
		for _, l := range locs {
			out = append(out, l.String())
		}
		return out
	}())
}

// Verifies: Walking, Locating, and Path Matching — Locate through descent and filters.
func TestLocateDescentAndFilter(t *testing.T) {
	d := store()
	eqStrSet(t, "descent set", []string{"$.inv[0].qty", "$.inv[1].qty", "$.inv[2].qty"},
		locStrs(mustParse(t, "$..qty").Locate(d, 0)))
	eqStrSet(t, "filter set", []string{"$.inv[0].sku", "$.inv[2].sku"},
		locStrs(mustParse(t, "$.inv[?(@.qty > 0)].sku").Locate(d, 0)))
	for _, l := range mustParse(t, "$..qty").Locate(d, 0) {
		if !l.Normal() {
			t.Fatalf("Locate path %q must be normal", l.String())
		}
	}
}

// Verifies: Walking, Locating, and Path Matching — PathMatch fragment rules.
func TestPathMatchFragments(t *testing.T) {
	cases := []struct {
		target, path string
		want         bool
	}{
		{"$.a.b", "$.a.b", true},
		{"$.a.b", "a.b", true},
		{"@.a", "$.a", true},
		{"$.*.b", "$.a.b", true},
		{"$.a[1]", "$.a[1]", true},
		{"$.a[1]", "$.a[2]", false},
		{"$.a[1:3]", "$.a[0]", true},
		{"$.a[1:3]", "$.a.b", false},
		{"$['a','c'].b", "$.c.b", true},
		{"$['a','b']", "$[1]", false},
		{"$[0,'a']", "$[0]", true},
		{"$[?(@.x)].b", "$.q.b", true},
		{"$.*", "$[1]", true},
	}
	for _, c := range cases {
		got := jp.PathMatch(mustParse(t, c.target), mustParse(t, c.path))
		eq(t, "PathMatch("+c.target+", "+c.path+")", c.want, got)
	}
}

// Verifies: Walking, Locating, and Path Matching — descent runs and prefixes.
func TestPathMatchDescentAndPrefix(t *testing.T) {
	cases := []struct {
		target, path string
		want         bool
	}{
		{"$..x", "$.x", true},
		{"$..x", "$.a.b.c.x", true},
		{"$..x.y", "$.a.x.y", true},
		{"$..x..y", "$.x.q.y", true},
		{"$.a..", "$.a.b", true},
		{"$", "$.a", true},
		{"$.a", "$.a.b", true},
		{"$.a.b", "$.a", false},
	}
	for _, c := range cases {
		got := jp.PathMatch(mustParse(t, c.target), mustParse(t, c.path))
		eq(t, "PathMatch("+c.target+", "+c.path+")", c.want, got)
	}
}
