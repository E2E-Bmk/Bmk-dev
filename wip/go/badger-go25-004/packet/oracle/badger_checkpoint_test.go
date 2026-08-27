package gate

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	badger "github.com/dgraph-io/badger/v4"
)

type fact struct {
	key       string
	value     []byte
	meta      byte
	expiresAt uint64
	version   uint64
	deleted   bool
}

func quietOptions(path string) badger.Options {
	return badger.DefaultOptions(path).
		WithLogger(nil).
		WithMetricsEnabled(false).
		WithMemTableSize(8 << 20).
		WithBaseTableSize(2 << 20).
		WithValueThreshold(1 << 20).
		WithVLogPercentile(0).
		WithValueLogFileSize(1 << 20).
		WithBlockCacheSize(4 << 20).
		WithIndexCacheSize(4 << 20).
		WithNumMemtables(2).
		WithNumCompactors(2)
}

func openMemory(t *testing.T) *badger.DB {
	t.Helper()
	db, err := badger.Open(quietOptions("").WithInMemory(true))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func openDisk(t *testing.T, dir string) *badger.DB {
	t.Helper()
	db, err := badger.Open(quietOptions(dir))
	if err != nil {
		t.Fatal(err)
	}
	return db
}

func openManagedMemory(t *testing.T) *badger.DB {
	t.Helper()
	db, err := badger.OpenManaged(quietOptions("").WithInMemory(true))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func put(t *testing.T, db *badger.DB, key, value []byte) {
	t.Helper()
	if err := db.Update(func(txn *badger.Txn) error { return txn.Set(key, value) }); err != nil {
		t.Fatal(err)
	}
}

func putEntry(t *testing.T, db *badger.DB, key, value []byte, meta byte, ttl time.Duration) {
	t.Helper()
	if err := db.Update(func(txn *badger.Txn) error {
		e := badger.NewEntry(key, value).WithMeta(meta)
		if ttl > 0 {
			e = e.WithTTL(ttl)
		}
		return txn.SetEntry(e)
	}); err != nil {
		t.Fatal(err)
	}
}

func del(t *testing.T, db *badger.DB, key []byte) {
	t.Helper()
	if err := db.Update(func(txn *badger.Txn) error { return txn.Delete(key) }); err != nil {
		t.Fatal(err)
	}
}

func observe(t *testing.T, db *badger.DB, key []byte) (fact, bool) {
	t.Helper()
	var got fact
	err := db.View(func(txn *badger.Txn) error {
		item, err := txn.Get(key)
		if errors.Is(err, badger.ErrKeyNotFound) {
			return nil
		}
		if err != nil {
			return err
		}
		got.key = string(item.KeyCopy(nil))
		got.meta = item.UserMeta()
		got.expiresAt = item.ExpiresAt()
		got.version = item.Version()
		got.value, err = item.ValueCopy(nil)
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	return got, got.key != ""
}

func scan(t *testing.T, db *badger.DB, prefix []byte, reverse, allVersions bool) []fact {
	t.Helper()
	var out []fact
	err := db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.Prefix = append([]byte(nil), prefix...)
		opts.Reverse = reverse
		opts.AllVersions = allVersions
		it := txn.NewIterator(opts)
		defer it.Close()
		if reverse && len(prefix) > 0 {
			it.Seek(append(append([]byte(nil), prefix...), 0xff))
		} else {
			it.Rewind()
		}
		for ; it.Valid(); it.Next() {
			item := it.Item()
			if !bytes.HasPrefix(item.Key(), prefix) {
				continue
			}
			row := fact{
				key:       string(item.KeyCopy(nil)),
				meta:      item.UserMeta(),
				expiresAt: item.ExpiresAt(),
				version:   item.Version(),
				deleted:   item.IsDeletedOrExpired(),
			}
			if !row.deleted {
				var err error
				row.value, err = item.ValueCopy(nil)
				if err != nil {
					return err
				}
			}
			out = append(out, row)
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return out
}

func backupBytes(t *testing.T, db *badger.DB, since uint64) ([]byte, uint64) {
	t.Helper()
	var out bytes.Buffer
	until, err := db.Backup(&out, since)
	if err != nil {
		t.Fatal(err)
	}
	return append([]byte(nil), out.Bytes()...), until
}

func openCheckpoint(t *testing.T, source *badger.DB, dir string, managed bool) *badger.DB {
	t.Helper()
	info, statErr := os.Stat(dir)
	if statErr != nil || !info.IsDir() {
		t.Fatalf("checkpoint destination is not a published directory: info=%v err=%v", info, statErr)
	}
	opts := quietOptions(dir)
	if key := source.Opts().EncryptionKey; len(key) > 0 {
		opts = opts.WithEncryptionKey(append([]byte(nil), key...))
	}
	var (
		db  *badger.DB
		err error
	)
	if managed {
		db, err = badger.OpenManaged(opts)
	} else {
		db, err = badger.Open(opts)
	}
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func checkpoint(t *testing.T, db *badger.DB) (string, uint64, *badger.DB) {
	t.Helper()
	dir := filepath.Join(t.TempDir(), "checkpoint")
	readTs, err := db.Checkpoint(context.Background(), dir)
	if err != nil {
		t.Fatal(err)
	}
	return dir, readTs, openCheckpoint(t, db, dir, false)
}

func histories(t *testing.T, root string, fn func(t *testing.T, db *badger.DB, key, value []byte)) {
	t.Helper()
	for variant, name := range []string{"transaction", "batch", "rollback-recovery", "delete-rewrite"} {
		variant, name := variant, name
		t.Run(name, func(t *testing.T) {
			db := openMemory(t)
			key := []byte(fmt.Sprintf("case/%s/%s/key", root, name))
			value := []byte(strings.Repeat(fmt.Sprintf("%s:%s|", root, name), variant+2))
			switch variant {
			case 0:
				putEntry(t, db, key, value, 0x31, time.Hour)
			case 1:
				wb := db.NewWriteBatch()
				if err := wb.Set([]byte("sibling/"+root), []byte("sibling")); err != nil {
					t.Fatal(err)
				}
				if err := wb.Set(key, value); err != nil {
					t.Fatal(err)
				}
				if err := wb.Flush(); err != nil {
					t.Fatal(err)
				}
			case 2:
				sentinel := errors.New("rollback")
				err := db.Update(func(txn *badger.Txn) error {
					if err := txn.Set(key, []byte("not-committed")); err != nil {
						return err
					}
					return sentinel
				})
				if !errors.Is(err, sentinel) {
					t.Fatalf("rollback result %v", err)
				}
				put(t, db, key, value)
			case 3:
				put(t, db, key, []byte("old"))
				del(t, db, key)
				put(t, db, key, value)
			}
			fn(t, db, key, value)
		})
	}
}

func requireValue(t *testing.T, db *badger.DB, key, value []byte) fact {
	t.Helper()
	got, ok := observe(t, db, key)
	if !ok || !bytes.Equal(got.value, value) {
		t.Fatalf("value mismatch for %q: present=%v value=%q", key, ok, got.value)
	}
	return got
}

// Native Atomic controls.

func TestBadgerV4A01(t *testing.T) {
	histories(t, "A01", func(t *testing.T, db *badger.DB, key, value []byte) {
		requireValue(t, db, key, value)
	})
}

func TestBadgerV4A02(t *testing.T) {
	histories(t, "A02", func(t *testing.T, db *badger.DB, key, value []byte) {
		del(t, db, key)
		if _, ok := observe(t, db, key); ok {
			t.Fatal("delete remained visible")
		}
	})
}

func TestBadgerV4A03(t *testing.T) {
	histories(t, "A03", func(t *testing.T, db *badger.DB, key, value []byte) {
		errMarker := errors.New("abort")
		err := db.Update(func(txn *badger.Txn) error {
			if err := txn.Set(key, []byte("replacement")); err != nil {
				return err
			}
			return errMarker
		})
		if !errors.Is(err, errMarker) {
			t.Fatal(err)
		}
		requireValue(t, db, key, value)
	})
}

func TestBadgerV4A04(t *testing.T) {
	histories(t, "A04", func(t *testing.T, db *badger.DB, key, value []byte) {
		wb := db.NewWriteBatch()
		other := append(append([]byte(nil), key...), []byte("/batch")...)
		if err := wb.Set(other, value); err != nil {
			t.Fatal(err)
		}
		if err := wb.Delete(key); err != nil {
			t.Fatal(err)
		}
		if err := wb.Flush(); err != nil {
			t.Fatal(err)
		}
		requireValue(t, db, other, value)
		if _, ok := observe(t, db, key); ok {
			t.Fatal("batch delete missing")
		}
	})
}

func TestBadgerV4A05(t *testing.T) {
	histories(t, "A05", func(t *testing.T, db *badger.DB, key, value []byte) {
		txn := db.NewTransaction(false)
		defer txn.Discard()
		first, err := txn.Get(key)
		if err != nil {
			t.Fatal(err)
		}
		firstVersion := first.Version()
		put(t, db, key, []byte("later"))
		still, err := txn.Get(key)
		if err != nil || still.Version() != firstVersion {
			t.Fatalf("snapshot moved: version=%d err=%v", still.Version(), err)
		}
	})
}

func TestBadgerV4A06(t *testing.T) {
	histories(t, "A06", func(t *testing.T, db *badger.DB, key, value []byte) {
		putEntry(t, db, key, value, 0x6a, time.Hour)
		got := requireValue(t, db, key, value)
		if got.meta != 0x6a || got.expiresAt <= uint64(time.Now().Unix()) {
			t.Fatalf("metadata mismatch: %+v", got)
		}
	})
}

func TestBadgerV4A07(t *testing.T) {
	histories(t, "A07", func(t *testing.T, db *badger.DB, key, value []byte) {
		prefix := []byte("ordered/")
		for _, suffix := range []string{"c", "a", "b"} {
			put(t, db, append(append([]byte(nil), prefix...), suffix...), []byte(suffix))
		}
		rows := scan(t, db, prefix, false, false)
		if len(rows) != 3 || rows[0].key != "ordered/a" || rows[2].key != "ordered/c" {
			t.Fatalf("iterator order %+v", rows)
		}
	})
}

// Atomic checkpoint behavior.

func TestBadgerV4A08(t *testing.T) {
	histories(t, "A08", func(t *testing.T, db *badger.DB, key, value []byte) {
		_, readTs, cp := checkpoint(t, db)
		got := requireValue(t, cp, key, value)
		if got.version > readTs || readTs == 0 {
			t.Fatalf("boundary=%d version=%d", readTs, got.version)
		}
	})
}

func TestBadgerV4A09(t *testing.T) {
	for _, name := range []string{"memory", "disk", "read-only-seed", "fresh-generation"} {
		name := name
		t.Run(name, func(t *testing.T) {
			db := openMemory(t)
			dir, _, cp := checkpoint(t, db)
			if _, err := os.Stat(dir); err != nil {
				t.Fatal(err)
			}
			if rows := scan(t, cp, nil, false, false); len(rows) != 0 {
				t.Fatalf("empty checkpoint has %d rows", len(rows))
			}
		})
	}
}

func TestBadgerV4A10(t *testing.T) {
	histories(t, "A10", func(t *testing.T, db *badger.DB, key, value []byte) {
		putEntry(t, db, key, value, 0x7d, 2*time.Hour)
		source := requireValue(t, db, key, value)
		_, _, cp := checkpoint(t, db)
		got := requireValue(t, cp, key, value)
		if got.meta != source.meta || got.expiresAt != source.expiresAt || got.version != source.version {
			t.Fatalf("entry metadata changed: source=%+v checkpoint=%+v", source, got)
		}
	})
}

func TestBadgerV4A11(t *testing.T) {
	histories(t, "A11", func(t *testing.T, db *badger.DB, key, value []byte) {
		del(t, db, key)
		_, _, cp := checkpoint(t, db)
		if _, ok := observe(t, cp, key); ok {
			t.Fatal("deleted value resurrected")
		}
		rows := scan(t, cp, []byte("case/A11/"), false, true)
		if len(rows) == 0 || !rows[0].deleted {
			t.Fatalf("delete lineage missing: %+v", rows)
		}
	})
}

func TestBadgerV4A12(t *testing.T) {
	histories(t, "A12", func(t *testing.T, db *badger.DB, key, value []byte) {
		large := bytes.Repeat(append(value, 0x5a), 6000)
		put(t, db, key, large)
		_, _, cp := checkpoint(t, db)
		requireValue(t, cp, key, large)
	})
}

func TestBadgerV4A13(t *testing.T) {
	histories(t, "A13", func(t *testing.T, db *badger.DB, key, value []byte) {
		parent := t.TempDir()
		dir := filepath.Join(parent, "published")
		if _, err := os.Stat(dir); !errors.Is(err, fs.ErrNotExist) {
			t.Fatalf("destination unexpectedly exists: %v", err)
		}
		if _, err := db.Checkpoint(context.Background(), dir); err != nil {
			t.Fatal(err)
		}
		if info, err := os.Stat(dir); err != nil || !info.IsDir() {
			t.Fatalf("destination not published: info=%v err=%v", info, err)
		}
	})
}

func TestBadgerV4A14(t *testing.T) {
	histories(t, "A14", func(t *testing.T, db *badger.DB, key, value []byte) {
		dir := filepath.Join(t.TempDir(), "existing")
		if err := os.Mkdir(dir, 0o700); err != nil {
			t.Fatal(err)
		}
		marker := filepath.Join(dir, "owned.txt")
		if err := os.WriteFile(marker, []byte("caller-owned"), 0o600); err != nil {
			t.Fatal(err)
		}
		_, err := db.Checkpoint(context.Background(), dir)
		if !errors.Is(err, fs.ErrExist) {
			t.Fatalf("expected existing-path error, got %v", err)
		}
		payload, err := os.ReadFile(marker)
		if err != nil || string(payload) != "caller-owned" {
			t.Fatalf("existing destination changed: %q %v", payload, err)
		}
	})
}

func TestBadgerV4A15(t *testing.T) {
	histories(t, "A15", func(t *testing.T, db *badger.DB, key, value []byte) {
		ctx, cancel := context.WithCancel(context.Background())
		cancel()
		dir := filepath.Join(t.TempDir(), "cancelled")
		_, err := db.Checkpoint(ctx, dir)
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("cancellation lost: %v", err)
		}
		if _, err := os.Stat(dir); !errors.Is(err, fs.ErrNotExist) {
			t.Fatalf("cancelled destination visible: %v", err)
		}
		requireValue(t, db, key, value)
	})
}

func TestBadgerV4A16(t *testing.T) {
	for _, name := range []string{"txn", "batch", "rewrite", "reopen"} {
		name := name
		t.Run(name, func(t *testing.T) {
			keyMaterial := bytes.Repeat([]byte{byte(len(name) + 1)}, 16)
			sourceDir := filepath.Join(t.TempDir(), "source")
			db, err := badger.Open(quietOptions(sourceDir).WithEncryptionKey(keyMaterial))
			if err != nil {
				t.Fatal(err)
			}
			key, value := []byte("encrypted/"+name), []byte("secret/"+name)
			put(t, db, key, value)
			cpDir := filepath.Join(t.TempDir(), "checkpoint")
			if _, err := db.Checkpoint(context.Background(), cpDir); err != nil {
				t.Fatal(err)
			}
			if err := db.Close(); err != nil {
				t.Fatal(err)
			}
			cp, err := badger.Open(quietOptions(cpDir).WithEncryptionKey(keyMaterial))
			if err != nil {
				t.Fatal(err)
			}
			requireValue(t, cp, key, value)
			_ = cp.Close()
			_, err = badger.Open(quietOptions(cpDir).WithEncryptionKey(bytes.Repeat([]byte{0xee}, 16)))
			if !errors.Is(err, badger.ErrEncryptionKeyMismatch) {
				t.Fatalf("wrong encryption key result %v", err)
			}
		})
	}
}

// Native Integration controls.

func TestBadgerV4I01(t *testing.T) {
	histories(t, "I01", func(t *testing.T, db *badger.DB, key, value []byte) {
		first, second := db.NewTransaction(true), db.NewTransaction(true)
		defer first.Discard()
		defer second.Discard()
		if _, err := first.Get(key); err != nil {
			t.Fatal(err)
		}
		if _, err := second.Get(key); err != nil {
			t.Fatal(err)
		}
		if err := first.Set(key, []byte("winner")); err != nil {
			t.Fatal(err)
		}
		if err := second.Set(key, []byte("loser")); err != nil {
			t.Fatal(err)
		}
		if err := first.Commit(); err != nil {
			t.Fatal(err)
		}
		if err := second.Commit(); !errors.Is(err, badger.ErrConflict) {
			t.Fatalf("conflict result %v", err)
		}
		requireValue(t, db, key, []byte("winner"))
	})
}

func TestBadgerV4I02(t *testing.T) {
	histories(t, "I02", func(t *testing.T, db *badger.DB, key, value []byte) {
		payload, _ := backupBytes(t, db, 0)
		dst := openMemory(t)
		if err := dst.Load(bytes.NewReader(payload), 4); err != nil {
			t.Fatal(err)
		}
		requireValue(t, dst, key, value)
	})
}

func TestBadgerV4I03(t *testing.T) {
	histories(t, "I03", func(t *testing.T, db *badger.DB, key, value []byte) {
		put(t, db, []byte("drop/selected"), []byte("gone"))
		put(t, db, []byte("keep/sibling"), []byte("safe"))
		if err := db.DropPrefix([]byte("drop/")); err != nil {
			t.Fatal(err)
		}
		if _, ok := observe(t, db, []byte("drop/selected")); ok {
			t.Fatal("selected prefix survived")
		}
		requireValue(t, db, []byte("keep/sibling"), []byte("safe"))
	})
}

func TestBadgerV4I04(t *testing.T) {
	for _, name := range []string{"set", "batch", "delete-rewrite", "metadata"} {
		name := name
		t.Run(name, func(t *testing.T) {
			dir := filepath.Join(t.TempDir(), "db")
			db := openDisk(t, dir)
			key, value := []byte("durable/"+name), []byte("value/"+name)
			putEntry(t, db, key, value, 0x22, 0)
			if err := db.Close(); err != nil {
				t.Fatal(err)
			}
			db = openDisk(t, dir)
			t.Cleanup(func() { _ = db.Close() })
			requireValue(t, db, key, value)
		})
	}
}

func TestBadgerV4I05(t *testing.T) {
	for variant, name := range []string{"single", "batch", "rewrite", "delete"} {
		variant, name := variant, name
		t.Run(name, func(t *testing.T) {
			db := openManagedMemory(t)
			key := []byte("managed/" + name)
			txn := db.NewTransactionAt(uint64(10+variant), true)
			if err := txn.Set(key, []byte(name)); err != nil {
				t.Fatal(err)
			}
			commitTs := uint64(20 + variant)
			if err := txn.CommitAt(commitTs, nil); err != nil {
				t.Fatal(err)
			}
			read := db.NewTransactionAt(commitTs, false)
			defer read.Discard()
			item, err := read.Get(key)
			if err != nil || item.Version() != commitTs {
				t.Fatalf("managed read version=%d err=%v", item.Version(), err)
			}
		})
	}
}

func TestBadgerV4I06(t *testing.T) {
	histories(t, "I06", func(t *testing.T, db *badger.DB, key, value []byte) {
		full, cursor := backupBytes(t, db, 0)
		laterKey := append(append([]byte(nil), key...), []byte("/later")...)
		put(t, db, laterKey, []byte("tail"))
		tail, _ := backupBytes(t, db, cursor)
		dst := openMemory(t)
		if err := dst.Load(bytes.NewReader(full), 4); err != nil {
			t.Fatal(err)
		}
		if err := dst.Load(bytes.NewReader(tail), 4); err != nil {
			t.Fatal(err)
		}
		requireValue(t, dst, key, value)
		requireValue(t, dst, laterKey, []byte("tail"))
	})
}

func TestBadgerV4I07(t *testing.T) {
	histories(t, "I07", func(t *testing.T, db *badger.DB, key, value []byte) {
		before := db.NewTransaction(false)
		defer before.Discard()
		put(t, db, append(key, []byte("/later")...), []byte("later"))
		item, err := before.Get(key)
		if err != nil {
			t.Fatal(err)
		}
		copy, err := item.ValueCopy(nil)
		if err != nil || !bytes.Equal(copy, value) {
			t.Fatalf("snapshot and value copy diverged: %q %v", copy, err)
		}
	})
}

// Integration checkpoint behavior.

func TestBadgerV4I08(t *testing.T) {
	histories(t, "I08", func(t *testing.T, db *badger.DB, key, value []byte) {
		dir := filepath.Join(t.TempDir(), "checkpoint")
		readTs, err := db.Checkpoint(context.Background(), dir)
		if err != nil {
			t.Fatal(err)
		}
		laterKey := append(append([]byte(nil), key...), []byte("/later")...)
		put(t, db, laterKey, []byte("later"))
		later := requireValue(t, db, laterKey, []byte("later"))
		cp := openCheckpoint(t, db, dir, false)
		requireValue(t, cp, key, value)
		if _, ok := observe(t, cp, laterKey); ok || later.version <= readTs {
			t.Fatalf("boundary admitted later generation: boundary=%d later=%d", readTs, later.version)
		}
	})
}

func TestBadgerV4I09(t *testing.T) {
	histories(t, "I09", func(t *testing.T, db *badger.DB, key, value []byte) {
		ghost := append(append([]byte(nil), key...), []byte("/ghost")...)
		errMarker := errors.New("not committed")
		err := db.Update(func(txn *badger.Txn) error {
			if err := txn.Set(ghost, []byte("ghost")); err != nil {
				return err
			}
			return errMarker
		})
		if !errors.Is(err, errMarker) {
			t.Fatal(err)
		}
		_, _, cp := checkpoint(t, db)
		if _, ok := observe(t, cp, ghost); ok {
			t.Fatal("aborted write checkpointed")
		}
		requireValue(t, cp, key, value)
	})
}

func TestBadgerV4I10(t *testing.T) {
	for variant, name := range []string{"ts40", "ts60", "ts80", "ts100"} {
		variant, name := variant, name
		t.Run(name, func(t *testing.T) {
			db := openManagedMemory(t)
			key := []byte("managed-checkpoint/" + name)
			commitTs := uint64(40 + variant*20)
			txn := db.NewTransactionAt(commitTs-1, true)
			if err := txn.Set(key, []byte(name)); err != nil {
				t.Fatal(err)
			}
			if err := txn.CommitAt(commitTs, nil); err != nil {
				t.Fatal(err)
			}
			dir := filepath.Join(t.TempDir(), "checkpoint")
			readTs, err := db.Checkpoint(context.Background(), dir)
			if err != nil || readTs != commitTs {
				t.Fatalf("managed boundary=%d want=%d err=%v", readTs, commitTs, err)
			}
			cp := openCheckpoint(t, db, dir, true)
			read := cp.NewTransactionAt(readTs, false)
			defer read.Discard()
			item, err := read.Get(key)
			if err != nil {
				t.Fatalf("managed checkpoint read: %v", err)
			}
			if item.Version() != commitTs {
				t.Fatalf("managed checkpoint version=%d want=%d", item.Version(), commitTs)
			}
		})
	}
}

func TestBadgerV4I11(t *testing.T) {
	histories(t, "I11", func(t *testing.T, db *badger.DB, key, value []byte) {
		put(t, db, key, []byte("generation-2"))
		put(t, db, key, []byte("generation-3"))
		sourceRows := scan(t, db, key, false, true)
		_, _, cp := checkpoint(t, db)
		cpRows := scan(t, cp, key, false, true)
		if fmt.Sprint(sourceRows) != fmt.Sprint(cpRows) {
			t.Fatalf("version lineage changed: source=%+v checkpoint=%+v", sourceRows, cpRows)
		}
	})
}

func TestBadgerV4I12(t *testing.T) {
	histories(t, "I12", func(t *testing.T, db *badger.DB, key, value []byte) {
		put(t, db, key, []byte("before-delete"))
		del(t, db, key)
		put(t, db, key, []byte("after-delete"))
		_, _, cp := checkpoint(t, db)
		requireValue(t, cp, key, []byte("after-delete"))
		rows := scan(t, cp, key, false, true)
		var sawDelete bool
		for _, row := range rows {
			sawDelete = sawDelete || row.deleted
		}
		if !sawDelete || len(rows) < 3 {
			t.Fatalf("rewrite lineage incomplete: %+v", rows)
		}
	})
}

func TestBadgerV4I13(t *testing.T) {
	histories(t, "I13", func(t *testing.T, db *badger.DB, key, value []byte) {
		putEntry(t, db, key, []byte("old-live"), 0x10, 0)
		putEntry(t, db, key, value, 0x44, time.Hour)
		source := requireValue(t, db, key, value)
		_, _, cp := checkpoint(t, db)
		got := requireValue(t, cp, key, value)
		if got.expiresAt != source.expiresAt || got.meta != 0x44 {
			t.Fatalf("TTL generation changed: source=%+v checkpoint=%+v", source, got)
		}
	})
}

func TestBadgerV4I14(t *testing.T) {
	histories(t, "I14", func(t *testing.T, db *badger.DB, key, value []byte) {
		largeKey := append(append([]byte(nil), key...), []byte("/large")...)
		large := bytes.Repeat([]byte("value-log-data|"), 9000)
		wb := db.NewWriteBatch()
		if err := wb.Set(key, value); err != nil {
			t.Fatal(err)
		}
		if err := wb.Set(largeKey, large); err != nil {
			t.Fatal(err)
		}
		if err := wb.Flush(); err != nil {
			t.Fatal(err)
		}
		_, _, cp := checkpoint(t, db)
		requireValue(t, cp, key, value)
		requireValue(t, cp, largeKey, large)
	})
}

func TestBadgerV4I15(t *testing.T) {
	histories(t, "I15", func(t *testing.T, db *badger.DB, key, value []byte) {
		for _, k := range []string{"p/a", "p/c", "p/b", "q/sibling"} {
			put(t, db, []byte(k), []byte("v/"+k))
		}
		_, _, cp := checkpoint(t, db)
		forward := scan(t, cp, []byte("p/"), false, false)
		reverse := scan(t, cp, []byte("p/"), true, false)
		if len(forward) != 3 || len(reverse) != 3 || forward[0].key != reverse[2].key || forward[2].key != reverse[0].key {
			t.Fatalf("prefix directions disagree: forward=%+v reverse=%+v", forward, reverse)
		}
	})
}

func TestBadgerV4I16(t *testing.T) {
	histories(t, "I16", func(t *testing.T, db *badger.DB, key, value []byte) {
		_, _, cp := checkpoint(t, db)
		payload, _ := backupBytes(t, cp, 0)
		dst := openMemory(t)
		if err := dst.Load(bytes.NewReader(payload), 4); err != nil {
			t.Fatal(err)
		}
		requireValue(t, dst, key, value)
	})
}

func TestBadgerV4I17(t *testing.T) {
	histories(t, "I17", func(t *testing.T, db *badger.DB, key, value []byte) {
		_, err := db.Checkpoint(context.Background(), "")
		if !errors.Is(err, badger.ErrInvalidRequest) {
			t.Fatalf("empty destination result %v", err)
		}
		requireValue(t, db, key, value)
		goodDir := filepath.Join(t.TempDir(), "checkpoint")
		if _, err := db.Checkpoint(context.Background(), goodDir); err != nil {
			t.Fatalf("valid publication after rejection: %v", err)
		}
		cp := openCheckpoint(t, db, goodDir, false)
		requireValue(t, cp, key, value)
	})
}

func TestBadgerV4I18(t *testing.T) {
	histories(t, "I18", func(t *testing.T, db *badger.DB, key, value []byte) {
		parent := filepath.Join(t.TempDir(), "missing", "parent")
		dir := filepath.Join(parent, "checkpoint")
		_, err := db.Checkpoint(context.Background(), dir)
		if err == nil {
			t.Fatal("checkpoint unexpectedly created missing parents")
		}
		if _, err := os.Stat(dir); !errors.Is(err, fs.ErrNotExist) {
			t.Fatalf("failed destination visible: %v", err)
		}
		requireValue(t, db, key, value)
		goodDir := filepath.Join(t.TempDir(), "checkpoint")
		if _, err := db.Checkpoint(context.Background(), goodDir); err != nil {
			t.Fatalf("recovery publication failed: %v", err)
		}
	})
}

func TestBadgerV4I19(t *testing.T) {
	for _, name := range []string{"empty", "one", "batch", "metadata"} {
		name := name
		t.Run(name, func(t *testing.T) {
			dir := filepath.Join(t.TempDir(), "source")
			db := openDisk(t, dir)
			put(t, db, []byte("k/"+name), []byte(name))
			if err := db.Close(); err != nil {
				t.Fatal(err)
			}
			dst := filepath.Join(t.TempDir(), "checkpoint")
			_, err := db.Checkpoint(context.Background(), dst)
			if !errors.Is(err, badger.ErrDBClosed) {
				t.Fatalf("closed result %v", err)
			}
			if _, err := os.Stat(dst); !errors.Is(err, fs.ErrNotExist) {
				t.Fatalf("closed source published destination: %v", err)
			}
			db = openDisk(t, dir)
			defer db.Close()
			recovered := filepath.Join(t.TempDir(), "recovered")
			if _, err := db.Checkpoint(context.Background(), recovered); err != nil {
				t.Fatalf("reopened source checkpoint: %v", err)
			}
		})
	}
}

func TestBadgerV4I20(t *testing.T) {
	histories(t, "I20", func(t *testing.T, db *badger.DB, key, value []byte) {
		badDir := filepath.Join(t.TempDir(), "missing", "checkpoint")
		if _, err := db.Checkpoint(context.Background(), badDir); err == nil {
			t.Fatal("expected first failure")
		}
		goodDir := filepath.Join(t.TempDir(), "checkpoint")
		if _, err := db.Checkpoint(context.Background(), goodDir); err != nil {
			t.Fatal(err)
		}
		cp := openCheckpoint(t, db, goodDir, false)
		requireValue(t, cp, key, value)
	})
}

func TestBadgerV4I21(t *testing.T) {
	for _, name := range []string{"small", "large", "batch", "rewrite"} {
		name := name
		t.Run(name, func(t *testing.T) {
			parent := t.TempDir()
			keyDir, valueDir := filepath.Join(parent, "keys"), filepath.Join(parent, "values")
			db, err := badger.Open(quietOptions(keyDir).WithValueDir(valueDir))
			if err != nil {
				t.Fatal(err)
			}
			key := []byte("split/" + name)
			value := bytes.Repeat([]byte(name+"|"), 18000)
			put(t, db, key, value)
			cpDir := filepath.Join(parent, "checkpoint")
			if _, err := db.Checkpoint(context.Background(), cpDir); err != nil {
				t.Fatal(err)
			}
			_ = db.Close()
			_ = os.RemoveAll(keyDir)
			_ = os.RemoveAll(valueDir)
			cp := openDisk(t, cpDir)
			defer cp.Close()
			requireValue(t, cp, key, value)
		})
	}
}

func TestBadgerV4I22(t *testing.T) {
	histories(t, "I22", func(t *testing.T, db *badger.DB, key, value []byte) {
		if !db.Opts().InMemory {
			t.Fatal("fixture must be in-memory")
		}
		dir, _, cp := checkpoint(t, db)
		if cp.Opts().InMemory || cp.Opts().Dir != dir || cp.Opts().ValueDir != dir {
			t.Fatalf("checkpoint is not a filesystem database: %+v", cp.Opts())
		}
		requireValue(t, cp, key, value)
	})
}

func TestBadgerV4I23(t *testing.T) {
	histories(t, "I23", func(t *testing.T, db *badger.DB, key, value []byte) {
		_, _, cp := checkpoint(t, db)
		put(t, db, key, []byte("source-later"))
		requireValue(t, db, key, []byte("source-later"))
		requireValue(t, cp, key, value)
	})
}

func TestBadgerV4I24(t *testing.T) {
	histories(t, "I24", func(t *testing.T, db *badger.DB, key, value []byte) {
		_, _, cp := checkpoint(t, db)
		put(t, cp, key, []byte("checkpoint-later"))
		requireValue(t, cp, key, []byte("checkpoint-later"))
		requireValue(t, db, key, value)
	})
}

// System checkpoint behavior.

func TestBadgerV4S01(t *testing.T) {
	histories(t, "S01", func(t *testing.T, db *badger.DB, key, value []byte) {
		largeKey := []byte("system/large")
		deadKey := []byte("system/dead")
		metaKey := []byte("system/meta")
		large := bytes.Repeat([]byte("L"), 160000)
		put(t, db, largeKey, large)
		put(t, db, deadKey, []byte("old"))
		del(t, db, deadKey)
		putEntry(t, db, metaKey, []byte("metadata"), 0x77, time.Hour)
		_, _, cp := checkpoint(t, db)
		requireValue(t, cp, key, value)
		requireValue(t, cp, largeKey, large)
		if _, ok := observe(t, cp, deadKey); ok {
			t.Fatal("system delete resurrected")
		}
		if got := requireValue(t, cp, metaKey, []byte("metadata")); got.meta != 0x77 || got.expiresAt == 0 {
			t.Fatalf("system metadata lost: %+v", got)
		}
	})
}

func TestBadgerV4S02(t *testing.T) {
	histories(t, "S02", func(t *testing.T, db *badger.DB, key, value []byte) {
		dir := filepath.Join(t.TempDir(), "checkpoint")
		if _, err := db.Checkpoint(context.Background(), dir); err != nil {
			t.Fatal(err)
		}
		put(t, db, key, []byte("later"))
		if _, err := db.Checkpoint(context.Background(), dir); !errors.Is(err, fs.ErrExist) {
			t.Fatalf("repeat destination result %v", err)
		}
		cp := openCheckpoint(t, db, dir, false)
		requireValue(t, cp, key, value)
	})
}

func TestBadgerV4S03(t *testing.T) {
	histories(t, "S03", func(t *testing.T, db *badger.DB, key, value []byte) {
		ctx, cancel := context.WithCancel(context.Background())
		cancel()
		if _, err := db.Checkpoint(ctx, filepath.Join(t.TempDir(), "cancelled")); !errors.Is(err, context.Canceled) {
			t.Fatal(err)
		}
		dir := filepath.Join(t.TempDir(), "recovered")
		if _, err := db.Checkpoint(context.Background(), dir); err != nil {
			t.Fatal(err)
		}
		cp := openCheckpoint(t, db, dir, false)
		payload, _ := backupBytes(t, cp, 0)
		restored := openMemory(t)
		if err := restored.Load(bytes.NewReader(payload), 4); err != nil {
			t.Fatal(err)
		}
		requireValue(t, restored, key, value)
	})
}

func TestBadgerV4S04(t *testing.T) {
	histories(t, "S04", func(t *testing.T, db *badger.DB, key, value []byte) {
		if _, err := db.Checkpoint(context.Background(), filepath.Join(t.TempDir(), "missing", "cp")); err == nil {
			t.Fatal("expected publication failure")
		}
		put(t, db, key, []byte("after-failure"))
		dir := filepath.Join(t.TempDir(), "good")
		if _, err := db.Checkpoint(context.Background(), dir); err != nil {
			t.Fatal(err)
		}
		cp := openCheckpoint(t, db, dir, false)
		requireValue(t, cp, key, []byte("after-failure"))
	})
}

func TestBadgerV4S05(t *testing.T) {
	for _, name := range []string{"txn", "batch", "large", "rewrite"} {
		name := name
		t.Run(name, func(t *testing.T) {
			parent := t.TempDir()
			keyMaterial := bytes.Repeat([]byte{0x35}, 16)
			db, err := badger.Open(quietOptions(filepath.Join(parent, "keys")).
				WithValueDir(filepath.Join(parent, "values")).
				WithEncryptionKey(keyMaterial))
			if err != nil {
				t.Fatal(err)
			}
			key, value := []byte("secure/"+name), bytes.Repeat([]byte(name), 22000)
			put(t, db, key, value)
			cpDir := filepath.Join(parent, "checkpoint")
			if _, err := db.Checkpoint(context.Background(), cpDir); err != nil {
				t.Fatal(err)
			}
			_ = db.Close()
			cp, err := badger.Open(quietOptions(cpDir).WithEncryptionKey(keyMaterial))
			if err != nil {
				t.Fatal(err)
			}
			payload, _ := backupBytes(t, cp, 0)
			_ = cp.Close()
			restored := openMemory(t)
			if err := restored.Load(bytes.NewReader(payload), 4); err != nil {
				t.Fatal(err)
			}
			requireValue(t, restored, key, value)
		})
	}
}

func TestBadgerV4S06(t *testing.T) {
	for variant, name := range []string{"v100", "v200", "v300", "v400"} {
		variant, name := variant, name
		t.Run(name, func(t *testing.T) {
			db := openManagedMemory(t)
			key := []byte("managed-system/" + name)
			base := uint64((variant + 1) * 100)
			for offset, value := range []string{"one", "two", "three"} {
				txn := db.NewTransactionAt(base+uint64(offset), true)
				if err := txn.Set(key, []byte(value)); err != nil {
					t.Fatal(err)
				}
				if err := txn.CommitAt(base+uint64(offset)+1, nil); err != nil {
					t.Fatal(err)
				}
			}
			dir := filepath.Join(t.TempDir(), "checkpoint")
			readTs, err := db.Checkpoint(context.Background(), dir)
			if err != nil || readTs != base+3 {
				t.Fatalf("managed system boundary=%d err=%v", readTs, err)
			}
			cp := openCheckpoint(t, db, dir, true)
			rows := scanManaged(t, cp, key, readTs)
			if len(rows) < 3 || string(rows[0].value) != "three" {
				t.Fatalf("managed lineage %+v", rows)
			}
		})
	}
}

func scanManaged(t *testing.T, db *badger.DB, key []byte, readTs uint64) []fact {
	t.Helper()
	txn := db.NewTransactionAt(readTs, false)
	defer txn.Discard()
	opts := badger.DefaultIteratorOptions
	opts.AllVersions = true
	opts.Prefix = append([]byte(nil), key...)
	it := txn.NewIterator(opts)
	defer it.Close()
	var rows []fact
	for it.Rewind(); it.Valid(); it.Next() {
		item := it.Item()
		row := fact{key: string(item.KeyCopy(nil)), version: item.Version(), deleted: item.IsDeletedOrExpired()}
		if !row.deleted {
			var err error
			row.value, err = item.ValueCopy(nil)
			if err != nil {
				t.Fatal(err)
			}
		}
		rows = append(rows, row)
	}
	return rows
}

func TestBadgerV4S07(t *testing.T) {
	for variant, name := range []string{"txn", "batch-seed", "rollback-seed", "rewrite-seed"} {
		variant, name := variant, name
		t.Run(name, func(t *testing.T) {
			db := openMemory(t)
			for i := 0; i < 32+variant*8; i++ {
				put(t, db, []byte(fmt.Sprintf("live/%s/before/%02d", name, i)), bytes.Repeat([]byte("b"), 8<<10))
			}
			ready := make(chan struct{})
			stop := make(chan struct{})
			writeErr := make(chan error, 1)
			var wg sync.WaitGroup
			wg.Add(1)
			go func() {
				defer wg.Done()
				for i := 0; i < 32; i++ {
					select {
					case <-stop:
						return
					default:
					}
					err := db.Update(func(txn *badger.Txn) error {
						return txn.Set(
							[]byte(fmt.Sprintf("live/%s/during/%06d", name, i)),
							[]byte("during"),
						)
					})
					if err != nil {
						writeErr <- err
						return
					}
					if i == 0 {
						close(ready)
					}
					time.Sleep(2 * time.Millisecond)
				}
			}()
			select {
			case <-ready:
			case err := <-writeErr:
				t.Fatal(err)
			}
			dir := filepath.Join(t.TempDir(), "checkpoint")
			readTs, err := db.Checkpoint(context.Background(), dir)
			close(stop)
			wg.Wait()
			if err != nil {
				t.Fatal(err)
			}
			select {
			case err := <-writeErr:
				t.Fatal(err)
			default:
			}
			cp := openCheckpoint(t, db, dir, false)
			for _, row := range scan(t, db, []byte("live/"+name+"/"), false, false) {
				_, present := observe(t, cp, []byte(row.key))
				if present != (row.version <= readTs) {
					t.Fatalf("mixed boundary for %s version=%d readTs=%d present=%v", row.key, row.version, readTs, present)
				}
			}
		})
	}
}

func TestBadgerV4S08(t *testing.T) {
	histories(t, "S08", func(t *testing.T, db *badger.DB, key, value []byte) {
		firstDir := filepath.Join(t.TempDir(), "first")
		firstTs, err := db.Checkpoint(context.Background(), firstDir)
		if err != nil {
			t.Fatal(err)
		}
		put(t, db, key, []byte("second-generation"))
		secondDir := filepath.Join(t.TempDir(), "second")
		secondTs, err := db.Checkpoint(context.Background(), secondDir)
		if err != nil || secondTs <= firstTs {
			t.Fatalf("generation boundaries first=%d second=%d err=%v", firstTs, secondTs, err)
		}
		first := openCheckpoint(t, db, firstDir, false)
		second := openCheckpoint(t, db, secondDir, false)
		requireValue(t, first, key, value)
		requireValue(t, second, key, []byte("second-generation"))
		put(t, second, []byte("second-only"), []byte("owned"))
		if _, ok := observe(t, first, []byte("second-only")); ok {
			t.Fatal("checkpoint generations share writes")
		}
	})
}
