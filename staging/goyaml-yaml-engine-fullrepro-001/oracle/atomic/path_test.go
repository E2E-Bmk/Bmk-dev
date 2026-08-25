package atomic

import (
	"fmt"
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/parser"
)

const bookstoreDoc = "store:\n  book:\n    - author: alpha\n      price: 10\n    - author: beta\n      price: 20\n  bicycle:\n    color: red\n"

// Verifies: Path Queries (PathString parse and canonical String rendering).
func TestPathStringParseAndRender(t *testing.T) {
	for _, s := range []string{"$.store.book[0].author", "$.a.b", "$.a[2]"} {
		p, err := yaml.PathString(s)
		if err != nil {
			t.Fatalf("PathString(%q): %v", s, err)
		}
		if p.String() != s {
			t.Fatalf("String() = %q, want %q", p.String(), s)
		}
	}
}

// Verifies: Path Queries (PathBuilder builds the same canonical paths).
func TestPathBuilderBuildsCanonicalString(t *testing.T) {
	p := (&yaml.PathBuilder{}).Root().Child("store").Child("book").Index(0).Child("author").Build()
	want := "$.store.book[0].author"
	if p.String() != want {
		t.Fatalf("built path = %q, want %q", p.String(), want)
	}
}

// Verifies: Path Queries > Reading (Read decodes the addressed node).
func TestPathRead(t *testing.T) {
	p, err := yaml.PathString("$.store.book[1].author")
	if err != nil {
		t.Fatal(err)
	}
	var author string
	if err := p.Read(strings.NewReader(bookstoreDoc), &author); err != nil {
		t.Fatal(err)
	}
	if author != "beta" {
		t.Fatalf("Read = %q, want beta", author)
	}
	var price int
	p2, _ := yaml.PathString("$.store.book[0].price")
	if err := p2.Read(strings.NewReader(bookstoreDoc), &price); err != nil {
		t.Fatal(err)
	}
	if price != 10 {
		t.Fatalf("Read price = %d, want 10", price)
	}
}

// Verifies: Path Queries > Reading (ReadNode returns the addressed node).
func TestPathReadNode(t *testing.T) {
	p, _ := yaml.PathString("$.store.bicycle")
	node, err := p.ReadNode(strings.NewReader(bookstoreDoc))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(node.String(), "color: red") {
		t.Fatalf("ReadNode rendering %q does not contain the subtree content", node.String())
	}
}

// Verifies: Path Queries > Reading (Filter projects a plain Go value).
func TestPathFilterGoValue(t *testing.T) {
	p, _ := yaml.PathString("$.a[1]")
	var out int
	if err := p.Filter(map[string]interface{}{"a": []interface{}{10, 20, 30}}, &out); err != nil {
		t.Fatal(err)
	}
	if out != 20 {
		t.Fatalf("Filter = %d, want 20", out)
	}
}

// Verifies: Path Queries > Reading (FilterFile and FilterNode address into a
// parsed tree).
func TestPathFilterFileAndNode(t *testing.T) {
	f, err := parser.ParseBytes([]byte(bookstoreDoc), 0)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := yaml.PathString("$.store.book[0].author")
	nodeFromFile, err := p.FilterFile(f)
	if err != nil {
		t.Fatal(err)
	}
	if nodeFromFile.String() != "alpha" {
		t.Fatalf("FilterFile = %q, want alpha", nodeFromFile.String())
	}
	nodeFromNode, err := p.FilterNode(f.Docs[0].Body)
	if err != nil {
		t.Fatal(err)
	}
	if nodeFromNode.String() != "alpha" {
		t.Fatalf("FilterNode = %q, want alpha", nodeFromNode.String())
	}
}

// Verifies: Path Queries > Failure paths; Error Semantics (malformed path).
func TestInvalidPathString(t *testing.T) {
	_, err := yaml.PathString("!!bad")
	if err == nil {
		t.Fatal("expected an error for a malformed path string")
	}
	if !yaml.IsInvalidPathStringError(err) {
		t.Fatalf("IsInvalidPathStringError(%v) = false, want true", err)
	}
	if !yaml.IsInvalidPathStringError(fmt.Errorf("wrapped: %w", err)) {
		t.Fatal("predicate must hold through wrapped chains")
	}
	if yaml.IsNotFoundNodeError(err) {
		t.Fatal("a malformed path must not satisfy IsNotFoundNodeError")
	}
}

// Verifies: Path Queries > Failure paths; Error Semantics (valid path, absent
// node).
func TestPathNotFound(t *testing.T) {
	p, err := yaml.PathString("$.zzz")
	if err != nil {
		t.Fatal(err)
	}
	var dst interface{}
	readErr := p.Read(strings.NewReader("a: 1\n"), &dst)
	if readErr == nil {
		t.Fatal("expected a not-found error")
	}
	if !yaml.IsNotFoundNodeError(readErr) {
		t.Fatalf("IsNotFoundNodeError(%v) = false, want true", readErr)
	}
	if !yaml.IsNotFoundNodeError(fmt.Errorf("wrapped: %w", readErr)) {
		t.Fatal("predicate must hold through wrapped chains")
	}
	if yaml.IsInvalidPathStringError(readErr) {
		t.Fatal("a not-found error must not satisfy IsInvalidPathStringError")
	}
}

// Verifies: Path Queries > Annotation (AnnotateSource renders a numbered
// excerpt with a caret; colors appear exactly when colored is true).
func TestAnnotateSource(t *testing.T) {
	p, _ := yaml.PathString("$.b.c")
	src := []byte("a: 1\nb:\n  c: 2\n")
	plain, err := p.AnnotateSource(src, false)
	if err != nil {
		t.Fatal(err)
	}
	text := string(plain)
	if !strings.Contains(text, ">  3 |   c: 2") {
		t.Fatalf("annotation %q does not mark line 3", text)
	}
	if !strings.Contains(text, "^") {
		t.Fatalf("annotation %q has no caret", text)
	}
	if strings.Contains(text, "\x1b[") {
		t.Fatal("plain annotation must not contain ANSI escapes")
	}
	colored, err := p.AnnotateSource(src, true)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(colored), "\x1b[") {
		t.Fatal("colored annotation must contain ANSI escapes")
	}
}
