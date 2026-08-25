package atomic

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

type strConcat struct {
	V string `@Ident "=" @Int`
}

func TestStringCaptureConcatenatesTokens(t *testing.T) {
	p := participle.MustBuild[strConcat]()
	v, err := p.ParseString("", "count = 12")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.V != "count12" {
		t.Fatalf("string captures must concatenate without separator: got %q", v.V)
	}
}

type intCap struct {
	N int `@("-"? Int)`
}

func TestIntCaptureParsesConcatenatedText(t *testing.T) {
	p := participle.MustBuild[intCap]()
	neg, err := p.ParseString("", "-5")
	if err != nil {
		t.Fatalf("negative parse failed: %v", err)
	}
	if neg.N != -5 {
		t.Fatalf("got %d, want -5", neg.N)
	}
	pos, err := p.ParseString("", "7")
	if err != nil {
		t.Fatalf("positive parse failed: %v", err)
	}
	if pos.N != 7 {
		t.Fatalf("got %d, want 7", pos.N)
	}
}

type numCaps struct {
	U uint    `@Int`
	F float64 `@Float`
}

func TestUnsignedAndFloatCaptures(t *testing.T) {
	p := participle.MustBuild[numCaps]()
	v, err := p.ParseString("", "12 3.5")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.U != 12 || v.F != 3.5 {
		t.Fatalf("unexpected values: %+v", v)
	}
}

type badNum struct {
	N int `@Ident`
}

func TestNumericConversionFailureIsPositionedError(t *testing.T) {
	p := participle.MustBuild[badNum]()
	_, err := p.ParseString("nf", "notanumber")
	if err == nil {
		t.Fatal("non-numeric capture into int must fail the parse")
	}
	if !strings.Contains(err.Error(), "failed to conform") {
		t.Fatalf("error must mention conversion failure: %v", err)
	}
	if !strings.HasPrefix(err.Error(), "nf:1:1:") {
		t.Fatalf("error must carry the capturing token position: %v", err)
	}
}

type boolCap struct {
	Flag bool `@("true" | "false")`
	Rest string `@Ident?`
}

func TestBoolCaptureSetsTrueRegardlessOfText(t *testing.T) {
	p := participle.MustBuild[boolCap]()
	vt, err := p.ParseString("", "true")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if vt.Flag != true {
		t.Fatal("matched bool capture must set the field to true")
	}
	vf, err := p.ParseString("", "false")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if vf.Flag != true {
		t.Fatal(`capturing the text "false" must still set the bool field to true`)
	}
}

type boolAbsent struct {
	Name string `@Ident`
	Bang bool   `@"!"?`
}

func TestBoolCaptureFalseWhenUnmatched(t *testing.T) {
	p := participle.MustBuild[boolAbsent]()
	with, err := p.ParseString("", "n !")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if !with.Bang {
		t.Fatal("matched optional bool must be true")
	}
	without, err := p.ParseString("", "n")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if without.Bang {
		t.Fatal("unmatched optional bool must remain false")
	}
}

type sliceCap struct {
	Ns []int `@Int+`
}

func TestSliceCaptureAppendsConvertedElements(t *testing.T) {
	p := participle.MustBuild[sliceCap]()
	v, err := p.ParseString("", "1 2 3")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if len(v.Ns) != 3 || v.Ns[0] != 1 || v.Ns[1] != 2 || v.Ns[2] != 3 {
		t.Fatalf("unexpected slice: %v", v.Ns)
	}
}

type ptrCap struct {
	Name *string `@Ident?`
	Val  int     `@Int`
}

func TestPointerCaptureAllocatesOnlyOnMatch(t *testing.T) {
	p := participle.MustBuild[ptrCap]()
	with, err := p.ParseString("", "tag 5")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if with.Name == nil || *with.Name != "tag" {
		t.Fatalf("matched pointer capture must allocate: %+v", with.Name)
	}
	without, err := p.ParseString("", "6")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if without.Name != nil {
		t.Fatal("unmatched optional pointer must stay nil")
	}
}

type kv struct {
	K string `@Ident "="`
	V int    `@Int`
}

type kvList struct {
	Pairs []kv `@@ ("," @@)*`
}

func TestStructCaptureAccumulatesPerMatch(t *testing.T) {
	p := participle.MustBuild[kvList]()
	v, err := p.ParseString("", "a = 1, b = 2")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if len(v.Pairs) != 2 {
		t.Fatalf("expected 2 structs, got %d", len(v.Pairs))
	}
	if v.Pairs[0].K != "a" || v.Pairs[0].V != 1 || v.Pairs[1].K != "b" || v.Pairs[1].V != 2 {
		t.Fatalf("unexpected pairs: %+v", v.Pairs)
	}
}

type upperVal string

func (u *upperVal) Capture(values []string) error {
	*u = upperVal(strings.ToUpper(strings.Join(values, "")))
	return nil
}

type customCap struct {
	V upperVal `@Ident`
}

func TestCustomCaptureInterfaceReceivesValues(t *testing.T) {
	p := participle.MustBuild[customCap]()
	v, err := p.ParseString("", "hello")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if string(v.V) != "HELLO" {
		t.Fatalf("Capture implementation must control conversion: got %q", v.V)
	}
}

type recorder struct{ calls []string }

func (r *recorder) UnmarshalText(b []byte) error {
	r.calls = append(r.calls, string(b))
	return nil
}

type textUn struct {
	V *recorder `@(Ident Ident)`
}

func TestTextUnmarshalerCalledPerToken(t *testing.T) {
	p := participle.MustBuild[textUn]()
	v, err := p.ParseString("", "aa bb")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.V == nil {
		t.Fatal("captured TextUnmarshaler field must be allocated")
	}
	if len(v.V.calls) != 2 || v.V.calls[0] != "aa" || v.V.calls[1] != "bb" {
		t.Fatalf("UnmarshalText must run once per captured token in order: %v", v.V.calls)
	}
}

type tokCap struct {
	T lexer.Token `@Ident`
}

func TestLexerTokenFieldReceivesToken(t *testing.T) {
	p := participle.MustBuild[tokCap]()
	v, err := p.ParseString("tf", "word")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.T.Value != "word" {
		t.Fatalf("token value: got %q", v.T.Value)
	}
	if v.T.Pos.Filename != "tf" || v.T.Pos.Line != 1 || v.T.Pos.Column != 1 {
		t.Fatalf("token position wrong: %+v", v.T.Pos)
	}
}

type posFields struct {
	Pos    lexer.Position
	Name   string `@Ident`
	EndPos lexer.Position
}

func TestPosAndEndPosPopulated(t *testing.T) {
	p := participle.MustBuild[posFields]()
	v, err := p.ParseString("pf", "  hello")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.Pos.Line != 1 || v.Pos.Column != 3 {
		t.Fatalf("Pos must point at the first consumed token: %+v", v.Pos)
	}
	if v.EndPos.Offset < v.Pos.Offset+len("hello") {
		t.Fatalf("EndPos must not precede the end of consumed input: pos=%+v end=%+v", v.Pos, v.EndPos)
	}
	if v.Pos.Filename != "pf" || v.EndPos.Filename != "pf" {
		t.Fatalf("positions must carry the caller filename: %+v %+v", v.Pos, v.EndPos)
	}
}

type tokensField struct {
	Tokens []lexer.Token
	A      string `@Ident "=" @Ident`
}

func TestTokensFieldRecordsConsumedTokens(t *testing.T) {
	p := participle.MustBuild[tokensField]()
	v, err := p.ParseString("", "a = b")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if len(v.Tokens) != 3 {
		t.Fatalf("Tokens must record every consumed token: got %d", len(v.Tokens))
	}
	if v.Tokens[0].Value != "a" || v.Tokens[1].Value != "=" || v.Tokens[2].Value != "b" {
		t.Fatalf("unexpected token record: %v", v.Tokens)
	}
}
