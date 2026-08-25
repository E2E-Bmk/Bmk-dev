package integration

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
	"github.com/zclconf/go-cty/cty/convert"
	ctyjson "github.com/zclconf/go-cty/cty/json"
)

func TestConversionPreservesEqualityClasses(t *testing.T) {
	a := cty.ListVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(2)})
	b := cty.ListVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(2)})
	if !a.Equals(b).True() {
		t.Fatal("premise: a == b")
	}
	ca, err := convert.Convert(a, cty.List(cty.String))
	if err != nil {
		t.Fatalf("convert a: %v", err)
	}
	cb, err := convert.Convert(b, cty.List(cty.String))
	if err != nil {
		t.Fatalf("convert b: %v", err)
	}
	if !ca.Equals(cb).True() {
		t.Error("converted equal values must stay equal")
	}
	n, err := convert.Convert(cty.NullVal(cty.List(cty.Number)), cty.Set(cty.Number))
	if err != nil || !n.IsNull() || !n.Type().Equals(cty.Set(cty.Number)) {
		t.Errorf("null class = %#v, %v", n, err)
	}
	u, err := convert.Convert(cty.UnknownVal(cty.List(cty.Number)), cty.Set(cty.Number))
	if err != nil || u.IsKnown() || !u.Type().Equals(cty.Set(cty.Number)) {
		t.Errorf("unknown class = %#v, %v", u, err)
	}
}

func TestRefinedAnswersAgreeWithEventualValues(t *testing.T) {
	refined := cty.UnknownVal(cty.Number).Refine().
		NumberRangeInclusive(cty.Zero, cty.NumberIntVal(10)).
		NewValue()
	early := refined.GreaterThan(cty.NumberIntVal(20))
	if !early.IsKnown() {
		t.Fatal("out-of-range comparison must be known early")
	}
	for _, concrete := range []cty.Value{cty.Zero, cty.NumberIntVal(5), cty.NumberIntVal(10)} {
		late := concrete.GreaterThan(cty.NumberIntVal(20))
		if early.True() != late.True() {
			t.Errorf("early answer %v disagrees with concrete %#v -> %v", early.True(), concrete, late.True())
		}
	}

	exactLen := cty.UnknownVal(cty.List(cty.String)).Refine().CollectionLength(2).NewValue()
	earlyLen := exactLen.Length()
	concrete := cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("b")})
	if !earlyLen.RawEquals(concrete.Length()) {
		t.Error("refined length must equal the eventual concrete length")
	}

	notNull := cty.UnknownVal(cty.String).RefineNotNull()
	earlyEq := notNull.Equals(cty.NullVal(cty.String))
	lateEq := cty.StringVal("anything").Equals(cty.NullVal(cty.String))
	if earlyEq.True() != lateEq.True() {
		t.Error("non-null refinement answer must agree with any concrete non-null value")
	}
}

func TestMarksNeverAlterData(t *testing.T) {
	plainSum := cty.NumberIntVal(1).Add(cty.NumberIntVal(2))
	markedSum := cty.NumberIntVal(1).Mark("m").Add(cty.NumberIntVal(2).Mark("n"))
	content, marks := markedSum.Unmark()
	if !content.RawEquals(plainSum) {
		t.Error("marked operands must not change the numeric result")
	}
	if _, ok := marks["m"]; !ok {
		t.Error("result must carry mark m")
	}
	if _, ok := marks["n"]; !ok {
		t.Error("result must carry mark n (union)")
	}

	plainConv, err := convert.Convert(cty.NumberIntVal(5), cty.String)
	if err != nil {
		t.Fatal(err)
	}
	markedConv, err := convert.Convert(cty.NumberIntVal(5).Mark("m"), cty.String)
	if err != nil {
		t.Fatal(err)
	}
	mc, _ := markedConv.Unmark()
	if !mc.RawEquals(plainConv) {
		t.Error("marked conversion must not change the converted content")
	}
}

func TestTypeProjectionsAgree(t *testing.T) {
	v := cty.SetVal([]cty.Value{cty.StringVal("a")})
	ty := v.Type()
	if !ty.ElementType().Equals(v.AsValueSet().ElementType()) {
		t.Error("value type element and ValueSet element type disagree")
	}
	if !v.Range().TypeConstraint().Equals(ty) {
		t.Error("Range TypeConstraint disagrees with Type")
	}
	b, err := ctyjson.MarshalType(ty)
	if err != nil {
		t.Fatalf("MarshalType: %v", err)
	}
	back, err := ctyjson.UnmarshalType(b)
	if err != nil || !back.Equals(ty) {
		t.Errorf("type serialization round trip = %v, %v", back.GoString(), err)
	}
}

func TestIterationAgreesWithAccess(t *testing.T) {
	check := func(name string, v cty.Value) {
		t.Helper()
		count := 0
		v.ForEachElement(func(k, ev cty.Value) bool {
			count++
			if !v.HasIndex(k).True() {
				t.Errorf("%s: iterated key %#v not reported by HasIndex", name, k)
			}
			if !v.Index(k).RawEquals(ev) {
				t.Errorf("%s: Index(%#v) disagrees with iterated element", name, k)
			}
			return false
		})
		if count != v.LengthInt() {
			t.Errorf("%s: iterated %d elements, LengthInt=%d", name, count, v.LengthInt())
		}
	}
	check("list", cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("b")}))
	check("map", cty.MapVal(map[string]cty.Value{"x": cty.NumberIntVal(1), "y": cty.NumberIntVal(2)}))
	check("tuple", cty.TupleVal([]cty.Value{cty.True, cty.StringVal("s")}))
}

func TestEqualityLadderDisagreesExactlyAsSpecified(t *testing.T) {
	u1 := cty.UnknownVal(cty.Number)
	u2 := cty.UnknownVal(cty.Number)
	if !u1.RawEquals(u2) {
		t.Error("RawEquals must treat same-typed unknowns as equal")
	}
	if u1.Equals(u2).IsKnown() {
		t.Error("Equals must stay unknown for unknown operands")
	}

	m := cty.NumberIntVal(1).Mark("m")
	p := cty.NumberIntVal(1)
	if m.RawEquals(p) {
		t.Error("RawEquals must be mark-sensitive")
	}
	eq := m.Equals(p)
	if !eq.IsMarked() {
		t.Error("Equals must propagate the mark instead")
	}
	inner, _ := eq.Unmark()
	if !inner.True() {
		t.Error("Equals content must ignore the mark")
	}

	if !cty.List(cty.String).Equals(cty.List(cty.String)) {
		t.Error("type equality must hold for identical types")
	}
	if cty.ListValEmpty(cty.String).Equals(cty.SetValEmpty(cty.String)).True() {
		t.Error("values of different types must not be Equals-true")
	}
}

func TestWalkTransformAgree(t *testing.T) {
	o := cty.ObjectVal(map[string]cty.Value{
		"nums":  cty.ListVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(2)}),
		"label": cty.StringVal("x"),
	})
	var visited int
	err := cty.Walk(o, func(p cty.Path, v cty.Value) (bool, error) {
		visited++
		return true, nil
	})
	if err != nil {
		t.Fatalf("walk: %v", err)
	}
	// root + nums + 2 elements + label
	if visited != 5 {
		t.Errorf("walk visited %d nodes, want 5", visited)
	}

	pruned := 0
	_ = cty.Walk(o, func(p cty.Path, v cty.Value) (bool, error) {
		pruned++
		return false, nil
	})
	if pruned != 1 {
		t.Errorf("pruned walk visited %d nodes, want 1 (root only)", pruned)
	}

	doubled, err := cty.Transform(o, func(p cty.Path, v cty.Value) (cty.Value, error) {
		if v.Type() == cty.Number {
			return v.Multiply(cty.NumberIntVal(2)), nil
		}
		return v, nil
	})
	if err != nil {
		t.Fatalf("transform: %v", err)
	}
	want := cty.ObjectVal(map[string]cty.Value{
		"nums":  cty.ListVal([]cty.Value{cty.NumberIntVal(2), cty.NumberIntVal(4)}),
		"label": cty.StringVal("x"),
	})
	if !doubled.RawEquals(want) {
		t.Errorf("transform = %#v, want %#v", doubled, want)
	}

	_, err = cty.Transform(o, func(p cty.Path, v cty.Value) (cty.Value, error) {
		if v.Type() == cty.Number {
			return cty.NilVal, errFor("boom")
		}
		return v, nil
	})
	if err == nil || err.Error() != "boom" {
		t.Errorf("transform error propagation = %v", err)
	}
}

type errFor string

func (e errFor) Error() string { return string(e) }

func TestSetLevelMarksVisibleAcrossViews(t *testing.T) {
	s := cty.SetVal([]cty.Value{cty.StringVal("a").Mark("m"), cty.StringVal("b")})
	if !s.IsMarked() {
		t.Fatal("set with marked input must be marked as a whole")
	}
	asList, err := convert.Convert(s, cty.List(cty.String))
	if err != nil {
		t.Fatalf("marked set -> list: %v", err)
	}
	if !asList.IsMarked() {
		t.Error("conversion must keep the set-level mark")
	}
	inner, _ := asList.Unmark()
	if inner.LengthInt() != 2 {
		t.Error("both elements must survive")
	}
	if _, err := ctyjson.Marshal(s, cty.Set(cty.String)); err == nil {
		t.Error("marked set must refuse JSON serialization")
	}
	clean, _ := s.UnmarkDeep()
	if _, err := ctyjson.Marshal(clean, cty.Set(cty.String)); err != nil {
		t.Errorf("unmarked set must serialize: %v", err)
	}
}

func TestPathApplyAgreesWithDirectAccess(t *testing.T) {
	o := cty.ObjectVal(map[string]cty.Value{
		"servers": cty.ListVal([]cty.Value{
			cty.ObjectVal(map[string]cty.Value{"port": cty.NumberIntVal(80)}),
			cty.ObjectVal(map[string]cty.Value{"port": cty.NumberIntVal(443)}),
		}),
	})
	p := cty.GetAttrPath("servers").IndexInt(1).GetAttr("port")
	viaPath, err := p.Apply(o)
	if err != nil {
		t.Fatalf("apply: %v", err)
	}
	direct := o.GetAttr("servers").Index(cty.NumberIntVal(1)).GetAttr("port")
	if !viaPath.RawEquals(direct) {
		t.Errorf("path %#v disagrees with direct access %#v", viaPath, direct)
	}
}
