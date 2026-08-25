package integration

import (
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
	stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)

func TestRbacDocumentWorkflow(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "report", "edit")
	e.AddGroupingPolicy("alice", "admin")

	mustEnforce(t, e, true, "alice", "report", "edit")
	roles, err := e.GetImplicitRolesForUser("alice")
	if err != nil || !reflect.DeepEqual(roles, []string{"admin"}) {
		t.Fatalf("implicit roles = (%v, %v)", roles, err)
	}
	perms, err := e.GetImplicitPermissionsForUser("alice")
	if err != nil || !reflect.DeepEqual(perms, [][]string{{"admin", "report", "edit"}}) {
		t.Fatalf("implicit permissions = (%v, %v)", perms, err)
	}
	mustEnforce(t, e, false, "mallory", "report", "edit")
}

func TestDenyAuditWorkflow(t *testing.T) {
	e := mkEnforcer(t, rbacDenyModel)
	e.AddPolicy("alice", "ledger", "read", "allow")
	e.AddPolicy("alice", "ledger", "read", "deny")

	mustEnforce(t, e, false, "alice", "ledger", "read")
	_, why, err := e.EnforceEx("alice", "ledger", "read")
	if err != nil {
		t.Fatalf("EnforceEx: %v", err)
	}
	if len(why) == 0 {
		t.Fatal("the veto verdict must name a deciding rule")
	}
	has, _ := e.HasPolicy(toIface(why)...)
	if !has {
		t.Fatalf("explanation %v must be a stored rule", why)
	}
	e.RemovePolicy("alice", "ledger", "read", "deny")
	mustEnforce(t, e, true, "alice", "ledger", "read")
}

func TestDenyOverridesInheritedAllow(t *testing.T) {
	e := mkEnforcer(t, rbacDenyModel)
	e.AddPolicy("admin", "vault", "open", "allow")
	e.AddPolicy("alice", "vault", "open", "deny")
	e.AddGroupingPolicy("alice", "admin")

	mustEnforce(t, e, false, "alice", "vault", "open")
	mustEnforce(t, e, true, "admin", "vault", "open")
	e.AddGroupingPolicy("bob", "admin")
	mustEnforce(t, e, true, "bob", "vault", "open")
}

func TestTransitiveChainEnforcement(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("root", "system", "reboot")
	e.AddGroupingPolicy("alice", "ops")
	e.AddGroupingPolicy("ops", "sre")
	e.AddGroupingPolicy("sre", "root")

	mustEnforce(t, e, true, "alice", "system", "reboot")
	roles, _ := e.GetImplicitRolesForUser("alice")
	if !reflect.DeepEqual(roles, []string{"ops", "sre", "root"}) {
		t.Fatalf("implicit chain = %v", roles)
	}
	mustEnforce(t, e, false, "sre", "other", "reboot")
}

func TestKeyMatchWithRbacWorkflow(t *testing.T) {
	text := `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && keyMatch2(r.obj, p.obj) && regexMatch(r.act, p.act)
`
	e := mkEnforcer(t, text)
	e.AddPolicy("api_user", "/api/items/:id", "(GET)|(HEAD)")
	e.AddGroupingPolicy("alice", "api_user")

	mustEnforce(t, e, true, "alice", "/api/items/42", "GET")
	mustEnforce(t, e, true, "alice", "/api/items/7", "HEAD")
	mustEnforce(t, e, false, "alice", "/api/items/42", "DELETE")
	mustEnforce(t, e, false, "alice", "/api/items/42/sub", "GET")
	mustEnforce(t, e, false, "eve", "/api/items/42", "GET")
}

type Requester struct {
	Name  string
	Level int
}

func TestAbacWithRbacMixed(t *testing.T) {
	text := `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub.Name, p.sub) && r.sub.Level >= 3 && r.obj == p.obj && r.act == p.act
`
	e := mkEnforcer(t, text)
	e.AddPolicy("staff", "console", "use")
	e.AddGroupingPolicy("alice", "staff")

	mustEnforce(t, e, true, Requester{"alice", 4}, "console", "use")
	mustEnforce(t, e, false, Requester{"alice", 2}, "console", "use")
	mustEnforce(t, e, false, Requester{"eve", 9}, "console", "use")
}

func TestEvalWorkflowWithMutations(t *testing.T) {
	text := `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub_rule, obj, act

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = eval(p.sub_rule) && r.obj == p.obj && r.act == p.act
`
	e := mkEnforcer(t, text)
	e.AddPolicy("r.sub.Level > 2", "data", "read")
	mustEnforce(t, e, true, Requester{"alice", 3}, "data", "read")
	mustEnforce(t, e, false, Requester{"bob", 1}, "data", "read")

	e.UpdatePolicy([]string{"r.sub.Level > 2", "data", "read"}, []string{"r.sub.Level > 5", "data", "read"})
	mustEnforce(t, e, false, Requester{"alice", 3}, "data", "read")
	mustEnforce(t, e, true, Requester{"carol", 6}, "data", "read")
}

func TestPriorityWithRoleRules(t *testing.T) {
	text := `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[policy_effect]
e = priority(p.eft) || deny

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
`
	e := mkEnforcer(t, text)
	e.AddPolicy("alice", "data", "read", "deny")
	e.AddPolicy("staff", "data", "read", "allow")
	e.AddGroupingPolicy("alice", "staff")

	mustEnforce(t, e, false, "alice", "data", "read")
	e.AddGroupingPolicy("bob", "staff")
	mustEnforce(t, e, true, "bob", "data", "read")
	mustEnforce(t, e, false, "carol", "data", "read")
}

func TestStringAdapterPersistenceWorkflow(t *testing.T) {
	a := stringadapter.NewAdapter("p, admin, data, write\ng, alice, admin")
	m, _ := model.NewModelFromString(rbacModel)
	e, err := casbin.NewEnforcer(m, a)
	if err != nil {
		t.Fatalf("NewEnforcer: %v", err)
	}
	mustEnforce(t, e, true, "alice", "data", "write")

	e.AddGroupingPolicy("bob", "admin")
	if err := e.SavePolicy(); err != nil {
		t.Fatalf("SavePolicy: %v", err)
	}
	if !strings.Contains(a.Line, "g, bob, admin") {
		t.Fatalf("saved text must contain the new grouping rule, got %q", a.Line)
	}

	m2, _ := model.NewModelFromString(rbacModel)
	e2, err := casbin.NewEnforcer(m2, a)
	if err != nil {
		t.Fatalf("rebuild: %v", err)
	}
	mustEnforce(t, e2, true, "bob", "data", "write")
	mustEnforce(t, e2, true, "alice", "data", "write")
	p1, _ := e.GetPolicy()
	p2, _ := e2.GetPolicy()
	if !reflect.DeepEqual(p1, p2) {
		t.Fatalf("rebuilt store %v != original %v", p2, p1)
	}
}

func TestSaveLoadRoundTrip(t *testing.T) {
	a := stringadapter.NewAdapter("p, alice, data1, read")
	m, _ := model.NewModelFromString(aclModel)
	e, _ := casbin.NewEnforcer(m, a)

	e.AddPolicy("bob", "data2", "write")
	if err := e.SavePolicy(); err != nil {
		t.Fatalf("SavePolicy: %v", err)
	}
	before, _ := e.GetPolicy()

	e.AddPolicy("ghost", "data3", "read")
	if err := e.LoadPolicy(); err != nil {
		t.Fatalf("LoadPolicy: %v", err)
	}
	after, _ := e.GetPolicy()
	if !reflect.DeepEqual(before, after) {
		t.Fatalf("reload must restore the saved store: %v != %v", after, before)
	}
	mustEnforce(t, e, false, "ghost", "data3", "read")
	mustEnforce(t, e, true, "bob", "data2", "write")
}

func TestFileAdapterRoundTrip(t *testing.T) {
	dir := t.TempDir()
	mpath := filepath.Join(dir, "model.conf")
	ppath := filepath.Join(dir, "policy.csv")
	os.WriteFile(mpath, []byte(rbacModel), 0o644)
	os.WriteFile(ppath, []byte("p, admin, data, write\ng, alice, admin\n"), 0o644)

	e, err := casbin.NewEnforcer(mpath, ppath)
	if err != nil {
		t.Fatalf("NewEnforcer(files): %v", err)
	}
	mustEnforce(t, e, true, "alice", "data", "write")

	e.AddPolicy("bob", "data2", "read")
	if err := e.SavePolicy(); err != nil {
		t.Fatalf("SavePolicy: %v", err)
	}
	raw, _ := os.ReadFile(ppath)
	text := string(raw)
	for _, want := range []string{"p, admin, data, write", "p, bob, data2, read", "g, alice, admin"} {
		if !strings.Contains(text, want) {
			t.Fatalf("saved csv must contain %q, got:\n%s", want, text)
		}
	}

	e2, err := casbin.NewEnforcer(mpath, ppath)
	if err != nil {
		t.Fatalf("reopen: %v", err)
	}
	mustEnforce(t, e2, true, "bob", "data2", "read")
	mustEnforce(t, e2, true, "alice", "data", "write")
}

func TestLoadPolicyRebuildsRoleGraph(t *testing.T) {
	dir := t.TempDir()
	mpath := filepath.Join(dir, "model.conf")
	ppath := filepath.Join(dir, "policy.csv")
	os.WriteFile(mpath, []byte(rbacModel), 0o644)
	os.WriteFile(ppath, []byte("p, admin, data, write\ng, alice, admin\n"), 0o644)
	e, err := casbin.NewEnforcer(mpath, ppath)
	if err != nil {
		t.Fatalf("NewEnforcer(files): %v", err)
	}

	e.DeleteRoleForUser("alice", "admin")
	mustEnforce(t, e, false, "alice", "data", "write")

	if err := e.LoadPolicy(); err != nil {
		t.Fatalf("LoadPolicy: %v", err)
	}
	mustEnforce(t, e, true, "alice", "data", "write")
	roles, _ := e.GetImplicitRolesForUser("alice")
	if !reflect.DeepEqual(roles, []string{"admin"}) {
		t.Fatalf("role graph after reload = %v", roles)
	}
}

func TestExplanationTracksStoreMutation(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	_, why, _ := e.EnforceEx("alice", "data1", "read")
	if !reflect.DeepEqual(why, []string{"alice", "data1", "read"}) {
		t.Fatalf("explanation = %v", why)
	}
	e.RemovePolicy("alice", "data1", "read")
	ok, why2, _ := e.EnforceEx("alice", "data1", "read")
	if ok || len(why2) != 0 {
		t.Fatalf("after removal: (%v, %v), want (false, empty)", ok, why2)
	}
}

func TestManyModelsOneStoreShape(t *testing.T) {
	// The same rule set must produce effect-dependent verdicts.
	rules := [][]string{
		{"alice", "data", "read", "allow"},
		{"alice", "data", "read", "deny"},
	}
	eDeny := mkEnforcer(t, rbacDenyModel)
	for _, r := range rules {
		eDeny.AddPolicy(toIface(r)...)
	}
	mustEnforce(t, eDeny, false, "alice", "data", "read")

	prText := strings.Replace(rbacDenyModel,
		"e = some(where (p.eft == allow)) && !some(where (p.eft == deny))",
		"e = priority(p.eft) || deny", 1)
	ePr := mkEnforcer(t, prText)
	for _, r := range rules {
		ePr.AddPolicy(toIface(r)...)
	}
	mustEnforce(t, ePr, true, "alice", "data", "read")

	pDeny, _ := eDeny.GetPolicy()
	pPr, _ := ePr.GetPolicy()
	if !reflect.DeepEqual(pDeny, pPr) {
		t.Fatalf("stores must be identical across models: %v vs %v", pDeny, pPr)
	}
}

func TestGetUsersForRoleInDomainProjection(t *testing.T) {
	e := mkEnforcer(t, domainModel)
	e.AddGroupingPolicy("alice", "admin", "t1")
	e.AddGroupingPolicy("bob", "admin", "t2")
	e.AddGroupingPolicy("carol", "admin", "t1")

	u1 := e.GetUsersForRoleInDomain("admin", "t1")
	if !reflect.DeepEqual(u1, []string{"alice", "carol"}) {
		t.Fatalf("t1 admins = %v", u1)
	}
	u2 := e.GetUsersForRoleInDomain("admin", "t2")
	if !reflect.DeepEqual(u2, []string{"bob"}) {
		t.Fatalf("t2 admins = %v", u2)
	}
	gp, _ := e.GetGroupingPolicy()
	if len(gp) != 3 {
		t.Fatalf("grouping store = %v", gp)
	}
}

func TestWrongArityLeavesStoreUsable(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	res, err := e.Enforce("alice")
	if err == nil || !strings.Contains(fmt.Sprint(err), "invalid request size") {
		t.Fatalf("err = %v, want invalid request size", err)
	}
	if res {
		t.Fatal("malformed request must not be allowed")
	}
	mustEnforce(t, e, true, "alice", "data1", "read")
}
