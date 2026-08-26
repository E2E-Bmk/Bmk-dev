package atomic

import (
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

// capturePath records the first path admitted by match while comparing x and y.
// The filtered Ignore never applies (the predicate returns false after capture),
// so the capture does not disturb the comparison.
func capturePath(t *testing.T, x, y interface{}, opts []cmp.Option, match func(cmp.Path) bool) cmp.Path {
	t.Helper()
	var got cmp.Path
	all := append([]cmp.Option{cmp.FilterPath(func(p cmp.Path) bool {
		if got == nil && match(p) {
			got = append(cmp.Path(nil), p...)
		}
		return false
	}, cmp.Ignore())}, opts...)
	cmp.Equal(x, y, all...)
	if got == nil {
		t.Fatal("expected path was never observed during the traversal")
	}
	return got
}

func lastFieldNamed(name string) func(cmp.Path) bool {
	return func(p cmp.Path) bool {
		sf, ok := p.Last().(cmp.StructField)
		return ok && sf.Name() == name
	}
}

func TestPathStringSimplified(t *testing.T) {
	p := capturePath(t, Nested{Pt{1, 2}}, Nested{Pt{1, 3}}, nil, lastFieldNamed("Y"))
	if got := p.String(); got != "P.Y" {
		t.Fatalf("Path.String must keep only dotted struct-field accesses, got %q", got)
	}
}

func TestPathGoStringFull(t *testing.T) {
	p := capturePath(t, Nested{Pt{1, 2}}, Nested{Pt{1, 3}}, nil, lastFieldNamed("Y"))
	gs := p.GoString()
	if !strings.HasPrefix(gs, "{") || !strings.Contains(gs, "Nested") {
		t.Fatalf("GoString must brace the root type, got %q", gs)
	}
	if !strings.HasSuffix(gs, "}.P.Y") {
		t.Fatalf("GoString must render the full field chain, got %q", gs)
	}
}

func TestPathIndexAndLast(t *testing.T) {
	p := capturePath(t, Nested{Pt{1, 2}}, Nested{Pt{1, 3}}, nil, lastFieldNamed("Y"))
	if p.Index(-1) != p.Last() {
		t.Fatal("Index(-1) must return the same step as Last")
	}
	if p.Index(len(p)-1) != p.Last() {
		t.Fatal("Index(len-1) must return the same step as Last")
	}
	oor := p.Index(99)
	if oor == nil {
		t.Fatal("an out-of-range index must return a non-nil step")
	}
	if oor.Type() != nil {
		t.Fatal("the out-of-range step must report a nil Type")
	}
}

func TestStructFieldAccessors(t *testing.T) {
	p := capturePath(t, Pt{1, 2}, Pt{1, 3}, nil, lastFieldNamed("Y"))
	sf := p.Last().(cmp.StructField)
	if sf.Name() != "Y" {
		t.Fatalf("StructField.Name = %q, want Y", sf.Name())
	}
	if sf.Index() != 1 {
		t.Fatalf("StructField.Index = %d, want 1", sf.Index())
	}
}

func TestSliceIndexKeyAndSplitKeys(t *testing.T) {
	p := capturePath(t, []int{1, 2}, []int{1, 9}, nil, func(p cmp.Path) bool {
		si, ok := p.Last().(cmp.SliceIndex)
		return ok && si.Key() == 1
	})
	si := p.Last().(cmp.SliceIndex)
	kx, ky := si.SplitKeys()
	if kx != 1 || ky != 1 {
		t.Fatalf("aligned element: SplitKeys = (%d,%d), want (1,1)", kx, ky)
	}

	q := capturePath(t, []int{1, 2}, []int{1, 2, 3}, nil, func(p cmp.Path) bool {
		si, ok := p.Last().(cmp.SliceIndex)
		if !ok {
			return false
		}
		a, b := si.SplitKeys()
		return a == -1 && b >= 0
	})
	sq := q.Last().(cmp.SliceIndex)
	if sq.Key() != -1 {
		t.Fatalf("diverged element: Key = %d, want -1", sq.Key())
	}
}

func TestMapIndexKeyAccessor(t *testing.T) {
	p := capturePath(t, map[string]int{"k": 1}, map[string]int{"k": 2}, nil, func(p cmp.Path) bool {
		_, ok := p.Last().(cmp.MapIndex)
		return ok
	})
	mi := p.Last().(cmp.MapIndex)
	if got, ok := mi.Key().Interface().(string); !ok || got != "k" {
		t.Fatalf("MapIndex.Key = %v, want \"k\"", mi.Key())
	}
}

func TestIndirectStepObserved(t *testing.T) {
	x, y := 5, 6
	p := capturePath(t, &x, &y, nil, func(p cmp.Path) bool {
		_, ok := p.Last().(cmp.Indirect)
		return ok
	})
	if _, ok := p.Last().(cmp.Indirect); !ok {
		t.Fatal("descending through a pointer must present an Indirect step")
	}
	if cmp.Equal(&x, &y) {
		t.Fatal("the dereferenced pointees must still decide the verdict")
	}
}

func TestTypeAssertionStepObserved(t *testing.T) {
	p := capturePath(t, IfaceHolder{5}, IfaceHolder{6}, nil, func(p cmp.Path) bool {
		_, ok := p.Last().(cmp.TypeAssertion)
		return ok
	})
	ta := p.Last().(cmp.TypeAssertion)
	if ta.Type() == nil || ta.Type().Kind().String() != "int" {
		t.Fatalf("the TypeAssertion step must report the concrete type, got %v", ta.Type())
	}
}

func TestTransformStepAccessors(t *testing.T) {
	tr := cmp.Transformer("Mod10", func(x int) int { return x % 10 })
	p := capturePath(t, 3, 14, []cmp.Option{tr}, func(p cmp.Path) bool {
		_, ok := p.Last().(cmp.Transform)
		return ok
	})
	ts := p.Last().(cmp.Transform)
	if ts.Name() != "Mod10" {
		t.Fatalf("Transform.Name = %q, want Mod10", ts.Name())
	}
	if ts.Option() != tr {
		t.Fatal("Transform.Option must return the originally constructed option")
	}
	if !ts.Func().IsValid() {
		t.Fatal("Transform.Func must return the transformer function")
	}
}
