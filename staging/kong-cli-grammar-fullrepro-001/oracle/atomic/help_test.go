package atomic

import (
	"strings"
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Help Rendering and Diagnostics — default layout.
func TestHelpDefaultLayout(t *testing.T) {
	var cli struct {
		Verbose bool `short:"v" help:"Enable verbose mode."`
		Level   int  `help:"Level." default:"2" env:"LEVEL"`
		Sub     struct {
			Thing string `arg:"" help:"The thing."`
		} `cmd:"" help:"Do the sub thing."`
	}
	a := build(t, &cli, kong.Description("An app."))
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	wantContains(t, out, "Usage: app <command> [flags]", "usage line")
	wantContains(t, out, "An app.", "description paragraph")
	wantContains(t, out, "-h, --help", "help flag row")
	wantContains(t, out, "Show context-sensitive help.", "help flag text")
	wantContains(t, out, "-v, --verbose", "short and long form")
	wantContains(t, out, "Enable verbose mode.", "flag help text")
	wantContains(t, out, "sub <thing> [flags]", "command summary")
	wantContains(t, out, "Do the sub thing.", "command help")
	wantContains(t, out, `Run "app <command> --help" for more information on a command.`, "footer")
}

// Verifies: Help Rendering and Diagnostics — default layout (exit 0 on
// stdout).
func TestHelpExitsZero(t *testing.T) {
	var cli struct {
		X bool
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	if len(a.exits) == 0 || a.exits[0] != 0 {
		t.Fatalf("exit codes = %v, want [0]", a.exits)
	}
	if a.out.Len() == 0 {
		t.Fatal("help not written to stdout")
	}
	wantEq(t, a.errw.Len(), 0, "nothing on stderr")
}

// Verifies: Help Rendering and Diagnostics — default layout
// (placeholders).
func TestHelpPlaceholders(t *testing.T) {
	var cli struct {
		Req   string            `required:"" help:"Required."`
		Level int               `default:"2" help:"Level."`
		Out   string            `placeholder:"FILE" help:"Output."`
		List  []string          `help:"Items."`
		M     map[string]string `help:"Pairs."`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	wantContains(t, out, "--req=STRING", "type placeholder")
	wantContains(t, out, "--level=2", "default as placeholder")
	wantContains(t, out, "--out=FILE", "placeholder tag override")
	wantContains(t, out, "--list=LIST,...", "slice placeholder")
	wantContains(t, out, "--m=KEY=VALUE;...", "map placeholder")
}

// Verifies: Help Rendering and Diagnostics — default layout (env
// annotation).
func TestHelpEnvAnnotation(t *testing.T) {
	var cli struct {
		Level int `help:"Level." env:"LEVEL"`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	wantContains(t, a.out.String(), "($LEVEL)", "environment annotation")
}

// Verifies: Help Rendering and Diagnostics — groups, aliases, and hiding
// (hidden entries).
func TestHelpHiddenOmitted(t *testing.T) {
	var cli struct {
		Secret  bool     `hidden:""`
		Visible bool     `help:"Visible."`
		Hid     struct{} `cmd:"" hidden:""`
		Shown   struct{} `cmd:"" help:"Shown."`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	if strings.Contains(out, "secret") || strings.Contains(out, "hid ") {
		t.Fatalf("hidden entries appear in help:\n%s", out)
	}
	wantContains(t, out, "--visible", "visible flag present")

	var cli2 struct {
		Secret bool `hidden:""`
	}
	b := build(t, &cli2)
	mustParse(t, b, []string{"--secret"})
	wantEq(t, cli2.Secret, true, "hidden flag still parseable")
}

// Verifies: Help Rendering and Diagnostics — groups, aliases, and hiding
// (flag groups).
func TestHelpFlagGroups(t *testing.T) {
	var cli struct {
		Alpha bool `help:"Alpha." group:"Main"`
		Beta  bool `help:"Beta." group:"Main"`
		Gamma bool `help:"Gamma."`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	wantContains(t, out, "Main", "group title")
	if strings.Index(out, "--gamma") > strings.Index(out, "Main") {
		t.Fatalf("ungrouped flag listed after group heading:\n%s", out)
	}
}

// Verifies: Help Rendering and Diagnostics — groups, aliases, and hiding
// (explicit command groups).
func TestHelpExplicitCommandGroups(t *testing.T) {
	var cli struct {
		One struct{} `cmd:"" group:"g1" help:"One."`
		Zed struct{} `cmd:"" help:"Zed."`
	}
	a := build(t, &cli, kong.ExplicitGroups([]kong.Group{
		{Key: "g1", Title: "Group One:", Description: "About group one."},
	}))
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	wantContains(t, out, "Group One:", "group title")
	wantContains(t, out, "About group one.", "group description")
}

// Verifies: Help Rendering and Diagnostics — alternate layouts (compact
// aliases).
func TestHelpCompactAliases(t *testing.T) {
	var cli struct {
		Sub struct{} `cmd:"" help:"Sub." aliases:"s,su"`
	}
	a := build(t, &cli, kong.ConfigureHelp(kong.HelpOptions{Compact: true}))
	a.k.Parse([]string{"--help"})
	wantContains(t, a.out.String(), "sub (s,su)", "aliases in parentheses")
}

// Verifies: Help Rendering and Diagnostics — alternate layouts (tree).
func TestHelpTreeLayout(t *testing.T) {
	var cli struct {
		Sub struct {
			Inner struct{} `cmd:"" help:"Inner."`
		} `cmd:"" help:"Sub."`
	}
	a := build(t, &cli, kong.ConfigureHelp(kong.HelpOptions{Tree: true}))
	a.k.Parse([]string{"--help"})
	out := a.out.String()
	wantContains(t, out, "sub", "parent present")
	wantContains(t, out, "  inner", "child indented beneath parent")
	if strings.Contains(out, "sub inner") {
		t.Fatalf("tree layout used flat summaries:\n%s", out)
	}
}

// Verifies: Help Rendering and Diagnostics — context-sensitive help.
func TestContextSensitiveHelp(t *testing.T) {
	var cli struct {
		Global bool `help:"Global flag."`
		Sub    struct {
			Local string `help:"Local flag."`
			Arg   string `arg:"" help:"The arg."`
		} `cmd:"" help:"Sub."`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"sub", "--help"})
	out := a.out.String()
	wantContains(t, out, "Usage: app sub <arg> [flags]", "sub usage line")
	wantContains(t, out, "Arguments:", "arguments section")
	wantContains(t, out, "<arg>", "positional listed")
	wantContains(t, out, "--local=STRING", "local flag listed")
	wantContains(t, out, "--global", "ancestor flag listed")
}

type helpedCmd struct{}

func (h *helpedCmd) Help() string { return "Extended help text here." }

// Verifies: Help Rendering and Diagnostics — context-sensitive help
// (Help() detail).
func TestHelpProviderDetail(t *testing.T) {
	var cli struct {
		Sub helpedCmd `cmd:"" help:"Short."`
	}
	a := build(t, &cli)
	a.k.Parse([]string{"sub", "--help"})
	wantContains(t, a.out.String(), "Extended help text here.", "detail rendered")
	b := build(t, &cli)
	b.k.Parse([]string{"--help"})
	if strings.Contains(b.out.String(), "Extended help text here.") {
		t.Fatal("detail leaked into root help")
	}
}

// Verifies: Help Rendering and Diagnostics — usage on error.
func TestUsageOnError(t *testing.T) {
	var cli struct {
		Req string `required:"" help:"Required."`
	}
	a := build(t, &cli, kong.UsageOnError())
	_, err := a.k.Parse(nil)
	a.k.FatalIfErrorf(err)
	wantContains(t, a.out.String(), "Usage: app --req=STRING", "usage on stdout")
	wantContains(t, a.out.String(), "--req=STRING", "flag listing")
	wantContains(t, a.errw.String(), "app: error: missing flags: --req=STRING", "error on stderr")
	if len(a.exits) == 0 || a.exits[0] != 80 {
		t.Fatalf("exit codes = %v, want [80]", a.exits)
	}
}

// Verifies: Help Rendering and Diagnostics — usage on error (short form).
func TestShortUsageOnError(t *testing.T) {
	var cli struct {
		Req string `required:""`
	}
	a := build(t, &cli, kong.ShortUsageOnError())
	_, err := a.k.Parse(nil)
	a.k.FatalIfErrorf(err)
	wantContains(t, a.out.String(), "Usage: app --req=STRING", "summary usage")
	if strings.Contains(a.out.String(), "Flags:") {
		t.Fatalf("short usage rendered full flag listing:\n%s", a.out.String())
	}
	wantContains(t, a.errw.String(), "app: error: missing flags: --req=STRING", "error on stderr")
}

// Verifies: Help Rendering and Diagnostics — message helpers.
func TestMessageHelpers(t *testing.T) {
	var cli struct{}
	a := build(t, &cli)
	a.k.Printf("info %d", 1)
	wantEq(t, a.out.String(), "app: info 1\n", "Printf prefix and stream")
	a.k.Errorf("bad %s", "thing")
	wantEq(t, a.errw.String(), "app: error: bad thing\n", "Errorf prefix and stream")
	a.k.Fatalf("fatal")
	wantContains(t, a.errw.String(), "app: error: fatal\n", "Fatalf message")
	if len(a.exits) == 0 || a.exits[0] != 1 {
		t.Fatalf("exit codes = %v, want [1]", a.exits)
	}
}

// Verifies: Help Rendering and Diagnostics — usage on error
// (PrintUsage).
func TestPrintUsage(t *testing.T) {
	var cli struct {
		Flag string
		Sub  struct{} `cmd:""`
	}
	a := build(t, &cli)
	ctx, err := kong.Trace(a.k, []string{"sub"})
	if err != nil {
		t.Fatalf("Trace failed: %v", err)
	}
	if err := ctx.PrintUsage(true); err != nil {
		t.Fatalf("PrintUsage(true) failed: %v", err)
	}
	summary := a.out.String()
	wantContains(t, summary, "Usage: app sub [flags]", "summary usage line")
	wantContains(t, summary, `Run "app sub --help" for more information.`, "summary footer")
	a.out.Reset()
	if err := ctx.PrintUsage(false); err != nil {
		t.Fatalf("PrintUsage(false) failed: %v", err)
	}
	wantContains(t, a.out.String(), "Flags:", "full form lists flags")
	wantContains(t, a.out.String(), "--flag=STRING", "flag row present")
}
