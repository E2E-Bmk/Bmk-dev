// Spec2Repo oracle - integration tests for xpath-query-engine-fullrepro-001
package integration

import (
	"fmt"
	"strings"
	"testing"

	"github.com/antchfx/xpath"
)

const exampleNSI = "http://example.com/ns"

// pathCorpus is the node-set expression corpus shared by the invariant
// sweeps. Every entry compiles; some select nothing on the bookstore
// document (the sweeps assert emptiness agreement for those).
var pathCorpus = []string{
	"//book",
	"//book/@id",
	"/bookstore/book[2]/title",
	"//author",
	"//book[price>30]/@id",
	"//text()",
	"//comment()",
	"//book[1]/@*",
	"//title | //price",
	"(//author)[last()]",
	"//nothing",
	"//book[0]",
}

// collect drains an iterator into descriptors.
func collect(t *testing.T, it *xpath.NodeIterator) []string {
	t.Helper()
	var out []string
	for it.MoveNext() {
		out = append(out, desc(it.Current()))
	}
	return out
}

func TestStringRoundTripAcrossCompilers(t *testing.T) {
	doc := bookstore()
	total := 0
	for _, src := range pathCorpus {
		if got := compileOK(t, src).String(); got != src {
			t.Fatalf("Compile String() = %q, want %q", got, src)
		}
		if got := xpath.MustCompile(src).String(); got != src {
			t.Fatalf("MustCompile String() = %q, want %q", got, src)
		}
		total += len(selDesc(t, doc, src))
	}
	nsSrc := "count(//x:child)"
	e, err := xpath.CompileWithNS(nsSrc, map[string]string{"x": exampleNSI})
	if err != nil {
		t.Fatalf("CompileWithNS: %v", err)
	}
	if got := e.String(); got != nsSrc {
		t.Fatalf("CompileWithNS String() = %q, want %q", got, nsSrc)
	}
	if total < 20 {
		t.Fatalf("corpus selected only %d nodes in total, expected at least 20", total)
	}
}

func TestStringRoundTripOnNoOpExpressions(t *testing.T) {
	doc := bookstore()
	for _, src := range []string{"///", "book[", "1 +"} {
		e := xpath.MustCompile(src)
		if got := e.String(); got != src {
			t.Fatalf("no-op String() = %q, want %q", got, src)
		}
		if e.Select(newNav(doc)).MoveNext() {
			t.Fatalf("no-op expression %q yielded a node", src)
		}
	}
	// Guard: a valid source both round-trips and selects.
	e := xpath.MustCompile("//book")
	if e.String() != "//book" || !e.Select(newNav(doc)).MoveNext() {
		t.Fatal("valid MustCompile expression failed to round-trip and select")
	}
}

func TestEvaluateSelectAgreement(t *testing.T) {
	doc := bookstore()
	total := 0
	for _, src := range pathCorpus {
		e := compileOK(t, src)
		fromSelect := collect(t, e.Select(newNav(doc)))
		v := e.Evaluate(newNav(doc))
		it, ok := v.(*xpath.NodeIterator)
		if !ok {
			t.Fatalf("Evaluate(%q) returned %T, want *xpath.NodeIterator", src, v)
		}
		fromEvaluate := collect(t, it)
		wantSlice(t, fromEvaluate, fromSelect, "Evaluate vs Select for "+src)
		total += len(fromSelect)
	}
	if total < 20 {
		t.Fatalf("corpus selected only %d nodes in total, expected at least 20", total)
	}
}

func TestCountAgreesWithIteration(t *testing.T) {
	doc := bookstore()
	nonEmpty := 0
	for _, src := range pathCorpus {
		n := len(selDesc(t, doc, src))
		if got := evalNum(t, doc, fmt.Sprintf("count(%s)", src)); got != float64(n) {
			t.Fatalf("count(%s) = %v, iteration yielded %d", src, got, n)
		}
		if n > 0 {
			nonEmpty++
		}
	}
	if nonEmpty < 8 {
		t.Fatalf("only %d corpus paths were non-empty, expected at least 8", nonEmpty)
	}
}

func TestBooleanAgreesWithNonEmptiness(t *testing.T) {
	doc := bookstore()
	nonEmpty := 0
	for _, src := range pathCorpus {
		n := len(selDesc(t, doc, src))
		want := n > 0
		if got := evalBool(t, doc, fmt.Sprintf("boolean(%s)", src)); got != want {
			t.Fatalf("boolean(%s) = %v with %d selected nodes", src, got, n)
		}
		if got := evalBool(t, doc, fmt.Sprintf("not(%s)", src)); got != !want {
			t.Fatalf("not(%s) = %v with %d selected nodes", src, got, n)
		}
		if want {
			nonEmpty++
		}
	}
	if nonEmpty < 8 {
		t.Fatalf("only %d corpus paths were non-empty, expected at least 8", nonEmpty)
	}
}

func TestStringAgreesWithFirstValue(t *testing.T) {
	doc := bookstore()
	nonEmpty := 0
	for _, src := range pathCorpus {
		it := compileOK(t, src).Select(newNav(doc))
		want := ""
		if it.MoveNext() {
			want = it.Current().Value()
			nonEmpty++
		}
		if got := evalStr(t, doc, fmt.Sprintf("string(%s)", src)); got != want {
			t.Fatalf("string(%s) = %q, first selected value is %q", src, got, want)
		}
	}
	if nonEmpty < 8 {
		t.Fatalf("only %d corpus paths were non-empty, expected at least 8", nonEmpty)
	}
}

func TestReuseAcrossDocumentsAndNavigators(t *testing.T) {
	store := bookstore()
	divs := nestedDivs()
	e := compileOK(t, "count(//div)")
	if got := e.Evaluate(newNav(divs)).(float64); got != 3 {
		t.Fatalf("divs count = %v, want 3", got)
	}
	if got := e.Evaluate(newNav(store)).(float64); got != 0 {
		t.Fatalf("bookstore div count = %v, want 0", got)
	}
	if got := e.Evaluate(newNav(divs)).(float64); got != 3 {
		t.Fatalf("divs count after other document = %v, want 3", got)
	}
	if got := e.Evaluate(newPlainNav(divs)).(float64); got != 3 {
		t.Fatalf("divs count via plain navigator = %v, want 3", got)
	}
}

func TestReuseInterleavedSelectEvaluate(t *testing.T) {
	doc := bookstore()
	e := compileOK(t, "//book/@id")
	first := collect(t, e.Select(newNav(doc)))
	wantSlice(t, first, []string{"@id=b1", "@id=b2", "@id=b3"}, "first pass")
	it := e.Evaluate(newNav(doc)).(*xpath.NodeIterator)
	if !it.MoveNext() {
		t.Fatal("evaluate pass yielded nothing")
	}
	// A half-consumed Evaluate iterator does not disturb a fresh Select.
	second := collect(t, e.Select(newNav(doc)))
	wantSlice(t, second, first, "second pass after interleaved Evaluate")
}

func TestAdoptionIdentityAcrossCorpus(t *testing.T) {
	doc := bookstore()
	checked := 0
	for _, src := range []string{"//book", "//book/@id", "//text()"} {
		n := newNav(doc)
		it := compileOK(t, src).Select(n)
		for it.MoveNext() {
			if it.Current() != xpath.NodeNavigator(n) {
				t.Fatalf("%s: Current is not the adopted navigator", src)
			}
			checked++
		}
	}
	if checked < 15 {
		t.Fatalf("only %d matches checked, expected at least 15", checked)
	}
}

// noMoveNavI wraps nav with a MoveTo that always fails.
type noMoveNavI struct {
	*nav
}

func (n *noMoveNavI) MoveTo(other xpath.NodeNavigator) bool { return false }

func (n *noMoveNavI) Copy() xpath.NodeNavigator {
	c := *n.nav
	return &noMoveNavI{nav: &c}
}

func TestAdoptionCopyFallbackAgreement(t *testing.T) {
	doc := bookstore()
	for _, src := range []string{"//book/@id", "//title"} {
		viaNav := selValues(t, doc, src)
		it := compileOK(t, src).Select(&noMoveNavI{nav: newNav(doc)})
		var viaCopy []string
		for it.MoveNext() {
			viaCopy = append(viaCopy, it.Current().Value())
		}
		wantSlice(t, viaCopy, viaNav, "copy-fallback values for "+src)
		if len(viaCopy) == 0 {
			t.Fatalf("%s selected nothing", src)
		}
	}
}

func TestUnionSelfIdentity(t *testing.T) {
	doc := bookstore()
	nonEmpty := 0
	for _, src := range []string{"//book", "//book/@id", "//title", "//nothing"} {
		base := selDesc(t, doc, src)
		union := selDesc(t, doc, src+" | "+src)
		wantSlice(t, union, base, "P | P for "+src)
		if len(base) > 0 {
			nonEmpty++
		}
	}
	if nonEmpty < 3 {
		t.Fatalf("only %d non-empty union bases, expected at least 3", nonEmpty)
	}
}

func TestUnionSupersetAbsorbsSubset(t *testing.T) {
	doc := bookstore()
	wantSlice(t, selDesc(t, doc, "//book | //book[2]"),
		selDesc(t, doc, "//book"), "//book | //book[2]")
	wantNum(t, doc, "count(//book | //book[2])", 3)
	wantNum(t, doc, "count(//book[2] | //book)", 3)
}

func TestStringJoinReverseAgreement(t *testing.T) {
	doc := bookstore()
	checked := 0
	for _, src := range []string{"//book/@id", "//title", "//author"} {
		vals := selValues(t, doc, src)
		if len(vals) < 2 {
			t.Fatalf("%s selected %d nodes, need at least 2", src, len(vals))
		}
		var rev []string
		for i := len(vals) - 1; i >= 0; i-- {
			rev = append(rev, vals[i])
		}
		want := strings.Join(rev, ";")
		got := evalStr(t, doc, fmt.Sprintf("string-join(reverse(%s), ';')", src))
		if got != want {
			t.Fatalf("string-join(reverse(%s)) = %q, want %q", src, got, want)
		}
		checked++
	}
	if checked != 3 {
		t.Fatalf("checked %d paths, want 3", checked)
	}
}

func TestReverseTwiceRestoresOrder(t *testing.T) {
	doc := bookstore()
	want := strings.Join(selValues(t, doc, "//book/@id"), ",")
	if want == "" {
		t.Fatal("//book/@id selected nothing")
	}
	got := evalStr(t, doc, "string-join(reverse(reverse(//book/@id)), ',')")
	if got != want {
		t.Fatalf("double reverse join = %q, want %q", got, want)
	}
}

func TestNameAgreementAcrossNodes(t *testing.T) {
	doc := nsDoc()
	it := compileOK(t, "//*").Select(newNav(doc))
	k := 0
	for it.MoveNext() {
		k++
		c := it.Current()
		wantName := c.LocalName()
		if p := c.Prefix(); p != "" {
			wantName = p + ":" + c.LocalName()
		}
		gotName := evalStr(t, doc, fmt.Sprintf("name((//*)[%d])", k))
		if gotName != wantName {
			t.Fatalf("name((//*)[%d]) = %q, navigator reports %q", k, gotName, wantName)
		}
		gotLocal := evalStr(t, doc, fmt.Sprintf("local-name((//*)[%d])", k))
		if gotLocal != c.LocalName() {
			t.Fatalf("local-name((//*)[%d]) = %q, navigator reports %q",
				k, gotLocal, c.LocalName())
		}
	}
	if k != 3 {
		t.Fatalf("//* visited %d elements, want 3", k)
	}
}

func TestNameAgreementUnderCompileWithNS(t *testing.T) {
	doc := nsDoc()
	eName, err := xpath.CompileWithNS("name(//x:child)",
		map[string]string{"x": exampleNSI})
	if err != nil {
		t.Fatalf("CompileWithNS: %v", err)
	}
	if got := eName.Evaluate(newNav(doc)).(string); got != "ns:child" {
		t.Fatalf("name via URI-bound test = %q, want the node's own %q", got, "ns:child")
	}
	eLocal, err := xpath.CompileWithNS("local-name(//x:child)",
		map[string]string{"x": exampleNSI})
	if err != nil {
		t.Fatalf("CompileWithNS: %v", err)
	}
	if got := eLocal.Evaluate(newNav(doc)).(string); got != "child" {
		t.Fatalf("local-name via URI-bound test = %q, want %q", got, "child")
	}
}
