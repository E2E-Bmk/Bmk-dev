package raftv3_test

import (
	"errors"
	"io"
	"sync"
	"testing"
	"time"

	raft "github.com/hashicorp/raft"
)

type nodeFixture struct {
	r     *raft.Raft
	fsm   raft.FSM
	store *raft.InmemStore
	snaps *raft.InmemSnapshotStore
	trans *raft.InmemTransport
	id    raft.ServerID
	addr  raft.ServerAddress
}

func testConfig(id raft.ServerID) *raft.Config {
	conf := raft.DefaultConfig()
	conf.LocalID = id
	conf.HeartbeatTimeout = 80 * time.Millisecond
	conf.ElectionTimeout = 80 * time.Millisecond
	conf.LeaderLeaseTimeout = 80 * time.Millisecond
	conf.CommitTimeout = 5 * time.Millisecond
	conf.SnapshotThreshold = 8192
	conf.SnapshotInterval = time.Hour
	conf.LogOutput = io.Discard
	return conf
}

func oneVoter(id raft.ServerID, addr raft.ServerAddress) raft.Configuration {
	return raft.Configuration{Servers: []raft.Server{{Suffrage: raft.Voter, ID: id, Address: addr}}}
}

func waitForState(t *testing.T, r *raft.Raft, state raft.RaftState) {
	t.Helper()
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if r.State() == state {
			return
		}
		time.Sleep(5 * time.Millisecond)
	}
	t.Fatalf("state did not become %v; got %v", state, r.State())
}

func newSingle(t *testing.T, label string, fsm raft.FSM) *nodeFixture {
	t.Helper()
	id := raft.ServerID(label)
	addr, trans := raft.NewInmemTransport(raft.ServerAddress(label + "-addr"))
	conf := testConfig(id)
	store := raft.NewInmemStore()
	snaps := raft.NewInmemSnapshotStore()
	if err := raft.BootstrapCluster(conf, store, store, snaps, trans, oneVoter(id, addr)); err != nil {
		t.Fatalf("bootstrap: %v", err)
	}
	r, err := raft.NewRaft(conf, fsm, store, store, snaps, trans)
	if err != nil {
		t.Fatalf("new raft: %v", err)
	}
	n := &nodeFixture{r: r, fsm: fsm, store: store, snaps: snaps, trans: trans, id: id, addr: addr}
	t.Cleanup(func() {
		_ = n.r.Shutdown().Error()
		_ = n.trans.Close()
	})
	waitForState(t, r, raft.Leader)
	return n
}

func newFollower(t *testing.T, label string) *nodeFixture {
	t.Helper()
	id := raft.ServerID(label)
	addr, trans := raft.NewInmemTransport(raft.ServerAddress(label + "-addr"))
	store := raft.NewInmemStore()
	snaps := raft.NewInmemSnapshotStore()
	fsm := &raft.MockFSM{}
	r, err := raft.NewRaft(testConfig(id), fsm, store, store, snaps, trans)
	if err != nil {
		t.Fatalf("new raft: %v", err)
	}
	n := &nodeFixture{r: r, fsm: fsm, store: store, snaps: snaps, trans: trans, id: id, addr: addr}
	t.Cleanup(func() {
		_ = n.r.Shutdown().Error()
		_ = n.trans.Close()
	})
	return n
}

type blockingFSM struct {
	inner       raft.MockFSM
	entered     chan struct{}
	release     chan struct{}
	once        sync.Once
	releaseOnce sync.Once
}

func newBlockingFSM() *blockingFSM {
	return &blockingFSM{entered: make(chan struct{}), release: make(chan struct{})}
}

func (f *blockingFSM) Apply(log *raft.Log) interface{} {
	f.once.Do(func() { close(f.entered) })
	<-f.release
	return f.inner.Apply(log)
}

func (f *blockingFSM) Snapshot() (raft.FSMSnapshot, error) { return f.inner.Snapshot() }
func (f *blockingFSM) Restore(reader io.ReadCloser) error  { return f.inner.Restore(reader) }
func (f *blockingFSM) unblock()                            { f.releaseOnce.Do(func() { close(f.release) }) }

type blockingBatchFSM struct{ blockingFSM }

func newBlockingBatchFSM() *blockingBatchFSM {
	return &blockingBatchFSM{blockingFSM: *newBlockingFSM()}
}

func (f *blockingBatchFSM) Apply(log *raft.Log) interface{} {
	return f.inner.Apply(log)
}

func (f *blockingBatchFSM) ApplyBatch(logs []*raft.Log) []interface{} {
	f.once.Do(func() { close(f.entered) })
	<-f.release
	responses := make([]interface{}, len(logs))
	for i, log := range logs {
		if log.Type == raft.LogCommand {
			responses[i] = f.inner.Apply(log)
		}
	}
	return responses
}

type blockingSnapshotFSM struct {
	inner       raft.MockFSM
	entered     chan struct{}
	release     chan struct{}
	once        sync.Once
	releaseOnce sync.Once
}

func newBlockingSnapshotFSM() *blockingSnapshotFSM {
	return &blockingSnapshotFSM{entered: make(chan struct{}), release: make(chan struct{})}
}

func (f *blockingSnapshotFSM) Apply(log *raft.Log) interface{} { return f.inner.Apply(log) }
func (f *blockingSnapshotFSM) Restore(reader io.ReadCloser) error {
	return f.inner.Restore(reader)
}
func (f *blockingSnapshotFSM) Snapshot() (raft.FSMSnapshot, error) {
	f.once.Do(func() { close(f.entered) })
	<-f.release
	return f.inner.Snapshot()
}
func (f *blockingSnapshotFSM) unblock() { f.releaseOnce.Do(func() { close(f.release) }) }

type blockingConfigurationFSM struct {
	inner       raft.MockFSM
	entered     chan struct{}
	release     chan struct{}
	armed       bool
	mu          sync.Mutex
	once        sync.Once
	releaseOnce sync.Once
}

func newBlockingConfigurationFSM() *blockingConfigurationFSM {
	return &blockingConfigurationFSM{entered: make(chan struct{}), release: make(chan struct{})}
}

func (f *blockingConfigurationFSM) Apply(log *raft.Log) interface{} { return f.inner.Apply(log) }
func (f *blockingConfigurationFSM) Snapshot() (raft.FSMSnapshot, error) {
	return f.inner.Snapshot()
}
func (f *blockingConfigurationFSM) Restore(reader io.ReadCloser) error {
	return f.inner.Restore(reader)
}
func (f *blockingConfigurationFSM) StoreConfiguration(_ uint64, _ raft.Configuration) {
	f.mu.Lock()
	armed := f.armed
	f.mu.Unlock()
	if !armed {
		return
	}
	f.once.Do(func() { close(f.entered) })
	<-f.release
}
func (f *blockingConfigurationFSM) arm() {
	f.mu.Lock()
	f.armed = true
	f.mu.Unlock()
}
func (f *blockingConfigurationFSM) unblock() {
	f.releaseOnce.Do(func() { close(f.release) })
}

func requireNoCompletion(t *testing.T, done <-chan error) {
	t.Helper()
	select {
	case err := <-done:
		t.Fatalf("future completed before FSM fence: %v", err)
	case <-time.After(40 * time.Millisecond):
	}
}

type clusterFixture struct {
	nodes []*nodeFixture
}

func newCluster(t *testing.T, label string, suffrages ...raft.ServerSuffrage) *clusterFixture {
	t.Helper()
	nodes := make([]*nodeFixture, len(suffrages))
	servers := make([]raft.Server, len(suffrages))
	for i, suffrage := range suffrages {
		suffix := string(rune('a' + i))
		id := raft.ServerID(label + "-n" + suffix)
		addr, trans := raft.NewInmemTransport(raft.ServerAddress(label + "-a" + suffix))
		nodes[i] = &nodeFixture{id: id, addr: addr, trans: trans, store: raft.NewInmemStore(), snaps: raft.NewInmemSnapshotStore(), fsm: &raft.MockFSM{}}
		servers[i] = raft.Server{Suffrage: suffrage, ID: id, Address: addr}
	}
	configuration := raft.Configuration{Servers: servers}
	for _, node := range nodes {
		conf := testConfig(node.id)
		if err := raft.BootstrapCluster(conf, node.store, node.store, node.snaps, node.trans, configuration); err != nil {
			t.Fatalf("bootstrap %s: %v", node.id, err)
		}
	}
	for _, left := range nodes {
		for _, right := range nodes {
			if left != right {
				left.trans.Connect(right.addr, right.trans)
			}
		}
	}
	for _, node := range nodes {
		r, err := raft.NewRaft(testConfig(node.id), node.fsm, node.store, node.store, node.snaps, node.trans)
		if err != nil {
			t.Fatalf("new raft %s: %v", node.id, err)
		}
		node.r = r
	}
	t.Cleanup(func() {
		for _, node := range nodes {
			_ = node.r.Shutdown().Error()
			_ = node.trans.Close()
		}
	})
	c := &clusterFixture{nodes: nodes}
	_ = c.leader(t)
	return c
}

func (c *clusterFixture) leader(t *testing.T) *nodeFixture {
	t.Helper()
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		var leader *nodeFixture
		for _, node := range c.nodes {
			if node.r.State() == raft.Leader {
				if leader != nil {
					leader = nil
					break
				}
				leader = node
			}
		}
		if leader != nil {
			return leader
		}
		time.Sleep(10 * time.Millisecond)
	}
	t.Fatal("cluster did not elect one leader")
	return nil
}

func disconnect(a, b *nodeFixture) {
	a.trans.Disconnect(b.addr)
	b.trans.Disconnect(a.addr)
}

func readError(t *testing.T, future raft.ReadIndexFuture) error {
	t.Helper()
	done := make(chan error, 1)
	go func() { done <- future.Error() }()
	select {
	case err := <-done:
		return err
	case <-time.After(4 * time.Second):
		t.Fatal("read future did not settle")
		return nil
	}
}

func TestRaftV3A01SingleVoterRead(t *testing.T) {
	n := newSingle(t, "a01", &raft.MockFSM{})
	future := n.r.ReadIndex(time.Second)
	if err := future.Error(); err != nil {
		t.Fatal(err)
	}
	if future.Index() == 0 || future.Index() > n.r.CommitIndex() {
		t.Fatalf("index=%d commit=%d", future.Index(), n.r.CommitIndex())
	}
}

func TestRaftV3A02ReadDoesNotAppend(t *testing.T) {
	n := newSingle(t, "a02", &raft.MockFSM{})
	before := n.r.LastIndex()
	if err := n.r.ReadIndex(time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	if after := n.r.LastIndex(); after != before {
		t.Fatalf("read appended a log: before=%d after=%d", before, after)
	}
}

func TestRaftV3A03IncludesCommittedCommand(t *testing.T) {
	fsm := &raft.MockFSM{}
	n := newSingle(t, "a03", fsm)
	apply := n.r.Apply([]byte("before-read"), time.Second)
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	read := n.r.ReadIndex(time.Second)
	if err := read.Error(); err != nil {
		t.Fatal(err)
	}
	if read.Index() < apply.Index() {
		t.Fatalf("read index %d below applied command %d", read.Index(), apply.Index())
	}
	logs := fsm.Logs()
	if len(logs) != 1 || string(logs[0]) != "before-read" {
		t.Fatalf("FSM logs=%q", logs)
	}
}

func TestRaftV3A04FollowerRejected(t *testing.T) {
	n := newFollower(t, "a04")
	if err := n.r.ReadIndex(time.Second).Error(); !errors.Is(err, raft.ErrNotLeader) {
		t.Fatalf("error=%v", err)
	}
}

func TestRaftV3A05ShutdownRejected(t *testing.T) {
	n := newFollower(t, "a05")
	if err := n.r.Shutdown().Error(); err != nil {
		t.Fatal(err)
	}
	if err := n.r.ReadIndex(time.Second).Error(); !errors.Is(err, raft.ErrRaftShutdown) {
		t.Fatalf("error=%v", err)
	}
}

func TestRaftV3A06RepeatedReadsStayReadOnly(t *testing.T) {
	n := newSingle(t, "a06", &raft.MockFSM{})
	before := n.r.LastIndex()
	var prior uint64
	for i := 0; i < 4; i++ {
		future := n.r.ReadIndex(time.Second)
		if err := future.Error(); err != nil {
			t.Fatal(err)
		}
		if future.Index() < prior {
			t.Fatalf("index regressed: %d then %d", prior, future.Index())
		}
		prior = future.Index()
	}
	if after := n.r.LastIndex(); after != before {
		t.Fatalf("repeated reads appended logs: before=%d after=%d", before, after)
	}
}

func TestRaftV3A07NativeVerifyLeader(t *testing.T) {
	n := newSingle(t, "a07", &raft.MockFSM{})
	before := n.r.LastIndex()
	if err := n.r.VerifyLeader().Error(); err != nil {
		t.Fatal(err)
	}
	if n.r.LastIndex() != before {
		t.Fatalf("VerifyLeader changed log: %d -> %d", before, n.r.LastIndex())
	}
}

func TestRaftV3A08ReadDoesNotTriggerSnapshot(t *testing.T) {
	n := newSingle(t, "a08", &raft.MockFSM{})
	if err := n.r.Apply([]byte("snapshot-control"), time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	before, err := n.snaps.List()
	if err != nil {
		t.Fatal(err)
	}
	if err := n.r.ReadIndex(time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	var after []*raft.SnapshotMeta
	deadline := time.Now().Add(200 * time.Millisecond)
	for {
		after, err = n.snaps.List()
		if err != nil {
			t.Fatal(err)
		}
		if len(after) != len(before) || time.Now().After(deadline) {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}
	if len(after) != len(before) {
		t.Fatalf("read triggered snapshot: %d -> %d", len(before), len(after))
	}
}

func TestRaftV3I01WaitsForFSMConsumption(t *testing.T) {
	fsm := newBlockingFSM()
	defer fsm.unblock()
	n := newSingle(t, "i01", fsm)
	apply := n.r.Apply([]byte("blocked"), time.Second)
	select {
	case <-fsm.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("FSM apply did not start")
	}
	read := n.r.ReadIndex(time.Second)
	done := make(chan error, 1)
	go func() { done <- read.Error() }()
	requireNoCompletion(t, done)
	fsm.unblock()
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	if read.Index() < apply.Index() {
		t.Fatalf("read index %d below apply %d", read.Index(), apply.Index())
	}
}

func TestRaftV3I02ReadDoesNotApplySyntheticCommand(t *testing.T) {
	fsm := &raft.MockFSM{}
	n := newSingle(t, "i02", fsm)
	if err := n.r.Apply([]byte("only-command"), time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	if err := n.r.ReadIndex(time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	logs := fsm.Logs()
	if len(logs) != 1 || string(logs[0]) != "only-command" {
		t.Fatalf("FSM received synthetic work: %q", logs)
	}
}

func TestRaftV3I03ReadAfterBarrierAddsNoSecondEntry(t *testing.T) {
	n := newSingle(t, "i03", &raft.MockFSM{})
	if err := n.r.Barrier(time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	before := n.r.LastIndex()
	if err := n.r.ReadIndex(time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	if after := n.r.LastIndex(); after != before {
		t.Fatalf("read added an entry after barrier: %d -> %d", before, after)
	}
}

func TestRaftV3I04SnapshotThenRead(t *testing.T) {
	n := newSingle(t, "i04", &raft.MockFSM{})
	apply := n.r.Apply([]byte("snapshotted"), time.Second)
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	if err := n.r.Snapshot().Error(); err != nil {
		t.Fatal(err)
	}
	read := n.r.ReadIndex(time.Second)
	if err := read.Error(); err != nil {
		t.Fatal(err)
	}
	if read.Index() < apply.Index() {
		t.Fatalf("read index %d below snapshot command %d", read.Index(), apply.Index())
	}
}

func TestRaftV3I05ConcurrentReadsShareNoLogEntry(t *testing.T) {
	fsm := newBlockingFSM()
	defer fsm.unblock()
	n := newSingle(t, "i05", fsm)
	apply := n.r.Apply([]byte("fan-in"), time.Second)
	select {
	case <-fsm.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("FSM apply did not start")
	}
	before := n.r.LastIndex()
	futures := []raft.ReadIndexFuture{
		n.r.ReadIndex(time.Second),
		n.r.ReadIndex(time.Second),
		n.r.ReadIndex(time.Second),
	}
	done := make(chan error, len(futures))
	for _, future := range futures {
		go func(f raft.ReadIndexFuture) { done <- f.Error() }(future)
	}
	requireNoCompletion(t, done)
	fsm.unblock()
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	for range futures {
		if err := <-done; err != nil {
			t.Fatal(err)
		}
	}
	if after := n.r.LastIndex(); after != before {
		t.Fatalf("concurrent reads appended logs: %d -> %d", before, after)
	}
}

func TestRaftV3I06FailedReadDoesNotAppend(t *testing.T) {
	n := newFollower(t, "i06")
	before := n.r.LastIndex()
	if err := n.r.ReadIndex(time.Second).Error(); !errors.Is(err, raft.ErrNotLeader) {
		t.Fatalf("error=%v", err)
	}
	if after := n.r.LastIndex(); after != before {
		t.Fatalf("failed read changed log: %d -> %d", before, after)
	}
}

func TestRaftV3I07WaitsForBatchConsumption(t *testing.T) {
	fsm := newBlockingBatchFSM()
	defer fsm.unblock()
	n := newSingle(t, "i07", fsm)
	apply := n.r.Apply([]byte("batched"), time.Second)
	select {
	case <-fsm.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("FSM batch did not start")
	}
	read := n.r.ReadIndex(time.Second)
	done := make(chan error, 1)
	go func() { done <- read.Error() }()
	requireNoCompletion(t, done)
	fsm.unblock()
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatal(err)
	}
}

func TestRaftV3I08WaitsForSnapshotCapture(t *testing.T) {
	fsm := newBlockingSnapshotFSM()
	defer fsm.unblock()
	n := newSingle(t, "i08", fsm)
	if err := n.r.Apply([]byte("before-snapshot"), time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	snapshot := n.r.Snapshot()
	snapshotDone := make(chan error, 1)
	go func() { snapshotDone <- snapshot.Error() }()
	select {
	case <-fsm.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("FSM snapshot did not start")
	}
	read := n.r.ReadIndex(time.Second)
	readDone := make(chan error, 1)
	go func() { readDone <- read.Error() }()
	requireNoCompletion(t, readDone)
	fsm.unblock()
	if err := <-snapshotDone; err != nil {
		t.Fatal(err)
	}
	if err := <-readDone; err != nil {
		t.Fatal(err)
	}
}

func TestRaftV3I09WaitsForConfigurationConsumption(t *testing.T) {
	fsm := newBlockingConfigurationFSM()
	defer fsm.unblock()
	n := newSingle(t, "i09", fsm)
	fsm.arm()
	change := n.r.AddNonvoter("i09-observer", "i09-observer-addr", 0, time.Second)
	select {
	case <-fsm.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("FSM configuration store did not start")
	}
	read := n.r.ReadIndex(time.Second)
	done := make(chan error, 1)
	go func() { done <- read.Error() }()
	requireNoCompletion(t, done)
	fsm.unblock()
	if err := change.Error(); err != nil {
		t.Fatal(err)
	}
	if err := <-done; err != nil {
		t.Fatal(err)
	}
}

func TestRaftV3I10HealthyVotingQuorum(t *testing.T) {
	c := newCluster(t, "i10", raft.Voter, raft.Voter, raft.Voter)
	leader := c.leader(t)
	before := leader.r.LastIndex()
	read := leader.r.ReadIndex(time.Second)
	if err := readError(t, read); err != nil {
		t.Fatal(err)
	}
	if read.Index() == 0 || leader.r.LastIndex() != before {
		t.Fatalf("index=%d log=%d->%d", read.Index(), before, leader.r.LastIndex())
	}
}

func TestRaftV3I11OneUnavailableVoterStillFormsQuorum(t *testing.T) {
	c := newCluster(t, "i11", raft.Voter, raft.Voter, raft.Voter)
	leader := c.leader(t)
	for _, node := range c.nodes {
		if node != leader {
			disconnect(leader, node)
			break
		}
	}
	before := leader.r.LastIndex()
	if err := readError(t, leader.r.ReadIndex(time.Second)); err != nil {
		t.Fatal(err)
	}
	if leader.r.LastIndex() != before {
		t.Fatalf("read appended a log: %d -> %d", before, leader.r.LastIndex())
	}
}

func TestRaftV3I12IsolatedLeaderCannotConfirm(t *testing.T) {
	c := newCluster(t, "i12", raft.Voter, raft.Voter, raft.Voter)
	leader := c.leader(t)
	for _, node := range c.nodes {
		if node != leader {
			disconnect(leader, node)
		}
	}
	before := leader.r.LastIndex()
	err := readError(t, leader.r.ReadIndex(time.Second))
	if !errors.Is(err, raft.ErrLeadershipLost) && !errors.Is(err, raft.ErrNotLeader) {
		t.Fatalf("error=%v", err)
	}
	if leader.r.LastIndex() != before {
		t.Fatalf("failed read appended a log: %d -> %d", before, leader.r.LastIndex())
	}
}

func TestRaftV3I13NonvoterDoesNotReplaceVoter(t *testing.T) {
	c := newCluster(t, "i13", raft.Voter, raft.Voter, raft.Nonvoter)
	leader := c.leader(t)
	var otherVoter *nodeFixture
	for i, node := range c.nodes {
		if node != leader && i < 2 {
			otherVoter = node
		}
	}
	if otherVoter == nil {
		t.Fatal("missing second voter")
	}
	disconnect(leader, otherVoter)
	err := readError(t, leader.r.ReadIndex(time.Second))
	if !errors.Is(err, raft.ErrLeadershipLost) && !errors.Is(err, raft.ErrNotLeader) {
		t.Fatalf("nonvoter substituted for voter: %v", err)
	}
}

func TestRaftV3I14NativeBarrierOrdersFSM(t *testing.T) {
	fsm := &raft.MockFSM{}
	n := newSingle(t, "i14", fsm)
	if err := n.r.Apply([]byte("native-barrier"), time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	if err := n.r.Barrier(time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	logs := fsm.Logs()
	if len(logs) != 1 || string(logs[0]) != "native-barrier" {
		t.Fatalf("FSM logs=%q", logs)
	}
}

func TestRaftV3I15SnapshotCommandAndReadShareOrder(t *testing.T) {
	fsm := newBlockingSnapshotFSM()
	defer fsm.unblock()
	n := newSingle(t, "i15", fsm)
	if err := n.r.Apply([]byte("before-snapshot"), time.Second).Error(); err != nil {
		t.Fatal(err)
	}
	snapshot := n.r.Snapshot()
	snapshotDone := make(chan error, 1)
	go func() { snapshotDone <- snapshot.Error() }()
	select {
	case <-fsm.entered:
	case <-time.After(3 * time.Second):
		t.Fatal("FSM snapshot did not start")
	}
	priorLast := n.r.LastIndex()
	apply := n.r.Apply([]byte("behind-snapshot"), time.Second)
	deadline := time.Now().Add(3 * time.Second)
	for n.r.LastIndex() == priorLast && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	for n.r.CommitIndex() < n.r.LastIndex() && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	beforeRead := n.r.LastIndex()
	read := n.r.ReadIndex(time.Second)
	readDone := make(chan error, 1)
	go func() { readDone <- read.Error() }()
	requireNoCompletion(t, readDone)
	fsm.unblock()
	if err := <-snapshotDone; err != nil {
		t.Fatal(err)
	}
	if err := apply.Error(); err != nil {
		t.Fatal(err)
	}
	if err := <-readDone; err != nil {
		t.Fatal(err)
	}
	if read.Index() < apply.Index() {
		t.Fatalf("read index %d below command %d", read.Index(), apply.Index())
	}
	if n.r.LastIndex() != beforeRead {
		t.Fatalf("read appended a log: %d -> %d", beforeRead, n.r.LastIndex())
	}
}
