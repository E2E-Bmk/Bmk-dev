package atomic

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
)

func TestStringNFCNormalization(t *testing.T) {
	v := cty.StringVal("e\u0301") // e + combining acute
	if got := v.AsString(); got != "\u00e9" {
		t.Errorf("AsString = %q, want precomposed \u00e9", got)
	}
	if !v.RawEquals(cty.StringVal("\u00e9")) {
		t.Error("decomposed and precomposed constructions must be equal")
	}
}

func TestAsStringPanicsOnNumber(t *testing.T) {
	mustPanic(t, "AsString on number", func() { cty.NumberIntVal(1).AsString() })
}

func TestBoolValTrueFalse(t *testing.T) {
	if !cty.BoolVal(true).RawEquals(cty.True) || !cty.BoolVal(false).RawEquals(cty.False) {
		t.Error("BoolVal must produce the ready-made booleans")
	}
	if !cty.True.True() || cty.True.False() {
		t.Error("True/False projections wrong on cty.True")
	}
	if cty.False.True() || !cty.False.False() {
		t.Error("True/False projections wrong on cty.False")
	}
	mustPanic(t, "True on number", func() { cty.NumberIntVal(1).True() })
}

func TestNumberIntegerExactness(t *testing.T) {
	maxV := cty.NumberIntVal(9223372036854775807)
	i, acc := maxV.AsBigFloat().Int64()
	if i != 9223372036854775807 || acc != 0 { // big.Accuracy Exact == 0
		t.Errorf("int64 max not exact: %d acc=%v", i, acc)
	}
	minV := cty.NumberIntVal(-9223372036854775808)
	i2, acc2 := minV.AsBigFloat().Int64()
	if i2 != -9223372036854775808 || acc2 != 0 {
		t.Errorf("int64 min not exact: %d acc=%v", i2, acc2)
	}
	u := cty.NumberUIntVal(18446744073709551615)
	u2, acc3 := u.AsBigFloat().Uint64()
	if u2 != 18446744073709551615 || acc3 != 0 {
		t.Errorf("uint64 max not exact: %d acc=%v", u2, acc3)
	}
	mustPanic(t, "AsBigFloat on string", func() { cty.StringVal("x").AsBigFloat() })
}

func TestParseNumberValInvalid(t *testing.T) {
	_, err := cty.ParseNumberVal("bananas")
	if err == nil {
		t.Fatal("ParseNumberVal must reject non-numeric input")
	}
	if got := err.Error(); got != "a number is required" {
		t.Errorf("error = %q, want %q", got, "a number is required")
	}
	mustPanic(t, "MustParseNumberVal invalid", func() { cty.MustParseNumberVal("bananas") })
	v, err := cty.ParseNumberVal("2.5")
	if err != nil || !v.RawEquals(cty.NumberFloatVal(2.5)) {
		t.Errorf("ParseNumberVal(2.5) = %#v, %v", v, err)
	}
}

func TestDecimalCorrection(t *testing.T) {
	if !cty.NumberFloatVal(0.1).RawEquals(cty.MustParseNumberVal("0.1")) {
		t.Error("float 0.1 and parsed 0.1 must be the same number")
	}
	if cty.NumberFloatVal(0.1).RawEquals(cty.MustParseNumberVal("0.2")) {
		t.Error("0.1 must not equal 0.2")
	}
	sum := cty.MustParseNumberVal("0.1").Add(cty.MustParseNumberVal("0.2"))
	if !sum.Equals(cty.MustParseNumberVal("0.3")).True() {
		t.Error("0.1 + 0.2 must equal 0.3 for parsed decimals")
	}
	if sum.Equals(cty.MustParseNumberVal("0.4")).True() {
		t.Error("0.1 + 0.2 must not equal 0.4")
	}
	if got, _ := sum.AsBigFloat().Float64(); got != 0.3 {
		t.Errorf("sum content = %v, want 0.3", got)
	}
	if !cty.NumberIntVal(1).RawEquals(cty.MustParseNumberVal("1.0")) {
		t.Error("1 and 1.0 must be the same number")
	}
}

func TestNegativeZeroEqualsZero(t *testing.T) {
	if !cty.MustParseNumberVal("-0").RawEquals(cty.Zero) {
		t.Error("-0 must equal 0")
	}
	if cty.MustParseNumberVal("-1").RawEquals(cty.Zero) {
		t.Error("-1 must not equal 0")
	}
	if got, _ := cty.MustParseNumberVal("-0").AsBigFloat().Float64(); got != 0 {
		t.Errorf("-0 content = %v, want 0", got)
	}
}

func TestInfinityOrdering(t *testing.T) {
	big := cty.NumberIntVal(1 << 62)
	if !cty.PositiveInfinity.GreaterThan(big).True() {
		t.Error("PositiveInfinity must exceed all finite numbers")
	}
	if cty.PositiveInfinity.LessThan(big).True() {
		t.Error("PositiveInfinity must not be below a finite number")
	}
	if !cty.NegativeInfinity.LessThan(big.Negate()).True() {
		t.Error("NegativeInfinity must be below all finite numbers")
	}
	if cty.NegativeInfinity.GreaterThan(big.Negate()).True() {
		t.Error("NegativeInfinity must not exceed a finite number")
	}
}

func TestListValPreconditions(t *testing.T) {
	mustPanic(t, "ListVal empty", func() { cty.ListVal([]cty.Value{}) })
	mustPanic(t, "ListVal mixed", func() {
		cty.ListVal([]cty.Value{cty.StringVal("a"), cty.NumberIntVal(1)})
	})
}

func TestListValEmpty(t *testing.T) {
	l := cty.ListValEmpty(cty.String)
	if !l.Type().Equals(cty.List(cty.String)) {
		t.Error("ListValEmpty type wrong")
	}
	if l.Type().Equals(cty.List(cty.Number)) {
		t.Error("ListValEmpty element type must be the requested one")
	}
	if !l.Type().ElementType().Equals(cty.String) {
		t.Error("element type must round-trip through ElementType")
	}
	if l.LengthInt() != 0 {
		t.Error("ListValEmpty must have zero length")
	}
	if l.IsNull() || !l.IsKnown() {
		t.Error("ListValEmpty must be known non-null")
	}
}

func TestMapValAndEmpty(t *testing.T) {
	m := cty.MapVal(map[string]cty.Value{"k": cty.NumberIntVal(1)})
	if !m.Type().Equals(cty.Map(cty.Number)) {
		t.Error("MapVal type wrong")
	}
	if !m.Index(cty.StringVal("k")).RawEquals(cty.NumberIntVal(1)) {
		t.Error("MapVal content wrong")
	}
	e := cty.MapValEmpty(cty.Bool)
	if !e.Type().Equals(cty.Map(cty.Bool)) || e.LengthInt() != 0 {
		t.Error("MapValEmpty wrong")
	}
	mustPanic(t, "MapVal mixed", func() {
		cty.MapVal(map[string]cty.Value{"a": cty.True, "b": cty.NumberIntVal(1)})
	})
}

func TestSetValDedup(t *testing.T) {
	s := cty.SetVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(1), cty.NumberIntVal(2)})
	if s.LengthInt() != 2 {
		t.Errorf("set length = %d, want 2 after dedup", s.LengthInt())
	}
	objA := cty.ObjectVal(map[string]cty.Value{"x": cty.NumberIntVal(1)})
	objB := cty.ObjectVal(map[string]cty.Value{"x": cty.NumberIntVal(1)})
	if cty.SetVal([]cty.Value{objA, objB}).LengthInt() != 1 {
		t.Error("independently built equal objects must occupy one set slot")
	}
	e := cty.SetValEmpty(cty.String)
	if !e.Type().Equals(cty.Set(cty.String)) || e.LengthInt() != 0 {
		t.Error("SetValEmpty wrong")
	}
}

func TestTupleObjectValTypeDerivation(t *testing.T) {
	tp := cty.TupleVal([]cty.Value{cty.StringVal("x"), cty.NumberIntVal(3)})
	if !tp.Type().Equals(cty.Tuple([]cty.Type{cty.String, cty.Number})) {
		t.Error("TupleVal type derivation wrong")
	}
	if tp.Type().Equals(cty.Tuple([]cty.Type{cty.Number, cty.String})) {
		t.Error("tuple element order must matter")
	}
	if got := tp.Index(cty.NumberIntVal(0)).AsString(); got != "x" {
		t.Errorf("tuple element 0 = %q, want x", got)
	}
	o := cty.ObjectVal(map[string]cty.Value{"name": cty.StringVal("n"), "on": cty.True})
	if !o.Type().Equals(cty.Object(map[string]cty.Type{"name": cty.String, "on": cty.Bool})) {
		t.Error("ObjectVal type derivation wrong")
	}
	if o.Type().Equals(cty.Object(map[string]cty.Type{"name": cty.Bool, "on": cty.String})) {
		t.Error("object attribute types must matter")
	}
	if got := o.GetAttr("name").AsString(); got != "n" {
		t.Errorf("object attr name = %q, want n", got)
	}
}

func TestNullAndUnknownConstructors(t *testing.T) {
	n := cty.NullVal(cty.String)
	if !n.IsNull() || !n.IsKnown() {
		t.Error("null must be null and known")
	}
	if !n.Type().Equals(cty.String) {
		t.Error("null type wrong")
	}
	u := cty.UnknownVal(cty.Number)
	if u.IsNull() || u.IsKnown() {
		t.Error("unknown must be non-null and not known")
	}
	if !u.Type().Equals(cty.Number) {
		t.Error("unknown type wrong")
	}
	dn := cty.NullVal(cty.DynamicPseudoType)
	if !dn.IsNull() || !dn.Type().Equals(cty.DynamicPseudoType) {
		t.Error("dynamic null wrong")
	}
	if cty.DynamicVal.IsKnown() || cty.DynamicVal.IsNull() {
		t.Error("DynamicVal must be unknown and non-null")
	}
}

func TestWhollyKnownDistinction(t *testing.T) {
	l := cty.ListVal([]cty.Value{cty.UnknownVal(cty.String)})
	if !l.IsKnown() {
		t.Error("list itself is known")
	}
	if l.IsWhollyKnown() {
		t.Error("list with unknown element is not wholly known")
	}
	if !cty.ListVal([]cty.Value{cty.StringVal("a")}).IsWhollyKnown() {
		t.Error("fully known list must be wholly known")
	}
	if cty.DynamicVal.HasWhollyKnownType() {
		t.Error("HasWhollyKnownType must be false for the dynamic unknown")
	}
	if cty.TupleVal([]cty.Value{cty.DynamicVal}).HasWhollyKnownType() {
		t.Error("HasWhollyKnownType must be false with a nested dynamic unknown")
	}
	if !cty.ListValEmpty(cty.DynamicPseudoType).HasWhollyKnownType() {
		t.Error("empty collection of dynamic element type contains no dynamic unknowns")
	}
	if !cty.NullVal(cty.DynamicPseudoType).HasWhollyKnownType() {
		t.Error("dynamic null contains no dynamic unknowns")
	}
	if !cty.ListValEmpty(cty.String).HasWhollyKnownType() {
		t.Error("HasWhollyKnownType must be true for concrete values")
	}
}

func TestUnknownAsNullDeep(t *testing.T) {
	l := cty.ListVal([]cty.Value{cty.UnknownVal(cty.String), cty.StringVal("x")})
	got := cty.UnknownAsNull(l)
	want := cty.ListVal([]cty.Value{cty.NullVal(cty.String), cty.StringVal("x")})
	if !got.RawEquals(want) {
		t.Errorf("UnknownAsNull = %#v, want %#v", got, want)
	}
	if got.RawEquals(l) {
		t.Error("result must differ from the input that held an unknown")
	}
	elems := got.AsValueSlice()
	if len(elems) != 2 || !elems[0].IsNull() || elems[1].IsNull() {
		t.Errorf("element nullity wrong: %#v", elems)
	}
	if got := elems[1].AsString(); got != "x" {
		t.Errorf("known element = %q, want x", got)
	}
	top := cty.UnknownAsNull(cty.UnknownVal(cty.Number))
	if !top.RawEquals(cty.NullVal(cty.Number)) {
		t.Error("top-level unknown must become typed null")
	}
	if !top.IsNull() || !top.IsKnown() {
		t.Error("result must be a known null")
	}
}
