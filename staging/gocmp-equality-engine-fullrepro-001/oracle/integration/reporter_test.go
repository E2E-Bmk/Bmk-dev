package integration

import (
	"fmt"
	"reflect"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

type Pt struct{ X, Y int }

type Nested struct{ P Pt }

type recorder struct {
	pushes, pops int
	depth        int
	negDepth     bool
	firstStep    cmp.PathStep
	steps        []cmp.PathStep
	path         cmp.Path
	leafPaths    []string
	leafStrings  []string
	results      []cmp.Result
}

func (r *recorder) PushStep(ps cmp.PathStep) {
	r.path = append(r.path, ps)
	if r.pushes == 0 {
		r.firstStep = ps
	}
	r.steps = append(r.steps, ps)
	r.pushes++
	r.depth++
}

func (r *recorder) PopStep() {
	r.path = r.path[:len(r.path)-1]
	r.pops++
	r.depth--
	if r.depth < 0 {
		r.negDepth = true
	}
}

func (r *recorder) Report(res cmp.Result) {
	r.results = append(r.results, res)
	r.leafPaths = append(r.leafPaths, r.path.GoString())
	r.leafStrings = append(r.leafStrings, r.path.String())
}

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

func TestReporterPushPopBalance(t *testing.T) {
	var r recorder
	cmp.Equal(Nested{Pt{1, 2}}, Nested{Pt{1, 3}}, cmp.Reporter(&r))
	if r.pushes == 0 {
		t.Fatal("the reporter must observe the traversal")
	}
	if r.pushes != r.pops {
		t.Fatalf("PushStep (%d) and PopStep (%d) must balance over a run", r.pushes, r.pops)
	}
	if r.negDepth {
		t.Fatal("a pop must never arrive before its matching push")
	}
}

func TestReporterFirstPushCarriesRoot(t *testing.T) {
	var r recorder
	cmp.Equal(Nested{Pt{1, 2}}, Nested{Pt{1, 3}}, cmp.Reporter(&r))
	if r.firstStep == nil {
		t.Fatal("the run must begin with a push")
	}
	if r.firstStep.Type() != reflect.TypeOf(Nested{}) {
		t.Fatalf("the first push must identify the root type, got %v", r.firstStep.Type())
	}
	vx, vy := r.firstStep.Values()
	if vx.Interface().(Nested).P.Y != 2 || vy.Interface().(Nested).P.Y != 3 {
		t.Fatal("the root step must carry the two compared values")
	}
}

func TestReporterReportsOncePerLeaf(t *testing.T) {
	var r recorder
	cmp.Equal(Pt{1, 2}, Pt{1, 3}, cmp.Reporter(&r))
	if len(r.results) != 2 {
		t.Fatalf("a two-field struct has two leaves; Report was called %d times", len(r.results))
	}
	joined := strings.Join(r.leafStrings, ",")
	if !strings.Contains(joined, "X") || !strings.Contains(joined, "Y") {
		t.Fatalf("each field leaf must be reported, got %v", r.leafStrings)
	}
}

func TestVerdictIsConjunctionOfLeafVerdicts(t *testing.T) {
	var r recorder
	verdict := cmp.Equal(Pt{1, 2}, Pt{1, 3}, cmp.Reporter(&r))
	if verdict {
		t.Fatal("differing structs must be judged unequal")
	}
	conj := true
	for _, res := range r.results {
		conj = conj && res.Equal()
	}
	if conj {
		t.Fatal("an unequal verdict requires at least one unequal leaf")
	}

	var r2 recorder
	verdict2 := cmp.Equal(Pt{1, 2}, Pt{1, 2}, cmp.Reporter(&r2))
	if !verdict2 {
		t.Fatal("identical structs must be judged equal")
	}
	for _, res := range r2.results {
		if !res.Equal() {
			t.Fatal("an equal verdict requires every leaf to be equal")
		}
	}
}

func TestReporterObservesMapAndSliceSteps(t *testing.T) {
	x := map[string][]int{"a": {1, 2}}
	y := map[string][]int{"a": {1, 3}}
	var r recorder
	if cmp.Equal(x, y, cmp.Reporter(&r)) {
		t.Fatal("the nested difference must make the maps unequal")
	}
	var sawMap, sawSlice bool
	for _, s := range r.steps {
		if mi, ok := s.(cmp.MapIndex); ok {
			if k, _ := mi.Key().Interface().(string); k == "a" {
				sawMap = true
			}
		}
		if si, ok := s.(cmp.SliceIndex); ok && si.Key() == 1 {
			sawSlice = true
		}
	}
	if !sawMap {
		t.Fatal("the traversal must present a MapIndex step for the entry")
	}
	if !sawSlice {
		t.Fatal("the traversal must present a SliceIndex step for the differing element")
	}
}

func TestReporterPathRenderingsConsistent(t *testing.T) {
	var r recorder
	cmp.Equal(Nested{Pt{1, 2}}, Nested{Pt{1, 3}}, cmp.Reporter(&r))
	var found bool
	for i, gs := range r.leafPaths {
		if r.leafStrings[i] == "P.Y" {
			found = true
			if !strings.HasPrefix(gs, "{") || !strings.HasSuffix(gs, "}.P.Y") {
				t.Fatalf("GoString must brace the root and render the chain, got %q", gs)
			}
		}
	}
	if !found {
		t.Fatalf("the differing leaf's simplified path must be P.Y, got %v", r.leafStrings)
	}
}

func TestTransformStepObservedInTraversal(t *testing.T) {
	tr := cmp.Transformer("Mod10", func(x int) int { return x % 10 })
	var r recorder
	if !cmp.Equal(3, 13, tr, cmp.Reporter(&r)) {
		t.Fatal("3 and 13 must be equal mod 10")
	}
	var saw bool
	for _, s := range r.steps {
		if ts, ok := s.(cmp.Transform); ok {
			if ts.Name() != "Mod10" {
				t.Fatalf("Transform.Name = %q, want Mod10", ts.Name())
			}
			if ts.Option() != tr {
				t.Fatal("Transform.Option must identify the originating option under ==")
			}
			saw = true
		}
	}
	if !saw {
		t.Fatal("the transformer application must appear as a Transform step")
	}
}

func TestPointerAndInterfaceStepsObserved(t *testing.T) {
	type Box struct {
		P *int
		I interface{}
	}
	five, six := 5, 6
	var r recorder
	if cmp.Equal(Box{&five, 7}, Box{&six, 8}, cmp.Reporter(&r)) {
		t.Fatal("the boxes differ in both fields")
	}
	var sawIndirect, sawAssert bool
	for _, s := range r.steps {
		switch s.(type) {
		case cmp.Indirect:
			sawIndirect = true
		case cmp.TypeAssertion:
			sawAssert = true
		}
	}
	if !sawIndirect {
		t.Fatal("pointer descent must present an Indirect step")
	}
	if !sawAssert {
		t.Fatal("interface descent must present a TypeAssertion step")
	}
}

func TestEmbeddedStructEnteredAsOwnStep(t *testing.T) {
	type Base struct{ W int }
	type Wrapper struct {
		Base
		Z int
	}
	var r recorder
	if cmp.Equal(Wrapper{Base{1}, 2}, Wrapper{Base{5}, 2}, cmp.Reporter(&r)) {
		t.Fatal("the embedded field difference must make the wrappers unequal")
	}
	var sawEmbedded bool
	for _, ls := range r.leafStrings {
		if ls == "Base.W" {
			sawEmbedded = true
		}
		if ls == "W" {
			t.Fatal("an embedded struct's field must never appear as a direct field of the outer struct")
		}
	}
	if !sawEmbedded {
		t.Fatalf("the embedded struct must be entered as its own field step, got %v", r.leafStrings)
	}
}
