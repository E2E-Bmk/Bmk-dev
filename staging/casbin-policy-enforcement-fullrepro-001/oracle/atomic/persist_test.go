package atomic

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
	stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)

func TestStringAdapterLoadsRules(t *testing.T) {
	a := stringadapter.NewAdapter("p, cathy, data9, read")
	m, err := model.NewModelFromString(aclModel)
	if err != nil {
		t.Fatalf("model: %v", err)
	}
	e, err := casbin.NewEnforcer(m, a)
	if err != nil {
		t.Fatalf("NewEnforcer with adapter: %v", err)
	}
	mustEnforce(t, e, true, "cathy", "data9", "read")
	mustEnforce(t, e, false, "cathy", "data9", "write")
}

func TestSavePolicyWritesStringAdapter(t *testing.T) {
	a := stringadapter.NewAdapter("p, cathy, data9, read")
	m, _ := model.NewModelFromString(aclModel)
	e, _ := casbin.NewEnforcer(m, a)
	e.AddPolicy("dave", "data9", "write")
	if err := e.SavePolicy(); err != nil {
		t.Fatalf("SavePolicy: %v", err)
	}
	if !strings.Contains(a.Line, "p, cathy, data9, read") || !strings.Contains(a.Line, "p, dave, data9, write") {
		t.Fatalf("adapter text must hold both rules, got %q", a.Line)
	}
}

func TestLoadPolicyDiscardsUnsaved(t *testing.T) {
	a := stringadapter.NewAdapter("p, cathy, data9, read")
	m, _ := model.NewModelFromString(aclModel)
	e, _ := casbin.NewEnforcer(m, a)
	e.AddPolicy("ephemeral", "data", "read")
	if err := e.LoadPolicy(); err != nil {
		t.Fatalf("LoadPolicy: %v", err)
	}
	has, _ := e.HasPolicy("ephemeral", "data", "read")
	if has {
		t.Fatal("an unsaved rule must vanish after LoadPolicy")
	}
	mustEnforce(t, e, true, "cathy", "data9", "read")
}

func TestFileEnforcerConstruction(t *testing.T) {
	dir := t.TempDir()
	mpath := filepath.Join(dir, "model.conf")
	ppath := filepath.Join(dir, "policy.csv")
	if err := os.WriteFile(mpath, []byte(aclModel), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(ppath, []byte("p, alice, data1, read\np, bob, data2, write\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	e, err := casbin.NewEnforcer(mpath, ppath)
	if err != nil {
		t.Fatalf("NewEnforcer(files): %v", err)
	}
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, true, "bob", "data2", "write")
	mustEnforce(t, e, false, "alice", "data2", "write")
}

func TestModelOnlyEnforcerStartsEmpty(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	pol, err := e.GetPolicy()
	if err != nil {
		t.Fatalf("GetPolicy: %v", err)
	}
	if len(pol) != 0 {
		t.Fatalf("a model-only enforcer must start with an empty store, got %v", pol)
	}
	mustEnforce(t, e, false, "anyone", "anything", "anyhow")
}
