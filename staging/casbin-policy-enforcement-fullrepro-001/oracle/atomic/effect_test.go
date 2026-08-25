package atomic

import "testing"

func TestAllowOverrideEffect(t *testing.T) {
	e := mkEnforcer(t, aclModel)
	e.AddPolicy("alice", "data1", "read")
	e.AddPolicy("bob", "data2", "write")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, true, "bob", "data2", "write")
	mustEnforce(t, e, false, "alice", "data2", "write")
}

func TestDenyOverrideVeto(t *testing.T) {
	e := mkEnforcer(t, aclEftModel)
	e.AddPolicy("alice", "data1", "read", "allow")
	e.AddPolicy("alice", "data1", "read", "deny")
	mustEnforce(t, e, false, "alice", "data1", "read")
}

func TestDenyOverrideAllowOnly(t *testing.T) {
	e := mkEnforcer(t, aclEftModel)
	e.AddPolicy("alice", "data1", "read", "allow")
	mustEnforce(t, e, true, "alice", "data1", "read")
	mustEnforce(t, e, false, "bob", "data1", "read")
}

func TestDenyRuleAloneDoesNotAllow(t *testing.T) {
	e := mkEnforcer(t, aclEftModel)
	e.AddPolicy("alice", "data1", "read", "deny")
	mustEnforce(t, e, false, "alice", "data1", "read")
}

func TestPriorityFirstMatchDecides(t *testing.T) {
	e := mkEnforcer(t, priorityModel)
	e.AddPolicy("alice", "data1", "read", "deny")
	e.AddPolicy("alice", "data1", "read", "allow")
	mustEnforce(t, e, false, "alice", "data1", "read")

	e2 := mkEnforcer(t, priorityModel)
	e2.AddPolicy("alice", "data1", "read", "allow")
	e2.AddPolicy("alice", "data1", "read", "deny")
	mustEnforce(t, e2, true, "alice", "data1", "read")
}

func TestPriorityNoMatchDenies(t *testing.T) {
	e := mkEnforcer(t, priorityModel)
	e.AddPolicy("alice", "data1", "read", "allow")
	mustEnforce(t, e, false, "stranger", "data1", "read")
}
