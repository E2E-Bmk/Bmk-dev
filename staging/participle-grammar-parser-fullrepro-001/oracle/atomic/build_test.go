package atomic

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

type unknownTok struct {
	A string `@Bogus`
}

func TestUnknownTokenTypeBuildError(t *testing.T) {
	_, err := participle.Build[unknownTok]()
	if err == nil {
		t.Fatal("reference to an undefined token type must fail Build")
	}
	if !strings.Contains(err.Error(), `unknown token type "Bogus"`) {
		t.Fatalf("error must name the unknown token type: %v", err)
	}
	if !strings.Contains(err.Error(), "A") {
		t.Fatalf("error must name the offending field: %v", err)
	}
}

type badTypedLit struct {
	V string `@"x":Bogus`
}

func TestUnknownTokenTypeInLiteralConstraint(t *testing.T) {
	_, err := participle.Build[badTypedLit]()
	if err == nil {
		t.Fatal("typed literal with undefined type must fail Build")
	}
	if !strings.Contains(err.Error(), `unknown token type "Bogus"`) ||
		!strings.Contains(err.Error(), "literal type constraint") {
		t.Fatalf("error must identify the literal type constraint: %v", err)
	}
}

type leftRec struct {
	L *leftRec `@@`
	V string   `@Ident`
}

func TestLeftRecursionRejected(t *testing.T) {
	_, err := participle.Build[leftRec]()
	if err == nil {
		t.Fatal("left-recursive grammar must fail Build")
	}
	if !strings.Contains(err.Error(), "left recursion detected") {
		t.Fatalf("error must mention left recursion: %v", err)
	}
}

type emptyStruct struct {
	A string
}

func TestEmptyStructRejected(t *testing.T) {
	_, err := participle.Build[emptyStruct]()
	if err == nil {
		t.Fatal("a struct with no grammar content must fail Build")
	}
	if !strings.Contains(err.Error(), "empty struct") {
		t.Fatalf("error must mention the empty struct: %v", err)
	}
}

func TestNonStructRootRejected(t *testing.T) {
	_, err := participle.Build[int]()
	if err == nil {
		t.Fatal("a non-struct root must fail Build")
	}
	if !strings.Contains(err.Error(), "should be a struct or should implement the Parseable interface") {
		t.Fatalf("error must state the struct/Parseable requirement: %v", err)
	}
}

type unclosed struct {
	A string `("x" @Ident`
}

func TestMalformedFragmentNamesField(t *testing.T) {
	_, err := participle.Build[unclosed]()
	if err == nil {
		t.Fatal("an unclosed group must fail Build")
	}
	if !strings.Contains(err.Error(), "A") {
		t.Fatalf("error must name the offending field: %v", err)
	}
}

func TestMustBuildPanicsOnBuildError(t *testing.T) {
	defer func() {
		r := recover()
		if r == nil {
			t.Fatal("MustBuild must panic when Build fails")
		}
	}()
	participle.MustBuild[unknownTok]()
}

func TestMustBuildReturnsWorkingParser(t *testing.T) {
	p := participle.MustBuild[assign]()
	if p == nil {
		t.Fatal("MustBuild must return a parser for a valid grammar")
	}
	if _, err := p.ParseString("", "a = 1"); err != nil {
		t.Fatalf("parser from MustBuild failed: %v", err)
	}
}

type notAnInterface struct {
	V string `@Ident`
}

type unionHost struct {
	V any `@@`
}

func TestUnionRequiresInterfaceType(t *testing.T) {
	_, err := participle.Build[unionHost](participle.Union[notAnInterface](notAnInterface{}))
	if err == nil {
		t.Fatal("Union over a non-interface type must fail Build")
	}
	if !strings.Contains(err.Error(), "interface") {
		t.Fatalf("error must state the interface requirement: %v", err)
	}
}

func TestParseTypeWithRequiresInterfaceType(t *testing.T) {
	_, err := participle.Build[unionHost](
		participle.ParseTypeWith(func(lex *lexer.PeekingLexer) (notAnInterface, error) {
			return notAnInterface{}, nil
		}))
	if err == nil {
		t.Fatal("ParseTypeWith over a non-interface type must fail Build")
	}
	if !strings.Contains(err.Error(), "must be an interface type") {
		t.Fatalf("error must state the interface requirement: %v", err)
	}
}
