package integration

import (
	"strings"
	"testing"

	"github.com/zclconf/go-cty/cty"
	"github.com/zclconf/go-cty/cty/convert"
	ctyjson "github.com/zclconf/go-cty/cty/json"
	ctymsgpack "github.com/zclconf/go-cty/cty/msgpack"
)

func roundTripJSON(t *testing.T, v cty.Value, ty cty.Type) cty.Value {
	t.Helper()
	b, err := ctyjson.Marshal(v, ty)
	if err != nil {
		t.Fatalf("json marshal %#v: %v", v, err)
	}
	back, err := ctyjson.Unmarshal(b, ty)
	if err != nil {
		t.Fatalf("json unmarshal %s: %v", b, err)
	}
	return back
}

func TestJSONRoundTripIdentity(t *testing.T) {
	cases := []struct {
		v  cty.Value
		ty cty.Type
	}{
		{cty.StringVal("hello"), cty.String},
		{cty.MustParseNumberVal("3.14159265358979323846264338327950288419"), cty.Number},
		{cty.ListVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(2)}), cty.List(cty.Number)},
		{cty.SetVal([]cty.Value{cty.StringVal("b"), cty.StringVal("a")}), cty.Set(cty.String)},
		{cty.MapVal(map[string]cty.Value{"k": cty.True}), cty.Map(cty.Bool)},
		{cty.TupleVal([]cty.Value{cty.StringVal("x"), cty.NumberIntVal(1)}), cty.Tuple([]cty.Type{cty.String, cty.Number})},
		{
			cty.ObjectVal(map[string]cty.Value{
				"nested": cty.ListVal([]cty.Value{cty.ObjectVal(map[string]cty.Value{"a": cty.True})}),
			}),
			cty.Object(map[string]cty.Type{
				"nested": cty.List(cty.Object(map[string]cty.Type{"a": cty.Bool})),
			}),
		},
		{cty.NullVal(cty.List(cty.String)), cty.List(cty.String)},
	}
	for _, c := range cases {
		back := roundTripJSON(t, c.v, c.ty)
		if !back.RawEquals(c.v) {
			t.Errorf("round trip changed value: %#v -> %#v", c.v, back)
		}
		if back.RawEquals(cty.StringVal("sentinel-not-a-case")) {
			t.Errorf("round trip result claims equality with an unrelated value: %#v", back)
		}
	}
	b, err := ctyjson.Marshal(cty.StringVal("hello"), cty.String)
	if err != nil || string(b) != `"hello"` {
		t.Errorf("string document = %s, %v", b, err)
	}
	if got := roundTripJSON(t, cty.StringVal("hello"), cty.String).AsString(); got != "hello" {
		t.Errorf("decoded string content = %q, want hello", got)
	}
}

func TestJSONMarshalConvertsFirst(t *testing.T) {
	b, err := ctyjson.Marshal(cty.NumberIntVal(5), cty.String)
	if err != nil || string(b) != `"5"` {
		t.Errorf("marshal with conversion = %s, %v", b, err)
	}
	_, err = ctyjson.Marshal(cty.StringVal("bananas"), cty.Number)
	if err == nil {
		t.Error("inconvertible value must surface the conversion error")
	}
}

func TestJSONDynamicEmbedding(t *testing.T) {
	b, err := ctyjson.Marshal(cty.StringVal("x"), cty.DynamicPseudoType)
	if err != nil || string(b) != `{"value":"x","type":"string"}` {
		t.Errorf("dynamic wrapper = %s, %v", b, err)
	}
	nestedTy := cty.Object(map[string]cty.Type{"v": cty.DynamicPseudoType})
	nb, err := ctyjson.Marshal(cty.ObjectVal(map[string]cty.Value{"v": cty.NumberIntVal(7)}), nestedTy)
	if err != nil || string(nb) != `{"v":{"value":7,"type":"number"}}` {
		t.Errorf("nested dynamic = %s, %v", nb, err)
	}
	back, err := ctyjson.Unmarshal(nb, nestedTy)
	if err != nil {
		t.Fatalf("unmarshal nested dynamic: %v", err)
	}
	got := back.GetAttr("v")
	if !got.Type().Equals(cty.Number) || !got.RawEquals(cty.NumberIntVal(7)) {
		t.Errorf("recovered dynamic attr = %#v", got)
	}
}

func TestJSONUnmarshalObjectLenience(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"name": cty.String, "count": cty.Number})
	v, err := ctyjson.Unmarshal([]byte(`{"name":"n"}`), ty)
	if err != nil {
		t.Fatalf("missing attribute must be tolerated: %v", err)
	}
	if !v.GetAttr("count").RawEquals(cty.NullVal(cty.Number)) {
		t.Errorf("missing attribute must decode to typed null: %#v", v)
	}
	_, err = ctyjson.Unmarshal([]byte(`{"name":"n","count":1,"zzz":2}`), ty)
	if err == nil || !strings.Contains(err.Error(), "zzz") {
		t.Errorf("extraneous property error must name it: %v", err)
	}
	nv, err := ctyjson.Unmarshal([]byte(`null`), ty)
	if err != nil || !nv.RawEquals(cty.NullVal(ty)) {
		t.Errorf("null document = %#v, %v", nv, err)
	}
}

func TestImpliedTypeDecodeAgreesWithTypedDecode(t *testing.T) {
	doc := []byte(`{"name":"web","port":8080,"on":true}`)
	ity, err := ctyjson.ImpliedType(doc)
	if err != nil {
		t.Fatalf("ImpliedType: %v", err)
	}
	loose, err := ctyjson.Unmarshal(doc, ity)
	if err != nil {
		t.Fatalf("loose decode: %v", err)
	}
	declared := cty.Object(map[string]cty.Type{"name": cty.String, "port": cty.Number, "on": cty.Bool})
	converted, err := convert.Convert(loose, declared)
	if err != nil {
		t.Fatalf("convert loose->declared: %v", err)
	}
	typed, err := ctyjson.Unmarshal(doc, declared)
	if err != nil {
		t.Fatalf("typed decode: %v", err)
	}
	if !converted.RawEquals(typed) {
		t.Errorf("implied-then-convert %#v != typed decode %#v", converted, typed)
	}
	if got := typed.GetAttr("name").AsString(); got != "web" {
		t.Errorf("typed name = %q, want web", got)
	}
	if got, _ := converted.GetAttr("port").AsBigFloat().Int64(); got != 8080 {
		t.Errorf("converted port = %d, want 8080", got)
	}
	if !converted.GetAttr("on").True() {
		t.Error("converted on must be true")
	}
}

func TestMsgpackRoundTripBattery(t *testing.T) {
	cases := []struct {
		v  cty.Value
		ty cty.Type
	}{
		{cty.StringVal("hello"), cty.String},
		{cty.MustParseNumberVal("3.14159265358979323846264338327950288419"), cty.Number},
		{cty.SetVal([]cty.Value{cty.NumberIntVal(2), cty.NumberIntVal(1)}), cty.Set(cty.Number)},
		{cty.NullVal(cty.Object(map[string]cty.Type{"a": cty.String})), cty.Object(map[string]cty.Type{"a": cty.String})},
		{cty.TupleVal([]cty.Value{cty.True, cty.StringVal("x")}), cty.Tuple([]cty.Type{cty.Bool, cty.String})},
	}
	for _, c := range cases {
		b, err := ctymsgpack.Marshal(c.v, c.ty)
		if err != nil {
			t.Errorf("marshal %#v: %v", c.v, err)
			continue
		}
		back, err := ctymsgpack.Unmarshal(b, c.ty)
		if err != nil || !back.RawEquals(c.v) {
			t.Errorf("round trip changed value: %#v -> %#v (%v)", c.v, back, err)
		}
		if back.RawEquals(cty.StringVal("sentinel-not-a-case")) {
			t.Errorf("round trip result claims equality with an unrelated value: %#v", back)
		}
	}
	b, err := ctymsgpack.Marshal(cty.StringVal("hello"), cty.String)
	if err != nil {
		t.Fatalf("marshal string: %v", err)
	}
	back, err := ctymsgpack.Unmarshal(b, cty.String)
	if err != nil || back.AsString() != "hello" {
		t.Errorf("decoded string content = %#v, %v", back, err)
	}
}

func TestMsgpackUnknownPreservation(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"a": cty.String, "b": cty.Number})
	v := cty.ObjectVal(map[string]cty.Value{
		"a": cty.UnknownVal(cty.String),
		"b": cty.NumberIntVal(2),
	})
	b, err := ctymsgpack.Marshal(v, ty)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	back, err := ctymsgpack.Unmarshal(b, ty)
	if err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if back.GetAttr("a").IsKnown() {
		t.Error("unknown attribute must stay unknown")
	}
	if !back.GetAttr("a").Type().Equals(cty.String) {
		t.Error("unknown attribute type must be preserved")
	}
	if !back.GetAttr("b").RawEquals(cty.NumberIntVal(2)) {
		t.Error("known attribute must round trip")
	}
}

func TestMsgpackRefinementSuperset(t *testing.T) {
	in := cty.UnknownVal(cty.Number).Refine().
		NotNull().
		NumberRangeInclusive(cty.Zero, cty.NumberIntVal(10)).
		NewValue()
	b, err := ctymsgpack.Marshal(in, cty.Number)
	if err != nil {
		t.Fatalf("marshal refined: %v", err)
	}
	back, err := ctymsgpack.Unmarshal(b, cty.Number)
	if err != nil || back.IsKnown() {
		t.Fatalf("round trip = %#v, %v", back, err)
	}
	r := back.Range()
	if !r.DefinitelyNotNull() {
		t.Error("non-nullness must survive")
	}
	lo, loInc := r.NumberLowerBound()
	hi, hiInc := r.NumberUpperBound()
	if !lo.RawEquals(cty.Zero) || !loInc || !hi.RawEquals(cty.NumberIntVal(10)) || !hiInc {
		t.Errorf("bounds after round trip: [%#v %v, %#v %v]", lo, loInc, hi, hiInc)
	}
	over := back.GreaterThan(cty.NumberIntVal(20))
	if !over.IsKnown() || over.True() {
		t.Error("decoded refinement must still answer out-of-range comparisons")
	}
}

func TestMsgpackDynamicTypeEmbedding(t *testing.T) {
	b, err := ctymsgpack.Marshal(cty.NumberIntVal(1), cty.DynamicPseudoType)
	if err != nil {
		t.Fatalf("marshal dynamic: %v", err)
	}
	back, err := ctymsgpack.Unmarshal(b, cty.DynamicPseudoType)
	if err != nil || !back.RawEquals(cty.NumberIntVal(1)) {
		t.Errorf("dynamic round trip = %#v, %v", back, err)
	}
	if !back.Type().Equals(cty.Number) {
		t.Error("embedded type must be recovered")
	}
	if back.Type().Equals(cty.String) {
		t.Error("recovered type must not be string")
	}
	if got, _ := back.AsBigFloat().Int64(); got != 1 {
		t.Errorf("decoded content = %d, want 1", got)
	}
}

func TestCodecsAgreeOnKnownValues(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"name": cty.String, "count": cty.Number})
	v := cty.ObjectVal(map[string]cty.Value{"name": cty.StringVal("n"), "count": cty.NumberIntVal(3)})

	jb, err := ctyjson.Marshal(v, ty)
	if err != nil {
		t.Fatalf("json marshal: %v", err)
	}
	jv, err := ctyjson.Unmarshal(jb, ty)
	if err != nil {
		t.Fatalf("json unmarshal: %v", err)
	}

	mb, err := ctymsgpack.Marshal(v, ty)
	if err != nil {
		t.Fatalf("msgpack marshal: %v", err)
	}
	mv, err := ctymsgpack.Unmarshal(mb, ty)
	if err != nil {
		t.Fatalf("msgpack unmarshal: %v", err)
	}

	if !jv.RawEquals(mv) {
		t.Errorf("codecs disagree: json %#v vs msgpack %#v", jv, mv)
	}
	if got := jv.GetAttr("name").AsString(); got != "n" {
		t.Errorf("json-decoded name = %q, want n", got)
	}
	if got, _ := mv.GetAttr("count").AsBigFloat().Int64(); got != 3 {
		t.Errorf("msgpack-decoded count = %d, want 3", got)
	}

	jt, err := ctyjson.ImpliedType(jb)
	if err != nil {
		t.Fatalf("json ImpliedType: %v", err)
	}
	mt, err := ctymsgpack.ImpliedType(mb)
	if err != nil {
		t.Fatalf("msgpack ImpliedType: %v", err)
	}
	if !jt.Equals(mt) {
		t.Errorf("implied types disagree: %v vs %v", jt.GoString(), mt.GoString())
	}
	if jt.Equals(cty.Number) {
		t.Error("implied type of an object document must not be a primitive")
	}
}

func TestUnknownAsNullEnablesJSON(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"a": cty.String, "b": cty.Number})
	v := cty.ObjectVal(map[string]cty.Value{
		"a": cty.UnknownVal(cty.String),
		"b": cty.NumberIntVal(1),
	})
	if _, err := ctyjson.Marshal(v, ty); err == nil {
		t.Fatal("marshaling a value containing unknowns must fail")
	}
	flat := cty.UnknownAsNull(v)
	b, err := ctyjson.Marshal(flat, ty)
	if err != nil {
		t.Fatalf("marshal after UnknownAsNull: %v", err)
	}
	back, err := ctyjson.Unmarshal(b, ty)
	if err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	if !back.GetAttr("a").RawEquals(cty.NullVal(cty.String)) {
		t.Error("unknown must have been serialized as null")
	}
	if !back.GetAttr("b").RawEquals(cty.NumberIntVal(1)) {
		t.Error("known attr must survive")
	}
}
