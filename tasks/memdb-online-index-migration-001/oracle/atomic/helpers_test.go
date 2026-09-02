package memdb_test

import (
	"fmt"
	"sort"
	"sync"
	"testing"
	"time"

	memdb "github.com/hashicorp/go-memdb"
)

const testTimeout = 2 * time.Second

type row struct {
	ID       string
	Color    string
	Email    string
	Group    string
	Optional string
	Tags     []string
}

func baseSchema(tables ...string) *memdb.DBSchema {
	all := make(map[string]*memdb.TableSchema, len(tables))
	for _, name := range tables {
		all[name] = &memdb.TableSchema{Name: name, Indexes: map[string]*memdb.IndexSchema{
			"id":    {Name: "id", Unique: true, Indexer: &memdb.StringFieldIndex{Field: "ID"}},
			"color": {Name: "color", Indexer: &memdb.StringFieldIndex{Field: "Color"}},
			"tags":  {Name: "tags", Indexer: &memdb.StringSliceFieldIndex{Field: "Tags"}},
		}}
	}
	return &memdb.DBSchema{Tables: all}
}

func freshDB(t *testing.T, rows ...*row) *memdb.MemDB {
	t.Helper()
	db, err := memdb.NewMemDB(baseSchema("items"))
	if err != nil {
		t.Fatal(err)
	}
	insertRows(t, db, "items", rows...)
	return db
}

func normalizeRow(r *row) {
	if r.Color == "" {
		r.Color = "color-" + r.ID
	}
	if r.Tags == nil {
		r.Tags = []string{"tag-" + r.ID}
	}
}

func insertRows(t *testing.T, db *memdb.MemDB, table string, rows ...*row) {
	t.Helper()
	txn := db.Txn(true)
	defer txn.Abort()
	for _, r := range rows {
		normalizeRow(r)
		if err := txn.Insert(table, r); err != nil {
			t.Fatal(err)
		}
	}
	txn.Commit()
}

func stringIndex(name, field string) *memdb.IndexSchema {
	return &memdb.IndexSchema{Name: name, Indexer: &memdb.StringFieldIndex{Field: field}}
}

func queryIDs(t *testing.T, txn *memdb.Txn, table, index string, arg string) []string {
	t.Helper()
	iter, err := txn.Get(table, index, arg)
	if err != nil {
		t.Fatal(err)
	}
	var ids []string
	for raw := iter.Next(); raw != nil; raw = iter.Next() {
		ids = append(ids, raw.(*row).ID)
	}
	sort.Strings(ids)
	return ids
}

func safeGet(txn *memdb.Txn, table, index, arg string) (iter memdb.ResultIterator, err error) {
	defer func() {
		if recovered := recover(); recovered != nil {
			err = fmt.Errorf("query panicked: %v", recovered)
		}
	}()
	return txn.Get(table, index, arg)
}

func requireIDs(t *testing.T, got []string, want ...string) {
	t.Helper()
	sort.Strings(want)
	if fmt.Sprint(got) != fmt.Sprint(want) {
		t.Fatalf("ids=%v want=%v", got, want)
	}
}

func requireOpen(t *testing.T, ch <-chan struct{}) {
	t.Helper()
	select {
	case <-ch:
		t.Fatal("watch closed unexpectedly")
	case <-time.After(25 * time.Millisecond):
	}
}

func requireClosed(t *testing.T, ch <-chan struct{}) {
	t.Helper()
	select {
	case <-ch:
	case <-time.After(testTimeout):
		t.Fatal("watch did not close")
	}
}

type failingIndexer struct{ failID string }

func (f failingIndexer) FromArgs(args ...interface{}) ([]byte, error) {
	return (&memdb.StringFieldIndex{Field: "Email"}).FromArgs(args...)
}

func (f failingIndexer) FromObject(raw interface{}) (bool, []byte, error) {
	r := raw.(*row)
	if r.ID == f.failID {
		return false, nil, fmt.Errorf("indexer rejected %s", r.ID)
	}
	return (&memdb.StringFieldIndex{Field: "Email"}).FromObject(raw)
}

type blockingIndexer struct {
	once    sync.Once
	started chan struct{}
	release <-chan struct{}
}

func (b *blockingIndexer) FromArgs(args ...interface{}) ([]byte, error) {
	return (&memdb.StringFieldIndex{Field: "Email"}).FromArgs(args...)
}

func (b *blockingIndexer) FromObject(raw interface{}) (bool, []byte, error) {
	b.once.Do(func() {
		close(b.started)
		<-b.release
	})
	return (&memdb.StringFieldIndex{Field: "Email"}).FromObject(raw)
}
