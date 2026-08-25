package atomic

import (
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Parsing and Binding — flag syntaxes (long forms).
func TestLongFlagValueForms(t *testing.T) {
	var cli struct {
		Str string
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--str=hello"})
	wantEq(t, cli.Str, "hello", "attached form")
	mustParse(t, a, []string{"--str", "world"})
	wantEq(t, cli.Str, "world", "detached form")
}

// Verifies: Parsing and Binding — flag syntaxes (short forms).
func TestShortFlagValueForms(t *testing.T) {
	var cli struct {
		Num int `short:"n"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"-n5"})
	wantEq(t, cli.Num, 5, "attached short value")
	mustParse(t, a, []string{"-n", "7"})
	wantEq(t, cli.Num, 7, "detached short value")
}

// Verifies: Parsing and Binding — flag syntaxes (= is not a short
// separator).
func TestShortEqualsIsNotSeparator(t *testing.T) {
	var cli struct {
		Num int `short:"n"`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"-n=5"})
	wantEq(t, err.Error(), `--num: expected a valid 64 bit int but got "=5"`, "error text")
}

// Verifies: Parsing and Binding — flag syntaxes (combined shorts).
func TestCombinedShortFlags(t *testing.T) {
	var cli struct {
		Flag bool `short:"f"`
		Num  int  `short:"n"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"-fn", "7"})
	wantEq(t, cli.Flag, true, "leading bool in combination")
	wantEq(t, cli.Num, 7, "trailing value flag in combination")
}

// Verifies: Parsing and Binding — boolean flags.
func TestBooleanFlagSemantics(t *testing.T) {
	var cli struct {
		Flag bool
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--flag"})
	wantEq(t, cli.Flag, true, "bare mention")
	mustParse(t, a, []string{"--flag=false"})
	wantEq(t, cli.Flag, false, "attached false")
}

// Verifies: Parsing and Binding — boolean flags (detached value not
// consumed).
func TestBooleanDetachedValueNotConsumed(t *testing.T) {
	var cli struct {
		Flag bool
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--flag", "true"})
	wantEq(t, err.Error(), "unexpected argument true", "error text")
}

// Verifies: Parsing and Binding — boolean flags (negatable).
func TestNegatableFlag(t *testing.T) {
	var cli struct {
		Color bool `negatable:"" default:"true"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.Color, true, "default true")

	var cli2 struct {
		Color bool `negatable:"" default:"true"`
	}
	b := build(t, &cli2)
	mustParse(t, b, []string{"--no-color"})
	wantEq(t, cli2.Color, false, "negated form sets false")

	var cli3 struct {
		Color bool `negatable:"" default:"true"`
	}
	c := build(t, &cli3)
	mustParse(t, c, []string{"--color"})
	wantEq(t, cli3.Color, true, "positive form sets true")
}

// Verifies: Parsing and Binding — boolean flags (custom negation name).
func TestCustomNegationName(t *testing.T) {
	var cli struct {
		Feature bool `negatable:"no-custom-feature" default:"true"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--no-custom-feature"})
	wantEq(t, cli.Feature, false, "custom negation")
}

// Verifies: Parsing and Binding — terminator and passthrough (--).
func TestDashDashTerminator(t *testing.T) {
	var cli struct {
		Flag bool
		Args []string `arg:"" optional:""`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--", "--flag", "x"})
	wantEq(t, cli.Flag, false, "flag not parsed after --")
	wantEq(t, len(cli.Args), 2, "positional count")
	wantEq(t, cli.Args[0], "--flag", "hyphen token as positional")
	wantEq(t, cli.Args[1], "x", "second positional")
}

// Verifies: Parsing and Binding — terminator and passthrough
// (passthrough positional).
func TestPassthroughPositional(t *testing.T) {
	var cli struct {
		Flag bool
		Cmd  struct {
			Rest []string `arg:"" optional:"" passthrough:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"cmd", "one", "--flag", "two"})
	wantEq(t, cli.Flag, false, "flag captured raw, not parsed")
	wantEq(t, len(cli.Cmd.Rest), 3, "raw token count")
	wantEq(t, cli.Cmd.Rest[1], "--flag", "flag-shaped token kept verbatim")
}

// Verifies: Parsing and Binding — flag scope (ancestor flags after entry).
func TestAncestorFlagAfterCommand(t *testing.T) {
	var cli struct {
		Root string
		Sub  struct{} `cmd:""`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"sub", "--root", "x"})
	wantEq(t, cli.Root, "x", "root flag set while in subcommand")
}

// Verifies: Parsing and Binding — flag scope (descendant flag before its
// command).
func TestDescendantFlagBeforeCommandRejected(t *testing.T) {
	var cli struct {
		Sub struct {
			Local string
		} `cmd:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--local", "x", "sub"})
	wantContains(t, err.Error(), "unknown flag --local", "error text")
}

// Verifies: Parsing and Binding — command selection (leaf requirement).
func TestNonLeafSelectionErrors(t *testing.T) {
	var cli struct {
		Parent struct {
			Child struct{} `cmd:""`
			Other struct{} `cmd:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"parent"})
	wantEq(t, err.Error(), `expected one of "child", "other"`, "several children")

	var cli2 struct {
		Sub struct{} `cmd:""`
	}
	b := build(t, &cli2)
	err = parseErr(t, b, nil)
	wantEq(t, err.Error(), `expected "sub"`, "single child")
}

// Verifies: Parsing and Binding — command selection (Command strings).
func TestCommandStringForms(t *testing.T) {
	var cli struct {
		Mv struct {
			Src string `arg:""`
			Dst string `arg:""`
		} `cmd:""`
		Parent struct {
			Child struct{} `cmd:""`
		} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"mv", "a", "b"})
	wantEq(t, ctx.Command(), "mv <src> <dst>", "positional placeholders")
	ctx = mustParse(t, a, []string{"parent", "child"})
	wantEq(t, ctx.Command(), "parent child", "space-joined path")
}

// Verifies: Parsing and Binding — default commands (default:"1").
func TestDefaultCommand(t *testing.T) {
	var cli struct {
		Def struct {
			Val string `default:"dv"`
		} `cmd:"" default:"1"`
		Other struct{} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, nil)
	wantEq(t, ctx.Command(), "def", "default command selected")
	wantEq(t, cli.Def.Val, "dv", "default value applied")
}

// Verifies: Parsing and Binding — default commands (withargs).
func TestDefaultCommandWithArgs(t *testing.T) {
	var cli struct {
		Def struct {
			Arg string `arg:"" optional:""`
		} `cmd:"" default:"withargs"`
		Other struct{} `cmd:""`
	}
	a := build(t, &cli)
	ctx := mustParse(t, a, []string{"freearg"})
	wantEq(t, ctx.Command(), "def <arg>", "withargs command selected")
	wantEq(t, cli.Def.Arg, "freearg", "leading positional consumed")
}

// Verifies: Parsing and Binding — collections and counters (slices).
func TestSliceAccumulationAndSeparator(t *testing.T) {
	var cli struct {
		Nums []int `sep:","`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--nums", "1,2", "--nums", "3"})
	wantEq(t, len(cli.Nums), 3, "accumulated length")
	wantEq(t, cli.Nums[0], 1, "first")
	wantEq(t, cli.Nums[2], 3, "appended")
}

// Verifies: Parsing and Binding — collections and counters (default
// separators).
func TestDefaultSeparators(t *testing.T) {
	var cli struct {
		L []string
		M map[string]string
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--l", "a,b", "--m", "x=1;y=2"})
	wantEq(t, len(cli.L), 2, "slice split on comma by default")
	wantEq(t, cli.L[1], "b", "second element")
	wantEq(t, len(cli.M), 2, "map split on semicolon by default")
	wantEq(t, cli.M["y"], "2", "map value")
}

// Verifies: Parsing and Binding — collections and counters (maps).
func TestMapFlagCustomSeparator(t *testing.T) {
	var cli struct {
		M map[string]int `mapsep:","`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--m", "x=1,y=2"})
	wantEq(t, cli.M["x"], 1, "first pair")
	wantEq(t, cli.M["y"], 2, "second pair")
}

// Verifies: Parsing and Binding — collections and counters (counter).
func TestCounterFlag(t *testing.T) {
	var cli struct {
		Verbose int `type:"counter" short:"v"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"-vvv"})
	wantEq(t, cli.Verbose, 3, "three occurrences")
}

// Verifies: Parsing and Binding — collections and counters (pointer
// allocation).
func TestPointerFieldAllocation(t *testing.T) {
	var cli struct {
		Ptr *string
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	if cli.Ptr != nil {
		t.Fatal("pointer allocated without flag")
	}
	mustParse(t, a, []string{"--ptr", "set"})
	if cli.Ptr == nil {
		t.Fatal("pointer not allocated when flag set")
	}
	wantEq(t, *cli.Ptr, "set", "pointed-to value")
}

// Verifies: Parsing and Binding — positional completion (missing).
func TestMissingPositionalError(t *testing.T) {
	var cli struct {
		A string `arg:""`
		B string `arg:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"one"})
	wantEq(t, err.Error(), `expected "<b>"`, "error names first missing positional")
}

// Verifies: Parsing and Binding — positional completion (excess).
func TestExcessPositionalError(t *testing.T) {
	var cli struct {
		A string `arg:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"one", "two"})
	wantEq(t, err.Error(), "unexpected argument two", "error names token")
}

// Verifies: Parsing and Binding — positional completion (optional default).
func TestOptionalPositionalDefault(t *testing.T) {
	var cli struct {
		A string `arg:"" optional:"" default:"defA"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.A, "defA", "default applied to absent optional positional")
}

// Verifies: Parsing and Binding — collections and counters (escaped
// separators).
func TestSplitAndJoinEscaped(t *testing.T) {
	parts := kong.SplitEscaped(`a,b\,c`, ',')
	wantEq(t, len(parts), 2, "escaped comma not split")
	wantEq(t, parts[1], "b,c", "escape removed in result")
	joined := kong.JoinEscaped([]string{"a", "b,c"}, ',')
	wantEq(t, joined, `a,b\,c`, "join escapes embedded separator")
}
