// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// Incremental and Fragment Parsing
package atomic

import (
	"fmt"
	"io"
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

func TestStmtsSeqIteration(t *testing.T) {
	p := syntax.NewParser()
	var got []string
	var semis []bool
	for st, err := range p.StmtsSeq(strings.NewReader("foo\nbar; baz\n")) {
		if err != nil {
			t.Fatal(err)
		}
		got = append(got, printDefault(t, st))
		semis = append(semis, st.Semicolon.IsValid())
	}
	wantEq(t, len(got), 3, "statement count")
	wantEq(t, got[0], "foo", "stmt 0")
	wantEq(t, got[1], "bar", "stmt 1")
	wantEq(t, got[2], "baz", "stmt 2")
	wantEq(t, semis[1], true, "middle statement has semicolon")
	wantEq(t, semis[2], false, "last statement has none")
}

func TestStmtsSeqError(t *testing.T) {
	p := syntax.NewParser()
	count := 0
	var gotErr error
	for _, err := range p.StmtsSeq(strings.NewReader("foo\nbar |\n")) {
		if err != nil {
			gotErr = err
			break
		}
		count++
	}
	wantEq(t, count, 1, "statements before error")
	if gotErr == nil {
		t.Fatal("expected error")
	}
	wantContains(t, gotErr.Error(), "`|` must be followed by a statement", "error text")
}

func TestStmtsCallbackStopEarly(t *testing.T) {
	p := syntax.NewParser()
	count := 0
	err := p.Stmts(strings.NewReader("a\nb\nc\n"), func(st *syntax.Stmt) bool {
		count++
		return count < 2
	})
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, count, 2, "callback invocations after early stop")
}

func TestWordsSeqMultiline(t *testing.T) {
	p := syntax.NewParser()
	var got []string
	for w, err := range p.WordsSeq(strings.NewReader("a  b\nc")) {
		if err != nil {
			t.Fatal(err)
		}
		got = append(got, w.Lit())
	}
	wantEq(t, fmt.Sprint(got), "[a b c]", "words across lines")
}

func TestWordsSeqNonWordError(t *testing.T) {
	p := syntax.NewParser()
	var got []string
	var gotErr error
	for w, err := range p.WordsSeq(strings.NewReader("a; b")) {
		if err != nil {
			gotErr = err
			break
		}
		got = append(got, w.Lit())
	}
	wantEq(t, len(got), 1, "words before error")
	if gotErr == nil {
		t.Fatal("expected error")
	}
	wantContains(t, gotErr.Error(), "`;` is not a valid word", "error text")
}

func TestDocumentParsesExpansion(t *testing.T) {
	p := syntax.NewParser()
	w, err := p.Document(strings.NewReader("foo $bar\nbaz\n"))
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, len(w.Parts), 3, "part count")
	pe, ok := w.Parts[1].(*syntax.ParamExp)
	if !ok {
		t.Fatalf("part 1 is %T, want *syntax.ParamExp", w.Parts[1])
	}
	wantEq(t, pe.Param.Value, "bar", "parameter name")
	// Double quotes need no escaping in a here-document body.
	w2, err := p.Document(strings.NewReader(`say "hi"`))
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, w2.Lit(), `say "hi"`, "double quotes literal in document")
}

func TestArithmeticFragment(t *testing.T) {
	p := syntax.NewParser()
	expr, err := p.Arithmetic(strings.NewReader("3 + x*2"))
	if err != nil {
		t.Fatal(err)
	}
	ba, ok := expr.(*syntax.BinaryArithm)
	if !ok {
		t.Fatalf("expr is %T, want *syntax.BinaryArithm", expr)
	}
	wantEq(t, ba.Op, syntax.Add, "top operator")
	x, ok := ba.X.(*syntax.Word)
	if !ok {
		t.Fatalf("X is %T, want *syntax.Word", ba.X)
	}
	wantEq(t, x.Lit(), "3", "left operand")
	inner, ok := ba.Y.(*syntax.BinaryArithm)
	if !ok {
		t.Fatalf("Y is %T, want *syntax.BinaryArithm", ba.Y)
	}
	wantEq(t, inner.Op, syntax.Mul, "nested operator")
}

func TestArithmeticFragmentError(t *testing.T) {
	p := syntax.NewParser()
	_, err := p.Arithmetic(strings.NewReader("3 +"))
	if err == nil {
		t.Fatal("expected error")
	}
	wantContains(t, err.Error(), "`+` must be followed by an expression", "error text")
}

func TestInteractiveSeqBatches(t *testing.T) {
	pr, pw := io.Pipe()
	p := syntax.NewParser()
	type batch struct {
		n          int
		incomplete bool
	}
	results := make(chan batch, 8)
	go func() {
		defer close(results)
		for stmts, err := range p.InteractiveSeq(pr) {
			if err != nil {
				return
			}
			results <- batch{len(stmts), p.Incomplete()}
		}
	}()
	io.WriteString(pw, "foo; bar\n")
	b := <-results
	wantEq(t, b.n, 2, "first line statement count")
	wantEq(t, b.incomplete, false, "first line complete")
	io.WriteString(pw, "if true; then\n")
	b = <-results
	wantEq(t, b.n, 0, "incomplete line yields no statements")
	wantEq(t, b.incomplete, true, "parser incomplete mid-if")
	io.WriteString(pw, "baz\nfi\n")
	// One empty batch for the still-incomplete "baz" line, then the if.
	for b = range results {
		if b.n > 0 {
			break
		}
		wantEq(t, b.incomplete, true, "still incomplete before fi")
	}
	wantEq(t, b.n, 1, "completed if yields one statement")
	wantEq(t, b.incomplete, false, "complete after fi")
	pw.Close()
}

func TestInteractiveCallbackStop(t *testing.T) {
	p := syntax.NewParser()
	calls := 0
	err := p.Interactive(strings.NewReader("a\nb\nc\n"), func(stmts []*syntax.Stmt) bool {
		calls++
		return false
	})
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, calls, 1, "callback stops iteration")
}

func TestIsIncompleteClassification(t *testing.T) {
	err := parseErr(t, "echo 'foo")
	wantEq(t, syntax.IsIncomplete(err), true, "unclosed quote is incomplete")
	err2 := parseErr(t, "foo )")
	wantEq(t, syntax.IsIncomplete(err2), false, "stray paren is not incomplete")
	wrapped := fmt.Errorf("outer: %w", err)
	wantEq(t, syntax.IsIncomplete(wrapped), false, "wrapped errors are not unwrapped")
}
