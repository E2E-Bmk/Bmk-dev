package atomic

import (
	"fmt"
	"reflect"
	"sort"
	"testing"

	"github.com/ohler55/ojg/jp"
)

// store returns the canonical test document used across the suite.
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

// eqVals compares result slices in order; a nil result and an empty
// result are both treated as empty.
func eqVals(t *testing.T, what string, want, got []any) {
	t.Helper()
	if len(want) == 0 && len(got) == 0 {
		return
	}
	if !reflect.DeepEqual(want, got) {
		t.Fatalf("%s: want %#v got %#v", what, want, got)
	}
}

// eqSet compares result slices ignoring order (for map-derived results
// whose order the engine leaves unspecified).
func eqSet(t *testing.T, what string, want, got []any) {
	t.Helper()
	if len(want) != len(got) {
		t.Fatalf("%s: want %d values %#v got %d %#v", what, len(want), want, len(got), got)
	}
	ws := make([]string, len(want))
	gs := make([]string, len(got))
	for i := range want {
		ws[i] = fmt.Sprintf("%#v", want[i])
		gs[i] = fmt.Sprintf("%#v", got[i])
	}
	sort.Strings(ws)
	sort.Strings(gs)
	if !reflect.DeepEqual(ws, gs) {
		t.Fatalf("%s: want set %v got %v", what, ws, gs)
	}
}

func wantErr(t *testing.T, what string, err error, exact string) {
	t.Helper()
	if err == nil {
		t.Fatalf("%s: expected error %q, got nil", what, exact)
	}
	if err.Error() != exact {
		t.Fatalf("%s: want error %q got %q", what, exact, err.Error())
	}
}

func wantNoErr(t *testing.T, what string, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("%s: unexpected error %v", what, err)
	}
}

func wantPanic(t *testing.T, what, exact string, fn func()) {
	t.Helper()
	defer func() {
		r := recover()
		if r == nil {
			t.Fatalf("%s: expected panic %q, got none", what, exact)
		}
		msg := fmt.Sprint(r)
		if e, ok := r.(error); ok {
			msg = e.Error()
		}
		if msg != exact {
			t.Fatalf("%s: want panic %q got %q", what, exact, msg)
		}
	}()
	fn()
}

func locStrs(locs []jp.Expr) []string {
	out := make([]string, 0, len(locs))
	for _, l := range locs {
		out = append(out, l.String())
	}
	return out
}

func eqStrs(t *testing.T, what string, want, got []string) {
	t.Helper()
	if len(want) == 0 && len(got) == 0 {
		return
	}
	if !reflect.DeepEqual(want, got) {
		t.Fatalf("%s: want %v got %v", what, want, got)
	}
}

func eqStrSet(t *testing.T, what string, want, got []string) {
	t.Helper()
	w := append([]string(nil), want...)
	g := append([]string(nil), got...)
	sort.Strings(w)
	sort.Strings(g)
	if len(w) == 0 && len(g) == 0 {
		return
	}
	if !reflect.DeepEqual(w, g) {
		t.Fatalf("%s: want set %v got %v", what, w, g)
	}
}
