package blevegate_test

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"testing"

	bleve "github.com/blevesearch/bleve/v2"
	"github.com/blevesearch/bleve/v2/mapping"
	"github.com/blevesearch/bleve/v2/search/query"
)

func must(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

func textMapping() *mapping.IndexMappingImpl {
	m := bleve.NewIndexMapping()
	d := bleve.NewDocumentMapping()
	body := bleve.NewTextFieldMapping()
	body.Store = true
	tag := bleve.NewKeywordFieldMapping()
	tag.Store = true
	d.AddFieldMappingsAt("body", body)
	d.AddFieldMappingsAt("tag", tag)
	m.DefaultMapping = d
	return m
}

func memIndex(t *testing.T) bleve.Index {
	t.Helper()
	idx, err := bleve.NewMemOnly(textMapping())
	must(t, err)
	t.Cleanup(func() { _ = idx.Close() })
	return idx
}

func addDocs(t *testing.T, idx bleve.Index, docs map[string]map[string]interface{}) {
	t.Helper()
	ids := make([]string, 0, len(docs))
	for id := range docs {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		must(t, idx.Index(id, docs[id]))
	}
}

func planFor(t *testing.T, q query.Query) *bleve.ObservationPlan {
	t.Helper()
	p := bleve.NewObservationPlan()
	must(t, p.AddDocument("doc", "a"))
	r := bleve.NewSearchRequest(q)
	r.Size = 20
	r.Fields = []string{"body", "tag"}
	r.SortBy([]string{"_id"})
	must(t, p.AddSearch("hits", r))
	must(t, p.AddDictionary("terms", "tag", nil, nil))
	p.IncludeMapping()
	return p
}

func requireReceipt(t *testing.T, idx bleve.Index, plan *bleve.ObservationPlan) *bleve.IndexReceipt {
	t.Helper()
	receipt, err := bleve.CaptureIndex(idx, plan)
	must(t, err)
	must(t, receipt.Validate())
	if receipt.Digest() == "" {
		t.Fatal("empty semantic digest")
	}
	return receipt
}

func assertMappedReceipt(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "alpha beta", "tag": "red"}})
	r := requireReceipt(t, idx, planFor(t, bleve.NewTermQuery("alpha")))
	fields, ok := r.DocumentFields("doc")
	if !ok || len(fields["body"]) == 0 || fields["body"][0] != "alpha beta" {
		t.Fatalf("mapped document lineage missing: %#v", fields)
	}
	if len(r.MappingJSON()) == 0 {
		t.Fatal("mapping was not captured")
	}
}

func assertBatchReceipt(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	b := idx.NewBatch()
	must(t, b.Index("a", map[string]interface{}{"body": "alpha", "tag": "red"}))
	must(t, b.Index("b", map[string]interface{}{"body": "beta", "tag": "blue"}))
	must(t, idx.Batch(b))
	r := requireReceipt(t, idx, planFor(t, bleve.NewMatchAllQuery()))
	if r.Count() != 2 {
		t.Fatalf("batch receipt count=%d", r.Count())
	}
	ids, ok := r.SearchIDs("hits")
	if !ok || strings.Join(ids, ",") != "a,b" {
		t.Fatalf("batch hit generation=%v", ids)
	}
}

func assertQueryReceipt(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"b": {"body": "alpha two", "tag": "red"}, "a": {"body": "alpha one", "tag": "blue"}})
	q := bleve.NewMatchQuery("alpha")
	q.SetField("body")
	r := requireReceipt(t, idx, planFor(t, q))
	ids, ok := r.SearchIDs("hits")
	if !ok || strings.Join(ids, ",") != "a,b" {
		t.Fatalf("normalized query order=%v", ids)
	}
	total, ok := r.SearchTotal("hits")
	if !ok || total != 2 {
		t.Fatalf("query total=%d", total)
	}
}

func assertFacetDictionaryReceipt(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "alpha", "tag": "red"}, "b": {"body": "beta", "tag": "red"}, "c": {"body": "gamma", "tag": "blue"}})
	req := bleve.NewSearchRequest(bleve.NewMatchAllQuery())
	req.SortBy([]string{"_id"})
	req.AddFacet("tags", bleve.NewFacetRequest("tag", 10))
	p := bleve.NewObservationPlan()
	must(t, p.AddSearch("hits", req))
	must(t, p.AddDictionary("terms", "tag", nil, nil))
	r := requireReceipt(t, idx, p)
	entries, ok := r.Dictionary("terms")
	if !ok || len(entries) != 2 || entries[1].Term != "red" || entries[1].Count != 2 {
		t.Fatalf("dictionary=%v", entries)
	}
	facets, ok := r.FacetTerms("hits", "tags")
	if !ok || facets["red"] != 2 || facets["blue"] != 1 {
		t.Fatalf("facets=%v", facets)
	}
}

func durableIndex(t *testing.T, path string) bleve.Index {
	t.Helper()
	idx, err := bleve.New(path, textMapping())
	must(t, err)
	return idx
}

func scratchDir(t *testing.T) string {
	t.Helper()
	dir, err := os.MkdirTemp("", "bleve-go25-")
	must(t, err)
	t.Cleanup(func() { _ = os.RemoveAll(dir) })
	return dir
}

func assertReopenReceipt(t *testing.T) {
	t.Parallel()
	memory := memIndex(t)
	addDocs(t, memory, map[string]map[string]interface{}{"a": {"body": "alpha", "tag": "red"}, "b": {"body": "beta", "tag": "blue"}})
	path := filepath.Join(scratchDir(t), "index")
	idx := durableIndex(t, path)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "alpha", "tag": "red"}, "b": {"body": "beta", "tag": "blue"}})
	plan := bleve.NewObservationPlan()
	req := bleve.NewSearchRequest(bleve.NewMatchAllQuery())
	req.SortBy([]string{"_id"})
	req.Fields = []string{"body", "tag"}
	must(t, plan.AddSearch("hits", req))
	must(t, plan.AddDictionary("terms", "tag", nil, nil))
	memoryReceipt := requireReceipt(t, memory, plan)
	before := requireReceipt(t, idx, plan)
	if !memoryReceipt.Equivalent(before) {
		memoryIDs, _ := memoryReceipt.SearchIDs("hits")
		durableIDs, _ := before.SearchIDs("hits")
		memoryDict, _ := memoryReceipt.Dictionary("terms")
		durableDict, _ := before.Dictionary("terms")
		t.Fatalf("memory and durable receipts differ: digest=%s/%s count=%d/%d fields=%v/%v ids=%v/%v dict=%v/%v", memoryReceipt.Digest(), before.Digest(), memoryReceipt.Count(), before.Count(), memoryReceipt.Fields(), before.Fields(), memoryIDs, durableIDs, memoryDict, durableDict)
	}
	must(t, idx.Close())
	reopened, err := bleve.Open(path)
	must(t, err)
	defer reopened.Close()
	after := requireReceipt(t, reopened, plan)
	if !before.Equivalent(after) || before.Digest() != after.Digest() {
		t.Fatalf("reopen changed receipt: %s %s", before.Digest(), after.Digest())
	}
}

func assertAliasReceipt(t *testing.T) {
	t.Parallel()
	left := memIndex(t)
	right := memIndex(t)
	addDocs(t, left, map[string]map[string]interface{}{"a": {"body": "alpha", "tag": "red"}})
	addDocs(t, right, map[string]map[string]interface{}{"b": {"body": "beta", "tag": "blue"}})
	alias := bleve.NewIndexAlias(left, right)
	p := bleve.NewObservationPlan()
	req := bleve.NewSearchRequest(bleve.NewMatchAllQuery())
	req.SortBy([]string{"_id"})
	must(t, p.AddSearch("hits", req))
	r := requireReceipt(t, alias, p)
	ids, ok := r.SearchIDs("hits")
	if !ok || strings.Join(ids, ",") != "a,b" || r.Count() != 2 {
		t.Fatalf("alias receipt count=%d ids=%v", r.Count(), ids)
	}
}

func assertFailureReceipt(t *testing.T) {
	t.Parallel()
	left := memIndex(t)
	right := memIndex(t)
	addDocs(t, left, map[string]map[string]interface{}{"a": {"body": "alpha", "tag": "red"}})
	addDocs(t, right, map[string]map[string]interface{}{"b": {"body": "beta", "tag": "blue"}})
	alias := bleve.NewIndexAlias(left, right)
	p := bleve.NewObservationPlan()
	req := bleve.NewSearchRequest(bleve.NewMatchAllQuery())
	req.SortBy([]string{"_id"})
	must(t, p.AddSearch("hits", req))
	before := requireReceipt(t, alias, p)
	if err := alias.Index("bad", map[string]interface{}{"body": "bad"}); err == nil {
		t.Fatal("ambiguous alias write unexpectedly succeeded")
	}
	after := requireReceipt(t, alias, p)
	if !before.Equivalent(after) {
		t.Fatal("failed publication changed receipt")
	}
}

func nativeCount(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	n, err := idx.DocCount()
	must(t, err)
	if n != 0 {
		t.Fatalf("count=%d", n)
	}
	must(t, idx.Index("a", map[string]interface{}{"body": "alpha"}))
	n, err = idx.DocCount()
	must(t, err)
	if n != 1 {
		t.Fatalf("count=%d", n)
	}
}
func nativeTerm(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "alpha"}})
	q := bleve.NewTermQuery("alpha")
	q.SetField("body")
	r, err := idx.Search(bleve.NewSearchRequest(q))
	must(t, err)
	if r.Total != 1 || r.Hits[0].ID != "a" {
		t.Fatalf("term result=%v", r)
	}
}
func nativeStored(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "alpha"}})
	q := bleve.NewTermQuery("alpha")
	q.SetField("body")
	req := bleve.NewSearchRequest(q)
	req.Fields = []string{"body"}
	r, err := idx.Search(req)
	must(t, err)
	if r.Total != 1 || r.Hits[0].Fields["body"] != "alpha" {
		t.Fatalf("stored=%v", r.Hits)
	}
}
func nativeDelete(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	must(t, idx.Delete("missing"))
	must(t, idx.Index("a", map[string]interface{}{"body": "alpha"}))
	must(t, idx.Delete("a"))
	n, err := idx.DocCount()
	must(t, err)
	if n != 0 {
		t.Fatalf("count=%d", n)
	}
}
func nativePagination(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "x"}, "b": {"body": "x"}, "c": {"body": "x"}})
	req := bleve.NewSearchRequestOptions(bleve.NewMatchAllQuery(), 1, 1, false)
	req.SortBy([]string{"_id"})
	r, err := idx.Search(req)
	must(t, err)
	if len(r.Hits) != 1 || r.Hits[0].ID != "b" {
		t.Fatalf("page=%v", r.Hits)
	}
}
func nativeHighlight(t *testing.T) {
	t.Parallel()
	idx := memIndex(t)
	addDocs(t, idx, map[string]map[string]interface{}{"a": {"body": "alpha beta"}})
	q := bleve.NewMatchQuery("alpha")
	q.SetField("body")
	req := bleve.NewSearchRequest(q)
	req.Highlight = bleve.NewHighlight()
	req.Highlight.AddField("body")
	r, err := idx.Search(req)
	must(t, err)
	if len(r.Hits) != 1 || len(r.Hits[0].Fragments["body"]) == 0 {
		t.Fatalf("fragments=%v", r.Hits)
	}
}
func nativeReopen(t *testing.T) string {
	t.Parallel()
	path := filepath.Join(scratchDir(t), "index")
	idx := durableIndex(t, path)
	must(t, idx.Index("a", map[string]interface{}{"body": "alpha"}))
	must(t, idx.Close())
	reopened, err := bleve.Open(path)
	must(t, err)
	defer reopened.Close()
	q := bleve.NewTermQuery("alpha")
	q.SetField("body")
	r, err := reopened.Search(bleve.NewSearchRequest(q))
	must(t, err)
	if r.Total != 1 {
		t.Fatalf("reopen hits=%d", r.Total)
	}
	return path
}
func nativeReadOnly(t *testing.T) {
	t.Parallel()
	path := filepath.Join(scratchDir(t), "index")
	idx := durableIndex(t, path)
	must(t, idx.Index("a", map[string]interface{}{"body": "alpha"}))
	must(t, idx.Close())
	ro, err := bleve.OpenUsing(path, map[string]interface{}{"read_only": true})
	must(t, err)
	defer ro.Close()
	n, err := ro.DocCount()
	must(t, err)
	if n != 1 {
		t.Fatalf("count=%d", n)
	}
}
func nativeAlias(t *testing.T) {
	t.Parallel()
	left := memIndex(t)
	right := memIndex(t)
	must(t, left.Index("a", map[string]interface{}{"body": "alpha"}))
	must(t, right.Index("b", map[string]interface{}{"body": "beta"}))
	alias := bleve.NewIndexAlias(left, right)
	req := bleve.NewSearchRequest(bleve.NewMatchAllQuery())
	req.SortBy([]string{"_id"})
	r, err := alias.Search(req)
	must(t, err)
	if r.Total != 2 || r.Hits[0].ID != "a" || r.Hits[1].ID != "b" {
		t.Fatalf("alias=%v", r.Hits)
	}
}

var cliOnce sync.Once
var cliPath string
var cliBuildErr error

func cliBinary() (string, error) {
	cliOnce.Do(func() {
		suffix := ""
		if runtime.GOOS == "windows" {
			suffix = ".exe"
		}
		cliPath = filepath.Join(os.TempDir(), fmt.Sprintf("bleve-gate-%d%s", os.Getpid(), suffix))
		goexe := filepath.Join(runtime.GOROOT(), "bin", "go")
		if runtime.GOOS == "windows" {
			goexe += ".exe"
		}
		cmd := exec.Command(goexe, "build", "-o", cliPath, "github.com/blevesearch/bleve/v2/cmd/bleve")
		var out bytes.Buffer
		cmd.Stdout = &out
		cmd.Stderr = &out
		if err := cmd.Run(); err != nil {
			cliBuildErr = fmt.Errorf("build bleve CLI: %w: %s", err, out.String())
		}
	})
	return cliPath, cliBuildErr
}
func nativeCLI(t *testing.T, mode string) {
	t.Parallel()
	path := filepath.Join(scratchDir(t), "index")
	idx := durableIndex(t, path)
	must(t, idx.Index("a", map[string]interface{}{"body": "alpha"}))
	if mode == "count" {
		must(t, idx.Index("b", map[string]interface{}{"body": "beta"}))
		must(t, idx.Delete("a"))
	}
	must(t, idx.Close())
	binary, err := cliBinary()
	must(t, err)
	args := []string{mode, path}
	if mode == "query" {
		args = append(args, "body:alpha")
	}
	out, err := exec.Command(binary, args...).CombinedOutput()
	must(t, err)
	if mode == "count" && strings.TrimSpace(string(out)) != "1" {
		t.Fatalf("count output=%q", out)
	}
	if mode == "query" && !strings.Contains(string(out), "1. a") {
		t.Fatalf("query output=%q", out)
	}
}
