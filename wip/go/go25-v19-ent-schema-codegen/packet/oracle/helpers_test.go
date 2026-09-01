package entgate_test

import (
	"testing"

	"entgo.io/ent/entc/receipt"
	"entgo.io/ent/schema/field"
)

func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	nodeName := "User" + root
	empty := receipt.NewPlan()
	if _, err := empty.SelectNode(""); err == nil {
		t.Fatal("empty node accepted")
	}
	plan, err := empty.SelectNode(nodeName)
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeTables().IncludeArtifacts().IncludeDriverCalls()
	selected := receipt.NodeFact{Name: nodeName, Fields: []receipt.FieldFact{{Name: "id", Type: "int", Identity: true}, {Name: "name", Type: "string", Default: "unknown", Validators: []string{"not-empty"}}}, Edges: []receipt.EdgeFact{{Name: "groups", Target: "Group", Inverse: "users", Cardinality: "many", StorageOwner: "groups"}}, Indexes: []receipt.IndexFact{{Name: "user_name", Fields: []string{"name"}, Unique: true}}, Mixins: []string{"Time"}, Annotations: map[string]string{"root": root}}
	other := receipt.NodeFact{Name: "Group", Fields: []receipt.FieldFact{{Name: "id", Type: "int", Identity: true}}, Annotations: map[string]string{}}
	nodes := []receipt.NodeFact{other, selected}
	if family != "M-GRAPH-NORMALIZATION" {
		nodes = []receipt.NodeFact{selected, other}
	}
	artifacts := []receipt.ArtifactFact{{Path: "user_" + root + ".go", Digest: "digest-" + root, Declarations: []string{"User", "UserCreate"}, Compiles: true}}
	tables := []receipt.TableFact{{Name: "users_" + root, Columns: []receipt.ColumnFact{{Name: "id", Type: "integer", Identity: true}, {Name: "name", Type: "text", Default: "unknown"}}, Indexes: []receipt.IndexFact{{Name: "user_name", Fields: []string{"name"}, Unique: true}}, ForeignKeys: []string{"groups"}}}
	drivers := []receipt.DriverFact{{Operation: "insert", Table: "users_" + root, Arguments: []string{"name", "alice"}, Result: "id=1", Committed: true}}
	journal := receipt.NewDriverJournal()
	args := []string{"name", "alice"}
	entry := journal.Record(receipt.DriverFact{Operation: "insert", Table: "users_" + root, Arguments: args, Committed: true})
	args[0] = "mutated"
	if entry.Seq != 1 || journal.Entries()[0].Fact.Arguments[0] != "name" {
		t.Fatal("journal ownership failure")
	}
	got, err := receipt.Capture(plan, nodes, artifacts, tables, drivers, journal)
	if err != nil {
		t.Fatal(err)
	}
	if got.Digest() == "" || got.Validate() != nil {
		t.Fatal("invalid receipt generation")
	}
	nodes[0].Name = "mutated"
	if got.Nodes[0].Name == "mutated" {
		t.Fatal("capture retained caller storage")
	}
	switch family {
	case "M-SCHEMA-LOAD":
		bad := got
		bad.Nodes = nil
		if bad.Validate() == nil {
			t.Fatal("missing selected schema validated")
		}
	case "M-FIELD-TYPE-RULES":
		bad := got
		bad.Nodes = append([]receipt.NodeFact(nil), got.Nodes...)
		for i := range bad.Nodes {
			if bad.Nodes[i].Name == nodeName {
				bad.Nodes[i].Fields = append([]receipt.FieldFact(nil), bad.Nodes[i].Fields...)
				bad.Nodes[i].Fields[0].Optional = true
			}
		}
		if bad.Validate() == nil {
			t.Fatal("optional identity validated")
		}
	case "M-EDGE-INVERSE":
		bad := got
		bad.Nodes = append([]receipt.NodeFact(nil), got.Nodes...)
		for i := range bad.Nodes {
			if bad.Nodes[i].Name == nodeName {
				bad.Nodes[i].Edges = append([]receipt.EdgeFact(nil), bad.Nodes[i].Edges...)
				bad.Nodes[i].Edges[0].StorageOwner = ""
			}
		}
		if bad.Validate() == nil {
			t.Fatal("ownerless inverse edge validated")
		}
	case "M-INDEX-CONSTRAINT":
		bad := got
		bad.Nodes = append([]receipt.NodeFact(nil), got.Nodes...)
		for i := range bad.Nodes {
			if bad.Nodes[i].Name == nodeName {
				bad.Nodes[i].Indexes = append([]receipt.IndexFact(nil), bad.Nodes[i].Indexes...)
				bad.Nodes[i].Indexes[0].Fields = []string{"missing"}
			}
		}
		if bad.Validate() == nil {
			t.Fatal("index on missing field validated")
		}
	case "M-GRAPH-NORMALIZATION":
		equal, err := receipt.Capture(plan, []receipt.NodeFact{selected, other}, artifacts, tables, drivers, journal)
		if err != nil || got.Digest() != equal.Digest() {
			t.Fatal("independent graph order did not normalize")
		}
	case "M-CODEGEN-ARTIFACT":
		bad := got
		bad.Artifacts = append([]receipt.ArtifactFact(nil), got.Artifacts...)
		bad.Artifacts[0].Compiles = false
		if bad.Validate() == nil {
			t.Fatal("uncompilable artifact validated")
		}
	case "M-MIGRATION-DIFF":
		changedTables := append([]receipt.TableFact(nil), tables...)
		changedTables[0].Columns = append(changedTables[0].Columns, receipt.ColumnFact{Name: "email", Type: "text"})
		changed, err := receipt.Capture(plan, []receipt.NodeFact{selected, other}, artifacts, changedTables, drivers, journal)
		if err != nil || len(receipt.Diff(got, changed).Changes) != 1 {
			t.Fatal("migration change hidden")
		}
	case "M-CLI-API-EQUIVALENCE":
		equal, err := receipt.Capture(plan, []receipt.NodeFact{selected, other}, artifacts, tables, drivers, journal)
		if err != nil || !got.Equivalent(equal) {
			t.Fatal("equivalent API and command receipts disagree")
		}
	default:
		t.Fatalf("unknown family %q", family)
	}
}

func runNative(t *testing.T, root, _ string) {
	t.Helper()
	descriptor := field.String("name_" + root).Optional().Immutable().Default("default").Descriptor()
	if descriptor.Name != "name_"+root || !descriptor.Optional || !descriptor.Immutable || descriptor.Default != "default" || descriptor.Err != nil {
		t.Fatal("field descriptor drift")
	}
	enum := field.Enum("state_"+root).Values("new", "ready").Descriptor()
	if len(enum.Enums) != 2 || enum.Enums[0].V != "new" || enum.Enums[1].V != "ready" {
		t.Fatal("enum descriptor drift")
	}
}
