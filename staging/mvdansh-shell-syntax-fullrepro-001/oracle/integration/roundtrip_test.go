package integration

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

// checkFixpoint asserts CVI 1 for one source under one dialect and one
// fixed set of printer options: print, reparse, print again, and the two
// printed forms must be byte-identical.
func checkFixpoint(t *testing.T, src string, lang syntax.LangVariant, opts ...syntax.PrinterOption) {
	t.Helper()
	f := mustParse(t, src, lang)
	out1 := printWith(t, f, opts...)
	if out1 == "" || !strings.HasSuffix(out1, "\n") {
		t.Fatalf("printed file must be non-empty and newline-terminated, got %q for %q", out1, src)
	}
	f2, err := syntax.NewParser(syntax.Variant(lang)).Parse(strings.NewReader(out1), "")
	if err != nil {
		t.Fatalf("reparse of printed output failed: %v\nsource: %q\nprinted: %q", err, src, out1)
	}
	out2 := printWith(t, f2, opts...)
	if out1 != out2 {
		t.Fatalf("print not a fixpoint\nsource: %q\nfirst:  %q\nsecond: %q", src, out1, out2)
	}
}

func TestRoundTripFixpointBash(t *testing.T) {
	for _, src := range bashCorpus {
		checkFixpoint(t, src, syntax.LangBash)
	}
}

func TestRoundTripFixpointPOSIX(t *testing.T) {
	for _, src := range posixCorpus {
		checkFixpoint(t, src, syntax.LangPOSIX)
	}
}

func TestRoundTripFixpointMksh(t *testing.T) {
	for _, src := range mkshCorpus {
		checkFixpoint(t, src, syntax.LangMirBSDKorn)
	}
}

func TestRoundTripFixpointBats(t *testing.T) {
	for _, src := range batsCorpus {
		checkFixpoint(t, src, syntax.LangBats)
	}
}

func TestRoundTripLayoutOptions(t *testing.T) {
	optSets := []struct {
		name string
		opts []syntax.PrinterOption
	}{
		{"indent4", []syntax.PrinterOption{syntax.Indent(4)}},
		{"binaryNextLine", []syntax.PrinterOption{syntax.BinaryNextLine(true)}},
		{"switchCaseIndent", []syntax.PrinterOption{syntax.SwitchCaseIndent(true)}},
		{"spaceRedirects", []syntax.PrinterOption{syntax.SpaceRedirects(true)}},
		{"functionNextLine", []syntax.PrinterOption{syntax.FunctionNextLine(true)}},
		{"combined", []syntax.PrinterOption{
			syntax.Indent(2), syntax.BinaryNextLine(true), syntax.SwitchCaseIndent(true),
			syntax.SpaceRedirects(true), syntax.FunctionNextLine(true),
		}},
	}
	for _, set := range optSets {
		for _, src := range bashCorpus {
			f := mustParse(t, src, syntax.LangBash)
			out1 := printWith(t, f, set.opts...)
			f2, err := syntax.NewParser().Parse(strings.NewReader(out1), "")
			if err != nil {
				t.Fatalf("%s: reparse failed: %v\nprinted: %q", set.name, err, out1)
			}
			out2 := printWith(t, f2, set.opts...)
			if out1 != out2 {
				t.Fatalf("%s: not a fixpoint\nfirst:  %q\nsecond: %q", set.name, out1, out2)
			}
		}
	}
}

func TestMinifyReparsesAndStabilises(t *testing.T) {
	for lang, corpus := range dialectCorpora() {
		for _, src := range corpus {
			f := mustParse(t, src, lang)
			min1 := printWith(t, f, syntax.Minify(true))
			f2, err := syntax.NewParser(syntax.Variant(lang)).Parse(strings.NewReader(min1), "")
			if err != nil {
				t.Fatalf("minified output does not reparse under %v: %v\nminified: %q", lang, err, min1)
			}
			min2 := printWith(t, f2, syntax.Minify(true))
			if min1 != min2 {
				t.Fatalf("minify not stable under %v\nfirst:  %q\nsecond: %q", lang, min1, min2)
			}
		}
	}
}

func TestKeepCommentsFixpoint(t *testing.T) {
	src := "#!/bin/bash\n# leading comment\nfoo bar # trailing\n\n# block\n# of comments\nbaz\nif true; then # why\n\tok\nfi\n"
	f := mustParse(t, src, syntax.LangBash, syntax.KeepComments(true))
	out1 := printWith(t, f)
	f2, err := syntax.NewParser(syntax.KeepComments(true)).Parse(strings.NewReader(out1), "")
	if err != nil {
		t.Fatalf("reparse with comments failed: %v", err)
	}
	out2 := printWith(t, f2)
	if out1 != out2 {
		t.Fatalf("comment-preserving print not a fixpoint\nfirst:  %q\nsecond: %q", out1, out2)
	}
	for _, want := range []string{"# leading comment", "# trailing", "# why"} {
		if !strings.Contains(out1, want) {
			t.Fatalf("printed output lost comment %q: %q", want, out1)
		}
	}
}

func TestSimplifyThenRoundTrip(t *testing.T) {
	srcs := []string{
		"echo $(( (x) ))\n",
		"[[ \"$var\" == str ]] && [[ ! -n $b ]]\n",
		"echo \"\\$foo\" $( (bar) )\n",
	}
	for _, src := range srcs {
		f := mustParse(t, src, syntax.LangBash)
		if !syntax.Simplify(f) {
			t.Fatalf("Simplify should report a change for %q", src)
		}
		out1 := printWith(t, f)
		if out1 == "" || !strings.HasSuffix(out1, "\n") {
			t.Fatalf("simplified print must be non-empty and newline-terminated, got %q", out1)
		}
		f2, err := syntax.NewParser().Parse(strings.NewReader(out1), "")
		if err != nil {
			t.Fatalf("simplified output does not reparse: %v\nprinted: %q", err, out1)
		}
		if changed := syntax.Simplify(f2); changed {
			t.Fatalf("simplify not idempotent: reparsed simplified tree changed again for %q", src)
		}
		out2 := printWith(t, f2)
		if out1 != out2 {
			t.Fatalf("simplified print not a fixpoint\nfirst:  %q\nsecond: %q", out1, out2)
		}
	}
}
