// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"
)

func TestNumericPredicatePositions(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[1]/@id"), []string{"@id=b1"}, "[1]")
	wantSlice(t, selDesc(t, doc, "//book[2]/@id"), []string{"@id=b2"}, "[2]")
	wantSlice(t, selDesc(t, doc, "//book[3]/@id"), []string{"@id=b3"}, "[3]")
}

func TestNumericPredicateTruncation(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[1.2]/@id"), []string{"@id=b1"}, "[1.2]")
	wantSlice(t, selDesc(t, doc, "//book[1.9]/@id"), []string{"@id=b1"}, "[1.9]")
	wantSlice(t, selDesc(t, doc, "//book[2.5]/@id"), []string{"@id=b2"}, "[2.5]")
	wantSlice(t, selDesc(t, doc, "//book[3.99]/@id"), []string{"@id=b3"}, "[3.99]")
}

func TestNumericPredicateOutOfRange(t *testing.T) {
	doc := bookstore()
	// Guard: an in-range position matches.
	wantSlice(t, selDesc(t, doc, "//book[1]/@id"), []string{"@id=b1"}, "guard [1]")
	for _, expr := range []string{"//book[0]", "//book[-1]", "//book[4]"} {
		if got := selDesc(t, doc, expr); len(got) != 0 {
			t.Fatalf("%s matched %v, want nothing", expr, got)
		}
	}
}

func TestPositionFunction(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[position()=2]/@id"),
		[]string{"@id=b2"}, "position()=2")
	wantSlice(t, selDesc(t, doc, "//book[position()<3]/@id"),
		[]string{"@id=b1", "@id=b2"}, "position()<3")
	wantSlice(t, selDesc(t, doc, "//book[position() mod 2 = 1]/@id"),
		[]string{"@id=b1", "@id=b3"}, "position() mod 2 = 1")
}

func TestLastFunction(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[last()]/@id"), []string{"@id=b3"}, "[last()]")
	wantSlice(t, selDesc(t, doc, "//book[last()-1]/@id"), []string{"@id=b2"}, "[last()-1]")
}

func TestTopLevelPositionAndLast(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "position()", 1)
	wantNum(t, doc, "last()", 1)
}

func TestReverseAxisPositionCountsOutward(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[3]/preceding-sibling::book[1]/@id"),
		[]string{"@id=b2"}, "nearest preceding sibling")
	wantSlice(t, selDesc(t, doc, "//book[3]/preceding-sibling::book[2]/@id"),
		[]string{"@id=b1"}, "second-nearest preceding sibling")
}

func TestStackedPredicates(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[year=2005][2]/@id"),
		[]string{"@id=b2"}, "second node passing the first predicate")
	wantSlice(t, selDesc(t, doc, "//book[2][1]/@id"),
		[]string{"@id=b2"}, "[2][1]")
	if got := selDesc(t, doc, "//book[1][2]/@id"); len(got) != 0 {
		t.Fatalf("[1][2] matched %v, want nothing (one node remains after [1])", got)
	}
}

func TestAttributeAxisPositions(t *testing.T) {
	doc := bookstore()
	// Every attribute sits at position 1 of its own context.
	wantSlice(t, selDesc(t, doc, "//book[1]/@*[1]"),
		[]string{"@id=b1", "@category=cooking"}, "@*[1] keeps all attributes")
	if got := selDesc(t, doc, "//book[1]/@*[2]"); len(got) != 0 {
		t.Fatalf("@*[2] matched %v, want nothing", got)
	}
	if got := selDesc(t, doc, "//@*[position()=2]"); len(got) != 0 {
		t.Fatalf("//@*[position()=2] matched %v, want nothing", got)
	}
	// Guard: the attributes are all reachable.
	wantNum(t, doc, "count(//@*)", 10)
}

func TestParenthesizedNodeSetPositions(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selValues(t, doc, "(//author)[2]"),
		[]string{"J K. Rowling"}, "(//author)[2]")
	wantSlice(t, selValues(t, doc, "(//author)[last()]"),
		[]string{"Per Bothner"}, "(//author)[last()]")
}

func TestExistenceAndAttributePredicates(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[title]/@id"),
		[]string{"@id=b1", "@id=b2", "@id=b3"}, "[title] existence")
	wantSlice(t, selDesc(t, doc, "//book[@category='web']/@id"),
		[]string{"@id=b3"}, "[@category='web']")
	wantSlice(t, selDesc(t, doc, "//book[@id='b1' or @id='b3']/@id"),
		[]string{"@id=b1", "@id=b3"}, "or predicate")
	wantSlice(t, selDesc(t, doc, "//book[@id='b1' and @category='cooking']/@id"),
		[]string{"@id=b1"}, "and predicate")
}

func TestContentComparisonPredicates(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[price>30]/@id"),
		[]string{"@id=b3"}, "[price>30]")
	wantSlice(t, selDesc(t, doc, "//book[author='Per Bothner']/@id"),
		[]string{"@id=b3"}, "[author='...']")
	wantSlice(t, selDesc(t, doc, "//author[.='Per Bothner']"),
		[]string{"author"}, "[.='...']")
	wantSlice(t, selDesc(t, doc, "//book[count(author)=2]/@id"),
		[]string{"@id=b3"}, "[count(author)=2]")
}

func TestNumericExpressionInsidePredicates(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[position()*2=2]/@id"),
		[]string{"@id=b1"}, "position()*2=2")
	wantSlice(t, selDesc(t, doc, "//book[position() + 1 = 3]/@id"),
		[]string{"@id=b2"}, "position()+1=3")
	wantSlice(t, selDesc(t, doc, "//book[price * 2 > 59]/@id"),
		[]string{"@id=b1", "@id=b2", "@id=b3"}, "price*2>59")
}

func TestConstantTruthPredicates(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book['x']/@id"),
		[]string{"@id=b1", "@id=b2", "@id=b3"}, "non-empty string constant keeps all")
	wantSlice(t, selDesc(t, doc, "//book[true()]/@id"),
		[]string{"@id=b1", "@id=b2", "@id=b3"}, "[true()]")
}
