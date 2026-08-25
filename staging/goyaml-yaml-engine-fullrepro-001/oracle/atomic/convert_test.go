package atomic

import (
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
)

// Verifies: Format Conversion > YAML to JSON (scalar types and document key
// order).
func TestYAMLToJSONScalarsAndOrder(t *testing.T) {
	out, err := yaml.YAMLToJSON([]byte("z: 1\na: text\nf: 1.5\nb: true\nn: null\n"))
	if err != nil {
		t.Fatal(err)
	}
	want := `{"z": 1, "a": "text", "f": 1.5, "b": true, "n": null}`
	if strings.TrimSpace(string(out)) != want {
		t.Fatalf("YAMLToJSON = %q, want %q", out, want)
	}
}

// Verifies: Format Conversion > YAML to JSON (anchors, aliases, and merge
// keys resolve before conversion); Anchors, Aliases, and Merge Keys > Merge
// keys.
func TestYAMLToJSONResolvesAnchorsAndMerge(t *testing.T) {
	src := "base: &b\n  x: 1\nderived:\n  <<: *b\n  y: 2\n"
	out, err := yaml.YAMLToJSON([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	want := `{"base": {"x": 1}, "derived": {"x": 1, "y": 2}}`
	if strings.TrimSpace(string(out)) != want {
		t.Fatalf("YAMLToJSON = %q, want %q", out, want)
	}
}

// Verifies: Format Conversion > JSON to YAML (block style output).
func TestJSONToYAMLBlockStyle(t *testing.T) {
	out, err := yaml.JSONToYAML([]byte(`{"a":[1,2],"b":"x"}`))
	if err != nil {
		t.Fatal(err)
	}
	want := "a:\n- 1\n- 2\nb: x\n"
	if string(out) != want {
		t.Fatalf("JSONToYAML = %q, want %q", out, want)
	}
}

// Verifies: Format Conversion (parse failures return source-annotated
// errors); Error Semantics.
func TestConverterErrorsAnnotated(t *testing.T) {
	_, err := yaml.YAMLToJSON([]byte("a: [1,\n"))
	if err == nil {
		t.Fatal("expected an error for malformed YAML input")
	}
	if !strings.HasPrefix(err.Error(), "[") || !strings.Contains(err.Error(), "^") {
		t.Fatalf("converter error %q is not source-annotated", err.Error())
	}
	_, err2 := yaml.JSONToYAML([]byte(`{"a": `))
	if err2 == nil {
		t.Fatal("expected an error for malformed JSON input")
	}
}
