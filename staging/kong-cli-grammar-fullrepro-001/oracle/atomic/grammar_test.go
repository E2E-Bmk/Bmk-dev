package atomic

import (
	"strings"
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Grammar Construction — entry points (non-struct rejection).
func TestNewRejectsNonStructPointer(t *testing.T) {
	v := 3
	_, err := kong.New(&v, kong.Name("app"))
	if err == nil {
		t.Fatal("New accepted a non-struct pointer")
	}
	wantEq(t, err.Error(), "expected a pointer to a struct but got *int", "error text")
}

// Verifies: Grammar Construction — entry points (Must panics).
func TestMustPanicsOnGrammarError(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("Must did not panic on invalid grammar")
		}
	}()
	v := 3
	kong.Must(&v, kong.Name("app"))
}

// Verifies: Grammar Construction — field classification.
func TestFieldClassification(t *testing.T) {
	var cli struct {
		Flag string
		Sub  struct {
			Pos string `arg:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"--flag", "f", "sub", "p"})
	wantEq(t, cli.Flag, "f", "flag bound")
	wantEq(t, cli.Sub.Pos, "p", "positional bound")
	wantEq(t, ctx.Command(), "sub <pos>", "command string")
}

// Verifies: Grammar Construction — field classification (anonymous embed).
func TestAnonymousEmbedFlattened(t *testing.T) {
	type Common struct {
		Verbose bool
	}
	var cli struct {
		Common
		Other string
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--verbose", "--other", "x"})
	if !cli.Verbose {
		t.Fatal("embedded flag not flattened into parent")
	}
}

// Verifies: Grammar Construction — field classification (Plugins).
func TestPluginsContributeFlags(t *testing.T) {
	type PluginFlags struct {
		Extra string `default:"exdef"`
	}
	var cli struct {
		Base string
		kong.Plugins
	}
	p := &PluginFlags{}
	cli.Plugins = kong.Plugins{p}
	a := build(t, &cli)
	mustParse(t, a, []string{"--extra", "ex", "--base", "b"})
	wantEq(t, p.Extra, "ex", "plugin flag bound")
	wantEq(t, cli.Base, "b", "base flag bound")
}

// Verifies: Grammar Construction — naming (case-boundary hyphenation).
func TestKebabCaseNaming(t *testing.T) {
	var cli struct {
		SomeLongFlag string
		HTTPPort     int
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--some-long-flag", "v", "--http-port", "8080"})
	wantEq(t, cli.SomeLongFlag, "v", "kebab flag")
	wantEq(t, cli.HTTPPort, 8080, "initialism flag")
}

// Verifies: Grammar Construction — naming (name tag override).
func TestNameTagOverride(t *testing.T) {
	var cli struct {
		Field string `name:"renamed"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--renamed", "x"})
	wantEq(t, cli.Field, "x", "renamed flag bound")
	b := build(t, &cli)
	err := parseErr(t, b, []string{"--field", "x"})
	wantContains(t, err.Error(), "unknown flag --field", "original name rejected")
}

// Verifies: Grammar Construction — naming (FlagNamer option).
func TestFlagNamerOption(t *testing.T) {
	var cli struct {
		SomeFlag string
	}
	a := build(t, &cli, kong.FlagNamer(func(name string) string { return strings.ToLower(name) }))
	mustParse(t, a, []string{"--someflag", "v"})
	wantEq(t, cli.SomeFlag, "v", "namer applied")
}

// Verifies: Grammar Construction — naming (aliases).
func TestCommandAliasParses(t *testing.T) {
	var cli struct {
		Sub struct {
			N string
		} `cmd:"" aliases:"s"`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"s", "--n", "x"})
	wantEq(t, ctx.Command(), "sub", "alias resolves to primary name")
	wantEq(t, cli.Sub.N, "x", "flag under alias")
}

// Verifies: Grammar Construction — structure tags (duplicate short).
func TestDuplicateShortFlagError(t *testing.T) {
	var cli struct {
		A bool `short:"x"`
		B bool `short:"x"`
	}
	_, err := kong.New(&cli, kong.Name("app"))
	if err == nil {
		t.Fatal("duplicate short flags accepted")
	}
	wantContains(t, err.Error(), "duplicate short flag -x", "error text")
}

// Verifies: Grammar Construction — commands and argument branches.
func TestArgumentBranch(t *testing.T) {
	var cli struct {
		User struct {
			Name struct {
				Name string   `arg:""`
				Show struct{} `cmd:""`
			} `arg:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"user", "alice", "show"})
	wantEq(t, cli.User.Name.Name, "alice", "branch value bound")
	wantEq(t, ctx.Command(), "user <name> show", "command string through branch")
}

// Verifies: Grammar Construction — commands and argument branches
// (missing same-named child).
func TestArgumentBranchMissingChildError(t *testing.T) {
	var cli struct {
		User struct {
			Name struct {
				Show struct{} `cmd:""`
			} `arg:""`
		} `cmd:""`
	}
	_, err := kong.New(&cli, kong.Name("app"))
	if err == nil {
		t.Fatal("branch without same-named child accepted")
	}
	wantContains(t, err.Error(),
		`positional branch must have at least one child positional argument named "name"`,
		"error text")
}

// Verifies: Grammar Construction — positional ordering.
func TestRequiredAfterOptionalPositionalError(t *testing.T) {
	var cli struct {
		A string `arg:"" optional:""`
		B string `arg:""`
	}
	_, err := kong.New(&cli, kong.Name("app"))
	if err == nil {
		t.Fatal("required-after-optional accepted")
	}
	wantContains(t, err.Error(), `required "b" cannot come after optional "a"`, "error text")
}

// Verifies: Grammar Construction — dynamic commands.
func TestDynamicCommandOption(t *testing.T) {
	var cli struct {
		Base struct{} `cmd:""`
	}
	dyn := &dynCmd{}
	a := build(t, &cli, kong.DynamicCommand("dyn", "Dynamic.", "", dyn))
	ctx := mustParse(t, a, []string{"dyn", "--val", "v"})
	wantEq(t, ctx.Command(), "dyn", "dynamic command selected")
	wantEq(t, dyn.Val, "v", "dynamic flag bound")
	if err := ctx.Run(); err != nil {
		t.Fatalf("dynamic Run failed: %v", err)
	}
	if !dyn.ran {
		t.Fatal("dynamic Run method not invoked")
	}
}

type dynCmd struct {
	Val string
	ran bool
}

func (d *dynCmd) Run() error { d.ran = true; return nil }

// Verifies: Grammar Construction — dynamic commands and the automatic help
// flag.
func TestAutomaticHelpFlag(t *testing.T) {
	var cli struct {
		X bool
	}
	a := build(t, &cli)
	flags := a.k.Model.Flags
	if len(flags) == 0 {
		t.Fatal("model has no flags")
	}
	help := flags[0]
	wantEq(t, help.Name, "help", "help flag first in model")
	wantEq(t, help.Short, 'h', "help short form")
	wantEq(t, help.Help, "Show context-sensitive help.", "help text")
}

// Verifies: Grammar Construction — the automatic help flag (NoDefaultHelp).
func TestNoDefaultHelp(t *testing.T) {
	var cli struct {
		X bool
	}
	a := build(t, &cli, kong.NoDefaultHelp())
	err := parseErr(t, a, []string{"--help"})
	wantContains(t, err.Error(), "unknown flag --help", "help flag removed")
}

// Verifies: Grammar Construction — grammar-level validation at build time
// (enum).
func TestEnumRequiresDefaultOrRequired(t *testing.T) {
	var cli struct {
		Mode string `enum:"a,b"`
	}
	_, err := kong.New(&cli, kong.Name("app"))
	if err == nil {
		t.Fatal("bare enum accepted")
	}
	wantContains(t, err.Error(),
		"enum value is only valid if it is either required or has a valid default value",
		"error text")
}

// Verifies: Grammar Construction — grammar-level validation at build time
// (negatable).
func TestNegatableNonBoolError(t *testing.T) {
	var cli struct {
		Neg string `negatable:""`
	}
	_, err := kong.New(&cli, kong.Name("app"))
	if err == nil {
		t.Fatal("negatable string accepted")
	}
	wantContains(t, err.Error(), "negatable can only be set on booleans", "error text")
}

// Verifies: Grammar Construction — grammar-level validation at build time
// (undefined variable).
func TestUndefinedInterpolationVarError(t *testing.T) {
	var cli struct {
		A string `default:"${undeclared}"`
	}
	_, err := kong.New(&cli, kong.Name("app"))
	if err == nil {
		t.Fatal("undefined variable accepted")
	}
	wantEq(t, err.Error(), `default value for --a="": undefined variable ${undeclared}`, "error text")
}

