package atomic

import (
	"strings"
	"testing"
)

// Verifies: Anchors, Aliases, and Merge Keys > Resolution.
func TestAliasResolvesToAnchorValue(t *testing.T) {
	v := decodeUntyped(t, "a: &x 42\nb: *x\n")
	m := v.(map[string]interface{})
	wantEqual(t, m["a"], uint64(42), "anchor value")
	wantEqual(t, m["b"], uint64(42), "alias value")
}

// Verifies: Anchors, Aliases, and Merge Keys > Resolution (alias and anchor
// decode to the same shared Go value for container values).
func TestAliasSharesContainerIdentity(t *testing.T) {
	v := decodeUntyped(t, "a: &x\n  k: 1\nb: *x\n")
	root := v.(map[string]interface{})
	ma := root["a"].(map[string]interface{})
	mb := root["b"].(map[string]interface{})
	wantEqual(t, mb["k"], uint64(1), "alias content")
	ma["k"] = "mutated"
	if mb["k"] != "mutated" {
		t.Fatalf("mutating the anchored map is not observable through the alias: got %#v", mb["k"])
	}
}

// Verifies: Anchors, Aliases, and Merge Keys > Failure path; Error Semantics
// (alias to an undefined anchor).
func TestUndefinedAliasFails(t *testing.T) {
	var v interface{}
	err := unmarshalInto(t, "a: *missing\n", &v)
	if err == nil {
		t.Fatal("expected an error for the undefined alias")
	}
	if !strings.Contains(err.Error(), `could not find alias "missing"`) {
		t.Fatalf("message %q does not contain could not find alias with the quoted name", err.Error())
	}
}

// Verifies: Anchors, Aliases, and Merge Keys > Merge keys (splice; explicit
// host entries win).
func TestMergeKeySplice(t *testing.T) {
	src := "base: &b\n  x: 1\n  y: 2\nderived:\n  <<: *b\n  y: 99\n  z: 3\n"
	v := decodeUntyped(t, src)
	derived := v.(map[string]interface{})["derived"].(map[string]interface{})
	wantEqual(t, derived["x"], uint64(1), "merged entry")
	wantEqual(t, derived["y"], uint64(99), "host entry wins over merged entry")
	wantEqual(t, derived["z"], uint64(3), "host-only entry")
}

// Verifies: Anchors, Aliases, and Merge Keys > Encoding anchors (anchor and
// alias struct tag options).
func TestAnchorAliasStructTags(t *testing.T) {
	type inner struct {
		X int `yaml:"x"`
	}
	type doc struct {
		P *inner `yaml:"p,anchor"`
		Q *inner `yaml:"q,alias"`
	}
	shared := &inner{7}
	out := mustMarshal(t, doc{P: shared, Q: shared})
	want := "p: &p\n  x: 7\nq: *p\n"
	if out != want {
		t.Fatalf("anchor/alias encode = %q, want %q", out, want)
	}

	// An explicit name via anchor=name / alias=name.
	type namedDoc struct {
		P *inner `yaml:"p,anchor=root"`
		Q *inner `yaml:"q,alias=root"`
	}
	outNamed := mustMarshal(t, namedDoc{P: shared, Q: shared})
	wantNamed := "p: &root\n  x: 7\nq: *root\n"
	if outNamed != wantNamed {
		t.Fatalf("named anchor encode = %q, want %q", outNamed, wantNamed)
	}

	// The emitted document decodes back to shared values.
	var back doc
	if err := unmarshalInto(t, out, &back); err != nil {
		t.Fatal(err)
	}
	if back.P == nil || back.P != back.Q {
		t.Fatalf("decoded anchor/alias fields are not the same pointer: p=%p q=%p", back.P, back.Q)
	}
	if back.P.X != 7 {
		t.Fatalf("decoded shared value X = %d, want 7", back.P.X)
	}
}
