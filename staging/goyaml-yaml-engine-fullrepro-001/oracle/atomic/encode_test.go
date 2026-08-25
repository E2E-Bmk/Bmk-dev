package atomic

import (
	"bytes"
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
)

// Verifies: Encoding from Go Values > Key derivation and ordering.
func TestEncodeKeyDerivation(t *testing.T) {
	type s struct {
		Tagged   int `yaml:"custom"`
		JSONOnly int `json:"jt"`
		Count    int
	}
	out := mustMarshal(t, s{1, 2, 3})
	want := "custom: 1\njt: 2\ncount: 3\n"
	if out != want {
		t.Fatalf("encode = %q, want %q", out, want)
	}
}

// Verifies: Encoding from Go Values > Key derivation and ordering (Go map
// keys sorted; MapSlice keys in slice order).
func TestEncodeMapKeyOrdering(t *testing.T) {
	out := mustMarshal(t, map[string]int{"zebra": 1, "alpha": 2, "mid": 3})
	want := "alpha: 2\nmid: 3\nzebra: 1\n"
	if out != want {
		t.Fatalf("map encode = %q, want sorted keys %q", out, want)
	}
	ms := yaml.MapSlice{
		yaml.MapItem{Key: "zebra", Value: 1},
		yaml.MapItem{Key: "alpha", Value: 2},
	}
	outMS := mustMarshal(t, ms)
	wantMS := "zebra: 1\nalpha: 2\n"
	if outMS != wantMS {
		t.Fatalf("MapSlice encode = %q, want slice order %q", outMS, wantMS)
	}
}

// Verifies: Encoding from Go Values > Key derivation and ordering (nil
// values encode as null).
func TestEncodeNilAsNull(t *testing.T) {
	var p *int
	out := mustMarshal(t, map[string]interface{}{"a": nil, "b": p})
	want := "a: null\nb: null\n"
	if out != want {
		t.Fatalf("nil encode = %q, want %q", out, want)
	}
}

// Verifies: Encoding from Go Values > Quoting rules (spellings of other
// scalar types are quoted; 1e3 stays unquoted).
func TestQuoteOtherScalarSpellings(t *testing.T) {
	quoted := []string{"null", "~", "123", "-3", "0x1F", "1.5"}
	for _, s := range quoted {
		out := mustMarshal(t, map[string]string{"k": s})
		want := "k: \"" + s + "\"\n"
		if out != want {
			t.Fatalf("string %q encoded as %q, want quoted %q", s, out, want)
		}
	}
	out := mustMarshal(t, map[string]string{"k": "1e3"})
	if out != "k: 1e3\n" {
		t.Fatalf("1e3 encoded as %q, want unquoted", out)
	}
}

// Verifies: Encoding from Go Values > Quoting rules (boolean-like words in
// lowercase, Title-case, and all-uppercase; mixed casing stays plain).
func TestQuoteBooleanLikeWords(t *testing.T) {
	for _, s := range []string{
		"y", "n", "yes", "no", "on", "off", "true", "false",
		"Y", "N", "Yes", "No", "On", "Off", "True", "False",
		"YES", "NO", "ON", "OFF", "TRUE", "FALSE",
	} {
		out := mustMarshal(t, map[string]string{"k": s})
		want := "k: \"" + s + "\"\n"
		if out != want {
			t.Fatalf("boolean-like %q encoded as %q, want quoted %q", s, out, want)
		}
	}
	for _, s := range []string{"yEs", "oN", "tRue", "fAlse"} {
		out := mustMarshal(t, map[string]string{"k": s})
		want := "k: " + s + "\n"
		if out != want {
			t.Fatalf("mixed-case %q encoded as %q, want unquoted %q", s, out, want)
		}
	}
}

// Verifies: Encoding from Go Values > Quoting rules (strings that begin a
// YAML construct are quoted).
func TestQuoteConstructStarters(t *testing.T) {
	cases := map[string]string{
		"a: b": `k: "a: b"` + "\n",
		"- x":  `k: "- x"` + "\n",
		"#c":   `k: "#c"` + "\n",
		"%v":   `k: "%v"` + "\n",
		"&a":   `k: "&a"` + "\n",
		"*a":   `k: "*a"` + "\n",
		"!t":   `k: "!t"` + "\n",
		"|x":   `k: "|x"` + "\n",
		">x":   `k: ">x"` + "\n",
		"[x":   `k: "[x"` + "\n",
		"{x":   `k: "{x"` + "\n",
		"@x":   `k: "@x"` + "\n",
		"`x":   "k: \"`x\"\n",
		"'x":   `k: "'x"` + "\n",
	}
	for s, want := range cases {
		out := mustMarshal(t, map[string]string{"k": s})
		if out != want {
			t.Fatalf("construct starter %q encoded as %q, want %q", s, out, want)
		}
	}
}

// Verifies: Encoding from Go Values > Quoting rules (empty strings and
// leading/trailing spaces quote; interior spaces, version-like forms and
// non-ASCII text stay plain).
func TestQuoteEdgeAndPlainStrings(t *testing.T) {
	quoted := map[string]string{
		"":       `k: ""` + "\n",
		" lead":  `k: " lead"` + "\n",
		"trail ": `k: "trail "` + "\n",
	}
	for s, want := range quoted {
		out := mustMarshal(t, map[string]string{"k": s})
		if out != want {
			t.Fatalf("string %q encoded as %q, want %q", s, out, want)
		}
	}
	plain := []string{"in side", "v1.2", "3.0.1", "héllo"}
	for _, s := range plain {
		out := mustMarshal(t, map[string]string{"k": s})
		want := "k: " + s + "\n"
		if out != want {
			t.Fatalf("plain string %q encoded as %q, want unquoted %q", s, out, want)
		}
	}
}

// Verifies: Encoding from Go Values > Quoting rules (strings containing
// newlines become literal block scalars).
func TestMultilineStringsUseLiteralBlocks(t *testing.T) {
	out := mustMarshal(t, map[string]string{"k": "line1\nline2"})
	want := "k: |-\n  line1\n  line2\n"
	if out != want {
		t.Fatalf("no-final-newline multiline = %q, want %q", out, want)
	}
	out2 := mustMarshal(t, map[string]string{"k": "line1\nline2\n"})
	want2 := "k: |\n  line1\n  line2\n"
	if out2 != want2 {
		t.Fatalf("final-newline multiline = %q, want %q", out2, want2)
	}
}

// Verifies: Encoding from Go Values > Quoting rules (UseSingleQuote).
func TestUseSingleQuoteOption(t *testing.T) {
	out := mustMarshal(t, map[string]string{"k": "123"}, yaml.UseSingleQuote(true))
	want := "k: '123'\n"
	if out != want {
		t.Fatalf("single-quote encode = %q, want %q", out, want)
	}
}

// Verifies: Encoding from Go Values > Styles and layout options (Flow, JSON).
func TestFlowAndJSONStyles(t *testing.T) {
	val := map[string]interface{}{"a": []interface{}{1, 2}}
	flow := mustMarshal(t, val, yaml.Flow(true))
	if flow != "{a: [1, 2]}\n" {
		t.Fatalf("flow = %q, want {a: [1, 2]}", flow)
	}
	js := mustMarshal(t, map[string]interface{}{"a": "x", "b": []interface{}{1, "two"}}, yaml.JSON())
	want := "{\"a\": \"x\", \"b\": [1, \"two\"]}\n"
	if js != want {
		t.Fatalf("json = %q, want %q", js, want)
	}
}

// Verifies: Encoding from Go Values > Styles and layout options (Indent,
// IndentSequence).
func TestIndentAndIndentSequence(t *testing.T) {
	val := map[string]interface{}{"a": []interface{}{1, 2}}
	// Default: dashes flush with the parent key column.
	def := mustMarshal(t, val)
	if def != "a:\n- 1\n- 2\n" {
		t.Fatalf("default sequence layout = %q, want flush dashes", def)
	}
	seq := mustMarshal(t, val, yaml.IndentSequence(true))
	if seq != "a:\n  - 1\n  - 2\n" {
		t.Fatalf("IndentSequence = %q, want two-space indented dashes", seq)
	}
	wide := mustMarshal(t, val, yaml.Indent(4), yaml.IndentSequence(true))
	if wide != "a:\n    - 1\n    - 2\n" {
		t.Fatalf("Indent(4) = %q, want four-space indented dashes", wide)
	}
	nested := mustMarshal(t, map[string]interface{}{"outer": map[string]interface{}{"inner": 1}}, yaml.Indent(4))
	if nested != "outer:\n    inner: 1\n" {
		t.Fatalf("Indent(4) mapping = %q, want four-space nesting", nested)
	}
}

// Verifies: Encoding from Go Values > Value shaping options (AutoInt).
func TestAutoIntOption(t *testing.T) {
	out := mustMarshal(t, map[string]float64{"a": 3.0, "b": 3.5}, yaml.AutoInt())
	want := "a: 3\nb: 3.5\n"
	if out != want {
		t.Fatalf("AutoInt = %q, want %q", out, want)
	}
}

// Verifies: Encoding from Go Values > Value shaping options (OmitEmpty,
// OmitZero, per-field tag options, all-dropped struct encodes as {}).
func TestOmitEmptyAndOmitZero(t *testing.T) {
	type s struct {
		A int    `yaml:"a"`
		B string `yaml:"b"`
	}
	if out := mustMarshal(t, s{}, yaml.OmitEmpty()); out != "{}\n" {
		t.Fatalf("OmitEmpty all-empty = %q, want {}", out)
	}
	if out := mustMarshal(t, s{}, yaml.OmitZero()); out != "{}\n" {
		t.Fatalf("OmitZero all-zero = %q, want {}", out)
	}
	if out := mustMarshal(t, s{A: 1}, yaml.OmitEmpty()); out != "a: 1\n" {
		t.Fatalf("OmitEmpty partial = %q, want only a", out)
	}
	type tagged struct {
		A int `yaml:"a,omitempty"`
		B int `yaml:"b"`
	}
	if out := mustMarshal(t, tagged{B: 2}); out != "b: 2\n" {
		t.Fatalf("omitempty tag = %q, want only b", out)
	}
	type taggedZero struct {
		A int `yaml:"a,omitzero"`
		B int `yaml:"b"`
	}
	if out := mustMarshal(t, taggedZero{B: 2}); out != "b: 2\n" {
		t.Fatalf("omitzero tag = %q, want only b", out)
	}
}

// Verifies: Encoding from Go Values > Multiple documents.
func TestEncoderMultipleDocuments(t *testing.T) {
	var buf bytes.Buffer
	enc := yaml.NewEncoder(&buf)
	if err := enc.Encode(map[string]int{"a": 1}); err != nil {
		t.Fatal(err)
	}
	if err := enc.Encode(map[string]int{"b": 2}); err != nil {
		t.Fatal(err)
	}
	if err := enc.Close(); err != nil {
		t.Fatal(err)
	}
	want := "a: 1\n---\nb: 2\n"
	if buf.String() != want {
		t.Fatalf("multi-document encode = %q, want %q", buf.String(), want)
	}
}

// Verifies: Encoding from Go Values > Value-to-tree (ValueToNode renders
// identically to Marshal).
func TestValueToNodeRendersLikeMarshal(t *testing.T) {
	val := map[string]interface{}{"a": []interface{}{1, 2}, "b": "x"}
	node, err := yaml.ValueToNode(val)
	if err != nil {
		t.Fatal(err)
	}
	rendered := node.String()
	if rendered == "" {
		t.Fatal("ValueToNode rendering is empty")
	}
	marshaled := mustMarshal(t, val)
	if rendered != strings.TrimSuffix(marshaled, "\n") {
		t.Fatalf("node rendering %q differs from Marshal output %q", rendered, marshaled)
	}
	if !strings.Contains(rendered, "b: x") {
		t.Fatalf("rendering %q does not contain the expected mapping content", rendered)
	}
}

// Verifies: Encoding from Go Values (exported constants).
func TestExportedConstants(t *testing.T) {
	if yaml.StructTagName != "yaml" {
		t.Fatalf("StructTagName = %q, want yaml", yaml.StructTagName)
	}
	if yaml.DefaultIndentSpaces != 2 {
		t.Fatalf("DefaultIndentSpaces = %d, want 2", yaml.DefaultIndentSpaces)
	}
}
