package integration

import (
	"fmt"
	"reflect"
	"sort"
	"testing"

	"github.com/ohler55/ojg/jp"
)

// store returns the canonical document used by the invariant checks.
func store() map[string]any {
	return map[string]any{
		"inv": []any{
			map[string]any{"sku": "A1", "qty": 3, "tags": []any{"new"}},
			map[string]any{"sku": "B2", "qty": 0},
			map[string]any{"sku": "C3", "qty": 9, "tags": []any{"new", "sale"}},
		},
		"meta":  map[string]any{"count": 3, "active": true},
		"name":  "main",
		"blank": nil,
		"limit": 7,
	}
}

func mustParse(t *testing.T, src string) jp.Expr {
	t.Helper()
	x, err := jp.ParseString(src)
	if err != nil {
		t.Fatalf("parse %q failed: %v", src, err)
	}
	return x
}

func eq(t *testing.T, what string, want, got any) {
	t.Helper()
	if !reflect.DeepEqual(want, got) {
		t.Fatalf("%s: want %#v got %#v", what, want, got)
	}
}

func wantNoErr(t *testing.T, what string, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("%s: unexpected error %v", what, err)
	}
}

// asMultiset renders values order-insensitively for comparison.
func asMultiset(vals []any) []string {
	out := make([]string, 0, len(vals))
	for _, v := range vals {
		out = append(out, fmt.Sprintf("%#v", v))
	}
	sort.Strings(out)
	return out
}

func eqMultiset(t *testing.T, what string, want, got []any) {
	t.Helper()
	w := asMultiset(want)
	g := asMultiset(got)
	if !reflect.DeepEqual(w, g) {
		t.Fatalf("%s: want multiset %v got %v", what, w, g)
	}
}

func locStrs(locs []jp.Expr) []string {
	out := make([]string, 0, len(locs))
	for _, l := range locs {
		out = append(out, l.String())
	}
	return out
}
