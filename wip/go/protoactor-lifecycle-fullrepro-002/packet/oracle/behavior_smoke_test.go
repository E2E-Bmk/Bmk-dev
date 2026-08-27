package passivationoracle_test

import (
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/asynkron/protoactor-go/actor"
	"github.com/asynkron/protoactor-go/plugin"
)

const smokeIdle = 120 * time.Millisecond

type smokeWork struct {
	sequence  int
	entered   chan<- struct{}
	release   <-chan struct{}
	completed chan<- struct{}
	reply     bool
	crash     bool
}

type smokeObserver struct {
	generation atomic.Int32
	started    chan int
	stopping   chan int
	stopped    chan int
	processed  chan int
	startGate  <-chan struct{}
}

type smokeActor struct {
	plugin.PassivationHolder
	observer   *smokeObserver
	generation int
}

func (probe *smokeActor) Receive(ctx actor.Context) {
	switch message := ctx.Message().(type) {
	case *actor.Started:
		probe.observer.started <- probe.generation
		if probe.generation == 1 && probe.observer.startGate != nil {
			<-probe.observer.startGate
		}
	case *smokeWork:
		if message.entered != nil {
			message.entered <- struct{}{}
		}
		if message.release != nil {
			<-message.release
		}
		if message.crash {
			panic("smoke restart")
		}
		probe.observer.processed <- message.sequence
		if message.reply {
			ctx.Respond(fmt.Sprintf("reply-%d", message.sequence))
		}
		if message.completed != nil {
			message.completed <- struct{}{}
		}
	case *actor.Stopping:
		probe.observer.stopping <- probe.generation
	case *actor.Stopped:
		probe.observer.stopped <- probe.generation
	}
}

func newSmokeObserver(startGate <-chan struct{}) *smokeObserver {
	return &smokeObserver{
		started:   make(chan int, 8),
		stopping:  make(chan int, 8),
		stopped:   make(chan int, 8),
		processed: make(chan int, 32),
		startGate: startGate,
	}
}

func spawnSmoke(t *testing.T, system *actor.ActorSystem, observer *smokeObserver) *actor.PID {
	t.Helper()
	props := actor.PropsFromProducer(func() actor.Actor {
		generation := int(observer.generation.Add(1))
		return &smokeActor{observer: observer, generation: generation}
	}, actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	return system.Root.Spawn(props)
}

func passIdleWindow() {
	<-time.After(4 * smokeIdle)
}

type gatedDispatcher struct {
	mu   sync.Mutex
	auto bool
	jobs chan func()
}

func newGatedDispatcher() *gatedDispatcher {
	return &gatedDispatcher{jobs: make(chan func(), 16)}
}

func (dispatcher *gatedDispatcher) Schedule(fn func()) {
	dispatcher.mu.Lock()
	auto := dispatcher.auto
	dispatcher.mu.Unlock()
	if auto {
		go fn()
		return
	}
	dispatcher.jobs <- fn
}

func (*gatedDispatcher) Throughput() int { return 300 }

func (dispatcher *gatedDispatcher) runNext(t *testing.T) {
	t.Helper()
	job := awaitValue(t, dispatcher.jobs)
	job()
}

func (dispatcher *gatedDispatcher) enableAutomatic() {
	dispatcher.mu.Lock()
	dispatcher.auto = true
	dispatcher.mu.Unlock()
	for {
		select {
		case job := <-dispatcher.jobs:
			go job()
		default:
			return
		}
	}
}

func expectReply(t *testing.T, future *actor.Future, want string) {
	t.Helper()
	value, err := future.Result()
	if err != nil || value != want {
		t.Fatalf("future result = %#v, %v; want %q", value, err, want)
	}
}

func TestPA2AtomicIdleBeginsAfterStartedCompletes(t *testing.T) {
	system := actor.NewActorSystem()
	startRelease := make(chan struct{})
	observer := newSmokeObserver(startRelease)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)

	if generation := awaitValue(t, observer.started); generation != 1 {
		t.Fatalf("first generation = %d", generation)
	}
	passIdleWindow()
	future := system.Root.RequestFuture(pid, &smokeWork{sequence: 1, reply: true}, testDeadline)
	close(startRelease)
	expectReply(t, future, "reply-1")
}

func TestPA2IntegrationConsecutiveHandlersRenewAfterCompletion(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)

	expectReply(t, system.Root.RequestFuture(pid, &smokeWork{sequence: 1, reply: true}, testDeadline), "reply-1")
	entered := make(chan struct{})
	release := make(chan struct{})
	completed := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 2, entered: entered, release: release, completed: completed})
	awaitValue(t, entered)
	passIdleWindow()
	future := system.Root.RequestFuture(pid, &smokeWork{sequence: 3, reply: true}, testDeadline)
	close(release)
	awaitValue(t, completed)
	expectReply(t, future, "reply-3")
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)
}

func TestPA2SystemReadyActivityRestartIdleChain(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	if generation := awaitValue(t, observer.started); generation != 1 {
		t.Fatalf("first generation = %d", generation)
	}

	system.Root.Send(pid, &smokeWork{sequence: 1, crash: true})
	if generation := awaitValue(t, observer.started); generation != 2 {
		t.Fatalf("replacement generation = %d", generation)
	}
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 2, entered: entered, release: release})
	awaitValue(t, entered)
	passIdleWindow()
	future := system.Root.RequestFuture(pid, &smokeWork{sequence: 3, reply: true}, testDeadline)
	close(release)
	expectReply(t, future, "reply-3")
}

func TestPA2AtomicPassivationDrainsAdmittedMessage(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	dispatcher := newGatedDispatcher()
	props := actor.PropsFromProducer(func() actor.Actor {
		generation := int(observer.generation.Add(1))
		return &smokeActor{observer: observer, generation: generation}
	}, actor.WithDispatcher(dispatcher),
		actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	pid := system.Root.Spawn(props)
	defer stopAndWait(t, system, pid)
	defer dispatcher.enableAutomatic()
	dispatcher.runNext(t)
	awaitValue(t, observer.started)

	firstDone := make(chan struct{}, 1)
	secondDone := make(chan struct{}, 1)
	system.Root.Send(pid, &smokeWork{sequence: 1, completed: firstDone})
	system.Root.Send(pid, &smokeWork{sequence: 2, completed: secondDone})
	passIdleWindow()
	dispatcher.runNext(t)
	awaitValue(t, firstDone)
	awaitValue(t, secondDone)
}

func TestPA2IntegrationBoundaryPreservesFIFO(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 10, entered: entered, release: release})
	awaitValue(t, entered)
	system.Root.Send(pid, &smokeWork{sequence: 20})
	system.Root.Send(pid, &smokeWork{sequence: 30})
	passIdleWindow()
	close(release)
	got := []int{awaitValue(t, observer.processed), awaitValue(t, observer.processed), awaitValue(t, observer.processed)}
	want := []int{10, 20, 30}
	for index := range want {
		if got[index] != want[index] {
			t.Fatalf("processed order = %v; want %v", got, want)
		}
	}
}

type watchTarget struct {
	target     *actor.PID
	terminated chan<- *actor.Terminated
	ready      chan<- struct{}
}

func (watcher *watchTarget) Receive(ctx actor.Context) {
	switch message := ctx.Message().(type) {
	case *actor.Started:
		ctx.Watch(watcher.target)
		watcher.ready <- struct{}{}
	case *actor.Terminated:
		watcher.terminated <- message
	}
}

func TestPA2SystemDrainFutureWatchDeadLetterChain(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)

	watchReady := make(chan struct{})
	terminated := make(chan *actor.Terminated, 1)
	watcherPID := system.Root.Spawn(actor.PropsFromProducer(func() actor.Actor {
		return &watchTarget{target: pid, terminated: terminated, ready: watchReady}
	}))
	defer stopAndWait(t, system, watcherPID)
	awaitValue(t, watchReady)

	deadLetters := make(chan *actor.DeadLetterEvent, 8)
	subscription := system.EventStream.SubscribeWithPredicate(func(event interface{}) {
		deadLetters <- event.(*actor.DeadLetterEvent)
	}, func(event interface{}) bool {
		eventValue, ok := event.(*actor.DeadLetterEvent)
		return ok && eventValue.PID != nil && eventValue.PID.Equal(pid)
	})
	defer system.EventStream.Unsubscribe(subscription)

	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	admitted := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, testDeadline)
	passIdleWindow()
	close(release)
	expectReply(t, admitted, "reply-2")

	termination := awaitValue(t, terminated)
	if !termination.Who.Equal(pid) {
		t.Fatalf("watcher observed %v; want %v", termination.Who, pid)
	}
	late := system.Root.RequestFuture(pid, &smokeWork{sequence: 3, reply: true}, testDeadline)
	if _, err := late.Result(); !errors.Is(err, actor.ErrDeadLetter) {
		t.Fatalf("late request error = %v; want ErrDeadLetter", err)
	}
	event := awaitValue(t, deadLetters)
	if !event.PID.Equal(pid) {
		t.Fatalf("dead-letter target = %v; want %v", event.PID, pid)
	}
}
