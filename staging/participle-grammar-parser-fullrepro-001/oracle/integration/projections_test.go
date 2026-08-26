package integration

import (
	"strings"
	"sync"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

type stmt struct {
	Pos    lexer.Position
	Name   string `@Ident "=" @Int`
	EndPos lexer.Position
}

func TestEntryPointsProduceIdenticalResults(t *testing.T) {
	p := participle.MustBuild[stmt]()
	input := "x = 42"

	vs, errS := p.ParseString("f", input)
	vb, errB := p.ParseBytes("f", []byte(input))
	vr, errR := p.Parse("f", strings.NewReader(input))
	if errS != nil || errB != nil || errR != nil {
		t.Fatalf("entry points disagreed on success: %v %v %v", errS, errB, errR)
	}
	lx, err := p.Lexer().Lex("f", strings.NewReader(input))
	if err != nil {
		t.Fatalf("lex failed: %v", err)
	}
	pl, err := lexer.Upgrade(lx)
	if err != nil {
		t.Fatalf("upgrade failed: %v", err)
	}
	vl, errL := p.ParseFromLexer(pl)
	if errL != nil {
		t.Fatalf("ParseFromLexer failed: %v", errL)
	}
	for i, v := range []*stmt{vb, vr, vl} {
		if v.Name != vs.Name || v.Pos != vs.Pos || v.EndPos != vs.EndPos {
			t.Fatalf("entry point %d produced a different AST: %+v vs %+v", i, v, vs)
		}
	}
}

func TestEntryPointsProduceIdenticalErrors(t *testing.T) {
	p := participle.MustBuild[stmt]()
	input := "x + 42"
	_, errS := p.ParseString("f", input)
	_, errB := p.ParseBytes("f", []byte(input))
	_, errR := p.Parse("f", strings.NewReader(input))
	if errS == nil || errB == nil || errR == nil {
		t.Fatal("all entry points must reject the same bad input")
	}
	if errS.Error() != errB.Error() || errS.Error() != errR.Error() {
		t.Fatalf("entry points must report identical errors: %q %q %q", errS, errB, errR)
	}
}

type tokenRoot struct {
	Tokens []lexer.Token
	A      string `@Ident "=" @Int`
}

func TestParserLexAgreesWithParsedTokens(t *testing.T) {
	p := participle.MustBuild[tokenRoot]()
	input := "k = 5"
	raw, err := p.Lex("f", strings.NewReader(input))
	if err != nil {
		t.Fatalf("Lex failed: %v", err)
	}
	v, err := p.ParseString("f", input)
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if len(raw) != len(v.Tokens)+1 {
		t.Fatalf("raw stream must be the parsed tokens plus EOF: %d vs %d", len(raw), len(v.Tokens))
	}
	for i, tok := range v.Tokens {
		if raw[i].Value != tok.Value || raw[i].Type != tok.Type || raw[i].Pos != tok.Pos {
			t.Fatalf("token %d mismatch: lexed %+v, parsed %+v", i, raw[i], tok)
		}
	}
	if !raw[len(raw)-1].EOF() {
		t.Fatal("raw stream must end with EOF")
	}
}

func TestPositionCoherenceAcrossViews(t *testing.T) {
	p := participle.MustBuild[stmt]()
	v, err := p.ParseString("pc.go", "  answer = 7")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if v.Pos.Filename != "pc.go" || v.EndPos.Filename != "pc.go" {
		t.Fatalf("positions must carry the caller filename: %+v %+v", v.Pos, v.EndPos)
	}
	if v.Pos.Line != 1 || v.Pos.Column != 3 {
		t.Fatalf("Pos must locate the first non-elided token: %+v", v.Pos)
	}
	if v.EndPos.Offset < v.Pos.Offset {
		t.Fatal("EndPos must not precede Pos")
	}
	_, err = p.ParseString("pc.go", "  answer + 7")
	if err == nil {
		t.Fatal("bad input must fail")
	}
	perr, ok := err.(participle.Error)
	if !ok {
		t.Fatalf("parse errors must implement the Error interface: %T", err)
	}
	if perr.Position().Filename != "pc.go" {
		t.Fatalf("error position must carry the filename: %+v", perr.Position())
	}
}

func TestErrorInterfaceCoherence(t *testing.T) {
	p := participle.MustBuild[stmt]()
	inputs := []string{"x + 1", "x = y", "= 1", "x = 1 trailing"}
	for _, input := range inputs {
		_, err := p.ParseString("ec.go", input)
		if err == nil {
			t.Fatalf("input %q must fail", input)
		}
		perr, ok := err.(participle.Error)
		if !ok {
			t.Fatalf("input %q: error type %T does not implement Error", input, err)
		}
		if perr.Error() != participle.FormatError(perr) {
			t.Fatalf("input %q: Error()=%q, FormatError=%q", input, perr.Error(), participle.FormatError(perr))
		}
		wantPrefix := perr.Position().String() + ": "
		if !strings.HasPrefix(perr.Error(), wantPrefix) {
			t.Fatalf("input %q: Error() must be position-prefixed: %q", input, perr.Error())
		}
		if !strings.HasSuffix(perr.Error(), perr.Message()) {
			t.Fatalf("input %q: Error() must end with Message(): %q vs %q", input, perr.Error(), perr.Message())
		}
	}
}

type item struct {
	Name string `@Ident`
	Qty  int    `"x" @Int`
}

type itemList struct {
	Items []item `(@@ ("," @@)*)?`
}

func TestSubParserAcceptsProductionFragments(t *testing.T) {
	parent := participle.MustBuild[itemList]()
	sub, err := participle.ParserForProduction[item](parent)
	if err != nil {
		t.Fatalf("ParserForProduction failed: %v", err)
	}
	vSub, err := sub.ParseString("", "kiwi x 9")
	if err != nil {
		t.Fatalf("sub-parser failed: %v", err)
	}
	vList, err := parent.ParseString("", "kiwi x 9")
	if err != nil {
		t.Fatalf("parent parse failed: %v", err)
	}
	if len(vList.Items) != 1 || *vSub != vList.Items[0] {
		t.Fatalf("sub-parser AST must equal the parent's sub-AST: %+v vs %+v", vSub, vList.Items)
	}
	if _, err := sub.ParseString("", "kiwi y 9"); err == nil {
		t.Fatal("sub-parser must reject fragments the production rejects")
	}
}

func TestEBNFAgreesWithAcceptance(t *testing.T) {
	p := participle.MustBuild[itemList]()
	ebnf := p.String()
	if !strings.Contains(ebnf, `("," Item)*`) {
		t.Fatalf("EBNF must render the repetition that the grammar accepts: %q", ebnf)
	}
	if _, err := p.ParseString("", ""); err != nil {
		t.Fatalf("optional group renders with ? and must accept empty input: %v", err)
	}
	if !strings.Contains(ebnf, ")?") {
		t.Fatalf("EBNF must mark the optional group: %q", ebnf)
	}
	if _, err := p.ParseString("", "a x 1, b x 2, c x 3"); err != nil {
		t.Fatalf("repetition per EBNF must accept repeated elements: %v", err)
	}
}

type term interface{ isTerm() }

type numTerm struct {
	V int `@Int`
}

func (numTerm) isTerm() {}

type varTerm struct {
	V string `@Ident`
}

func (varTerm) isTerm() {}

type binExpr struct {
	L  term   `@@`
	Op string `@("+" | "-")`
	R  term   `@@`
}

func TestUnionDynamicTypesAndEBNF(t *testing.T) {
	p := participle.MustBuild[binExpr](participle.Union[term](numTerm{}, varTerm{}))
	v, err := p.ParseString("", "1 + x")
	if err != nil {
		t.Fatalf("union parse failed: %v", err)
	}
	if _, ok := v.L.(numTerm); !ok {
		t.Fatalf("left operand must be numTerm, got %T", v.L)
	}
	if _, ok := v.R.(varTerm); !ok {
		t.Fatalf("right operand must be varTerm, got %T", v.R)
	}
	ebnf := p.String()
	if !strings.Contains(ebnf, "Term = NumTerm | VarTerm .") {
		t.Fatalf("union must render as an alternation production: %q", ebnf)
	}
	if !strings.Contains(ebnf, "NumTerm = <int> .") || !strings.Contains(ebnf, "VarTerm = <ident> .") {
		t.Fatalf("member productions must be rendered: %q", ebnf)
	}
}

func TestPartialResultReturnedOnFailure(t *testing.T) {
	type two struct {
		First  string `@Ident`
		Second string `"," @Ident`
	}
	p := participle.MustBuild[two]()
	v, err := p.ParseString("", "alpha ;")
	if err == nil {
		t.Fatal("incomplete input must fail")
	}
	if v == nil {
		t.Fatal("failed parse must still return the partial AST pointer")
	}
	if v.First != "alpha" {
		t.Fatalf("fields matched before the failure must be populated: %+v", v)
	}
}

type capItem struct {
	Name string `@Ident "x" @Int`
}

type capList struct {
	Items []capItem `(@@ ("," @@)*)?`
}

type uncapItem struct {
	Name string `Ident "x" Int`
}

type uncapList struct {
	Items []uncapItem `(@@ ("," @@)*)?`
}

func TestCaptureNeutralityAcrossProjections(t *testing.T) {
	pc := participle.MustBuild[capList]()
	pu := participle.MustBuild[uncapList]()
	inputs := []string{"", "a x 1", "a x 1, b x 2", "a x", "x 1", "a x 1,"}
	for _, input := range inputs {
		_, errC := pc.ParseString("", input)
		_, errU := pu.ParseString("", input)
		if (errC == nil) != (errU == nil) {
			t.Fatalf("input %q: capture markers changed acceptance (cap err=%v, uncap err=%v)", input, errC, errU)
		}
	}
	bodyC := strings.ReplaceAll(pc.String(), "Cap", "")
	bodyU := strings.ReplaceAll(pu.String(), "Uncap", "")
	if bodyC != bodyU {
		t.Fatalf("EBNF must be identical modulo production names:\n cap=%q\n uncap=%q", bodyC, bodyU)
	}
}

type quotedCap struct {
	K string `@Ident "="`
	V string `@String`
}

type quotedUncap struct {
	K string `Ident "="`
	V string `String`
}

func TestCaptureNeutralityUnderOptions(t *testing.T) {
	opts := func() []participle.Option {
		return []participle.Option{participle.Unquote()}
	}
	pc := participle.MustBuild[quotedCap](opts()...)
	pu := participle.MustBuild[quotedUncap](opts()...)
	inputs := []string{`k = "v"`, `k = 1`, `k "v"`, `"v" = k`}
	for _, input := range inputs {
		_, errC := pc.ParseString("", input)
		_, errU := pu.ParseString("", input)
		if (errC == nil) != (errU == nil) {
			t.Fatalf("input %q: capture markers changed acceptance under options (cap err=%v, uncap err=%v)", input, errC, errU)
		}
	}
	v, err := pc.ParseString("", `k = "v"`)
	if err != nil {
		t.Fatalf("capturing variant failed: %v", err)
	}
	if v.K != "k" || v.V != "v" {
		t.Fatalf("capturing variant must store values: %+v", v)
	}
}

func TestParserIsConcurrencySafe(t *testing.T) {
	p := participle.MustBuild[stmt]()
	var wg sync.WaitGroup
	errs := make(chan error, 16)
	for i := 0; i < 16; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			v, err := p.ParseString("", "n = 3")
			if err != nil {
				errs <- err
				return
			}
			if v.Name != "n3" {
				errs <- err
			}
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		t.Fatalf("concurrent parse failed: %v", err)
	}
}
