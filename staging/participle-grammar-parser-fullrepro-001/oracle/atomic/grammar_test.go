package atomic

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
)

type assign struct {
	Name  string `@Ident "=" @Int`
	After string `@Ident?`
}

func TestSequenceMatchesInOrder(t *testing.T) {
	p := participle.MustBuild[assign]()
	v, err := p.ParseString("", "x = 42")
	if err != nil {
		t.Fatalf("sequence parse failed: %v", err)
	}
	if v.Name != "x42" {
		t.Fatalf("captured %q, want concatenated token values %q", v.Name, "x42")
	}
	if _, err := p.ParseString("", "= x 42"); err == nil {
		t.Fatal("out-of-order input must not parse")
	}
}

type litOnly struct {
	V string `"begin" @Ident "end"`
}

func TestLiteralTerminalMatchesExactValue(t *testing.T) {
	p := participle.MustBuild[litOnly]()
	v, err := p.ParseString("", "begin middle end")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.V != "middle" {
		t.Fatalf("got %q, want %q", v.V, "middle")
	}
	if _, err := p.ParseString("", "Begin middle end"); err == nil {
		t.Fatal("literals must match exactly (case-sensitive by default)")
	}
}

type bareRef struct {
	A string `Ident @Int`
}

func TestTokenTypeReferenceMatchesWithoutCapture(t *testing.T) {
	p := participle.MustBuild[bareRef]()
	v, err := p.ParseString("", "label 7")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.A != "7" {
		t.Fatalf("uncaptured token leaked into field: got %q, want %q", v.A, "7")
	}
	if _, err := p.ParseString("", "7 7"); err == nil {
		t.Fatal("Int token must not satisfy an Ident reference")
	}
}

type alt struct {
	A string `  "a" @Ident`
	B string `| "b" @Ident`
}

func TestAlternationFirstMatchWins(t *testing.T) {
	p := participle.MustBuild[alt]()
	va, err := p.ParseString("", "a left")
	if err != nil {
		t.Fatalf("first alternative failed: %v", err)
	}
	if va.A != "left" || va.B != "" {
		t.Fatalf("first branch must fill A only: %+v", va)
	}
	vb, err := p.ParseString("", "b right")
	if err != nil {
		t.Fatalf("second alternative failed: %v", err)
	}
	if vb.B != "right" || vb.A != "" {
		t.Fatalf("second branch must fill B only: %+v", vb)
	}
}

type grouped struct {
	Head string   `@Ident`
	Tail []string `("," @Ident)*`
}

func TestGroupRepetitionCollectsElements(t *testing.T) {
	p := participle.MustBuild[grouped]()
	v, err := p.ParseString("", "a, b, c")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.Head != "a" || strings.Join(v.Tail, "+") != "b+c" {
		t.Fatalf("unexpected result: %+v", v)
	}
	solo, err := p.ParseString("", "only")
	if err != nil {
		t.Fatalf("zero repetitions must be accepted: %v", err)
	}
	if len(solo.Tail) != 0 {
		t.Fatalf("expected empty tail, got %v", solo.Tail)
	}
}

type optional struct {
	Name string `@Ident`
	Val  int    `("=" @Int)?`
}

func TestOptionalMatchesZeroOrOnce(t *testing.T) {
	p := participle.MustBuild[optional]()
	with, err := p.ParseString("", "n = 3")
	if err != nil {
		t.Fatalf("optional present failed: %v", err)
	}
	if with.Val != 3 {
		t.Fatalf("got %d, want 3", with.Val)
	}
	without, err := p.ParseString("", "n")
	if err != nil {
		t.Fatalf("optional absent failed: %v", err)
	}
	if without.Val != 0 {
		t.Fatalf("absent optional must leave zero value, got %d", without.Val)
	}
}

type plusRep struct {
	Vs []string `@Ident+`
}

func TestPlusRequiresAtLeastOneMatch(t *testing.T) {
	p := participle.MustBuild[plusRep]()
	v, err := p.ParseString("", "a b c")
	if err != nil {
		t.Fatalf("plus repetition failed: %v", err)
	}
	if len(v.Vs) != 3 {
		t.Fatalf("expected 3 captures, got %v", v.Vs)
	}
	if _, err := p.ParseString("", "1"); err == nil {
		t.Fatal("plus must fail with zero matches")
	}
}

type starRep struct {
	Vs  []string `@Ident*`
	End string   `@Int`
}

func TestStarAllowsZeroMatches(t *testing.T) {
	p := participle.MustBuild[starRep]()
	v, err := p.ParseString("", "9")
	if err != nil {
		t.Fatalf("star with zero matches failed: %v", err)
	}
	if len(v.Vs) != 0 || v.End != "9" {
		t.Fatalf("unexpected result: %+v", v)
	}
}

type negation struct {
	Body []string `@~";"* ";"`
}

func TestNegationMatchesAnyOtherToken(t *testing.T) {
	p := participle.MustBuild[negation]()
	v, err := p.ParseString("", "a 1 b ;")
	if err != nil {
		t.Fatalf("negation parse failed: %v", err)
	}
	if strings.Join(v.Body, "+") != "a+1+b" {
		t.Fatalf("negation must capture every non-terminator token: %v", v.Body)
	}
	empty, err := p.ParseString("", ";")
	if err != nil {
		t.Fatalf("immediate terminator failed: %v", err)
	}
	if len(empty.Body) != 0 {
		t.Fatalf("expected no captures, got %v", empty.Body)
	}
}

type posLook struct {
	A string `  (?= Ident "=") @Ident "=" @Int`
	B string `| @Ident`
}

func TestPositiveLookaheadSelectsBranchWithoutConsuming(t *testing.T) {
	p := participle.MustBuild[posLook]()
	va, err := p.ParseString("", "x = 1")
	if err != nil {
		t.Fatalf("lookahead branch failed: %v", err)
	}
	if va.A != "x1" || va.B != "" {
		t.Fatalf("assignment must take the lookahead branch: %+v", va)
	}
	vb, err := p.ParseString("", "solo")
	if err != nil {
		t.Fatalf("fallback branch failed: %v", err)
	}
	if vb.B != "solo" || vb.A != "" {
		t.Fatalf("bare ident must take the fallback branch: %+v", vb)
	}
}

type negLook struct {
	A string `(?! "x") @Ident`
}

func TestNegativeLookaheadBlocksMatch(t *testing.T) {
	p := participle.MustBuild[negLook]()
	v, err := p.ParseString("", "y")
	if err != nil {
		t.Fatalf("non-blocked input failed: %v", err)
	}
	if v.A != "y" {
		t.Fatalf("got %q, want %q", v.A, "y")
	}
	if _, err := p.ParseString("", "x"); err == nil {
		t.Fatal("negative lookahead must reject the blocked token")
	}
}

type typedLit struct {
	V string `@"42":Int`
}

func TestTypedLiteralMatchesValueAndType(t *testing.T) {
	p := participle.MustBuild[typedLit]()
	v, err := p.ParseString("", "42")
	if err != nil {
		t.Fatalf("typed literal failed: %v", err)
	}
	if v.V != "42" {
		t.Fatalf("got %q, want %q", v.V, "42")
	}
	if _, err := p.ParseString("", "43"); err == nil {
		t.Fatal("typed literal must reject a different value of the same type")
	}
}

type namedTag struct {
	Field string `parser:"@Ident (',' Ident)*" json:"field"`
}

func TestParserTagKeyWithSingleQuotes(t *testing.T) {
	p := participle.MustBuild[namedTag]()
	v, err := p.ParseString("", "a, b, c")
	if err != nil {
		t.Fatalf("parser-keyed tag failed: %v", err)
	}
	if v.Field != "a" {
		t.Fatalf("only the @-marked token must be captured: got %q", v.Field)
	}
}

type nonEmpty struct {
	G    string `("a"? "b"? "c"?)!`
	Rest string `@Ident`
}

func TestNonEmptyModifierRejectsEmptyMatch(t *testing.T) {
	p := participle.MustBuild[nonEmpty]()
	if _, err := p.ParseString("", "rest"); err == nil {
		t.Fatal("empty match under ! must be an error")
	} else if !strings.Contains(err.Error(), "cannot be empty") {
		t.Fatalf("error must mention the empty sub-expression: %v", err)
	}
	v, err := p.ParseString("", "b rest")
	if err != nil {
		t.Fatalf("non-empty match failed: %v", err)
	}
	if v.Rest != "rest" {
		t.Fatalf("got %q, want %q", v.Rest, "rest")
	}
}

type captured struct {
	V string `"k" @Ident`
}

type uncaptured struct {
	V string `"k" Ident`
}

func TestCaptureMarkerDoesNotChangeAcceptance(t *testing.T) {
	pc := participle.MustBuild[captured]()
	pu := participle.MustBuild[uncaptured]()
	for _, input := range []string{"k v", "k 1", "v k", "k"} {
		_, errC := pc.ParseString("", input)
		_, errU := pu.ParseString("", input)
		if (errC == nil) != (errU == nil) {
			t.Fatalf("input %q: capture marker changed acceptance (captured err=%v, uncaptured err=%v)", input, errC, errU)
		}
	}
}

type recursiveExpr struct {
	Inner *recursiveExpr `"(" @@ ")"`
	Leaf  string         `| @Ident`
}

func TestRecursiveGrammarNests(t *testing.T) {
	p := participle.MustBuild[recursiveExpr]()
	v, err := p.ParseString("", "((x))")
	if err != nil {
		t.Fatalf("recursive parse failed: %v", err)
	}
	if v.Inner == nil || v.Inner.Inner == nil || v.Inner.Inner.Leaf != "x" {
		t.Fatalf("nesting depth or leaf wrong: %+v", v)
	}
}
