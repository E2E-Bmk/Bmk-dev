// Spec2Repo oracle - integration tests for goose-sqlite-migrations-fullrepro-001.
package integration

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"testing/fstest"

	"github.com/pressly/goose/v3"
	_ "modernc.org/sqlite"
)

var basicMigrations = fstest.MapFS{
	"001_users.sql": {Data: []byte("-- +goose Up\nCREATE TABLE users(id INTEGER PRIMARY KEY);\n-- +goose Down\nDROP TABLE users;")},
	"002_names.sql": {Data: []byte("-- +goose Up\nALTER TABLE users ADD COLUMN name TEXT;\n-- +goose Down\nALTER TABLE users DROP COLUMN name;")},
	"003_posts.sql": {Data: []byte("-- +goose Up\nCREATE TABLE posts(id INTEGER PRIMARY KEY);\n-- +goose Down\nDROP TABLE posts;")},
}

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

func newProvider(t *testing.T, fsys fstest.MapFS, opts ...goose.ProviderOption) (*goose.Provider, *sql.DB) {
	t.Helper()
	db, err := sql.Open("sqlite", "file:"+t.Name()+"?mode=memory&cache=shared")
	if err != nil {
		t.Fatal(err)
	}
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { _ = db.Close() })
	p, err := goose.NewProvider(goose.DialectSQLite3, db, fsys, opts...)
	if err != nil {
		t.Fatal(err)
	}
	return p, db
}

func tableExists(t *testing.T, db *sql.DB, name string) bool {
	t.Helper()
	var count int
	if err := db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", name).Scan(&count); err != nil {
		t.Fatal(err)
	}
	return count == 1
}

// Verifies: GOOSE-PROV-007, GOOSE-PROV-008.
// Depends-On: TestListSourcesSortsByVersion, TestProviderPing
func TestInitialStatusIsPending(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	status, err := p.Status(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(status) != 3 {
		t.Fatalf("got %d statuses", len(status))
	}
	for _, item := range status {
		if item.State != goose.StatePending || !item.AppliedAt.IsZero() {
			t.Fatalf("unexpected pending status: %#v", item)
		}
	}
}

// Verifies: GOOSE-PROV-009.
// Depends-On: TestListSourcesSortsByVersion, TestProviderPing
func TestHasPendingBeforeAndAfterUp(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	pending, err := p.HasPending(context.Background())
	if err != nil || !pending {
		t.Fatalf("before Up got (%v, %v)", pending, err)
	}
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	pending, err = p.HasPending(context.Background())
	if err != nil || pending {
		t.Fatalf("after Up got (%v, %v)", pending, err)
	}
}

// Verifies: GOOSE-PROV-014, GOOSE-INV-002.
// Depends-On: TestDefaultTableNameValue, TestProviderPing
func TestInitialVersions(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	current, target, err := p.GetVersions(context.Background())
	if err != nil || current != 0 || target != 3 {
		t.Fatalf("got (%d, %d, %v)", current, target, err)
	}
}

// Verifies: GOOSE-RUN-001, GOOSE-RUN-010, GOOSE-INV-003.
// Depends-On: TestCollectMigrationsSortsSources, TestProviderPing
func TestUpAppliesAllSources(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	results, err := p.Up(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(results) != 3 || results[0].Source.Version != 1 || results[2].Source.Version != 3 {
		t.Fatalf("unexpected results: %#v", results)
	}
	if !tableExists(t, db, "users") || !tableExists(t, db, "posts") {
		t.Fatal("expected migrated tables")
	}
	for _, result := range results {
		if result.Direction != "up" || result.Duration < 0 || result.Error != nil {
			t.Fatalf("unexpected result: %#v", result)
		}
	}
}

// Verifies: GOOSE-RUN-001.
// Depends-On: TestCollectMigrationsSortsSources
func TestUpWhenCompleteIsEmptySuccess(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	results, err := p.Up(context.Background())
	if err != nil || len(results) != 0 {
		t.Fatalf("got (%#v, %v)", results, err)
	}
}

// Verifies: GOOSE-RUN-002, GOOSE-INV-002.
// Depends-On: TestListSourcesSortsByVersion
func TestUpByOneAppliesNextSource(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	result, err := p.UpByOne(context.Background())
	if err != nil || result.Source.Version != 1 || !tableExists(t, db, "users") {
		t.Fatalf("unexpected result (%#v, %v)", result, err)
	}
	version, err := p.GetDBVersion(context.Background())
	if err != nil || version != 1 {
		t.Fatalf("got version (%d, %v)", version, err)
	}
}

// Verifies: GOOSE-RUN-002.
// Depends-On: TestListSourcesSortsByVersion
func TestUpByOneWhenCompleteReturnsSentinel(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	_, err := p.UpByOne(context.Background())
	if !errors.Is(err, goose.ErrNoNextVersion) {
		t.Fatalf("got %v", err)
	}
}

// Verifies: GOOSE-RUN-003.
// Depends-On: TestListSourcesSortsByVersion
func TestUpToStopsAtTarget(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	results, err := p.UpTo(context.Background(), 2)
	if err != nil || len(results) != 2 || results[1].Source.Version != 2 {
		t.Fatalf("got (%#v, %v)", results, err)
	}
	if !tableExists(t, db, "users") || tableExists(t, db, "posts") {
		t.Fatal("database did not stop at version 2")
	}
}

// Verifies: GOOSE-RUN-004, GOOSE-INV-004.
// Depends-On: TestListSourcesSortsByVersion
func TestDownRollsBackLatestSource(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	result, err := p.Down(context.Background())
	if err != nil || result.Source.Version != 3 || result.Direction != "down" {
		t.Fatalf("got (%#v, %v)", result, err)
	}
	if tableExists(t, db, "posts") || !tableExists(t, db, "users") {
		t.Fatal("unexpected schema after Down")
	}
}

// Verifies: GOOSE-RUN-004.
// Depends-On: TestProviderPing
func TestDownWhenEmptyReturnsSentinel(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	_, err := p.Down(context.Background())
	if !errors.Is(err, goose.ErrNoNextVersion) {
		t.Fatalf("got %v", err)
	}
}

// Verifies: GOOSE-RUN-005, GOOSE-INV-004.
// Depends-On: TestListSourcesSortsByVersion
func TestDownToPreservesTarget(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	results, err := p.DownTo(context.Background(), 1)
	if err != nil || len(results) != 2 {
		t.Fatalf("got (%#v, %v)", results, err)
	}
	if !tableExists(t, db, "users") || tableExists(t, db, "posts") {
		t.Fatal("target state was not preserved")
	}
	version, _ := p.GetDBVersion(context.Background())
	if version != 1 {
		t.Fatalf("got version %d", version)
	}
}

// Verifies: GOOSE-RUN-005.
// Depends-On: TestListSourcesSortsByVersion
func TestDownToRejectsNegativeWithoutStateChange(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	if _, err := p.DownTo(context.Background(), -1); err == nil {
		t.Fatal("expected an error")
	}
	version, _ := p.GetDBVersion(context.Background())
	if version != 3 {
		t.Fatalf("state changed to version %d", version)
	}
}

// Verifies: GOOSE-RUN-006.
// Depends-On: TestListSourcesSortsByVersion
func TestApplyVersionTargetsOneSource(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	result, err := p.ApplyVersion(context.Background(), 3, true)
	if err != nil || result.Source.Version != 3 || !tableExists(t, db, "posts") {
		t.Fatalf("got (%#v, %v)", result, err)
	}
	if tableExists(t, db, "users") {
		t.Fatal("unrequested version was applied")
	}
}

// Verifies: GOOSE-RUN-006.
// Depends-On: TestListSourcesSortsByVersion
func TestApplyVersionRejectsMissingSource(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	_, err := p.ApplyVersion(context.Background(), 99, true)
	if !errors.Is(err, goose.ErrVersionNotFound) {
		t.Fatalf("got %v", err)
	}
}

// Verifies: GOOSE-RUN-006.
// Depends-On: TestListSourcesSortsByVersion
func TestApplyVersionRejectsUnappliedDown(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	_, err := p.ApplyVersion(context.Background(), 1, false)
	if !errors.Is(err, goose.ErrNotApplied) {
		t.Fatalf("got %v", err)
	}
}

// Verifies: GOOSE-PROV-007, GOOSE-INV-001.
// Depends-On: TestListSourcesReportsSQLMetadata
func TestStatusAgreesWithAppliedSchema(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	if _, err := p.UpTo(context.Background(), 2); err != nil {
		t.Fatal(err)
	}
	status, err := p.Status(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if status[0].State != goose.StateApplied || status[0].AppliedAt.IsZero() || status[1].State != goose.StateApplied || status[2].State != goose.StatePending {
		t.Fatalf("unexpected status: %#v", status)
	}
	if !tableExists(t, db, "users") || tableExists(t, db, "posts") {
		t.Fatal("status and schema disagree")
	}
}

// Verifies: GOOSE-PROV-010, GOOSE-INV-001.
// Depends-On: TestTableNameRejectsEmpty, TestDefaultTableNameValue
func TestCustomVersionTableIsUsed(t *testing.T) {
	p, db := newProvider(t, basicMigrations, goose.WithTableName("migration_history"))
	if _, err := p.UpByOne(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !tableExists(t, db, "migration_history") || tableExists(t, db, goose.DefaultTablename) {
		t.Fatal("provider did not use custom version table")
	}
}

// Verifies: GOOSE-PROV-013, GOOSE-INV-010.
// Depends-On: TestDefaultTableNameValue
func TestDisableVersioningChangesSchemaWithoutHistory(t *testing.T) {
	p, db := newProvider(t, basicMigrations, goose.WithDisableVersioning(true))
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !tableExists(t, db, "users") || !tableExists(t, db, "posts") || tableExists(t, db, goose.DefaultTablename) {
		t.Fatal("unexpected schema or history")
	}
	if _, err := p.GetDBVersion(context.Background()); err == nil {
		t.Fatal("expected GetDBVersion error")
	}
}

// Verifies: GOOSE-SQL-003, GOOSE-RUN-011, GOOSE-INV-005.
// Depends-On: TestListSourcesReportsSQLMetadata
func TestTransactionalFailureRollsBackSchemaAndVersion(t *testing.T) {
	fsys := fstest.MapFS{"001_bad.sql": {Data: []byte("-- +goose Up\nCREATE TABLE transient(id INTEGER);\nINSERT INTO missing_table VALUES (1);")}}
	p, db := newProvider(t, fsys)
	if _, err := p.Up(context.Background()); err == nil {
		t.Fatal("expected an error")
	}
	if tableExists(t, db, "transient") {
		t.Fatal("transactional schema change survived")
	}
	version, err := p.GetDBVersion(context.Background())
	if err != nil || version != 0 {
		t.Fatalf("got version (%d, %v)", version, err)
	}
}

// Verifies: GOOSE-PROV-005, GOOSE-RUN-001, GOOSE-INV-012.
// Depends-On: TestGoMigrationAppearsAsSource
func TestGoMigrationRunsTxCallback(t *testing.T) {
	up := &goose.GoFunc{RunTx: func(ctx context.Context, tx *sql.Tx) error {
		_, err := tx.ExecContext(ctx, "CREATE TABLE audit(id INTEGER PRIMARY KEY)")
		return err
	}}
	m := goose.NewGoMigration(1, up, nil)
	p, db := newProvider(t, nil, goose.WithGoMigrations(m))
	result, err := p.UpByOne(context.Background())
	if err != nil || result.Source.Type != goose.TypeGo || !tableExists(t, db, "audit") {
		t.Fatalf("got (%#v, %v)", result, err)
	}
}

// Verifies: GOOSE-RUN-011.
// Depends-On: TestGoMigrationAppearsAsSource
func TestPartialErrorReportsSuccessAndFailure(t *testing.T) {
	marker := errors.New("callback failed")
	ok := goose.NewGoMigration(1, &goose.GoFunc{RunTx: func(ctx context.Context, tx *sql.Tx) error {
		_, err := tx.ExecContext(ctx, "CREATE TABLE first_ok(id INTEGER)")
		return err
	}}, nil)
	bad := goose.NewGoMigration(2, &goose.GoFunc{RunTx: func(context.Context, *sql.Tx) error { return marker }}, nil)
	p, db := newProvider(t, nil, goose.WithGoMigrations(ok, bad))
	_, err := p.Up(context.Background())
	var partial *goose.PartialError
	if !errors.As(err, &partial) || !errors.Is(err, marker) {
		t.Fatalf("got %T %v", err, err)
	}
	if len(partial.Applied) != 1 || partial.Applied[0].Source.Version != 1 || partial.Failed.Source.Version != 2 || partial.Failed.Error == nil {
		t.Fatalf("unexpected partial result: %#v", partial)
	}
	if !tableExists(t, db, "first_ok") {
		t.Fatal("successful earlier migration was not committed")
	}
	version, versionErr := p.GetDBVersion(context.Background())
	if versionErr != nil || version != 1 {
		t.Fatalf("got version (%d, %v)", version, versionErr)
	}
}

// Verifies: GOOSE-SQL-004.
// Depends-On: TestListSourcesReportsSQLMetadata
func TestEnvironmentSubstitutionWritesExpandedValue(t *testing.T) {
	t.Setenv("GOOSE_ORACLE_VALUE", "expanded")
	sqlText := fmt.Sprintf("-- +goose Up\nCREATE TABLE config(value TEXT);\n-- +goose ENVSUB ON\nINSERT INTO config VALUES ('${%s}');\n-- +goose ENVSUB OFF", "GOOSE_ORACLE_VALUE")
	p, db := newProvider(t, fstest.MapFS{"001_env.sql": {Data: []byte(sqlText)}})
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	var got string
	if err := db.QueryRow("SELECT value FROM config").Scan(&got); err != nil || got != "expanded" {
		t.Fatalf("got (%q, %v)", got, err)
	}
}

// Verifies: GOOSE-RUN-006.
// Depends-On: TestListSourcesSortsByVersion
func TestApplyVersionRejectsAlreadyApplied(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	if _, err := p.ApplyVersion(context.Background(), 1, true); err != nil {
		t.Fatal(err)
	}
	_, err := p.ApplyVersion(context.Background(), 1, true)
	if !errors.Is(err, goose.ErrAlreadyApplied) {
		t.Fatalf("got %v", err)
	}
}

// Verifies: GOOSE-RUN-006, GOOSE-INV-004.
// Depends-On: TestListSourcesSortsByVersion
func TestApplyVersionRollsBackExactSource(t *testing.T) {
	p, db := newProvider(t, basicMigrations)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	result, err := p.ApplyVersion(context.Background(), 3, false)
	if err != nil || result.Source.Version != 3 || result.Direction != "down" {
		t.Fatalf("got (%#v, %v)", result, err)
	}
	if tableExists(t, db, "posts") || !tableExists(t, db, "users") {
		t.Fatal("exact rollback changed the wrong schema")
	}
}

// Verifies: GOOSE-PROV-014, GOOSE-INV-003.
// Depends-On: TestListSourcesSortsByVersion
func TestVersionsAgreeAfterUpTo(t *testing.T) {
	p, _ := newProvider(t, basicMigrations)
	if _, err := p.UpTo(context.Background(), 2); err != nil {
		t.Fatal(err)
	}
	current, target, err := p.GetVersions(context.Background())
	if err != nil || current != 2 || target != 3 {
		t.Fatalf("got (%d, %d, %v)", current, target, err)
	}
	dbVersion, err := p.GetDBVersion(context.Background())
	if err != nil || dbVersion != current {
		t.Fatalf("database version got (%d, %v)", dbVersion, err)
	}
}

// Verifies: GOOSE-PROV-015, GOOSE-INV-003.
// Depends-On: TestProviderCloseStopsPing, TestProviderPing
func TestCommittedStateSurvivesCloseAndReopen(t *testing.T) {
	path := filepath.Join(t.TempDir(), "reopen.db")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	p, err := goose.NewProvider(goose.DialectSQLite3, db, basicMigrations)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := p.UpTo(context.Background(), 2); err != nil {
		t.Fatal(err)
	}
	if err := p.Close(); err != nil {
		t.Fatal(err)
	}
	reopened, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = reopened.Close() })
	p2, err := goose.NewProvider(goose.DialectSQLite3, reopened, basicMigrations)
	if err != nil {
		t.Fatal(err)
	}
	version, err := p2.GetDBVersion(context.Background())
	if err != nil || version != 2 || !tableExists(t, reopened, "users") {
		t.Fatalf("reopened state got version (%d, %v)", version, err)
	}
}

// Verifies: GOOSE-PROV-003, GOOSE-INV-008.
// Depends-On: TestExcludeNameRemovesSource, TestExcludeVersionRemovesSource
func TestExclusionChangesEveryProjection(t *testing.T) {
	p, _ := newProvider(t, basicMigrations, excludeVersionsOption(t, []int64{2}))
	if len(p.ListSources()) != 2 {
		t.Fatal("excluded source remained listed")
	}
	status, err := p.Status(context.Background())
	if err != nil || len(status) != 2 {
		t.Fatalf("status got (%#v, %v)", status, err)
	}
	results, err := p.Up(context.Background())
	if err != nil || len(results) != 2 || results[0].Source.Version != 1 || results[1].Source.Version != 3 {
		t.Fatalf("results got (%#v, %v)", results, err)
	}
	pending, err := p.HasPending(context.Background())
	if err != nil || pending {
		t.Fatalf("pending got (%v, %v)", pending, err)
	}
}

// Verifies: GOOSE-PROV-004, GOOSE-PROV-012, GOOSE-INV-009.
// Depends-On: TestCollectMigrationsSortsSources
func TestOutOfOrderOptionAppliesMissingBeforeNew(t *testing.T) {
	initial := fstest.MapFS{
		"001_users.sql": basicMigrations["001_users.sql"],
		"003_posts.sql": basicMigrations["003_posts.sql"],
	}
	p, db := newProvider(t, initial)
	if _, err := p.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	expanded := fstest.MapFS{
		"001_users.sql":    basicMigrations["001_users.sql"],
		"002_names.sql":    basicMigrations["002_names.sql"],
		"003_posts.sql":    basicMigrations["003_posts.sql"],
		"004_comments.sql": {Data: []byte("-- +goose Up\nCREATE TABLE comments(id INTEGER PRIMARY KEY);\n-- +goose Down\nDROP TABLE comments;")},
	}
	strict, err := goose.NewProvider(goose.DialectSQLite3, db, expanded)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := strict.HasPending(context.Background()); err == nil {
		t.Fatal("expected strict out-of-order error")
	}
	allowed, err := goose.NewProvider(goose.DialectSQLite3, db, expanded, goose.WithAllowOutofOrder(true))
	if err != nil {
		t.Fatal(err)
	}
	results, err := allowed.Up(context.Background())
	if err != nil || len(results) != 2 || results[0].Source.Version != 2 || results[1].Source.Version != 4 {
		t.Fatalf("got (%#v, %v)", results, err)
	}
}

// Verifies: GOOSE-SQL-003, GOOSE-INV-005.
// Depends-On: TestListSourcesReportsSQLMetadata
func TestNoTransactionFailureKeepsDatabaseEffectWithoutVersion(t *testing.T) {
	fsys := fstest.MapFS{"001_bad.sql": {Data: []byte("-- +goose NO TRANSACTION\n-- +goose Up\nCREATE TABLE survives(id INTEGER);\nINSERT INTO missing_table VALUES (1);")}}
	p, db := newProvider(t, fsys)
	if _, err := p.Up(context.Background()); err == nil {
		t.Fatal("expected an error")
	}
	if !tableExists(t, db, "survives") {
		t.Fatal("non-transactional effect was rolled back")
	}
	version, err := p.GetDBVersion(context.Background())
	if err != nil || version != 0 {
		t.Fatalf("got version (%d, %v)", version, err)
	}
}

// Verifies: GOOSE-SQL-004, GOOSE-INV-005.
// Depends-On: TestListSourcesReportsSQLMetadata
func TestMissingRequiredEnvironmentVariableLeavesVersionPending(t *testing.T) {
	const key = "GOOSE_ORACLE_MISSING"
	previous, existed := os.LookupEnv(key)
	_ = os.Unsetenv(key)
	t.Cleanup(func() {
		if existed {
			_ = os.Setenv(key, previous)
		} else {
			_ = os.Unsetenv(key)
		}
	})
	sqlText := "-- +goose Up\n-- +goose ENVSUB ON\nCREATE TABLE ${GOOSE_ORACLE_MISSING?required}(id INTEGER);\n-- +goose ENVSUB OFF"
	p, _ := newProvider(t, fstest.MapFS{"001_env.sql": {Data: []byte(sqlText)}})
	if _, err := p.Up(context.Background()); err == nil {
		t.Fatal("expected an error")
	}
	version, err := p.GetDBVersion(context.Background())
	if err != nil || version != 0 {
		t.Fatalf("got version (%d, %v)", version, err)
	}
}
