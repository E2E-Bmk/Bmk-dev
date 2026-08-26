package atomic

import (
	"fmt"
	"reflect"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func wantPanic(t *testing.T, frag string, f func()) {
	t.Helper()
	defer func() {
		r := recover()
		if r == nil {
			t.Fatalf("expected a panic containing %q, got none", frag)
		}
		if !strings.Contains(fmt.Sprint(r), frag) {
			t.Fatalf("panic %q does not contain %q", fmt.Sprint(r), frag)
		}
	}()
	f()
}

type secret struct{ v int }

type Vault struct {
	Label string
	S     secret
}

func TestComparerDecidesLeaf(t *testing.T) {
	near := cmp.Comparer(func(x, y float64) bool {
		d := x - y
		return d < 0.01 && d > -0.01
	})
	if !cmp.Equal(1.000, 1.005, near) {
		t.Fatal("the Comparer's verdict must decide the leaf (within tolerance)")
	}
	if cmp.Equal(1.0, 1.5, near) {
		t.Fatal("the Comparer's verdict must decide the leaf (outside tolerance)")
	}
}

func TestUnfilteredIgnorePanics(t *testing.T) {
	wantPanic(t, "cannot use an unfiltered option", func() {
		cmp.Equal(1, 1, cmp.Ignore())
	})
}

func TestAmbiguousOptionsPanic(t *testing.T) {
	wantPanic(t, "ambiguous set of applicable options", func() {
		cmp.Equal(1.0, 1.0,
			cmp.Comparer(func(a, b float64) bool { return true }),
			cmp.Comparer(func(a, b float64) bool { return false }))
	})
}

func TestInvalidComparerPanics(t *testing.T) {
	wantPanic(t, "invalid comparer function", func() {
		cmp.Comparer(func(a int, b string) bool { return true })
	})
	wantPanic(t, "invalid comparer function", func() {
		cmp.Comparer(42)
	})
}

func TestTransformerRewritesValues(t *testing.T) {
	tr := cmp.Transformer("Mod10", func(x int) int { return x % 10 })
	if !cmp.Equal(3, 13, tr) {
		t.Fatal("matched values must be transformed before comparing (3 == 13 mod 10)")
	}
	if cmp.Equal(3, 14, tr) {
		t.Fatal("transformed outputs must still be compared for real (3 != 14 mod 10)")
	}
}

func TestTransformerInvalidNamePanics(t *testing.T) {
	wantPanic(t, "invalid name", func() {
		cmp.Transformer("bad name!", func(x int) int { return x })
	})
}

func TestTransformerEmptyNameAllowed(t *testing.T) {
	anon := cmp.Transformer("", func(x int) int { return x % 10 })
	if !cmp.Equal(3, 13, anon) {
		t.Fatal("an empty transformer name must be accepted (placeholder substituted)")
	}
	if cmp.Equal(3, 14, anon) {
		t.Fatal("the anonymous transformer must still decide by transformed outputs")
	}
}

func TestTransformerRecursionGuardTerminates(t *testing.T) {
	inc := cmp.Transformer("Inc", func(x int) int { return x + 1 })
	if !cmp.Equal(3, 3, inc) {
		t.Fatal("a transformer whose output feeds its own input type must terminate and judge equal values equal")
	}
	if cmp.Equal(3, 4, inc) {
		t.Fatal("the recursion guard must not change the verdict for unequal values")
	}
}

func TestFilterPathScopesOption(t *testing.T) {
	igX := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "X" }, cmp.Ignore())
	if !cmp.Equal(Pt{1, 2}, Pt{9, 2}, igX) {
		t.Fatal("the ignore must apply on the admitted field")
	}
	if cmp.Equal(Pt{1, 2}, Pt{1, 9}, igX) {
		t.Fatal("the ignore must not apply outside the admitted path")
	}
}

func TestFilterValuesScopesOption(t *testing.T) {
	nearSmall := cmp.FilterValues(func(x, y float64) bool { return x < 10 && y < 10 },
		cmp.Comparer(func(x, y float64) bool {
			d := x - y
			return d < 0.5 && d > -0.5
		}))
	if !cmp.Equal(1.0, 1.2, nearSmall) {
		t.Fatal("the comparer must apply where the value predicate admits")
	}
	if cmp.Equal(100.0, 100.2, nearSmall) {
		t.Fatal("outside the value predicate the default == rule must decide")
	}
}

func TestFilterValuesSkipsOneSidedElements(t *testing.T) {
	fv := cmp.FilterValues(func(x, y int) bool { return true }, cmp.Ignore())
	if cmp.Equal([]int{1, 2}, []int{1, 2, 3}, fv) {
		t.Fatal("FilterValues must never apply when one side's value is invalid (missing element)")
	}
	if !cmp.Equal([]int{1, 2}, []int{1, 5}, fv) {
		t.Fatal("FilterValues must apply on aligned pairs, ignoring the difference")
	}
}

func TestFilterPathSeesOneSidedElements(t *testing.T) {
	igEdges := cmp.FilterPath(func(p cmp.Path) bool {
		si, ok := p.Last().(cmp.SliceIndex)
		if !ok {
			return false
		}
		kx, ky := si.SplitKeys()
		return kx == -1 || ky == -1
	}, cmp.Ignore())
	if !cmp.Equal([]int{1, 2}, []int{1, 2, 3}, igEdges) {
		t.Fatal("a path-filtered ignore must be able to consume one-sided additions")
	}
	type Doc struct {
		L []int
		N int
	}
	if !cmp.Equal(Doc{[]int{1}, 5}, Doc{[]int{1, 2}, 5}, igEdges) {
		t.Fatal("the slice-scoped filter must consume the addition inside the struct")
	}
	if cmp.Equal(Doc{[]int{1}, 5}, Doc{[]int{1}, 6}, igEdges) {
		t.Fatal("the slice-scoped filter must not consume differences at non-slice steps")
	}
}

func TestOptionsListActsAsOneOption(t *testing.T) {
	near := cmp.Comparer(func(x, y float64) bool {
		d := x - y
		return d < 0.01 && d > -0.01
	})
	opts := cmp.Options{near}
	if !cmp.Equal(1.000, 1.005, opts) {
		t.Fatal("passing an Options list must behave like passing its elements")
	}
	if cmp.Equal(1.0, 2.0, opts) {
		t.Fatal("the Options list must not change the options' verdicts")
	}
	if opts.String() == "" {
		t.Fatal("Options.String must describe the held options")
	}
}

func TestFilteredOptionsListAppliesToElements(t *testing.T) {
	scoped := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "X" },
		cmp.Options{cmp.Ignore()})
	if !cmp.Equal(Pt{1, 2}, Pt{9, 2}, scoped) {
		t.Fatal("filtering an Options list must filter every element (ignore applies on X)")
	}
	if cmp.Equal(Pt{1, 2}, Pt{1, 9}, scoped) {
		t.Fatal("the filtered list's elements must not apply outside the filter")
	}
}

func TestExporterAdmitsUnexportedFields(t *testing.T) {
	ex := cmp.Exporter(func(tt reflect.Type) bool { return tt == reflect.TypeOf(secret{}) })
	if !cmp.Equal(Vault{"a", secret{1}}, Vault{"a", secret{1}}, ex) {
		t.Fatal("admitted unexported fields must be compared normally (equal case)")
	}
	if cmp.Equal(Vault{"a", secret{1}}, Vault{"a", secret{2}}, ex) {
		t.Fatal("admitted unexported fields must be compared normally (unequal case)")
	}
}

func TestAllowUnexportedAdmitsListedTypes(t *testing.T) {
	if !cmp.Equal(Vault{"a", secret{1}}, Vault{"a", secret{1}}, cmp.AllowUnexported(secret{})) {
		t.Fatal("AllowUnexported must admit the listed type's unexported fields (equal case)")
	}
	if cmp.Equal(Vault{"a", secret{1}}, Vault{"a", secret{2}}, cmp.AllowUnexported(secret{})) {
		t.Fatal("AllowUnexported must compare admitted fields for real (unequal case)")
	}
}

func TestUnexportedFieldPanicsWithoutPermission(t *testing.T) {
	wantPanic(t, "cannot handle unexported field", func() {
		cmp.Equal(Vault{"a", secret{1}}, Vault{"a", secret{1}})
	})
}

func TestIgnoredUnexportedFieldDoesNotPanic(t *testing.T) {
	igS := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "S" }, cmp.Ignore())
	if !cmp.Equal(Vault{"a", secret{1}}, Vault{"a", secret{2}}, igS) {
		t.Fatal("an ignored unexported subtree must not panic and must count as equal")
	}
	if cmp.Equal(Vault{"a", secret{1}}, Vault{"b", secret{1}}, igS) {
		t.Fatal("fields outside the ignored subtree must still be compared")
	}
}
