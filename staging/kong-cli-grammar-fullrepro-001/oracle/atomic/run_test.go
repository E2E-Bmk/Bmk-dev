package atomic

import (
	"errors"
	"testing"

	"github.com/alecthomas/kong"
)

var hookLog []string

type hookFlag bool

func (h hookFlag) BeforeReset() error   { hookLog = append(hookLog, "BeforeReset"); return nil }
func (h hookFlag) BeforeResolve() error { hookLog = append(hookLog, "BeforeResolve"); return nil }
func (h hookFlag) BeforeApply() error   { hookLog = append(hookLog, "BeforeApply"); return nil }
func (h hookFlag) AfterApply() error    { hookLog = append(hookLog, "AfterApply"); return nil }

// Verifies: Hooks, Bindings and Command Execution — lifecycle hooks
// (order).
func TestHookOrder(t *testing.T) {
	hookLog = nil
	var cli struct {
		Flag hookFlag
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--flag"})
	want := []string{"BeforeReset", "BeforeResolve", "BeforeApply", "AfterApply"}
	if len(hookLog) != len(want) {
		t.Fatalf("hook log = %v, want %v", hookLog, want)
	}
	for i := range want {
		wantEq(t, hookLog[i], want[i], "hook order position")
	}
}

type failingHook bool

func (f failingHook) AfterApply() error { return errors.New("hook rejected") }

// Verifies: Hooks, Bindings and Command Execution — lifecycle hooks
// (error aborts parse).
func TestHookErrorAbortsParse(t *testing.T) {
	var cli struct {
		Flag failingHook
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--flag"})
	wantContains(t, err.Error(), "hook rejected", "hook error propagated")
}

var afterRunLog []string

type afterRunCmd struct{}

func (a *afterRunCmd) Run() error      { afterRunLog = append(afterRunLog, "Run"); return nil }
func (a *afterRunCmd) AfterRun() error { afterRunLog = append(afterRunLog, "AfterRun"); return nil }

// Verifies: Hooks, Bindings and Command Execution — lifecycle hooks
// (AfterRun).
func TestAfterRunHook(t *testing.T) {
	afterRunLog = nil
	var cli struct {
		Cmd afterRunCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"cmd"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, len(afterRunLog), 2, "both phases ran")
	wantEq(t, afterRunLog[0], "Run", "run first")
	wantEq(t, afterRunLog[1], "AfterRun", "after-run second")
}

var chainLog []string

type parentCmd struct {
	Child childCmd `cmd:""`
}

func (p *parentCmd) Run() error { chainLog = append(chainLog, "parent"); return nil }

type childCmd struct{}

func (c *childCmd) Run() error { chainLog = append(chainLog, "child"); return nil }

// Verifies: Hooks, Bindings and Command Execution — run dispatch
// (leaf-to-root chain).
func TestRunChainLeafToRoot(t *testing.T) {
	chainLog = nil
	var cli struct {
		Parent parentCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"parent", "child"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, len(chainLog), 2, "both Run methods invoked")
	wantEq(t, chainLog[0], "child", "leaf first")
	wantEq(t, chainLog[1], "parent", "root last")
}

type runlessCmd struct{}

// Verifies: Hooks, Bindings and Command Execution — run dispatch (no
// method anywhere).
func TestRunNoMethodError(t *testing.T) {
	var cli struct {
		Cmd runlessCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"cmd"})
	err := ctx.Run()
	if err == nil {
		t.Fatal("Run succeeded without any Run method")
	}
	wantEq(t, err.Error(), "no Run() method found in hierarchy of cmd", "error text")
}

var ctxBound bool

type ctxCmd struct{}

func (c *ctxCmd) Run(ctx *kong.Context) error { ctxBound = ctx != nil; return nil }

// Verifies: Hooks, Bindings and Command Execution — bindings (context
// auto-bound).
func TestContextAutoBound(t *testing.T) {
	ctxBound = false
	var cli struct {
		Cmd ctxCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"cmd"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, ctxBound, true, "*kong.Context injected")
}

type dep struct{ V string }

var depSeen string

type depCmd struct{}

func (d *depCmd) Run(x *dep) error { depSeen = x.V; return nil }

// Verifies: Hooks, Bindings and Command Execution — bindings (Bind option
// and Run arguments).
func TestBindOptionAndRunArguments(t *testing.T) {
	depSeen = ""
	var cli struct {
		Cmd depCmd `cmd:""`
	}
	a := build(t, &cli, kong.Bind(&dep{V: "opt"}))
	ctx := mustParse(t, a, []string{"cmd"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run with option binding failed: %v", err)
	}
	wantEq(t, depSeen, "opt", "option-bound dependency")

	depSeen = ""
	ctx2 := mustParse(t, a, []string{"cmd"})
	if err := ctx2.Run(&dep{V: "call"}); err != nil {
		t.Fatalf("Run with call binding failed: %v", err)
	}
	wantEq(t, depSeen, "call", "call-site binding wins")
}

type iface interface{ Val() string }

type impl struct{}

func (i *impl) Val() string { return "impl" }

var ifaceSeen string

type ifaceCmd struct{}

func (c *ifaceCmd) Run(i iface) error { ifaceSeen = i.Val(); return nil }

// Verifies: Hooks, Bindings and Command Execution — bindings (BindTo
// interface).
func TestBindToInterface(t *testing.T) {
	ifaceSeen = ""
	var cli struct {
		Cmd ifaceCmd `cmd:""`
	}
	a := build(t, &cli, kong.BindTo(&impl{}, (*iface)(nil)))
	ctx := mustParse(t, a, []string{"cmd"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, ifaceSeen, "impl", "interface binding used")
}

// Verifies: Hooks, Bindings and Command Execution — bindings
// (BindToProvider).
func TestBindToProvider(t *testing.T) {
	depSeen = ""
	var cli struct {
		Cmd depCmd `cmd:""`
	}
	a := build(t, &cli, kong.BindToProvider(func() (*dep, error) { return &dep{V: "prov"}, nil }))
	ctx := mustParse(t, a, []string{"cmd"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, depSeen, "prov", "provider-supplied dependency")
}

// Verifies: Hooks, Bindings and Command Execution — bindings (missing
// binding error).
func TestMissingBindingError(t *testing.T) {
	var cli struct {
		Cmd depCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"cmd"})
	err := ctx.Run()
	if err == nil {
		t.Fatal("Run succeeded without binding")
	}
	wantContains(t, err.Error(), "couldn't find binding of type", "error prefix")
	wantContains(t, err.Error(), "use kong.Bind(", "remedy suggestion")
}

type exitErr struct{}

func (e exitErr) Error() string { return "coded failure" }
func (e exitErr) ExitCode() int { return 7 }

type exitCmd struct{}

func (c *exitCmd) Run() error { return exitErr{} }

// Verifies: Hooks, Bindings and Command Execution — errors from commands
// (ExitCoder honoured by FatalIfErrorf).
func TestExitCoderHonoured(t *testing.T) {
	var cli struct {
		Cmd exitCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"cmd"})
	err := ctx.Run()
	wantEq(t, err.Error(), "coded failure", "run error propagated unchanged")
	a.k.FatalIfErrorf(err)
	wantContains(t, a.errw.String(), "app: error: coded failure", "stderr message")
	if len(a.exits) == 0 || a.exits[0] != 7 {
		t.Fatalf("exit codes = %v, want [7]", a.exits)
	}
}
