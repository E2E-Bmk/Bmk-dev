package atomic

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Mutating Data — Set stores at existing locations.
func TestSetExisting(t *testing.T) {
	d := store()
	wantNoErr(t, "set", mustParse(t, "$.meta.count").Set(d, 99))
	eqVals(t, "read back", []any{99}, mustParse(t, "$.meta.count").Get(d))
}

// Verifies: Mutating Data — Set creates missing map chains.
func TestSetCreatesMapChain(t *testing.T) {
	d := map[string]any{}
	wantNoErr(t, "set", mustParse(t, "$.q.r.s").Set(d, 5))
	eqVals(t, "created chain", []any{5}, mustParse(t, "$.q.r.s").Get(d))
	if _, ok := d["q"].(map[string]any); !ok {
		t.Fatalf("created intermediate must be map[string]any, got %#v", d["q"])
	}
}

// Verifies: Mutating Data — Set creates an array for a missing key + index.
func TestSetCreatesArrayForIndex(t *testing.T) {
	d := map[string]any{}
	wantNoErr(t, "set", mustParse(t, "$.q[0]").Set(d, 5))
	eqVals(t, "created array", []any{5}, mustParse(t, "$.q[0]").Get(d))
	arr, ok := d["q"].([]any)
	if !ok || len(arr) != 1 {
		t.Fatalf("created value must be a 1-element []any, got %#v", d["q"])
	}
}

// Verifies: Mutating Data — Set does not extend existing slices.
func TestSetOutOfBounds(t *testing.T) {
	d := map[string]any{"a": []any{1, 2}}
	err := mustParse(t, "$.a[2]").Set(d, 5)
	wantErr(t, "out of bounds", err, "can not follow out of bounds array index at '$.a[2]'")
	eqVals(t, "unchanged", []any{1, 2}, mustParse(t, "$.a[*]").Get(d))
	// negative indexes resolve from the end and write in place
	wantNoErr(t, "negative", mustParse(t, "$.a[-1]").Set(d, 9))
	eqVals(t, "after negative set", []any{1, 9}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — Set through wildcard writes every element.
func TestSetWildcardAll(t *testing.T) {
	d := store()
	wantNoErr(t, "set", mustParse(t, "$.inv[*].qty").Set(d, 1))
	eqVals(t, "all set", []any{1, 1, 1}, mustParse(t, "$.inv[*].qty").Get(d))
}

// Verifies: Mutating Data — SetOne writes only the first match.
func TestSetOneFirstOnly(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	wantNoErr(t, "setone", mustParse(t, "$.a[*]").SetOne(d, 9))
	eqVals(t, "first only", []any{9, 2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — Set through filter and slice fragments mid-path.
func TestSetThroughFilterAndSlice(t *testing.T) {
	d := map[string]any{"a": []any{map[string]any{"x": 1}, map[string]any{"x": 2}}}
	wantNoErr(t, "filter mid", mustParse(t, "$.a[?(@.x == 2)].y").Set(d, 9))
	eqVals(t, "filter target", []any{9}, mustParse(t, "$.a[1].y").Get(d))
	wantNoErr(t, "slice mid", mustParse(t, "$.a[0:2].x").Set(d, 7))
	eqVals(t, "slice targets", []any{7, 7}, mustParse(t, "$.a[*].x").Get(d))
}

// Verifies: Mutating Data — final union and descent set existing keys.
func TestSetUnionAndDescentLast(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	wantNoErr(t, "union last", mustParse(t, "$.a[0,2]").Set(d, 9))
	eqVals(t, "union targets", []any{9, 2, 9}, mustParse(t, "$.a[*]").Get(d))
	d2 := map[string]any{"m": map[string]any{"k": 1, "j": 2}}
	wantNoErr(t, "descent last", mustParse(t, "$..k").Set(d2, 9))
	eqVals(t, "descent nested key", []any{9}, mustParse(t, "$.m.k").Get(d2))
	// a final descent also creates the key in every visited map
	eqVals(t, "descent created at root", []any{9}, mustParse(t, "$['k']").Get(d2))
	d3 := map[string]any{"m": map[string]any{"j": 1}}
	wantNoErr(t, "descent create", mustParse(t, "$..zz").Set(d3, 1))
	eqVals(t, "created everywhere", []any{1, 1}, mustParse(t, "$..zz").Get(d3))
}

// Verifies: Mutating Data — silent no-op writes.
func TestSetSilentNoOps(t *testing.T) {
	wantNoErr(t, "nil data", mustParse(t, "$.a").Set(nil, 2))
	wantNoErr(t, "key on slice", mustParse(t, "zz").Set([]any{1}, 5))
	d := map[string]any{"m": map[string]any{}}
	wantNoErr(t, "wildcard on empty map", mustParse(t, "$.m.*").Set(d, 1))
	eq(t, "map still empty", 0, len(d["m"].(map[string]any)))
	// anchor: a real write on the same document works
	wantNoErr(t, "anchor", mustParse(t, "$.m.k").Set(d, 1))
	eqVals(t, "anchor read", []any{1}, mustParse(t, "$.m.k").Get(d))
}

// Verifies: Mutating Data — partial creation stays when a later step fails.
func TestSetPartialCreationRemains(t *testing.T) {
	d := map[string]any{"m": map[string]any{}}
	err := mustParse(t, "$.m.list[1].x").Set(d, 5)
	wantErr(t, "follow created nil", err, "can not follow a <nil> at '$.m.list[1]'")
	arr, ok := d["m"].(map[string]any)["list"].([]any)
	if !ok || len(arr) != 2 || arr[0] != nil || arr[1] != nil {
		t.Fatalf("created [nil nil] array must remain, got %#v", d["m"])
	}
}

// Verifies: Mutating Data — MustSet panics with the Set error message.
func TestMustSetPanics(t *testing.T) {
	wantPanic(t, "root", "can not set with an expression ending with a Root", func() {
		jp.MustParseString("$").MustSet(map[string]any{}, 1)
	})
	// anchor: valid MustSet stores
	d := map[string]any{}
	jp.MustParseString("$.k").MustSet(d, 2)
	eqVals(t, "anchor", []any{2}, mustParse(t, "$.k").Get(d))
}

// Verifies: Mutating Data — Del removes map keys and leaves slice holes.
func TestDelSemantics(t *testing.T) {
	d := store()
	wantNoErr(t, "map del", mustParse(t, "$.name").Del(d))
	eq(t, "key removed", false, mustParse(t, "$.name").Has(d))
	d2 := map[string]any{"a": []any{1, 2, 3}}
	wantNoErr(t, "slice del", mustParse(t, "$.a[1]").Del(d2))
	eqVals(t, "hole left", []any{1, nil, 3}, mustParse(t, "$.a[*]").Get(d2))
	eq(t, "length kept", 3, len(d2["a"].([]any)))
}

// Verifies: Mutating Data — DelOne clears only the first match.
func TestDelOneFirstOnly(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	wantNoErr(t, "delone", mustParse(t, "$.a[*]").DelOne(d))
	eqVals(t, "first cleared", []any{nil, 2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — Del union and negative index positions.
func TestDelUnionAndNegative(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	wantNoErr(t, "union", mustParse(t, "$.a[0,2]").Del(d))
	eqVals(t, "union holes", []any{nil, 2, nil}, mustParse(t, "$.a[*]").Get(d))
	d2 := map[string]any{"a": []any{1, 2, 3}}
	wantNoErr(t, "negative", mustParse(t, "$.a[-1]").Del(d2))
	eqVals(t, "negative hole", []any{1, 2, nil}, mustParse(t, "$.a[*]").Get(d2))
}

// Verifies: Mutating Data — descent Del removes existing matching keys.
func TestDelDescent(t *testing.T) {
	d := map[string]any{"m": map[string]any{"k": 1, "j": 2}}
	wantNoErr(t, "descent del", mustParse(t, "$..k").Del(d))
	eq(t, "removed", false, mustParse(t, "$.m.k").Has(d))
	eqVals(t, "sibling kept", []any{2}, mustParse(t, "$.m.j").Get(d))
}

// Verifies: Mutating Data — Remove excises slice elements.
func TestRemoveShortensSlice(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	r, err := mustParse(t, "$.a[1]").Remove(d)
	wantNoErr(t, "remove", err)
	eqVals(t, "shortened", []any{1, 3}, mustParse(t, "$.a[*]").Get(d))
	eq(t, "same root", true, r != nil)
	rm, ok := r.(map[string]any)
	if !ok || len(rm["a"].([]any)) != 2 {
		t.Fatalf("returned root must reflect the removal, got %#v", r)
	}
}

// Verifies: Mutating Data — Remove on a top-level slice returns a new root.
func TestRemoveTopSliceRoot(t *testing.T) {
	d := []any{1, 2, 3}
	r, err := mustParse(t, "[1]").Remove(d)
	wantNoErr(t, "remove", err)
	eqVals(t, "returned root", []any{1, 3}, mustParse(t, "[*]").Get(r))
}

// Verifies: Mutating Data — Remove of map keys, wildcards, and filters.
func TestRemoveKindsOfTargets(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}, "m": map[string]any{"k": 1, "j": 2}}
	_, err := mustParse(t, "$.m.k").Remove(d)
	wantNoErr(t, "map key", err)
	eq(t, "map key gone", false, mustParse(t, "$.m.k").Has(d))
	_, err = mustParse(t, "$.a[*]").Remove(d)
	wantNoErr(t, "wildcard", err)
	eq(t, "emptied", 0, len(d["a"].([]any)))
	d2 := []any{map[string]any{"x": 1}, map[string]any{"x": 2}}
	r, err := mustParse(t, "[?(@.x == 1)]").Remove(d2)
	wantNoErr(t, "filter last", err)
	eqVals(t, "filtered out", []any{map[string]any{"x": 2}}, mustParse(t, "[*]").Get(r))
}

// Verifies: Mutating Data — RemoveOne excises only the first match.
func TestRemoveOneFirstOnly(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	_, err := mustParse(t, "$.a[*]").RemoveOne(d)
	wantNoErr(t, "removeone", err)
	eqVals(t, "one removed", []any{2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — Remove slice fragment target.
func TestRemoveSliceFragment(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	_, err := mustParse(t, "$.a[1:3]").Remove(d)
	wantNoErr(t, "slice target", err)
	eqVals(t, "kept head", []any{1}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — no-match Remove is silent.
func TestRemoveNoMatchSilent(t *testing.T) {
	d := store()
	_, err := mustParse(t, "$.zz").Remove(d)
	wantNoErr(t, "no match", err)
	// anchor: the document is intact and a real remove works
	eqVals(t, "anchor intact", []any{"main"}, mustParse(t, "$.name").Get(d))
	_, err = mustParse(t, "$.name").Remove(d)
	wantNoErr(t, "anchor remove", err)
	eq(t, "anchor removed", false, mustParse(t, "$.name").Has(d))
}

// Verifies: Mutating Data — Modify replaces matched elements via callback.
func TestModifyReplaces(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	r, err := mustParse(t, "$.a[*]").Modify(d, func(e any) (any, bool) {
		if n, ok := e.(int); ok {
			return n * 10, true
		}
		return e, false
	})
	wantNoErr(t, "modify", err)
	eqVals(t, "all modified", []any{10, 20, 30}, mustParse(t, "$.a[*]").Get(d))
	eq(t, "root returned", true, r != nil)
}

// Verifies: Mutating Data — modifier returning false leaves elements.
func TestModifyUnchangedFlag(t *testing.T) {
	d := map[string]any{"a": []any{1, 2}}
	_, err := mustParse(t, "$.a[*]").Modify(d, func(e any) (any, bool) { return 99, false })
	wantNoErr(t, "modify", err)
	eqVals(t, "unchanged", []any{1, 2}, mustParse(t, "$.a[*]").Get(d))
	// anchor: with true the same modifier applies
	_, err = mustParse(t, "$.a[*]").Modify(d, func(e any) (any, bool) { return 99, true })
	wantNoErr(t, "modify true", err)
	eqVals(t, "changed", []any{99, 99}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — ModifyOne stops after the first replacement.
func TestModifyOneFirstOnly(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	_, err := mustParse(t, "$.a[*]").ModifyOne(d, func(e any) (any, bool) { return 0, true })
	wantNoErr(t, "modifyone", err)
	eqVals(t, "first only", []any{0, 2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — Modify can replace a whole slice value.
func TestModifyReplacesSliceValue(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	_, err := mustParse(t, "$.a").Modify(d, func(e any) (any, bool) {
		return append(e.([]any), 4), true
	})
	wantNoErr(t, "modify", err)
	eqVals(t, "extended", []any{1, 2, 3, 4}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Mutating Data — Modify on the root calls the modifier once.
func TestModifyRoot(t *testing.T) {
	d := map[string]any{"k": 1}
	called := 0
	r, err := mustParse(t, "$").Modify(d, func(e any) (any, bool) { called++; return e, false })
	wantNoErr(t, "modify root", err)
	eq(t, "called once", 1, called)
	eq(t, "root returned", true, r != nil)
	eqVals(t, "intact", []any{1}, mustParse(t, "$.k").Get(d))
}
