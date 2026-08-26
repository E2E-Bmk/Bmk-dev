package integration

import (
	"reflect"
	"testing"

	yaml "github.com/goccy/go-yaml"
	"github.com/goccy/go-yaml/ast"
)

type kindVisitor func(ast.Node)

func (f kindVisitor) Visit(n ast.Node) ast.Visitor { f(n); return f }

// collectKinds records the node-kind name of every node in the subtree.
func collectKinds(root ast.Node, kinds map[string]bool) {
	ast.Walk(kindVisitor(func(n ast.Node) { kinds[n.Type().String()] = true }), root)
}

// mergeDocs merges the first document of src into the first document of dst
// at the tree level.
func mergeDocs(dst, src *ast.File) error {
	return ast.Merge(dst.Docs[0].Body, src.Docs[0].Body)
}

func decodeUntyped(t *testing.T, src string, opts ...yaml.DecodeOption) interface{} {
	t.Helper()
	var v interface{}
	if err := yaml.UnmarshalWithOptions([]byte(src), &v, opts...); err != nil {
		t.Fatalf("Unmarshal(%q): %v", src, err)
	}
	return v
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
