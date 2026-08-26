// Spec2Repo oracle - integration tests for xpath-query-engine-fullrepro-001
package integration

import (
	"strings"
	"testing"

	"github.com/antchfx/xpath"
)

func TestWorkflowFilterAndExtract(t *testing.T) {
	doc := bookstore()
	e := compileOK(t, "//book[price > 29.99]/title")
	it := e.Select(newNav(doc))
	var titles []string
	for it.MoveNext() {
		titles = append(titles, it.Current().Value())
	}
	wantSlice(t, titles, []string{"Everyday Italian", "XQuery Kick Start"},
		"filtered titles")
	wantBool(t, doc, "boolean(//book[price > 29.99]/title)", true)
	wantNum(t, doc, "count(//book[price > 29.99]/title)", 2)
	wantStr(t, doc, "string(//book[price > 29.99]/title)", "Everyday Italian")
}

func TestWorkflowNamespaceDualNavigators(t *testing.T) {
	doc := nsDoc()
	e, err := xpath.CompileWithNS("//x:child", map[string]string{"x": exampleNSI})
	if err != nil {
		t.Fatalf("CompileWithNS: %v", err)
	}
	// Navigator with NamespaceURL: URI matching succeeds.
	it := e.Select(newNav(doc))
	if !it.MoveNext() {
		t.Fatal("URI matching found nothing on the extended navigator")
	}
	if got := it.Current().Value(); got != "v1" {
		t.Fatalf("value = %q, want v1", got)
	}
	// Navigator without NamespaceURL: same expression matches nothing.
	if e.Select(newPlainNav(doc)).MoveNext() {
		t.Fatal("URI matching succeeded on a navigator without NamespaceURL")
	}
	// The literal-prefix form works on both navigator flavors.
	lit := compileOK(t, "//ns:child")
	if !lit.Select(newNav(doc)).MoveNext() {
		t.Fatal("literal prefix failed on the extended navigator")
	}
	if !lit.Select(newPlainNav(doc)).MoveNext() {
		t.Fatal("literal prefix failed on the plain navigator")
	}
	// namespace-uri projects the URI or falls back to the prefix.
	uriExpr := compileOK(t, "namespace-uri(//ns:child)")
	if got := uriExpr.Evaluate(newNav(doc)).(string); got != exampleNSI {
		t.Fatalf("namespace-uri via extended navigator = %q, want %q", got, exampleNSI)
	}
	if got := uriExpr.Evaluate(newPlainNav(doc)).(string); got != "ns" {
		t.Fatalf("namespace-uri via plain navigator = %q, want the prefix ns", got)
	}
}

func TestWorkflowRelativeExploration(t *testing.T) {
	doc := bookstore()
	n := newNav(doc)
	if !n.MoveToChild() || !n.MoveToChild() || !n.MoveToNext() {
		t.Fatal("failed to walk the navigator to the second book")
	}
	run := func(expr string) []string {
		t.Helper()
		it := compileOK(t, expr).Select(n.Copy())
		var out []string
		for it.MoveNext() {
			out = append(out, it.Current().Value())
		}
		return out
	}
	wantSlice(t, run("title"), []string{"Harry Potter"}, "relative child")
	wantSlice(t, run("@id"), []string{"b2"}, "relative attribute")
	wantSlice(t, run(".//text()"),
		[]string{"Harry Potter", "J K. Rowling", "2005", "29.99"}, "relative descendants")
	wantSlice(t, run("/bookstore/book[1]/title"),
		[]string{"Everyday Italian"}, "absolute path from relative context")
	parent := run("..")
	if len(parent) != 1 || !strings.Contains(parent[0], "Harry Potter") {
		t.Fatalf("parent step returned %v, want the bookstore's full text", parent)
	}
}

func TestWorkflowAggregateReport(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "concat('ids=', string-join(//book/@id, '+'))", "ids=b1+b2+b3")
	wantStr(t, doc, "string-join(reverse(//title), ';')",
		"XQuery Kick Start;Harry Potter;Everyday Italian")
	wantNum(t, doc, "count(//book[year=2005])", 2)
	wantBool(t, doc, "sum(//price) > 100", true)
}

func TestWorkflowErrorRecovery(t *testing.T) {
	doc := bookstore()
	// A malformed expression reports the documented compile error.
	_, err := xpath.Compile("book[")
	if err == nil || err.Error() != "expression must evaluate to a node-set" {
		t.Fatalf("Compile error = %v, want %q", err, "expression must evaluate to a node-set")
	}
	// MustCompile downgrades the same failure to a no-op expression.
	noop := xpath.MustCompile("book[")
	if noop.String() != "book[" {
		t.Fatalf("no-op String() = %q", noop.String())
	}
	if noop.Select(newNav(doc)).MoveNext() {
		t.Fatal("no-op selected a node")
	}
	if v := noop.Evaluate(newNav(doc)); v != nil {
		t.Fatalf("no-op Evaluate = %#v, want nil", v)
	}
	// The package-level Select panics on the same input.
	func() {
		defer func() {
			if recover() == nil {
				t.Fatal("package-level Select did not panic")
			}
		}()
		xpath.Select(newNav(doc), "book[")
	}()
	// Recovery: a corrected expression works end to end.
	it := compileOK(t, "//book/@id").Select(newNav(doc))
	var ids []string
	for it.MoveNext() {
		ids = append(ids, it.Current().Value())
	}
	wantSlice(t, ids, []string{"b1", "b2", "b3"}, "recovered query")
}

func TestWorkflowDocumentEvolution(t *testing.T) {
	count := compileOK(t, "count(//book)")
	firstID := compileOK(t, "string(//book[1]/@id)")

	store := bookstore()
	if got := count.Evaluate(newNav(store)).(float64); got != 3 {
		t.Fatalf("store count = %v, want 3", got)
	}
	if got := firstID.Evaluate(newNav(store)).(string); got != "b1" {
		t.Fatalf("store first id = %q, want b1", got)
	}

	tiny := newRoot()
	tiny.elem("shelf").elem("book").attr("id", "solo")
	if got := count.Evaluate(newNav(tiny)).(float64); got != 1 {
		t.Fatalf("tiny count = %v, want 1", got)
	}
	if got := firstID.Evaluate(newNav(tiny)).(string); got != "solo" {
		t.Fatalf("tiny first id = %q, want solo", got)
	}

	divs := nestedDivs()
	if got := count.Evaluate(newNav(divs)).(float64); got != 0 {
		t.Fatalf("divs count = %v, want 0", got)
	}
	if got := firstID.Evaluate(newNav(divs)).(string); got != "" {
		t.Fatalf("divs first id = %q, want empty", got)
	}

	// Back to the first document: identical results.
	if got := count.Evaluate(newNav(store)).(float64); got != 3 {
		t.Fatalf("store count after evolution = %v, want 3", got)
	}
}
