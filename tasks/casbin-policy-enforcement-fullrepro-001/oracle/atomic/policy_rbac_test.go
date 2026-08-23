package atomic_test

import (
	"reflect"
	"sort"
	"strings"
	"testing"
)

func sortedStrings(in []string) []string {
	out := append([]string(nil), in...)
	sort.Strings(out)
	return out
}

func sortedRows(in [][]string) []string {
	out := make([]string, len(in))
	for i := range in {
		out[i] = strings.Join(in[i], "\x00")
	}
	sort.Strings(out)
	return out
}

// Verifies: CAS-POL-003, CAS-POL-004, CAS-POL-005
func TestCAS016VariadicPolicyShapesAndDuplicates(t *testing.T) {
	e := mustEnforcer(t, aclText)
	ok, err := e.AddPolicy("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("fields: %v %v", ok, err)
	}
	ok, err = e.AddPolicy([]string{"alice", "data1", "read"})
	if err != nil || ok {
		t.Fatalf("duplicate slice: %v %v", ok, err)
	}
	has, err := e.HasPolicy([]string{"alice", "data1", "read"})
	if err != nil || !has {
		t.Fatalf("has: %v %v", has, err)
	}
	ok, err = e.RemovePolicy("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("remove: %v %v", ok, err)
	}
	ok, err = e.RemovePolicy([]string{"alice", "data1", "read"})
	if err != nil || ok {
		t.Fatalf("remove absent: %v %v", ok, err)
	}
}

// Verifies: CAS-POL-001
func TestCAS017DefaultAndNamedPolicyAgree(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	a, ea := e.GetPolicy()
	b, eb := e.GetNamedPolicy("p")
	if ea != nil || eb != nil || !reflect.DeepEqual(a, b) {
		t.Fatalf("a=%v/%v b=%v/%v", a, ea, b, eb)
	}
}

// Verifies: CAS-POL-002
func TestCAS018FilteredPolicyAndWildcards(t *testing.T) {
	e := mustEnforcer(t, aclText)
	for _, r := range [][]string{{"alice", "data1", "read"}, {"alice", "data2", "write"}, {"bob", "data1", "write"}} {
		add(t, e, r...)
	}
	got, err := e.GetFilteredPolicy(0, "alice", "", "write")
	if err != nil || !reflect.DeepEqual(got, [][]string{{"alice", "data2", "write"}}) {
		t.Fatalf("got=%v err=%v", got, err)
	}
}

// Verifies: CAS-POL-006
func TestCAS019AddPoliciesStoredDuplicateIsAtomic(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	ok, err := e.AddPolicies([][]string{{"bob", "data2", "read"}, {"alice", "data1", "read"}})
	if err != nil || ok {
		t.Fatalf("ok=%v err=%v", ok, err)
	}
	has, _ := e.HasPolicy("bob", "data2", "read")
	if has {
		t.Fatal("partial batch addition")
	}
}

// Verifies: CAS-POL-007
func TestCAS020AddPoliciesExSkipsDuplicates(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	_, err := e.AddPoliciesEx([][]string{{"alice", "data1", "read"}, {"bob", "data2", "write"}, {"bob", "data2", "write"}})
	if err != nil {
		t.Fatal(err)
	}
	p, _ := e.GetPolicy()
	if !reflect.DeepEqual(sortedRows(p), sortedRows([][]string{{"alice", "data1", "read"}, {"bob", "data2", "write"}})) {
		t.Fatalf("policy=%v", p)
	}
}

// Verifies: CAS-POL-008
func TestCAS021UpdatePolicyExistingAndAbsent(t *testing.T) {
	e := mustEnforcer(t, aclText)
	old := []string{"alice", "data1", "read"}
	newRule := []string{"alice", "data1", "write"}
	add(t, e, old...)
	ok, err := e.UpdatePolicy(old, newRule)
	if err != nil || !ok {
		t.Fatalf("update: %v %v", ok, err)
	}
	ok, err = e.UpdatePolicy([]string{"missing", "x", "x"}, old)
	if err != nil || ok {
		t.Fatalf("missing: %v %v", ok, err)
	}
	has, _ := e.HasPolicy(newRule)
	if !has {
		t.Fatal("replacement missing")
	}
}

// Verifies: CAS-POL-009
func TestCAS022RemoveFilteredPolicy(t *testing.T) {
	e := mustEnforcer(t, aclText)
	for _, r := range [][]string{{"alice", "data1", "read"}, {"alice", "data2", "write"}, {"bob", "data1", "read"}} {
		add(t, e, r...)
	}
	ok, err := e.RemoveFilteredPolicy(0, "alice")
	if err != nil || !ok {
		t.Fatalf("remove: %v %v", ok, err)
	}
	p, _ := e.GetPolicy()
	if !reflect.DeepEqual(p, [][]string{{"bob", "data1", "read"}}) {
		t.Fatalf("remaining=%v", p)
	}
}

// Verifies: CAS-MOD-004, CAS-POL-010
func TestCAS023NamedPolicyIsolation(t *testing.T) {
	text := `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
p2 = sub, obj, act
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`
	e := mustEnforcer(t, text)
	ok, err := e.AddNamedPolicy("p2", "bob", "data2", "write")
	if err != nil || !ok {
		t.Fatalf("add named: %v %v", ok, err)
	}
	defaultP, _ := e.GetPolicy()
	named, err := e.GetNamedPolicy("p2")
	if err != nil || len(defaultP) != 0 || !reflect.DeepEqual(named, [][]string{{"bob", "data2", "write"}}) {
		t.Fatalf("default=%v named=%v err=%v", defaultP, named, err)
	}
}

// Verifies: CAS-RBAC-001, CAS-RBAC-004
func TestCAS024GroupingPolicyChangedSemantics(t *testing.T) {
	e := mustEnforcer(t, rbacText)
	ok, err := e.AddGroupingPolicy("alice", "admin")
	if err != nil || !ok {
		t.Fatalf("add: %v %v", ok, err)
	}
	ok, err = e.AddGroupingPolicy([]string{"alice", "admin"})
	if err != nil || ok {
		t.Fatalf("duplicate: %v %v", ok, err)
	}
	has, _ := e.HasGroupingPolicy("alice", "admin")
	if !has {
		t.Fatal("grouping membership missing")
	}
	ok, err = e.RemoveGroupingPolicy("alice", "admin")
	if err != nil || !ok {
		t.Fatalf("remove: %v %v", ok, err)
	}
}

// Verifies: CAS-RBAC-002, CAS-RBAC-003
func TestCAS025DirectAndTransitiveRoles(t *testing.T) {
	e := mustEnforcer(t, rbacText)
	for _, r := range [][]string{{"alice", "editor"}, {"editor", "admin"}} {
		if ok, err := e.AddGroupingPolicy(r); err != nil || !ok {
			t.Fatalf("%v: %v %v", r, ok, err)
		}
	}
	roles, _ := e.GetRolesForUser("alice")
	users, _ := e.GetUsersForRole("editor")
	direct, err := e.HasRoleForUser("alice", "editor")
	transitive, err2 := e.HasRoleForUser("alice", "admin")
	if !reflect.DeepEqual(roles, []string{"editor"}) || !reflect.DeepEqual(users, []string{"alice"}) || err != nil || err2 != nil || !direct || transitive {
		t.Fatalf("roles=%v users=%v direct=%v transitive=%v err=%v/%v", roles, users, direct, transitive, err, err2)
	}
}

// Verifies: CAS-RBAC-006, CAS-ERR-002
func TestCAS026ImplicitRolesTerminateForCycle(t *testing.T) {
	e := mustEnforcer(t, rbacText)
	for _, r := range [][]string{{"alice", "r1"}, {"r1", "r2"}, {"r2", "r1"}} {
		if _, err := e.AddGroupingPolicy(r); err != nil {
			t.Fatal(err)
		}
	}
	got, err := e.GetImplicitRolesForUser("alice")
	if err != nil || !reflect.DeepEqual(sortedStrings(got), []string{"r1", "r2"}) {
		t.Fatalf("got=%v err=%v", got, err)
	}
}

// Verifies: CAS-RBAC-007, CAS-INV-002
func TestCAS027DirectAndImplicitPermissions(t *testing.T) {
	e := mustEnforcer(t, rbacText)
	add(t, e, "admin", "data1", "read")
	add(t, e, "alice", "data2", "write")
	if _, err := e.AddRoleForUser("alice", "admin"); err != nil {
		t.Fatal(err)
	}
	direct, _ := e.GetPermissionsForUser("alice")
	implicit, err := e.GetImplicitPermissionsForUser("alice")
	if err != nil || !reflect.DeepEqual(direct, [][]string{{"alice", "data2", "write"}}) {
		t.Fatalf("direct=%v implicit=%v err=%v", direct, implicit, err)
	}
	want := [][]string{{"alice", "data2", "write"}, {"admin", "data1", "read"}}
	if !reflect.DeepEqual(sortedRows(implicit), sortedRows(want)) {
		t.Fatalf("implicit=%v", implicit)
	}
	ok, err := e.Enforce("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("enforce=%v %v", ok, err)
	}
}

// Verifies: CAS-RBAC-008
func TestCAS028PermissionMutation(t *testing.T) {
	e := mustEnforcer(t, rbacText)
	ok, err := e.AddPermissionForUser("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("add: %v %v", ok, err)
	}
	has, err := e.HasPermissionForUser("alice", "data1", "read")
	if err != nil || !has {
		t.Fatalf("has: %v %v", has, err)
	}
	ok, err = e.DeletePermissionForUser("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("delete: %v %v", ok, err)
	}
	has, _ = e.HasPermissionForUser("alice", "data1", "read")
	if has {
		t.Fatal("permission survived deletion")
	}
}

// Verifies: CAS-RBAC-005
func TestCAS029BuildRoleLinksIsIdempotent(t *testing.T) {
	e := mustEnforcer(t, rbacText)
	add(t, e, "admin", "data1", "read")
	if _, err := e.AddRoleForUser("alice", "admin"); err != nil {
		t.Fatal(err)
	}
	before, _ := e.GetGroupingPolicy()
	if err := e.BuildRoleLinks(); err != nil {
		t.Fatal(err)
	}
	after, _ := e.GetGroupingPolicy()
	ok, err := e.Enforce("alice", "data1", "read")
	if err != nil || !ok || !reflect.DeepEqual(before, after) {
		t.Fatalf("before=%v after=%v ok=%v err=%v", before, after, ok, err)
	}
}

// Verifies: CAS-STA-001, CAS-INV-001, CAS-INV-006
func TestCAS030RejectedMutationsPreserveLaterUse(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	if ok, err := e.AddPolicy("alice", "data1", "read"); err != nil || ok {
		t.Fatalf("duplicate: %v %v", ok, err)
	}
	if ok, err := e.RemovePolicy("missing", "data1", "read"); err != nil || ok {
		t.Fatalf("missing: %v %v", ok, err)
	}
	ok, err := e.Enforce("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("later enforce: %v %v", ok, err)
	}
}
