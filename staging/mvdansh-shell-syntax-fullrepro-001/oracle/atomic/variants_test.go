// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// Language Variants
package atomic

import (
	"fmt"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

func TestLangVariantValuesAndStrings(t *testing.T) {
	cases := []struct {
		l    syntax.LangVariant
		num  int
		name string
	}{
		{syntax.LangBash, 1, "bash"},
		{syntax.LangPOSIX, 2, "posix"},
		{syntax.LangMirBSDKorn, 4, "mksh"},
		{syntax.LangBats, 8, "bats"},
		{syntax.LangZsh, 16, "zsh"},
		{syntax.LangAuto, 32, "auto"},
	}
	for _, tc := range cases {
		wantEq(t, int(tc.l), tc.num, "numeric value of "+tc.name)
		wantEq(t, tc.l.String(), tc.name, "String of "+tc.name)
	}
}

func TestLangVariantSetAccepted(t *testing.T) {
	cases := []struct {
		name string
		want syntax.LangVariant
	}{
		{"bash", syntax.LangBash},
		{"posix", syntax.LangPOSIX},
		{"sh", syntax.LangPOSIX},
		{"mksh", syntax.LangMirBSDKorn},
		{"bats", syntax.LangBats},
		{"zsh", syntax.LangZsh},
		{"auto", syntax.LangAuto},
	}
	for _, tc := range cases {
		var l syntax.LangVariant
		if err := l.Set(tc.name); err != nil {
			t.Fatalf("Set(%q): %v", tc.name, err)
		}
		wantEq(t, l, tc.want, "Set("+tc.name+")")
	}
}

func TestLangVariantSetUnknown(t *testing.T) {
	l := syntax.LangMirBSDKorn
	err := l.Set("fish")
	if err == nil {
		t.Fatal("Set(fish): expected error")
	}
	wantEq(t, err.Error(), `unknown shell language variant: "fish"`, "Set error text")
	wantEq(t, l, syntax.LangMirBSDKorn, "receiver after failed Set")
}

func TestPosixRejectsArrays(t *testing.T) {
	err := parseErr(t, "a=(1 2)", syntax.Variant(syntax.LangPOSIX))
	le, ok := err.(syntax.LangError)
	if !ok {
		t.Fatalf("error type %T, want syntax.LangError", err)
	}
	wantEq(t, le.Filename, "src.sh", "LangError.Filename")
	wantEq(t, le.Feature, "arrays", "LangError.Feature")
	wantEq(t, le.LangUsed, syntax.LangPOSIX, "LangError.LangUsed")
	if len(le.Langs) == 0 {
		t.Fatal("LangError.Langs is empty")
	}
	found := false
	for _, l := range le.Langs {
		if l == syntax.LangBash {
			found = true
		}
	}
	if !found {
		t.Fatalf("LangError.Langs %v does not include LangBash", le.Langs)
	}
	wantEq(t, le.Error(), "src.sh:1:3: arrays are a bash/mksh/zsh feature; tried parsing as posix", "LangError message")
}

func TestPosixRejectsExtGlob(t *testing.T) {
	err := parseErr(t, "echo @(a)", syntax.Variant(syntax.LangPOSIX))
	if _, ok := err.(syntax.LangError); !ok {
		t.Fatalf("error type %T, want syntax.LangError", err)
	}
	wantContains(t, err.Error(), "extended globs are a bash/mksh feature; tried parsing as posix", "extglob gate message")
}

func TestPosixRejectsFunctionKeyword(t *testing.T) {
	err := parseErr(t, "function f { x; }", syntax.Variant(syntax.LangPOSIX))
	if _, ok := err.(syntax.LangError); !ok {
		t.Fatalf("error type %T, want syntax.LangError", err)
	}
	wantContains(t, err.Error(), `the "function" builtin is a bash feature; tried parsing as posix`, "function gate message")
}

func TestPosixParsesDoubleBracketAsCommand(t *testing.T) {
	f := parse(t, "[[ -n $x ]]", syntax.Variant(syntax.LangPOSIX))
	ce := call(t, f, 0)
	wantEq(t, ce.Args[0].Lit(), "[[", "first word under POSIX")
}

func TestPosixParsesLetAsCommand(t *testing.T) {
	f := parse(t, "let x=1", syntax.Variant(syntax.LangPOSIX))
	ce := call(t, f, 0)
	wantEq(t, ce.Args[0].Lit(), "let", "let as plain word under POSIX")
	wantEq(t, len(ce.Args), 2, "arg count")
}

func TestMkshCaseResumeKorn(t *testing.T) {
	f := parse(t, "case x in\na) f1 ;|\nesac\n", syntax.Variant(syntax.LangMirBSDKorn))
	cc, ok := f.Stmts[0].Cmd.(*syntax.CaseClause)
	if !ok {
		t.Fatalf("command is %T, want *syntax.CaseClause", f.Stmts[0].Cmd)
	}
	wantEq(t, cc.Items[0].Op, syntax.ResumeKorn, "case operator")
	wantEq(t, cc.Items[0].Op.String(), ";|", "operator text")
}

func TestBashRejectsResumeKorn(t *testing.T) {
	parseErr(t, "case x in\na) f1 ;|\nesac\n")
}

func TestBatsTestDecl(t *testing.T) {
	f := parse(t, "@test \"my test\" {\n  run foo\n}\n", syntax.Variant(syntax.LangBats))
	td, ok := f.Stmts[0].Cmd.(*syntax.TestDecl)
	if !ok {
		t.Fatalf("command is %T, want *syntax.TestDecl", f.Stmts[0].Cmd)
	}
	wantEq(t, printDefault(t, td.Description), `"my test"`, "description")
	if _, ok := td.Body.Cmd.(*syntax.Block); !ok {
		t.Fatalf("body command is %T, want *syntax.Block", td.Body.Cmd)
	}
}

func TestBashRejectsAtTest(t *testing.T) {
	parseErr(t, "@test \"my test\" {\n  run foo\n}\n")
}

func TestVariantLangAutoPanics(t *testing.T) {
	defer func() {
		r := recover()
		if r == nil {
			t.Fatal("Variant(LangAuto) did not panic")
		}
		wantEq(t, fmt.Sprint(r), "LangAuto is not supported by the parser at this time", "panic message")
	}()
	syntax.NewParser(syntax.Variant(syntax.LangAuto))
}
