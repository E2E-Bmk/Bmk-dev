package integration

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Cross-View Invariants 1, 5, 7 — parse, render, reparse,
// select, locate, mutate, and re-read one document end to end.
func TestWorkflowParseSelectMutateReread(t *testing.T) {
	d := store()
	x := mustParse(t, "$.inv[?(@.qty > 1)].sku")
	form := x.String()
	eq(t, "canonical form", "$.inv[?(@.qty > 1)].sku", form)
	re := mustParse(t, form)

	eqMultiset(t, "selected skus", []any{"A1", "C3"}, re.Get(d))
	locs := re.Locate(d, 0)
	eq(t, "location count", 2, len(locs))

	for _, loc := range locs {
		wantNoErr(t, "set at "+loc.String(), loc.Set(d, "SOLD"))
	}
	eqMultiset(t, "post-mutation skus", []any{"SOLD", "SOLD", "B2"},
		mustParse(t, "$.inv[*].sku").Get(d))
	eq(t, "filter now empty", false, mustParse(t, "$.inv[?(@.qty > 1)].sku[?(@ != 'SOLD')]").Has(d))
}

// Verifies: Cross-View Invariants 3, 8 — assemble a rooted filter
// query from a parsed equation, select with root references, then
// write through the filter.
func TestWorkflowRootFilterQuery(t *testing.T) {
	d := map[string]any{
		"floor": 2,
		"recs": []any{
			map[string]any{"v": 1}, map[string]any{"v": 5}, map[string]any{"v": 9},
		},
	}
	eqn := jp.MustParseEquation("@.v > $.floor")
	assembled := jp.R().C("recs").F(eqn).C("v")
	eq(t, "assembled form", "$.recs[?(@.v > $.floor)].v", assembled.String())
	parsed := mustParse(t, assembled.String())
	eqMultiset(t, "assembled Get", []any{5, 9}, assembled.Get(d))
	eqMultiset(t, "parsed Get", assembled.Get(d), parsed.Get(d))

	wantNoErr(t, "write through filter", assembled.Set(d, 0))
	eqMultiset(t, "all clamped", []any{1, 0, 0}, mustParse(t, "$.recs[*].v").Get(d))
	eq(t, "nothing above floor", false, assembled.Has(d))
}

// Verifies: Cross-View Invariants 6, 7 — grow a document with Set
// auto-creation, prune with Del and Remove, and audit with Walk.
func TestWorkflowGrowPruneAudit(t *testing.T) {
	d := map[string]any{}
	wantNoErr(t, "create chain", mustParse(t, "$.cfg.retries").Set(d, 3))
	wantNoErr(t, "create array", mustParse(t, "$.cfg.hosts[1]").Set(d, "b"))
	wantNoErr(t, "fill hole", mustParse(t, "$.cfg.hosts[0]").Set(d, "a"))
	eq(t, "grown doc", map[string]any{
		"cfg": map[string]any{"retries": 3, "hosts": []any{"a", "b"}},
	}, d)

	wantNoErr(t, "del leaves hole", mustParse(t, "$.cfg.hosts[0]").Del(d))
	eq(t, "hole is nil", []any{nil, "b"},
		mustParse(t, "$.cfg.hosts").First(d))

	_, err := mustParse(t, "$.cfg.hosts[0]").Remove(d)
	wantNoErr(t, "remove excises", err)
	eq(t, "shortened", []any{"b"}, mustParse(t, "$.cfg.hosts").First(d))

	var leafPaths []string
	jp.Walk(d, func(path jp.Expr, value any) {
		leafPaths = append(leafPaths, path.String())
		eq(t, "walk value "+path.String(), value, path.First(d))
	}, true)
	eqMultiset(t, "final leaves",
		[]any{"$.cfg.retries", "$.cfg.hosts[0]"},
		func() []any {
			out := make([]any, 0, len(leafPaths))
			for _, p := range leafPaths {
				out = append(out, p)
			}
			return out
		}())
}

// Verifies: Cross-View Invariants 7, 8 — equation-driven modify: parse
// a predicate, attach it to a path, and rewrite matching elements.
func TestWorkflowEquationDrivenModify(t *testing.T) {
	d := store()
	eqn := jp.MustParseEquation("@.qty == 0")
	x := jp.R().C("inv").F(eqn)
	eq(t, "attached form", "$.inv[?(@.qty == 0)]", x.String())

	_, err := x.Modify(d, func(element any) (any, bool) {
		m := element.(map[string]any)
		m["restock"] = true
		return m, true
	})
	wantNoErr(t, "modify", err)
	eqMultiset(t, "flagged skus", []any{"B2"},
		mustParse(t, "$.inv[?(@.restock == true)].sku").Get(d))
	eq(t, "others untouched", false,
		mustParse(t, "$.inv[?(@.qty > 0 && @.restock == true)]").Has(d))

	script := eqn.Script()
	count := 0
	for _, rec := range mustParse(t, "$.inv[*]").Get(d) {
		if script.Match(rec) {
			count++
		}
	}
	eq(t, "script agrees with filter", 1, count)
}

// Verifies: Cross-View Invariants 5, 6 — locate a moving target across
// mutations and keep PathMatch agreement.
func TestWorkflowLocateAcrossMutations(t *testing.T) {
	d := map[string]any{"q": []any{
		map[string]any{"id": 1, "hot": true},
		map[string]any{"id": 2},
		map[string]any{"id": 3, "hot": true},
	}}
	target := mustParse(t, "$.q[?(@.hot == true)].id")
	locs := target.Locate(d, 0)
	// filter-derived location order is unspecified; compare as a set
	eqMultiset(t, "initial locations",
		[]any{"$.q[0].id", "$.q[2].id"},
		func() []any {
			out := make([]any, 0, len(locs))
			for _, s := range locStrs(locs) {
				out = append(out, s)
			}
			return out
		}())
	for _, loc := range locs {
		eq(t, "match "+loc.String(), true, jp.PathMatch(target, loc))
	}

	_, err := mustParse(t, "$.q[0]").Remove(d)
	wantNoErr(t, "remove first", err)
	locs = target.Locate(d, 0)
	eq(t, "relocated", []string{"$.q[1].id"}, locStrs(locs))
	eqMultiset(t, "value at new location", []any{3}, locs[0].Get(d))
	eq(t, "still matches", true, jp.PathMatch(target, locs[0]))
}

// Verifies: Cross-View Invariants 2, 4 — a report pipeline renders
// bracket paths for storage and re-reads them consistently.
func TestWorkflowBracketPathRoundTripReport(t *testing.T) {
	d := store()
	queries := []string{"$.inv[*].qty", "$.meta.count", "$.inv[?(@.qty > 1)]"}
	stored := make([]string, 0, len(queries))
	for _, q := range queries {
		stored = append(stored, mustParse(t, q).BracketString())
	}
	eq(t, "stored forms", []string{
		"$['inv'][*]['qty']",
		"$['meta']['count']",
		"$['inv'][?(@.qty > 1)]",
	}, stored)
	for i, s := range stored {
		orig := mustParse(t, queries[i])
		re := mustParse(t, s)
		eqMultiset(t, "re-read "+s, orig.Get(d), re.Get(d))
		eq(t, "Has agrees "+s, orig.Has(d), re.Has(d))
	}
}
