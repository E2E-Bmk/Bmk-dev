package atomic

import (
	"strings"
	"testing"

	"github.com/alecthomas/participle/v2/lexer"
)

func TestDefaultLexerSymbolTable(t *testing.T) {
	syms := lexer.TextScannerLexer.Symbols()
	want := map[string]lexer.TokenType{
		"EOF":       -1,
		"Ident":     -2,
		"Int":       -3,
		"Float":     -4,
		"Char":      -5,
		"String":    -6,
		"RawString": -7,
		"Comment":   -8,
	}
	for name, typ := range want {
		if got, ok := syms[name]; !ok || got != typ {
			t.Fatalf("symbol %s: got %d (present=%v), want %d", name, got, ok, typ)
		}
	}
}

func TestDefaultLexerRuneTokens(t *testing.T) {
	lx := lexer.LexString("", "a = b")
	toks, err := lexer.ConsumeAll(lx)
	if err != nil {
		t.Fatalf("lex failed: %v", err)
	}
	// a, =, b, EOF
	if len(toks) != 4 {
		t.Fatalf("expected 4 tokens, got %d: %v", len(toks), toks)
	}
	if toks[1].Value != "=" || toks[1].Type != lexer.TokenType('=') {
		t.Fatalf("single-rune token must use the rune code point as its type: %+v", toks[1])
	}
	if !toks[3].EOF() {
		t.Fatal("stream must end with an EOF token")
	}
}

func TestSimpleLexerFirstMatchWins(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "A", Pattern: `a`},
		{Name: "AB", Pattern: `ab`},
	})
	lx, err := def.LexString("", "ab")
	if err != nil {
		t.Fatalf("lex construction failed: %v", err)
	}
	tok, err := lx.Next()
	if err != nil {
		t.Fatalf("first token failed: %v", err)
	}
	if tok.Value != "a" {
		t.Fatalf("earlier rule must win even when a later rule matches longer: got %q", tok.Value)
	}
	if _, err := lx.Next(); err == nil {
		t.Fatal(`remaining "b" matches no rule and must error`)
	}
}

func TestSimpleLexerOrderResolvesAmbiguity(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "AB", Pattern: `ab`},
		{Name: "A", Pattern: `a`},
	})
	lx, _ := def.LexString("", "aab")
	toks, err := lexer.ConsumeAll(lx)
	if err != nil {
		t.Fatalf("lex failed: %v", err)
	}
	if len(toks) != 3 || toks[0].Value != "a" || toks[1].Value != "ab" {
		t.Fatalf("unexpected tokens: %v", toks)
	}
}

func TestSimpleLexerInvalidInputError(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "N", Pattern: `[0-9]+`},
	})
	lx, _ := def.LexString("bad.txt", "x12")
	_, err := lexer.ConsumeAll(lx)
	if err == nil {
		t.Fatal("unmatched input must produce a lexing error")
	}
	lerr, ok := err.(*lexer.Error)
	if !ok {
		t.Fatalf("error must be *lexer.Error, got %T", err)
	}
	if !strings.Contains(lerr.Msg, "invalid input text") {
		t.Fatalf("message must mention invalid input text: %q", lerr.Msg)
	}
	if lerr.Pos.Filename != "bad.txt" || lerr.Pos.Line != 1 || lerr.Pos.Column != 1 {
		t.Fatalf("error position wrong: %+v", lerr.Pos)
	}
}

func TestSimpleLexerSymbolNumbering(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "One", Pattern: `1`},
		{Name: "Two", Pattern: `2`},
		{Name: "Three", Pattern: `3`},
	})
	syms := def.Symbols()
	if syms["EOF"] != lexer.EOF {
		t.Fatalf("EOF symbol must be %d, got %d", lexer.EOF, syms["EOF"])
	}
	if syms["One"] != lexer.EOF-1 || syms["Two"] != lexer.EOF-2 || syms["Three"] != lexer.EOF-3 {
		t.Fatalf("rule symbols must descend from EOF in rule order: %v", syms)
	}
}

func TestSimpleLexerInvalidPatternRejected(t *testing.T) {
	if _, err := lexer.NewSimple([]lexer.SimpleRule{{Name: "Bad", Pattern: `[`}}); err == nil {
		t.Fatal("invalid regular expression must be rejected")
	}
	defer func() {
		if recover() == nil {
			t.Fatal("MustSimple must panic on an invalid pattern")
		}
	}()
	lexer.MustSimple([]lexer.SimpleRule{{Name: "Bad", Pattern: `[`}})
}

func statefulDef(t *testing.T) *lexer.StatefulDefinition {
	t.Helper()
	return lexer.MustStateful(lexer.Rules{
		"Root": {
			{Name: "String", Pattern: `"`, Action: lexer.Push("Str")},
			{Name: "Ident", Pattern: `\w+`},
			{Name: "WS", Pattern: `\s+`},
		},
		"Str": {
			{Name: "Expr", Pattern: `\${`, Action: lexer.Push("Exp")},
			{Name: "StringEnd", Pattern: `"`, Action: lexer.Pop()},
			{Name: "Chars", Pattern: `[^"$]+`},
		},
		"Exp": {
			{Name: "ExprEnd", Pattern: `}`, Action: lexer.Pop()},
			{Name: "Ident", Pattern: `\w+`},
		},
	})
}

func TestStatefulLexerPushPop(t *testing.T) {
	def := statefulDef(t)
	lx, err := def.LexString("", `hi "a${b}c"`)
	if err != nil {
		t.Fatalf("lex construction failed: %v", err)
	}
	toks, err := lexer.ConsumeAll(lx)
	if err != nil {
		t.Fatalf("lex failed: %v", err)
	}
	byRune := lexer.SymbolsByRune(def)
	var names []string
	for _, tok := range toks {
		if tok.EOF() {
			break
		}
		names = append(names, byRune[tok.Type])
	}
	want := "Ident WS String Chars Expr Ident ExprEnd Chars StringEnd"
	if strings.Join(names, " ") != want {
		t.Fatalf("token type sequence:\n got %v\nwant %v", strings.Join(names, " "), want)
	}
}

func TestStatefulLexerIncludeSplicesRules(t *testing.T) {
	def := lexer.MustStateful(lexer.Rules{
		"Common": {
			{Name: "WS", Pattern: `\s+`},
		},
		"Root": {
			lexer.Include("Common"),
			{Name: "Word", Pattern: `[a-z]+`},
			{Name: "Enter", Pattern: `\{`, Action: lexer.Push("Inner")},
		},
		"Inner": {
			lexer.Include("Common"),
			{Name: "Num", Pattern: `[0-9]+`},
			{Name: "Leave", Pattern: `\}`, Action: lexer.Pop()},
		},
	})
	lx, _ := def.LexString("", "ab {1 2} cd")
	toks, err := lexer.ConsumeAll(lx)
	if err != nil {
		t.Fatalf("included whitespace rule must apply in both states: %v", err)
	}
	if len(toks) == 0 || !toks[len(toks)-1].EOF() {
		t.Fatal("stream must terminate with EOF")
	}
}

func TestStatefulLexerNoMatchError(t *testing.T) {
	def := statefulDef(t)
	lx, _ := def.LexString("sf", "!")
	_, err := lexer.ConsumeAll(lx)
	if err == nil {
		t.Fatal("input matching no rule of the active state must error")
	}
	if !strings.Contains(err.Error(), "invalid input text") {
		t.Fatalf("error must mention invalid input text: %v", err)
	}
}

func TestConsumeAllIncludesEOF(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "A", Pattern: `a+`},
	})
	lx, _ := def.LexString("", "aaa")
	toks, err := lexer.ConsumeAll(lx)
	if err != nil {
		t.Fatalf("lex failed: %v", err)
	}
	if len(toks) != 2 || toks[0].Value != "aaa" || !toks[1].EOF() {
		t.Fatalf("expected value token plus EOF, got %v", toks)
	}
}

func TestSymbolsByRuneInvertsSymbols(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "X", Pattern: `x`},
		{Name: "Y", Pattern: `y`},
	})
	fwd := def.Symbols()
	if _, ok := fwd["X"]; !ok {
		t.Fatalf("symbol table must contain rule X: %v", fwd)
	}
	if _, ok := fwd["Y"]; !ok {
		t.Fatalf("symbol table must contain rule Y: %v", fwd)
	}
	rev := lexer.SymbolsByRune(def)
	for name, typ := range fwd {
		if rev[typ] != name {
			t.Fatalf("inverse mapping broken for %s (%d): got %q", name, typ, rev[typ])
		}
	}
}

func TestPositionStringForms(t *testing.T) {
	withFile := lexer.Position{Filename: "f.go", Line: 3, Column: 9}
	if withFile.String() != "f.go:3:9" {
		t.Fatalf("got %q, want %q", withFile.String(), "f.go:3:9")
	}
	noFile := lexer.Position{Line: 2, Column: 4}
	if noFile.String() != "2:4" {
		t.Fatalf("empty filename must be omitted: got %q", noFile.String())
	}
}

func TestEOFTokenConstruction(t *testing.T) {
	pos := lexer.Position{Filename: "e", Line: 1, Column: 5}
	tok := lexer.EOFToken(pos)
	if !tok.EOF() {
		t.Fatal("EOFToken must report EOF")
	}
	if tok.Type != lexer.EOF {
		t.Fatalf("EOF token type must be %d, got %d", lexer.EOF, tok.Type)
	}
	if tok.Pos != pos {
		t.Fatalf("EOF token must keep the given position: %+v", tok.Pos)
	}
}

func TestUpgradePeekAndNextSkipElided(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "Word", Pattern: `[a-z]+`},
		{Name: "WS", Pattern: `\s+`},
	})
	lx, _ := def.LexString("", "one two")
	pl, err := lexer.Upgrade(lx, def.Symbols()["WS"])
	if err != nil {
		t.Fatalf("upgrade failed: %v", err)
	}
	if pk := pl.Peek(); pk.Value != "one" {
		t.Fatalf("peek: got %q", pk.Value)
	}
	if nx := pl.Next(); nx.Value != "one" {
		t.Fatalf("next: got %q", nx.Value)
	}
	if nx := pl.Next(); nx.Value != "two" {
		t.Fatalf("elided whitespace must be skipped: got %q", nx.Value)
	}
	if !pl.Next().EOF() {
		t.Fatal("exhausted stream must yield EOF")
	}
}

func TestMustWrapsDefinitionErrors(t *testing.T) {
	def := lexer.Must(lexer.NewSimple([]lexer.SimpleRule{{Name: "A", Pattern: `a`}}))
	if def == nil {
		t.Fatal("Must must return the definition when there is no error")
	}
	defer func() {
		if recover() == nil {
			t.Fatal("Must must panic when given an error")
		}
	}()
	lexer.Must(lexer.New(lexer.Rules{"Root": {{Name: "Bad", Pattern: `[`}}}))
}
