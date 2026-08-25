package atomic

import (
	"strings"
	"testing"

	"github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
)

const aclModel = `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act
`

const aclEftModel = `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[policy_effect]
e = some(where (p.eft == allow)) && !some(where (p.eft == deny))

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act
`

const priorityModel = `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[policy_effect]
e = priority(p.eft) || deny

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act
`

const rbacModel = `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
`

func mkEnforcer(t *testing.T, text string) *casbin.Enforcer {
	t.Helper()
	m, err := model.NewModelFromString(text)
	if err != nil {
		t.Fatalf("model parse: %v", err)
	}
	e, err := casbin.NewEnforcer(m)
	if err != nil {
		t.Fatalf("enforcer construction: %v", err)
	}
	return e
}

func mustEnforce(t *testing.T, e *casbin.Enforcer, want bool, rvals ...interface{}) {
	t.Helper()
	got, err := e.Enforce(rvals...)
	if err != nil {
		t.Fatalf("enforce %v: %v", rvals, err)
	}
	if got != want {
		t.Fatalf("enforce %v = %v, want %v", rvals, got, want)
	}
}

func TestModelFromStringParses(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	if _, err := e.AddPolicy("alice", "data1", "read"); err != nil {
		t.Fatalf("add: %v", err)
	}
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, false, "alice", "data1", "write")
}

func TestMissingSectionsError(t *testing.T) {
	_, err := model.NewModelFromString("[request_definition]\nr = sub, obj, act\n")
	if err == nil {
		t.Fatal("a model missing mandatory sections must be rejected")
	}
	if !strings.Contains(err.Error(), "missing required sections") {
		t.Fatalf("error %q must mention missing required sections", err)
	}
}

func TestMissingSectionErrorNamesSection(t *testing.T) {
	text := `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[policy_effect]
e = some(where (p.eft == allow))
`
	_, err := model.NewModelFromString(text)
	if err == nil {
		t.Fatal("a model without [matchers] must be rejected")
	}
	if !strings.Contains(err.Error(), "matchers") {
		t.Fatalf("error %q must name the missing matchers section", err)
	}
}

func TestEnforceWrongArityError(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	got, err := e.Enforce("alice", "data1")
	if err == nil || !strings.Contains(err.Error(), "invalid request size") {
		t.Fatalf("short request: err = %v, want invalid request size", err)
	}
	if got {
		t.Fatal("a malformed request must not be allowed")
	}
	_, err = e.Enforce("alice", "data1", "read", "extra")
	if err == nil || !strings.Contains(err.Error(), "invalid request size") {
		t.Fatalf("long request: err = %v, want invalid request size", err)
	}
}

func TestUndefinedFunctionError(t *testing.T) {
	text := `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = mysteryFn(r.sub, p.sub)
`
	e := mkEnforcer(t, text)
	e.AddPolicy("a", "b", "c")
	got, err := e.Enforce("a", "b", "c")
	if err == nil || !strings.Contains(err.Error(), "Undefined function") {
		t.Fatalf("err = %v, want Undefined function", err)
	}
	if got {
		t.Fatal("an unevaluable matcher must not allow")
	}
}

func TestEmptyPolicyDeniesAllEffects(t *testing.T) {
	for _, text := range []string{aclModel, aclEftModel, priorityModel} {
		e := mkEnforcer(t, text)
		got, err := e.Enforce("anyone", "anything", "anyhow")
		if err != nil {
			t.Fatalf("empty-store enforce: %v", err)
		}
		if got {
			t.Fatal("an empty policy store must deny under every in-scope effect rule")
		}
	}
}

func TestImplicitEftReadsAllow(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, false, "bob", "data1", "read")
}

func TestThreePlaceRoleDefinitionParses(t *testing.T) {
	text := `
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && r.obj == p.obj && r.act == p.act
`
	e := mkEnforcer(t, text)
	e.AddPolicy("admin", "t1", "data", "write")
	e.AddGroupingPolicy("alice", "admin", "t1")
	mustEnforce(t, e, true, "alice", "t1", "data", "write")
	mustEnforce(t, e, false, "alice", "t2", "data", "write")
}
