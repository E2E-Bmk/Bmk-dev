package atomic

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
)

func mustPanic(t *testing.T, name string, f func()) {
	t.Helper()
	defer func() {
		if recover() == nil {
			t.Fatalf("%s: expected panic, got none", name)
		}
	}()
	f()
}

func TestPrimitiveTypeIdentity(t *testing.T) {
	for _, ty := range []cty.Type{cty.Number, cty.String, cty.Bool} {
		if !ty.IsPrimitiveType() {
			t.Errorf("%v: IsPrimitiveType = false", ty.FriendlyName())
		}
		if ty.IsCollectionType() {
			t.Errorf("%v: IsCollectionType = true", ty.FriendlyName())
		}
	}
	if cty.List(cty.String).IsPrimitiveType() {
		t.Error("list of string reported primitive")
	}
}

func TestCollectionKindPredicates(t *testing.T) {
	l := cty.List(cty.Number)
	m := cty.Map(cty.Bool)
	s := cty.Set(cty.String)
	for _, ty := range []cty.Type{l, m, s} {
		if !ty.IsCollectionType() {
			t.Errorf("%v: IsCollectionType = false", ty.FriendlyName())
		}
	}
	if !l.IsListType() || l.IsMapType() || l.IsSetType() {
		t.Error("list kind predicates wrong")
	}
	if !m.IsMapType() || m.IsListType() {
		t.Error("map kind predicates wrong")
	}
	if !s.IsSetType() || s.IsListType() {
		t.Error("set kind predicates wrong")
	}
	if !l.ElementType().Equals(cty.Number) {
		t.Error("list element type wrong")
	}
	if !m.ElementType().Equals(cty.Bool) {
		t.Error("map element type wrong")
	}
	if !s.ElementType().Equals(cty.String) {
		t.Error("set element type wrong")
	}
}

func TestKindSpecificElementAccessors(t *testing.T) {
	l := cty.List(cty.Number)
	if p := l.ListElementType(); p == nil || !p.Equals(cty.Number) {
		t.Error("ListElementType on list wrong")
	}
	if l.MapElementType() != nil || l.SetElementType() != nil {
		t.Error("non-matching kind accessors must return nil")
	}
	if cty.String.ListElementType() != nil {
		t.Error("ListElementType on primitive must return nil")
	}
	m := cty.Map(cty.String)
	if p := m.MapElementType(); p == nil || !p.Equals(cty.String) {
		t.Error("MapElementType on map wrong")
	}
	s := cty.Set(cty.Bool)
	if p := s.SetElementType(); p == nil || !p.Equals(cty.Bool) {
		t.Error("SetElementType on set wrong")
	}
}

func TestElementTypeOnNonCollectionPanics(t *testing.T) {
	mustPanic(t, "ElementType on string", func() { cty.String.ElementType() })
}

func TestObjectAttributeIntrospection(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"name": cty.String, "count": cty.Number})
	if !ty.IsObjectType() {
		t.Fatal("IsObjectType = false")
	}
	atys := ty.AttributeTypes()
	if len(atys) != 2 || !atys["name"].Equals(cty.String) || !atys["count"].Equals(cty.Number) {
		t.Errorf("AttributeTypes wrong: %#v", atys)
	}
	if !ty.AttributeType("count").Equals(cty.Number) {
		t.Error("AttributeType(count) wrong")
	}
	if !ty.HasAttribute("name") || ty.HasAttribute("missing") {
		t.Error("HasAttribute wrong")
	}
}

func TestObjectAttributeTypeMissingPanics(t *testing.T) {
	ty := cty.Object(map[string]cty.Type{"a": cty.String})
	mustPanic(t, "AttributeType missing", func() { ty.AttributeType("nope") })
}

func TestTupleElementIntrospection(t *testing.T) {
	ty := cty.Tuple([]cty.Type{cty.String, cty.Bool, cty.Number})
	if !ty.IsTupleType() {
		t.Fatal("IsTupleType = false")
	}
	if ty.Length() != 3 {
		t.Errorf("Length = %d, want 3", ty.Length())
	}
	if !ty.TupleElementType(1).Equals(cty.Bool) {
		t.Error("TupleElementType(1) wrong")
	}
	etys := ty.TupleElementTypes()
	if len(etys) != 3 || !etys[0].Equals(cty.String) || !etys[2].Equals(cty.Number) {
		t.Errorf("TupleElementTypes wrong: %#v", etys)
	}
}

func TestTypeLengthOnNonTuplePanics(t *testing.T) {
	mustPanic(t, "Length on list type", func() { cty.List(cty.String).Length() })
}

func TestTypeEqualityStructural(t *testing.T) {
	a := cty.Object(map[string]cty.Type{"a": cty.String, "b": cty.Number})
	b := cty.Object(map[string]cty.Type{"b": cty.Number, "a": cty.String})
	if !a.Equals(b) {
		t.Error("object equality must ignore constructor map order")
	}
	if cty.List(cty.String).Equals(cty.List(cty.Number)) {
		t.Error("lists of different element types must not be equal")
	}
	if cty.Tuple([]cty.Type{cty.String, cty.Number}).Equals(cty.Tuple([]cty.Type{cty.Number, cty.String})) {
		t.Error("tuple element order matters for equality")
	}
	if cty.List(cty.String).Equals(cty.Set(cty.String)) {
		t.Error("list and set of same element type must not be equal")
	}
}

func TestOptionalAttrsAffectTypeIdentity(t *testing.T) {
	opt := cty.ObjectWithOptionalAttrs(map[string]cty.Type{"a": cty.String, "b": cty.Number}, []string{"b"})
	plain := cty.Object(map[string]cty.Type{"a": cty.String, "b": cty.Number})
	if opt.Equals(plain) {
		t.Error("optional annotation must participate in type identity")
	}
	if !opt.WithoutOptionalAttributesDeep().Equals(plain) {
		t.Error("WithoutOptionalAttributesDeep must strip annotations")
	}
	if opt.AttributeOptional("a") || !opt.AttributeOptional("b") {
		t.Error("AttributeOptional wrong")
	}
	oa := opt.OptionalAttributes()
	if _, ok := oa["b"]; !ok || len(oa) != 1 {
		t.Errorf("OptionalAttributes wrong: %#v", oa)
	}
}

func TestConformanceDynamicWildcard(t *testing.T) {
	if errs := cty.List(cty.String).TestConformance(cty.DynamicPseudoType); len(errs) != 0 {
		t.Errorf("conformance to dynamic must succeed, got %v", errs)
	}
	if errs := cty.List(cty.String).TestConformance(cty.List(cty.DynamicPseudoType)); len(errs) != 0 {
		t.Errorf("conformance to list of dynamic must succeed, got %v", errs)
	}
	if errs := cty.List(cty.String).TestConformance(cty.List(cty.Number)); len(errs) == 0 {
		t.Error("conformance of list(string) to list(number) must fail")
	}
	if errs := cty.String.TestConformance(cty.String); len(errs) != 0 {
		t.Errorf("self conformance must succeed, got %v", errs)
	}
}

func TestFriendlyNames(t *testing.T) {
	if got := cty.List(cty.String).FriendlyName(); got != "list of string" {
		t.Errorf("FriendlyName list = %q", got)
	}
	if got := cty.Object(map[string]cty.Type{"a": cty.String}).FriendlyName(); got != "object" {
		t.Errorf("FriendlyName object = %q", got)
	}
	if got := cty.DynamicPseudoType.FriendlyName(); got != "dynamic" {
		t.Errorf("FriendlyName dynamic = %q", got)
	}
	if got := cty.DynamicPseudoType.FriendlyNameForConstraint(); got != "any type" {
		t.Errorf("FriendlyNameForConstraint dynamic = %q", got)
	}
}

func TestGoStringOfTypes(t *testing.T) {
	if got := cty.Map(cty.Bool).GoString(); got != "cty.Map(cty.Bool)" {
		t.Errorf("GoString = %q", got)
	}
	if got := cty.String.GoString(); got != "cty.String" {
		t.Errorf("GoString = %q", got)
	}
}

func TestHasDynamicTypesDeep(t *testing.T) {
	if !cty.Object(map[string]cty.Type{"a": cty.List(cty.DynamicPseudoType)}).HasDynamicTypes() {
		t.Error("nested dynamic not detected")
	}
	if cty.Object(map[string]cty.Type{"a": cty.List(cty.String)}).HasDynamicTypes() {
		t.Error("false positive for concrete type")
	}
}

func TestEmptyStructuralTypes(t *testing.T) {
	if !cty.EmptyObject.Equals(cty.Object(map[string]cty.Type{})) {
		t.Error("EmptyObject != Object(empty)")
	}
	if !cty.EmptyTuple.Equals(cty.Tuple([]cty.Type{})) {
		t.Error("EmptyTuple != Tuple(empty)")
	}
	if !cty.EmptyObjectVal.Type().Equals(cty.EmptyObject) {
		t.Error("EmptyObjectVal type wrong")
	}
	if !cty.EmptyTupleVal.Type().Equals(cty.EmptyTuple) {
		t.Error("EmptyTupleVal type wrong")
	}
	if cty.EmptyObjectVal.IsNull() || !cty.EmptyObjectVal.IsKnown() {
		t.Error("EmptyObjectVal must be known non-null")
	}
	if cty.EmptyObject.Equals(cty.EmptyTuple) {
		t.Error("empty object and empty tuple are distinct types")
	}
	if cty.EmptyObjectVal.Type().Equals(cty.Object(map[string]cty.Type{"a": cty.String})) {
		t.Error("EmptyObjectVal must have no attributes")
	}
	if got := cty.EmptyObjectVal.LengthInt(); got != 0 {
		t.Errorf("EmptyObjectVal length = %d, want 0", got)
	}
}
