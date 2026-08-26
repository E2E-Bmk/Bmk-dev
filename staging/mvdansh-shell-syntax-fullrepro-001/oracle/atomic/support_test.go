// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
package atomic

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

// parse parses src with a fresh parser and fails the test on error.
func parse(t *testing.T, src string, opts ...syntax.ParserOption) *syntax.File {
	t.Helper()
	f, err := syntax.NewParser(opts...).Parse(strings.NewReader(src), "src.sh")
	if err != nil {
		t.Fatalf("parse %q: %v", src, err)
	}
	return f
}

// parseNamed parses with an explicit file name.
func parseNamed(t *testing.T, src, name string, opts ...syntax.ParserOption) *syntax.File {
	t.Helper()
	f, err := syntax.NewParser(opts...).Parse(strings.NewReader(src), name)
	if err != nil {
		t.Fatalf("parse %q: %v", src, err)
	}
	return f
}

// parseErr parses src expecting an error.
func parseErr(t *testing.T, src string, opts ...syntax.ParserOption) error {
	t.Helper()
	_, err := syntax.NewParser(opts...).Parse(strings.NewReader(src), "src.sh")
	if err == nil {
		t.Fatalf("parse %q: expected error, got none", src)
	}
	return err
}

// printDefault prints node with the given printer options.
func printDefault(t *testing.T, node syntax.Node, opts ...syntax.PrinterOption) string {
	t.Helper()
	var b strings.Builder
	if err := syntax.NewPrinter(opts...).Print(&b, node); err != nil {
		t.Fatalf("print: %v", err)
	}
	return b.String()
}

// call returns the CallExpr of statement i.
func call(t *testing.T, f *syntax.File, i int) *syntax.CallExpr {
	t.Helper()
	if len(f.Stmts) <= i {
		t.Fatalf("want at least %d statements, got %d", i+1, len(f.Stmts))
	}
	ce, ok := f.Stmts[i].Cmd.(*syntax.CallExpr)
	if !ok {
		t.Fatalf("stmt %d command is %T, want *syntax.CallExpr", i, f.Stmts[i].Cmd)
	}
	return ce
}

// arg returns argument i of the first statement's call.
func arg(t *testing.T, f *syntax.File, i int) *syntax.Word {
	t.Helper()
	ce := call(t, f, 0)
	if len(ce.Args) <= i {
		t.Fatalf("want at least %d args, got %d", i+1, len(ce.Args))
	}
	return ce.Args[i]
}

func wantEq(t *testing.T, got, want interface{}, what string) {
	t.Helper()
	if got != want {
		t.Fatalf("%s = %#v, want %#v", what, got, want)
	}
}

func wantContains(t *testing.T, haystack, needle, what string) {
	t.Helper()
	if !strings.Contains(haystack, needle) {
		t.Fatalf("%s: %q does not contain %q", what, haystack, needle)
	}
}

func wantPos(t *testing.T, p syntax.Pos, off, line, col uint, what string) {
	t.Helper()
	if p.Offset() != off || p.Line() != line || p.Col() != col {
		t.Fatalf("%s = offset %d line %d col %d, want %d/%d/%d",
			what, p.Offset(), p.Line(), p.Col(), off, line, col)
	}
}
