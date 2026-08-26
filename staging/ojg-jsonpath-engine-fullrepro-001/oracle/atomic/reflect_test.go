package atomic

import (
	"testing"
)

type inner struct {
	X int
	Y string
}

type outer struct {
	A inner
	B []int
	M map[string]any
	p int
}

// Verifies: Selecting Values from Data — typed slices and maps via reflection.
func TestReflectTypedContainers(t *testing.T) {
	m := map[string]any{"a": []int{1, 2, 3}, "s": []string{"x"}}
	eqVals(t, "typed slice index", []any{2}, mustParse(t, "$.a[1]").Get(m))
	eqVals(t, "typed slice wildcard", []any{1, 2, 3}, mustParse(t, "$.a[*]").Get(m))
	eqVals(t, "string slice", []any{"x"}, mustParse(t, "$.s[0]").Get(m))
	eqVals(t, "typed map value", []any{3}, mustParse(t, "$.k").Get(map[string]int{"k": 3}))
	eqVals(t, "map of typed slices", []any{7, 8}, mustParse(t, "$.a[*]").Get(map[string][]int{"a": {7, 8}}))
}

// Verifies: Selecting Values from Data — Go arrays are indexable.
func TestReflectArray(t *testing.T) {
	var arr [2]int
	arr[0], arr[1] = 5, 6
	eqVals(t, "array index", []any{6}, mustParse(t, "[1]").Get(arr))
	eqVals(t, "array wildcard", []any{5, 6}, mustParse(t, "[*]").Get(arr))
}

// Verifies: Selecting Values from Data — struct field matching ignores ASCII case.
func TestReflectStructFieldCase(t *testing.T) {
	o := &outer{A: inner{X: 5, Y: "y"}, B: []int{1, 2}, M: map[string]any{"k": "v"}, p: 9}
	_ = o.p
	eqVals(t, "lower path", []any{5}, mustParse(t, "$.a.x").Get(o))
	eqVals(t, "exact path", []any{5}, mustParse(t, "$.A.X").Get(o))
	eqVals(t, "slice field", []any{2}, mustParse(t, "$.b[1]").Get(o))
	eqVals(t, "map field", []any{"v"}, mustParse(t, "$.m.k").Get(o))
}

// Verifies: Selecting Values from Data — multi-character case-insensitive match.
func TestReflectStructMultiCharCase(t *testing.T) {
	type rec struct {
		AgeYear int
		URL     string
	}
	r := &rec{AgeYear: 3, URL: "u"}
	for _, p := range []string{"$.ageYear", "$.ageyear", "$.AgeYear"} {
		eqVals(t, p, []any{3}, mustParse(t, p).Get(r))
	}
	eqVals(t, "underscore differs", nil, mustParse(t, "$.age_year").Get(r))
	for _, p := range []string{"$.url", "$.URL", "$.uRL"} {
		eqVals(t, p, []any{"u"}, mustParse(t, p).Get(r))
	}
}

// Verifies: Selecting Values from Data — unexported fields are invisible.
func TestReflectUnexportedInvisible(t *testing.T) {
	o := &outer{A: inner{X: 5}, p: 9}
	_ = o.p
	eqVals(t, "unexported", nil, mustParse(t, "$.p").Get(o))
	eqVals(t, "anchor exported", []any{5}, mustParse(t, "$.a.x").Get(o))
}

// Verifies: Selecting Values from Data — wildcard and descent over struct fields.
func TestReflectStructTraversal(t *testing.T) {
	o := &outer{A: inner{X: 5, Y: "y"}, B: []int{1, 2}, M: map[string]any{"k": "v"}}
	eq(t, "wildcard field count", 3, len(mustParse(t, "$.*").Get(o)))
	eqSet(t, "descent x", []any{5}, mustParse(t, "$..x").Get(o))
}

// Verifies: Selecting Values from Data — struct values work like pointers.
func TestReflectStructValue(t *testing.T) {
	v := inner{X: 4, Y: "s"}
	eqVals(t, "value receiver", []any{4}, mustParse(t, "$.x").Get(v))
	eqVals(t, "value field", []any{"s"}, mustParse(t, "$.y").Get(v))
}
