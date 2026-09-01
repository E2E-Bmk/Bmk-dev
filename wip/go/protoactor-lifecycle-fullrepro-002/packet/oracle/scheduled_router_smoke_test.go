package passivationoracle_test

import (
	"testing"
	"time"

	"github.com/asynkron/protoactor-go/actor"
	"github.com/asynkron/protoactor-go/plugin"
	"github.com/asynkron/protoactor-go/router"
	"github.com/asynkron/protoactor-go/scheduler"
)

type armOnce struct {
	delay time.Duration
}

type armRepeated struct {
	initial  time.Duration
	interval time.Duration
}

type armSelf struct {
	delay time.Duration
}

type scheduledActor struct {
	plugin.PassivationHolder
	sink      *actor.PID
	started   chan<- struct{}
	cancelOut chan<- scheduler.CancelFunc
}

func (probe *scheduledActor) Receive(ctx actor.Context) {
	switch message := ctx.Message().(type) {
	case *actor.Started:
		if probe.started != nil {
			probe.started <- struct{}{}
		}
	case *armOnce:
		scheduler.NewTimerScheduler(ctx).SendOnce(message.delay, probe.sink, "once")
		ctx.Respond("armed")
	case *armRepeated:
		cancel := scheduler.NewTimerScheduler(ctx).SendRepeatedly(message.initial, message.interval, probe.sink, "repeat")
		if probe.cancelOut != nil {
			probe.cancelOut <- cancel
		}
		ctx.Respond("armed")
	case *armSelf:
		scheduler.NewTimerScheduler(ctx).SendOnce(message.delay, ctx.Self(), "self-tick")
		ctx.Respond("armed")
	}
}

func spawnWatcher(t *testing.T, system *actor.ActorSystem, target *actor.PID) (<-chan *actor.Terminated, *actor.PID) {
	t.Helper()
	ready := make(chan struct{})
	terminated := make(chan *actor.Terminated, 1)
	pid := system.Root.Spawn(actor.PropsFromProducer(func() actor.Actor {
		return &watchTarget{target: target, terminated: terminated, ready: ready}
	}))
	awaitValue(t, ready)
	return terminated, pid
}

func spawnSink(system *actor.ActorSystem, values chan<- string) *actor.PID {
	return system.Root.Spawn(actor.PropsFromFunc(func(ctx actor.Context) {
		if value, ok := ctx.Message().(string); ok {
			values <- value
		}
	}))
}

func expectNoString(t *testing.T, values <-chan string, observation time.Duration) {
	t.Helper()
	select {
	case value := <-values:
		t.Fatalf("unexpected callback after terminal boundary: %q", value)
	case <-time.After(observation):
	}
}

func TestPA2AtomicActorOwnedTimerStopsWithIncarnation(t *testing.T) {
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

	expectReply(t, system.Root.RequestFuture(pid, &armOnce{delay: 5 * smokeIdle}, testDeadline), "armed")
	awaitValue(t, terminated)
	expectNoString(t, values, 6*smokeIdle)
}

func TestPA2IntegrationRepeatedScheduleCannotRearm(t *testing.T) {
	system := actor.NewActorSystem()
	values := make(chan string, 32)
	sink := spawnSink(system, values)
	defer stopAndWait(t, system, sink)
	started := make(chan struct{}, 1)
	cancelOut := make(chan scheduler.CancelFunc, 1)
	props := actor.PropsFromProducer(func() actor.Actor {
		return &scheduledActor{sink: sink, started: started, cancelOut: cancelOut}
	}, actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	pid := system.Root.Spawn(props)
	defer stopAndWait(t, system, pid)
	awaitValue(t, started)
	terminated, watcher := spawnWatcher(t, system, pid)
	defer stopAndWait(t, system, watcher)

	expectReply(t, system.Root.RequestFuture(pid, &armRepeated{initial: 20 * time.Millisecond, interval: 30 * time.Millisecond}, testDeadline), "armed")
	cancel := awaitValue(t, cancelOut)
	defer cancel()
	awaitValue(t, terminated)
	for {
		select {
		case <-values:
			continue
		default:
			goto drained
		}
	}
drained:
	expectNoString(t, values, 4*smokeIdle)
}

func routeeView(t *testing.T, system *actor.ActorSystem, routerPID *actor.PID) []*actor.PID {
	t.Helper()
	value, err := system.Root.RequestFuture(routerPID, &router.GetRoutees{}, testDeadline).Result()
	if err != nil {
		t.Fatalf("get routees: %v", err)
	}
	return value.(*router.Routees).PIDs
}

func TestPA2SystemScheduledRouteePassivationChain(t *testing.T) {
	system := actor.NewActorSystem()
	values := make(chan string, 8)
	sink := spawnSink(system, values)
	defer stopAndWait(t, system, sink)
	started := make(chan struct{}, 1)
	props := actor.PropsFromProducer(func() actor.Actor {
		return &scheduledActor{sink: sink, started: started}
	}, actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle})))
	routee := system.Root.Spawn(props)
	defer stopAndWait(t, system, routee)
	awaitValue(t, started)
	group := system.Root.Spawn(router.NewRoundRobinGroup(routee))
	defer stopAndWait(t, system, group)
	terminated, watcher := spawnWatcher(t, system, routee)
	defer stopAndWait(t, system, watcher)

	expectReply(t, system.Root.RequestFuture(routee, &armOnce{delay: 5 * smokeIdle}, testDeadline), "armed")
	awaitValue(t, terminated)
	if view := routeeView(t, system, group); len(view) != 0 {
		t.Fatalf("completed group view retained passivated routee: %v", view)
	}
	expectNoString(t, values, 6*smokeIdle)
}

type idleRoutee struct {
	plugin.PassivationHolder
	started chan<- *actor.PID
}

func (routee *idleRoutee) Receive(ctx actor.Context) {
	switch ctx.Message().(type) {
	case *actor.Started:
		if routee.started != nil {
			routee.started <- ctx.Self()
		}
	case string:
		ctx.Respond(ctx.Self())
	}
}

func TestPA2AtomicGroupRemovesPassivatedRoutee(t *testing.T) {
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
		t.Fatalf("group retained passivated routee: %v", view)
	}
}

func TestPA2IntegrationPoolReplenishesPassivatedRoutee(t *testing.T) {
	system := actor.NewActorSystem()
	started := make(chan *actor.PID, 8)
	pool := system.Root.Spawn(router.NewRoundRobinPool(1,
		actor.WithProducer(func() actor.Actor { return &idleRoutee{started: started} }),
		actor.WithReceiverMiddleware(plugin.Use(&plugin.PassivationPlugin{Duration: smokeIdle}))))
	defer stopAndWait(t, system, pool)
	first := awaitValue(t, started)
	terminated, watcher := spawnWatcher(t, system, first)
	defer stopAndWait(t, system, watcher)
	awaitValue(t, terminated)
	replacement := awaitValue(t, started)
	if replacement.Equal(first) {
		t.Fatalf("pool reused passivated routee identity: %v", replacement)
	}
	view := routeeView(t, system, pool)
	if len(view) != 1 || !view[0].Equal(replacement) {
		t.Fatalf("pool view = %v; replacement = %v", view, replacement)
	}
}
