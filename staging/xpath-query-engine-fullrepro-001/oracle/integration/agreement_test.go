// Spec2Repo oracle - integration tests for xpath-query-engine-fullrepro-001
package integration

import (
	"fmt"
	"testing"
)

func TestSumAgreesWithPerNodeNumbers(t *testing.T) {
	doc := bookstore()
	var manual float64
	for k := 1; k <= 3; k++ {
		manual += evalNum(t, doc, fmt.Sprintf("number(//book[%d]/price)", k))
	}
	total := evalNum(t, doc, "sum(//price)")
	if total != manual {
		t.Fatalf("sum(//price) = %v, per-node numbers add to %v", total, manual)
	}
	if total != 109.97999999999999 {
		t.Fatalf("sum(//price) = %v, want 109.97999999999999", total)
	}
}

func TestAverageViaDivAgreesWithParts(t *testing.T) {
	doc := bookstore()
	sum := evalNum(t, doc, "sum(//price)")
	count := evalNum(t, doc, "count(//price)")
	if count != 3 {
		t.Fatalf("count(//price) = %v, want 3", count)
	}
	avg := evalNum(t, doc, "sum(//price) div count(//price)")
	if avg != sum/count {
		t.Fatalf("engine average %v differs from parts %v", avg, sum/count)
	}
	if avg != 36.66 {
		t.Fatalf("average = %v, want 36.66", avg)
	}
}

func TestPositionalSelectionAgreesWithIteration(t *testing.T) {
	doc := bookstore()
	vals := selValues(t, doc, "//author")
	if len(vals) != 4 {
		t.Fatalf("//author selected %d nodes, want 4", len(vals))
	}
	first := selValues(t, doc, "(//author)[1]")
	wantSlice(t, first, vals[:1], "(//author)[1]")
	last := selValues(t, doc, "(//author)[last()]")
	wantSlice(t, last, vals[len(vals)-1:], "(//author)[last()]")
	if got := evalStr(t, doc, "string((//author)[2])"); got != vals[1] {
		t.Fatalf("string((//author)[2]) = %q, iteration says %q", got, vals[1])
	}
}

func TestPredicateAgreesWithPerNodeEvaluation(t *testing.T) {
	doc := bookstore()
	filtered := selValues(t, doc, "//book[price > 30]/@id")
	var manual []string
	for k := 1; k <= 3; k++ {
		if evalBool(t, doc, fmt.Sprintf("//book[%d]/price > 30", k)) {
			manual = append(manual, evalStr(t, doc, fmt.Sprintf("string(//book[%d]/@id)", k)))
		}
	}
	wantSlice(t, filtered, manual, "predicate filter vs per-node comparisons")
	if len(filtered) == 0 {
		t.Fatal("no book matched the predicate; expected at least one")
	}
}

func TestUnionAgreesWithConcatenationDedup(t *testing.T) {
	doc := bookstore()
	left := selDesc(t, doc, "//book[2]/@id")
	right := selDesc(t, doc, "//book/@id")
	got := selDesc(t, doc, "//book[2]/@id | //book/@id")
	seen := map[string]bool{}
	var want []string
	for _, d := range append(append([]string{}, left...), right...) {
		if !seen[d] {
			seen[d] = true
			want = append(want, d)
		}
	}
	wantSlice(t, got, want, "union vs manual concatenate-and-dedup")
	if len(got) != 3 {
		t.Fatalf("union yielded %d nodes, want 3", len(got))
	}
}

func TestCountStringLengthComposition(t *testing.T) {
	doc := bookstore()
	// string-length(string(P)) must agree with string-length(P).
	direct := evalNum(t, doc, "string-length(//book[1]/title)")
	composed := evalNum(t, doc, "string-length(string(//book[1]/title))")
	if direct != composed {
		t.Fatalf("string-length direct %v != composed %v", direct, composed)
	}
	if direct != 16 {
		t.Fatalf("string-length = %v, want 16", direct)
	}
}
