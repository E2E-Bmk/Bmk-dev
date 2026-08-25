package atomic

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/zclconf/go-cty/cty"
	ctyjson "github.com/zclconf/go-cty/cty/json"
	ctymsgpack "github.com/zclconf/go-cty/cty/msgpack"
)

func TestJSONMarshalShapes(t *testing.T) {
	b, err := ctyjson.Marshal(cty.ListVal([]cty.Value{cty.True, cty.False}), cty.List(cty.Bool))
	if err != nil || string(b) != "[true,false]" {
		t.Errorf("list = %s, %v", b, err)
	}
	b, err = ctyjson.Marshal(cty.MapVal(map[string]cty.Value{"k": cty.NumberIntVal(1)}), cty.Map(cty.Number))
	if err != nil || string(b) != `{"k":1}` {
		t.Errorf("map = %s, %v", b, err)
	}
	b, err = ctyjson.Marshal(cty.NullVal(cty.String), cty.String)
	if err != nil || string(b) != "null" {
		t.Errorf("null = %s, %v", b, err)
	}
	pi := "3.14159265358979323846264338327950288419"
	b, err = ctyjson.Marshal(cty.MustParseNumberVal(pi), cty.Number)
	if err != nil || string(b) != pi {
		t.Errorf("number precision = %s, %v", b, err)
	}
}

func TestJSONMarshalRefusals(t *testing.T) {
	_, err := ctyjson.Marshal(cty.UnknownVal(cty.String), cty.String)
	if err == nil || !strings.Contains(err.Error(), "not known") {
		t.Errorf("unknown refusal = %v", err)
	}
	_, err = ctyjson.Marshal(cty.StringVal("x").Mark("m"), cty.String)
	if err == nil || !strings.Contains(err.Error(), "marks") {
		t.Errorf("marked refusal = %v", err)
	}
}

func TestJSONTypeSerialization(t *testing.T) {
	b, err := ctyjson.MarshalType(cty.String)
	if err != nil || string(b) != `"string"` {
		t.Errorf("primitive type = %s, %v", b, err)
	}
	b, err = ctyjson.MarshalType(cty.List(cty.Object(map[string]cty.Type{"a": cty.String})))
	if err != nil || string(b) != `["list",["object",{"a":"string"}]]` {
		t.Errorf("compound type = %s, %v", b, err)
	}
	for _, ty := range []cty.Type{
		cty.Number,
		cty.Set(cty.Number),
		cty.Map(cty.Bool),
		cty.Tuple([]cty.Type{cty.String, cty.Number}),
		cty.Object(map[string]cty.Type{"x": cty.List(cty.String)}),
		cty.DynamicPseudoType,
	} {
		bb, err := ctyjson.MarshalType(ty)
		if err != nil {
			t.Errorf("MarshalType(%v): %v", ty.GoString(), err)
			continue
		}
		back, err := ctyjson.UnmarshalType(bb)
		if err != nil || !back.Equals(ty) {
			t.Errorf("type round trip %v -> %s -> %v (%v)", ty.GoString(), bb, back.GoString(), err)
		}
	}
}

func TestJSONImpliedType(t *testing.T) {
	ty, err := ctyjson.ImpliedType([]byte(`{"a":1,"b":[true,"x"],"c":null}`))
	if err != nil {
		t.Fatalf("ImpliedType error: %v", err)
	}
	want := cty.Object(map[string]cty.Type{
		"a": cty.Number,
		"b": cty.Tuple([]cty.Type{cty.Bool, cty.String}),
		"c": cty.DynamicPseudoType,
	})
	if !ty.Equals(want) {
		t.Errorf("ImpliedType = %v, want %v", ty.GoString(), want.GoString())
	}
	_, err = ctyjson.ImpliedType([]byte(`{`))
	if err == nil {
		t.Error("malformed JSON must yield an error")
	}
}

func TestSimpleJSONValue(t *testing.T) {
	b, err := json.Marshal(ctyjson.SimpleJSONValue{Value: cty.NumberIntVal(43)})
	if err != nil || string(b) != "43" {
		t.Errorf("marshal = %s, %v", b, err)
	}
	var arr ctyjson.SimpleJSONValue
	if err := json.Unmarshal([]byte(`[1,"a",true]`), &arr); err != nil {
		t.Fatalf("unmarshal array: %v", err)
	}
	if !arr.Value.Type().Equals(cty.Tuple([]cty.Type{cty.Number, cty.String, cty.Bool})) {
		t.Errorf("array type = %v", arr.Value.Type().GoString())
	}
	var obj ctyjson.SimpleJSONValue
	if err := json.Unmarshal([]byte(`{"a":1}`), &obj); err != nil {
		t.Fatalf("unmarshal object: %v", err)
	}
	if !obj.Value.Type().Equals(cty.Object(map[string]cty.Type{"a": cty.Number})) {
		t.Errorf("object type = %v", obj.Value.Type().GoString())
	}
	var nl ctyjson.SimpleJSONValue
	if err := json.Unmarshal([]byte(`null`), &nl); err != nil {
		t.Fatalf("unmarshal null: %v", err)
	}
	if !nl.Value.RawEquals(cty.NullVal(cty.DynamicPseudoType)) {
		t.Errorf("null = %#v", nl.Value)
	}
}

func TestMsgpackRoundTripKnown(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"name": cty.String, "count": cty.Number})
	v := cty.ObjectVal(map[string]cty.Value{"name": cty.StringVal("n"), "count": cty.NumberIntVal(3)})
	b, err := ctymsgpack.Marshal(v, ty)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	back, err := ctymsgpack.Unmarshal(b, ty)
	if err != nil || !back.RawEquals(v) {
		t.Errorf("round trip = %#v, %v", back, err)
	}
	if got := back.GetAttr("name").AsString(); got != "n" {
		t.Errorf("decoded name = %q, want n", got)
	}
	if got, _ := back.GetAttr("count").AsBigFloat().Int64(); got != 3 {
		t.Errorf("decoded count = %d, want 3", got)
	}
	ity, err := ctymsgpack.ImpliedType(b)
	if err != nil || !ity.Equals(ty) {
		t.Errorf("ImpliedType = %v, %v", ity.GoString(), err)
	}
	if ity.Equals(cty.String) {
		t.Error("implied type must not be a primitive")
	}
}

func TestMsgpackUnknownAndRefinements(t *testing.T) {
	b, err := ctymsgpack.Marshal(cty.UnknownVal(cty.String), cty.String)
	if err != nil {
		t.Fatalf("marshal unknown: %v", err)
	}
	back, err := ctymsgpack.Unmarshal(b, cty.String)
	if err != nil || back.IsKnown() || !back.Type().Equals(cty.String) {
		t.Errorf("unknown round trip = %#v, %v", back, err)
	}

	refined := cty.UnknownVal(cty.String).Refine().
		NotNull().
		StringPrefixFull("https://").
		NewValue()
	b2, err := ctymsgpack.Marshal(refined, cty.String)
	if err != nil {
		t.Fatalf("marshal refined: %v", err)
	}
	back2, err := ctymsgpack.Unmarshal(b2, cty.String)
	if err != nil || back2.IsKnown() {
		t.Fatalf("refined round trip = %#v, %v", back2, err)
	}
	if !back2.Range().DefinitelyNotNull() {
		t.Error("non-nullness must survive the round trip")
	}
	if got := back2.Range().StringPrefix(); got != "https://" {
		t.Errorf("string prefix after round trip = %q", got)
	}
}

func TestMsgpackMarkedRefused(t *testing.T) {
	_, err := ctymsgpack.Marshal(cty.StringVal("x").Mark("m"), cty.String)
	if err == nil || !strings.Contains(err.Error(), "marks") {
		t.Errorf("marked refusal = %v", err)
	}
}
