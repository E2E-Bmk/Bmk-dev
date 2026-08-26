package atomic

import (
	"reflect"
	"testing"

	yaml "github.com/goccy/go-yaml"
)

// decodeUntyped unmarshals one document into an untyped destination and
// fails the test on error.
func decodeUntyped(t *testing.T, src string) interface{} {
	t.Helper()
	var v interface{}
	if err := yaml.Unmarshal([]byte(src), &v); err != nil {
		t.Fatalf("Unmarshal(%q): %v", src, err)
	}
	return v
}

// scalar decodes "v: <lit>" into an untyped map and returns the value slot.
func scalar(t *testing.T, lit string) interface{} {
	t.Helper()
	v := decodeUntyped(t, "v: "+lit+"\n")
	m, ok := v.(map[string]interface{})
	if !ok {
		t.Fatalf("decode of %q produced %T, want map[string]interface{}", lit, v)
	}
	return m["v"]
}

// unmarshalInto decodes src into dst and returns the error for inspection.
func unmarshalInto(t *testing.T, src string, dst interface{}, opts ...yaml.DecodeOption) error {
	t.Helper()
	return yaml.UnmarshalWithOptions([]byte(src), dst, opts...)
}

func mustMarshal(t *testing.T, v interface{}, opts ...yaml.EncodeOption) string {
	t.Helper()
	out, err := yaml.MarshalWithOptions(v, opts...)
	if err != nil {
		t.Fatalf("Marshal(%#v): %v", v, err)
	}
	return string(out)
}

func wantEqual(t *testing.T, got, want interface{}, label string) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("%s: got %#v (%T), want %#v (%T)", label, got, got, want, want)
	}
}
