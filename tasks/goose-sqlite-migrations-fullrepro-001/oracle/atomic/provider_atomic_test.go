// Spec2Repo oracle - atomic tests for goose-sqlite-migrations-fullrepro-001.
package atomic

import (
	"context"
	"database/sql"
	"errors"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"testing/fstest"

	"github.com/pressly/goose/v3"
	_ "modernc.org/sqlite"
)

func excludeNamesOption(t *testing.T, names []string) goose.ProviderOption {
	t.Helper()
	fn := reflect.ValueOf(goose.WithExcludeNames)
	args := []reflect.Value{reflect.ValueOf(names)}
	var out []reflect.Value
	if fn.Type().IsVariadic() {
		out = fn.CallSlice(args)
	} else {
		out = fn.Call(args)
	}
	if len(out) != 1 {
		t.Fatalf("WithExcludeNames returned %d values", len(out))
	}
	option, ok := out[0].Interface().(goose.ProviderOption)
	if !ok {
		t.Fatal("WithExcludeNames did not return ProviderOption")
	}
	return option
}

func excludeVersionsOption(t *testing.T, versions []int64) goose.ProviderOption {
	t.Helper()
	fn := reflect.ValueOf(goose.WithExcludeVersions)
	args := []reflect.Value{reflect.ValueOf(versions)}
	var out []reflect.Value
	if fn.Type().IsVariadic() {
		out = fn.CallSlice(args)
	} else {
		out = fn.Call(args)
	}
	if len(out) != 1 {
		t.Fatalf("WithExcludeVersions returned %d values", len(out))
	}
	option, ok := out[0].Interface().(goose.ProviderOption)
	if !ok {
		t.Fatal("WithExcludeVersions did not return ProviderOption")
	}
	return option
}

func createMigration(t *testing.T, dir, name, migrationType string) error {
	t.Helper()
	fn := reflect.ValueOf(goose.Create)
	fnType := fn.Type()
	stringArg := func(index int, value string) reflect.Value {
		t.Helper()
		arg := reflect.ValueOf(value)
		if arg.Type().AssignableTo(fnType.In(index)) {
			return arg
		}
		if arg.Type().ConvertibleTo(fnType.In(index)) {
			return arg.Convert(fnType.In(index))
		}
		t.Fatalf("Create argument %d does not accept a string-like value", index)
		return reflect.Value{}
	}

	var args []reflect.Value
	switch fnType.NumIn() {
	case 3:
		args = []reflect.Value{
			stringArg(0, dir),
			stringArg(1, name),
			stringArg(2, migrationType),
		}
	case 4:
		args = []reflect.Value{
			reflect.Zero(fnType.In(0)),
			stringArg(1, dir),
			stringArg(2, name),
			stringArg(3, migrationType),
		}
	default:
		t.Fatalf("Create accepts %d arguments, want a documented 3- or legacy 4-argument form", fnType.NumIn())
	}
	out := fn.Call(args)
	if len(out) != 1 && len(out) != 2 {
		t.Fatalf("Create returned %d values", len(out))
	}
	last := out[len(out)-1]
	if last.IsNil() {
		return nil
	}
	err, ok := last.Interface().(error)
	if !ok {
		t.Fatal("Create final return value is not an error")
	}
	return err
}

func openDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite", "file:"+t.Name()+"?mode=memory&cache=shared")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func sources() fstest.MapFS {
	return fstest.MapFS{
		"001_users.sql": {Data: []byte("-- +goose Up\nCREATE TABLE users(id INTEGER PRIMARY KEY);\n-- +goose Down\nDROP TABLE users;")},
		"003_posts.sql": {Data: []byte("-- +goose Up\nCREATE TABLE posts(id INTEGER PRIMARY KEY);\n-- +goose Down\nDROP TABLE posts;")},
		"002_names.sql": {Data: []byte("-- +goose Up\nALTER TABLE users ADD COLUMN name TEXT;\n-- +goose Down\nALTER TABLE users DROP COLUMN name;")},
	}
}

func requireUsableProvider(t *testing.T) {
	t.Helper()
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources())
	if err != nil {
		t.Fatal(err)
	}
	if got := p.ListSources(); len(got) != 3 || got[0].Version != 1 {
		t.Fatalf("valid provider produced unexpected sources: %#v", got)
	}
}

func requireUsableGoMigration(t *testing.T) {
	t.Helper()
	p, err := goose.NewProvider(
		goose.DialectSQLite3,
		openDB(t),
		nil,
		goose.WithGoMigrations(goose.NewGoMigration(1, nil, nil)),
	)
	if err != nil {
		t.Fatal(err)
	}
	if got := p.ListSources(); len(got) != 1 || got[0].Version != 1 {
		t.Fatalf("valid Go migration produced unexpected sources: %#v", got)
	}
}

// Verifies: GOOSE-SRC-001.
func TestNumericComponentSQL(t *testing.T) {
	got, err := goose.NumericComponent("00042_add_users.sql")
	if err != nil || got != 42 {
		t.Fatalf("got (%d, %v), want (42, nil)", got, err)
	}
}

// Verifies: GOOSE-SRC-001.
func TestNumericComponentGo(t *testing.T) {
	got, err := goose.NumericComponent("migrations/7_seed.go")
	if err != nil || got != 7 {
		t.Fatalf("got (%d, %v), want (7, nil)", got, err)
	}
}

// Verifies: GOOSE-SRC-001.
func TestNumericComponentRejectsMissingPrefix(t *testing.T) {
	if _, err := goose.NumericComponent("users.sql"); err == nil {
		t.Fatal("expected an error")
	}
	if got, err := goose.NumericComponent("9_users.sql"); err != nil || got != 9 {
		t.Fatalf("valid filename got (%d, %v)", got, err)
	}
}

// Verifies: GOOSE-SRC-001.
func TestNumericComponentRejectsZero(t *testing.T) {
	if _, err := goose.NumericComponent("000_users.sql"); err == nil {
		t.Fatal("expected an error")
	}
	if got, err := goose.NumericComponent("1_users.sql"); err != nil || got != 1 {
		t.Fatalf("valid filename got (%d, %v)", got, err)
	}
}

// Verifies: GOOSE-SRC-001.
func TestNumericComponentRejectsExtension(t *testing.T) {
	if _, err := goose.NumericComponent("001_users.txt"); err == nil {
		t.Fatal("expected an error")
	}
	if got, err := goose.NumericComponent("1_users.go"); err != nil || got != 1 {
		t.Fatalf("valid filename got (%d, %v)", got, err)
	}
}

// Verifies: GOOSE-PROV-001.
func TestNewProviderRejectsNilDatabase(t *testing.T) {
	if _, err := goose.NewProvider(goose.DialectSQLite3, nil, sources()); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableProvider(t)
}

// Verifies: GOOSE-PROV-001, GOOSE-PROV-002.
func TestNewProviderRejectsNoSources(t *testing.T) {
	_, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), fstest.MapFS{})
	if !errors.Is(err, goose.ErrNoMigrations) {
		t.Fatalf("got %v, want ErrNoMigrations", err)
	}
}

// Verifies: GOOSE-PROV-006.
func TestListSourcesSortsByVersion(t *testing.T) {
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources())
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()
	if len(got) != 3 || got[0].Version != 1 || got[1].Version != 2 || got[2].Version != 3 {
		t.Fatalf("unexpected source order: %#v", got)
	}
}

// Verifies: GOOSE-PROV-006.
func TestListSourcesReportsSQLMetadata(t *testing.T) {
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources())
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()[0]
	if got.Type != goose.TypeSQL || got.Path != "001_users.sql" || got.Version != 1 {
		t.Fatalf("unexpected source: %#v", got)
	}
}

// Verifies: GOOSE-PROV-003, GOOSE-INV-008.
func TestExcludeNameRemovesSource(t *testing.T) {
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources(), excludeNamesOption(t, []string{"002_names.sql"}))
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()
	if len(got) != 2 || got[0].Version != 1 || got[1].Version != 3 {
		t.Fatalf("unexpected sources: %#v", got)
	}
}

// Verifies: GOOSE-PROV-003, GOOSE-INV-008.
func TestExcludeVersionRemovesSource(t *testing.T) {
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources(), excludeVersionsOption(t, []int64{3}))
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()
	if len(got) != 2 || got[0].Version != 1 || got[1].Version != 2 {
		t.Fatalf("unexpected sources: %#v", got)
	}
}

// Verifies: GOOSE-PROV-003.
func TestExcludeVersionRejectsNonPositive(t *testing.T) {
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources(), excludeVersionsOption(t, []int64{0})); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableProvider(t)
}

// Verifies: GOOSE-PROV-003.
func TestExcludeNameRejectsDuplicate(t *testing.T) {
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources(), excludeNamesOption(t, []string{"001_users.sql", "001_users.sql"})); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableProvider(t)
}

// Verifies: GOOSE-PROV-010.
func TestTableNameRejectsEmpty(t *testing.T) {
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources(), goose.WithTableName("")); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableProvider(t)
}

// Verifies: GOOSE-PROV-005, GOOSE-INV-012.
func TestGoMigrationAppearsAsSource(t *testing.T) {
	m := goose.NewGoMigration(4, nil, nil)
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), nil, goose.WithGoMigrations(m))
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()
	if len(got) != 1 || got[0].Type != goose.TypeGo || got[0].Version != 4 {
		t.Fatalf("unexpected source: %#v", got)
	}
}

// Verifies: GOOSE-PROV-005.
func TestGoMigrationRejectsNonPositiveVersion(t *testing.T) {
	m := goose.NewGoMigration(0, nil, nil)
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), nil, goose.WithGoMigrations(m)); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableGoMigration(t)
}

// Verifies: GOOSE-PROV-005.
func TestGoMigrationRejectsTwoCallbacks(t *testing.T) {
	f := &goose.GoFunc{
		RunTx: func(_ context.Context, _ *sql.Tx) error { return nil },
		RunDB: func(_ context.Context, _ *sql.DB) error { return nil },
	}
	m := goose.NewGoMigration(1, f, nil)
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), nil, goose.WithGoMigrations(m)); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableGoMigration(t)
}

// Verifies: GOOSE-PROV-005, GOOSE-INV-012.
func TestGoMigrationRejectsDuplicateVersion(t *testing.T) {
	a := goose.NewGoMigration(2, nil, nil)
	b := goose.NewGoMigration(2, nil, nil)
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), nil, goose.WithGoMigrations(a, b)); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableGoMigration(t)
}

// Verifies: GOOSE-PROV-010.
func TestDefaultTableNameValue(t *testing.T) {
	if goose.DefaultTablename != "goose_db_version" {
		t.Fatalf("got %q", goose.DefaultTablename)
	}
}

// Verifies: GOOSE-PROV-003.
func TestExcludeNamesMergeAcrossOptions(t *testing.T) {
	p, err := goose.NewProvider(
		goose.DialectSQLite3,
		openDB(t),
		sources(),
		excludeNamesOption(t, []string{"001_users.sql"}),
		excludeNamesOption(t, []string{"003_posts.sql"}),
	)
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()
	if len(got) != 1 || got[0].Version != 2 {
		t.Fatalf("unexpected sources: %#v", got)
	}
}

// Verifies: GOOSE-PROV-003.
func TestExcludeVersionsMergeAcrossOptions(t *testing.T) {
	p, err := goose.NewProvider(
		goose.DialectSQLite3,
		openDB(t),
		sources(),
		excludeVersionsOption(t, []int64{1}),
		excludeVersionsOption(t, []int64{2}),
	)
	if err != nil {
		t.Fatal(err)
	}
	got := p.ListSources()
	if len(got) != 1 || got[0].Version != 3 {
		t.Fatalf("unexpected sources: %#v", got)
	}
}

// Verifies: GOOSE-SRC-001, GOOSE-PROV-006.
func TestCollectMigrationsSortsSources(t *testing.T) {
	goose.SetBaseFS(sources())
	t.Cleanup(func() { goose.SetBaseFS(nil) })
	got, err := goose.CollectMigrations(".", 0, math.MaxInt64)
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 3 || got[0].Version != 1 || got[1].Version != 2 || got[2].Version != 3 {
		t.Fatalf("unexpected migrations: %#v", got)
	}
}

// Verifies: GOOSE-SRC-001.
func TestCollectMigrationsEmptySourceSetReturnsSentinel(t *testing.T) {
	goose.SetBaseFS(fstest.MapFS{})
	t.Cleanup(func() { goose.SetBaseFS(nil) })
	got, err := goose.CollectMigrations(".", 0, math.MaxInt64)
	if !errors.Is(err, goose.ErrNoMigrationFiles) || len(got) != 0 {
		t.Fatalf("got (%#v, %v), want empty migrations and ErrNoMigrationFiles", got, err)
	}
}

// Verifies: GOOSE-SRC-001.
func TestCollectMigrationsRejectsDuplicateVersion(t *testing.T) {
	duplicates := fstest.MapFS{
		"001_a.sql": {Data: []byte("-- +goose Up")},
		"001_b.sql": {Data: []byte("-- +goose Up")},
	}
	if _, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), duplicates); err == nil {
		t.Fatal("expected an error")
	}
	requireUsableProvider(t)
}

// Verifies: GOOSE-SRC-001.
func TestCollectMigrationsRejectsMissingDirectory(t *testing.T) {
	goose.SetBaseFS(fstest.MapFS{})
	t.Cleanup(func() { goose.SetBaseFS(nil) })
	if _, err := goose.CollectMigrations("missing", 0, math.MaxInt64); err == nil {
		t.Fatal("expected an error")
	}
	goose.SetBaseFS(sources())
	got, err := goose.CollectMigrations(".", 0, 1)
	if err != nil || len(got) != 1 || got[0].Version != 1 {
		t.Fatalf("valid collection got (%#v, %v)", got, err)
	}
}

// Verifies: GOOSE-PROV-015.
func TestProviderPing(t *testing.T) {
	p, err := goose.NewProvider(goose.DialectSQLite3, openDB(t), sources())
	if err != nil {
		t.Fatal(err)
	}
	if err := p.Ping(context.Background()); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GOOSE-PROV-015.
func TestProviderCloseStopsPing(t *testing.T) {
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	p, err := goose.NewProvider(goose.DialectSQLite3, db, sources())
	if err != nil {
		t.Fatal(err)
	}
	if err := p.Close(); err != nil {
		t.Fatal(err)
	}
	if err := p.Ping(context.Background()); err == nil {
		t.Fatal("expected ping error after close")
	}
}

// Verifies: GOOSE-FILE-001, GOOSE-FILE-003.
func TestCreateSequentialSQL(t *testing.T) {
	goose.SetSequential(true)
	t.Cleanup(func() { goose.SetSequential(false) })
	dir := t.TempDir()
	if err := createMigration(t, dir, "add users", "sql"); err != nil {
		t.Fatal(err)
	}
	matches, err := filepath.Glob(filepath.Join(dir, "00001_add_users.sql"))
	if err != nil || len(matches) != 1 {
		t.Fatalf("got files %#v, err %v", matches, err)
	}
	data, err := os.ReadFile(matches[0])
	if err != nil || len(data) == 0 {
		t.Fatalf("created file is unreadable or empty: %v", err)
	}
}

// Verifies: GOOSE-FILE-001.
func TestCreateSequentialGo(t *testing.T) {
	goose.SetSequential(true)
	t.Cleanup(func() { goose.SetSequential(false) })
	dir := t.TempDir()
	if err := createMigration(t, dir, "seed audit", "go"); err != nil {
		t.Fatal(err)
	}
	matches, err := filepath.Glob(filepath.Join(dir, "00001_seed_audit.go"))
	if err != nil || len(matches) != 1 {
		t.Fatalf("got files %#v, err %v", matches, err)
	}
}

// Verifies: GOOSE-FILE-001.
func TestCreateRejectsUnavailableDirectory(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "missing")
	if err := createMigration(t, dir, "bad", "sql"); err == nil {
		t.Fatal("expected an error")
	}
	if _, err := os.Stat(dir); !os.IsNotExist(err) {
		t.Fatalf("unexpected directory state: %v", err)
	}
	goose.SetSequential(true)
	t.Cleanup(func() { goose.SetSequential(false) })
	valid := t.TempDir()
	if err := createMigration(t, valid, "works", "sql"); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(valid, "00001_works.sql")); err != nil {
		t.Fatalf("valid create did not produce its file: %v", err)
	}
}
