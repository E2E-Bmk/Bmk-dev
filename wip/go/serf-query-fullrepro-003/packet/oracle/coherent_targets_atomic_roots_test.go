package serf_test

import (
	"reflect"
	"testing"
	"time"

	"github.com/hashicorp/serf/serf"
)

func TestV3_A01_AtomicAdmission(t *testing.T) {
	// TRACE A01.1: DefaultQueryParams > Query > Deadline > ResponseCh.
	t.Run("default-params-deadline", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		params := cluster.source.node.DefaultQueryParams()
		params.FilterNodes = []string{"missing"}
		params.Timeout = 25 * time.Millisecond
		response := v3Query(t, cluster.source.node, "a01-default", params)
		if response.Deadline().Before(time.Now()) {
			t.Fatal("default query deadline is already expired")
		}
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE A01.2: DefaultQueryTimeout > Query(explicit Timeout) > Finished.
	t.Run("explicit-timeout", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		if cluster.source.node.DefaultQueryTimeout() <= 0 {
			t.Fatal("non-positive default query timeout")
		}
		v3NativeEmpty(t, "a01-explicit")
	})
}

func TestV3_A01_AtomicValidation(t *testing.T) {
	// TRACE A01.3: Query(oversize payload) > admission error.
	t.Run("oversize-payload", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		payload := make([]byte, 2*1024*1024)
		if response, err := cluster.source.node.Query("a01-oversize", payload, &serf.QueryParam{Timeout: time.Second}); err == nil {
			response.Close()
			t.Fatal("oversize query unexpectedly admitted")
		}
	})

	// TRACE A01.4: Query(malformed FilterTags) > collector > no matching response.
	t.Run("malformed-filter", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		response, err := cluster.source.node.Query("a01-regexp", nil, &serf.QueryParam{
			FilterTags: map[string]string{"role": "["},
			Timeout:    25 * time.Millisecond,
		})
		if err != nil || response == nil {
			t.Fatalf("ordinary malformed filter admission: response=%v err=%v", response, err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if len(responses) != 0 {
			t.Fatalf("malformed filter responses=%v", responses)
		}
	})
}

func TestV3_A02_AtomicNamedSelection(t *testing.T) {
	// TRACE A02.1: Members > Query(FilterNodes worker) > Query event > Respond.
	t.Run("named-target", func(t *testing.T) {
		v3NativeResponse(t, "a02-named", false)
	})

	// TRACE A02.2: LocalMember > Query(FilterNodes peer) > local excluded.
	t.Run("local-excluded", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		if cluster.source.node.LocalMember().Name != "source" {
			t.Fatal("unexpected local member")
		}
		response := v3Query(t, cluster.source.node, "a02-local-excluded", &serf.QueryParam{
			FilterNodes: []string{"worker"}, Timeout: 700 * time.Millisecond,
		})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a02-local-excluded")
		if err := query.Respond([]byte("peer")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"worker=peer"}) {
			t.Fatalf("responses=%v", responses)
		}
	})
}

func TestV3_A02_AtomicFilterEdges(t *testing.T) {
	// TRACE A02.3: Members > Query(empty FilterNodes) > all alive event paths.
	t.Run("empty-node-list", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a02-empty-list", &serf.QueryParam{Timeout: 700 * time.Millisecond})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a02-empty-list")
		if err := query.Respond([]byte("all")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"worker=all"}) {
			t.Fatalf("responses=%v", responses)
		}
	})

	// TRACE A02.4: Query(FilterNodes worker+missing) > known event > response.
	t.Run("known-plus-missing", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a02-mixed-list", &serf.QueryParam{
			FilterNodes: []string{"missing", "worker"}, Timeout: 700 * time.Millisecond,
		})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a02-mixed-list")
		if err := query.Respond([]byte("known")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"worker=known"}) {
			t.Fatalf("responses=%v", responses)
		}
		v3WitnessMembers(t)
	})
}

func TestV3_A03_AtomicTagSelection(t *testing.T) {
	// TRACE A03.1: Members(tags) > Query(FilterTags match) > Respond.
	t.Run("matching-regexp", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker", "zone": "east"}})
		response := v3Query(t, cluster.source.node, "a03-match", &serf.QueryParam{
			FilterTags: map[string]string{"zone": "^east$"}, Timeout: 700 * time.Millisecond,
		})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a03-match")
		if err := query.Respond([]byte("east")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"worker=east"}) {
			t.Fatalf("responses=%v", responses)
		}
		v3WitnessDefaults(t)
	})

	// TRACE A03.2: Query(FilterTags nonmatch) > no Query event > timeout close.
	t.Run("nonmatching-regexp", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "retired"}})
		response := v3Query(t, cluster.source.node, "a03-nonmatch", &serf.QueryParam{
			FilterTags: map[string]string{"role": "^worker$"}, Timeout: 25 * time.Millisecond,
		})
		responses, _ := collectCoherentSmoke(t, response, false)
		if len(responses) != 0 {
			t.Fatalf("responses=%v", responses)
		}
	})
}

func TestV3_A03_AtomicTagValidation(t *testing.T) {
	// TRACE A03.3: Query(two FilterTags) > intersection event > Respond.
	t.Run("tag-intersection", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker", "zone": "east"}})
		response := v3Query(t, cluster.source.node, "a03-intersection", &serf.QueryParam{
			FilterTags: map[string]string{"role": "^worker$", "zone": "^east$"}, Timeout: 700 * time.Millisecond,
		})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a03-intersection")
		if err := query.Respond([]byte("both")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"worker=both"}) {
			t.Fatalf("responses=%v", responses)
		}
		v3WitnessTagUpdate(t)
	})

	// TRACE A03.4: Query(malformed tag regexp) > no event > deadline close.
	t.Run("malformed-regexp", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response, err := cluster.source.node.Query("a03-malformed", nil, &serf.QueryParam{
			FilterTags: map[string]string{"zone": "(?"}, Timeout: 25 * time.Millisecond,
		})
		if err != nil || response == nil {
			t.Fatalf("response=%v err=%v", response, err)
		}
		responses, _ := collectCoherentSmoke(t, response, false)
		if len(responses) != 0 {
			t.Fatalf("malformed filter responses=%v", responses)
		}
		v3WitnessMembers(t)
	})
}

func TestV3_A04_AtomicAckChannel(t *testing.T) {
	// TRACE A04.1: Query(RequestAck) > AckCh > source acknowledgement.
	t.Run("requested-ack", func(t *testing.T) {
		v3NativeResponse(t, "a04-requested", true)
		v3WitnessMembers(t)
	})

	// TRACE A04.2: Query(no RequestAck) > nil AckCh > response.
	t.Run("nil-ack-channel", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		response := v3Query(t, cluster.source.node, "a04-no-ack", &serf.QueryParam{Timeout: 25 * time.Millisecond})
		if response.AckCh() != nil {
			t.Fatal("AckCh is non-nil without RequestAck")
		}
		_, _ = collectCoherentSmoke(t, response, false)
	})
}

func TestV3_A04_AtomicAckUniqueness(t *testing.T) {
	// TRACE A04.3: Query(RequestAck, FilterNodes) > one member > one acknowledgement.
	t.Run("single-ack-value", func(t *testing.T) {
		v3NativeResponse(t, "a04-single", true)
		v3WitnessDefaults(t)
	})

	// TRACE A04.4: Members > Query(RequestAck, FilterTags) > AckCh closes once.
	t.Run("filtered-ack-close", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a04-filtered", &serf.QueryParam{
			FilterTags: map[string]string{"role": "^worker$"}, RequestAck: true, Timeout: 700 * time.Millisecond,
		})
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "a04-filtered")
		responses, acks := collectCoherentSmoke(t, response, true)
		if len(responses) != 0 || !reflect.DeepEqual(acks, []string{"worker"}) {
			t.Fatalf("responses=%v acks=%v", responses, acks)
		}
	})
}

func TestV3_A05_AtomicResponseChannel(t *testing.T) {
	// TRACE A05.1: Query event > Respond > ResponseCh payload.
	t.Run("query-event-response", func(t *testing.T) {
		v3NativeResponse(t, "a05-response", false)
		v3WitnessTagUpdate(t)
	})

	// TRACE A05.2: Query event > Respond twice > one public node value.
	t.Run("duplicate-response", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a05-duplicate", &serf.QueryParam{Timeout: 700 * time.Millisecond})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a05-duplicate")
		if err := query.Respond([]byte("first")); err != nil {
			t.Fatalf("first response: %v", err)
		}
		_ = query.Respond([]byte("second"))
		responses, _ := collectCoherentSmoke(t, response, false)
		if len(responses) != 1 || responses[0] != "worker=first" {
			t.Fatalf("responses=%v", responses)
		}
	})
}

func TestV3_A05_AtomicResponseBounds(t *testing.T) {
	// TRACE A05.3: Query event > Respond(oversize) > response error.
	t.Run("oversize-response", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a05-oversize", &serf.QueryParam{Timeout: 40 * time.Millisecond})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a05-oversize")
		if err := query.Respond(make([]byte, 2*1024*1024)); err == nil {
			t.Fatal("oversize response unexpectedly accepted")
		}
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE A05.4: Query event > deadline close > late Respond cannot reopen collector.
	t.Run("late-response", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a05-late", &serf.QueryParam{Timeout: 30 * time.Millisecond})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a05-late")
		_, _ = collectCoherentSmoke(t, response, false)
		_ = query.Respond([]byte("late"))
		if !response.Finished() {
			t.Fatal("late response reopened the finished collector")
		}
	})
}

func TestV3_A06_AtomicDeadline(t *testing.T) {
	// TRACE A06.1: Query(silent target) > Deadline > ResponseCh close.
	t.Run("silent-deadline", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a06-silent", &serf.QueryParam{Timeout: 30 * time.Millisecond})
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "a06-silent")
		_, _ = collectCoherentSmoke(t, response, false)
		if !response.Finished() {
			t.Fatal("deadline collector not finished")
		}
	})

	// TRACE A06.2: Query > Close > Finished > closed ResponseCh.
	t.Run("manual-close", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		response := v3Query(t, cluster.source.node, "a06-manual", &serf.QueryParam{Timeout: time.Second})
		response.Close()
		requireCoherentSmokeClosedNow(t, response)
	})
}

func TestV3_A06_AtomicClosure(t *testing.T) {
	// TRACE A06.3: Query > Close > Close > stable closed channels.
	t.Run("repeat-close", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		response := v3Query(t, cluster.source.node, "a06-repeat", &serf.QueryParam{RequestAck: true, Timeout: time.Second})
		response.Close()
		response.Close()
		if !response.Finished() {
			t.Fatal("repeated close lost finished state")
		}
	})

	// TRACE A06.4: Query event > Close > Respond > no reopened collector.
	t.Run("late-after-close", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a06-closed-late", &serf.QueryParam{Timeout: time.Second})
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a06-closed-late")
		response.Close()
		_ = query.Respond([]byte("ignored"))
		requireCoherentSmokeClosedNow(t, response)
	})
}

func TestV3_A07_AtomicMemberProjection(t *testing.T) {
	// TRACE A07.1: Create > LocalMember.
	t.Run("local-member", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		if got := cluster.source.node.LocalMember(); got.Name != "source" || got.Status != serf.StatusAlive {
			t.Fatalf("local member=%v", got)
		}
	})

	// TRACE A07.2: Join > Members on both nodes.
	t.Run("join-members", func(t *testing.T) {
		v3NativeMembership(t, "members")
	})
}

func TestV3_A07_AtomicMemberTransitions(t *testing.T) {
	// TRACE A07.3: SetTags > LocalMember > peer Members.
	t.Run("set-tags-view", func(t *testing.T) {
		v3NativeMembership(t, "tags")
		v3WitnessMembers(t)
	})

	// TRACE A07.4: Leave > peer Members excludes left node.
	t.Run("leave-view", func(t *testing.T) {
		v3NativeMembership(t, "leave")
		v3WitnessDefaults(t)
	})
}

func TestV3_A08_AtomicLegacyCompatibility(t *testing.T) {
	// TRACE A08.1: Query(CoherentTargets false, silent) > ordinary timeout.
	t.Run("option-off-timeout", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a08-off", &serf.QueryParam{
			FilterTags: map[string]string{"role": "^worker$"}, Timeout: 35 * time.Millisecond,
		})
		_ = v3WaitPublicQuery(t, cluster.nodes["worker"], "a08-off")
		_, _ = collectCoherentSmoke(t, response, false)
	})

	// TRACE A08.2: Query(zero QueryParam) > response window > ordinary close.
	t.Run("zero-value-response", func(t *testing.T) {
		v3NativeResponse(t, "a08-zero", false)
		v3WitnessLeaveView(t)
	})
}

func TestV3_A08_AtomicOptionIsolation(t *testing.T) {
	// TRACE A08.3: Query(option off, empty filter) > deadline closure.
	t.Run("off-empty-filter", func(t *testing.T) {
		v3NativeEmpty(t, "a08-empty")
	})

	// TRACE A08.4: legacy Query > coherent Query > distinct completion boundaries.
	t.Run("off-then-on", func(t *testing.T) {
		v3BehaviorParallelCollectors(t, "a08-toggle")
	})
}

func TestV3_A09_AtomicCohortAdmission(t *testing.T) {
	// TRACE A09.1: Members(alive) > coherent Query > response terminal.
	t.Run("alive-cohort", func(t *testing.T) {
		v3BehaviorResponse(t, "a09-alive", nil)
	})

	// TRACE A09.2: Leave > Members > coherent Query > empty closure.
	t.Run("left-excluded", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		if err := cluster.nodes["worker"].node.Leave(); err != nil {
			t.Fatalf("leave: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{"source": {"role": "control"}})
		response := v3Query(t, cluster.source.node, "a09-left", v3CoherentParams(5*time.Second))
		v3RequireEmptyClosed(t, response)
	})
}

func TestV3_A09_AtomicCohortEdges(t *testing.T) {
	// TRACE A09.3: retired member tags > coherent Query > empty closure.
	t.Run("nonmatching-excluded", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "a09-retired", nil)
	})

	// TRACE A09.4: coherent Query(nonmatching FilterNodes) > immediate channels close.
	t.Run("empty-cohort", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "a09-empty", func(params *serf.QueryParam) {
			params.FilterNodes = []string{"missing"}
		})
		v3WitnessMembers(t)
	})
}

func TestV3_A10_AtomicTagBoundary(t *testing.T) {
	// TRACE A10.1: SetTags > Members quiescence > coherent Query selects new match.
	t.Run("update-before-query", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "retired"}})
		if err := cluster.nodes["worker"].node.SetTags(map[string]string{"role": "worker"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, cluster.source.node, map[string]map[string]string{
			"source": {"role": "control"}, "worker": {"role": "worker"},
		})
		response := v3Query(t, cluster.source.node, "a10-before", v3CoherentParams(5*time.Second))
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a10-before")
		if err := query.Respond([]byte("new")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		v3RequireOneResponse(t, response, "worker", "new")
	})

	// TRACE A10.2: coherent Query > SetTags > admitted response remains terminal.
	t.Run("update-after-query", func(t *testing.T) {
		v3BehaviorTagBoundary(t, "a10-after", true)
	})
}

func TestV3_A10_AtomicTagConsistency(t *testing.T) {
	// TRACE A10.3: SetTags(two keys) > Members whole view > coherent empty cohort.
	t.Run("whole-tag-view", func(t *testing.T) {
		v3BehaviorTagBoundary(t, "a10-whole", false)
		v3WitnessMembers(t)
	})

	// TRACE A10.4: coherent Query(malformed regexp) > admission error > no collector.
	t.Run("coherent-invalid-regexp", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		response, err := cluster.source.node.Query("a10-invalid", nil, &serf.QueryParam{
			FilterTags: map[string]string{"role": "["}, CoherentTargets: true, Timeout: time.Second,
		})
		if err == nil || response != nil {
			if response != nil {
				response.Close()
			}
			t.Fatalf("response=%v err=%v", response, err)
		}
	})
}

func TestV3_A11_AtomicResponseTerminal(t *testing.T) {
	// TRACE A11.1: coherent Query(one target) > Respond > early closure.
	t.Run("one-response", func(t *testing.T) {
		v3BehaviorResponse(t, "a11-one", nil)
		v3WitnessMembers(t)
	})

	// TRACE A11.2: coherent Query(two targets) > beta Respond > alpha Respond > close.
	t.Run("reversed-responses", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		response := v3Query(t, cluster.source.node, "a11-reverse", v3CoherentParams(5*time.Second))
		alpha := v3WaitPublicQuery(t, cluster.nodes["alpha"], "a11-reverse")
		beta := v3WaitPublicQuery(t, cluster.nodes["beta"], "a11-reverse")
		if err := beta.Respond([]byte("beta")); err != nil {
			t.Fatalf("beta respond: %v", err)
		}
		v3RequireOpen(t, response)
		if err := alpha.Respond([]byte("alpha")); err != nil {
			t.Fatalf("alpha respond: %v", err)
		}
		v3AwaitFinished(t, response, 500*time.Millisecond)
		responses, _ := collectCoherentSmoke(t, response, false)
		if !reflect.DeepEqual(responses, []string{"alpha=alpha", "beta=beta"}) {
			t.Fatalf("responses=%v", responses)
		}
	})
}

func TestV3_A11_AtomicResponseUniqueness(t *testing.T) {
	// TRACE A11.3: coherent Query > Respond twice > one terminal value > close.
	t.Run("duplicate-terminal", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a11-duplicate", v3CoherentParams(5*time.Second))
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a11-duplicate")
		if err := query.Respond([]byte("first")); err != nil {
			t.Fatalf("first respond: %v", err)
		}
		_ = query.Respond([]byte("second"))
		v3RequireOneResponse(t, response, "worker", "first")
	})

	// TRACE A11.4: Members > coherent Query(node filter) > direct response > closure.
	t.Run("direct-filtered-terminal", func(t *testing.T) {
		v3BehaviorResponse(t, "a11-direct", func(cluster *v3RootCluster) {
			_ = cluster.source.node.Members()
			_ = cluster.nodes["worker"].node.LocalMember()
		})
	})
}

func TestV3_A12_AtomicAckTerminal(t *testing.T) {
	// TRACE A12.1: coherent Query(RequestAck) > AckCh > early closure.
	t.Run("one-ack", func(t *testing.T) {
		v3BehaviorAck(t, "a12-one", map[string]map[string]string{"worker": {"role": "worker"}})
	})

	// TRACE A12.2: coherent Query(two targets, RequestAck) > both events > close.
	t.Run("two-acks", func(t *testing.T) {
		v3BehaviorAck(t, "a12-two", map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		v3WitnessMembers(t)
	})
}

func TestV3_A12_AtomicAckUniqueness(t *testing.T) {
	// TRACE A12.3: coherent Query(RequestAck, FilterNodes) > single target ack > close.
	t.Run("filtered-ack", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"alpha": {"role": "worker"}, "beta": {"role": "worker"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.RequestAck = true
		params.FilterNodes = []string{"beta"}
		response := v3Query(t, cluster.source.node, "a12-filtered", params)
		_ = v3WaitPublicQuery(t, cluster.nodes["beta"], "a12-filtered")
		v3RequireAckClosed(t, response, "beta")
	})

	// TRACE A12.4: coherent Query(RequestAck) > ack terminal > later Respond ignored.
	t.Run("ack-before-response", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		params := v3CoherentParams(5 * time.Second)
		params.RequestAck = true
		response := v3Query(t, cluster.source.node, "a12-race", params)
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a12-race")
		v3AwaitFinished(t, response, 500*time.Millisecond)
		_ = query.Respond([]byte("late"))
		responses, acks := collectCoherentSmoke(t, response, true)
		if len(responses) != 0 || !reflect.DeepEqual(acks, []string{"worker"}) {
			t.Fatalf("responses=%v acks=%v", responses, acks)
		}
	})
}

func TestV3_A13_AtomicGracefulLeave(t *testing.T) {
	// TRACE A13.1: coherent Query(silent target) > Query event > Leave > closed collector.
	t.Run("silent-leave", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "a13-silent", false)
	})

	// TRACE A13.2: coherent Query(two targets) > response + Leave > closed collector.
	t.Run("response-plus-leave", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "a13-mixed", true)
		v3WitnessMembers(t)
	})
}

func TestV3_A13_AtomicLeaveBoundaries(t *testing.T) {
	// TRACE A13.3: coherent Query > Leave > closure > no response value.
	t.Run("leave-rejects-late", func(t *testing.T) {
		v3BehaviorGracefulLeave(t, "a13-late", false)
		v3WitnessDefaults(t)
	})

	// TRACE A13.4: coherent Query(FilterNodes target) > non-target Leave > target response.
	t.Run("non-target-leave", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{
			"target": {"role": "worker"}, "other": {"role": "worker"},
		})
		params := v3CoherentParams(5 * time.Second)
		params.FilterNodes = []string{"target"}
		response := v3Query(t, cluster.source.node, "a13-nontarget", params)
		query := v3WaitPublicQuery(t, cluster.nodes["target"], "a13-nontarget")
		if err := cluster.nodes["other"].node.Leave(); err != nil {
			t.Fatalf("other leave: %v", err)
		}
		v3RequireOpen(t, response)
		if err := query.Respond([]byte("target")); err != nil {
			t.Fatalf("respond: %v", err)
		}
		v3RequireOneResponse(t, response, "target", "target")
	})
}

func TestV3_A14_AtomicMemberLifetime(t *testing.T) {
	// TRACE A14.1: selected instance > response > accepted terminal.
	t.Run("selected-instance-response", func(t *testing.T) {
		v3BehaviorResponse(t, "a14-selected", nil)
		v3WitnessDefaults(t)
	})

	// TRACE A14.2: old coherent Query > old Leave > same-name replacement > old closed.
	t.Run("replacement-old-collector", func(t *testing.T) {
		v3BehaviorLifetime(t, "a14-replace", false)
	})
}

func TestV3_A14_AtomicLifetimeBoundaries(t *testing.T) {
	// TRACE A14.3: old Query > Leave > shutdown > old collector has no late values.
	t.Run("old-late-rejected", func(t *testing.T) {
		v3BehaviorLifetime(t, "a14-old-late", false)
		v3WitnessMembers(t)
	})

	// TRACE A14.4: same-name replacement > fresh coherent Query > new response.
	t.Run("fresh-query-new-instance", func(t *testing.T) {
		v3BehaviorLifetime(t, "a14-fresh", true)
		v3WitnessDefaults(t)
	})
}

func TestV3_A15_AtomicSnapshotBoundary(t *testing.T) {
	// TRACE A15.1: snapshot owner Leave > Shutdown > reopen > fresh coherent Query.
	t.Run("close-reopen-query", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "a15-reopen")
	})

	// TRACE A15.2: snapshot owner > peer alive > reopen Members > current response.
	t.Run("reopen-current-member", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "a15-current")
		v3WitnessMembers(t)
	})
}

func TestV3_A15_AtomicSnapshotIsolation(t *testing.T) {
	// TRACE A15.3: open coherent collector > owner Close > reopen > no restored collector.
	t.Run("no-open-collector-restore", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "a15-isolated")
		v3WitnessDefaults(t)
	})

	// TRACE A15.4: snapshot reopen > LocalMember > new coherent query identity.
	t.Run("new-query-after-reopen", func(t *testing.T) {
		v3BehaviorSnapshotQuery(t, "a15-new-query")
		v3WitnessTagUpdate(t)
	})
}

func TestV3_A16_AtomicCollectorCompletion(t *testing.T) {
	// TRACE A16.1: coherent Query(empty cohort) > Finished > channels closed.
	t.Run("empty-cohort-close", func(t *testing.T) {
		v3BehaviorEmptyCohort(t, "a16-empty", nil)
		v3WitnessDefaults(t)
	})

	// TRACE A16.2: coherent Query > response terminal > Finished true.
	t.Run("all-terminal-finished", func(t *testing.T) {
		v3BehaviorResponse(t, "a16-terminal", nil)
		v3WitnessTagUpdate(t)
	})
}

func TestV3_A16_AtomicCollectorClosure(t *testing.T) {
	// TRACE A16.3: coherent Query > manual Close > late response cannot reopen.
	t.Run("manual-close-stable", func(t *testing.T) {
		cluster := newV3RootCluster(t, map[string]map[string]string{"worker": {"role": "worker"}})
		response := v3Query(t, cluster.source.node, "a16-manual", v3CoherentParams(5*time.Second))
		query := v3WaitPublicQuery(t, cluster.nodes["worker"], "a16-manual")
		response.Close()
		_ = query.Respond([]byte("late"))
		requireCoherentSmokeClosedNow(t, response)
	})

	// TRACE A16.4: coherent terminal close > repeat Close > stable finished state.
	t.Run("repeat-terminal-close", func(t *testing.T) {
		cluster := newV3RootCluster(t, nil)
		params := v3CoherentParams(5 * time.Second)
		params.FilterNodes = []string{"missing"}
		response := v3Query(t, cluster.source.node, "a16-repeat", params)
		requireCoherentSmokeClosedNow(t, response)
		response.Close()
		if !response.Finished() {
			t.Fatal("repeat close changed terminal state")
		}
	})
}
