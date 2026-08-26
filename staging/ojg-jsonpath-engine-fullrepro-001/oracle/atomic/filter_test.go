package atomic

import (
	"testing"
)

func filterDocs() []any {
	return []any{
		map[string]any{"x": 1, "s": "abc", "l": []any{1, 2}, "f": 1.5},
		map[string]any{"x": 2, "s": "abd", "n": nil},
		map[string]any{"s": "xyz"},
	}
}

func matchCount(t *testing.T, src string, data any) int {
	t.Helper()
	return len(mustParse(t, src).Get(data))
}

// Verifies: Filters and Scripts — equality and inequality.
func TestFilterEquality(t *testing.T) {
	d := filterDocs()
	eq(t, "==", 1, matchCount(t, "[?(@.x == 1)]", d))
	eq(t, "!=", 2, matchCount(t, "[?(@.x != 1)]", d))
	eq(t, "int/float equal", 1, matchCount(t, "[?(@.x == 1.0)]", d))
	eq(t, "string equal", 1, matchCount(t, "[?(@.s == 'abc')]", d))
}

// Verifies: Filters and Scripts — ordering comparisons.
func TestFilterOrdering(t *testing.T) {
	d := filterDocs()
	eq(t, ">", 1, matchCount(t, "[?(@.x > 1)]", d))
	eq(t, ">=", 1, matchCount(t, "[?(@.x >= 2)]", d))
	eq(t, "<", 1, matchCount(t, "[?(@.x < 2)]", d))
	eq(t, "<=", 1, matchCount(t, "[?(@.x <= 1)]", d))
	eq(t, "float compare", 1, matchCount(t, "[?(@.f > 1)]", d))
	eq(t, "reversed operand", 1, matchCount(t, "[?(3 < @.x)]", []any{map[string]any{"x": 4}}))
}

// Verifies: Filters and Scripts — string ordering is lexicographic.
func TestFilterStringOrdering(t *testing.T) {
	d := []any{map[string]any{"s": "aa"}, map[string]any{"s": "b"}}
	eqVals(t, "less", []any{map[string]any{"s": "aa"}}, mustParse(t, "[?(@.s < 'b')]").Get(d))
	eq(t, "greater", 2, matchCount(t, "[?(@.s > 'a')]", d))
	eq(t, "lte", 1, matchCount(t, "[?(@.s <= 'aa')]", d))
}

// Verifies: Filters and Scripts — no cross-kind coercion.
func TestFilterNoCrossKindCoercion(t *testing.T) {
	d := filterDocs()
	eq(t, "string vs number", 0, matchCount(t, "[?(@.s == 1)]", d))
	eq(t, "number vs string", 0, matchCount(t, "[?(@.x == '1')]", d))
	eq(t, "number vs bool", 0, matchCount(t, "[?(@.x == true)]", d))
	eq(t, "order on missing", 0, matchCount(t, "[?(@.zz > 0)]", d))
	// anchor: same-kind comparison still matches
	eq(t, "anchor", 1, matchCount(t, "[?(@.x == 2)]", d))
}

// Verifies: Filters and Scripts — logical composition and grouping.
func TestFilterLogic(t *testing.T) {
	d := filterDocs()
	eq(t, "||", 2, matchCount(t, "[?(@.x == 1 || @.x == 2)]", d))
	eq(t, "&&", 1, matchCount(t, "[?(@.x == 1 && @.s == 'abc')]", d))
	eq(t, "grouped !", 2, matchCount(t, "[?(!(@.x == 1))]", d))
}

// Verifies: Filters and Scripts — arithmetic inside predicates.
func TestFilterArithmetic(t *testing.T) {
	d := filterDocs()
	eq(t, "+", 1, matchCount(t, "[?(@.x + 1 == 2)]", d))
	eq(t, "-", 1, matchCount(t, "[?(@.x - 1 == 0)]", d))
	eq(t, "*", 1, matchCount(t, "[?(@.x * 2 == 4)]", d))
	eq(t, "/", 1, matchCount(t, "[?(@.x / 2 == 1)]", d))
	// precedence: * binds tighter than +
	eq(t, "precedence", 1, matchCount(t, "[?(@.x + 2 * 3 == 7)]", d))
}

// Verifies: Filters and Scripts — bare-path predicates test existence.
func TestFilterBarePathExistence(t *testing.T) {
	d := []any{
		map[string]any{"x": false},
		map[string]any{"x": true},
		map[string]any{"x": 0},
		map[string]any{"x": nil},
		map[string]any{"y": 1},
	}
	eq(t, "bare path counts stored false/0/nil", 4, matchCount(t, "[?(@.x)]", d))
	eq(t, "negated bare path", 1, matchCount(t, "[?(!@.x)]", d))
	eq(t, "at itself", 5, matchCount(t, "[?(@)]", d))
}

// Verifies: Filters and Scripts — exists and has operators.
func TestFilterExistsHas(t *testing.T) {
	d := filterDocs()
	eq(t, "exists true", 2, matchCount(t, "[?(@.x exists true)]", d))
	eq(t, "exists false", 1, matchCount(t, "[?(@.x exists false)]", d))
	eq(t, "has true", 2, matchCount(t, "[?(@.x has true)]", d))
	eq(t, "has false", 1, matchCount(t, "[?(@.x has false)]", d))
}

// Verifies: Filters and Scripts — null vs Nothing vs missing.
func TestFilterNullAndNothing(t *testing.T) {
	d := filterDocs()
	eq(t, "null matches stored nil", 1, matchCount(t, "[?(@.n == null)]", d))
	eq(t, "null does not match missing", 0, matchCount(t, "[?(@.zz == null)]", d))
	eq(t, "Nothing matches missing x", 1, matchCount(t, "[?(@.x == Nothing)]", d))
}

// Verifies: Filters and Scripts — membership with in.
func TestFilterIn(t *testing.T) {
	d := filterDocs()
	eq(t, "string membership", 2, matchCount(t, "[?(@.s in ['abc','xyz'])]", d))
	eq(t, "number membership", 1, matchCount(t, "[?(@.x in [2,5])]", d))
	eq(t, "no member", 0, matchCount(t, "[?(@.s in ['qq'])]", d))
}

// Verifies: Filters and Scripts — emptiness operator.
func TestFilterEmpty(t *testing.T) {
	d := []any{
		map[string]any{"s": "", "l": []any{}, "m": map[string]any{}},
		map[string]any{"s": "ab", "l": []any{1}, "m": map[string]any{"k": 1}},
	}
	eq(t, "empty string", 1, matchCount(t, "[?(@.s empty true)]", d))
	eq(t, "empty slice", 1, matchCount(t, "[?(@.l empty true)]", d))
	eq(t, "empty map", 1, matchCount(t, "[?(@.m empty true)]", d))
	eq(t, "non-empty slice", 1, matchCount(t, "[?(@.l empty false)]", d))
}

// Verifies: Filters and Scripts — regex operator forms.
func TestFilterRegex(t *testing.T) {
	d := filterDocs()
	eq(t, "regex literal", 2, matchCount(t, "[?(@.s ~= /ab./)]", d))
	eq(t, "string pattern", 2, matchCount(t, "[?(@.s ~= 'ab')]", d))
	eq(t, "alt spelling accepted", 2, matchCount(t, "[?(@.s =~ /ab./)]", d))
	eq(t, "no match", 0, matchCount(t, "[?(@.s ~= /zz9/)]", d))
}

// Verifies: Filters and Scripts — length and count functions.
func TestFilterLengthCount(t *testing.T) {
	d := filterDocs()
	eq(t, "length of strings", 3, matchCount(t, "[?(length(@.s) == 3)]", d))
	eq(t, "length of slice", 1, matchCount(t, "[?(length(@.l) == 2)]", d))
	eq(t, "length missing is no value", 0, matchCount(t, "[?(length(@.zz) == 0)]", d))
	cd := []any{map[string]any{"l": []any{1, 2, 3}}, map[string]any{"l": []any{1}}}
	eq(t, "count matches", 1, matchCount(t, "[?(count(@.l[*]) == 3)]", cd))
}

// Verifies: Filters and Scripts — match and search functions.
func TestFilterMatchSearch(t *testing.T) {
	d := []any{map[string]any{"s": "abc"}, map[string]any{"s": "zzz"}}
	eq(t, "match is whole-string", 0, matchCount(t, "[?(match(@.s, '^a'))]", d))
	eq(t, "match full pattern", 1, matchCount(t, "[?(match(@.s, 'a.c'))]", d))
	eq(t, "search is substring", 1, matchCount(t, "[?(search(@.s, 'b'))]", d))
}

// Verifies: Filters and Scripts — filters apply to map elements.
func TestFilterOnMap(t *testing.T) {
	d := map[string]any{"a": map[string]any{"x": 1}, "b": map[string]any{"x": 2}}
	eqSet(t, "map filter", []any{map[string]any{"x": 2}}, mustParse(t, "$[?(@.x > 1)]").Get(d))
	eqSet(t, "map filter then child", []any{1, 2}, mustParse(t, "$[?(@.x > 0)].x").Get(d))
}
