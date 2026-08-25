package integration

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/alecthomas/kong"
)

type wfGlobals struct {
	Debug bool `short:"d" help:"Enable debug output."`
}

type wfRmCmd struct {
	Force     bool     `short:"f" help:"Force removal."`
	Recursive bool     `short:"r" help:"Recurse into directories."`
	Paths     []string `arg:"" name:"path" help:"Paths to remove."`
}

var wfRmRan []string

func (r *wfRmCmd) Run(g *wfGlobals) error {
	wfRmRan = append([]string{}, r.Paths...)
	if g.Debug {
		wfRmRan = append(wfRmRan, "debug")
	}
	return nil
}

type wfLsCmd struct {
	Paths []string `arg:"" optional:"" name:"path" help:"Paths to list."`
}

var wfLsRan bool

func (l *wfLsCmd) Run(g *wfGlobals) error { wfLsRan = true; return nil }

// Verifies: Representative Workflows (file utility) spanning Grammar
// Construction, Parsing and Binding, and Hooks, Bindings and Command
// Execution.
func TestFileUtilityWorkflow(t *testing.T) {
	wfRmRan = nil
	wfLsRan = false
	var cli struct {
		wfGlobals
		Rm wfRmCmd `cmd:"" help:"Remove files."`
		Ls wfLsCmd `cmd:"" help:"List paths."`
	}
	a := build(t, &cli, kong.Description("A file utility."))
	ctx := mustParse(t, a, []string{"rm", "-rf", "a", "b", "-d"})
	wantEq(t, ctx.Command(), "rm <path>", "command string")
	wantEq(t, cli.Rm.Force, true, "combined short -f")
	wantEq(t, cli.Rm.Recursive, true, "combined short -r")
	wantEq(t, cli.Debug, true, "embedded global flag after command")
	if err := ctx.Run(&cli.wfGlobals); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, len(wfRmRan), 3, "run saw paths plus debug marker")
	wantEq(t, wfRmRan[0], "a", "first path")
	wantEq(t, wfRmRan[2], "debug", "bound globals visible to Run")

	ctx2 := mustParse(t, a, []string{"ls"})
	wantEq(t, ctx2.Command(), "ls", "optional positional absent")
	if err := ctx2.Run(&cli.wfGlobals); err != nil {
		t.Fatalf("ls Run failed: %v", err)
	}
	wantEq(t, wfLsRan, true, "ls dispatched")
}

// Verifies: Representative Workflows (server resolution) spanning
// Defaults, Environment Variables and Resolvers and Value Mapping.
func TestServerResolutionWorkflow(t *testing.T) {
	t.Setenv("ORACLE_WF_PORT", "9090")
	var cli struct {
		Port    int           `env:"ORACLE_WF_PORT" default:"80" help:"Listen port."`
		Timeout time.Duration `default:"5s"`
		Name    string        `default:"${app_name}"`
	}
	resolver, err := kong.JSON(strings.NewReader(`{"port": 8080}`))
	if err != nil {
		t.Fatalf("JSON resolver: %v", err)
	}
	a := build(t, &cli, kong.Vars{"app_name": "srv"}, kong.Resolvers(resolver))
	mustParse(t, a, nil)
	wantEq(t, cli.Port, 8080, "resolver beats env and default")
	wantEq(t, cli.Timeout, 5*time.Second, "duration default")
	wantEq(t, cli.Name, "srv", "interpolated default")
}

// Verifies: Grammar Construction (argument branches) with Parsing and
// Binding and Model Introspection.
func TestArgumentBranchWorkflow(t *testing.T) {
	var cli struct {
		User struct {
			Name struct {
				Name   string   `arg:""`
				Show   struct{} `cmd:""`
				Delete struct{} `cmd:""`
			} `arg:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"user", "alice", "delete"})
	wantEq(t, cli.User.Name.Name, "alice", "branch value")
	wantEq(t, ctx.Command(), "user <name> delete", "command through branch")
	wantEq(t, ctx.Selected().Name, "delete", "leaf selection")

	user := a.k.Model.Children[0]
	wantEq(t, user.Type, kong.CommandNode, "user is a command")
	branch := user.Children[0]
	wantEq(t, branch.Type, kong.ArgumentNode, "branch is an argument node")
	if branch.Argument == nil {
		t.Fatal("argument node has no Argument value")
	}
	wantEq(t, branch.Argument.Name, "name", "argument value name")

	b := build(t, &cli)
	err := parseErr(t, b, []string{"user", "alice"})
	wantEq(t, err.Error(), `expected one of "show", "delete"`, "branch requires leaf")
}

// Verifies: Grammar Construction (embed, prefix, envprefix) across
// parsing, environment resolution, and help rendering.
func TestEmbeddedPrefixWorkflow(t *testing.T) {
	type DB struct {
		Host string `env:"HOST" default:"localhost" help:"DB host."`
		Port int    `default:"5432" help:"DB port."`
	}
	newCli := func() *struct {
		DB DB `embed:"" prefix:"db-" envprefix:"DB_"`
	} {
		return &struct {
			DB DB `embed:"" prefix:"db-" envprefix:"DB_"`
		}{}
	}

	c1 := newCli()
	a := build(t, c1)
	mustParse(t, a, []string{"--db-host", "remote"})
	wantEq(t, c1.DB.Host, "remote", "prefixed flag")
	wantEq(t, c1.DB.Port, 5432, "embedded default")

	c2 := newCli()
	b := build(t, c2)
	err := parseErr(t, b, []string{"--host", "x"})
	wantContains(t, err.Error(), "unknown flag --host", "unprefixed rejected")

	t.Setenv("DB_HOST", "envhost")
	c3 := newCli()
	c := build(t, c3)
	mustParse(t, c, nil)
	wantEq(t, c3.DB.Host, "envhost", "envprefix composition")

	c4 := newCli()
	d := build(t, c4)
	d.k.Parse([]string{"--help"})
	wantContains(t, d.out.String(), "--db-host", "prefixed name in help")
	wantContains(t, d.out.String(), "($DB_HOST)", "prefixed env in help")
}

// Verifies: Grammar Construction (Plugins) with parsing and help.
func TestPluginsWorkflow(t *testing.T) {
	type AuthPlugin struct {
		Token string `help:"Auth token." default:"none"`
	}
	var cli struct {
		Base string `help:"Base flag."`
		kong.Plugins
	}
	p := &AuthPlugin{}
	cli.Plugins = kong.Plugins{p}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	wantContains(t, a.out.String(), "--token", "plugin flag in help")

	var cli2 struct {
		Base string `help:"Base flag."`
		kong.Plugins
	}
	p2 := &AuthPlugin{}
	cli2.Plugins = kong.Plugins{p2}
	b := build(t, &cli2)
	mustParse(t, b, []string{"--token", "abc", "--base", "z"})
	wantEq(t, p2.Token, "abc", "plugin flag bound to plugin struct")
	wantEq(t, cli2.Base, "z", "host flag still bound")
}

// Verifies: Grammar Construction (DynamicCommand) with execution and
// help.
func TestDynamicCommandWorkflow(t *testing.T) {
	type DynCmd struct {
		Val  string `help:"Value."`
		ran  bool
	}
	var cli struct {
		Base struct{} `cmd:"" help:"Base."`
	}
	dyn := &DynCmd{}
	a := build(t, &cli, kong.DynamicCommand("added", "Added dynamically.", "", dyn))
	a.k.Parse([]string{"--help"})
	wantContains(t, a.out.String(), "added", "dynamic command in help")
	wantContains(t, a.out.String(), "Added dynamically.", "dynamic help text")

	b := build(t, &cli, kong.DynamicCommand("added", "Added dynamically.", "", dyn))
	ctx := mustParse(t, b, []string{"added", "--val", "v"})
	wantEq(t, ctx.Command(), "added", "dynamic selection")
	wantEq(t, dyn.Val, "v", "dynamic flag bound")
	names := []string{}
	for _, c := range b.k.Model.Children {
		names = append(names, c.Name)
	}
	wantEq(t, strings.Join(names, ","), "base,added", "dynamic command in model")
}

// Verifies: Value Mapping (ConfigFlag) with Defaults, Environment
// Variables and Resolvers precedence.
func TestConfigFlagWorkflow(t *testing.T) {
	dir := t.TempDir()
	file := filepath.Join(dir, "conf.json")
	if err := os.WriteFile(file, []byte(`{"port": 7070, "name": "conf"}`), 0o644); err != nil {
		t.Fatal(err)
	}
	var cli struct {
		Port   int             `default:"80"`
		Name   string          `default:"anon"`
		Config kong.ConfigFlag `name:"config"`
	}
	a := build(t, &cli, kong.Configuration(kong.JSON))
	mustParse(t, a, []string{"--config", file, "--name", "cli"})
	wantEq(t, cli.Port, 7070, "config value applied")
	wantEq(t, cli.Name, "cli", "explicit flag beats config")
}

// Verifies: Hooks, Bindings and Command Execution (hooks observe the
// resolution pipeline).
func TestHooksObserveResolution(t *testing.T) {
	hookSeen = nil
	var cli struct {
		Flag hookProbe `default:"dv"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	want := []string{"BeforeReset", "BeforeResolve", "BeforeApply", "AfterApply"}
	if len(hookSeen) != len(want) {
		t.Fatalf("hook sequence %v, want %v", hookSeen, want)
	}
	for i := range want {
		wantEq(t, hookSeen[i], want[i], "hook order")
	}
	wantEq(t, string(cli.Flag), "dv", "default applied to hook-bearing flag")
}

type hookProbe string

var hookSeen []string

func (h hookProbe) BeforeReset() error   { hookSeen = append(hookSeen, "BeforeReset"); return nil }
func (h hookProbe) BeforeResolve() error { hookSeen = append(hookSeen, "BeforeResolve"); return nil }
func (h hookProbe) BeforeApply() error   { hookSeen = append(hookSeen, "BeforeApply"); return nil }
func (h hookProbe) AfterApply() error    { hookSeen = append(hookSeen, "AfterApply"); return nil }

// Verifies: Parsing and Binding (passthrough) delivered into command
// execution.
func TestPassthroughIntoRun(t *testing.T) {
	execSeen = nil
	var cli struct {
		Exec execCmd `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"exec", "prog", "--flag", "arg"})
	if err := ctx.Run(); err != nil {
		t.Fatalf("Run failed: %v", err)
	}
	wantEq(t, len(execSeen), 3, "all raw tokens delivered")
	wantEq(t, execSeen[1], "--flag", "flag token untouched")
}

type execCmd struct {
	Args []string `arg:"" optional:"" passthrough:""`
}

var execSeen []string

func (e *execCmd) Run() error { execSeen = append([]string{}, e.Args...); return nil }
