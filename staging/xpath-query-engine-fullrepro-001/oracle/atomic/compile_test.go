// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"

	"github.com/antchfx/xpath"
)

func TestCompileValidExpression(t *testing.T) {
	e, err := xpath.Compile("//book[1]")
	if err != nil {
		t.Fatalf("Compile returned error: %v", err)
	}
	if e == nil {
		t.Fatal("Compile returned nil expression")
	}
	if got := e.String(); got != "//book[1]" {
		t.Fatalf("String() = %q, want %q", got, "//book[1]")
	}
	// The compiled expression is immediately usable.
	it := e.Select(newNav(bookstore()))
	if !it.MoveNext() {
		t.Fatal("compiled expression selected nothing")
	}
	if got := it.Current().LocalName(); got != "book" {
		t.Fatalf("selected %q, want book", got)
	}
}

func TestStringReturnsExactSource(t *testing.T) {
	for _, src := range []string{
		"//book[1]",
		"count(//book) * 2",
		"concat('a', 'b')",
		"/bookstore/book[@id='b2']/title",
	} {
		if got := compileOK(t, src).String(); got != src {
			t.Fatalf("String() = %q, want the source %q", got, src)
		}
	}
	// The round-tripped expressions stay usable for evaluation.
	wantNum(t, bookstore(), "count(//book) * 2", 6)
}

func TestMustCompileValidMatchesCompile(t *testing.T) {
	doc := bookstore()
	e := xpath.MustCompile("//book/@id")
	if e == nil {
		t.Fatal("MustCompile returned nil for a valid expression")
	}
	it := e.Select(newNav(doc))
	var got []string
	for it.MoveNext() {
		got = append(got, it.Current().Value())
	}
	wantSlice(t, got, []string{"b1", "b2", "b3"}, "MustCompile select")
}

func TestMustCompileInvalidNoOp(t *testing.T) {
	doc := bookstore()
	e := xpath.MustCompile("///")
	if e == nil {
		t.Fatal("MustCompile returned nil for an invalid expression")
	}
	if got := e.String(); got != "///" {
		t.Fatalf("no-op String() = %q, want %q", got, "///")
	}
	it := e.Select(newNav(doc))
	if it == nil {
		t.Fatal("no-op Select returned nil iterator")
	}
	if it.MoveNext() {
		t.Fatal("no-op Select yielded a node")
	}
	if v := e.Evaluate(newNav(doc)); v != nil {
		t.Fatalf("no-op Evaluate = %#v, want nil", v)
	}
	// A valid expression on the same document does produce results.
	if got := evalNum(t, doc, "count(//book)"); got != 3 {
		t.Fatalf("count(//book) = %v, want 3", got)
	}
}

func TestCompileWithNSStringRoundTrip(t *testing.T) {
	e, err := xpath.CompileWithNS("count(//x:child)",
		map[string]string{"x": "http://example.com/ns"})
	if err != nil {
		t.Fatalf("CompileWithNS returned error: %v", err)
	}
	if got := e.String(); got != "count(//x:child)" {
		t.Fatalf("String() = %q, want %q", got, "count(//x:child)")
	}
	if got := e.Evaluate(newNav(nsDoc())).(float64); got != 1 {
		t.Fatalf("count(//x:child) = %v, want 1", got)
	}
}

func TestCompileWithNSUnboundPrefix(t *testing.T) {
	_, err := xpath.CompileWithNS("//y:item",
		map[string]string{"x": "http://example.com/ns"})
	if err == nil {
		t.Fatal("CompileWithNS accepted an unbound prefix")
	}
	if got := err.Error(); got != "prefix y not defined." {
		t.Fatalf("error = %q, want %q", got, "prefix y not defined.")
	}
	// The bound prefix compiles.
	if _, err := xpath.CompileWithNS("//x:item",
		map[string]string{"x": "http://example.com/ns"}); err != nil {
		t.Fatalf("bound prefix failed: %v", err)
	}
}

func TestPackageLevelSelect(t *testing.T) {
	doc := bookstore()
	it := xpath.Select(newNav(doc), "//book/@id")
	var got []string
	for it.MoveNext() {
		got = append(got, it.Current().Value())
	}
	wantSlice(t, got, []string{"b1", "b2", "b3"}, "package-level Select")
}

func TestPackageLevelSelectPanicsOnInvalid(t *testing.T) {
	doc := bookstore()
	// Guard: the same navigator works for a valid expression.
	if got := len(selValues(t, doc, "//book")); got != 3 {
		t.Fatalf("guard select found %d books, want 3", got)
	}
	defer func() {
		if recover() == nil {
			t.Fatal("package-level Select did not panic on an invalid expression")
		}
	}()
	xpath.Select(newNav(doc), "///")
}

func TestExprReuseAcrossDocuments(t *testing.T) {
	e := compileOK(t, "count(//book)")
	doc1 := bookstore()
	doc2 := newRoot()
	doc2.elem("bookstore").elem("book")
	if got := e.Evaluate(newNav(doc1)).(float64); got != 3 {
		t.Fatalf("doc1 count = %v, want 3", got)
	}
	if got := e.Evaluate(newNav(doc2)).(float64); got != 1 {
		t.Fatalf("doc2 count = %v, want 1", got)
	}
	if got := e.Evaluate(newNav(doc1)).(float64); got != 3 {
		t.Fatalf("doc1 count after reuse = %v, want 3", got)
	}
}

func TestSelectStartsIndependentTraversals(t *testing.T) {
	doc := bookstore()
	e := compileOK(t, "//book/@id")
	it1 := e.Select(newNav(doc))
	if !it1.MoveNext() {
		t.Fatal("first iterator yielded nothing")
	}
	if got := it1.Current().Value(); got != "b1" {
		t.Fatalf("first iterator first value = %q, want b1", got)
	}
	it2 := e.Select(newNav(doc))
	if !it2.MoveNext() {
		t.Fatal("second iterator yielded nothing")
	}
	if got := it2.Current().Value(); got != "b1" {
		t.Fatalf("second iterator restarts at %q, want b1", got)
	}
}

func TestCompileEmptyExpressionRejected(t *testing.T) {
	wantCompileErr(t, "", "expr expression is nil")
	_, err := xpath.CompileWithNS("", map[string]string{"x": "u"})
	if err == nil || err.Error() != "expr expression is nil" {
		t.Fatalf("CompileWithNS(\"\") error = %v, want %q", err, "expr expression is nil")
	}
}
