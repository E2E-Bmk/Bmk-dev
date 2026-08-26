package integration

import (
	"bytes"
	"reflect"
	"strconv"
	"strings"
	"testing"

	"mvdan.cc/sh/v3/syntax"
	"mvdan.cc/sh/v3/syntax/typedjson"
)

// checkJSONRoundTrip asserts CVI 3 for a single tree: encoding then
// decoding must reproduce a deep-equal tree that prints identically.
func checkJSONRoundTrip(t *testing.T, f *syntax.File, src string) {
	t.Helper()
	var buf bytes.Buffer
	if err := typedjson.Encode(&buf, f); err != nil {
		t.Fatalf("encode %q: %v", src, err)
	}
	if !strings.Contains(buf.String(), `"Type":"File"`) {
		t.Fatalf("encoded JSON for %q lacks the File type tag: %q", src, buf.String())
	}
	decoded, err := typedjson.Decode(&buf)
	if err != nil {
		t.Fatalf("decode %q: %v", src, err)
	}
	f2, ok := decoded.(*syntax.File)
	if !ok {
		t.Fatalf("decoded %q to %T, want *syntax.File", src, decoded)
	}
	if !reflect.DeepEqual(f, f2) {
		t.Fatalf("JSON round trip not deep-equal for %q", src)
	}
	before := printWith(t, f)
	after := printWith(t, f2)
	if before != after {
		t.Fatalf("JSON round trip changes print for %q\nbefore: %q\nafter:  %q", src, before, after)
	}
}

func TestJSONRoundTripBashCorpus(t *testing.T) {
	for _, src := range bashCorpus {
		checkJSONRoundTrip(t, mustParse(t, src, syntax.LangBash), src)
	}
}

func TestJSONRoundTripOtherDialects(t *testing.T) {
	for lang, corpus := range dialectCorpora() {
		if lang == syntax.LangBash {
			continue
		}
		for _, src := range corpus {
			checkJSONRoundTrip(t, mustParse(t, src, lang), src)
		}
	}
}

func TestJSONRoundTripSubtrees(t *testing.T) {
	f := mustParse(t, bashCorpus[0], syntax.LangBash)
	roundTrip := func(node syntax.Node, what string) syntax.Node {
		t.Helper()
		var buf bytes.Buffer
		if err := typedjson.Encode(&buf, node); err != nil {
			t.Fatalf("encode %s: %v", what, err)
		}
		decoded, err := typedjson.Decode(&buf)
		if err != nil {
			t.Fatalf("decode %s: %v", what, err)
		}
		if !reflect.DeepEqual(node, decoded) {
			t.Fatalf("%s JSON round trip not deep-equal", what)
		}
		return decoded
	}

	ifc := f.Stmts[0].Cmd
	if _, ok := roundTrip(ifc, "if clause").(*syntax.IfClause); !ok {
		t.Fatal("if clause decoded to unexpected type")
	}
	word := mustParse(t, "echo \"nested $inner\"\n", syntax.LangBash).
		Stmts[0].Cmd.(*syntax.CallExpr).Args[1]
	if _, ok := roundTrip(word, "word").(*syntax.Word); !ok {
		t.Fatal("word decoded to unexpected type")
	}
	part := word.Parts[0]
	if _, ok := roundTrip(part, "word part").(*syntax.DblQuoted); !ok {
		t.Fatal("word part decoded to unexpected type")
	}
}

func TestJSONStructuralRootsDoNotDecode(t *testing.T) {
	f := mustParse(t, "cat <in >out\n", syntax.LangBash)
	stmt := f.Stmts[0]
	for _, tc := range []struct {
		node syntax.Node
		name string
	}{
		{stmt, "Stmt"},
		{stmt.Redirs[0], "Redirect"},
	} {
		var buf bytes.Buffer
		if err := typedjson.Encode(&buf, tc.node); err != nil {
			t.Fatalf("encode %s: %v", tc.name, err)
		}
		_, err := typedjson.Decode(&buf)
		if err == nil {
			t.Fatalf("decoding a %s root should fail", tc.name)
		}
		want := "unknown type: " + strconv.Quote(tc.name)
		if err.Error() != want {
			t.Fatalf("decode %s error = %q, want %q", tc.name, err.Error(), want)
		}
	}
}

func TestJSONIndentedEncodeDecodesEqual(t *testing.T) {
	src := bashCorpus[6]
	f := mustParse(t, src, syntax.LangBash)
	var plain, indented bytes.Buffer
	if err := typedjson.Encode(&plain, f); err != nil {
		t.Fatalf("plain encode: %v", err)
	}
	opts := typedjson.EncodeOptions{Indent: "  "}
	if err := opts.Encode(&indented, f); err != nil {
		t.Fatalf("indented encode: %v", err)
	}
	if plain.String() == indented.String() {
		t.Fatal("indented encoding should differ textually from plain encoding")
	}
	fromPlain, err := typedjson.Decode(strings.NewReader(plain.String()))
	if err != nil {
		t.Fatalf("decode plain: %v", err)
	}
	fromIndented, err := typedjson.Decode(strings.NewReader(indented.String()))
	if err != nil {
		t.Fatalf("decode indented: %v", err)
	}
	if !reflect.DeepEqual(fromPlain, fromIndented) {
		t.Fatal("plain and indented encodings decode to different trees")
	}
}
