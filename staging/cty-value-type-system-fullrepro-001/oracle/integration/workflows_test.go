package integration

import (
	"testing"

	"github.com/zclconf/go-cty/cty"
	"github.com/zclconf/go-cty/cty/convert"
	ctyjson "github.com/zclconf/go-cty/cty/json"
	ctymsgpack "github.com/zclconf/go-cty/cty/msgpack"
)

func TestConfigNormalizationWorkflow(t *testing.T) {
	schema := cty.Object(map[string]cty.Type{
		"name": cty.String,
		"port": cty.Number,
		"tags": cty.Set(cty.String),
	})
	input := cty.ObjectVal(map[string]cty.Value{
		"name": cty.StringVal("web"),
		"port": cty.StringVal("8080"),
		"tags": cty.ListVal([]cty.Value{cty.StringVal("a"), cty.StringVal("a")}),
	})
	v, err := convert.Convert(input, schema)
	if err != nil {
		t.Fatalf("normalize: %v", err)
	}
	if !v.GetAttr("port").RawEquals(cty.NumberIntVal(8080)) {
		t.Error("port must be converted to a number")
	}
	if v.GetAttr("tags").LengthInt() != 1 {
		t.Error("tag list must deduplicate into the set")
	}

	buf, err := ctyjson.Marshal(v, schema)
	if err != nil {
		t.Fatalf("store: %v", err)
	}
	restored, err := ctyjson.Unmarshal(buf, schema)
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if !restored.RawEquals(v) {
		t.Errorf("stored and restored configs differ: %#v vs %#v", v, restored)
	}

	bad := cty.ObjectVal(map[string]cty.Value{
		"name": cty.StringVal("web"),
		"port": cty.StringVal("eighty"),
		"tags": cty.ListValEmpty(cty.String),
	})
	if _, err := convert.Convert(bad, schema); err == nil {
		t.Error("non-numeric port must be a conversion error, not a panic")
	}
}

func TestPartialEvaluationWorkflow(t *testing.T) {
	count := cty.UnknownVal(cty.Number).Refine().
		NotNull().
		NumberRangeInclusive(cty.Zero, cty.NumberIntVal(10)).
		NewValue()

	over := count.GreaterThan(cty.NumberIntVal(20))
	if !over.IsKnown() || over.True() {
		t.Error("range refinement must answer the out-of-range comparison now")
	}

	sum := count.Add(cty.NumberIntVal(1)).Mark("audit")
	if !sum.IsMarked() || sum.IsKnown() {
		t.Error("sum must be a marked unknown")
	}

	buf, err := ctymsgpack.Marshal(count, cty.Number)
	if err != nil {
		t.Fatalf("ship: %v", err)
	}
	later, err := ctymsgpack.Unmarshal(buf, cty.Number)
	if err != nil {
		t.Fatalf("receive: %v", err)
	}
	if later.IsKnown() {
		t.Fatal("shipped unknown must stay unknown")
	}
	stillOver := later.GreaterThan(cty.NumberIntVal(20))
	if !stillOver.IsKnown() || stillOver.True() {
		t.Error("refinements must keep working after the round trip")
	}

	plain, marks := sum.Unmark()
	if plain.IsMarked() {
		t.Error("Unmark must strip the mark")
	}
	if _, ok := marks["audit"]; !ok {
		t.Error("mark set must surface at the integration boundary")
	}

	final := cty.NumberIntVal(4)
	if final.GreaterThan(cty.NumberIntVal(20)).True() != over.True() {
		t.Error("early refined answer must agree with the concrete outcome")
	}
}

func TestSchemaEvolutionWorkflow(t *testing.T) {
	oldSchema := cty.Object(map[string]cty.Type{"name": cty.String})
	newSchema := cty.ObjectWithOptionalAttrs(map[string]cty.Type{
		"name":    cty.String,
		"retries": cty.Number,
	}, []string{"retries"})

	oldDoc := []byte(`{"name":"svc"}`)
	oldVal, err := ctyjson.Unmarshal(oldDoc, oldSchema)
	if err != nil {
		t.Fatalf("decode old: %v", err)
	}
	upgraded, err := convert.Convert(oldVal, newSchema)
	if err != nil {
		t.Fatalf("upgrade: %v", err)
	}
	if !upgraded.GetAttr("retries").RawEquals(cty.NullVal(cty.Number)) {
		t.Error("missing optional attribute must become a typed null")
	}

	storeTy := upgraded.Type()
	buf, err := ctyjson.Marshal(upgraded, storeTy)
	if err != nil {
		t.Fatalf("store upgraded: %v", err)
	}
	restored, err := ctyjson.Unmarshal(buf, storeTy)
	if err != nil || !restored.RawEquals(upgraded) {
		t.Errorf("round trip after upgrade: %#v, %v", restored, err)
	}
}

func TestSensitiveDataAuditWorkflow(t *testing.T) {
	config := cty.ObjectVal(map[string]cty.Value{
		"user":     cty.StringVal("admin"),
		"password": cty.StringVal("hunter2").Mark("sensitive"),
	})

	if config.IsMarked() {
		t.Fatal("container must not be marked; only the element is")
	}
	if !config.ContainsMarked() {
		t.Fatal("audit must detect nested sensitive data")
	}

	clean, records := config.UnmarkDeepWithPaths()
	if len(records) != 1 {
		t.Fatalf("expected one sensitive record, got %d", len(records))
	}
	if !records[0].Path.Equals(cty.GetAttrPath("password")) {
		t.Errorf("recorded path = %#v", records[0].Path)
	}

	buf, err := ctyjson.Marshal(clean, clean.Type())
	if err != nil {
		t.Fatalf("serialize after unmark: %v", err)
	}
	restored, err := ctyjson.Unmarshal(buf, clean.Type())
	if err != nil {
		t.Fatalf("decode: %v", err)
	}
	remarked := restored.MarkWithPaths(records)
	if !remarked.GetAttr("password").IsMarked() {
		t.Error("sensitive mark must be restorable after the round trip")
	}
	if remarked.GetAttr("user").IsMarked() {
		t.Error("non-sensitive attribute must stay unmarked")
	}
	via, err := records[0].Path.Apply(remarked)
	if err != nil {
		t.Fatalf("path apply on remarked: %v", err)
	}
	if !via.IsMarked() {
		t.Error("path application must observe the restored mark")
	}
}

func TestTypeInferenceWorkflow(t *testing.T) {
	doc := []byte(`{"replicas":3,"regions":["eu","us"]}`)
	ity, err := ctyjson.ImpliedType(doc)
	if err != nil {
		t.Fatalf("infer: %v", err)
	}
	loose, err := ctyjson.Unmarshal(doc, ity)
	if err != nil {
		t.Fatalf("decode loose: %v", err)
	}

	declared := cty.Object(map[string]cty.Type{
		"replicas": cty.Number,
		"regions":  cty.Set(cty.String),
	})
	v, err := convert.Convert(loose, declared)
	if err != nil {
		t.Fatalf("conform: %v", err)
	}

	doubled := v.GetAttr("replicas").Multiply(cty.NumberIntVal(2))
	if !doubled.RawEquals(cty.NumberIntVal(6)) {
		t.Error("arithmetic on conformed data wrong")
	}
	if !v.GetAttr("regions").HasElement(cty.StringVal("eu")).True() {
		t.Error("set membership on conformed data wrong")
	}

	out := cty.ObjectVal(map[string]cty.Value{
		"replicas": doubled,
		"regions":  v.GetAttr("regions"),
	})
	outTy := out.Type()
	buf, err := ctyjson.Marshal(out, outTy)
	if err != nil {
		t.Fatalf("emit: %v", err)
	}
	back, err := ctyjson.Unmarshal(buf, outTy)
	if err != nil || !back.RawEquals(out) {
		t.Errorf("emitted document round trip: %#v, %v", back, err)
	}
}
