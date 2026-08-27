package containerregistrygate_test

import (
	"crypto/sha256"
	"encoding/hex"
	"io"
	"strings"
	"testing"

	"github.com/google/go-containerregistry/pkg/name"
	v1 "github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/empty"
	"github.com/google/go-containerregistry/pkg/v1/mutate"
	"github.com/google/go-containerregistry/pkg/v1/receipt"
	"github.com/google/go-containerregistry/pkg/v1/static"
	"github.com/google/go-containerregistry/pkg/v1/types"
)

func descriptor(raw []byte, mediaType string) receipt.DescriptorFact {
	sum := sha256.Sum256(raw)
	return receipt.DescriptorFact{Digest: "sha256:" + hex.EncodeToString(sum[:]), Size: int64(len(raw)), MediaType: mediaType}
}

func syntheticReceipt(t *testing.T, root string) receipt.GraphReceipt {
	t.Helper()
	plan := receipt.NewGraphPlan()
	if _, err := plan.SelectImage("", empty.Image); err == nil {
		t.Fatal("empty image name accepted")
	}
	var err error
	plan, err = plan.SelectImage("image-"+root, empty.Image)
	if err != nil {
		t.Fatal(err)
	}
	plan, err = plan.SelectIndex("index-"+root, empty.Index)
	if err != nil {
		t.Fatal(err)
	}
	plan = plan.IncludeLayers().IncludeRawJSON().IncludeTransfers()
	manifest := []byte(`{"schemaVersion":2,"kind":"image"}`)
	compressed := []byte("compressed-layer-" + root)
	uncompressed := []byte("uncompressed-layer-" + root)
	imageDescriptor := descriptor(manifest, "application/vnd.oci.image.manifest.v1+json")
	image := receipt.ImageFact{
		Name: "image-" + root, Projection: "api", Descriptor: imageDescriptor,
		ConfigDigest: descriptor([]byte("config-"+root), "config").Digest,
		RawManifest:  manifest, Valid: true,
		Layers: []receipt.LayerFact{{
			Descriptor: descriptor(compressed, "application/vnd.oci.image.layer.v1.tar"),
			DiffID:     descriptor(uncompressed, "layer").Digest, Order: 0,
			Compressed: compressed, Uncompressed: uncompressed,
		}},
	}
	indexRaw := []byte(`{"schemaVersion":2,"kind":"index"}`)
	index := receipt.IndexFact{
		Name: "index-" + root, Projection: "api",
		Descriptor: descriptor(indexRaw, "application/vnd.oci.image.index.v1+json"),
		Children:   []receipt.DescriptorFact{imageDescriptor}, Platforms: []string{"linux/amd64"},
		RawManifest: indexRaw, Valid: true,
	}
	journal := receipt.NewTransferJournal()
	fact := journal.Record(receipt.TransferFact{Reference: "registry.example/demo:latest", Direction: "push", Descriptor: imageDescriptor.Digest, Complete: true, Location: "memory://one"})
	if fact.Seq != 1 || len(journal.Entries()) != 1 {
		t.Fatal("transfer journal lost ordering")
	}
	got, err := receipt.Capture(plan, []receipt.ImageFact{image}, []receipt.IndexFact{index}, journal)
	if err != nil {
		t.Fatal(err)
	}
	if got.Digest() == "" || got.Validate() != nil {
		t.Fatal("invalid graph receipt")
	}
	manifest[0] = 'X'
	if got.Images[0].RawManifest[0] == 'X' {
		t.Fatal("capture retained manifest storage")
	}
	return got
}

func runSynthetic(t *testing.T, root, family string) {
	t.Helper()
	got := syntheticReceipt(t, root)
	switch family {
	case "M-REFERENCE-NORMALIZATION":
		bad := got
		bad.Transfers = append([]receipt.TransferFact(nil), got.Transfers...)
		bad.Transfers[0].Reference = "Registry.Example/Demo:Latest"
		if bad.Validate() == nil {
			t.Fatal("noncanonical reference validated")
		}
	case "M-DESCRIPTOR-INTEGRITY":
		bad := got
		bad.Images = append([]receipt.ImageFact(nil), got.Images...)
		bad.Images[0].Descriptor.Size++
		if bad.Validate() == nil {
			t.Fatal("bad descriptor size validated")
		}
	case "M-LAYER-LIFECYCLE":
		bad := got
		bad.Images = append([]receipt.ImageFact(nil), got.Images...)
		bad.Images[0].Layers = append([]receipt.LayerFact(nil), got.Images[0].Layers...)
		bad.Images[0].Layers[0].DiffID = "sha256:bad"
		if bad.Validate() == nil {
			t.Fatal("bad layer diff identity validated")
		}
	case "M-MANIFEST-INDEX":
		bad := got
		bad.Indexes = append([]receipt.IndexFact(nil), got.Indexes...)
		bad.Indexes[0].Children = append([]receipt.DescriptorFact(nil), got.Indexes[0].Children...)
		bad.Indexes[0].Children[0].Digest = "sha256:missing"
		if bad.Validate() == nil {
			t.Fatal("missing index child validated")
		}
	case "M-MUTATE-GRAPH":
		changed := got
		changed.Images = append([]receipt.ImageFact(nil), got.Images...)
		changed.Images[0].RawManifest = []byte(`{"schemaVersion":2,"changed":true}`)
		changed.Images[0].Descriptor = descriptor(changed.Images[0].RawManifest, got.Images[0].Descriptor.MediaType)
		if len(receipt.Diff(got, changed).Changes) != 1 {
			t.Fatal("graph mutation was hidden")
		}
	case "M-LAYOUT-TARBALL":
		other := got
		other.Transfers = append([]receipt.TransferFact(nil), got.Transfers...)
		other.Transfers[0].Location = "file:///tmp/layout-two"
		if !got.Equivalent(other) {
			t.Fatal("temporary persistence location changed identity")
		}
	case "M-REGISTRY-TRANSPORT":
		bad := got
		bad.Transfers = append([]receipt.TransferFact(nil), got.Transfers...)
		bad.Transfers[0].Error = "registry denied upload"
		if bad.Validate() == nil {
			t.Fatal("failed transfer claimed completion")
		}
	case "M-CLI-API-EQUIVALENCE":
		other := got
		other.Images = append([]receipt.ImageFact(nil), got.Images...)
		other.Indexes = append([]receipt.IndexFact(nil), got.Indexes...)
		other.Images[0].Projection = "crane"
		other.Indexes[0].Projection = "crane"
		if !got.Equivalent(other) {
			t.Fatal("CLI and API projections diverged")
		}
	default:
		t.Fatalf("unknown family %q", family)
	}
}

func runNative(t *testing.T, root, _ string) {
	t.Helper()
	lowerRoot := strings.ToLower(root)
	ref, err := name.ParseReference("registry.example/native/"+lowerRoot+":latest", name.StrictValidation)
	if err != nil || ref.Context().Name() != "registry.example/native/"+lowerRoot {
		t.Fatal("native reference drift")
	}
	layer := static.NewLayer([]byte("native-layer-"+root), types.OCILayer)
	digest, err := layer.Digest()
	if err != nil || digest.String() == "" {
		t.Fatal("native layer digest drift")
	}
	size, err := layer.Size()
	if err != nil || size != int64(len("native-layer-"+root)) {
		t.Fatal("native layer size drift")
	}
	reader, err := layer.Compressed()
	if err != nil {
		t.Fatal(err)
	}
	content, err := io.ReadAll(reader)
	reader.Close()
	if err != nil || string(content) != "native-layer-"+root {
		t.Fatal("native layer read drift")
	}
	image, err := mutate.AppendLayers(empty.Image, layer)
	if err != nil {
		t.Fatal(err)
	}
	layers, err := image.Layers()
	if err != nil || len(layers) != 1 {
		t.Fatal("native image mutation drift")
	}
	if _, err := image.Digest(); err != nil {
		t.Fatal(err)
	}
	if _, err := v1.NewHash(digest.String()); err != nil {
		t.Fatal("native hash round trip drift")
	}
}
