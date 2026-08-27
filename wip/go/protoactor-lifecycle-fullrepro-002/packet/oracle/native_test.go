package passivationoracle_test

import (
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/asynkron/protoactor-go/actor"
	"github.com/asynkron/protoactor-go/eventstream"
	"github.com/asynkron/protoactor-go/persistence"
	"github.com/asynkron/protoactor-go/plugin"
	"github.com/asynkron/protoactor-go/router"
	"google.golang.org/protobuf/proto"
)

const testDeadline = 5 * time.Second

func awaitValue[T any](t *testing.T, ch <-chan T) T {
	t.Helper()
	select {
	case value := <-ch:
		return value
	case <-time.After(testDeadline):
		t.Fatal("timed out waiting for an explicitly signalled observation")
		var zero T
		return zero
	}
}

func stopAndWait(t *testing.T, system *actor.ActorSystem, pid *actor.PID) {
	t.Helper()
	if pid == nil {
		return
	}
	if err := system.Root.StopFuture(pid).Wait(); err != nil {
		t.Fatalf("stop actor: %v", err)
	}
}

func TestPA2NativePIDIdentity(t *testing.T) {
	a := actor.NewPID("local", "worker")
	b := actor.NewPID("local", "worker")
	c := actor.NewPID("remote", "worker")
	if !a.Equal(b) || a.Equal(c) || a.String() != b.String() {
		t.Fatalf("PID identity mismatch: a=%v b=%v c=%v", a, b, c)
	}
}

func TestPA2NativePIDSetOwnership(t *testing.T) {
	a := actor.NewPID("local", "a")
	b := actor.NewPID("local", "b")
	set := actor.NewPIDSet(a)
	clone := set.Clone()
	clone.Add(b)
	if set.Len() != 1 || clone.Len() != 2 || !set.Contains(a) || set.Contains(b) {
		t.Fatalf("PIDSet membership leaked between owner and clone")
	}
}

func TestPA2NativeEnvelopeRoundTrip(t *testing.T) {
	sender := actor.NewPID("local", "sender")
	envelope := &actor.MessageEnvelope{Message: 42, Sender: sender}
	envelope.SetHeader("trace", "native")
	header, message, unwrappedSender := actor.UnwrapEnvelope(envelope)
	if message != 42 || !sender.Equal(unwrappedSender) || header.Get("trace") != "native" {
		t.Fatalf("envelope did not preserve public fields")
	}
}

func TestPA2NativeEventPredicate(t *testing.T) {
	stream := eventstream.NewEventStream()
	accepted := make(chan int, 1)
	sub := stream.SubscribeWithPredicate(func(event interface{}) { accepted <- event.(int) }, func(event interface{}) bool {
		value, ok := event.(int)
		return ok && value%2 == 0
	})
	stream.Publish(3)
	stream.Publish(4)
	if got := awaitValue(t, accepted); got != 4 {
		t.Fatalf("predicate accepted %d", got)
	}
	stream.Unsubscribe(sub)
}

func TestPA2NativeBehaviorStack(t *testing.T) {
	var behavior actor.Behavior
	seen := make(chan string, 2)
	base := func(actor.Context) { seen <- "base" }
	stacked := func(actor.Context) { seen <- "stacked" }
	behavior.Become(base)
	behavior.BecomeStacked(stacked)
	behavior.Receive(nil)
	behavior.UnbecomeStacked()
	behavior.Receive(nil)
	if first, second := awaitValue(t, seen), awaitValue(t, seen); first != "stacked" || second != "base" {
		t.Fatalf("behavior stack order = %q, %q", first, second)
	}
}

func TestPA2NativeFutureTimeout(t *testing.T) {
	system := actor.NewActorSystem()
	future := actor.NewFuture(system, 20*time.Millisecond)
	if err := future.Wait(); !errors.Is(err, actor.ErrTimeout) {
		t.Fatalf("future error = %v, want ErrTimeout", err)
	}
}

func TestPA2NativePassivationHolderCancel(t *testing.T) {
	system := actor.NewActorSystem()
	holder := &plugin.PassivationHolder{}
	holder.Init(system, actor.NewPID(system.Address(), "not-registered"), 20*time.Millisecond)
	holder.Cancel()
	// Cancellation itself is synchronous; repeated cancellation and reset after
	// cancellation exercise the holder's ordinary public lifecycle.
	holder.Cancel()
	holder.Reset(time.Second)
	holder.Cancel()
}

func TestPA2NativeSpawnNamedRegistry(t *testing.T) {
	system := actor.NewActorSystem()
	started := make(chan struct{}, 1)
	props := actor.PropsFromFunc(func(ctx actor.Context) {
		if _, ok := ctx.Message().(*actor.Started); ok {
			started <- struct{}{}
		}
	})
	pid, err := system.Root.SpawnNamed(props, "native-spawn")
	if err != nil {
		t.Fatal(err)
	}
	defer stopAndWait(t, system, pid)
	awaitValue(t, started)
	process, ok := system.ProcessRegistry.Get(pid)
	if !ok || process == nil {
		t.Fatal("named actor is absent from process registry")
	}
	if _, err := system.Root.SpawnNamed(props, "native-spawn"); err == nil {
		t.Fatal("duplicate live name unexpectedly replaced the actor")
	}
}

func TestPA2NativeRequestResponse(t *testing.T) {
	system := actor.NewActorSystem()
	pid := system.Root.Spawn(actor.PropsFromFunc(func(ctx actor.Context) {
		if value, ok := ctx.Message().(string); ok {
			ctx.Respond("reply:" + value)
		}
	}))
	defer stopAndWait(t, system, pid)
	value, err := system.Root.RequestFuture(pid, "hello", testDeadline).Result()
	if err != nil || value != "reply:hello" {
		t.Fatalf("request result = %#v, %v", value, err)
	}
}

func TestPA2NativeDeadLetterEvent(t *testing.T) {
	system := actor.NewActorSystem()
	seen := make(chan *actor.DeadLetterEvent, 1)
	sub := system.EventStream.SubscribeWithPredicate(func(event interface{}) {
		seen <- event.(*actor.DeadLetterEvent)
	}, func(event interface{}) bool {
		_, ok := event.(*actor.DeadLetterEvent)
		return ok
	})
	defer system.EventStream.Unsubscribe(sub)
	target := actor.NewPID(system.Address(), "stale-native-target")
	system.Root.Send(target, "payload")
	event := awaitValue(t, seen)
	if event.Message != "payload" || !event.PID.Equal(target) {
		t.Fatalf("dead letter lost target or payload: %#v", event)
	}
}

func TestPA2NativeLiveGroupRouting(t *testing.T) {
	system := actor.NewActorSystem()
	routee := system.Root.Spawn(actor.PropsFromFunc(func(ctx actor.Context) {
		if message, ok := ctx.Message().(string); ok {
			ctx.Respond("routee:" + message)
		}
	}))
	defer stopAndWait(t, system, routee)
	group := system.Root.Spawn(router.NewRoundRobinGroup(routee))
	defer stopAndWait(t, system, group)
	viewValue, err := system.Root.RequestFuture(group, &router.GetRoutees{}, testDeadline).Result()
	if err != nil {
		t.Fatal(err)
	}
	view := viewValue.(*router.Routees)
	if len(view.PIDs) != 1 || !view.PIDs[0].Equal(routee) {
		t.Fatalf("group view = %#v", view.PIDs)
	}
	value, err := system.Root.RequestFuture(group, "ping", testDeadline).Result()
	if err != nil || value != "routee:ping" {
		t.Fatalf("routed result = %#v, %v", value, err)
	}
}

type persistValue struct {
	proto.Message
	value string
}

type persistSnapshot struct {
	proto.Message
	value string
}

type persistentProbe struct {
	persistence.Mixin
	value string
}

type inMemoryPersistence struct {
	*persistence.InMemoryProvider
}

func (provider *inMemoryPersistence) GetState() persistence.ProviderState {
	return provider.InMemoryProvider
}

func (probe *persistentProbe) Receive(ctx actor.Context) {
	switch message := ctx.Message().(type) {
	case *persistSnapshot:
		probe.value = message.value
	case *persistValue:
		probe.value += message.value
		if !probe.Recovering() {
			probe.PersistReceive(message)
		}
	case string:
		if message == "query" {
			ctx.Respond(probe.value)
		}
	}
}

func TestPA2NativeBasicPersistenceRecovery(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(100)}
	provider.PersistEvent("native-persistent", 0, &persistValue{value: "represented"})
	provider.PersistEvent("native-persistent", 1, &persistValue{value: "+tail"})
	provider.PersistSnapshot("native-persistent", 1, &persistSnapshot{value: "base"})
	props := actor.PropsFromProducer(func() actor.Actor { return &persistentProbe{} },
		actor.WithReceiverMiddleware(persistence.Using(provider)))
	pid, err := system.Root.SpawnNamed(props, "native-persistent")
	if err != nil {
		t.Fatal(err)
	}
	defer stopAndWait(t, system, pid)
	value, err := system.Root.RequestFuture(pid, "query", testDeadline).Result()
	if err != nil || value != "base+tail" {
		t.Fatalf("snapshot and tail recovery = %#v, %v", value, err)
	}
}

func TestPA2NativeActorLifecycle(t *testing.T) {
	system := actor.NewActorSystem()
	started := make(chan struct{}, 1)
	stopped := make(chan struct{}, 1)
	pid := system.Root.Spawn(actor.PropsFromFunc(func(ctx actor.Context) {
		switch ctx.Message().(type) {
		case *actor.Started:
			started <- struct{}{}
		case string:
			ctx.Respond("live")
		case *actor.Stopped:
			stopped <- struct{}{}
		}
	}))
	awaitValue(t, started)
	value, err := system.Root.RequestFuture(pid, "probe", testDeadline).Result()
	if err != nil || value != "live" {
		t.Fatalf("lifecycle request = %#v, %v", value, err)
	}
	stopAndWait(t, system, pid)
	awaitValue(t, stopped)
}

func TestPA2NativePersistentRouterLifecycle(t *testing.T) {
	system := actor.NewActorSystem()
	var mu sync.Mutex
	count := 0
	routee := system.Root.Spawn(actor.PropsFromFunc(func(ctx actor.Context) {
		if _, ok := ctx.Message().(string); ok {
			mu.Lock()
			count++
			current := count
			mu.Unlock()
			ctx.Respond(current)
		}
	}))
	defer stopAndWait(t, system, routee)
	group := system.Root.Spawn(router.NewRoundRobinGroup(routee))
	defer stopAndWait(t, system, group)
	for want := 1; want <= 2; want++ {
		value, err := system.Root.RequestFuture(group, "increment", testDeadline).Result()
		if err != nil || value != want {
			t.Fatalf("router lifecycle step %d = %#v, %v", want, value, err)
		}
	}
}
