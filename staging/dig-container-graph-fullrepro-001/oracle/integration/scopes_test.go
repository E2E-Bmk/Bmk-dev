package integration

import (
	"strings"
	"testing"

	"go.uber.org/dig"
)

type Widget struct{ V int }
type Gadget struct{ V int }
type Logger struct{ Tag string }

func wantContains(t *testing.T, err error, frag string) {
	t.Helper()
	if err == nil {
		t.Fatalf("expected error containing %q, got nil", frag)
	}
	if !strings.Contains(err.Error(), frag) {
		t.Fatalf("error %q does not contain %q", err.Error(), frag)
	}
}

func TestChildScopeSeesParentRegistrations(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 1} })
	child := c.Scope("child")
	child.Provide(func(w *Widget) *Logger { return &Logger{Tag: "child"} })
	var w int
	var tag string
	if err := child.Invoke(func(a *Widget, l *Logger) { w, tag = a.V, l.Tag }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if w != 1 || tag != "child" {
		t.Fatalf("w=%d tag=%q, want 1 and %q", w, tag, "child")
	}
}

func TestParentCannotSeeChildRegistrations(t *testing.T) {
	c := dig.New()
	child := c.Scope("child")
	child.Provide(func() *Logger { return &Logger{Tag: "private"} })
	err := c.Invoke(func(l *Logger) {})
	wantContains(t, err, "missing type:")
}

func TestSiblingScopesAreIsolated(t *testing.T) {
	c := dig.New()
	s1 := c.Scope("s1")
	s2 := c.Scope("s2")
	s1.Provide(func() *Logger { return &Logger{Tag: "s1"} })
	err := s2.Invoke(func(l *Logger) {})
	wantContains(t, err, "missing type:")
}

func TestExportedRegistrationVisibleEverywhere(t *testing.T) {
	c := dig.New()
	s1 := c.Scope("s1")
	s2 := c.Scope("s2")
	s1.Provide(func() *Logger { return &Logger{Tag: "exported"} }, dig.Export(true))
	var fromSibling, fromRoot, fromLate *Logger
	if err := s2.Invoke(func(l *Logger) { fromSibling = l }); err != nil {
		t.Fatalf("sibling invoke: %v", err)
	}
	if err := c.Invoke(func(l *Logger) { fromRoot = l }); err != nil {
		t.Fatalf("root invoke: %v", err)
	}
	late := c.Scope("late")
	if err := late.Invoke(func(l *Logger) { fromLate = l }); err != nil {
		t.Fatalf("late scope invoke: %v", err)
	}
	if fromSibling == nil || fromSibling.Tag != "exported" {
		t.Fatalf("sibling saw %v", fromSibling)
	}
	if fromSibling != fromRoot || fromRoot != fromLate {
		t.Fatal("exported registration must memoize one shared instance for all scopes")
	}
}

func TestExportFalseKeepsScopePrivacy(t *testing.T) {
	c := dig.New()
	s1 := c.Scope("s1")
	s2 := c.Scope("s2")
	s1.Provide(func() *Logger { return &Logger{Tag: "priv"} }, dig.Export(false))
	wantContains(t, s2.Invoke(func(l *Logger) {}), "missing type:")
	var tag string
	if err := s1.Invoke(func(l *Logger) { tag = l.Tag }); err != nil {
		t.Fatalf("owning scope invoke: %v", err)
	}
	if tag != "priv" {
		t.Fatalf("tag=%q, want %q", tag, "priv")
	}
}

func TestLateRegistrationVisibleToExistingChild(t *testing.T) {
	c := dig.New()
	child := c.Scope("early")
	c.Provide(func() *Widget { return &Widget{V: 42} })
	var got int
	if err := child.Invoke(func(w *Widget) { got = w.V }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if got != 42 {
		t.Fatalf("got %d, want 42", got)
	}
}

func TestSharedRegistrationMemoizesAcrossScopes(t *testing.T) {
	c := dig.New()
	runs := 0
	c.Provide(func() *Widget { runs++; return &Widget{V: runs} })
	a := c.Scope("a")
	b := c.Scope("b")
	var fromA, fromB, fromRoot *Widget
	if err := a.Invoke(func(w *Widget) { fromA = w }); err != nil {
		t.Fatalf("a: %v", err)
	}
	if err := b.Invoke(func(w *Widget) { fromB = w }); err != nil {
		t.Fatalf("b: %v", err)
	}
	if err := c.Invoke(func(w *Widget) { fromRoot = w }); err != nil {
		t.Fatalf("root: %v", err)
	}
	if runs != 1 {
		t.Fatalf("constructor ran %d times, want 1", runs)
	}
	if fromA != fromB || fromB != fromRoot {
		t.Fatal("scopes observed different instances of one shared registration")
	}
}

func TestSiblingPrivateRegistrationsIndependent(t *testing.T) {
	c := dig.New()
	runs := 0
	ctor := func() *Widget { runs++; return &Widget{V: runs} }
	s1 := c.Scope("s1")
	s2 := c.Scope("s2")
	s1.Provide(ctor)
	s2.Provide(ctor)
	var v1, v2 *Widget
	if err := s1.Invoke(func(w *Widget) { v1 = w }); err != nil {
		t.Fatalf("s1: %v", err)
	}
	if err := s2.Invoke(func(w *Widget) { v2 = w }); err != nil {
		t.Fatalf("s2: %v", err)
	}
	if runs != 2 {
		t.Fatalf("constructor ran %d times, want 2 (one per independent registration)", runs)
	}
	if v1 == v2 {
		t.Fatal("independent sibling registrations must build independent instances")
	}
}

func TestGrandchildSeesWholeAncestorChain(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 1} })
	child := c.Scope("child")
	child.Provide(func() *Gadget { return &Gadget{V: 2} })
	grand := child.Scope("grand")
	grand.Provide(func() *Logger { return &Logger{Tag: "g"} })
	var w, g int
	var tag string
	if err := grand.Invoke(func(a *Widget, b *Gadget, l *Logger) { w, g, tag = a.V, b.V, l.Tag }); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	if w != 1 || g != 2 || tag != "g" {
		t.Fatalf("w=%d g=%d tag=%q", w, g, tag)
	}
}
