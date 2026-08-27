package koanf_oracle_test

import (
	"os"
	"sort"
	"testing"

	jsonparser "github.com/knadh/koanf/parsers/json"
	yamlparser "github.com/knadh/koanf/parsers/yaml"
	"github.com/knadh/koanf/providers/confmap"
	"github.com/knadh/koanf/providers/file"
	"github.com/knadh/koanf/providers/rawbytes"
	koanf "github.com/knadh/koanf/v2"
)

// Verifies: KCFG-SEAM-001.
func TestKoanfGenerationAcrossOrderedProviders(t *testing.T) {
	k := koanf.New(".")
	for _, facts := range []map[string]any{{"owner": "base"}, {"port": 80}, {"owner": "overlay"}} {
		mustNoErr(t, k.Load(confmap.Provider(facts, ""), nil))
	}
	equal(t, koanf.Generation(3), k.Generation())
	equal(t, "overlay", k.String("owner"))
}

// Verifies: KCFG-SEAM-002.
func TestKoanfSnapshotSurvivesLiveDelete(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api", "port": 80}})
	s := k.Snapshot()
	k.Delete("service.name")
	equal(t, "api", s.Get("service.name"))
	truth(t, !k.Exists("service.name"), "live delete must publish")
	equal(t, koanf.Generation(1), s.Generation())
}

// Verifies: KCFG-SEAM-003.
func TestKoanfReceiptChangeSetAcrossNestedCollision(t *testing.T) {
	k := loaded(t, ".", map[string]any{"node": map[string]any{"a": 1, "b": 2}})
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"node": "scalar"}, ""), nil)
	mustNoErr(t, err)
	equal(t, []string{"added:node", "removed:node.a", "removed:node.b"}, changePaths(r))
}

// Verifies: KCFG-SEAM-004.
func TestKoanfTransactionLoadsFileAndOverlay(t *testing.T) {
	path := tempFile(t, "base.json", `{"service":{"host":"file","port":80}}`)
	k := koanf.New(".")
	tx := k.BeginReload()
	mustNoErr(t, tx.Load(file.Provider(path), jsonparser.Parser()))
	mustNoErr(t, tx.Load(confmap.Provider(map[string]any{"service": map[string]any{"host": "overlay"}}, ""), nil))
	s, err := tx.Preview()
	mustNoErr(t, err)
	equal(t, "overlay", s.Get("service.host"))
	equal(t, float64(80), s.Get("service.port"))
	equal(t, []string{}, k.Keys())
}

// Verifies: KCFG-SEAM-005.
func TestKoanfConcurrentReloadDetectsStaleBase(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": 1})
	first, second := k.BeginReload(), k.BeginReload()
	mustNoErr(t, first.Set("version", 2))
	mustNoErr(t, second.Set("version", 3))
	_, err := first.Commit()
	mustNoErr(t, err)
	_, err = second.Commit()
	mustErrIs(t, err, koanf.ErrStaleGeneration)
	equal(t, 2, k.Int("version"))
}

// Verifies: KCFG-SEAM-006.
func TestKoanfDigestAcrossMarshalReload(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api", "port": 8080}})
	requireDigest(t, k.Snapshot().Digest())
	equal(t, "api", k.String("service.name"))
	b, err := k.Snapshot().Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	equal(t, k.Snapshot().Digest(), fresh.Snapshot().Digest())
}

// Verifies: KCFG-SEAM-007.
func TestKoanfFailedStagedParseRetainsPreview(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": "live"})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("version", "last-good"))
	before, err := tx.Preview()
	mustNoErr(t, err)
	err = tx.Load(rawbytes.Provider([]byte(`{"broken":`)), jsonparser.Parser())
	truth(t, err != nil, "parse must fail")
	after, err := tx.Preview()
	mustNoErr(t, err)
	equal(t, before.Digest(), after.Digest())
	equal(t, "last-good", after.Get("version"))
	equal(t, "live", k.String("version"))
}

// Verifies: KCFG-SEAM-008.
func TestKoanfGenerationSharedBySetMergeDelete(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	mustNoErr(t, k.Set("b", 2))
	other := loaded(t, ".", map[string]any{"c": 3})
	mustNoErr(t, k.Merge(other))
	k.Delete("a")
	equal(t, koanf.Generation(4), k.Generation())
	equal(t, []string{"b", "c"}, k.Keys())
}

// Verifies: KCFG-SEAM-009.
func TestKoanfSnapshotTypedAndRawAgreement(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api", "port": 8080}})
	s := k.Snapshot()
	var out struct {
		Name string `koanf:"name"`
		Port int    `koanf:"port"`
	}
	mustNoErr(t, s.Unmarshal("service", &out))
	equal(t, s.Get("service.name"), out.Name)
	equal(t, 8080, out.Port)
	equal(t, "api", asMap(t, s.Raw()["service"])["name"])
}

// Verifies: KCFG-SEAM-010.
func TestKoanfReceiptSortedAcrossMultiSourceMerge(t *testing.T) {
	k := loaded(t, ".", map[string]any{"z": 0})
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"z": 1, "a": 2, "m": 3}, ""), nil)
	mustNoErr(t, err)
	equal(t, []string{"added:a", "added:m", "updated:z"}, changePaths(r))
	paths := changePaths(r)
	truth(t, sort.StringsAreSorted(paths), "receipt changes must be sorted")
}

// Verifies: KCFG-SEAM-011.
func TestKoanfTransactionPreviewThenCommit(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": "old"})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("version", "new"))
	preview, err := tx.Preview()
	mustNoErr(t, err)
	receipt, err := tx.Commit()
	mustNoErr(t, err)
	truth(t, receipt.Published, "changed transaction must publish")
	equal(t, preview.Digest(), receipt.Digest)
	equal(t, receipt.After, k.Generation())
	equal(t, "new", k.String("version"))
}

// Verifies: KCFG-SEAM-012.
func TestKoanfStaleCommitLeavesLiveReceipt(t *testing.T) {
	k := loaded(t, ".", map[string]any{"owner": "base"})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("owner", "staged"))
	liveReceipt, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"owner": "newer"}, ""), nil)
	mustNoErr(t, err)
	staleReceipt, err := tx.Commit()
	mustErrIs(t, err, koanf.ErrStaleGeneration)
	equal(t, liveReceipt.Digest, staleReceipt.Digest)
	equal(t, liveReceipt.After, staleReceipt.After)
	equal(t, "newer", k.String("owner"))
}

// Verifies: KCFG-SEAM-013.
func TestKoanfDigestDelimiterNormalization(t *testing.T) {
	a := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api"}})
	b := loaded(t, "/", map[string]any{"service": map[string]any{"name": "api"}})
	equal(t, []string{"service.name"}, a.Keys())
	equal(t, []string{"service/name"}, b.Keys())
	equal(t, a.Snapshot().Digest(), b.Snapshot().Digest())
}

// Verifies: KCFG-SEAM-014.
func TestKoanfAbortClosesWithoutPublication(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": "live"})
	before := k.Snapshot()
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("version", "staged"))
	mustNoErr(t, tx.Abort())
	equal(t, before.Digest(), k.Snapshot().Digest())
	equal(t, before.Generation(), k.Generation())
	_, err := tx.Commit()
	mustErrIs(t, err, koanf.ErrClosedReload)
}

// Verifies: KCFG-SEAM-015.
func TestKoanfWatchReloadPublishesSingleGeneration(t *testing.T) {
	path := tempFile(t, "watched.json", `{"version":"one"}`)
	provider := file.Provider(path)
	k := koanf.New(".")
	mustNoErr(t, k.Load(provider, jsonparser.Parser()))
	mustNoErr(t, os.WriteFile(path, []byte(`{"version":"two"}`), 0o600))
	mustNoErr(t, k.Load(provider, jsonparser.Parser()))
	equal(t, koanf.Generation(2), k.Generation())
	equal(t, "two", k.String("version"))
}

// Verifies: KCFG-SEAM-016.
func TestKoanfSnapshotCutAndMarshalAgreement(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api"}, "other": true})
	s := k.Snapshot()
	b, err := s.Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	equal(t, s.Digest(), fresh.Snapshot().Digest())
	equal(t, s.Get("service.name"), fresh.String("service.name"))
}

// Verifies: KCFG-SEAM-017.
func TestKoanfReceiptNoopAfterEquivalentReload(t *testing.T) {
	k := loaded(t, ".", map[string]any{"count": int64(3)})
	equal(t, 3, k.Int("count"))
	before := k.Generation()
	r, err := k.LoadWithReceipt(rawbytes.Provider([]byte(`{"count":3}`)), jsonparser.Parser())
	mustNoErr(t, err)
	truth(t, !r.Published && len(r.Changes) == 0, "losslessly equal numeric reload must be a no-op")
	equal(t, before, k.Generation())
}

// Verifies: KCFG-SEAM-018.
func TestKoanfNativeInvalidJSONIsAtomic(t *testing.T) {
	k := loaded(t, ".", map[string]any{"stable": true})
	before := k.Raw()
	err := k.Load(rawbytes.Provider([]byte(`{"broken":`)), jsonparser.Parser())
	truth(t, err != nil, "invalid JSON must fail")
	equal(t, before, k.Raw())
	equal(t, koanf.Generation(1), k.Generation())
}

// Verifies: KCFG-SEAM-019.
func TestKoanfNativeEmptyProviderNoop(t *testing.T) {
	k := loaded(t, ".", map[string]any{"stable": true})
	before := k.Generation()
	mustNoErr(t, k.Load(mapProvider{map[string]any{}}, nil))
	equal(t, before, k.Generation())
	truth(t, k.Bool("stable"), "empty provider must retain facts")
}

// Verifies: KCFG-SEAM-020.
func TestKoanfNativeIndependentInstances(t *testing.T) {
	facts := map[string]any{"nested": map[string]any{"value": 1}}
	provider := mapProvider{facts}
	left, right := koanf.New("."), koanf.New(".")
	mustNoErr(t, left.Load(provider, nil))
	mustNoErr(t, right.Load(provider, nil))
	facts["nested"].(map[string]any)["value"] = 9
	mustNoErr(t, left.Set("nested.value", 2))
	equal(t, 1, right.Int("nested.value"))
	equal(t, 2, left.Int("nested.value"))
}

// Verifies: KCFG-SEAM-021.
func TestKoanfNativeDeterministicKeys(t *testing.T) {
	k := loaded(t, ".", map[string]any{"z": 1, "a": map[string]any{"z": 2, "a": 3}, "m": 4})
	want := []string{"a.a", "a.z", "m", "z"}
	for i := 0; i < 4; i++ {
		equal(t, want, k.Keys())
	}
}

// Verifies: KCFG-SEAM-022.
func TestKoanfNativeMarshalReloadEquivalence(t *testing.T) {
	k := loaded(t, ".", map[string]any{"nested": map[string]any{"a": "x", "b": 2}, "flag": true})
	b, err := k.Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	equal(t, k.Keys(), fresh.Keys())
	equal(t, "x", fresh.String("nested.a"))
	truth(t, fresh.Bool("flag"), "flag must survive")
}

// Verifies: KCFG-SEAM-023.
func TestKoanfNativeCustomProviderParser(t *testing.T) {
	k := koanf.New(".")
	mustNoErr(t, k.Load(rawbytes.Provider([]byte("name=api\nport=8080")), lineParser{}))
	equal(t, "api", k.String("name"))
	equal(t, "8080", k.String("port"))
	b, err := k.Marshal(lineParser{})
	mustNoErr(t, err)
	truth(t, len(b) > 0, "custom parser must marshal")
}

// Verifies: KCFG-SEAM-024.
func TestKoanfNativeDeleteMarshalAgreement(t *testing.T) {
	k := loaded(t, ".", map[string]any{"keep": 1, "drop": map[string]any{"a": 2}})
	k.Delete("drop")
	b, err := k.Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	truth(t, !fresh.Exists("drop") && fresh.Int("keep") == 1, "serialized projection must exclude deleted subtree")
}

// Verifies: KCFG-SYSTEM-001.
func TestKoanfTransactionalLocalReloadReceipt(t *testing.T) {
	path := tempFile(t, "system.json", `{"service":{"host":"file","port":80}}`)
	k := koanf.New(".")
	tx := k.BeginReload()
	mustNoErr(t, tx.Load(file.Provider(path), jsonparser.Parser()))
	mustNoErr(t, tx.Load(confmap.Provider(map[string]any{"service": map[string]any{"host": "overlay"}}, ""), nil))
	preview, err := tx.Preview()
	mustNoErr(t, err)
	receipt, err := tx.Commit()
	mustNoErr(t, err)
	fresh := k.Snapshot()
	equal(t, preview.Digest(), receipt.Digest)
	equal(t, receipt.Digest, fresh.Digest())
	equal(t, "overlay", fresh.Get("service.host"))
	equal(t, float64(80), fresh.Get("service.port"))
}

// Verifies: KCFG-SYSTEM-002.
func TestKoanfConcurrentReloadStaleClosure(t *testing.T) {
	k := loaded(t, ".", map[string]any{"owner": "base"})
	stale, winner := k.BeginReload(), k.BeginReload()
	mustNoErr(t, stale.Set("owner", "stale"))
	mustNoErr(t, winner.Set("owner", "winner"))
	won, err := winner.Commit()
	mustNoErr(t, err)
	_, err = stale.Commit()
	mustErrIs(t, err, koanf.ErrStaleGeneration)
	mustErrIs(t, stale.Abort(), koanf.ErrClosedReload)
	equal(t, won.Digest, k.Snapshot().Digest())
	equal(t, "winner", k.String("owner"))
}

// Verifies: KCFG-SYSTEM-003.
func TestKoanfSnapshotDigestSourceConvergence(t *testing.T) {
	fromMap := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api", "port": int64(8080)}})
	fromJSON := loadedJSON(t, `{"service":{"port":8080,"name":"api"}}`)
	equal(t, "api", fromMap.String("service.name"))
	equal(t, "api", fromJSON.String("service.name"))
	requireDigest(t, fromMap.Snapshot().Digest())
	equal(t, fromMap.Snapshot().Digest(), fromJSON.Snapshot().Digest())
	equal(t, fromMap.Keys(), fromJSON.Keys())
	b, err := fromMap.Snapshot().Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	equal(t, fromMap.Snapshot().Digest(), fresh.Snapshot().Digest())
}

// Verifies: KCFG-SYSTEM-004.
func TestKoanfFailedReloadRecoveryReceipt(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": "live"})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("version", "last-good"))
	err := tx.Load(rawbytes.Provider([]byte(`{"bad":`)), jsonparser.Parser())
	truth(t, err != nil, "failed parse must be recoverable")
	preview, err := tx.Preview()
	mustNoErr(t, err)
	mustNoErr(t, tx.Set("recovered", true))
	receipt, err := tx.Commit()
	mustNoErr(t, err)
	truth(t, receipt.Published && k.Bool("recovered"), "recovered transaction must publish")
	equal(t, "last-good", k.String("version"))
	truth(t, preview.Digest() != receipt.Digest, "later recovery edit must change preview")
}

// Verifies: KCFG-SYSTEM-005.
func TestKoanfAbortCustomMergeLeavesLiveGeneration(t *testing.T) {
	k := loaded(t, ".", map[string]any{"owner": "live", "stable": true})
	before := k.Snapshot()
	tx := k.BeginReload()
	mustNoErr(t, tx.Load(confmap.Provider(map[string]any{"owner": "custom"}, ""), nil, koanf.WithMergeFunc(func(src, dest map[string]any) error { dest["owner"] = src["owner"]; dest["extra"] = 1; return nil })))
	preview, err := tx.Preview()
	mustNoErr(t, err)
	equal(t, "custom", preview.Get("owner"))
	mustNoErr(t, tx.Abort())
	equal(t, before.Generation(), k.Generation())
	equal(t, before.Digest(), k.Snapshot().Digest())
	equal(t, "live", k.String("owner"))
}

// Verifies: KCFG-SYSTEM-006.
func TestKoanfNativeFileYAMLTypedWorkflow(t *testing.T) {
	path := tempFile(t, "config.yaml", "service:\n  name: api\n  port: 8080\nenabled: true\n")
	k := koanf.New(".")
	mustNoErr(t, k.Load(file.Provider(path), yamlparser.Parser()))
	var out struct {
		Service struct {
			Name string `koanf:"name"`
			Port int    `koanf:"port"`
		} `koanf:"service"`
		Enabled bool `koanf:"enabled"`
	}
	mustNoErr(t, k.Unmarshal("", &out))
	equal(t, "api", out.Service.Name)
	equal(t, 8080, out.Service.Port)
	truth(t, out.Enabled, "enabled must decode")
	b, err := k.Marshal(yamlparser.Parser())
	mustNoErr(t, err)
	truth(t, len(b) > 0, "YAML marshal must produce bytes")
}

// Verifies: KCFG-SYSTEM-007.
func TestKoanfNativeDeleteRestoreWorkflow(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api", "port": 80}, "stable": true})
	k.Delete("service.name")
	truth(t, !k.Exists("service.name"), "name must be deleted")
	mustNoErr(t, k.Load(confmap.Provider(map[string]any{"service": map[string]any{"name": "restored"}}, ""), nil))
	b, err := k.Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	equal(t, "restored", fresh.String("service.name"))
	equal(t, 80, fresh.Int("service.port"))
	truth(t, fresh.Bool("stable"), "stable fact must remain")
}

// Verifies: KCFG-SYSTEM-008.
func TestKoanfNativeOrderedSourcesWorkflow(t *testing.T) {
	path := tempFile(t, "ordered.json", `{"service":{"host":"file","port":80},"source":"file"}`)
	k := koanf.New(".")
	mustNoErr(t, k.Load(file.Provider(path), jsonparser.Parser()))
	receipt, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"service": map[string]any{"host": "overlay"}, "source": "overlay"}, ""), nil)
	mustNoErr(t, err)
	equal(t, []string{"updated:service.host", "updated:source"}, changePaths(receipt))
	equal(t, "overlay", k.String("service.host"))
	equal(t, 80, k.Int("service.port"))
	fresh := k.Snapshot()
	equal(t, receipt.Digest, fresh.Digest())
	equal(t, receipt.After, fresh.Generation())
}
