package centrifugegate_test

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"

	centrifuge "github.com/centrifugal/centrifuge"
)

type recordingTransport struct {
	mu     sync.Mutex
	writes [][]byte
	closes []centrifuge.Disconnect
}

func (t *recordingTransport) Name() string                      { return "memory-recorder" }
func (t *recordingTransport) AcceptProtocol() string            { return "memory" }
func (t *recordingTransport) Protocol() centrifuge.ProtocolType { return centrifuge.ProtocolTypeJSON }
func (t *recordingTransport) ProtocolVersion() centrifuge.ProtocolVersion {
	return centrifuge.ProtocolVersion2
}
func (t *recordingTransport) Unidirectional() bool      { return true }
func (t *recordingTransport) Emulation() bool           { return false }
func (t *recordingTransport) DisabledPushFlags() uint64 { return 0 }
func (t *recordingTransport) PingPongConfig() centrifuge.PingPongConfig {
	return centrifuge.PingPongConfig{}
}
func (t *recordingTransport) Write(value []byte) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.writes = append(t.writes, append([]byte(nil), value...))
	return nil
}
func (t *recordingTransport) WriteMany(values ...[]byte) error {
	for _, value := range values {
		if err := t.Write(value); err != nil {
			return err
		}
	}
	return nil
}
func (t *recordingTransport) Close(disconnect centrifuge.Disconnect) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.closes = append(t.closes, disconnect)
	return nil
}
func (t *recordingTransport) writeCount() int {
	t.mu.Lock()
	defer t.mu.Unlock()
	return len(t.writes)
}
func (t *recordingTransport) closeValues() []centrifuge.Disconnect {
	t.mu.Lock()
	defer t.mu.Unlock()
	return append([]centrifuge.Disconnect(nil), t.closes...)
}
func (t *recordingTransport) contains(value string) bool {
	t.mu.Lock()
	defer t.mu.Unlock()
	for _, write := range t.writes {
		if bytes.Contains(write, []byte(value)) {
			return true
		}
	}
	return false
}

type fixture struct {
	node       *centrifuge.Node
	broker     *centrifuge.MemoryBroker
	presence   *centrifuge.MemoryPresenceManager
	closers    []centrifuge.ClientCloseFunc
	clients    []*centrifuge.Client
	transports []*recordingTransport
}

func newFixture(t *testing.T) *fixture {
	t.Helper()
	node, err := centrifuge.New(centrifuge.Config{
		Name:                  "snapshot-gate",
		ClientStaleCloseDelay: time.Minute,
	})
	if err != nil {
		t.Fatal(err)
	}
	broker, err := centrifuge.NewMemoryBroker(node, centrifuge.MemoryBrokerConfig{})
	if err != nil {
		t.Fatal(err)
	}
	presence, err := centrifuge.NewMemoryPresenceManager(node, centrifuge.MemoryPresenceManagerConfig{})
	if err != nil {
		t.Fatal(err)
	}
	node.SetBroker(broker)
	node.SetPresenceManager(presence)
	if err := node.Run(); err != nil {
		t.Fatal(err)
	}
	f := &fixture{node: node, broker: broker, presence: presence}
	t.Cleanup(func() {
		for _, closer := range f.closers {
			_ = closer()
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		_ = node.Shutdown(ctx)
	})
	return f
}

func (f *fixture) addClient(t *testing.T, user string, subscriptions map[string][]centrifuge.SubscribeOption) (*centrifuge.Client, *recordingTransport) {
	t.Helper()
	transport := &recordingTransport{}
	ctx := centrifuge.SetCredentials(context.Background(), &centrifuge.Credentials{UserID: user, Info: []byte("info/" + user)})
	client, closer, err := centrifuge.NewClient(ctx, f.node, transport)
	if err != nil {
		t.Fatal(err)
	}
	if err := client.ConnectNoErrorToDisconnect(centrifuge.ConnectRequest{}); err != nil {
		t.Fatal(err)
	}
	for channel, options := range subscriptions {
		if err := client.Subscribe(channel, options...); err != nil {
			t.Fatal(err)
		}
		waitFor(t, func() bool {
			return client.IsSubscribed(channel) && f.node.Hub().NumSubscribers(channel) > 0
		})
	}
	f.closers = append(f.closers, closer)
	f.clients = append(f.clients, client)
	f.transports = append(f.transports, transport)
	return client, transport
}

func (f *fixture) publish(t *testing.T, channel, payload string, size int, options ...centrifuge.PublishOption) centrifuge.PublishResult {
	t.Helper()
	all := []centrifuge.PublishOption{centrifuge.WithHistory(size, time.Hour)}
	all = append(all, options...)
	result, err := f.node.Publish(channel, []byte(payload), all...)
	if err != nil {
		t.Fatal(err)
	}
	return result
}

func capture(t *testing.T, node *centrifuge.Node, request centrifuge.MemorySnapshotRequest) centrifuge.MemorySnapshot {
	t.Helper()
	result, err := node.CaptureMemorySnapshot(context.Background(), request)
	if err != nil {
		t.Fatal(err)
	}
	return result
}

func channel(t *testing.T, snapshot centrifuge.MemorySnapshot, name string) centrifuge.MemoryChannelSnapshot {
	t.Helper()
	for _, value := range snapshot.Channels {
		if value.Channel == name {
			return value
		}
	}
	t.Fatalf("channel %q absent from snapshot", name)
	return centrifuge.MemoryChannelSnapshot{}
}

func waitFor(t *testing.T, predicate func() bool) {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if predicate() {
			return
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatal("observable state did not settle")
}

func equalStrings(values []string, expected ...string) bool {
	return fmt.Sprint(values) == fmt.Sprint(expected)
}

// Native atomic baseline: seven unrelated stable upstream surfaces.

func TestCentrifugeV2A01DisconnectProjection(t *testing.T) {
	value := centrifuge.Disconnect{Code: 4311, Reason: "maintenance"}
	if value.Code != 4311 || value.Reason != "maintenance" || !strings.Contains(value.String(), "4311") || !strings.Contains(value.Error(), "maintenance") {
		t.Fatalf("disconnect projection changed: %v", value)
	}
}

func TestCentrifugeV2A02ErrorProjection(t *testing.T) {
	value := &centrifuge.Error{Code: 701, Message: "retry later", Temporary: true}
	if value.Code != 701 || value.Message != "retry later" || !value.Temporary || value.Error() != "701: retry later" {
		t.Fatalf("error projection changed: %+v", value)
	}
}

func TestCentrifugeV2A03StreamPositionValue(t *testing.T) {
	first := centrifuge.StreamPosition{Offset: 17, Epoch: "epoch-a"}
	second := first
	second.Offset++
	if first.Offset != 17 || second.Offset != 18 || first.Epoch != second.Epoch || first == second {
		t.Fatalf("stream position value semantics changed: first=%+v second=%+v", first, second)
	}
}

func TestCentrifugeV2A04PublicationContainer(t *testing.T) {
	publication := centrifuge.Publication{Offset: 9, Data: []byte("body"), Tags: map[string]string{"kind": "alpha"}, Info: &centrifuge.ClientInfo{ClientID: "c4", UserID: "u4"}}
	if publication.Offset != 9 || string(publication.Data) != "body" || publication.Tags["kind"] != "alpha" || publication.Info.UserID != "u4" {
		t.Fatalf("publication projection changed: %+v", publication)
	}
}

func TestCentrifugeV2A05MemoryPresenceLifecycle(t *testing.T) {
	f := newFixture(t)
	info := &centrifuge.ClientInfo{ClientID: "manual-a05", UserID: "user-a05"}
	if err := f.presence.AddPresence("presence/a05", "manual-a05", info); err != nil {
		t.Fatal(err)
	}
	values, _ := f.presence.Presence("presence/a05")
	stats, _ := f.presence.PresenceStats("presence/a05")
	if len(values) != 1 || values["manual-a05"].UserID != "user-a05" || stats.NumClients != 1 || stats.NumUsers != 1 {
		t.Fatalf("presence add projection changed: values=%v stats=%+v", values, stats)
	}
}

func TestCentrifugeV2A06MemoryBrokerRetainsPublication(t *testing.T) {
	f := newFixture(t)
	result := f.publish(t, "broker/a06", "retained-a06", 3)
	history, top, err := f.broker.History("broker/a06", centrifuge.HistoryOptions{Filter: centrifuge.HistoryFilter{Limit: -1}})
	if err != nil || result.Offset != 1 || result.Epoch == "" || top != result.StreamPosition || len(history) != 1 || string(history[0].Data) != "retained-a06" {
		t.Fatalf("memory broker projection changed: result=%+v top=%+v history=%v err=%v", result, top, history, err)
	}
}

func TestCentrifugeV2A07FreshHubIsEmpty(t *testing.T) {
	f := newFixture(t)
	if f.node.Hub().NumClients() != 0 || f.node.Hub().NumSubscriptions() != 0 || f.node.Hub().NumChannels() != 0 || len(f.node.Hub().Channels()) != 0 {
		t.Fatalf("fresh Hub is not empty: clients=%d subscriptions=%d channels=%v", f.node.Hub().NumClients(), f.node.Hub().NumSubscriptions(), f.node.Hub().Channels())
	}
}

// Atomic snapshot behavior.

func TestCentrifugeV2A08RejectsEmptySelectedChannel(t *testing.T) {
	f := newFixture(t)
	valid := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"valid/a08"}, HistoryLimit: 0})
	result, err := f.node.CaptureMemorySnapshot(context.Background(), centrifuge.MemorySnapshotRequest{Channels: []string{"valid", "  "}, HistoryLimit: -1})
	if len(valid.Channels) != 1 || valid.Channels[0].Channel != "valid/a08" || err == nil || !errors.Is(err, centrifuge.ErrMemorySnapshotUnavailable) || len(result.Channels) != 0 || len(result.Clients) != 0 {
		t.Fatalf("empty channel was not rejected atomically: result=%+v err=%v", result, err)
	}
}

func TestCentrifugeV2A09RejectsDuplicateSelectedChannel(t *testing.T) {
	f := newFixture(t)
	valid := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"dup/a09"}, HistoryLimit: 0})
	request := centrifuge.MemorySnapshotRequest{Channels: []string{"dup/a09", "dup/a09"}, HistoryLimit: -1}
	result, err := f.node.CaptureMemorySnapshot(context.Background(), request)
	if len(valid.Channels) != 1 || !valid.Consistent || err == nil || !errors.Is(err, centrifuge.ErrMemorySnapshotUnavailable) || result.Consistent || len(result.Problems) != 0 {
		t.Fatalf("duplicate selection published a result: result=%+v err=%v", result, err)
	}
}

func TestCentrifugeV2A10RejectsInvalidHistoryLimit(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "limit/a10", "kept", 2)
	valid := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"limit/a10"}, HistoryLimit: 0})
	result, err := f.node.CaptureMemorySnapshot(context.Background(), centrifuge.MemorySnapshotRequest{Channels: []string{"limit/a10"}, HistoryLimit: -2})
	if valid.Channels[0].Position.Offset != 1 || len(valid.Channels[0].Publications) != 0 || err == nil || !errors.Is(err, centrifuge.ErrMemorySnapshotUnavailable) || len(result.Channels) != 0 || channelCount(result) != 0 {
		t.Fatalf("invalid history limit published a result: result=%+v err=%v", result, err)
	}
}

func channelCount(snapshot centrifuge.MemorySnapshot) int { return len(snapshot.Channels) }

func TestCentrifugeV2A11CanonicalizesExplicitChannelOrder(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "order/z", "z", 2)
	f.publish(t, "order/a", "a", 2)
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"order/z", "order/a"}, HistoryLimit: -1})
	if len(snapshot.Channels) != 2 || snapshot.Channels[0].Channel != "order/a" || snapshot.Channels[1].Channel != "order/z" || !snapshot.Consistent {
		t.Fatalf("explicit order was not canonical: %+v", snapshot)
	}
}

func TestCentrifugeV2A12DiscoversRetainedChannel(t *testing.T) {
	f := newFixture(t)
	first := f.publish(t, "discover/a12", "one", 4)
	second := f.publish(t, "discover/a12", "two", 4)
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{HistoryLimit: -1})
	view := channel(t, snapshot, "discover/a12")
	if len(snapshot.Channels) != 1 || view.Position != second.StreamPosition || len(view.Publications) != 2 || view.Publications[0].Offset != first.Offset {
		t.Fatalf("retained channel discovery failed: %+v", snapshot)
	}
}

func TestCentrifugeV2A13PositionOnlyHistoryView(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "position/a13", "one", 3)
	top := f.publish(t, "position/a13", "two", 3)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"position/a13"}, HistoryLimit: 0}), "position/a13")
	if view.Position != top.StreamPosition || len(view.Publications) != 0 || view.Channel != "position/a13" || view.Recovery.Requested {
		t.Fatalf("position-only view changed: %+v", view)
	}
}

func TestCentrifugeV2A14BoundsRetainedView(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "bound/a14", "first", 5)
	f.publish(t, "bound/a14", "second", 5)
	top := f.publish(t, "bound/a14", "third", 5)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"bound/a14"}, HistoryLimit: 1}), "bound/a14")
	if len(view.Publications) != 1 || view.Publications[0].Offset != 1 || view.Position != top.StreamPosition || string(view.Publications[0].Data) != "first" {
		t.Fatalf("history limit projection changed: %+v", view)
	}
}

func TestCentrifugeV2A15OwnsPublicationProjection(t *testing.T) {
	f := newFixture(t)
	info := &centrifuge.ClientInfo{ClientID: "publisher-a15", UserID: "user-a15", ConnInfo: []byte("conn-a15")}
	f.publish(t, "ownership/a15", "original-a15", 2, centrifuge.WithTags(map[string]string{"kind": "original"}), centrifuge.WithClientInfo(info))
	first := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"ownership/a15"}, HistoryLimit: -1})
	if len(first.Channels) != 1 || len(first.Channels[0].Publications) != 1 {
		t.Fatalf("publication projection missing: %+v", first)
	}
	first.Channels[0].Publications[0].Data[0] = 'X'
	first.Channels[0].Publications[0].Tags["kind"] = "changed"
	first.Channels[0].Publications[0].Info.ConnInfo[0] = 'Y'
	second := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"ownership/a15"}, HistoryLimit: -1})
	pub := second.Channels[0].Publications[0]
	if string(pub.Data) != "original-a15" || pub.Tags["kind"] != "original" || string(pub.Info.ConnInfo) != "conn-a15" || pub.Info.UserID != "user-a15" {
		t.Fatalf("snapshot exposed runtime publication storage: %+v", pub)
	}
}

func TestCentrifugeV2A16HonorsCancelledContext(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "cancel/a16", "stable", 2)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	result, err := f.node.CaptureMemorySnapshot(ctx, centrifuge.MemorySnapshotRequest{Channels: []string{"cancel/a16"}, HistoryLimit: -1})
	if !errors.Is(err, context.Canceled) || len(result.Channels) != 0 || len(result.Clients) != 0 || result.Consistent {
		t.Fatalf("cancelled capture published partial state: result=%+v err=%v", result, err)
	}
}

// Native composition baseline: seven genuine upstream cross-component flows.

func TestCentrifugeV2I01NodePublishFeedsHistory(t *testing.T) {
	f := newFixture(t)
	first := f.publish(t, "native/i01", "one", 4)
	second := f.publish(t, "native/i01", "two", 4)
	history, err := f.node.History("native/i01", centrifuge.WithLimit(-1))
	if err != nil || first.Offset != 1 || second.Offset != 2 || history.StreamPosition != second.StreamPosition || len(history.Publications) != 2 {
		t.Fatalf("publish/history seam changed: first=%+v second=%+v history=%+v err=%v", first, second, history, err)
	}
}

func TestCentrifugeV2I02HistorySinceSelectsSuffix(t *testing.T) {
	f := newFixture(t)
	first := f.publish(t, "native/i02", "one", 5)
	f.publish(t, "native/i02", "two", 5)
	top := f.publish(t, "native/i02", "three", 5)
	history, err := f.node.History("native/i02", centrifuge.WithSince(&first.StreamPosition), centrifuge.WithLimit(-1))
	if err != nil || len(history.Publications) != 2 || history.Publications[0].Offset != 2 || history.Publications[1].Offset != 3 || history.StreamPosition != top.StreamPosition {
		t.Fatalf("history suffix seam changed: %+v err=%v", history, err)
	}
}

func TestCentrifugeV2I03PresenceAndStatsAgree(t *testing.T) {
	f := newFixture(t)
	for _, row := range []struct{ id, user string }{{"c1", "u"}, {"c2", "u"}, {"c3", "v"}} {
		if err := f.presence.AddPresence("native/i03", row.id, &centrifuge.ClientInfo{ClientID: row.id, UserID: row.user}); err != nil {
			t.Fatal(err)
		}
	}
	presence, _ := f.node.Presence("native/i03")
	stats, _ := f.node.PresenceStats("native/i03")
	if len(presence.Presence) != 3 || stats.NumClients != 3 || stats.NumUsers != 2 || presence.Presence["c2"].UserID != "u" {
		t.Fatalf("presence/stats seam changed: presence=%v stats=%+v", presence, stats)
	}
}

func TestCentrifugeV2I04ConnectAddsHubMembership(t *testing.T) {
	f := newFixture(t)
	client, transport := f.addClient(t, "native-user-i04", nil)
	connections := f.node.Hub().Connections()
	users := f.node.Hub().UserConnections("native-user-i04")
	if len(connections) != 1 || connections[client.ID()] != client || len(users) != 1 || transport.Name() != "memory-recorder" {
		t.Fatalf("connect/Hub seam changed: connections=%v users=%v writes=%d", connections, users, transport.writeCount())
	}
}

func TestCentrifugeV2I05SubscribeAddsHubChannel(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "native-user-i05", map[string][]centrifuge.SubscribeOption{"native/i05": nil})
	channels := f.node.Hub().Channels()
	sort.Strings(channels)
	if !client.IsSubscribed("native/i05") || f.node.Hub().NumSubscribers("native/i05") != 1 || !equalStrings(channels, "native/i05") || f.node.Hub().NumSubscriptions() != 1 {
		t.Fatalf("subscribe/Hub seam changed: client=%v channels=%v", client.Channels(), channels)
	}
}

func TestCentrifugeV2I06UnsubscribePreservesSibling(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "native-user-i06", map[string][]centrifuge.SubscribeOption{"native/i06/a": nil, "native/i06/b": nil})
	client.Unsubscribe("native/i06/a")
	if client.IsSubscribed("native/i06/a") || !client.IsSubscribed("native/i06/b") || f.node.Hub().NumSubscribers("native/i06/a") != 0 || f.node.Hub().NumSubscribers("native/i06/b") != 1 {
		t.Fatalf("unsubscribe removed wrong membership: client=%v hub=%v", client.Channels(), f.node.Hub().Channels())
	}
}

func TestCentrifugeV2I07DisconnectClosesTransportAndHub(t *testing.T) {
	f := newFixture(t)
	client, transport := f.addClient(t, "native-user-i07", map[string][]centrifuge.SubscribeOption{"native/i07": nil})
	client.Disconnect(centrifuge.DisconnectForceNoReconnect)
	waitFor(t, func() bool { return len(transport.closeValues()) == 1 })
	closes := transport.closeValues()
	if len(closes) != 1 || closes[0] != centrifuge.DisconnectForceNoReconnect || f.node.Hub().NumClients() != 0 || f.node.Hub().NumSubscribers("native/i07") != 0 {
		t.Fatalf("disconnect cleanup seam changed: closes=%v clients=%d subscribers=%d", closes, f.node.Hub().NumClients(), f.node.Hub().NumSubscribers("native/i07"))
	}
}

// Integration snapshot behavior.

func TestCentrifugeV2I08CapturesContinuousRecoverySuffix(t *testing.T) {
	f := newFixture(t)
	first := f.publish(t, "recovery/i08", "one", 6)
	f.publish(t, "recovery/i08", "two", 6)
	top := f.publish(t, "recovery/i08", "three", 6)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"recovery/i08"}, Since: map[string]centrifuge.StreamPosition{"recovery/i08": first.StreamPosition}, HistoryLimit: 0}), "recovery/i08")
	if !view.Recovery.Requested || !view.Recovery.Recoverable || len(view.Recovery.Publications) != 2 || view.Recovery.Publications[0].Offset != 2 || view.Position != top.StreamPosition {
		t.Fatalf("continuous recovery projection changed: %+v", view)
	}
}

func TestCentrifugeV2I09CapturesCurrentPositionAsEmptySuffix(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "recovery/i09", "one", 3)
	top := f.publish(t, "recovery/i09", "two", 3)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"recovery/i09"}, Since: map[string]centrifuge.StreamPosition{"recovery/i09": top.StreamPosition}, HistoryLimit: -1}), "recovery/i09")
	if !view.Recovery.Requested || !view.Recovery.Recoverable || len(view.Recovery.Publications) != 0 || view.Recovery.Since != top.StreamPosition {
		t.Fatalf("current-position recovery changed: %+v", view.Recovery)
	}
}

func TestCentrifugeV2I10MarksEpochMismatchUnrecoverable(t *testing.T) {
	f := newFixture(t)
	top := f.publish(t, "recovery/i10", "one", 3)
	wrong := centrifuge.StreamPosition{Offset: top.Offset, Epoch: "wrong-epoch"}
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"recovery/i10"}, Since: map[string]centrifuge.StreamPosition{"recovery/i10": wrong}, HistoryLimit: -1}), "recovery/i10")
	if !view.Recovery.Requested || view.Recovery.Recoverable || len(view.Recovery.Publications) != 0 || view.Position.Epoch == wrong.Epoch {
		t.Fatalf("epoch mismatch claimed recovery: %+v", view)
	}
}

func TestCentrifugeV2I11DetectsTrimmedRecoveryGap(t *testing.T) {
	f := newFixture(t)
	first := f.publish(t, "recovery/i11", "one", 2)
	f.publish(t, "recovery/i11", "two", 2)
	f.publish(t, "recovery/i11", "three", 2)
	top := f.publish(t, "recovery/i11", "four", 2)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"recovery/i11"}, Since: map[string]centrifuge.StreamPosition{"recovery/i11": first.StreamPosition}, HistoryLimit: -1}), "recovery/i11")
	if view.Recovery.Recoverable || len(view.Recovery.Publications) != 0 || view.Position != top.StreamPosition || len(view.Publications) != 2 {
		t.Fatalf("trimmed gap was hidden: %+v", view)
	}
}

func TestCentrifugeV2I12TracksHistoryRemovalGeneration(t *testing.T) {
	f := newFixture(t)
	old := f.publish(t, "reset/i12", "old", 3)
	if err := f.node.RemoveHistory("reset/i12"); err != nil {
		t.Fatal(err)
	}
	fresh := f.publish(t, "reset/i12", "fresh", 3)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"reset/i12"}, Since: map[string]centrifuge.StreamPosition{"reset/i12": old.StreamPosition}, HistoryLimit: -1}), "reset/i12")
	if fresh.Offset != old.Offset+1 || fresh.Epoch != old.Epoch || !view.Recovery.Recoverable || len(view.Publications) != 1 || string(view.Publications[0].Data) != "fresh" {
		t.Fatalf("removed history generation leaked: old=%+v fresh=%+v view=%+v", old, fresh, view)
	}
}

func TestCentrifugeV2I13CanonicalizesMultiChannelState(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "multi/i13/z", "z1", 2)
	f.publish(t, "multi/i13/a", "a1", 2)
	f.publish(t, "multi/i13/m", "m1", 2)
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"multi/i13/z", "multi/i13/m", "multi/i13/a"}, HistoryLimit: -1})
	if len(snapshot.Channels) != 3 || snapshot.Channels[0].Channel != "multi/i13/a" || snapshot.Channels[1].Channel != "multi/i13/m" || snapshot.Channels[2].Channel != "multi/i13/z" {
		t.Fatalf("multi-channel order changed: %+v", snapshot.Channels)
	}
}

func TestCentrifugeV2I14DiscoversUnionOfRuntimeViews(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "union/i14/history", "history", 2)
	if err := f.presence.AddPresence("union/i14/presence", "manual-i14", &centrifuge.ClientInfo{ClientID: "manual-i14", UserID: "user-i14"}); err != nil {
		t.Fatal(err)
	}
	f.addClient(t, "union-user-i14", map[string][]centrifuge.SubscribeOption{"union/i14/hub": nil})
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{HistoryLimit: 0})
	if len(snapshot.Channels) != 3 {
		t.Fatalf("runtime-view union has %d channels: %+v", len(snapshot.Channels), snapshot)
	}
	names := []string{snapshot.Channels[0].Channel, snapshot.Channels[1].Channel, snapshot.Channels[2].Channel}
	if !equalStrings(names, "union/i14/history", "union/i14/hub", "union/i14/presence") || snapshot.Consistent || len(snapshot.Problems) != 1 {
		t.Fatalf("runtime-view union changed: names=%v snapshot=%+v", names, snapshot)
	}
}

func TestCentrifugeV2I15SortsSubscriberIdentities(t *testing.T) {
	f := newFixture(t)
	clients := make([]*centrifuge.Client, 0, 3)
	for _, user := range []string{"user-z", "user-a", "user-m"} {
		client, _ := f.addClient(t, user, map[string][]centrifuge.SubscribeOption{"subs/i15": nil})
		clients = append(clients, client)
	}
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"subs/i15"}, HistoryLimit: 0})
	view := snapshot.Channels[0]
	expected := []string{clients[0].ID(), clients[1].ID(), clients[2].ID()}
	sort.Strings(expected)
	if !equalStrings(view.Subscribers, expected...) || len(snapshot.Clients) != 3 || f.node.Hub().NumSubscribers("subs/i15") != 3 || !snapshot.Consistent {
		t.Fatalf("subscriber identities not canonical: got=%v expected=%v", view.Subscribers, expected)
	}
}

func TestCentrifugeV2I16FiltersClientChannelsBySelection(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "filter-user-i16", map[string][]centrifuge.SubscribeOption{"filter/i16/a": nil, "filter/i16/b": nil, "filter/i16/c": nil})
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"filter/i16/c", "filter/i16/a"}, HistoryLimit: 0})
	if len(snapshot.Clients) != 1 || snapshot.Clients[0].ClientID != client.ID() || !equalStrings(snapshot.Clients[0].Channels, "filter/i16/a", "filter/i16/c") || snapshot.Clients[0].UserID != "filter-user-i16" {
		t.Fatalf("client selection leaked channels: %+v", snapshot.Clients)
	}
}

func TestCentrifugeV2I17SortsPresenceIdentities(t *testing.T) {
	f := newFixture(t)
	for _, id := range []string{"presence-z", "presence-a", "presence-m"} {
		if err := f.presence.AddPresence("presence/i17", id, &centrifuge.ClientInfo{ClientID: id, UserID: "u/" + id}); err != nil {
			t.Fatal(err)
		}
	}
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"presence/i17"}, HistoryLimit: 0}), "presence/i17")
	if len(view.Presence) != 3 || view.Presence[0].ClientID != "presence-a" || view.Presence[1].ClientID != "presence-m" || view.Presence[2].ClientID != "presence-z" {
		t.Fatalf("presence identities not canonical: %+v", view.Presence)
	}
}

func TestCentrifugeV2I18OwnsPresenceProjection(t *testing.T) {
	f := newFixture(t)
	info := &centrifuge.ClientInfo{ClientID: "presence-i18", UserID: "user-i18", ConnInfo: []byte("conn-i18"), ChanInfo: []byte("chan-i18")}
	if err := f.presence.AddPresence("presence/i18", "presence-i18", info); err != nil {
		t.Fatal(err)
	}
	first := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"presence/i18"}, HistoryLimit: 0})
	if len(first.Channels) != 1 || len(first.Channels[0].Presence) != 1 {
		t.Fatalf("presence projection missing: %+v", first)
	}
	first.Channels[0].Presence[0].ConnInfo[0] = 'X'
	first.Channels[0].Presence[0].ChanInfo[0] = 'Y'
	second := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"presence/i18"}, HistoryLimit: 0})
	row := second.Channels[0].Presence[0]
	if string(row.ConnInfo) != "conn-i18" || string(row.ChanInfo) != "chan-i18" || row.UserID != "user-i18" || row.ClientID != "presence-i18" {
		t.Fatalf("snapshot exposed presence storage: %+v", row)
	}
}

func TestCentrifugeV2I19ReconcilesSubscriberAndPresence(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "coherent-user-i19", map[string][]centrifuge.SubscribeOption{"coherent/i19": {centrifuge.WithEmitPresence(true)}})
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"coherent/i19"}, HistoryLimit: 0})
	view := snapshot.Channels[0]
	if !snapshot.Consistent || len(snapshot.Problems) != 0 || !equalStrings(view.Subscribers, client.ID()) || len(view.Presence) != 1 || view.Presence[0].ClientID != client.ID() {
		t.Fatalf("coherent runtime reported disagreement: %+v", snapshot)
	}
}

func TestCentrifugeV2I20ReportsOrphanPresence(t *testing.T) {
	f := newFixture(t)
	if err := f.presence.AddPresence("orphan/i20", "orphan-client", &centrifuge.ClientInfo{ClientID: "orphan-client", UserID: "orphan-user"}); err != nil {
		t.Fatal(err)
	}
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"orphan/i20"}, HistoryLimit: 0})
	if snapshot.Consistent || len(snapshot.Problems) != 1 || !strings.Contains(snapshot.Problems[0], "orphan-client") || len(snapshot.Channels[0].Subscribers) != 0 {
		t.Fatalf("orphan presence was hidden: %+v", snapshot)
	}
}

func TestCentrifugeV2I21ReflectsUnsubscribeCleanup(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "cleanup-user-i21", map[string][]centrifuge.SubscribeOption{"cleanup/i21": {centrifuge.WithEmitPresence(true)}, "cleanup/i21/keep": nil})
	before := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"cleanup/i21", "cleanup/i21/keep"}, HistoryLimit: 0})
	client.Unsubscribe("cleanup/i21")
	after := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"cleanup/i21", "cleanup/i21/keep"}, HistoryLimit: 0})
	removed, kept := channel(t, after, "cleanup/i21"), channel(t, after, "cleanup/i21/keep")
	if len(before.Channels[0].Subscribers) != 1 || len(removed.Subscribers) != 0 || len(removed.Presence) != 0 || !equalStrings(kept.Subscribers, client.ID()) {
		t.Fatalf("unsubscribe cleanup snapshot changed: before=%+v after=%+v", before, after)
	}
}

func TestCentrifugeV2I22ReflectsDisconnectCleanup(t *testing.T) {
	f := newFixture(t)
	client, transport := f.addClient(t, "disconnect-user-i22", map[string][]centrifuge.SubscribeOption{"disconnect/i22/a": {centrifuge.WithEmitPresence(true)}, "disconnect/i22/b": {centrifuge.WithEmitPresence(true)}})
	client.Disconnect(centrifuge.DisconnectForceNoReconnect)
	waitFor(t, func() bool { return len(transport.closeValues()) == 1 })
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"disconnect/i22/a", "disconnect/i22/b"}, HistoryLimit: 0})
	if len(snapshot.Clients) != 0 || len(snapshot.Channels[0].Subscribers) != 0 || len(snapshot.Channels[1].Subscribers) != 0 || len(snapshot.Channels[0].Presence)+len(snapshot.Channels[1].Presence) != 0 {
		t.Fatalf("disconnect cleanup leaked into snapshot: %+v", snapshot)
	}
}

func TestCentrifugeV2I23PreservesIdempotentPublishResult(t *testing.T) {
	f := newFixture(t)
	first := f.publish(t, "idempotent/i23", "payload", 4, centrifuge.WithIdempotencyKey("same-key"))
	second := f.publish(t, "idempotent/i23", "different", 4, centrifuge.WithIdempotencyKey("same-key"))
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"idempotent/i23"}, HistoryLimit: -1}), "idempotent/i23")
	if first.StreamPosition != second.StreamPosition || second.FromCache != true || len(view.Publications) != 1 || string(view.Publications[0].Data) != "payload" {
		t.Fatalf("idempotent publication duplicated: first=%+v second=%+v view=%+v", first, second, view)
	}
}

func TestCentrifugeV2I24RejectsUnselectedRecoveryChannel(t *testing.T) {
	f := newFixture(t)
	f.publish(t, "selected/i24", "selected", 2)
	f.publish(t, "other/i24", "other", 2)
	request := centrifuge.MemorySnapshotRequest{Channels: []string{"selected/i24"}, Since: map[string]centrifuge.StreamPosition{"other/i24": {Offset: 1, Epoch: "foreign"}}, HistoryLimit: -1}
	result, err := f.node.CaptureMemorySnapshot(context.Background(), request)
	valid := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"selected/i24"}, HistoryLimit: -1})
	if err == nil || !errors.Is(err, centrifuge.ErrMemorySnapshotUnavailable) || len(result.Channels) != 0 || len(result.Clients) != 0 || len(valid.Channels) != 1 || len(valid.Channels[0].Publications) != 1 || string(valid.Channels[0].Publications[0].Data) != "selected" {
		t.Fatalf("unselected recovery channel produced a partial result: result=%+v err=%v", result, err)
	}
}

// System behavior: end-to-end views across at least three owners.

func TestCentrifugeV2S01LivePublishSessionView(t *testing.T) {
	f := newFixture(t)
	client, transport := f.addClient(t, "system-user-s01", map[string][]centrifuge.SubscribeOption{"system/s01": {centrifuge.WithPositioning(true), centrifuge.WithEmitPresence(true)}})
	baseline := transport.writeCount()
	result := f.publish(t, "system/s01", `{"root":"live-s01"}`, 5, centrifuge.WithTags(map[string]string{"root": "s01"}))
	waitFor(t, func() bool { return transport.writeCount() > baseline && transport.contains("live-s01") })
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s01"}, HistoryLimit: -1})
	view := snapshot.Channels[0]
	if !snapshot.Consistent || view.Position != result.StreamPosition || len(view.Publications) != 1 || !equalStrings(view.Subscribers, client.ID()) || len(view.Presence) != 1 {
		t.Fatalf("live session views diverged: snapshot=%+v writes=%d", snapshot, transport.writeCount())
	}
}

func TestCentrifugeV2S02TwoClientSharedUserView(t *testing.T) {
	f := newFixture(t)
	first, _ := f.addClient(t, "shared-user-s02", map[string][]centrifuge.SubscribeOption{"system/s02": {centrifuge.WithEmitPresence(true)}})
	second, _ := f.addClient(t, "shared-user-s02", map[string][]centrifuge.SubscribeOption{"system/s02": {centrifuge.WithEmitPresence(true)}})
	f.publish(t, "system/s02", `{"value":"shared"}`, 3)
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s02"}, HistoryLimit: -1})
	expected := []string{first.ID(), second.ID()}
	sort.Strings(expected)
	stats, _ := f.node.PresenceStats("system/s02")
	if !equalStrings(snapshot.Channels[0].Subscribers, expected...) || len(snapshot.Clients) != 2 || len(snapshot.Channels[0].Presence) != 2 || stats.NumClients != 2 || stats.NumUsers != 1 {
		t.Fatalf("shared-user views diverged: snapshot=%+v stats=%+v", snapshot, stats)
	}
}

func TestCentrifugeV2S03PartialUnsubscribeWorkflow(t *testing.T) {
	f := newFixture(t)
	client, firstTransport := f.addClient(t, "partial-user-s03", map[string][]centrifuge.SubscribeOption{"system/s03/a": {centrifuge.WithEmitPresence(true)}, "system/s03/b": {centrifuge.WithEmitPresence(true)}})
	_, secondTransport := f.addClient(t, "remaining-user-s03", map[string][]centrifuge.SubscribeOption{"system/s03/a": {centrifuge.WithEmitPresence(true)}})
	client.Unsubscribe("system/s03/a")
	secondWrites := secondTransport.writeCount()
	f.publish(t, "system/s03/a", `{"value":"only-remaining"}`, 3)
	waitFor(t, func() bool {
		return secondTransport.writeCount() > secondWrites && secondTransport.contains("only-remaining")
	})
	snapshot := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s03/a", "system/s03/b"}, HistoryLimit: -1})
	if firstTransport.contains("only-remaining") || len(channel(t, snapshot, "system/s03/a").Subscribers) != 1 || !equalStrings(channel(t, snapshot, "system/s03/b").Subscribers, client.ID()) || !snapshot.Consistent {
		t.Fatalf("partial unsubscribe workflow diverged: %+v", snapshot)
	}
}

func TestCentrifugeV2S04TrimmedWindowRecoveryBoundary(t *testing.T) {
	f := newFixture(t)
	positions := make([]centrifuge.PublishResult, 0, 5)
	for i := 1; i <= 5; i++ {
		positions = append(positions, f.publish(t, "system/s04", fmt.Sprintf("value-%d", i), 3))
	}
	request := centrifuge.MemorySnapshotRequest{Channels: []string{"system/s04"}, Since: map[string]centrifuge.StreamPosition{"system/s04": positions[1].StreamPosition}, HistoryLimit: -1}
	view := channel(t, capture(t, f.node, request), "system/s04")
	if !view.Recovery.Recoverable || len(view.Recovery.Publications) != 3 || view.Recovery.Publications[0].Offset != 3 || view.Recovery.Publications[2].Offset != 5 || len(view.Publications) != 3 {
		t.Fatalf("retained recovery boundary changed: %+v", view)
	}
}

func TestCentrifugeV2S05HistoryResetStartsFreshGeneration(t *testing.T) {
	f := newFixture(t)
	old := f.publish(t, "system/s05", "old-one", 4)
	f.publish(t, "system/s05", "old-two", 4)
	if err := f.node.RemoveHistory("system/s05"); err != nil {
		t.Fatal(err)
	}
	fresh := f.publish(t, "system/s05", "fresh-one", 4)
	view := channel(t, capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s05"}, Since: map[string]centrifuge.StreamPosition{"system/s05": old.StreamPosition}, HistoryLimit: -1}), "system/s05")
	if fresh.Offset != 3 || fresh.Epoch != old.Epoch || view.Recovery.Recoverable || len(view.Publications) != 1 || view.Position != fresh.StreamPosition {
		t.Fatalf("fresh generation reused removed state: old=%+v fresh=%+v view=%+v", old, fresh, view)
	}
}

func TestCentrifugeV2S06SnapshotGenerationOwnsPriorState(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "owned-user-s06", map[string][]centrifuge.SubscribeOption{"system/s06": {centrifuge.WithEmitPresence(true)}})
	firstResult := f.publish(t, "system/s06", `{"generation":"one"}`, 4)
	first := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s06"}, HistoryLimit: -1})
	client.Unsubscribe("system/s06")
	secondResult := f.publish(t, "system/s06", `{"generation":"two"}`, 4)
	second := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s06"}, HistoryLimit: -1})
	if first.Channels[0].Position != firstResult.StreamPosition || len(first.Channels[0].Subscribers) != 1 || len(first.Channels[0].Presence) != 1 || second.Channels[0].Position != secondResult.StreamPosition || len(second.Channels[0].Subscribers) != 0 {
		t.Fatalf("snapshot generations shared lifecycle state: first=%+v second=%+v", first, second)
	}
}

func TestCentrifugeV2S07CancellationLeavesRuntimeUntouched(t *testing.T) {
	f := newFixture(t)
	client, _ := f.addClient(t, "cancel-user-s07", map[string][]centrifuge.SubscribeOption{"system/s07": {centrifuge.WithEmitPresence(true)}})
	top := f.publish(t, "system/s07", `{"state":"before-cancel"}`, 3)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	failed, err := f.node.CaptureMemorySnapshot(ctx, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s07"}, HistoryLimit: -1})
	after := capture(t, f.node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s07"}, HistoryLimit: -1})
	if !errors.Is(err, context.Canceled) || len(failed.Channels) != 0 || after.Channels[0].Position != top.StreamPosition || !equalStrings(after.Channels[0].Subscribers, client.ID()) || !after.Consistent {
		t.Fatalf("cancelled capture mutated runtime: failed=%+v err=%v after=%+v", failed, err, after)
	}
}

func TestCentrifugeV2S08ShutdownRejectsNewSnapshot(t *testing.T) {
	node, err := centrifuge.New(centrifuge.Config{Name: "shutdown-s08"})
	if err != nil {
		t.Fatal(err)
	}
	if err := node.Run(); err != nil {
		t.Fatal(err)
	}
	if _, err := node.Publish("system/s08", []byte("before-shutdown"), centrifuge.WithHistory(2, time.Hour)); err != nil {
		t.Fatal(err)
	}
	before := capture(t, node, centrifuge.MemorySnapshotRequest{Channels: []string{"system/s08"}, HistoryLimit: -1})
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := node.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
	result, captureErr := node.CaptureMemorySnapshot(context.Background(), centrifuge.MemorySnapshotRequest{Channels: []string{"system/s08"}, HistoryLimit: -1})
	if len(before.Channels) != 1 || before.Channels[0].Position.Offset != 1 || captureErr == nil || !errors.Is(captureErr, centrifuge.ErrMemorySnapshotUnavailable) || len(result.Channels) != 0 || result.Consistent {
		t.Fatalf("shutdown node published snapshot: result=%+v err=%v", result, captureErr)
	}
}
