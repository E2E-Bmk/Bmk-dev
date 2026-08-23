package atomic_test

import (
	"reflect"
	"testing"

	casbin "github.com/casbin/casbin/v3"
	"github.com/casbin/casbin/v3/model"
	stringadapter "github.com/casbin/casbin/v3/persist/string-adapter"
)

const aclText = `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`

const rbacText = `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
[role_definition]
g = _, _
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act`

func mustModel(t *testing.T, text string) model.Model {
	t.Helper()
	m, err := model.NewModelFromString(text)
	if err != nil {
		t.Fatalf("model: %v", err)
	}
	return m
}

func mustEnforcer(t *testing.T, text string) *casbin.Enforcer {
	t.Helper()
	e, err := casbin.NewEnforcer(mustModel(t, text))
	if err != nil {
		t.Fatalf("enforcer: %v", err)
	}
	return e
}

func add(t *testing.T, e *casbin.Enforcer, rule ...string) {
	t.Helper()
	ok, err := e.AddPolicy(rule)
	if err != nil || !ok {
		t.Fatalf("add %v: ok=%v err=%v", rule, ok, err)
	}
}

// Verifies: CAS-MOD-001
func TestCAS001NewModelAndAddDef(t *testing.T) {
	m := model.NewModel()
	if m == nil || m.AddDef("r", "r", "") {
		t.Fatal("empty model or empty definition accepted")
	}
	for _, d := range [][3]string{{"r", "r", "sub, obj, act"}, {"p", "p", "sub, obj, act"}, {"e", "e", "some(where (p.eft == allow))"}, {"m", "m", "r.sub == p.sub && r.obj == p.obj && r.act == p.act"}} {
		if !m.AddDef(d[0], d[1], d[2]) {
			t.Fatalf("AddDef%v", d)
		}
	}
	e, err := casbin.NewEnforcer(m)
	if err != nil || e == nil {
		t.Fatalf("constructed model unusable: %v", err)
	}
}

// Verifies: CAS-MOD-002
func TestCAS002TextAndAddDefModelsAgree(t *testing.T) {
	fromText := mustEnforcer(t, aclText)
	m := model.NewModel()
	m.AddDef("r", "r", "sub, obj, act")
	m.AddDef("p", "p", "sub, obj, act")
	m.AddDef("e", "e", "some(where (p.eft == allow))")
	m.AddDef("m", "m", "r.sub == p.sub && r.obj == p.obj && r.act == p.act")
	fromDefs, err := casbin.NewEnforcer(m)
	if err != nil {
		t.Fatal(err)
	}
	for _, e := range []*casbin.Enforcer{fromText, fromDefs} {
		add(t, e, "alice", "data1", "read")
	}
	for _, req := range [][]interface{}{{"alice", "data1", "read"}, {"alice", "data1", "write"}} {
		a, ea := fromText.Enforce(req...)
		b, eb := fromDefs.Enforce(req...)
		if ea != nil || eb != nil || a != b {
			t.Fatalf("%v: %v/%v %v/%v", req, a, ea, b, eb)
		}
	}
}

// Verifies: CAS-MOD-003, CAS-ERR-001
func TestCAS003ModelTextRequiredSections(t *testing.T) {
	if _, err := model.NewModelFromString(aclText); err != nil {
		t.Fatal(err)
	}
	bad := `[request_definition]
r = sub
[policy_definition]
p = sub`
	if _, err := model.NewModelFromString(bad); err == nil {
		t.Fatal("incomplete model accepted")
	}
}

// Verifies: CAS-NEW-001
func TestCAS004ModelOnlyStartsEmpty(t *testing.T) {
	e := mustEnforcer(t, aclText)
	p, err := e.GetPolicy()
	if err != nil || len(p) != 0 {
		t.Fatalf("policy=%v err=%v", p, err)
	}
	ok, err := e.Enforce("alice", "data1", "read")
	if err != nil || ok {
		t.Fatalf("empty decision=%v err=%v", ok, err)
	}
}

// Verifies: CAS-ENF-001, CAS-ENF-005
func TestCAS005ACLAllowAndDeny(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	for _, tc := range []struct {
		r []interface{}
		w bool
	}{{[]interface{}{"alice", "data1", "read"}, true}, {[]interface{}{"alice", "data1", "write"}, false}, {[]interface{}{"bob", "data1", "read"}, false}} {
		got, err := e.Enforce(tc.r...)
		if err != nil || got != tc.w {
			t.Fatalf("%v: got=%v err=%v", tc.r, got, err)
		}
	}
}

// Verifies: CAS-ENF-002, CAS-ERR-002
func TestCAS006InvalidRequestArityReturnsError(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	if _, err := e.Enforce("alice", "data1"); err == nil {
		t.Fatal("too few values accepted")
	}
	if _, err := e.Enforce("alice", "data1", "read", "extra"); err == nil {
		t.Fatal("too many values accepted")
	}
}

// Verifies: CAS-ENF-008
func TestCAS007EnableEnforceRoundTrip(t *testing.T) {
	e := mustEnforcer(t, aclText)
	e.EnableEnforce(false)
	if ok, err := e.Enforce("nobody", "missing", "write"); err != nil || !ok {
		t.Fatalf("disabled: %v %v", ok, err)
	}
	e.EnableEnforce(true)
	if ok, err := e.Enforce("nobody", "missing", "write"); err != nil || ok {
		t.Fatalf("enabled: %v %v", ok, err)
	}
}

// Verifies: CAS-ENF-009
func TestCAS008MatcherOverrideIsCallLocal(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	ok, err := e.EnforceWithMatcher("r.sub == p.sub && r.obj == p.obj", "alice", "data1", "write")
	if err != nil || !ok {
		t.Fatalf("override: %v %v", ok, err)
	}
	ok, err = e.Enforce("alice", "data1", "write")
	if err != nil || ok {
		t.Fatalf("stored matcher changed: %v %v", ok, err)
	}
}

// Verifies: CAS-ENF-010
func TestCAS009EnforceExExplanation(t *testing.T) {
	e := mustEnforcer(t, aclText)
	rule := []string{"alice", "data1", "read"}
	add(t, e, rule...)
	ok, explain, err := e.EnforceEx("alice", "data1", "read")
	if err != nil || !ok || !reflect.DeepEqual(explain, rule) {
		t.Fatalf("ok=%v explain=%v err=%v", ok, explain, err)
	}
}

// Verifies: CAS-ENF-011
func TestCAS010BatchEnforceOrder(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	reqs := [][]interface{}{{"alice", "data1", "read"}, {"alice", "data1", "write"}, {"bob", "data1", "read"}}
	got, err := e.BatchEnforce(reqs)
	if err != nil || !reflect.DeepEqual(got, []bool{true, false, false}) {
		t.Fatalf("got=%v err=%v", got, err)
	}
}

// Verifies: CAS-ENF-003
func TestCAS011ABACStructAndMapFields(t *testing.T) {
	text := `[request_definition]
r = sub, obj
[policy_definition]
p = sub
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub == p.sub && r.obj.Owner == r.sub`
	e := mustEnforcer(t, text)
	add(t, e, "alice")
	type resource struct{ Owner string }
	for _, obj := range []interface{}{resource{Owner: "alice"}, map[string]interface{}{"Owner": "alice"}} {
		ok, err := e.Enforce("alice", obj)
		if err != nil || !ok {
			t.Fatalf("%T: %v %v", obj, ok, err)
		}
	}
}

// Verifies: CAS-ENF-004
func TestCAS012BuiltInPathAndRegexMatchers(t *testing.T) {
	for _, fn := range []string{"keyMatch", "keyMatch2", "regexMatch", "globMatch"} {
		text := `[request_definition]
r = obj
[policy_definition]
p = obj
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = ` + fn + `(r.obj, p.obj)`
		e := mustEnforcer(t, text)
		pattern := "/book/*"
		if fn == "keyMatch2" {
			pattern = "/book/:id"
		} else if fn == "regexMatch" {
			pattern = "^/book/[0-9]+$"
		} else if fn == "globMatch" {
			pattern = "/book/**"
		}
		add(t, e, pattern)
		ok, err := e.Enforce("/book/12")
		if err != nil || !ok {
			t.Fatalf("%s: %v %v", fn, ok, err)
		}
	}
}

// Verifies: CAS-ENF-006
func TestCAS013DenyOverride(t *testing.T) {
	text := `[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act, eft
[policy_effect]
e = !some(where (p.eft == deny))
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`
	e := mustEnforcer(t, text)
	add(t, e, "alice", "data1", "read", "allow")
	add(t, e, "alice", "data1", "read", "deny")
	if ok, err := e.Enforce("alice", "data1", "read"); err != nil || ok {
		t.Fatalf("deny override: %v %v", ok, err)
	}
}

// Verifies: CAS-ENF-007
func TestCAS014PriorityEffect(t *testing.T) {
	text := `[request_definition]
r = sub, obj, act
[policy_definition]
p = priority, sub, obj, act, eft
[policy_effect]
e = priority(p.eft) || deny
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`
	m := mustModel(t, text)
	a := stringadapter.NewAdapter("p, 20, alice, data1, read, allow\np, 10, alice, data1, read, deny")
	e, err := casbin.NewEnforcer(m, a)
	if err != nil {
		t.Fatal(err)
	}
	if ok, err := e.Enforce("alice", "data1", "read"); err != nil || ok {
		t.Fatalf("priority: %v %v", ok, err)
	}
}

// Verifies: CAS-STA-002
func TestCAS015ReturnedPolicyIsCallerOwned(t *testing.T) {
	e := mustEnforcer(t, aclText)
	add(t, e, "alice", "data1", "read")
	p, err := e.GetPolicy()
	if err != nil {
		t.Fatal(err)
	}
	p[0][0] = "mallory"
	stored, _ := e.HasPolicy("alice", "data1", "read")
	changed, _ := e.HasPolicy("mallory", "data1", "read")
	if !stored || changed {
		t.Fatalf("caller mutation leaked: stored=%v changed=%v", stored, changed)
	}
}
