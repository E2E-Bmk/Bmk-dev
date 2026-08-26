package integration

import (
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

// collectNodes walks f and returns every non-nil node visited in pre-order.
// A parsed corpus file always yields the root, a statement, and a command
// at minimum, so fewer than three nodes means the walk did not happen.
func collectNodes(t *testing.T, f *syntax.File) []syntax.Node {
	t.Helper()
	var nodes []syntax.Node
	syntax.Walk(f, func(n syntax.Node) bool {
		if n != nil {
			nodes = append(nodes, n)
		}
		return true
	})
	if len(nodes) < 3 {
		t.Fatalf("walk visited only %d nodes, want at least 3", len(nodes))
	}
	return nodes
}

func TestNodeExtentsOrdered(t *testing.T) {
	for lang, corpus := range dialectCorpora() {
		for _, src := range corpus {
			f := mustParse(t, src, lang)
			for _, n := range collectNodes(t, f) {
				p, e := n.Pos(), n.End()
				if !p.IsValid() || !e.IsValid() {
					t.Fatalf("%v: node %T has invalid position in %q", lang, n, src)
				}
				if e.Offset() < p.Offset() {
					t.Fatalf("%v: node %T ends (%v) before it starts (%v) in %q", lang, n, e, p, src)
				}
				if int(e.Offset()) > len(src) {
					t.Fatalf("%v: node %T extent [%d,%d] exceeds source length %d in %q",
						lang, n, p.Offset(), e.Offset(), len(src), src)
				}
			}
		}
	}
}

func TestHeredocExtentBeyondStatement(t *testing.T) {
	src := "cat <<EOF >out.txt\nbody $HOME\nEOF\n"
	f := mustParse(t, src, syntax.LangBash)
	st := f.Stmts[0]
	hdocRedir := st.Redirs[0]
	if got := int(st.End().Offset()); got != len("cat <<EOF >out.txt") {
		t.Fatalf("statement end offset = %d, want end of the >out.txt redirect", got)
	}
	if got := int(hdocRedir.End().Offset()); got != len(src)-1 {
		t.Fatalf("heredoc redirect end offset = %d, want %d (after the closing delimiter)", got, len(src)-1)
	}

	last := "cat <<EOF\nbody\nEOF\n"
	f2 := mustParse(t, last, syntax.LangBash)
	st2 := f2.Stmts[0]
	if st2.End().Offset() != st2.Redirs[0].End().Offset() {
		t.Fatalf("statement with trailing heredoc should end with it: stmt %d, redirect %d",
			st2.End().Offset(), st2.Redirs[0].End().Offset())
	}
	if got := int(st2.End().Offset()); got != len(last)-1 {
		t.Fatalf("trailing heredoc statement end = %d, want %d", got, len(last)-1)
	}
}

func TestPositionsAgreeWithSource(t *testing.T) {
	for lang, corpus := range dialectCorpora() {
		for _, src := range corpus {
			f := mustParse(t, src, lang)
			for _, n := range collectNodes(t, f) {
				for _, p := range []syntax.Pos{n.Pos(), n.End()} {
					off := int(p.Offset())
					if off > len(src) {
						t.Fatalf("%v: offset %d beyond source length %d", lang, off, len(src))
					}
					line, col := lineColFromOffset(src, off)
					if int(p.Line()) != line || int(p.Col()) != col {
						t.Fatalf("%v: node %T position %d reports %d:%d, source counting gives %d:%d in %q",
							lang, n, off, p.Line(), p.Col(), line, col, src)
					}
				}
			}
		}
	}
}

func TestWalkVisitCounts(t *testing.T) {
	for lang, corpus := range dialectCorpora() {
		for _, src := range corpus {
			f := mustParse(t, src, lang)
			var enter, leave int
			syntax.Walk(f, func(n syntax.Node) bool {
				if n == nil {
					leave++
				} else {
					enter++
				}
				return true
			})
			if enter != leave {
				t.Fatalf("%v: %d node visits but %d nil visits for %q", lang, enter, leave, src)
			}
			if enter < 2 {
				t.Fatalf("%v: implausibly few nodes (%d) for %q", lang, enter, src)
			}
		}
	}
}

func TestPosAfterAgreesWithOffsets(t *testing.T) {
	src := bashCorpus[0] + bashCorpus[3]
	f := mustParse(t, src, syntax.LangBash)
	nodes := collectNodes(t, f)
	positions := make([]syntax.Pos, 0, len(nodes))
	for _, n := range nodes {
		positions = append(positions, n.Pos())
	}
	for i, p := range positions {
		for j, q := range positions {
			want := p.Offset() > q.Offset()
			if got := p.After(q); got != want {
				t.Fatalf("After mismatch: positions %d (%v) and %d (%v): After=%v, offset comparison=%v",
					i, p, j, q, got, want)
			}
		}
	}
}
