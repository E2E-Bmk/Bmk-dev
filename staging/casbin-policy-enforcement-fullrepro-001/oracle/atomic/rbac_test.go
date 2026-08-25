package atomic

import (
	"reflect"
	"sort"
	"testing"
)

func TestGetRolesForUserDirectOnly(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddGroupingPolicy("alice", "admin")
	e.AddGroupingPolicy("admin", "super")
	roles, err := e.GetRolesForUser("alice")
	if err != nil {
		t.Fatalf("GetRolesForUser: %v", err)
	}
	if !reflect.DeepEqual(roles, []string{"admin"}) {
		t.Fatalf("direct roles = %v, want [admin] only", roles)
	}
}

func TestGetUsersForRole(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddGroupingPolicy("alice", "admin")
	e.AddGroupingPolicy("bob", "admin")
	users, err := e.GetUsersForRole("admin")
	if err != nil {
		t.Fatalf("GetUsersForRole: %v", err)
	}
	sort.Strings(users)
	if !reflect.DeepEqual(users, []string{"alice", "bob"}) {
		t.Fatalf("users = %v, want [alice bob]", users)
	}
}

func TestHasRoleForUser(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddGroupingPolicy("alice", "admin")
	has, err := e.HasRoleForUser("alice", "admin")
	if err != nil || !has {
		t.Fatalf("HasRoleForUser = (%v, %v), want (true, nil)", has, err)
	}
	has, _ = e.HasRoleForUser("bob", "admin")
	if has {
		t.Fatal("an unlinked user must not have the role")
	}
}

func TestAddRoleForUserAndDelete(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	ok, err := e.AddRoleForUser("bob", "admin")
	if err != nil || !ok {
		t.Fatalf("AddRoleForUser = (%v, %v), want (true, nil)", ok, err)
	}
	has, _ := e.HasRoleForUser("bob", "admin")
	if !has {
		t.Fatal("the link must be visible after AddRoleForUser")
	}
	ok, err = e.DeleteRoleForUser("bob", "admin")
	if err != nil || !ok {
		t.Fatalf("DeleteRoleForUser = (%v, %v), want (true, nil)", ok, err)
	}
	has, _ = e.HasRoleForUser("bob", "admin")
	if has {
		t.Fatal("the link must be gone after DeleteRoleForUser")
	}
}

func TestGetImplicitRolesTransitive(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddGroupingPolicy("alice", "admin")
	e.AddGroupingPolicy("admin", "super")
	roles, err := e.GetImplicitRolesForUser("alice")
	if err != nil {
		t.Fatalf("GetImplicitRolesForUser: %v", err)
	}
	if !reflect.DeepEqual(roles, []string{"admin", "super"}) {
		t.Fatalf("implicit roles = %v, want [admin super]", roles)
	}
}

func TestGetImplicitRolesDiamond(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddGroupingPolicy("u", "r1")
	e.AddGroupingPolicy("u", "r2")
	e.AddGroupingPolicy("r1", "top")
	e.AddGroupingPolicy("r2", "top")
	roles, err := e.GetImplicitRolesForUser("u")
	if err != nil {
		t.Fatalf("GetImplicitRolesForUser: %v", err)
	}
	sort.Strings(roles)
	if !reflect.DeepEqual(roles, []string{"r1", "r2", "top"}) {
		t.Fatalf("diamond implicit roles = %v, want each role once", roles)
	}
}

func TestPermissionsForUserDirectOnly(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddGroupingPolicy("alice", "admin")
	perms, err := e.GetPermissionsForUser("alice")
	if err != nil {
		t.Fatalf("GetPermissionsForUser: %v", err)
	}
	if len(perms) != 0 {
		t.Fatalf("alice has no direct rules; got %v", perms)
	}
	aperms, _ := e.GetPermissionsForUser("admin")
	if !reflect.DeepEqual(aperms, [][]string{{"admin", "data", "write"}}) {
		t.Fatalf("admin's direct rules = %v", aperms)
	}
}

func TestImplicitPermissionsIncludeRoleRules(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddPolicy("alice", "own", "read")
	e.AddGroupingPolicy("alice", "admin")
	perms, err := e.GetImplicitPermissionsForUser("alice")
	if err != nil {
		t.Fatalf("GetImplicitPermissionsForUser: %v", err)
	}
	sort.Slice(perms, func(i, j int) bool { return perms[i][0] < perms[j][0] })
	want := [][]string{{"admin", "data", "write"}, {"alice", "own", "read"}}
	if !reflect.DeepEqual(perms, want) {
		t.Fatalf("implicit permissions = %v, want %v", perms, want)
	}
}

func TestPermissionHelpers(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	ok, err := e.AddPermissionForUser("carol", "data9", "read")
	if err != nil || !ok {
		t.Fatalf("AddPermissionForUser = (%v, %v), want (true, nil)", ok, err)
	}
	has, err := e.HasPermissionForUser("carol", "data9", "read")
	if err != nil || !has {
		t.Fatalf("HasPermissionForUser = (%v, %v), want (true, nil)", has, err)
	}
	ok, err = e.DeletePermissionsForUser("carol")
	if err != nil || !ok {
		t.Fatalf("DeletePermissionsForUser = (%v, %v), want (true, nil)", ok, err)
	}
	has, _ = e.HasPermissionForUser("carol", "data9", "read")
	if has {
		t.Fatal("permissions must be gone after DeletePermissionsForUser")
	}
	ok, _ = e.DeletePermissionsForUser("carol")
	if ok {
		t.Fatal("deleting when nothing remains must report false")
	}
}
