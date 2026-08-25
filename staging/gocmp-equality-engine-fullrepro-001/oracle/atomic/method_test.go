package atomic

import (
	"testing"

	"github.com/google/go-cmp/cmp"
)

type EqMod struct{ V int }

func (e EqMod) Equal(o EqMod) bool { return e.V%10 == o.V%10 }

type EqPtr struct{ V int }

func (e *EqPtr) Equal(o *EqPtr) bool {
	if e == nil || o == nil {
		return e == nil && o == nil
	}
	return e.V == o.V
}

type valIface interface{ Val() int }

type EqIface struct{ V int }

func (e EqIface) Val() int { return e.V }

func (e EqIface) Equal(o valIface) bool { return e.V%10 == o.Val()%10 }

func TestEqualMethodDecidesVerdict(t *testing.T) {
	if !cmp.Equal(EqMod{3}, EqMod{13}) {
		t.Fatal("the type's Equal method must decide the verdict (3 == 13 mod 10)")
	}
	if cmp.Equal(EqMod{3}, EqMod{4}) {
		t.Fatal("the type's Equal method must decide the verdict (3 != 4 mod 10)")
	}
}

func TestEqualMethodOnNilPointerReceiver(t *testing.T) {
	var a, b *EqPtr
	if !cmp.Equal(a, b) {
		t.Fatal("the Equal method must be consulted even when both values are nil")
	}
	if cmp.Equal(a, &EqPtr{1}) {
		t.Fatal("nil vs non-nil must be unequal per the Equal method")
	}
	if !cmp.Equal(&EqPtr{2}, &EqPtr{2}) {
		t.Fatal("non-nil receivers with equal payloads must compare equal via the method")
	}
}

func TestEqualMethodInterfaceForm(t *testing.T) {
	if !cmp.Equal(EqIface{3}, EqIface{13}) {
		t.Fatal("an Equal(I) bool method with T assignable to I must decide the verdict")
	}
	if cmp.Equal(EqIface{3}, EqIface{4}) {
		t.Fatal("the interface-form Equal method must also decide inequality")
	}
}

func TestComparerOverridesEqualMethod(t *testing.T) {
	exact := cmp.Comparer(func(a, b EqMod) bool { return a.V == b.V })
	if cmp.Equal(EqMod{3}, EqMod{13}, exact) {
		t.Fatal("an applicable Comparer must take precedence over the type's Equal method")
	}
	if !cmp.Equal(EqMod{3}, EqMod{3}, exact) {
		t.Fatal("the overriding Comparer must still judge identical values equal")
	}
}

func TestIgnoreOverridesEqualMethod(t *testing.T) {
	ig := cmp.FilterValues(func(a, b EqMod) bool { return true }, cmp.Ignore())
	if !cmp.Equal(EqMod{3}, EqMod{4}, ig) {
		t.Fatal("an applicable Ignore must take precedence over the type's Equal method")
	}
	if cmp.Equal(EqMod{3}, EqMod{4}) {
		t.Fatal("without the ignore the method must reject 3 vs 4")
	}
}
