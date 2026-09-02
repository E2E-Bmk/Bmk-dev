package integration_test

import (
	"context"
	"errors"
	"reflect"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/go-co-op/gocron/v2"
	"github.com/google/uuid"
)

const testTimeout = 4 * time.Second

func newWorkflow(t *testing.T, schedulerOptions ...gocron.SchedulerOption) (gocron.Scheduler, gocron.Workflow) {
	t.Helper()
	s, err := gocron.NewScheduler(schedulerOptions...)
	if err != nil {
		t.Fatal(err)
	}
	w, err := gocron.NewWorkflow(s, "pipeline")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
		defer cancel()
		_ = w.Shutdown(ctx)
		_ = s.Shutdown()
	})
	return s, w
}

func waitRun(t *testing.T, run gocron.WorkflowRun) (gocron.WorkflowResult, error) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	return run.Wait(ctx)
}

func addTask(t *testing.T, w gocron.Workflow, name string, deps []string, fn any, options ...gocron.JobOption) gocron.Job {
	t.Helper()
	job, err := w.Add(name, gocron.NewTask(fn), deps, options...)
	if err != nil {
		t.Fatal(err)
	}
	return job
}

func statuses(result gocron.WorkflowResult) map[string]gocron.WorkflowNodeStatus {
	out := make(map[string]gocron.WorkflowNodeStatus, len(result.Nodes))
	for name, node := range result.Nodes {
		out[name] = node.Status
	}
	return out
}

type failingLocker struct{ err error }

func (l failingLocker) Lock(context.Context, string) (gocron.Lock, error) { return nil, l.err }

// Verifies: GCWF-EPOCH-005, GCWF-EPOCH-006
// Depends-On: TestEpochIDsIncrease, TestSuccessResultHasTerminalTimes
func TestLinearChainRunsInDependencyOrder(t *testing.T) {
	s, w := newWorkflow(t)
	var mu sync.Mutex
	order := []string{}
	for i, name := range []string{"extract", "transform", "load"} {
		var deps []string
		if i > 0 {
			deps = []string{[]string{"extract", "transform"}[i-1]}
		}
		current := name
		addTask(t, w, current, deps, func() {
			mu.Lock()
			order = append(order, current)
			mu.Unlock()
		})
	}
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if err != nil || !reflect.DeepEqual(order, []string{"extract", "transform", "load"}) {
		t.Fatalf("order=%v status=%v error=%v", order, statuses(result), err)
	}
}

// Verifies: GCWF-EPOCH-007
// Depends-On: TestRunNowReturnsBeforeTaskCompletes, TestSuccessResultHasTerminalTimes
func TestIndependentRootsRunConcurrently(t *testing.T) {
	s, w := newWorkflow(t)
	started := make(chan string, 2)
	release := make(chan struct{})
	for _, name := range []string{"left", "right"} {
		current := name
		addTask(t, w, current, nil, func() { started <- current; <-release })
	}
	s.Start()
	run, _ := w.RunNow(context.Background())
	seen := map[string]bool{}
	for range 2 {
		select {
		case name := <-started:
			seen[name] = true
		case <-time.After(testTimeout):
			t.Fatal("roots did not run concurrently")
		}
	}
	close(release)
	result, err := waitRun(t, run)
	if err != nil || !seen["left"] || !seen["right"] || len(result.Nodes) != 2 {
		t.Fatalf("seen=%v status=%v error=%v", seen, statuses(result), err)
	}
}

// Verifies: GCWF-EPOCH-008
// Depends-On: TestNodesDeduplicateAndCopyDependencies, TestSuccessResultHasTerminalTimes
func TestDiamondJoinRunsExactlyOnce(t *testing.T) {
	s, w := newWorkflow(t)
	var joinCalls atomic.Int32
	addTask(t, w, "root", nil, func() {})
	addTask(t, w, "left", []string{"root"}, func() {})
	addTask(t, w, "right", []string{"root"}, func() {})
	addTask(t, w, "join", []string{"left", "right"}, func() { joinCalls.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if err != nil || joinCalls.Load() != 1 || result.Nodes["join"].Status != gocron.WorkflowNodeSucceeded {
		t.Fatalf("calls=%d status=%v error=%v", joinCalls.Load(), statuses(result), err)
	}
}

// Verifies: GCWF-EPOCH-008
// Depends-On: TestNodesDeduplicateAndCopyDependencies, TestSuccessResultHasTerminalTimes
func TestDiamondJoinWaitsForSlowLeftParent(t *testing.T) {
	s, w := newWorkflow(t)
	leftRelease := make(chan struct{})
	rightDone := make(chan struct{})
	joinStarted := make(chan struct{})
	addTask(t, w, "root", nil, func() {})
	addTask(t, w, "left", []string{"root"}, func() { <-leftRelease })
	addTask(t, w, "right", []string{"root"}, func() { close(rightDone) })
	addTask(t, w, "join", []string{"left", "right"}, func() { close(joinStarted) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	select {
	case <-rightDone:
	case <-time.After(testTimeout):
		t.Fatal("right did not finish")
	}
	select {
	case <-joinStarted:
		t.Fatal("join started before left")
	default:
	}
	close(leftRelease)
	if _, err := waitRun(t, run); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GCWF-EPOCH-008
// Depends-On: TestNodesDeduplicateAndCopyDependencies, TestSuccessResultHasTerminalTimes
func TestDiamondJoinWaitsForSlowRightParent(t *testing.T) {
	s, w := newWorkflow(t)
	rightRelease := make(chan struct{})
	leftDone := make(chan struct{})
	joinStarted := make(chan struct{})
	addTask(t, w, "root", nil, func() {})
	addTask(t, w, "left", []string{"root"}, func() { close(leftDone) })
	addTask(t, w, "right", []string{"root"}, func() { <-rightRelease })
	addTask(t, w, "join", []string{"left", "right"}, func() { close(joinStarted) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	select {
	case <-leftDone:
	case <-time.After(testTimeout):
		t.Fatal("left did not finish")
	}
	select {
	case <-joinStarted:
		t.Fatal("join started before right")
	default:
	}
	close(rightRelease)
	if _, err := waitRun(t, run); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GCWF-EPOCH-006, GCWF-EPOCH-008, GCWF-RESULT-004
// Depends-On: TestNodesDeduplicateAndCopyDependencies, TestSuccessResultHasTerminalTimes
func TestDiamondJoinRemainsPendingUntilBlockedParentCompletes(t *testing.T) {
	s, w := newWorkflow(t)
	slowStarted := make(chan struct{})
	slowRelease := make(chan struct{})
	fastCompleted := make(chan struct{})
	joinStarted := make(chan struct{})
	var releaseOnce sync.Once
	releaseSlow := func() { releaseOnce.Do(func() { close(slowRelease) }) }
	defer releaseSlow()

	addTask(t, w, "root", nil, func() {})
	addTask(t, w, "slow", []string{"root"}, func() {
		close(slowStarted)
		<-slowRelease
	})
	addTask(t, w, "fast", []string{"root"}, func() {}, gocron.WithEventListeners(
		gocron.AfterJobRuns(func(uuid.UUID, string) { close(fastCompleted) }),
	))
	addTask(t, w, "join", []string{"fast", "slow"}, func() { close(joinStarted) })
	s.Start()
	run, err := w.RunNow(context.Background())
	if err != nil {
		t.Fatal(err)
	}

	for name, signal := range map[string]<-chan struct{}{
		"slow start":      slowStarted,
		"fast completion": fastCompleted,
	} {
		select {
		case <-signal:
		case <-time.After(testTimeout):
			t.Fatalf("timed out waiting for %s", name)
		}
	}

	deadline := time.Now().Add(testTimeout)
	for {
		snapshot := run.Snapshot()
		if snapshot.Nodes["fast"].Status == gocron.WorkflowNodeSucceeded &&
			snapshot.Nodes["slow"].Status == gocron.WorkflowNodeRunning {
			break
		}
		if time.Now().After(deadline) {
			t.Fatalf("parent states did not settle: %v", statuses(snapshot))
		}
		time.Sleep(time.Millisecond)
	}

	// Give a scheduler that incorrectly releases on the first successful
	// parent a bounded opportunity to make that public state observable.
	select {
	case <-joinStarted:
		t.Fatal("join task started before slow parent completed")
	case <-time.After(250 * time.Millisecond):
	}
	snapshot := run.Snapshot()
	if snapshot.Nodes["join"].Status != gocron.WorkflowNodePending {
		t.Fatalf("join status before slow completion = %s", snapshot.Nodes["join"].Status)
	}

	releaseSlow()
	result, err := waitRun(t, run)
	if err != nil || result.Nodes["join"].Status != gocron.WorkflowNodeSucceeded {
		t.Fatalf("terminal status=%v error=%v", statuses(result), err)
	}
}

// Verifies: GCWF-RESULT-005, GCWF-RESULT-007
// Depends-On: TestTaskErrorProducesFailedResult, TestNodesDeduplicateAndCopyDependencies
func TestFailureBlocksDirectChild(t *testing.T) {
	s, w := newWorkflow(t)
	var childCalls atomic.Int32
	addTask(t, w, "root", nil, func() error { return errors.New("root failed") })
	addTask(t, w, "child", []string{"root"}, func() { childCalls.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if !errors.Is(err, gocron.ErrWorkflowFailed) || childCalls.Load() != 0 || result.Nodes["child"].Status != gocron.WorkflowNodeBlocked || !errors.Is(result.Nodes["child"].Err, gocron.ErrWorkflowDependencyFailed) {
		t.Fatalf("calls=%d status=%v error=%v", childCalls.Load(), statuses(result), err)
	}
}

// Verifies: GCWF-RESULT-007
// Depends-On: TestTaskErrorProducesFailedResult, TestNodesDeduplicateAndCopyDependencies
func TestFailureBlocksTransitiveDescendants(t *testing.T) {
	s, w := newWorkflow(t)
	var calls atomic.Int32
	addTask(t, w, "a", nil, func() error { return errors.New("fail") })
	addTask(t, w, "b", []string{"a"}, func() { calls.Add(1) })
	addTask(t, w, "c", []string{"b"}, func() { calls.Add(1) })
	addTask(t, w, "d", []string{"c"}, func() { calls.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, _ := waitRun(t, run)
	if calls.Load() != 0 || result.Nodes["b"].Status != gocron.WorkflowNodeBlocked || result.Nodes["d"].Status != gocron.WorkflowNodeBlocked {
		t.Fatalf("calls=%d status=%v", calls.Load(), statuses(result))
	}
}

// Verifies: GCWF-RESULT-008
// Depends-On: TestTaskErrorProducesFailedResult, TestSuccessResultHasTerminalTimes
func TestFailureDoesNotStopUnrelatedBranch(t *testing.T) {
	s, w := newWorkflow(t)
	var unrelated atomic.Int32
	addTask(t, w, "bad", nil, func() error { return errors.New("bad") })
	addTask(t, w, "blocked", []string{"bad"}, func() {})
	addTask(t, w, "good", nil, func() { unrelated.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, _ := waitRun(t, run)
	if unrelated.Load() != 1 || result.Nodes["good"].Status != gocron.WorkflowNodeSucceeded || result.Nodes["blocked"].Status != gocron.WorkflowNodeBlocked {
		t.Fatalf("calls=%d status=%v", unrelated.Load(), statuses(result))
	}
}

// Verifies: GCWF-RESULT-006, GCWF-RESULT-007
// Depends-On: TestTaskPanicProducesFailedResult, TestNodesDeduplicateAndCopyDependencies
func TestPanicBlocksDescendant(t *testing.T) {
	s, w := newWorkflow(t)
	var child atomic.Int32
	addTask(t, w, "panic", nil, func() { panic("boom") })
	addTask(t, w, "child", []string{"panic"}, func() { child.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if !errors.Is(err, gocron.ErrWorkflowFailed) || child.Load() != 0 || !errors.Is(result.Nodes["panic"].Err, gocron.ErrPanicRecovered) {
		t.Fatalf("calls=%d status=%v error=%v", child.Load(), statuses(result), err)
	}
}

// Verifies: GCWF-SCHED-002, GCWF-RESULT-007
// Depends-On: TestTaskErrorProducesFailedResult, TestAddedJobVisibleInScheduler
func TestBeforeListenerRejectionBlocksDescendant(t *testing.T) {
	s, w := newWorkflow(t)
	var tasks atomic.Int32
	addTask(t, w, "root", nil, func() { tasks.Add(1) }, gocron.WithEventListeners(gocron.BeforeJobRunsSkipIfBeforeFuncErrors(func(uuid.UUID, string) error { return errors.New("reject") })))
	addTask(t, w, "child", []string{"root"}, func() { tasks.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if !errors.Is(err, gocron.ErrWorkflowFailed) || tasks.Load() != 0 || result.Nodes["root"].Status != gocron.WorkflowNodeFailed || result.Nodes["child"].Status != gocron.WorkflowNodeBlocked {
		t.Fatalf("tasks=%d status=%v error=%v", tasks.Load(), statuses(result), err)
	}
}

// Verifies: GCWF-SCHED-003, GCWF-RESULT-007
// Depends-On: TestTaskErrorProducesFailedResult, TestAddedJobVisibleInScheduler
func TestLockErrorBlocksDescendant(t *testing.T) {
	s, w := newWorkflow(t)
	lockErr := errors.New("lock unavailable")
	var calls atomic.Int32
	addTask(t, w, "root", nil, func() { calls.Add(1) }, gocron.WithDistributedJobLocker(failingLocker{err: lockErr}))
	addTask(t, w, "child", []string{"root"}, func() { calls.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if !errors.Is(err, gocron.ErrWorkflowFailed) || calls.Load() != 0 || !errors.Is(result.Nodes["root"].Err, lockErr) || result.Nodes["child"].Status != gocron.WorkflowNodeBlocked {
		t.Fatalf("calls=%d status=%v nodeErr=%v wait=%v", calls.Load(), statuses(result), result.Nodes["root"].Err, err)
	}
}

// Verifies: GCWF-SCHED-002
// Depends-On: TestSuccessResultHasTerminalTimes
func TestSuccessListenersRemainObservable(t *testing.T) {
	s, w := newWorkflow(t)
	var before, after atomic.Int32
	addTask(t, w, "node", nil, func() {}, gocron.WithEventListeners(
		gocron.BeforeJobRuns(func(uuid.UUID, string) { before.Add(1) }),
		gocron.AfterJobRuns(func(uuid.UUID, string) { after.Add(1) }),
	))
	s.Start()
	run, _ := w.RunNow(context.Background())
	if _, err := waitRun(t, run); err != nil || before.Load() != 1 || after.Load() != 1 {
		t.Fatalf("before=%d after=%d error=%v", before.Load(), after.Load(), err)
	}
}

// Verifies: GCWF-SCHED-002
// Depends-On: TestTaskErrorProducesFailedResult
func TestErrorListenerReceivesTaskError(t *testing.T) {
	s, w := newWorkflow(t)
	boom := errors.New("boom")
	received := make(chan error, 1)
	addTask(t, w, "node", nil, func() error { return boom }, gocron.WithEventListeners(gocron.AfterJobRunsWithError(func(_ uuid.UUID, _ string, err error) { received <- err })))
	s.Start()
	run, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, run)
	select {
	case err := <-received:
		if !errors.Is(err, boom) {
			t.Fatalf("listener error=%v", err)
		}
	case <-time.After(testTimeout):
		t.Fatal("error listener not called")
	}
}

// Verifies: GCWF-SCHED-002
// Depends-On: TestTaskPanicProducesFailedResult
func TestPanicListenerReceivesRecoveredValue(t *testing.T) {
	s, w := newWorkflow(t)
	received := make(chan any, 1)
	addTask(t, w, "node", nil, func() { panic("panic-value") }, gocron.WithEventListeners(gocron.AfterJobRunsWithPanic(func(_ uuid.UUID, _ string, value any) { received <- value })))
	s.Start()
	run, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, run)
	select {
	case value := <-received:
		if value != "panic-value" {
			t.Fatalf("panic value=%v", value)
		}
	case <-time.After(testTimeout):
		t.Fatal("panic listener not called")
	}
}

// Verifies: GCWF-SCHED-002, GCWF-SCHED-003
// Depends-On: TestTaskErrorProducesFailedResult, TestAddedJobVisibleInScheduler
func TestLockListenerReceivesLockError(t *testing.T) {
	s, w := newWorkflow(t)
	lockErr := errors.New("lock")
	received := make(chan error, 1)
	addTask(t, w, "node", nil, func() {}, gocron.WithDistributedJobLocker(failingLocker{err: lockErr}), gocron.WithEventListeners(gocron.AfterLockError(func(_ uuid.UUID, _ string, err error) { received <- err })))
	s.Start()
	run, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, run)
	select {
	case err := <-received:
		if !errors.Is(err, lockErr) {
			t.Fatalf("lock listener error=%v", err)
		}
	case <-time.After(testTimeout):
		t.Fatal("lock listener not called")
	}
}

// Verifies: GCWF-SCHED-004
// Depends-On: TestRunNowReturnsBeforeTaskCompletes, TestSuccessResultHasTerminalTimes
func TestGlobalWaitLimitBoundsReadyNodeConcurrency(t *testing.T) {
	s, w := newWorkflow(t, gocron.WithLimitConcurrentJobs(2, gocron.LimitModeWait))
	release := make(chan struct{})
	var current, maximum atomic.Int32
	for i := 0; i < 6; i++ {
		name := string(rune('a' + i))
		addTask(t, w, name, nil, func() {
			now := current.Add(1)
			for {
				old := maximum.Load()
				if now <= old || maximum.CompareAndSwap(old, now) {
					break
				}
			}
			<-release
			current.Add(-1)
		})
	}
	s.Start()
	run, _ := w.RunNow(context.Background())
	deadline := time.After(testTimeout)
	for maximum.Load() < 2 {
		select {
		case <-deadline:
			t.Fatal("two jobs did not start")
		default:
			time.Sleep(time.Millisecond)
		}
	}
	close(release)
	result, err := waitRun(t, run)
	if err != nil || maximum.Load() != 2 || len(result.Nodes) != 6 {
		t.Fatalf("max=%d status=%v error=%v", maximum.Load(), statuses(result), err)
	}
}

// Verifies: GCWF-SCHED-005, GCWF-EPOCH-009
// Depends-On: TestEpochIDsIncrease, TestRunNowReturnsBeforeTaskCompletes
func TestSameNodeSerializesAcrossEpochs(t *testing.T) {
	s, w := newWorkflow(t)
	firstRelease := make(chan struct{})
	secondRelease := make(chan struct{})
	started := make(chan int, 2)
	var invocation atomic.Int32
	addTask(t, w, "node", nil, func() {
		n := int(invocation.Add(1))
		started <- n
		if n == 1 {
			<-firstRelease
		} else {
			<-secondRelease
		}
	})
	s.Start()
	first, _ := w.RunNow(context.Background())
	second, _ := w.RunNow(context.Background())
	select {
	case n := <-started:
		if n != 1 {
			t.Fatalf("first invocation = %d", n)
		}
	case <-time.After(testTimeout):
		t.Fatal("first epoch did not start")
	}
	select {
	case n := <-started:
		t.Fatalf("second started concurrently: %d", n)
	case <-time.After(30 * time.Millisecond):
	}
	close(firstRelease)
	select {
	case n := <-started:
		if n != 2 {
			t.Fatalf("second invocation = %d", n)
		}
	case <-time.After(testTimeout):
		t.Fatal("second epoch did not start")
	}
	close(secondRelease)
	if _, err := waitRun(t, first); err != nil {
		t.Fatal(err)
	}
	if _, err := waitRun(t, second); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GCWF-EPOCH-009
// Depends-On: TestEpochIDsIncrease, TestTaskErrorProducesFailedResult
func TestOverlappingEpochResultsRemainIsolated(t *testing.T) {
	s, w := newWorkflow(t)
	type contextKey string
	addTask(t, w, "node", nil, func(ctx context.Context) error {
		if ctx.Value(contextKey("fail")) == true {
			return errors.New("epoch failure")
		}
		return nil
	})
	s.Start()
	failingCtx := context.WithValue(context.Background(), contextKey("fail"), true)
	successCtx := context.WithValue(context.Background(), contextKey("fail"), false)
	failed, _ := w.RunNow(failingCtx)
	succeeded, _ := w.RunNow(successCtx)
	failedResult, failedErr := waitRun(t, failed)
	successResult, successErr := waitRun(t, succeeded)
	if !errors.Is(failedErr, gocron.ErrWorkflowFailed) || successErr != nil || failedResult.Nodes["node"].Status != gocron.WorkflowNodeFailed || successResult.Nodes["node"].Status != gocron.WorkflowNodeSucceeded {
		t.Fatalf("failed=%v/%v succeeded=%v/%v", statuses(failedResult), failedErr, statuses(successResult), successErr)
	}
}

// Verifies: GCWF-GRAPH-012, GCWF-GRAPH-009
// Depends-On: TestUpdatePreservesJobID, TestSuccessResultHasTerminalTimes
func TestUpdatedTaskRunsInNextEpoch(t *testing.T) {
	s, w := newWorkflow(t)
	var oldCalls, newCalls atomic.Int32
	job := addTask(t, w, "node", nil, func() { oldCalls.Add(1) })
	s.Start()
	first, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, first)
	updated, err := w.Update("node", gocron.NewTask(func() { newCalls.Add(1) }), nil)
	if err != nil || updated.ID() != job.ID() {
		t.Fatalf("update = %v ids=%s/%s", err, job.ID(), updated.ID())
	}
	second, _ := w.RunNow(context.Background())
	_, err = waitRun(t, second)
	if err != nil || oldCalls.Load() != 1 || newCalls.Load() != 1 {
		t.Fatalf("old=%d new=%d error=%v", oldCalls.Load(), newCalls.Load(), err)
	}
}

// Verifies: GCWF-GRAPH-012, GCWF-EPOCH-006
// Depends-On: TestUpdatePreservesJobID, TestNodesDeduplicateAndCopyDependencies
func TestUpdatedDependenciesControlNextEpoch(t *testing.T) {
	s, w := newWorkflow(t)
	var mu sync.Mutex
	order := []string{}
	addTask(t, w, "a", nil, func() { mu.Lock(); order = append(order, "a"); mu.Unlock() })
	addTask(t, w, "b", nil, func() { mu.Lock(); order = append(order, "b"); mu.Unlock() })
	_, err := w.Update("b", gocron.NewTask(func() { mu.Lock(); order = append(order, "b"); mu.Unlock() }), []string{"a"})
	if err != nil {
		t.Fatal(err)
	}
	s.Start()
	run, _ := w.RunNow(context.Background())
	_, err = waitRun(t, run)
	if err != nil || !reflect.DeepEqual(order, []string{"a", "b"}) {
		t.Fatalf("order=%v error=%v", order, err)
	}
}

// Verifies: GCWF-GRAPH-014
// Depends-On: TestRemoveLeafDeletesSchedulerJob
func TestRemoveThenRunExcludesRemovedLeaf(t *testing.T) {
	s, w := newWorkflow(t)
	var kept, removed atomic.Int32
	addTask(t, w, "kept", nil, func() { kept.Add(1) })
	addTask(t, w, "removed", nil, func() { removed.Add(1) })
	if err := w.Remove("removed"); err != nil {
		t.Fatal(err)
	}
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if err != nil || kept.Load() != 1 || removed.Load() != 0 || len(result.Nodes) != 1 {
		t.Fatalf("kept=%d removed=%d status=%v error=%v", kept.Load(), removed.Load(), statuses(result), err)
	}
}

// Verifies: GCWF-SCHED-006
// Depends-On: TestEpochIDsIncrease, TestTaskErrorProducesFailedResult
func TestLimitedRunsAppliesAcrossEpochs(t *testing.T) {
	s, w := newWorkflow(t)
	var calls atomic.Int32
	addTask(t, w, "node", nil, func() { calls.Add(1) }, gocron.WithLimitedRuns(1))
	s.Start()
	first, _ := w.RunNow(context.Background())
	_, firstErr := waitRun(t, first)
	second, _ := w.RunNow(context.Background())
	secondResult, secondErr := waitRun(t, second)
	if firstErr != nil || !errors.Is(secondErr, gocron.ErrWorkflowFailed) || calls.Load() != 1 || secondResult.Nodes["node"].Status != gocron.WorkflowNodeFailed {
		t.Fatalf("calls=%d first=%v second=%v status=%v", calls.Load(), firstErr, secondErr, statuses(secondResult))
	}
}

// Verifies: GCWF-RESULT-010
// Depends-On: TestRunCancelReachesContextTask
func TestStopCancelsEveryActiveEpoch(t *testing.T) {
	s, w := newWorkflow(t)
	started := make(chan struct{}, 2)
	addTask(t, w, "node", nil, func(ctx context.Context) error { started <- struct{}{}; <-ctx.Done(); return ctx.Err() })
	s.Start()
	first, _ := w.RunNow(context.Background())
	second, _ := w.RunNow(context.Background())
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	if err := w.Stop(ctx); err != nil {
		t.Fatal(err)
	}
	firstResult, firstErr := waitRun(t, first)
	secondResult, secondErr := waitRun(t, second)
	if !errors.Is(firstErr, context.Canceled) || !errors.Is(secondErr, context.Canceled) || firstResult.Nodes["node"].Status != gocron.WorkflowNodeCanceled || secondResult.Nodes["node"].Status != gocron.WorkflowNodeCanceled {
		t.Fatalf("first=%v/%v second=%v/%v", statuses(firstResult), firstErr, statuses(secondResult), secondErr)
	}
}

// Verifies: GCWF-LIFE-002
// Depends-On: TestAddedJobVisibleInScheduler, TestWorkflowShutdownIsIdempotent
func TestShutdownRemovesAllWorkflowJobs(t *testing.T) {
	s, w := newWorkflow(t)
	for _, name := range []string{"a", "b", "c"} {
		addTask(t, w, name, nil, func() {})
	}
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	if err := w.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
	if len(s.Jobs()) != 0 || len(w.Nodes()) != 0 {
		t.Fatalf("scheduler=%d workflow=%d", len(s.Jobs()), len(w.Nodes()))
	}
}

// Verifies: GCWF-LIFE-003
// Depends-On: TestAddedJobVisibleInScheduler, TestWorkflowShutdownIsIdempotent
func TestShutdownPreservesExternalSchedulerJob(t *testing.T) {
	s, w := newWorkflow(t)
	external, err := s.NewJob(gocron.DurationJob(time.Hour), gocron.NewTask(func() {}))
	if err != nil {
		t.Fatal(err)
	}
	addTask(t, w, "owned", nil, func() {})
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	if err := w.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
	found := false
	for _, job := range s.Jobs() {
		found = found || job.ID() == external.ID()
	}
	if !found {
		t.Fatal("external job removed")
	}
}

// Verifies: GCWF-RESULT-009, GCWF-RESULT-008
// Depends-On: TestRunCancelReachesContextTask, TestSuccessResultHasTerminalTimes
func TestCancelOneEpochDoesNotCancelAnother(t *testing.T) {
	s, w := newWorkflow(t)
	entered := make(chan struct{}, 2)
	addTask(t, w, "node", nil, func(ctx context.Context) error {
		entered <- struct{}{}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(40 * time.Millisecond):
			return nil
		}
	})
	s.Start()
	first, _ := w.RunNow(context.Background())
	second, _ := w.RunNow(context.Background())
	first.Cancel()
	firstResult, firstErr := waitRun(t, first)
	secondResult, secondErr := waitRun(t, second)
	if !errors.Is(firstErr, context.Canceled) || secondErr != nil || firstResult.Nodes["node"].Status != gocron.WorkflowNodeCanceled || secondResult.Nodes["node"].Status != gocron.WorkflowNodeSucceeded {
		t.Fatalf("first=%v/%v second=%v/%v", statuses(firstResult), firstErr, statuses(secondResult), secondErr)
	}
}

// Verifies: GCWF-RESULT-001, GCWF-RESULT-004
// Depends-On: TestSnapshotReturnsCopiedMap, TestSuccessResultHasTerminalTimes
func TestSnapshotShowsRunningThenSucceeded(t *testing.T) {
	s, w := newWorkflow(t)
	started := make(chan struct{})
	release := make(chan struct{})
	addTask(t, w, "node", nil, func() { close(started); <-release })
	s.Start()
	run, _ := w.RunNow(context.Background())
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("task did not start")
	}
	if status := run.Snapshot().Nodes["node"].Status; status != gocron.WorkflowNodeRunning {
		t.Fatalf("running status = %s", status)
	}
	close(release)
	result, err := waitRun(t, run)
	if err != nil || result.Nodes["node"].Status != gocron.WorkflowNodeSucceeded {
		t.Fatalf("terminal=%v error=%v", statuses(result), err)
	}
}

// Verifies: GCWF-RESULT-007, GCWF-RESULT-008
// Depends-On: TestTaskErrorProducesFailedResult, TestNodesDeduplicateAndCopyDependencies
func TestDiamondFailureBlocksJoinAfterOtherParentCompletes(t *testing.T) {
	s, w := newWorkflow(t)
	var right, join atomic.Int32
	addTask(t, w, "root", nil, func() {})
	addTask(t, w, "left", []string{"root"}, func() error { return errors.New("left failed") })
	addTask(t, w, "right", []string{"root"}, func() { right.Add(1) })
	addTask(t, w, "join", []string{"left", "right"}, func() { join.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, _ := waitRun(t, run)
	if right.Load() != 1 || join.Load() != 0 || result.Nodes["right"].Status != gocron.WorkflowNodeSucceeded || result.Nodes["join"].Status != gocron.WorkflowNodeBlocked {
		t.Fatalf("right=%d join=%d status=%v", right.Load(), join.Load(), statuses(result))
	}
}

// Verifies: GCWF-RESULT-007
// Depends-On: TestTaskErrorProducesFailedResult, TestNodesDeduplicateAndCopyDependencies
func TestTwoFailedRootsBlockSharedJoinOnce(t *testing.T) {
	s, w := newWorkflow(t)
	var join atomic.Int32
	addTask(t, w, "a", nil, func() error { return errors.New("a") })
	addTask(t, w, "b", nil, func() error { return errors.New("b") })
	addTask(t, w, "join", []string{"a", "b"}, func() { join.Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, _ := waitRun(t, run)
	if join.Load() != 0 || result.Nodes["a"].Status != gocron.WorkflowNodeFailed || result.Nodes["b"].Status != gocron.WorkflowNodeFailed || result.Nodes["join"].Status != gocron.WorkflowNodeBlocked {
		t.Fatalf("join=%d status=%v", join.Load(), statuses(result))
	}
}

// Verifies: GCWF-EPOCH-006, GCWF-EPOCH-008
// Depends-On: TestNodesDeduplicateAndCopyDependencies, TestSuccessResultHasTerminalTimes
func TestWideLayeredDagRunsEveryNodeOnce(t *testing.T) {
	s, w := newWorkflow(t)
	counts := make([]atomic.Int32, 13)
	addTask(t, w, "root", nil, func() { counts[0].Add(1) })
	for i := 1; i <= 8; i++ {
		idx := i
		name := string(rune('a' + i - 1))
		addTask(t, w, name, []string{"root"}, func() { counts[idx].Add(1) })
	}
	addTask(t, w, "j1", []string{"a", "b", "c", "d"}, func() { counts[9].Add(1) })
	addTask(t, w, "j2", []string{"e", "f", "g", "h"}, func() { counts[10].Add(1) })
	addTask(t, w, "merge", []string{"j1", "j2"}, func() { counts[11].Add(1) })
	addTask(t, w, "final", []string{"merge"}, func() { counts[12].Add(1) })
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if err != nil || len(result.Nodes) != 13 {
		t.Fatalf("nodes=%d error=%v status=%v", len(result.Nodes), err, statuses(result))
	}
	for i := range counts {
		if counts[i].Load() != 1 {
			t.Fatalf("node %d calls=%d", i, counts[i].Load())
		}
	}
}

// Verifies: GCWF-LIFE-002, GCWF-RESULT-010
// Depends-On: TestRunCancelReachesContextTask, TestWorkflowShutdownIsIdempotent
func TestShutdownCancelsActiveEpochBeforeRemovingJobs(t *testing.T) {
	s, w := newWorkflow(t)
	started := make(chan struct{})
	addTask(t, w, "node", nil, func(ctx context.Context) error { close(started); <-ctx.Done(); return ctx.Err() })
	s.Start()
	run, _ := w.RunNow(context.Background())
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("task did not start")
	}
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	if err := w.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
	result, err := waitRun(t, run)
	if !errors.Is(err, context.Canceled) || result.Nodes["node"].Status != gocron.WorkflowNodeCanceled || len(s.Jobs()) != 0 {
		t.Fatalf("status=%v wait=%v jobs=%d", statuses(result), err, len(s.Jobs()))
	}
}
