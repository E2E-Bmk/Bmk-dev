package atomic_test

import (
	"io"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"testing"
	"time"

	"github.com/spf13/afero"
)

func write(t *testing.T, fs afero.Fs, name, value string) {
	t.Helper()
	f, err := fs.OpenFile(name, os.O_CREATE|os.O_TRUNC|os.O_RDWR, 0o640)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.WriteString(value); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
}

func read(t *testing.T, fs afero.Fs, name string) string {
	t.Helper()
	f, err := fs.Open(name)
	if err != nil {
		t.Fatal(err)
	}
	b, err := io.ReadAll(f)
	if err != nil {
		t.Fatal(err)
	}
	_ = f.Close()
	return string(b)
}

var atomicCases = []struct {
	name string
	run  func(*testing.T)
}{
	{"AFERO-001-constructor-and-name", func(t *testing.T) {
		if afero.NewMemMapFs().Name() != "MemMapFS" {
			t.Fatal("name")
		}
	}},
	{"AFERO-002-root-directory", func(t *testing.T) {
		fi, err := afero.NewMemMapFs().Stat(".")
		if err != nil || !fi.IsDir() {
			t.Fatalf("%v %v", fi, err)
		}
	}},
	{"AFERO-003-mkdir-creates-parent", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		err := fs.Mkdir(filepath.Join("a", "b"), 0o755)
		if err != nil {
			t.Fatalf("%v", err)
		}
		if fi, e := fs.Stat("a"); e != nil || !fi.IsDir() {
			t.Fatalf("%v %v", fi, e)
		}
	}},
	{"AFERO-004-mkdirall-mode", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		if err := fs.MkdirAll("a/b", 0o750); err != nil {
			t.Fatal(err)
		}
		fi, _ := fs.Stat("a/b")
		if fi.Mode().Perm() != 0o750 || !fi.IsDir() {
			t.Fatalf("%v", fi.Mode())
		}
	}},
	{"AFERO-005-create-read", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "hello")
		if got := read(t, fs, "x"); got != "hello" {
			t.Fatal(got)
		}
	}},
	{"AFERO-006-create-truncates", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "hello")
		f, e := fs.Create("x")
		if e != nil {
			t.Fatal(e)
		}
		_ = f.Close()
		if got := read(t, fs, "x"); got != "" {
			t.Fatal(got)
		}
	}},
	{"AFERO-007-exclusive-create", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "v")
		_, e := fs.OpenFile("x", os.O_CREATE|os.O_EXCL|os.O_RDWR, 0o600)
		if !os.IsExist(e) {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-008-append-uses-current-offset", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "ab")
		f, e := fs.OpenFile("x", os.O_RDWR|os.O_APPEND, 0)
		if e != nil {
			t.Fatal(e)
		}
		_, _ = f.Seek(0, io.SeekStart)
		_, e = f.WriteString("c")
		if e != nil {
			t.Fatal(e)
		}
		_ = f.Close()
		if read(t, fs, "x") != "cb" {
			t.Fatal("offset")
		}
	}},
	{"AFERO-009-seek-gap-zero-filled", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		f, _ := fs.Create("x")
		_, _ = f.Seek(3, io.SeekStart)
		_, _ = f.Write([]byte{'z'})
		_ = f.Close()
		if !reflect.DeepEqual([]byte(read(t, fs, "x")), []byte{0, 0, 0, 'z'}) {
			t.Fatal("gap")
		}
	}},
	{"AFERO-010-readat-keeps-offset", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "abcd")
		f, _ := fs.Open("x")
		b := make([]byte, 2)
		n, e := f.ReadAt(b, 1)
		if n != 2 || e != nil || string(b) != "bc" {
			t.Fatalf("%d %v %q", n, e, b)
		}
		one := make([]byte, 1)
		_, _ = f.Read(one)
		if string(one) != "a" {
			t.Fatal(string(one))
		}
	}},
	{"AFERO-011-writeat-keeps-offset", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "abcd")
		f, _ := fs.OpenFile("x", os.O_RDWR, 0)
		_, _ = f.Seek(1, io.SeekStart)
		_, e := f.WriteAt([]byte("Z"), 2)
		if e != nil {
			t.Fatal(e)
		}
		_, _ = f.Write([]byte("Y"))
		_ = f.Close()
		if read(t, fs, "x") != "aYZd" {
			t.Fatal(read(t, fs, "x"))
		}
	}},
	{"AFERO-012-truncate-extends", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "a")
		f, _ := fs.OpenFile("x", os.O_RDWR, 0)
		if e := f.Truncate(3); e != nil {
			t.Fatal(e)
		}
		_ = f.Close()
		if !reflect.DeepEqual([]byte(read(t, fs, "x")), []byte{'a', 0, 0}) {
			t.Fatal("extend")
		}
	}},
	{"AFERO-013-chmod", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "a")
		if e := fs.Chmod("x", 0o604); e != nil {
			t.Fatal(e)
		}
		fi, _ := fs.Stat("x")
		if fi.Mode().Perm() != 0o604 {
			t.Fatalf("%o", fi.Mode().Perm())
		}
	}},
	{"AFERO-014-chtimes", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "a")
		m := time.Unix(1234, 0)
		if e := fs.Chtimes("x", m, m); e != nil {
			t.Fatal(e)
		}
		fi, _ := fs.Stat("x")
		if !fi.ModTime().Equal(m) {
			t.Fatalf("%v", fi.ModTime())
		}
	}},
	{"AFERO-015-remove-file", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "a")
		if e := fs.Remove("x"); e != nil {
			t.Fatal(e)
		}
		if _, e := fs.Stat("x"); !os.IsNotExist(e) {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-016-remove-directory-entry", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		_ = fs.MkdirAll("a", 0o755)
		write(t, fs, "a/x", "a")
		if e := fs.Remove("a"); e != nil {
			t.Fatal(e)
		}
		if _, e := fs.Stat("a"); !os.IsNotExist(e) {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-017-removeall-is-scoped", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		_ = fs.MkdirAll("a", 0o755)
		write(t, fs, "a/x", "x")
		write(t, fs, "y", "y")
		if e := fs.RemoveAll("a"); e != nil {
			t.Fatal(e)
		}
		if read(t, fs, "y") != "y" {
			t.Fatal("sibling")
		}
		if e := fs.RemoveAll("missing"); e != nil {
			t.Fatal(e)
		}
	}},
	{"AFERO-018-rename-file", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "v")
		if e := fs.Rename("x", "y"); e != nil {
			t.Fatal(e)
		}
		if read(t, fs, "y") != "v" {
			t.Fatal("value")
		}
		if _, e := fs.Stat("x"); !os.IsNotExist(e) {
			t.Fatal(e)
		}
	}},
	{"AFERO-019-rename-directory-tree", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		_ = fs.MkdirAll("a/b", 0o755)
		write(t, fs, "a/b/x", "v")
		if e := fs.Rename("a", "z"); e != nil {
			t.Fatal(e)
		}
		if read(t, fs, "z/b/x") != "v" {
			t.Fatal("tree")
		}
	}},
	{"AFERO-020-shared-file-state", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "abc")
		a, _ := fs.OpenFile("x", os.O_RDWR, 0)
		b, _ := fs.Open("x")
		_, _ = a.WriteAt([]byte("Z"), 1)
		buf := make([]byte, 3)
		_, _ = b.Read(buf)
		if string(buf) != "aZc" {
			t.Fatal(string(buf))
		}
	}},
	{"AFERO-021-independent-offsets", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "abc")
		a, _ := fs.Open("x")
		b, _ := fs.Open("x")
		x := make([]byte, 1)
		_, _ = a.Read(x)
		_, _ = a.Read(x)
		_, _ = b.Read(x)
		if string(x) != "a" {
			t.Fatal(string(x))
		}
	}},
	{"AFERO-022-closed-handle", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		f, _ := fs.Create("x")
		_ = f.Close()
		_, e := f.Write([]byte("x"))
		if e == nil || e.Error() != afero.ErrFileClosed.Error() {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-023-double-close", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		f, _ := fs.Create("x")
		_ = f.Close()
		if e := f.Close(); e == nil || e.Error() != afero.ErrFileClosed.Error() {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-024-readonly-openfile-write-rejected", func(t *testing.T) {
		base := afero.NewMemMapFs()
		write(t, base, "x", "v")
		ro := afero.NewReadOnlyFs(base)
		if _, e := ro.OpenFile("x", os.O_RDWR, 0); !os.IsPermission(e) {
			t.Fatalf("%v", e)
		}
	}},
	{"AFERO-025-readonly-mutators", func(t *testing.T) {
		ro := afero.NewReadOnlyFs(afero.NewMemMapFs())
		errs := []error{ro.Mkdir("x", 0o755), ro.MkdirAll("a/b", 0o755), ro.Remove("x"), ro.RemoveAll("x"), ro.Rename("x", "y")}
		for _, e := range errs {
			if !os.IsPermission(e) {
				t.Fatalf("%v", e)
			}
		}
	}},
	{"AFERO-026-directory-sorted", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		_ = fs.Mkdir("d", 0o755)
		for _, n := range []string{"c", "a", "b"} {
			write(t, fs, "d/"+n, n)
		}
		f, _ := fs.Open("d")
		names, e := f.Readdirnames(-1)
		if e != nil {
			t.Fatal(e)
		}
		if !sort.StringsAreSorted(names) || !reflect.DeepEqual(names, []string{"a", "b", "c"}) {
			t.Fatal(names)
		}
	}},
	{"AFERO-027-directory-cursor", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		_ = fs.Mkdir("d", 0o755)
		write(t, fs, "d/a", "a")
		write(t, fs, "d/b", "b")
		f, _ := fs.Open("d")
		n, e := f.Readdirnames(1)
		if e != nil || len(n) != 1 {
			t.Fatalf("%v %v", n, e)
		}
		n, e = f.Readdirnames(1)
		if e != nil || len(n) != 1 {
			t.Fatalf("%v %v", n, e)
		}
		n, e = f.Readdirnames(1)
		if len(n) != 0 || e != io.EOF {
			t.Fatalf("%v %v", n, e)
		}
	}},
	{"AFERO-028-readdir-regular-file", func(t *testing.T) {
		fs := afero.NewMemMapFs()
		write(t, fs, "x", "v")
		f, _ := fs.Open("x")
		if _, e := f.Readdir(1); e == nil {
			t.Fatal("expected error")
		}
	}},
	{"AFERO-029-basepath-read", func(t *testing.T) {
		src := afero.NewMemMapFs()
		_ = src.MkdirAll("root", 0o755)
		write(t, src, "root/x", "v")
		bp := afero.NewBasePathFs(src, "root")
		if read(t, bp, "x") != "v" {
			t.Fatal("read")
		}
	}},
	{"AFERO-030-basepath-create", func(t *testing.T) {
		src := afero.NewMemMapFs()
		_ = src.MkdirAll("root", 0o755)
		bp := afero.NewBasePathFs(src, "root")
		write(t, bp, "x", "v")
		if read(t, src, "root/x") != "v" {
			t.Fatal("backing")
		}
	}},
	{"AFERO-031-basepath-escape", func(t *testing.T) {
		src := afero.NewMemMapFs()
		_ = src.MkdirAll("root", 0o755)
		bp := afero.NewBasePathFs(src, "root")
		if _, e := bp.Create(filepath.Join("..", "escape")); e == nil {
			t.Fatal("escape accepted")
		}
		if _, e := src.Stat("escape"); !os.IsNotExist(e) {
			t.Fatal("mutated outside")
		}
	}},
	{"AFERO-032-nested-basepath", func(t *testing.T) {
		src := afero.NewMemMapFs()
		_ = src.MkdirAll("a/b", 0o755)
		bp := afero.NewBasePathFs(afero.NewBasePathFs(src, "a"), "b")
		write(t, bp, "x", "v")
		if read(t, src, "a/b/x") != "v" {
			t.Fatal("nested")
		}
	}},
	{"AFERO-033-cow-read-does-not-copy", func(t *testing.T) {
		base, layer := afero.NewMemMapFs(), afero.NewMemMapFs()
		write(t, base, "x", "v")
		cow := afero.NewCopyOnWriteFs(base, layer)
		if read(t, cow, "x") != "v" {
			t.Fatal("read")
		}
		if _, e := layer.Stat("x"); !os.IsNotExist(e) {
			t.Fatal("copied")
		}
	}},
	{"AFERO-034-cow-create-overlay", func(t *testing.T) {
		base, layer := afero.NewMemMapFs(), afero.NewMemMapFs()
		cow := afero.NewCopyOnWriteFs(base, layer)
		write(t, cow, "x", "v")
		if read(t, layer, "x") != "v" {
			t.Fatal("layer")
		}
		if _, e := base.Stat("x"); !os.IsNotExist(e) {
			t.Fatal("base")
		}
	}},
	{"AFERO-035-cache-populates", func(t *testing.T) {
		base, cache := afero.NewMemMapFs(), afero.NewMemMapFs()
		write(t, base, "x", "v")
		c := afero.NewCacheOnReadFs(base, cache, 0)
		if read(t, c, "x") != "v" || read(t, cache, "x") != "v" {
			t.Fatal("cache")
		}
	}},
}

func TestAFERO001(t *testing.T) { atomicCases[0].run(t) }
func TestAFERO002(t *testing.T) { atomicCases[1].run(t) }
func TestAFERO003(t *testing.T) { atomicCases[2].run(t) }
func TestAFERO004(t *testing.T) { atomicCases[3].run(t) }
func TestAFERO005(t *testing.T) { atomicCases[4].run(t) }
func TestAFERO006(t *testing.T) { atomicCases[5].run(t) }
func TestAFERO007(t *testing.T) { atomicCases[6].run(t) }
func TestAFERO009(t *testing.T) { atomicCases[8].run(t) }
func TestAFERO010(t *testing.T) { atomicCases[9].run(t) }
func TestAFERO011(t *testing.T) { atomicCases[10].run(t) }
func TestAFERO012(t *testing.T) { atomicCases[11].run(t) }
func TestAFERO013(t *testing.T) { atomicCases[12].run(t) }
func TestAFERO014(t *testing.T) { atomicCases[13].run(t) }
func TestAFERO015(t *testing.T) { atomicCases[14].run(t) }
func TestAFERO016(t *testing.T) { atomicCases[15].run(t) }
func TestAFERO017(t *testing.T) { atomicCases[16].run(t) }
func TestAFERO018(t *testing.T) { atomicCases[17].run(t) }
func TestAFERO019(t *testing.T) { atomicCases[18].run(t) }
func TestAFERO020(t *testing.T) { atomicCases[19].run(t) }
func TestAFERO021(t *testing.T) { atomicCases[20].run(t) }
func TestAFERO022(t *testing.T) { atomicCases[21].run(t) }
func TestAFERO023(t *testing.T) { atomicCases[22].run(t) }
func TestAFERO024(t *testing.T) { atomicCases[23].run(t) }
func TestAFERO025(t *testing.T) { atomicCases[24].run(t) }
func TestAFERO026(t *testing.T) { atomicCases[25].run(t) }
func TestAFERO027(t *testing.T) { atomicCases[26].run(t) }
func TestAFERO028(t *testing.T) { atomicCases[27].run(t) }
func TestAFERO029(t *testing.T) { atomicCases[28].run(t) }
func TestAFERO030(t *testing.T) { atomicCases[29].run(t) }
func TestAFERO031(t *testing.T) { atomicCases[30].run(t) }
func TestAFERO032(t *testing.T) { atomicCases[31].run(t) }
func TestAFERO033(t *testing.T) { atomicCases[32].run(t) }
func TestAFERO034(t *testing.T) { atomicCases[33].run(t) }
func TestAFERO035(t *testing.T) { atomicCases[34].run(t) }
