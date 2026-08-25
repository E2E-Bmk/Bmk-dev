package integration

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

func commentLexer() *lexer.StatefulDefinition {
	return lexer.MustSimple([]lexer.SimpleRule{
		{Name: "Comment", Pattern: `//[^\n]*`},
		{Name: "String", Pattern: `"(\\"|[^"])*"`},
		{Name: "Int", Pattern: `[0-9]+`},
		{Name: "Ident", Pattern: `[a-zA-Z_]\w*`},
		{Name: "Punct", Pattern: `[=,;]`},
		{Name: "WS", Pattern: `\s+`},
	})
}

type elideKV struct {
	Key string `@Ident "="`
	Val int    `@Int`
}

func TestElideDropsTokensAtEveryPosition(t *testing.T) {
	p := participle.MustBuild[elideKV](
		participle.Lexer(commentLexer()),
		participle.Elide("WS", "Comment"),
	)
	v, err := p.ParseString("", "  // leading\n  k // mid\n = // more\n 7 // trailing")
	if err != nil {
		t.Fatalf("elided tokens must be invisible to the grammar: %v", err)
	}
	if v.Key != "k" || v.Val != 7 {
		t.Fatalf("unexpected result: %+v", v)
	}
}

type docDecl struct {
	Doc  string `@Comment?`
	Name string `@Ident`
}

func TestExplicitMatchOfElidedToken(t *testing.T) {
	p := participle.MustBuild[docDecl](
		participle.Lexer(commentLexer()),
		participle.Elide("WS", "Comment"),
	)
	with, err := p.ParseString("", "// doc line\nfoo")
	if err != nil {
		t.Fatalf("explicit reference to elided type must match: %v", err)
	}
	if with.Doc != "// doc line" || with.Name != "foo" {
		t.Fatalf("unexpected result: %+v", with)
	}
	without, err := p.ParseString("", "bar")
	if err != nil {
		t.Fatalf("optional elided match must accept absence: %v", err)
	}
	if without.Doc != "" || without.Name != "bar" {
		t.Fatalf("unexpected result: %+v", without)
	}
}

type quoted struct {
	Key string `@Ident "="`
	Val string `@String`
}

func TestUnquoteDefaultsToStringTokens(t *testing.T) {
	p := participle.MustBuild[quoted](
		participle.Lexer(commentLexer()),
		participle.Elide("WS", "Comment"),
		participle.Unquote(),
	)
	v, err := p.ParseString("", `name = "hello \"world\""`)
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.Val != `hello "world"` {
		t.Fatalf("Unquote must strip quoting and resolve escapes: got %q", v.Val)
	}
}

func TestUnquoteInvalidStringFailsParse(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "String", Pattern: `"(\\.|[^"])*"`},
		{Name: "WS", Pattern: `\s+`},
	})
	type g struct {
		V string `@String`
	}
	p := participle.MustBuild[g](participle.Lexer(def), participle.Unquote())
	_, err := p.ParseString("", `"\q"`)
	if err == nil {
		t.Fatal("a string with an invalid escape must fail the parse under Unquote")
	}
	if !strings.Contains(err.Error(), "invalid quoted string") {
		t.Fatalf("error must mention the invalid quoted string: %v", err)
	}
}

type upperG struct {
	A string `@Ident`
}

func TestUpperNormalisesListedTokenTypes(t *testing.T) {
	p := participle.MustBuild[upperG](
		participle.Lexer(commentLexer()),
		participle.Elide("WS", "Comment"),
		participle.Upper("Ident"),
	)
	v, err := p.ParseString("", "hello")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.A != "HELLO" {
		t.Fatalf("Upper must transform values before capture: got %q", v.A)
	}
}

func TestMapAppliesInOptionOrder(t *testing.T) {
	p := participle.MustBuild[upperG](
		participle.Lexer(commentLexer()),
		participle.Elide("WS", "Comment"),
		participle.Map(func(tok lexer.Token) (lexer.Token, error) {
			tok.Value = tok.Value + "-a"
			return tok, nil
		}, "Ident"),
		participle.Map(func(tok lexer.Token) (lexer.Token, error) {
			tok.Value = tok.Value + "-b"
			return tok, nil
		}, "Ident"),
	)
	v, err := p.ParseString("", "x")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.A != "x-a-b" {
		t.Fatalf("mappers must compose in option order: got %q", v.A)
	}
}

func TestMapWithoutSymbolsAppliesToAllTokens(t *testing.T) {
	type pair struct {
		A string `@Ident`
		B string `@Int`
	}
	p := participle.MustBuild[pair](
		participle.Lexer(commentLexer()),
		participle.Elide("WS", "Comment"),
		participle.Map(func(tok lexer.Token) (lexer.Token, error) {
			if !tok.EOF() {
				tok.Value = "<" + tok.Value + ">"
			}
			return tok, nil
		}),
	)
	v, err := p.ParseString("", "a 1")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.A != "<a>" || v.B != "<1>" {
		t.Fatalf("mapper without symbols must touch every token: %+v", v)
	}
}

func TestCaseInsensitiveLiteralsKeepInputSpelling(t *testing.T) {
	type sel struct {
		Kw    string `@"select"`
		Table string `@Ident`
	}
	p := participle.MustBuild[sel](participle.CaseInsensitive("Ident"))
	v, err := p.ParseString("", "SELECT users")
	if err != nil {
		t.Fatalf("case-insensitive literal must match: %v", err)
	}
	if v.Kw != "SELECT" {
		t.Fatalf("captured value must keep the input spelling: got %q", v.Kw)
	}
	if v.Table != "users" {
		t.Fatalf("got %q", v.Table)
	}
	pSensitive := participle.MustBuild[sel]()
	if _, err := pSensitive.ParseString("", "SELECT users"); err == nil {
		t.Fatal("without CaseInsensitive the literal must not match a different case")
	}
}

type laAttr struct {
	Key   string `@Ident "="`
	Value string `@Int`
}

type laGroup struct {
	Name string `@Ident "{" "}"`
}

type laEntry struct {
	Attr  *laAttr  `  @@`
	Group *laGroup `| @@`
}

func TestBranchDisambiguationAcrossLookaheads(t *testing.T) {
	for _, n := range []int{1, 2, participle.MaxLookahead} {
		p := participle.MustBuild[laEntry](participle.UseLookahead(n))
		va, err := p.ParseString("", "k = 1")
		if err != nil {
			t.Fatalf("lookahead %d: attribute branch failed: %v", n, err)
		}
		if va.Attr == nil || va.Attr.Key != "k" || va.Attr.Value != "1" || va.Group != nil {
			t.Fatalf("lookahead %d: unexpected capture: %+v", n, va)
		}
		vb, err := p.ParseString("", "blk { }")
		if err != nil {
			t.Fatalf("lookahead %d: group branch sharing an Ident prefix must backtrack: %v", n, err)
		}
		if vb.Group == nil || vb.Group.Name != "blk" || vb.Attr != nil {
			t.Fatalf("lookahead %d: unexpected capture: %+v", n, vb)
		}
	}
}

func TestCustomLexerDrivesParser(t *testing.T) {
	def := lexer.MustStateful(lexer.Rules{
		"Root": {
			{Name: "String", Pattern: `"`, Action: lexer.Push("Str")},
			{Name: "Ident", Pattern: `\w+`},
			{Name: "Eq", Pattern: `=`},
			{Name: "WS", Pattern: `\s+`},
		},
		"Str": {
			{Name: "StringEnd", Pattern: `"`, Action: lexer.Pop()},
			{Name: "Chars", Pattern: `[^"]+`},
		},
	})
	type g struct {
		Key string `@Ident Eq`
		Val string `String @Chars StringEnd`
	}
	p := participle.MustBuild[g](participle.Lexer(def), participle.Elide("WS"))
	v, err := p.ParseString("", `greeting = "hi there"`)
	if err != nil {
		t.Fatalf("stateful lexer + parser failed: %v", err)
	}
	if v.Key != "greeting" || v.Val != "hi there" {
		t.Fatalf("unexpected result: %+v", v)
	}
}
