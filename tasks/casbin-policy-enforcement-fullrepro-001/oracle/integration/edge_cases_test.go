package integration_test

import (
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	casbin "github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
	fileadapter "github.com/casbin/casbin/v3/persist/file-adapter"
	stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)

// Verifies: CAS-ENF-002, CAS-ENF-011
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS046BatchInvalidRequestErrors(t *testing.T) {
	e := newE(t, aclModel)
	addP(t, e, "alice", "data1", "read")
	if _, err := e.BatchEnforce([][]interface{}{{"alice", "data1", "read"}, {"too", "short"}}); err == nil {
		t.Fatal("invalid batch request accepted")
	}
}

// Verifies: CAS-ENF-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS047BooleanMatcherShortCircuits(t *testing.T) {
	text := `[request_definition]
r = bypass, obj
[policy_definition]
p = marker
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.bypass == true || r.obj.Missing == p.marker`
	e := newE(t, text)
	addP(t, e, "x")
	ok, err := e.Enforce(true, map[string]interface{}{})
	if err != nil || !ok {
		t.Fatalf("short circuit: %v %v", ok, err)
	}
}

// Verifies: CAS-ENF-003
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS048MapNumericComparison(t *testing.T) {
	text := `[request_definition]
r = sub
[policy_definition]
p = marker
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub.Age >= 18`
	e := newE(t, text)
	addP(t, e, "adult")
	ok, err := e.Enforce(map[string]interface{}{"Age": 21})
	if err != nil || !ok {
		t.Fatalf("adult: %v %v", ok, err)
	}
	ok, err = e.Enforce(map[string]interface{}{"Age": 17})
	if err != nil || ok {
		t.Fatalf("minor: %v %v", ok, err)
	}
}

// Verifies: CAS-POL-006
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS049AddPoliciesRepeatedInputRetainedOnce(t *testing.T) {
	e := newE(t, aclModel)
	r := []string{"alice", "data1", "read"}
	ok, err := e.AddPolicies([][]string{r, append([]string(nil), r...)})
	if err != nil || !ok {
		t.Fatalf("add: %v %v", ok, err)
	}
	p, _ := e.GetPolicy()
	if !reflect.DeepEqual(p, [][]string{r}) {
		t.Fatalf("policy=%v", p)
	}
}

// Verifies: CAS-MOD-004, CAS-POL-002, CAS-POL-010
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS050NamedMembershipAndFilter(t *testing.T) {
	text := `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
p2 = sub, obj, act
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`
	e := newE(t, text)
	if ok, err := e.AddNamedPolicy("p2", "alice", "data2", "write"); err != nil || !ok {
		t.Fatalf("add: %v %v", ok, err)
	}
	has, err := e.HasNamedPolicy("p2", []string{"alice", "data2", "write"})
	filtered, ferr := e.GetFilteredNamedPolicy("p2", 0, "alice", "", "write")
	if err != nil || ferr != nil || !has || !reflect.DeepEqual(filtered, [][]string{{"alice", "data2", "write"}}) {
		t.Fatalf("has=%v filtered=%v err=%v/%v", has, filtered, err, ferr)
	}
}

// Verifies: CAS-POL-009
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS051RemoveFilteredWildcard(t *testing.T) {
	e := newE(t, aclModel)
	for _, r := range [][]string{{"alice", "data1", "read"}, {"alice", "data2", "read"}, {"alice", "data3", "write"}} {
		addP(t, e, r...)
	}
	ok, err := e.RemoveFilteredPolicy(0, "alice", "", "read")
	if err != nil || !ok {
		t.Fatalf("remove: %v %v", ok, err)
	}
	p, _ := e.GetPolicy()
	if !reflect.DeepEqual(p, [][]string{{"alice", "data3", "write"}}) {
		t.Fatalf("policy=%v", p)
	}
}

// Verifies: CAS-RBAC-006, CAS-RBAC-007
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS052MultipleRolePathsDoNotDuplicatePermissions(t *testing.T) {
	e := newE(t, rbacModelForEdge)
	addP(t, e, "admin", "data", "read")
	for _, r := range [][]string{{"alice", "r1"}, {"alice", "r2"}, {"r1", "admin"}, {"r2", "admin"}} {
		if _, err := e.AddGroupingPolicy(r); err != nil {
			t.Fatal(err)
		}
	}
	perms, err := e.GetImplicitPermissionsForUser("alice")
	if err != nil || !reflect.DeepEqual(perms, [][]string{{"admin", "data", "read"}}) {
		t.Fatalf("permissions=%v err=%v", perms, err)
	}
}

const rbacModelForEdge = `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
[role_definition]
g = _, _
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act`

// Verifies: CAS-DOM-002, CAS-STA-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS053DomainRoleNoOpBooleans(t *testing.T) {
	e := newE(t, domainModel)
	ok, err := e.AddRoleForUserInDomain("alice", "admin", "tenant1")
	if err != nil || !ok {
		t.Fatalf("first add: %v %v", ok, err)
	}
	if ok, err = e.AddRoleForUserInDomain("alice", "admin", "tenant1"); err != nil || ok {
		t.Fatalf("duplicate add: %v %v", ok, err)
	}
	if ok, err = e.DeleteRoleForUserInDomain("alice", "admin", "tenant2"); err != nil || ok {
		t.Fatalf("missing delete: %v %v", ok, err)
	}
}

// Verifies: CAS-STR-002, CAS-INV-005
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS054StringRoundTripIncludesGroupingPolicy(t *testing.T) {
	a := stringadapter.NewAdapter("p, admin, data, read\ng, alice, admin")
	e := newE(t, rbacModelForEdge, a)
	if err := e.SavePolicy(); err != nil {
		t.Fatal(err)
	}
	fresh := newE(t, rbacModelForEdge, stringadapter.NewAdapter(a.Line))
	grouping, _ := fresh.GetGroupingPolicy()
	ok, err := fresh.Enforce("alice", "data", "read")
	if err != nil || !ok || !reflect.DeepEqual(grouping, [][]string{{"alice", "admin"}}) {
		t.Fatalf("grouping=%v enforce=%v err=%v line=%q", grouping, ok, err, a.Line)
	}
}

// Verifies: CAS-FIL-002
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS055FileSaveTruncatesOldContents(t *testing.T) {
	path := filepath.Join(t.TempDir(), "policy.csv")
	old := "p, alice, data1, read\np, stale, very-long-object-name, forbidden-action"
	if err := os.WriteFile(path, []byte(old), 0o600); err != nil {
		t.Fatal(err)
	}
	a := fileadapter.NewAdapter(path)
	e := newE(t, aclModel, a)
	e.EnableAutoSave(false)
	if ok, err := e.RemovePolicy("stale", "very-long-object-name", "forbidden-action"); err != nil || !ok {
		t.Fatalf("remove: %v %v", ok, err)
	}
	if err := e.SavePolicy(); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(path)
	if strings.Contains(string(b), "stale") || string(b) != "p, alice, data1, read" {
		t.Fatalf("file=%q", b)
	}
}

// Verifies: CAS-LOD-002, CAS-INV-004
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS056LoadPolicyReplacesRatherThanMerges(t *testing.T) {
	a := stringadapter.NewAdapter("p, alice, data1, read")
	e := newE(t, aclModel, a)
	e.EnableAutoSave(false)
	addP(t, e, "stale", "data9", "write")
	a.Line = "p, bob, data2, write"
	if err := e.LoadPolicy(); err != nil {
		t.Fatal(err)
	}
	p, _ := e.GetPolicy()
	if !reflect.DeepEqual(p, [][]string{{"bob", "data2", "write"}}) {
		t.Fatalf("policy=%v", p)
	}
}

// Verifies: CAS-FIL-001, CAS-ERR-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS057UnreadablePolicyPathErrors(t *testing.T) {
	m, _ := model.NewModelFromString(aclModel)
	a := fileadapter.NewAdapter(filepath.Join(t.TempDir(), "missing.csv"))
	if err := a.LoadPolicy(m); err == nil {
		t.Fatal("missing file loaded")
	}
}

// Verifies: CAS-STA-002
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS058DistinctEnforcersDoNotSharePolicy(t *testing.T) {
	a := newE(t, aclModel)
	b := newE(t, aclModel)
	addP(t, a, "alice", "data1", "read")
	if p, _ := b.GetPolicy(); len(p) != 0 {
		t.Fatalf("shared policy=%v", p)
	}
}

// Verifies: CAS-INV-006
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS059InvalidRequestDoesNotPoisonLaterRequest(t *testing.T) {
	e := newE(t, aclModel)
	addP(t, e, "alice", "data1", "read")
	if _, err := e.Enforce("too", "short"); err == nil {
		t.Fatal("invalid request accepted")
	}
	ok, err := e.Enforce("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("later request: %v %v", ok, err)
	}
}

// Verifies: CAS-LOD-001
// Depends-On: TestCAS005ACLAllowAndDeny
func TestCAS060ClearPolicyRemovesAuthorizationAndGroupingRows(t *testing.T) {
	e := newE(t, rbacModelForEdge)
	addP(t, e, "admin", "data", "read")
	if _, err := e.AddGroupingPolicy("alice", "admin"); err != nil {
		t.Fatal(err)
	}
	e.ClearPolicy()
	p, pe := e.GetPolicy()
	g, ge := e.GetGroupingPolicy()
	if pe != nil || ge != nil || len(p) != 0 || len(g) != 0 {
		t.Fatalf("policy=%v grouping=%v errors=%v/%v", p, g, pe, ge)
	}
}

var _ = casbin.NewEnforcer
