package atomic

import (
	"regexp"
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Building and Parsing Equations — comparison constructors render.
func TestEquationComparisonRendering(t *testing.T) {
	e := jp.Eq(jp.Get(jp.A().C("x")), jp.ConstInt(3))
	eq(t, "Eq", "(@.x == 3)", e.String())
	eq(t, "Neq", "(@.x != 3)", jp.Neq(jp.Get(jp.A().C("x")), jp.ConstInt(3)).String())
	eq(t, "Lt", "(@.x < 2.5)", jp.Lt(jp.Get(jp.A().C("x")), jp.ConstFloat(2.5)).String())
	eq(t, "Gte", "(@.x >= 2)", jp.Gte(jp.Get(jp.A().C("x")), jp.ConstInt(2)).String())
}

// Verifies: Building and Parsing Equations — logical and arithmetic nesting.
func TestEquationNestedRendering(t *testing.T) {
	e := jp.And(
		jp.Lt(jp.Get(jp.A().C("x")), jp.ConstFloat(2.5)),
		jp.Or(jp.ConstBool(true), jp.Not(jp.Get(jp.A().C("y")))),
	)
	eq(t, "nested", "(@.x < 2.5 && true || !(@.y))", e.String())
	a := jp.Sub(jp.ConstInt(5), jp.Divide(jp.ConstFloat(1.25), jp.Get(jp.A().C("q"))))
	eq(t, "arith", "(5 - 1.25 / @.q)", a.String())
}

// Verifies: Building and Parsing Equations — constant rendering forms.
func TestEquationConstants(t *testing.T) {
	eq(t, "nothing", "(Nothing)", jp.ConstNothing().String())
	eq(t, "nil", "(null)", jp.ConstNil().String())
	eq(t, "float minimal", "(2)", jp.ConstFloat(2.0).String())
	eq(t, "string escape", `('a\'b')`, jp.ConstString("a'b").String())
	eq(t, "regex", "(/ab./)", jp.ConstRegex(regexp.MustCompile("ab.")).String())
	eq(t, "list", "([1,'a'])", jp.ConstList([]any{int64(1), "a"}).String())
	eq(t, "list mixed", "([null,2.5,true,'s'])", jp.ConstList([]any{nil, 2.5, true, "s"}).String())
}

// Verifies: Building and Parsing Equations — function constructors render bare.
func TestEquationFunctionRendering(t *testing.T) {
	eq(t, "length", "length(@.s)", jp.Length(jp.A().C("s")).String())
	eq(t, "count", "count(@.l)", jp.Count(jp.A().C("l")).String())
	eq(t, "match", "match(@.s, '^a')", jp.Match(jp.Get(jp.A().C("s")), jp.ConstString("^a")).String())
	eq(t, "search", "search(@.s, 'b')", jp.Search(jp.Get(jp.A().C("s")), jp.ConstString("b")).String())
}

// Verifies: Building and Parsing Equations — operator constructors render.
func TestEquationOperatorRendering(t *testing.T) {
	g := jp.Get(jp.A().C("v"))
	eq(t, "empty op", "(@.v empty true)", jp.Empty(g, jp.ConstBool(true)).String())
	eq(t, "in op", "(@.v in ['a','b'])", jp.In(g, jp.ConstList([]any{"a", "b"})).String())
	eq(t, "has op", "(@.v has true)", jp.Has(g, jp.ConstBool(true)).String())
	eq(t, "exists op", "(@.v exists true)", jp.Exists(g, jp.ConstBool(true)).String())
}

// Verifies: Building and Parsing Equations — MustParseEquation round trip.
func TestEquationParse(t *testing.T) {
	e := jp.MustParseEquation("(@.x + 2) * 3 == 9")
	eq(t, "grouping kept", "((@.x + 2) * 3 == 9)", e.String())
	e2 := jp.MustParseEquation("@.x == 3 && @.y > 2")
	eq(t, "flat parse", "(@.x == 3 && @.y > 2)", e2.String())
	e3 := jp.MustParseEquation("(@.a || @.b) && @.c")
	eq(t, "precedence parens", "((@.a || @.b) && @.c)", e3.String())
	e4 := jp.MustParseEquation("@.x + 2 * 3 == 9")
	eq(t, "no extra parens", "(@.x + 2 * 3 == 9)", e4.String())
}

// Verifies: Building and Parsing Equations — Filter conversion.
func TestEquationFilterConversion(t *testing.T) {
	e := jp.Eq(jp.Get(jp.A().C("x")), jp.ConstInt(3))
	f := e.Filter()
	eq(t, "filter form", "[?(@.x == 3)]", f.String())
	d := []any{map[string]any{"x": 3}, map[string]any{"x": 4}}
	x := jp.X().F(e)
	eqVals(t, "attached filter selects", []any{map[string]any{"x": 3}}, x.Get(d))
}

// Verifies: Building and Parsing Equations — Script conversion and Match.
func TestEquationScriptConversion(t *testing.T) {
	e := jp.Eq(jp.Get(jp.A().C("x")), jp.ConstInt(3))
	s := e.Script()
	eq(t, "script form", "(@.x == 3)", s.String())
	eq(t, "match hit", true, s.Match(map[string]any{"x": 3}))
	eq(t, "match miss", false, s.Match(map[string]any{"x": 4}))
}

// Verifies: Filters and Scripts — NewScript accepts optional parentheses.
func TestNewScriptForms(t *testing.T) {
	s1, err := jp.NewScript("@.x == 3")
	wantNoErr(t, "bare form", err)
	eq(t, "bare renders wrapped", "(@.x == 3)", s1.String())
	s2, err := jp.NewScript("(@.x == 3)")
	wantNoErr(t, "wrapped form", err)
	eq(t, "wrapped renders", "(@.x == 3)", s2.String())
	eq(t, "behave alike", s1.Match(map[string]any{"x": 3}), s2.Match(map[string]any{"x": 3}))
	eq(t, "hit", true, s2.Match(map[string]any{"x": 3}))
}

// Verifies: Filters and Scripts — Script.Match on single elements.
func TestScriptMatchSemantics(t *testing.T) {
	s := jp.MustNewScript("(@ > 2)")
	eq(t, "scalar hit", true, s.Match(5))
	eq(t, "scalar miss", false, s.Match(1))
	eq(t, "slice is one element", false, s.Match([]any{1, 5}))
	eq(t, "nil data", false, jp.MustNewScript("(@.x == 3)").Match(nil))
	// document root reference works standalone
	eq(t, "root ref", true, jp.MustNewScript("($.k == 1)").Match(map[string]any{"k": 1}))
}

// Verifies: Filters and Scripts — NewFilter requires the full bracket form.
func TestNewFilterForms(t *testing.T) {
	f, err := jp.NewFilter("[?(@.x == 3)]")
	wantNoErr(t, "full form", err)
	eq(t, "renders", "[?(@.x == 3)]", f.String())
	eq(t, "embeds Script Match", true, f.Match(map[string]any{"x": 3}))
	_, err = jp.NewFilter("(@.x == 3)")
	wantErr(t, "parens only", err, "a filter must start with a '[?' and end with ']'")
	_, err = jp.NewFilter("@.x == 3")
	wantErr(t, "bare", err, "a filter must start with a '[?' and end with ']'")
}
