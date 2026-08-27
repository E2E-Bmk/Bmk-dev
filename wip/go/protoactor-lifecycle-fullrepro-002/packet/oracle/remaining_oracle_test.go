package passivationoracle_test

import (
	"errors"
	"testing"
	"time"

	"github.com/asynkron/protoactor-go/actor"
	"github.com/asynkron/protoactor-go/persistence"
	"github.com/asynkron/protoactor-go/plugin"
	"github.com/asynkron/protoactor-go/router"
	"github.com/asynkron/protoactor-go/scheduler"
)

func TestPA2AtomicBusyHandlerSuspendsIdleWindow(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	passIdleWindow()
	probe := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	close(release)
	expectReply(t, probe, "reply-2")
}

func TestPA2AtomicLateRequestGetsDeadLetter(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	system.Root.Poison(pid)
	late := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	close(release)
	if _, err := late.Result(); !errors.Is(err, actor.ErrDeadLetter) {
		t.Fatalf("late boundary request error = %v; want ErrDeadLetter", err)
	}
}

func TestPA2IntegrationLifecycleDoesNotRenewOldIdleWindow(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release, crash: true})
	awaitValue(t, entered)
	passIdleWindow()
	close(release)
	if generation := awaitValue(t, observer.started); generation != 2 {
		t.Fatalf("replacement generation = %d", generation)
	}
	replacementEntered := make(chan struct{})
	replacementRelease := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 2, entered: replacementEntered, release: replacementRelease})
	awaitValue(t, replacementEntered)
	passIdleWindow()
	probe := system.Root.RequestFuture(pid, &smokeWork{sequence: 3, reply: true}, 2*time.Second)
	close(replacementRelease)
	expectReply(t, probe, "reply-3")
}

func TestPA2IntegrationLateOneWayPublishesDeadLetter(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	deadLetters := make(chan *actor.DeadLetterEvent, 4)
	sub := system.EventStream.SubscribeWithPredicate(func(event interface{}) {
		deadLetters <- event.(*actor.DeadLetterEvent)
	}, func(event interface{}) bool {
		value, ok := event.(*actor.DeadLetterEvent)
		return ok && value.PID != nil && value.PID.Equal(pid)
	})
	defer system.EventStream.Unsubscribe(sub)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	system.Root.Poison(pid)
	system.Root.Send(pid, &smokeWork{sequence: 2})
	close(release)
	event := awaitValue(t, deadLetters)
	work, ok := event.Message.(*smokeWork)
	if !ok || work.sequence != 2 {
		t.Fatalf("late dead letter = %#v", event.Message)
	}
}

func TestPA2IntegrationTerminationViewsConverge(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	queued := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	passIdleWindow()
	close(release)
	expectReply(t, queued, "reply-2")
	awaitValue(t, terminated)
	if _, ok := system.ProcessRegistry.Get(pid); ok {
		t.Fatalf("terminated PID remains registered: %v", pid)
	}
	late := system.Root.RequestFuture(pid, &smokeWork{sequence: 3}, 2*time.Second)
	if _, err := late.Result(); !errors.Is(err, actor.ErrDeadLetter) {
		t.Fatalf("registry/dead-letter convergence error = %v", err)
	}
}

func TestPA2IntegrationOneShotDoesNotCrossPassivation(t *testing.T) {
	system := actor.NewActorSystem()
	started := make(chan struct{}, 1)
	props := actor.PropsFromProducer(func() actor.Actor {
		return &scheduledActor{started: started}
	}, actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	pid := system.Root.Spawn(props)
	defer stopAndWait(t, system, pid)
	awaitValue(t, started)
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	deadLetters := make(chan *actor.DeadLetterEvent, 4)
	sub := system.EventStream.SubscribeWithPredicate(func(event interface{}) {
		deadLetters <- event.(*actor.DeadLetterEvent)
	}, func(event interface{}) bool {
		value, ok := event.(*actor.DeadLetterEvent)
		return ok && value.PID != nil && value.PID.Equal(pid)
	})
	defer system.EventStream.Unsubscribe(sub)
	expectReply(t, system.Root.RequestFuture(pid, &armSelf{delay: 5 * smokeIdle}, testDeadline), "armed")
	awaitValue(t, terminated)
	select {
	case event := <-deadLetters:
		t.Fatalf("actor-owned one-shot crossed passivation: %#v", event.Message)
	case <-time.After(6 * smokeIdle):
	}
}

func TestPA2IntegrationRootScheduleRemainsIndependent(t *testing.T) {
	system := actor.NewActorSystem()
	values := make(chan string, 8)
	sink := spawnSink(system, values)
	defer stopAndWait(t, system, sink)
	started := make(chan struct{}, 1)
	props := actor.PropsFromProducer(func() actor.Actor {
		return &scheduledActor{sink: sink, started: started}
	}, actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	pid := system.Root.Spawn(props)
	defer stopAndWait(t, system, pid)
	awaitValue(t, started)
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	delay := 5 * smokeIdle
	scheduler.NewTimerScheduler(system.Root).SendOnce(delay, sink, "root")
	expectReply(t, system.Root.RequestFuture(pid, &armOnce{delay: delay}, testDeadline), "armed")
	awaitValue(t, terminated)
	if value := awaitValue(t, values); value != "root" {
		t.Fatalf("surviving schedule owner = %q; want root", value)
	}
	expectNoString(t, values, 2*smokeIdle)
}

func TestPA2IntegrationOldTimerCannotStopReplacement(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	props := actor.PropsFromProducer(func() actor.Actor {
		generation := int(observer.generation.Add(1))
		return &smokeActor{observer: observer, generation: generation}
	}, actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	pid, err := system.Root.SpawnNamed(props, "old-timer-replacement")
	if err != nil {
		t.Fatal(err)
	}
	awaitValue(t, observer.started)
	if err := system.Root.StopFuture(pid).Wait(); err != nil {
		t.Fatal(err)
	}
	pid, err = system.Root.SpawnNamed(props, "old-timer-replacement")
	if err != nil {
		t.Fatal(err)
	}
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 2, entered: entered, release: release})
	awaitValue(t, entered)
	passIdleWindow()
	query := system.Root.RequestFuture(pid, &smokeWork{sequence: 3, reply: true}, 2*time.Second)
	close(release)
	expectReply(t, query, "reply-3")
}

func TestPA2IntegrationCommittedPassivationBeatsRestart(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	lateFailures := make(chan *actor.DeadLetterEvent, 1)
	sub := system.EventStream.SubscribeWithPredicate(func(event interface{}) {
		lateFailures <- event.(*actor.DeadLetterEvent)
	}, func(event interface{}) bool {
		value, ok := event.(*actor.DeadLetterEvent)
		if !ok || value.PID == nil || !value.PID.Equal(pid) {
			return false
		}
		work, ok := value.Message.(*smokeWork)
		return ok && work.sequence == 2
	})
	defer system.EventStream.Unsubscribe(sub)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	system.Root.Poison(pid)
	system.Root.Send(pid, &smokeWork{sequence: 2, crash: true})
	close(release)
	awaitValue(t, observer.stopped)
	awaitValue(t, lateFailures)
	select {
	case generation := <-observer.started:
		t.Fatalf("restart escaped committed passivation into generation %d", generation)
	case <-time.After(4 * smokeIdle):
	}
}

func TestPA2IntegrationReplyAndPassivationHaveOneWinner(t *testing.T) {
	system := actor.NewActorSystem()
	observer := newSmokeObserver(nil)
	pid := spawnSmoke(t, system, observer)
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.started)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &smokeWork{sequence: 1, entered: entered, release: release})
	awaitValue(t, entered)
	future := system.Root.RequestFuture(pid, &smokeWork{sequence: 2, reply: true}, 2*time.Second)
	passIdleWindow()
	close(release)
	expectReply(t, future, "reply-2")
	value, err := future.Result()
	if err != nil || value != "reply-2" {
		t.Fatalf("retained terminal changed = %#v, %v", value, err)
	}
}

func TestPA2IntegrationGroupViewExcludesPassivatedRoutee(t *testing.T) {
	system := actor.NewActorSystem()
	started := make(chan *actor.PID, 1)
	props := actor.PropsFromProducer(func() actor.Actor { return &idleRoutee{started: started} },
		actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	routee := system.Root.Spawn(props)
	defer stopAndWait(t, system, routee)
	awaitValue(t, started)
	group := system.Root.Spawn(router.NewRoundRobinGroup(routee))
	defer stopAndWait(t, system, group)
	terminated, watcher := spawnWatcher(t, system, routee)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)
	if view := routeeView(t, system, group); len(view) != 0 {
		t.Fatalf("completed view contains passivated routee: %v", view)
	}
	late := system.Root.RequestFuture(routee, "late", 2*time.Second)
	if _, err := late.Result(); !errors.Is(err, actor.ErrDeadLetter) {
		t.Fatalf("direct late routee request error = %v", err)
	}
}

func TestPA2IntegrationStoppingPoolDoesNotReplenish(t *testing.T) {
	system := actor.NewActorSystem()
	started := make(chan *actor.PID, 8)
	pool := system.Root.Spawn(router.NewRoundRobinPool(1,
		actor.WithProducer(func() actor.Actor { return &idleRoutee{started: started} }),
		actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle}))))
	first := awaitValue(t, started)
	terminated, watcher := spawnWatcher(t, system, first)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)
	awaitValue(t, started)
	if err := system.Root.StopFuture(pool).Wait(); err != nil {
		t.Fatal(err)
	}
	select {
	case replacement := <-started:
		t.Fatalf("stopping pool replenished routee %v", replacement)
	case <-time.After(4 * smokeIdle):
	}
}

func TestPA2IntegrationNonIdempotentEventsSurvivePassivation(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(100)}
	observer := newPersistenceObserver()
	props := persistentProps(provider, observer, smokeIdle)
	pid := spawnPersistentNamed(t, system, props, "non-idempotent")
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.recovered)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &persistentBlock{entered: entered, release: release})
	awaitValue(t, entered)
	appendFuture := system.Root.RequestFuture(pid, &persistedAppend{value: "A"}, 2*time.Second)
	passIdleWindow()
	close(release)
	if value, err := appendFuture.Result(); err != nil || value != "A" {
		t.Fatalf("admitted non-idempotent event = %#v, %v", value, err)
	}
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)
	pid = spawnPersistentNamed(t, system, props, "non-idempotent")
	awaitValue(t, observer.recovered)
	if value, err := system.Root.RequestFuture(pid, "query", testDeadline).Result(); err != nil || value != "A" {
		t.Fatalf("reactivated non-idempotent state = %#v, %v", value, err)
	}
}

func TestPA2IntegrationReactivatedActorRejectsOldTimer(t *testing.T) {
	system := actor.NewActorSystem()
	provider := &inMemoryPersistence{InMemoryProvider: persistence.NewInMemoryProvider(100)}
	observer := newPersistenceObserver()
	props := persistentProps(provider, observer, smokeIdle)
	pid := spawnPersistentNamed(t, system, props, "persistent-old-timer")
	awaitValue(t, observer.recovered)
	if err := system.Root.StopFuture(pid).Wait(); err != nil {
		t.Fatal(err)
	}
	pid = spawnPersistentNamed(t, system, props, "persistent-old-timer")
	defer stopAndWait(t, system, pid)
	awaitValue(t, observer.recovered)
	entered := make(chan struct{})
	release := make(chan struct{})
	system.Root.Send(pid, &persistentBlock{entered: entered, release: release})
	awaitValue(t, entered)
	passIdleWindow()
	query := system.Root.RequestFuture(pid, "query", 2*time.Second)
	close(release)
	if value, err := query.Result(); err != nil || value != "" {
		t.Fatalf("replacement query = %#v, %v", value, err)
	}
}
