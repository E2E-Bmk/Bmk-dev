package memberlist_gate_test

import (
	"errors"
	"net"
	"reflect"
	"strings"
	"testing"
	"time"

	memberlist "github.com/hashicorp/memberlist"
	"github.com/hashicorp/memberlist/transcript"
)

func require(t *testing.T, condition bool, message string, args ...any) {
	t.Helper()
	if !condition {
		t.Fatalf(message, args...)
	}
}

func runAliveContract(t *testing.T) {
	t.Helper()
	topology := transcript.NewTopology(nil, "")
	input := []byte("m1")
	first, err := topology.RecordAlive("node-b", transcript.Generation{Incarnation: 3, Metadata: 1}, input)
	require(t, err == nil && first.Accepted && first.Node == "node-b", "initial alive receipt: %#v %v", first, err)
	input[0] = 'x'
	equal, err := topology.RecordAlive("node-b", transcript.Generation{Incarnation: 3, Metadata: 2}, []byte("m2"))
	require(t, err == nil && equal.Accepted && string(equal.Metadata) == "m2", "equal-incarnation metadata advance: %#v %v", equal, err)
	higher, err := topology.RecordAlive("node-b", transcript.Generation{Incarnation: 4}, []byte("fresh"))
	require(t, err == nil && higher.Accepted, "higher incarnation: %#v %v", higher, err)
	_, err = topology.RecordAlive("node-b", transcript.Generation{Incarnation: 2}, []byte("stale"))
	require(t, errors.Is(err, transcript.ErrStaleGeneration), "stale incarnation accepted: %v", err)
	snapshot := topology.Snapshot()
	require(t, len(snapshot.Nodes) == 1 && snapshot.Nodes[0].Generation.Incarnation == 4, "alive snapshot: %#v", snapshot.Nodes)
}

func runJoinContract(t *testing.T) {
	t.Helper()
	remote := transcript.NewTopology(nil, "")
	_, _ = remote.RecordAlive("node-z", transcript.Generation{Incarnation: 2}, []byte("z"))
	_, _ = remote.RecordAlive("node-a", transcript.Generation{Incarnation: 5}, []byte("a"))
	local := transcript.NewTopology(nil, "")
	receipt, err := local.RecordJoin("seed", remote.Snapshot())
	require(t, err == nil, "join: %v", err)
	require(t, receipt.Contact == "seed" && reflect.DeepEqual(receipt.Changed, []string{"node-a", "node-z"}), "ordered join receipt: %#v", receipt)
	snapshot := local.Snapshot()
	require(t, len(snapshot.Nodes) == 2 && snapshot.Nodes[0].Node == "node-a" && snapshot.Nodes[1].Node == "node-z", "merged topology: %#v", snapshot.Nodes)
}

func runBroadcastContract(t *testing.T) {
	t.Helper()
	topology := transcript.NewTopology(nil, "")
	old, err := topology.RecordBroadcast("config", 2, []byte("old"), false)
	require(t, err == nil && old.Accepted, "old named broadcast: %#v %v", old, err)
	latest, err := topology.RecordBroadcast("config", 3, []byte("new"), false)
	require(t, err == nil && latest.Accepted && latest.Ordinal > old.Ordinal, "new named broadcast: %#v %v", latest, err)
	_, err = topology.RecordBroadcast("config", 1, []byte("stale"), false)
	require(t, errors.Is(err, transcript.ErrStaleGeneration), "stale named broadcast accepted: %v", err)
	unique, err := topology.RecordBroadcast("config", 1, []byte("once"), true)
	require(t, err == nil && unique.Unique, "unique broadcast: %#v %v", unique, err)
	snapshot := topology.Snapshot()
	require(t, len(snapshot.Broadcasts) == 2 && string(snapshot.Broadcasts[0].Payload) == "new", "broadcast projection: %#v", snapshot.Broadcasts)
}

func runLeaveContract(t *testing.T) {
	t.Helper()
	topology := transcript.NewTopology(nil, "")
	_, _ = topology.RecordAlive("departing", transcript.Generation{Incarnation: 8, Metadata: 2}, []byte("ready"))
	leave, err := topology.RecordLeave("departing", transcript.Generation{Incarnation: 8, Metadata: 3})
	require(t, err == nil && leave.Accepted, "leave receipt: %#v %v", leave, err)
	_, err = topology.RecordAlive("departing", transcript.Generation{Incarnation: 8, Metadata: 3}, []byte("late"))
	require(t, errors.Is(err, transcript.ErrStaleGeneration), "tombstone did not suppress alive: %v", err)
	restored, err := topology.RecordAlive("departing", transcript.Generation{Incarnation: 9}, []byte("restored"))
	require(t, err == nil && restored.Accepted && !restored.Left, "new incarnation did not restore: %#v %v", restored, err)
}

func runMetadataContract(t *testing.T) {
	t.Helper()
	topology := transcript.NewTopology(nil, "")
	_, _ = topology.RecordAlive("metadata-node", transcript.Generation{Incarnation: 1, Metadata: 1}, []byte("v1"))
	input := []byte("v2")
	receipt, err := topology.RecordMetadata("metadata-node", 2, input)
	require(t, err == nil && receipt.Accepted && string(receipt.Metadata) == "v2", "metadata receipt: %#v %v", receipt, err)
	input[0] = 'x'
	snapshot := topology.Snapshot()
	require(t, len(snapshot.Nodes) == 1 && snapshot.Nodes[0].Generation.Metadata == 2 && string(snapshot.Nodes[0].Metadata) == "v2", "metadata alias or generation loss: %#v", snapshot.Nodes)
	idempotent, err := topology.RecordMetadata("metadata-node", 2, []byte("v2"))
	require(t, err == nil && !idempotent.Accepted, "metadata idempotence: %#v %v", idempotent, err)
}

func runSuspicionContract(t *testing.T) {
	t.Helper()
	topology := transcript.NewTopology(nil, "")
	_, _ = topology.RecordAlive("suspect", transcript.Generation{Incarnation: 4}, nil)
	base := time.Unix(2_000, 0).UTC()
	_, _ = topology.RecordSuspicion("suspect", "observer-b", base.Add(5*time.Second))
	_, _ = topology.RecordSuspicion("suspect", "observer-b", base.Add(9*time.Second))
	receipt, err := topology.RecordSuspicion("suspect", "observer-a", base.Add(2*time.Second))
	require(t, err == nil && reflect.DeepEqual(receipt.Confirmers, []string{"observer-a", "observer-b"}), "distinct suspicion confirmations: %#v %v", receipt, err)
	require(t, receipt.Deadline.Equal(base.Add(2*time.Second)), "earliest suspicion deadline: %v", receipt.Deadline)
	_, err = topology.RecordAlive("suspect", transcript.Generation{Incarnation: 5}, nil)
	require(t, err == nil && len(topology.Snapshot().Suspicions) == 0, "new alive did not clear suspicion: %v", err)
}

func runKeyContract(t *testing.T) {
	t.Helper()
	topology := transcript.NewTopology([]string{"secondary", "primary"}, "primary")
	primary, err := topology.RecordKeyUse("primary")
	require(t, err == nil && primary.Known && primary.Primary && primary.Accepted, "primary key receipt: %#v %v", primary, err)
	secondary, err := topology.RecordKeyUse("secondary")
	require(t, err == nil && secondary.Known && !secondary.Primary && secondary.Accepted, "secondary key receipt: %#v %v", secondary, err)
	_, err = topology.RecordKeyUse("unknown")
	require(t, errors.Is(err, transcript.ErrStaleGeneration), "unknown key accepted: %v", err)
	snapshot := topology.Snapshot()
	require(t, reflect.DeepEqual(snapshot.Keys, []string{"primary", "secondary"}) && snapshot.PrimaryKey == "primary", "key projection: %#v", snapshot)
}

func runNativeContract(t *testing.T) {
	t.Helper()
	config := memberlist.DefaultLocalConfig()
	require(t, config.ProtocolVersion >= memberlist.ProtocolVersionMin && config.ProtocolVersion <= memberlist.ProtocolVersionMax, "protocol bounds: %#v", config.BuildVsnArray())
	allowed, err := memberlist.ParseCIDRs([]string{"127.0.0.0/8"})
	require(t, err == nil && len(allowed) == 1, "CIDR parse: %#v %v", allowed, err)
	node := &memberlist.Node{Name: "loop-node", Addr: net.ParseIP("127.0.0.1"), Port: 7946, State: memberlist.StateAlive}
	require(t, node.Name == "loop-node" && strings.Contains(node.Address(), "7946") && node.FullAddress().Name == "loop-node", "node projections: %#v", node)
	events := make(chan memberlist.NodeEvent, 1)
	delegate := &memberlist.ChannelEventDelegate{Ch: events}
	delegate.NotifyJoin(node)
	node.Name = "caller-mutated"
	event := <-events
	require(t, event.Event == memberlist.NodeJoin && event.Node.Name == "loop-node", "event copy: %#v", event)
	network := &memberlist.MockNetwork{}
	transport := network.NewTransport("loop-node")
	ip, port, err := transport.FinalAdvertiseAddr("", 0)
	require(t, err == nil && ip.IsLoopback() && port > 0, "mock advertise: %v %d %v", ip, port, err)
	require(t, transport.Shutdown() == nil, "mock shutdown")
}
