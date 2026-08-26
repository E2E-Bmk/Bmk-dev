// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// Word Utilities and Rewrites
package atomic

import (
	"fmt"
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

func TestWalkOrder(t *testing.T) {
	f := parse(t, "foo bar\n")
	var seq []string
	syntax.Walk(f, func(n syntax.Node) bool {
		if n == nil {
			seq = append(seq, "nil")
			return false
		}
		seq = append(seq, strings.TrimPrefix(fmt.Sprintf("%T", n), "*syntax."))
		return true
	})
	want := "File Stmt CallExpr Word Lit nil nil Word Lit nil nil nil nil nil"
	wantEq(t, strings.Join(seq, " "), want, "depth-first order with nil terminators")
}

func TestWalkPruning(t *testing.T) {
	f := parse(t, "foo bar\nbaz qux\n")
	var seq []string
	syntax.Walk(f, func(n syntax.Node) bool {
		if n == nil {
			seq = append(seq, "nil")
			return false
		}
		seq = append(seq, strings.TrimPrefix(fmt.Sprintf("%T", n), "*syntax."))
		if _, ok := n.(*syntax.Stmt); ok {
			return false
		}
		return true
	})
	wantEq(t, strings.Join(seq, " "), "File Stmt Stmt nil", "false skips children and their nil marker")
}

func TestQuoteUnchanged(t *testing.T) {
	for _, s := range []string{"foo", "abc123", "névé"} {
		q, err := syntax.Quote(s, syntax.LangBash)
		if err != nil {
			t.Fatal(err)
		}
		wantEq(t, q, s, "no quoting needed for "+s)
	}
}

func TestQuoteSingleQuotes(t *testing.T) {
	cases := map[string]string{
		"foo bar": "'foo bar'",
		"$foo":    "'$foo'",
		"a=b":     "'a=b'",
		"~foo":    "'~foo'",
	}
	for in, want := range cases {
		q, err := syntax.Quote(in, syntax.LangBash)
		if err != nil {
			t.Fatal(err)
		}
		wantEq(t, q, want, "single-quoted "+in)
	}
}

func TestQuoteEmpty(t *testing.T) {
	q, err := syntax.Quote("", syntax.LangBash)
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, q, "''", "empty string")
}

func TestQuoteDoubleQuotes(t *testing.T) {
	q, err := syntax.Quote("foo'bar", syntax.LangBash)
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, q, `"foo'bar"`, "embedded single quote")
}

func TestQuoteDollarEscapes(t *testing.T) {
	q, err := syntax.Quote("foo\nbar", syntax.LangBash)
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, q, `$'foo\nbar'`, "newline escape")
	q2, err := syntax.Quote("\xff", syntax.LangBash)
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, q2, `$'\xff'`, "invalid UTF-8 escape")
}

func TestQuoteNullByteError(t *testing.T) {
	for _, lang := range []syntax.LangVariant{syntax.LangBash, syntax.LangPOSIX} {
		_, err := syntax.Quote("a\x00b", lang)
		qe, ok := err.(*syntax.QuoteError)
		if !ok {
			t.Fatalf("%v: error type %T, want *syntax.QuoteError", lang, err)
		}
		wantEq(t, qe.ByteOffset, 1, "byte offset")
		wantEq(t, qe.Message, "shell strings cannot contain null bytes", "message")
		wantEq(t, qe.Error(), "cannot quote character at byte 1: shell strings cannot contain null bytes", "rendered")
	}
}

func TestQuotePosixEscapesError(t *testing.T) {
	_, err := syntax.Quote("foo\nbar", syntax.LangPOSIX)
	qe, ok := err.(*syntax.QuoteError)
	if !ok {
		t.Fatalf("error type %T, want *syntax.QuoteError", err)
	}
	wantEq(t, qe.ByteOffset, 3, "byte offset")
	wantEq(t, qe.Message, "POSIX shell lacks escape sequences", "message")
	// The same string succeeds under bash.
	if _, err := syntax.Quote("foo\nbar", syntax.LangBash); err != nil {
		t.Fatalf("bash quote failed: %v", err)
	}
}

func splitWord(t *testing.T, src string) *syntax.Word {
	t.Helper()
	p := syntax.NewParser()
	var w *syntax.Word
	err := p.Words(strings.NewReader(src), func(g *syntax.Word) bool {
		w = g
		return false
	})
	if err != nil {
		t.Fatal(err)
	}
	return w
}

func TestSplitBracesValid(t *testing.T) {
	w := splitWord(t, "foo{bar,baz}")
	wantEq(t, syntax.SplitBraces(w), true, "changed")
	var be *syntax.BraceExp
	for _, part := range w.Parts {
		if b, ok := part.(*syntax.BraceExp); ok {
			be = b
		}
	}
	if be == nil {
		t.Fatal("no BraceExp produced")
	}
	wantEq(t, be.Sequence, false, "comma form")
	wantEq(t, len(be.Elems), 2, "element count")
	wantEq(t, be.Elems[0].Lit(), "bar", "first element")
	wantEq(t, be.Elems[1].Lit(), "baz", "second element")
	l, ok := w.Parts[0].(*syntax.Lit)
	if !ok || l.Value != "foo" {
		t.Fatalf("leading part = %#v, want Lit foo", w.Parts[0])
	}
}

func TestSplitBracesSequence(t *testing.T) {
	w := splitWord(t, "{1..10..2}")
	wantEq(t, syntax.SplitBraces(w), true, "changed")
	be, ok := w.Parts[0].(*syntax.BraceExp)
	if !ok {
		t.Fatalf("part 0 is %T, want *syntax.BraceExp", w.Parts[0])
	}
	wantEq(t, be.Sequence, true, "sequence form")
	wantEq(t, len(be.Elems), 3, "bounds plus increment")
	wantEq(t, be.Elems[0].Lit(), "1", "lower bound")
	wantEq(t, be.Elems[1].Lit(), "10", "upper bound")
	wantEq(t, be.Elems[2].Lit(), "2", "increment")
}

func TestSplitBracesMalformed(t *testing.T) {
	for _, src := range []string{"a{b", "{}", "{a}"} {
		w := splitWord(t, src)
		syntax.SplitBraces(w)
		joined := ""
		for _, part := range w.Parts {
			if _, ok := part.(*syntax.BraceExp); ok {
				t.Fatalf("%q produced a BraceExp", src)
			}
			if l, ok := part.(*syntax.Lit); ok {
				joined += l.Value
			}
		}
		wantEq(t, joined, src, "literal text preserved for "+src)
	}
}

func TestSplitBracesNoBraces(t *testing.T) {
	w := splitWord(t, "plain")
	wantEq(t, syntax.SplitBraces(w), false, "no change without braces")
	wantEq(t, len(w.Parts), 1, "single part untouched")
}

func TestSimplifyRules(t *testing.T) {
	cases := map[string]string{
		"echo $(( (x) ))":     "echo $((x))\n",
		"(($var))":            "((var))\n",
		"$( (foo) )":          "$(foo)\n",
		`[[ "$var" == str ]]`: "[[ $var == str ]]\n",
		"[[ ! -n $var ]]":     "[[ -z $var ]]\n",
		`echo "\$foo"`:        "echo '$foo'\n",
	}
	for src, want := range cases {
		f := parse(t, src)
		wantEq(t, syntax.Simplify(f), true, "changed for "+src)
		wantEq(t, printDefault(t, f), want, "simplified print for "+src)
	}
}

func TestSimplifyNoChange(t *testing.T) {
	f := parse(t, "echo foo\n")
	wantEq(t, syntax.Simplify(f), false, "no redundant syntax")
	wantEq(t, printDefault(t, f), "echo foo\n", "tree unchanged")
}

func TestOperatorStrings(t *testing.T) {
	wantEq(t, syntax.RdrOut.String(), ">", "RdrOut")
	wantEq(t, syntax.AppOut.String(), ">>", "AppOut")
	wantEq(t, syntax.DashHdoc.String(), "<<-", "DashHdoc")
	wantEq(t, syntax.WordHdoc.String(), "<<<", "WordHdoc")
	wantEq(t, syntax.RdrAll.String(), "&>", "RdrAll")
	wantEq(t, syntax.AndStmt.String(), "&&", "AndStmt")
	wantEq(t, syntax.PipeAll.String(), "|&", "PipeAll")
	wantEq(t, syntax.Fallthrough.String(), ";&", "Fallthrough")
	wantEq(t, syntax.Resume.String(), ";;&", "Resume")
	wantEq(t, syntax.GlobExcept.String(), "!(", "GlobExcept")
	wantEq(t, syntax.CmdIn.String(), "<(", "CmdIn")
	wantEq(t, syntax.Pow.String(), "**", "Pow")
	wantEq(t, syntax.TernQuest.String(), "?", "TernQuest")
	wantEq(t, syntax.AddAssgn.String(), "+=", "AddAssgn")
	wantEq(t, syntax.Inc.String(), "++", "Inc")
	wantEq(t, syntax.TsNempStr.String(), "-n", "TsNempStr")
	wantEq(t, syntax.TsReMatch.String(), "=~", "TsReMatch")
	wantEq(t, syntax.TsEql.String(), "-eq", "TsEql")
	wantEq(t, syntax.DefaultUnsetOrNull.String(), ":-", "DefaultUnsetOrNull")
	wantEq(t, syntax.RemLargePrefix.String(), "##", "RemLargePrefix")
	wantEq(t, syntax.UpperAll.String(), "^^", "UpperAll")
	wantEq(t, syntax.NamesPrefix.String(), "*", "NamesPrefix")
}
