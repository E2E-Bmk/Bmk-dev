package atomic

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Path Expressions and Parsing — parse entry points.
func TestParseStringAndParseAgree(t *testing.T) {
	xs, err := jp.ParseString("$.inv[0].sku")
	wantNoErr(t, "ParseString", err)
	xb, err := jp.Parse([]byte("$.inv[0].sku"))
	wantNoErr(t, "Parse", err)
	eq(t, "String equality", xs.String(), xb.String())
	eqVals(t, "Get equality", []any{"A1"}, xb.Get(store()))
}

// Verifies: Path Expressions and Parsing — empty input.
func TestParseEmptyInput(t *testing.T) {
	x, err := jp.ParseString("")
	wantNoErr(t, "empty parse", err)
	eq(t, "empty length", 0, len(x))
	eq(t, "empty String", "", x.String())
	eqVals(t, "empty Get", nil, x.Get(store()))
	// anchor: a non-empty path on the same data produces a value
	eqVals(t, "anchor", []any{"main"}, mustParse(t, "$.name").Get(store()))
}

// Verifies: Path Expressions and Parsing — optional leading anchors.
func TestParseOptionalLeader(t *testing.T) {
	d := store()
	eqVals(t, "bare path", []any{"main"}, mustParse(t, "name").Get(d))
	eqVals(t, "rooted path", []any{"main"}, mustParse(t, "$.name").Get(d))
	eqVals(t, "at path", []any{"main"}, mustParse(t, "@.name").Get(d))
	eq(t, "bare len", 1, len(mustParse(t, "name")))
	eq(t, "rooted len", 2, len(mustParse(t, "$.name")))
}

// Verifies: Path Expressions and Parsing — digit-only dot token is a key.
func TestParseDigitDotTokenIsChild(t *testing.T) {
	x := mustParse(t, "a.0.b")
	eq(t, "String", "a.0.b", x.String())
	eq(t, "BracketString", "['a']['0']['b']", x.BracketString())
	d := map[string]any{"a": map[string]any{"0": map[string]any{"b": 9}}}
	eqVals(t, "string-key lookup", []any{9}, x.Get(d))
	eqVals(t, "no index lookup", nil, x.Get(map[string]any{"a": []any{map[string]any{"b": 1}}}))
}

// Verifies: Path Expressions and Parsing — bracket quoting and normalization.
func TestParseBracketQuoting(t *testing.T) {
	eq(t, "double quote normalizes", "$.q", mustParse(t, `$["q"]`).String())
	eq(t, "simple key drops brackets", "$.a", mustParse(t, "$[ 'a' ]").String())
	eq(t, "special key keeps brackets", "$['a-b']", mustParse(t, "$['a-b']").String())
	eq(t, "escaped quote kept", `$['a\'b']`, mustParse(t, `$['a\'b']`).String())
	d := map[string]any{"a-b": 5}
	eqVals(t, "special key lookup", []any{5}, mustParse(t, "$['a-b']").Get(d))
}

// Verifies: Path Expressions and Parsing — integer tokens.
func TestParseIntegerTokens(t *testing.T) {
	eq(t, "leading zeros normalize", "$[1]", mustParse(t, "$[01]").String())
	eq(t, "negative index", "$[-1]", mustParse(t, "$[-1]").String())
	eqVals(t, "negative index Get", []any{3}, mustParse(t, "$[-1]").Get([]any{1, 2, 3}))
	eqVals(t, "normalized index Get", []any{2}, mustParse(t, "$[01]").Get([]any{1, 2, 3}))
}

// Verifies: Path Expressions and Parsing — slice forms parse and render.
func TestParseSliceForms(t *testing.T) {
	for _, s := range []string{"$[1:3]", "$[1:3:2]", "$[::2]", "$[:2]", "$[1:]", "$[::-1]", "$[-2:-1]"} {
		x := mustParse(t, s)
		eq(t, "slice render "+s, s, x.String())
	}
	eqVals(t, "slice Get", []any{2, 3}, mustParse(t, "$[1:3]").Get([]any{1, 2, 3, 4}))
}

// Verifies: Path Expressions and Parsing — union forms.
func TestParseUnionForms(t *testing.T) {
	eq(t, "whitespace discarded", "$[1,2]", mustParse(t, "$[ 1 , 2 ]").String())
	eq(t, "mixed union", "$['a',2,'b']", mustParse(t, "$['a',2,'b']").String())
	eqVals(t, "union Get", []any{"str", 7},
		mustParse(t, "$['c','i']").Get(map[string]any{"c": "str", "i": 7}))
}

// Verifies: Path Expressions and Parsing — wildcard spellings.
func TestParseWildcardSpellings(t *testing.T) {
	eq(t, "dot form", "$.*", mustParse(t, "$.*").String())
	eq(t, "bracket form kept", "$[*]", mustParse(t, "$[*]").String())
	eq(t, "bare wildcard", "*", mustParse(t, "*").String())
	eqVals(t, "wildcard slice Get", []any{1, 2}, mustParse(t, "$[*]").Get([]any{1, 2}))
}

// Verifies: Path Expressions and Parsing — descent forms.
func TestParseDescentForms(t *testing.T) {
	x := mustParse(t, "$..b")
	eq(t, "descent String", "$..b", x.String())
	eq(t, "descent Bracket", "$[..]['b']", x.BracketString())
	eq(t, "descent len", 3, len(x))
	eqVals(t, "descent Get", []any{1},
		x.Get(map[string]any{"a": map[string]any{"b": 1}}))
	// trailing descent accepted
	tx := mustParse(t, "a..")
	eq(t, "trailing descent String", "a..", tx.String())
}

// Verifies: Path Expressions and Parsing — filter normalization at parse time.
func TestParseFilterNormalization(t *testing.T) {
	eq(t, "spacing added", "$[?(@.x == 1)]", mustParse(t, "$[?(@.x==1)]").String())
	eq(t, "spacing collapsed", "$[?(@.x == 1)]", mustParse(t, "$[?( @.x == 1 )]").String())
	eq(t, "double quotes normalize", "a[?(@.x == 'q')]", mustParse(t, `a[?(@.x == "q")]`).String())
	eq(t, "regex spelling normalizes", "[?(@ ~= /x/)]", mustParse(t, "[?(@ =~ /x/)]").String())
	eq(t, "exponent normalizes", "$[?(@.x > 100)]", mustParse(t, "$[?(@.x > 1e2)]").String())
	eq(t, "operators keep order", "$[?(3 < @.x)]", mustParse(t, "$[?(3 < @.x)]").String())
}

// Verifies: Path Expressions and Parsing — unicode and underscore dot keys.
func TestParseDotKeyCharset(t *testing.T) {
	eq(t, "underscore", "$.k_2", mustParse(t, "$.k_2").String())
	eq(t, "unicode", "$.日本", mustParse(t, "$.日本").String())
	eqVals(t, "unicode lookup", []any{1}, mustParse(t, "$.日本").Get(map[string]any{"日本": 1}))
}

// Verifies: Path Expressions and Parsing — MustParse panics on bad input.
func TestMustParsePanics(t *testing.T) {
	wantPanic(t, "MustParse", "not terminated at 3 in $[", func() {
		jp.MustParse([]byte("$["))
	})
	wantPanic(t, "MustParseString", "parse error at 3 in a[b]", func() {
		jp.MustParseString("a[b]")
	})
	// anchor: valid input does not panic and evaluates
	eqVals(t, "anchor", []any{7}, jp.MustParseString("$.limit").Get(store()))
}

// Verifies: Path Expressions and Parsing — bracketed key with space.
func TestParseSpacedKey(t *testing.T) {
	x := mustParse(t, "['x y']")
	eq(t, "String", "['x y']", x.String())
	eqVals(t, "lookup", []any{2}, x.Get(map[string]any{"x y": 2}))
	x2 := mustParse(t, "$.a[?(@['k 2'] > 1)]")
	eq(t, "filter spaced key", "$.a[?(@['k 2'] > 1)]", x2.String())
}
