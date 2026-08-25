package atomic

import (
	"fmt"
	"testing"
)

const fnModelTemplate = `
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = %s
`

type Person struct {
	Name string
	Age  int
}

func TestExactStringMatcher(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && r.obj == p.obj && r.act == p.act"))
	e.AddPolicy("alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, false, "Alice", "data1", "read")
}

func TestInequalityMatcher(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub != p.sub && r.obj == p.obj && r.act == p.act"))
	e.AddPolicy("banned", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, false, "banned", "data1", "read")
}

func TestBooleanConnectives(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate,
		"r.sub == p.sub && (r.act == p.act || r.act == \"list\") && !(r.obj == \"secret\")"))
	e.AddPolicy("alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "list")
	mustEnforce(t, e, false, "alice", "data1", "write")
	mustEnforce(t, e, false, "alice", "secret", "read")
}

func TestNumericComparisonMatcher(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub.Age >= 21 && r.obj == p.obj && r.act == p.act"))
	e.AddPolicy("any", "bar", "enter")
	mustEnforce(t, e, true, Person{"alice", 21}, "bar", "enter")
	mustEnforce(t, e, false, Person{"bob", 20}, "bar", "enter")
}

func TestInOperator(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate,
		"r.sub in (\"alice\", \"bob\") && r.obj == p.obj && r.act == p.act"))
	e.AddPolicy("any", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, true, "bob", "data1", "read")
	mustEnforce(t, e, false, "carol", "data1", "read")
}

func TestAbacFieldAccess(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate,
		"r.sub.Name == p.sub && r.obj == p.obj && r.act == p.act"))
	e.AddPolicy("alice", "data1", "read")
	mustEnforce(t, e, true, Person{"alice", 30}, "data1", "read")
	mustEnforce(t, e, false, Person{"eve", 30}, "data1", "read")
}

func TestEvalPolicyRule(t *testing.T) {
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
	e.AddPolicy("r.sub.Age > 18", "data1", "read")
	mustEnforce(t, e, true, Person{"alice", 25}, "data1", "read")
	mustEnforce(t, e, false, Person{"kid", 12}, "data1", "read")
}

func TestKeyMatchPrefix(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && keyMatch(r.obj, p.obj) && r.act == p.act"))
	e.AddPolicy("alice", "/data/*", "read")
	mustEnforce(t, e, true, "alice", "/data/1", "read")
	mustEnforce(t, e, true, "alice", "/data/deep/2", "read")
	mustEnforce(t, e, false, "alice", "/data2", "read")
}

func TestKeyMatchExactEquality(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && keyMatch(r.obj, p.obj) && r.act == p.act"))
	e.AddPolicy("alice", "/exact", "read")
	mustEnforce(t, e, true, "alice", "/exact", "read")
	mustEnforce(t, e, false, "alice", "/exact/sub", "read")
}

func TestKeyMatch2NamedSegment(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && keyMatch2(r.obj, p.obj) && r.act == p.act"))
	e.AddPolicy("alice", "/res/:id", "read")
	mustEnforce(t, e, true, "alice", "/res/42", "read")
	mustEnforce(t, e, false, "alice", "/res/42/sub", "read")
}

func TestRegexMatch(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && r.obj == p.obj && regexMatch(r.act, p.act)"))
	e.AddPolicy("alice", "data1", "(read)|(write)")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, true, "alice", "data1", "write")
	mustEnforce(t, e, false, "alice", "data1", "delete")
}

func TestGlobMatchSegmentScoped(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && globMatch(r.obj, p.obj) && r.act == p.act"))
	e.AddPolicy("alice", "/data/*", "read")
	mustEnforce(t, e, true, "alice", "/data/1", "read")
	mustEnforce(t, e, false, "alice", "/data/1/2", "read")
}

func TestIpMatchCidr(t *testing.T) {
	e := mkEnforcer(t, fmt.Sprintf(fnModelTemplate, "r.sub == p.sub && ipMatch(r.obj, p.obj) && r.act == p.act"))
	e.AddPolicy("alice", "192.168.2.0/24", "connect")
	mustEnforce(t, e, true, "alice", "192.168.2.123", "connect")
	mustEnforce(t, e, false, "alice", "10.0.0.1", "connect")
}

func TestRolePredicateInMatcher(t *testing.T) {
	e := mkEnforcer(t, rbacModel)
	e.AddPolicy("admin", "data", "write")
	e.AddGroupingPolicy("alice", "admin")
	mustEnforce(t, e, true, "alice", "data", "write")
	mustEnforce(t, e, true, "admin", "data", "write")
	mustEnforce(t, e, false, "mallory", "data", "write")
}
