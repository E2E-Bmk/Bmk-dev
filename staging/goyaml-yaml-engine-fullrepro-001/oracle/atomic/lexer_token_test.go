package atomic

import (
	"strings"
	"testing"

	"github.com/goccy/go-yaml/lexer"
)

// Verifies: Syntax Tree and Tokens > Tokenizing (structural token types).
func TestTokenizeStructuralTypes(t *testing.T) {
	tokens := lexer.Tokenize("a: [1, 2]\n")
	var kinds []string
	for _, tk := range tokens {
		kinds = append(kinds, tk.Type.String())
	}
	want := []string{"String", "MappingValue", "SequenceStart", "Integer", "CollectEntry", "Integer", "SequenceEnd"}
	wantEqual(t, kinds, want, "token type sequence")
}

// Verifies: Syntax Tree and Tokens > Tokenizing (scalar token kinds).
func TestTokenizeScalarKinds(t *testing.T) {
	tokens := lexer.Tokenize("s: hi\nn: 42\nb: true\n# note\n")
	byValue := map[string]string{}
	for _, tk := range tokens {
		byValue[tk.Value] = tk.Type.String()
	}
	if byValue["hi"] != "String" {
		t.Fatalf("hi tokenized as %q, want String", byValue["hi"])
	}
	if byValue["42"] != "Integer" {
		t.Fatalf("42 tokenized as %q, want Integer", byValue["42"])
	}
	if byValue["true"] != "Bool" {
		t.Fatalf("true tokenized as %q, want Bool", byValue["true"])
	}
	if byValue[" note"] != "Comment" {
		t.Fatalf("comment tokenized as %q, want Comment (value %v)", byValue[" note"], byValue)
	}
}

// Verifies: Syntax Tree and Tokens > Tokenizing (Value carries the cleaned
// scalar text while Origin carries the exact source text).
func TestTokenValueVersusOrigin(t *testing.T) {
	tokens := lexer.Tokenize("a: [1, x]\n")
	// The x scalar sits after a space: origin keeps the space, value is clean.
	var found bool
	for _, tk := range tokens {
		if tk.Value == "x" {
			found = true
			if tk.Origin != " x" {
				t.Fatalf("origin of x = %q, want \" x\"", tk.Origin)
			}
		}
	}
	if !found {
		t.Fatal("token with value x not found")
	}
}

// Verifies: Syntax Tree and Tokens > Tokenizing (origins concatenate to the
// input; trailing newlines after a final plain scalar are dropped).
func TestTokenOriginsConcatenate(t *testing.T) {
	// Input ending in a comment reproduces exactly.
	exact := "a: [1, x]\nb: 4\n# c\n"
	tokens := lexer.Tokenize(exact)
	if len(tokens) == 0 {
		t.Fatal("no tokens produced")
	}
	var sb strings.Builder
	for _, tk := range tokens {
		sb.WriteString(tk.Origin)
	}
	if sb.String() != exact {
		t.Fatalf("concatenated origins %q != input %q", sb.String(), exact)
	}

	// Input ending in a plain scalar plus newline reproduces without the
	// final newline.
	trailing := "a: [1, x]\n# c\nb: true\n"
	var sb2 strings.Builder
	for _, tk := range lexer.Tokenize(trailing) {
		sb2.WriteString(tk.Origin)
	}
	if sb2.String() != strings.TrimSuffix(trailing, "\n") {
		t.Fatalf("concatenated origins %q != input-minus-final-newline %q", sb2.String(), strings.TrimSuffix(trailing, "\n"))
	}
}

// Verifies: Syntax Tree and Tokens > Tokenizing (positions: 1-based line and
// column, byte offset, indent).
func TestTokenPositions(t *testing.T) {
	src := "a:\n  b: 1\n"
	tokens := lexer.Tokenize(src)
	type pos struct{ line, column, offset, indent int }
	got := map[string]pos{}
	for _, tk := range tokens {
		got[tk.Type.String()+":"+tk.Value] = pos{tk.Position.Line, tk.Position.Column, tk.Position.Offset, tk.Position.IndentNum}
	}
	if p := got["String:a"]; p != (pos{1, 1, 1, 0}) {
		t.Fatalf("token a position = %+v, want line=1 col=1 offset=1 indent=0", p)
	}
	if p := got["String:b"]; p != (pos{2, 3, 6, 2}) {
		t.Fatalf("token b position = %+v, want line=2 col=3 offset=6 indent=2", p)
	}
	if p := got["Integer:1"]; p != (pos{2, 6, 9, 2}) {
		t.Fatalf("token 1 position = %+v, want line=2 col=6 offset=9 indent=2", p)
	}
}
