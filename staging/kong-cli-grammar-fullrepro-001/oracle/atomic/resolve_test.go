package atomic

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/alecthomas/kong"
)

// Verifies: Defaults, Environment Variables and Resolvers — defaults.
func TestDefaultTag(t *testing.T) {
	var cli struct {
		Name string `default:"anon"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.Name, "anon", "default applied")
	mustParse(t, a, []string{"--name", "given"})
	wantEq(t, cli.Name, "given", "explicit value wins")
}

// Verifies: Defaults, Environment Variables and Resolvers — defaults
// (ApplyDefaults function).
func TestApplyDefaultsFunction(t *testing.T) {
	var target struct {
		N int    `default:"42"`
		S string `default:"x"`
	}
	if err := kong.ApplyDefaults(&target); err != nil {
		t.Fatalf("ApplyDefaults failed: %v", err)
	}
	wantEq(t, target.N, 42, "int default")
	wantEq(t, target.S, "x", "string default")
}

// Verifies: Defaults, Environment Variables and Resolvers — environment
// variables (env beats default, command line beats env).
func TestEnvTagPrecedence(t *testing.T) {
	t.Setenv("ORACLE_PORT", "9999")
	var cli struct {
		Port int `env:"ORACLE_PORT" default:"80"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.Port, 9999, "env beats default")
	mustParse(t, a, []string{"--port", "1"})
	wantEq(t, cli.Port, 1, "command line beats env")
}

// Verifies: Defaults, Environment Variables and Resolvers — environment
// variables (multi-variable fallback).
func TestEnvMultiFallback(t *testing.T) {
	t.Setenv("ORACLE_B", "fromB")
	os.Unsetenv("ORACLE_A_UNSET")
	var cli struct {
		V string `env:"ORACLE_A_UNSET,ORACLE_B"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.V, "fromB", "first set variable wins")
}

// Verifies: Defaults, Environment Variables and Resolvers — environment
// variables (DefaultEnvars).
func TestDefaultEnvarsOption(t *testing.T) {
	t.Setenv("MYAPP_SOME_FLAG", "fromenv")
	var cli struct {
		SomeFlag string
	}
	a := build(t, &cli, kong.DefaultEnvars("MYAPP"))
	mustParse(t, a, nil)
	wantEq(t, cli.SomeFlag, "fromenv", "derived envar read")
}

// Verifies: Defaults, Environment Variables and Resolvers — environment
// variables (envprefix composition).
func TestEnvPrefixComposition(t *testing.T) {
	t.Setenv("DB_HOST", "envhost")
	type Nested struct {
		Host string `env:"HOST"`
	}
	var cli struct {
		DB Nested `embed:"" prefix:"db-" envprefix:"DB_"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.DB.Host, "envhost", "prefixed env name read")
	mustParse(t, a, []string{"--db-host", "cli"})
	wantEq(t, cli.DB.Host, "cli", "prefixed flag name")
}

// Verifies: Defaults, Environment Variables and Resolvers — variable
// interpolation.
func TestVarsInterpolation(t *testing.T) {
	var cli struct {
		Msg string `default:"${greeting}"`
	}
	a := build(t, &cli, kong.Vars{"greeting": "hi"})
	mustParse(t, a, nil)
	wantEq(t, cli.Msg, "hi", "variable substituted in default")
}

// Verifies: Defaults, Environment Variables and Resolvers — variable
// interpolation (fallback form).
func TestInterpolationFallback(t *testing.T) {
	var cli struct {
		A string `default:"${missing=falldef}"`
	}
	a := build(t, &cli)
	mustParse(t, a, nil)
	wantEq(t, cli.A, "falldef", "fallback substituted for undeclared variable")
}

// Verifies: Defaults, Environment Variables and Resolvers — variable
// interpolation (HasInterpolatedVar).
func TestHasInterpolatedVar(t *testing.T) {
	wantEq(t, kong.HasInterpolatedVar("x ${foo} y", "foo"), true, "reference found")
	wantEq(t, kong.HasInterpolatedVar("x ${foo} y", "bar"), false, "other variable")
	wantEq(t, kong.HasInterpolatedVar("no vars", "foo"), false, "no reference")
}

// Verifies: Defaults, Environment Variables and Resolvers — resolvers
// (custom ResolverFunc).
func TestCustomResolver(t *testing.T) {
	var cli struct {
		Val string
	}
	res := kong.ResolverFunc(func(ctx *kong.Context, parent *kong.Path, flag *kong.Flag) (interface{}, error) {
		if flag.Name == "val" {
			return "resolved", nil
		}
		return nil, nil
	})
	a := build(t, &cli, kong.Resolvers(res))
	mustParse(t, a, nil)
	wantEq(t, cli.Val, "resolved", "resolver supplied value")
	mustParse(t, a, []string{"--val", "cli"})
	wantEq(t, cli.Val, "cli", "command line beats resolver")
}

// Verifies: Defaults, Environment Variables and Resolvers — JSON
// configuration (key variants).
func TestJSONResolverKeyVariants(t *testing.T) {
	var cli struct {
		SomeFlag string
		DbHost   string `name:"db-host"`
	}
	r, err := kong.JSON(strings.NewReader(`{"some_flag": "sf", "dbHost": "dbh"}`))
	if err != nil {
		t.Fatalf("JSON resolver: %v", err)
	}
	a := build(t, &cli, kong.Resolvers(r))
	mustParse(t, a, nil)
	wantEq(t, cli.SomeFlag, "sf", "snake_case key")
	wantEq(t, cli.DbHost, "dbh", "camelCase key")
}

// Verifies: Defaults, Environment Variables and Resolvers — JSON
// configuration (Configuration option and LoadConfig).
func TestConfigurationOption(t *testing.T) {
	dir := t.TempDir()
	file := filepath.Join(dir, "app.json")
	if err := os.WriteFile(file, []byte(`{"port": 8080}`), 0o644); err != nil {
		t.Fatal(err)
	}
	var cli struct {
		Port int `default:"80"`
	}
	a := build(t, &cli, kong.Configuration(kong.JSON, file))
	mustParse(t, a, nil)
	wantEq(t, cli.Port, 8080, "config file value applied")

	var cli2 struct {
		Port int `default:"80"`
	}
	b := build(t, &cli2, kong.Configuration(kong.JSON))
	if _, err := b.k.LoadConfig(file); err != nil {
		t.Fatalf("LoadConfig failed: %v", err)
	}
}

// Verifies: Defaults, Environment Variables and Resolvers — resolvers
// (ClearResolvers does not affect env bindings).
func TestClearResolversKeepsEnv(t *testing.T) {
	t.Setenv("ORACLE_V", "fromenv")
	var cli struct {
		V string `env:"ORACLE_V" default:"def"`
	}
	a := build(t, &cli, kong.ClearResolvers())
	mustParse(t, a, nil)
	wantEq(t, cli.V, "fromenv", "env binding survives ClearResolvers")
}

// Verifies: Defaults, Environment Variables and Resolvers — precedence
// (required satisfied by resolver).
func TestRequiredSatisfiedByResolver(t *testing.T) {
	var cli struct {
		R string `required:""`
	}
	r, _ := kong.JSON(strings.NewReader(`{"r": "given"}`))
	a := build(t, &cli, kong.Resolvers(r))
	mustParse(t, a, nil)
	wantEq(t, cli.R, "given", "resolver satisfies required")
}

// Verifies: Defaults, Environment Variables and Resolvers — precedence
// (resolver beats environment).
func TestResolverBeatsEnvironment(t *testing.T) {
	t.Setenv("ORACLE_V", "fromenv")
	var cli struct {
		V string `env:"ORACLE_V" default:"def"`
	}
	r, _ := kong.JSON(strings.NewReader(`{"v": "fromjson"}`))
	a := build(t, &cli, kong.Resolvers(r))
	mustParse(t, a, nil)
	wantEq(t, cli.V, "fromjson", "resolver value wins over env")
}
