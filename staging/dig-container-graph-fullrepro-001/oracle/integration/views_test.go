package integration

import (
	"bytes"
	"errors"
	"strings"
	"testing"

	"go.uber.org/dig"
)

func TestValuesAppearInStringOnlyAfterBuild(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Widget { return &Widget{V: 9} })
	c.Provide(func(w *Widget) *Gadget { return &Gadget{V: w.V} })
	before := c.String()
	if !strings.Contains(before, "nodes:") || !strings.Contains(before, "values:") {
		t.Fatalf("String() = %q, want nodes: and values: blocks", before)
	}
	widgetBefore := strings.Count(before, "integration.Widget")
	gadgetBefore := strings.Count(before, "integration.Gadget")
	if widgetBefore == 0 || gadgetBefore == 0 {
		t.Fatalf("String() must list both registered constructors: %q", before)
	}
	if err := c.Invoke(func(g *Gadget) {}); err != nil {
		t.Fatalf("invoke: %v", err)
	}
	after := c.String()
	if strings.Count(after, "integration.Widget") <= widgetBefore ||
		strings.Count(after, "integration.Gadget") <= gadgetBefore {
		t.Fatalf("built values did not appear after Invoke:\nbefore=%q\nafter=%q", before, after)
	}
}

func TestVisualizeMentionsEveryProducedType(t *testing.T) {
	c := dig.New()
	c.Provide(func() *Config { return &Config{} })
	c.Provide(func(cfg *Config) *Store { return &Store{Cfg: cfg} })
	c.Provide(func() *Logger { return &Logger{} }, dig.Name("app"))
	var buf bytes.Buffer
	if err := dig.Visualize(c, &buf); err != nil {
		t.Fatalf("visualize: %v", err)
	}
	out := buf.String()
	if !strings.HasPrefix(out, "digraph") {
		t.Fatalf("output %q does not begin with digraph", out)
	}
	for _, want := range []string{"integration.Config", "integration.Store", "integration.Logger"} {
		if !strings.Contains(out, want) {
			t.Fatalf("DOT output missing produced type %s:\n%s", want, out)
		}
	}
}

func TestVisualizeErrorOptionKeepsValidDot(t *testing.T) {
	c := dig.New()
	err := c.Invoke(func(w *Widget) {})
	if err == nil {
		t.Fatal("expected a missing-type error")
	}
	var buf bytes.Buffer
	if verr := dig.Visualize(c, &buf, dig.VisualizeError(err)); verr != nil {
		t.Fatalf("visualize with error option: %v", verr)
	}
	if !strings.HasPrefix(buf.String(), "digraph") {
		t.Fatalf("output %q does not begin with digraph", buf.String())
	}
}

func TestErrorRenderingConsistentAcrossStages(t *testing.T) {
	// registration-time and resolution-time errors must annotate a named key
	// with the same syntax
	c := dig.New()
	if err := c.Provide(func() *Widget { return &Widget{V: 1} }, dig.Name("ro")); err != nil {
		t.Fatalf("provide: %v", err)
	}
	dupErr := c.Provide(func() *Widget { return &Widget{V: 2} }, dig.Name("ro"))
	wantContains(t, dupErr, `[name="ro"]`)
	type params struct {
		dig.In
		W *Widget `name:"missing"`
	}
	missErr := c.Invoke(func(p params) {})
	wantContains(t, missErr, `[name="missing"]`)
	wantContains(t, missErr, "missing type:")
}

func TestErrorClassificationSeparatesUserAndContainerErrors(t *testing.T) {
	c := dig.New()
	sentinel := errors.New("db down")
	c.Provide(func() (*Store, error) { return nil, sentinel })

	// container-originated failure: dig.Error all the way down
	missErr := c.Invoke(func(w *Widget) {})
	var de dig.Error
	if !errors.As(missErr, &de) {
		t.Fatalf("missing-type error %v must implement dig.Error", missErr)
	}
	if !errors.As(dig.RootCause(missErr), &de) {
		t.Fatal("RootCause of a container-only chain must still be a dig.Error")
	}

	// user-originated failure: RootCause returns the user's error
	userErr := c.Invoke(func(s *Store) {})
	if !errors.As(userErr, &de) {
		t.Fatalf("wrapper around a user error must implement dig.Error, got %v", userErr)
	}
	if dig.RootCause(userErr) != sentinel {
		t.Fatalf("RootCause = %v, want the user sentinel", dig.RootCause(userErr))
	}
}

func TestApplicationAssemblyWorkflow(t *testing.T) {
	// end-to-end: named values + groups + scope + decorator resolve together
	type Route struct{ Path string }
	type App struct {
		RO     *Conn
		Routes []string
	}
	c := dig.New()
	c.Provide(func() *Conn { return &Conn{Addr: "ro:5432"} }, dig.Name("ro"))
	c.Provide(func() *Conn { return &Conn{Addr: "rw:5432"} }, dig.Name("rw"))
	c.Provide(func() Route { return Route{Path: "/health"} }, dig.Group("routes"))
	c.Provide(func() Route { return Route{Path: "/metrics"} }, dig.Group("routes"))

	web := c.Scope("web")
	if err := web.Decorate(func(p struct {
		dig.In
		Routes []Route `group:"routes"`
	}) struct {
		dig.Out
		Routes []Route `group:"routes"`
	} {
		return struct {
			dig.Out
			Routes []Route `group:"routes"`
		}{Routes: append(p.Routes, Route{Path: "/debug"})}
	}); err != nil {
		t.Fatalf("decorate: %v", err)
	}

	build := func(s interface {
		Invoke(interface{}, ...dig.InvokeOption) error
	}) (*App, error) {
		var app *App
		err := s.Invoke(func(p struct {
			dig.In
			RO     *Conn   `name:"ro"`
			Routes []Route `group:"routes"`
		}) {
			paths := make([]string, 0, len(p.Routes))
			for _, r := range p.Routes {
				paths = append(paths, r.Path)
			}
			app = &App{RO: p.RO, Routes: paths}
		})
		return app, err
	}

	webApp, err := build(web)
	if err != nil {
		t.Fatalf("web build: %v", err)
	}
	if webApp == nil || webApp.RO == nil || webApp.RO.Addr != "ro:5432" {
		t.Fatalf("web app conn not delivered: %+v", webApp)
	}
	if !hasAll(webApp.Routes, "/health", "/metrics", "/debug") || len(webApp.Routes) != 3 {
		t.Fatalf("web routes = %v, want the two provided plus the decorated one", webApp.Routes)
	}

	rootApp, err := build(c)
	if err != nil {
		t.Fatalf("root build: %v", err)
	}
	if rootApp == nil {
		t.Fatal("root build produced no app")
	}
	if !hasAll(rootApp.Routes, "/health", "/metrics") || len(rootApp.Routes) != 2 {
		t.Fatalf("root routes = %v, want only the two provided (no decoration)", rootApp.Routes)
	}
}

type Conn struct{ Addr string }

func hasAll(xs []string, wants ...string) bool {
	set := make(map[string]bool, len(xs))
	for _, x := range xs {
		set[x] = true
	}
	for _, w := range wants {
		if !set[w] {
			return false
		}
	}
	return true
}
