// Spec2Repo oracle - CLI integration tests for goose-sqlite-migrations-fullrepro-001.
package integration

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"testing"

	"github.com/pressly/goose/v3"
	_ "modernc.org/sqlite"
)

var (
	cliBuildOnce    sync.Once
	gooseExecutable string
	cliBuildOutput  []byte
	cliBuildErr     error
)

func ensureCLI(t *testing.T) string {
	t.Helper()
	cliBuildOnce.Do(func() {
		buildDir, err := os.MkdirTemp("", "goose-cli-oracle-")
		if err != nil {
			cliBuildErr = fmt.Errorf("create CLI build directory: %w", err)
			return
		}
		name := "goose"
		if runtime.GOOS == "windows" {
			name += ".exe"
		}
		gooseExecutable = filepath.Join(buildDir, name)
		build := exec.Command("go", "build", "-o", gooseExecutable, "github.com/pressly/goose/v3/cmd/goose")
		cliBuildOutput, cliBuildErr = build.CombinedOutput()
	})
	if cliBuildErr != nil {
		t.Fatalf("build goose CLI: %v\n%s", cliBuildErr, cliBuildOutput)
	}
	return gooseExecutable
}

func cleanCLIEnv(overrides map[string]string) []string {
	blocked := map[string]bool{
		"GOOSE_DRIVER": true, "GOOSE_DBSTRING": true, "GOOSE_MIGRATION_DIR": true,
		"GOOSE_TABLE": true, "GOOSE_ENV": true,
	}
	env := make([]string, 0, len(os.Environ())+len(overrides)+1)
	for _, item := range os.Environ() {
		key, _, _ := strings.Cut(item, "=")
		if !blocked[strings.ToUpper(key)] && !strings.EqualFold(key, "NO_COLOR") {
			env = append(env, item)
		}
	}
	env = append(env, "NO_COLOR=1")
	for key, value := range overrides {
		env = append(env, key+"="+value)
	}
	return env
}

func runCLI(t *testing.T, overrides map[string]string, args ...string) (string, int) {
	t.Helper()
	cmd := exec.Command(ensureCLI(t), args...)
	cmd.Env = cleanCLIEnv(overrides)
	output, err := cmd.CombinedOutput()
	if err == nil {
		return string(output), 0
	}
	var exitErr *exec.ExitError
	if errors.As(err, &exitErr) {
		return string(output), exitErr.ExitCode()
	}
	t.Fatalf("execute goose CLI: %v", err)
	return "", -1
}

func writeMigration(t *testing.T, dir, name, body string) {
	t.Helper()
	if err := os.WriteFile(filepath.Join(dir, name), []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
}

func workflowMigrations(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	writeMigration(t, dir, "001_widgets.sql", "-- +goose Up\nCREATE TABLE widgets(id INTEGER PRIMARY KEY, name TEXT);\nINSERT INTO widgets(name) VALUES ('first');\n-- +goose Down\nDROP TABLE widgets;\n")
	writeMigration(t, dir, "002_audit.sql", "-- +goose Up\nCREATE TABLE audit(id INTEGER PRIMARY KEY);\n-- +goose Down\nDROP TABLE audit;\n")
	return dir
}

func openFileDB(t *testing.T, path string) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	return db
}

func requireTable(t *testing.T, db *sql.DB, name string, want bool) {
	t.Helper()
	var count int
	if err := db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", name).Scan(&count); err != nil {
		t.Fatal(err)
	}
	if got := count == 1; got != want {
		t.Fatalf("table %q exists=%v, want %v", name, got, want)
	}
}

// Verifies: GOOSE-CLI-003.
// Depends-On: TestProviderPing
func TestCLIHelpExitsSuccessfully(t *testing.T) {
	output, code := runCLI(t, nil, "-h")
	if code != 0 {
		t.Fatalf("help exit code=%d, output=%q", code, output)
	}
	lower := strings.ToLower(output)
	if !strings.Contains(lower, "usage") || !strings.Contains(lower, "goose") {
		t.Fatalf("help lacks expected public anchors: %q", output)
	}
}

// Verifies: GOOSE-CLI-003.
// Depends-On: TestProviderPing
func TestCLIVersionExitsSuccessfully(t *testing.T) {
	output, code := runCLI(t, nil, "-version")
	if code != 0 {
		t.Fatalf("version exit code=%d, output=%q", code, output)
	}
	if !strings.Contains(strings.ToLower(output), "goose") {
		t.Fatalf("version output lacks executable name: %q", output)
	}
}

// Verifies: GOOSE-CLI-002, GOOSE-CLI-008.
// Depends-On: TestProviderPing
func TestCLIUnknownCommandExitsNonZero(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "unknown.db")
	output, code := runCLI(t, nil, "sqlite3", dbPath, "not-a-goose-command")
	if code == 0 {
		t.Fatalf("unknown command unexpectedly succeeded: %q", output)
	}
}

// Verifies: GOOSE-RUN-001, GOOSE-CLI-003, GOOSE-INV-001, GOOSE-INV-005, GOOSE-INV-006.
// Depends-On: TestListSourcesSortsByVersion, TestProviderPing
func TestCLIUpIsVisibleThroughLibraryProvider(t *testing.T) {
	dir := workflowMigrations(t)
	dbPath := filepath.Join(t.TempDir(), "cli-up.db")
	output, code := runCLI(t, nil, "-dir", dir, "sqlite3", dbPath, "up")
	if code != 0 {
		t.Fatalf("CLI up exit code=%d, output=%q", code, output)
	}

	db := openFileDB(t, dbPath)
	provider, err := goose.NewProvider(goose.DialectSQLite3, db, os.DirFS(dir))
	if err != nil {
		t.Fatal(err)
	}
	statuses, err := provider.Status(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	version, err := provider.GetDBVersion(context.Background())
	if err != nil || version != 2 || len(statuses) != 2 || statuses[0].State != goose.StateApplied || statuses[1].State != goose.StateApplied {
		t.Fatalf("library projection after CLI up: version=%d statuses=%#v err=%v", version, statuses, err)
	}
	requireTable(t, db, "widgets", true)
	requireTable(t, db, "audit", true)
}

// Verifies: GOOSE-RUN-001, GOOSE-CLI-003, GOOSE-INV-004, GOOSE-INV-006.
// Depends-On: TestListSourcesSortsByVersion, TestProviderPing
func TestLibraryUpIsVisibleThroughCLIStatusAndVersion(t *testing.T) {
	dir := workflowMigrations(t)
	dbPath := filepath.Join(t.TempDir(), "library-up.db")
	db := openFileDB(t, dbPath)
	provider, err := goose.NewProvider(goose.DialectSQLite3, db, os.DirFS(dir))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := provider.Up(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}

	statusOutput, statusCode := runCLI(t, nil, "-dir", dir, "sqlite3", dbPath, "status")
	if statusCode != 0 {
		t.Fatalf("CLI status exit code=%d, output=%q", statusCode, statusOutput)
	}
	statusLower := strings.ToLower(statusOutput)
	if !strings.Contains(statusLower, "001_widgets.sql") || !strings.Contains(statusLower, "002_audit.sql") || !strings.Contains(statusLower, "applied") {
		t.Fatalf("CLI status lacks applied source anchors: %q", statusOutput)
	}
	versionOutput, versionCode := runCLI(t, nil, "-dir", dir, "sqlite3", dbPath, "version")
	if versionCode != 0 || !strings.Contains(versionOutput, "2") {
		t.Fatalf("CLI version projection: code=%d output=%q", versionCode, versionOutput)
	}
}

// Verifies: GOOSE-CLI-001, GOOSE-CLI-005, GOOSE-INV-005.
// Depends-On: TestProviderPing
func TestCLIUsesEnvironmentConfiguration(t *testing.T) {
	dir := workflowMigrations(t)
	dbPath := filepath.Join(t.TempDir(), "environment.db")
	env := map[string]string{
		"GOOSE_DRIVER": "sqlite3", "GOOSE_DBSTRING": dbPath,
		"GOOSE_MIGRATION_DIR": dir, "GOOSE_TABLE": "environment_history",
	}
	output, code := runCLI(t, env, "up")
	if code != 0 {
		t.Fatalf("environment-configured up exit code=%d, output=%q", code, output)
	}
	db := openFileDB(t, dbPath)
	requireTable(t, db, "widgets", true)
	requireTable(t, db, "environment_history", true)
	requireTable(t, db, goose.DefaultTablename, false)
}

// Verifies: GOOSE-FILE-003, GOOSE-FILE-004, GOOSE-CLI-003.
// Depends-On: TestCreateSequentialSQL
func TestCLICreateSequentialSQLFile(t *testing.T) {
	dir := t.TempDir()
	output, code := runCLI(t, nil, "-s", "-dir", dir, "create", "add widgets", "sql")
	if code != 0 {
		t.Fatalf("CLI create exit code=%d, output=%q", code, output)
	}
	matches, err := filepath.Glob(filepath.Join(dir, "00001_add_widgets.sql"))
	if err != nil || len(matches) != 1 {
		t.Fatalf("created files=%#v, err=%v", matches, err)
	}
	data, err := os.ReadFile(matches[0])
	if err != nil || len(data) == 0 {
		t.Fatalf("created migration is missing or empty: %v", err)
	}
}

// Verifies: GOOSE-CLI-002, GOOSE-CLI-003, GOOSE-CLI-007, GOOSE-CLI-008.
// Depends-On: TestCollectMigrationsSortsSources, TestCollectMigrationsRejectsDuplicateVersion
func TestCLIValidateAcceptsValidAndRejectsInvalidWithoutMutation(t *testing.T) {
	dir := t.TempDir()
	valid := []byte("-- +goose Up\nCREATE TABLE valid_table(id INTEGER);\n-- +goose Down\nDROP TABLE valid_table;\n")
	validPath := filepath.Join(dir, "001_valid.sql")
	if err := os.WriteFile(validPath, valid, 0o600); err != nil {
		t.Fatal(err)
	}
	output, code := runCLI(t, nil, "-dir", dir, "validate")
	if code != 0 {
		t.Fatalf("valid migration rejected: code=%d output=%q", code, output)
	}
	afterValid, err := os.ReadFile(validPath)
	if err != nil || string(afterValid) != string(valid) {
		t.Fatalf("validation changed valid source: %v", err)
	}

	invalid := []byte("CREATE TABLE missing_directive(id INTEGER);\n")
	invalidPath := filepath.Join(dir, "002_invalid.sql")
	if err := os.WriteFile(invalidPath, invalid, 0o600); err != nil {
		t.Fatal(err)
	}
	output, code = runCLI(t, nil, "-dir", dir, "validate")
	if code == 0 {
		t.Fatalf("invalid migration unexpectedly validated: %q", output)
	}
	afterInvalid, err := os.ReadFile(invalidPath)
	if err != nil || string(afterInvalid) != string(invalid) {
		t.Fatalf("validation changed invalid source: %v", err)
	}
}
