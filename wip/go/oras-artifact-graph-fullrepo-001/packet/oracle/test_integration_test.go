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
	oras "oras.land/oras-go/v2"
	"oras.land/oras-go/v2/content"
	"oras.land/oras-go/v2/content/file"
	"oras.land/oras-go/v2/content/memory"
	"oras.land/oras-go/v2/content/oci"
	"oras.land/oras-go/v2/errdef"
	"oras.land/oras-go/v2/flow"
)

func TestIntegrationPackResolveFetchSeam(t *testing.T) {
	store := memory.New()
	root, children := packedGraph(t, store, "one", "two")
	if err := store.Tag(context.Background(), root, "artifact"); err != nil {
		t.Fatal(err)
	}
	resolved, err := store.Resolve(context.Background(), "artifact")
	if err != nil || resolved.Digest != root.Digest {
		t.Fatalf("resolved=%+v err=%v", resolved, err)
	}
	successors, err := content.Successors(context.Background(), store, resolved)
	if err != nil {
		t.Fatal(err)
	}
	requireDescriptorSet(t, successors, children)
}

func TestIntegrationMemoryToLayoutCopySeam(t *testing.T) {
	source := memory.New()
	root, children := packedGraph(t, source, "left", "right")
	destination, err := oci.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if err := oras.CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	for _, desc := range append(children, root) {
		if fetch(t, destination, desc) != fetch(t, source, desc) {
			t.Fatalf("copied bytes differ for %s", desc.Digest)
		}
	}
}

func TestIntegrationTagReplaceResolveFetchSeam(t *testing.T) {
	store := memory.New()
	first, second := descriptor("tag-first"), descriptor("tag-second")
	push(t, store, first, "tag-first")
	push(t, store, second, "tag-second")
	_ = store.Tag(context.Background(), first, "current")
	_ = store.Tag(context.Background(), second, "current")
	resolved, err := store.Resolve(context.Background(), "current")
	if err != nil || resolved.Digest != second.Digest || fetch(t, store, resolved) != "tag-second" {
		t.Fatalf("resolved=%+v err=%v", resolved, err)
	}
}

func TestIntegrationFileStoreAddFetchSeam(t *testing.T) {
	input := filepath.Join(t.TempDir(), "payload.txt")
	if err := os.WriteFile(input, []byte("file payload"), 0o600); err != nil {
		t.Fatal(err)
	}
	store, err := file.New(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = store.Close() })
	desc, err := store.Add(context.Background(), "payload.txt", "text/plain", input)
	if err != nil || fetch(t, store, desc) != "file payload" {
		t.Fatalf("desc=%+v err=%v", desc, err)
	}
}

func TestIntegrationSuccessorsExposePackedChildren(t *testing.T) {
	store := memory.New()
	root, children := packedGraph(t, store, "s1", "s2", "s3")
	successors, err := content.Successors(context.Background(), store, root)
	if err != nil {
		t.Fatal(err)
	}
	requireDescriptorSet(t, successors, children)
	for _, child := range children {
		predecessors, err := store.Predecessors(context.Background(), child)
		if err != nil {
			t.Fatal(err)
		}
		requireDescriptorSet(t, predecessors, []ocispec.Descriptor{root})
	}
}

func TestIntegrationDeleteTargetKeepsReachableBlob(t *testing.T) {
	store, _ := oci.New(t.TempDir())
	desc := descriptor("shared-target")
	push(t, store, desc, "shared-target")
	_ = store.Tag(context.Background(), desc, "first")
	_ = store.Tag(context.Background(), desc, "second")
	if err := store.Untag(context.Background(), "first"); err != nil {
		t.Fatal(err)
	}
	resolved, err := store.Resolve(context.Background(), "second")
	if err != nil || resolved.Digest != desc.Digest || fetch(t, store, desc) != "shared-target" {
		t.Fatalf("resolved=%+v err=%v", resolved, err)
	}
}

func TestIntegrationSubjectReceiptUpdatesReferrerView(t *testing.T) {
	index := flow.NewReceiptIndex()
	subject := descriptor("receipt-subject")
	refs := []ocispec.Descriptor{descriptor("r1"), descriptor("r2")}
	for _, ref := range refs {
		if _, err := index.Record(subject, ref); err != nil {
			t.Fatal(err)
		}
	}
	requireDescriptorSet(t, index.Referrers(subject), refs)
	for _, ref := range refs {
		got, ok := index.Subject(ref)
		if !ok || got.Digest != subject.Digest {
			t.Fatalf("subject=%+v ok=%v", got, ok)
		}
	}
}

func TestIntegrationCopyPreservesSubjectClosure(t *testing.T) {
	source := memory.New()
	subject, _ := packedGraph(t, source, "subject-child")
	referrer, err := oras.Pack(context.Background(), source, "application/vnd.go25.referrer", nil, oras.PackOptions{Subject: &subject})
	if err != nil {
		t.Fatal(err)
	}
	destination := memory.New()
	if err := oras.CopyGraph(context.Background(), source, destination, referrer, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	successors, err := content.Successors(context.Background(), destination, referrer)
	if err != nil || !containsDigest(successors, subject) {
		t.Fatalf("successors=%v err=%v", successors, err)
	}
	index := flow.NewReceiptIndex()
	_, _ = index.Record(subject, referrer)
	got, ok := index.Subject(referrer)
	if !ok || got.Digest != subject.Digest {
		t.Fatalf("receipt subject=%+v ok=%v", got, ok)
	}
}

func TestIntegrationDeleteReferrerClosesBothViews(t *testing.T) {
	index := flow.NewReceiptIndex()
	subject, referrer := descriptor("delete-subject"), descriptor("delete-referrer")
	_, _ = index.Record(subject, referrer)
	if _, err := index.Remove(referrer); err != nil {
		t.Fatal(err)
	}
	if len(index.Referrers(subject)) != 0 {
		t.Fatal("subject view retained removed referrer")
	}
	if _, ok := index.Subject(referrer); ok {
		t.Fatal("referrer view retained removed subject")
	}
}

func TestIntegrationPreCopySkipMatchesDestinationState(t *testing.T) {
	source := memory.New()
	root, _ := packedGraph(t, source, "already-there")
	destination := memory.New()
	if err := oras.CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	journal := flow.NewCopyJournal()
	if err := flow.NewCoordinator(journal).CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	if journal.Counts()[flow.Skipped] != 1 || fetch(t, destination, root) != fetch(t, source, root) {
		t.Fatalf("entries=%+v counts=%v", journal.Entries(), journal.Counts())
	}
}

func TestIntegrationMountReceiptMatchesResolve(t *testing.T) {
	store, _ := oci.New(t.TempDir())
	desc := descriptor("mounted")
	push(t, store, desc, "mounted")
	_ = store.Tag(context.Background(), desc, "mounted")
	journal := flow.NewCopyJournal()
	receipt := journal.Record(desc, flow.Mounted, "source/repository")
	resolved, err := store.Resolve(context.Background(), "mounted")
	if err != nil || resolved.Digest != journal.Entries()[0].Descriptor.Digest || receipt.Disposition != flow.Mounted || receipt.Source != "source/repository" {
		t.Fatalf("resolved=%+v entries=%+v err=%v", resolved, journal.Entries(), err)
	}
}

func TestIntegrationMixedSkipCopyReceiptTotals(t *testing.T) {
	source := memory.New()
	root, _ := packedGraph(t, source, "mixed-a", "mixed-b")
	destination := memory.New()
	journal := flow.NewCopyJournal()
	coordinator := flow.NewCoordinator(journal)
	if err := coordinator.CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	if err := coordinator.CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	journal.Record(descriptor("mounted-account"), flow.Mounted, "source")
	counts := journal.Counts()
	if counts[flow.Copied] == 0 || counts[flow.Skipped] == 0 || counts[flow.Mounted] != 1 || counts[flow.Copied]+counts[flow.Skipped]+counts[flow.Mounted] != len(journal.Entries()) {
		t.Fatalf("entries=%+v counts=%v", journal.Entries(), counts)
	}
}

func TestIntegrationRetargetUpdatesResolveNotHistory(t *testing.T) {
	store, _ := oci.New(t.TempDir())
	first, second := descriptor("history-first"), descriptor("history-second")
	push(t, store, first, "history-first")
	push(t, store, second, "history-second")
	_ = store.Tag(context.Background(), first, "current")
	retargeter := flow.NewRetargeter(store)
	receipt, err := retargeter.Retarget(context.Background(), "current", second)
	if err != nil {
		t.Fatal(err)
	}
	resolved, _ := store.Resolve(context.Background(), "current")
	history := retargeter.History("current")
	if resolved.Digest != second.Digest || len(history) != 1 || history[0].Revision != receipt.Revision || history[0].Current.Digest != receipt.Current.Digest || history[0].Previous.Digest != first.Digest {
		t.Fatalf("resolved=%+v history=%+v", resolved, history)
	}
}

func TestIntegrationRetargetFailureRollsBackViews(t *testing.T) {
	base, _ := oci.New(t.TempDir())
	first, second := descriptor("rollback-first"), descriptor("rollback-second")
	push(t, base, first, "rollback-first")
	push(t, base, second, "rollback-second")
	_ = base.Tag(context.Background(), first, "current")
	store := &failTagStore{Store: base, tagErr: errors.New("injected tag failure")}
	retargeter := flow.NewRetargeter(store)
	if _, err := retargeter.Retarget(context.Background(), "current", second); err == nil {
		t.Fatal("retarget succeeded")
	}
	resolved, _ := base.Resolve(context.Background(), "current")
	if resolved.Digest != first.Digest || len(retargeter.History("current")) != 0 {
		t.Fatalf("resolved=%+v history=%+v", resolved, retargeter.History("current"))
	}
}

func TestIntegrationUntagSharedGraphRemainsCopyable(t *testing.T) {
	store, _ := oci.New(t.TempDir())
	desc := descriptor("untag-copy")
	push(t, store, desc, "untag-copy")
	_ = store.Tag(context.Background(), desc, "one")
	_ = store.Tag(context.Background(), desc, "two")
	if _, err := flow.NewRetargeter(store).Untag(context.Background(), "one"); err != nil {
		t.Fatal(err)
	}
	if _, err := store.Resolve(context.Background(), "one"); !errors.Is(err, errdef.ErrNotFound) {
		t.Fatalf("removed name resolve error=%v", err)
	}
	if resolved, err := store.Resolve(context.Background(), "two"); err != nil || resolved.Digest != desc.Digest {
		t.Fatalf("shared name resolved=%+v err=%v", resolved, err)
	}
	destination := memory.New()
	if err := oras.CopyGraph(context.Background(), store, destination, desc, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	if fetch(t, destination, desc) != "untag-copy" {
		t.Fatal("shared content was not copyable")
	}
}

func TestIntegrationVerifiedPushFailureLeavesResolveUnchanged(t *testing.T) {
	store := memory.New()
	current := descriptor("current-value")
	push(t, store, current, "current-value")
	_ = store.Tag(context.Background(), current, "current")
	_, err := flow.NewVerifier(store).Push(context.Background(), descriptor("expected-value"), bytes.NewBufferString("bad"))
	if err == nil {
		t.Fatal("mismatch succeeded")
	}
	resolved, _ := store.Resolve(context.Background(), "current")
	if resolved.Digest != current.Digest {
		t.Fatalf("resolved=%+v", resolved)
	}
}

func TestIntegrationFailedChildIngestLeavesNoGraphEdge(t *testing.T) {
	store := memory.New()
	subject := descriptor("existing-subject")
	push(t, store, subject, "existing-subject")
	badChild := descriptor("correct-child")
	_, err := flow.NewVerifier(store).Push(context.Background(), badChild, bytes.NewBufferString("wrong-child"))
	if err == nil {
		t.Fatal("bad child committed")
	}
	predecessors, err := store.Predecessors(context.Background(), badChild)
	if err != nil || len(predecessors) != 0 {
		t.Fatalf("predecessors=%v err=%v", predecessors, err)
	}
}

func TestIntegrationRetryAfterRollbackProducesOneReceipt(t *testing.T) {
	store := memory.New()
	desc := descriptor("retry-value")
	verifier := flow.NewVerifier(store)
	failed, firstErr := verifier.Push(context.Background(), desc, bytes.NewBufferString("bad"))
	committed, secondErr := verifier.Push(context.Background(), desc, bytes.NewBufferString("retry-value"))
	if firstErr == nil || failed.Committed || secondErr != nil || !committed.Committed || committed.Bytes != int64(len("retry-value")) {
		t.Fatalf("failed=%+v/%v committed=%+v/%v", failed, firstErr, committed, secondErr)
	}
}

func TestIntegrationReopenReconcilesIndexAndResolve(t *testing.T) {
	dir := t.TempDir()
	store, _ := oci.New(dir)
	desc, stale := descriptor("reopen-resolve"), descriptor("reopen-stale")
	push(t, store, desc, "reopen-resolve")
	push(t, store, stale, "reopen-stale")
	_ = store.Tag(context.Background(), desc, "stable")
	_ = store.Tag(context.Background(), stale, "stale")
	_ = os.Remove(filepath.Join(dir, ocispec.ImageBlobsDir, stale.Digest.Algorithm().String(), stale.Digest.Encoded()))
	reopened, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || !receipt.Changed || !reflect.DeepEqual(receipt.RemovedNames, []string{"stale"}) {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	resolved, err := reopened.Resolve(context.Background(), "stable")
	if err != nil || resolved.Digest != desc.Digest {
		t.Fatalf("resolved=%+v err=%v", resolved, err)
	}
	if _, err := reopened.Resolve(context.Background(), "stale"); !errors.Is(err, errdef.ErrNotFound) {
		t.Fatalf("stale resolve error=%v", err)
	}
}

func TestIntegrationReconcileKeepsReachableReferrers(t *testing.T) {
	dir := t.TempDir()
	store, _ := oci.New(dir)
	subject := descriptor("reconcile-subject")
	referrer := descriptor("reconcile-referrer")
	push(t, store, subject, "reconcile-subject")
	push(t, store, referrer, "reconcile-referrer")
	_ = store.Tag(context.Background(), subject, "subject")
	_ = store.Tag(context.Background(), referrer, "referrer")
	index := flow.NewReceiptIndex()
	_, _ = index.Record(subject, referrer)
	reopened, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || receipt.Changed {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	if fetch(t, reopened, referrer) != "reconcile-referrer" || len(index.Referrers(subject)) != 1 {
		t.Fatal("reopen did not preserve referrer projections")
	}
}

func TestIntegrationSecondReopenHasEmptyRepairReceipt(t *testing.T) {
	dir := t.TempDir()
	store, _ := oci.New(dir)
	desc := descriptor("second-reopen")
	push(t, store, desc, "second-reopen")
	_ = store.Tag(context.Background(), desc, "gone")
	_ = os.Remove(filepath.Join(dir, ocispec.ImageBlobsDir, desc.Digest.Algorithm().String(), desc.Digest.Encoded()))
	_, first, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || !first.Changed {
		t.Fatalf("first=%+v err=%v", first, err)
	}
	_, second, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || second.Changed || len(second.RemovedNames) != 0 || len(second.MissingDescriptors) != 0 {
		t.Fatalf("second=%+v err=%v", second, err)
	}
}

func TestIntegrationTagPagerRejectsCursorLoop(t *testing.T) {
	pager, _ := flow.NewPager(5)
	source := &tagPages{pages: map[string]struct {
		items []string
		next  string
	}{"": {[]string{"one"}, "next"}, "next": {[]string{"two"}, "next"}}}
	result, err := pager.CollectTags(context.Background(), source)
	assertErrorIs(t, err, flow.ErrCursorLoop)
	if result != nil || source.calls != 2 {
		t.Fatalf("result=%v calls=%d", result, source.calls)
	}
}

func TestIntegrationReferrerPagerAccumulatesUniqueDescriptors(t *testing.T) {
	first, second := descriptor("page-r1"), descriptor("page-r2")
	pager, _ := flow.NewPager(3)
	source := &referrerPages{pages: map[string]struct {
		items []ocispec.Descriptor
		next  string
	}{"": {[]ocispec.Descriptor{first, second}, "last"}, "last": {[]ocispec.Descriptor{first}, ""}}}
	result, err := pager.CollectReferrers(context.Background(), source)
	if err != nil {
		t.Fatal(err)
	}
	requireDescriptorSet(t, result, []ocispec.Descriptor{first, second})
	index := flow.NewReceiptIndex()
	subject := descriptor("paged-subject")
	for _, referrer := range result {
		_, _ = index.Record(subject, referrer)
	}
	requireDescriptorSet(t, index.Referrers(subject), result)
}

func TestIntegrationCancelledFileIngestDoesNotRetarget(t *testing.T) {
	store, _ := oci.New(t.TempDir())
	current := descriptor("cancel-current")
	push(t, store, current, "cancel-current")
	_ = store.Tag(context.Background(), current, "current")
	ingester, _ := flow.NewFileIngester(store, t.TempDir())
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := ingester.Ingest(ctx, descriptor("cancel-next"), bytes.NewBufferString("cancel-next"))
	assertErrorIs(t, err, context.Canceled)
	resolved, _ := store.Resolve(context.Background(), "current")
	if resolved.Digest != current.Digest {
		t.Fatalf("resolved=%+v", resolved)
	}
}

func TestSystemPackCopyLayoutReopenRoundTrip(t *testing.T) {
	source := memory.New()
	root, children := packedGraph(t, source, "system-left", "system-right")
	_ = source.Tag(context.Background(), root, "artifact")
	dir := t.TempDir()
	destination, _ := oci.New(dir)
	if _, err := oras.Copy(context.Background(), source, "artifact", destination, "artifact-copy", oras.CopyOptions{}); err != nil {
		t.Fatal(err)
	}
	reopened, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || receipt.Changed {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	resolved, err := reopened.Resolve(context.Background(), "artifact-copy")
	if err != nil || resolved.Digest != root.Digest {
		t.Fatalf("resolved=%+v err=%v", resolved, err)
	}
	for _, desc := range append(children, root) {
		if fetch(t, reopened, desc) != fetch(t, source, desc) {
			t.Fatalf("bytes differ for %s", desc.Digest)
		}
	}
}

func TestSystemRegistryPullCopyPushRoundTrip(t *testing.T) {
	source := memory.New()
	root, _ := packedGraph(t, source, "remote-one", "remote-two")
	_ = source.Tag(context.Background(), root, "artifact")
	remoteRepo := remoteTarget(t)
	pushed, err := oras.Copy(context.Background(), source, "artifact", remoteRepo, "release", oras.CopyOptions{})
	if err != nil {
		t.Fatal(err)
	}
	destination := memory.New()
	pulled, err := oras.Copy(context.Background(), remoteRepo, "release", destination, "local", oras.CopyOptions{})
	if err != nil || pulled.Digest != pushed.Digest || pulled.Digest != root.Digest {
		t.Fatalf("pushed=%+v pulled=%+v err=%v", pushed, pulled, err)
	}
	resolved, err := destination.Resolve(context.Background(), "local")
	if err != nil || resolved.Digest != root.Digest {
		t.Fatalf("resolved=%+v err=%v", resolved, err)
	}
}

func TestSystemCorruptChildRollbackAndCleanRetry(t *testing.T) {
	source := memory.New()
	bad := descriptor("valid-child")
	failed, err := flow.NewVerifier(source).Push(context.Background(), bad, bytes.NewBufferString("invalid-child"))
	if err == nil || failed.Committed {
		t.Fatalf("failed=%+v err=%v", failed, err)
	}
	committed, err := flow.NewVerifier(source).Push(context.Background(), bad, bytes.NewBufferString("valid-child"))
	if err != nil || !committed.Committed {
		t.Fatalf("committed=%+v err=%v", committed, err)
	}
	root, err := oras.Pack(context.Background(), source, "application/vnd.go25.artifact", []ocispec.Descriptor{bad}, oras.PackOptions{})
	if err != nil {
		t.Fatal(err)
	}
	destination := memory.New()
	journal := flow.NewCopyJournal()
	if err := flow.NewCoordinator(journal).CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	if fetch(t, destination, bad) != "valid-child" || journal.Counts()[flow.Copied] < 2 {
		t.Fatalf("journal=%+v", journal.Entries())
	}
}

func TestSystemCrashLayoutReconcileThenCopy(t *testing.T) {
	dir := t.TempDir()
	store, _ := oci.New(dir)
	keep, drop := descriptor("keep"), descriptor("drop")
	push(t, store, keep, "keep")
	push(t, store, drop, "drop")
	_ = store.Tag(context.Background(), keep, "keep")
	_ = store.Tag(context.Background(), drop, "drop")
	_ = os.Remove(filepath.Join(dir, ocispec.ImageBlobsDir, drop.Digest.Algorithm().String(), drop.Digest.Encoded()))
	reopened, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || !receipt.Changed {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	destination := memory.New()
	if err := oras.CopyGraph(context.Background(), reopened, destination, keep, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	if fetch(t, destination, keep) != "keep" {
		t.Fatal("retained graph was not copyable")
	}
}

func TestSystemBoundedTagPaginationFeedsCopy(t *testing.T) {
	source := memory.New()
	first, _ := packedGraph(t, source, "tag-page-first")
	second, _ := packedGraph(t, source, "tag-page-second")
	if err := source.Tag(context.Background(), first, "one"); err != nil {
		t.Fatal(err)
	}
	if err := source.Tag(context.Background(), second, "two"); err != nil {
		t.Fatal(err)
	}
	pages := &tagPages{pages: map[string]struct {
		items []string
		next  string
	}{
		"":     {[]string{"one"}, "more"},
		"more": {[]string{"two", "one"}, ""},
	}}
	pager, _ := flow.NewPager(3)
	tags, err := pager.CollectTags(context.Background(), pages)
	if err != nil {
		t.Fatal(err)
	}
	if len(tags) != 2 || tags[0] != "one" || tags[1] != "two" {
		t.Fatalf("tags=%v", tags)
	}
	destination, _ := oci.New(t.TempDir())
	for _, tag := range tags {
		if _, err := oras.Copy(context.Background(), source, tag, destination, tag, oras.CopyOptions{}); err != nil {
			t.Fatal(err)
		}
	}
	for _, tag := range []string{"one", "two"} {
		if _, err := destination.Resolve(context.Background(), tag); err != nil {
			t.Fatalf("resolve %s: %v", tag, err)
		}
	}
}

func TestSystemBoundedReferrersCloseSubjectGraph(t *testing.T) {
	source := memory.New()
	subject, _ := packedGraph(t, source, "subject-child")
	first, err := oras.Pack(context.Background(), source, "application/vnd.go25.referrer", nil, oras.PackOptions{Subject: &subject})
	if err != nil {
		t.Fatal(err)
	}
	child := descriptor("referrer-child")
	push(t, source, child, "referrer-child")
	second, err := oras.Pack(context.Background(), source, "application/vnd.go25.referrer", []ocispec.Descriptor{child}, oras.PackOptions{Subject: &subject})
	if err != nil {
		t.Fatal(err)
	}
	pages := &referrerPages{pages: map[string]struct {
		items []ocispec.Descriptor
		next  string
	}{
		"":     {[]ocispec.Descriptor{first}, "more"},
		"more": {[]ocispec.Descriptor{second, first}, ""},
	}}
	pager, _ := flow.NewPager(3)
	referrers, err := pager.CollectReferrers(context.Background(), pages)
	if err != nil {
		t.Fatal(err)
	}
	destination := memory.New()
	index := flow.NewReceiptIndex()
	for _, referrer := range referrers {
		if err := oras.CopyGraph(context.Background(), source, destination, referrer, oras.CopyGraphOptions{}); err != nil {
			t.Fatal(err)
		}
		if _, err := index.Record(subject, referrer); err != nil {
			t.Fatal(err)
		}
	}
	requireDescriptorSet(t, index.Referrers(subject), []ocispec.Descriptor{first, second})
}

func TestSystemCancelIngestReopenShowsNoPartialState(t *testing.T) {
	dir := t.TempDir()
	store, _ := oci.New(dir)
	ingester, _ := flow.NewFileIngester(store, t.TempDir())
	ctx, cancel := context.WithCancel(context.Background())
	desc := descriptor("cancelled")
	_, err := ingester.Ingest(ctx, desc, &cancelAfterReader{cancel: cancel})
	assertErrorIs(t, err, context.Canceled)
	reopened, receipt, err := flow.ReopenLayout(context.Background(), dir)
	if err != nil || receipt.Changed {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	if exists, err := reopened.Exists(context.Background(), desc); err != nil || exists {
		t.Fatalf("exists=%v err=%v", exists, err)
	}
}

func TestSystemCancelThenRetryClosesCopyReceipts(t *testing.T) {
	source := memory.New()
	ingester, _ := flow.NewFileIngester(source, t.TempDir())
	desc := descriptor("cancel-then-retry")
	ctx, cancel := context.WithCancel(context.Background())
	if _, err := ingester.Ingest(ctx, desc, &cancelAfterReader{cancel: cancel}); !errors.Is(err, context.Canceled) {
		t.Fatalf("cancel error=%v", err)
	}
	if receipt, err := ingester.Ingest(context.Background(), desc, bytes.NewBufferString("cancel-then-retry")); err != nil || !receipt.Committed {
		t.Fatalf("receipt=%+v err=%v", receipt, err)
	}
	root, err := oras.Pack(context.Background(), source, "application/vnd.go25.artifact", []ocispec.Descriptor{desc}, oras.PackOptions{})
	if err != nil {
		t.Fatal(err)
	}
	destination := memory.New()
	journal := flow.NewCopyJournal()
	if err := flow.NewCoordinator(journal).CopyGraph(context.Background(), source, destination, root, oras.CopyGraphOptions{}); err != nil {
		t.Fatal(err)
	}
	if fetch(t, destination, desc) != "cancel-then-retry" || journal.Counts()[flow.Copied] < 2 {
		t.Fatalf("entries=%+v", journal.Entries())
	}
}

func containsDigest(rows []ocispec.Descriptor, want ocispec.Descriptor) bool {
	for _, row := range rows {
		if row.Digest == want.Digest {
			return true
		}
	}
	return false
}
