package atomic_test

import (
	"context"
	"errors"
	"reflect"
	"sort"
	"sync/atomic"
	"testing"
	"time"

	"github.com/go-co-op/gocron/v2"
	"github.com/google/uuid"
)

const testTimeout = 3 * time.Second

func newWorkflow(t *testing.T, name string) (gocron.Scheduler, gocron.Workflow) {
	t.Helper()
	s, err := gocron.NewScheduler()
	if err != nil {
		t.Fatal(err)
	}
	w, err := gocron.NewWorkflow(s, name)
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

func containsJob(s gocron.Scheduler, id uuid.UUID) bool {
	for _, job := range s.Jobs() {
		if job.ID() == id {
			return true
		}
	}
	return false
}

// Verifies: GCWF-GRAPH-001
func TestNewWorkflowRejectsNilScheduler(t *testing.T) {
	_, err := gocron.NewWorkflow(nil, "flow")
	if !errors.Is(err, gocron.ErrWorkflowSchedulerRequired) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-002
func TestNewWorkflowRejectsEmptyName(t *testing.T) {
	s, err := gocron.NewScheduler()
	if err != nil {
		t.Fatal(err)
	}
	defer s.Shutdown()
	_, err = gocron.NewWorkflow(s, "")
	if !errors.Is(err, gocron.ErrWorkflowNameRequired) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-003
func TestWorkflowNameRoundTrips(t *testing.T) {
	_, w := newWorkflow(t, "nightly-release")
	if w.Name() != "nightly-release" {
		t.Fatalf("name = %q", w.Name())
	}
}

// Verifies: GCWF-GRAPH-004
func TestAddRejectsEmptyNodeName(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, err := w.Add("", gocron.NewTask(func() {}), nil)
	if !errors.Is(err, gocron.ErrWorkflowNodeNameRequired) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-006
func TestAddRejectsUnknownDependency(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, err := w.Add("child", gocron.NewTask(func() {}), []string{"missing"})
	if !errors.Is(err, gocron.ErrWorkflowDependencyNotFound) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-005
func TestAddRejectsDuplicateNode(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	if _, err := w.Add("node", gocron.NewTask(func() {}), nil); err != nil {
		t.Fatal(err)
	}
	_, err := w.Add("node", gocron.NewTask(func() {}), nil)
	if !errors.Is(err, gocron.ErrWorkflowNodeExists) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-008
func TestAddRejectsSelfDependency(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, err := w.Add("node", gocron.NewTask(func() {}), []string{"node"})
	if !errors.Is(err, gocron.ErrWorkflowCycle) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-010
func TestNodesAreSortedByName(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	for _, name := range []string{"zeta", "alpha", "middle"} {
		if _, err := w.Add(name, gocron.NewTask(func() {}), nil); err != nil {
			t.Fatal(err)
		}
	}
	got := []string{}
	for _, node := range w.Nodes() {
		got = append(got, node.Name)
	}
	if !reflect.DeepEqual(got, []string{"alpha", "middle", "zeta"}) {
		t.Fatalf("nodes = %v", got)
	}
}

// Verifies: GCWF-GRAPH-007, GCWF-GRAPH-011
func TestNodesDeduplicateAndCopyDependencies(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, _ = w.Add("a", gocron.NewTask(func() {}), nil)
	_, _ = w.Add("b", gocron.NewTask(func() {}), nil)
	_, err := w.Add("join", gocron.NewTask(func() {}), []string{"b", "a", "b"})
	if err != nil {
		t.Fatal(err)
	}
	nodes := w.Nodes()
	var deps []string
	for _, node := range nodes {
		if node.Name == "join" {
			deps = node.Dependencies
		}
	}
	if !reflect.DeepEqual(deps, []string{"a", "b"}) {
		t.Fatalf("dependencies = %v", deps)
	}
	deps[0] = "corrupt"
	for _, node := range w.Nodes() {
		if node.Name == "join" && node.Dependencies[0] != "a" {
			t.Fatalf("dependencies aliased: %v", node.Dependencies)
		}
	}
}

// Verifies: GCWF-SCHED-001
func TestAddedJobVisibleInScheduler(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	job, err := w.Add("node", gocron.NewTask(func() {}), nil)
	if err != nil {
		t.Fatal(err)
	}
	if !containsJob(s, job.ID()) {
		t.Fatalf("job %s not visible", job.ID())
	}
}

// Verifies: GCWF-GRAPH-006
func TestUpdateRejectsMissingNode(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, err := w.Update("missing", gocron.NewTask(func() {}), nil)
	if !errors.Is(err, gocron.ErrWorkflowNodeNotFound) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-012
func TestUpdatePreservesJobID(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	before, _ := w.Add("node", gocron.NewTask(func() {}), nil)
	after, err := w.Update("node", gocron.NewTask(func() {}), nil)
	if err != nil {
		t.Fatal(err)
	}
	if before.ID() != after.ID() {
		t.Fatalf("ids differ: %s %s", before.ID(), after.ID())
	}
}

// Verifies: GCWF-GRAPH-006, GCWF-GRAPH-009
func TestRejectedUpdatePreservesDependencies(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, _ = w.Add("root", gocron.NewTask(func() {}), nil)
	job, _ := w.Add("child", gocron.NewTask(func() {}), []string{"root"})
	_, err := w.Update("child", gocron.NewTask(func() {}), []string{"missing"})
	if !errors.Is(err, gocron.ErrWorkflowDependencyNotFound) {
		t.Fatalf("error = %v", err)
	}
	nodes := w.Nodes()
	for _, node := range nodes {
		if node.Name == "child" {
			if node.Job.ID() != job.ID() || !reflect.DeepEqual(node.Dependencies, []string{"root"}) {
				t.Fatalf("child changed: %#v", node)
			}
		}
	}
}

// Verifies: GCWF-GRAPH-008, GCWF-GRAPH-009
func TestUpdateRejectsTransitiveCycle(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, _ = w.Add("a", gocron.NewTask(func() {}), nil)
	_, _ = w.Add("b", gocron.NewTask(func() {}), []string{"a"})
	_, _ = w.Add("c", gocron.NewTask(func() {}), []string{"b"})
	_, err := w.Update("a", gocron.NewTask(func() {}), []string{"c"})
	if !errors.Is(err, gocron.ErrWorkflowCycle) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-014
func TestRemoveRejectsMissingNode(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	if err := w.Remove("missing"); !errors.Is(err, gocron.ErrWorkflowNodeNotFound) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-013
func TestRemoveRejectsNodeWithDependent(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, _ = w.Add("root", gocron.NewTask(func() {}), nil)
	_, _ = w.Add("child", gocron.NewTask(func() {}), []string{"root"})
	if err := w.Remove("root"); !errors.Is(err, gocron.ErrWorkflowNodeHasDependents) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-014
func TestRemoveLeafDeletesSchedulerJob(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	job, _ := w.Add("leaf", gocron.NewTask(func() {}), nil)
	if err := w.Remove("leaf"); err != nil {
		t.Fatal(err)
	}
	if containsJob(s, job.ID()) || len(w.Nodes()) != 0 {
		t.Fatalf("leaf still present")
	}
}

// Verifies: GCWF-EPOCH-001
func TestRunNowRejectsEmptyWorkflow(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	s.Start()
	_, err := w.RunNow(context.Background())
	if !errors.Is(err, gocron.ErrWorkflowEmpty) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-EPOCH-002
func TestRunNowRejectsStoppedScheduler(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, _ = w.Add("node", gocron.NewTask(func() {}), nil)
	_, err := w.RunNow(context.Background())
	if !errors.Is(err, gocron.ErrWorkflowSchedulerStopped) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-EPOCH-003
func TestRunNowReturnsBeforeTaskCompletes(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	release := make(chan struct{})
	_, _ = w.Add("node", gocron.NewTask(func() { <-release }), nil)
	s.Start()
	start := time.Now()
	run, err := w.RunNow(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if time.Since(start) > 300*time.Millisecond {
		t.Fatalf("RunNow blocked")
	}
	close(release)
	if _, err := waitRun(t, run); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GCWF-EPOCH-004
func TestEpochIDsIncrease(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	_, _ = w.Add("node", gocron.NewTask(func() {}), nil)
	s.Start()
	first, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, first)
	second, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, second)
	if first.Epoch() == 0 || second.Epoch() <= first.Epoch() {
		t.Fatalf("epochs = %d, %d", first.Epoch(), second.Epoch())
	}
}

// Verifies: GCWF-RESULT-001
func TestSnapshotReturnsCopiedMap(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	_, _ = w.Add("node", gocron.NewTask(func() {}), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	_, _ = waitRun(t, run)
	first := run.Snapshot()
	delete(first.Nodes, "node")
	if _, ok := run.Snapshot().Nodes["node"]; !ok {
		t.Fatalf("snapshot map aliased")
	}
}

// Verifies: GCWF-RESULT-002
func TestWaitDeadlineDoesNotCancelEpoch(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	release := make(chan struct{})
	_, _ = w.Add("node", gocron.NewTask(func() { <-release }), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if _, err := run.Wait(ctx); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("wait error = %v", err)
	}
	close(release)
	result, err := waitRun(t, run)
	if err != nil || result.Nodes["node"].Status != gocron.WorkflowNodeSucceeded {
		t.Fatalf("terminal = %s, %v", result.Nodes["node"].Status, err)
	}
}

// Verifies: GCWF-RESULT-009, GCWF-EPOCH-010
func TestRunCancelReachesContextTask(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	started := make(chan struct{})
	_, _ = w.Add("node", gocron.NewTask(func(ctx context.Context) error {
		close(started)
		<-ctx.Done()
		return ctx.Err()
	}), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("task did not start")
	}
	run.Cancel()
	result, err := waitRun(t, run)
	if !errors.Is(err, context.Canceled) || result.Nodes["node"].Status != gocron.WorkflowNodeCanceled {
		t.Fatalf("terminal = %s, %v", result.Nodes["node"].Status, err)
	}
}

// Verifies: GCWF-EPOCH-010
func TestEpochContextReplacesTaskContext(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	type key string
	original := context.WithValue(context.Background(), key("source"), "original")
	epoch := context.WithValue(context.Background(), key("source"), "epoch")
	seen := make(chan any, 1)
	_, _ = w.Add("node", gocron.NewTask(func(ctx context.Context) { seen <- ctx.Value(key("source")) }, original), nil)
	s.Start()
	run, _ := w.RunNow(epoch)
	if _, err := waitRun(t, run); err != nil {
		t.Fatal(err)
	}
	select {
	case value := <-seen:
		if value != "epoch" {
			t.Fatalf("context value = %v", value)
		}
	case <-time.After(testTimeout):
		t.Fatal("context task did not report")
	}
}

// Verifies: GCWF-EPOCH-011
func TestTaskParametersArePreserved(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	seen := make(chan string, 1)
	_, _ = w.Add("node", gocron.NewTask(func(prefix string, n int) { seen <- prefix + string(rune('0'+n)) }, "v", 2), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	if _, err := waitRun(t, run); err != nil {
		t.Fatal(err)
	}
	select {
	case value := <-seen:
		if value != "v2" {
			t.Fatalf("value = %q", value)
		}
	case <-time.After(testTimeout):
		t.Fatal("parameter task did not report")
	}
}

// Verifies: GCWF-RESULT-005
func TestTaskErrorProducesFailedResult(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	boom := errors.New("boom")
	_, _ = w.Add("node", gocron.NewTask(func() error { return boom }), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if !errors.Is(err, gocron.ErrWorkflowFailed) || !errors.Is(result.Nodes["node"].Err, boom) {
		t.Fatalf("result error = %v, wait = %v", result.Nodes["node"].Err, err)
	}
}

// Verifies: GCWF-RESULT-006
func TestTaskPanicProducesFailedResult(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	_, _ = w.Add("node", gocron.NewTask(func() { panic("boom") }), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if !errors.Is(err, gocron.ErrWorkflowFailed) || !errors.Is(result.Nodes["node"].Err, gocron.ErrPanicRecovered) {
		t.Fatalf("result error = %v, wait = %v", result.Nodes["node"].Err, err)
	}
}

// Verifies: GCWF-RESULT-004
func TestSuccessResultHasTerminalTimes(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	_, _ = w.Add("node", gocron.NewTask(func() {}), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	result, err := waitRun(t, run)
	if err != nil {
		t.Fatal(err)
	}
	node := result.Nodes["node"]
	if node.Status != gocron.WorkflowNodeSucceeded || node.StartedAt.IsZero() || node.CompletedAt.IsZero() || result.CompletedAt.IsZero() {
		t.Fatalf("result = %#v", result)
	}
}

// Verifies: GCWF-RESULT-010
func TestStopWithNoActiveEpochIsNoop(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	if err := w.Stop(ctx); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GCWF-LIFE-001
func TestWorkflowShutdownIsIdempotent(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	if err := w.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
	if err := w.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}
}

// Verifies: GCWF-LIFE-004
func TestAddAfterShutdownReturnsClosed(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	_ = w.Shutdown(ctx)
	_, err := w.Add("node", gocron.NewTask(func() {}), nil)
	if !errors.Is(err, gocron.ErrWorkflowClosed) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-LIFE-004
func TestRunAfterShutdownReturnsClosed(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	_, _ = w.Add("node", gocron.NewTask(func() {}), nil)
	s.Start()
	ctx, cancel := context.WithTimeout(context.Background(), testTimeout)
	defer cancel()
	_ = w.Shutdown(ctx)
	_, err := w.RunNow(context.Background())
	if !errors.Is(err, gocron.ErrWorkflowClosed) {
		t.Fatalf("error = %v", err)
	}
}

// Verifies: GCWF-GRAPH-015
func TestMutationDuringActiveEpochReturnsBusy(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	started := make(chan struct{})
	release := make(chan struct{})
	_, _ = w.Add("node", gocron.NewTask(func() { close(started); <-release }), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	select {
	case <-started:
	case <-time.After(testTimeout):
		t.Fatal("task did not start")
	}
	_, addErr := w.Add("other", gocron.NewTask(func() {}), nil)
	_, updateErr := w.Update("node", gocron.NewTask(func() {}), nil)
	removeErr := w.Remove("node")
	if !errors.Is(addErr, gocron.ErrWorkflowBusy) || !errors.Is(updateErr, gocron.ErrWorkflowBusy) || !errors.Is(removeErr, gocron.ErrWorkflowBusy) {
		t.Fatalf("errors = %v, %v, %v", addErr, updateErr, removeErr)
	}
	close(release)
	_, _ = waitRun(t, run)
}

// Verifies: GCWF-RESULT-003
func TestRepeatedWaitReturnsEquivalentResult(t *testing.T) {
	s, w := newWorkflow(t, "flow")
	var calls atomic.Int32
	_, _ = w.Add("node", gocron.NewTask(func() { calls.Add(1) }), nil)
	s.Start()
	run, _ := w.RunNow(context.Background())
	first, firstErr := waitRun(t, run)
	second, secondErr := waitRun(t, run)
	if firstErr != nil || secondErr != nil || calls.Load() != 1 || !reflect.DeepEqual(first, second) {
		t.Fatalf("first=%#v second=%#v calls=%d errors=%v/%v", first, second, calls.Load(), firstErr, secondErr)
	}
}

// Verifies: GCWF-GRAPH-010
func TestNodesRemainSortedAfterUpdate(t *testing.T) {
	_, w := newWorkflow(t, "flow")
	_, _ = w.Add("a", gocron.NewTask(func() {}), nil)
	_, _ = w.Add("c", gocron.NewTask(func() {}), nil)
	_, _ = w.Add("b", gocron.NewTask(func() {}), nil)
	_, _ = w.Update("b", gocron.NewTask(func() {}), []string{"a"})
	names := make([]string, 0, 3)
	for _, node := range w.Nodes() {
		names = append(names, node.Name)
	}
	if !sort.StringsAreSorted(names) {
		t.Fatalf("names = %v", names)
	}
}
