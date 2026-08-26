package atomic

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

func TestUnexpectedTokenErrorShape(t *testing.T) {
	p := participle.MustBuild[assign]()
	_, err := p.ParseString("file.go", "x + 42")
	if err == nil {
		t.Fatal("mismatched token must fail")
	}
	ut, ok := err.(*participle.UnexpectedTokenError)
	if !ok {
		t.Fatalf("error must be *UnexpectedTokenError, got %T", err)
	}
	if ut.Unexpected.Value != "+" {
		t.Fatalf("Unexpected token: got %q", ut.Unexpected.Value)
	}
	if !strings.HasPrefix(ut.Message(), `unexpected token "+"`) {
		t.Fatalf("message must begin with the offending token: %q", ut.Message())
	}
	if ut.Position().Filename != "file.go" || ut.Position().Line != 1 || ut.Position().Column != 3 {
		t.Fatalf("position wrong: %+v", ut.Position())
	}
	if ut.Error() != "file.go:1:3: "+ut.Message() {
		t.Fatalf("Error() must be position-prefixed Message(): %q", ut.Error())
	}
}

func TestTrailingTokensRejectedWithoutAllowTrailing(t *testing.T) {
	p := participle.MustBuild[strConcat]()
	_, err := p.ParseString("", "a = 1 extra")
	if err == nil {
		t.Fatal("trailing tokens must fail the parse by default")
	}
	if !strings.Contains(err.Error(), `unexpected token "extra"`) {
		t.Fatalf("error must point at the first trailing token: %v", err)
	}
	v, err := p.ParseString("", "a = 1 extra", participle.AllowTrailing(true))
	if err != nil {
		t.Fatalf("AllowTrailing must accept the same input: %v", err)
	}
	if v.V != "a1" {
		t.Fatalf("prefix parse result wrong: %+v", v)
	}
}

func TestLexerErrorImplementsErrorInterface(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "Ident", Pattern: `[a-z]+`},
	})
	type w struct {
		A string `@Ident`
	}
	p := participle.MustBuild[w](participle.Lexer(def))
	_, err := p.ParseString("lf", "ABC")
	if err == nil {
		t.Fatal("unlexable input must fail")
	}
	le, ok := err.(*lexer.Error)
	if !ok {
		t.Fatalf("error must be *lexer.Error, got %T", err)
	}
	var pe participle.Error = le
	if pe.Message() != le.Msg {
		t.Fatalf("Message() must return Msg: %q vs %q", pe.Message(), le.Msg)
	}
	if pe.Position() != le.Pos {
		t.Fatalf("Position() must return Pos")
	}
	if !strings.Contains(le.Msg, "invalid input text") {
		t.Fatalf("message must mention invalid input text: %q", le.Msg)
	}
}

func TestErrorfBuildsPositionedError(t *testing.T) {
	pos := lexer.Position{Filename: "f", Line: 2, Column: 3}
	e := participle.Errorf(pos, "boom %d", 42)
	if e.Message() != "boom 42" {
		t.Fatalf("Message(): got %q", e.Message())
	}
	if e.Position() != pos {
		t.Fatalf("Position(): got %+v", e.Position())
	}
	if e.Error() != "f:2:3: boom 42" {
		t.Fatalf("Error(): got %q", e.Error())
	}
}

func TestWrapfKeepsInnerErrorPosition(t *testing.T) {
	inner := participle.Errorf(lexer.Position{Filename: "f", Line: 2, Column: 3}, "inner")
	outer := participle.Wrapf(lexer.Position{Line: 9, Column: 9}, inner, "outer")
	if outer.Message() != "outer: inner" {
		t.Fatalf("wrapped message must compose: %q", outer.Message())
	}
	if outer.Position().Line != 2 || outer.Position().Column != 3 {
		t.Fatalf("wrapping an Error must keep the inner position: %+v", outer.Position())
	}
}

func TestWrapfUsesGivenPositionForPlainErrors(t *testing.T) {
	plainErr := errFrom("plain failure")
	wrapped := participle.Wrapf(lexer.Position{Line: 4, Column: 5}, plainErr, "ctx")
	if wrapped.Message() != "ctx: plain failure" {
		t.Fatalf("message: %q", wrapped.Message())
	}
	if wrapped.Position().Line != 4 || wrapped.Position().Column != 5 {
		t.Fatalf("plain error must use the given position: %+v", wrapped.Position())
	}
}

func TestFormatErrorOmitsZeroPosition(t *testing.T) {
	positioned := participle.Errorf(lexer.Position{Filename: "f", Line: 1, Column: 2}, "m")
	if participle.FormatError(positioned) != "f:1:2: m" {
		t.Fatalf("got %q", participle.FormatError(positioned))
	}
	posless := participle.Errorf(lexer.Position{}, "bare")
	if participle.FormatError(posless) != "bare" {
		t.Fatalf("zero position must render the message alone: %q", participle.FormatError(posless))
	}
}

func TestParseErrorImplementsErrorInterface(t *testing.T) {
	pe := &participle.ParseError{Msg: "pm", Pos: lexer.Position{Filename: "f", Line: 3, Column: 9}}
	var e participle.Error = pe
	if e.Message() != "pm" {
		t.Fatalf("Message(): %q", e.Message())
	}
	if e.Error() != "f:3:9: pm" {
		t.Fatalf("Error(): %q", e.Error())
	}
}

type spinner struct {
	X   []string `(@Ident?)*`
	End string   `";"`
}

func TestRepetitionGuardStopsEmptyLoops(t *testing.T) {
	p := participle.MustBuild[spinner]()
	_, err := p.ParseString("", "a b", participle.AllowTrailing(true))
	if err == nil {
		t.Fatal("an empty-matching repetition must trip the iteration guard")
	}
	if !strings.Contains(err.Error(), "too many iterations") {
		t.Fatalf("error must mention the iteration guard: %v", err)
	}
}

func errFrom(msg string) error { return &plainError{msg} }

type plainError struct{ s string }

func (p *plainError) Error() string { return p.s }
