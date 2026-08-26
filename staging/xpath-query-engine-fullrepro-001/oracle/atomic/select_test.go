// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"

	"github.com/antchfx/xpath"
)

func TestEvaluateNumericType(t *testing.T) {
	v := evalVal(t, bookstore(), "1 + 2 * 3")
	f, ok := v.(float64)
	if !ok {
		t.Fatalf("Evaluate returned %T, want float64", v)
	}
	if f != 7 {
		t.Fatalf("1 + 2 * 3 = %v, want 7", f)
	}
}

func TestEvaluateBooleanType(t *testing.T) {
	v := evalVal(t, bookstore(), "1 < 2")
	b, ok := v.(bool)
	if !ok {
		t.Fatalf("Evaluate returned %T, want bool", v)
	}
	if !b {
		t.Fatal("1 < 2 = false, want true")
	}
}

func TestEvaluateStringType(t *testing.T) {
	v := evalVal(t, bookstore(), "concat('a', 'b', 'c')")
	s, ok := v.(string)
	if !ok {
		t.Fatalf("Evaluate returned %T, want string", v)
	}
	if s != "abc" {
		t.Fatalf("concat = %q, want %q", s, "abc")
	}
}

func TestEvaluateNodeSetType(t *testing.T) {
	v := evalVal(t, bookstore(), "//book")
	it, ok := v.(*xpath.NodeIterator)
	if !ok {
		t.Fatalf("Evaluate returned %T, want *xpath.NodeIterator", v)
	}
	n := 0
	for it.MoveNext() {
		if got := it.Current().LocalName(); got != "book" {
			t.Fatalf("node %d local name = %q, want book", n, got)
		}
		n++
	}
	if n != 3 {
		t.Fatalf("iterator yielded %d nodes, want 3", n)
	}
}

func TestEvaluateEmptyNodeSetType(t *testing.T) {
	doc := bookstore()
	// Guard: a non-empty path yields nodes on this document.
	if got := len(selValues(t, doc, "//book")); got != 3 {
		t.Fatalf("guard found %d books, want 3", got)
	}
	v := evalVal(t, doc, "//nothing")
	it, ok := v.(*xpath.NodeIterator)
	if !ok {
		t.Fatalf("Evaluate returned %T, want *xpath.NodeIterator", v)
	}
	if it.MoveNext() {
		t.Fatal("empty node-set iterator yielded a node")
	}
}

func TestSelectOnNonNodeSetYieldsNothing(t *testing.T) {
	doc := bookstore()
	// Guard: Select over a real path yields nodes.
	if got := len(selValues(t, doc, "//book")); got != 3 {
		t.Fatalf("guard found %d books, want 3", got)
	}
	it := compileOK(t, "1+1").Select(newNav(doc))
	if it == nil {
		t.Fatal("Select returned nil iterator")
	}
	if it.MoveNext() {
		t.Fatal("Select over a numeric expression yielded a node")
	}
}

func TestIteratorCurrentBeforeMoveNext(t *testing.T) {
	doc := bookstore()
	n := newNav(doc)
	it := compileOK(t, "//book").Select(n)
	c := it.Current()
	if c == nil {
		t.Fatal("Current returned nil before MoveNext")
	}
	if got := c.NodeType(); got != xpath.RootNode {
		t.Fatalf("Current before MoveNext is at node type %v, want RootNode", got)
	}
	if !it.MoveNext() {
		t.Fatal("MoveNext found no first match")
	}
	if got := it.Current().LocalName(); got != "book" {
		t.Fatalf("first match = %q, want book", got)
	}
}

func TestIteratorExhaustion(t *testing.T) {
	doc := bookstore()
	it := compileOK(t, "//book/@id").Select(newNav(doc))
	n := 0
	for it.MoveNext() {
		n++
	}
	if n != 3 {
		t.Fatalf("yielded %d nodes, want 3", n)
	}
	if it.MoveNext() {
		t.Fatal("MoveNext returned true after exhaustion")
	}
	if got := it.Current().Value(); got != "b3" {
		t.Fatalf("Current after exhaustion = %q, want the last match b3", got)
	}
}
