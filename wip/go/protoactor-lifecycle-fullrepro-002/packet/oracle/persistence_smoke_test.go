package passivationoracle_test

import (
	"sync/atomic"
	"testing"
	"time"

	"github.com/asynkron/protoactor-go/actor"
	"github.com/asynkron/protoactor-go/persistence"
	"github.com/asynkron/protoactor-go/plugin"
	"github.com/asynkron/protoactor-go/router"
	"google.golang.org/protobuf/proto"
)

type persistedAppend struct {
	proto.Message
	value string
}

type persistedSnapshot struct {
	proto.Message
	value string
}

type recoveryBarrier struct {
	proto.Message
	value   string
	entered chan<- struct{}
	release <-chan struct{}
}

type persistentCrash struct{}

type persistentBlock struct {
	entered chan<- struct{}
	release <-chan struct{}
}

type persistenceObserver struct {
	generation atomic.Int32
	recovered  chan int
}

type passivatingPersistentActor struct {
	persistence.Mixin
	plugin.PassivationHolder
	observer   *persistenceObserver
	generation int
	value      string
}

func (probe *passivatingPersistentActor) Receive(ctx actor.Context) {
	switch message := ctx.Message().(type) {
	case *persistedSnapshot:
		probe.value = message.value
	case *persistedAppend:
		probe.value += message.value
		if !probe.Recovering() {
			probe.PersistReceive(message)
			ctx.Respond(probe.value)
		}
	case *recoveryBarrier:
		message.entered <- struct{}{}
		<-message.release
		probe.value += message.value
	case *persistence.RequestSnapshot:
		probe.PersistSnapshot(&persistedSnapshot{value: probe.value})
	case *persistence.ReplayComplete:
		probe.observer.recovered <- probe.generation
	case *persistentCrash:
		panic("persistent restart")
	case *persistentBlock:
		message.entered <- struct{}{}
		<-message.release
	case string:
		if message == "query" {
			ctx.Respond(probe.value)
		}
	}
}

func newPersistenceObserver() *persistenceObserver {
	return &persistenceObserver{recovered: make(chan int, 16)}
}

func persistentProps(provider persistence.Provider, observer *persistenceObserver, idle time.Duration) *actor.Props {
	return actor.PropsFromProducer(func() actor.Actor {
		generation := int(observer.generation.Add(1))
		return &passivatingPersistentActor{observer: observer, generation: generation}
	}, actor.WithReceiverMiddleware(
		plugin.Use(&plugin.PassivationPlugin{Duration: idle}),
		persistence.Using(provider),
	))
}

func spawnPersistentNamed(t *testing.T, system *actor.ActorSystem, props *actor.Props, name string) *actor.PID {
	t.Helper()
	pid, err := system.Root.SpawnNamed(props, name)
	if err != nil {
		t.Fatalf("spawn persistent actor %q: %v", name, err)
	}
	return pid
}

func TestPA2AtomicPersistentReplayPrecedesIdleClock(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(100)}
	entered := make(chan struct{})
	release := make(chan struct{})
	provider.PersistEvent("slow-replay", 0, &recoveryBarrier{value: "replayed", entered: entered, release: release})
	observer := newPersistenceObserver()
	props := persistentProps(provider, observer, smokeIdle)
	pid := spawnPersistentNamed(t, system, props, "slow-replay")
	defer stopAndWait(t, system, pid)

	awaitValue(t, entered)
	select {
	case generation := <-observer.recovered:
		t.Fatalf("replay completed before blocked event in generation %d", generation)
	default:
	}
	passIdleWindow()
	query := system.Root.RequestFuture(pid, "query", 2*time.Second)
	close(release)
	if generation := awaitValue(t, observer.recovered); generation != 1 {
		t.Fatalf("recovered generation = %d", generation)
	}
	value, err := query.Result()
	if err != nil || value != "replayed" {
		t.Fatalf("query after slow replay = %#v, %v", value, err)
	}
}

func TestPA2IntegrationSnapshotTailReplaysExactlyOnce(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(2)}
	observer := newPersistenceObserver()
	props := persistentProps(provider, observer, 3*time.Second)
	pid := spawnPersistentNamed(t, system, props, "snapshot-tail")
	if generation := awaitValue(t, observer.recovered); generation != 1 {
		t.Fatalf("initial generation = %d", generation)
	}
	for index, value := range []string{"A", "B", "C"} {
		result, err := system.Root.RequestFuture(pid, &persistedAppend{value: value}, testDeadline).Result()
		if err != nil || result != "ABC"[:index+1] {
			t.Fatalf("append %s result = %#v, %v", value, result, err)
		}
	}
	if err := system.Root.PoisonFuture(pid).Wait(); err != nil {
		t.Fatal(err)
	}

	pid = spawnPersistentNamed(t, system, props, "snapshot-tail")
	defer stopAndWait(t, system, pid)
	if generation := awaitValue(t, observer.recovered); generation != 2 {
		t.Fatalf("reactivated generation = %d", generation)
	}
	result, err := system.Root.RequestFuture(pid, "query", testDeadline).Result()
	if err != nil || result != "ABC" {
		t.Fatalf("snapshot-tail replay = %#v, %v", result, err)
	}
}

func TestPA2SystemFailurePersistenceReactivationChain(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(100)}
	observer := newPersistenceObserver()
	props := persistentProps(provider, observer, smokeIdle)
	pid := spawnPersistentNamed(t, system, props, "failure-persistent")
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.recovered)
	if value, err := system.Root.RequestFuture(pid, &persistedAppend{value: "A"}, testDeadline).Result(); err != nil || value != "A" {
		t.Fatalf("initial persist = %#v, %v", value, err)
	}
	system.Root.Send(pid, &persistentCrash{})
	if generation := awaitValue(t, observer.recovered); generation != 2 {
		t.Fatalf("replacement generation = %d", generation)
	}

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &persistentBlock{entered: entered, release: release})
	awaitValue(t, entered)
	passIdleWindow()
	appendFuture := system.Root.RequestFuture(pid, &persistedAppend{value: "B"}, 2*time.Second)
	close(release)
	if value, err := appendFuture.Result(); err != nil || value != "AB" {
		t.Fatalf("queued persistent append = %#v, %v", value, err)
	}
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)

	pid = spawnPersistentNamed(t, system, props, "failure-persistent")
	if generation := awaitValue(t, observer.recovered); generation != 3 {
		t.Fatalf("reactivated generation = %d", generation)
	}
	value, err := system.Root.RequestFuture(pid, "query", testDeadline).Result()
	if err != nil || value != "AB" {
		t.Fatalf("reactivated persistent value = %#v, %v", value, err)
	}
}

func TestPA2SystemRouterPersistentRouteeReactivationChain(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(100)}
	observer := newPersistenceObserver()
	props := persistentProps(provider, observer, smokeIdle)
	pid := spawnPersistentNamed(t, system, props, "router-persistent")
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.recovered)
	if value, err := system.Root.RequestFuture(pid, &persistedAppend{value: "A"}, testDeadline).Result(); err != nil || value != "A" {
		t.Fatalf("persist routee state = %#v, %v", value, err)
	}
	group := system.Root.Spawn(router.NewRoundRobinGroup(pid))
	defer stopAndWait(t, system, group)
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)
	if view := routeeView(t, system, group); len(view) != 0 {
		t.Fatalf("group retained passivated persistent routee: %v", view)
	}

	pid = spawnPersistentNamed(t, system, props, "router-persistent")
	if generation := awaitValue(t, observer.recovered); generation != 2 {
		t.Fatalf("reactivated generation = %d", generation)
	}
	system.Root.Send(group, &router.AddRoutee{PID: pid})
	if view := routeeView(t, system, group); len(view) != 1 || !view[0].Equal(pid) {
		t.Fatalf("reactivated group view = %v; want %v", view, pid)
	}
	result, err := system.Root.RequestFuture(group, "query", testDeadline).Result()
	if err != nil || result != "A" {
		t.Fatalf("routed reactivated query = %#v, %v", result, err)
	}
}
