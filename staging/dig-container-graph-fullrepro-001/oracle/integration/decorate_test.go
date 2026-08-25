package integration

import (
	"testing"

	"go.uber.org/dig"
)

func TestDecoratorReplacesValueInScope(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Logger { return &Logger{Tag: "base"} })
	if err := c.Decorate(func(l *Logger) *Logger { return &Logger{Tag: l.Tag + "+dec"} }); err != nil {
		t.Fatalf("decorate: %v", err)
	}
	var tag string
	if err := c.Invoke(func(l *Logger) { tag = l.Tag }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if tag != "base+dec" {
		t.Fatalf("tag=%q, want %q", tag, "base+dec")
	}
}

func TestChildDecorationInvisibleToParent(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Logger { return &Logger{Tag: "base"} })
	child := c.Scope("child")
	child.Decorate(func(l *Logger) *Logger { return &Logger{Tag: l.Tag + "+child"} })
	grand := child.Scope("grand")
	for i := 0; i < 2; i++ {
		var fromChild, fromRoot, fromGrand string
		if err := child.Invoke(func(l *Logger) { fromChild = l.Tag }); err != nil {
			t.Fatalf("child invoke: %v", err)
		}
		if err := c.Invoke(func(l *Logger) { fromRoot = l.Tag }); err != nil {
			t.Fatalf("root invoke: %v", err)
		}
		if err := grand.Invoke(func(l *Logger) { fromGrand = l.Tag }); err != nil {
			t.Fatalf("grandchild invoke: %v", err)
		}
		if fromChild != "base+child" || fromGrand != "base+child" {
			t.Fatalf("round %d: child=%q grand=%q, want decorated", i, fromChild, fromGrand)
		}
		if fromRoot != "base" {
			t.Fatalf("round %d: root=%q, want undecorated %q", i, fromRoot, "base")
		}
	}
}

func TestDecoratorReceivesUndecoratedValue(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 1} })
	c.Decorate(func(w *Widget) *Widget { return &Widget{V: w.V + 10} })
	var got int
	if err := c.Invoke(func(w *Widget) { got = w.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 11 {
		t.Fatalf("got %d, want 11 (decorator applied once to the base value)", got)
	}
}

func TestDecoratorSeesSameBaseInstanceAsAncestor(t *testing.T) {
	c := dig.New()
	var made *Widget
	c.Provide(func() *Widget { made = &Widget{V: 5}; return made })
	child := c.Scope("child")
	var decorated *Widget
	child.Decorate(func(w *Widget) *Widget { decorated = w; return &Widget{V: w.V + 100} })
	var fromChild, fromRoot *Widget
	if err := child.Invoke(func(w *Widget) { fromChild = w }); err != nil {
		t.Fatalf("child invoke: %v", err)
	}
	if err := c.Invoke(func(w *Widget) { fromRoot = w }); err != nil {
		t.Fatalf("root invoke: %v", err)
	}
	if fromChild == nil || fromChild.V != 105 {
		t.Fatalf("child got %v, want V=105", fromChild)
	}
	if made == nil || fromRoot != made || decorated != made {
		t.Fatal("decorator and ancestor must both work from the one memoized base instance")
	}
}

func TestDecoratorRunsAtMostOncePerScope(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Logger { return &Logger{Tag: "x"} })
	runs := 0
	c.Decorate(func(l *Logger) *Logger { runs++; return l })
	if err := c.Invoke(func(l *Logger) {}); err != nil {
		t.Fatalf("invoke 1: %v", err)
	}
	if err := c.Invoke(func(l *Logger) {}); err != nil {
		t.Fatalf("invoke 2: %v", err)
	}
	if runs != 1 {
		t.Fatalf("decorator ran %d times, want 1", runs)
	}
}

func TestSecondDecorationSameScopeRejected(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Logger { return &Logger{Tag: "base"} })
	if err := c.Decorate(func(l *Logger) *Logger { return l }); err != nil {
		t.Fatalf("first decorate: %v", err)
	}
	wantContains(t, c.Decorate(func(l *Logger) *Logger { return l }), "already decorated")
	// an unrelated scope still accepts its own decoration for the same key
	child := c.Scope("child")
	if err := child.Decorate(func(l *Logger) *Logger { return &Logger{Tag: l.Tag + "+child"} }); err != nil {
		t.Fatalf("child decorate: %v", err)
	}
	var tag string
	if err := child.Invoke(func(l *Logger) { tag = l.Tag }); err != nil {
		t.Fatalf("child invoke: %v", err)
	}
	if tag != "base+child" {
		t.Fatalf("tag=%q, want %q", tag, "base+child")
	}
}

func TestDecoratorDependencyFailureSurfacesAtInvoke(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Logger { return &Logger{Tag: "base"} })
	if err := c.Decorate(func(l *Logger, cfg *Config) *Logger { return l }); err != nil {
		t.Fatalf("decorate with unresolvable dependency must not fail eagerly: %v", err)
	}
	err := c.Invoke(func(l *Logger) {})
	wantContains(t, err, "missing type:")
	wantContains(t, err, "integration.Config")
}

func TestGroupDecorationReplacesContent(t *testing.T) {
	c := dig.New()
	c.Provide(func() int { return 1 }, dig.Group("nums"))
	c.Provide(func() int { return 2 }, dig.Group("nums"))
	type gIn struct {
		dig.In
		Nums []int `group:"nums"`
	}
	type gOut struct {
		dig.Out
		Nums []int `group:"nums"`
	}
	if err := c.Decorate(func(p gIn) gOut {
		out := make([]int, 0, len(p.Nums))
		for _, v := range p.Nums {
			out = append(out, v*10)
		}
		return gOut{Nums: out}
	}); err != nil {
		t.Fatalf("decorate: %v", err)
	}
	var got []int
	if err := c.Invoke(func(p gIn) { got = sorted(p.Nums) }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !equalInts(got, []int{10, 20}) {
		t.Fatalf("got %v, want multiset {10,20}", got)
	}
}
