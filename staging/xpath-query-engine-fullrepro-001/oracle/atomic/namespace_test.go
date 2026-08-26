// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"

	"github.com/antchfx/xpath"
)

const exampleNS = "http://example.com/ns"

func TestUnprefixedTestRequiresEmptyPrefix(t *testing.T) {
	doc := nsDoc()
	wantNum(t, doc, "count(//ns:child)", 1)
	wantNum(t, doc, "count(//child)", 0)
	wantNum(t, doc, "count(//plain)", 1)
}

func TestPrefixLiteralMatch(t *testing.T) {
	doc := nsDoc()
	it := compileOK(t, "//ns:child").Select(newNav(doc))
	if !it.MoveNext() {
		t.Fatal("//ns:child matched nothing")
	}
	c := it.Current()
	if got := c.LocalName(); got != "child" {
		t.Fatalf("local name = %q, want child", got)
	}
	if got := c.Prefix(); got != "ns" {
		t.Fatalf("prefix = %q, want ns", got)
	}
	if got := c.Value(); got != "v1" {
		t.Fatalf("value = %q, want v1", got)
	}
	if it.MoveNext() {
		t.Fatal("more than one match for //ns:child")
	}
}

func TestWildcardMatchesPrefixedElements(t *testing.T) {
	wantSlice(t, selDesc(t, nsDoc(), "//*"),
		[]string{"root", "child", "plain"}, "//* spans prefixed and plain")
}

func TestCompileWithNSMatchesByURI(t *testing.T) {
	doc := nsDoc()
	e, err := xpath.CompileWithNS("//x:child", map[string]string{"x": exampleNS})
	if err != nil {
		t.Fatalf("CompileWithNS: %v", err)
	}
	it := e.Select(newNav(doc))
	if !it.MoveNext() {
		t.Fatal("URI-bound test matched nothing")
	}
	if got := it.Current().Value(); got != "v1" {
		t.Fatalf("matched value = %q, want v1", got)
	}
	if it.MoveNext() {
		t.Fatal("more than one match")
	}
	// A different bound URI matches nothing.
	e2, err := xpath.CompileWithNS("//x:child", map[string]string{"x": "http://other"})
	if err != nil {
		t.Fatalf("CompileWithNS(other): %v", err)
	}
	if e2.Select(newNav(doc)).MoveNext() {
		t.Fatal("mismatched URI still matched")
	}
}

func TestCompileWithNSFallsBackWithoutExtension(t *testing.T) {
	doc := nsDoc()
	e, err := xpath.CompileWithNS("//x:child", map[string]string{"x": exampleNS})
	if err != nil {
		t.Fatalf("CompileWithNS: %v", err)
	}
	// The plain navigator has no NamespaceURL method; matching falls back
	// to literal prefix comparison, and prefix "x" matches no node.
	if e.Select(newPlainNav(doc)).MoveNext() {
		t.Fatal("URI-bound test matched via a navigator without NamespaceURL")
	}
	// The literal prefix still matches through the same navigator.
	it := compileOK(t, "//ns:child").Select(newPlainNav(doc))
	if !it.MoveNext() {
		t.Fatal("literal prefix match failed on plain navigator")
	}
	if got := it.Current().Value(); got != "v1" {
		t.Fatalf("value = %q, want v1", got)
	}
}

func TestNameQualifiedForm(t *testing.T) {
	doc := nsDoc()
	wantStr(t, doc, "name(//ns:child)", "ns:child")
	wantStr(t, doc, "local-name(//ns:child)", "child")
	wantStr(t, doc, "name(//plain)", "plain")
	wantStr(t, doc, "local-name(//plain)", "plain")
}

func TestNamespaceURIWithExtension(t *testing.T) {
	doc := nsDoc()
	wantStr(t, doc, "namespace-uri(//ns:child)", exampleNS)
	wantStr(t, doc, "namespace-uri(//plain)", "")
	// Empty node-set: empty string.
	wantStr(t, doc, "namespace-uri(//missing)", "")
}

func TestNamespaceURIFallbackReturnsPrefix(t *testing.T) {
	doc := nsDoc()
	e := compileOK(t, "namespace-uri(//ns:child)")
	v, ok := e.Evaluate(newPlainNav(doc)).(string)
	if !ok {
		t.Fatal("namespace-uri did not evaluate to a string")
	}
	if v != "ns" {
		t.Fatalf("namespace-uri via plain navigator = %q, want the prefix %q", v, "ns")
	}
}

func TestNameFunctionsOnNonElements(t *testing.T) {
	doc := bookstore()
	wantStr(t, doc, "name(/)", "")
	wantStr(t, doc, "local-name(/)", "")
	wantStr(t, doc, "name(//comment())", "")
	wantStr(t, doc, "name(//text()[1])", "")
	// Guard: a real element still reports its name.
	wantStr(t, doc, "name(//book[1])", "book")
}
