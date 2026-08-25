package atomic

import (
	"testing"
)

// Verifies: Decoding into Go Values > Struct destinations and field matching.
func TestTagNamedFieldMatching(t *testing.T) {
	var s struct {
		Host string `yaml:"host"`
		Port int    `yaml:"port"`
	}
	if err := unmarshalInto(t, "host: example\nport: 8080\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.Host != "example" || s.Port != 8080 {
		t.Fatalf("decoded %+v, want Host=example Port=8080", s)
	}
}

// Verifies: Decoding into Go Values > Struct destinations and field matching
// (untagged fields match the field name lowercased in full).
func TestUntaggedFieldLowercasedKey(t *testing.T) {
	var s struct {
		Count  int
		FooBar int
	}
	if err := unmarshalInto(t, "count: 3\nfoobar: 4\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.Count != 3 || s.FooBar != 4 {
		t.Fatalf("decoded %+v, want Count=3 FooBar=4", s)
	}

	// Matching is exact and case-sensitive against the derived key: a
	// document key FooBar must not populate the untagged field FooBar.
	var s2 struct {
		FooBar int
	}
	if err := unmarshalInto(t, "FooBar: 9\n", &s2); err != nil {
		t.Fatal(err)
	}
	if s2.FooBar != 0 {
		t.Fatalf("document key FooBar populated field FooBar (derived key foobar): got %d, want 0", s2.FooBar)
	}
}

// Verifies: Decoding into Go Values > Struct destinations and field matching
// (json tag fallback when no yaml tag is present).
func TestJSONTagFallback(t *testing.T) {
	var s struct {
		Value int `json:"jt"`
	}
	if err := unmarshalInto(t, "jt: 5\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.Value != 5 {
		t.Fatalf("json-tag fallback: got %d, want 5", s.Value)
	}
	// A yaml tag wins over a json tag.
	var s2 struct {
		Value int `yaml:"yt" json:"jt"`
	}
	if err := unmarshalInto(t, "yt: 6\njt: 7\n", &s2); err != nil {
		t.Fatal(err)
	}
	if s2.Value != 6 {
		t.Fatalf("yaml tag should win over json tag: got %d, want 6", s2.Value)
	}
}

// Verifies: Decoding into Go Values > Struct destinations and field matching
// (a tag value of - excludes the field; unmatched keys are ignored).
func TestDashTagExcludesField(t *testing.T) {
	var s struct {
		Kept    int `yaml:"kept"`
		Skipped int `yaml:"-"`
	}
	if err := unmarshalInto(t, "kept: 1\nskipped: 2\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.Kept != 1 || s.Skipped != 0 {
		t.Fatalf("decoded %+v, want Kept=1 Skipped=0", s)
	}
}

// Verifies: Decoding into Go Values > Struct destinations and field matching
// (unmatched document keys are ignored without error by default).
func TestUnmatchedKeysIgnoredByDefault(t *testing.T) {
	var s struct {
		A int `yaml:"a"`
	}
	if err := unmarshalInto(t, "a: 1\nextra: 2\nmore: [1, 2]\n", &s); err != nil {
		t.Fatalf("unmatched keys must not error by default: %v", err)
	}
	if s.A != 1 {
		t.Fatalf("A = %d, want 1", s.A)
	}
}

type InlineInner struct {
	X int `yaml:"x"`
}

type inlineOuter struct {
	InlineInner `yaml:",inline"`
	Y           int `yaml:"y"`
}

// Verifies: Decoding into Go Values > Struct destinations and field matching
// (inline splices inner struct keys into the parent namespace, decode side).
func TestInlineStructDecode(t *testing.T) {
	var o inlineOuter
	if err := unmarshalInto(t, "x: 1\ny: 2\n", &o); err != nil {
		t.Fatal(err)
	}
	if o.X != 1 || o.Y != 2 {
		t.Fatalf("decoded %+v, want X=1 Y=2", o)
	}
}

// Verifies: Encoding from Go Values > Key derivation and ordering (inline on
// the encode side splices keys into the parent mapping).
func TestInlineStructEncode(t *testing.T) {
	out := mustMarshal(t, inlineOuter{InlineInner{5}, 6})
	// Field Y derives key "y", a boolean-like word, so it is quoted.
	want := "x: 5\n\"y\": 6\n"
	if out != want {
		t.Fatalf("inline encode = %q, want %q", out, want)
	}
}
