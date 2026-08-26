package integration

import (
	"errors"
	"reflect"
	"strconv"
	"strings"
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Help Rendering and Diagnostics (usage on error) with the
// ParseError contract from Model Introspection and the Parse Context.
func TestUsageOnErrorFullFlow(t *testing.T) {
	var cli struct {
		Req string `required:"" help:"Required."`
		Sub struct{} `cmd:"" help:"Sub."`
	}
	a := build(t, &cli, kong.UsageOnError())
	_, err := a.k.Parse(nil)
	if err == nil {
		t.Fatal("expected parse failure")
	}
	var pe *kong.ParseError
	if !errors.As(err, &pe) {
		t.Fatalf("error type %T", err)
	}
	wantEq(t, pe.ExitCode(), 80, "usage error code")
	a.k.FatalIfErrorf(err)
	stdout := a.out.String()
	wantContains(t, stdout, "Usage: app --req=STRING <command>", "usage line includes required flag")
	wantContains(t, stdout, "--req=STRING", "flags rendered")
	wantContains(t, stdout, "sub", "commands rendered")
	wantContains(t, a.errw.String(), "app: error: ", "error prefix on stderr")
	if len(a.exits) == 0 || a.exits[0] != 80 {
		t.Fatalf("exit codes = %v, want [80]", a.exits)
	}
}

// Verifies: Model Introspection and the Parse Context (ParseError.Context
// drives PrintUsage after a failure).
func TestParseErrorContextPrintsUsage(t *testing.T) {
	var cli struct {
		Req string `required:""`
	}
	a := build(t, &cli)
	_, err := a.k.Parse(nil)
	var pe *kong.ParseError
	if !errors.As(err, &pe) {
		t.Fatalf("error type %T", err)
	}
	if err := pe.Context.PrintUsage(false); err != nil {
		t.Fatalf("PrintUsage from error context failed: %v", err)
	}
	wantContains(t, a.out.String(), "Usage: app", "usage from failed context")
	wantContains(t, a.out.String(), "--req=STRING", "flag row present")
}

// Verifies: Value Mapping (custom mappers) composed with Defaults and
// enum validation in one grammar.
func TestMapperWithDefaultsAndEnums(t *testing.T) {
	type pair struct{ A, B int }
	mapper := kong.MapperFunc(func(ctx *kong.DecodeContext, target reflect.Value) error {
		var s string
		if err := ctx.Scan.PopValueInto("pair", &s); err != nil {
			return err
		}
		parts := strings.SplitN(s, ":", 2)
		a, err := strconv.Atoi(parts[0])
		if err != nil {
			return err
		}
		b, err := strconv.Atoi(parts[1])
		if err != nil {
			return err
		}
		target.Set(reflect.ValueOf(pair{A: a, B: b}))
		return nil
	})
	var cli struct {
		P    pair   `type:"pair" default:"1:2"`
		Mode string `enum:"x,y" default:"x"`
	}
	a := build(t, &cli, kong.NamedMapper("pair", mapper))
	mustParse(t, a, nil)
	wantEq(t, cli.P, pair{1, 2}, "default text decoded through custom mapper")
	mustParse(t, a, []string{"--p", "3:4", "--mode", "y"})
	wantEq(t, cli.P, pair{3, 4}, "explicit value decoded")
	wantEq(t, cli.Mode, "y", "enum companion")
}

// Verifies: Parsing and Binding (default commands) with Context.Empty and
// execution.
func TestDefaultCommandPipeline(t *testing.T) {
	defRan = false
	var cli struct {
		Def   defCmd   `cmd:"" default:"1" help:"Default."`
		Other struct{} `cmd:"" help:"Other."`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, nil)
	wantEq(t, ctx.Command(), "def", "default command selected on empty argv")
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, defRan, true, "default command executed")
}

type defCmd struct{}

var defRan bool

func (d *defCmd) Run() error { defRan = true; return nil }

// Verifies: Validation and Flag Groups (xor/and) rendered consistently in
// help and enforced at parse (Cross-View Invariants 8).
func TestGroupConstraintsAcrossViews(t *testing.T) {
	newCli := func() *struct {
		Json bool `xor:"fmt" help:"JSON output."`
		Yaml bool `xor:"fmt" help:"YAML output."`
		User string `and:"cred" help:"User."`
		Pass string `and:"cred" help:"Pass."`
	} {
		return &struct {
			Json bool `xor:"fmt" help:"JSON output."`
			Yaml bool `xor:"fmt" help:"YAML output."`
			User string `and:"cred" help:"User."`
			Pass string `and:"cred" help:"Pass."`
		}{}
	}

	c1 := newCli()
	a := build(t, c1)
	err := parseErr(t, a, []string{"--json", "--yaml"})
	wantEq(t, err.Error(), "--json and --yaml can't be used together", "xor enforced")

	c2 := newCli()
	b := build(t, c2)
	err = parseErr(t, b, []string{"--user", "u"})
	wantEq(t, err.Error(), "--user and --pass must be used together", "and enforced")

	c3 := newCli()
	c := build(t, c3)
	mustParse(t, c, []string{"--json", "--user", "u", "--pass", "p"})
	wantEq(t, c3.Json, true, "satisfying combination accepted")

	// The same flag names appear in help and in the model's Xor/And
	// metadata.
	c4 := newCli()
	d := build(t, c4)
	d.k.Parse([]string{"--help"})
	wantContains(t, d.out.String(), "--json", "xor member in help")
	for _, f := range d.k.Model.Flags {
		switch f.Name {
		case "json", "yaml":
			wantEq(t, len(f.Xor), 1, "xor group recorded")
			wantEq(t, f.Xor[0], "fmt", "xor group name")
		case "user", "pass":
			wantEq(t, len(f.And), 1, "and group recorded")
			wantEq(t, f.And[0], "cred", "and group name")
		}
	}
}

// Verifies: Hooks, Bindings and Command Execution (providers and parent
// struct bindings along the run chain).
func TestRunChainWithProviderBindings(t *testing.T) {
	chainSeen = nil
	var cli struct {
		Parent chainParent `cmd:""`
	}
	a := build(t, &cli, kong.BindToProvider(func() (*chainDep, error) {
		return &chainDep{Tag: "provided"}, nil
	}))
	ctx := mustParse(t, a, []string{"parent", "--label", "P", "child"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, len(chainSeen), 2, "both Run methods executed")
	wantEq(t, chainSeen[0], "child:P:provided", "child saw parent struct and provided dep")
	wantEq(t, chainSeen[1], "parent:P", "parent ran after child")
}

type chainDep struct{ Tag string }

var chainSeen []string

type chainParent struct {
	Label string      `help:"Label."`
	Child chainChild `cmd:""`
}

func (p *chainParent) Run() error {
	chainSeen = append(chainSeen, "parent:"+p.Label)
	return nil
}

type chainChild struct{}

func (c *chainChild) Run(p *chainParent, d *chainDep) error {
	chainSeen = append(chainSeen, "child:"+p.Label+":"+d.Tag)
	return nil
}

// Verifies: Value Mapping (VersionFlag) leaves the rest of the grammar
// untouched (Cross-View Invariants 6).
func TestVersionFlagPipeline(t *testing.T) {
	var cli struct {
		Version kong.VersionFlag `help:"Show version."`
		Name    string           `default:"anon"`
	}
	a := build(t, &cli, kong.Vars{"version": "9.9"})
	a.k.Parse([]string{"--version"})
	wantEq(t, a.out.String(), "9.9\n", "version printed")
	if len(a.exits) == 0 || a.exits[0] != 0 {
		t.Fatalf("exits = %v, want [0]", a.exits)
	}

	var cli2 struct {
		Version kong.VersionFlag `help:"Show version."`
		Name    string           `default:"anon"`
	}
	b := build(t, &cli2, kong.Vars{"version": "9.9"})
	mustParse(t, b, []string{"--name", "x"})
	wantEq(t, cli2.Name, "x", "grammar works without version flag")
	wantEq(t, b.out.String(), "", "no version output when flag absent")
}

// Verifies: Help Rendering and Diagnostics (alternate layouts) driven by
// one grammar (Cross-View Invariants 1).
func TestAlternateHelpLayoutsSameGrammar(t *testing.T) {
	type grammar struct {
		Flag string `help:"A flag."`
		Sub  struct {
			Inner struct{} `cmd:"" help:"Inner."`
		} `cmd:"" help:"Sub."`
	}

	g1 := &grammar{}
	def := build(t, g1)
	def.k.Parse([]string{"--help"})
	defaultOut := def.out.String()
	wantContains(t, defaultOut, "sub inner", "default layout expands nested command")

	g2 := &grammar{}
	tree := build(t, g2, kong.ConfigureHelp(kong.HelpOptions{Tree: true}))
	tree.k.Parse([]string{"--help"})
	treeOut := tree.out.String()
	if strings.Contains(treeOut, "sub inner") {
		t.Fatalf("tree layout used flat command chains:\n%s", treeOut)
	}
	wantContains(t, treeOut, "inner", "tree lists nested command")

	g3 := &grammar{}
	compact := build(t, g3, kong.ConfigureHelp(kong.HelpOptions{Compact: true}))
	compact.k.Parse([]string{"--help"})
	wantContains(t, compact.out.String(), "--flag", "compact keeps flags")
}

// Verifies: Parsing and Binding (scope) and Grammar Construction across a
// deep tree: each level's flags become available exactly at that level.
func TestFlagScopeAcrossTree(t *testing.T) {
	newCli := func() *struct {
		Top   string
		First struct {
			Mid    string
			Second struct {
				Bot string
			} `cmd:""`
		} `cmd:""`
	} {
		return &struct {
			Top   string
			First struct {
				Mid    string
				Second struct {
					Bot string
				} `cmd:""`
			} `cmd:""`
		}{}
	}

	c1 := newCli()
	a := build(t, c1)
	mustParse(t, a, []string{"first", "second", "--top", "t", "--mid", "m", "--bot", "b"})
	wantEq(t, c1.Top, "t", "root flag at leaf")
	wantEq(t, c1.First.Mid, "m", "mid flag at leaf")
	wantEq(t, c1.First.Second.Bot, "b", "leaf flag at leaf")

	c2 := newCli()
	b := build(t, c2)
	err := parseErr(t, b, []string{"first", "--bot", "b", "second"})
	wantContains(t, err.Error(), "unknown flag --bot", "leaf flag rejected before leaf")

	c3 := newCli()
	c := build(t, c3)
	mustParse(t, c, []string{"first", "--mid", "m", "second"})
	wantEq(t, c3.First.Mid, "m", "mid flag accepted at mid level")
}
