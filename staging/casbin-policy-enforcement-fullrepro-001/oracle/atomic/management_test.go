package atomic

import (
	"reflect"
	"testing"
)

func TestAddPolicyAndHasPolicy(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	ok, err := e.AddPolicy("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("AddPolicy = (%v, %v), want (true, nil)", ok, err)
	}
	has, err := e.HasPolicy("alice", "data1", "read")
	if err != nil || !has {
		t.Fatalf("HasPolicy = (%v, %v), want (true, nil)", has, err)
	}
	has, _ = e.HasPolicy("alice", "data1", "write")
	if has {
		t.Fatal("HasPolicy must be false for an absent rule")
	}
}

func TestAddPolicyDuplicateReturnsFalse(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	ok, err := e.AddPolicy("alice", "data1", "read")
	if err != nil {
		t.Fatalf("duplicate add must not error, got %v", err)
	}
	if ok {
		t.Fatal("adding an existing rule must report false")
	}
	pol, _ := e.GetPolicy()
	if len(pol) != 1 {
		t.Fatalf("store must be unchanged, got %v", pol)
	}
}

func TestRemovePolicy(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	ok, err := e.RemovePolicy("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("RemovePolicy = (%v, %v), want (true, nil)", ok, err)
	}
	ok, err = e.RemovePolicy("alice", "data1", "read")
	if err != nil || ok {
		t.Fatalf("removing an absent rule must report (false, nil), got (%v, %v)", ok, err)
	}
	mustEnforce(t, e, false, "alice", "data1", "read")
}

func TestGetPolicyListsAll(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("bob", "data2", "write")
	pol, err := e.GetPolicy()
	if err != nil {
		t.Fatalf("GetPolicy: %v", err)
	}
	want := [][]string{{"alice", "data1", "read"}, {"bob", "data2", "write"}}
	if !reflect.DeepEqual(pol, want) {
		t.Fatalf("GetPolicy = %v, want %v", pol, want)
	}
}

func TestGetFilteredPolicyByIndex(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("alice", "data2", "write")
	e.AddPolicy("bob", "data2", "read")
	fp, err := e.GetFilteredPolicy(0, "alice")
	if err != nil {
		t.Fatalf("GetFilteredPolicy: %v", err)
	}
	want := [][]string{{"alice", "data1", "read"}, {"alice", "data2", "write"}}
	if !reflect.DeepEqual(fp, want) {
		t.Fatalf("filtered by subject = %v, want %v", fp, want)
	}
	fp2, _ := e.GetFilteredPolicy(1, "data2")
	if len(fp2) != 2 {
		t.Fatalf("filtered by object = %v, want two rules", fp2)
	}
}

func TestGetFilteredPolicyEmptyStringWildcard(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("alice", "data2", "write")
	e.AddPolicy("bob", "data1", "write")
	fp, err := e.GetFilteredPolicy(0, "alice", "", "write")
	if err != nil {
		t.Fatalf("GetFilteredPolicy: %v", err)
	}
	want := [][]string{{"alice", "data2", "write"}}
	if !reflect.DeepEqual(fp, want) {
		t.Fatalf("wildcarded filter = %v, want %v", fp, want)
	}
}

func TestRemoveFilteredPolicy(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("alice", "data2", "write")
	e.AddPolicy("bob", "data2", "write")
	ok, err := e.RemoveFilteredPolicy(0, "alice")
	if err != nil || !ok {
		t.Fatalf("RemoveFilteredPolicy = (%v, %v), want (true, nil)", ok, err)
	}
	pol, _ := e.GetPolicy()
	want := [][]string{{"bob", "data2", "write"}}
	if !reflect.DeepEqual(pol, want) {
		t.Fatalf("policy after filtered removal = %v, want %v", pol, want)
	}
	ok, _ = e.RemoveFilteredPolicy(0, "nobody")
	if ok {
		t.Fatal("a selection matching nothing must report false")
	}
}

func TestAddPoliciesAtomicOnDuplicate(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	ok, err := e.AddPolicies([][]string{{"a", "d1", "read"}, {"b", "d2", "read"}})
	if err != nil || !ok {
		t.Fatalf("AddPolicies = (%v, %v), want (true, nil)", ok, err)
	}
	ok, err = e.AddPolicies([][]string{{"c", "d3", "read"}, {"a", "d1", "read"}})
	if err != nil {
		t.Fatalf("batch with duplicate must not error, got %v", err)
	}
	if ok {
		t.Fatal("a batch containing an existing rule must report false")
	}
	has, _ := e.HasPolicy("c", "d3", "read")
	if has {
		t.Fatal("no rule from a rejected batch may be added")
	}
}

func TestUpdatePolicyReplacesRule(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	ok, err := e.UpdatePolicy([]string{"alice", "data1", "read"}, []string{"alice", "data1", "write"})
	if err != nil || !ok {
		t.Fatalf("UpdatePolicy = (%v, %v), want (true, nil)", ok, err)
	}
	mustEnforce(t, e, false, "alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "write")
	ok, err = e.UpdatePolicy([]string{"ghost", "x", "y"}, []string{"g2", "x", "y"})
	if err != nil || ok {
		t.Fatalf("updating an absent rule must report (false, nil), got (%v, %v)", ok, err)
	}
}

func TestGroupingPolicyCrud(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	ok, err := e.AddGroupingPolicy("alice", "admin")
	if err != nil || !ok {
		t.Fatalf("AddGroupingPolicy = (%v, %v), want (true, nil)", ok, err)
	}
	ok, _ = e.AddGroupingPolicy("alice", "admin")
	if ok {
		t.Fatal("duplicate grouping rule must report false")
	}
	has, err := e.HasGroupingPolicy("alice", "admin")
	if err != nil || !has {
		t.Fatalf("HasGroupingPolicy = (%v, %v), want (true, nil)", has, err)
	}
	gp, err := e.GetGroupingPolicy()
	if err != nil {
		t.Fatalf("GetGroupingPolicy: %v", err)
	}
	if !reflect.DeepEqual(gp, [][]string{{"alice", "admin"}}) {
		t.Fatalf("GetGroupingPolicy = %v", gp)
	}
	ok, _ = e.RemoveGroupingPolicy("alice", "admin")
	if !ok {
		t.Fatal("removing an existing grouping rule must report true")
	}
	ok, _ = e.RemoveGroupingPolicy("alice", "admin")
	if ok {
		t.Fatal("removing an absent grouping rule must report false")
	}
}

func TestGetAllCatalogs(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddPolicy("bob", "data2", "read")
	e.AddGroupingPolicy("alice", "admin")
	subs, err := e.GetAllSubjects()
	if err != nil || !reflect.DeepEqual(subs, []string{"admin", "bob"}) {
		t.Fatalf("GetAllSubjects = (%v, %v)", subs, err)
	}
	objs, _ := e.GetAllObjects()
	if !reflect.DeepEqual(objs, []string{"data", "data2"}) {
		t.Fatalf("GetAllObjects = %v", objs)
	}
	acts, _ := e.GetAllActions()
	if !reflect.DeepEqual(acts, []string{"write", "read"}) {
		t.Fatalf("GetAllActions = %v", acts)
	}
	roles, _ := e.GetAllRoles()
	if !reflect.DeepEqual(roles, []string{"admin"}) {
		t.Fatalf("GetAllRoles = %v", roles)
	}
}

func TestBatchEnforceOrder(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("bob", "data2", "write")
	res, err := e.BatchEnforce([][]interface{}{
		{"alice", "data1", "read"},
		{"eve", "data1", "read"},
		{"bob", "data2", "write"},
	})
	if err != nil {
		t.Fatalf("BatchEnforce: %v", err)
	}
	if !reflect.DeepEqual(res, []bool{true, false, true}) {
		t.Fatalf("BatchEnforce = %v, want [true false true]", res)
	}
}

func TestEnforceExExplanation(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	ok, why, err := e.EnforceEx("alice", "data1", "read")
	if err != nil || !ok {
		t.Fatalf("EnforceEx = (%v, %v, %v)", ok, why, err)
	}
	if !reflect.DeepEqual(why, []string{"alice", "data1", "read"}) {
		t.Fatalf("explanation = %v, want the matched rule", why)
	}
	ok, why, _ = e.EnforceEx("eve", "data1", "read")
	if ok || len(why) != 0 {
		t.Fatalf("denied request must have empty explanation, got (%v, %v)", ok, why)
	}
}
