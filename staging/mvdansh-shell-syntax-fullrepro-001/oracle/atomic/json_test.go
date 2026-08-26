// Spec2Repo oracle - atomic tests for mvdansh-shell-syntax-fullrepro-001
// Typed JSON Interchange
package atomic

import (
	"encoding/json"
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
	"mvdan.cc/sh/v3/syntax/typedjson"
)

func encode(t *testing.T, node syntax.Node) string {
	t.Helper()
	var b strings.Builder
	if err := typedjson.Encode(&b, node); err != nil {
		t.Fatal(err)
	}
	return b.String()
}

func TestEncodeTypeKeyFirst(t *testing.T) {
	f := parse(t, "foo\n")
	out := encode(t, f)
	if !strings.HasPrefix(out, `{"Type":"File",`) {
		t.Fatalf("output does not start with the root Type key: %s", out)
	}
	wantContains(t, out, `"Type":"CallExpr"`, "interface-typed Cmd carries Type")
	wantContains(t, out, `"Type":"Lit"`, "word parts carry Type")
	wantContains(t, out, `"Name":"src.sh"`, "file name field")
}

func TestEncodeNoTypeOnFixedFields(t *testing.T) {
	f := parse(t, "foo\n")
	out := encode(t, f)
	// Stmt objects inside File.Stmts have a fixed concrete type, so their
	// first key is Pos, not Type.
	wantContains(t, out, `"Stmts":[{"Pos":`, "statements carry no Type key")
}

func TestEncodePosObjects(t *testing.T) {
	f := parse(t, "foo\n")
	out := encode(t, f)
	wantContains(t, out, `"Pos":{"Offset":0,"Line":1,"Col":1}`, "position object shape")
	wantContains(t, out, `"End":{"Offset":3,"Line":1,"Col":4}`, "end object shape")
}

func TestEncodeOmitsZeroFields(t *testing.T) {
	f := parse(t, "foo\n")
	out := encode(t, f)
	wantContains(t, out, `"Type":"File"`, "root type tag present")
	wantContains(t, out, `"Stmts"`, "populated field encoded under its Go name")
	if strings.Contains(out, "Semicolon") {
		t.Fatalf("invalid Semicolon position was encoded: %s", out)
	}
	if strings.Contains(out, "Negated") || strings.Contains(out, "Background") {
		t.Fatalf("false booleans were encoded: %s", out)
	}
	f2, err := syntax.NewParser().Parse(strings.NewReader("foo\n"), "")
	if err != nil {
		t.Fatal(err)
	}
	out2 := encode(t, f2)
	if strings.Contains(out2, `"Name"`) {
		t.Fatalf("empty Name was encoded: %s", out2)
	}
}

func TestEncodeIndent(t *testing.T) {
	f := parse(t, "x=1\n")
	var b strings.Builder
	if err := (typedjson.EncodeOptions{Indent: "  "}).Encode(&b, f); err != nil {
		t.Fatal(err)
	}
	out := b.String()
	wantContains(t, out, "{\n  \"Type\": \"File\",", "indented output")
	// Indented output remains valid JSON.
	var v map[string]interface{}
	if err := json.Unmarshal([]byte(out), &v); err != nil {
		t.Fatalf("indented output is not valid JSON: %v", err)
	}
	wantEq(t, v["Type"], "File", "Type key")
}

func TestEncodeNonFileRoot(t *testing.T) {
	f := parse(t, "foo\n")
	w := call(t, f, 0).Args[0]
	out := encode(t, w)
	if !strings.HasPrefix(out, `{"Type":"Word",`) {
		t.Fatalf("word root does not start with Type: %s", out)
	}
	node, err := typedjson.Decode(strings.NewReader(out))
	if err != nil {
		t.Fatal(err)
	}
	dw, ok := node.(*syntax.Word)
	if !ok {
		t.Fatalf("decoded %T, want *syntax.Word", node)
	}
	wantEq(t, dw.Lit(), "foo", "decoded word content")
}

func TestDecodeRoundTrip(t *testing.T) {
	f := parse(t, "foo bar | baz\n")
	out := encode(t, f)
	node, err := typedjson.Decode(strings.NewReader(out))
	if err != nil {
		t.Fatal(err)
	}
	nf, ok := node.(*syntax.File)
	if !ok {
		t.Fatalf("decoded %T, want *syntax.File", node)
	}
	wantEq(t, printDefault(t, nf), printDefault(t, f), "reprint equality")
	wantEq(t, nf.Stmts[0].Pos(), f.Stmts[0].Pos(), "positions preserved")
}

func TestDecodeUnknownTypeError(t *testing.T) {
	_, err := typedjson.Decode(strings.NewReader(`{"Type":"Nope"}`))
	if err == nil {
		t.Fatal("expected error")
	}
	wantEq(t, err.Error(), `unknown type: "Nope"`, "error text")
}

func TestDecodeWhitespaceTolerant(t *testing.T) {
	f := parse(t, "x=1\n")
	var b strings.Builder
	if err := (typedjson.EncodeOptions{Indent: "\t"}).Encode(&b, f); err != nil {
		t.Fatal(err)
	}
	node, err := (typedjson.DecodeOptions{}).Decode(strings.NewReader(b.String()))
	if err != nil {
		t.Fatal(err)
	}
	wantEq(t, printDefault(t, node), "x=1\n", "decoded indented JSON")
}
