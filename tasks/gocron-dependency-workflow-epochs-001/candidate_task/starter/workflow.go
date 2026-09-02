package gocron

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
)

var (
	ErrWorkflowNameRequired       = errors.New("gocron: workflow name is required")
	ErrWorkflowSchedulerRequired  = errors.New("gocron: workflow scheduler is required")
	ErrWorkflowNodeNameRequired   = errors.New("gocron: workflow node name is required")
	ErrWorkflowNodeExists         = errors.New("gocron: workflow node already exists")
	ErrWorkflowNodeNotFound       = errors.New("gocron: workflow node not found")
	ErrWorkflowDependencyNotFound = errors.New("gocron: workflow dependency not found")
	ErrWorkflowCycle              = errors.New("gocron: workflow dependency cycle")
	ErrWorkflowNodeHasDependents  = errors.New("gocron: workflow node has dependents")
	ErrWorkflowEmpty              = errors.New("gocron: workflow has no nodes")
	ErrWorkflowBusy               = errors.New("gocron: workflow has an active epoch")
	ErrWorkflowClosed             = errors.New("gocron: workflow is closed")
	ErrWorkflowSchedulerStopped   = errors.New("gocron: workflow scheduler is not running")
	ErrWorkflowFailed             = errors.New("gocron: workflow epoch failed")
	ErrWorkflowDependencyFailed   = errors.New("gocron: workflow node blocked by a failed dependency")
)

type WorkflowNodeStatus string

const (
	WorkflowNodePending   WorkflowNodeStatus = "pending"
	WorkflowNodeRunning   WorkflowNodeStatus = "running"
	WorkflowNodeSucceeded WorkflowNodeStatus = "succeeded"
	WorkflowNodeFailed    WorkflowNodeStatus = "failed"
	WorkflowNodeBlocked   WorkflowNodeStatus = "blocked"
	WorkflowNodeCanceled  WorkflowNodeStatus = "canceled"
)

type WorkflowNode struct {
	Name         string
	Dependencies []string
	Job          Job
}

type WorkflowNodeResult struct {
	Name        string
	JobID       uuid.UUID
	Status      WorkflowNodeStatus
	StartedAt   time.Time
	CompletedAt time.Time
	Err         error
}

type WorkflowResult struct {
	Epoch       uint64
	StartedAt   time.Time
	CompletedAt time.Time
	Nodes       map[string]WorkflowNodeResult
}

type WorkflowRun interface {
	Epoch() uint64
	Wait(context.Context) (WorkflowResult, error)
	Cancel()
	Snapshot() WorkflowResult
}

type Workflow interface {
	Name() string
	Add(string, Task, []string, ...JobOption) (Job, error)
	Update(string, Task, []string, ...JobOption) (Job, error)
	Remove(string) error
	Nodes() []WorkflowNode
	RunNow(context.Context) (WorkflowRun, error)
	Stop(context.Context) error
	Shutdown(context.Context) error
}

func NewWorkflow(s Scheduler, name string) (Workflow, error) {
	return &workflowStub{scheduler: s, name: name, jobs: make(map[string]Job)}, nil
}

type workflowStub struct {
	mu        sync.Mutex
	scheduler Scheduler
	name      string
	jobs      map[string]Job
	epoch     atomic.Uint64
}

func (w *workflowStub) Name() string { return w.name }
func (w *workflowStub) Add(name string, task Task, _ []string, options ...JobOption) (Job, error) {
	job, err := w.scheduler.NewJob(DurationJob(time.Hour), task, options...)
	if err == nil {
		w.mu.Lock()
		w.jobs[name] = job
		w.mu.Unlock()
	}
	return job, err
}
func (w *workflowStub) Update(name string, task Task, deps []string, options ...JobOption) (Job, error) {
	w.mu.Lock()
	job := w.jobs[name]
	w.mu.Unlock()
	if job == nil {
		return w.Add(name, task, deps, options...)
	}
	updated, err := w.scheduler.Update(job.ID(), DurationJob(time.Hour), task, options...)
	if err == nil {
		w.mu.Lock()
		w.jobs[name] = updated
		w.mu.Unlock()
	}
	return updated, err
}
func (w *workflowStub) Remove(name string) error {
	w.mu.Lock()
	job := w.jobs[name]
	delete(w.jobs, name)
	w.mu.Unlock()
	if job == nil {
		return nil
	}
	return w.scheduler.RemoveJob(job.ID())
}
func (w *workflowStub) Nodes() []WorkflowNode {
	w.mu.Lock()
	defer w.mu.Unlock()
	out := make([]WorkflowNode, 0, len(w.jobs))
	for name, job := range w.jobs {
		out = append(out, WorkflowNode{Name: name, Job: job})
	}
	return out
}
func (w *workflowStub) RunNow(context.Context) (WorkflowRun, error) {
	epoch := w.epoch.Add(1)
	result := WorkflowResult{Epoch: epoch, StartedAt: time.Now(), CompletedAt: time.Now(), Nodes: map[string]WorkflowNodeResult{}}
	return &workflowRunStub{epoch: epoch, result: result}, nil
}
func (*workflowStub) Stop(context.Context) error { return nil }
func (w *workflowStub) Shutdown(context.Context) error {
	w.mu.Lock()
	jobs := make([]Job, 0, len(w.jobs))
	for _, job := range w.jobs {
		jobs = append(jobs, job)
	}
	w.jobs = make(map[string]Job)
	w.mu.Unlock()
	for _, job := range jobs {
		_ = w.scheduler.RemoveJob(job.ID())
	}
	return nil
}

type workflowRunStub struct {
	epoch  uint64
	result WorkflowResult
}

func (r *workflowRunStub) Epoch() uint64            { return r.epoch }
func (*workflowRunStub) Cancel()                    {}
func (r *workflowRunStub) Snapshot() WorkflowResult { return r.result }
func (r *workflowRunStub) Wait(context.Context) (WorkflowResult, error) {
	return r.result, nil
}
