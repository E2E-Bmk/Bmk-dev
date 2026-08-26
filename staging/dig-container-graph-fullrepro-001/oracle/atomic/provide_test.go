package atomic

import (
	"io"
	"sort"
	"strings"
	"testing"

	"go.uber.org/dig"
)

type Widget struct{ V int }
type Gadget struct{ V int }

func wantContains(t *testing.T, err error, frag string) {
	t.Helper()
	if err == nil {
		t.Fatalf("expected error containing %q, got nil", frag)
	}
	if !strings.Contains(err.Error(), frag) {
		t.Fatalf("error %q does not contain %q", err.Error(), frag)
	}
}

func TestProvideRejectsNonFunction(t *testing.T) {
	c := dig.New()
	err := c.Provide(42)
	wantContains(t, err, "must provide constructor function")
}

func TestProvideRequiresNonErrorResult(t *testing.T) {
	c := dig.New()
	wantContains(t, c.Provide(func() {}), "must provide at least one non-error type")
	wantContains(t, c.Provide(func() error { return nil }), "must provide at least one non-error type")
}

func TestProvideDoesNotCallConstructor(t *testing.T) {
	c := dig.New()
	calls := 0
	if err := c.Provide(func() *Widget { calls++; return &Widget{V: 7} }); err != nil {
		t.Fatalf("provide: %v", err)
	}
	if calls != 0 {
		t.Fatalf("constructor ran %d times at Provide time", calls)
	}
	var got int
	if err := c.Invoke(func(w *Widget) { got = w.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if calls != 1 || got != 7 {
		t.Fatalf("calls=%d got=%d, want 1 and 7", calls, got)
	}
}

func TestConstructorRunsAtMostOnce(t *testing.T) {
	c := dig.New()
	calls := 0
	c.Provide(func() *Widget { calls++; return &Widget{V: calls} })
	var first, second *Widget
	if err := c.Invoke(func(w *Widget) { first = w }); err != nil {
		t.Fatalf("invoke 1: %v", err)
	}
	if err := c.Invoke(func(w *Widget) { second = w }); err != nil {
		t.Fatalf("invoke 2: %v", err)
	}
	if calls != 1 {
		t.Fatalf("constructor ran %d times, want 1", calls)
	}
	if first == nil || first != second {
		t.Fatalf("invocations observed different instances: %p vs %p", first, second)
	}
}

func TestFailedConstructorIsNotMemoized(t *testing.T) {
	c := dig.New()
	calls := 0
	c.Provide(func() (*Widget, error) { calls++; return nil, io.ErrUnexpectedEOF })
	if err := c.Invoke(func(w *Widget) {}); err == nil {
		t.Fatal("first invoke should fail")
	}
	if err := c.Invoke(func(w *Widget) {}); err == nil {
		t.Fatal("second invoke should fail")
	}
	if calls != 2 {
		t.Fatalf("failing constructor ran %d times across two demands, want 2 (no memoization of failure)", calls)
	}
}

func TestDuplicateProvideRejectedAndRolledBack(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() *Widget { return &Widget{V: 1} }); err != nil {
		t.Fatalf("first provide: %v", err)
	}
	wantContains(t, c.Provide(func() *Widget { return &Widget{V: 2} }), "already provided")
	var got int
	if err := c.Invoke(func(w *Widget) { got = w.V }); err != nil {
		t.Fatalf("invoke after rejected duplicate: %v", err)
	}
	if got != 1 {
		t.Fatalf("got %d, want the original registration's value 1", got)
	}
}

func TestNamedProvidesDoNotConflict(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() *Widget { return &Widget{V: 1} }, dig.Name("ro")); err != nil {
		t.Fatalf("provide ro: %v", err)
	}
	if err := c.Provide(func() *Widget { return &Widget{V: 2} }, dig.Name("rw")); err != nil {
		t.Fatalf("provide rw: %v", err)
	}
	type params struct {
		dig.In
		RO *Widget `name:"ro"`
		RW *Widget `name:"rw"`
	}
	var ro, rw int
	if err := c.Invoke(func(p params) { ro, rw = p.RO.V, p.RW.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if ro != 1 || rw != 2 {
		t.Fatalf("ro=%d rw=%d, want 1 and 2", ro, rw)
	}
}

func TestDuplicateNamedProvideRejected(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() *Widget { return &Widget{V: 1} }, dig.Name("ro")); err != nil {
		t.Fatalf("first provide: %v", err)
	}
	err := c.Provide(func() *Widget { return &Widget{V: 3} }, dig.Name("ro"))
	wantContains(t, err, "already provided")
	type params struct {
		dig.In
		RO *Widget `name:"ro"`
	}
	var got int
	if err := c.Invoke(func(p params) { got = p.RO.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 1 {
		t.Fatalf("got %d, want original value 1", got)
	}
}

func TestNamedAndUnnamedKeysAreDistinct(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() *Widget { return &Widget{V: 10} }); err != nil {
		t.Fatalf("unnamed: %v", err)
	}
	if err := c.Provide(func() *Widget { return &Widget{V: 20} }, dig.Name("x")); err != nil {
		t.Fatalf("named: %v", err)
	}
	type params struct {
		dig.In
		Plain *Widget
		X     *Widget `name:"x"`
	}
	var plain, x int
	if err := c.Invoke(func(p params) { plain, x = p.Plain.V, p.X.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if plain != 10 || x != 20 {
		t.Fatalf("plain=%d x=%d, want 10 and 20", plain, x)
	}
}

func TestVariadicConstructorArgsIgnored(t *testing.T) {
	c := dig.New()
	c.Provide(func(extras ...string) *Widget { return &Widget{V: len(extras)} })
	var got int
	if err := c.Invoke(func(w *Widget) { got = w.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 0 {
		t.Fatalf("constructor received %d variadic args, want 0", got)
	}
}

func TestMultipleResultsAllRegistered(t *testing.T) {
	c := dig.New()
	c.Provide(func() (*Widget, *Gadget) { return &Widget{V: 1}, &Gadget{V: 2} })
	var w, g int
	if err := c.Invoke(func(a *Widget, b *Gadget) { w, g = a.V, b.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if w != 1 || g != 2 {
		t.Fatalf("w=%d g=%d, want 1 and 2", w, g)
	}
}

func TestTrailingNilErrorMeansSuccess(t *testing.T) {
	c := dig.New()
	c.Provide(func() (*Widget, error) { return &Widget{V: 4}, nil })
	var got int
	if err := c.Invoke(func(w *Widget) { got = w.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 4 {
		t.Fatalf("got %d, want 4", got)
	}
}

func TestProvideCycleRejectedByDefault(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func(g *Gadget) *Widget { return &Widget{} }); err != nil {
		t.Fatalf("first provide: %v", err)
	}
	err := c.Provide(func(w *Widget) *Gadget { return &Gadget{} })
	wantContains(t, err, "this function introduces a cycle")
	if !dig.IsCycleDetected(err) {
		t.Fatal("IsCycleDetected should report true for a provide-time cycle rejection")
	}
	// rejected registration must leave the container unchanged
	if err := c.Provide(func() int { return 3 }); err != nil {
		t.Fatalf("unrelated provide after rejection: %v", err)
	}
	var got int
	if err := c.Invoke(func(x int) { got = x }); err != nil {
		t.Fatalf("unrelated invoke after rejection: %v", err)
	}
	if got != 3 {
		t.Fatalf("got %d, want 3", got)
	}
	wantContains(t, c.Invoke(func(g *Gadget) {}), "missing type:")
}

func TestIsCycleDetectedFalseForOtherErrors(t *testing.T) {
	c := dig.New()
	err := c.Invoke(func(w *Widget) {})
	if err == nil {
		t.Fatal("expected missing-type error")
	}
	if dig.IsCycleDetected(err) {
		t.Fatal("IsCycleDetected must be false for a missing-type error")
	}
	if dig.IsCycleDetected(c.Provide(9)) {
		t.Fatal("IsCycleDetected must be false for a validation error")
	}
}

func TestGroupOptionCollectsValues(t *testing.T) {
	c := dig.New()
	c.Provide(func() int { return 3 }, dig.Group("nums"))
	c.Provide(func() int { return 1 }, dig.Group("nums"))
	c.Provide(func() int { return 2 }, dig.Group("nums"))
	type params struct {
		dig.In
		Nums []int `group:"nums"`
	}
	var got []int
	if err := c.Invoke(func(p params) { got = append([]int{}, p.Nums...) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	sort.Ints(got)
	if len(got) != 3 || got[0] != 1 || got[1] != 2 || got[2] != 3 {
		t.Fatalf("got %v, want multiset {1,2,3}", got)
	}
}

func TestFlattenOptionSpreadsSliceElements(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() []int { return []int{7, 8} }, dig.Group("nums,flatten")); err != nil {
		t.Fatalf("provide: %v", err)
	}
	type params struct {
		dig.In
		Nums []int `group:"nums"`
	}
	var got []int
	if err := c.Invoke(func(p params) { got = append([]int{}, p.Nums...) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	sort.Ints(got)
	if len(got) != 2 || got[0] != 7 || got[1] != 8 {
		t.Fatalf("got %v, want elements 7 and 8 individually", got)
	}
}

func TestFlattenRequiresSlice(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() int { return 1 }, dig.Group("nums,flatten"))
	wantContains(t, err, "flatten can be applied to slices only")
}

func TestNameAndGroupOptionsConflict(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() *Widget { return &Widget{} }, dig.Name("n"), dig.Group("g"))
	wantContains(t, err, "cannot use named values with value groups")
}

func TestAsRegistersInterfaceOnly(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() *strings.Reader { return strings.NewReader("hi") }, dig.As(new(io.Reader))); err != nil {
		t.Fatalf("provide: %v", err)
	}
	var read string
	err := c.Invoke(func(r io.Reader) {
		b, _ := io.ReadAll(r)
		read = string(b)
	})
	if err != nil {
		t.Fatalf("invoke via interface: %v", err)
	}
	if read != "hi" {
		t.Fatalf("read %q, want %q", read, "hi")
	}
	wantContains(t, c.Invoke(func(r *strings.Reader) {}), "missing type:")
}

func TestAsRejectsNonInterfacePointer(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() *Widget { return &Widget{} }, dig.As(42))
	wantContains(t, err, "argument must be a pointer to an interface")
}

func TestAsRejectsUnimplementedInterface(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() *Widget { return &Widget{} }, dig.As(new(io.Reader)))
	wantContains(t, err, "does not implement")
}

func TestAsWithNameRegistersNamedInterface(t *testing.T) {
	c := dig.New()
	if err := c.Provide(func() *strings.Reader { return strings.NewReader("temp") }, dig.As(new(io.Reader)), dig.Name("temp")); err != nil {
		t.Fatalf("provide: %v", err)
	}
	type params struct {
		dig.In
		R io.Reader `name:"temp"`
	}
	var read string
	if err := c.Invoke(func(p params) {
		b, _ := io.ReadAll(p.R)
		read = string(b)
	}); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if read != "temp" {
		t.Fatalf("read %q, want %q", read, "temp")
	}
}
