// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// Canonical Printing
package atomic

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

// reprint parses src and prints it with the given options.
func reprint(t *testing.T, src string, popts []syntax.ParserOption, opts ...syntax.PrinterOption) string {
	t.Helper()
	f := parse(t, src, popts...)
	return printDefault(t, f, opts...)
}

func canon(t *testing.T, src string, opts ...syntax.PrinterOption) string {
	t.Helper()
	return reprint(t, src, nil, opts...)
}

func TestPrintCanonicalSpacing(t *testing.T) {
	wantEq(t, canon(t, "foo  bar ;  baz"), "foo bar\nbaz\n", "space collapse and semicolon split")
}

func TestPrintKeywordSpacing(t *testing.T) {
	wantEq(t, canon(t, "if true;then foo;fi"), "if true; then foo; fi\n", "keyword spacing")
	wantEq(t, canon(t, "for x in a b; do foo; done"), "for x in a b; do foo; done\n", "for layout")
}

func TestPrintBlankLineCollapse(t *testing.T) {
	wantEq(t, canon(t, "foo\nbar\n\n\n\nbaz\n"), "foo\nbar\n\nbaz\n", "blank lines collapse to one")
}

func TestPrintBackquoteConversion(t *testing.T) {
	wantEq(t, canon(t, "foo $(bar baz) `qux`\n"), "foo $(bar baz) $(qux)\n", "backquotes to dollar form")
}

func TestPrintSubshellBraces(t *testing.T) {
	wantEq(t, canon(t, "( foo )"), "(foo)\n", "subshell without padding")
	wantEq(t, canon(t, "{ foo; }"), "{ foo; }\n", "block keeps mandatory spaces")
}

func TestPrintMultilineBlock(t *testing.T) {
	wantEq(t, canon(t, "{ foo; bar; }"), "{\n\tfoo\n\tbar\n}\n", "multi-command block spans lines with tabs")
	wantEq(t, canon(t, "(foo; bar)"), "(\n\tfoo\n\tbar\n)\n", "multi-command subshell spans lines")
}

func TestPrintPipelineContinuation(t *testing.T) {
	wantEq(t, canon(t, "foo |\nbar |\nbaz\n"), "foo |\n\tbar |\n\tbaz\n", "operator stays at line end, continuation indented")
}

func TestPrintCommentSpacing(t *testing.T) {
	got := reprint(t, "foo   #   comment\n", []syntax.ParserOption{syntax.KeepComments(true)})
	wantEq(t, got, "foo #   comment\n", "one space before hash, text preserved")
}

func TestPrintTrailingNewlineOnlyForFile(t *testing.T) {
	f := parse(t, "foo bar >out\n")
	wantEq(t, printDefault(t, f.Stmts[0]), "foo bar >out", "Stmt has no trailing newline")
	ce := call(t, f, 0)
	wantEq(t, printDefault(t, ce.Args[1]), "bar", "Word prints bare")
	wantEq(t, printDefault(t, ce), "foo bar", "CallExpr prints without redirects")
	f2 := parse(t, "x=12\n")
	wantEq(t, printDefault(t, call(t, f2, 0).Assigns[0]), "x=12", "Assign prints bare")
	f3 := parse(t, "echo ${x:-def}\n")
	wantEq(t, printDefault(t, call(t, f3, 0).Args[1].Parts[0]), "${x:-def}", "WordPart prints bare")
}

func TestPrintUnsupportedNodeError(t *testing.T) {
	f := parse(t, "foo >out\n")
	var b strings.Builder
	err := syntax.NewPrinter().Print(&b, f.Stmts[0].Redirs[0])
	if err == nil {
		t.Fatal("expected error for *syntax.Redirect")
	}
	wantEq(t, err.Error(), "unsupported node type: *syntax.Redirect", "error text")
}

func TestIndentSpaces(t *testing.T) {
	src := "if true; then\n\tfoo\nfi\n"
	wantEq(t, canon(t, src), "if true; then\n\tfoo\nfi\n", "default tabs")
	wantEq(t, canon(t, src, syntax.Indent(4)), "if true; then\n    foo\nfi\n", "four spaces")
}

func TestBinaryNextLine(t *testing.T) {
	got := canon(t, "foo |\nbar |\nbaz\n", syntax.BinaryNextLine(true))
	wantEq(t, got, "foo \\\n\t| bar \\\n\t| baz\n", "operator leads continuation with backslash escape")
}

func TestSwitchCaseIndent(t *testing.T) {
	src := "case x in\na) foo ;;\nesac\n"
	wantEq(t, canon(t, src), "case x in\na) foo ;;\nesac\n", "default keeps items at case level")
	wantEq(t, canon(t, src, syntax.SwitchCaseIndent(true)), "case x in\n\ta) foo ;;\nesac\n", "indented items")
}

func TestSpaceRedirects(t *testing.T) {
	src := "foo >file 2>&1 <in >>app\n"
	wantEq(t, canon(t, src), "foo >file 2>&1 <in >>app\n", "default attaches operators")
	wantEq(t, canon(t, src, syntax.SpaceRedirects(true)),
		"foo > file 2>&1 < in >> app\n", "spaced operators except dups")
	got := canon(t, "diff <(a) >(b)\n", syntax.SpaceRedirects(true))
	wantEq(t, got, "diff <(a) >(b)\n", "process substitutions stay attached")
}

func TestFunctionNextLine(t *testing.T) {
	wantEq(t, canon(t, "f() { foo; }"), "f() { foo; }\n", "default keeps brace inline")
	wantEq(t, canon(t, "f() { foo; }", syntax.FunctionNextLine(true)),
		"f()\n{\n\tfoo\n}\n", "brace moves to next line")
}

func TestMinifyRules(t *testing.T) {
	wantEq(t, canon(t, "echo $(( x + y ))", syntax.Minify(true)), "echo $((x+y))\n", "arithmetic spaces vanish")
	wantEq(t, canon(t, "if true; then foo; fi", syntax.Minify(true)), "if true;then foo;fi\n", "keyword compression")
	wantEq(t, canon(t, "case x in a) b ;; c) d ;; esac", syntax.Minify(true)),
		"case x in a)b;;c)d;esac\n", "final case terminator compresses")
	wantEq(t, canon(t, "foo | bar && baz", syntax.Minify(true)), "foo|bar&&baz\n", "operators join operands")
	wantEq(t, canon(t, "f() { x; }", syntax.Minify(true)), "f(){ x;}\n", "function compression")
	wantEq(t, canon(t, "foo; bar", syntax.Minify(true)), "foo\nbar\n", "statements keep one per line")
}

func TestMinifyDropsComments(t *testing.T) {
	got := reprint(t, "foo # c1\nbar\n", []syntax.ParserOption{syntax.KeepComments(true)}, syntax.Minify(true))
	wantEq(t, got, "foo\nbar\n", "comments dropped under minify")
}

func TestSingleLineJoins(t *testing.T) {
	got := canon(t, "if true; then\n\tfoo\nfi\n", syntax.SingleLine(true))
	wantEq(t, got, "if true; then foo; fi\n", "multiline if joins")
}

func TestSingleLineHeredoc(t *testing.T) {
	got := canon(t, "cat <<EOF\nbody\nEOF\nfoo\n", syntax.SingleLine(true))
	wantEq(t, got, "cat <<EOF; foo\nbody\nEOF\n", "heredoc body still forces newlines")
}

func TestPrintNegationBackground(t *testing.T) {
	wantEq(t, canon(t, "! foo &\nbar"), "! foo &\nbar\n", "negation and background rendering")
}

func TestPrintHeredocVerbatim(t *testing.T) {
	src := "cat <<EOF\nhello $x\nEOF\n"
	wantEq(t, canon(t, src), src, "heredoc body verbatim")
}

func TestPrintOptionDirectApplication(t *testing.T) {
	p := syntax.NewPrinter()
	syntax.Minify(true)(p)
	f := parse(t, "foo | bar\n")
	var b strings.Builder
	if err := p.Print(&b, f); err != nil {
		t.Fatal(err)
	}
	wantEq(t, b.String(), "foo|bar\n", "option applied to existing printer")
}
