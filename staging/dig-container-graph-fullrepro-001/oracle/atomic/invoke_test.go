package atomic

import (
	"bytes"
	"errors"
	"strings"
	"testing"

	"go.uber.org/dig"
)

func TestInvokeZeroArgFunctionRuns(t *testing.T) {
	c := dig.New()
	ran := false
	if err := c.Invoke(func() { ran = true }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if !ran {
		t.Fatal("zero-argument function did not run")
	}
}

func TestInvokeRejectsNonFunction(t *testing.T) {
	c := dig.New()
	err := c.Invoke(7)
	wantContains(t, err, "can't invoke non-function")
}

func TestMissingTypeErrorRendersKey(t *testing.T) {
	c := dig.New()
	ran := false
	err := c.Invoke(func(w *Widget) { ran = true })
	wantContains(t, err, "missing type:")
	wantContains(t, err, "atomic.Widget")
	if ran {
		t.Fatal("invoked function must not run when a dependency is missing")
	}
}

func TestMissingNamedKeyRendersNameAnnotation(t *testing.T) {
	c := dig.New()
	type params struct {
		dig.In
		W *Widget `name:"ro"`
	}
	err := c.Invoke(func(p params) {})
	wantContains(t, err, "missing type:")
	wantContains(t, err, `[name="ro"]`)
}

func TestInvokedFunctionErrorReturnedUnchanged(t *testing.T) {
	c := dig.New()
	sentinel := errors.New("user failure")
	ran := false
	err := c.Invoke(func() error { ran = true; return sentinel })
	if !ran {
		t.Fatal("invoked function did not run")
	}
	if err != sentinel {
		t.Fatalf("invoke returned %v, want the sentinel error unchanged", err)
	}
}

func TestInvokeExtraResultsIgnored(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 2} })
	got := 0
	if err := c.Invoke(func(w *Widget) *Gadget { got = w.V; return &Gadget{} }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 2 {
		t.Fatalf("got %d, want 2", got)
	}
	// the Gadget returned by the invoked function is not registered
	wantContains(t, c.Invoke(func(g *Gadget) {}), "missing type:")
}

func TestUserConstructorErrorReachableViaRootCause(t *testing.T) {
	c := dig.New()
	sentinel := errors.New("ctor exploded")
	c.Provide(func() (*Widget, error) { return nil, sentinel })
	err := c.Invoke(func(w *Widget) {})
	wantContains(t, err, "received non-nil error from function")
	if root := dig.RootCause(err); root != sentinel {
		t.Fatalf("RootCause = %v, want the constructor's own error", root)
	}
}

func TestContainerErrorsImplementDigError(t *testing.T) {
	c := dig.New()
	var de dig.Error
	if err := c.Provide(42); !errors.As(err, &de) {
		t.Fatalf("Provide validation error %v does not implement dig.Error", err)
	}
	if err := c.Invoke(func(w *Widget) {}); !errors.As(err, &de) {
		t.Fatalf("missing-type error %v does not implement dig.Error", err)
	}
}

func TestRootCauseOfContainerOnlyChainIsDigError(t *testing.T) {
	c := dig.New()
	err := c.Invoke(func(w *Widget) {})
	root := dig.RootCause(err)
	if root == nil {
		t.Fatal("RootCause returned nil")
	}
	wantContains(t, root, "missing type:")
	var de dig.Error
	if !errors.As(root, &de) {
		t.Fatal("bottom of an all-container chain must still implement dig.Error")
	}
}

func TestRecoverFromPanicsReturnsPanicError(t *testing.T) {
	c := dig.New(dig.RecoverFromPanics())
	c.Provide(func() *Widget { panic("ctor boom") })
	err := c.Invoke(func(w *Widget) {})
	if err == nil {
		t.Fatal("expected an error from a panicking constructor")
	}
	var pe dig.PanicError
	if !errors.As(err, &pe) {
		t.Fatalf("error %v does not carry a PanicError", err)
	}
	if pe.Panic != "ctor boom" {
		t.Fatalf("PanicError.Panic = %v, want %q", pe.Panic, "ctor boom")
	}
	if !strings.HasPrefix(pe.Error(), "panic:") {
		t.Fatalf("PanicError message %q does not begin with %q", pe.Error(), "panic:")
	}
}

func TestPanicErrorIsNotADigError(t *testing.T) {
	c := dig.New(dig.RecoverFromPanics())
	c.Provide(func() *Widget { panic("kaboom") })
	err := c.Invoke(func(w *Widget) {})
	root := dig.RootCause(err)
	var pe dig.PanicError
	if !errors.As(root, &pe) {
		t.Fatalf("RootCause = %v, want the PanicError", root)
	}
	var de dig.Error
	if errors.As(root, &de) {
		t.Fatal("PanicError must not implement dig.Error")
	}
}

func TestPanicPropagatesWithoutRecoverOption(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { panic("unrecovered") })
	panicked := false
	func() {
		defer func() {
			if recover() != nil {
				panicked = true
			}
		}()
		_ = c.Invoke(func(w *Widget) {})
	}()
	if !panicked {
		t.Fatal("panic must propagate when RecoverFromPanics was not given")
	}
}

func TestInvokePanicRecoveredToo(t *testing.T) {
	c := dig.New(dig.RecoverFromPanics())
	err := c.Invoke(func() { panic("invoke boom") })
	var pe dig.PanicError
	if !errors.As(err, &pe) {
		t.Fatalf("error %v does not carry a PanicError for an invoked-function panic", err)
	}
	if pe.Panic != "invoke boom" {
		t.Fatalf("PanicError.Panic = %v, want %q", pe.Panic, "invoke boom")
	}
}

func TestStringListsNodesAndValues(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 5} })
	before := c.String()
	if !strings.Contains(before, "nodes:") || !strings.Contains(before, "values:") {
		t.Fatalf("String() = %q, want nodes: and values: blocks", before)
	}
	if !strings.Contains(before, "atomic.Widget") {
		t.Fatalf("String() = %q, want the registered result type listed", before)
	}
	countBefore := strings.Count(before, "atomic.Widget")
	if err := c.Invoke(func(w *Widget) {}); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	after := c.String()
	if strings.Count(after, "atomic.Widget") <= countBefore {
		t.Fatalf("String() gained no built-value entry after Invoke:\nbefore=%q\nafter=%q", before, after)
	}
}

func TestVisualizeEmitsDotDigraph(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{} })
	c.Provide(func(w *Widget) *Gadget { return &Gadget{} })
	var buf bytes.Buffer
	if err := dig.Visualize(c, &buf); err != nil {
		t.Fatalf("visualize: %v", err)
	}
	out := buf.String()
	if !strings.HasPrefix(out, "digraph") {
		t.Fatalf("output %q does not begin with digraph", out)
	}
	if !strings.Contains(out, "atomic.Widget") || !strings.Contains(out, "atomic.Gadget") {
		t.Fatalf("output does not mention every produced type: %q", out)
	}
}

func TestInvokeDemandsOnlyRequestedSubgraph(t *testing.T) {
	c := dig.New()
	widgetRuns, gadgetRuns := 0, 0
	c.Provide(func() *Widget { widgetRuns++; return &Widget{} })
	c.Provide(func() *Gadget { gadgetRuns++; return &Gadget{} })
	if err := c.Invoke(func(w *Widget) {}); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if widgetRuns != 1 || gadgetRuns != 0 {
		t.Fatalf("widgetRuns=%d gadgetRuns=%d, want 1 and 0", widgetRuns, gadgetRuns)
	}
}
