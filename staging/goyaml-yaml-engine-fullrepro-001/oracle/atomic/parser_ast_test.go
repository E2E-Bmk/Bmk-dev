package atomic

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/goccy/go-yaml/ast"
	"github.com/goccy/go-yaml/lexer"
	"github.com/goccy/go-yaml/parser"
)

// Verifies: Syntax Tree and Tokens > Parsing (one DocumentNode per document).
func TestParseBytesDocumentCount(t *testing.T) {
	f, err := parser.ParseBytes([]byte("a: 1\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(f.Docs) != 1 {
		t.Fatalf("single document parsed into %d docs", len(f.Docs))
	}
	f2, err := parser.ParseBytes([]byte("a: 1\n---\nb: 2\n---\nc: 3\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(f2.Docs) != 3 {
		t.Fatalf("three documents parsed into %d docs", len(f2.Docs))
	}
}

// Verifies: Syntax Tree and Tokens > Parsing (ParseComments preserves
// comments; without it they are dropped).
func TestParseCommentsMode(t *testing.T) {
	src := "# top\na: 1 # inline\n"
	withComments, err := parser.ParseBytes([]byte(src), parser.ParseComments)
	if err != nil {
		t.Fatal(err)
	}
	if withComments.String() != src {
		t.Fatalf("ParseComments rendering = %q, want %q", withComments.String(), src)
	}
	without, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(without.String(), "#") {
		t.Fatalf("default-mode rendering %q still contains comments", without.String())
	}
}

// Verifies: Syntax Tree and Tokens > Parsing (parser.AllowDuplicateMapKey
// lifts the duplicate-key parse error).
func TestParserAllowDuplicateMapKey(t *testing.T) {
	if _, err := parser.ParseBytes([]byte("a: 1\na: 2\n"), 0); err == nil {
		t.Fatal("duplicate keys must be a parse error by default")
	}
	f, err := parser.ParseBytes([]byte("a: 1\na: 2\n"), 0, parser.AllowDuplicateMapKey())
	if err != nil {
		t.Fatalf("AllowDuplicateMapKey must lift the error: %v", err)
	}
	if f.String() != "a: 1\na: 2\n" {
		t.Fatalf("rendering = %q, want both entries kept", f.String())
	}
}

// Verifies: Syntax Tree and Tokens > Parsing (parser.Parse accepts a token
// stream; parser.ParseFile reads a file by name).
func TestParseTokensAndParseFile(t *testing.T) {
	tokens := lexer.Tokenize("a: [1, 2]\n")
	f, err := parser.Parse(tokens, 0)
	if err != nil {
		t.Fatal(err)
	}
	if f.String() != "a: [1, 2]\n" {
		t.Fatalf("Parse over tokens rendered %q", f.String())
	}

	dir := t.TempDir()
	path := filepath.Join(dir, "doc.yaml")
	if err := os.WriteFile(path, []byte("k: v\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	f2, err := parser.ParseFile(path, 0)
	if err != nil {
		t.Fatal(err)
	}
	if f2.String() != "k: v\n" {
		t.Fatalf("ParseFile rendered %q", f2.String())
	}
}

// Verifies: Syntax Tree and Tokens > Nodes (Type() reports the node kind,
// String() names it).
func TestNodeTypeNames(t *testing.T) {
	f, err := parser.ParseBytes([]byte("a:\n  b: 1\nc: [x, 1.5, true, null]\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	if got := f.Docs[0].Type().String(); got != "Document" {
		t.Fatalf("document node type = %q, want Document", got)
	}
	if got := f.Docs[0].Body.Type().String(); got != "Mapping" {
		t.Fatalf("body node type = %q, want Mapping", got)
	}
	seen := map[string]bool{}
	ast.Walk(visitAll(func(n ast.Node) { seen[n.Type().String()] = true }), f.Docs[0])
	for _, kind := range []string{"Document", "Mapping", "MappingValue", "String", "Integer", "Sequence", "Float", "Bool", "Null"} {
		if !seen[kind] {
			t.Fatalf("node kind %q not observed in walk over %v", kind, seen)
		}
	}
}

// Verifies: Syntax Tree and Tokens > Nodes (String renders the node as YAML
// text; GetToken exposes the underlying token position).
func TestNodeStringAndGetToken(t *testing.T) {
	f, err := parser.ParseBytes([]byte("a: 1\nbb: 2\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	body := f.Docs[0].Body
	if body.String() != "a: 1\nbb: 2" {
		t.Fatalf("mapping String() = %q", body.String())
	}
	mapping, ok := body.(*ast.MappingNode)
	if !ok {
		t.Fatalf("body is %T, want *ast.MappingNode", body)
	}
	if len(mapping.Values) != 2 {
		t.Fatalf("mapping has %d values, want 2", len(mapping.Values))
	}
	tk := mapping.Values[1].Key.GetToken()
	if tk.Value != "bb" {
		t.Fatalf("second key token = %q, want bb", tk.Value)
	}
	if tk.Position.Line != 2 || tk.Position.Column != 1 || tk.Position.Offset != 6 {
		t.Fatalf("second key position = %+v, want line=2 col=1 offset=6", tk.Position)
	}
}

// Verifies: Syntax Tree and Tokens > Nodes (File.String reproduces ---
// separators).
func TestFileStringMultiDoc(t *testing.T) {
	src := "a: 1\n---\nb: 2\n"
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	if f.String() != src {
		t.Fatalf("File.String() = %q, want %q", f.String(), src)
	}
}

// Verifies: Syntax Tree and Tokens > Nodes (ast.Walk visits the subtree and
// descends only while the returned visitor is non-nil).
func TestAstWalkVisitsAndStops(t *testing.T) {
	f, err := parser.ParseBytes([]byte("a:\n  b: 1\nc: 2\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	full := 0
	ast.Walk(visitAll(func(ast.Node) { full++ }), f.Docs[0])
	if full != 11 {
		t.Fatalf("full walk visited %d nodes, want 11", full)
	}
	stopped := 0
	ast.Walk(visitUntil(func(n ast.Node) bool {
		stopped++
		return n.Type().String() != "MappingValue"
	}), f.Docs[0])
	if stopped >= full {
		t.Fatalf("stopping visitor visited %d nodes, expected fewer than the full %d", stopped, full)
	}
	if stopped != 4 {
		t.Fatalf("stopping at MappingValue visited %d nodes, want 4", stopped)
	}
}

// Verifies: Syntax Tree and Tokens > Nodes (ast.Merge merges mapping nodes).
func TestAstMergeMappings(t *testing.T) {
	dst, err := parser.ParseBytes([]byte("a: 1\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	src, err := parser.ParseBytes([]byte("b: 2\nc: 3\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	if err := ast.Merge(dst.Docs[0].Body, src.Docs[0].Body); err != nil {
		t.Fatal(err)
	}
	if dst.String() != "a: 1\nb: 2\nc: 3\n" {
		t.Fatalf("merged rendering = %q, want all three entries", dst.String())
	}
}

type visitAll func(ast.Node)

func (f visitAll) Visit(n ast.Node) ast.Visitor { f(n); return f }

type visitUntil func(ast.Node) bool

func (f visitUntil) Visit(n ast.Node) ast.Visitor {
	if f(n) {
		return f
	}
	return nil
}
