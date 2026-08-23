package integration_test

import (
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"sync"
	"testing"
	"time"

	"github.com/spf13/afero"
)

func put(t *testing.T, fs afero.Fs, name, value string) {
	t.Helper()
	f, e := fs.OpenFile(name, os.O_CREATE|os.O_TRUNC|os.O_RDWR, 0o640)
	if e != nil {
		t.Fatal(e)
	}
	_, e = f.WriteString(value)
	if e != nil {
		t.Fatal(e)
	}
	if e = f.Close(); e != nil {
		t.Fatal(e)
	}
}
func get(t *testing.T, fs afero.Fs, name string) string {
	t.Helper()
	f, e := fs.Open(name)
	if e != nil {
		t.Fatal(e)
	}
	b, e := io.ReadAll(f)
	if e != nil {
		t.Fatal(e)
	}
	_ = f.Close()
	return string(b)
}
func names(t *testing.T, fs afero.Fs, path string) []string {
	t.Helper()
	f, e := fs.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	n, e := f.Readdirnames(-1)
	if e != nil {
		t.Fatal(e)
	}
	_ = f.Close()
	sort.Strings(n)
	return n
}

var integrationCases = []struct {
	name string
	run  func(*testing.T)
}{
	{"AFERO-036-cow-copyup-write-isolates-base", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "abcdef")
		u := afero.NewCopyOnWriteFs(afero.NewReadOnlyFs(b), l)
		f, e := u.OpenFile("x", os.O_RDWR, 0)
		if e != nil {
			t.Fatal(e)
		}
		_, _ = f.WriteAt([]byte("ZZ"), 2)
		_ = f.Close()
		if get(t, u, "x") != "abZZef" || get(t, b, "x") != "abcdef" || get(t, l, "x") != "abZZef" {
			t.Fatal("copy-up isolation")
		}
	}},
	{"AFERO-037-cow-truncate-isolates-base", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "abcdef")
		u := afero.NewCopyOnWriteFs(afero.NewReadOnlyFs(b), l)
		f, e := u.OpenFile("x", os.O_RDWR|os.O_TRUNC, 0)
		if e != nil {
			t.Fatal(e)
		}
		_ = f.Close()
		if get(t, b, "x") != "abcdef" || get(t, u, "x") != "" {
			t.Fatal("truncate")
		}
	}},
	{"AFERO-038-cow-chmod-copyup", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "v")
		u := afero.NewCopyOnWriteFs(afero.NewReadOnlyFs(b), l)
		if e := u.Chmod("x", 0o600); e != nil {
			t.Fatal(e)
		}
		bi, _ := b.Stat("x")
		li, _ := l.Stat("x")
		if bi.Mode().Perm() == li.Mode().Perm() || li.Mode().Perm() != 0o600 {
			t.Fatalf("%o %o", bi.Mode().Perm(), li.Mode().Perm())
		}
	}},
	{"AFERO-039-cow-chtime-copyup", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "v")
		u := afero.NewCopyOnWriteFs(afero.NewReadOnlyFs(b), l)
		old, _ := b.Stat("x")
		m := time.Unix(4567, 0)
		if e := u.Chtimes("x", m, m); e != nil {
			t.Fatal(e)
		}
		li, _ := l.Stat("x")
		bi, _ := b.Stat("x")
		if !li.ModTime().Equal(m) || !bi.ModTime().Equal(old.ModTime()) {
			t.Fatal("times")
		}
	}},
	{"AFERO-040-cow-base-rename-fails", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "v")
		u := afero.NewCopyOnWriteFs(b, l)
		if e := u.Rename("x", "y"); e == nil {
			t.Fatal("expected failure")
		}
		if get(t, b, "x") != "v" {
			t.Fatal("base changed")
		}
	}},
	{"AFERO-041-cow-base-remove-fails", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "v")
		u := afero.NewCopyOnWriteFs(b, l)
		if e := u.Remove("x"); e == nil {
			t.Fatal("expected failure")
		}
		if get(t, b, "x") != "v" {
			t.Fatal("base changed")
		}
	}},
	{"AFERO-042-cow-remove-reveals-base", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "base")
		put(t, l, "x", "layer")
		u := afero.NewCopyOnWriteFs(b, l)
		if get(t, u, "x") != "layer" {
			t.Fatal("precedence")
		}
		if e := u.Remove("x"); e != nil {
			t.Fatal(e)
		}
		if get(t, u, "x") != "base" {
			t.Fatal("reveal")
		}
	}},
	{"AFERO-043-cow-union-deduplicates", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		_ = b.Mkdir("d", 0o755)
		_ = l.Mkdir("d", 0o755)
		put(t, b, "d/a", "base")
		put(t, b, "d/b", "b")
		put(t, l, "d/a", "layer")
		put(t, l, "d/c", "c")
		u := afero.NewCopyOnWriteFs(b, l)
		if got := names(t, u, "d"); !reflect.DeepEqual(got, []string{"a", "b", "c"}) {
			t.Fatal(got)
		}
		if get(t, u, "d/a") != "layer" {
			t.Fatal("winner")
		}
	}},
	{"AFERO-044-cow-union-directory-cursor", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		_ = b.Mkdir("d", 0o755)
		_ = l.Mkdir("d", 0o755)
		put(t, b, "d/a", "a")
		put(t, l, "d/b", "b")
		u := afero.NewCopyOnWriteFs(b, l)
		f, _ := u.Open("d")
		one, e := f.Readdirnames(1)
		if e != nil || len(one) != 1 {
			t.Fatalf("%v %v", one, e)
		}
		two, e := f.Readdirnames(1)
		if e != nil || len(two) != 1 || one[0] == two[0] {
			t.Fatalf("%v %v", two, e)
		}
	}},
	{"AFERO-045-cow-mkdirall-existing-base", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		_ = b.MkdirAll("a/b", 0o755)
		u := afero.NewCopyOnWriteFs(b, l)
		if e := u.MkdirAll("a/b", 0o700); e != nil {
			t.Fatal(e)
		}
		if _, e := l.Stat("a/b"); !os.IsNotExist(e) {
			t.Fatal("unnecessary overlay")
		}
	}},
	{"AFERO-046-cow-create-under-base-dir", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		_ = b.MkdirAll("a/b", 0o755)
		u := afero.NewCopyOnWriteFs(b, l)
		put(t, u, "a/b/x", "v")
		if get(t, l, "a/b/x") != "v" {
			t.Fatal("parent copy")
		}
		if _, e := b.Stat("a/b/x"); !os.IsNotExist(e) {
			t.Fatal("base write")
		}
	}},
	{"AFERO-047-cow-overlay-shadows-base", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "base")
		put(t, l, "x", "layer")
		u := afero.NewCopyOnWriteFs(b, l)
		if get(t, u, "x") != "layer" {
			t.Fatal("shadow")
		}
	}},
	{"AFERO-048-cow-overlay-file-shadows-base-dir", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		_ = b.Mkdir("x", 0o755)
		put(t, b, "x/a", "a")
		put(t, l, "x", "file")
		u := afero.NewCopyOnWriteFs(b, l)
		if get(t, u, "x") != "file" {
			t.Fatal("shadow type")
		}
	}},
	{"AFERO-049-cow-missing-open", func(t *testing.T) {
		u := afero.NewCopyOnWriteFs(afero.NewMemMapFs(), afero.NewMemMapFs())
		if _, e := u.Open("missing"); !os.IsNotExist(e) {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-050-cache-zero-keeps-hit", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "one")
		u := afero.NewCacheOnReadFs(b, c, 0)
		if get(t, u, "x") != "one" {
			t.Fatal("first")
		}
		put(t, b, "x", "two")
		if get(t, u, "x") != "one" {
			t.Fatal("unlimited cache")
		}
	}},
	{"AFERO-051-cache-stale-refresh", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "one")
		old := time.Now().Add(-time.Hour)
		_ = b.Chtimes("x", old, old)
		u := afero.NewCacheOnReadFs(b, c, time.Second)
		if get(t, u, "x") != "one" {
			t.Fatal("first")
		}
		put(t, b, "x", "two")
		fresh := time.Now()
		_ = b.Chtimes("x", fresh, fresh)
		_ = c.Chtimes("x", old, old)
		if get(t, u, "x") != "two" {
			t.Fatal("refresh")
		}
	}},
	{"AFERO-052-cache-create-writes-both", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		u := afero.NewCacheOnReadFs(b, c, 0)
		f, e := u.Create("x")
		if e != nil {
			t.Fatal(e)
		}
		_, _ = f.WriteString("v")
		_ = f.Close()
		if get(t, b, "x") != "v" || get(t, u, "x") != "v" {
			t.Fatal("base-wrapper agreement")
		}
	}},
	{"AFERO-053-cache-openfile-writes-both", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "abc")
		u := afero.NewCacheOnReadFs(b, c, 0)
		f, e := u.OpenFile("x", os.O_RDWR, 0)
		if e != nil {
			t.Fatal(e)
		}
		_, _ = f.WriteAt([]byte("Z"), 1)
		_ = f.Close()
		if get(t, b, "x") != "aZc" || get(t, u, "x") != "aZc" {
			t.Fatal("base-wrapper agreement")
		}
	}},
	{"AFERO-054-cache-mkdirall-writes-both", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		u := afero.NewCacheOnReadFs(b, c, 0)
		if e := u.MkdirAll("a/b", 0o750); e != nil {
			t.Fatal(e)
		}
		for _, fs := range []afero.Fs{b, u} {
			fi, e := fs.Stat("a/b")
			if e != nil || !fi.IsDir() {
				t.Fatalf("%v %v", fi, e)
			}
		}
	}},
	{"AFERO-055-cache-remove-writes-both", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "v")
		put(t, c, "x", "v")
		u := afero.NewCacheOnReadFs(b, c, 0)
		if e := u.Remove("x"); e != nil {
			t.Fatal(e)
		}
		for _, fs := range []afero.Fs{b, c} {
			if _, e := fs.Stat("x"); !os.IsNotExist(e) {
				t.Fatal(e)
			}
		}
	}},
	{"AFERO-056-cache-rename-writes-both", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "v")
		put(t, c, "x", "v")
		u := afero.NewCacheOnReadFs(b, c, 0)
		if e := u.Rename("x", "y"); e != nil {
			t.Fatal(e)
		}
		if get(t, b, "y") != "v" || get(t, u, "y") != "v" {
			t.Fatal("base-wrapper rename agreement")
		}
	}},
	{"AFERO-057-cache-local-file", func(t *testing.T) {
		b, c := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, c, "x", "local")
		u := afero.NewCacheOnReadFs(b, c, time.Second)
		if get(t, u, "x") != "local" {
			t.Fatal("local")
		}
		if _, e := b.Stat("x"); !os.IsNotExist(e) {
			t.Fatal("created base")
		}
	}},
	{"AFERO-058-basepath-mutator-roundtrip", func(t *testing.T) {
		s := afero.NewMemMapFs()
		_ = s.Mkdir("root", 0o755)
		v := afero.NewBasePathFs(s, "root")
		_ = v.MkdirAll("a", 0o755)
		put(t, v, "a/x", "v")
		if e := v.Rename("a/x", "a/y"); e != nil {
			t.Fatal(e)
		}
		if e := v.Chmod("a/y", 0o600); e != nil {
			t.Fatal(e)
		}
		if get(t, s, "root/a/y") != "v" {
			t.Fatal("backing")
		}
		if e := v.Remove("a/y"); e != nil {
			t.Fatal(e)
		}
	}},
	{"AFERO-059-readonly-over-basepath", func(t *testing.T) {
		s := afero.NewMemMapFs()
		_ = s.Mkdir("root", 0o755)
		put(t, s, "root/x", "v")
		v := afero.NewReadOnlyFs(afero.NewBasePathFs(s, "root"))
		if get(t, v, "x") != "v" {
			t.Fatal("read")
		}
		if _, e := v.Create("y"); !os.IsPermission(e) {
			t.Fatal(e)
		}
	}},
	{"AFERO-060-cow-with-readonly-base", func(t *testing.T) {
		b, l := afero.NewMemMapFs(), afero.NewMemMapFs()
		put(t, b, "x", "base")
		u := afero.NewCopyOnWriteFs(afero.NewReadOnlyFs(b), l)
		f, e := u.OpenFile("x", os.O_RDWR, 0)
		if e != nil {
			t.Fatal(e)
		}
		_, _ = f.WriteAt([]byte("Z"), 0)
		_ = f.Close()
		if get(t, u, "x") != "Zase" || get(t, b, "x") != "base" {
			t.Fatal("composition")
		}
	}},
	{"AFERO-061-open-handle-survives-rename", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		put(t, fs, "x", "abc")
		f, _ := fs.Open("x")
		if e := fs.Rename("x", "y"); e != nil {
			t.Fatal(e)
		}
		buf := make([]byte, 3)
		_, e := f.Read(buf)
		if e != nil || string(buf) != "abc" {
			t.Fatalf("%q %v", buf, e)
		}
		if get(t, fs, "y") != "abc" {
			t.Fatal("new path")
		}
	}},
	{"AFERO-062-open-handle-survives-remove", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		put(t, fs, "x", "abc")
		f, _ := fs.Open("x")
		if e := fs.Remove("x"); e != nil {
			t.Fatal(e)
		}
		buf := make([]byte, 3)
		_, e := f.Read(buf)
		if e != nil || string(buf) != "abc" {
			t.Fatalf("%q %v", buf, e)
		}
		if _, e := fs.Open("x"); !os.IsNotExist(e) {
			t.Fatal(e)
		}
	}},
	{"AFERO-063-concurrent-distinct-paths", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		_ = fs.Mkdir("d", 0o755)
		var wg sync.WaitGroup
		for i := 0; i < 12; i++ {
			i := i
			wg.Add(1)
			go func() {
				defer wg.Done()
				name := filepath.Join("d", string(rune('a'+i)))
				f, e := fs.Create(name)
				if e == nil {
					_, _ = f.WriteString(name)
					_ = f.Close()
				}
			}()
		}
		wg.Wait()
		if got := names(t, fs, "d"); len(got) != 12 {
			t.Fatal(got)
		}
	}},
	{"AFERO-064-concurrent-independent-readers", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		put(t, fs, "x", "payload")
		var wg sync.WaitGroup
		errs := make(chan string, 16)
		for i := 0; i < 16; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				f, e := fs.Open("x")
				if e != nil {
					errs <- e.Error()
					return
				}
				b, e := io.ReadAll(f)
				_ = f.Close()
				if e != nil || string(b) != "payload" {
					errs <- string(b)
				}
			}()
		}
		wg.Wait()
		close(errs)
		for e := range errs {
			t.Fatal(e)
		}
	}},
	{"AFERO-065-interface-signatures", func(t *testing.T) {
		values := []afero.Fs{afero.NewMemMapFs(), afero.NewBasePathFs(afero.NewMemMapFs(), "."), afero.NewReadOnlyFs(afero.NewMemMapFs()), afero.NewCopyOnWriteFs(afero.NewMemMapFs(), afero.NewMemMapFs()), afero.NewCacheOnReadFs(afero.NewMemMapFs(), afero.NewMemMapFs(), 0)}
		want := []string{"MemMapFS", "BasePathFs", "ReadOnlyFilter", "CopyOnWriteFs", "CacheOnReadFs"}
		for i := range values {
			if values[i].Name() != want[i] {
				t.Fatalf("name[%d]=%q", i, values[i].Name())
			}
		}
	}},
}

// Depends-On: atomic::TestAFERO033
func TestAFERO036(t *testing.T) { integrationCases[0].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO037(t *testing.T) { integrationCases[1].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO038(t *testing.T) { integrationCases[2].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO039(t *testing.T) { integrationCases[3].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO040(t *testing.T) { integrationCases[4].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO041(t *testing.T) { integrationCases[5].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO042(t *testing.T) { integrationCases[6].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO043(t *testing.T) { integrationCases[7].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO044(t *testing.T) { integrationCases[8].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO045(t *testing.T) { integrationCases[9].run(t) }

// Depends-On: atomic::TestAFERO034
func TestAFERO046(t *testing.T) { integrationCases[10].run(t) }

// Depends-On: atomic::TestAFERO034
func TestAFERO047(t *testing.T) { integrationCases[11].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO048(t *testing.T) { integrationCases[12].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO049(t *testing.T) { integrationCases[13].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO050(t *testing.T) { integrationCases[14].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO051(t *testing.T) { integrationCases[15].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO052(t *testing.T) { integrationCases[16].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO053(t *testing.T) { integrationCases[17].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO054(t *testing.T) { integrationCases[18].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO055(t *testing.T) { integrationCases[19].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO056(t *testing.T) { integrationCases[20].run(t) }

// Depends-On: atomic::TestAFERO035
func TestAFERO057(t *testing.T) { integrationCases[21].run(t) }

// Depends-On: atomic::TestAFERO030
func TestAFERO058(t *testing.T) { integrationCases[22].run(t) }

// Depends-On: atomic::TestAFERO024
func TestAFERO059(t *testing.T) { integrationCases[23].run(t) }

// Depends-On: atomic::TestAFERO033
func TestAFERO060(t *testing.T) { integrationCases[24].run(t) }

// Depends-On: atomic::TestAFERO018
func TestAFERO061(t *testing.T) { integrationCases[25].run(t) }

// Depends-On: atomic::TestAFERO015
func TestAFERO062(t *testing.T) { integrationCases[26].run(t) }

// Depends-On: atomic::TestAFERO005
func TestAFERO063(t *testing.T) { integrationCases[27].run(t) }

// Depends-On: atomic::TestAFERO020
func TestAFERO064(t *testing.T) { integrationCases[28].run(t) }

// Depends-On: atomic::TestAFERO001
func TestAFERO065(t *testing.T) { integrationCases[29].run(t) }
