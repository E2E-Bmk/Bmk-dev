package atomic

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
)

func TestEqualsKnownValues(t *testing.T) {
	if !cty.NumberIntVal(5).Equals(cty.NumberIntVal(5)).True() {
		t.Error("5 == 5 must be True")
	}
	if cty.StringVal("a").Equals(cty.StringVal("b")).True() {
		t.Error("a == b must be False")
	}
	if !cty.True.Equals(cty.True).True() {
		t.Error("true == true must be True")
	}
}

func TestEqualsCrossTypeFalse(t *testing.T) {
	res := cty.NumberIntVal(5).Equals(cty.StringVal("5"))
	if !res.IsKnown() {
		t.Fatal("cross-type equality of known values must be known")
	}
	if res.True() {
		t.Error("values of different types must not be equal")
	}
}

func TestEqualsNulls(t *testing.T) {
	if !cty.NullVal(cty.String).Equals(cty.NullVal(cty.String)).True() {
		t.Error("nulls of one type must be equal")
	}
	if !cty.NullVal(cty.DynamicPseudoType).Equals(cty.NullVal(cty.String)).True() {
		t.Error("dynamic null must equal typed null")
	}
	res := cty.NullVal(cty.String).Equals(cty.StringVal("x"))
	if !res.IsKnown() || res.True() {
		t.Error("null vs known value must be known False")
	}
}

func TestEqualsUnknownYieldsRefinedUnknownBool(t *testing.T) {
	res := cty.UnknownVal(cty.Number).Equals(cty.NumberIntVal(5))
	if res.IsKnown() {
		t.Fatal("equality with unknown operand must be unknown")
	}
	if !res.Type().Equals(cty.Bool) {
		t.Error("result type must be Bool")
	}
	if !res.Range().DefinitelyNotNull() {
		t.Error("unknown equality result must be refined non-null")
	}
	dres := cty.DynamicVal.Equals(cty.NumberIntVal(5))
	if dres.IsKnown() || !dres.Type().Equals(cty.Bool) {
		t.Error("DynamicVal equality must be unknown Bool")
	}
}

func TestNotEqual(t *testing.T) {
	if !cty.NumberIntVal(1).NotEqual(cty.NumberIntVal(2)).True() {
		t.Error("1 != 2 must be True")
	}
	if cty.NumberIntVal(1).NotEqual(cty.NumberIntVal(1)).True() {
		t.Error("1 != 1 must be False")
	}
}

func TestRawEqualsUnknowns(t *testing.T) {
	if !cty.UnknownVal(cty.Number).RawEquals(cty.UnknownVal(cty.Number)) {
		t.Error("same-typed unrefined unknowns must be raw-equal")
	}
	if cty.UnknownVal(cty.Number).RawEquals(cty.UnknownVal(cty.String)) {
		t.Error("unknowns of different types must not be raw-equal")
	}
	a := cty.UnknownVal(cty.Number).RefineNotNull()
	if a.RawEquals(cty.UnknownVal(cty.Number)) {
		t.Error("refined and unrefined unknowns must not be raw-equal")
	}
	if !a.RawEquals(cty.UnknownVal(cty.Number).RefineNotNull()) {
		t.Error("identically refined unknowns must be raw-equal")
	}
}

func TestArithmetic(t *testing.T) {
	sum := cty.NumberIntVal(2).Add(cty.NumberIntVal(3))
	if !sum.RawEquals(cty.NumberIntVal(5)) {
		t.Error("2+3 != 5")
	}
	if sum.RawEquals(cty.NumberIntVal(6)) {
		t.Error("2+3 must not equal 6")
	}
	if got, _ := sum.AsBigFloat().Int64(); got != 5 {
		t.Errorf("sum content = %d, want 5", got)
	}
	if !cty.NumberIntVal(2).Subtract(cty.NumberIntVal(3)).RawEquals(cty.NumberIntVal(-1)) {
		t.Error("2-3 != -1")
	}
	if !cty.NumberIntVal(4).Multiply(cty.NumberIntVal(3)).RawEquals(cty.NumberIntVal(12)) {
		t.Error("4*3 != 12")
	}
	if !cty.NumberIntVal(7).Negate().RawEquals(cty.NumberIntVal(-7)) {
		t.Error("negate wrong")
	}
	if cty.NumberIntVal(7).Negate().RawEquals(cty.NumberIntVal(7)) {
		t.Error("negate must change the sign")
	}
	if !cty.NumberIntVal(-7).Absolute().RawEquals(cty.NumberIntVal(7)) {
		t.Error("absolute wrong")
	}
}

func TestDivisionAndModulo(t *testing.T) {
	q := cty.NumberIntVal(5).Divide(cty.NumberIntVal(2))
	if !q.RawEquals(cty.NumberFloatVal(2.5)) {
		t.Error("5/2 != 2.5")
	}
	if q.RawEquals(cty.NumberIntVal(2)) {
		t.Error("5/2 must not truncate to 2")
	}
	if got, _ := q.AsBigFloat().Float64(); got != 2.5 {
		t.Errorf("quotient content = %v, want 2.5", got)
	}
	if !cty.NumberIntVal(5).Divide(cty.Zero).RawEquals(cty.PositiveInfinity) {
		t.Error("5/0 must be positive infinity")
	}
	if !cty.NumberIntVal(-5).Divide(cty.Zero).RawEquals(cty.NegativeInfinity) {
		t.Error("-5/0 must be negative infinity")
	}
	if cty.NumberIntVal(5).Divide(cty.Zero).RawEquals(cty.NegativeInfinity) {
		t.Error("5/0 must not be negative infinity")
	}
	m := cty.NumberIntVal(11).Modulo(cty.NumberIntVal(3))
	if !m.RawEquals(cty.NumberIntVal(2)) {
		t.Error("11%3 != 2")
	}
	if got, _ := m.AsBigFloat().Int64(); got != 2 {
		t.Errorf("modulo content = %d, want 2", got)
	}
	if !cty.NumberIntVal(5).Modulo(cty.Zero).RawEquals(cty.NumberIntVal(5)) {
		t.Error("modulo with zero divisor must return the dividend")
	}
}

func TestComparisons(t *testing.T) {
	if !cty.NumberIntVal(2).LessThan(cty.NumberIntVal(3)).True() {
		t.Error("2 < 3")
	}
	if !cty.NumberIntVal(3).GreaterThan(cty.NumberIntVal(2)).True() {
		t.Error("3 > 2")
	}
	if !cty.NumberIntVal(2).LessThanOrEqualTo(cty.NumberIntVal(2)).True() {
		t.Error("2 <= 2")
	}
	if !cty.NumberIntVal(2).GreaterThanOrEqualTo(cty.NumberIntVal(2)).True() {
		t.Error("2 >= 2")
	}
	if cty.NumberIntVal(3).LessThan(cty.NumberIntVal(2)).True() {
		t.Error("3 < 2 must be False")
	}
}

func TestBoolOps(t *testing.T) {
	if cty.True.And(cty.False).True() {
		t.Error("true AND false must be False")
	}
	if !cty.True.Or(cty.False).True() {
		t.Error("true OR false must be True")
	}
	if cty.True.Not().True() {
		t.Error("NOT true must be False")
	}
}

func TestOperationTypeMismatchPanics(t *testing.T) {
	mustPanic(t, "Add on strings", func() { cty.StringVal("a").Add(cty.StringVal("b")) })
	mustPanic(t, "And on numbers", func() { cty.NumberIntVal(1).And(cty.NumberIntVal(2)) })
	mustPanic(t, "Negate on bool", func() { cty.True.Negate() })
}

func TestUnknownOperandPropagation(t *testing.T) {
	res := cty.NumberIntVal(5).Add(cty.UnknownVal(cty.Number))
	if res.IsKnown() {
		t.Fatal("sum with unknown must be unknown")
	}
	if !res.Type().Equals(cty.Number) {
		t.Error("sum type must be Number")
	}
	if !res.Range().DefinitelyNotNull() {
		t.Error("unknown result of non-null operands must be refined non-null")
	}
	nres := cty.UnknownVal(cty.Bool).Not()
	if nres.IsKnown() || !nres.Type().Equals(cty.Bool) {
		t.Error("NOT unknown must be unknown Bool")
	}
	cres := cty.UnknownVal(cty.Number).LessThan(cty.Zero)
	if cres.IsKnown() || !cres.Type().Equals(cty.Bool) {
		t.Error("comparison with unknown must be unknown Bool")
	}
}

func TestListIndexing(t *testing.T) {
	l := cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("b")})
	if !l.Index(cty.NumberIntVal(1)).RawEquals(cty.StringVal("b")) {
		t.Error("Index(1) wrong")
	}
	if !l.HasIndex(cty.NumberIntVal(0)).True() {
		t.Error("HasIndex(0) must be True")
	}
	if l.HasIndex(cty.NumberIntVal(5)).True() {
		t.Error("HasIndex(5) must be False")
	}
	if !l.Length().RawEquals(cty.NumberIntVal(2)) {
		t.Error("Length wrong")
	}
	if l.LengthInt() != 2 {
		t.Error("LengthInt wrong")
	}
	mustPanic(t, "Index out of range", func() { l.Index(cty.NumberIntVal(9)) })
}

func TestMapIndexing(t *testing.T) {
	m := cty.MapVal(map[string]cty.Value{"a": cty.NumberIntVal(1), "b": cty.NumberIntVal(2)})
	if !m.Index(cty.StringVal("b")).RawEquals(cty.NumberIntVal(2)) {
		t.Error("map Index wrong")
	}
	if m.HasIndex(cty.StringVal("zzz")).True() {
		t.Error("HasIndex missing key must be False")
	}
	if !m.Length().RawEquals(cty.NumberIntVal(2)) {
		t.Error("map Length wrong")
	}
}

func TestTupleIndexing(t *testing.T) {
	tp := cty.TupleVal([]cty.Value{cty.StringVal("x"), cty.NumberIntVal(3)})
	if !tp.Index(cty.NumberIntVal(1)).RawEquals(cty.NumberIntVal(3)) {
		t.Error("tuple Index wrong")
	}
	if !tp.HasIndex(cty.NumberIntVal(0)).True() || tp.HasIndex(cty.NumberIntVal(2)).True() {
		t.Error("tuple HasIndex wrong")
	}
	if tp.LengthInt() != 2 {
		t.Error("tuple LengthInt wrong")
	}
}

func TestSetMembership(t *testing.T) {
	s := cty.SetVal([]cty.Value{cty.NumberIntVal(1), cty.NumberIntVal(2)})
	if !s.HasElement(cty.NumberIntVal(1)).True() {
		t.Error("HasElement present must be True")
	}
	if s.HasElement(cty.NumberIntVal(9)).True() {
		t.Error("HasElement absent must be False")
	}
	mustPanic(t, "HasIndex on set", func() { s.HasIndex(cty.NumberIntVal(1)) })
	mustPanic(t, "HasElement on list", func() {
		cty.ListVal([]cty.Value{cty.True}).HasElement(cty.True)
	})
}

func TestGetAttrBehavior(t *testing.T) {
	o := cty.ObjectVal(map[string]cty.Value{"name": cty.StringVal("n")})
	if !o.GetAttr("name").RawEquals(cty.StringVal("n")) {
		t.Error("GetAttr wrong")
	}
	mustPanic(t, "GetAttr missing", func() { o.GetAttr("nope") })
	u := cty.UnknownVal(cty.Object(map[string]cty.Type{"name": cty.String}))
	got := u.GetAttr("name")
	if got.IsKnown() || !got.Type().Equals(cty.String) {
		t.Error("GetAttr on unknown object must be unknown of attribute type")
	}
}

func TestLengthOnNullPanics(t *testing.T) {
	mustPanic(t, "Length on null list", func() { cty.NullVal(cty.List(cty.String)).Length() })
}

func TestSetWithUnknownsLengthRange(t *testing.T) {
	s := cty.SetVal([]cty.Value{cty.NumberIntVal(1), cty.UnknownVal(cty.Number)})
	ln := s.Length()
	if ln.IsKnown() {
		t.Fatal("length of set with unknown member must be unknown")
	}
	r := ln.Range()
	if !r.DefinitelyNotNull() {
		t.Error("unknown length must be refined non-null")
	}
	lo, loInc := r.NumberLowerBound()
	hi, hiInc := r.NumberUpperBound()
	if !lo.RawEquals(cty.NumberIntVal(1)) || !loInc {
		t.Errorf("lower bound = %#v inclusive=%v, want 1 inclusive", lo, loInc)
	}
	if !hi.RawEquals(cty.NumberIntVal(2)) || !hiInc {
		t.Errorf("upper bound = %#v inclusive=%v, want 2 inclusive", hi, hiInc)
	}
	if !s.HasElement(cty.NumberIntVal(1)).True() {
		t.Error("known member of mixed set must still be reported present")
	}
}

func TestIterationOrderAndEarlyStop(t *testing.T) {
	l := cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("b")})
	it := l.ElementIterator()
	var keys []int64
	var vals []string
	for it.Next() {
		k, v := it.Element()
		ki, _ := k.AsBigFloat().Int64()
		keys = append(keys, ki)
		vals = append(vals, v.AsString())
	}
	if len(keys) != 2 || keys[0] != 0 || keys[1] != 1 || vals[0] != "a" || vals[1] != "b" {
		t.Errorf("list iteration wrong: %v %v", keys, vals)
	}

	m := cty.MapVal(map[string]cty.Value{"b": cty.NumberIntVal(2), "a": cty.NumberIntVal(1), "c": cty.NumberIntVal(3)})
	var mkeys []string
	m.ForEachElement(func(k, v cty.Value) bool {
		mkeys = append(mkeys, k.AsString())
		return false
	})
	if len(mkeys) != 3 || mkeys[0] != "a" || mkeys[1] != "b" || mkeys[2] != "c" {
		t.Errorf("map iteration must be lexicographic by key: %v", mkeys)
	}

	n := 0
	stopped := l.ForEachElement(func(k, v cty.Value) bool { n++; return true })
	if n != 1 || !stopped {
		t.Errorf("early stop wrong: visited=%d stopped=%v", n, stopped)
	}
	full := l.ForEachElement(func(k, v cty.Value) bool { return false })
	if full {
		t.Error("uninterrupted iteration must report not-stopped")
	}
	mustPanic(t, "ElementIterator on unknown", func() {
		cty.UnknownVal(cty.List(cty.String)).ElementIterator()
	})
}

func TestNativeExtractors(t *testing.T) {
	l := cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("b")})
	sl := l.AsValueSlice()
	if len(sl) != 2 || !sl[1].RawEquals(cty.StringVal("b")) {
		t.Error("AsValueSlice wrong")
	}
	m := cty.MapVal(map[string]cty.Value{"k": cty.True})
	mm := m.AsValueMap()
	if len(mm) != 1 || !mm["k"].RawEquals(cty.True) {
		t.Error("AsValueMap wrong")
	}
	s := cty.SetVal([]cty.Value{cty.NumberIntVal(7)})
	vs := s.AsValueSet()
	if !vs.Has(cty.NumberIntVal(7)) || vs.Length() != 1 {
		t.Error("AsValueSet wrong")
	}
}

func TestCanIterateElements(t *testing.T) {
	yes := []cty.Value{
		cty.ListValEmpty(cty.String),
		cty.MapValEmpty(cty.String),
		cty.SetValEmpty(cty.String),
		cty.EmptyTupleVal,
		cty.EmptyObjectVal,
	}
	for _, v := range yes {
		if !v.CanIterateElements() {
			t.Errorf("%v must be iterable", v.Type().FriendlyName())
		}
	}
	if cty.StringVal("x").CanIterateElements() {
		t.Error("string must not be iterable")
	}
	if cty.NumberIntVal(1).CanIterateElements() {
		t.Error("number must not be iterable")
	}
}
