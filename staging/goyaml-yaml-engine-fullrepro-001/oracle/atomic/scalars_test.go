package atomic

import (
	"math"
	"testing"
)

// Verifies: Decoding into Go Values > Scalar typing into untyped destinations.
func TestScalarUnsignedIntegerForms(t *testing.T) {
	cases := map[string]uint64{
		"123":   123,
		"0x1F":  31,
		"0o17":  15,
		"0b101": 5,
		"1_000": 1000,
		"0":     0,
	}
	for lit, want := range cases {
		got := scalar(t, lit)
		wantEqual(t, got, want, "literal "+lit)
	}
}

// Verifies: Decoding into Go Values > Scalar typing into untyped destinations.
func TestScalarNegativeIntegerIsInt64(t *testing.T) {
	wantEqual(t, scalar(t, "-3"), int64(-3), "-3")
	wantEqual(t, scalar(t, "-1_000"), int64(-1000), "-1_000")
}

// Verifies: Decoding into Go Values > Scalar typing into untyped destinations.
func TestScalarFloatForms(t *testing.T) {
	wantEqual(t, scalar(t, "1.5"), 1.5, "1.5")
	wantEqual(t, scalar(t, "1.5e3"), 1500.0, "1.5e3")
	wantEqual(t, scalar(t, "1_234.5"), 1234.5, "1_234.5")
	wantEqual(t, scalar(t, "-0.25"), -0.25, "-0.25")
}

// Verifies: Decoding into Go Values > Scalar typing (exponent form without a
// decimal point stays a string untyped, converts for typed destinations).
func TestScalarExponentWithoutPoint(t *testing.T) {
	wantEqual(t, scalar(t, "1e3"), "1e3", "untyped 1e3")

	var typed struct {
		V float64 `yaml:"v"`
	}
	if err := unmarshalInto(t, "v: 1e3\n", &typed); err != nil {
		t.Fatalf("typed decode of 1e3: %v", err)
	}
	if typed.V != 1000 {
		t.Fatalf("typed 1e3 = %v, want 1000", typed.V)
	}
}

// Verifies: Decoding into Go Values > Scalar typing (infinities and NaN).
func TestScalarInfinityAndNaN(t *testing.T) {
	if got := scalar(t, ".inf"); got != math.Inf(1) {
		t.Fatalf(".inf = %v, want +Inf", got)
	}
	if got := scalar(t, ".Inf"); got != math.Inf(1) {
		t.Fatalf(".Inf = %v, want +Inf", got)
	}
	if got := scalar(t, "-.inf"); got != math.Inf(-1) {
		t.Fatalf("-.inf = %v, want -Inf", got)
	}
	f, ok := scalar(t, ".nan").(float64)
	if !ok || !math.IsNaN(f) {
		t.Fatalf(".nan did not decode as a floating NaN")
	}
	f2, ok := scalar(t, ".NaN").(float64)
	if !ok || !math.IsNaN(f2) {
		t.Fatalf(".NaN did not decode as a floating NaN")
	}
	// +.inf is not an infinity spelling.
	wantEqual(t, scalar(t, "+.inf"), "+.inf", "+.inf")
}

// Verifies: Decoding into Go Values > Scalar typing (boolean spellings).
func TestScalarBooleanSpellings(t *testing.T) {
	wantEqual(t, scalar(t, "true"), true, "true")
	wantEqual(t, scalar(t, "True"), true, "True")
	wantEqual(t, scalar(t, "false"), false, "false")
	wantEqual(t, scalar(t, "False"), false, "False")
	// YAML 1.1 spellings decode as strings.
	for _, lit := range []string{"yes", "no", "on", "off", "y", "n"} {
		wantEqual(t, scalar(t, lit), lit, "1.1 spelling "+lit)
	}
}

// Verifies: Decoding into Go Values > Scalar typing (null forms).
func TestScalarNullForms(t *testing.T) {
	if got := scalar(t, "null"); got != nil {
		t.Fatalf("null = %#v, want nil", got)
	}
	if got := scalar(t, "~"); got != nil {
		t.Fatalf("~ = %#v, want nil", got)
	}
	v := decodeUntyped(t, "a:\nb: 1\n")
	m := v.(map[string]interface{})
	if m["a"] != nil {
		t.Fatalf("empty value = %#v, want nil", m["a"])
	}
	wantEqual(t, m["b"], uint64(1), "sibling of empty value")
}

// Verifies: Decoding into Go Values > Scalar typing (quoted scalars are
// always strings).
func TestQuotedScalarsAlwaysStrings(t *testing.T) {
	wantEqual(t, scalar(t, `"true"`), "true", `"true"`)
	wantEqual(t, scalar(t, `"123"`), "123", `"123"`)
	wantEqual(t, scalar(t, `'1.5'`), "1.5", `'1.5'`)
	wantEqual(t, scalar(t, `"null"`), "null", `"null"`)
}

// Verifies: Decoding into Go Values > Scalar typing (date-like scalars).
func TestDateLikeScalarStaysString(t *testing.T) {
	wantEqual(t, scalar(t, "2024-01-15"), "2024-01-15", "date-like")
}

// Verifies: Decoding into Go Values (untyped container shapes).
func TestUntypedContainerShapes(t *testing.T) {
	v := decodeUntyped(t, "outer:\n  inner:\n    x: 1\nitems:\n  - name: a\n  - name: b\n")
	root, ok := v.(map[string]interface{})
	if !ok {
		t.Fatalf("root is %T, want map[string]interface{}", v)
	}
	outer, ok := root["outer"].(map[string]interface{})
	if !ok {
		t.Fatalf("outer is %T, want map[string]interface{}", root["outer"])
	}
	inner, ok := outer["inner"].(map[string]interface{})
	if !ok {
		t.Fatalf("inner is %T, want map[string]interface{}", outer["inner"])
	}
	wantEqual(t, inner["x"], uint64(1), "inner.x")
	items, ok := root["items"].([]interface{})
	if !ok {
		t.Fatalf("items is %T, want []interface{}", root["items"])
	}
	if len(items) != 2 {
		t.Fatalf("items has %d elements, want 2", len(items))
	}
	first, ok := items[0].(map[string]interface{})
	if !ok {
		t.Fatalf("items[0] is %T, want map[string]interface{}", items[0])
	}
	wantEqual(t, first["name"], "a", "items[0].name")
}

// Verifies: Decoding into Go Values (literal block scalars).
func TestLiteralBlockDecode(t *testing.T) {
	v := decodeUntyped(t, "a: |\n  line1\n  line2\nb: |-\n  x\n  y\n")
	m := v.(map[string]interface{})
	wantEqual(t, m["a"], "line1\nline2\n", "keep-final-newline literal")
	wantEqual(t, m["b"], "x\ny", "strip-final-newline literal")
}

