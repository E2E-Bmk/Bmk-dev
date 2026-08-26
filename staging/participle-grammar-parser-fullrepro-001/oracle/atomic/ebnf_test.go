package atomic

import (
	"strings"
	"testing"

	participle "github.com/alecthomas/participle/v2"
	"github.com/alecthomas/participle/v2/lexer"
)

type ebnfBasic struct {
	Name  string `@Ident`
	Value int    `"=" @Int`
}

func TestEBNFBasicProductionShape(t *testing.T) {
	p := participle.MustBuild[ebnfBasic]()
	got := p.String()
	// Production names render the type name with its first rune upper-cased.
	want := `EbnfBasic = <ident> "=" <int> .`
	if got != want {
		t.Fatalf("EBNF rendering:\n got %q\nwant %q", got, want)
	}
}

type ebnfCased struct {
	A string `@MyNumber @UPPER`
}

func TestEBNFTokenReferencesLowercased(t *testing.T) {
	def := lexer.MustSimple([]lexer.SimpleRule{
		{Name: "MyNumber", Pattern: `[0-9]+`},
		{Name: "UPPER", Pattern: `[A-Z]+`},
		{Name: "WS", Pattern: `\s+`},
	})
	p := participle.MustBuild[ebnfCased](participle.Lexer(def), participle.Elide("WS"))
	got := p.String()
	if !strings.Contains(got, "<mynumber>") || !strings.Contains(got, "<upper>") {
		t.Fatalf("token references must render lower-cased in angle brackets: %q", got)
	}
}

type ebnfMods struct {
	Head  string   `@Ident`
	Tail  []string `("," @Ident)*`
	Bang  bool     `@"!"?`
	Multi []string `@Int+`
}

func TestEBNFModifiersRendered(t *testing.T) {
	p := participle.MustBuild[ebnfMods]()
	got := p.String()
	for _, frag := range []string{`("," <ident>)*`, `"!"?`, `<int>+`} {
		if !strings.Contains(got, frag) {
			t.Fatalf("EBNF must contain %q, got %q", frag, got)
		}
	}
}

type ebnfNeg struct {
	Body []string `@~";"* ";"`
}

func TestEBNFNegationRendered(t *testing.T) {
	p := participle.MustBuild[ebnfNeg]()
	got := p.String()
	if !strings.Contains(got, `~";"*`) {
		t.Fatalf("negation must render as prefix ~: %q", got)
	}
}

type ebnfLook struct {
	A string `  (?= Ident "=") @Ident "=" @Int`
	B string `| (?! "z") @Ident`
}

func TestEBNFLookaheadGroupsRendered(t *testing.T) {
	p := participle.MustBuild[ebnfLook]()
	got := p.String()
	if !strings.Contains(got, "(?= ") {
		t.Fatalf("positive lookahead must render as (?= ...): %q", got)
	}
	if !strings.Contains(got, "(?! ") {
		t.Fatalf("negative lookahead must render as (?! ...): %q", got)
	}
}

type ebnfCapA struct {
	V string `"k" @Ident`
}

type ebnfCapB struct {
	V string `"k" Ident`
}

func TestEBNFCaptureMarkersInvisible(t *testing.T) {
	pa := participle.MustBuild[ebnfCapA]()
	pb := participle.MustBuild[ebnfCapB]()
	bodyA := strings.TrimPrefix(pa.String(), "EbnfCapA")
	bodyB := strings.TrimPrefix(pb.String(), "EbnfCapB")
	if bodyA != bodyB {
		t.Fatalf("capture markers must not appear in EBNF:\n a=%q\n b=%q", bodyA, bodyB)
	}
}

type ebnfItem struct {
	Name string `@Ident "x" @Int`
}

type ebnfList struct {
	Items []ebnfItem `(@@ ("," @@)*)?`
}

func TestEBNFMultipleProductions(t *testing.T) {
	p := participle.MustBuild[ebnfList]()
	got := p.String()
	lines := strings.Split(got, "\n")
	if len(lines) != 2 {
		t.Fatalf("expected one production per line, got %q", got)
	}
	if !strings.HasPrefix(lines[0], "EbnfList = ") || !strings.HasSuffix(lines[0], " .") {
		t.Fatalf("root production first, terminated by ' .': %q", lines[0])
	}
	if !strings.HasPrefix(lines[1], "EbnfItem = ") {
		t.Fatalf("referenced production must follow: %q", lines[1])
	}
	if !strings.Contains(lines[0], "EbnfItem") {
		t.Fatalf("struct references must render as production names: %q", lines[0])
	}
}
