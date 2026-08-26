// Spec2Repo oracle - atomic tests for xpath-query-engine-fullrepro-001
package atomic

import (
	"math"
	"strings"
	"testing"

	"github.com/antchfx/xpath"
)

// node is a test-owned in-memory document node.
type node struct {
	parent, firstChild, lastChild, prevSibling, nextSibling *node

	typ   xpath.NodeType
	data  string // element name (possibly prefixed), text, or comment body
	attrs [][2]string
	nsURI string
}

func newRoot() *node { return &node{typ: xpath.RootNode} }

func (n *node) add(data string, typ xpath.NodeType) *node {
	c := &node{typ: typ, data: data, parent: n}
	if n.lastChild == nil {
		n.firstChild = c
	} else {
		n.lastChild.nextSibling = c
		c.prevSibling = n.lastChild
	}
	n.lastChild = c
	return c
}

func (n *node) elem(name string) *node     { return n.add(name, xpath.ElementNode) }
func (n *node) text(s string) *node        { n.add(s, xpath.TextNode); return n }
func (n *node) comment(s string) *node     { n.add(s, xpath.CommentNode); return n }
func (n *node) attr(k, v string) *node     { n.attrs = append(n.attrs, [2]string{k, v}); return n }
func (n *node) namespace(uri string) *node { n.nsURI = uri; return n }

func (n *node) deepText() string {
	if n.typ == xpath.TextNode {
		return n.data
	}
	var sb strings.Builder
	var walk func(*node)
	walk = func(m *node) {
		if m.typ == xpath.TextNode {
			sb.WriteString(m.data)
		}
		for c := m.firstChild; c != nil; c = c.nextSibling {
			walk(c)
		}
	}
	walk(n)
	return sb.String()
}

// nav is a cursor over node implementing xpath.NodeNavigator plus the
// optional NamespaceURL extension.
type nav struct {
	root, curr *node
	attr       int // -1 when positioned on the node itself
}

func newNav(root *node) *nav { return &nav{root: root, curr: root, attr: -1} }

func (n *nav) NodeType() xpath.NodeType {
	if n.attr != -1 {
		return xpath.AttributeNode
	}
	return n.curr.typ
}

func (n *nav) LocalName() string {
	if n.attr != -1 {
		name := n.curr.attrs[n.attr][0]
		if i := strings.Index(name, ":"); i >= 0 {
			return name[i+1:]
		}
		return name
	}
	if n.curr.typ != xpath.ElementNode {
		return ""
	}
	name := n.curr.data
	if i := strings.Index(name, ":"); i >= 0 {
		return name[i+1:]
	}
	return name
}

func (n *nav) Prefix() string {
	if n.attr == -1 && n.curr.typ == xpath.ElementNode {
		if i := strings.Index(n.curr.data, ":"); i >= 0 {
			return n.curr.data[:i]
		}
	}
	return ""
}

func (n *nav) NamespaceURL() string {
	if n.attr == -1 {
		return n.curr.nsURI
	}
	return ""
}

func (n *nav) Value() string {
	if n.attr != -1 {
		return n.curr.attrs[n.attr][1]
	}
	switch n.curr.typ {
	case xpath.CommentNode, xpath.TextNode:
		return n.curr.data
	default:
		return n.curr.deepText()
	}
}

func (n *nav) Copy() xpath.NodeNavigator {
	c := *n
	return &c
}

func (n *nav) MoveToRoot() { n.curr, n.attr = n.root, -1 }

func (n *nav) MoveToParent() bool {
	if n.attr != -1 {
		n.attr = -1
		return true
	}
	if n.curr.parent == nil {
		return false
	}
	n.curr = n.curr.parent
	return true
}

func (n *nav) MoveToNextAttribute() bool {
	if n.curr.typ != xpath.ElementNode || n.attr >= len(n.curr.attrs)-1 {
		return false
	}
	n.attr++
	return true
}

func (n *nav) MoveToChild() bool {
	if n.attr != -1 || n.curr.firstChild == nil {
		return false
	}
	n.curr = n.curr.firstChild
	return true
}

func (n *nav) MoveToFirst() bool {
	if n.attr != -1 || n.curr.prevSibling == nil {
		return false
	}
	for n.curr.prevSibling != nil {
		n.curr = n.curr.prevSibling
	}
	return true
}

func (n *nav) MoveToNext() bool {
	if n.attr != -1 || n.curr.nextSibling == nil {
		return false
	}
	n.curr = n.curr.nextSibling
	return true
}

func (n *nav) MoveToPrevious() bool {
	if n.attr != -1 || n.curr.prevSibling == nil {
		return false
	}
	n.curr = n.curr.prevSibling
	return true
}

func (n *nav) MoveTo(other xpath.NodeNavigator) bool {
	o, ok := other.(*nav)
	if !ok || o.root != n.root {
		return false
	}
	n.curr, n.attr = o.curr, o.attr
	return true
}

// plainNav wraps nav without exposing the optional NamespaceURL method.
type plainNav struct {
	n *nav
}

func newPlainNav(root *node) *plainNav { return &plainNav{n: newNav(root)} }

func (p *plainNav) NodeType() xpath.NodeType { return p.n.NodeType() }
func (p *plainNav) LocalName() string        { return p.n.LocalName() }
func (p *plainNav) Prefix() string           { return p.n.Prefix() }
func (p *plainNav) Value() string            { return p.n.Value() }
func (p *plainNav) Copy() xpath.NodeNavigator {
	c := *p.n
	return &plainNav{n: &c}
}
func (p *plainNav) MoveToRoot()               { p.n.MoveToRoot() }
func (p *plainNav) MoveToParent() bool        { return p.n.MoveToParent() }
func (p *plainNav) MoveToNextAttribute() bool { return p.n.MoveToNextAttribute() }
func (p *plainNav) MoveToChild() bool         { return p.n.MoveToChild() }
func (p *plainNav) MoveToFirst() bool         { return p.n.MoveToFirst() }
func (p *plainNav) MoveToNext() bool          { return p.n.MoveToNext() }
func (p *plainNav) MoveToPrevious() bool      { return p.n.MoveToPrevious() }
func (p *plainNav) MoveTo(other xpath.NodeNavigator) bool {
	o, ok := other.(*plainNav)
	if !ok {
		return false
	}
	return p.n.MoveTo(o.n)
}

// bookstore builds the canonical test document:
//
// <bookstore specialty="novel">
//
//	<book id="b1" category="cooking">
//	  <title lang="en">Everyday Italian</title>
//	  <author>Giada De Laurentiis</author>
//	  <year>2005</year>
//	  <price>30.00</price>
//	</book>
//	<book id="b2" category="children">
//	  <title lang="en">Harry Potter</title>
//	  <author>J K. Rowling</author>
//	  <year>2005</year>
//	  <price>29.99</price>
//	</book>
//	<book id="b3" category="web">
//	  <title lang="en">XQuery Kick Start</title>
//	  <author>James McGovern</author>
//	  <author>Per Bothner</author>
//	  <year>2003</year>
//	  <price>49.99</price>
//	</book>
//	<!-- top comment -->
//
// </bookstore>
func bookstore() *node {
	root := newRoot()
	bs := root.elem("bookstore")
	bs.attr("specialty", "novel")
	b1 := bs.elem("book")
	b1.attr("id", "b1").attr("category", "cooking")
	b1.elem("title").attr("lang", "en").text("Everyday Italian")
	b1.elem("author").text("Giada De Laurentiis")
	b1.elem("year").text("2005")
	b1.elem("price").text("30.00")
	b2 := bs.elem("book")
	b2.attr("id", "b2").attr("category", "children")
	b2.elem("title").attr("lang", "en").text("Harry Potter")
	b2.elem("author").text("J K. Rowling")
	b2.elem("year").text("2005")
	b2.elem("price").text("29.99")
	b3 := bs.elem("book")
	b3.attr("id", "b3").attr("category", "web")
	b3.elem("title").attr("lang", "en").text("XQuery Kick Start")
	b3.elem("author").text("James McGovern")
	b3.elem("author").text("Per Bothner")
	b3.elem("year").text("2003")
	b3.elem("price").text("49.99")
	bs.comment("top comment")
	return root
}

// nsDoc builds <root><ns:child xmlns:ns="http://example.com/ns">v1</ns:child><plain>v2</plain></root>.
func nsDoc() *node {
	root := newRoot()
	r := root.elem("root")
	c := r.elem("ns:child")
	c.namespace("http://example.com/ns")
	c.text("v1")
	r.elem("plain").text("v2")
	return root
}

// nestedDivs builds <div><div><div>x</div></div></div> under the root.
func nestedDivs() *node {
	root := newRoot()
	d1 := root.elem("div")
	d2 := d1.elem("div")
	d2.elem("div").text("x")
	return root
}

// compileOK compiles and fails the test on error.
func compileOK(t *testing.T, expr string) *xpath.Expr {
	t.Helper()
	e, err := xpath.Compile(expr)
	if err != nil {
		t.Fatalf("Compile(%q): %v", expr, err)
	}
	if e == nil {
		t.Fatalf("Compile(%q) returned nil expression", expr)
	}
	return e
}

// desc renders one navigator position as a compact descriptor.
func desc(c xpath.NodeNavigator) string {
	switch c.NodeType() {
	case xpath.ElementNode:
		return c.LocalName()
	case xpath.AttributeNode:
		return "@" + c.LocalName() + "=" + c.Value()
	case xpath.TextNode:
		return "text:" + c.Value()
	case xpath.CommentNode:
		return "comment:" + c.Value()
	case xpath.RootNode:
		return "ROOT"
	}
	return "?"
}

// selDesc selects expr from the document root and returns descriptors in order.
func selDesc(t *testing.T, root *node, expr string) []string {
	t.Helper()
	it := compileOK(t, expr).Select(newNav(root))
	var out []string
	for it.MoveNext() {
		out = append(out, desc(it.Current()))
	}
	return out
}

// selValues selects expr and returns each matched node's Value in order.
func selValues(t *testing.T, root *node, expr string) []string {
	t.Helper()
	it := compileOK(t, expr).Select(newNav(root))
	var out []string
	for it.MoveNext() {
		out = append(out, it.Current().Value())
	}
	return out
}

func evalVal(t *testing.T, root *node, expr string) interface{} {
	t.Helper()
	return compileOK(t, expr).Evaluate(newNav(root))
}

func evalNum(t *testing.T, root *node, expr string) float64 {
	t.Helper()
	v, ok := evalVal(t, root, expr).(float64)
	if !ok {
		t.Fatalf("Evaluate(%q) did not return float64", expr)
	}
	return v
}

func evalStr(t *testing.T, root *node, expr string) string {
	t.Helper()
	v, ok := evalVal(t, root, expr).(string)
	if !ok {
		t.Fatalf("Evaluate(%q) did not return string", expr)
	}
	return v
}

func evalBool(t *testing.T, root *node, expr string) bool {
	t.Helper()
	v, ok := evalVal(t, root, expr).(bool)
	if !ok {
		t.Fatalf("Evaluate(%q) did not return bool", expr)
	}
	return v
}

func wantNum(t *testing.T, root *node, expr string, want float64) {
	t.Helper()
	if got := evalNum(t, root, expr); got != want {
		t.Fatalf("Evaluate(%q) = %v, want %v", expr, got, want)
	}
}

func wantNaN(t *testing.T, root *node, expr string) {
	t.Helper()
	if got := evalNum(t, root, expr); !math.IsNaN(got) {
		t.Fatalf("Evaluate(%q) = %v, want NaN", expr, got)
	}
}

func wantStr(t *testing.T, root *node, expr string, want string) {
	t.Helper()
	if got := evalStr(t, root, expr); got != want {
		t.Fatalf("Evaluate(%q) = %q, want %q", expr, got, want)
	}
}

func wantBool(t *testing.T, root *node, expr string, want bool) {
	t.Helper()
	if got := evalBool(t, root, expr); got != want {
		t.Fatalf("Evaluate(%q) = %v, want %v", expr, got, want)
	}
}

func wantSlice(t *testing.T, got, want []string, msg string) {
	t.Helper()
	if len(got) != len(want) {
		t.Fatalf("%s: got %v, want %v", msg, got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("%s: got %v, want %v", msg, got, want)
		}
	}
}

// wantCompileErr asserts Compile fails with exactly the given message.
func wantCompileErr(t *testing.T, expr, wantMsg string) {
	t.Helper()
	e, err := xpath.Compile(expr)
	if err == nil {
		t.Fatalf("Compile(%q) succeeded (%v), want error %q", expr, e, wantMsg)
	}
	if err.Error() != wantMsg {
		t.Fatalf("Compile(%q) error = %q, want %q", expr, err.Error(), wantMsg)
	}
}
