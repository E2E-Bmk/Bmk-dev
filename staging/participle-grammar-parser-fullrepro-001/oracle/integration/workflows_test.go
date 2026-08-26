package integration

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

type iniProp struct {
	Key   string `@Ident "="`
	Value string `@String`
}

type iniSection struct {
	Name  string    `"[" @Ident "]"`
	Props []iniProp `@@*`
}

type iniFile struct {
	Globals  []iniProp    `@@*`
	Sections []iniSection `@@*`
}

func TestINIConfigWorkflow(t *testing.T) {
	p := participle.MustBuild[iniFile](participle.Unquote())
	src := `
top = "level"
[server]
host = "localhost"
port = "8080"
[client]
retries = "3"
`
	v, err := p.ParseString("cfg.ini", src)
	if err != nil {
		t.Fatalf("ini parse failed: %v", err)
	}
	if len(v.Globals) != 1 || v.Globals[0].Key != "top" || v.Globals[0].Value != "level" {
		t.Fatalf("globals wrong: %+v", v.Globals)
	}
	if len(v.Sections) != 2 {
		t.Fatalf("expected 2 sections, got %d", len(v.Sections))
	}
	if v.Sections[0].Name != "server" || len(v.Sections[0].Props) != 2 {
		t.Fatalf("server section wrong: %+v", v.Sections[0])
	}
	if v.Sections[1].Props[0].Key != "retries" || v.Sections[1].Props[0].Value != "3" {
		t.Fatalf("client section wrong: %+v", v.Sections[1])
	}
}

type factor struct {
	Number *int      `  @Int`
	Sub    *addition `| "(" @@ ")"`
}

type multiplication struct {
	Left  factor   `@@`
	Right []factor `("*" @@)*`
}

type addition struct {
	Left  multiplication   `@@`
	Right []multiplication `("+" @@)*`
}

func evalFactor(f factor) int {
	if f.Number != nil {
		return *f.Number
	}
	if f.Sub == nil {
		return 0
	}
	return evalAdd(*f.Sub)
}

func evalMul(m multiplication) int {
	acc := evalFactor(m.Left)
	for _, r := range m.Right {
		acc *= evalFactor(r)
	}
	return acc
}

func evalAdd(a addition) int {
	acc := evalMul(a.Left)
	for _, r := range a.Right {
		acc += evalMul(r)
	}
	return acc
}

func TestRecursiveExpressionWorkflow(t *testing.T) {
	p := participle.MustBuild[addition]()
	v, err := p.ParseString("", "1 + 2 * (3 + 4)")
	if err != nil {
		t.Fatalf("expression parse failed: %v", err)
	}
	if got := evalAdd(*v); got != 15 {
		t.Fatalf("structure must encode precedence via nesting: got %d, want 15", got)
	}
}

type interpString struct {
	Parts []interpPart `String @@* StringEnd`
}

type interpPart struct {
	Chars string  `  @Chars`
	Expr  *string `| Expr @Ident ExprEnd`
}

func TestStatefulInterpolationWorkflow(t *testing.T) {
	def := lexer.MustStateful(lexer.Rules{
		"Root": {
			{Name: "String", Pattern: `"`, Action: lexer.Push("Str")},
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
	p := participle.MustBuild[interpString](participle.Lexer(def), participle.Elide("WS"))
	v, err := p.ParseString("", `"pre${name}post"`)
	if err != nil {
		t.Fatalf("interpolation parse failed: %v", err)
	}
	if len(v.Parts) != 3 {
		t.Fatalf("expected 3 parts, got %+v", v.Parts)
	}
	if v.Parts[0].Chars != "pre" {
		t.Fatalf("part 0: %+v", v.Parts[0])
	}
	if v.Parts[1].Expr == nil || *v.Parts[1].Expr != "name" {
		t.Fatalf("part 1 must be the interpolated identifier: %+v", v.Parts[1])
	}
	if v.Parts[2].Chars != "post" {
		t.Fatalf("part 2: %+v", v.Parts[2])
	}
}

type boolean bool

func (b *boolean) Capture(values []string) error {
	*b = values[0] == "true"
	return nil
}

type value interface{ isValue() }

type numValue struct {
	V int `@Int`
}

func (numValue) isValue() {}

type boolValue struct {
	V boolean `@("true" | "false")`
}

func (boolValue) isValue() {}

type setting struct {
	Key string `@Ident "="`
	Val value  `@@`
}

func TestUnionWithCustomCaptureWorkflow(t *testing.T) {
	p := participle.MustBuild[setting](participle.Union[value](numValue{}, boolValue{}))
	vNum, err := p.ParseString("", "count = 3")
	if err != nil {
		t.Fatalf("numeric setting failed: %v", err)
	}
	if n, ok := vNum.Val.(numValue); !ok || n.V != 3 {
		t.Fatalf("numeric member must win: %#v", vNum.Val)
	}
	vBool, err := p.ParseString("", "enabled = false")
	if err != nil {
		t.Fatalf("boolean setting failed: %v", err)
	}
	b, ok := vBool.Val.(boolValue)
	if !ok {
		t.Fatalf("boolean member must win: %#v", vBool.Val)
	}
	if bool(b.V) != false {
		t.Fatal("custom Capture must convert the literal text, not default to true")
	}
}

type sexpr interface{ isSexpr() }

type atom struct {
	V string `@Ident`
}

func (atom) isSexpr() {}

type sexprHost struct {
	E sexpr `@@`
}

func TestParseTypeWithCustomFunction(t *testing.T) {
	parseAtom := func(lex *lexer.PeekingLexer) (sexpr, error) {
		tok := lex.Peek()
		if tok.EOF() {
			return nil, participle.Errorf(tok.Pos, "unexpected eof")
		}
		lex.Next()
		return atom{V: strings.ToUpper(tok.Value)}, nil
	}
	p := participle.MustBuild[sexprHost](participle.ParseTypeWith(parseAtom))
	v, err := p.ParseString("", "hello")
	if err != nil {
		t.Fatalf("custom parse failed: %v", err)
	}
	a, ok := v.E.(atom)
	if !ok || a.V != "HELLO" {
		t.Fatalf("custom function must control the captured value: %#v", v.E)
	}
}

type magicWord struct {
	N string
}

func (m *magicWord) Parse(lex *lexer.PeekingLexer) error {
	tok := lex.Peek()
	if tok.Value != "magic" {
		return participle.NextMatch
	}
	lex.Next()
	m.N = "found-" + tok.Value
	return nil
}

type parseableHost struct {
	M *magicWord `  @@`
	F string     `| @Ident`
}

func TestParseableNextMatchFallthrough(t *testing.T) {
	p := participle.MustBuild[parseableHost]()
	hit, err := p.ParseString("", "magic")
	if err != nil {
		t.Fatalf("parseable branch failed: %v", err)
	}
	if hit.M == nil || hit.M.N != "found-magic" {
		t.Fatalf("Parseable must populate its receiver: %+v", hit.M)
	}
	miss, err := p.ParseString("", "ordinary")
	if err != nil {
		t.Fatalf("NextMatch must fall through to the next alternative: %v", err)
	}
	if miss.M != nil || miss.F != "ordinary" {
		t.Fatalf("fallback branch must win on NextMatch: %+v", miss)
	}
}

type spanned struct {
	Pos    lexer.Position
	Tokens []lexer.Token
	Key    string `@Ident "="`
	Val    string `@String`
	EndPos lexer.Position
}

func TestSideChannelsWithElision(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "Comment", Pattern: `//[^\n]*`},
		{Name: "String", Pattern: `"[^"]*"`},
		{Name: "Ident", Pattern: `[a-zA-Z_]\w*`},
		{Name: "Eq", Pattern: `=`},
		{Name: "WS", Pattern: `\s+`},
	})
	p := participle.MustBuild[spanned](
		participle.Lexer(def),
		participle.Elide("WS", "Comment"),
		participle.Unquote("String"),
	)
	v, err := p.ParseString("sc", ` // note
key = "val"`)
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.Key != "key" || v.Val != "val" {
		t.Fatalf("unexpected result: %+v", v)
	}
	if v.Pos.Line != 2 || v.Pos.Column != 1 {
		t.Fatalf("Pos must point at the first non-elided token: %+v", v.Pos)
	}
	sawElided := false
	for _, tok := range v.Tokens {
		if strings.HasPrefix(tok.Value, "//") || strings.TrimSpace(tok.Value) == "" {
			sawElided = true
		}
	}
	if !sawElided {
		t.Fatalf("Tokens must include elided tokens: %v", v.Tokens)
	}
}

func TestAllowTrailingEnablesPrefixComposition(t *testing.T) {
	type header struct {
		Name string `@Ident ":"`
	}
	p := participle.MustBuild[header]()
	v, err := p.ParseString("", "content: rest of line ignored", participle.AllowTrailing(true))
	if err != nil {
		t.Fatalf("prefix parse failed: %v", err)
	}
	if v.Name != "content" {
		t.Fatalf("got %q", v.Name)
	}
	if _, err := p.ParseString("", "content: rest"); err == nil {
		t.Fatal("the same input must fail without AllowTrailing")
	}
}

func TestErrorReportingAcrossInputs(t *testing.T) {
	type decl struct {
		Kw   string `@"let"`
		Name string `@Ident`
		Val  int    `"=" @Int`
	}
	p := participle.MustBuild[decl]()
	cases := []struct {
		input   string
		wantPos string
		wantSub string
	}{
		{"let x = y", "e:1:9", "unexpected token"},
		{"let 1 = 2", "e:1:5", "unexpected token"},
		{"var x = 1", "e:1:1", "unexpected token"},
	}
	for _, c := range cases {
		_, err := p.ParseString("e", c.input)
		if err == nil {
			t.Fatalf("input %q must fail", c.input)
		}
		if !strings.HasPrefix(err.Error(), c.wantPos+":") {
			t.Fatalf("input %q: error position %q, want prefix %q", c.input, err.Error(), c.wantPos)
		}
		if !strings.Contains(err.Error(), c.wantSub) {
			t.Fatalf("input %q: error %q must contain %q", c.input, err.Error(), c.wantSub)
		}
	}
}

func TestGrammarEvolutionRoundTrip(t *testing.T) {
	type v1 struct {
		Names []string `@Ident ("," @Ident)*`
	}
	p1 := participle.MustBuild[v1]()
	a, err := p1.ParseString("", "x, y, z")
	if err != nil {
		t.Fatalf("v1 parse failed: %v", err)
	}
	if strings.Join(a.Names, "") != "xyz" {
		t.Fatalf("v1 result: %v", a.Names)
	}
	ebnf := p1.String()
	if !strings.Contains(ebnf, `<ident> ("," <ident>)*`) {
		t.Fatalf("EBNF must round-trip the list shape: %q", ebnf)
	}
	sub, err := participle.ParserForProduction[v1](p1)
	if err != nil {
		t.Fatalf("root production sub-parser failed: %v", err)
	}
	b, err := sub.ParseString("", "x, y, z")
	if err != nil {
		t.Fatalf("sub parse failed: %v", err)
	}
	if strings.Join(b.Names, "") != strings.Join(a.Names, "") {
		t.Fatal("root sub-parser must agree with the parent")
	}
}
