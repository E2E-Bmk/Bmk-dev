package koanf_oracle_test

import (
	"errors"
	"testing"

	jsonparser "github.com/knadh/koanf/parsers/json"
	"github.com/knadh/koanf/providers/confmap"
	"github.com/knadh/koanf/providers/rawbytes"
	koanf "github.com/knadh/koanf/v2"
)

// Verifies: KCFG-GEN-001.
func TestKoanfGenerationAdvancesOnSemanticLoad(t *testing.T) {
	k := koanf.New(".")
	equal(t, koanf.Generation(0), k.Generation())
	mustNoErr(t, k.Load(confmap.Provider(map[string]any{"service": "api"}, ""), nil))
	equal(t, koanf.Generation(1), k.Generation())
}

// Verifies: KCFG-GEN-001.
func TestKoanfGenerationAdvancesOnSemanticLoadBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	mustNoErr(t, k.Set("a", 2))
	equal(t, koanf.Generation(2), k.Generation())
}

// Verifies: KCFG-GEN-002.
func TestKoanfGenerationIgnoresNoopAndFailure(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	mustNoErr(t, k.Load(confmap.Provider(map[string]any{"a": 1}, ""), nil))
	equal(t, koanf.Generation(1), k.Generation())
}

// Verifies: KCFG-GEN-002.
func TestKoanfGenerationIgnoresNoopAndFailureBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	truth(t, k.Load(failingProvider{errors.New("offline acquisition")}, nil) != nil, "load must fail")
	equal(t, koanf.Generation(1), k.Generation())
	equal(t, 1, k.Int("a"))
}

// Verifies: KCFG-SNAP-001.
func TestKoanfSnapshotFreezesGeneration(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": "old"})
	s := k.Snapshot()
	mustNoErr(t, k.Set("version", "new"))
	equal(t, koanf.Generation(1), s.Generation())
	equal(t, "old", s.Get("version"))
}

// Verifies: KCFG-SNAP-001.
func TestKoanfSnapshotFreezesGenerationBoundary(t *testing.T) {
	k := koanf.New(".")
	s := k.Snapshot()
	truth(t, s.Published(), "live snapshot must be published")
	equal(t, koanf.Generation(0), s.Generation())
	equal(t, []string{}, s.Keys())
}

// Verifies: KCFG-SNAP-002.
func TestKoanfSnapshotDefensiveProjection(t *testing.T) {
	k := loaded(t, ".", map[string]any{"nested": map[string]any{"value": 1}})
	s := k.Snapshot()
	raw := s.Raw()
	asMap(t, raw["nested"])["value"] = 9
	equal(t, 1, s.Get("nested.value"))
}

// Verifies: KCFG-SNAP-002.
func TestKoanfSnapshotDefensiveProjectionBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"items": []any{map[string]any{"name": "first"}}})
	s := k.Snapshot()
	items := asSlice(t, s.Get("items"))
	asMap(t, items[0])["name"] = "changed"
	equal(t, "first", asMap(t, asSlice(t, s.Raw()["items"])[0])["name"])
}

// Verifies: KCFG-RECEIPT-001.
func TestKoanfLoadReceiptClassifiesChanges(t *testing.T) {
	k := loaded(t, ".", map[string]any{"old": 1, "same": true})
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"old": 2, "new": 3}, ""), nil)
	mustNoErr(t, err)
	equal(t, []string{"added:new", "updated:old"}, changePaths(r))
	truth(t, r.Published, "semantic changes must publish")
}

// Verifies: KCFG-RECEIPT-001.
func TestKoanfLoadReceiptClassifiesChangesBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"node": "scalar"})
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"node": map[string]any{"leaf": "value"}}, ""), nil)
	mustNoErr(t, err)
	equal(t, []string{"removed:node", "added:node.leaf"}, changePaths(r))
}

// Verifies: KCFG-RECEIPT-002.
func TestKoanfLoadReceiptNoopAndFailure(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	equal(t, koanf.Generation(1), k.Generation())
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"a": 1}, ""), nil)
	mustNoErr(t, err)
	truth(t, !r.Published && len(r.Changes) == 0, "no-op receipt must be unpublished and empty")
	equal(t, r.Before, r.After)
}

// Verifies: KCFG-RECEIPT-002.
func TestKoanfLoadReceiptNoopAndFailureBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	r, err := k.LoadWithReceipt(failingProvider{errors.New("read failed")}, nil)
	truth(t, err != nil, "load must fail")
	truth(t, !r.Published && len(r.Changes) == 0, "failed receipt must retain state")
	equal(t, k.Snapshot().Digest(), r.Digest)
}

// Verifies: KCFG-TXN-001.
func TestKoanfReloadTransactionStagingInvisible(t *testing.T) {
	k := loaded(t, ".", map[string]any{"version": "live"})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("version", "staged"))
	equal(t, "live", k.String("version"))
	s, err := tx.Preview()
	mustNoErr(t, err)
	equal(t, "staged", s.Get("version"))
}

// Verifies: KCFG-TXN-001.
func TestKoanfReloadTransactionStagingInvisibleBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"keep": true})
	tx := k.BeginReload()
	mustNoErr(t, tx.Delete("keep"))
	truth(t, k.Exists("keep"), "staged delete must not affect live state")
}

// Verifies: KCFG-TXN-002.
func TestKoanfReloadPreviewComposesChanges(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("a", 2))
	mustNoErr(t, tx.Set("b", 3))
	s, err := tx.Preview()
	mustNoErr(t, err)
	equal(t, 2, s.Get("a"))
	equal(t, 3, s.Get("b"))
	truth(t, !s.Published(), "preview must be unpublished")
}

// Verifies: KCFG-TXN-002.
func TestKoanfReloadPreviewComposesChangesBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"base": 1})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("next", nil))
	s, err := tx.Preview()
	mustNoErr(t, err)
	truth(t, s.Exists("next"), "preview must distinguish a present nil fact")
	equal(t, k.Generation(), s.Generation())
}

// Verifies: KCFG-STALE-001.
func TestKoanfReloadCommitRejectsStale(t *testing.T) {
	k := loaded(t, ".", map[string]any{"owner": "base"})
	tx := k.BeginReload()
	mustNoErr(t, tx.Set("owner", "staged"))
	mustNoErr(t, k.Set("owner", "newer"))
	_, err := tx.Commit()
	mustErrIs(t, err, koanf.ErrStaleGeneration)
	equal(t, "newer", k.String("owner"))
}

// Verifies: KCFG-STALE-001.
func TestKoanfReloadCommitRejectsStaleBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	tx := k.BeginReload()
	mustNoErr(t, k.Set("b", 2))
	_, err := tx.Commit()
	mustErrIs(t, err, koanf.ErrStaleGeneration)
	_, err = tx.Preview()
	mustErrIs(t, err, koanf.ErrClosedReload)
}

// Verifies: KCFG-RECOVERY-001.
func TestKoanfReloadTransactionTerminalState(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	tx := k.BeginReload()
	_, err := tx.Commit()
	mustNoErr(t, err)
	mustErrIs(t, tx.Set("a", 2), koanf.ErrClosedReload)
}

// Verifies: KCFG-RECOVERY-001.
func TestKoanfReloadTransactionTerminalStateBoundary(t *testing.T) {
	k := koanf.New(".")
	tx := k.BeginReload()
	mustNoErr(t, tx.Abort())
	mustErrIs(t, tx.Abort(), koanf.ErrClosedReload)
	mustErrIs(t, tx.Delete("missing"), koanf.ErrClosedReload)
}

// Verifies: KCFG-DIGEST-001.
func TestKoanfProjectionDigestSemanticEquivalence(t *testing.T) {
	a := loaded(t, ".", map[string]any{"n": int64(3), "nested": map[string]any{"x": true}})
	b := loaded(t, "/", map[string]any{"nested": map[string]any{"x": true}, "n": float64(3)})
	requireDigest(t, a.Snapshot().Digest())
	requireDigest(t, b.Snapshot().Digest())
	equal(t, a.Snapshot().Digest(), b.Snapshot().Digest())
}

// Verifies: KCFG-DIGEST-001.
func TestKoanfProjectionDigestSemanticEquivalenceBoundary(t *testing.T) {
	a := loaded(t, ".", map[string]any{"items": []any{1, 2}})
	b := loaded(t, ".", map[string]any{"items": []any{2, 1}})
	truth(t, a.Snapshot().Digest() != b.Snapshot().Digest(), "slice order must affect digest")
	requireDigest(t, a.Snapshot().Digest())
}

// Verifies: KCFG-DIGEST-002.
func TestKoanfReceiptSnapshotDigestAgreement(t *testing.T) {
	k := koanf.New(".")
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"a": 1}, ""), nil)
	mustNoErr(t, err)
	requireDigest(t, r.Digest)
	equal(t, k.Snapshot().Digest(), r.Digest)
	equal(t, k.Generation(), r.After)
}

// Verifies: KCFG-DIGEST-002.
func TestKoanfReceiptSnapshotDigestAgreementBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	r, err := k.LoadWithReceipt(confmap.Provider(map[string]any{"a": 1}, ""), nil)
	mustNoErr(t, err)
	equal(t, k.Snapshot().Digest(), r.Digest)
	requireDigest(t, r.Digest)
}

// Verifies: KCFG-NATIVE-001.
func TestKoanfNativeJSONSemanticRoundTrip(t *testing.T) {
	k := loadedJSON(t, `{"service":{"name":"api","port":8080}}`)
	equal(t, "api", k.String("service.name"))
	equal(t, 8080, k.Int("service.port"))
	b, err := k.Marshal(jsonparser.Parser())
	mustNoErr(t, err)
	fresh := koanf.New(".")
	mustNoErr(t, fresh.Load(rawbytes.Provider(b), jsonparser.Parser()))
	equal(t, k.Raw(), fresh.Raw())
}

// Verifies: KCFG-NATIVE-001.
func TestKoanfNativeJSONSemanticRoundTripBoundary(t *testing.T) {
	k := loadedJSON(t, `{"nil":null,"items":[]}`)
	truth(t, k.Exists("nil") && k.Get("nil") == nil, "present nil must survive JSON parsing")
	equal(t, []any{}, k.Get("items"))
}

// Verifies: KCFG-NATIVE-002.
func TestKoanfNativeDefaultMerge(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"host": "local", "port": 80}})
	mustNoErr(t, k.Load(confmap.Provider(map[string]any{"service": map[string]any{"port": 8080}}, ""), nil))
	equal(t, "local", k.String("service.host"))
	equal(t, 8080, k.Int("service.port"))
}

// Verifies: KCFG-NATIVE-002.
func TestKoanfNativeDefaultMergeBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"node": "scalar"})
	mustNoErr(t, k.Load(confmap.Provider(map[string]any{"node": map[string]any{"leaf": 1}}, ""), nil))
	equal(t, 1, k.Int("node.leaf"))
}

// Verifies: KCFG-NATIVE-003.
func TestKoanfNativeTypedDecode(t *testing.T) {
	k := loaded(t, ".", map[string]any{"service": map[string]any{"name": "api", "port": 8080}})
	var out struct {
		Name string `koanf:"name"`
		Port int    `koanf:"port"`
	}
	mustNoErr(t, k.Unmarshal("service", &out))
	equal(t, "api", out.Name)
	equal(t, 8080, out.Port)
}

// Verifies: KCFG-NATIVE-003.
func TestKoanfNativeTypedDecodeBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"enabled": "true"})
	var out struct {
		Enabled bool `koanf:"enabled"`
	}
	mustNoErr(t, k.Unmarshal("", &out))
	truth(t, out.Enabled, "weak typed decode must convert true")
}

// Verifies: KCFG-NATIVE-004.
func TestKoanfNativeDeleteProjection(t *testing.T) {
	k := loaded(t, ".", map[string]any{"drop": map[string]any{"a": 1}, "keep": 2})
	k.Delete("drop")
	truth(t, !k.Exists("drop") && !k.Exists("drop.a"), "deleted subtree must leave every projection")
	equal(t, []string{"keep"}, k.Keys())
}

// Verifies: KCFG-NATIVE-004.
func TestKoanfNativeDeleteProjectionBoundary(t *testing.T) {
	k := loaded(t, ".", map[string]any{"a": 1})
	truth(t, k.Exists("a"), "loaded fact must exist before whole-graph deletion")
	k.Delete("")
	equal(t, []string{}, k.Keys())
	equal(t, map[string]any{}, k.Raw())
}
