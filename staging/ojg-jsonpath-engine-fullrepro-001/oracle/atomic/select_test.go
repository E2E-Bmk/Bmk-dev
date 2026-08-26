package atomic

import (
	"testing"
)

// Verifies: Selecting Values from Data — root-only expressions.
func TestSelectRootOnly(t *testing.T) {
	d := store()
	got := mustParse(t, "$").Get(d)
	eq(t, "one match", 1, len(got))
	eq(t, "identity", true, len(got) == 1 && got[0] != nil)
	eqVals(t, "scalar root", []any{7}, mustParse(t, "$").Get(7))
	eqVals(t, "nil root", []any{nil}, mustParse(t, "$").Get(nil))
	eq(t, "at equals root", mustParse(t, "@").First(7), mustParse(t, "$").First(7))
}

// Verifies: Selecting Values from Data — child key steps.
func TestSelectChildKeys(t *testing.T) {
	d := store()
	eqVals(t, "top key", []any{"main"}, mustParse(t, "$.name").Get(d))
	eqVals(t, "nested key", []any{3}, mustParse(t, "$.meta.count").Get(d))
	eqVals(t, "missing key", nil, mustParse(t, "$.zz").Get(d))
	eqVals(t, "child of scalar", nil, mustParse(t, "$.name.x").Get(d))
	eqVals(t, "child of slice", nil, mustParse(t, "$.inv.sku").Get(d))
}

// Verifies: Selecting Values from Data — index steps and bounds.
func TestSelectIndexes(t *testing.T) {
	d := store()
	eqVals(t, "first", []any{"A1"}, mustParse(t, "$.inv[0].sku").Get(d))
	eqVals(t, "negative", []any{"C3"}, mustParse(t, "$.inv[-1].sku").Get(d))
	eqVals(t, "out of bounds", nil, mustParse(t, "$.inv[5]").Get(d))
	eqVals(t, "negative out of bounds", nil, mustParse(t, "$.inv[-5]").Get(d))
	eqVals(t, "index on map", nil, mustParse(t, "$.meta[0]").Get(d))
	eqVals(t, "index on string", nil, mustParse(t, "[0]").Get("ab"))
}

// Verifies: Selecting Values from Data — wildcard over slices in order.
func TestSelectWildcardSlice(t *testing.T) {
	d := store()
	eqVals(t, "slice wildcard order", []any{"A1", "B2", "C3"},
		mustParse(t, "$.inv[*].sku").Get(d))
	eqVals(t, "wildcard on scalar", nil, mustParse(t, "[*]").Get(7))
}

// Verifies: Selecting Values from Data — wildcard over maps is order-free.
func TestSelectWildcardMapSet(t *testing.T) {
	d := map[string]any{"z": 1, "a": 2, "m": 3}
	eqSet(t, "map wildcard set", []any{1, 2, 3}, mustParse(t, "$.*").Get(d))
	eqSet(t, "map values", []any{3, true}, mustParse(t, "$.meta.*").Get(store()))
}

// Verifies: Selecting Values from Data — slice fragments with clamping.
func TestSelectSliceFragment(t *testing.T) {
	d := []any{1, 2, 3, 4}
	eqVals(t, "middle", []any{2, 3}, mustParse(t, "[1:3]").Get(d))
	eqVals(t, "open end", []any{2, 3, 4}, mustParse(t, "[1:]").Get(d))
	eqVals(t, "step", []any{1, 3}, mustParse(t, "[::2]").Get(d))
	eqVals(t, "negative step reverses", []any{4, 3, 2, 1}, mustParse(t, "[::-1]").Get(d))
	eqVals(t, "negative bounds", []any{3}, mustParse(t, "[-2:-1]").Get(d))
	eqVals(t, "on map", nil, mustParse(t, "[1:3]").Get(map[string]any{"a": 1}))
}

// Verifies: Selecting Values from Data — union concatenation and duplicates.
func TestSelectUnion(t *testing.T) {
	d := map[string]any{"a": []any{10, 20}, "b": []any{30}}
	eqVals(t, "member order", []any{[]any{30}, []any{10, 20}}, mustParse(t, "$['b','a']").Get(d))
	eqVals(t, "duplicate members", []any{7, 7},
		mustParse(t, "$['i','i']").Get(map[string]any{"i": 7}))
	eqVals(t, "int member on map matches nothing", []any{[]any{10, 20}},
		mustParse(t, "$['a',0]").Get(d))
}

// Verifies: Selecting Values from Data — descent matching.
func TestSelectDescent(t *testing.T) {
	d := store()
	eqSet(t, "all qty", []any{3, 0, 9}, mustParse(t, "$..qty").Get(d))
	eqSet(t, "descent filter", []any{"C3"}, mustParse(t, "$..[?(@.qty == 9)].sku").Get(d))
	// trailing descent matches the node itself and everything beneath it
	got := mustParse(t, "meta..").Get(d)
	eqSet(t, "trailing descent", []any{map[string]any{"count": 3, "active": true}, 3, true}, got)
}

// Verifies: Selecting Values from Data — First and FirstFound basics.
func TestSelectFirstAndFirstFound(t *testing.T) {
	d := store()
	eq(t, "First value", "A1", mustParse(t, "$.inv[*].sku").First(d))
	eq(t, "First no match", nil, mustParse(t, "$.zz").First(d))
	v, found := mustParse(t, "$.name").FirstFound(d)
	eq(t, "FirstFound value", "main", v)
	eq(t, "FirstFound flag", true, found)
	_, found = mustParse(t, "$.zz").FirstFound(d)
	eq(t, "FirstFound miss", false, found)
}

// Verifies: Selecting Values from Data — stored nil is a real match.
func TestSelectNilValueIsMatch(t *testing.T) {
	d := store()
	eq(t, "Has nil value", true, mustParse(t, "$.blank").Has(d))
	v, found := mustParse(t, "$.blank").FirstFound(d)
	eq(t, "FirstFound nil value", nil, v)
	eq(t, "FirstFound nil flag", true, found)
	eqVals(t, "Get nil value", []any{nil}, mustParse(t, "$.blank").Get(d))
	eq(t, "Has missing", false, mustParse(t, "$.zz").Has(d))
}

// Verifies: Selecting Values from Data — Has across fragment kinds.
func TestSelectHas(t *testing.T) {
	d := store()
	eq(t, "existing filter", true, mustParse(t, "$.inv[?(@.qty > 5)]").Has(d))
	eq(t, "failing filter", false, mustParse(t, "$.inv[?(@.qty > 50)]").Has(d))
	eq(t, "root on nil", true, mustParse(t, "$").Has(nil))
	eq(t, "missing mid", false, mustParse(t, "a.b").Has(map[string]any{}))
}

// Verifies: Selecting Values from Data — empty expression matches nothing.
func TestSelectEmptyExpression(t *testing.T) {
	d := store()
	empty := mustParse(t, "")
	eqVals(t, "Get", nil, empty.Get(d))
	eq(t, "First", nil, empty.First(d))
	eq(t, "Has", false, empty.Has(d))
	_, found := empty.FirstFound(d)
	eq(t, "FirstFound", false, found)
	// anchor
	eq(t, "anchor Has", true, mustParse(t, "$.name").Has(d))
}

// Verifies: Selecting Values from Data — First order on slice-only branching.
func TestSelectFirstSliceOrder(t *testing.T) {
	d := []any{map[string]any{"x": 1}, map[string]any{"x": 2}, map[string]any{"x": 3}}
	eq(t, "filter first", map[string]any{"x": 2}, mustParse(t, "[?(@.x > 1)]").First(d))
	eq(t, "wildcard first", 1, mustParse(t, "[*]").First([]any{1, 2}))
	eq(t, "reverse slice first", 3, mustParse(t, "[::-1]").First([]any{1, 2, 3}))
}

// Verifies: Selecting Values from Data — filters over slices keep element order.
func TestSelectFilterSliceOrder(t *testing.T) {
	d := store()
	eqVals(t, "filter order", []any{"A1", "C3"}, mustParse(t, "$.inv[?(@.qty > 0)].sku").Get(d))
	eqVals(t, "reverse comparison", []any{"B2"}, mustParse(t, "$.inv[?(1 > @.qty)].sku").Get(d))
}

// Verifies: Selecting Values from Data — absolute references inside filters.
func TestSelectFilterRootReference(t *testing.T) {
	d := map[string]any{
		"lo":   1,
		"hi":   10,
		"recs": []any{map[string]any{"v": 3}, map[string]any{"v": 20}},
	}
	x := mustParse(t, "$.recs[?(@.v > $.lo && @.v < $.hi)]")
	eqVals(t, "root-bounded filter", []any{map[string]any{"v": 3}}, x.Get(d))
	eq(t, "String kept", "$.recs[?(@.v > $.lo && @.v < $.hi)]", x.String())
}
