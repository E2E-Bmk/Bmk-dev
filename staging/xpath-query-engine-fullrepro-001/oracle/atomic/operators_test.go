// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"math"
	"testing"
)

func TestArithmeticPrecedence(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "1 + 2 * 3", 7)
	wantNum(t, doc, "2 * 3 + 4 * 5", 26)
	wantNum(t, doc, "(2 + 3) * 4", 20)
	wantNum(t, doc, "6 div 2 * 3", 9)
	wantNum(t, doc, "10 mod 4 mod 3", 2)
}

func TestUnaryMinus(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "2 - -3", 5)
	wantNum(t, doc, "- 2 + 10", 8)
	wantNum(t, doc, "-//book[1]/price", -30)
}

func TestDivAndMod(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "10 div 4", 2.5)
	wantNum(t, doc, "10 mod 3", 1)
	wantNum(t, doc, "-3 mod 2", -1)
}

func TestDivisionByZero(t *testing.T) {
	doc := bookstore()
	if got := evalNum(t, doc, "5 div 0"); !math.IsInf(got, 1) {
		t.Fatalf("5 div 0 = %v, want +Inf", got)
	}
	if got := evalNum(t, doc, "-5 div 0"); !math.IsInf(got, -1) {
		t.Fatalf("-5 div 0 = %v, want -Inf", got)
	}
	wantNaN(t, doc, "0 div 0")
}

func TestArithmeticStringCoercion(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "'3' + 4", 7)
	wantNaN(t, doc, "'a' + 1")
}

func TestArithmeticNodeSetCoercion(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "//price + 1", 31)
	wantNum(t, doc, "//book[1]/price * 2", 60)
	wantNum(t, doc, "//book[1]/price + //book[2]/price", 59.989999999999995)
}

func TestMultiplicationAfterCall(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "count(//book)*2", 6)
	wantNum(t, doc, "count(//book)*count(//author)", 12)
}

func TestEqualityStrings(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "'a' = 'a'", true)
	wantBool(t, doc, "'a' != 'a'", false)
	wantBool(t, doc, "'a' != 'b'", true)
}

func TestEqualityStringNumber(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "'1' = 1", true)
	wantBool(t, doc, "1 != 2", true)
	wantBool(t, doc, "2 != 2", false)
}

func TestRelationalNumeric(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "1 < 2", true)
	wantBool(t, doc, "2 <= 2", true)
	wantBool(t, doc, "3 >= 4", false)
	wantBool(t, doc, "1 >= 1", true)
	wantBool(t, doc, "'3' < 4", true)
	wantBool(t, doc, "'10' < '9'", false)
}

func TestRelationalNaNAlwaysFalse(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "'b' > 'a'", false)
	wantBool(t, doc, "'abc' < 1", false)
	// Guard: a parsable comparison is still true.
	wantBool(t, doc, "'3' < 4", true)
}

func TestNodeSetComparisonExistential(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "//book/@id = 'b2'", true)
	wantBool(t, doc, "//book/@id != 'b2'", true)
	wantBool(t, doc, "//price > 40", true)
	wantBool(t, doc, "//year = 2005", true)
	wantBool(t, doc, "'2005' = //year", true)
	wantNum(t, doc, "count(//book[year=2005])", 2)
}

func TestNodeSetVsNodeSetComparison(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "//book[1]/year = //book[2]/year", true)
	wantBool(t, doc, "//book[1]/year = //book[3]/year", false)
	wantBool(t, doc, "//price < //year", true)
	wantBool(t, doc, "//book[1]/author != //book[3]/author", true)
	wantBool(t, doc, "//book[1]/author = //book[2]/author", false)
}

func TestLogicalOperators(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "1 = 1 or 2 = 3 and 4 = 5", true)
	wantBool(t, doc, "(1 = 1 or 2 = 3) and 4 = 5", false)
	wantBool(t, doc, "0 or '0'", true)
	wantBool(t, doc, "'' or 0", false)
	wantBool(t, doc, "1 and 'x'", true)
}

func TestUnionConcatenationOrder(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//price | //book"),
		[]string{"price", "price", "price", "book", "book", "book"},
		"left operand first")
	wantSlice(t, selDesc(t, doc, "//book | //price"),
		[]string{"book", "book", "book", "price", "price", "price"},
		"operand order, not document order")
	wantSlice(t, selDesc(t, doc, "//book[2]/@id | //book[1]/@id"),
		[]string{"@id=b2", "@id=b1"}, "attribute union keeps operand order")
}

func TestUnionDeduplication(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//title | //title"),
		[]string{"title", "title", "title"}, "self union")
	wantNum(t, doc, "count(//book | //book[2])", 3)
}

func TestUnionNonNodeSetOperands(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book | 'x'"),
		[]string{"book", "book", "book"}, "string operand contributes nothing")
	if got := selDesc(t, doc, "1 | 2"); len(got) != 0 {
		t.Fatalf("1 | 2 yielded %v, want nothing", got)
	}
}

func TestUnionMixedNodeKinds(t *testing.T) {
	wantSlice(t, selDesc(t, bookstore(), "//book[1]/@id | //book[1]/title"),
		[]string{"@id=b1", "title"}, "attribute and element operands")
}

func TestUnionGroupedStep(t *testing.T) {
	wantSlice(t, selDesc(t, bookstore(), "(//book[1] | //book[2])/title"),
		[]string{"title", "title"}, "step applied to a grouped union")
}

func TestBooleanConversion(t *testing.T) {
	doc := bookstore()
	wantBool(t, doc, "boolean('')", false)
	wantBool(t, doc, "boolean('false')", true)
	wantBool(t, doc, "boolean('0')", true)
	wantBool(t, doc, "boolean(0)", false)
	wantBool(t, doc, "boolean(-1)", true)
	wantBool(t, doc, "boolean(0 div 0)", true)
	wantBool(t, doc, "boolean(//book)", true)
	wantBool(t, doc, "boolean(//nope)", false)
}

func TestNumberConversion(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "number(' 12 ')", 12)
	wantNum(t, doc, "number('1e2')", 100)
	wantNum(t, doc, "number('-.5')", -0.5)
	wantNum(t, doc, "number('12.')", 12)
	wantNaN(t, doc, "number('')")
	wantNaN(t, doc, "number('abc')")
	wantNum(t, doc, "number(true())", 1)
	wantNum(t, doc, "number(false())", 0)
	wantNum(t, doc, "number(//year)", 2005)
	wantNaN(t, doc, "number(//title)")
	wantNaN(t, doc, "number(//book[9])")
}

func TestStringConversionNumbers(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "string(12.0)", "12")
	wantStr(t, doc, "string(0.5)", "0.5")
	wantStr(t, doc, "string(-1.5)", "-1.5")
	wantStr(t, doc, "string(-0)", "0")
	wantStr(t, doc, "string(2 - 3)", "-1")
	wantStr(t, doc, "string(1 div 0)", "Infinity")
	wantStr(t, doc, "string(-1 div 0)", "-Infinity")
	wantStr(t, doc, "string(0 div 0)", "NaN")
	wantStr(t, doc, "string(0.1 + 0.2)", "0.30000000000000004")
	wantStr(t, doc, "string(0.0000001)", "0.0000001")
	wantStr(t, doc, "string(1000000000000000000000)", "1000000000000000000000")
}

func TestStringConversionBooleansAndNodeSets(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "string(true())", "true")
	wantStr(t, doc, "string(false())", "false")
	wantStr(t, doc, "string(//book/@id)", "b1")
	wantStr(t, doc, "string(//title)", "Everyday Italian")
	wantStr(t, doc, "string(//book[9])", "")
}
