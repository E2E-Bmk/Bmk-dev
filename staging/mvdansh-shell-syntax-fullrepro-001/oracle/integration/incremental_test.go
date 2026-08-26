package integration

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

// wholeSource concatenates the bash corpus into one multi-statement script.
func wholeSource() string {
	var sb strings.Builder
	for _, src := range bashCorpus {
		sb.WriteString(src)
	}
	return sb.String()
}

func TestStmtsSeqAgreesWithParse(t *testing.T) {
	src := wholeSource()
	batch := mustParse(t, src, syntax.LangBash)

	var seq []*syntax.Stmt
	for st, err := range syntax.NewParser().StmtsSeq(strings.NewReader(src)) {
		if err != nil {
			t.Fatalf("StmtsSeq error: %v", err)
		}
		seq = append(seq, st)
	}
	if len(seq) != len(batch.Stmts) {
		t.Fatalf("StmtsSeq yielded %d statements, Parse %d", len(seq), len(batch.Stmts))
	}
	for i := range seq {
		a := printWith(t, batch.Stmts[i])
		b := printWith(t, seq[i])
		if a != b {
			t.Fatalf("statement %d differs between Parse and StmtsSeq\nparse:    %q\nstmtsseq: %q", i, a, b)
		}
	}
}

func TestInteractiveSeqAgreesWithParse(t *testing.T) {
	src := wholeSource()
	batch := mustParse(t, src, syntax.LangBash)

	var seq []*syntax.Stmt
	for stmts, err := range syntax.NewParser().InteractiveSeq(strings.NewReader(src)) {
		if err != nil {
			t.Fatalf("InteractiveSeq error: %v", err)
		}
		seq = append(seq, stmts...)
	}
	if len(seq) != len(batch.Stmts) {
		t.Fatalf("InteractiveSeq yielded %d statements, Parse %d", len(seq), len(batch.Stmts))
	}
	for i := range seq {
		a := printWith(t, batch.Stmts[i])
		b := printWith(t, seq[i])
		if a != b {
			t.Fatalf("statement %d differs between Parse and InteractiveSeq\nparse:       %q\ninteractive: %q", i, a, b)
		}
	}
}
