package integration

import (
	"reflect"
	"sort"
	"testing"
)

func TestMutationVisibleAcrossProjections(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddGroupingPolicy("alice", "admin")

	mustEnforce(t, e, true, "alice", "data", "write")
	has, _ := e.HasPolicy("admin", "data", "write")
	if !has {
		t.Fatal("HasPolicy must see the added rule")
	}
	roles, _ := e.GetImplicitRolesForUser("alice")
	if !reflect.DeepEqual(roles, []string{"admin"}) {
		t.Fatalf("implicit roles = %v", roles)
	}

	if ok, _ := e.RemovePolicy("admin", "data", "write"); !ok {
		t.Fatal("RemovePolicy must report true")
	}
	mustEnforce(t, e, false, "alice", "data", "write")
	pol, _ := e.GetPolicy()
	if len(pol) != 0 {
		t.Fatalf("GetPolicy after removal = %v", pol)
	}
	perms, _ := e.GetImplicitPermissionsForUser("alice")
	if len(perms) != 0 {
		t.Fatalf("implicit permissions after removal = %v", perms)
	}
}

func TestEnforceExAgreesWithEnforce(t *testing.T) {
	e := mkEnforcer(t, rbacDenyModel)
	e.AddPolicy("admin", "data", "write", "allow")
	e.AddPolicy("alice", "data", "read", "deny")
	e.AddGroupingPolicy("alice", "admin")
	requests := [][]interface{}{
		{"alice", "data", "write"},
		{"alice", "data", "read"},
		{"bob", "data", "write"},
	}
	for _, r := range requests {
		v1, err1 := e.Enforce(r...)
		v2, why, err2 := e.EnforceEx(r...)
		if err1 != nil || err2 != nil {
			t.Fatalf("errors: %v %v", err1, err2)
		}
		if v1 != v2 {
			t.Fatalf("Enforce (%v) and EnforceEx (%v) disagree on %v", v1, v2, r)
		}
		if len(why) > 0 {
			has, _ := e.HasPolicy(toIface(why)...)
			if !has {
				t.Fatalf("explanation %v is not a rule in the store", why)
			}
		}
	}
	if v, _ := e.Enforce("alice", "data", "write"); !v {
		t.Fatal("alice must be allowed to write via admin")
	}
	if v, _ := e.Enforce("alice", "data", "read"); v {
		t.Fatal("the deny rule must veto alice's read")
	}
}

func toIface(ss []string) []interface{} {
	out := make([]interface{}, len(ss))
	for i, s := range ss {
		out[i] = s
	}
	return out
}

func TestBatchAgreesWithSingle(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddPolicy("bob", "file", "read")
	e.AddGroupingPolicy("alice", "admin")
	reqs := [][]interface{}{
		{"alice", "data", "write"},
		{"bob", "file", "read"},
		{"bob", "data", "write"},
		{"admin", "data", "write"},
	}
	batch, err := e.BatchEnforce(reqs)
	if err != nil {
		t.Fatalf("BatchEnforce: %v", err)
	}
	if len(batch) != len(reqs) {
		t.Fatalf("batch length %d != %d", len(batch), len(reqs))
	}
	for i, r := range reqs {
		single, _ := e.Enforce(r...)
		if batch[i] != single {
			t.Fatalf("request %v: batch %v != single %v", r, batch[i], single)
		}
	}
	if !batch[0] || !batch[1] || batch[2] || !batch[3] {
		t.Fatalf("batch verdicts = %v, want [true true false true]", batch)
	}
}

func TestRoleSubsetInvariant(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddPolicy("alice", "own", "read")
	e.AddGroupingPolicy("alice", "admin")
	e.AddGroupingPolicy("admin", "super")

	direct, _ := e.GetRolesForUser("alice")
	implicit, _ := e.GetImplicitRolesForUser("alice")
	iset := map[string]bool{}
	for _, r := range implicit {
		iset[r] = true
	}
	for _, r := range direct {
		if !iset[r] {
			t.Fatalf("direct role %q missing from implicit set %v", r, implicit)
		}
	}
	if !iset["super"] {
		t.Fatalf("implicit set %v must include the transitive role", implicit)
	}

	perms, _ := e.GetPermissionsForUser("alice")
	iperms, _ := e.GetImplicitPermissionsForUser("alice")
	for _, p := range perms {
		found := false
		for _, ip := range iperms {
			if reflect.DeepEqual(p, ip) {
				found = true
			}
		}
		if !found {
			t.Fatalf("direct rule %v missing from implicit permissions %v", p, iperms)
		}
	}
	if len(iperms) != 2 {
		t.Fatalf("implicit permissions = %v, want alice's own rule plus admin's", iperms)
	}
}

func TestRoleLinkFlipsVerdictAndQuery(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddGroupingPolicy("alice", "admin")
	mustEnforce(t, e, true, "alice", "data", "write")

	if ok, _ := e.DeleteRoleForUser("alice", "admin"); !ok {
		t.Fatal("DeleteRoleForUser must report true")
	}
	mustEnforce(t, e, false, "alice", "data", "write")
	roles, _ := e.GetImplicitRolesForUser("alice")
	if len(roles) != 0 {
		t.Fatalf("implicit roles after unlink = %v", roles)
	}
	has, _ := e.HasGroupingPolicy("alice", "admin")
	if has {
		t.Fatal("the grouping store must not hold the removed link")
	}
}

func TestGroupingRemovalRebuildsGraph(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("top", "data", "admin_op")
	e.AddGroupingPolicy("alice", "mid")
	e.AddGroupingPolicy("mid", "top")
	mustEnforce(t, e, true, "alice", "data", "admin_op")

	e.RemoveGroupingPolicy("mid", "top")
	mustEnforce(t, e, false, "alice", "data", "admin_op")
	roles, _ := e.GetImplicitRolesForUser("alice")
	if !reflect.DeepEqual(roles, []string{"mid"}) {
		t.Fatalf("implicit roles after cutting the chain = %v, want [mid]", roles)
	}
	mustEnforce(t, e, true, "top", "data", "admin_op")
}

func TestDomainIsolation(t *testing.T) {
	e := mkEnforcer(t, domainModel)
	e.AddPolicy("admin", "t1", "data", "write")
	e.AddPolicy("admin", "t2", "data", "write")
	e.AddGroupingPolicy("alice", "admin", "t1")
	e.AddGroupingPolicy("bob", "admin", "t2")

	mustEnforce(t, e, true, "alice", "t1", "data", "write")
	mustEnforce(t, e, false, "alice", "t2", "data", "write")
	mustEnforce(t, e, true, "bob", "t2", "data", "write")
	mustEnforce(t, e, false, "bob", "t1", "data", "write")

	r1 := e.GetRolesForUserInDomain("alice", "t1")
	if !reflect.DeepEqual(r1, []string{"admin"}) {
		t.Fatalf("alice roles in t1 = %v", r1)
	}
	r2 := e.GetRolesForUserInDomain("alice", "t2")
	if len(r2) != 0 {
		t.Fatalf("alice roles in t2 = %v, want none", r2)
	}
	u1 := e.GetUsersForRoleInDomain("admin", "t1")
	if !reflect.DeepEqual(u1, []string{"alice"}) {
		t.Fatalf("admin users in t1 = %v", u1)
	}
}

func TestDomainRoleRemovalScoped(t *testing.T) {
	e := mkEnforcer(t, domainModel)
	e.AddPolicy("admin", "t1", "data", "write")
	e.AddPolicy("admin", "t2", "data", "write")
	e.AddGroupingPolicy("alice", "admin", "t1")
	e.AddGroupingPolicy("alice", "admin", "t2")

	ok, err := e.DeleteRoleForUserInDomain("alice", "admin", "t1")
	if err != nil || !ok {
		t.Fatalf("DeleteRoleForUserInDomain = (%v, %v)", ok, err)
	}
	mustEnforce(t, e, false, "alice", "t1", "data", "write")
	mustEnforce(t, e, true, "alice", "t2", "data", "write")
}

func TestCatalogsFollowStore(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("a", "o1", "read")
	e.AddPolicy("b", "o2", "write")
	e.AddGroupingPolicy("u", "role1")
	subs, _ := e.GetAllSubjects()
	sort.Strings(subs)
	if !reflect.DeepEqual(subs, []string{"a", "b"}) {
		t.Fatalf("subjects = %v", subs)
	}
	e.RemovePolicy("a", "o1", "read")
	subs, _ = e.GetAllSubjects()
	if !reflect.DeepEqual(subs, []string{"b"}) {
		t.Fatalf("subjects after removal = %v", subs)
	}
	objs, _ := e.GetAllObjects()
	if !reflect.DeepEqual(objs, []string{"o2"}) {
		t.Fatalf("objects after removal = %v", objs)
	}
	roles, _ := e.GetAllRoles()
	if !reflect.DeepEqual(roles, []string{"role1"}) {
		t.Fatalf("roles = %v", roles)
	}
}

func TestFilteredRemovalAffectsEnforcement(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("alice", "data2", "read")
	e.AddPolicy("bob", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "read")

	if ok, _ := e.RemoveFilteredPolicy(0, "alice"); !ok {
		t.Fatal("RemoveFilteredPolicy must report true")
	}
	mustEnforce(t, e, false, "alice", "data1", "read")
	mustEnforce(t, e, false, "alice", "data2", "read")
	mustEnforce(t, e, true, "bob", "data1", "read")
}

func TestUpdatePolicyAffectsEnforcement(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	if ok, _ := e.UpdatePolicy([]string{"alice", "data1", "read"}, []string{"alice", "data1", "write"}); !ok {
		t.Fatal("UpdatePolicy must report true")
	}
	mustEnforce(t, e, false, "alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "write")
	_, why, _ := e.EnforceEx("alice", "data1", "write")
	if !reflect.DeepEqual(why, []string{"alice", "data1", "write"}) {
		t.Fatalf("explanation must track the updated rule, got %v", why)
	}
}

func TestAddPoliciesVisibleAtomically(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	if ok, _ := e.AddPolicies([][]string{{"a", "d1", "read"}, {"b", "d2", "read"}}); !ok {
		t.Fatal("first batch must be added")
	}
	mustEnforce(t, e, true, "a", "d1", "read")
	mustEnforce(t, e, true, "b", "d2", "read")

	if ok, _ := e.AddPolicies([][]string{{"c", "d3", "read"}, {"b", "d2", "read"}}); ok {
		t.Fatal("a batch with a duplicate must be rejected")
	}
	mustEnforce(t, e, false, "c", "d3", "read")
}

func TestPermissionHelpersProjectToPolicy(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPermissionForUser("carol", "data9", "read")
	pol, _ := e.GetPolicy()
	if !reflect.DeepEqual(pol, [][]string{{"carol", "data9", "read"}}) {
		t.Fatalf("GetPolicy = %v, want carol's rule", pol)
	}
	mustEnforce(t, e, true, "carol", "data9", "read")
	e.DeletePermissionsForUser("carol")
	pol, _ = e.GetPolicy()
	if len(pol) != 0 {
		t.Fatalf("policy after DeletePermissionsForUser = %v", pol)
	}
	mustEnforce(t, e, false, "carol", "data9", "read")
}
