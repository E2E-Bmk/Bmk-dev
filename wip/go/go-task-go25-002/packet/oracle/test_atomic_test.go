package task_oracle_test

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"path/filepath"
	"strings"
	"testing"

	task "github.com/go-task/task/v3"
	"github.com/go-task/task/v3/taskfile/ast"
)

func TestGoTaskAtomicIncludeNamespaceReceipt(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\nincludes:\n  ns: ./child.yml\ntasks:\n  root:\n    deps: [ns:unit]\n")
	writeTaskFile(t, dir, "child.yml", "version: '3'\ntasks:\n  unit:\n    cmds: [echo child > child.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "child", "child.txt"))
	tasks := strings.Join(eventValues(receipt, "task"), "\n")
	if err != nil || receipt.Status != task.ReceiptCompleted || !strings.Contains(tasks, "ns:unit|") || receipt.Workspace["child"] == "missing" {
		t.Fatalf("namespace receipt mismatch: err=%v tasks=%q workspace=%#v", err, tasks, receipt.Workspace)
	}
}

func TestGoTaskAtomicSelectionOverrideLineage(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  paint:\n    cmds: ['echo {{.COLOR}} > color.txt']\n")
	base := selectPlan(t, "paint", map[string]string{"COLOR": "blue"}, "color", "color.txt")
	override, err := base.WithVariables(map[string]string{"COLOR": "amber"})
	if err != nil {
		t.Fatal(err)
	}
	receipt, runErr := captureTask(t, newTaskHarness(t, dir), override)
	if runErr != nil || strings.TrimSpace(readTaskFile(t, dir, "color.txt")) != "amber" || receipt.Variables["COLOR"] != "amber" {
		t.Fatalf("override lineage mismatch: run=%v vars=%#v", runErr, receipt.Variables)
	}
}

func TestGoTaskAtomicTaskVariableSnapshot(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  label:\n    vars:\n      LOCAL: task-frame\n    cmds: ['echo {{.LOCAL}}-{{.SUFFIX}} > label.txt']\n")
	plan := selectPlan(t, "label", map[string]string{"SUFFIX": "selection"}, "label", "label.txt")
	plan, err := plan.WithVariables(map[string]string{"SUFFIX": "override"})
	if err != nil {
		t.Fatal(err)
	}
	receipt, runErr := captureTask(t, newTaskHarness(t, dir), plan)
	if runErr != nil || strings.TrimSpace(readTaskFile(t, dir, "label.txt")) != "task-frame-override" || receipt.Variables["LOCAL"] != "task-frame" || receipt.Variables["SUFFIX"] != "override" {
		t.Fatalf("task frame snapshot mismatch: run=%v vars=%#v", runErr, receipt.Variables)
	}
}

func TestGoTaskAtomicDependencyReceiptOrder(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  alpha:\n    cmds: [echo alpha > alpha.txt]\n  zeta:\n    cmds: [echo zeta > zeta.txt]\n  root:\n    deps: [zeta, alpha]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "alpha", "alpha.txt", "zeta", "zeta.txt"))
	deps := strings.Join(eventValues(receipt, "dependency"), "\n")
	if err != nil || strings.Index(deps, "alpha|") < 0 || strings.Index(deps, "zeta|") < 0 || strings.Index(deps, "alpha|") > strings.Index(deps, "zeta|") {
		t.Fatalf("dependency receipt not canonical: err=%v deps=%q", err, deps)
	}
}

func TestGoTaskAtomicDeferredReceiptLIFO(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  tidy:\n    cmds:\n      - defer: echo outer >> cleanup.txt\n      - defer: echo inner >> cleanup.txt\n      - echo body > body.txt\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "tidy", nil, "cleanup", "cleanup.txt", "body", "body.txt"))
	deferred := eventValues(receipt, "defer")
	if err != nil || len(deferred) != 2 || !strings.Contains(deferred[0], "inner") || !strings.Contains(deferred[1], "outer") || !strings.HasPrefix(readTaskFile(t, dir, "cleanup.txt"), "inner") {
		t.Fatalf("defer stack mismatch: err=%v events=%#v", err, deferred)
	}
}

func TestGoTaskAtomicFingerprintChangesByTask(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  red:\n    cmds: [echo red > red.txt]\n  blue:\n    cmds: [echo blue > blue.txt]\n")
	red, redErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "red", nil, "output", "red.txt"))
	blue, blueErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "blue", nil, "output", "blue.txt"))
	if redErr != nil || blueErr != nil || red.Fingerprint == "" || blue.Fingerprint == "" || red.Fingerprint == blue.Fingerprint {
		t.Fatalf("task identity did not separate fingerprints: %v %v %q %q", redErr, blueErr, red.Fingerprint, blue.Fingerprint)
	}
}

func TestGoTaskAtomicFingerprintChangesBySource(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "first")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  build:\n    method: checksum\n    sources: [source.txt]\n    generates: [output.txt]\n    cmds: [cp source.txt output.txt]\n")
	plan := selectPlan(t, "build", nil, "source", "source.txt", "output", "output.txt")
	first, firstErr := captureTask(t, newTaskHarness(t, dir), plan)
	writeTaskFile(t, dir, "source.txt", "second")
	second, secondErr := captureTask(t, newTaskHarness(t, dir), plan)
	if firstErr != nil || secondErr != nil || first.Fingerprint == second.Fingerprint || !strings.Contains(strings.Join(task.ReceiptDiff(first, second), ","), "fingerprint") {
		t.Fatalf("source edit did not change receipt: %v %v %#v", firstErr, secondErr, task.ReceiptDiff(first, second))
	}
}

func TestGoTaskAtomicPreconditionClassification(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  guarded:\n    preconditions: [{sh: 'test -f permit.flag'}]\n    cmds: [echo ran > ran.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "guarded", nil, "effect", "ran.txt"))
	if !errors.Is(err, task.ErrPreconditionFailed) || receipt.Status != task.ReceiptFailedPrecondition || receipt.Workspace["effect"] != "missing" || receipt.Fingerprint != "" {
		t.Fatalf("precondition classification mismatch: err=%v receipt=%#v", err, receipt)
	}
}

func TestGoTaskAtomicDryPlanNoWorkspaceEffect(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  render:\n    cmds: [echo material > material.txt]\n")
	plan := selectPlan(t, "render", nil, "material", "material.txt").WithDryRun(true)
	receipt, err := captureTask(t, newTaskHarness(t, dir), plan)
	if err != nil || receipt.Status != task.ReceiptRenderedDry || receipt.Workspace["material"] != "missing" || receipt.Fingerprint != "" {
		t.Fatalf("dry plan published effects: err=%v receipt=%#v", err, receipt)
	}
}

func TestGoTaskAtomicNativeDefaultDiscovery(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  discovered:\n    cmds: [echo ok]\n")
	out, errOut := &bytes.Buffer{}, &bytes.Buffer{}
	exec := task.NewExecutor(task.WithDir(dir), task.WithOffline(true), task.WithVersionCheck(false), task.WithStdout(out), task.WithStderr(errOut))
	if err := exec.Setup(); err != nil {
		t.Fatal(err)
	}
	tasks, err := exec.GetTaskList()
	if err != nil || len(tasks) != 1 || tasks[0].Task != "discovered" {
		t.Fatalf("default discovery mismatch: %v %#v", err, tasks)
	}
}

func TestGoTaskAtomicNativeExplicitEntrypoint(t *testing.T) {
	root := t.TempDir()
	writeTaskFile(t, root, "chosen.yml", "version: '3'\ntasks:\n  chosen:\n    cmds: [echo chosen > chosen.txt]\n")
	nested := filepath.Join(root, "nested")
	writeTaskFile(t, nested, "placeholder.txt", "nested")
	exec := task.NewExecutor(task.WithDir(nested), task.WithEntrypoint(filepath.Join(root, "chosen.yml")), task.WithOffline(true), task.WithVersionCheck(false), task.WithStdout(&bytes.Buffer{}), task.WithStderr(&bytes.Buffer{}))
	if err := exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := exec.Run(context.Background(), &task.Call{Task: "chosen"}); err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(readTaskFile(t, nested, "chosen.txt")) != "chosen" {
		t.Fatal("explicit entrypoint did not retain caller directory")
	}
}

func TestGoTaskAtomicNativeTaskNamesAliases(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  greet:\n    aliases: [hello]\n    desc: Greeting\n    cmds: [echo hi]\n")
	h := newTaskHarness(t, dir)
	if err := h.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := h.exec.ListTaskNames(true); err != nil {
		t.Fatal(err)
	}
	text := h.out.String()
	if !strings.Contains(text, "greet") || !strings.Contains(text, "hello") {
		t.Fatalf("alias listing mismatch: %q", text)
	}
}

func TestGoTaskAtomicNativeTaskListJSON(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  inspect:\n    desc: Inspect target\n    cmds: [echo inspect]\n")
	h := newTaskHarness(t, dir)
	if err := h.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	found, err := h.exec.ListTasks(task.NewListOptions(false, true, true, true, false))
	var payload any
	decodeErr := json.Unmarshal(h.out.Bytes(), &payload)
	if err != nil || !found || decodeErr != nil || !strings.Contains(h.out.String(), "inspect") {
		t.Fatalf("JSON task list mismatch: err=%v decode=%v out=%q", err, decodeErr, h.out.String())
	}
}

func TestGoTaskAtomicNativeVariableCommand(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  emit:\n    cmds: ['echo {{.WORD}} > word.txt']\n")
	h := newTaskHarness(t, dir)
	if err := h.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	vars := ast.NewVars()
	vars.Set("WORD", ast.Var{Value: "native-value"})
	if err := h.exec.Run(context.Background(), &task.Call{Task: "emit", Vars: vars}); err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(readTaskFile(t, dir, "word.txt")) != "native-value" {
		t.Fatal("call variable did not reach native command")
	}
}

func TestGoTaskAtomicNativeSilentCommand(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  quiet:\n    cmds: [echo quiet > quiet.txt]\n")
	h := newTaskHarness(t, dir, task.WithSilent(true))
	if err := h.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := h.exec.Run(context.Background(), &task.Call{Task: "quiet"}); err != nil {
		t.Fatal(err)
	}
	if readTaskFile(t, dir, "quiet.txt") != "quiet\n" || strings.Contains(h.out.String(), "echo quiet") {
		t.Fatalf("silent run mismatch: %q", h.out.String())
	}
}

func TestGoTaskAtomicNativeStatusLifecycle(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "native")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  build:\n    sources: [source.txt]\n    generates: [generated.txt]\n    cmds: [cp source.txt generated.txt]\n")
	stale := newTaskHarness(t, dir)
	if err := stale.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := stale.exec.Status(context.Background(), &task.Call{Task: "build"}); err == nil {
		t.Fatal("missing target reported current")
	}
	if err := stale.exec.Run(context.Background(), &task.Call{Task: "build"}); err != nil {
		t.Fatal(err)
	}
	current := newTaskHarness(t, dir)
	if err := current.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := current.exec.Status(context.Background(), &task.Call{Task: "build"}); err != nil {
		t.Fatalf("generated target not current: %v", err)
	}
}
