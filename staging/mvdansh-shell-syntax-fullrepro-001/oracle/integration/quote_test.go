package integration

import (
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
)

var trickyStrings = []string{
	"plain",
	"has space",
	"semi;colon",
	"dollar$var",
	"sq'uote",
	"dq\"uote",
	"tab\there",
	"new\nline",
	"uni•code",
	"back\\slash",
	"glob*[a]?",
	"~tilde",
	"#hash",
	"a=b",
	"(paren)",
	"&&and||or",
	"bell\a",
}

// quoteThenParse asserts CVI 5: the quoted form must parse as exactly one
// argument word with no expansion parts. It returns that word.
func quoteThenParse(t *testing.T, s string, lang syntax.LangVariant) *syntax.Word {
	t.Helper()
	quoted, err := syntax.Quote(s, lang)
	if err != nil {
		t.Fatalf("quote %q under %v: %v", s, lang, err)
	}
	f, err := syntax.NewParser(syntax.Variant(lang)).Parse(strings.NewReader("echo "+quoted+"\n"), "")
	if err != nil {
		t.Fatalf("quoted form %q of %q does not parse under %v: %v", quoted, s, lang, err)
	}
	call, ok := f.Stmts[0].Cmd.(*syntax.CallExpr)
	if !ok {
		t.Fatalf("quoted form %q of %q parsed to %T, want call", quoted, s, f.Stmts[0].Cmd)
	}
	if len(call.Args) != 2 {
		t.Fatalf("quoted form %q of %q split into %d words, want 1", quoted, s, len(call.Args)-1)
	}
	w := call.Args[1]
	for _, part := range w.Parts {
		switch part.(type) {
		case *syntax.Lit, *syntax.SglQuoted, *syntax.DblQuoted:
		default:
			t.Fatalf("quoted form %q of %q contains expansion part %T", quoted, s, part)
		}
	}
	return w
}

func TestQuoteParseAgreementBash(t *testing.T) {
	for _, s := range trickyStrings {
		quoteThenParse(t, s, syntax.LangBash)
	}
}

func TestQuoteParseAgreementMksh(t *testing.T) {
	for _, s := range trickyStrings {
		quoteThenParse(t, s, syntax.LangMirBSDKorn)
	}
}

// literalContent extracts the plain string content of a word whose parts
// carry no escape sequences, or reports false if it cannot.
func literalContent(w *syntax.Word) (string, bool) {
	var sb strings.Builder
	for _, part := range w.Parts {
		switch p := part.(type) {
		case *syntax.Lit:
			sb.WriteString(p.Value)
		case *syntax.SglQuoted:
			if p.Dollar {
				return "", false
			}
			sb.WriteString(p.Value)
		case *syntax.DblQuoted:
			for _, inner := range p.Parts {
				lit, ok := inner.(*syntax.Lit)
				if !ok {
					return "", false
				}
				sb.WriteString(lit.Value)
			}
		default:
			return "", false
		}
	}
	return sb.String(), true
}

func TestQuoteContentPreserved(t *testing.T) {
	for _, s := range trickyStrings {
		w := quoteThenParse(t, s, syntax.LangBash)
		content, ok := literalContent(w)
		if !ok {
			// Strings needing $'...' escapes are exempt from the
			// content-equality half of the invariant.
			continue
		}
		if content != s {
			t.Fatalf("quoted content %q does not match original %q", content, s)
		}
	}
}
