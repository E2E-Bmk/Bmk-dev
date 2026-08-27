package task_oracle_test

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	task "github.com/go-task/task/v3"
	"github.com/go-task/task/v3/taskfile/ast"
)

type taskHarness struct {
	dir    string
	out    *bytes.Buffer
	errOut *bytes.Buffer
	exec   *task.Executor
}

func writeTaskFile(t *testing.T, root, name, body string) {
	t.Helper()
	path := filepath.Join(root, filepath.FromSlash(name))
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(strings.TrimSpace(body)+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func readTaskFile(t *testing.T, root, name string) string {
	t.Helper()
	data, err := os.ReadFile(filepath.Join(root, filepath.FromSlash(name)))
	if err != nil {
		t.Fatal(err)
	}
	return strings.ReplaceAll(string(data), "\r\n", "\n")
}

func newTaskHarness(t *testing.T, dir string, extra ...task.ExecutorOption) *taskHarness {
	t.Helper()
	out, errOut := &bytes.Buffer{}, &bytes.Buffer{}
	options := []task.ExecutorOption{
		task.WithDir(dir),
		task.WithEntrypoint(filepath.Join(dir, "Taskfile.yml")),
		task.WithTempDir(task.TempDir{
			Remote:      filepath.Join(dir, ".task-cache", "remote"),
			Fingerprint: filepath.Join(dir, ".task-cache", "fingerprint"),
		}),
		task.WithOffline(true),
		task.WithVersionCheck(false),
		task.WithStdin(strings.NewReader("")),
		task.WithStdout(out),
		task.WithStderr(errOut),
	}
	options = append(options, extra...)
	return &taskHarness{dir: dir, out: out, errOut: errOut, exec: task.NewExecutor(options...)}
}

func selectPlan(t *testing.T, name string, variables map[string]string, observations ...string) task.ReceiptPlan {
	t.Helper()
	plan, err := task.NewReceiptPlan().Select(task.TaskSelection{Name: name, Variables: variables})
	if err != nil {
		t.Fatal(err)
	}
	for index := 0; index+1 < len(observations); index += 2 {
		plan, err = plan.ObserveWorkspace(observations[index], observations[index+1])
		if err != nil {
			t.Fatal(err)
		}
	}
	plan, err = plan.ObserveStatus("terminal-observation")
	if err != nil {
		t.Fatal(err)
	}
	return plan
}

func captureTask(t *testing.T, harness *taskHarness, plan task.ReceiptPlan) (task.RunReceipt, error) {
	t.Helper()
	receipt, err := task.CaptureRun(context.Background(), harness.exec, plan)
	if validationErr := receipt.Validate(); validationErr != nil {
		t.Fatalf("invalid public receipt: %v (run error %v)", validationErr, err)
	}
	if receipt.Digest() == "" {
		t.Fatal("valid receipt has an empty digest")
	}
	return receipt, err
}

func eventValues(receipt task.RunReceipt, kind string) []string {
	var result []string
	for _, event := range receipt.Events {
		if event.Kind == kind {
			result = append(result, event.Task+"|"+event.Value+"|"+event.Outcome)
		}
	}
	return result
}

func requireIncludeNamespace(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
includes:
  ns:
    taskfile: ./sub/Taskfile.yml
    dir: ./sub
  flat:
    taskfile: ./flat/Taskfile.yml
    dir: ./flat
    flatten: true
  optional:
    taskfile: ./missing.yml
    optional: true
tasks:
  root:
    deps: [ns:emit, flat_emit]
    cmds:
      - echo root > root.txt
`)
	writeTaskFile(t, dir, "sub/Taskfile.yml", `
version: '3'
tasks:
  emit:
    cmds:
      - echo included > included.txt
`)
	writeTaskFile(t, dir, "flat/Taskfile.yml", `
version: '3'
tasks:
  flat_emit:
    cmds:
      - echo flat > flat.txt
`)
	h := newTaskHarness(t, dir)
	plan := selectPlan(t, "root", nil, "root-output", "root.txt", "included-output", "sub/included.txt", "flat-output", "flat/flat.txt")
	receipt, err := captureTask(t, h, plan)
	if err != nil || receipt.Status != task.ReceiptCompleted {
		t.Fatalf("included graph did not complete: status=%v err=%v", receipt.Status, err)
	}
	if receipt.Task != "root" || receipt.Workspace["included-output"] == "missing" || receipt.Workspace["flat-output"] == "missing" {
		t.Fatalf("receipt lost included identity or effects: %#v", receipt)
	}
	joined := strings.Join(eventValues(receipt, "task"), "\n")
	if !strings.Contains(joined, "ns:emit|sub|") || !strings.Contains(joined, "flat_emit|flat|") {
		t.Fatalf("namespaces or included directories absent from receipt: %s", joined)
	}
	if _, err := task.NewReceiptPlan().ObserveWorkspace("escape", "../outside"); err == nil {
		t.Fatal("plan accepted a workspace escape")
	}
	if _, err := task.NewReceiptPlan().Select(task.TaskSelection{Name: "-invalid"}); err == nil {
		t.Fatal("plan accepted an option-like task name")
	}

	collision := t.TempDir()
	writeTaskFile(t, collision, "Taskfile.yml", `
version: '3'
includes:
  left: {taskfile: ./left.yml, flatten: true}
  right: {taskfile: ./right.yml, flatten: true}
`)
	writeTaskFile(t, collision, "left.yml", "version: '3'\ntasks:\n  same:\n    cmds: [echo left]\n")
	writeTaskFile(t, collision, "right.yml", "version: '3'\ntasks:\n  same:\n    cmds: [echo right]\n")
	if setupErr := newTaskHarness(t, collision).exec.Setup(); setupErr == nil {
		t.Fatal("flatten collision was not rejected")
	}
}

func requireVariableLineage(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
vars:
  VALUE: root-default
  DYNAMIC:
    sh: 'echo dynamic'
includes:
  ns:
    taskfile: ./sub/Taskfile.yml
    dir: ./sub
    vars:
      INCLUDED: include-frame
tasks:
  dependency:
    cmds:
      - echo "{{.DEP}}" > dependency.txt
  root:
    deps:
      - task: dependency
        vars:
          DEP: '{{.DYNAMIC}}'
      - ns:included
    cmds:
      - echo "{{.VALUE}}-{{.DYNAMIC}}" > value.txt
`)
	writeTaskFile(t, dir, "sub/Taskfile.yml", `
version: '3'
tasks:
  included:
    cmds:
      - 'echo {{.INCLUDED}} > included-variable.txt'
`)
	h := newTaskHarness(t, dir)
	base := selectPlan(t, "root", map[string]string{"VALUE": "selection"}, "value", "value.txt", "dependency", "dependency.txt", "included", "sub/included-variable.txt")
	overridden, err := base.WithVariables(map[string]string{"VALUE": "plan"})
	if err != nil {
		t.Fatal(err)
	}
	receipt, runErr := captureTask(t, h, overridden)
	if runErr != nil || receipt.Status != task.ReceiptCompleted {
		t.Fatalf("variable workflow failed: %v %#v", runErr, receipt)
	}
	if got := strings.TrimSpace(readTaskFile(t, dir, "value.txt")); got != "plan-dynamic" {
		t.Fatalf("wrong variable precedence: %q", got)
	}
	if got := strings.TrimSpace(readTaskFile(t, dir, "dependency.txt")); got != "dynamic" {
		t.Fatalf("dynamic dependency frame lost: %q", got)
	}
	if got := strings.TrimSpace(readTaskFile(t, dir, "sub/included-variable.txt")); got != "include-frame" || receipt.Workspace["included"] == "missing" {
		t.Fatalf("include variable frame or directory lost: %q %#v", got, receipt.Workspace)
	}
	if receipt.Variables["VALUE"] != "plan" || receipt.Variables["DYNAMIC"] != "dynamic" {
		t.Fatalf("receipt variable lineage incomplete: %#v", receipt.Variables)
	}
	if _, err := base.WithVariables(map[string]string{"BAD-NAME": "x"}); err == nil {
		t.Fatal("invalid variable name accepted")
	}
	secondDir := t.TempDir()
	writeTaskFile(t, secondDir, "Taskfile.yml", `
version: '3'
tasks:
  root:
    cmds:
      - 'echo {{.VALUE}} > value.txt'
`)
	baseReceipt, baseErr := captureTask(t, newTaskHarness(t, secondDir), base)
	if baseErr != nil || baseReceipt.Variables["VALUE"] != "selection" {
		t.Fatalf("immutable base plan was mutated: err=%v vars=%#v", baseErr, baseReceipt.Variables)
	}
}

func requireDependencyScheduling(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
tasks:
  shared:
    run: once
    cmds: [echo shared >> order.txt]
  left:
    deps: [shared]
    cmds: [echo left >> order.txt]
  right:
    deps: [shared]
    cmds: [echo right >> order.txt]
  worker:
    cmds:
      - 'echo {{.ITEM}} >> workers.txt'
  root:
    deps: [right, left]
    cmds:
      - task: worker
        vars:
          ITEM: one
      - task: worker
        vars:
          ITEM: two
      - echo root >> order.txt
  current-dependency:
    status: [test -f current.ok]
    cmds: [echo current >> status-order.txt]
  status-parent:
    deps: [current-dependency]
    cmds: [echo parent >> status-order.txt]
`)
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "order", "order.txt", "workers", "workers.txt"))
	if err != nil || receipt.Status != task.ReceiptCompleted {
		t.Fatalf("dependency graph failed: %v %#v", err, receipt)
	}
	orderText := strings.TrimSpace(readTaskFile(t, dir, "order.txt"))
	if strings.Count(orderText, "shared") != 1 || strings.Count(orderText, "left") != 1 || strings.Count(orderText, "right") != 1 || strings.Count(orderText, "root") != 1 || !strings.HasSuffix(orderText, "root") {
		t.Fatalf("dependency effects were duplicated or parent ran early: %q", orderText)
	}
	workers := strings.Fields(readTaskFile(t, dir, "workers.txt"))
	if len(workers) != 2 || workers[0] != "one" || workers[1] != "two" {
		t.Fatalf("task-call variable frames collapsed: %#v", workers)
	}
	dependencies := strings.Join(eventValues(receipt, "dependency"), "\n")
	if strings.Index(dependencies, "left|") > strings.Index(dependencies, "right|") || strings.Count(strings.Join(eventValues(receipt, "task"), "\n"), "shared|") != 1 {
		t.Fatalf("receipt graph ordering or de-duplication wrong: %s", dependencies)
	}

	cycle := t.TempDir()
	writeTaskFile(t, cycle, "Taskfile.yml", "version: '3'\ntasks:\n  a:\n    deps: [b]\n  b:\n    deps: [a]\n")
	plan := selectPlan(t, "a", nil)
	if _, cycleErr := task.CaptureRun(context.Background(), newTaskHarness(t, cycle).exec, plan); cycleErr == nil {
		t.Fatal("dependency cycle accepted")
	}
	writeTaskFile(t, dir, "current.ok", "current\n")
	statusPlan := selectPlan(t, "status-parent", nil, "status-order", "status-order.txt")
	if _, statusErr := captureTask(t, newTaskHarness(t, dir), statusPlan); statusErr != nil {
		t.Fatal(statusErr)
	}
	if got := strings.Fields(readTaskFile(t, dir, "status-order.txt")); len(got) != 1 || got[0] != "parent" {
		t.Fatalf("current dependency was not skipped: %#v", got)
	}
	if err := os.Remove(filepath.Join(dir, "current.ok")); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(filepath.Join(dir, "status-order.txt")); err != nil {
		t.Fatal(err)
	}
	if _, statusErr := captureTask(t, newTaskHarness(t, dir), statusPlan); statusErr != nil {
		t.Fatal(statusErr)
	}
	if got := strings.Fields(readTaskFile(t, dir, "status-order.txt")); len(got) != 2 || got[0] != "current" || got[1] != "parent" {
		t.Fatalf("stale dependency did not precede parent: %#v", got)
	}
}

func requireDeferFailure(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
tasks:
  fail:
    cmds:
      - defer: echo first >> cleanup.txt
      - defer: echo second >> cleanup.txt
      - false
  ignored:
    cmds:
      - cmd: false
        ignore_error: true
      - echo continued > continued.txt
  deferred-fail:
    cmds:
      - defer: false
      - echo ran > ran.txt
`)
	failure, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "fail", nil, "cleanup", "cleanup.txt"))
	if err == nil || failure.Status != task.ReceiptFailedCommand || strings.Fields(readTaskFile(t, dir, "cleanup.txt"))[0] != "second" {
		t.Fatalf("failure/defer contract wrong: status=%v err=%v", failure.Status, err)
	}
	defers := eventValues(failure, "defer")
	if len(defers) != 2 || !strings.Contains(defers[0], "second") || !strings.Contains(defers[1], "first") {
		t.Fatalf("defer receipt not reverse order: %#v", defers)
	}
	commands := strings.Join(eventValues(failure, "command"), "\n")
	if !strings.Contains(commands, "|false|failed") || failure.Fingerprint != "" {
		t.Fatalf("failed command status was not preserved: %s %#v", commands, failure)
	}
	ignored, ignoredErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "ignored", nil, "continued", "continued.txt"))
	if ignoredErr != nil || ignored.Status != task.ReceiptCompleted || !strings.Contains(strings.Join(eventValues(ignored, "command"), "\n"), "|false|ignored") {
		t.Fatalf("ignore-error boundary lost: %v %#v", ignoredErr, ignored)
	}
	deferred, deferredErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "deferred-fail", nil, "ran", "ran.txt"))
	if deferredErr != nil || deferred.Status != task.ReceiptFailedDeferred || !strings.Contains(strings.Join(eventValues(deferred, "defer"), "\n"), "|false|failed") || deferred.Fingerprint != "" {
		t.Fatalf("deferred failure classification wrong: %v %#v", deferredErr, deferred)
	}
}

func requireFingerprintCache(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "src.txt", "one\n")
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
tasks:
  build:
    method: checksum
    sources: [src.txt]
    generates: [out.txt]
    cmds:
      - echo run >> runs.txt
      - cp src.txt out.txt
  alternate:
    method: checksum
    sources: [src.txt]
    generates: [other.txt]
    cmds:
      - cp src.txt other.txt
`)
	plan := selectPlan(t, "build", nil, "source", "src.txt", "output", "out.txt", "runs", "runs.txt")
	first, firstErr := captureTask(t, newTaskHarness(t, dir), plan)
	second, secondErr := captureTask(t, newTaskHarness(t, dir), plan)
	third, thirdErr := captureTask(t, newTaskHarness(t, dir), plan)
	if firstErr != nil || secondErr != nil || thirdErr != nil || first.Status != task.ReceiptCompleted || second.Status != task.ReceiptSkippedCurrent || third.Status != task.ReceiptSkippedCurrent {
		t.Fatalf("cache lifecycle wrong: %v/%v/%v err=%v/%v/%v", first.Status, second.Status, third.Status, firstErr, secondErr, thirdErr)
	}
	if first.Fingerprint == "" || first.Fingerprint != second.Fingerprint || len(task.ReceiptDiff(second, third)) != 0 {
		t.Fatalf("stable last-good fingerprint or digest lost: %#v", task.ReceiptDiff(second, third))
	}
	writeTaskFile(t, dir, "unrelated.txt", "ignored\n")
	unrelated, unrelatedErr := captureTask(t, newTaskHarness(t, dir), plan)
	if unrelatedErr != nil || unrelated.Status != task.ReceiptSkippedCurrent || unrelated.Fingerprint != first.Fingerprint {
		t.Fatalf("unrelated edit invalidated cache: %v %#v", unrelatedErr, unrelated)
	}
	writeTaskFile(t, dir, "src.txt", "two\n")
	changed, changedErr := captureTask(t, newTaskHarness(t, dir), plan)
	if changedErr != nil || changed.Status != task.ReceiptCompleted || changed.Fingerprint == first.Fingerprint || !strings.Contains(strings.Join(task.ReceiptDiff(first, changed), ","), "fingerprint") {
		t.Fatalf("source edit did not invalidate fingerprint: %v %#v", changedErr, changed)
	}
	if strings.Count(readTaskFile(t, dir, "runs.txt"), "run") != 2 {
		t.Fatalf("cache executed wrong number of times: %q", readTaskFile(t, dir, "runs.txt"))
	}
	if err := os.Remove(filepath.Join(dir, "out.txt")); err != nil {
		t.Fatal(err)
	}
	missing, missingErr := captureTask(t, newTaskHarness(t, dir), plan)
	if missingErr != nil || missing.Status != task.ReceiptCompleted || missing.Workspace["output"] == "missing" {
		t.Fatalf("missing generated file did not force execution: %v %#v", missingErr, missing)
	}
	alternate, alternateErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "alternate", nil, "source", "src.txt", "output", "other.txt"))
	if alternateErr != nil || alternate.Status != task.ReceiptCompleted || alternate.Fingerprint == missing.Fingerprint {
		t.Fatalf("task identities share cache receipt: %v %#v", alternateErr, alternate)
	}

	timestampDir := t.TempDir()
	writeTaskFile(t, timestampDir, "source.txt", "source\n")
	writeTaskFile(t, timestampDir, "target.txt", "target\n")
	writeTaskFile(t, timestampDir, "Taskfile.yml", "version: '3'\ntasks:\n  stamp:\n    method: timestamp\n    sources: [source.txt]\n    generates: [target.txt]\n    cmds: [echo updated > target.txt]\n")
	old, recent := time.Now().Add(-2*time.Hour), time.Now().Add(-time.Hour)
	if err := os.Chtimes(filepath.Join(timestampDir, "source.txt"), old, old); err != nil {
		t.Fatal(err)
	}
	if err := os.Chtimes(filepath.Join(timestampDir, "target.txt"), recent, recent); err != nil {
		t.Fatal(err)
	}
	stampPlan := selectPlan(t, "stamp", nil, "target", "target.txt")
	current, currentErr := captureTask(t, newTaskHarness(t, timestampDir), stampPlan)
	if currentErr != nil || current.Status != task.ReceiptSkippedCurrent {
		t.Fatalf("timestamp current state wrong: %v %#v", currentErr, current)
	}
	if err := os.Remove(filepath.Join(timestampDir, "target.txt")); err != nil {
		t.Fatal(err)
	}
	stale, staleErr := captureTask(t, newTaskHarness(t, timestampDir), stampPlan)
	if staleErr != nil || stale.Status != task.ReceiptCompleted {
		t.Fatalf("timestamp missing target not stale: %v %#v", staleErr, stale)
	}
}

func requirePreconditionStatus(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "source\n")
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
tasks:
  guarded:
    preconditions:
      - sh: test -f allow.flag
    cmds: [echo allowed > allowed.txt]
  statused:
    method: checksum
    sources: [source.txt]
    generates: [status-output.txt]
    status: [test -f status.ok]
    cmds:
      - echo ran >> status-runs.txt
      - echo output > status-output.txt
`)
	blocked, blockedErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "guarded", nil, "allowed", "allowed.txt"))
	if !errors.Is(blockedErr, task.ErrPreconditionFailed) || blocked.Status != task.ReceiptFailedPrecondition || blocked.Workspace["allowed"] != "missing" || blocked.Fingerprint != "" {
		t.Fatalf("precondition failure crossed execution boundary: %v %#v", blockedErr, blocked)
	}
	writeTaskFile(t, dir, "allow.flag", "yes\n")
	allowed, allowedErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "guarded", nil, "allowed", "allowed.txt"))
	if allowedErr != nil || allowed.Status != task.ReceiptCompleted || allowed.Workspace["allowed"] == "missing" {
		t.Fatalf("passing precondition did not execute: %v %#v", allowedErr, allowed)
	}
	statusPlan := selectPlan(t, "statused", nil, "output", "status-output.txt", "status", "status.ok")
	first, firstErr := captureTask(t, newTaskHarness(t, dir), statusPlan)
	if firstErr != nil || first.Status != task.ReceiptCompleted {
		t.Fatalf("initial status run failed: %v %#v", firstErr, first)
	}
	writeTaskFile(t, dir, "status.ok", "ok\n")
	current, currentErr := captureTask(t, newTaskHarness(t, dir), statusPlan)
	if currentErr != nil || current.Status != task.ReceiptSkippedCurrent {
		t.Fatalf("status did not suppress current command: %v %#v", currentErr, current)
	}
	if err := os.Remove(filepath.Join(dir, "status.ok")); err != nil {
		t.Fatal(err)
	}
	stale, staleErr := captureTask(t, newTaskHarness(t, dir), statusPlan)
	if staleErr != nil || stale.Status != task.ReceiptCompleted || strings.Count(readTaskFile(t, dir, "status-runs.txt"), "ran") != 2 {
		t.Fatalf("failed status did not force command: %v %#v", staleErr, stale)
	}
}

func requireDryNoPublish(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
tasks:
  dep:
    cmds: [echo dependency > dep.txt]
  root:
    deps: [dep]
    cmds: [echo root > root.txt]
  guarded:
    cmds:
      - test ! -f fail.flag
      - echo success > guarded.txt
`)
	plan := selectPlan(t, "root", nil, "dep", "dep.txt", "root", "root.txt")
	dry, dryErr := captureTask(t, newTaskHarness(t, dir), plan.WithDryRun(true))
	if dryErr != nil || dry.Status != task.ReceiptRenderedDry || dry.Workspace["dep"] != "missing" || dry.Workspace["root"] != "missing" || dry.Fingerprint != "" {
		t.Fatalf("dry run executed or published: %v %#v", dryErr, dry)
	}
	for _, event := range dry.Events {
		if event.Kind != "status" && event.Outcome != "planned" {
			t.Fatalf("dry event was not planned: %#v", event)
		}
	}
	normal, normalErr := captureTask(t, newTaskHarness(t, dir), plan)
	if normalErr != nil || normal.Status != task.ReceiptCompleted || normal.Workspace["dep"] == "missing" || normal.Workspace["root"] == "missing" || normal.Fingerprint == "" {
		t.Fatalf("normal run failed after dry: %v %#v", normalErr, normal)
	}
	dryAgain, dryAgainErr := captureTask(t, newTaskHarness(t, dir), plan.WithDryRun(true))
	if dryAgainErr != nil || dryAgain.Status != task.ReceiptRenderedDry || dryAgain.Fingerprint != normal.Fingerprint || readTaskFile(t, dir, "root.txt") != "root\n" {
		t.Fatalf("dry run changed last-good state: %v %#v", dryAgainErr, dryAgain)
	}
	guardPlan := selectPlan(t, "guarded", nil, "guarded", "guarded.txt")
	good, goodErr := captureTask(t, newTaskHarness(t, dir), guardPlan)
	if goodErr != nil || good.Status != task.ReceiptCompleted || good.Fingerprint == "" {
		t.Fatalf("guard baseline failed: %v %#v", goodErr, good)
	}
	writeTaskFile(t, dir, "fail.flag", "fail\n")
	failed, failedErr := captureTask(t, newTaskHarness(t, dir), guardPlan)
	if failedErr == nil || failed.Status != task.ReceiptFailedCommand || failed.Fingerprint != good.Fingerprint {
		t.Fatalf("failure published over last good receipt: %v %#v", failedErr, failed)
	}
}

func requireNativeTask(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", `
version: '3'
tasks:
  hello:
    desc: Writes an environment-backed greeting
    aliases: [hi]
    cmds:
      - echo "{{.GREETING}}" > greeting.txt
  dep:
    desc: Dependency
    cmds: [echo dep > dep.txt]
  root:
    desc: Root task
    deps: [dep]
    cmds: [echo root > root.txt]
  quiet:
    cmds:
      - echo quiet > quiet.txt
  statused:
    sources: [source.txt]
    generates: [generated.txt]
    cmds: [cp source.txt generated.txt]
`)
	writeTaskFile(t, dir, "source.txt", "native\n")
	discoveryOut, discoveryErr := &bytes.Buffer{}, &bytes.Buffer{}
	discovery := task.NewExecutor(
		task.WithDir(dir),
		task.WithTempDir(task.TempDir{Remote: filepath.Join(dir, ".discover-cache", "remote"), Fingerprint: filepath.Join(dir, ".discover-cache", "fingerprint")}),
		task.WithOffline(true), task.WithVersionCheck(false), task.WithStdout(discoveryOut), task.WithStderr(discoveryErr),
	)
	if err := discovery.Setup(); err != nil {
		t.Fatal(err)
	}
	discoveredTasks, err := discovery.GetTaskList()
	if err != nil || len(discoveredTasks) < 5 {
		t.Fatalf("native default discovery failed: %v %d", err, len(discoveredTasks))
	}
	h := newTaskHarness(t, dir)
	if err := h.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	tasks, err := h.exec.GetTaskList()
	if err != nil || len(tasks) < 5 {
		t.Fatalf("native discovery failed: %v %d", err, len(tasks))
	}
	if err := h.exec.ListTaskNames(true); err != nil || !strings.Contains(h.out.String(), "hello") || !strings.Contains(h.out.String(), "hi") {
		t.Fatalf("native names failed: %v %q", err, h.out.String())
	}
	h.out.Reset()
	found, err := h.exec.ListTasks(task.NewListOptions(false, true, false, true, false))
	if err != nil || !found || !strings.Contains(h.out.String(), "Root task") {
		t.Fatalf("native list failed: %v %q", err, h.out.String())
	}
	h.out.Reset()
	found, err = h.exec.ListTasks(task.NewListOptions(false, true, true, true, false))
	if err != nil || !found {
		t.Fatalf("native JSON list failed: %v", err)
	}
	var listed any
	if json.Unmarshal(h.out.Bytes(), &listed) != nil {
		t.Fatalf("invalid native JSON: %q", h.out.String())
	}

	vars := ast.NewVars()
	vars.Set("GREETING", ast.Var{Value: "hello-native"})
	run := newTaskHarness(t, dir)
	if err := run.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := run.exec.Run(context.Background(), &task.Call{Task: "hello", Vars: vars}); err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(readTaskFile(t, dir, "greeting.txt")) != "hello-native" {
		t.Fatal("native variable did not reach command")
	}

	summary := newTaskHarness(t, dir, task.WithSummary(true))
	if err := summary.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := summary.exec.Run(context.Background(), &task.Call{Task: "root"}); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(summary.out.String(), "root") || !strings.Contains(summary.out.String(), "dep") {
		t.Fatalf("native summary lost dependency: %q", summary.out.String())
	}

	quiet := newTaskHarness(t, dir, task.WithSilent(true))
	if err := quiet.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := quiet.exec.Run(context.Background(), &task.Call{Task: "quiet"}); err != nil || readTaskFile(t, dir, "quiet.txt") != "quiet\n" {
		t.Fatalf("native silent execution failed: %v", err)
	}
	if strings.Contains(quiet.out.String(), "echo quiet") {
		t.Fatalf("silent mode echoed command: %q", quiet.out.String())
	}
	verbose := newTaskHarness(t, dir, task.WithVerbose(true))
	if err := verbose.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := verbose.exec.Run(context.Background(), &task.Call{Task: "quiet"}); err != nil || !strings.Contains(verbose.out.String()+verbose.errOut.String(), "quiet") {
		t.Fatalf("native verbose reporting missing task identity: %v stdout=%q stderr=%q", err, verbose.out.String(), verbose.errOut.String())
	}

	status := newTaskHarness(t, dir)
	if err := status.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := status.exec.Status(context.Background(), &task.Call{Task: "statused"}); err == nil {
		t.Fatal("stale native status reported current")
	}
	if err := status.exec.Run(context.Background(), &task.Call{Task: "statused"}); err != nil {
		t.Fatal(err)
	}
	current := newTaskHarness(t, dir)
	if err := current.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := current.exec.Status(context.Background(), &task.Call{Task: "statused"}); err != nil {
		t.Fatalf("native current status failed: %v", err)
	}

	dryDir := t.TempDir()
	writeTaskFile(t, dryDir, "Taskfile.yml", "version: '3'\ntasks:\n  dep:\n    cmds: [echo dep > dep.txt]\n  root:\n    deps: [dep]\n    cmds: [echo root > root.txt]\n")
	dry := newTaskHarness(t, dryDir, task.WithDry(true))
	if err := dry.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := dry.exec.Run(context.Background(), &task.Call{Task: "root"}); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dryDir, "root.txt")); !os.IsNotExist(err) {
		t.Fatal("native dry run created root output")
	}
	wet := newTaskHarness(t, dryDir)
	if err := wet.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := wet.exec.Run(context.Background(), &task.Call{Task: "root"}); err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(readTaskFile(t, dryDir, "dep.txt")) != "dep" || strings.TrimSpace(readTaskFile(t, dryDir, "root.txt")) != "root" {
		t.Fatal("native graph run did not materialize outputs")
	}

	nested := filepath.Join(dir, "nested")
	if err := os.MkdirAll(nested, 0o755); err != nil {
		t.Fatal(err)
	}
	explicit := task.NewExecutor(task.WithDir(nested), task.WithEntrypoint(filepath.Join(dir, "Taskfile.yml")), task.WithOffline(true), task.WithVersionCheck(false), task.WithStdout(&bytes.Buffer{}), task.WithStderr(&bytes.Buffer{}))
	if err := explicit.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := explicit.Run(context.Background(), &task.Call{Task: "quiet"}); err != nil {
		t.Fatalf("explicit native Taskfile failed: %v", err)
	}
}

func requireOneFamily(t *testing.T, family string) {
	t.Helper()
	switch family {
	case "include":
		requireIncludeNamespace(t)
	case "variables":
		requireVariableLineage(t)
	case "dependencies":
		requireDependencyScheduling(t)
	case "defer":
		requireDeferFailure(t)
	case "fingerprint":
		requireFingerprintCache(t)
	case "precondition":
		requirePreconditionStatus(t)
	case "dry":
		requireDryNoPublish(t)
	case "native":
		requireNativeTask(t)
	default:
		t.Fatalf("unknown family %q", family)
	}
}
