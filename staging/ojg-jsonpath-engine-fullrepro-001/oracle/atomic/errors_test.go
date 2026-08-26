package atomic

import (
	"testing"

	"github.com/ohler55/ojg/jp"
)

// Verifies: Error Semantics — unterminated fragments.
func TestErrNotTerminated(t *testing.T) {
	for src, msg := range map[string]string{
		"$[":   "not terminated at 3 in $[",
		"a.":   "not terminated at 3 in a.",
		"[?":   "not terminated at 3 in [?",
		"$.a[": "not terminated at 5 in $.a[",
	} {
		_, err := jp.ParseString(src)
		wantErr(t, src, err, msg)
	}
	// anchor: terminated input parses and evaluates
	eqVals(t, "anchor", []any{7}, mustParse(t, "$.limit").Get(store()))
}

// Verifies: Error Semantics — predicate operand and operator errors.
func TestErrPredicateTokens(t *testing.T) {
	_, err := jp.ParseString("[?(")
	wantErr(t, "empty operand", err, "'' is not a value or function at 4 in [?(")
	_, err = jp.ParseString("[?(@.n == nil)]")
	wantErr(t, "nil literal", err, "'nil' is not a value or function at 11 in [?(@.n == nil)]")
	_, err = jp.ParseString("a[?(@.x @ 3)]")
	wantErr(t, "bad operator", err, "'' is not a valid operation at 9 in a[?(@.x @ 3)]")
	_, err = jp.ParseString("a[?(@.x ==)]")
	wantErr(t, "missing right operand", err, "'' is not a value or function at 11 in a[?(@.x ==)]")
}

// Verifies: Error Semantics — bracket fragment errors.
func TestErrBracketFragments(t *testing.T) {
	_, err := jp.ParseString("$[1")
	wantErr(t, "unterminated number", err, "expected a number at 4 in $[1")
	_, err = jp.ParseString("['a'")
	wantErr(t, "unclosed after key", err, "invalid bracket fragment at 5 in ['a'")
	_, err = jp.ParseString("$['a]")
	wantErr(t, "unterminated quote", err, "invalid bracket fragment at 6 in $['a]")
	_, err = jp.ParseString("a[1:2:3:4]")
	wantErr(t, "four-part slice", err, "invalid slice syntax at 9 in a[1:2:3:4]")
	_, err = jp.ParseString("$['a',{}]")
	wantErr(t, "bad union member", err, "invalid union syntax at 8 in $['a',{}]")
}

// Verifies: Error Semantics — generic parse errors.
func TestErrGenericParse(t *testing.T) {
	for src, msg := range map[string]string{
		"a[b]": "parse error at 3 in a[b]",
		"$[=]": "parse error at 3 in $[=]",
		"!":    "parse error at 1 in !",
		"$!":   "parse error at 2 in $!",
	} {
		_, err := jp.ParseString(src)
		wantErr(t, src, err, msg)
	}
}

// Verifies: Error Semantics — fragment-start errors.
func TestErrFragmentStart(t *testing.T) {
	_, err := jp.ParseString("$.'x y'")
	wantErr(t, "quote after dot", err, "an expression fragment can not start with a ''' at 4 in $.'x y'")
	_, err = jp.ParseString("$.[1]")
	wantErr(t, "bracket after dot", err, "an expression fragment can not start with a '[' at 4 in $.[1]")
}

// Verifies: Error Semantics — Set ending-fragment rules.
func TestErrSetEndings(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	wantErr(t, "root", mustParse(t, "$").Set(d, 1),
		"can not set with an expression ending with a Root")
	wantErr(t, "filter", mustParse(t, "$.a[?(@ == 2)]").Set(d, 9),
		"can not set with an expression ending with a Filter")
	wantErr(t, "slice", mustParse(t, "$.a[0:2]").Set(d, 9),
		"can not set with an expression ending with a Slice")
	wantErr(t, "empty", mustParse(t, "").Set(d, 9),
		"can not set with an empty expression")
	eqVals(t, "unchanged", []any{1, 2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Error Semantics — Del ending-fragment rules.
func TestErrDelEndings(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	wantErr(t, "root", mustParse(t, "$").Del(d),
		"can not delete with an expression ending with a Root")
	wantErr(t, "slice", mustParse(t, "$.a[0:2]").Del(d),
		"can not delete with an expression ending with a Slice")
	wantErr(t, "filter", mustParse(t, "$.a[?(@ == 2)]").Del(d),
		"can not delete with an expression ending with a Filter")
	wantErr(t, "empty", mustParse(t, "").Del(d),
		"can not delete with an empty expression")
	eqVals(t, "unchanged", []any{1, 2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Error Semantics — Remove ending-fragment rules.
func TestErrRemoveEndings(t *testing.T) {
	d := map[string]any{"a": []any{1, 2, 3}}
	_, err := mustParse(t, "$").Remove(d)
	wantErr(t, "root", err, "can not remove with an expression where the last fragment is a Root")
	_, err = mustParse(t, "$..a").Remove(d)
	wantErr(t, "descent", err, "can not modify with an expression where the last fragment is a Descent")
	eqVals(t, "unchanged", []any{1, 2, 3}, mustParse(t, "$.a[*]").Get(d))
}

// Verifies: Error Semantics — follow errors name the kind and prefix.
func TestErrFollowKinds(t *testing.T) {
	d := map[string]any{"a": []any{1, 2}, "c": "str"}
	wantErr(t, "out of bounds", mustParse(t, "$.a[5]").Set(d, 1),
		"can not follow out of bounds array index at '$.a[5]'")
	wantErr(t, "through string", mustParse(t, "$.c[1]").Set(d, 1),
		"can not follow a string at '$.c'")
}

// Verifies: Error Semantics — Must panics mirror error texts.
func TestErrMustPanics(t *testing.T) {
	wantPanic(t, "MustRemove root",
		"can not remove with an expression where the last fragment is a Root", func() {
			jp.MustParseString("$").MustRemove(map[string]any{})
		})
	wantPanic(t, "MustDel filter",
		"can not delete with an expression ending with a Filter", func() {
			jp.MustParseString("$.a[?(@ == 2)]").MustDel(map[string]any{"a": []any{1, 2}})
		})
	wantPanic(t, "MustParseEquation",
		"equation not terminated at 7 in @.x ==", func() {
			jp.MustParseEquation("@.x ==")
		})
	wantPanic(t, "MustNewFilter",
		"a filter must start with a '[?' and end with ']'", func() {
			jp.MustNewFilter("nope")
		})
	wantPanic(t, "MustNewScript",
		"'' is not a valid operation at 6 in (@.x @@ 1)", func() {
			jp.MustNewScript("(@.x @@ 1)")
		})
}
