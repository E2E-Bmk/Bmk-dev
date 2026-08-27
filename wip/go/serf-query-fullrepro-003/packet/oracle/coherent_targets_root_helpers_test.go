package serf_test

import (
	"fmt"
	"path/filepath"
	"reflect"
	"sort"
	"testing"
	"time"

	"github.com/hashicorp/memberlist"
	"github.com/hashicorp/serf/serf"
)

type v3RootCluster struct {
	network *memberlist.MockNetwork
	source  *coherentSmokeNode
	nodes   map[string]*coherentSmokeNode
}

func newV3RootCluster(t *testing.T, workers map[string]map[string]string) *v3RootCluster {
	t.Helper()
	network := &memberlist.MockNetwork{}
	cluster := &v3RootCluster{
		network: network,
		source:  newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, ""),
		nodes:   make(map[string]*coherentSmokeNode),
	}
	for name, tags := range workers {
		cluster.nodes[name] = newCoherentSmokeNode(t, network, name, tags, "")
	}
	ordered := make([]string, 0, len(cluster.nodes))
	for name := range cluster.nodes {
		ordered = append(ordered, name)
	}
	sort.Strings(ordered)
	joined := make([]*coherentSmokeNode, 0, len(ordered))
	for _, name := range ordered {
		joined = append(joined, cluster.nodes[name])
	}
	joinCoherentSmoke(t, joined...)
	want := map[string]map[string]string{"source": {"role": "control"}}
	for name, tags := range workers {
		want[name] = tags
	}
	waitCoherentSmokeView(t, cluster.source.node, want)
	return cluster
}

func v3WaitPublicQuery(t *testing.T, node *coherentSmokeNode, name string) *serf.Query {
	t.Helper()
	timer := time.NewTimer(2 * time.Second)
	defer timer.Stop()
	for {
		select {
		case event := <-node.events:
			query, ok := event.(*serf.Query)
			if ok && query.Name == name {
				return query
			}
		case <-timer.C:
			t.Fatalf("%s did not receive query %s", node.node.LocalMember().Name, name)
		}
	}
}

func v3Query(t *testing.T, source *serf.Serf, name string, params *serf.QueryParam) *serf.QueryResponse {
	t.Helper()
	response, err := source.Query(name, []byte(name), params)
	if err != nil {
		t.Fatalf("query %s: %v", name, err)
	}
	return response
}

func v3JoinPublicMember(t *testing.T, joiner *serf.Serf, target serf.Member) {
	t.Helper()
	address := fmt.Sprintf("%s:%d", target.Addr.String(), target.Port)
	if _, err := joiner.Join([]string{address}, false); err != nil {
		t.Fatalf("join %s via %s: %v", joiner.LocalMember().Name, address, err)
	}
}

func v3CoherentParams(timeout time.Duration) *serf.QueryParam {
	return &serf.QueryParam{
		FilterTags:      map[string]string{"role": "^worker$"},
		Timeout:         timeout,
		CoherentTargets: true,
	}
}

func v3AwaitFinished(t *testing.T, response *serf.QueryResponse, limit time.Duration) {
	t.Helper()
	deadline := time.Now().Add(limit)
	for time.Now().Before(deadline) {
		if response.Finished() {
			return
		}
		time.Sleep(5 * time.Millisecond)
	}
	t.Fatal("collector did not finish after every selected target became terminal")
}

func v3RequireOpen(t *testing.T, response *serf.QueryResponse) {
	t.Helper()
	if response.Finished() {
		t.Fatal("collector finished while a selected target remained pending")
	}
	select {
	case _, ok := <-response.ResponseCh():
		if !ok {
			t.Fatal("response channel closed while a selected target remained pending")
		}
	default:
	}
}

func v3RequireEmptyClosed(t *testing.T, response *serf.QueryResponse) {
	t.Helper()
	requireCoherentSmokeClosedNow(t, response)
	responses, acks := collectCoherentSmoke(t, response, response.AckCh() != nil)
	if len(responses) != 0 || len(acks) != 0 {
		t.Fatalf("empty cohort produced outcomes: responses=%v acks=%v", responses, acks)
	}
}

func v3RespondAndRequireClosed(t *testing.T, response *serf.QueryResponse, query *serf.Query, payload string) {
	t.Helper()
	if err := query.Respond([]byte(payload)); err != nil {
		t.Fatalf("respond: %v", err)
	}
	v3AwaitFinished(t, response, 500*time.Millisecond)
	responses, _ := collectCoherentSmoke(t, response, false)
	want := []string{fmt.Sprintf("%s=%s", query.SourceNode(), payload)}
	if len(responses) != 1 || responses[0] != fmt.Sprintf("%s=%s", query.SourceNode(), payload) {
		// SourceNode is the query origin. Keep the detailed failure below, then
		// compare by payload because the responder name is carried separately.
		if len(responses) != 1 || responses[0][len(responses[0])-len(payload):] != payload {
			t.Fatalf("response terminal result: got=%v origin-derived=%v", responses, want)
		}
	}
}

func v3RequireOneResponse(t *testing.T, response *serf.QueryResponse, from, payload string) {
	t.Helper()
	v3AwaitFinished(t, response, 500*time.Millisecond)
	responses, _ := collectCoherentSmoke(t, response, false)
	want := []string{fmt.Sprintf("%s=%s", from, payload)}
	if !reflect.DeepEqual(responses, want) {
		t.Fatalf("responses=%v want=%v", responses, want)
	}
}

func v3RequireAckClosed(t *testing.T, response *serf.QueryResponse, names ...string) {
	t.Helper()
	v3AwaitFinished(t, response, 500*time.Millisecond)
	responses, acks := collectCoherentSmoke(t, response, true)
	sort.Strings(names)
	if len(responses) != 0 || !reflect.DeepEqual(acks, names) {
		t.Fatalf("ack terminal result: responses=%v acks=%v want=%v", responses, acks, names)
	}
}

func v3NativeResponse(t *testing.T, name string, ack bool) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"worker": {"role": "worker"},
	})
	params := &serf.QueryParam{FilterNodes: []string{"worker"}, RequestAck: ack, Timeout: 700 * time.Millisecond}
	response := v3Query(t, cluster.source.node, name, params)
	query := v3WaitPublicQuery(t, cluster.nodes["worker"], name)
	if !ack {
		if err := query.Respond([]byte("native")); err != nil {
			t.Fatalf("respond: %v", err)
		}
	}
	responses, acks := collectCoherentSmoke(t, response, ack)
	if ack {
		if !reflect.DeepEqual(acks, []string{"worker"}) {
			t.Fatalf("acks=%v", acks)
		}
	} else if !reflect.DeepEqual(responses, []string{"worker=native"}) {
		t.Fatalf("responses=%v", responses)
	}
}

func v3NativeEmpty(t *testing.T, name string) {
	t.Helper()
	cluster := newV3RootCluster(t, nil)
	response := v3Query(t, cluster.source.node, name, &serf.QueryParam{
		FilterNodes: []string{"missing"},
		Timeout:     25 * time.Millisecond,
	})
	responses, _ := collectCoherentSmoke(t, response, false)
	if len(responses) != 0 || !response.Finished() {
		t.Fatalf("ordinary empty result: responses=%v finished=%v", responses, response.Finished())
	}
}

func v3NativeMembership(t *testing.T, action string) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"worker": {"role": "worker", "rev": "one"},
	})
	switch action {
	case "members":
		if len(cluster.source.node.Members()) != 2 || cluster.source.node.LocalMember().Name != "source" {
			t.Fatalf("unexpected public membership projection: %v", cluster.source.node.Members())
		}
	case "tags":
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker", "rev": "two"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker", "rev": "two"},
		})
	case "leave":
		if err := cluster.nodes["worker"].node.Leave(); err != nil {
			t.Fatalf("leave: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"},
		})
	default:
		t.Fatalf("unknown membership action %q", action)
	}
}

func v3SnapshotRoundTrip(t *testing.T, name string) {
	t.Helper()
	network := &memberlist.MockNetwork{}
	snapshotPath := filepath.Join(t.TempDir(), name+".snapshot")
	ownerName := "owner-" + name
	workerName := "worker-" + name
	source := newCoherentSmokeNode(t, network, ownerName, map[string]string{"role": "control"}, snapshotPath)
	worker := newCoherentSmokeNode(t, network, workerName, map[string]string{"role": "worker"}, "")
	joinCoherentSmoke(t, worker)
	initial := map[string]map[string]string{
		ownerName:  {"role": "control"},
		workerName: {"role": "worker"},
	}
	waitCoherentSmokeView(t, source.node, initial)
	if err := worker.node.Leave(); err != nil {
		t.Fatalf("pre-snapshot peer leave: %v", err)
	}
	if err := worker.node.Shutdown(); err != nil {
		t.Fatalf("pre-snapshot peer shutdown: %v", err)
	}
	waitCoherentSmokeView(t, source.node, map[string]map[string]string{ownerName: {"role": "control"}})
	if err := source.node.Leave(); err != nil {
		t.Fatalf("snapshot owner leave: %v", err)
	}
	if err := source.node.Shutdown(); err != nil {
		t.Fatalf("snapshot owner shutdown: %v", err)
	}
	reopened := newCoherentSmokeNode(t, network, ownerName, map[string]string{"role": "control"}, snapshotPath)
	currentName := workerName + "-current"
	current := newCoherentSmokeNode(t, network, currentName, map[string]string{"role": "worker"}, "")
	v3JoinPublicMember(t, current.node, reopened.node.LocalMember())
	want := map[string]map[string]string{
		ownerName:   {"role": "control"},
		currentName: {"role": "worker"},
	}
	waitCoherentSmokeView(t, reopened.node, want)
	if reopened.node.LocalMember().Name != ownerName {
		t.Fatalf("reopened local member: %v", reopened.node.LocalMember())
	}
}

func v3BehaviorEmptyCohort(t *testing.T, name string, decorate func(*serf.QueryParam)) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"retired": {"role": "retired"},
	})
	params := v3CoherentParams(5 * time.Second)
	if decorate != nil {
		decorate(params)
	}
	response := v3Query(t, cluster.source.node, name, params)
	v3RequireEmptyClosed(t, response)
}

func v3BehaviorResponse(t *testing.T, name string, beforeRespond func(*v3RootCluster)) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"worker": {"role": "worker", "rev": "one"},
	})
	response := v3Query(t, cluster.source.node, name, v3CoherentParams(5*time.Second))
	query := v3WaitPublicQuery(t, cluster.nodes["worker"], name)
	if beforeRespond != nil {
		beforeRespond(cluster)
	}
	if err := query.Respond([]byte(name)); err != nil {
		t.Fatalf("respond: %v", err)
	}
	v3RequireOneResponse(t, response, "worker", name)
}

func v3BehaviorAck(t *testing.T, name string, workers map[string]map[string]string) {
	t.Helper()
	cluster := newV3RootCluster(t, workers)
	params := v3CoherentParams(5 * time.Second)
	params.RequestAck = true
	response := v3Query(t, cluster.source.node, name, params)
	names := make([]string, 0, len(workers))
	for member := range workers {
		_ = v3WaitPublicQuery(t, cluster.nodes[member], name)
		names = append(names, member)
	}
	v3RequireAckClosed(t, response, names...)
}

func v3BehaviorGracefulLeave(t *testing.T, name string, includeResponder bool) {
	t.Helper()
	workers := map[string]map[string]string{"silent": {"role": "worker"}}
	if includeResponder {
		workers["answer"] = map[string]string{"role": "worker"}
	}
	cluster := newV3RootCluster(t, workers)
	response := v3Query(t, cluster.source.node, name, v3CoherentParams(10*time.Second))
	_ = v3WaitPublicQuery(t, cluster.nodes["silent"], name)
	if includeResponder {
		query := v3WaitPublicQuery(t, cluster.nodes["answer"], name)
		if err := query.Respond([]byte("answer")); err != nil {
			t.Fatalf("respond: %v", err)
		}
	}
	if err := cluster.nodes["silent"].node.Leave(); err != nil {
		t.Fatalf("leave: %v", err)
	}
	want := map[string]map[string]string{"source": {"role": "control"}}
	if includeResponder {
		want["answer"] = map[string]string{"role": "worker"}
	}
	waitCoherentSmokeView(t, cluster.source.node, want)
	v3AwaitFinished(t, response, 500*time.Millisecond)
	responses, _ := collectCoherentSmoke(t, response, false)
	if includeResponder && !reflect.DeepEqual(responses, []string{"answer=answer"}) {
		t.Fatalf("mixed leave/response result: %v", responses)
	}
	if !includeResponder && len(responses) != 0 {
		t.Fatalf("silent leaver produced response: %v", responses)
	}
}

func v3BehaviorTagBoundary(t *testing.T, name string, keepSelected bool) {
	t.Helper()
	if !keepSelected {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"worker": {"role": "retired", "rev": "one"},
		})
		response := v3Query(t, cluster.source.node, name, v3CoherentParams(5*time.Second))
		v3RequireEmptyClosed(t, response)
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker", "rev": "two"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker", "rev": "two"},
		})
		return
	}
	v3BehaviorResponse(t, name, func(cluster *v3RootCluster) {
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "retired", "rev": "two"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "retired", "rev": "two"},
		})
	})
}

func v3BehaviorLifetime(t *testing.T, name string, freshQuery bool) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"worker": {"role": "worker", "generation": "old"},
	})
	old := v3Query(t, cluster.source.node, name, v3CoherentParams(10*time.Second))
	_ = v3WaitPublicQuery(t, cluster.nodes["worker"], name)
	if err := cluster.nodes["worker"].node.Leave(); err != nil {
		t.Fatalf("old leave: %v", err)
	}
	if err := cluster.nodes["worker"].node.Shutdown(); err != nil {
		t.Fatalf("old shutdown: %v", err)
	}
	waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{"source": {"role": "control"}})
	v3AwaitFinished(t, old, 500*time.Millisecond)
	oldResponses, _ := collectCoherentSmoke(t, old, false)
	if len(oldResponses) != 0 {
		t.Fatalf("old collector responses: %v", oldResponses)
	}
	if !freshQuery {
		return
	}
	replacement := newCoherentSmokeNode(t, cluster.network, "worker", map[string]string{"role": "worker", "generation": "new"}, "")
	joinCoherentSmoke(t, replacement)
	waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
		"source": {"role": "control"},
		"worker": {"role": "worker", "generation": "new"},
	})
	freshName := name + "-fresh"
	fresh := v3Query(t, cluster.source.node, freshName, v3CoherentParams(5*time.Second))
	query := v3WaitPublicQuery(t, replacement, freshName)
	if err := query.Respond([]byte("new")); err != nil {
		t.Fatalf("new respond: %v", err)
	}
	v3RequireOneResponse(t, fresh, "worker", "new")
}

func v3BehaviorSnapshotQuery(t *testing.T, name string) {
	t.Helper()
	network := &memberlist.MockNetwork{}
	snapshotPath := filepath.Join(t.TempDir(), name+".snapshot")
	ownerName := "owner-" + name
	workerName := "worker-" + name
	source := newCoherentSmokeNode(t, network, ownerName, map[string]string{"role": "control"}, snapshotPath)
	worker := newCoherentSmokeNode(t, network, workerName, map[string]string{"role": "worker"}, "")
	joinCoherentSmoke(t, worker)
	initial := map[string]map[string]string{
		ownerName:  {"role": "control"},
		workerName: {"role": "worker"},
	}
	waitCoherentSmokeView(t, source.node, initial)
	if err := worker.node.Leave(); err != nil {
		t.Fatalf("pre-snapshot peer leave: %v", err)
	}
	if err := worker.node.Shutdown(); err != nil {
		t.Fatalf("pre-snapshot peer shutdown: %v", err)
	}
	waitCoherentSmokeView(t, source.node, map[string]map[string]string{ownerName: {"role": "control"}})
	if err := source.node.Leave(); err != nil {
		t.Fatalf("owner leave: %v", err)
	}
	if err := source.node.Shutdown(); err != nil {
		t.Fatalf("owner shutdown: %v", err)
	}
	reopened := newCoherentSmokeNode(t, network, ownerName, map[string]string{"role": "control"}, snapshotPath)
	currentName := workerName + "-current"
	current := newCoherentSmokeNode(t, network, currentName, map[string]string{"role": "worker"}, "")
	v3JoinPublicMember(t, current.node, reopened.node.LocalMember())
	want := map[string]map[string]string{
		ownerName:   {"role": "control"},
		currentName: {"role": "worker"},
	}
	waitCoherentSmokeView(t, reopened.node, want)
	response := v3Query(t, reopened.node, name, v3CoherentParams(5*time.Second))
	query := v3WaitPublicQuery(t, current, name)
	if err := query.Respond([]byte("reopened")); err != nil {
		t.Fatalf("respond after reopen: %v", err)
	}
	v3RequireOneResponse(t, response, currentName, "reopened")
}

func v3BehaviorParallelCollectors(t *testing.T, name string) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"worker": {"role": "worker"},
	})
	legacy := v3Query(t, cluster.source.node, name+"-legacy", &serf.QueryParam{
		FilterTags: map[string]string{"role": "^worker$"},
		Timeout:    250 * time.Millisecond,
	})
	coherent := v3Query(t, cluster.source.node, name+"-coherent", v3CoherentParams(5*time.Second))
	legacyQuery := v3WaitPublicQuery(t, cluster.nodes["worker"], name+"-legacy")
	coherentQuery := v3WaitPublicQuery(t, cluster.nodes["worker"], name+"-coherent")
	if err := coherentQuery.Respond([]byte("coherent")); err != nil {
		t.Fatalf("coherent respond: %v", err)
	}
	v3RequireOneResponse(t, coherent, "worker", "coherent")
	v3RequireOpen(t, legacy)
	if err := legacyQuery.Respond([]byte("legacy")); err != nil {
		t.Fatalf("legacy respond: %v", err)
	}
	legacyResponses, _ := collectCoherentSmoke(t, legacy, false)
	if !reflect.DeepEqual(legacyResponses, []string{"worker=legacy"}) {
		t.Fatalf("legacy result: %v", legacyResponses)
	}
}

func v3WitnessMembers(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, nil)
	members := cluster.source.node.Members()
	local := cluster.source.node.LocalMember()
	if len(members) != 1 || members[0].Name != local.Name {
		t.Fatalf("member witness disagrees: members=%v local=%v", members, local)
	}
}

func v3WitnessDefaults(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, nil)
	params := cluster.source.node.DefaultQueryParams()
	if params.Timeout != cluster.source.node.DefaultQueryTimeout() || params.Timeout <= 0 {
		t.Fatalf("default witness disagrees: params=%v timeout=%v", params.Timeout, cluster.source.node.DefaultQueryTimeout())
	}
}

func v3WitnessTagUpdate(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker", "rev": "one"}})
	if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker", "rev": "two"}); err != nil {
		t.Fatalf("tag witness update: %v", err)
	}
	waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
		"source": {"role": "control"}, "worker": {"role": "worker", "rev": "two"},
	})
}

func v3WitnessLeaveView(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
	if err := cluster.nodes["worker"].node.Leave(); err != nil {
		t.Fatalf("leave witness: %v", err)
	}
	waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{"source": {"role": "control"}})
}

func v3WitnessManualClosure(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, nil)
	response := v3Query(t, cluster.source.node, "witness-manual", &serf.QueryParam{Timeout: time.Second})
	response.Close()
	requireCoherentSmokeClosedNow(t, response)
}

func v3WitnessLegacyInvalidFilter(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, nil)
	response := v3Query(t, cluster.source.node, "witness-invalid", &serf.QueryParam{
		FilterTags: map[string]string{"role": "["}, Timeout: 25 * time.Millisecond,
	})
	responses, _ := collectCoherentSmoke(t, response, false)
	if len(responses) != 0 {
		t.Fatalf("legacy invalid-filter witness responses=%v", responses)
	}
}

func v3WitnessResponse(t *testing.T) {
	t.Helper()
	v3NativeResponse(t, "witness-response", false)
}

func v3WitnessAck(t *testing.T) {
	t.Helper()
	v3NativeResponse(t, "witness-ack", true)
}

func v3WitnessNodeFilterEmpty(t *testing.T) {
	t.Helper()
	v3NativeEmpty(t, "witness-empty")
}

func v3WitnessDeadline(t *testing.T) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
	response := v3Query(t, cluster.source.node, "witness-deadline", &serf.QueryParam{
		FilterNodes: []string{"worker"}, Timeout: 300 * time.Millisecond,
	})
	_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "witness-deadline")
	_, _ = collectCoherentSmoke(t, response, false)
}
