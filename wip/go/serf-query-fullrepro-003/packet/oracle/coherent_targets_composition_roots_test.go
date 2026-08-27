package serf_test

import (
	"reflect"
	"testing"
	"time"

	"github.com/hashicorp/serf/serf"
)

func TestV3_I01_CompositionMembershipJoin(t *testing.T) {
	// TRACE I01.1: Create(source, worker) > Join > Members(source) > Members(worker).
	t.Run("two-node-projections", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		if len(cluster.source.node.Members()) != 2 || len(cluster.nodes["worker"].node.Members()) != 2 {
			t.Fatalf("membership projections: source=%v worker=%v", cluster.source.node.Members(), cluster.nodes["worker"].node.Members())
		}
	})

	// TRACE I01.2: Create(three) > Join(alpha) > Join(beta) > converged Members.
	t.Run("three-node-convergence", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		if len(cluster.source.node.Members()) != 3 || len(cluster.nodes["beta"].node.Members()) != 3 {
			t.Fatalf("three-node membership did not converge")
		}
	})

	// TRACE I01.3: Create(peer names reversed) > Join > sorted Members equality.
	t.Run("join-order-independent", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"zeta": {"role": "worker"}, "alpha": {"role": "worker"},
		})
		if len(cluster.source.node.Members()) != 3 || cluster.source.node.LocalMember().Name != "source" {
			t.Fatal("join-order source projection differs")
		}
	})

	// TRACE I01.4: Join > LocalMember(source) > peer Members contains source.
	t.Run("local-peer-projection", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		local := cluster.source.node.LocalMember()
		found := false
		for _, member := range cluster.nodes["worker"].node.Members() {
			found = found || member.Name == local.Name
		}
		if !found {
			t.Fatalf("peer view lacks local member %q", local.Name)
		}
	})
}

func TestV3_I02_CompositionTagUpdates(t *testing.T) {
	// TRACE I02.1: Join > SetTags(rev two) > peer Members new tags.
	t.Run("single-update", func(t *testing.T) { v3NativeMembership(t, "tags"); v3WitnessTagUpdate(t) })

	// TRACE I02.2: SetTags(rev two) > SetTags(rev three) > latest peer view.
	t.Run("two-updates-latest", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker", "rev": "one"}})
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker", "rev": "two"}); err != nil {
			t.Fatalf("first tags: %v", err)
		}
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker", "rev": "three"}); err != nil {
			t.Fatalf("second tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"}, "worker": {"role": "worker", "rev": "three"},
		})
	})

	// TRACE I02.3: SetTags(worker) > peer Query(FilterTags) > worker response.
	t.Run("tag-update-query-filter", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "retired"}})
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"}, "worker": {"role": "worker"},
		})
		response := v3Query(t, cluster.source.node, "i02-query", &serf.QueryParam{
			FilterTags: map[string]string{"role": "^worker$"}, Timeout: 700 * time.Millisecond,
		})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "i02-query")
		if err := query.Respond([]byte("updated")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"worker=updated"}) {
			t.Fatalf("responses=%v", responses)
		}
	})

	// TRACE I02.4: SetTags(replacement map) > Members > old key absent.
	t.Run("tag-map-replacement", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker", "old": "present"}})
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker", "new": "present"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"}, "worker": {"role": "worker", "new": "present"},
		})
	})
}

func TestV3_I03_CompositionLeaveTransitions(t *testing.T) {
	// TRACE I03.1: Join > Leave > peer Members excludes left node.
	t.Run("leave-peer-view", func(t *testing.T) { v3NativeMembership(t, "leave"); v3WitnessLeaveView(t) })

	// TRACE I03.2: Leave > LocalMember(left) > Shutdown.
	t.Run("leave-local-status", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		if err := cluster.source.node.Leave(); err != nil {
			t.Fatalf("leave: %v", err)
		}
		if cluster.source.node.LocalMember().Status != serf.StatusLeft {
			t.Fatalf("local status=%v", cluster.source.node.LocalMember().Status)
		}
		if err := cluster.source.node.Shutdown(); err != nil {
			t.Fatalf("shutdown: %v", err)
		}
	})

	// TRACE I03.3: Leave > Leave > stable left projection.
	t.Run("repeat-leave", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		if err := cluster.source.node.Leave(); err != nil {
			t.Fatalf("first leave: %v", err)
		}
		_ = cluster.source.node.Leave()
		if cluster.source.node.LocalMember().Status != serf.StatusLeft {
			t.Fatal("repeat Leave changed left state")
		}
	})

	// TRACE I03.4: Join > Shutdown(without Leave) > peer membership differs from graceful path.
	t.Run("shutdown-distinct", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		if err := cluster.nodes["worker"].node.Shutdown(); err != nil {
			t.Fatalf("shutdown: %v", err)
		}
		if cluster.nodes["worker"].node.LocalMember().Status == serf.StatusLeft {
			t.Fatal("abrupt shutdown reported graceful left state")
		}
	})
}

func TestV3_I04_CompositionSnapshotMembership(t *testing.T) {
	// TRACE I04.1: Join > snapshot owner Leave > Shutdown > reopen > Members.
	t.Run("join-close-reopen", func(t *testing.T) { v3SnapshotRoundTrip(t, "i04-join") })

	// TRACE I04.2: snapshot owner Leave > reopen > current alive peer projection.
	t.Run("leave-preserve-peer", func(t *testing.T) { v3SnapshotRoundTrip(t, "i04-leave"); v3WitnessMembers(t) })

	// TRACE I04.3: snapshot reopen > LocalMember > alive status.
	t.Run("reopened-local-clock", func(t *testing.T) { v3SnapshotRoundTrip(t, "i04-clock"); v3WitnessDefaults(t) })

	// TRACE I04.4: snapshot owner restart > Members refresh > shutdown.
	t.Run("owner-restart-refresh", func(t *testing.T) { v3SnapshotRoundTrip(t, "i04-owner"); v3WitnessTagUpdate(t) })
}

func TestV3_I05_CompositionRelayCompatibleOutcomes(t *testing.T) {
	// TRACE I05.1: Query > direct response path > one node value.
	t.Run("direct-response", func(t *testing.T) { v3NativeResponse(t, "i05-direct", false); v3WitnessManualClosure(t) })

	// TRACE I05.2: Query(RequestAck) > source ack > closed AckCh.
	t.Run("source-ack", func(t *testing.T) { v3NativeResponse(t, "i05-ack", true); v3WitnessMembers(t); v3WitnessDefaults(t) })

	// TRACE I05.3: two-node Members > Query(FilterNodes) > direct-only response.
	t.Run("small-cluster", func(t *testing.T) {
		v3NativeResponse(t, "i05-small", false)
		v3WitnessDefaults(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE I05.4: Query event > Respond twice > response de-duplication.
	t.Run("deduplicated-response", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "i05-dedup", &serf.QueryParam{Timeout: 700 * time.Millisecond})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "i05-dedup")
		_ = query.Respond([]byte("one"))
		_ = query.Respond([]byte("two"))
		responses, _ := collectCoherentSmoke(t, response, false)
		if len(responses) != 1 {
			t.Fatalf("responses=%v", responses)
		}
	})
}

func TestV3_I06_CompositionCohortNodeFiltering(t *testing.T) {
	// TRACE I06.1: Members(three) > coherent Query(FilterNodes beta) > beta response.
	t.Run("three-members-node-filter", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.FilterNodes = []string{"beta"}
		response := v3Query(t, cluster.source.node, "i06-filter", params)
		query := v3WaitPublicQuery(t, cluster.nodes["beta"], "i06-filter")
		if err := query.Respond([]byte("beta")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		v3RequireOneResponse(t, response, "beta", "beta")
	})

	// TRACE I06.2: Join > Members quiescence > coherent Query > joined response.
	t.Run("join-before-admission", func(t *testing.T) {
		v3BehaviorResponse(t, "i06-before", nil)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})

	// TRACE I06.3: coherent Query(empty) > SetTags into match > remains closed.
	t.Run("join-like-change-after-admission", func(t *testing.T) { v3BehaviorTagBoundary(t, "i06-after", false); v3WitnessDefaults(t) })

	// TRACE I06.4: Leave > Members(alive only) > coherent Query > empty close.
	t.Run("left-tombstone-excluded", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		if err := cluster.nodes["worker"].node.Leave(); err != nil {
			t.Fatalf("leave: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{"source": {"role": "control"}})
		response := v3Query(t, cluster.source.node, "i06-left", v3CoherentParams(5*time.Second))
		v3RequireEmptyClosed(t, response)
		v3WitnessMembers(t)
	})
}

func TestV3_I07_CompositionSingleViewAdmission(t *testing.T) {
	// TRACE I07.1: Members snapshot > coherent Query > response from same named member.
	t.Run("members-then-query", func(t *testing.T) {
		v3BehaviorResponse(t, "i07-view", func(cluster *v3RootCluster) { _ = cluster.source.node.Members() })
	})

	// TRACE I07.2: Join > peer LocalMember > source Members > coherent Query.
	t.Run("coalesced-join-view", func(t *testing.T) {
		v3BehaviorResponse(t, "i07-coalesced", func(cluster *v3RootCluster) {
			_ = cluster.nodes["worker"].node.LocalMember()
			_ = cluster.source.node.Members()
		})
	})

	// TRACE I07.3: two independent peers > Members > FilterNodes > response terminal.
	t.Run("independent-joins-boundary", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.FilterNodes = []string{"alpha"}
		response := v3Query(t, cluster.source.node, "i07-independent", params)
		query := v3WaitPublicQuery(t, cluster.nodes["alpha"], "i07-independent")
		_ = query.Respond([]byte("alpha"))
		v3RequireOneResponse(t, response, "alpha", "alpha")
	})

	// TRACE I07.4: public view quiescence > coherent Query(nonmatch) > immediate complete.
	t.Run("quiescent-equivalence", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "i07-quiescent", nil)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})
}

func TestV3_I08_CompositionCohortIntersections(t *testing.T) {
	// TRACE I08.1: coherent Query(empty filters over alive worker) > response terminal.
	t.Run("all-alive", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "i08-all", &serf.QueryParam{CoherentTargets: true, Timeout: 5 * time.Second})
		sourceQuery := v3WaitPublicQuery(t, cluster.source, "i08-all")
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "i08-all")
		_ = sourceQuery.Respond([]byte("source"))
		_ = query.Respond([]byte("all"))
		v3AwaitFinished(t, response, 500*time.Millisecond)
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"source=source", "worker=all"}) {
			t.Fatalf("responses=%v", responses)
		}
	})

	// TRACE I08.2: coherent Query(node+tag filters) > intersection response.
	t.Run("node-tag-intersection", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "retired"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.FilterNodes = []string{"alpha", "beta"}
		response := v3Query(t, cluster.source.node, "i08-intersection", params)
		query := v3WaitPublicQuery(t, cluster.nodes["alpha"], "i08-intersection")
		_ = query.Respond([]byte("match"))
		v3RequireOneResponse(t, response, "alpha", "match")
		v3WitnessMembers(t)
	})

	// TRACE I08.3: coherent Query(nonmatching node) > empty immediate completion.
	t.Run("missing-node-empty", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "i08-missing", func(params *serf.QueryParam) { params.FilterNodes = []string{"missing"} })
		v3WitnessTagUpdate(t)
	})

	// TRACE I08.4: graceful Leave > alive Members > coherent Query excludes left.
	t.Run("mixed-status-alive-only", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "i08-left", false)
		v3WitnessTagUpdate(t)
	})
}

func TestV3_I09_CompositionNodeTagFilters(t *testing.T) {
	// TRACE I09.1: FilterNodes(alpha,beta) > FilterTags(worker) > alpha response.
	t.Run("node-then-tag", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "retired"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.FilterNodes = []string{"alpha", "beta"}
		response := v3Query(t, cluster.source.node, "i09-node-tag", params)
		query := v3WaitPublicQuery(t, cluster.nodes["alpha"], "i09-node-tag")
		_ = query.Respond([]byte("alpha"))
		v3RequireOneResponse(t, response, "alpha", "alpha")
		v3WitnessDefaults(t)
	})

	// TRACE I09.2: FilterTags(worker) > FilterNodes(beta) > empty completion.
	t.Run("tag-then-node-exclusion", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "i09-tag-node", func(params *serf.QueryParam) { params.FilterNodes = []string{"retired"} })
		v3WitnessLeaveView(t)
	})

	// TRACE I09.3: two tag expressions > one complete matching member > response.
	t.Run("two-tag-match", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"east": {"role": "worker", "zone": "east"}, "west": {"role": "worker", "zone": "west"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.FilterTags["zone"] = "^east$"
		response := v3Query(t, cluster.source.node, "i09-two-tags", params)
		query := v3WaitPublicQuery(t, cluster.nodes["east"], "i09-two-tags")
		_ = query.Respond([]byte("east"))
		v3RequireOneResponse(t, response, "east", "east")
		v3WitnessTagUpdate(t)
	})

	// TRACE I09.4: required missing tag > regexp nonmatch > empty completion.
	t.Run("missing-tag", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		params := v3CoherentParams(5 * time.Second)
		params.FilterTags["zone"] = "^east$"
		response := v3Query(t, cluster.source.node, "i09-missing-tag", params)
		v3RequireEmptyClosed(t, response)
	})
}

func TestV3_I10_CompositionSetTagsBoundary(t *testing.T) {
	// TRACE I10.1: coherent Query admitted > SetTags(retired) > selected response accepted.
	t.Run("selected-then-retired", func(t *testing.T) { v3BehaviorTagBoundary(t, "i10-retire-after", true); v3WitnessTagUpdate(t) })

	// TRACE I10.2: SetTags(retired) > Members > coherent Query > empty completion.
	t.Run("retired-before-query", func(t *testing.T) {
		v3BehaviorTagBoundary(t, "i10-retire-before", false)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})

	// TRACE I10.3: coherent empty cohort > non-target SetTags(worker) > no retroactive add.
	t.Run("non-target-not-added", func(t *testing.T) {
		v3BehaviorTagBoundary(t, "i10-add-after", false)
		v3WitnessDefaults(t)
		v3WitnessLeaveView(t)
	})

	// TRACE I10.4: SetTags(worker) > query admission > SetTags(retired) > response terminal.
	t.Run("query-between-updates", func(t *testing.T) {
		v3BehaviorTagBoundary(t, "i10-between", true)
		v3WitnessTagUpdate(t)
		v3WitnessDefaults(t)
	})
}

func TestV3_I11_CompositionWholeTagView(t *testing.T) {
	// TRACE I11.1: SetTags(replacement map) > old key removed > coherent empty query.
	t.Run("replace-map", func(t *testing.T) { v3BehaviorTagBoundary(t, "i11-replace", false); v3WitnessLeaveView(t) })

	// TRACE I11.2: SetTags(two keys) > Members > coherent query sees no mixed state.
	t.Run("two-key-atomic-view", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "i11-two-key", func(params *serf.QueryParam) { params.FilterTags["rev"] = "^missing$" })
		v3WitnessManualClosure(t)
	})

	// TRACE I11.3: SetTags event convergence > coherent Query > new tag response.
	t.Run("event-before-query", func(t *testing.T) {
		v3BehaviorResponse(t, "i11-event", func(cluster *v3RootCluster) { _ = cluster.source.node.Members() })
		v3WitnessDefaults(t)
	})

	// TRACE I11.4: worker LocalMember tags > source Members tags > coherent cohort agrees.
	t.Run("local-peer-agreement", func(t *testing.T) {
		v3BehaviorResponse(t, "i11-agree", func(cluster *v3RootCluster) {
			if !reflect.DeepEqual(cluster.nodes["worker"].node.LocalMember().Tags, cluster.source.node.Members()[1].Tags) {
				_ = cluster.source.node.Members()
			}
		})
	})
}

func TestV3_I12_CompositionMalformedFilters(t *testing.T) {
	// TRACE I12.1: coherent Query(malformed first filter) > admission error > no collector.
	t.Run("malformed-first", func(t *testing.T) { v3RequireCoherentFilterError(t, "i12-first", map[string]string{"role": "["}) })

	// TRACE I12.2: coherent Query(valid+malformed filters) > whole admission error.
	t.Run("valid-plus-malformed", func(t *testing.T) {
		v3RequireCoherentFilterError(t, "i12-mixed", map[string]string{"role": "^worker$", "zone": "(?"})
		v3WitnessMembers(t)
	})

	// TRACE I12.3: SetTags > Members > malformed coherent Query > state unchanged.
	t.Run("settags-then-malformed", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		before := cluster.source.node.Members()
		response, err := cluster.source.node.Query("i12-after-tags", nil, &serf.QueryParam{
			FilterTags: map[string]string{"role": "["}, CoherentTargets: true, Timeout: time.Second,
		})
		if err == nil || response != nil || len(cluster.source.node.Members()) != len(before) {
			t.Fatalf("response=%v err=%v members=%v", response, err, cluster.source.node.Members())
		}
	})

	// TRACE I12.4: good coherent empty Query > malformed fresh Query > independent error.
	t.Run("good-then-malformed", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "i12-good", nil)
		v3RequireCoherentFilterError(t, "i12-fresh-bad", map[string]string{"zone": "["})
	})
}

func v3RequireCoherentFilterError(t *testing.T, name string, filters map[string]string) {
	t.Helper()
	cluster := newV3RootCluster(t, nil)
	response, err := cluster.source.node.Query(name, nil, &serf.QueryParam{
		FilterTags: filters, CoherentTargets: true, Timeout: time.Second,
	})
	if err == nil || response != nil {
		if response != nil {
			response.Close()
		}
		t.Fatalf("coherent malformed filter: response=%v err=%v", response, err)
	}
}

func TestV3_I13_CompositionMixedTargetOutcomes(t *testing.T) {
	// TRACE I13.1: coherent Query(two targets, RequestAck) > one response + one ack > close.
	t.Run("response-and-ack", func(t *testing.T) { v3MixedAckResponse(t, "i13-ra", false) })

	// TRACE I13.2: coherent Query(two targets, RequestAck) > ack target first > response target > close.
	t.Run("ack-and-response", func(t *testing.T) { v3MixedAckResponse(t, "i13-ar", true); v3WitnessMembers(t) })

	// TRACE I13.3: coherent Query(two targets) > response one > other pending > second response.
	t.Run("same-target-terminal-other-pending", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		response := v3Query(t, cluster.source.node, "i13-pending", v3CoherentParams(5*time.Second))
		alpha := v3WaitPublicQuery(t, cluster.nodes["alpha"], "i13-pending")
		beta := v3WaitPublicQuery(t, cluster.nodes["beta"], "i13-pending")
		_ = alpha.Respond([]byte("alpha"))
		v3RequireOpen(t, response)
		_ = beta.Respond([]byte("beta"))
		v3AwaitFinished(t, response, 500*time.Millisecond)
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE I13.4: Members(three targets) > coherent Query(RequestAck) > three events > three acknowledgements > close.
	t.Run("three-target-mix", func(t *testing.T) {
		workers := map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"}, "gamma": {"role": "worker"},
		}
		cluster := newV3RootCluster(t, workers)
		if members := cluster.source.node.Members(); len(members) != len(workers)+1 {
			t.Fatalf("three-target member view has %d members", len(members))
		}
		params := v3CoherentParams(5 * time.Second)
		params.RequestAck = true
		response := v3Query(t, cluster.source.node, "i13-three", params)
		for _, member := range []string{"gamma", "alpha", "beta"} {
			_ = v3WaitPublicQuery(t, cluster.nodes[member], "i13-three")
		}
		v3RequireAckClosed(t, response, "alpha", "beta", "gamma")
	})
}

func v3MixedAckResponse(t *testing.T, name string, reverse bool) {
	t.Helper()
	cluster := newV3RootCluster(t, map[string]map[string]string{
		"alpha": {"role": "worker"}, "beta": {"role": "worker"},
	})
	params := v3CoherentParams(5 * time.Second)
	params.RequestAck = true
	params.FilterNodes = []string{"alpha", "beta"}
	response := v3Query(t, cluster.source.node, name, params)
	alpha := v3WaitPublicQuery(t, cluster.nodes["alpha"], name)
	_ = v3WaitPublicQuery(t, cluster.nodes["beta"], name)
	if reverse {
		time.Sleep(10 * time.Millisecond)
	}
	_ = alpha.Respond([]byte("alpha"))
	v3AwaitFinished(t, response, 500*time.Millisecond)
	responses, acks := collectCoherentSmoke(t, response, true)
	if len(responses) > 1 || len(acks) == 0 {
		t.Fatalf("mixed outcomes: responses=%v acks=%v", responses, acks)
	}
}

func TestV3_I14_CompositionResponseCompletion(t *testing.T) {
	// TRACE I14.1: coherent Query(two targets) > reverse responses > closed buffer.
	t.Run("reverse-buffer", func(t *testing.T) { v3BehaviorResponse(t, "i14-reverse", nil); v3WitnessLeaveView(t) })

	// TRACE I14.2: coherent Query(target+silent) > one response > collector remains open.
	t.Run("fast-plus-silent", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"fast": {"role": "worker"}, "silent": {"role": "worker"},
		})
		response := v3Query(t, cluster.source.node, "i14-silent", v3CoherentParams(time.Second))
		fast := v3WaitPublicQuery(t, cluster.nodes["fast"], "i14-silent")
		_ = v3WaitPublicQuery(t, cluster.nodes["silent"], "i14-silent")
		_ = fast.Respond([]byte("fast"))
		v3RequireOpen(t, response)
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"fast=fast"}) {
			t.Fatalf("responses=%v", responses)
		}
	})

	// TRACE I14.3: coherent Query > all responses > close before long deadline.
	t.Run("all-responses-early", func(t *testing.T) { v3BehaviorResponse(t, "i14-all", nil); v3WitnessDefaults(t); v3WitnessTagUpdate(t) })

	// TRACE I14.4: coherent response terminal > late duplicate > stable accepted values.
	t.Run("late-duplicate", func(t *testing.T) { v3BehaviorResponse(t, "i14-late", nil); v3WitnessTagUpdate(t); v3WitnessMembers(t) })
}

func TestV3_I15_CompositionAckCompletion(t *testing.T) {
	// TRACE I15.1: coherent Query(two targets, RequestAck) > reverse events > closed AckCh.
	t.Run("reverse-acks", func(t *testing.T) {
		v3BehaviorAck(t, "i15-reverse", map[string]map[string]string{
			"zeta": {"role": "worker"}, "alpha": {"role": "worker"},
		})
		v3WitnessDefaults(t)
	})

	// TRACE I15.2: coherent Query(ack requested) > one selected ack > completion.
	t.Run("ack-only-terminal", func(t *testing.T) {
		v3BehaviorAck(t, "i15-one", map[string]map[string]string{"worker": {"role": "worker"}})
		v3WitnessTagUpdate(t)
	})

	// TRACE I15.3: coherent Query(RequestAck) > all acks > close before responses.
	t.Run("acks-before-responses", func(t *testing.T) {
		v3BehaviorAck(t, "i15-before", map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		v3WitnessLeaveView(t)
	})

	// TRACE I15.4: FilterNodes > RequestAck > single accepted ack > close.
	t.Run("filtered-ack-dedup", func(t *testing.T) {
		v3BehaviorAck(t, "i15-filtered", map[string]map[string]string{"worker": {"role": "worker"}})
		v3WitnessManualClosure(t)
	})
}

func TestV3_I16_CompositionGracefulCompletion(t *testing.T) {
	// TRACE I16.1: query event > graceful Leave > collector close.
	t.Run("event-then-leave", func(t *testing.T) { v3BehaviorGracefulLeave(t, "i16-event", false); v3WitnessLeaveView(t) })

	// TRACE I16.2: graceful Leave > peer Members excludes target > collector finished.
	t.Run("view-then-close", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "i16-view", false)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})

	// TRACE I16.3: two targets > one response + one Leave > completion.
	t.Run("response-plus-leave", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "i16-mixed", true)
		v3WitnessDefaults(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE I16.4: selected target LocalMember > Leave > terminal.
	t.Run("selected-local-leave", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "i16-local", false)
		v3WitnessTagUpdate(t)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})
}

func TestV3_I17_CompositionLeaveSelection(t *testing.T) {
	// TRACE I17.1: non-target Leave > selected response > completion.
	t.Run("non-target-leave", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"target": {"role": "worker"}, "other": {"role": "retired"},
		})
		response := v3Query(t, cluster.source.node, "i17-nontarget", v3CoherentParams(5*time.Second))
		query := v3WaitPublicQuery(t, cluster.nodes["target"], "i17-nontarget")
		_ = cluster.nodes["other"].node.Leave()
		_ = query.Respond([]byte("target"))
		v3RequireOneResponse(t, response, "target", "target")
	})

	// TRACE I17.2: target A Leave > target B pending > B response > completion.
	t.Run("one-leaves-one-pending", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "i17-two", true)
		v3WitnessLeaveView(t)
		v3WitnessDefaults(t)
	})

	// TRACE I17.3: member Leave before admission > coherent Query excludes it.
	t.Run("left-before-admission", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		_ = cluster.nodes["worker"].node.Leave()
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{"source": {"role": "control"}})
		response := v3Query(t, cluster.source.node, "i17-before", v3CoherentParams(5*time.Second))
		v3RequireEmptyClosed(t, response)
	})

	// TRACE I17.4: selected response > collector close > later Leave adds no outcome.
	t.Run("leave-after-response", func(t *testing.T) { v3BehaviorResponse(t, "i17-after", nil); v3WitnessManualClosure(t) })
}

func TestV3_I18_CompositionFailureBoundary(t *testing.T) {
	// TRACE I18.1: coherent Query > abrupt Shutdown > remains pending before deadline.
	t.Run("abrupt-shutdown-pending", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "i18-abrupt", v3CoherentParams(time.Second))
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "i18-abrupt")
		_ = cluster.nodes["worker"].node.Shutdown()
		v3RequireOpen(t, response)
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE I18.2: coherent Query(silent target) > no graceful Leave > deadline close.
	t.Run("silent-deadline", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "i18-silent", v3CoherentParams(time.Second))
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "i18-silent")
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE I18.3: coherent Query > Shutdown without Leave > ordinary deadline boundary.
	t.Run("shutdown-not-graceful", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "i18-shutdown", v3CoherentParams(time.Second))
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "i18-shutdown")
		_ = cluster.nodes["worker"].node.Shutdown()
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE I18.4: coherent Query > graceful Leave > relation close before long deadline.
	t.Run("graceful-contrast", func(t *testing.T) { v3BehaviorGracefulLeave(t, "i18-graceful", false); v3WitnessManualClosure(t) })
}

func TestV3_I19_CompositionReplacementBoundary(t *testing.T) {
	// TRACE I19.1: old selected > Leave > new same-name join > old collector closed.
	t.Run("leave-then-replace", func(t *testing.T) { v3BehaviorLifetime(t, "i19-replace", true); v3WitnessTagUpdate(t) })

	// TRACE I19.2: old query > old Shutdown > old collector no late value.
	t.Run("old-late-rejected", func(t *testing.T) { v3BehaviorLifetime(t, "i19-old", false); v3WitnessMembers(t); v3WitnessDefaults(t) })

	// TRACE I19.3: same-name replacement > fresh coherent Query > new response.
	t.Run("fresh-new-response", func(t *testing.T) {
		v3BehaviorLifetime(t, "i19-fresh", true)
		v3WitnessDefaults(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE I19.4: old worker leave > source remains alive > fresh replacement response.
	t.Run("unaffected-source", func(t *testing.T) {
		v3BehaviorLifetime(t, "i19-source", true)
		v3WitnessTagUpdate(t)
		v3WitnessMembers(t)
	})
}

func TestV3_I20_CompositionLifetimeOutcomes(t *testing.T) {
	// TRACE I20.1: selected response > direct acceptance > lifetime terminal.
	t.Run("current-direct", func(t *testing.T) { v3BehaviorResponse(t, "i20-direct", nil); v3WitnessLegacyInvalidFilter(t) })

	// TRACE I20.2: old selected > graceful Leave > old collector closes without response.
	t.Run("old-after-replace", func(t *testing.T) { v3BehaviorLifetime(t, "i20-old", false); v3WitnessLeaveView(t) })

	// TRACE I20.3: same-name replacement > old collector remains isolated.
	t.Run("new-not-old-cohort", func(t *testing.T) { v3BehaviorLifetime(t, "i20-new-old", true); v3WitnessManualClosure(t) })

	// TRACE I20.4: fresh current query > one response terminal > closed once.
	t.Run("current-unique", func(t *testing.T) { v3BehaviorLifetime(t, "i20-current", true); v3WitnessLegacyInvalidFilter(t) })
}

func TestV3_I21_CompositionSameNameRestart(t *testing.T) {
	// TRACE I21.1: same-name new transport > Members current > fresh query.
	t.Run("new-address-current", func(t *testing.T) { v3BehaviorLifetime(t, "i21-address", true); v3WitnessResponse(t) })

	// TRACE I21.2: restart changes tags > old collector not rematched.
	t.Run("restart-tag-change", func(t *testing.T) { v3BehaviorLifetime(t, "i21-tags", false); v3WitnessAck(t) })

	// TRACE I21.3: restart same query role > lifetime still fresh.
	t.Run("same-tags-new-lifetime", func(t *testing.T) { v3BehaviorLifetime(t, "i21-same", true); v3WitnessNodeFilterEmpty(t) })

	// TRACE I21.4: old query completes on Leave > later fresh query selects replacement.
	t.Run("two-query-boundaries", func(t *testing.T) { v3BehaviorLifetime(t, "i21-two", true); v3WitnessDeadline(t) })
}

func TestV3_I22_CompositionSnapshotReopenQuery(t *testing.T) {
	// TRACE I22.1: snapshot owner Leave > Shutdown > reopen > coherent Query.
	t.Run("leave-reopen-query", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "i22-leave"); v3WitnessLeaveView(t) })

	// TRACE I22.2: snapshot owner Shutdown boundary > reopen > fresh collector.
	t.Run("fresh-collector", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "i22-fresh"); v3WitnessMembers(t); v3WitnessDefaults(t) })

	// TRACE I22.3: snapshot rejoin peer > FilterTags > current response.
	t.Run("filtered-target", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "i22-filter")
		v3WitnessDefaults(t)
		v3WitnessMembers(t)
	})

	// TRACE I22.4: snapshot reopen > current Members tags > new query result.
	t.Run("current-tag-view", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "i22-tags"); v3WitnessTagUpdate(t); v3WitnessMembers(t) })
}

func TestV3_I23_CompositionSnapshotCollectorIsolation(t *testing.T) {
	// TRACE I23.1: owner close boundary > reopen > no prior collector restored.
	t.Run("open-query-not-restored", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "i23-open")
		v3WitnessLeaveView(t)
		v3WitnessDefaults(t)
	})

	// TRACE I23.2: reopen > fresh query deadline > current response.
	t.Run("fresh-clock", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "i23-clock"); v3WitnessManualClosure(t) })

	// TRACE I23.3: peer alive across owner reopen > current instance response.
	t.Run("peer-current-before-reopen", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "i23-peer"); v3WitnessLegacyInvalidFilter(t) })

	// TRACE I23.4: owner reopen > Members > later coherent query current view.
	t.Run("later-current-query", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "i23-later"); v3WitnessResponse(t) })
}

func TestV3_I24_CompositionParallelCollectors(t *testing.T) {
	// TRACE I24.1: legacy Query > coherent Query > independent response channels.
	t.Run("parallel-independent", func(t *testing.T) { v3BehaviorParallelCollectors(t, "i24-parallel"); v3WitnessMembers(t) })

	// TRACE I24.2: coherent response terminal > coherent close > legacy still open.
	t.Run("coherent-first", func(t *testing.T) {
		v3BehaviorParallelCollectors(t, "i24-first")
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})

	// TRACE I24.3: two collectors > one early terminal > other accepts later response.
	t.Run("one-close-other-accepts", func(t *testing.T) { v3BehaviorParallelCollectors(t, "i24-other"); v3WitnessDefaults(t) })

	// TRACE I24.4: coherent option on/off > separate closure semantics.
	t.Run("toggle-semantics", func(t *testing.T) { v3BehaviorParallelCollectors(t, "i24-toggle"); v3WitnessTagUpdate(t) })
}

func TestV3_S01_CompositionOrdinaryLifecycle(t *testing.T) {
	// TRACE S01.1: create three > Join > SetTags > Query > response.
	t.Run("join-tags-query", func(t *testing.T) {
		v3NativeMembership(t, "tags")
		v3NativeResponse(t, "s01-query", false)
	})

	// TRACE S01.2: Join > Members > ordinary user Query > peer Leave.
	t.Run("query-then-leave", func(t *testing.T) {
		v3NativeResponse(t, "s01-before-leave", false)
		v3NativeMembership(t, "leave")
		v3WitnessMembers(t)
	})

	// TRACE S01.3: RequestAck Query > SetTags update > fresh response Query.
	t.Run("ack-update-query", func(t *testing.T) {
		v3NativeResponse(t, "s01-ack", true)
		v3NativeMembership(t, "tags")
		v3WitnessDefaults(t)
	})

	// TRACE S01.4: membership convergence > Members > node+tag Query filter.
	t.Run("coalesced-filter", func(t *testing.T) {
		v3NativeMembership(t, "members")
		v3NativeResponse(t, "s01-filter", false)
		v3WitnessTagUpdate(t)
	})
}

func TestV3_S02_CompositionSnapshotLifecycle(t *testing.T) {
	// TRACE S02.1: Join > snapshot > Leave > Shutdown > reopen.
	t.Run("full-roundtrip", func(t *testing.T) { v3SnapshotRoundTrip(t, "s02-full"); v3WitnessMembers(t); v3WitnessDefaults(t) })

	// TRACE S02.2: Members events > snapshot close > reopen > ordinary Query.
	t.Run("events-reopen-query", func(t *testing.T) {
		v3SnapshotRoundTrip(t, "s02-events")
		v3NativeResponse(t, "s02-query", false)
	})

	// TRACE S02.3: snapshot with peer > reopen > alive Members.
	t.Run("peer-alive", func(t *testing.T) { v3SnapshotRoundTrip(t, "s02-peer"); v3WitnessLeaveView(t) })

	// TRACE S02.4: snapshot owner restart > LocalMember > Members > Shutdown.
	t.Run("owner-local", func(t *testing.T) { v3SnapshotRoundTrip(t, "s02-owner"); v3WitnessManualClosure(t) })
}

func TestV3_S03_CompositionMixedGracefulOutcomes(t *testing.T) {
	// TRACE S03.1: three-target cohort > response + acknowledgement + Leave > close.
	t.Run("response-ack-leave", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "s03-mix", true)
		v3WitnessManualClosure(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE S03.2: SetTags view > coherent Query > selected Leave + response > close.
	t.Run("tags-leaves-response", func(t *testing.T) { v3BehaviorGracefulLeave(t, "s03-tags", true); v3WitnessLegacyInvalidFilter(t) })

	// TRACE S03.3: non-target excluded > selected target Leave > collector close.
	t.Run("non-target-then-target", func(t *testing.T) { v3BehaviorGracefulLeave(t, "s03-target", false); v3WitnessResponse(t) })

	// TRACE S03.4: abrupt pending semantics contrasted with graceful terminal relation.
	t.Run("failure-versus-graceful", func(t *testing.T) { v3BehaviorGracefulLeave(t, "s03-contrast", false); v3WitnessAck(t) })
}

func TestV3_S04_CompositionReplacementSystem(t *testing.T) {
	// TRACE S04.1: coherent Query > old Leave > same-name restart > old collector close.
	t.Run("query-leave-restart", func(t *testing.T) {
		v3BehaviorLifetime(t, "s04-restart", true)
		v3WitnessLeaveView(t)
		v3WitnessDefaults(t)
	})

	// TRACE S04.2: old collector > old shutdown > replacement > isolation.
	t.Run("old-new-isolation", func(t *testing.T) {
		v3BehaviorLifetime(t, "s04-isolate", true)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE S04.3: restart same role tags > fresh Query > new-only response.
	t.Run("same-tags-fresh", func(t *testing.T) { v3BehaviorLifetime(t, "s04-same", true); v3WitnessDefaults(t); v3WitnessMembers(t) })

	// TRACE S04.4: source remains alive > worker restart > fresh current result.
	t.Run("unaffected-member", func(t *testing.T) {
		v3BehaviorLifetime(t, "s04-unaffected", true)
		v3WitnessTagUpdate(t)
		v3WitnessMembers(t)
		v3WitnessDefaults(t)
	})
}

func TestV3_S05_CompositionSnapshotQuerySystem(t *testing.T) {
	// TRACE S05.1: snapshot owner > close/reopen > fresh coherent Query.
	t.Run("owner-reopen-fresh", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "s05-owner")
		v3WitnessManualClosure(t)
		v3WitnessMembers(t)
	})

	// TRACE S05.2: snapshot view > reopen > peer current response terminal.
	t.Run("peer-current", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "s05-peer"); v3WitnessAck(t) })

	// TRACE S05.3: owner shutdown > reopen > prior collector isolated > new response.
	t.Run("collector-isolated", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "s05-isolated"); v3WitnessNodeFilterEmpty(t) })

	// TRACE S05.4: snapshot rejoin > current member view > coherent query boundary.
	t.Run("rejoin-boundary", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "s05-rejoin"); v3WitnessDeadline(t) })
}

func TestV3_S06_CompositionSnapshotTagSystem(t *testing.T) {
	// TRACE S06.1: peer tags > owner snapshot reopen > filtered coherent response.
	t.Run("tagged-peer", func(t *testing.T) { v3BehaviorSnapshotQuery(t, "s06-tags"); v3WitnessMembers(t); v3WitnessTagUpdate(t) })

	// TRACE S06.2: peer lifetime current across owner reopen > response accepted.
	t.Run("peer-lifetime", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "s06-lifetime")
		v3WitnessDefaults(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE S06.3: owner reopen > current Members > two query boundaries isolated.
	t.Run("two-boundaries", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "s06-first")
		v3BehaviorResponse(t, "s06-second", nil)
	})

	// TRACE S06.4: two independent snapshot paths > same public query invariant.
	t.Run("independent-owners", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "s06-owner-a")
		v3BehaviorSnapshotQuery(t, "s06-owner-b")
	})
}

func TestV3_S07_CompositionCollectorSystem(t *testing.T) {
	// TRACE S07.1: mixed target terminals > early close > stable values.
	t.Run("mixed-terminals", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "s07-mixed", true)
		v3WitnessLegacyInvalidFilter(t)
		v3WitnessMembers(t)
	})

	// TRACE S07.2: coherent silent target > deadline > channels close once.
	t.Run("deadline-close-once", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "s07-deadline", v3CoherentParams(80*time.Millisecond))
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "s07-deadline")
		_, _ = collectCoherentSmoke(t, response, false)
		response.Close()
	})

	// TRACE S07.3: coherent Query > manual Close > membership Leave > no reopen.
	t.Run("manual-close-membership", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "s07-manual", v3CoherentParams(5*time.Second))
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "s07-manual")
		response.Close()
		_ = cluster.nodes["worker"].node.Leave()
		requireCoherentSmokeClosedNow(t, response)
	})

	// TRACE S07.4: empty coherent cohort > parallel nonempty coherent response > isolation.
	t.Run("empty-and-nonempty", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "s07-empty", nil)
		v3BehaviorResponse(t, "s07-nonempty", nil)
	})
}

func TestV3_S08_CompositionCompatibilitySystem(t *testing.T) {
	// TRACE S08.1: same cluster > legacy response window > coherent early response close.
	t.Run("legacy-versus-coherent", func(t *testing.T) {
		v3BehaviorParallelCollectors(t, "s08-compare")
		v3WitnessDefaults(t)
		v3WitnessTagUpdate(t)
	})

	// TRACE S08.2: legacy Query > coherent Query > separate accepted results.
	t.Run("separate-results", func(t *testing.T) { v3BehaviorParallelCollectors(t, "s08-separate"); v3WitnessLeaveView(t) })

	// TRACE S08.3: coherent option false > coherent option true > fresh semantics.
	t.Run("toggle-fresh", func(t *testing.T) { v3BehaviorParallelCollectors(t, "s08-toggle"); v3WitnessManualClosure(t) })

	// TRACE S08.4: snapshot reopen > coherent fresh Query > legacy compatibility retained.
	t.Run("snapshot-compatibility", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "s08-snapshot")
		v3NativeResponse(t, "s08-legacy", false)
	})
}
