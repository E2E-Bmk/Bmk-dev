package atomic

import (
	"strings"
	"testing"

	"github.com/zclconf/go-cty/cty"
	"github.com/zclconf/go-cty/cty/convert"
)

func TestPrimitiveConversionTiers(t *testing.T) {
	if convert.GetConversion(cty.Number, cty.String) == nil {
		t.Error("number->string must be a safe conversion")
	}
	if convert.GetConversion(cty.Bool, cty.String) == nil {
		t.Error("bool->string must be a safe conversion")
	}
	if convert.GetConversion(cty.String, cty.Number) != nil {
		t.Error("string->number must not be in the safe tier")
	}
	if convert.GetConversionUnsafe(cty.String, cty.Number) == nil {
		t.Error("string->number must be an unsafe conversion")
	}
	if convert.GetConversionUnsafe(cty.String, cty.Bool) == nil {
		t.Error("string->bool must be an unsafe conversion")
	}
	if convert.GetConversionUnsafe(cty.Number, cty.Bool) != nil {
		t.Error("number->bool must not exist in either tier")
	}
	if convert.GetConversion(cty.String, cty.String) != nil {
		t.Error("no conversion from a type to itself")
	}
}

func TestNumberToStringFormatting(t *testing.T) {
	cases := map[string]cty.Value{
		"5":                     cty.NumberIntVal(5),
		"2.5":                   cty.NumberFloatVal(2.5),
		"1":                     cty.MustParseNumberVal("1.0"),
		"1000000000000000000000": cty.MustParseNumberVal("1e21"),
		"0.001":                 cty.MustParseNumberVal("1e-3"),
		"true":                  cty.True,
	}
	for want, in := range cases {
		got, err := convert.Convert(in, cty.String)
		if err != nil {
			t.Errorf("convert %#v: %v", in, err)
			continue
		}
		if got.AsString() != want {
			t.Errorf("convert %#v = %q, want %q", in, got.AsString(), want)
		}
	}
}

func TestStringToNumberParsing(t *testing.T) {
	got, err := convert.Convert(cty.StringVal("2.5"), cty.Number)
	if err != nil || !got.RawEquals(cty.NumberFloatVal(2.5)) {
		t.Errorf("string->number = %#v, %v", got, err)
	}
	_, err = convert.Convert(cty.StringVal("bananas"), cty.Number)
	if err == nil || err.Error() != "a number is required" {
		t.Errorf("non-numeric string error = %v", err)
	}
}

func TestStringToBoolStrict(t *testing.T) {
	got, err := convert.Convert(cty.StringVal("true"), cty.Bool)
	if err != nil || !got.True() {
		t.Errorf("\"true\"->bool = %#v, %v", got, err)
	}
	got, err = convert.Convert(cty.StringVal("false"), cty.Bool)
	if err != nil || got.True() {
		t.Errorf("\"false\"->bool = %#v, %v", got, err)
	}
	_, err = convert.Convert(cty.StringVal("True"), cty.Bool)
	if err == nil || !strings.Contains(err.Error(), "lowercase") {
		t.Errorf("\"True\" error must direct to lowercase: %v", err)
	}
	_, err = convert.Convert(cty.StringVal("yes"), cty.Bool)
	if err == nil {
		t.Error("\"yes\" must not convert to bool")
	}
}

func TestConvertNullAndUnknownPassthrough(t *testing.T) {
	n, err := convert.Convert(cty.NullVal(cty.Number), cty.String)
	if err != nil || !n.RawEquals(cty.NullVal(cty.String)) {
		t.Errorf("null passthrough = %#v, %v", n, err)
	}
	u, err := convert.Convert(cty.UnknownVal(cty.Number), cty.String)
	if err != nil || u.IsKnown() || !u.Type().Equals(cty.String) {
		t.Errorf("unknown passthrough = %#v, %v", u, err)
	}
}

func TestConvertSameTypeIdentity(t *testing.T) {
	v := cty.NumberIntVal(7)
	got, err := convert.Convert(v, cty.Number)
	if err != nil || !got.RawEquals(v) {
		t.Errorf("same-type convert = %#v, %v", got, err)
	}
	if n, _ := got.AsBigFloat().Int64(); n != 7 {
		t.Errorf("converted content = %d, want 7", n)
	}
	if got.RawEquals(cty.NumberIntVal(8)) {
		t.Error("converted value must not equal a different number")
	}
}

func TestMismatchMessages(t *testing.T) {
	if got := convert.MismatchMessage(cty.String, cty.Number); got != "number required" {
		t.Errorf("primitive mismatch = %q", got)
	}
	got := convert.MismatchMessage(
		cty.Object(map[string]cty.Type{"a": cty.String}),
		cty.Object(map[string]cty.Type{"a": cty.String, "b": cty.Number}),
	)
	if got != `attribute "b" is required` {
		t.Errorf("object mismatch = %q", got)
	}
	if got := convert.MismatchMessage(cty.List(cty.Bool), cty.List(cty.Number)); got != "incorrect list element type: number required, but have bool" {
		t.Errorf("list mismatch = %q", got)
	}
	if got := convert.MismatchMessage(cty.Tuple([]cty.Type{cty.Bool, cty.Number}), cty.List(cty.Number)); got != "element 0: number required, but have bool" {
		t.Errorf("tuple mismatch = %q", got)
	}
}
