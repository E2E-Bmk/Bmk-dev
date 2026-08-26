package atomic

import (
	"io"
	"reflect"
	"testing"

	"go.uber.org/dig"
)

type Conn struct{ Addr string }

type basicIn struct {
	dig.In
	W *Widget
}

type basicOut struct {
	dig.Out
	W *Widget `name:"made"`
}

func TestIsInAndIsOutClassifyStructs(t *testing.T) {
	if !dig.IsIn(basicIn{}) {
		t.Fatal("IsIn(basicIn) = false, want true")
	}
	if dig.IsIn(basicOut{}) {
		t.Fatal("IsIn(basicOut) = true, want false")
	}
	if !dig.IsOut(basicOut{}) {
		t.Fatal("IsOut(basicOut) = false, want true")
	}
	if dig.IsOut(basicIn{}) {
		t.Fatal("IsOut(basicIn) = true, want false")
	}
	if dig.IsIn(5) || dig.IsOut("x") {
		t.Fatal("non-structs must not qualify as parameter or result objects")
	}
	if !dig.IsIn(reflect.TypeOf(basicIn{})) {
		t.Fatal("IsIn must accept a reflect.Type as well")
	}
}

type InnerParams struct {
	dig.In
	W *Widget
}

type OuterParams struct {
	InnerParams
	S string
}

func TestNestedEmbeddingQualifiesAsParameterObject(t *testing.T) {
	if !dig.IsIn(OuterParams{}) {
		t.Fatal("a struct embedding an In-embedding struct must qualify as a parameter object")
	}
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 3} })
	c.Provide(func() string { return "s" })
	var v int
	var s string
	if err := c.Invoke(func(p OuterParams) { v, s = p.W.V, p.S }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if v != 3 || s != "s" {
		t.Fatalf("v=%d s=%q, want 3 and \"s\"", v, s)
	}
}

func TestParameterObjectFieldsBecomeDependencies(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 11} })
	c.Provide(func() *Gadget { return &Gadget{V: 22} })
	type params struct {
		dig.In
		W *Widget
		G *Gadget
	}
	var w, g int
	if err := c.Invoke(func(p params) { w, g = p.W.V, p.G.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if w != 11 || g != 22 {
		t.Fatalf("w=%d g=%d, want 11 and 22", w, g)
	}
}

func TestResultObjectFieldsBecomeValues(t *testing.T) {
	c := dig.New()
	type twoOut struct {
		dig.Out
		W *Widget
		G *Gadget
	}
	c.Provide(func() twoOut { return twoOut{W: &Widget{V: 5}, G: &Gadget{V: 6}} })
	var w, g int
	if err := c.Invoke(func(a *Widget, b *Gadget) { w, g = a.V, b.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if w != 5 || g != 6 {
		t.Fatalf("w=%d g=%d, want 5 and 6", w, g)
	}
}

func TestOutFieldNameTagRegistersNamedValue(t *testing.T) {
	c := dig.New()
	c.Provide(func() basicOut { return basicOut{W: &Widget{V: 8}} })
	type params struct {
		dig.In
		W *Widget `name:"made"`
	}
	var got int
	if err := c.Invoke(func(p params) { got = p.W.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 8 {
		t.Fatalf("got %d, want 8", got)
	}
	wantContains(t, c.Invoke(func(w *Widget) {}), "missing type:")
}

func TestOutFieldGroupTagSendsValue(t *testing.T) {
	c := dig.New()
	type groupOut struct {
		dig.Out
		N int `group:"nums"`
	}
	c.Provide(func() groupOut { return groupOut{N: 9} })
	type params struct {
		dig.In
		Nums []int `group:"nums"`
	}
	var got []int
	if err := c.Invoke(func(p params) { got = append([]int{}, p.Nums...) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if len(got) != 1 || got[0] != 9 {
		t.Fatalf("got %v, want [9]", got)
	}
}

func TestOutFieldFlattenTagSpreadsSlice(t *testing.T) {
	c := dig.New()
	type flatOut struct {
		dig.Out
		Ns []int `group:"nums,flatten"`
	}
	c.Provide(func() flatOut { return flatOut{Ns: []int{4, 5}} })
	type params struct {
		dig.In
		Nums []int `group:"nums"`
	}
	var got []int
	if err := c.Invoke(func(p params) { got = append([]int{}, p.Nums...) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("got %v, want two elements", got)
	}
}

func TestOutFieldFlattenRequiresSlice(t *testing.T) {
	c := dig.New()
	type badFlat struct {
		dig.Out
		N int `group:"nums,flatten"`
	}
	err := c.Provide(func() badFlat { return badFlat{N: 1} })
	wantContains(t, err, "flatten can be applied to slices only")
}

func TestUnexportedInFieldRejected(t *testing.T) {
	c := dig.New()
	type badIn struct {
		dig.In
		w *Widget
	}
	err := c.Invoke(func(p badIn) { _ = p.w })
	wantContains(t, err, "unexported fields not allowed in dig.In")
}

func TestUnexportedOutFieldRejected(t *testing.T) {
	c := dig.New()
	type badOut struct {
		dig.Out
		w *Widget
	}
	err := c.Provide(func() badOut { return badOut{} })
	wantContains(t, err, "unexported fields not allowed in dig.Out")
}

func TestPointerToParameterObjectRejected(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 1} })
	err := c.Invoke(func(p *basicIn) {})
	wantContains(t, err, "cannot depend on a pointer to a parameter object")
	// the by-value form of the same parameter object still resolves
	var got int
	if err := c.Invoke(func(p basicIn) { got = p.W.V }); err != nil {
		t.Fatalf("by-value parameter object: %v", err)
	}
	if got != 1 {
		t.Fatalf("got %d, want 1", got)
	}
}

func TestResultObjectAsParameterRejected(t *testing.T) {
	c := dig.New()
	err := c.Provide(func(o basicOut) int { return 0 })
	wantContains(t, err, "cannot depend on result objects")
}

func TestParameterObjectAsResultRejected(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() basicIn { return basicIn{} })
	wantContains(t, err, "cannot provide parameter objects")
}

func TestNameOptionRejectedForResultObjects(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() basicOut { return basicOut{} }, dig.Name("n"))
	wantContains(t, err, "cannot specify a name for result objects")
}

func TestGroupOptionRejectedForResultObjects(t *testing.T) {
	c := dig.New()
	err := c.Provide(func() basicOut { return basicOut{} }, dig.Group("g"))
	wantContains(t, err, "cannot specify a group for result objects")
}

func TestOptionalMissingYieldsZeroValue(t *testing.T) {
	c := dig.New()
	type params struct {
		dig.In
		W *Widget `optional:"true"`
		N int     `optional:"true"`
	}
	ran := false
	if err := c.Invoke(func(p params) {
		ran = true
		if p.W != nil {
			t.Errorf("missing optional pointer = %v, want nil", p.W)
		}
		if p.N != 0 {
			t.Errorf("missing optional int = %d, want 0", p.N)
		}
	}); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !ran {
		t.Fatal("invoked function did not run")
	}
}

func TestOptionalPresentUsesRegisteredValue(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 13} })
	type params struct {
		dig.In
		W *Widget `optional:"true"`
	}
	var got int
	if err := c.Invoke(func(p params) { got = p.W.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 13 {
		t.Fatalf("got %d, want 13", got)
	}
}

func TestOptionalDoesNotTolerateConstructorFailure(t *testing.T) {
	c := dig.New()
	c.Provide(func() (*Widget, error) { return nil, io.ErrClosedPipe })
	type params struct {
		dig.In
		W *Widget `optional:"true"`
	}
	err := c.Invoke(func(p params) {})
	wantContains(t, err, "received non-nil error from function")
}

func TestNamedTagWithOptionalMissing(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 1} }, dig.Name("present"))
	type params struct {
		dig.In
		P *Widget `name:"present"`
		A *Widget `name:"absent" optional:"true"`
	}
	var p, a *Widget
	if err := c.Invoke(func(x params) { p, a = x.P, x.A }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if p == nil || p.V != 1 {
		t.Fatalf("present named value not delivered: %v", p)
	}
	if a != nil {
		t.Fatalf("absent optional named value = %v, want nil", a)
	}
}

func TestGroupTagMustBeSlice(t *testing.T) {
	c := dig.New()
	c.Provide(func() int { return 1 }, dig.Group("nums"))
	type badIn struct {
		dig.In
		N int `group:"nums"`
	}
	err := c.Invoke(func(p badIn) {})
	wantContains(t, err, "value groups may be consumed as slices only")
}

func TestNameAndGroupTagsConflict(t *testing.T) {
	c := dig.New()
	type badIn struct {
		dig.In
		Ns []int `name:"n" group:"g"`
	}
	err := c.Invoke(func(p badIn) {})
	wantContains(t, err, "cannot use named values with value groups")
}

func TestOptionalGroupTagRejected(t *testing.T) {
	c := dig.New()
	type badIn struct {
		dig.In
		Ns []int `group:"g" optional:"true"`
	}
	err := c.Invoke(func(p badIn) {})
	wantContains(t, err, "value groups cannot be optional")
}

func TestEmptyGroupYieldsEmptySlice(t *testing.T) {
	c := dig.New()
	type params struct {
		dig.In
		Ns []int `group:"untouched"`
	}
	ran := false
	if err := c.Invoke(func(p params) {
		ran = true
		if len(p.Ns) != 0 {
			t.Errorf("empty group produced %v", p.Ns)
		}
	}); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !ran {
		t.Fatal("invoked function did not run")
	}
}

func TestPlainStructIsOrdinaryDependency(t *testing.T) {
	c := dig.New()
	c.Provide(func() Conn { return Conn{Addr: "db:5432"} })
	var got string
	if err := c.Invoke(func(x Conn) { got = x.Addr }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != "db:5432" {
		t.Fatalf("got %q, want %q", got, "db:5432")
	}
}
