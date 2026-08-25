package integration

import (
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

const rbacDenyModel = `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow)) && !some(where (p.eft == deny))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
`

const domainModel = `
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
