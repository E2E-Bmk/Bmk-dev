package integration

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Cross-View Invariants 1 — canonical String form is a parse
// fixpoint for dot-form expressions.
func TestCVI1StringFixpointCorpus(t *testing.T) {
	corpus := []string{
		"$", "@", "$.inv", "$.inv[0].sku", "$.inv[*].qty", "$.inv[-1]",
		"$.inv[0:2]", "$.inv[::-1]", "$['inv',0]", "$.inv[1:3:2]",
		"$..qty", "$..tags", "$.meta..", "inv[2].tags[1]",
		"$.inv[?(@.qty > 1)].sku", "$[?(@.limit == 7)]",
		"$.inv[?(@.sku == 'A1' || @.qty > 5)]",
		"$['it\\'s']", "$.*", "*", "$[*].x",
	}
	for _, src := range corpus {
		one := mustParse(t, src).String()
		two := mustParse(t, one).String()
		if one != two {
			t.Fatalf("fixpoint broken for %q: first %q second %q", src, one, two)
		}
	}
	// behavioural anchors: normalization is real, not an echo, and the
	// canonical text still selects.
	eq(t, "bracket key normalizes", "$.inv",
		mustParse(t, "$[ 'inv' ]").String())
	eq(t, "filter spacing normalizes", "$.inv[?(@.qty > 1)]",
		mustParse(t, "$.inv[?(@.qty>1)]").String())
	eq(t, "canonical form selects", []any{"B2"},
		mustParse(t, mustParse(t, "$.inv[1].sku").String()).Get(store()))
}

// Verifies: Cross-View Invariants 1 — fixpoint holds across repeated
// render/parse cycles including normalized filters.
func TestCVI1FixpointRepeated(t *testing.T) {
	cases := []struct {
		src  string
		form string
		want []any
	}{
		{"$[ 'inv' ][?(  @.qty==3  )]", "$.inv[?(@.qty == 3)]",
			[]any{map[string]any{"sku": "A1", "qty": 3, "tags": []any{"new"}}}},
		{"$[\"meta\"][\"count\"]", "$.meta.count", []any{3}},
		{"inv[?(@.qty in [0,9])]", "inv[?(@.qty in [0,9])]",
			[]any{map[string]any{"sku": "B2", "qty": 0},
				map[string]any{"sku": "C3", "qty": 9, "tags": []any{"new", "sale"}}}},
		{"$.inv[?(@.qty >= 3 && @.sku != 'C3')]", "$.inv[?(@.qty >= 3 && @.sku != 'C3')]",
			[]any{map[string]any{"sku": "A1", "qty": 3, "tags": []any{"new"}}}},
	}
	for _, c := range cases {
		x := mustParse(t, c.src)
		form := x.String()
		eq(t, "canonical form "+c.src, c.form, form)
		eqMultiset(t, "results "+c.src, c.want, x.Get(store()))
		for i := 0; i < 3; i++ {
			re := mustParse(t, form)
			if re.String() != form {
				t.Fatalf("cycle %d changed %q -> %q (from %q)", i, form, re.String(), c.src)
			}
			eqMultiset(t, "results stable "+c.src, c.want, re.Get(store()))
			x = re
		}
	}
}

// Verifies: Cross-View Invariants 2 — String and BracketString reparse
// to Get-equivalent expressions for descent-free paths.
func TestCVI2DualFormReparse(t *testing.T) {
	d := store()
	corpus := []struct {
		src  string
		hits int
	}{
		{"$.inv[0].sku", 1}, {"$.inv[*].qty", 3}, {"$.inv[0:2].sku", 2},
		{"$['inv',-1]", 1}, {"$.inv[?(@.qty > 1)].sku", 2}, {"$.meta.*", 2},
		{"$.inv[1]", 1}, {"$[?(@.count == 3)]", 1}, {"$.inv[::-1].sku", 3},
		{"$['name']", 1},
	}
	for _, c := range corpus {
		x := mustParse(t, c.src)
		want := x.Get(d)
		eq(t, "result count "+c.src, c.hits, len(want))
		dot := mustParse(t, x.String())
		br := mustParse(t, x.BracketString())
		eqMultiset(t, "dot reparse "+c.src, want, dot.Get(d))
		eqMultiset(t, "bracket reparse "+c.src, want, br.Get(d))
	}
}

// Verifies: Cross-View Invariants 2 — dual-form reparse equivalence for
// built expressions without descent.
func TestCVI2DualFormBuilt(t *testing.T) {
	d := store()
	cases := []struct {
		x    jp.Expr
		want []any
	}{
		{jp.R().C("inv").N(0).C("sku"), []any{"A1"}},
		{jp.R().C("inv").W().C("qty"), []any{3, 0, 9}},
		{jp.R().C("inv").S(1, 3).C("sku"), []any{"B2", "C3"}},
		{jp.R().C("inv").F(jp.Gt(jp.Get(jp.A().C("qty")), jp.ConstInt(1))).C("sku"),
			[]any{"A1", "C3"}},
		{jp.B().C("meta").C("count"), []any{3}},
	}
	for _, c := range cases {
		eqMultiset(t, "built "+c.x.String(), c.want, c.x.Get(d))
		eqMultiset(t, "dot "+c.x.String(), c.want, mustParse(t, c.x.String()).Get(d))
		eqMultiset(t, "bracket "+c.x.String(), c.want, mustParse(t, c.x.BracketString()).Get(d))
	}
}

// Verifies: Cross-View Invariants 3 — built and parsed expressions are
// interchangeable across Get, Locate, Set, and PathMatch.
func TestCVI3BuiltParsedInterchangeable(t *testing.T) {
	built := jp.R().C("inv").F(jp.Eq(jp.Get(jp.A().C("sku")), jp.ConstString("C3"))).C("qty")
	parsed := mustParse(t, "$.inv[?(@.sku == 'C3')].qty")
	eq(t, "String equal", parsed.String(), built.String())

	d1 := store()
	d2 := store()
	eqMultiset(t, "Get equal", parsed.Get(d1), built.Get(d1))
	eq(t, "Locate equal", locStrs(parsed.Locate(d1, 0)), locStrs(built.Locate(d1, 0)))

	wantNoErr(t, "built Set", built.Set(d1, 100))
	wantNoErr(t, "parsed Set", parsed.Set(d2, 100))
	eq(t, "post-Set documents equal", d1, d2)

	loc := mustParse(t, "$.inv[2].qty")
	eq(t, "PathMatch built", true, jp.PathMatch(built, loc))
	eq(t, "PathMatch parsed", true, jp.PathMatch(parsed, loc))
}

// Verifies: Cross-View Invariants 3 — builder short and spelled-out
// forms produce identical expressions end to end.
func TestCVI3BuilderFormsAgree(t *testing.T) {
	short := jp.R().C("inv").N(1).C("sku")
	long := jp.R().Child("inv").Nth(1).Child("sku")
	eq(t, "String", "$.inv[1].sku", short.String())
	eq(t, "long String", "$.inv[1].sku", long.String())
	d := store()
	eq(t, "Get", []any{"B2"}, short.Get(d))
	eq(t, "long Get", []any{"B2"}, long.Get(d))
	eq(t, "Locate", []string{"$.inv[1].sku"}, locStrs(short.Locate(d, 0)))
	eq(t, "long Locate", []string{"$.inv[1].sku"}, locStrs(long.Locate(d, 0)))
	eq(t, "parsed matches", "$.inv[1].sku", mustParse(t, short.String()).String())
}

// Verifies: Cross-View Invariants 4 — Has mirrors Get non-emptiness and
// FirstFound mirrors Has across expression kinds.
func TestCVI4HasGetFirstFoundAgree(t *testing.T) {
	d := store()
	corpus := []struct {
		src     string
		present bool
	}{
		{"$.inv[0].sku", true}, {"$.missing", false}, {"$.blank", true},
		{"$.inv[9]", false}, {"$.inv[*].tags", true}, {"$..qty", true},
		{"$..nope", false}, {"$.inv[?(@.qty > 100)]", false},
		{"$.inv[?(@.qty > 1)]", true}, {"$.inv[0:0]", false},
		{"$['name','missing']", true}, {"$.meta.active", true}, {"", false},
	}
	for _, c := range corpus {
		x := mustParse(t, c.src)
		got := x.Get(d)
		has := x.Has(d)
		eq(t, "presence "+c.src, c.present, has)
		if has != (len(got) > 0) {
			t.Fatalf("%q: Has=%v but Get returned %d values", c.src, has, len(got))
		}
		_, found := x.FirstFound(d)
		if found != has {
			t.Fatalf("%q: FirstFound found=%v but Has=%v", c.src, found, has)
		}
	}
}

// Verifies: Cross-View Invariants 4 — stored nil counts as present for
// Has, Get, and FirstFound alike.
func TestCVI4NilValuePresence(t *testing.T) {
	d := map[string]any{"a": nil, "l": []any{nil}}
	for _, src := range []string{"$.a", "$.l[0]", "$.l[*]", "$..a"} {
		x := mustParse(t, src)
		eq(t, "Has "+src, true, x.Has(d))
		eq(t, "Get count "+src, 1, len(x.Get(d)))
		v, found := x.FirstFound(d)
		eq(t, "FirstFound found "+src, true, found)
		if v != nil {
			t.Fatalf("%q: FirstFound value want nil got %#v", src, v)
		}
	}
}

// Verifies: Cross-View Invariants 5 — Locate returns one Normal path
// per Get result and the paths re-evaluate to the same multiset.
func TestCVI5LocateGetCorrespondence(t *testing.T) {
	d := store()
	corpus := []struct {
		src  string
		hits int
	}{
		{"$.inv[*].sku", 3}, {"$..qty", 3}, {"$.inv[?(@.qty > 1)]", 2},
		{"$.meta.*", 2}, {"$.inv[0:3:2].sku", 2}, {"$['inv',0]", 1},
		{"$.inv[-1].tags[*]", 2}, {"$.*", 5},
	}
	for _, c := range corpus {
		src := c.src
		x := mustParse(t, src)
		got := x.Get(d)
		eq(t, "result count "+src, c.hits, len(got))
		locs := x.Locate(d, 0)
		if len(locs) != len(got) {
			t.Fatalf("%q: %d locations for %d results", src, len(locs), len(got))
		}
		revals := make([]any, 0, len(locs))
		for _, loc := range locs {
			if !loc.Normal() {
				t.Fatalf("%q: location %q is not normal", src, loc.String())
			}
			vals := loc.Get(d)
			if len(vals) != 1 {
				t.Fatalf("%q: location %q returned %d values", src, loc.String(), len(vals))
			}
			revals = append(revals, vals[0])
		}
		eqMultiset(t, "re-evaluated values "+src, got, revals)
	}
}

// Verifies: Cross-View Invariants 5 — the correspondence holds for
// nested slice data with union and descent branching.
func TestCVI5LocateOnNestedSlices(t *testing.T) {
	d := []any{[]any{10, 20}, []any{30, []any{40}}}
	hits := map[string]int{"$[*][*]": 4, "$..[0]": 4, "$[0,1][1]": 2, "[1][1][0]": 1}
	for _, src := range []string{"$[*][*]", "$..[0]", "$[0,1][1]", "[1][1][0]"} {
		x := mustParse(t, src)
		got := x.Get(d)
		eq(t, "result count "+src, hits[src], len(got))
		locs := x.Locate(d, 0)
		if len(locs) != len(got) {
			t.Fatalf("%q: %d locations for %d results", src, len(locs), len(got))
		}
		revals := make([]any, 0, len(locs))
		for _, loc := range locs {
			eq(t, "normal "+loc.String(), true, loc.Normal())
			vals := loc.Get(d)
			eq(t, "single value at "+loc.String(), 1, len(vals))
			revals = append(revals, vals[0])
		}
		eqMultiset(t, "values "+src, got, revals)
	}
}

// Verifies: Cross-View Invariants 6 — Walk paths evaluate back to the
// exact callback values.
func TestCVI6WalkPathsEvaluate(t *testing.T) {
	d := store()
	visited := 0
	jp.Walk(d, func(path jp.Expr, value any) {
		visited++
		vals := path.Get(d)
		if len(vals) != 1 {
			t.Fatalf("walk path %q returned %d values", path.String(), len(vals))
		}
		eq(t, "walk value at "+path.String(), value, vals[0])
	})
	if visited < 10 {
		t.Fatalf("walk visited only %d nodes", visited)
	}
	leaves := 0
	jp.Walk(d, func(path jp.Expr, value any) {
		leaves++
		vals := path.Get(d)
		eq(t, "leaf count at "+path.String(), 1, len(vals))
		eq(t, "leaf value at "+path.String(), value, vals[0])
	}, true)
	if leaves >= visited {
		t.Fatalf("justLeaves visited %d, full walk %d", leaves, visited)
	}
}

// Verifies: Cross-View Invariants 6 — every Locate path satisfies
// PathMatch with the originating expression as target (targets without
// negative index fragments).
func TestCVI6LocatePathMatch(t *testing.T) {
	d := store()
	corpus := []string{
		"$.inv[*].sku", "$..qty", "$.inv[?(@.qty > 1)]", "$.meta.*",
		"$.inv[0:2]", "$['inv','meta']", "$.inv[2].tags[*]",
	}
	for _, src := range corpus {
		target := mustParse(t, src)
		locs := target.Locate(d, 0)
		if len(locs) == 0 {
			t.Fatalf("%q located nothing", src)
		}
		for _, loc := range locs {
			if !jp.PathMatch(target, loc) {
				t.Fatalf("PathMatch(%q, %q) = false", src, loc.String())
			}
		}
	}
	// anchor: PathMatch discriminates — a sibling path does not match
	eq(t, "non-matching path", false,
		jp.PathMatch(mustParse(t, "$.inv[*].sku"), mustParse(t, "$.inv[0].qty")))
}

// Verifies: Cross-View Invariants 7 — a nil-error Set on a rooted
// normal path is immediately visible through Get.
func TestCVI7SetThenGet(t *testing.T) {
	cases := []struct {
		path  string
		value any
	}{
		{"$.name", "renamed"},
		{"$.inv[1].qty", 42},
		{"$.meta.fresh", true},
		{"$.wing.span[1]", 3.5},
		{"$.blank", "filled"},
	}
	for _, c := range cases {
		d := store()
		x := mustParse(t, c.path)
		wantNoErr(t, "Set "+c.path, x.Set(d, c.value))
		eq(t, "Get after Set "+c.path, []any{c.value}, x.Get(d))
	}
}

// Verifies: Cross-View Invariants 7 — Del and Remove of map-child
// paths leave Has false.
func TestCVI7DelRemoveThenHas(t *testing.T) {
	for _, path := range []string{"$.meta.count", "$.name", "$.inv[0].sku"} {
		d := store()
		x := mustParse(t, path)
		eq(t, "present before Del "+path, true, x.Has(d))
		wantNoErr(t, "Del "+path, x.Del(d))
		eq(t, "Has after Del "+path, false, x.Has(d))

		d2 := store()
		eq(t, "present before Remove "+path, true, x.Has(d2))
		_, err := x.Remove(d2)
		wantNoErr(t, "Remove "+path, err)
		eq(t, "Has after Remove "+path, false, x.Has(d2))
	}
}

// Verifies: Cross-View Invariants 8 — a predicate behaves identically
// as parsed filter, built Equation filter, and per-element Script.
func TestCVI8PredicateCarriersAgree(t *testing.T) {
	recs := []any{
		map[string]any{"sku": "A1", "qty": 3},
		map[string]any{"sku": "B2", "qty": 0},
		map[string]any{"sku": "C3", "qty": 9},
	}
	type carrier struct {
		filterSrc string
		eqn       *jp.Equation
		wantSkus  []any
	}
	cases := []carrier{
		{"[?(@.qty > 1)]", jp.Gt(jp.Get(jp.A().C("qty")), jp.ConstInt(1)),
			[]any{"A1", "C3"}},
		{"[?(@.sku == 'B2')]", jp.Eq(jp.Get(jp.A().C("sku")), jp.ConstString("B2")),
			[]any{"B2"}},
		{"[?(@.qty > 1 && @.sku != 'C3')]",
			jp.And(
				jp.Gt(jp.Get(jp.A().C("qty")), jp.ConstInt(1)),
				jp.Neq(jp.Get(jp.A().C("sku")), jp.ConstString("C3")),
			),
			[]any{"A1"}},
	}
	skusOf := func(sel []any) []any {
		out := make([]any, 0, len(sel))
		for _, e := range sel {
			out = append(out, e.(map[string]any)["sku"])
		}
		return out
	}
	for _, c := range cases {
		parsed := mustParse(t, c.filterSrc)
		built := jp.F(c.eqn)
		eqMultiset(t, "parsed selection "+c.filterSrc, c.wantSkus, skusOf(parsed.Get(recs)))
		eqMultiset(t, "built selection "+c.filterSrc, c.wantSkus, skusOf(built.Get(recs)))

		script := c.eqn.Script()
		var byScript []any
		for _, r := range recs {
			if script.Match(r) {
				byScript = append(byScript, r)
			}
		}
		eqMultiset(t, "script selection "+c.filterSrc, c.wantSkus, skusOf(byScript))
	}
}

// Verifies: Cross-View Invariants 8 — the three carriers render
// consistently as given in Building and Parsing Equations.
func TestCVI8CarrierRenderingsAgree(t *testing.T) {
	eqn := jp.Gt(jp.Get(jp.A().C("qty")), jp.ConstInt(1))
	eq(t, "equation form", "(@.qty > 1)", eqn.String())
	eq(t, "script form", "(@.qty > 1)", eqn.Script().String())
	eq(t, "filter form", "[?(@.qty > 1)]", eqn.Filter().String())
	parsed := mustParse(t, "[?(@.qty>1)]")
	eq(t, "parsed filter normalizes", "[?(@.qty > 1)]", parsed.String())
	reEqn := jp.MustParseEquation(eqn.String())
	eq(t, "equation round trip", eqn.String(), reEqn.String())
}
