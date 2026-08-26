package integration

import (
	"errors"
	"fmt"
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

var badInputs = []string{
	"if true; then",
	"echo ${",
	"foo(",
	"case x in a)",
	"echo \"unclosed",
	"((1 +",
	"foo )",
	"do echo\n",
}

func TestParseErrorRenderingAgreesWithPosition(t *testing.T) {
	for _, src := range badInputs {
		_, err := syntax.NewParser().Parse(strings.NewReader(src), "script.sh")
		if err == nil {
			t.Fatalf("expected error for %q", src)
		}
		var pe syntax.ParseError
		if !errors.As(err, &pe) {
			t.Fatalf("error for %q is %T, want ParseError", src, err)
		}
		want := fmt.Sprintf("script.sh:%d:%d: %s", pe.Pos.Line(), pe.Pos.Col(), pe.Text)
		if err.Error() != want {
			t.Fatalf("rendered error %q does not recompose from fields, want %q", err.Error(), want)
		}
		if pe.Filename != "script.sh" {
			t.Fatalf("ParseError.Filename = %q, want script.sh", pe.Filename)
		}
		off := int(pe.Pos.Offset())
		if off > len(src) {
			t.Fatalf("error offset %d beyond input length %d for %q", off, len(src), src)
		}
		line, col := lineColFromOffset(src, off)
		if int(pe.Pos.Line()) != line || int(pe.Pos.Col()) != col {
			t.Fatalf("error position %d:%d disagrees with source counting %d:%d for %q",
				pe.Pos.Line(), pe.Pos.Col(), line, col, src)
		}
	}
}

func TestFileNameThreading(t *testing.T) {
	f, err := syntax.NewParser().Parse(strings.NewReader("echo ok\n"), "named.sh")
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if f.Name != "named.sh" {
		t.Fatalf("File.Name = %q, want named.sh", f.Name)
	}
	_, err = syntax.NewParser().Parse(strings.NewReader("echo ${"), "")
	if err == nil {
		t.Fatal("expected error")
	}
	if strings.HasPrefix(err.Error(), ":") || strings.Contains(err.Error(), ".sh") {
		t.Fatalf("unnamed parse error should carry no filename prefix: %q", err.Error())
	}
	var pe syntax.ParseError
	if !errors.As(err, &pe) || pe.Filename != "" {
		t.Fatalf("unnamed ParseError.Filename = %q, want empty", pe.Filename)
	}
}

func TestIncompleteAcrossEntryPoints(t *testing.T) {
	incomplete := []string{"if true; then\n", "echo \"open\n", "foo | \n", "echo $(cat\n"}
	complete := []string{"foo )\n", "do echo\n", ";;\n"}

	for _, src := range incomplete {
		_, err := syntax.NewParser().Parse(strings.NewReader(src), "")
		if err == nil {
			t.Fatalf("expected error for %q", src)
		}
		if !syntax.IsIncomplete(err) {
			t.Fatalf("Parse error for %q should classify as incomplete: %v", src, err)
		}
		var pe syntax.ParseError
		if !errors.As(err, &pe) || !pe.Incomplete {
			t.Fatalf("ParseError.Incomplete should be true for %q", src)
		}
	}
	for _, src := range complete {
		_, err := syntax.NewParser().Parse(strings.NewReader(src), "")
		if err == nil {
			t.Fatalf("expected error for %q", src)
		}
		if syntax.IsIncomplete(err) {
			t.Fatalf("Parse error for %q should not classify as incomplete: %v", src, err)
		}
	}

	// The same classification must hold for errors surfaced by the
	// incremental entry points.
	for st, err := range syntax.NewParser().StmtsSeq(strings.NewReader("echo hi\nif true; then\n")) {
		_ = st
		if err != nil {
			if !syntax.IsIncomplete(err) {
				t.Fatalf("StmtsSeq error should be incomplete: %v", err)
			}
		}
	}
	var seqErr error
	for _, err := range syntax.NewParser().InteractiveSeq(strings.NewReader("foo )")) {
		if err != nil {
			seqErr = err
			break
		}
	}
	if seqErr == nil {
		t.Fatal("expected InteractiveSeq error")
	}
	if syntax.IsIncomplete(seqErr) {
		t.Fatalf("InteractiveSeq syntax error should not be incomplete: %v", seqErr)
	}

	// Non-parse errors never classify as incomplete.
	_, langErr := syntax.NewParser(syntax.Variant(syntax.LangPOSIX)).
		Parse(strings.NewReader("a=(1 2)\n"), "")
	if langErr == nil {
		t.Fatal("expected LangError")
	}
	if syntax.IsIncomplete(langErr) {
		t.Fatalf("LangError should not classify as incomplete: %v", langErr)
	}
}
