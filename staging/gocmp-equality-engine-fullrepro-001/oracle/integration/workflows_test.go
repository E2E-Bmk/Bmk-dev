package integration

import (
	"reflect"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

type Reading struct {
	Sensor string
	Value  float64
}

type secret struct{ v int }

type Vault struct {
	Label string
	S     secret
}

func TestApproximateComparisonWorkflow(t *testing.T) {
	near := nearComparer(0.01)
	a := Reading{Sensor: "t1", Value: 1.000}
	b := Reading{Sensor: "t1", Value: 1.005}
	if cmp.Equal(a, b) {
		t.Fatal("under default == the readings must be unequal")
	}
	if cmp.Diff(a, b) == "" {
		t.Fatal("the default-rule report must be non-empty")
	}
	if !cmp.Equal(a, b, near) {
		t.Fatal("under the tolerance comparer the readings must be equal")
	}
	if d := cmp.Diff(a, b, near); d != "" {
		t.Fatalf("the tolerant report must be empty, got %q", d)
	}
}

type pathCollector struct {
	path  cmp.Path
	diffs []string
}

func (c *pathCollector) PushStep(ps cmp.PathStep) { c.path = append(c.path, ps) }
func (c *pathCollector) PopStep()                 { c.path = c.path[:len(c.path)-1] }
func (c *pathCollector) Report(r cmp.Result) {
	if !r.Equal() {
		c.diffs = append(c.diffs, c.path.GoString())
	}
}

func TestPathCollectorWorkflow(t *testing.T) {
	var c pathCollector
	if cmp.Equal(Nested{Pt{1, 2}}, Nested{Pt{5, 2}}, cmp.Reporter(&c)) {
		t.Fatal("the nested difference must make the values unequal")
	}
	if len(c.diffs) != 1 {
		t.Fatalf("exactly one leaf differs, collected %v", c.diffs)
	}
	if !strings.HasSuffix(c.diffs[0], "}.P.X") || !strings.HasPrefix(c.diffs[0], "{") {
		t.Fatalf("the collected location must name the differing leaf, got %q", c.diffs[0])
	}
}

type Mixed struct {
	F float64
	S string
	T int
}

func TestMultiOptionComposition(t *testing.T) {
	near := nearComparer(0.01)
	igS := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "S" }, cmp.Ignore())
	mod := cmp.Transformer("Mod10", func(x int) int { return x % 10 })
	x := Mixed{1.000, "a", 3}
	y := Mixed{1.004, "b", 13}
	if !cmp.Equal(x, y, near, igS, mod) {
		t.Fatal("with all three options every field must reconcile")
	}
	if d := cmp.Diff(x, y, near, igS, mod); d != "" {
		t.Fatalf("the fully-optioned report must be empty, got %q", d)
	}
	if cmp.Equal(x, y, igS, mod) {
		t.Fatal("dropping the comparer must expose the float difference")
	}
	if cmp.Equal(x, y, near, mod) {
		t.Fatal("dropping the ignore must expose the string difference")
	}
	if cmp.Equal(x, y, near, igS) {
		t.Fatal("dropping the transformer must expose the integer difference")
	}
}

func TestOptionsListNestingAndFiltering(t *testing.T) {
	near := nearComparer(0.01)
	igS := cmp.FilterPath(func(p cmp.Path) bool { return p.String() == "S" }, cmp.Ignore())
	mod := cmp.Transformer("Mod10", func(x int) int { return x % 10 })
	bundle := cmp.Options{near, cmp.Options{igS, mod}}
	x := Mixed{1.000, "a", 3}
	y := Mixed{1.004, "b", 13}
	if !cmp.Equal(x, y, bundle) {
		t.Fatal("a nested Options list must behave like its flattened elements")
	}
	if cmp.Equal(x, y) {
		t.Fatal("without the bundle the values must be unequal")
	}
	if d := cmp.Diff(x, y, bundle); d != "" {
		t.Fatalf("the bundled report must agree with the verdict, got %q", d)
	}
}

func TestExporterScopedWorkflow(t *testing.T) {
	x := Vault{"a", secret{1}}
	yEq := Vault{"a", secret{1}}
	yNe := Vault{"a", secret{2}}
	wantPanic(t, "cannot handle unexported field", func() {
		cmp.Equal(x, yEq)
	})
	ex := cmp.Exporter(func(tt reflect.Type) bool { return tt == reflect.TypeOf(secret{}) })
	if !cmp.Equal(x, yEq, ex) {
		t.Fatal("the exporter must admit the unexported field (equal case)")
	}
	if cmp.Equal(x, yNe, ex) {
		t.Fatal("the exporter must admit the unexported field (unequal case)")
	}
	if !cmp.Equal(x, yEq, cmp.AllowUnexported(secret{})) {
		t.Fatal("AllowUnexported must admit the listed type (equal case)")
	}
	if cmp.Equal(x, yNe, cmp.AllowUnexported(secret{})) {
		t.Fatal("AllowUnexported must admit the listed type (unequal case)")
	}
	if (cmp.Diff(x, yNe, ex) == "") != cmp.Equal(x, yNe, ex) {
		t.Fatal("Diff emptiness must track the exporter-scoped verdict")
	}
}

func TestIgnoreAdditionsScopedToSlices(t *testing.T) {
	type Server struct {
		Routes []string
		Port   int
	}
	igEdges := cmp.FilterPath(func(p cmp.Path) bool {
		si, ok := p.Last().(cmp.SliceIndex)
		if !ok {
			return false
		}
		kx, ky := si.SplitKeys()
		return kx == -1 || ky == -1
	}, cmp.Ignore())
	x := Server{Routes: []string{"/health"}, Port: 80}
	yExtra := Server{Routes: []string{"/health", "/metrics"}, Port: 80}
	yPort := Server{Routes: []string{"/health"}, Port: 81}
	if !cmp.Equal(x, yExtra, igEdges) {
		t.Fatal("one-sided route additions must be consumable by the path-filtered ignore")
	}
	if d := cmp.Diff(x, yExtra, igEdges); d != "" {
		t.Fatalf("the addition-ignoring report must be empty, got %q", d)
	}
	if cmp.Equal(x, yPort, igEdges) {
		t.Fatal("differences at non-slice steps must still be detected")
	}
	if cmp.Diff(x, yPort, igEdges) == "" {
		t.Fatal("the port-difference report must be non-empty")
	}
}

func TestMapEntryOneSidedIgnore(t *testing.T) {
	igOneSided := cmp.FilterPath(func(p cmp.Path) bool {
		mi, ok := p.Last().(cmp.MapIndex)
		if !ok {
			return false
		}
		vx, vy := mi.Values()
		return !vx.IsValid() || !vy.IsValid()
	}, cmp.Ignore())
	base := map[string]int{"a": 1}
	extra := map[string]int{"a": 1, "b": 2}
	changed := map[string]int{"a": 9, "b": 2}
	if !cmp.Equal(base, extra, igOneSided) {
		t.Fatal("entries present on one side only must be consumable by the filter")
	}
	if d := cmp.Diff(base, extra, igOneSided); d != "" {
		t.Fatalf("the entry-ignoring report must be empty, got %q", d)
	}
	if cmp.Equal(base, changed, igOneSided) {
		t.Fatal("a changed value present on both sides must still be detected")
	}
}

type Record struct {
	Name string
	E    EqMod
}

func TestEqualMethodWithinLargerStructure(t *testing.T) {
	var r recorder
	if !cmp.Equal(Record{"a", EqMod{3}}, Record{"a", EqMod{13}}, cmp.Reporter(&r)) {
		t.Fatal("the embedded Equal method must reconcile 3 and 13 mod 10")
	}
	var sawMethod bool
	for i, res := range r.results {
		if strings.Contains(r.leafStrings[i], "E") && res.ByMethod() {
			sawMethod = true
		}
	}
	if !sawMethod {
		t.Fatal("the method-decided leaf inside the tree must claim ByMethod")
	}
	if d := cmp.Diff(Record{"a", EqMod{3}}, Record{"a", EqMod{13}}); d != "" {
		t.Fatalf("the report must agree with the method verdict, got %q", d)
	}
	if cmp.Equal(Record{"a", EqMod{3}}, Record{"b", EqMod{13}}) {
		t.Fatal("differences outside the method's leaf must still be detected")
	}
}

func TestTransformerOnNestedField(t *testing.T) {
	lower := cmp.Transformer("Lower", strings.ToLower)
	x := []string{"Hello", "World"}
	y := []string{"HELLO", "world"}
	if !cmp.Equal(x, y, lower) {
		t.Fatal("case-normalized elements must compare equal")
	}
	if d := cmp.Diff(x, y, lower); d != "" {
		t.Fatalf("the normalized report must be empty, got %q", d)
	}
	if cmp.Equal(x, y) {
		t.Fatal("without the transformer the elements must be unequal")
	}
	z := []string{"HELLO", "there"}
	if cmp.Equal(x, z, lower) {
		t.Fatal("truly different elements must stay unequal after normalization")
	}
}

func TestReporterAgreesWithDiffOnUnequalLeaves(t *testing.T) {
	countUnequal := func(x, y interface{}) int {
		var r recorder
		cmp.Equal(x, y, cmp.Reporter(&r))
		n := 0
		for _, res := range r.results {
			if !res.Equal() {
				n++
			}
		}
		return n
	}
	if n := countUnequal(Pt{1, 2}, Pt{9, 8}); n != 2 {
		t.Fatalf("both leaves differ, counted %d", n)
	}
	if cmp.Diff(Pt{1, 2}, Pt{9, 8}) == "" {
		t.Fatal("unequal leaves require a non-empty report")
	}
	if n := countUnequal(Pt{1, 2}, Pt{1, 2}); n != 0 {
		t.Fatalf("no leaf differs, counted %d", n)
	}
	if cmp.Diff(Pt{1, 2}, Pt{1, 2}) != "" {
		t.Fatal("zero unequal leaves require an empty report")
	}
}

func TestMismatchedTypesDeepWorkflow(t *testing.T) {
	type Box struct{ I interface{} }
	var r recorder
	if cmp.Equal(Box{5}, Box{"5"}, cmp.Reporter(&r)) {
		t.Fatal("interfaces holding different concrete types must be unequal")
	}
	if r.pushes != r.pops {
		t.Fatal("the traversal must stay balanced across a type mismatch")
	}
	if cmp.Diff(Box{5}, Box{"5"}) == "" {
		t.Fatal("the mismatch report must be non-empty")
	}
	if !cmp.Equal(Box{5}, Box{5}) {
		t.Fatal("matching concrete types and values must be equal")
	}
}
