package atomic

import (
	"testing"
)

// Verifies: Validation and Flag Groups — required and missing values.
func TestMissingRequiredFlag(t *testing.T) {
	var cli struct {
		Req string `required:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, nil)
	wantEq(t, err.Error(), "missing flags: --req=STRING", "placeholder rendering in message")
}

// Verifies: Validation and Flag Groups — required and missing values
// (multiple joined with commas).
func TestMissingMultipleRequiredFlags(t *testing.T) {
	var cli struct {
		Alpha string `required:""`
		Beta  int    `required:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, nil)
	wantContains(t, err.Error(), "missing flags: ", "prefix")
	wantContains(t, err.Error(), "--alpha=STRING", "first flag with placeholder")
	wantContains(t, err.Error(), "--beta=INT", "second flag with placeholder")
	wantContains(t, err.Error(), ", ", "comma joined")
}

// Verifies: Validation and Flag Groups — exclusive and inclusive groups
// (xor conflict).
func TestXorConflict(t *testing.T) {
	var cli struct {
		A bool `xor:"grp"`
		B bool `xor:"grp"`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--a", "--b"})
	wantEq(t, err.Error(), "--a and --b can't be used together", "error text")

	var cli2 struct {
		A bool `xor:"grp"`
		B bool `xor:"grp"`
	}
	b := build(t, &cli2)
	mustParse(t, b, []string{"--a"})
	wantEq(t, cli2.A, true, "single member accepted")
}

// Verifies: Validation and Flag Groups — exclusive and inclusive groups
// (and partial).
func TestAndGroupPartial(t *testing.T) {
	var cli struct {
		U string `and:"cred"`
		P string `and:"cred"`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--u", "x"})
	wantEq(t, err.Error(), "--u and --p must be used together", "error text")
	mustParse(t, a, []string{"--u", "x", "--p", "y"})
	wantEq(t, cli.P, "y", "full group accepted")
}

// Verifies: Validation and Flag Groups — exclusive and inclusive groups
// (required xor absent).
func TestRequiredXorAbsent(t *testing.T) {
	var cli struct {
		A bool `xor:"g" required:""`
		B bool `xor:"g" required:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, nil)
	wantEq(t, err.Error(), "missing flags: --a or --b", "alternatives joined with or")
}

// Verifies: Validation and Flag Groups — unknown input.
func TestUnknownFlag(t *testing.T) {
	var cli struct {
		Completely bool
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--zzz"})
	wantEq(t, err.Error(), "unknown flag --zzz", "error text")
}

// Verifies: Validation and Flag Groups — unknown input (flag suggestion).
func TestUnknownFlagSuggestion(t *testing.T) {
	var cli struct {
		Verbose bool
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--verbse"})
	wantEq(t, err.Error(), `unknown flag --verbse, did you mean "--verbose"?`, "suggestion appended")
}

// Verifies: Validation and Flag Groups — unknown input (command
// suggestion).
func TestUnknownCommandSuggestion(t *testing.T) {
	var cli struct {
		Sub     struct{} `cmd:""`
		Another struct{} `cmd:""`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"sib"})
	wantEq(t, err.Error(), `unexpected argument sib, did you mean "sub"?`, "suggestion appended")
}
