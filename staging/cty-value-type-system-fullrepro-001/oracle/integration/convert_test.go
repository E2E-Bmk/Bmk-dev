package integration

import (
	"strings"
	"testing"

	"github.com/zclconf/go-cty/cty"
	"github.com/zclconf/go-cty/cty/convert"
)

func TestListSetConversionsBothWays(t *testing.T) {
	l := cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("a"), cty.StringVal("b")})
	s, err := convert.Convert(l, cty.Set(cty.String))
	if err != nil {
		t.Fatalf("list->set: %v", err)
	}
	if !s.Type().Equals(cty.Set(cty.String)) || s.LengthInt() != 2 {
		t.Errorf("list->set must deduplicate: %#v", s)
	}
	back, err := convert.Convert(s, cty.List(cty.String))
	if err != nil {
		t.Fatalf("set->list: %v", err)
	}
	if !back.Type().Equals(cty.List(cty.String)) || back.LengthInt() != 2 {
		t.Errorf("set->list wrong: %#v", back)
	}
	seen := map[string]bool{}
	for _, v := range back.AsValueSlice() {
		seen[v.AsString()] = true
	}
	if !seen["a"] || !seen["b"] {
		t.Error("set->list must retain all distinct elements")
	}
}

func TestTupleToCollectionUnification(t *testing.T) {
	tp := cty.TupleVal([]cty.Value{cty.NumberIntVal(1), cty.StringVal("x")})
	l, err := convert.Convert(tp, cty.List(cty.String))
	if err != nil {
		t.Fatalf("tuple->list(string): %v", err)
	}
	want := cty.ListVal([]cty.Value{cty.StringVal("1"), cty.StringVal("x")})
	if !l.RawEquals(want) {
		t.Errorf("tuple->list = %#v, want %#v", l, want)
	}

	het := cty.TupleVal([]cty.Value{cty.NumberIntVal(1), cty.True})
	_, err = convert.Convert(het, cty.List(cty.DynamicPseudoType))
	if err == nil || !strings.Contains(err.Error(), "same type") {
		t.Errorf("non-unifiable tuple error = %v", err)
	}

	st, err := convert.Convert(cty.TupleVal([]cty.Value{cty.True, cty.NumberIntVal(1)}), cty.Set(cty.String))
	if err != nil {
		t.Fatalf("tuple->set(string): %v", err)
	}
	if st.LengthInt() != 2 || !st.HasElement(cty.StringVal("true")).True() || !st.HasElement(cty.StringVal("1")).True() {
		t.Errorf("tuple->set = %#v", st)
	}
}

func TestEmptyTupleToList(t *testing.T) {
	got, err := convert.Convert(cty.EmptyTupleVal, cty.List(cty.String))
	if err != nil {
		t.Fatalf("empty tuple->list: %v", err)
	}
	if !got.RawEquals(cty.ListValEmpty(cty.String)) {
		t.Errorf("empty tuple->list = %#v", got)
	}
	if got.RawEquals(cty.EmptyTupleVal) {
		t.Error("result must be a list, not the original tuple")
	}
	if !got.Type().IsListType() || got.Type().IsTupleType() {
		t.Errorf("result type = %#v, want a list type", got.Type())
	}
	if got.LengthInt() != 0 {
		t.Error("result must be empty")
	}
}

func TestObjectMapConversions(t *testing.T) {
	o := cty.ObjectVal(map[string]cty.Value{"a": cty.NumberIntVal(1), "b": cty.NumberIntVal(2)})
	m, err := convert.Convert(o, cty.Map(cty.Number))
	if err != nil {
		t.Fatalf("object->map: %v", err)
	}
	want := cty.MapVal(map[string]cty.Value{"a": cty.NumberIntVal(1), "b": cty.NumberIntVal(2)})
	if !m.RawEquals(want) {
		t.Errorf("object->map = %#v", m)
	}
	back, err := convert.Convert(m, cty.Object(map[string]cty.Type{"a": cty.Number, "b": cty.Number}))
	if err != nil || !back.RawEquals(o) {
		t.Errorf("map->object = %#v, %v", back, err)
	}
	_, err = convert.Convert(m, cty.Object(map[string]cty.Type{"a": cty.Number, "zzz": cty.Number}))
	if err == nil {
		t.Error("map->object with absent key must fail")
	}
}

func TestObjectStructuralTyping(t *testing.T) {
	in := cty.ObjectVal(map[string]cty.Value{"a": cty.StringVal("x"), "extra": cty.True})
	got, err := convert.Convert(in, cty.Object(map[string]cty.Type{"a": cty.String}))
	if err != nil {
		t.Fatalf("extra attr conversion: %v", err)
	}
	if !got.RawEquals(cty.ObjectVal(map[string]cty.Value{"a": cty.StringVal("x")})) {
		t.Errorf("extra attributes must be discarded: %#v", got)
	}

	_, err = convert.Convert(
		cty.ObjectVal(map[string]cty.Value{"a": cty.StringVal("x")}),
		cty.Object(map[string]cty.Type{"a": cty.String, "b": cty.Number}),
	)
	if err == nil || !strings.Contains(err.Error(), `attribute "b" is required`) {
		t.Errorf("missing attr error = %v", err)
	}

	optTy := cty.ObjectWithOptionalAttrs(map[string]cty.Type{"a": cty.String, "b": cty.Number}, []string{"b"})
	filled, err := convert.Convert(cty.ObjectVal(map[string]cty.Value{"a": cty.StringVal("x")}), optTy)
	if err != nil {
		t.Fatalf("optional fill: %v", err)
	}
	if !filled.GetAttr("b").RawEquals(cty.NullVal(cty.Number)) {
		t.Errorf("optional attribute must be filled with typed null: %#v", filled)
	}
	if !filled.GetAttr("a").RawEquals(cty.StringVal("x")) {
		t.Error("present attribute must be preserved")
	}
}

func TestObjectAttrRecursiveConversion(t *testing.T) {
	in := cty.ObjectVal(map[string]cty.Value{"port": cty.StringVal("8080")})
	got, err := convert.Convert(in, cty.Object(map[string]cty.Type{"port": cty.Number}))
	if err != nil {
		t.Fatalf("recursive attr conversion: %v", err)
	}
	if !got.GetAttr("port").RawEquals(cty.NumberIntVal(8080)) {
		t.Errorf("attr conversion = %#v", got)
	}
	_, err = convert.Convert(
		cty.ObjectVal(map[string]cty.Value{"port": cty.StringVal("x")}),
		cty.Object(map[string]cty.Type{"port": cty.Number}),
	)
	if err == nil {
		t.Error("inconvertible attr value must fail")
	}
}

func TestDynamicPlaceholderConversions(t *testing.T) {
	through, err := convert.Convert(cty.True, cty.DynamicPseudoType)
	if err != nil || !through.RawEquals(cty.True) {
		t.Errorf("to-dynamic passthrough = %#v, %v", through, err)
	}

	f := convert.GetConversionUnsafe(cty.DynamicPseudoType, cty.String)
	if f == nil {
		t.Fatal("from-dynamic conversion must exist in the unsafe tier")
	}
	out, err := f(cty.StringVal("hello"))
	if err != nil || !out.RawEquals(cty.StringVal("hello")) {
		t.Errorf("matching runtime type = %#v, %v", out, err)
	}
	out, err = f(cty.True)
	if err != nil || !out.RawEquals(cty.StringVal("true")) {
		t.Errorf("convertible runtime type = %#v, %v", out, err)
	}
	_, err = f(cty.ListValEmpty(cty.String))
	if err == nil {
		t.Error("inconvertible runtime type must fail at call time")
	}

	u, err := convert.Convert(cty.DynamicVal, cty.Number)
	if err != nil || u.IsKnown() || !u.Type().Equals(cty.Number) {
		t.Errorf("DynamicVal conversion = %#v, %v", u, err)
	}
}

func TestListToTupleUnavailable(t *testing.T) {
	_, err := convert.Convert(
		cty.ListVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(2)}),
		cty.Tuple([]cty.Type{cty.Number, cty.Number}),
	)
	if err == nil {
		t.Error("list->tuple must not be available")
	}
}

func TestMarksThroughConversion(t *testing.T) {
	scalar, err := convert.Convert(cty.NumberIntVal(5).Mark("m"), cty.String)
	if err != nil {
		t.Fatalf("marked scalar: %v", err)
	}
	if !scalar.IsMarked() {
		t.Error("mark must survive scalar conversion")
	}
	content, _ := scalar.Unmark()
	if !content.RawEquals(cty.StringVal("5")) {
		t.Error("marked conversion content wrong")
	}

	nested, err := convert.Convert(
		cty.ListVal([]cty.Value{cty.NumberIntVal(1).Mark("m")}),
		cty.List(cty.String),
	)
	if err != nil {
		t.Fatalf("nested mark: %v", err)
	}
	if nested.IsMarked() {
		t.Error("container must not gain the element mark")
	}
	if !nested.Index(cty.NumberIntVal(0)).IsMarked() {
		t.Error("element mark must stay in place")
	}

	lifted, err := convert.Convert(
		cty.TupleVal([]cty.Value{cty.NumberIntVal(1).Mark("m"), cty.NumberIntVal(2)}),
		cty.Set(cty.Number),
	)
	if err != nil {
		t.Fatalf("tuple->set with mark: %v", err)
	}
	if !lifted.IsMarked() {
		t.Error("element marks must lift onto the resulting set")
	}
	inner, marks := lifted.Unmark()
	if _, ok := marks["m"]; !ok {
		t.Error("set-level mark set must contain the element mark")
	}
	if inner.LengthInt() != 2 {
		t.Error("set content wrong")
	}
}

func TestUnifyTiers(t *testing.T) {
	ty, cs := convert.Unify([]cty.Type{cty.Number, cty.String})
	if !ty.Equals(cty.String) || len(cs) != 2 {
		t.Errorf("unify [num,str] = %v, %d conversions", ty.GoString(), len(cs))
	}
	if cs[0] == nil {
		t.Error("number input needs a conversion to string")
	}
	if cs[1] != nil {
		t.Error("string input must have a nil conversion")
	}

	if ty, _ := convert.Unify([]cty.Type{cty.Number, cty.Bool}); ty != cty.NilType {
		t.Error("number and bool must not unify safely")
	}
	if ty, _ := convert.UnifyUnsafe([]cty.Type{cty.Number, cty.Bool}); ty != cty.NilType {
		t.Error("number and bool must not unify unsafely either")
	}

	objTy, _ := convert.Unify([]cty.Type{
		cty.Object(map[string]cty.Type{"a": cty.Number}),
		cty.Object(map[string]cty.Type{"a": cty.String}),
	})
	if !objTy.Equals(cty.Object(map[string]cty.Type{"a": cty.String})) {
		t.Errorf("object unification = %v", objTy.GoString())
	}

	lsTy, _ := convert.Unify([]cty.Type{cty.List(cty.String), cty.Set(cty.String)})
	if !lsTy.Equals(cty.List(cty.String)) {
		t.Errorf("list+set unification = %v", lsTy.GoString())
	}

	dynTy, _ := convert.Unify([]cty.Type{cty.Number, cty.DynamicPseudoType})
	if !dynTy.Equals(cty.DynamicPseudoType) {
		t.Errorf("dynamic pull = %v", dynTy.GoString())
	}

	single, scs := convert.Unify([]cty.Type{cty.Number})
	if !single.Equals(cty.Number) || len(scs) != 1 || scs[0] != nil {
		t.Error("singleton unification must return the type with nil conversion")
	}

	empty, ecs := convert.Unify([]cty.Type{})
	if empty != cty.NilType || ecs != nil {
		t.Error("empty unification must return NilType and nil conversions")
	}
}

func TestUnifiedConversionsProduceOneType(t *testing.T) {
	types := []cty.Type{cty.Number, cty.String, cty.Bool}
	vals := []cty.Value{cty.NumberIntVal(5), cty.StringVal("x"), cty.True}
	ty, cs := convert.UnifyUnsafe(types)
	if ty == cty.NilType {
		t.Fatal("num/str/bool must unify unsafely (to string)")
	}
	for i, v := range vals {
		out := v
		if cs[i] != nil {
			var err error
			out, err = cs[i](v)
			if err != nil {
				t.Fatalf("conversion %d failed: %v", i, err)
			}
		}
		if !out.Type().Equals(ty) {
			t.Errorf("converted value %d has type %v, want %v", i, out.Type().GoString(), ty.GoString())
		}
	}
}
