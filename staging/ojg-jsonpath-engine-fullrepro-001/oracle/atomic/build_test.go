package atomic

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Building Expressions in Code — chained short-form builders.
func TestBuildShortForms(t *testing.T) {
	x := jp.R().C("inv").N(1).C("sku")
	eq(t, "String", "$.inv[1].sku", x.String())
	eqVals(t, "Get", []any{"B2"}, x.Get(store()))
}

// Verifies: Building Expressions in Code — spelled-out method forms.
func TestBuildLongForms(t *testing.T) {
	x := jp.R().Child("inv").Nth(0).Child("qty")
	eq(t, "String", "$.inv[0].qty", x.String())
	eqVals(t, "Get", []any{3}, x.Get(store()))
	x2 := jp.X().Child("inv").Wildcard().Child("sku")
	eq(t, "wildcard chain", "inv.*.sku", x2.String())
	eqVals(t, "wildcard chain Get", []any{"A1", "B2", "C3"}, x2.Get(store()))
}

// Verifies: Building Expressions in Code — built equals parsed.
func TestBuiltEqualsParsed(t *testing.T) {
	built := jp.R().C("inv").W().C("qty")
	eq(t, "built form", "$.inv.*.qty", built.String())
	parsed := mustParse(t, built.String())
	eq(t, "round trip String", "$.inv.*.qty", parsed.String())
	eqVals(t, "built Get", []any{3, 0, 9}, built.Get(store()))
	eqVals(t, "parsed Get", []any{3, 0, 9}, parsed.Get(store()))
}

// Verifies: Building Expressions in Code — descent builder.
func TestBuildDescent(t *testing.T) {
	x := jp.D().C("qty")
	eq(t, "String", "..qty", x.String())
	eqSet(t, "Get", []any{3, 0, 9}, x.Get(store()))
	eq(t, "package D standalone", "..", jp.D().String())
}

// Verifies: Building Expressions in Code — at and root starters.
func TestBuildAnchors(t *testing.T) {
	eq(t, "R", "$", jp.R().String())
	eq(t, "A", "@", jp.A().String())
	eq(t, "A chain", "@.name", jp.A().C("name").String())
	eqVals(t, "A Get", []any{"main"}, jp.A().C("name").Get(store()))
}

// Verifies: Building Expressions in Code — slice builder and SliceNotSet.
func TestBuildSlice(t *testing.T) {
	eq(t, "start only", "[2:]", jp.S(2).String())
	eq(t, "unset end", "[0:]", jp.S(0, jp.SliceNotSet).String())
	eq(t, "start end", "[1:3]", jp.S(1, 3).String())
	eq(t, "start end step", "[1:5:2]", jp.S(1, 5, 2).String())
	eq(t, "negative bounds", "[-2:-1]", jp.S(-2, -1).String())
	eqVals(t, "Get", []any{2, 3}, jp.S(1, 3).Get([]any{1, 2, 3, 4}))
}

// Verifies: Building Expressions in Code — NewSlice returns all-unset parts.
func TestNewSliceUnset(t *testing.T) {
	s := jp.NewSlice()
	eq(t, "start, end, and step parts", 3, len(s))
	for i, v := range s {
		eq(t, "part unset", jp.SliceNotSet, v)
		_ = i
	}
}

// Verifies: Building Expressions in Code — union builder and key kinds.
func TestBuildUnion(t *testing.T) {
	x := jp.U("a", 2)
	eq(t, "String", "['a',2]", x.String())
	u := jp.NewUnion("a", 1)
	eq(t, "NewUnion members", 2, len(u))
	if jp.NewUnion(int32(5)) != nil {
		t.Fatalf("NewUnion with non string/int key must return nil")
	}
	d := map[string]any{"a": []any{10, 20}}
	eqVals(t, "union Get", []any{[]any{10, 20}}, jp.U("a", 2).Get(d))
}

// Verifies: Building Expressions in Code — filter attachment with F.
func TestBuildFilterFragment(t *testing.T) {
	eqn := jp.Eq(jp.Get(jp.A().C("x")), jp.ConstInt(3))
	x := jp.F(eqn)
	eq(t, "String", "[?(@.x == 3)]", x.String())
	d := []any{map[string]any{"x": 3}, map[string]any{"x": 4}}
	eqVals(t, "Get", []any{map[string]any{"x": 3}}, x.Get(d))
}

// Verifies: Building Expressions in Code — X starts empty.
func TestBuildEmptyX(t *testing.T) {
	eq(t, "X String", "", jp.X().String())
	eq(t, "X len", 0, len(jp.X()))
	eqVals(t, "X Get", nil, jp.X().Get(store()))
	eqVals(t, "X extended", []any{7}, jp.X().C("limit").Get(store()))
}

// Verifies: Building Expressions in Code — bracket display flag.
func TestBuildBracketFlag(t *testing.T) {
	x := jp.B().C("a").N(1)
	eq(t, "String is bracket form", "['a'][1]", x.String())
	eq(t, "same as BracketString", x.BracketString(), x.String())
	if !x.Normal() {
		t.Fatalf("bracket flag must not affect Normal")
	}
	eqVals(t, "Get unaffected", []any{20}, x.Get(map[string]any{"a": []any{10, 20}}))
}

// Verifies: Building Expressions in Code — wildcard builder spelling.
func TestBuildWildcardSpelling(t *testing.T) {
	eq(t, "standalone", "*", jp.W().String())
	eq(t, "at start of chain", "*.b", jp.W().C("b").String())
	eq(t, "after fragment", "a.*", jp.C("a").W().String())
	eq(t, "bracket render", "[*]", jp.W().BracketString())
}

// Verifies: Building Expressions in Code — builders leave the receiver reusable.
func TestBuildAppendReturnsExtended(t *testing.T) {
	base := jp.R().C("inv")
	x1 := base.N(0).C("sku")
	eq(t, "extended", "$.inv[0].sku", x1.String())
	eqVals(t, "extended Get", []any{"A1"}, x1.Get(store()))
}

// Verifies: Building Expressions in Code — child keys with specials render quoted.
func TestBuildQuotedChild(t *testing.T) {
	eq(t, "dot in key", "['a.b']", jp.C("a.b").String())
	eq(t, "quote in key", `['it\'s']`, jp.C("it's").String())
	eqVals(t, "lookup", []any{4}, jp.C("a.b").Get(map[string]any{"a.b": 4}))
}
