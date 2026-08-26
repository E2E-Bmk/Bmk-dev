// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"
)

func TestAbsolutePathFromRoot(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "/bookstore"), []string{"bookstore"}, "/bookstore")
	wantSlice(t, selDesc(t, doc, "/bookstore/book"),
		[]string{"book", "book", "book"}, "/bookstore/book")
}

func TestAbsolutePathIgnoresContextPosition(t *testing.T) {
	doc := bookstore()
	// Position a navigator at the second book.
	n := newNav(doc)
	n.MoveToChild() // bookstore
	n.MoveToChild() // book 1
	n.MoveToNext()  // book 2
	it := compileOK(t, "/bookstore/book[1]/title").Select(n)
	if !it.MoveNext() {
		t.Fatal("absolute path from mid-document context found nothing")
	}
	if got := it.Current().Value(); got != "Everyday Italian" {
		t.Fatalf("value = %q, want %q", got, "Everyday Italian")
	}
}

func TestRelativePathFromContext(t *testing.T) {
	doc := bookstore()
	n := newNav(doc)
	n.MoveToChild() // bookstore
	n.MoveToChild() // book 1
	n.MoveToNext()  // book 2
	run := func(expr string) []string {
		t.Helper()
		it := compileOK(t, expr).Select(n.Copy())
		var out []string
		for it.MoveNext() {
			out = append(out, it.Current().Value())
		}
		return out
	}
	wantSlice(t, run("title"), []string{"Harry Potter"}, "bare child step")
	wantSlice(t, run("./title"), []string{"Harry Potter"}, "dot-prefixed child step")
	wantSlice(t, run(".//text()"),
		[]string{"Harry Potter", "J K. Rowling", "2005", "29.99"}, "descendant text")
	wantSlice(t, run("@id"), []string{"b2"}, "attribute abbreviation")
}

func TestDescendantAbbreviation(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book"),
		[]string{"book", "book", "book"}, "//book")
	wantSlice(t, selDesc(t, doc, "//book/title"),
		[]string{"title", "title", "title"}, "//book/title")
}

func TestExplicitChildAndDescendantAxes(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "child::bookstore"), []string{"bookstore"}, "child::")
	wantSlice(t, selDesc(t, doc, "descendant::book"),
		[]string{"book", "book", "book"}, "descendant::")
	wantSlice(t, selDesc(t, doc, "//book[2]/descendant::text()"),
		[]string{"text:Harry Potter", "text:J K. Rowling", "text:2005", "text:29.99"},
		"descendant text of book 2")
}

func TestParentAxis(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//title/.."),
		[]string{"book", "book", "book"}, "//title/..")
	wantSlice(t, selDesc(t, doc, "//year/parent::book"),
		[]string{"book", "book", "book"}, "parent::book")
	wantSlice(t, selDesc(t, doc, "//title/../.."),
		[]string{"bookstore", "bookstore", "bookstore"}, "//title/../..")
}

func TestParentAxisReportsPerContext(t *testing.T) {
	// Three books share one parent; the parent step reports it three times.
	wantNum(t, bookstore(), "count(//bookstore/book/..)", 3)
}

func TestAncestorAxisSharedAncestorsReportedOnce(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//price[1]/ancestor::*"),
		[]string{"book", "bookstore", "book", "book"},
		"ancestor::* over three price contexts")
	wantSlice(t, selDesc(t, doc, "//year[1]/ancestor::*"),
		[]string{"book", "bookstore", "book", "book"},
		"ancestor::* over three year contexts")
}

func TestAncestorOrSelf(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//price[1]/ancestor-or-self::*"),
		[]string{"price", "book", "bookstore", "price", "book", "price", "book"},
		"ancestor-or-self::*")
}

func TestAncestorNumericPredicatePerContext(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//price[1]/ancestor::*[1]"),
		[]string{"book", "book", "book"}, "nearest ancestor of each price")
	wantSlice(t, selDesc(t, doc, "//price[1]/ancestor::*[2]"),
		[]string{"bookstore", "bookstore", "bookstore"},
		"second-nearest ancestor of each price")
}

func TestDescendantChainKeepsDuplicates(t *testing.T) {
	doc := nestedDivs()
	wantNum(t, doc, "count(//div)", 3)
	// From div1: div2, div3; from div2: div3 again — once per context.
	wantNum(t, doc, "count(//div//div)", 3)
	wantSlice(t, selDesc(t, doc, "//div//div"),
		[]string{"div", "div", "div"}, "//div//div")
}

func TestSiblingAxes(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[1]/following-sibling::*"),
		[]string{"book", "book"}, "following-sibling of book 1")
	wantSlice(t, selDesc(t, doc, "//book[3]/preceding-sibling::*"),
		[]string{"book", "book"}, "preceding-sibling of book 3")
	wantSlice(t, selDesc(t, doc, "//book[1]/following-sibling::*[1]/@id"),
		[]string{"@id=b2"}, "nearest following sibling")
}

func TestFollowingAxis(t *testing.T) {
	wantSlice(t, selDesc(t, bookstore(), "//book[2]/following::*"),
		[]string{"book", "title", "author", "author", "year", "price"},
		"following::* includes descendants of later siblings")
}

func TestPrecedingAxisExcludesAncestors(t *testing.T) {
	wantSlice(t, selDesc(t, bookstore(), "//book[2]/preceding::*"),
		[]string{"book", "title", "author", "year", "price"},
		"preceding::* is book 1's subtree, not bookstore")
}

func TestSelfAxis(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book[1]/self::book"), []string{"book"}, "self::book")
	if got := selDesc(t, doc, "//book[1]/self::title"); len(got) != 0 {
		t.Fatalf("self::title matched %v, want nothing", got)
	}
}

func TestDescendantOrSelfInner(t *testing.T) {
	wantSlice(t, selDesc(t, bookstore(), "//book[2]/descendant-or-self::*"),
		[]string{"book", "title", "author", "year", "price"},
		"descendant-or-self::* of book 2")
}

func TestAttributeAxis(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book/@id"),
		[]string{"@id=b1", "@id=b2", "@id=b3"}, "//book/@id")
	wantSlice(t, selDesc(t, doc, "//book[1]/attribute::id"),
		[]string{"@id=b1"}, "attribute::id")
	wantSlice(t, selDesc(t, doc, "//book[1]/@*"),
		[]string{"@id=b1", "@category=cooking"}, "@* in declaration order")
	wantSlice(t, selDesc(t, doc, "//bookstore/@specialty"),
		[]string{"@specialty=novel"}, "root element attribute")
}

func TestAttributeParentIsOwningElement(t *testing.T) {
	wantSlice(t, selDesc(t, bookstore(), "//book[1]/@id/.."),
		[]string{"book"}, "parent of an attribute")
}

func TestWildcardElementTest(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "count(//*)", 17)
	wantSlice(t, selDesc(t, doc, "/bookstore/*"),
		[]string{"book", "book", "book"}, "/bookstore/*")
}

func TestNodeTypeTests(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "/bookstore/child::node()"),
		[]string{"book", "book", "book", "comment:top comment"},
		"child::node() spans elements and comments")
	wantSlice(t, selDesc(t, doc, "//comment()"),
		[]string{"comment:top comment"}, "//comment()")
	wantNum(t, doc, "count(//text())", 13)
	wantNum(t, doc, "count(//node())", 31)
	wantSlice(t, selValues(t, doc, "//title/text()"),
		[]string{"Everyday Italian", "Harry Potter", "XQuery Kick Start"},
		"//title/text()")
}

func TestDoubleSlashBetweenSteps(t *testing.T) {
	doc := bookstore()
	wantNum(t, doc, "count(//book//text())", 13)
	wantSlice(t, selDesc(t, doc, "/bookstore//price"),
		[]string{"price", "price", "price"}, "/bookstore//price")
	wantSlice(t, selDesc(t, doc, "//book[1]//node()"),
		[]string{"title", "text:Everyday Italian", "author", "text:Giada De Laurentiis",
			"year", "text:2005", "price", "text:30.00"},
		"//book[1]//node()")
}

func TestExpressionReuseAcrossNavigatorFlavors(t *testing.T) {
	doc := bookstore()
	e := compileOK(t, "count(//book)")
	if got := e.Evaluate(newNav(doc)).(float64); got != 3 {
		t.Fatalf("count via nav = %v, want 3", got)
	}
	if got := e.Evaluate(newPlainNav(doc)).(float64); got != 3 {
		t.Fatalf("count via plain navigator = %v, want 3", got)
	}
}
