package integration_test

import (
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"sync"
	"testing"

	casbin "github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
	fileadapter "github.com/casbin/casbin/v3/persist/file-adapter"
	stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)

const aclModel = `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`

const domainModel = `[request_definition]
r = sub, dom, obj, act
[policy_definition]
p = sub, dom, obj, act
[role_definition]
g = _, _, _
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && r.obj == p.obj && r.act == p.act`

func newE(t *testing.T, text string, adapter ...interface{}) *casbin.Enforcer {
	t.Helper()
	m, err := model.NewModelFromString(text)
	if err != nil {
		t.Fatal(err)
	}
	args := []interface{}{m}
	args = append(args, adapter...)
	e, err := casbin.NewEnforcer(args...)
	if err != nil {
		t.Fatal(err)
	}
	return e
}

func addP(t *testing.T, e *casbin.Enforcer, r ...string) {
	t.Helper()
	ok, err := e.AddPolicy(r)
	if err != nil || !ok {
		t.Fatalf("add %v: %v %v", r, ok, err)
	}
}

func rows(in [][]string) []string {
	out := make([]string, len(in))
	for i := range in {
		out[i] = strings.Join(in[i], "\x00")
	}
	sort.Strings(out)
	return out
}

func strs(in []string) []string {
	out := append([]string(nil), in...)
	sort.Strings(out)
	return out
}

// Verifies: CAS-DOM-001, CAS-DOM-002, CAS-INV-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS031DomainRoleEnforcementIsolation(t *testing.T) {
	e := newE(t, domainModel)
	addP(t, e, "admin", "tenant1", "data", "read")
	ok, err := e.AddRoleForUserInDomain("alice", "admin", "tenant1")
	if err != nil || !ok {
		t.Fatalf("role: %v %v", ok, err)
	}
	allowed, err := e.Enforce("alice", "tenant1", "data", "read")
	if err != nil || !allowed {
		t.Fatalf("tenant1: %v %v", allowed, err)
	}
	allowed, err = e.Enforce("alice", "tenant2", "data", "read")
	if err != nil || allowed {
		t.Fatalf("tenant2 leaked: %v %v", allowed, err)
	}
	ok, err = e.DeleteRoleForUserInDomain("alice", "admin", "tenant1")
	if err != nil || !ok {
		t.Fatalf("delete: %v %v", ok, err)
	}
}

// Verifies: CAS-DOM-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS032DomainDirectRoleProjections(t *testing.T) {
	e := newE(t, domainModel)
	for _, r := range [][]string{{"alice", "admin", "tenant1"}, {"bob", "admin", "tenant2"}, {"carol", "editor", "tenant1"}} {
		if _, err := e.AddGroupingPolicy(r); err != nil {
			t.Fatal(err)
		}
	}
	if got := e.GetRolesForUserInDomain("alice", "tenant1"); !reflect.DeepEqual(got, []string{"admin"}) {
		t.Fatalf("roles=%v", got)
	}
	if got := e.GetRolesForUserInDomain("alice", "tenant2"); len(got) != 0 {
		t.Fatalf("cross-domain roles=%v", got)
	}
	if got := e.GetUsersForRoleInDomain("admin", "tenant1"); !reflect.DeepEqual(got, []string{"alice"}) {
		t.Fatalf("users=%v", got)
	}
}

// Verifies: CAS-DOM-004
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS033DomainPermissionProjection(t *testing.T) {
	e := newE(t, domainModel)
	addP(t, e, "admin", "tenant1", "data1", "read")
	addP(t, e, "admin", "tenant2", "data2", "write")
	addP(t, e, "alice", "tenant1", "self", "read")
	if _, err := e.AddRoleForUserInDomain("alice", "admin", "tenant1"); err != nil {
		t.Fatal(err)
	}
	got := e.GetPermissionsForUserInDomain("alice", "tenant1")
	want := [][]string{{"admin", "tenant1", "data1", "read"}, {"alice", "tenant1", "self", "read"}}
	if !reflect.DeepEqual(rows(got), rows(want)) {
		t.Fatalf("permissions=%v", got)
	}
}

// Verifies: CAS-DOM-005
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS034AllUsersByDomain(t *testing.T) {
	e := newE(t, domainModel)
	addP(t, e, "bob", "tenant1", "data", "read")
	addP(t, e, "admin", "tenant1", "data", "write")
	if _, err := e.AddRoleForUserInDomain("alice", "admin", "tenant1"); err != nil {
		t.Fatal(err)
	}
	got, err := e.GetAllUsersByDomain("tenant1")
	if err != nil || !reflect.DeepEqual(strs(got), []string{"admin", "alice", "bob"}) {
		t.Fatalf("users=%v err=%v", got, err)
	}
}

// Verifies: CAS-NEW-002, CAS-STR-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS035StringAdapterLoadsAtConstruction(t *testing.T) {
	a := stringadapter.NewAdapter("p, alice, data1, read\n\np, bob, data2, write")
	e := newE(t, aclModel, a)
	if a.Line == "" {
		t.Fatal("Line not retained")
	}
	for _, req := range [][]interface{}{{"alice", "data1", "read"}, {"bob", "data2", "write"}} {
		ok, err := e.Enforce(req...)
		if err != nil || !ok {
			t.Fatalf("%v: %v %v", req, ok, err)
		}
	}
}

// Verifies: CAS-STR-001, CAS-ERR-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS036EmptyStringAdapterErrors(t *testing.T) {
	m, _ := model.NewModelFromString(aclModel)
	a := stringadapter.NewAdapter("")
	if err := a.LoadPolicy(m); err == nil {
		t.Fatal("empty Line loaded")
	}
}

// Verifies: CAS-STR-002, CAS-LOD-003, CAS-LOD-004, CAS-INV-005
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS037StringSaveLoadRoundTrip(t *testing.T) {
	a := stringadapter.NewAdapter("p, alice, data1, read")
	e := newE(t, aclModel, a)
	e.EnableAutoSave(false)
	addP(t, e, "bob", "data2", "write")
	if err := e.SavePolicy(); err != nil {
		t.Fatal(err)
	}
	fresh := newE(t, aclModel, stringadapter.NewAdapter(a.Line))
	want, _ := e.GetPolicy()
	got, _ := fresh.GetPolicy()
	if !reflect.DeepEqual(rows(got), rows(want)) {
		t.Fatalf("got=%v want=%v line=%q", got, want, a.Line)
	}
}

// Verifies: CAS-STR-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS038StringAdapterUnsupportedMutations(t *testing.T) {
	a := stringadapter.NewAdapter("p, alice, data1, read")
	if err := a.AddPolicy("p", "p", []string{"bob", "data2", "write"}); err == nil {
		t.Fatal("incremental add succeeded")
	}
	if err := a.RemoveFilteredPolicy("p", "p", 0, "alice"); err == nil {
		t.Fatal("filtered remove succeeded")
	}
	if err := a.RemovePolicy("p", "p", []string{"alice", "data1", "read"}); err != nil || a.Line != "" {
		t.Fatalf("remove: line=%q err=%v", a.Line, err)
	}
}

// Verifies: CAS-FIL-001, CAS-NEW-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS039FilePathConstruction(t *testing.T) {
	d := t.TempDir()
	modelPath := filepath.Join(d, "model.conf")
	policyPath := filepath.Join(d, "policy.csv")
	if err := os.WriteFile(modelPath, []byte(aclModel), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(policyPath, []byte("p, alice, data1, read\n\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	e, err := casbin.NewEnforcer(modelPath, policyPath)
	if err != nil {
		t.Fatal(err)
	}
	ok, err := e.Enforce("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("enforce=%v err=%v", ok, err)
	}
}

// Verifies: CAS-FIL-002, CAS-LOD-003, CAS-INV-005
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS040FileSaveLoadRoundTrip(t *testing.T) {
	path := filepath.Join(t.TempDir(), "policy.csv")
	if err := os.WriteFile(path, []byte("p, alice, data1, read"), 0o600); err != nil {
		t.Fatal(err)
	}
	a := fileadapter.NewAdapter(path)
	e := newE(t, aclModel, a)
	e.EnableAutoSave(false)
	addP(t, e, "bob", "data2", "write")
	if err := e.SavePolicy(); err != nil {
		t.Fatal(err)
	}
	fresh := newE(t, aclModel, fileadapter.NewAdapter(path))
	want, _ := e.GetPolicy()
	got, _ := fresh.GetPolicy()
	if !reflect.DeepEqual(rows(got), rows(want)) {
		t.Fatalf("got=%v want=%v", got, want)
	}
}

// Verifies: CAS-FIL-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS041FileAdapterUnsupportedMutations(t *testing.T) {
	path := filepath.Join(t.TempDir(), "policy.csv")
	original := []byte("p, alice, data1, read")
	if err := os.WriteFile(path, original, 0o600); err != nil {
		t.Fatal(err)
	}
	a := fileadapter.NewAdapter(path)
	if err := a.AddPolicy("p", "p", []string{"bob", "data2", "write"}); err == nil {
		t.Fatal("add succeeded")
	}
	if err := a.RemovePolicy("p", "p", []string{"alice", "data1", "read"}); err == nil {
		t.Fatal("remove succeeded")
	}
	if err := a.RemoveFilteredPolicy("p", "p", 0, "alice"); err == nil {
		t.Fatal("filtered remove succeeded")
	}
	got, _ := os.ReadFile(path)
	if !reflect.DeepEqual(got, original) {
		t.Fatalf("file changed: %q", got)
	}
}

// Verifies: CAS-LOD-001, CAS-LOD-002, CAS-INV-004
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS042ClearThenReloadUsesAdapter(t *testing.T) {
	a := stringadapter.NewAdapter("p, alice, data1, read")
	e := newE(t, aclModel, a)
	e.ClearPolicy()
	if p, _ := e.GetPolicy(); len(p) != 0 {
		t.Fatalf("clear=%v", p)
	}
	if err := e.LoadPolicy(); err != nil {
		t.Fatal(err)
	}
	if ok, err := e.Enforce("alice", "data1", "read"); err != nil || !ok {
		t.Fatalf("reload=%v %v", ok, err)
	}
}

// Verifies: CAS-FIL-001, CAS-ERR-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS043EmptyFileAdapterErrors(t *testing.T) {
	m, _ := model.NewModelFromString(aclModel)
	a := fileadapter.NewAdapter("")
	if err := a.LoadPolicy(m); err == nil {
		t.Fatal("empty-path load succeeded")
	}
	if err := a.SavePolicy(m); err == nil {
		t.Fatal("empty-path save succeeded")
	}
}

// Verifies: CAS-NEW-004, CAS-ERR-002
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS044ConstructorFailuresReturnErrors(t *testing.T) {
	if e, err := casbin.NewEnforcer(42, "policy.csv"); err == nil || e != nil {
		t.Fatalf("unsupported inputs: e=%v err=%v", e, err)
	}
	missing := filepath.Join(t.TempDir(), "missing.conf")
	if e, err := casbin.NewEnforcer(missing); err == nil || e != nil {
		t.Fatalf("missing model: e=%v err=%v", e, err)
	}
}

// Verifies: CAS-CON-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS045ConcurrentReadOnlyEnforcement(t *testing.T) {
	e := newE(t, aclModel)
	addP(t, e, "alice", "data1", "read")
	var wg sync.WaitGroup
	errCh := make(chan string, 32)
	for i := 0; i < 32; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 50; j++ {
				ok, err := e.Enforce("alice", "data1", "read")
				if err != nil || !ok {
					errCh <- "allowed request changed"
					return
				}
				ok, err = e.Enforce("bob", "data1", "read")
				if err != nil || ok {
					errCh <- "denied request changed"
					return
				}
			}
		}()
	}
	wg.Wait()
	close(errCh)
	for msg := range errCh {
		t.Fatal(msg)
	}
}
