package atomic

import (
	"math"
	"testing"

	"github.com/google/go-cmp/cmp"
)

type Pt struct{ X, Y int }

type Nested struct{ P Pt }

type IfaceHolder struct{ I interface{} }

func TestBoolEquality(t *testing.T) {
	if !cmp.Equal(true, true) {
		t.Fatal("identical booleans must compare equal")
	}
	if cmp.Equal(true, false) {
		t.Fatal("distinct booleans must compare unequal")
	}
}

func TestIntegerEquality(t *testing.T) {
	if !cmp.Equal(42, 42) {
		t.Fatal("identical integers must compare equal")
	}
	if cmp.Equal(42, 43) {
		t.Fatal("distinct integers must compare unequal")
	}
}

func TestFloatEquality(t *testing.T) {
	if !cmp.Equal(1.5, 1.5) {
		t.Fatal("identical floats must compare equal")
	}
	if cmp.Equal(1.5, 2.5) {
		t.Fatal("distinct floats must compare unequal")
	}
}

func TestNaNNeverEqualsNaN(t *testing.T) {
	if cmp.Equal(math.NaN(), math.NaN()) {
		t.Fatal("NaN must not equal NaN under default == semantics")
	}
	if !cmp.Equal(2.0, 2.0) {
		t.Fatal("ordinary floats must still compare equal")
	}
}

func TestComplexEquality(t *testing.T) {
	if !cmp.Equal(1+2i, 1+2i) {
		t.Fatal("identical complex numbers must compare equal")
	}
	if cmp.Equal(1+2i, 1+3i) {
		t.Fatal("distinct complex numbers must compare unequal")
	}
}

func TestStringEquality(t *testing.T) {
	if !cmp.Equal("go", "go") {
		t.Fatal("identical strings must compare equal")
	}
	if cmp.Equal("go", "Go") {
		t.Fatal("case-differing strings must compare unequal")
	}
}

func TestChannelEquality(t *testing.T) {
	a := make(chan int)
	b := make(chan int)
	if !cmp.Equal(a, a) {
		t.Fatal("a channel must equal itself under == semantics")
	}
	if cmp.Equal(a, b) {
		t.Fatal("distinct channels must compare unequal")
	}
}

func TestFunctionEquality(t *testing.T) {
	var fnil, gnil func()
	if !cmp.Equal(fnil, gnil) {
		t.Fatal("two nil functions must compare equal")
	}
	f := func() {}
	if cmp.Equal(f, f) {
		t.Fatal("non-nil functions are never equal, not even the same value")
	}
}

func TestStructFieldwiseEquality(t *testing.T) {
	if !cmp.Equal(Pt{1, 2}, Pt{1, 2}) {
		t.Fatal("structs with equal fields must compare equal")
	}
	if cmp.Equal(Pt{1, 2}, Pt{1, 3}) {
		t.Fatal("structs differing in one field must compare unequal")
	}
}

func TestNilSliceNotEqualEmptySlice(t *testing.T) {
	if cmp.Equal([]int(nil), []int{}) {
		t.Fatal("a nil slice must not equal an empty non-nil slice")
	}
	if !cmp.Equal([]int(nil), []int(nil)) {
		t.Fatal("two nil slices must compare equal")
	}
	if !cmp.Equal([]int{}, []int{}) {
		t.Fatal("two empty non-nil slices must compare equal")
	}
}

func TestSliceElementwiseEquality(t *testing.T) {
	if !cmp.Equal([]int{1, 2, 3}, []int{1, 2, 3}) {
		t.Fatal("slices with pairwise-equal elements must compare equal")
	}
	if cmp.Equal([]int{1, 2, 3}, []int{1, 2}) {
		t.Fatal("slices of different lengths must compare unequal")
	}
	if cmp.Equal([]int{1, 2, 3}, []int{1, 9, 3}) {
		t.Fatal("slices differing in one element must compare unequal")
	}
}

func TestNilMapNotEqualEmptyMap(t *testing.T) {
	if cmp.Equal(map[string]int(nil), map[string]int{}) {
		t.Fatal("a nil map must not equal an empty non-nil map")
	}
	if !cmp.Equal(map[string]int(nil), map[string]int(nil)) {
		t.Fatal("two nil maps must compare equal")
	}
}

func TestMapKeyAndValueEquality(t *testing.T) {
	if !cmp.Equal(map[string]int{"a": 1, "b": 2}, map[string]int{"b": 2, "a": 1}) {
		t.Fatal("maps with the same entries must compare equal regardless of construction order")
	}
	if cmp.Equal(map[string]int{"a": 1}, map[string]int{"a": 1, "b": 2}) {
		t.Fatal("maps with different key sets must compare unequal")
	}
	if cmp.Equal(map[string]int{"a": 1}, map[string]int{"a": 2}) {
		t.Fatal("maps differing in a value must compare unequal")
	}
}

func TestPointerEquality(t *testing.T) {
	var pnil, qnil *int
	if !cmp.Equal(pnil, qnil) {
		t.Fatal("two nil pointers must compare equal")
	}
	x, y := 5, 5
	if !cmp.Equal(&x, &y) {
		t.Fatal("distinct pointers to equal pointees must compare equal")
	}
	z := 6
	if cmp.Equal(&x, &z) {
		t.Fatal("pointers to unequal pointees must compare unequal")
	}
	if cmp.Equal(pnil, &x) {
		t.Fatal("a nil pointer must not equal a non-nil pointer")
	}
}

func TestInterfaceConcreteTypeRules(t *testing.T) {
	if !cmp.Equal(IfaceHolder{5}, IfaceHolder{5}) {
		t.Fatal("interfaces holding the same concrete type and equal values must compare equal")
	}
	if cmp.Equal(IfaceHolder{5}, IfaceHolder{"5"}) {
		t.Fatal("interfaces holding different concrete types must compare unequal")
	}
	if !cmp.Equal(IfaceHolder{nil}, IfaceHolder{nil}) {
		t.Fatal("two nil interfaces must compare equal")
	}
	if cmp.Equal(IfaceHolder{nil}, IfaceHolder{5}) {
		t.Fatal("a nil interface must not equal a non-nil one")
	}
}

func TestTopLevelTypeMismatchIsNotPanic(t *testing.T) {
	if cmp.Equal(1, "1") {
		t.Fatal("top-level arguments of different types must compare unequal")
	}
	if cmp.Diff(1, "1") == "" {
		t.Fatal("a top-level type mismatch must yield a non-empty report")
	}
}

func TestUntypedNilRootsEqual(t *testing.T) {
	if !cmp.Equal(nil, nil) {
		t.Fatal("two untyped nil arguments must compare equal")
	}
	if cmp.Equal(nil, 0) {
		t.Fatal("untyped nil must not equal a concrete value")
	}
}
