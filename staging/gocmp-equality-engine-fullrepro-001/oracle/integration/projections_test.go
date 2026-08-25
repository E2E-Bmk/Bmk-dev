package integration

import (
	"testing"

	"github.com/google/go-cmp/cmp"
)

type EqMod struct{ V int }

func (e EqMod) Equal(o EqMod) bool { return e.V%10 == o.V%10 }

func nearComparer(tol float64) cmp.Option {
	return cmp.Comparer(func(x, y float64) bool {
		d := x - y
		return d < tol && d > -tol
	})
}

func TestDiffEmptinessMatchesEqualUnderOptions(t *testing.T) {
	near := nearComparer(0.01)
	cases := []struct {
		name string
		x, y interface{}
		opts []cmp.Option
		want bool
	}{
		{"comparer equal", 1.000, 1.005, []cmp.Option{near}, true},
		{"comparer unequal", 1.0, 1.5, []cmp.Option{near}, false},
		{"method equal", EqMod{3}, EqMod{13}, nil, true},
		{"method unequal", EqMod{3}, EqMod{4}, nil, false},
		{"ignore makes equal", Pt{1, 2}, Pt{9, 2},
			[]cmp.Option{cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "X" }, cmp.Ignore())}, true},
	}
	for _, c := range cases {
		eq := cmp.Equal(c.x, c.y, c.opts...)
		if eq != c.want {
			t.Fatalf("%s: Equal = %v, want %v", c.name, eq, c.want)
		}
		d := cmp.Diff(c.x, c.y, c.opts...)
		if (d == "") != eq {
			t.Fatalf("%s: Diff emptiness (%v) must match Equal (%v)", c.name, d == "", eq)
		}
	}
}

func TestIgnoreFlipsVerdictExactlyWhenValuesDiffer(t *testing.T) {
	igX := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "X" }, cmp.Ignore())
	if !cmp.Equal(Pt{1, 2}, Pt{9, 2}, igX) {
		t.Fatal("ignoring the differing field must yield equal")
	}
	if cmp.Equal(Pt{1, 2}, Pt{9, 2}) {
		t.Fatal("without the ignore the differing field must yield unequal")
	}
	if !cmp.Equal(Pt{1, 2}, Pt{1, 2}, igX) || !cmp.Equal(Pt{1, 2}, Pt{1, 2}) {
		t.Fatal("on already-equal values the ignore must not change the verdict")
	}
	var r recorder
	cmp.Equal(Pt{1, 2}, Pt{9, 2}, igX, cmp.Reporter(&r))
	var sawIgnored bool
	for i, res := range r.results {
		if r.leafStrings[i] == "X" {
			if !res.ByIgnore() || !res.Equal() {
				t.Fatal("the consumed leaf must report ByIgnore with Equal true")
			}
			sawIgnored = true
		}
	}
	if !sawIgnored {
		t.Fatal("the ignored leaf must still be reported")
	}
}

type AB struct{ A, B float64 }

func TestFilterScopingProjectionIndependent(t *testing.T) {
	near := nearComparer(0.01)
	onA := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "A" }, near)
	onBoth := cmp.FilterPath(func(p cmp.Path) bool {
		s := p.String()
		return s == "A" || s == "B"
	}, near)
	x := AB{1.0, 2.0}
	y := AB{1.004, 2.004}

	if cmp.Equal(x, y, onA) {
		t.Fatal("with the comparer scoped to A only, B must fail under ==")
	}
	if cmp.Diff(x, y, onA) == "" {
		t.Fatal("Diff must agree with the scoped verdict (non-empty)")
	}
	if !cmp.Equal(x, y, onBoth) {
		t.Fatal("with the comparer scoped to both fields the values must be equal")
	}
	if d := cmp.Diff(x, y, onBoth); d != "" {
		t.Fatalf("Diff must agree with the scoped verdict (empty), got %q", d)
	}

	var r recorder
	cmp.Equal(x, y, onA, cmp.Reporter(&r))
	for i, res := range r.results {
		switch r.leafStrings[i] {
		case "A":
			if !res.ByFunc() || !res.Equal() {
				t.Fatal("the admitted leaf must be decided by the comparer and judged equal")
			}
		case "B":
			if res.ByFunc() {
				t.Fatal("the non-admitted leaf must not be touched by the comparer")
			}
			if res.Equal() {
				t.Fatal("the non-admitted leaf must fail under ==")
			}
		}
	}
}

func TestFilterValuesScopingAcrossProjections(t *testing.T) {
	small := cmp.FilterValues(func(x, y int) bool { return x < 10 && y < 10 }, cmp.Ignore())
	x := []int{5, 50}
	y := []int{7, 50}
	if !cmp.Equal(x, y, small) {
		t.Fatal("the small differing pair must be ignored")
	}
	if d := cmp.Diff(x, y, small); d != "" {
		t.Fatalf("Diff must be empty when the only difference is ignored, got %q", d)
	}
	y2 := []int{5, 60}
	if cmp.Equal(x, y2, small) {
		t.Fatal("the large differing pair is outside the filter and must fail")
	}
	if cmp.Diff(x, y2, small) == "" {
		t.Fatal("Diff must be non-empty for the non-admitted difference")
	}
	var r recorder
	cmp.Equal(x, y, small, cmp.Reporter(&r))
	var sawByIgnore bool
	for _, res := range r.results {
		if res.ByIgnore() {
			if !res.Equal() {
				t.Fatal("ByIgnore must never accompany a false Equal")
			}
			sawByIgnore = true
		}
	}
	if !sawByIgnore {
		t.Fatal("the ignored leaf must carry the ByIgnore cause")
	}
}

func TestAmbiguityResolvedByDisjointFilters(t *testing.T) {
	alwaysEq := cmp.Comparer(func(a, b int) bool { return true })
	neverEq := cmp.Comparer(func(a, b int) bool { return false })
	small := cmp.FilterValues(func(a, b int) bool { return a < 10 && b < 10 }, alwaysEq)
	large := cmp.FilterValues(func(a, b int) bool { return a >= 10 && b >= 10 }, neverEq)

	if !cmp.Equal(3, 4, small, large) {
		t.Fatal("in the small domain only the accept-all comparer survives")
	}
	if cmp.Equal(30, 30, small, large) {
		t.Fatal("in the large domain only the reject-all comparer survives")
	}
	wantPanic(t, "ambiguous set of applicable options", func() {
		cmp.Equal(3, 4, alwaysEq, neverEq)
	})
}

func TestStructuralRunKeepsCauseFlagsClean(t *testing.T) {
	type Rec struct {
		N int
		S string
		F float64
	}
	x := Rec{1, "a", 2.0}
	y := Rec{1, "a", 2.004}
	var r recorder
	if cmp.Equal(x, y, cmp.Reporter(&r)) {
		t.Fatal("the float difference must make the records unequal")
	}
	for _, res := range r.results {
		if res.ByFunc() || res.ByMethod() {
			t.Fatal("under purely structural comparison no leaf may claim ByFunc or ByMethod")
		}
	}

	var r2 recorder
	if !cmp.Equal(x, y, nearComparer(0.01), cmp.Reporter(&r2)) {
		t.Fatal("with the tolerance comparer the records must be equal")
	}
	var floatByFunc bool
	for i, res := range r2.results {
		if r2.leafStrings[i] == "F" {
			floatByFunc = res.ByFunc()
		} else if res.ByFunc() {
			t.Fatal("only the comparer's leaves may claim ByFunc")
		}
	}
	if !floatByFunc {
		t.Fatal("the float leaf must be decided by the comparer")
	}
}

func TestResultByFuncOnComparerLeaf(t *testing.T) {
	var r recorder
	if !cmp.Equal(1.000, 1.005, nearComparer(0.01), cmp.Reporter(&r)) {
		t.Fatal("the tolerance comparer must judge the floats equal")
	}
	if len(r.results) == 0 {
		t.Fatal("the leaf must be reported")
	}
	for _, res := range r.results {
		if !res.ByFunc() {
			t.Fatal("the comparer-decided leaf must claim ByFunc")
		}
		if res.ByMethod() {
			t.Fatal("no Equal method participated; ByMethod must stay false")
		}
		if !res.Equal() {
			t.Fatal("the comparer judged the leaf equal")
		}
	}
}

func TestResultByMethodOnMethodLeaf(t *testing.T) {
	var r recorder
	if !cmp.Equal(EqMod{3}, EqMod{13}, cmp.Reporter(&r)) {
		t.Fatal("the Equal method must judge 3 and 13 equal mod 10")
	}
	var sawMethod bool
	for _, res := range r.results {
		if res.ByMethod() {
			sawMethod = true
			if res.ByFunc() {
				t.Fatal("a method-decided leaf must not also claim ByFunc")
			}
		}
	}
	if !sawMethod {
		t.Fatal("the method-decided leaf must claim ByMethod")
	}

	var r2 recorder
	if cmp.Equal(EqMod{3}, EqMod{4}, cmp.Reporter(&r2)) {
		t.Fatal("the Equal method must judge 3 and 4 unequal mod 10")
	}
	var sawUnequalMethod bool
	for _, res := range r2.results {
		if res.ByMethod() && !res.Equal() {
			sawUnequalMethod = true
		}
	}
	if !sawUnequalMethod {
		t.Fatal("a method deciding unequal must still claim ByMethod")
	}
}

func TestResultByIgnoreImpliesEqual(t *testing.T) {
	igX := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "X" }, cmp.Ignore())
	var r recorder
	if !cmp.Equal(Pt{1, 2}, Pt{9, 2}, igX, cmp.Reporter(&r)) {
		t.Fatal("ignoring the only difference must yield equal")
	}
	var sawIgnore bool
	for _, res := range r.results {
		if res.ByIgnore() {
			sawIgnore = true
		}
		if res.ByIgnore() && !res.Equal() {
			t.Fatal("ByIgnore must never report true alongside a false Equal")
		}
	}
	if !sawIgnore {
		t.Fatal("the consumed leaf must carry ByIgnore")
	}
}
