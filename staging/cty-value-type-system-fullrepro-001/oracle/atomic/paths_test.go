package atomic

import (
	"strings"
	"testing"

	"github.com/zclconf/go-cty/cty"
)

func TestPathApplySuccess(t *testing.T) {
	o := cty.ObjectVal(map[string]cty.Value{
		"list": cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("b")}),
	})
	p := cty.GetAttrPath("list").IndexInt(1)
	got, err := p.Apply(o)
	if err != nil {
		t.Fatalf("Apply error: %v", err)
	}
	if !got.RawEquals(cty.StringVal("b")) {
		t.Errorf("Apply = %#v", got)
	}
	if s := got.AsString(); s != "b" {
		t.Errorf("Apply content = %q, want b", s)
	}
	mp := cty.GetAttrPath("list").Index(cty.NumberIntVal(0))
	got2, err := mp.Apply(o)
	if err != nil || !got2.RawEquals(cty.StringVal("a")) {
		t.Errorf("Apply via Index = %#v, %v", got2, err)
	}
	if s := got2.AsString(); s != "a" {
		t.Errorf("Apply via Index content = %q, want a", s)
	}
}

func TestPathApplyErrors(t *testing.T) {
	o := cty.ObjectVal(map[string]cty.Value{"a": cty.StringVal("v")})
	_, err := cty.GetAttrPath("nope").Apply(o)
	if err == nil || !strings.Contains(err.Error(), "at step 0") {
		t.Errorf("missing attribute error must name the step: %v", err)
	}
	l := cty.ListVal([]cty.Value{cty.StringVal("a")})
	_, err = cty.IndexIntPath(5).Apply(l)
	if err == nil || !strings.Contains(err.Error(), "at step 0") {
		t.Errorf("missing index error must name the step: %v", err)
	}
	nullObj := cty.NullVal(cty.Object(map[string]cty.Type{"a": cty.String}))
	_, err = cty.GetAttrPath("a").Apply(nullObj)
	if err == nil {
		t.Error("traversing a null must be an error, not a panic")
	}
	nested := cty.ObjectVal(map[string]cty.Value{"o": o})
	_, err = cty.GetAttrPath("o").GetAttr("zzz").Apply(nested)
	if err == nil || !strings.Contains(err.Error(), "at step 1") {
		t.Errorf("second-step failure must report step 1: %v", err)
	}
}

func TestPathEqualsAndHasPrefix(t *testing.T) {
	a := cty.GetAttrPath("a").IndexInt(0)
	b := cty.GetAttrPath("a").IndexInt(0)
	if !a.Equals(b) {
		t.Error("identical paths must be equal")
	}
	if a.Equals(cty.GetAttrPath("a").IndexInt(1)) {
		t.Error("paths with different keys must not be equal")
	}
	if !a.HasPrefix(cty.GetAttrPath("a")) {
		t.Error("prefix must be detected")
	}
	if a.HasPrefix(cty.GetAttrPath("b")) {
		t.Error("non-prefix must be rejected")
	}
}

func TestPathStepShapes(t *testing.T) {
	p := cty.GetAttrPath("name").IndexString("k").IndexInt(3)
	if len(p) != 3 {
		t.Fatalf("path length = %d", len(p))
	}
	ga, ok := p[0].(cty.GetAttrStep)
	if !ok || ga.Name != "name" {
		t.Errorf("step 0 = %#v, want GetAttrStep{name}", p[0])
	}
	is, ok := p[1].(cty.IndexStep)
	if !ok || !is.Key.RawEquals(cty.StringVal("k")) {
		t.Errorf("step 1 = %#v, want IndexStep{k}", p[1])
	}
	if !ok || is.Key.AsString() != "k" {
		t.Errorf("step 1 key content = %#v, want k", is.Key)
	}
	is2, ok := p[2].(cty.IndexStep)
	if !ok || !is2.Key.RawEquals(cty.NumberIntVal(3)) {
		t.Errorf("step 2 = %#v, want IndexStep{3}", p[2])
	}
	if !ok {
		t.Fatal("step 2 not an IndexStep")
	}
	if got, _ := is2.Key.AsBigFloat().Int64(); got != 3 {
		t.Errorf("step 2 key content = %d, want 3", got)
	}
	ip := cty.IndexPath(cty.NumberIntVal(1))
	if len(ip) != 1 {
		t.Error("IndexPath must start a one-step path")
	}
	sp := cty.IndexStringPath("s")
	if s0, ok := sp[0].(cty.IndexStep); !ok || !s0.Key.RawEquals(cty.StringVal("s")) || s0.Key.AsString() != "s" {
		t.Error("IndexStringPath step wrong")
	}
}

func TestPathCopyIndependence(t *testing.T) {
	base := cty.GetAttrPath("a")
	c := base.Copy()
	extended := c.GetAttr("b")
	if len(base) != 1 {
		t.Error("extending a copy must not affect the original")
	}
	if len(extended) != 2 {
		t.Error("extended copy must have both steps")
	}
	if !base.Equals(cty.GetAttrPath("a")) {
		t.Error("original path mutated")
	}
	if extended.Equals(base) {
		t.Error("diverged paths must not compare equal")
	}
}
