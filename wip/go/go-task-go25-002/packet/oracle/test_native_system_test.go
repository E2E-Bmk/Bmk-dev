package task_oracle_test

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	task "github.com/go-task/task/v3"
)

func TestGoTaskNativeSeamDiscoveryToTextList(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  build:\n    desc: Build artifact\n    cmds: [echo build]\n  check:\n    desc: Check artifact\n    cmds: [echo check]\n")
	out, errOut := &bytes.Buffer{}, &bytes.Buffer{}
	exec := task.NewExecutor(task.WithDir(dir), task.WithOffline(true), task.WithVersionCheck(false), task.WithStdout(out), task.WithStderr(errOut))
	if err := exec.Setup(); err != nil {
		t.Fatal(err)
	}
	tasks, err := exec.GetTaskList()
	if err != nil || len(tasks) != 2 {
		t.Fatalf("discovery mismatch: %v %#v", err, tasks)
	}
	found, listErr := exec.ListTasks(task.NewListOptions(false, true, false, true, false))
	if listErr != nil || !found || !strings.Contains(out.String(), "Build artifact") || !strings.Contains(out.String(), "Check artifact") {
		t.Fatalf("text list mismatch: err=%v out=%q", listErr, out.String())
	}
}

func TestGoTaskNativeSeamSummaryDependencies(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  prepare:\n    cmds: [echo prepare > prepare.txt]\n  publish:\n    deps: [prepare]\n    cmds: [echo publish > publish.txt]\n")
	h := newTaskHarness(t, dir, task.WithSummary(true))
	if err := h.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := h.exec.Run(context.Background(), &task.Call{Task: "publish"}); err != nil {
		t.Fatal(err)
	}
	output := h.out.String() + h.errOut.String()
	if !strings.Contains(output, "publish") || !strings.Contains(output, "prepare") {
		t.Fatalf("summary dependency mismatch: %q", output)
	}
}

func TestGoTaskNativeSeamExplicitFileWorkingDir(t *testing.T) {
	root := t.TempDir()
	writeTaskFile(t, root, "config/NamedTaskfile.yml", "version: '3'\ntasks:\n  locate:\n    cmds: [pwd > location.txt]\n")
	work := filepath.Join(root, "workspace")
	writeTaskFile(t, work, "seed.txt", "seed")
	out, errOut := &bytes.Buffer{}, &bytes.Buffer{}
	exec := task.NewExecutor(task.WithDir(work), task.WithEntrypoint(filepath.Join(root, "config", "NamedTaskfile.yml")), task.WithOffline(true), task.WithVersionCheck(false), task.WithStdout(out), task.WithStderr(errOut))
	if err := exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := exec.Run(context.Background(), &task.Call{Task: "locate"}); err != nil {
		t.Fatal(err)
	}
	location := filepath.Clean(strings.TrimSpace(readTaskFile(t, work, "location.txt")))
	if location != filepath.Clean(work) {
		t.Fatalf("explicit-file working directory mismatch: got=%q want=%q", location, work)
	}
}

func TestGoTaskNativeSeamListJSONMatchesText(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  alpha:\n    desc: Alpha action\n    cmds: [echo alpha]\n  beta:\n    desc: Beta action\n    cmds: [echo beta]\n")
	text := newTaskHarness(t, dir)
	if err := text.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	foundText, textErr := text.exec.ListTasks(task.NewListOptions(false, true, false, true, false))
	jsonView := newTaskHarness(t, dir)
	if err := jsonView.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	foundJSON, jsonErr := jsonView.exec.ListTasks(task.NewListOptions(false, true, true, true, false))
	var decoded any
	decodeErr := json.Unmarshal(jsonView.out.Bytes(), &decoded)
	if textErr != nil || jsonErr != nil || !foundText || !foundJSON || decodeErr != nil || !strings.Contains(text.out.String(), "alpha") || !strings.Contains(text.out.String(), "beta") || !strings.Contains(jsonView.out.String(), "alpha") || !strings.Contains(jsonView.out.String(), "beta") {
		t.Fatalf("list projection mismatch: text=%v json=%v decode=%v", textErr, jsonErr, decodeErr)
	}
}

func TestGoTaskSystemIncludeNamespaceFreshReceipt(t *testing.T) {
	requireIncludeNamespace(t)
}

func TestGoTaskSystemVariableLineageFreshReceipt(t *testing.T) {
	requireVariableLineage(t)
}

func TestGoTaskSystemDependencyFailureFreshReceipt(t *testing.T) {
	requireDependencyScheduling(t)
}

func TestGoTaskSystemDeferFailureFreshReceipt(t *testing.T) {
	requireDeferFailure(t)
}

func TestGoTaskSystemFingerprintCacheFreshReceipt(t *testing.T) {
	requireFingerprintCache(t)
}

func TestGoTaskSystemNativeDiscoverListRun(t *testing.T) {
	requireNativeTask(t)
}

func TestGoTaskSystemNativeDryThenRun(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  fetch:\n    cmds: [echo fetched > fetched.txt]\n  assemble:\n    deps: [fetch]\n    cmds: [echo assembled > assembled.txt]\n")
	dry := newTaskHarness(t, dir, task.WithDry(true))
	if err := dry.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := dry.exec.Run(context.Background(), &task.Call{Task: "assemble"}); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dir, "fetched.txt")); !os.IsNotExist(err) {
		t.Fatal("dry dependency materialized")
	}
	if _, err := os.Stat(filepath.Join(dir, "assembled.txt")); !os.IsNotExist(err) {
		t.Fatal("dry root materialized")
	}
	wet := newTaskHarness(t, dir)
	if err := wet.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := wet.exec.Run(context.Background(), &task.Call{Task: "assemble"}); err != nil {
		t.Fatal(err)
	}
	if readTaskFile(t, dir, "fetched.txt") != "fetched\n" || readTaskFile(t, dir, "assembled.txt") != "assembled\n" || !strings.Contains(dry.out.String()+dry.errOut.String(), "fetched.txt") {
		t.Fatalf("dry/wet native lifecycle mismatch: dry=%q", dry.out.String()+dry.errOut.String())
	}
}

func TestGoTaskSystemNativeStatusLifecycle(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "first")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  compile:\n    method: checksum\n    sources: [source.txt]\n    generates: [binary.txt]\n    cmds:\n      - echo run >> runs.txt\n      - cp source.txt binary.txt\n")
	stale := newTaskHarness(t, dir)
	if err := stale.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := stale.exec.Status(context.Background(), &task.Call{Task: "compile"}); err == nil {
		t.Fatal("fresh workspace reported current")
	}
	if err := stale.exec.Run(context.Background(), &task.Call{Task: "compile"}); err != nil {
		t.Fatal(err)
	}
	current := newTaskHarness(t, dir)
	if err := current.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := current.exec.Status(context.Background(), &task.Call{Task: "compile"}); err != nil {
		t.Fatalf("built workspace reported stale: %v", err)
	}
	writeTaskFile(t, dir, "source.txt", "second")
	changed := newTaskHarness(t, dir)
	if err := changed.exec.Setup(); err != nil {
		t.Fatal(err)
	}
	if err := changed.exec.Status(context.Background(), &task.Call{Task: "compile"}); err == nil {
		t.Fatal("changed source reported current")
	}
	runs := readTaskFile(t, dir, "runs.txt")
	binary := strings.TrimSpace(readTaskFile(t, dir, "binary.txt"))
	if strings.Count(runs, "run") != 1 || binary != "first" {
		t.Fatalf("status observation changed the workspace: runs=%q binary=%q", runs, binary)
	}
}
