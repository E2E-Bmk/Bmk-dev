package orasgate_test

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strconv"
	"strings"
	"sync"
	"testing"

	ocispec "github.com/opencontainers/image-spec/specs-go/v1"
	oras "oras.land/oras-go/v2"
	"oras.land/oras-go/v2/content"
	"oras.land/oras-go/v2/content/memory"
	"oras.land/oras-go/v2/content/oci"
	"oras.land/oras-go/v2/flow"
	"oras.land/oras-go/v2/registry/remote"
)

func descriptor(payload string) ocispec.Descriptor {
	return content.NewDescriptorFromBytes("application/vnd.go25.payload", []byte(payload))
}

func push(t *testing.T, target content.Pusher, desc ocispec.Descriptor, payload string) {
	t.Helper()
	if err := target.Push(context.Background(), desc, bytes.NewBufferString(payload)); err != nil {
		t.Fatalf("Push() error = %v", err)
	}
}

func fetch(t *testing.T, target content.Fetcher, desc ocispec.Descriptor) string {
	t.Helper()
	data, err := content.FetchAll(context.Background(), target, desc)
	if err != nil {
		t.Fatalf("FetchAll() error = %v", err)
	}
	return string(data)
}

func packedGraph(t *testing.T, target *memory.Store, payloads ...string) (ocispec.Descriptor, []ocispec.Descriptor) {
	t.Helper()
	children := make([]ocispec.Descriptor, 0, len(payloads))
	for _, payload := range payloads {
		desc := descriptor(payload)
		push(t, target, desc, payload)
		children = append(children, desc)
	}
	root, err := oras.Pack(context.Background(), target, "application/vnd.go25.artifact", children, oras.PackOptions{})
	if err != nil {
		t.Fatalf("Pack() error = %v", err)
	}
	return root, children
}

func requireDescriptorSet(t *testing.T, got, want []ocispec.Descriptor) {
	t.Helper()
	keys := func(rows []ocispec.Descriptor) map[string]bool {
		result := make(map[string]bool, len(rows))
		for _, row := range rows {
			result[row.Digest.String()] = true
		}
		return result
	}
	if !reflect.DeepEqual(keys(got), keys(want)) {
		t.Fatalf("descriptor set = %v, want %v", keys(got), keys(want))
	}
}

type tagPages struct {
	pages map[string]struct {
		items []string
		next  string
	}
	calls int
}

func (source *tagPages) TagsPage(ctx context.Context, cursor string) ([]string, string, error) {
	if err := ctx.Err(); err != nil {
		return nil, "", err
	}
	source.calls++
	page := source.pages[cursor]
	return append([]string(nil), page.items...), page.next, nil
}

type referrerPages struct {
	pages map[string]struct {
		items []ocispec.Descriptor
		next  string
	}
	calls int
}

func (source *referrerPages) ReferrersPage(ctx context.Context, cursor string) ([]ocispec.Descriptor, string, error) {
	if err := ctx.Err(); err != nil {
		return nil, "", err
	}
	source.calls++
	page := source.pages[cursor]
	return append([]ocispec.Descriptor(nil), page.items...), page.next, nil
}

type failTagStore struct {
	*oci.Store
	tagErr   error
	untagErr error
}

func (store *failTagStore) Tag(ctx context.Context, desc ocispec.Descriptor, name string) error {
	if store.tagErr != nil {
		return store.tagErr
	}
	return store.Store.Tag(ctx, desc, name)
}

func (store *failTagStore) Untag(ctx context.Context, name string) error {
	if store.untagErr != nil {
		return store.untagErr
	}
	return store.Store.Untag(ctx, name)
}

type cancelAfterReader struct {
	cancel context.CancelFunc
	done   bool
}

func (reader *cancelAfterReader) Read(p []byte) (int, error) {
	if reader.done {
		return 0, io.EOF
	}
	reader.done = true
	copy(p, "cancelled")
	reader.cancel()
	return len("cancelled"), nil
}

func assertErrorIs(t *testing.T, err, target error) {
	t.Helper()
	if !errors.Is(err, target) {
		t.Fatalf("error = %v, want errors.Is(_, %v)", err, target)
	}
}

var _ flow.TagPageSource = (*tagPages)(nil)
var _ flow.ReferrerPageSource = (*referrerPages)(nil)

type storedManifest struct {
	data      []byte
	mediaType string
}

type miniRegistry struct {
	mu        sync.Mutex
	blobs     map[string][]byte
	manifests map[string]storedManifest
	tags      map[string]string
	uploads   map[string][]byte
	nextID    int
}

func newMiniRegistry() *miniRegistry {
	return &miniRegistry{
		blobs: make(map[string][]byte), manifests: make(map[string]storedManifest),
		tags: make(map[string]string), uploads: make(map[string][]byte),
	}
}

func (registry *miniRegistry) ServeHTTP(writer http.ResponseWriter, request *http.Request) {
	registry.mu.Lock()
	defer registry.mu.Unlock()
	writer.Header().Set("Docker-Distribution-API-Version", "registry/2.0")
	if request.URL.Path == "/v2/" || request.URL.Path == "/v2" {
		writer.WriteHeader(http.StatusOK)
		return
	}
	path := strings.TrimPrefix(request.URL.Path, "/v2/")
	if marker := "/blobs/uploads/"; strings.Contains(path, marker) {
		repo, uploadPart, _ := strings.Cut(path, marker)
		_ = repo
		if request.Method == http.MethodPost {
			registry.nextID++
			id := fmt.Sprintf("u%d", registry.nextID)
			registry.uploads[id] = nil
			location := "/v2/" + repo + marker + id
			writer.Header().Set("Location", location)
			writer.Header().Set("Docker-Upload-UUID", id)
			writer.WriteHeader(http.StatusAccepted)
			return
		}
		id := strings.Trim(uploadPart, "/")
		body, _ := io.ReadAll(request.Body)
		registry.uploads[id] = append(registry.uploads[id], body...)
		if request.Method == http.MethodPatch {
			writer.Header().Set("Location", request.URL.Path)
			writer.Header().Set("Docker-Upload-UUID", id)
			writer.WriteHeader(http.StatusAccepted)
			return
		}
		if request.Method == http.MethodPut {
			digest := request.URL.Query().Get("digest")
			registry.blobs[digest] = append([]byte(nil), registry.uploads[id]...)
			delete(registry.uploads, id)
			writer.Header().Set("Docker-Content-Digest", digest)
			writer.Header().Set("Location", "/v2/"+repo+"/blobs/"+digest)
			writer.WriteHeader(http.StatusCreated)
			return
		}
	}
	if marker := "/blobs/"; strings.Contains(path, marker) {
		_, digest, _ := strings.Cut(path, marker)
		data, ok := registry.blobs[digest]
		if !ok {
			http.NotFound(writer, request)
			return
		}
		writer.Header().Set("Docker-Content-Digest", digest)
		writer.Header().Set("Content-Length", strconv.Itoa(len(data)))
		if request.Method == http.MethodGet {
			_, _ = writer.Write(data)
			return
		}
		writer.WriteHeader(http.StatusOK)
		return
	}
	if marker := "/manifests/"; strings.Contains(path, marker) {
		_, reference, _ := strings.Cut(path, marker)
		if request.Method == http.MethodPut {
			data, _ := io.ReadAll(request.Body)
			mediaType := request.Header.Get("Content-Type")
			desc := content.NewDescriptorFromBytes(mediaType, data)
			digest := desc.Digest.String()
			registry.manifests[digest] = storedManifest{data: append([]byte(nil), data...), mediaType: mediaType}
			if !strings.Contains(reference, ":") {
				registry.tags[reference] = digest
			}
			writer.Header().Set("Docker-Content-Digest", digest)
			writer.Header().Set("Location", request.URL.Path)
			writer.WriteHeader(http.StatusCreated)
			return
		}
		digest := reference
		if tagged, ok := registry.tags[reference]; ok {
			digest = tagged
		}
		manifest, ok := registry.manifests[digest]
		if !ok {
			http.NotFound(writer, request)
			return
		}
		writer.Header().Set("Docker-Content-Digest", digest)
		writer.Header().Set("Content-Type", manifest.mediaType)
		writer.Header().Set("Content-Length", strconv.Itoa(len(manifest.data)))
		if request.Method == http.MethodGet {
			_, _ = writer.Write(manifest.data)
			return
		}
		writer.WriteHeader(http.StatusOK)
		return
	}
	http.NotFound(writer, request)
}

func remoteTarget(t *testing.T) *remote.Repository {
	t.Helper()
	server := httptest.NewServer(newMiniRegistry())
	t.Cleanup(server.Close)
	repo, err := remote.NewRepository(strings.TrimPrefix(server.URL, "http://") + "/team/artifacts")
	if err != nil {
		t.Fatal(err)
	}
	repo.PlainHTTP = true
	return repo
}
