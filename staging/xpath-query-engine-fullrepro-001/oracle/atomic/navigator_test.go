// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"testing"

	"github.com/antchfx/xpath"
)

// noMoveNav wraps nav with a MoveTo that always fails, forcing the
// iterator onto its Copy fallback.
type noMoveNav struct {
	*nav
}

func (n *noMoveNav) MoveTo(other xpath.NodeNavigator) bool { return false }

func (n *noMoveNav) Copy() xpath.NodeNavigator {
	c := *n.nav
	return &noMoveNav{nav: &c}
}

func TestSelectAdoptsNavigator(t *testing.T) {
	doc := bookstore()
	n := newNav(doc)
	it := compileOK(t, "//book/@id").Select(n)
	if !it.MoveNext() {
		t.Fatal("no first match")
	}
	// The caller's navigator was repositioned in place.
	if got := n.Value(); got != "b1" {
		t.Fatalf("adopted navigator value = %q, want b1", got)
	}
	if it.Current() != xpath.NodeNavigator(n) {
		t.Fatal("Current is not the adopted navigator instance")
	}
	if !it.MoveNext() {
		t.Fatal("no second match")
	}
	if got := n.Value(); got != "b2" {
		t.Fatalf("adopted navigator value after second match = %q, want b2", got)
	}
}

func TestCurrentIdentityStableAcrossMatches(t *testing.T) {
	doc := bookstore()
	it := compileOK(t, "//book/@id").Select(newNav(doc))
	var seen []xpath.NodeNavigator
	for it.MoveNext() {
		seen = append(seen, it.Current())
	}
	if len(seen) != 3 {
		t.Fatalf("yielded %d matches, want 3", len(seen))
	}
	if seen[0] != seen[1] || seen[1] != seen[2] {
		t.Fatal("Current returned different navigator instances across matches")
	}
}

func TestMoveToFailureFallsBackToCopy(t *testing.T) {
	doc := bookstore()
	start := &noMoveNav{nav: newNav(doc)}
	it := compileOK(t, "//book/@id").Select(start)
	var vals []string
	var currents []xpath.NodeNavigator
	for it.MoveNext() {
		vals = append(vals, it.Current().Value())
		currents = append(currents, it.Current())
	}
	wantSlice(t, vals, []string{"b1", "b2", "b3"}, "values via copy fallback")
	// The original navigator was never repositioned.
	if got := start.nav.NodeType(); got != xpath.RootNode {
		t.Fatalf("original navigator moved to node type %v, want RootNode", got)
	}
	if currents[0] == xpath.NodeNavigator(start) {
		t.Fatal("iterator kept the original navigator although MoveTo failed")
	}
}

func TestCopyIsIndependentOfIteration(t *testing.T) {
	doc := bookstore()
	it := compileOK(t, "//book/@id").Select(newNav(doc))
	if !it.MoveNext() {
		t.Fatal("no first match")
	}
	snapshot := it.Current().Copy()
	if !it.MoveNext() {
		t.Fatal("no second match")
	}
	if got := snapshot.Value(); got != "b1" {
		t.Fatalf("copied navigator value = %q, want b1 (copy must not advance)", got)
	}
	if got := it.Current().Value(); got != "b2" {
		t.Fatalf("iterator value = %q, want b2", got)
	}
}

func TestNodeTypeConstantOrder(t *testing.T) {
	if xpath.RootNode != 0 || xpath.ElementNode != 1 || xpath.AttributeNode != 2 ||
		xpath.TextNode != 3 || xpath.CommentNode != 4 {
		t.Fatalf("NodeType constants out of order: %d %d %d %d %d",
			xpath.RootNode, xpath.ElementNode, xpath.AttributeNode,
			xpath.TextNode, xpath.CommentNode)
	}
	// The engine routes each node test to the matching taxonomy value.
	doc := bookstore()
	it := compileOK(t, "//comment()").Select(newNav(doc))
	if !it.MoveNext() {
		t.Fatal("//comment() matched nothing")
	}
	if got := it.Current().NodeType(); got != xpath.CommentNode {
		t.Fatalf("//comment() match type = %v, want CommentNode", got)
	}
	it = compileOK(t, "//book/@id").Select(newNav(doc))
	if !it.MoveNext() {
		t.Fatal("//book/@id matched nothing")
	}
	if got := it.Current().NodeType(); got != xpath.AttributeNode {
		t.Fatalf("attribute match type = %v, want AttributeNode", got)
	}
}
