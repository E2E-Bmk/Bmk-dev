package atomic

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
)

type auditMark string

func TestMarkAndInspect(t *testing.T) {
	m := auditMark("m")
	v := cty.NumberIntVal(1).Mark(m)
	if !v.IsMarked() || !v.HasMark(m) {
		t.Error("mark not visible after Mark")
	}
	if cty.NumberIntVal(1).IsMarked() {
		t.Error("fresh value must be unmarked")
	}
	twice := v.Mark(auditMark("n"))
	if len(twice.Marks()) != 2 {
		t.Error("repeated marking must accumulate distinct marks")
	}
	if !twice.HasMark(m) || !twice.HasMark(auditMark("n")) {
		t.Error("both marks must be present")
	}
}

func TestMarkPropagationThroughOps(t *testing.T) {
	m := auditMark("m")
	sum := cty.NumberIntVal(1).Mark(m).Add(cty.NumberIntVal(2))
	if !sum.IsMarked() || !sum.HasMark(m) {
		t.Error("Add must propagate marks")
	}
	un, _ := sum.Unmark()
	if !un.RawEquals(cty.NumberIntVal(3)) {
		t.Error("marked sum content wrong")
	}
	eq := cty.NumberIntVal(1).Mark(m).Equals(cty.NumberIntVal(1))
	if !eq.IsMarked() {
		t.Error("Equals must propagate marks to the boolean result")
	}
	uneq, _ := eq.Unmark()
	if !uneq.True() {
		t.Error("marked equality content wrong")
	}
	attr := cty.ObjectVal(map[string]cty.Value{"a": cty.StringVal("v")}).Mark(m).GetAttr("a")
	if !attr.IsMarked() {
		t.Error("GetAttr through marked object must yield marked attr")
	}
}

func TestUnmarkReturnsMarkSet(t *testing.T) {
	m := auditMark("m")
	v, marks := cty.NumberIntVal(1).Mark(m).Unmark()
	if v.IsMarked() {
		t.Error("Unmark result still marked")
	}
	if len(marks) != 1 {
		t.Errorf("mark set size = %d, want 1", len(marks))
	}
	if _, ok := marks[m]; !ok {
		t.Error("returned mark set must contain the original mark")
	}
}

func TestIntegrationMethodsPanicOnMarked(t *testing.T) {
	m := auditMark("m")
	mustPanic(t, "AsString on marked", func() { cty.StringVal("x").Mark(m).AsString() })
	mustPanic(t, "True on marked", func() { cty.True.Mark(m).True() })
	mustPanic(t, "LengthInt on marked", func() {
		cty.ListVal([]cty.Value{cty.True}).Mark(m).LengthInt()
	})
	mustPanic(t, "ElementIterator on marked", func() {
		cty.ListVal([]cty.Value{cty.True}).Mark(m).ElementIterator()
	})
}

func TestContainmentPredicates(t *testing.T) {
	m := auditMark("m")
	l := cty.ListVal([]cty.Value{cty.StringVal("a").Mark(m)})
	if l.IsMarked() {
		t.Error("container with marked element is not itself marked")
	}
	if !l.ContainsMarked() {
		t.Error("ContainsMarked must see nested marks")
	}
	if !l.HasMarkDeep(m) {
		t.Error("HasMarkDeep must see nested marks")
	}
	if l.HasMark(m) {
		t.Error("HasMark must not see nested marks")
	}
	a := cty.StringVal("x").Mark(m)
	b := cty.StringVal("y").Mark(m)
	if !a.HasSameMarks(b) {
		t.Error("same mark sets must compare equal")
	}
	if a.HasSameMarks(cty.StringVal("z")) {
		t.Error("marked vs unmarked must not have same marks")
	}
}

func TestRawEqualsIsMarkSensitive(t *testing.T) {
	m := auditMark("m")
	if cty.NumberIntVal(1).Mark(m).RawEquals(cty.NumberIntVal(1)) {
		t.Error("marked value must not be raw-equal to unmarked twin")
	}
	if !cty.NumberIntVal(1).Mark(m).RawEquals(cty.NumberIntVal(1).Mark(m)) {
		t.Error("identically marked values must be raw-equal")
	}
}

func TestDeepUnmarkAndPathRecords(t *testing.T) {
	m := auditMark("m")
	l := cty.ListVal([]cty.Value{cty.StringVal("a").Mark(m), cty.StringVal("b")})
	clean, all := l.UnmarkDeep()
	if clean.ContainsMarked() {
		t.Error("UnmarkDeep must strip nested marks")
	}
	if _, ok := all[m]; !ok || len(all) != 1 {
		t.Errorf("aggregate mark set wrong: %#v", all)
	}

	clean2, pvm := l.UnmarkDeepWithPaths()
	if clean2.ContainsMarked() || len(pvm) != 1 {
		t.Fatalf("UnmarkDeepWithPaths wrong: %#v", pvm)
	}
	if !pvm[0].Path.Equals(cty.IndexIntPath(0)) {
		t.Errorf("recorded path = %#v, want index 0", pvm[0].Path)
	}
	remarked := clean2.MarkWithPaths(pvm)
	if !remarked.Index(cty.NumberIntVal(0)).IsMarked() {
		t.Error("MarkWithPaths must restore the element mark")
	}
	if remarked.Index(cty.NumberIntVal(1)).IsMarked() {
		t.Error("unmarked element must stay unmarked")
	}
}

func TestSetValFlattensElementMarks(t *testing.T) {
	m := auditMark("m")
	s := cty.SetVal([]cty.Value{cty.StringVal("a").Mark(m), cty.StringVal("b")})
	if !s.IsMarked() {
		t.Error("set built from marked elements must be marked as a whole")
	}
	inner, marks := s.Unmark()
	if _, ok := marks[m]; !ok {
		t.Error("set-level mark set must contain the element mark")
	}
	if inner.ContainsMarked() {
		t.Error("set elements must not remain individually marked")
	}
	if inner.LengthInt() != 2 {
		t.Error("both elements must be present")
	}
}

func TestWithMarksAndNewValueMarks(t *testing.T) {
	v := cty.StringVal("x").WithMarks(cty.NewValueMarks("a", "b"))
	if len(v.Marks()) != 2 || !v.HasMark("a") || !v.HasMark("b") {
		t.Error("WithMarks must apply every mark in the set")
	}
	same := cty.StringVal("x").WithMarks(cty.NewValueMarks())
	if same.IsMarked() {
		t.Error("empty mark set must leave value unmarked")
	}
}
