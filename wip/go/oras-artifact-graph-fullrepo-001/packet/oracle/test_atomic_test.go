package orasgate_test

import (
	"bytes"
	"context"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
	"oras.land/oras-go/v2/content"
	"oras.land/oras-go/v2/content/memory"
	"oras.land/oras-go/v2/content/oci"
	"oras.land/oras-go/v2/errdef"
	"oras.land/oras-go/v2/flow"
	"oras.land/oras-go/v2/registry"
)

func TestAtomicDescriptorDigestIdentity(t *testing.T) {
	desc := content.NewDescriptorFromBytes("application/x-a", []byte("alpha"))
	if desc.Digest.String() != descriptor("alpha").Digest.String() {
		t.Fatal("equal bytes did not produce equal digest")
	}
	if desc.Digest == descriptor("beta").Digest {
		t.Fatal("different bytes produced equal digest")
	}
}

func TestAtomicDescriptorSizeAndMediaType(t *testing.T) {
	desc := content.NewDescriptorFromBytes("application/x-custom", []byte("abc"))
	if desc.Size != 3 || desc.MediaType != "application/x-custom" {
		t.Fatalf("descriptor = %+v", desc)
	}
}

func TestAtomicMemoryStorePushFetch(t *testing.T) {
	store := memory.New()
	desc := descriptor("memory-value")
	push(t, store, desc, "memory-value")
	if got := fetch(t, store, desc); got != "memory-value" {
		t.Fatalf("fetched %q", got)
	}
}

func TestAtomicMemoryStoreDuplicatePush(t *testing.T) {
	store := memory.New()
	desc := descriptor("stable")
	push(t, store, desc, "stable")
	err := store.Push(context.Background(), desc, bytes.NewBufferString("stable"))
	assertErrorIs(t, err, errdef.ErrAlreadyExists)
	if fetch(t, store, desc) != "stable" {
		t.Fatal("duplicate push changed stored bytes")
	}
}

func TestAtomicReferenceParseAbsolute(t *testing.T) {
	ref, err := registry.ParseReference("registry.example:5000/team/tool:v1")
	if err != nil {
		t.Fatal(err)
	}
	if ref.Registry != "registry.example:5000" || ref.Repository != "team/tool" || ref.Reference != "v1" {
		t.Fatalf("reference = %+v", ref)
	}
}

func TestAtomicReferenceRejectMalformed(t *testing.T) {
	for _, value := range []string{"missing-registry", "host/", "/repo"} {
		if _, err := registry.ParseReference(value); err == nil {
			t.Fatalf("ParseReference(%q) succeeded", value)
		}
	}
}

func TestAtomicTagResolveAndReplace(t *testing.T) {
	store := memory.New()
	first, second := descriptor("first"), descriptor("second")
	push(t, store, first, "first")
	push(t, store, second, "second")
	if err := store.Tag(context.Background(), first, "stable"); err != nil {
		t.Fatal(err)
	}
	if err := store.Tag(context.Background(), second, "stable"); err != nil {
		t.Fatal(err)
	}
	got, err := store.Resolve(context.Background(), "stable")
	if err != nil || got.Digest != second.Digest {
		t.Fatalf("resolved = %+v, %v", got, err)
	}
}

func TestAtomicUnknownTagIsNotFound(t *testing.T) {
	_, err := memory.New().Resolve(context.Background(), "missing")
	assertErrorIs(t, err, errdef.ErrNotFound)
}

func TestAtomicLayoutPushAndResolve(t *testing.T) {
	store, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	desc := descriptor("layout")
	push(t, store, desc, "layout")
	if err := store.Tag(context.Background(), desc, "current"); err != nil {
		t.Fatal(err)
	}
	got, err := store.Resolve(context.Background(), "current")
	if err != nil || got.Digest != desc.Digest {
		t.Fatalf("resolved = %+v, %v", got, err)
	}
}

func TestAtomicLayoutDeleteTarget(t *testing.T) {
	store, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	desc := descriptor("layout-untag")
	push(t, store, desc, "layout-untag")
	if err := store.Tag(context.Background(), desc, "gone"); err != nil {
		t.Fatal(err)
	}
	if err := store.Untag(context.Background(), "gone"); err != nil {
		t.Fatal(err)
	}
	_, err = store.Resolve(context.Background(), "gone")
	assertErrorIs(t, err, errdef.ErrNotFound)
	if fetch(t, store, desc) != "layout-untag" {
		t.Fatal("untag removed content")
	}
}

func TestAtomicFetchAllChecksDescriptor(t *testing.T) {
	store := memory.New()
	desc := descriptor("verified")
	push(t, store, desc, "verified")
	if got := fetch(t, store, desc); got != "verified" {
		t.Fatalf("got %q", got)
	}
}

func TestAtomicFetchAllRejectsTruncation(t *testing.T) {
	desc := descriptor("complete")
	if _, err := content.ReadAll(bytes.NewBufferString("comp"), desc); err == nil {
		t.Fatal("truncated stream accepted")
	}
}

func TestAtomicSubjectReceiptRecordsEdge(t *testing.T) {
	index := flow.NewReceiptIndex()
	subject, referrer := descriptor("subject"), descriptor("referrer")
	receipt, err := index.Record(subject, referrer)
	if err != nil || !receipt.Present || receipt.Revision != 1 {
		t.Fatalf("receipt = %+v, %v", receipt, err)
	}
	got, ok := index.Subject(referrer)
	if !ok || got.Digest != subject.Digest {
		t.Fatalf("subject = %+v, %v", got, ok)
	}
}

func TestAtomicSubjectReceiptIsIdempotent(t *testing.T) {
	index := flow.NewReceiptIndex()
	subject, referrer := descriptor("subject-idem"), descriptor("referrer-idem")
	first, _ := index.Record(subject, referrer)
	second, _ := index.Record(subject, referrer)
	if first.Revision != second.Revision || len(index.Referrers(subject)) != 1 {
		t.Fatalf("receipts = %+v / %+v", first, second)
	}
}

func TestAtomicReferrerReceiptRemovesLastEdge(t *testing.T) {
	index := flow.NewReceiptIndex()
	subject, referrer := descriptor("remove-subject"), descriptor("remove-referrer")
	_, _ = index.Record(subject, referrer)
	receipt, err := index.Remove(referrer)
	if err != nil || receipt.Present || len(index.Referrers(subject)) != 0 {
		t.Fatalf("receipt = %+v, err=%v", receipt, err)
	}
}

func TestAtomicReferrerReceiptRejectsWrongSubject(t *testing.T) {
	index := flow.NewReceiptIndex()
	_, err := index.Remove(descriptor("not-recorded"))
	assertErrorIs(t, err, errdef.ErrNotFound)
}

func TestAtomicSkipReceiptNamesDescriptor(t *testing.T) {
	journal := flow.NewCopyJournal()
	desc := descriptor("skip")
	receipt := journal.Record(desc, flow.Skipped, "")
	if receipt.Descriptor.Digest != desc.Digest || receipt.Disposition != flow.Skipped {
		t.Fatalf("receipt = %+v", receipt)
	}
}

func TestAtomicSkipReceiptDoesNotCountCopy(t *testing.T) {
	journal := flow.NewCopyJournal()
	journal.Record(descriptor("skip-count"), flow.Skipped, "")
	if journal.Counts()[flow.Copied] != 0 || journal.Counts()[flow.Skipped] != 1 {
		t.Fatalf("counts = %v", journal.Counts())
	}
}

func TestAtomicMountReceiptDistinguishesSource(t *testing.T) {
	journal := flow.NewCopyJournal()
	receipt := journal.Record(descriptor("mount"), flow.Mounted, "registry/source")
	if receipt.Source != "registry/source" || receipt.Disposition != flow.Mounted {
		t.Fatalf("receipt = %+v", receipt)
	}
}

func TestAtomicMountReceiptIsStable(t *testing.T) {
	journal := flow.NewCopyJournal()
	journal.Record(descriptor("mount-stable"), flow.Mounted, "repo")
	entries := journal.Entries()
	entries[0].Source = "changed"
	if journal.Entries()[0].Source != "repo" {
		t.Fatal("journal snapshot was not caller owned")
	}
}

func TestAtomicRetargetPreservesOldReachability(t *testing.T) {
	store, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	first, second := descriptor("old"), descriptor("new")
	push(t, store, first, "old")
	push(t, store, second, "new")
	if err := store.Tag(context.Background(), first, "current"); err != nil {
		t.Fatal(err)
	}
	receipt, err := flow.NewRetargeter(store).Retarget(context.Background(), "current", second)
	if err != nil || !receipt.PreviousPresent || fetch(t, store, first) != "old" {
		t.Fatalf("receipt = %+v, err=%v", receipt, err)
	}
}

func TestAtomicRetargetReturnsPreviousTarget(t *testing.T) {
	store, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	first, second := descriptor("previous"), descriptor("current")
	push(t, store, first, "previous")
	push(t, store, second, "current")
	_ = store.Tag(context.Background(), first, "tag")
	receipt, err := flow.NewRetargeter(store).Retarget(context.Background(), "tag", second)
	if err != nil || receipt.Previous.Digest != first.Digest || receipt.Current.Digest != second.Digest {
		t.Fatalf("receipt = %+v, err=%v", receipt, err)
	}
}

func TestAtomicUntagPreservesSharedContent(t *testing.T) {
	store, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	desc := descriptor("shared")
	push(t, store, desc, "shared")
	_ = store.Tag(context.Background(), desc, "one")
	_ = store.Tag(context.Background(), desc, "two")
	_, err = flow.NewRetargeter(store).Untag(context.Background(), "one")
	if err != nil || fetch(t, store, desc) != "shared" {
		t.Fatalf("untag err=%v", err)
	}
}

func TestAtomicUntagReceiptReportsOrphanState(t *testing.T) {
	store, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	desc := descriptor("orphan")
	push(t, store, desc, "orphan")
	_ = store.Tag(context.Background(), desc, "only")
	receipt, err := flow.NewRetargeter(store).Untag(context.Background(), "only")
	if err != nil || receipt.CurrentPresent || !receipt.Orphaned {
		t.Fatalf("receipt = %+v, err=%v", receipt, err)
	}
}

func TestAtomicVerifiedPushRejectsDigestMismatch(t *testing.T) {
	store := memory.New()
	receipt, err := flow.NewVerifier(store).Push(context.Background(), descriptor("expected"), bytes.NewBufferString("different"))
	if err == nil || receipt.Committed {
		t.Fatalf("receipt = %+v, err=%v", receipt, err)
	}
}

func TestAtomicVerifiedPushLeavesNoPartialBlob(t *testing.T) {
	store := memory.New()
	desc := descriptor("full-value")
	_, _ = flow.NewVerifier(store).Push(context.Background(), desc, bytes.NewBufferString("full"))
	exists, err := store.Exists(context.Background(), desc)
	if err != nil || exists {
		t.Fatalf("exists=%v err=%v", exists, err)
	}
}

func TestAtomicReopenRepairsMissingTarget(t *testing.T) {
	dir := t.TempDir()
	store, err := oci.New(dir)
	if err != nil {
		t.Fatal(err)
	}
	desc := descriptor("missing-target")
	push(t, store, desc, "missing-target")
	_ = store.Tag(context.Background(), desc, "stale")
	blob := filepath.Join(dir, ocispec.ImageBlobsDir, desc.Digest.Algorithm().String(), desc.Digest.Encoded())
	if err := os.Remove(blob); err != nil {
		t.Fatal(err)
	}
	reopened, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || !receipt.Changed || !reflect.DeepEqual(receipt.RemovedNames, []string{"stale"}) {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	_, err = reopened.Resolve(context.Background(), "stale")
	assertErrorIs(t, err, errdef.ErrNotFound)
}

func TestAtomicReopenReportsDiscardedIndexEntry(t *testing.T) {
	dir := t.TempDir()
	store, _ := oci.New(dir)
	desc := descriptor("discard")
	push(t, store, desc, "discard")
	_ = store.Tag(context.Background(), desc, "discarded")
	_ = os.Remove(filepath.Join(dir, ocispec.ImageBlobsDir, desc.Digest.Algorithm().String(), desc.Digest.Encoded()))
	_, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || len(receipt.MissingDescriptors) != 1 || receipt.MissingDescriptors[0].Digest != desc.Digest {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
}

func TestAtomicPagerRejectsRepeatedCursor(t *testing.T) {
	pager, _ := flow.NewPager(4)
	source := &tagPages{pages: map[string]struct {
		items []string
		next  string
	}{
		"": {[]string{"a"}, "same"}, "same": {[]string{"b"}, "same"},
	}}
	_, err := pager.CollectTags(context.Background(), source)
	assertErrorIs(t, err, flow.ErrCursorLoop)
}

func TestAtomicPagerHonorsPageBudget(t *testing.T) {
	pager, _ := flow.NewPager(1)
	source := &tagPages{pages: map[string]struct {
		items []string
		next  string
	}{
		"": {[]string{"a"}, "more"}, "more": {[]string{"b"}, ""},
	}}
	_, err := pager.CollectTags(context.Background(), source)
	assertErrorIs(t, err, flow.ErrPageBudget)
}

func TestAtomicCancelledIngestReturnsContextError(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	ingester, err := flow.NewFileIngester(memory.New(), t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	receipt, err := ingester.Ingest(ctx, descriptor("cancelled"), bytes.NewBufferString("cancelled"))
	assertErrorIs(t, err, context.Canceled)
	if receipt.Committed {
		t.Fatal("cancelled receipt committed")
	}
}

func TestAtomicCancelledIngestRemovesTemporaryFile(t *testing.T) {
	dir := t.TempDir()
	store := memory.New()
	ingester, _ := flow.NewFileIngester(store, dir)
	ctx, cancel := context.WithCancel(context.Background())
	receipt, err := ingester.Ingest(ctx, descriptor("cancelled"), &cancelAfterReader{cancel: cancel})
	assertErrorIs(t, err, context.Canceled)
	if receipt.Committed {
		t.Fatal("cancelled receipt committed")
	}
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 0 {
		t.Fatalf("staging entries=%v err=%v", entries, err)
	}
}

var _ = errors.Is
