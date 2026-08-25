package integration

import (
	"os"
	"strings"
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Cross-View Invariants 1 (help lists exactly the parseable
// surface).
func TestHelpMatchesParseableSurface(t *testing.T) {
	var cli struct {
		Alpha  string `help:"Alpha." short:"a"`
		Beta   int    `help:"Beta." default:"3"`
		Secret bool   `hidden:""`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	// Every visible flag renders and parses.
	wantContains(t, out, "-a, --alpha", "alpha with short form")
	wantContains(t, out, "--beta=3", "beta with default placeholder")
	if strings.Contains(out, "secret") {
		t.Fatalf("hidden flag rendered:\n%s", out)
	}
	b := build(t, &cli)
	mustParse(t, b, []string{"--alpha", "x", "--beta", "9", "--secret"})
	wantEq(t, cli.Alpha, "x", "alpha parses")
	wantEq(t, cli.Beta, 9, "beta parses")
	wantEq(t, cli.Secret, true, "hidden flag parses despite absence from help")
}

// Verifies: Cross-View Invariants 1 (model flags render and parse
// consistently for every declared flag).
func TestModelFlagsAllParseable(t *testing.T) {
	var cli struct {
		One   string `default:"1"`
		Two   bool
		Three []string
		Sub   struct {
			Local int `default:"5"`
		} `cmd:""`
	}
	a := build(t, &cli)
	flags := collectFlags(t, a.k, "sub")
	names := map[string]bool{}
	for _, f := range flags {
		names[f.Name] = true
	}
	for _, want := range []string{"help", "one", "two", "three", "local"} {
		if !names[want] {
			t.Fatalf("model flag set %v missing %q", names, want)
		}
	}
	// Each named flag is accepted by the parser at the sub command.
	b := build(t, &cli)
	mustParse(t, b, []string{"sub", "--one", "x", "--two", "--three", "e", "--local", "7"})
	wantEq(t, cli.One, "x", "root flag via model name")
	wantEq(t, cli.Sub.Local, 7, "sub flag via model name")
}

// Verifies: Cross-View Invariants 2 (Command agrees with the model
// summary).
func TestCommandAgreesWithSummary(t *testing.T) {
	var cli struct {
		Mv struct {
			Src string `arg:""`
			Dst string `arg:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"mv", "a", "b"})
	sub := a.k.Model.Children[0]
	summary := sub.Summary()
	cmd := ctx.Command()
	if !strings.HasPrefix(summary, cmd) {
		t.Fatalf("Command() %q is not a prefix of Summary() %q", cmd, summary)
	}
	wantEq(t, cmd, "mv <src> <dst>", "command string")
	wantEq(t, summary, "mv <src> <dst>", "summary string")
}

// Verifies: Cross-View Invariants 3 (model flags, context flags, and bound
// struct agree).
func TestModelContextStructAgreement(t *testing.T) {
	var cli struct {
		Num  int    `default:"3"`
		Name string `default:"anon"`
		Sub  struct {
			Local string
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"sub", "--num", "9", "--local", "L"})

	modelFlags := collectFlags(t, a.k, "sub")
	ctxFlags := ctx.Flags()
	if len(modelFlags) != len(ctxFlags) {
		t.Fatalf("model flags %d != context flags %d", len(modelFlags), len(ctxFlags))
	}
	for _, f := range ctxFlags {
		switch f.Name {
		case "num":
			wantEq(t, ctx.FlagValue(f), 9, "num agrees with struct")
			wantEq(t, cli.Num, 9, "struct field")
		case "name":
			wantEq(t, ctx.FlagValue(f), "anon", "default reported")
		case "local":
			wantEq(t, ctx.FlagValue(f), "L", "sub flag agrees")
			wantEq(t, cli.Sub.Local, "L", "struct field")
		}
	}
}

// Verifies: Cross-View Invariants 4 (precedence chain with all four
// sources).
func TestPrecedenceChainObservable(t *testing.T) {
	t.Setenv("ORACLE_CHAIN", "fromenv")
	newGrammar := func() *struct {
		V string `env:"ORACLE_CHAIN" default:"fromdefault"`
	} {
		return &struct {
			V string `env:"ORACLE_CHAIN" default:"fromdefault"`
		}{}
	}
	resolver, _ := kong.JSON(strings.NewReader(`{"v": "fromjson"}`))

	// Command line beats everything.
	g1 := newGrammar()
	a1 := build(t, g1, kong.Resolvers(resolver))
	mustParse(t, a1, []string{"--v", "fromcli"})
	wantEq(t, g1.V, "fromcli", "cli wins")

	// Resolver beats env and default.
	g2 := newGrammar()
	a2 := build(t, g2, kong.Resolvers(resolver))
	mustParse(t, a2, nil)
	wantEq(t, g2.V, "fromjson", "resolver wins over env")

	// Env beats default.
	g3 := newGrammar()
	a3 := build(t, g3)
	mustParse(t, a3, nil)
	wantEq(t, g3.V, "fromenv", "env wins over default")

	// Default applies when nothing else does. t.Setenv above registered
	// cleanup, so unsetting here is safe.
	os.Unsetenv("ORACLE_CHAIN")
	g4 := newGrammar()
	a4 := build(t, g4)
	mustParse(t, a4, nil)
	wantEq(t, g4.V, "fromdefault", "default applies with no other source")
}

// Verifies: Cross-View Invariants 4 (Value.Set reflects the winning
// source).
func TestValueSetReflectsSource(t *testing.T) {
	var cli struct {
		Given  string
		Absent string
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"--given", "x"})
	for _, f := range ctx.Flags() {
		switch f.Name {
		case "given":
			wantEq(t, f.Set, true, "explicitly set flag reports Set")
		case "absent":
			wantEq(t, f.Set, false, "untouched flag does not report Set")
		}
	}
}

// Verifies: Cross-View Invariants 5 (staged parsing equals one-shot
// parsing, success path).
func TestStagedEqualsOneShotSuccess(t *testing.T) {
	type grammar struct {
		Flag string `default:"dv"`
		Sub  struct {
			Arg string `arg:""`
		} `cmd:""`
	}
	args := []string{"sub", "val", "--flag", "x"}

	oneShot := &grammar{}
	a := build(t, oneShot)
	ctxA := mustParse(t, a, args)

	staged := &grammar{}
	b := build(t, staged)
	ctxB, err := kong.Trace(b.k, args)
	if err != nil || ctxB.Error != nil {
		t.Fatalf("Trace failed: %v / %v", err, ctxB.Error)
	}
	if err := ctxB.Resolve(); err != nil {
		t.Fatalf("Resolve failed: %v", err)
	}
	cmd, err := ctxB.Apply()
	if err != nil {
		t.Fatalf("Apply failed: %v", err)
	}
	if err := ctxB.Validate(); err != nil {
		t.Fatalf("Validate failed: %v", err)
	}
	wantEq(t, cmd, ctxA.Command(), "command strings agree")
	wantEq(t, staged.Flag, oneShot.Flag, "flag values agree")
	wantEq(t, staged.Sub.Arg, oneShot.Sub.Arg, "positional values agree")
	wantEq(t, ctxB.Selected().Name, ctxA.Selected().Name, "selection agrees")
}

// Verifies: Cross-View Invariants 5 (staged parsing equals one-shot
// parsing, failure path).
func TestStagedEqualsOneShotFailure(t *testing.T) {
	type grammar struct {
		Req string `required:""`
	}
	oneShot := &grammar{}
	a := build(t, oneShot)
	_, errA := a.k.Parse(nil)
	if errA == nil {
		t.Fatal("one-shot parse succeeded unexpectedly")
	}

	staged := &grammar{}
	b := build(t, staged)
	ctxB, err := kong.Trace(b.k, nil)
	if err != nil || ctxB.Error != nil {
		t.Fatalf("Trace failed early: %v / %v", err, ctxB.Error)
	}
	if err := ctxB.Resolve(); err != nil {
		t.Fatalf("Resolve failed: %v", err)
	}
	if _, err := ctxB.Apply(); err != nil {
		t.Fatalf("Apply failed: %v", err)
	}
	errB := ctxB.Validate()
	if errB == nil {
		t.Fatal("Validate succeeded where Parse failed")
	}
	wantEq(t, errB.Error(), "missing flags: --req=STRING", "same failure at validation stage")
	wantContains(t, errA.Error(), "missing flags: --req=STRING", "one-shot failure text")
}

// Verifies: Cross-View Invariants 6 (build-time rejection is total).
func TestBuildTimeRejectionTotal(t *testing.T) {
	bad := []struct {
		label   string
		grammar interface{}
	}{
		{"bare enum", &struct {
			Mode string `enum:"a,b"`
		}{}},
		{"negatable non-bool", &struct {
			Neg string `negatable:""`
		}{}},
		{"required after optional", &struct {
			A string `arg:"" optional:""`
			B string `arg:""`
		}{}},
		{"duplicate short", &struct {
			A bool `short:"x"`
			B bool `short:"x"`
		}{}},
	}
	for _, tc := range bad {
		if _, err := kong.New(tc.grammar, kong.Name("app")); err == nil {
			t.Fatalf("%s: invalid grammar accepted", tc.label)
		}
	}

	// A grammar accepted by New never fails structurally at parse time.
	var good struct {
		Mode string `enum:"a,b" default:"a"`
		Neg  bool   `negatable:""`
		A    string `arg:"" optional:""`
	}
	a := build(t, &good)
	mustParse(t, a, nil)
	mustParse(t, a, []string{"--mode", "b", "--no-neg", "pos"})
	wantEq(t, good.Mode, "b", "enum value bound")
	wantEq(t, good.A, "pos", "positional bound")
}

// Verifies: Cross-View Invariants 7 (interpolation is uniform across
// default, help, and enum).
func TestInterpolationUniform(t *testing.T) {
	var cli struct {
		Mode string `enum:"${opts}" default:"${mode_default}" help:"One of ${opts}."`
	}
	a := build(t, &cli, kong.Vars{"opts": "one,two", "mode_default": "one"})
	mustParse(t, a, nil)
	wantEq(t, cli.Mode, "one", "default interpolated")
	err := parseErr(t, a, []string{"--mode", "three"})
	wantEq(t, err.Error(), `--mode must be one of "one","two" but got "three"`, "enum interpolated")
	b := build(t, &cli, kong.Vars{"opts": "one,two", "mode_default": "one"})
	b.k.Parse([]string{"--help"})
	wantContains(t, b.out.String(), "One of one,two.", "help interpolated")
}

// Verifies: Cross-View Invariants 8 (errors name flags as help renders
// them).
func TestErrorsUseHelpRendering(t *testing.T) {
	var cli struct {
		Req string `required:"" help:"Required."`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	help := a.out.String()
	wantContains(t, help, "--req=STRING", "placeholder in help")

	b := build(t, &cli)
	err := parseErr(t, b, nil)
	wantEq(t, err.Error(), "missing flags: --req=STRING", "same rendering in error")
}

// Verifies: Cross-View Invariants 2 and 8 (expected-children error names
// the same children the model exposes).
func TestExpectedChildrenMatchModel(t *testing.T) {
	var cli struct {
		Parent struct {
			Child struct{} `cmd:""`
			Other struct{} `cmd:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"parent"})
	parent := a.k.Model.Children[0]
	for _, c := range parent.Children {
		wantContains(t, err.Error(), `"`+c.Name+`"`, "error names model child")
	}
	wantEq(t, err.Error(), `expected one of "child", "other"`, "full message")
}

// Verifies: Cross-View Invariants 1 and Help Rendering (DefaultEnvars
// annotation matches the variable actually read).
func TestDefaultEnvarsHelpAndResolution(t *testing.T) {
	var cli struct {
		SomeFlag string `help:"Some flag."`
	}
	a := build(t, &cli, kong.DefaultEnvars("MYAPP"))
	a.k.Parse([]string{"--help"})
	wantContains(t, a.out.String(), "($MYAPP_SOME_FLAG)", "derived envar in help")

	t.Setenv("MYAPP_SOME_FLAG", "fromenv")
	var cli2 struct {
		SomeFlag string `help:"Some flag."`
	}
	b := build(t, &cli2, kong.DefaultEnvars("MYAPP"))
	mustParse(t, b, nil)
	wantEq(t, cli2.SomeFlag, "fromenv", "annotated variable is the one read")
}

// Verifies: Cross-View Invariants 4 and Validation (required satisfied
// through each source in turn).
func TestRequiredSatisfiedThroughEachSource(t *testing.T) {
	type grammar struct {
		R string `env:"ORACLE_REQ" required:""`
	}

	// Unsatisfied.
	g1 := &grammar{}
	a1 := build(t, g1)
	err := parseErr(t, a1, nil)
	wantContains(t, err.Error(), "missing flags: --r=STRING", "missing without sources")

	// Via environment.
	t.Setenv("ORACLE_REQ", "envval")
	g2 := &grammar{}
	a2 := build(t, g2)
	mustParse(t, a2, nil)
	wantEq(t, g2.R, "envval", "env satisfies required")

	// Via resolver (still set env to prove resolver wins and satisfies).
	resolver, _ := kong.JSON(strings.NewReader(`{"r": "jsonval"}`))
	g3 := &grammar{}
	a3 := build(t, g3, kong.Resolvers(resolver))
	mustParse(t, a3, nil)
	wantEq(t, g3.R, "jsonval", "resolver satisfies required")

	// Via command line.
	g4 := &grammar{}
	a4 := build(t, g4, kong.Resolvers(resolver))
	mustParse(t, a4, []string{"--r", "cliv"})
	wantEq(t, g4.R, "cliv", "cli satisfies required and wins")
}

// Verifies: Cross-View Invariants 6 and Grammar Construction (a valid
// grammar parses every declared projection consistently after
// FlagNamer renaming).
func TestFlagNamerConsistentAcrossViews(t *testing.T) {
	namer := func(name string) string { return "x-" + strings.ToLower(name) }
	var cli struct {
		Alpha string `help:"Alpha."`
	}
	a := build(t, &cli, kong.FlagNamer(namer))
	a.k.Parse([]string{"--help"})
	wantContains(t, a.out.String(), "--x-alpha", "renamed in help")

	var cli2 struct {
		Alpha string `help:"Alpha."`
	}
	b := build(t, &cli2, kong.FlagNamer(namer))
	mustParse(t, b, []string{"--x-alpha", "v"})
	wantEq(t, cli2.Alpha, "v", "renamed flag parses")
	found := false
	for _, f := range b.k.Model.Flags {
		if f.Name == "x-alpha" {
			found = true
		}
	}
	wantEq(t, found, true, "renamed in model")
}
