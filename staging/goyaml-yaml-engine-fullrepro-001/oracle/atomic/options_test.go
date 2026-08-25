package atomic

import (
	"errors"
	"io"
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/parser"
)

// Verifies: Decoding into Go Values > Decode options (DisallowUnknownField).
func TestDisallowUnknownField(t *testing.T) {
	var s struct {
		A int `yaml:"a"`
	}
	err := unmarshalInto(t, "a: 1\nb: 2\n", &s, yaml.DisallowUnknownField())
	if err == nil {
		t.Fatal("expected an error for the unknown key b")
	}
	var ufe *yaml.UnknownFieldError
	if !errors.As(err, &ufe) {
		t.Fatalf("error %v does not match *yaml.UnknownFieldError", err)
	}
	if !strings.Contains(err.Error(), `unknown field "b"`) {
		t.Fatalf("message %q does not contain unknown field \"b\"", err.Error())
	}
}

// Verifies: Decoding into Go Values > Decode options (Strict behaves
// identically to DisallowUnknownField).
func TestStrictMatchesDisallowUnknownField(t *testing.T) {
	src := "a: 1\nzz: 2\n"
	var s1, s2 struct {
		A int `yaml:"a"`
	}
	errStrict := unmarshalInto(t, src, &s1, yaml.Strict())
	errDisallow := unmarshalInto(t, src, &s2, yaml.DisallowUnknownField())
	if errStrict == nil || errDisallow == nil {
		t.Fatal("both options must reject the unknown key")
	}
	var ufe *yaml.UnknownFieldError
	if !errors.As(errStrict, &ufe) {
		t.Fatalf("Strict error %v does not match *yaml.UnknownFieldError", errStrict)
	}
	if errStrict.Error() != errDisallow.Error() {
		t.Fatalf("Strict message %q differs from DisallowUnknownField message %q", errStrict, errDisallow)
	}
}

// Verifies: Decoding into Go Values > Decode options (duplicate keys are
// rejected by default); Error Semantics (duplicate mapping key row).
func TestDuplicateKeyRejectedByDefault(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "a: 1\na: 2\n", &v)
	if err == nil {
		t.Fatal("expected duplicate-key error")
	}
	if !strings.Contains(err.Error(), `mapping key "a" already defined at [1:1]`) {
		t.Fatalf("message %q does not name the key and the earlier position", err.Error())
	}
}

// Verifies: Decoding into Go Values > Decode options (AllowDuplicateMapKey:
// last occurrence wins).
func TestAllowDuplicateMapKeyLastWins(t *testing.T) {
	var v interface{}
	if err := unmarshalInto(t, "a: 1\na: 2\n", &v, yaml.AllowDuplicateMapKey()); err != nil {
		t.Fatal(err)
	}
	wantEqual(t, v.(map[string]interface{})["a"], uint64(2), "last duplicate wins")
}

// Verifies: Decoding into Go Values > Ordered maps (UseOrderedMap yields
// MapSlice in document order; ToMap projects to a plain map).
func TestUseOrderedMapDecode(t *testing.T) {
	var v interface{}
	if err := unmarshalInto(t, "z: 1\na: 2\nm: 3\n", &v, yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	ms, ok := v.(yaml.MapSlice)
	if !ok {
		t.Fatalf("decoded %T, want yaml.MapSlice", v)
	}
	if len(ms) != 3 {
		t.Fatalf("MapSlice has %d items, want 3", len(ms))
	}
	keys := []string{}
	for _, item := range ms {
		keys = append(keys, item.Key.(string))
	}
	wantEqual(t, keys, []string{"z", "a", "m"}, "document order preserved")
	m := ms.ToMap()
	if len(m) != 3 {
		t.Fatalf("ToMap has %d entries, want 3", len(m))
	}
	wantEqual(t, m["a"], uint64(2), "ToMap value")
}

// Verifies: Decoding into Go Values > Decode options (UseJSONUnmarshaler).
func TestUseJSONUnmarshaler(t *testing.T) {
	var n jsonBackedNumber
	if err := unmarshalInto(t, "7\n", &n, yaml.UseJSONUnmarshaler()); err != nil {
		t.Fatal(err)
	}
	if n != 77 {
		t.Fatalf("json.Unmarshaler hook produced %d, want 77", n)
	}
}

// Verifies: Decoding into Go Values > Raw subtrees (RawMessage capture and
// verbatim splice).
func TestRawMessageCaptureAndSplice(t *testing.T) {
	var s struct {
		A yaml.RawMessage `yaml:"a"`
	}
	if err := unmarshalInto(t, "a:\n  b: 1\n  c: [2, 3]\n", &s); err != nil {
		t.Fatal(err)
	}
	if string(s.A) != "b: 1\nc: [2, 3]" {
		t.Fatalf("raw capture = %q, want the exact source bytes of the subtree", string(s.A))
	}
	out := mustMarshal(t, s)
	want := "a:\n  b: 1\n  c: [2, 3]\n"
	if out != want {
		t.Fatalf("raw splice = %q, want %q", out, want)
	}
}

// Verifies: Decoding into Go Values > Multiple documents (one document per
// Decode call, io.EOF after the final document).
func TestDecoderStreamAndEOF(t *testing.T) {
	dec := yaml.NewDecoder(strings.NewReader("a: 1\n---\nb: 2\n"))
	var d1, d2, d3 interface{}
	if err := dec.Decode(&d1); err != nil {
		t.Fatalf("first document: %v", err)
	}
	wantEqual(t, d1.(map[string]interface{})["a"], uint64(1), "first document")
	if err := dec.Decode(&d2); err != nil {
		t.Fatalf("second document: %v", err)
	}
	wantEqual(t, d2.(map[string]interface{})["b"], uint64(2), "second document")
	if err := dec.Decode(&d3); !errors.Is(err, io.EOF) {
		t.Fatalf("after the last document: got %v, want io.EOF", err)
	}
}

// Verifies: Decoding into Go Values > Decoding through the tree (NodeToValue).
func TestNodeToValueDecodesNode(t *testing.T) {
	f, err := parser.ParseBytes([]byte("x: 5\nlist: [1, 2]\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	var v interface{}
	if err := yaml.NodeToValue(f.Docs[0].Body, &v); err != nil {
		t.Fatal(err)
	}
	m := v.(map[string]interface{})
	wantEqual(t, m["x"], uint64(5), "x")
	wantEqual(t, m["list"], []interface{}{uint64(1), uint64(2)}, "list")

	// Options apply exactly as with UnmarshalWithOptions.
	var ordered interface{}
	if err := yaml.NodeToValue(f.Docs[0].Body, &ordered, yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	if _, ok := ordered.(yaml.MapSlice); !ok {
		t.Fatalf("NodeToValue with UseOrderedMap produced %T, want yaml.MapSlice", ordered)
	}
}

// Verifies: Decoding into Go Values > Decoding through the tree
// (Decoder.DecodeFromNode).
func TestDecodeFromNode(t *testing.T) {
	f, err := parser.ParseBytes([]byte("x: 5\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	var v map[string]int
	if err := yaml.NewDecoder(strings.NewReader("")).DecodeFromNode(f.Docs[0].Body, &v); err != nil {
		t.Fatal(err)
	}
	wantEqual(t, v["x"], 5, "DecodeFromNode")
}

type jsonBackedNumber int

func (j *jsonBackedNumber) UnmarshalJSON(b []byte) error { *j = 77; return nil }
