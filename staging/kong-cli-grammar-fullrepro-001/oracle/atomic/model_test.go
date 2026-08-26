package atomic

import (
	"errors"
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Model Introspection and the Parse Context — the model (node
// fields and types).
func TestModelNodeFields(t *testing.T) {
	var cli struct {
		Verbose bool `short:"v" help:"Verbose."`
		Sub     struct {
			Arg string `arg:""`
		} `cmd:"" help:"Sub help." aliases:"s"`
	}
	a := build(t, &cli)
	m := a.k.Model
	wantEq(t, m.Name, "app", "application name")
	wantEq(t, m.Node.Type, kong.ApplicationNode, "root node type")
	if len(m.Children) != 1 {
		t.Fatalf("children = %d, want 1", len(m.Children))
	}
	sub := m.Children[0]
	wantEq(t, sub.Type, kong.CommandNode, "command node type")
	wantEq(t, sub.Name, "sub", "command name")
	wantEq(t, sub.Help, "Sub help.", "command help")
	wantEq(t, sub.Parent, m.Node, "parent link")
	wantEq(t, len(sub.Aliases), 1, "alias count")
	wantEq(t, sub.Aliases[0], "s", "alias value")
	wantEq(t, len(sub.Positional), 1, "positional count")
	wantEq(t, sub.Positional[0].Name, "arg", "positional name")
}

// Verifies: Model Introspection and the Parse Context — the model
// (node queries).
func TestModelNodeQueries(t *testing.T) {
	var cli struct {
		Sub struct {
			Local bool
			Inner struct{} `cmd:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	sub := a.k.Model.Children[0]
	wantEq(t, sub.Path(), "sub", "path below application")
	wantEq(t, sub.FullPath(), "app sub", "full path")
	wantEq(t, sub.Depth(), 0, "first-level command depth")
	wantEq(t, sub.Leaf(), false, "command with children is not leaf")
	inner := sub.Children[0]
	wantEq(t, inner.Depth(), 1, "second-level command depth")
	wantEq(t, inner.Leaf(), true, "leaf command")
	wantEq(t, a.k.Model.Node.Leaf(), false, "root with children is not leaf")

	var cli2 struct {
		Sub struct {
			Arg   string `arg:""`
			Local bool
		} `cmd:""`
	}
	b := build(t, &cli2)
	wantEq(t, b.k.Model.Children[0].Summary(), "sub <arg> [flags]", "summary")
}

// Verifies: Model Introspection and the Parse Context — the model (flag
// metadata).
func TestModelFlagFields(t *testing.T) {
	var cli struct {
		Level int  `short:"l" env:"LEVEL" default:"2" help:"Level."`
		Mode  string `enum:"a,b" default:"a"`
		Req   string `required:""`
	}
	a := build(t, &cli)
	byName := map[string]*kong.Flag{}
	for _, f := range a.k.Model.Flags {
		byName[f.Name] = f
	}
	level := byName["level"]
	if level == nil {
		t.Fatal("level flag missing from model")
	}
	wantEq(t, level.Short, 'l', "short rune")
	wantEq(t, len(level.Envs), 1, "env count")
	wantEq(t, level.Envs[0], "LEVEL", "env name")
	wantEq(t, level.HasDefault, true, "has default")
	wantEq(t, level.Default, "2", "default text")
	mode := byName["mode"]
	wantEq(t, mode.Enum, "a,b", "enum text")
	req := byName["req"]
	wantEq(t, req.Required, true, "required")
}

// Verifies: Model Introspection and the Parse Context — the context
// (queries after a parse).
func TestContextQueries(t *testing.T) {
	var cli struct {
		Num int `default:"3"`
		Sub struct {
			Local string
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"sub", "--local", "x", "--num", "9"})
	wantEq(t, ctx.Selected().Name, "sub", "selected node")
	wantEq(t, len(ctx.Args), 5, "original args retained")
	wantEq(t, ctx.Args[0], "sub", "first arg")
	var numFlag *kong.Flag
	for _, f := range ctx.Flags() {
		if f.Name == "num" {
			numFlag = f
		}
	}
	if numFlag == nil {
		t.Fatal("num flag not in context flags")
	}
	wantEq(t, ctx.FlagValue(numFlag), 9, "FlagValue reports bound value")
}

// Verifies: Model Introspection and the Parse Context — the context
// (Empty).
func TestContextEmpty(t *testing.T) {
	var cli struct {
		Flag string
		Sub  struct{} `cmd:""`
	}
	a := build(t, &cli)
	ctx, err := kong.Trace(a.k, nil)
	if err != nil {
		t.Fatalf("Trace failed: %v", err)
	}
	wantEq(t, ctx.Empty(), true, "no user input")
	ctx2, err := kong.Trace(a.k, []string{"--flag", "x"})
	if err != nil {
		t.Fatalf("Trace failed: %v", err)
	}
	wantEq(t, ctx2.Empty(), false, "flag counts as input")
}

// Verifies: Model Introspection and the Parse Context — the context
// (ParseError carries Context, ExitCode, Unwrap).
func TestParseErrorShape(t *testing.T) {
	var cli struct {
		Req string `required:""`
	}
	a := build(t, &cli)
	_, err := a.k.Parse(nil)
	if err == nil {
		t.Fatal("expected error")
	}
	var pe *kong.ParseError
	if !errors.As(err, &pe) {
		t.Fatalf("error is %T, want *kong.ParseError", err)
	}
	if pe.Context == nil {
		t.Fatal("ParseError.Context is nil")
	}
	wantEq(t, pe.ExitCode(), 80, "usage-error exit code")
	if pe.Unwrap() == nil {
		t.Fatal("Unwrap returned nil")
	}
	wantEq(t, pe.Unwrap().Error(), "missing flags: --req=STRING", "wrapped cause")
}

// Verifies: Model Introspection and the Parse Context — staged parsing.
func TestStagedParsing(t *testing.T) {
	var cli struct {
		Flag string `default:"dv"`
		Sub  struct{} `cmd:""`
	}
	a := build(t, &cli)
	ctx, err := kong.Trace(a.k, []string{"sub", "--flag", "x"})
	if err != nil {
		t.Fatalf("Trace failed: %v", err)
	}
	if ctx.Error != nil {
		t.Fatalf("trace error: %v", ctx.Error)
	}
	wantEq(t, cli.Flag, "", "trace does not bind values")
	if err := ctx.Resolve(); err != nil {
		t.Fatalf("Resolve failed: %v", err)
	}
	cmd, err := ctx.Apply()
	if err != nil {
		t.Fatalf("Apply failed: %v", err)
	}
	wantEq(t, cmd, "sub", "Apply returns command string")
	wantEq(t, cli.Flag, "x", "Apply binds values")
	if err := ctx.Validate(); err != nil {
		t.Fatalf("Validate failed: %v", err)
	}
}

// Verifies: Model Introspection and the Parse Context — the model (Kong
// struct fields).
func TestKongPublicFields(t *testing.T) {
	var cli struct {
		X bool
	}
	a := build(t, &cli)
	if a.k.Model == nil {
		t.Fatal("Model is nil")
	}
	wantEq(t, a.k.Model.Name, "app", "Model.Name from Name option")
	if a.k.Exit == nil {
		t.Fatal("Exit is nil")
	}
	if a.k.Stdout == nil || a.k.Stderr == nil {
		t.Fatal("writers are nil")
	}
	a.k.Printf("through model")
	wantEq(t, a.out.String(), "app: through model\n", "Stdout is the configured writer")
}
