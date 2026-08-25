package atomic

import (
	"errors"
	"strings"
	"testing"

	yaml "github.com/goccy/go-yaml"
)

// Verifies: Error Semantics (messages begin with [line:column]).
func TestErrorMessageLineColumnPrefix(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "a: 1\nb: [1,\n", &v)
	if err == nil {
		t.Fatal("expected a decode error")
	}
	if !strings.HasPrefix(err.Error(), "[2:4]") {
		t.Fatalf("message %q does not begin with the 1-based [line:column]", err.Error())
	}
}

// Verifies: Error Semantics (FormatError renders a numbered excerpt with a
// caret and a > marker; colors appear exactly when colored is true).
func TestFormatErrorSourceExcerpt(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "a: [1, 2\n", &v)
	if err == nil {
		t.Fatal("expected a decode error")
	}
	plain := yaml.FormatError(err, false, true)
	if !strings.Contains(plain, ">  1 | a: [1, 2") {
		t.Fatalf("formatted error %q has no marked source line", plain)
	}
	if !strings.Contains(plain, "^") {
		t.Fatalf("formatted error %q has no caret", plain)
	}
	if strings.Contains(plain, "\x1b[") {
		t.Fatal("uncolored FormatError output contains ANSI escapes")
	}
	colored := yaml.FormatError(err, true, true)
	if !strings.Contains(colored, "\x1b[") {
		t.Fatal("colored FormatError output contains no ANSI escapes")
	}
	// With inclSource false the excerpt is omitted but the message stays.
	bare := yaml.FormatError(err, false, false)
	if strings.Contains(bare, "|") {
		t.Fatalf("FormatError without source %q still shows the excerpt", bare)
	}
	if !strings.Contains(bare, "sequence end token") {
		t.Fatalf("FormatError without source %q lost the message", bare)
	}
}

// Verifies: Error Semantics (malformed YAML matches *yaml.SyntaxError and
// carries the offending Token and a Message).
func TestSyntaxErrorType(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "a: [1, 2\n", &v)
	if err == nil {
		t.Fatal("expected a syntax error")
	}
	var se *yaml.SyntaxError
	if !errors.As(err, &se) {
		t.Fatalf("error %v does not match *yaml.SyntaxError", err)
	}
	if se.Message == "" {
		t.Fatal("SyntaxError.Message is empty")
	}
	if se.Token == nil || se.Token.Value != "[" {
		t.Fatalf("SyntaxError.Token = %+v, want the offending [ token", se.Token)
	}
}

// Verifies: Error Semantics (duplicate mapping key names the key and the
// earlier position).
func TestDuplicateKeyMessageShape(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "x: 0\nkey: 1\nother: 2\nkey: 3\n", &v)
	if err == nil {
		t.Fatal("expected a duplicate-key error")
	}
	if !strings.HasPrefix(err.Error(), "[4:1]") {
		t.Fatalf("message %q does not point at the duplicate occurrence", err.Error())
	}
	if !strings.Contains(err.Error(), `mapping key "key" already defined at [2:1]`) {
		t.Fatalf("message %q does not name the key and the earlier definition", err.Error())
	}
}

// Verifies: Error Semantics (unknown field under DisallowUnknownField).
func TestUnknownFieldErrorType(t *testing.T) {
	var s struct {
		A int `yaml:"a"`
	}
	err := unmarshalInto(t, "a: 1\nmystery: 2\n", &s, yaml.DisallowUnknownField())
	if err == nil {
		t.Fatal("expected an unknown-field error")
	}
	var ufe *yaml.UnknownFieldError
	if !errors.As(err, &ufe) {
		t.Fatalf("error %v does not match *yaml.UnknownFieldError", err)
	}
	if !strings.Contains(err.Error(), `unknown field "mystery"`) {
		t.Fatalf("message %q does not contain unknown field \"mystery\"", err.Error())
	}
}

// Verifies: Error Semantics (scalar that does not convert matches
// *yaml.TypeError with DstType, SrcType, StructFieldName, Token).
func TestTypeErrorFields(t *testing.T) {
	type target struct {
		N int `yaml:"n"`
	}
	var s target
	err := unmarshalInto(t, "n: hello\n", &s)
	if err == nil {
		t.Fatal("expected a type error")
	}
	var te *yaml.TypeError
	if !errors.As(err, &te) {
		t.Fatalf("error %v does not match *yaml.TypeError", err)
	}
	if te.DstType == nil || te.DstType.Kind().String() != "int" {
		t.Fatalf("DstType = %v, want int", te.DstType)
	}
	if te.SrcType == nil || te.SrcType.Kind().String() != "string" {
		t.Fatalf("SrcType = %v, want string", te.SrcType)
	}
	if te.StructFieldName == nil || *te.StructFieldName != "target.N" {
		t.Fatalf("StructFieldName = %v, want target.N", te.StructFieldName)
	}
	if te.Token == nil || te.Token.Value != "hello" {
		t.Fatalf("Token = %+v, want the offending hello token", te.Token)
	}
	if !strings.Contains(err.Error(), "cannot unmarshal string into Go struct field target.N of type int") {
		t.Fatalf("message %q lacks the cannot-unmarshal shape", err.Error())
	}
}

// Verifies: Error Semantics (integer literal exceeding the destination range
// matches *yaml.OverflowError).
func TestOverflowErrorType(t *testing.T) {
	var s struct {
		N int8 `yaml:"n"`
	}
	err := unmarshalInto(t, "n: 300\n", &s)
	if err == nil {
		t.Fatal("expected an overflow error")
	}
	var oe *yaml.OverflowError
	if !errors.As(err, &oe) {
		t.Fatalf("error %v does not match *yaml.OverflowError", err)
	}

	var s2 struct {
		N uint8 `yaml:"n"`
	}
	err2 := unmarshalInto(t, "n: -5\n", &s2)
	if err2 == nil {
		t.Fatal("expected an overflow error for a negative literal into an unsigned field")
	}
	var oe2 *yaml.OverflowError
	if !errors.As(err2, &oe2) {
		t.Fatalf("error %v does not match *yaml.OverflowError", err2)
	}
}

// Verifies: Error Semantics (yaml.Error is satisfied by engine errors
// through errors.As).
func TestYamlErrorInterface(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "a: [1,\n", &v)
	if err == nil {
		t.Fatal("expected an error")
	}
	var ye yaml.Error
	if !errors.As(err, &ye) {
		t.Fatalf("error %v does not match the yaml.Error interface", err)
	}

	var s struct {
		A int `yaml:"a"`
	}
	err2 := unmarshalInto(t, "a: 1\nb: 2\n", &s, yaml.DisallowUnknownField())
	var ye2 yaml.Error
	if !errors.As(err2, &ye2) {
		t.Fatalf("unknown-field error %v does not match the yaml.Error interface", err2)
	}
}
