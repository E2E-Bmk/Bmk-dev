package atomic

import (
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/alecthomas/kong"
)

// Verifies: Value Mapping — built-in decoding (scalars).
func TestBuiltinScalarDecoding(t *testing.T) {
	var cli struct {
		S string
		I int
		U uint
		F float64
		B bool
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--s", "text", "--i=-3", "--u", "7", "--f", "1.5", "--b"})
	wantEq(t, cli.S, "text", "string")
	wantEq(t, cli.I, -3, "int (negative in attached form)")
	wantEq(t, cli.U, uint(7), "uint")
	wantEq(t, cli.F, 1.5, "float")
	wantEq(t, cli.B, true, "bool")
}

// Verifies: Value Mapping — built-in decoding (duration).
func TestDurationDecoding(t *testing.T) {
	var cli struct {
		T time.Duration
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--t", "2m30s"})
	wantEq(t, cli.T, 2*time.Minute+30*time.Second, "duration value")
	err := parseErr(t, a, []string{"--t", "bogus"})
	wantContains(t, err.Error(), `expected duration but got "bogus"`, "error text")
}

// Verifies: Value Mapping — built-in decoding (time defaults to RFC 3339).
func TestTimeDefaultsToRFC3339(t *testing.T) {
	var cli struct {
		T time.Time
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--t", "2024-03-01T10:00:00Z"})
	wantEq(t, cli.T.Format(time.RFC3339), "2024-03-01T10:00:00Z", "time value")
}

// Verifies: Value Mapping — built-in decoding (format tag).
func TestTimeFormatTag(t *testing.T) {
	var cli struct {
		Day time.Time `format:"2006-01-02"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--day", "2024-03-01"})
	wantEq(t, cli.Day.Year(), 2024, "year")
	wantEq(t, int(cli.Day.Month()), 3, "month")
	if _, err := a.k.Parse([]string{"--day", "01/02/2024"}); err == nil {
		t.Fatal("mismatched layout accepted")
	}
}

// Verifies: Value Mapping — built-in decoding (malformed int and float).
func TestMalformedNumberErrors(t *testing.T) {
	var cli struct {
		Num int
		F   float64
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"--num", "abc"})
	wantEq(t, err.Error(), `--num: expected a valid 64 bit int but got "abc"`, "int error")
	b := build(t, &cli)
	err = parseErr(t, b, []string{"--f", "abc"})
	wantEq(t, err.Error(), `--f: expected a float but got "abc" (string)`, "float error")
}

// Verifies: Value Mapping — special types and type tags (path).
func TestPathTypeExpansion(t *testing.T) {
	var cli struct {
		P string `type:"path"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--p", "~/thing"})
	home, _ := os.UserHomeDir()
	wantEq(t, cli.P, filepath.Join(home, "thing"), "tilde expanded")
	if !filepath.IsAbs(cli.P) {
		t.Fatal("path not absolute")
	}
	wantEq(t, kong.ExpandPath("~/thing"), filepath.Join(home, "thing"), "ExpandPath function")
}

// Verifies: Value Mapping — special types and type tags (FileContentFlag).
func TestFileContentFlag(t *testing.T) {
	dir := t.TempDir()
	file := filepath.Join(dir, "content.txt")
	if err := os.WriteFile(file, []byte("payload"), 0o644); err != nil {
		t.Fatal(err)
	}
	var cli struct {
		F kong.FileContentFlag
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--f", file})
	wantEq(t, string(cli.F), "payload", "file contents loaded")
}

// Verifies: Value Mapping — special types and type tags (ConfigFlag).
func TestConfigFlagLoadsResolver(t *testing.T) {
	dir := t.TempDir()
	file := filepath.Join(dir, "conf.json")
	if err := os.WriteFile(file, []byte(`{"port": 7070}`), 0o644); err != nil {
		t.Fatal(err)
	}
	var cli struct {
		Port   int             `default:"80"`
		Config kong.ConfigFlag `name:"config"`
	}
	a := build(t, &cli, kong.Configuration(kong.JSON))
	mustParse(t, a, []string{"--config", file})
	wantEq(t, cli.Port, 7070, "value from config file")
}

// Verifies: Value Mapping — special types and type tags (VersionFlag).
func TestVersionFlag(t *testing.T) {
	var cli struct {
		Version kong.VersionFlag
	}
	a := build(t, &cli, kong.Vars{"version": "1.2.3"})
	a.k.Parse([]string{"--version"})
	wantEq(t, a.out.String(), "1.2.3\n", "version text on stdout")
	if len(a.exits) == 0 || a.exits[0] != 0 {
		t.Fatalf("version did not exit 0: %v", a.exits)
	}
}

// Verifies: Value Mapping — custom mappers (NamedMapper).
func TestNamedMapper(t *testing.T) {
	var cli struct {
		P point `type:"point"`
	}
	a := build(t, &cli, kong.NamedMapper("point", pointMapper()))
	mustParse(t, a, []string{"--p", "3,4"})
	wantEq(t, cli.P, point{3, 4}, "decoded by named mapper")
}

// Verifies: Value Mapping — custom mappers (TypeMapper).
func TestTypeMapper(t *testing.T) {
	var cli struct {
		P point
	}
	a := build(t, &cli, kong.TypeMapper(reflect.TypeOf(point{}), pointMapper()))
	mustParse(t, a, []string{"--p", "5,6"})
	wantEq(t, cli.P, point{5, 6}, "decoded by type mapper")
}

// Verifies: Value Mapping — custom mappers (DecodeContext and scanner).
func TestMapperDecodeContext(t *testing.T) {
	var sawName string
	mapper := kong.MapperFunc(func(ctx *kong.DecodeContext, target reflect.Value) error {
		sawName = ctx.Value.Name
		token, err := ctx.Scan.PopValue("probe")
		if err != nil {
			return err
		}
		target.SetString("got:" + token.String())
		return nil
	})
	var cli struct {
		V string `type:"probe"`
	}
	a := build(t, &cli, kong.NamedMapper("probe", mapper))
	mustParse(t, a, []string{"--v", "raw"})
	wantEq(t, cli.V, "got:raw", "mapper consumed token")
	wantEq(t, sawName, "v", "DecodeContext.Value names the flag")
}

// Verifies: Value Mapping — custom mappers (negative number after short
// flag).
func TestNegativeNumberAfterShortFlag(t *testing.T) {
	var cli struct {
		Num int `short:"n"`
	}
	a := build(t, &cli)
	err := parseErr(t, a, []string{"-n", "-5"})
	wantContains(t, err.Error(), `perhaps try --num="-5"?`, "suggests attached form")
	mustParse(t, a, []string{"--num=-5"})
	wantEq(t, cli.Num, -5, "attached form accepted")
}

// Verifies: Value Mapping — enums (flag form).
func TestEnumFlagViolation(t *testing.T) {
	var cli struct {
		Enum string `enum:"a,b,c" default:"a"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"--enum", "b"})
	wantEq(t, cli.Enum, "b", "listed alternative accepted")
	err := parseErr(t, a, []string{"--enum", "z"})
	wantEq(t, err.Error(), `--enum must be one of "a","b","c" but got "z"`, "error text")
}

// Verifies: Value Mapping — enums (positional form).
func TestEnumPositionalViolation(t *testing.T) {
	var cli struct {
		Mode string `arg:"" enum:"fast,slow"`
	}
	a := build(t, &cli)
	mustParse(t, a, []string{"fast"})
	wantEq(t, cli.Mode, "fast", "listed alternative accepted")
	err := parseErr(t, a, []string{"wrong"})
	wantEq(t, err.Error(), `<mode> must be one of "fast","slow" but got "wrong"`, "error text")
}

type point struct{ X, Y int }

func pointMapper() kong.Mapper {
	return kong.MapperFunc(func(ctx *kong.DecodeContext, target reflect.Value) error {
		var s string
		if err := ctx.Scan.PopValueInto("point", &s); err != nil {
			return err
		}
		parts := strings.SplitN(s, ",", 2)
		x, err := strconv.Atoi(parts[0])
		if err != nil {
			return err
		}
		y, err := strconv.Atoi(parts[1])
		if err != nil {
			return err
		}
		target.Set(reflect.ValueOf(point{X: x, Y: y}))
		return nil
	})
}
