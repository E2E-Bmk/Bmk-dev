package passivationoracle_test

import (
	"testing"
	"time"

	"github.com/asynkron/protoactor-go/actor"
	"github.com/asynkron/protoactor-go/plugin"
	"github.com/asynkron/protoactor-go/router"
)

func TestPA2AtomicRestartCancelsOldIdleTimer(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	system.Root.Send(pid, &smokeWork{sequence: 1, crash: true})
	if generation := awaitValue(t, observer.started); generation != 2 {
		t.Fatalf("replacement generation = %d", generation)
	}

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 2, entered: entered, release: release})
	awaitValue(t, entered)
	passIdleWindow()
	future := system.Root.RequestFuture(pid, &smokeWork{sequence: 4, reply: true}, testDeadline)
	close(release)
	expectReply(t, future, "reply-4")
}

func TestPA2IntegrationRestartTransfersQueuedWork(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release, crash: true})
	awaitValue(t, entered)
	queued := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, testDeadline)
	passIdleWindow()
	close(release)
	if generation := awaitValue(t, observer.started); generation != 2 {
		t.Fatalf("replacement generation = %d", generation)
	}
	expectReply(t, queued, "reply-2")
}

func TestPA2AtomicAdmittedRequestRetainsReply(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	admitted := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	passIdleWindow()
	close(release)
	expectReply(t, admitted, "reply-2")
}

type pipeSink struct {
	values chan<- interface{}
}

func (sink *pipeSink) Receive(ctx actor.Context) {
	switch ctx.Message().(type) {
	case *actor.Started:
	default:
		sink.values <- ctx.Message()
	}
}

func TestPA2IntegrationPipeReceivesTerminalOnce(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)

	pipeValues := make(chan interface{}, 4)
	pipePID := system.Root.Spawn(actor.PropsFromProducer(func() actor.Actor { return &pipeSink{values: pipeValues} }))
	defer stopAndWait(t, system, pipePID)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	admitted := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	admitted.PipeTo(pipePID)
	passIdleWindow()
	close(release)
	expectReply(t, admitted, "reply-2")
	if value := awaitValue(t, pipeValues); value != "reply-2" {
		t.Fatalf("pipe terminal = %#v", value)
	}
	select {
	case duplicate := <-pipeValues:
		t.Fatalf("pipe received duplicate terminal: %#v", duplicate)
	case <-time.After(4 * smokeIdle):
	}
}

func TestPA2SystemRoutedFuturePassivationChain(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pool := system.Root.Spawn(router.NewRoundRobinPool(1,
		actor.WithProducer(func() actor.Actor {
			generation := int(observer.generation.Add(1))
			return &smokeActor{observer: observer, generation: generation}
		}),
		actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle}))))
	defer stopAndWait(t, system, pool)
	awaitValue(t, observer.started)
	view := routeeView(t, system, pool)
	if len(view) != 1 {
		t.Fatalf("initial pool size = %d", len(view))
	}
	first := view[0]

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(first, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	admitted := system.Root.RequestFuture(pool, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	passIdleWindow()
	close(release)
	expectReply(t, admitted, "reply-2")
	replacementStarted := awaitValue(t, observer.started)
	if replacementStarted < 2 {
		t.Fatalf("pool did not create a fresh routee generation: %d", replacementStarted)
	}
}
