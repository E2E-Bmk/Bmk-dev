package atomic

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
)

func TestRefineNotNullVsNull(t *testing.T) {
	v := cty.UnknownVal(cty.String).RefineNotNull()
	if v.IsKnown() {
		t.Fatal("refined unknown must remain unknown")
	}
	res := v.Equals(cty.NullVal(cty.String))
	if !res.IsKnown() || res.True() {
		t.Error("non-null-refined unknown must compare known False to null")
	}
	plain := cty.UnknownVal(cty.String).Equals(cty.NullVal(cty.String))
	if plain.IsKnown() {
		t.Error("unrefined unknown vs null must stay unknown")
	}
}

func TestStringPrefixTrimming(t *testing.T) {
	trimmed := cty.UnknownVal(cty.String).Refine().StringPrefix("abce").NewValue()
	if got := trimmed.Range().StringPrefix(); got != "abc" {
		t.Errorf("StringPrefix must drop the combinable trailing letter: got %q", got)
	}
	full := cty.UnknownVal(cty.String).Refine().StringPrefixFull("abce").NewValue()
	if got := full.Range().StringPrefix(); got != "abce" {
		t.Errorf("StringPrefixFull must keep the prefix exactly: got %q", got)
	}
	url := cty.UnknownVal(cty.String).Refine().StringPrefix("https://").NewValue()
	if got := url.Range().StringPrefix(); got != "https://" {
		t.Errorf("prefix ending in %q must not be trimmed: got %q", "/", got)
	}
}

func TestNumberRangeKnownComparisons(t *testing.T) {
	v := cty.UnknownVal(cty.Number).Refine().
		NumberRangeInclusive(cty.Zero, cty.NumberIntVal(10)).
		NewValue()
	over := v.GreaterThan(cty.NumberIntVal(20))
	if !over.IsKnown() || over.True() {
		t.Error("value bounded by 10 must be known not greater than 20")
	}
	within := v.GreaterThan(cty.NumberIntVal(5))
	if within.IsKnown() {
		t.Error("comparison inside the range must stay unknown")
	}
	lo, loInc := v.Range().NumberLowerBound()
	hi, hiInc := v.Range().NumberUpperBound()
	if !lo.RawEquals(cty.Zero) || !loInc || !hi.RawEquals(cty.NumberIntVal(10)) || !hiInc {
		t.Error("range bounds must reflect the declared refinement")
	}
}

func TestCollectionLengthRefinement(t *testing.T) {
	v := cty.UnknownVal(cty.List(cty.String)).Refine().CollectionLength(2).NewValue()
	ln := v.Length()
	if !ln.IsKnown() || !ln.RawEquals(cty.NumberIntVal(2)) {
		t.Errorf("exact-length refinement must make Length known: %#v", ln)
	}
	bounded := cty.UnknownVal(cty.Set(cty.String)).Refine().
		CollectionLengthLowerBound(1).
		CollectionLengthUpperBound(5).
		NewValue()
	if bounded.Range().LengthLowerBound() != 1 || bounded.Range().LengthUpperBound() != 5 {
		t.Error("length bounds must be readable from the range")
	}
}

func TestRefineKnownValueSelfCheck(t *testing.T) {
	ok := cty.StringVal("https://x").Refine().StringPrefixFull("https://").NewValue()
	if !ok.RawEquals(cty.StringVal("https://x")) {
		t.Error("consistent refinement of a known value must return it unchanged")
	}
	mustPanic(t, "inconsistent prefix on known value", func() {
		cty.StringVal("nope").Refine().StringPrefixFull("https://").NewValue()
	})
}

func TestContradictoryRefinementPanics(t *testing.T) {
	mustPanic(t, "conflicting prefixes", func() {
		cty.UnknownVal(cty.String).Refine().
			StringPrefixFull("https://").
			StringPrefixFull("ftp://").
			NewValue()
	})
	mustPanic(t, "refine null as non-null", func() {
		cty.NullVal(cty.String).RefineNotNull()
	})
}

func TestRefineNullCollapses(t *testing.T) {
	v := cty.UnknownVal(cty.String).Refine().Null().NewValue()
	if !v.RawEquals(cty.NullVal(cty.String)) {
		t.Errorf("null refinement must collapse to the known null: %#v", v)
	}
	if !v.IsNull() || !v.IsKnown() {
		t.Errorf("collapsed value must be a known null: %#v", v)
	}
	if v.RawEquals(cty.NullVal(cty.Number)) {
		t.Error("collapsed null must keep the string type")
	}
}

func TestDynamicValIgnoresRefinements(t *testing.T) {
	got := cty.DynamicVal.RefineNotNull()
	if got != cty.DynamicVal {
		t.Error("DynamicVal must ignore refinement attempts")
	}
	if got.IsKnown() {
		t.Error("result must remain unknown")
	}
	if !got.Type().Equals(cty.DynamicPseudoType) {
		t.Error("result must keep the dynamic pseudo-type")
	}
}

func TestValueRangeProjections(t *testing.T) {
	if !cty.StringVal("foo").Range().DefinitelyNotNull() {
		t.Error("known non-null value must be definitely not null")
	}
	if cty.UnknownVal(cty.String).Range().DefinitelyNotNull() {
		t.Error("unrefined unknown must not be definitely not null")
	}
	if !cty.UnknownVal(cty.String).Range().CouldBeNull() {
		t.Error("unrefined unknown could be null")
	}
	if cty.UnknownVal(cty.String).RefineNotNull().Range().CouldBeNull() {
		t.Error("non-null-refined unknown must not could-be-null")
	}
	if !cty.UnknownVal(cty.Set(cty.String)).Range().TypeConstraint().Equals(cty.Set(cty.String)) {
		t.Error("TypeConstraint must report the value type")
	}
	r := cty.UnknownVal(cty.Number).Refine().
		NumberRangeInclusive(cty.Zero, cty.NumberIntVal(10)).
		NewValue().Range()
	out := r.Includes(cty.NumberIntVal(50))
	if !out.IsKnown() || out.True() {
		t.Error("Includes outside the range must be known False")
	}
	in := r.Includes(cty.NumberIntVal(5))
	if in.IsKnown() {
		t.Error("Includes inside the range must stay unknown")
	}
}
