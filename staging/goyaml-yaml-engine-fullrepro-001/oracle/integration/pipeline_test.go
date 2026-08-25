package integration

import (
	"bytes"
	"errors"
	"io"
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/lexer"
	"github.com/goccy/go-yaml/parser"
)

// Verifies: Anchors, Aliases, and Merge Keys + Format Conversion (anchor
// resolution observable through decoded values and through conversion).
func TestAnchorSharingAcrossViews(t *testing.T) {
	src := "defaults: &d\n  retries: 3\njob_a:\n  <<: *d\n  name: a\njob_b: *d\n"
	v := decodeUntyped(t, src)
	root := v.(map[string]interface{})
	jobA := root["job_a"].(map[string]interface{})
	wantEqual(t, jobA["retries"], uint64(3), "merged retries")
	wantEqual(t, jobA["name"], "a", "own key")
	// job_b shares identity with defaults.
	defaults := root["defaults"].(map[string]interface{})
	jobB := root["job_b"].(map[string]interface{})
	defaults["retries"] = uint64(9)
	wantEqual(t, jobB["retries"], uint64(9), "alias shares the anchored map")

	jsonBytes, err := yaml.YAMLToJSON([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	text := string(jsonBytes)
	if !strings.Contains(text, `"job_b": {"retries": 3}`) {
		t.Fatalf("conversion did not resolve the alias: %q", text)
	}
	if !strings.Contains(text, `"job_a": {"retries": 3, "name": "a"}`) {
		t.Fatalf("conversion did not resolve the merge key: %q", text)
	}
}

// Verifies: Anchors, Aliases, and Merge Keys > Encoding anchors (tag-driven
// anchor emission round-trips through parse and decode).
func TestAnchorAliasTagRoundTrip(t *testing.T) {
	type box struct {
		V int `yaml:"v"`
	}
	type doc struct {
		P *box `yaml:"p,anchor"`
		Q *box `yaml:"q,alias"`
	}
	shared := &box{11}
	out := mustMarshal(t, doc{P: shared, Q: shared})
	if out != "p: &p\n  v: 11\nq: *p\n" {
		t.Fatalf("encode = %q", out)
	}
	// The emitted document parses to a tree containing an anchor and an
	// alias node.
	f, err := parser.ParseBytes([]byte(out), 0)
	if err != nil {
		t.Fatal(err)
	}
	kinds := map[string]bool{}
	collectKinds(f.Docs[0], kinds)
	if !kinds["Anchor"] || !kinds["Alias"] {
		t.Fatalf("parsed tree kinds %v lack Anchor/Alias nodes", kinds)
	}
	// And decodes back to shared values.
	var back doc
	if err := yaml.Unmarshal([]byte(out), &back); err != nil {
		t.Fatal(err)
	}
	if back.P != back.Q || back.P.V != 11 {
		t.Fatalf("decoded p=%p q=%p v=%d, want shared pointer with v=11", back.P, back.Q, back.P.V)
	}
}

// Verifies: Decoding into Go Values > Multiple documents + Encoding from Go
// Values > Multiple documents (multi-document round trip).
func TestMultiDocEncodeDecodeRoundTrip(t *testing.T) {
	docs := []interface{}{
		map[string]interface{}{"a": uint64(1)},
		map[string]interface{}{"b": "two"},
		map[string]interface{}{"c": true},
	}
	var buf bytes.Buffer
	enc := yaml.NewEncoder(&buf)
	for _, d := range docs {
		if err := enc.Encode(d); err != nil {
			t.Fatal(err)
		}
	}
	if err := enc.Close(); err != nil {
		t.Fatal(err)
	}
	if strings.Count(buf.String(), "---") != 2 {
		t.Fatalf("stream %q does not separate three documents with two --- lines", buf.String())
	}
	dec := yaml.NewDecoder(strings.NewReader(buf.String()))
	for i, want := range docs {
		var got interface{}
		if err := dec.Decode(&got); err != nil {
			t.Fatalf("document %d: %v", i, err)
		}
		wantEqual(t, got, want, "document round trip")
	}
	var extra interface{}
	if err := dec.Decode(&extra); !errors.Is(err, io.EOF) {
		t.Fatalf("after last document: %v, want io.EOF", err)
	}
}

// Verifies: Decoding into Go Values > Raw subtrees (raw capture round trips
// through encode and a second decode).
func TestRawMessageRoundTrip(t *testing.T) {
	type wrapper struct {
		Meta yaml.RawMessage `yaml:"meta"`
		Name string          `yaml:"name"`
	}
	src := "meta:\n  created: 2024-01-15\n  tags: [x, y]\nname: thing\n"
	var w wrapper
	if err := yaml.Unmarshal([]byte(src), &w); err != nil {
		t.Fatal(err)
	}
	if string(w.Meta) != "created: 2024-01-15\ntags: [x, y]" {
		t.Fatalf("raw capture = %q", string(w.Meta))
	}
	out := mustMarshal(t, w)
	var w2 wrapper
	if err := yaml.Unmarshal([]byte(out), &w2); err != nil {
		t.Fatalf("re-decode of %q: %v", out, err)
	}
	wantEqual(t, string(w2.Meta), string(w.Meta), "raw subtree after round trip")
	wantEqual(t, w2.Name, "thing", "sibling field")
}

// Verifies: Decoding into Go Values > Decoding through the tree (NodeToValue
// applies the same options as UnmarshalWithOptions).
func TestNodeToValueOptionsParity(t *testing.T) {
	src := "z: 1\na: 2\n"
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	var fromNode interface{}
	if err := yaml.NodeToValue(f.Docs[0].Body, &fromNode, yaml.UseOrderedMap()); err != nil {
		t.Fatal(err)
	}
	fromText := decodeUntyped(t, src, yaml.UseOrderedMap())
	ms, ok := fromNode.(yaml.MapSlice)
	if !ok {
		t.Fatalf("NodeToValue produced %T, want yaml.MapSlice", fromNode)
	}
	if ms[0].Key != "z" {
		t.Fatalf("order lost: %v", ms)
	}
	wantEqual(t, fromNode, fromText, "NodeToValue vs UnmarshalWithOptions")
}

// Verifies: Decoding into Go Values > Decoding through the tree
// (DecodeFromNode agrees with Unmarshal).
func TestDecodeFromNodeAgreesWithUnmarshal(t *testing.T) {
	src := "x: 5\nlist: [1, 2]\nname: n\n"
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	var fromNode, fromText interface{}
	if err := yaml.NewDecoder(strings.NewReader("")).DecodeFromNode(f.Docs[0].Body, &fromNode); err != nil {
		t.Fatal(err)
	}
	if err := yaml.Unmarshal([]byte(src), &fromText); err != nil {
		t.Fatal(err)
	}
	if fromNode == nil {
		t.Fatal("nil decode")
	}
	wantEqual(t, fromNode, fromText, "DecodeFromNode vs Unmarshal")
}

// Verifies: Encoding from Go Values > Quoting rules + Decoding into Go
// Values (every quoting decision round-trips to the original string).
func TestQuotingRoundTripBattery(t *testing.T) {
	inputs := []string{
		"null", "~", "123", "-3", "0x1F", "1.5", "1e3",
		"y", "yes", "Yes", "YES", "yEs", "on", "off", "true", "TRUE",
		"a: b", "- x", "#c", "&a", "*a", "!t", "|x", ">x", "[x", "{x",
		"", " lead", "trail ", "in side", "v1.2", "3.0.1", "héllo",
		"line1\nline2", "line1\nline2\n",
	}
	for _, s := range inputs {
		out := mustMarshal(t, map[string]string{"k": s})
		var back map[string]string
		if err := yaml.Unmarshal([]byte(out), &back); err != nil {
			t.Fatalf("re-decode of %q (from %q): %v", out, s, err)
		}
		if back["k"] != s {
			t.Fatalf("round trip of %q via %q produced %q", s, out, back["k"])
		}
	}
	// Untyped re-decode also returns strings, not re-typed scalars.
	for _, s := range []string{"null", "123", "true", "1.5"} {
		out := mustMarshal(t, map[string]string{"k": s})
		var v interface{}
		if err := yaml.Unmarshal([]byte(out), &v); err != nil {
			t.Fatal(err)
		}
		got := v.(map[string]interface{})["k"]
		if got != s {
			t.Fatalf("untyped round trip of %q produced %#v, want the string form", s, got)
		}
	}
}

// Verifies: Format Conversion + Decoding into Go Values (scalar typing is
// visible through YAMLToJSON rendering).
func TestScalarTypingThroughConverters(t *testing.T) {
	src := "u: 123\ni: -3\nf: 1.5\ns: 1e3\nb: true\nyaml11: yes\nq: \"42\"\nn: null\n"
	out, err := yaml.YAMLToJSON([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	text := strings.TrimSpace(string(out))
	want := `{"u": 123, "i": -3, "f": 1.5, "s": "1e3", "b": true, "yaml11": "yes", "q": "42", "n": null}`
	if text != want {
		t.Fatalf("YAMLToJSON = %q, want %q", text, want)
	}
}

// Verifies: Decoding into Go Values > Struct destinations (inline) +
// Encoding from Go Values (inline splice round trip).
func TestInlineStructRoundTrip(t *testing.T) {
	type Base struct {
		Kind string `yaml:"kind"`
	}
	type wide struct {
		Base `yaml:",inline"`
		Name string `yaml:"name"`
	}
	w := wide{Base{"engine"}, "primary"}
	out := mustMarshal(t, w)
	want := "kind: engine\nname: primary\n"
	if out != want {
		t.Fatalf("inline encode = %q, want %q", out, want)
	}
	var back wide
	if err := yaml.Unmarshal([]byte(out), &back); err != nil {
		t.Fatal(err)
	}
	wantEqual(t, back, w, "inline round trip")
}

// Verifies: Decoding into Go Values > Multiple documents (decoder options
// apply to every document in the stream).
func TestStreamDecoderWithOptions(t *testing.T) {
	dec := yaml.NewDecoder(strings.NewReader("z: 1\na: 2\n---\nq: 3\nb: 4\n"), yaml.UseOrderedMap())
	var d1, d2 interface{}
	if err := dec.Decode(&d1); err != nil {
		t.Fatal(err)
	}
	if err := dec.Decode(&d2); err != nil {
		t.Fatal(err)
	}
	ms1, ok := d1.(yaml.MapSlice)
	if !ok {
		t.Fatalf("first document is %T, want yaml.MapSlice", d1)
	}
	if ms1[0].Key != "z" || ms1[1].Key != "a" {
		t.Fatalf("first document order lost: %v", ms1)
	}
	ms2 := d2.(yaml.MapSlice)
	if ms2[0].Key != "q" || ms2[1].Key != "b" {
		t.Fatalf("second document order lost: %v", ms2)
	}
}

// Verifies: Path Queries > Rewriting + Reading (rewrite visible through
// FilterFile and NodeToValue).
func TestPathRewriteThenReRead(t *testing.T) {
	src := "servers:\n  - host: a\n    weight: 1\n  - host: b\n    weight: 2\n"
	f, err := parser.ParseBytes([]byte(src), 0)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := yaml.PathString("$.servers[1].weight")
	if err := p.ReplaceWithReader(f, strings.NewReader("9")); err != nil {
		t.Fatal(err)
	}
	node, err := p.FilterFile(f)
	if err != nil {
		t.Fatal(err)
	}
	if node.String() != "9" {
		t.Fatalf("FilterFile after replace = %q, want 9", node.String())
	}
	var v interface{}
	if err := yaml.NodeToValue(f.Docs[0].Body, &v); err != nil {
		t.Fatal(err)
	}
	servers := v.(map[string]interface{})["servers"].([]interface{})
	wantEqual(t, servers[1].(map[string]interface{})["weight"], uint64(9), "weight after rewrite")
	wantEqual(t, servers[0].(map[string]interface{})["weight"], uint64(1), "untouched sibling")
}

// Verifies: Syntax Tree and Tokens (tokens -> tree -> values pipeline agrees
// with direct decoding).
func TestTokensToTreeToValuePipeline(t *testing.T) {
	src := "name: pipeline\nsteps:\n  - id: 1\n    run: build\n  - id: 2\n    run: test\n"
	tokens := lexer.Tokenize(src)
	if len(tokens) == 0 {
		t.Fatal("no tokens")
	}
	f, err := parser.Parse(tokens, 0)
	if err != nil {
		t.Fatal(err)
	}
	var fromTree, direct interface{}
	if err := yaml.NodeToValue(f.Docs[0].Body, &fromTree); err != nil {
		t.Fatal(err)
	}
	if err := yaml.Unmarshal([]byte(src), &direct); err != nil {
		t.Fatal(err)
	}
	if fromTree == nil {
		t.Fatal("nil decode from tree")
	}
	wantEqual(t, fromTree, direct, "tokens->tree->value vs direct")
	steps := fromTree.(map[string]interface{})["steps"].([]interface{})
	wantEqual(t, steps[1].(map[string]interface{})["run"], "test", "content check")
}

// Verifies: Comment Association + Encoding from Go Values (comment map
// emission through a streaming encoder).
func TestCommentMapThroughEncoder(t *testing.T) {
	cm := yaml.CommentMap{
		"$.a": []*yaml.Comment{yaml.HeadComment(" first")},
		"$.b": []*yaml.Comment{yaml.LineComment(" second")},
	}
	var buf bytes.Buffer
	enc := yaml.NewEncoder(&buf, yaml.WithComment(cm))
	if err := enc.Encode(yaml.MapSlice{
		yaml.MapItem{Key: "a", Value: 1},
		yaml.MapItem{Key: "b", Value: 2},
	}); err != nil {
		t.Fatal(err)
	}
	if err := enc.Close(); err != nil {
		t.Fatal(err)
	}
	want := "# first\na: 1\nb: 2 # second\n"
	if buf.String() != want {
		t.Fatalf("encoder output = %q, want %q", buf.String(), want)
	}
}

// Verifies: Encoding from Go Values > Value-to-tree (ValueToNode output is
// usable for path replacement).
func TestValueToNodeUsableInRewrite(t *testing.T) {
	f, err := parser.ParseBytes([]byte("config:\n  level: 1\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	node, err := yaml.ValueToNode(map[string]interface{}{"level": 2, "mode": "fast"})
	if err != nil {
		t.Fatal(err)
	}
	p, _ := yaml.PathString("$.config")
	if err := p.ReplaceWithNode(f, node); err != nil {
		t.Fatal(err)
	}
	var v interface{}
	if err := yaml.NodeToValue(f.Docs[0].Body, &v); err != nil {
		t.Fatal(err)
	}
	cfg := v.(map[string]interface{})["config"].(map[string]interface{})
	wantEqual(t, cfg["level"], uint64(2), "replaced level")
	wantEqual(t, cfg["mode"], "fast", "new key")
}

// Verifies: Anchors, Aliases, and Merge Keys > Failure path (undefined alias
// error is annotated into the true source position).
func TestUndefinedAliasAnnotatedPosition(t *testing.T) {
	src := "ok: 1\nbroken: *nowhere\n"
	var v interface{}
	err := yaml.Unmarshal([]byte(src), &v)
	if err == nil {
		t.Fatal("expected an undefined-alias error")
	}
	if !strings.HasPrefix(err.Error(), "[2:10]") {
		t.Fatalf("error %q does not point at the alias name position", err.Error())
	}
	if !strings.Contains(err.Error(), `could not find alias "nowhere"`) {
		t.Fatalf("error %q lacks the alias name", err.Error())
	}
	formatted := yaml.FormatError(err, false, true)
	if !strings.Contains(formatted, ">  2 | broken: *nowhere") {
		t.Fatalf("formatted %q does not mark the source line", formatted)
	}
}

// Verifies: Decoding into Go Values > Ordered maps + Encoding from Go Values
// (MapSlice as the pivot between decode and encode preserves duplicate-free
// document order).
func TestMapSlicePivotRoundTrip(t *testing.T) {
	src := "third: 3\nfirst: 1\nsecond: 2\n"
	var ms yaml.MapSlice
	if err := yaml.Unmarshal([]byte(src), &ms); err != nil {
		t.Fatal(err)
	}
	if len(ms) != 3 || ms[0].Key != "third" {
		t.Fatalf("MapSlice decode = %v", ms)
	}
	m := ms.ToMap()
	wantEqual(t, m["second"], uint64(2), "ToMap projection")
	out := mustMarshal(t, ms)
	if out != src {
		t.Fatalf("re-encode = %q, want document order %q", out, src)
	}
}

// Verifies: Syntax Tree and Tokens > Nodes (tree-level ast.Merge feeds
// decoding like any parsed tree).
func TestAstMergeThenDecode(t *testing.T) {
	dst, err := parser.ParseBytes([]byte("a: 1\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	src, err := parser.ParseBytes([]byte("b: 2\n"), 0)
	if err != nil {
		t.Fatal(err)
	}
	if err := mergeDocs(dst, src); err != nil {
		t.Fatal(err)
	}
	var v interface{}
	if err := yaml.NodeToValue(dst.Docs[0].Body, &v); err != nil {
		t.Fatal(err)
	}
	m := v.(map[string]interface{})
	wantEqual(t, m["a"], uint64(1), "original entry")
	wantEqual(t, m["b"], uint64(2), "merged entry")
}
