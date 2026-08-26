package atomic

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
)

func TestValueSetBasics(t *testing.T) {
	s := cty.NewValueSet(cty.String)
	if !s.ElementType().Equals(cty.String) {
		t.Error("ElementType wrong")
	}
	s.Add(cty.StringVal("a"))
	s.Add(cty.StringVal("a"))
	s.Add(cty.StringVal("b"))
	if s.Length() != 2 {
		t.Errorf("Length = %d, want 2", s.Length())
	}
	if !s.Has(cty.StringVal("a")) || s.Has(cty.StringVal("zzz")) {
		t.Error("Has wrong")
	}
	s.Remove(cty.StringVal("a"))
	if s.Has(cty.StringVal("a")) || s.Length() != 1 {
		t.Error("Remove wrong")
	}
	vals := s.Values()
	if len(vals) != 1 || !vals[0].RawEquals(cty.StringVal("b")) {
		t.Errorf("Values = %#v", vals)
	}
}

func TestValueSetCopyIndependence(t *testing.T) {
	s := cty.NewValueSet(cty.Number)
	s.Add(cty.NumberIntVal(1))
	c := s.Copy()
	c.Add(cty.NumberIntVal(2))
	if s.Length() != 1 || c.Length() != 2 {
		t.Error("Copy must be independent of the original")
	}
}

func TestValueSetAlgebra(t *testing.T) {
	a := cty.NewValueSet(cty.Number)
	a.Add(cty.NumberIntVal(1))
	a.Add(cty.NumberIntVal(2))
	b := cty.NewValueSet(cty.Number)
	b.Add(cty.NumberIntVal(2))
	b.Add(cty.NumberIntVal(3))

	u := a.Union(b)
	if u.Length() != 3 {
		t.Errorf("union length = %d, want 3", u.Length())
	}
	i := a.Intersection(b)
	if i.Length() != 1 || !i.Has(cty.NumberIntVal(2)) {
		t.Error("intersection wrong")
	}
	d := a.Subtract(b)
	if d.Length() != 1 || !d.Has(cty.NumberIntVal(1)) {
		t.Error("subtract wrong")
	}
	sd := a.SymmetricDifference(b)
	if sd.Length() != 2 || !sd.Has(cty.NumberIntVal(1)) || !sd.Has(cty.NumberIntVal(3)) {
		t.Error("symmetric difference wrong")
	}
}

func TestValueSetWrongTypePanics(t *testing.T) {
	s := cty.NewValueSet(cty.String)
	mustPanic(t, "Add wrong element type", func() { s.Add(cty.NumberIntVal(1)) })
}

func TestSetValFromValueSet(t *testing.T) {
	s := cty.NewValueSet(cty.String)
	s.Add(cty.StringVal("x"))
	s.Add(cty.StringVal("y"))
	v := cty.SetValFromValueSet(s)
	if !v.Type().Equals(cty.Set(cty.String)) {
		t.Error("resulting set type wrong")
	}
	if v.LengthInt() != 2 || !v.HasElement(cty.StringVal("x")).True() {
		t.Error("resulting set content wrong")
	}
}
