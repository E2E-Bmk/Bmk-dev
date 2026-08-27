package kustomizegate_test

import (
	"crypto/sha256"
	"encoding/hex"
	"sigs.k8s.io/kustomize/api/hasher"
	"sigs.k8s.io/kustomize/api/receipt"
	"testing"
)

func sum(s string) string { h := sha256.Sum256([]byte(s)); return hex.EncodeToString(h[:]) }
func buildReceipt(t *testing.T, root string) receipt.BuildReceipt {
	t.Helper()
	plan := receipt.NewBuildPlan()
	files := []string{"kustomization.yaml", "base.yaml"}
	if _, err := plan.SelectTarget("", files); err == nil {
		t.Fatal("empty target accepted")
	}
	plan, err := plan.SelectTarget("overlay-"+root, files)
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeResources().IncludeTransforms().IncludeFiles().IncludeLocalization()
	configID := "config-abc123"
	deployID := "deployment-" + root
	resources := []receipt.ResourceFact{{ID: "ConfigMap/config", OriginalID: "config", CurrentID: configID, Kind: "ConfigMap", ContentHash: "abc123", YAML: "kind: ConfigMap", Generated: true, Valid: true}, {ID: "Deployment/app", OriginalID: "app", CurrentID: deployID, Kind: "Deployment", YAML: "kind: Deployment", References: []string{configID}, Valid: true}}
	transforms := []receipt.TransformerFact{{Seq: 1, Name: "patch", Kind: "patch", Target: deployID, Before: "replicas=1", After: "replicas=2", Applied: true}, {Seq: 2, Name: "replacement", Kind: "replacement", Target: deployID, Before: "image=old", After: "image=new", Applied: true}}
	fileFacts := []receipt.FileFact{{Path: files[0], Digest: sum(files[0]), Order: 0, Valid: true}, {Path: files[1], Digest: sum(files[1]), Order: 1, Valid: true}}
	build := &receipt.BuildFact{Resources: []string{configID, deployID}, YAML: []byte("kind: ConfigMap\n---\nkind: Deployment\n"), Projection: "api", Complete: true}
	journal := receipt.NewBuildJournal()
	for _, tr := range transforms {
		entry := journal.Record(receipt.JournalEntry{Transformer: tr.Name, Target: tr.Target, Before: tr.Before, After: tr.After, Applied: true})
		if entry.Seq != tr.Seq {
			t.Fatal("journal order drift")
		}
	}
	got, err := receipt.Capture(plan, resources, transforms, fileFacts, build, journal)
	if err != nil {
		t.Fatal(err)
	}
	if got.Digest() == "" || got.Validate() != nil {
		t.Fatal("invalid build receipt")
	}
	build.YAML[0] = 'X'
	if got.Build.YAML[0] == 'X' {
		t.Fatal("capture retained YAML storage")
	}
	return got
}
func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	got := buildReceipt(t, root)
	switch family {
	case "M-RESOURCE-ACCUMULATION":
		bad := got
		bad.Files = append([]receipt.FileFact(nil), got.Files...)
		bad.Files[0].Order = 1
		if bad.Validate() == nil {
			t.Fatal("bad dependency order validated")
		}
	case "M-GENERATOR-CONTENT":
		bad := got
		bad.Resources = append([]receipt.ResourceFact(nil), got.Resources...)
		bad.Resources[0].ContentHash = ""
		if bad.Validate() == nil {
			t.Fatal("generator without content hash validated")
		}
	case "M-HASH-IDENTITY":
		bad := got
		bad.Resources = append([]receipt.ResourceFact(nil), got.Resources...)
		bad.Resources[0].CurrentID = "config-stale"
		bad.Build = &receipt.BuildFact{Resources: []string{"config-stale", got.Build.Resources[1]}, YAML: append([]byte(nil), got.Build.YAML...), Projection: got.Build.Projection, Complete: true}
		bad.Resources[1].References = []string{"config-stale"}
		if bad.Validate() == nil {
			t.Fatal("stale generated identity validated")
		}
	case "M-NAME-REFERENCE":
		bad := got
		bad.Resources = append([]receipt.ResourceFact(nil), got.Resources...)
		bad.Resources[1].References = []string{"missing-config"}
		if bad.Validate() == nil {
			t.Fatal("dangling name reference validated")
		}
	case "M-TRANSFORM-ORDER":
		bad := got
		bad.Transformers = append([]receipt.TransformerFact(nil), got.Transformers...)
		bad.Transformers[0].Seq = 2
		if bad.Validate() == nil {
			t.Fatal("transform order divergence validated")
		}
	case "M-PATCH-REPLACEMENT":
		bad := got
		bad.Transformers = append([]receipt.TransformerFact(nil), got.Transformers...)
		bad.Transformers[0].After = bad.Transformers[0].Before
		if bad.Validate() == nil {
			t.Fatal("unapplied patch validated")
		}
	case "M-YAML-ROUNDTRIP":
		other := got
		b := *got.Build
		other.Build = &b
		other.Build.YAML = []byte("kind:   ConfigMap\n\n---\n kind: Deployment\n")
		if !got.Equivalent(other) {
			t.Fatal("presentation-only YAML changed identity")
		}
	case "M-CLI-API-EQUIVALENCE":
		other := got
		b := *got.Build
		other.Build = &b
		other.Build.Projection = "cli"
		if !got.Equivalent(other) {
			t.Fatal("CLI and API builds diverged")
		}
	default:
		t.Fatalf("unknown family %q", family)
	}
}
func runNative(t *testing.T, root, _ string) {
	t.Helper()
	left := []string{"z=" + root, "a=base"}
	right := []string{"a=base", "z=" + root}
	a, err := hasher.SortArrayAndComputeHash(left)
	if err != nil || len(a) != 10 {
		t.Fatal("native hash drift")
	}
	b, err := hasher.SortArrayAndComputeHash(right)
	if err != nil || a != b {
		t.Fatal("native content hash order drift")
	}
}
