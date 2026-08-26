// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"
)

func TestCountFunction(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "count(//book)", 3)
	wantNum(t, doc, "count(//book/author)", 4)
	wantNum(t, doc, "count(//book/author[2])", 1)
	wantNum(t, doc, "count(//@lang)", 3)
}

func TestSumNumericNodes(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "sum(//price)", 109.97999999999999)
	wantNum(t, doc, "sum(//year)", 6013)
}

func TestSumSkipsNonNumericNodes(t *testing.T) {
	doc := bookstore()
	// Guard: a numeric sum on the same document is non-zero.
	wantNum(t, doc, "sum(//year)", 6013)
	wantNum(t, doc, "sum(//author)", 0)
	wantNum(t, doc, "sum(//nothing)", 0)
}

func TestReverseFunction(t *testing.T) {
	doc := bookstore()
	it := compileOK(t, "reverse(//book/@id)").Select(newNav(doc))
	var got []string
	for it.MoveNext() {
		got = append(got, it.Current().Value())
	}
	wantSlice(t, got, []string{"b3", "b2", "b1"}, "reverse(//book/@id)")
}

func TestNameAndLocalName(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "name(//book[1])", "book")
	wantStr(t, doc, "local-name(//book[1])", "book")
	wantStr(t, doc, "name(//book[1]/@id)", "id")
	wantStr(t, doc, "name(//book[9])", "")
	wantStr(t, doc, "local-name(//book[9])", "")
}

func TestZeroArgContextFunctions(t *testing.T) {
	doc := bookstore()
	n := newNav(doc)
	n.MoveToChild() // bookstore
	n.MoveToChild() // book 1
	evalAt := func(expr string) interface{} {
		t.Helper()
		return compileOK(t, expr).Evaluate(n.Copy())
	}
	if got := evalAt("string()"); got != "Everyday ItalianGiada De Laurentiis200530.00" {
		t.Fatalf("string() = %#v", got)
	}
	if got := evalAt("normalize-space()"); got != "Everyday ItalianGiada De Laurentiis200530.00" {
		t.Fatalf("normalize-space() = %#v", got)
	}
	if got := evalAt("name()"); got != "book" {
		t.Fatalf("name() = %#v, want book", got)
	}
	if got := evalAt("local-name()"); got != "book" {
		t.Fatalf("local-name() = %#v, want book", got)
	}
}

func TestTrueFalseNot(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "true()", true)
	wantBool(t, doc, "false()", false)
	wantBool(t, doc, "not(true())", false)
	wantBool(t, doc, "not(false())", true)
	wantBool(t, doc, "not(//nope)", true)
	wantBool(t, doc, "not(//book)", false)
}

func TestNotOnStringsAndNumbersIsFalse(t *testing.T) {
	doc := bookstore()
	// Guard: not() on booleans and node-sets negates.
	wantBool(t, doc, "not(false())", true)
	wantBool(t, doc, "not('')", false)
	wantBool(t, doc, "not(0)", false)
}

func TestFloorCeiling(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "floor(2.7)", 2)
	wantNum(t, doc, "ceiling(2.1)", 3)
}

func TestRoundHalfTowardPositiveInfinity(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "round(2.5)", 3)
	wantNum(t, doc, "round(-2.5)", -2)
	wantNum(t, doc, "round(1.5)", 2)
	wantNum(t, doc, "round(2.4)", 2)
	wantNum(t, doc, "round(-2.6)", -3)
	wantNaN(t, doc, "round(0 div 0)")
}

func TestConcatFunction(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "concat('a', 'b', 'c')", "abc")
	wantStr(t, doc, "concat('n=', count(//book))", "n=3")
	wantStr(t, doc, "concat(//book[1]/title, '!')", "Everyday Italian!")
	wantStr(t, doc, "concat('x', //book[9])", "x")
	wantStr(t, doc, `concat("a", 'b')`, "ab")
}

func TestAffixFunctions(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "starts-with('abc', 'ab')", true)
	wantBool(t, doc, "starts-with('abc', 'b')", false)
	wantBool(t, doc, "ends-with('abc', 'bc')", true)
	wantBool(t, doc, "ends-with('abc', 'ab')", false)
	wantBool(t, doc, "contains('abc', 'b')", true)
	wantBool(t, doc, "contains('abc', 'x')", false)
}

func TestAffixEmptyString(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "starts-with('abc', '')", true)
	wantBool(t, doc, "contains('abc', '')", true)
}

func TestSubstringBasics(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "substring('12345', 2)", "2345")
	wantStr(t, doc, "substring('12345', 2, 3)", "234")
	wantStr(t, doc, "substring('abc', 1, 1)", "a")
	wantStr(t, doc, "substring('12345', 0)", "12345")
}

func TestSubstringRoundsBounds(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "substring('12345', 1.5, 2.6)", "234")
	wantStr(t, doc, "substring('12345', 2, 2.4)", "23")
}

func TestSubstringBoundaries(t *testing.T) {
	doc := bookstore()
	// Guard: an in-range extraction is non-empty.
	wantStr(t, doc, "substring('abc', 2)", "bc")
	wantStr(t, doc, "substring('abc', 4)", "")
	wantStr(t, doc, "substring('abc', 2, 0)", "")
	wantStr(t, doc, "substring('abc', 2, -1)", "")
	wantStr(t, doc, "substring('abc', -1 div 0)", "abc")
}

func TestSubstringBeforeAfter(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "substring-before('a-b', '-')", "a")
	wantStr(t, doc, "substring-after('a-b', '-')", "b")
	wantStr(t, doc, "substring-before('abc', 'x')", "")
	wantStr(t, doc, "substring-after('abc', 'x')", "")
	wantStr(t, doc, "substring-before('abc', '')", "")
	wantStr(t, doc, "substring-after('abc', '')", "")
}

func TestStringLength(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "string-length('abc')", 3)
	wantNum(t, doc, "string-length('')", 0)
	wantNum(t, doc, "string-length(//book[1]/title)", 16)
	wantNum(t, doc, "string-length(//comment())", 11)
}

func TestNormalizeSpace(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "normalize-space('  a  b  ')", "a b")
	wantStr(t, doc, "normalize-space('\ta\nb  c\t')", "a b c")
}

func TestTranslate(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "translate('abc', 'abc', 'xyz')", "xyz")
	wantStr(t, doc, "translate('abc', 'ab', 'x')", "xc")
	wantStr(t, doc, "translate('aabbcc', 'abc', 'ab')", "aabb")
	wantStr(t, doc, "translate('abc', '', 'x')", "abc")
}

func TestLowerCase(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "lower-case('ABC')", "abc")
	wantStr(t, doc, "lower-case('MiXeD123')", "mixed123")
}

func TestMatchesFunction(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "matches('abc123', '[0-9]+')", true)
	wantBool(t, doc, "matches('abc', '^[0-9]+$')", false)
}

func TestReplaceFunction(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "replace('aaa', 'a', 'b')", "bbb")
	wantStr(t, doc, "replace('a1b2', '[0-9]', 'x')", "axbx")
}

func TestStringJoin(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "string-join(//book/@id, ',')", "b1,b2,b3")
	wantStr(t, doc, "string-join(reverse(//book/@id), '<')", "b3<b2<b1")
}

func TestStringOfElementIsDeepText(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "string(//book[1])",
		"Everyday ItalianGiada De Laurentiis200530.00")
	wantStr(t, doc, "string(//book[3])",
		"XQuery Kick StartJames McGovernPer Bothner200349.99")
	wantStr(t, doc, "normalize-space(//book[1])",
		"Everyday ItalianGiada De Laurentiis200530.00")
}

func TestStringAndNumberOfNodeSetUseFirstNode(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "string(//price)", "30.00")
	wantNum(t, doc, "number(//book[1]/price)", 30)
	wantStr(t, doc, "string(//comment())", "top comment")
}
