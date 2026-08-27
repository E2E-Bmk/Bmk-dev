package shellgate_test

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"mvdan.cc/sh/v3/receipt"
	"mvdan.cc/sh/v3/syntax"
	"strings"
	"testing"
)

func hash(raw []byte) string {
	sum := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(sum[:])
}
func shellReceipt(t *testing.T, root string) receipt.ShellReceipt {
	t.Helper()
	source := []byte("name=" + root + "\nprintf '%s\\n' \"$name\" > output.txt\n")
	plan := receipt.NewShellPlan()
	if _, err := plan.SelectSource("", "posix", source); err == nil {
		t.Fatal("empty source accepted")
	}
	plan, err := plan.SelectSource("script-"+root, "posix", source)
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeSyntax().IncludeFormatted().IncludeExpansion().IncludeExecution()
	syntaxFact := &receipt.SyntaxFact{Name: "script-" + root, Dialect: "posix", NodeID: "file/0/" + root, SourceDigest: hash(source), Extent: len(source), Valid: true}
	format := &receipt.FormatFact{Bytes: []byte("name=" + root + "\nprintf '%s\\n' \"$name\" >output.txt\n"), SourceDigest: hash(source), SyntaxID: syntaxFact.NodeID, Idempotent: true, Projection: "api"}
	expansion := &receipt.ExpansionFact{Fields: []string{root, "output.txt"}, EnvironmentGeneration: 1, Pattern: "*.txt", Value: "output.txt", Matched: true}
	execution := &receipt.ExecutionFact{Stdout: root + "\n", Dir: "sandbox", Status: 0, EnvironmentGeneration: 1, Projection: "api"}
	journal := receipt.NewEffectJournal()
	first := journal.Record(receipt.EffectFact{Kind: "write", Path: "sandbox/output.txt", Digest: hash([]byte(root + "\n")), Complete: true})
	if first.Seq != 1 || len(journal.Entries()) != 1 {
		t.Fatal("effect journal lost order")
	}
	got, err := receipt.Capture(plan, syntaxFact, format, expansion, execution, journal)
	if err != nil {
		t.Fatal(err)
	}
	if got.Digest() == "" || got.Validate() != nil {
		t.Fatal("invalid shell receipt")
	}
	format.Bytes[0] = 'X'
	if got.Format.Bytes[0] == 'X' {
		t.Fatal("capture retained format bytes")
	}
	return got
}
func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	got := shellReceipt(t, root)
	switch family {
	case "M-PARSE-DIALECT":
		bad := got
		v := *got.Syntax
		bad.Syntax = &v
		bad.Syntax.Dialect = "bash"
		if bad.Validate() == nil {
			t.Fatal("cross-dialect syntax validated")
		}
	case "M-AST-IDENTITY":
		bad := got
		v := *got.Syntax
		f := *got.Format
		bad.Syntax = &v
		bad.Format = &f
		bad.Syntax.SourceDigest = "sha256:bad"
		bad.Format.SourceDigest = "sha256:bad"
		if bad.Validate() == nil {
			t.Fatal("foreign AST identity validated")
		}
	case "M-PRINT-IDEMPOTENCE":
		bad := got
		v := *got.Format
		bad.Format = &v
		bad.Format.Idempotent = false
		if bad.Validate() == nil {
			t.Fatal("non-idempotent format validated")
		}
	case "M-WORD-EXPANSION":
		bad := got
		v := *got.Expansion
		bad.Expansion = &v
		bad.Expansion.EnvironmentGeneration = 2
		if bad.Validate() == nil {
			t.Fatal("foreign expansion generation validated")
		}
	case "M-PATTERN-MATCH":
		bad := got
		v := *got.Expansion
		bad.Expansion = &v
		bad.Expansion.Matched = false
		if bad.Validate() == nil {
			t.Fatal("false pattern outcome validated")
		}
	case "M-RUNNER-ENVIRONMENT":
		bad := got
		v := *got.Execution
		bad.Execution = &v
		bad.Execution.Cancelled = true
		if bad.Validate() == nil {
			t.Fatal("cancelled execution validated")
		}
	case "M-FILESYSTEM-EFFECT":
		bad := got
		bad.Effects = append([]receipt.EffectFact(nil), got.Effects...)
		bad.Effects[0].Error = "write failed"
		if bad.Validate() == nil {
			t.Fatal("failed effect claimed completion")
		}
	case "M-CLI-API-EQUIVALENCE":
		other := got
		f := *got.Format
		e := *got.Execution
		other.Format = &f
		other.Execution = &e
		other.Format.Projection = "shfmt"
		other.Execution.Projection = "gosh"
		if !got.Equivalent(other) {
			t.Fatal("CLI and API projections diverged")
		}
	default:
		t.Fatalf("unknown family %q", family)
	}
}
func runNative(t *testing.T, root, _ string) {
	t.Helper()
	parser := syntax.NewParser()
	file, err := parser.Parse(strings.NewReader("echo "+root+"\n"), "")
	if err != nil {
		t.Fatal(err)
	}
	var out bytes.Buffer
	printer := syntax.NewPrinter()
	if err := printer.Print(&out, file); err != nil {
		t.Fatal(err)
	}
	if out.String() != "echo "+root+"\n" {
		t.Fatal("native printer drift")
	}
	if _, err := parser.Parse(strings.NewReader("if then\n"), ""); err == nil {
		t.Fatal("invalid native syntax accepted")
	}
}
