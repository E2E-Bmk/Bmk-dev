package integration

import (
	"testing"

	"github.com/google/go-cmp/cmp"
)

type Ring struct {
	V    int
	Next *Ring
}

type DNode struct {
	V          int
	Prev, Next *DNode
}

func ring1(v int) *Ring {
	r := &Ring{V: v}
	r.Next = r
	return r
}

func ring2(v1, v2 int) *Ring {
	a := &Ring{V: v1}
	b := &Ring{V: v2}
	a.Next = b
	b.Next = a
	return a
}

func TestEqualCyclesJudgedEqualByCycle(t *testing.T) {
	var r recorder
	if !cmp.Equal(ring1(7), ring1(7), cmp.Reporter(&r)) {
		t.Fatal("structurally identical cycles must compare equal")
	}
	var sawCycle bool
	for _, res := range r.results {
		if res.ByCycle() {
			sawCycle = true
			if !res.Equal() {
				t.Fatal("a cycle-closed leaf counts as equal")
			}
		}
	}
	if !sawCycle {
		t.Fatal("the closing leaf must carry the ByCycle cause")
	}
	if d := cmp.Diff(ring1(7), ring1(7)); d != "" {
		t.Fatalf("equal cycles must produce an empty report, got %q", d)
	}
}

func TestUnequalCyclicPayloadTerminates(t *testing.T) {
	if cmp.Equal(ring1(7), ring1(8)) {
		t.Fatal("cycles with different payloads must compare unequal")
	}
	if cmp.Diff(ring1(7), ring1(8)) == "" {
		t.Fatal("the unequal cyclic comparison must terminate with a non-empty report")
	}
}

func TestDifferentCycleLengthsUnequal(t *testing.T) {
	if cmp.Equal(ring1(7), ring2(7, 7)) {
		t.Fatal("cycles of different lengths must compare unequal rather than loop forever")
	}
	if cmp.Diff(ring1(7), ring2(7, 7)) == "" {
		t.Fatal("the mismatched-cycle comparison must terminate with a non-empty report")
	}
}

func TestDoublyLinkedCycleComparison(t *testing.T) {
	mk := func(v1, v2 int) *DNode {
		a := &DNode{V: v1}
		b := &DNode{V: v2}
		a.Next, a.Prev = b, b
		b.Next, b.Prev = a, a
		return a
	}
	if !cmp.Equal(mk(1, 2), mk(1, 2)) {
		t.Fatal("identical doubly-linked rings must compare equal")
	}
	if cmp.Equal(mk(1, 2), mk(1, 3)) {
		t.Fatal("doubly-linked rings with different payloads must compare unequal")
	}
	if d := cmp.Diff(mk(1, 2), mk(1, 2)); d != "" {
		t.Fatalf("the equal doubly-linked comparison must yield an empty report, got %q", d)
	}
}
