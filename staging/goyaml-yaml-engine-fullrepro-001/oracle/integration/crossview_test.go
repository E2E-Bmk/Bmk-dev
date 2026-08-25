package integration

import (
	"encoding/json"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/lexer"
	"github.com/goccy/go-yaml/parser"
)

// Verifies: Cross-View Invariants 1 (token origins reproduce the source
// across a battery of document shapes).
func TestTokenOriginsReproduceSourceBattery(t *testing.T) {
	exactDocs := []string{
		"a: 1\nb:\n  c: [1, 2]\n# trailing comment\n",
		"# head\nkey: value # line\n# foot\n",
		"a: |\n  block\n  text\n",
		"- 1\n- two\n- true\n# end\n",
		"a: &x 1\nb: *x\n# done\n",
	}
	for _, src := range exactDocs {
		tokens := lexer.Tokenize(src)
		if len(tokens) < 2 {
			t.Fatalf("input %q produced %d tokens", src, len(tokens))
		}
		var sb strings.Builder
		for _, tk := range tokens {
			sb.WriteString(tk.Origin)
		}
		if sb.String() != src {
			t.Fatalf("origins of %q concatenate to %q", src, sb.String())
		}
	}
	// Documents ending in a plain scalar reproduce minus the final newline.
	scalarEnd := []string{"a: 1\n", "x: [1, 2]\ny: done\n"}
	for _, src := range scalarEnd {
		var sb strings.Builder
		for _, tk := range lexer.Tokenize(src) {
			sb.WriteString(tk.Origin)
		}
		if sb.String() != strings.TrimSuffix(src, "\n") {
			t.Fatalf("origins of %q concatenate to %q, want input minus final newline", src, sb.String())
		}
	}
}

// Verifies: Cross-View Invariants 1 (line and column locate each token's
// source text in the input).
func TestTokenPositionsAgreeWithSource(t *testing.T) {
	src := "alpha: 1\nbeta:\n  gamma: [true, x]\n# note\ndelta: v\n"
	lines := strings.Split(src, "\n")
	tokens := lexer.Tokenize(src)
	if len(tokens) < 10 {
		t.Fatalf("only %d tokens", len(tokens))
	}
	for _, tk := range tokens {
		if tk.Position.Line < 1 || tk.Position.Line > len(lines) {
			t.Fatalf("token %q line %d out of range", tk.Value, tk.Position.Line)
		}
		if tk.Position.Offset < 1 || tk.Position.Offset > len(src) {
			t.Fatalf("token %q offset %d out of range", tk.Value, tk.Position.Offset)
		}
		line := lines[tk.Position.Line-1]
		// The token's source text is its origin without surrounding
		// whitespace; every content head in this document is unique on its
		// line, so its first occurrence is the token's location.
		content := strings.TrimSpace(tk.Origin)
		if content == "" {
			continue
		}
		head := strings.SplitN(content, "\n", 2)[0]
		idx := strings.Index(line, head)
		if idx == -1 {
			t.Fatalf("token %q content %q not on line %d (%q)", tk.Value, head, tk.Position.Line, line)
		}
		if tk.Position.Column != idx+1 {
			t.Fatalf("token %q column = %d, want %d on line %q", tk.Value, tk.Position.Column, idx+1, line)
		}
	}
}

// Verifies: Cross-View Invariants 2 (ValueToNode rendering equals Marshal
// output).
func TestValueToNodeAgreesWithMarshal(t *testing.T) {
	values := []interface{}{
		map[string]interface{}{"a": []interface{}{1, 2}, "b": "x"},
		map[string]interface{}{"nested": map[string]interface{}{"k": 1.5, "s": "yes"}},
		[]interface{}{uint64(1), "two", true, nil},
		map[string]interface{}{"multi": "l1\nl2\n", "empty": ""},
	}
	for _, v := range values {
		node, err := yaml.ValueToNode(v)
		if err != nil {
			t.Fatalf("ValueToNode(%#v): %v", v, err)
		}
		rendered := node.String()
		if rendered == "" {
			t.Fatalf("empty rendering for %#v", v)
		}
		marshaled := mustMarshal(t, v)
		if rendered != strings.TrimSuffix(marshaled, "\n") {
			t.Fatalf("node rendering %q != Marshal output %q", rendered, marshaled)
		}
	}
}

// Verifies: Cross-View Invariants 2 (parsing Marshal output back yields a
// tree whose NodeToValue decode equals the Unmarshal decode).
func TestParseBackNodeToValueAgreesWithUnmarshal(t *testing.T) {
	values := []interface{}{
		map[string]interface{}{"a": []interface{}{1, 2}, "b": "x"},
		map[string]interface{}{"outer": map[string]interface{}{"inner": true}},
	}
	for _, v := range values {
		text := mustMarshal(t, v)
		f, err := parser.ParseBytes([]byte(text), 0)
		if err != nil {
			t.Fatalf("parse of %q: %v", text, err)
		}
		var fromNode, fromText interface{}
		if err := yaml.NodeToValue(f.Docs[0].Body, &fromNode); err != nil {
			t.Fatal(err)
		}
		if err := yaml.Unmarshal([]byte(text), &fromText); err != nil {
			t.Fatal(err)
		}
		if fromNode == nil || fromText == nil {
			t.Fatalf("nil decode for %q", text)
		}
		wantEqual(t, fromNode, fromText, "NodeToValue vs Unmarshal for "+text)
	}
}

// Verifies: Cross-View Invariants 3 (ordered round trip is stable).
func TestOrderedRoundTripStable(t *testing.T) {
	src := "zebra: 1\nalpha: two\nmid:\n  inner2: x\n  inner1: 2\nlist:\n- 3\n- z\n"
	first := decodeUntyped(t, src, yaml.UseOrderedMap())
	encoded := mustMarshal(t, first)
	second := decodeUntyped(t, encoded, yaml.UseOrderedMap())
	wantEqual(t, second, first, "round trip value")
	reencoded := mustMarshal(t, second)
	if reencoded != encoded {
		t.Fatalf("second encoding %q != first %q", reencoded, encoded)
	}
	ms := first.(yaml.MapSlice)
	if ms[0].Key != "zebra" || ms[1].Key != "alpha" {
		t.Fatalf("document key order lost: %v", ms)
	}
}

// Verifies: Cross-View Invariants 3 (key order survives re-encoding at every
// nesting level).
func TestOrderedRoundTripPreservesKeyOrder(t *testing.T) {
	src := "z: 1\na:\n  q: 1\n  b: 2\nm: 3\n"
	v := decodeUntyped(t, src, yaml.UseOrderedMap())
	out := mustMarshal(t, v)
	if out != src {
		t.Fatalf("ordered re-encode = %q, want the original %q", out, src)
	}
}

// Verifies: Cross-View Invariants 4 (path reads agree with full decodes).
func TestPathReadAgreesWithFullDecode(t *testing.T) {
	src := "store:\n  book:\n    - author: alpha\n      price: 10\n    - author: beta\n      price: 20\n  open: true\n"
	full := decodeUntyped(t, src)
	store := full.(map[string]interface{})["store"].(map[string]interface{})
	books := store["book"].([]interface{})

	p1, _ := yaml.PathString("$.store.book[1].author")
	var author string
	if err := p1.Read(strings.NewReader(src), &author); err != nil {
		t.Fatal(err)
	}
	wantEqual(t, author, books[1].(map[string]interface{})["author"], "book[1].author")

	p2, _ := yaml.PathString("$.store.open")
	var open bool
	if err := p2.Read(strings.NewReader(src), &open); err != nil {
		t.Fatal(err)
	}
	wantEqual(t, open, store["open"], "store.open")
	if !open {
		t.Fatal("expected open to be true")
	}
}

// Verifies: Cross-View Invariants 4 (ReadNode renders the same subtree
// FilterFile exposes).
func TestReadNodeAgreesWithFilterFile(t *testing.T) {
	src := "store:\n  bicycle:\n    color: red\n    price: 19.95\n"
	p, _ := yaml.PathString("$.store.bicycle")
	fromReader, err := p.ReadNode(strings.NewReader(src))
	if err != nil {
		t.Fatal(err)
	}
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	fromFile, err := p.FilterFile(f)
	if err != nil {
		t.Fatal(err)
	}
	if fromReader.String() == "" {
		t.Fatal("empty subtree rendering")
	}
	if !strings.Contains(fromReader.String(), "color: red") {
		t.Fatalf("subtree %q lacks expected content", fromReader.String())
	}
	if fromReader.String() != fromFile.String() {
		t.Fatalf("ReadNode %q != FilterFile %q", fromReader.String(), fromFile.String())
	}
}

// Verifies: Cross-View Invariants 5 (replace changes only the addressed
// node's text and re-reading returns the replacement).
func TestReplaceIsLocal(t *testing.T) {
	src := "store:\n  bicycle:\n    color: red\n    price: 19.95\n  book: fine\n"
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := yaml.PathString("$.store.bicycle.color")
	if err := p.ReplaceWithReader(f, strings.NewReader("blue")); err != nil {
		t.Fatal(err)
	}
	got := f.String()
	want := strings.Replace(src, "color: red", "color: blue", 1)
	if got != want {
		t.Fatalf("rendered document %q, want only the color text changed: %q", got, want)
	}
	var color string
	if err := p.Read(strings.NewReader(got), &color); err != nil {
		t.Fatal(err)
	}
	if color != "blue" {
		t.Fatalf("re-read color = %q, want blue", color)
	}
}

// Verifies: Cross-View Invariants 5 (merge keeps every pre-existing key
// readable at its original path).
func TestMergePreservesExistingKeys(t *testing.T) {
	src := "store:\n  bicycle:\n    color: red\n  book: fine\n"
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := yaml.PathString("$.store.bicycle")
	if err := p.MergeFromReader(f, strings.NewReader("brand: acme")); err != nil {
		t.Fatal(err)
	}
	rendered := f.String()
	for path, want := range map[string]string{
		"$.store.bicycle.color": "red",
		"$.store.bicycle.brand": "acme",
		"$.store.book":          "fine",
	} {
		pp, _ := yaml.PathString(path)
		var got string
		if err := pp.Read(strings.NewReader(rendered), &got); err != nil {
			t.Fatalf("read %s after merge: %v", path, err)
		}
		if got != want {
			t.Fatalf("%s = %q, want %q", path, got, want)
		}
	}
	// New keys append after existing ones.
	if !strings.Contains(rendered, "color: red\n    brand: acme") {
		t.Fatalf("merged key not appended after existing keys: %q", rendered)
	}
}

// Verifies: Cross-View Invariants 6 (comments survive the value round trip).
func TestCommentRoundTripPositions(t *testing.T) {
	src := "# service block\nhost: web1 # primary\nport: 8080\nnested:\n  key: v # deep line\n"
	cm := yaml.CommentMap{}
	var v interface{}
	if err := yaml.UnmarshalWithOptions([]byte(src), &v, yaml.CommentToMap(cm), yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	out := mustMarshal(t, v, yaml.WithComment(cm))
	if out != src {
		t.Fatalf("comment round trip produced %q, want %q", out, src)
	}
}

// Verifies: Cross-View Invariants 6 (the re-emitted document decodes to the
// same value as the original).
func TestCommentRoundTripValueEquality(t *testing.T) {
	src := "# head\na: 1\nb:\n  c: text # line\n"
	cm := yaml.CommentMap{}
	var v interface{}
	if err := yaml.UnmarshalWithOptions([]byte(src), &v, yaml.CommentToMap(cm), yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	out := mustMarshal(t, v, yaml.WithComment(cm))
	var v2 interface{}
	if err := yaml.UnmarshalWithOptions([]byte(out), &v2, yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	var vPlain interface{}
	if err := yaml.UnmarshalWithOptions([]byte(src), &vPlain, yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	// Non-vacuity: the round-tripped value must actually carry the source data.
	ms, ok := v2.(yaml.MapSlice)
	if !ok || len(ms) != 2 {
		t.Fatalf("round-tripped value = %#v, want 2-entry MapSlice", v2)
	}
	if ms[0].Key != "a" || fmt.Sprint(ms[0].Value) != "1" {
		t.Fatalf("first entry = %#v, want a: 1", ms[0])
	}
	wantEqual(t, v2, vPlain, "value after comment round trip")
}

// Verifies: Cross-View Invariants 7 (conversion agrees with decoding).
func TestYAMLToJSONAgreesWithDecode(t *testing.T) {
	src := "base: &b\n  x: 1\nderived:\n  <<: *b\n  y: two\nflag: true\n"
	jsonBytes, err := yaml.YAMLToJSON([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	var fromJSON interface{}
	if err := json.Unmarshal(jsonBytes, &fromJSON); err != nil {
		t.Fatalf("converter output %q is not valid JSON: %v", jsonBytes, err)
	}
	derived := fromJSON.(map[string]interface{})["derived"].(map[string]interface{})
	if derived["x"] != float64(1) || derived["y"] != "two" {
		t.Fatalf("converted merge result = %#v, want x=1 y=two", derived)
	}
	direct := decodeUntyped(t, src)
	directDerived := direct.(map[string]interface{})["derived"].(map[string]interface{})
	if directDerived["y"] != "two" {
		t.Fatalf("direct decode derived = %#v", directDerived)
	}
	// Same key set through both views.
	if len(derived) != len(directDerived) {
		t.Fatalf("converted keys %v != decoded keys %v", derived, directDerived)
	}
	for k := range directDerived {
		if _, ok := derived[k]; !ok {
			t.Fatalf("key %q present in decode but missing from conversion", k)
		}
	}
}

// Verifies: Cross-View Invariants 7 (converter round trip decodes to the
// same value).
func TestConverterRoundTripDecodesSame(t *testing.T) {
	src := "name: engine\nitems:\n  - id: 1\n    tags: [a, b]\n  - id: 2\nenabled: true\n"
	jsonBytes, err := yaml.YAMLToJSON([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	yamlBytes, err := yaml.JSONToYAML(jsonBytes)
	if err != nil {
		t.Fatal(err)
	}
	round := decodeUntyped(t, string(yamlBytes))
	direct := decodeUntyped(t, src)
	wantEqual(t, round, direct, "round-tripped value")
	if round.(map[string]interface{})["name"] != "engine" {
		t.Fatal("round trip lost content")
	}
}

var lineColRe = regexp.MustCompile(`^\[(\d+):(\d+)\]`)

// Verifies: Cross-View Invariants 8 (the [line:column] in a decode error
// locates the offending token in the original input).
func TestErrorLineColumnLocatesToken(t *testing.T) {
	cases := []struct {
		src   string
		token string
	}{
		// An undefined alias is reported at the alias name.
		{"a: 1\nb: *ghost\n", "g"},
		{"a: 1\nb: 2\na: 3\n", "a"},
		{"ok: 1\nbad: [1, 2\n", "["},
	}
	for _, c := range cases {
		var v interface{}
		err := yaml.Unmarshal([]byte(c.src), &v)
		if err == nil {
			t.Fatalf("input %q decoded without error", c.src)
		}
		m := lineColRe.FindStringSubmatch(err.Error())
		if m == nil {
			t.Fatalf("error %q has no [line:column] prefix", err.Error())
		}
		line, _ := strconv.Atoi(m[1])
		col, _ := strconv.Atoi(m[2])
		lines := strings.Split(c.src, "\n")
		if line < 1 || line > len(lines) {
			t.Fatalf("line %d out of range for %q", line, c.src)
		}
		got := lines[line-1]
		if col < 1 || col > len(got) {
			t.Fatalf("column %d out of range on line %q", col, got)
		}
		if got[col-1] != c.token[0] {
			t.Fatalf("input %q: [%d:%d] points at %q, want %q", c.src, line, col, got[col-1], c.token[0])
		}
	}
}

// Verifies: Cross-View Invariants 8 (the caret line in FormatError shows the
// line the token occupies in the input).
func TestFormatErrorCaretPointsIntoSource(t *testing.T) {
	src := "x: 0\nkey: 1\nother: 2\nkey: 3\n"
	var v interface{}
	err := yaml.Unmarshal([]byte(src), &v)
	if err == nil {
		t.Fatal("expected duplicate-key error")
	}
	formatted := yaml.FormatError(err, false, true)
	if !strings.Contains(formatted, ">  4 | key: 3") {
		t.Fatalf("formatted error %q does not mark line 4 with its source text", formatted)
	}
	lines := strings.Split(formatted, "\n")
	var markIdx int = -1
	for i, l := range lines {
		if strings.HasPrefix(l, ">  4 |") {
			markIdx = i
		}
	}
	if markIdx == -1 || markIdx+1 >= len(lines) {
		t.Fatalf("no marked line in %q", formatted)
	}
	if !strings.Contains(lines[markIdx+1], "^") {
		t.Fatalf("line after the marker has no caret: %q", lines[markIdx+1])
	}
}
