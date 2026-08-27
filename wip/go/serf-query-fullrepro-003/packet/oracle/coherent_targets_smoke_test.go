package serf_test

import (
	"fmt"
	"io"
	"path/filepath"
	"reflect"
	"sort"
	"testing"
	"time"

	"github.com/hashicorp/memberlist"
	"github.com/hashicorp/serf/serf"
)

type coherentSmokeNode struct {
	node   *serf.Serf
	events chan serf.Event
	seen   chan string
	done   chan struct{}
}

func newCoherentSmokeNode(t *testing.T, network *memberlist.MockNetwork, name string, tags map[string]string, snapshotPath string) *coherentSmokeNode {
	t.Helper()
	events := make(chan serf.Event, 128)
	config := serf.DefaultConfig()
	config.NodeName = name
	config.Tags = tags
	config.EventCh = events
	config.LogOutput = io.Discard
	config.SnapshotPath = snapshotPath
	config.RejoinAfterLeave = snapshotPath != ""
	config.MemberlistConfig.Transport = network.NewTransport(name)
	config.MemberlistConfig.ProbeInterval = 0
	config.MemberlistConfig.PushPullInterval = 0
	node, err := serf.Create(config)
	if err != nil {
		t.Fatalf("create %s: %v", name, err)
	}
	t.Cleanup(func() { _ = node.Shutdown() })
	return &coherentSmokeNode{
		node:   node,
		events: events,
		seen:   make(chan string, 32),
		done:   make(chan struct{}),
	}
}

func (n *coherentSmokeNode) handleQueries(payload, silentName string) {
	go func() {
		defer close(n.done)
		for {
			select {
			case event := <-n.events:
				query, ok := event.(*serf.Query)
				if !ok {
					continue
				}
				select {
				case n.seen <- query.Name:
				default:
				}
				if query.Name != silentName {
					_ = query.Respond([]byte(payload))
				}
			case <-n.node.ShutdownCh():
				return
			}
		}
	}()
}

func joinCoherentSmoke(t *testing.T, nodes ...*coherentSmokeNode) {
	t.Helper()
	for _, node := range nodes {
		if _, err := node.node.Join([]string{"127.0.0.1:1"}, false); err != nil {
			t.Fatalf("join %s: %v", node.node.LocalMember().Name, err)
		}
	}
}

func waitCoherentSmokeView(t *testing.T, node *serf.Serf, want map[string]map[string]string) {
	t.Helper()
	deadline := time.Now().Add(4 * time.Second)
	for time.Now().Before(deadline) {
		got := make(map[string]map[string]string)
		for _, member := range node.Members() {
			if member.Status == serf.StatusAlive {
				got[member.Name] = member.Tags
			}
		}
		local := node.LocalMember()
		if reflect.DeepEqual(got, want) &&
			local.Status == serf.StatusAlive &&
			reflect.DeepEqual(local.Tags, want[local.Name]) {
			return
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatalf("member view did not quiesce: local=%v members=%v want=%v", node.LocalMember(), node.Members(), want)
}

func waitCoherentSmokeQuery(t *testing.T, node *coherentSmokeNode, name string) {
	t.Helper()
	timer := time.NewTimer(2 * time.Second)
	defer timer.Stop()
	for {
		select {
		case got := <-node.seen:
			if got == name {
				return
			}
		case <-timer.C:
			t.Fatalf("%s did not observe query %s", node.node.LocalMember().Name, name)
		}
	}
}

func startCoherentSmokeQuery(t *testing.T, node *serf.Serf, name string, coherent, ack bool, timeout time.Duration) (*serf.QueryResponse, time.Time) {
	t.Helper()
	started := time.Now()
	response, err := node.Query(name, []byte("smoke"), &serf.QueryParam{
		FilterTags:      map[string]string{"role": "^worker$"},
		RequestAck:      ack,
		Timeout:         timeout,
		CoherentTargets: coherent,
	})
	if err != nil {
		t.Fatalf("query %s: %v", name, err)
	}
	return response, started
}

func collectCoherentSmoke(t *testing.T, response *serf.QueryResponse, withAcks bool) ([]string, []string) {
	t.Helper()
	defer response.Close()
	var payloads []string
	var acknowledgements []string
	responses := response.ResponseCh()
	var acks <-chan string
	if withAcks {
		acks = response.AckCh()
	}
	timer := time.NewTimer(5 * time.Second)
	defer timer.Stop()
	for responses != nil || acks != nil {
		select {
		case item, ok := <-responses:
			if !ok {
				responses = nil
				continue
			}
			payloads = append(payloads, fmt.Sprintf("%s=%s", item.From, item.Payload))
		case item, ok := <-acks:
			if !ok {
				acks = nil
				continue
			}
			acknowledgements = append(acknowledgements, item)
		case <-timer.C:
			t.Fatal("query collector did not close")
		}
	}
	sort.Strings(payloads)
	sort.Strings(acknowledgements)
	return payloads, acknowledgements
}

func requireCoherentSmokeBefore(t *testing.T, started time.Time, limit time.Duration) {
	t.Helper()
	if elapsed := time.Since(started); elapsed >= limit {
		t.Fatalf("collector did not complete at its target boundary: elapsed=%s limit=%s", elapsed, limit)
	}
}

func requireCoherentSmokeClosedNow(t *testing.T, response *serf.QueryResponse) {
	t.Helper()
	if !response.Finished() {
		t.Fatal("collector is not finished after its public terminal transition")
	}
	select {
	case _, ok := <-response.ResponseCh():
		if ok {
			t.Fatal("collector produced an unexpected response at closure")
		}
	default:
		t.Fatal("response channel remains open after its public terminal transition")
	}
}

func TestCoherentTargetsFamilySmoke(t *testing.T) {
	t.Run("F01-CohortView", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, "")
		worker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker"}, "")
		worker.handleQueries("unused", "smoke-f01")
		joinCoherentSmoke(t, worker)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker"},
		})
		response, started := startCoherentSmokeQuery(t, source.node, "smoke-f01", true, true, 1800*time.Millisecond)
		waitCoherentSmokeQuery(t, worker, "smoke-f01")
		payloads, acks := collectCoherentSmoke(t, response, true)
		requireCoherentSmokeBefore(t, started, 900*time.Millisecond)
		if len(payloads) != 0 || !reflect.DeepEqual(acks, []string{"worker"}) {
			t.Fatalf("cohort ack result: responses=%v acks=%v", payloads, acks)
		}
	})

	t.Run("F02-TagTransition", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, "")
		worker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker", "rev": "one"}, "")
		worker.handleQueries("unexpected", "")
		joinCoherentSmoke(t, worker)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker", "rev": "one"},
		})
		if err := worker.node.SetTags(map[string]string{"role": "retired", "rev": "two"}); err != nil {
			t.Fatalf("set tags: %v", err)
		}
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "retired", "rev": "two"},
		})
		response, started := startCoherentSmokeQuery(t, source.node, "smoke-f02", true, false, 1800*time.Millisecond)
		payloads, _ := collectCoherentSmoke(t, response, false)
		requireCoherentSmokeBefore(t, started, 500*time.Millisecond)
		if len(payloads) != 0 {
			t.Fatalf("retired member responded: %v", payloads)
		}
	})

	t.Run("F03-TargetOutcome", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, "")
		alpha := newCoherentSmokeNode(t, network, "alpha", map[string]string{"role": "worker"}, "")
		beta := newCoherentSmokeNode(t, network, "beta", map[string]string{"role": "worker"}, "")
		alpha.handleQueries("alpha", "")
		beta.handleQueries("beta", "")
		joinCoherentSmoke(t, alpha, beta)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"alpha":  {"role": "worker"},
			"beta":   {"role": "worker"},
		})
		response, started := startCoherentSmokeQuery(t, source.node, "smoke-f03", true, false, 1800*time.Millisecond)
		payloads, _ := collectCoherentSmoke(t, response, false)
		requireCoherentSmokeBefore(t, started, 900*time.Millisecond)
		if !reflect.DeepEqual(payloads, []string{"alpha=alpha", "beta=beta"}) {
			t.Fatalf("response terminal result: %v", payloads)
		}
	})

	t.Run("F04-GracefulLeave", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, "")
		worker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker"}, "")
		worker.handleQueries("unused", "smoke-f04")
		joinCoherentSmoke(t, worker)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker"},
		})
		response, _ := startCoherentSmokeQuery(t, source.node, "smoke-f04", true, false, 10*time.Second)
		waitCoherentSmokeQuery(t, worker, "smoke-f04")
		if err := worker.node.Leave(); err != nil {
			t.Fatalf("leave: %v", err)
		}
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{"source": {"role": "control"}})
		requireCoherentSmokeClosedNow(t, response)
		payloads, _ := collectCoherentSmoke(t, response, false)
		if len(payloads) != 0 {
			t.Fatalf("leaving silent target responded: %v", payloads)
		}
	})

	t.Run("F05-MemberLifetime", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, "")
		oldWorker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker", "generation": "old"}, "")
		oldWorker.handleQueries("old", "smoke-f05")
		joinCoherentSmoke(t, oldWorker)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker", "generation": "old"},
		})
		response, _ := startCoherentSmokeQuery(t, source.node, "smoke-f05", true, false, 10*time.Second)
		waitCoherentSmokeQuery(t, oldWorker, "smoke-f05")
		if err := oldWorker.node.Leave(); err != nil {
			t.Fatalf("leave old worker: %v", err)
		}
		if err := oldWorker.node.Shutdown(); err != nil {
			t.Fatalf("shutdown old worker: %v", err)
		}
		<-oldWorker.done
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{"source": {"role": "control"}})
		requireCoherentSmokeClosedNow(t, response)
		oldPayloads, _ := collectCoherentSmoke(t, response, false)
		if len(oldPayloads) != 0 {
			t.Fatalf("old cohort accepted a terminal response: %v", oldPayloads)
		}
		newWorker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker", "generation": "new"}, "")
		newWorker.handleQueries("replacement", "")
		joinCoherentSmoke(t, newWorker)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker", "generation": "new"},
		})
		fresh, _ := startCoherentSmokeQuery(t, source.node, "smoke-f05-fresh", true, false, 1800*time.Millisecond)
		payloads, _ := collectCoherentSmoke(t, fresh, false)
		if !reflect.DeepEqual(payloads, []string{"worker=replacement"}) {
			t.Fatalf("fresh cohort did not select replacement: %v", payloads)
		}
	})

	t.Run("F06-SnapshotReopen", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		snapshotPath := filepath.Join(t.TempDir(), "source.snapshot")
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, snapshotPath)
		worker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker"}, "")
		worker.handleQueries("after-reopen", "")
		joinCoherentSmoke(t, worker)
		want := map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker"},
		}
		waitCoherentSmokeView(t, source.node, want)
		if err := source.node.Leave(); err != nil {
			t.Fatalf("leave snapshot owner: %v", err)
		}
		if err := source.node.Shutdown(); err != nil {
			t.Fatalf("shutdown snapshot owner: %v", err)
		}
		reopened := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, snapshotPath)
		waitCoherentSmokeView(t, reopened.node, want)
		response, started := startCoherentSmokeQuery(t, reopened.node, "smoke-f06", true, false, 1800*time.Millisecond)
		payloads, _ := collectCoherentSmoke(t, response, false)
		requireCoherentSmokeBefore(t, started, 900*time.Millisecond)
		if !reflect.DeepEqual(payloads, []string{"worker=after-reopen"}) {
			t.Fatalf("snapshot reopen result: %v", payloads)
		}
	})

	t.Run("F07-CollectorBoundary", func(t *testing.T) {
		network := &memberlist.MockNetwork{}
		source := newCoherentSmokeNode(t, network, "source", map[string]string{"role": "control"}, "")
		worker := newCoherentSmokeNode(t, network, "worker", map[string]string{"role": "worker"}, "")
		worker.handleQueries("boundary", "")
		joinCoherentSmoke(t, worker)
		waitCoherentSmokeView(t, source.node, map[string]map[string]string{
			"source": {"role": "control"},
			"worker": {"role": "worker"},
		})
		legacy, legacyStarted := startCoherentSmokeQuery(t, source.node, "smoke-f07-legacy", false, false, 1800*time.Millisecond)
		coherent, coherentStarted := startCoherentSmokeQuery(t, source.node, "smoke-f07-coherent", true, false, 1800*time.Millisecond)
		coherentPayloads, _ := collectCoherentSmoke(t, coherent, false)
		requireCoherentSmokeBefore(t, coherentStarted, 900*time.Millisecond)
		if legacy.Finished() {
			t.Fatal("ordinary collector finished at the coherent boundary")
		}
		legacyPayloads, _ := collectCoherentSmoke(t, legacy, false)
		if time.Since(legacyStarted) < 1500*time.Millisecond {
			t.Fatal("ordinary collector did not retain its timeout behavior")
		}
		if !reflect.DeepEqual(coherentPayloads, []string{"worker=boundary"}) ||
			!reflect.DeepEqual(legacyPayloads, []string{"worker=boundary"}) {
			t.Fatalf("collector isolation: coherent=%v legacy=%v", coherentPayloads, legacyPayloads)
		}
	})
}
