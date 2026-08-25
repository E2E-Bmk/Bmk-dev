package atomic

import (
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/ast"
)

type bytesMarshalerType struct{ v string }

func (b bytesMarshalerType) MarshalYAML() ([]byte, error) { return []byte("spliced-" + b.v), nil }

type interfaceMarshalerType struct{ v int }

func (m interfaceMarshalerType) MarshalYAML() (interface{}, error) {
	return map[string]int{"wrapped": m.v}, nil
}

type bytesUnmarshalerType struct{ raw string }

func (b *bytesUnmarshalerType) UnmarshalYAML(data []byte) error {
	b.raw = string(data)
	return nil
}

type interfaceUnmarshalerType struct{ n int }

func (u *interfaceUnmarshalerType) UnmarshalYAML(fn func(interface{}) error) error {
	var m map[string]int
	if err := fn(&m); err != nil {
		return err
	}
	u.n = m["n"]
	return nil
}

type nodeUnmarshalerType struct{ kind, text string }

func (u *nodeUnmarshalerType) UnmarshalYAML(n ast.Node) error {
	u.kind = n.Type().String()
	u.text = n.String()
	return nil
}

// Verifies: Custom Hooks > Marshaling interfaces (BytesMarshaler splices the
// returned bytes).
func TestBytesMarshalerSplice(t *testing.T) {
	var _ yaml.BytesMarshaler = bytesMarshalerType{}
	out := mustMarshal(t, map[string]interface{}{"m": bytesMarshalerType{"hello"}})
	want := "m: spliced-hello\n"
	if out != want {
		t.Fatalf("BytesMarshaler encode = %q, want %q", out, want)
	}
}

// Verifies: Custom Hooks > Marshaling interfaces (InterfaceMarshaler encodes
// the returned value in place).
func TestInterfaceMarshaler(t *testing.T) {
	var _ yaml.InterfaceMarshaler = interfaceMarshalerType{}
	out := mustMarshal(t, map[string]interface{}{"m": interfaceMarshalerType{4}})
	want := "m:\n  wrapped: 4\n"
	if out != want {
		t.Fatalf("InterfaceMarshaler encode = %q, want %q", out, want)
	}
}

// Verifies: Custom Hooks > Unmarshaling interfaces (BytesUnmarshaler receives
// the raw YAML text of its value).
func TestBytesUnmarshalerReceivesRawText(t *testing.T) {
	var s struct {
		M bytesUnmarshalerType `yaml:"m"`
	}
	var _ yaml.BytesUnmarshaler = &s.M
	if err := unmarshalInto(t, "m:\n  a: 1\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.M.raw != "a: 1" {
		t.Fatalf("BytesUnmarshaler received %q, want the raw value text a: 1", s.M.raw)
	}
}

// Verifies: Custom Hooks > Unmarshaling interfaces (InterfaceUnmarshaler
// receives a decode function).
func TestInterfaceUnmarshalerDecodeFunc(t *testing.T) {
	var s struct {
		M interfaceUnmarshalerType `yaml:"m"`
	}
	var _ yaml.InterfaceUnmarshaler = &s.M
	if err := unmarshalInto(t, "m:\n  n: 42\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.M.n != 42 {
		t.Fatalf("InterfaceUnmarshaler decoded %d, want 42", s.M.n)
	}
}

// Verifies: Custom Hooks > Unmarshaling interfaces (NodeUnmarshaler receives
// the value's syntax-tree node).
func TestNodeUnmarshalerReceivesNode(t *testing.T) {
	var s struct {
		M nodeUnmarshalerType `yaml:"m"`
	}
	var _ yaml.NodeUnmarshaler = &s.M
	if err := unmarshalInto(t, "m: [1, 2]\n", &s); err != nil {
		t.Fatal(err)
	}
	if s.M.kind != "Sequence" {
		t.Fatalf("NodeUnmarshaler node kind = %q, want Sequence", s.M.kind)
	}
	if s.M.text != "[1, 2]" {
		t.Fatalf("NodeUnmarshaler node text = %q, want [1, 2]", s.M.text)
	}
}

type optionHookType struct{ V int }

// Verifies: Custom Hooks > Registration (CustomMarshaler and
// CustomUnmarshaler options apply for a single call).
func TestCustomMarshalerAndUnmarshalerOptions(t *testing.T) {
	out := mustMarshal(t, map[string]optionHookType{"t": {3}},
		yaml.CustomMarshaler[optionHookType](func(v optionHookType) ([]byte, error) {
			return []byte("custom-3"), nil
		}))
	if out != "t: custom-3\n" {
		t.Fatalf("CustomMarshaler encode = %q, want t: custom-3", out)
	}
	// Without the option the hook does not apply.
	plain := mustMarshal(t, map[string]optionHookType{"t": {3}})
	if plain != "t:\n  v: 3\n" {
		t.Fatalf("plain encode = %q, want t:\\n  v: 3", plain)
	}

	var dst map[string]optionHookType
	err := unmarshalInto(t, "t: 9\n", &dst,
		yaml.CustomUnmarshaler[optionHookType](func(v *optionHookType, b []byte) error {
			v.V = 100
			return nil
		}))
	if err != nil {
		t.Fatal(err)
	}
	if dst["t"].V != 100 {
		t.Fatalf("CustomUnmarshaler decoded %d, want 100", dst["t"].V)
	}
}

type globalHookType struct{ V int }

// Verifies: Custom Hooks > Registration (global registration; the per-call
// option takes precedence for that call).
func TestGlobalRegistrationAndPrecedence(t *testing.T) {
	yaml.RegisterCustomMarshaler[globalHookType](func(v globalHookType) ([]byte, error) {
		return []byte("global"), nil
	})
	out := mustMarshal(t, map[string]globalHookType{"t": {3}})
	if out != "t: global\n" {
		t.Fatalf("global hook encode = %q, want t: global", out)
	}
	local := mustMarshal(t, map[string]globalHookType{"t": {3}},
		yaml.CustomMarshaler[globalHookType](func(v globalHookType) ([]byte, error) {
			return []byte("local"), nil
		}))
	if local != "t: local\n" {
		t.Fatalf("per-call option must win over global registration: got %q", local)
	}

	yaml.RegisterCustomUnmarshaler[globalHookType](func(v *globalHookType, b []byte) error {
		v.V = 55
		return nil
	})
	var dst map[string]globalHookType
	if err := unmarshalInto(t, "t: 1\n", &dst); err != nil {
		t.Fatal(err)
	}
	if dst["t"].V != 55 {
		t.Fatalf("global unmarshaler decoded %d, want 55", dst["t"].V)
	}
}

type jsonHookType int

func (j *jsonHookType) UnmarshalJSON(b []byte) error { *j = 77; return nil }
func (j jsonHookType) MarshalJSON() ([]byte, error)  { return []byte("88"), nil }

// Verifies: Custom Hooks > JSON interop (UseJSONMarshaler and
// UseJSONUnmarshaler).
func TestJSONInteropOptions(t *testing.T) {
	var n jsonHookType
	if err := unmarshalInto(t, "7\n", &n, yaml.UseJSONUnmarshaler()); err != nil {
		t.Fatal(err)
	}
	if n != 77 {
		t.Fatalf("UseJSONUnmarshaler decoded %d, want 77", n)
	}
	out := mustMarshal(t, map[string]jsonHookType{"v": 5}, yaml.UseJSONMarshaler())
	if out != "v: 88\n" {
		t.Fatalf("UseJSONMarshaler encode = %q, want v: 88", out)
	}
}

type fieldErrorValue struct{ field string }

func (e fieldErrorValue) Error() string       { return "port out of range" }
func (e fieldErrorValue) StructField() string { return e.field }

type fieldErrorSlice []fieldErrorValue

func (s fieldErrorSlice) Error() string { return s[0].Error() }

type sliceValidator struct{}

func (sliceValidator) Struct(interface{}) error { return fieldErrorSlice{{"Port"}} }

type plainValidator struct{}

func (plainValidator) Struct(interface{}) error { return fieldErrorValue{"Port"} }

// Verifies: Custom Hooks > Validation; Error Semantics (validator rejection).
func TestValidatorContract(t *testing.T) {
	var _ yaml.StructValidator = sliceValidator{}
	var _ yaml.FieldError = fieldErrorValue{}
	type server struct {
		Host string `yaml:"host"`
		Port int    `yaml:"port"`
	}
	src := "host: x\nport: 99999\n"

	// A slice of FieldError elements is source-annotated at the field.
	var s1 server
	err := unmarshalInto(t, src, &s1, yaml.Validator(sliceValidator{}))
	if err == nil {
		t.Fatal("expected a validation error")
	}
	if !strings.HasPrefix(err.Error(), "[2:7] port out of range") {
		t.Fatalf("slice validator error %q is not annotated at the field position", err.Error())
	}

	// Any other error shape is returned unchanged.
	var s2 server
	err2 := unmarshalInto(t, src, &s2, yaml.Validator(plainValidator{}))
	if err2 == nil {
		t.Fatal("expected a validation error")
	}
	if err2.Error() != "port out of range" {
		t.Fatalf("plain validator error %q was altered", err2.Error())
	}
}
