package atomic

import (
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestDiffEmptyOnEqualInputs(t *testing.T) {
	if d := cmp.Diff(Pt{1, 2}, Pt{1, 2}); d != "" {
		t.Fatalf("Diff of equal values must be empty, got %q", d)
	}
	if d := cmp.Diff(Pt{1, 2}, Pt{1, 3}); d == "" {
		t.Fatal("Diff of unequal values must be non-empty")
	}
}

func TestDiffPrefixesMarkSides(t *testing.T) {
	d := cmp.Diff(Pt{1, 2}, Pt{1, 3})
	var sawMinus, sawPlus bool
	for _, line := range strings.Split(d, "\n") {
		if strings.HasPrefix(line, "-") && strings.Contains(line, "2") {
			sawMinus = true
		}
		if strings.HasPrefix(line, "+") && strings.Contains(line, "3") {
			sawPlus = true
		}
	}
	if !sawMinus {
		t.Fatalf("no '-' line carrying the x-side value in:\n%s", d)
	}
	if !sawPlus {
		t.Fatalf("no '+' line carrying the y-side value in:\n%s", d)
	}
}

func TestDiffTypeMismatchNonEmpty(t *testing.T) {
	if cmp.Diff(1, "1") == "" {
		t.Fatal("a top-level type mismatch must yield a non-empty report")
	}
	if cmp.Diff(7, 7) != "" {
		t.Fatal("matching values of one type must yield an empty report")
	}
}

func TestDiffMentionsTransformerName(t *testing.T) {
	tr := cmp.Transformer("Mod10", func(x int) int { return x % 10 })
	d := cmp.Diff(3, 14, tr)
	if d == "" {
		t.Fatal("transformed values that still differ must yield a non-empty report")
	}
	if !strings.Contains(d, "Mod10") {
		t.Fatalf("the report must mention the participating transformer's name, got:\n%s", d)
	}
}

func TestDiffEmptyIffEqualUnderComparer(t *testing.T) {
	near := cmp.Comparer(func(x, y float64) bool {
		d := x - y
		return d < 0.01 && d > -0.01
	})
	if !cmp.Equal(1.000, 1.005, near) {
		t.Fatal("tolerance comparer must judge close floats equal")
	}
	if d := cmp.Diff(1.000, 1.005, near); d != "" {
		t.Fatalf("Diff must be empty exactly when Equal is true, got %q", d)
	}
	if cmp.Equal(1.000, 1.005) {
		t.Fatal("without the comparer the floats must be unequal")
	}
	if cmp.Diff(1.000, 1.005) == "" {
		t.Fatal("without the comparer the report must be non-empty")
	}
}
