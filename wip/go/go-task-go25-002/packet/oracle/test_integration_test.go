package task_oracle_test

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	task "github.com/go-task/task/v3"
)

func TestGoTaskSeamIncludedDirectoryWorkspace(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\nincludes:\n  tools:\n    taskfile: ./sub/Taskfile.yml\n    dir: ./sub\ntasks:\n  root:\n    deps: [tools:emit]\n    cmds: [echo root > root.txt]\n")
	writeTaskFile(t, dir, "sub/Taskfile.yml", "version: '3'\ntasks:\n  emit:\n    cmds: [echo nested > nested.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "nested", "sub/nested.txt", "root", "root.txt"))
	tasks := strings.Join(eventValues(receipt, "task"), "\n")
	if err != nil || receipt.Workspace["nested"] == "missing" || receipt.Workspace["root"] == "missing" || !strings.Contains(tasks, "tools:emit|sub|") {
		t.Fatalf("included directory seam mismatch: err=%v tasks=%q workspace=%#v", err, tasks, receipt.Workspace)
	}
}

func TestGoTaskSeamFlattenedDependencyReceipt(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\nincludes:\n  ns: ./named.yml\n  flat:\n    taskfile: ./flat.yml\n    flatten: true\ntasks:\n  root:\n    deps: [ns:named, flat_leaf]\n")
	writeTaskFile(t, dir, "named.yml", "version: '3'\ntasks:\n  named:\n    cmds: [echo named > named.txt]\n")
	writeTaskFile(t, dir, "flat.yml", "version: '3'\ntasks:\n  flat_leaf:\n    cmds: [echo flat > flat.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "named", "named.txt", "flat", "flat.txt"))
	tasks, deps := strings.Join(eventValues(receipt, "task"), "\n"), strings.Join(eventValues(receipt, "dependency"), "\n")
	if err != nil || !strings.Contains(tasks, "ns:named|") || !strings.Contains(tasks, "flat_leaf|") || !strings.Contains(deps, "flat_leaf|") || receipt.Workspace["flat"] == "missing" {
		t.Fatalf("flatten seam mismatch: err=%v tasks=%q deps=%q", err, tasks, deps)
	}
}

func TestGoTaskSeamOptionalIncludeRootReceipt(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\nincludes:\n  absent:\n    taskfile: ./absent.yml\n    optional: true\n  present: ./present.yml\ntasks:\n  root:\n    deps: [present:leaf]\n    cmds: [echo root > root.txt]\n")
	writeTaskFile(t, dir, "present.yml", "version: '3'\ntasks:\n  leaf:\n    cmds: [echo present > present.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "present", "present.txt", "root", "root.txt"))
	tasks := strings.Join(eventValues(receipt, "task"), "\n")
	if err != nil || receipt.Task != "root" || !strings.Contains(tasks, "present:leaf|") || strings.Contains(tasks, "absent:") || receipt.Workspace["root"] == "missing" {
		t.Fatalf("optional include seam mismatch: err=%v tasks=%q receipt=%#v", err, tasks, receipt)
	}
}

func TestGoTaskSeamPlanOverrideCommand(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  render:\n    cmds: ['echo {{.FORMAT}}-{{.COUNT}} > rendered.txt']\n")
	base := selectPlan(t, "render", map[string]string{"FORMAT": "plain", "COUNT": "one"}, "rendered", "rendered.txt")
	plan, err := base.WithVariables(map[string]string{"FORMAT": "json", "COUNT": "two"})
	if err != nil {
		t.Fatal(err)
	}
	receipt, runErr := captureTask(t, newTaskHarness(t, dir), plan)
	if runErr != nil || strings.TrimSpace(readTaskFile(t, dir, "rendered.txt")) != "json-two" || receipt.Variables["FORMAT"] != "json" || receipt.Variables["COUNT"] != "two" {
		t.Fatalf("plan override seam mismatch: run=%v vars=%#v", runErr, receipt.Variables)
	}
}

func TestGoTaskSeamIncludeVariableScope(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\nincludes:\n  child:\n    taskfile: ./sub/Taskfile.yml\n    dir: ./sub\n    vars: {PREFIX: include}\ntasks:\n  root:\n    deps: [child:emit]\n    cmds: ['echo {{.SUFFIX}} > root.txt']\n")
	writeTaskFile(t, dir, "sub/Taskfile.yml", "version: '3'\ntasks:\n  emit:\n    cmds: ['echo {{.PREFIX}} > scoped.txt']\n")
	plan := selectPlan(t, "root", map[string]string{"SUFFIX": "selection"}, "scoped", "sub/scoped.txt", "root", "root.txt")
	plan, err := plan.WithVariables(map[string]string{"SUFFIX": "override"})
	if err != nil {
		t.Fatal(err)
	}
	receipt, runErr := captureTask(t, newTaskHarness(t, dir), plan)
	if runErr != nil || strings.TrimSpace(readTaskFile(t, dir, "sub/scoped.txt")) != "include" || strings.TrimSpace(readTaskFile(t, dir, "root.txt")) != "override" || receipt.Variables["SUFFIX"] != "override" || !strings.Contains(strings.Join(eventValues(receipt, "task"), "\n"), "child:emit|") {
		t.Fatalf("include variable seam mismatch: run=%v vars=%#v", runErr, receipt.Variables)
	}
}

func TestGoTaskSeamDynamicVariableDependency(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\nvars:\n  DYNAMIC:\n    sh: echo dynamic\ntasks:\n  worker:\n    cmds: ['echo {{.ITEM}}-{{.SUFFIX}} > worker.txt']\n  root:\n    deps:\n      - task: worker\n        vars: {ITEM: '{{.DYNAMIC}}', SUFFIX: '{{.SUFFIX}}'}\n")
	plan := selectPlan(t, "root", map[string]string{"SUFFIX": "selection"}, "worker", "worker.txt")
	plan, err := plan.WithVariables(map[string]string{"SUFFIX": "override"})
	if err != nil {
		t.Fatal(err)
	}
	receipt, runErr := captureTask(t, newTaskHarness(t, dir), plan)
	if runErr != nil || strings.TrimSpace(readTaskFile(t, dir, "worker.txt")) != "dynamic-override" || receipt.Variables["SUFFIX"] != "override" || !strings.Contains(strings.Join(eventValues(receipt, "dependency"), "\n"), "worker|") {
		t.Fatalf("dynamic dependency seam mismatch: run=%v vars=%#v", runErr, receipt.Variables)
	}
}

func TestGoTaskSeamDependencySortedReceipt(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  alpha:\n    cmds: [echo alpha >> order.txt]\n  middle:\n    cmds: [echo middle >> order.txt]\n  zeta:\n    cmds: [echo zeta >> order.txt]\n  root:\n    deps: [zeta, middle, alpha]\n    cmds: [echo root >> order.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "order", "order.txt"))
	deps := strings.Join(eventValues(receipt, "dependency"), "\n")
	if err != nil || strings.Index(deps, "alpha|") > strings.Index(deps, "middle|") || strings.Index(deps, "middle|") > strings.Index(deps, "zeta|") || !strings.HasSuffix(strings.TrimSpace(readTaskFile(t, dir, "order.txt")), "root") {
		t.Fatalf("sorted dependency seam mismatch: err=%v deps=%q", err, deps)
	}
}

func TestGoTaskSeamSharedDependencyOnce(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  shared:\n    run: once\n    cmds: [echo shared >> trace.txt]\n  alpha:\n    deps: [shared]\n    cmds: [echo alpha >> trace.txt]\n  omega:\n    deps: [shared]\n    cmds: [echo omega >> trace.txt]\n  root:\n    deps: [omega, alpha]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "trace", "trace.txt"))
	deps, tasks := strings.Join(eventValues(receipt, "dependency"), "\n"), strings.Join(eventValues(receipt, "task"), "\n")
	if err != nil || strings.Count(readTaskFile(t, dir, "trace.txt"), "shared") != 1 || strings.Count(tasks, "shared|") != 1 || strings.Index(deps, "alpha|") > strings.Index(deps, "omega|") {
		t.Fatalf("shared dependency seam mismatch: err=%v deps=%q tasks=%q", err, deps, tasks)
	}
}

func TestGoTaskSeamTaskCallVariableIsolation(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  alpha:\n    cmds: [echo alpha >> deps.txt]\n  zeta:\n    cmds: [echo zeta >> deps.txt]\n  worker:\n    cmds: ['echo {{.ITEM}} >> workers.txt']\n  root:\n    deps: [zeta, alpha]\n    cmds:\n      - task: worker\n        vars: {ITEM: first}\n      - task: worker\n        vars: {ITEM: second}\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "workers", "workers.txt", "deps", "deps.txt"))
	deps, workers := strings.Join(eventValues(receipt, "dependency"), "\n"), strings.Fields(readTaskFile(t, dir, "workers.txt"))
	if err != nil || len(workers) != 2 || workers[0] != "first" || workers[1] != "second" || strings.Index(deps, "alpha|") > strings.Index(deps, "zeta|") || strings.Count(strings.Join(eventValues(receipt, "task"), "\n"), "worker|") != 2 {
		t.Fatalf("task-call isolation mismatch: err=%v deps=%q workers=%#v", err, deps, workers)
	}
}

func TestGoTaskSeamStatusDependencySkip(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "ready.flag", "ready")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  alpha:\n    status: [test -f ready.flag]\n    cmds: [echo alpha >> order.txt]\n  zeta:\n    cmds: [echo zeta >> order.txt]\n  root:\n    deps: [zeta, alpha]\n    cmds: [echo root >> order.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "order", "order.txt"))
	deps, order := strings.Join(eventValues(receipt, "dependency"), "\n"), strings.Fields(readTaskFile(t, dir, "order.txt"))
	if err != nil || len(order) != 2 || order[0] != "zeta" || order[1] != "root" || strings.Index(deps, "alpha|") > strings.Index(deps, "zeta|") {
		t.Fatalf("status dependency seam mismatch: err=%v deps=%q order=%#v", err, deps, order)
	}
}

func TestGoTaskSeamFailedCommandStillDefers(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  fail:\n    cmds:\n      - defer: echo first >> cleanup.txt\n      - defer: echo second >> cleanup.txt\n      - false\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "fail", nil, "cleanup", "cleanup.txt"))
	defers := eventValues(receipt, "defer")
	if err == nil || receipt.Status != task.ReceiptFailedCommand || len(defers) != 2 || !strings.Contains(defers[0], "second") || strings.Fields(readTaskFile(t, dir, "cleanup.txt"))[0] != "second" {
		t.Fatalf("failed command defer seam mismatch: err=%v status=%v defers=%#v", err, receipt.Status, defers)
	}
}

func TestGoTaskSeamNestedDeferredReverse(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  child:\n    cmds:\n      - defer: echo child-a >> cleanup.txt\n      - defer: echo child-b >> cleanup.txt\n      - echo child >> body.txt\n  root:\n    cmds:\n      - defer: echo root-a >> cleanup.txt\n      - defer: echo root-b >> cleanup.txt\n      - task: child\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "cleanup", "cleanup.txt", "body", "body.txt"))
	defers := strings.Join(eventValues(receipt, "defer"), "\n")
	if err != nil || strings.Index(defers, "child-b") > strings.Index(defers, "child-a") || strings.Index(defers, "root-b") > strings.Index(defers, "root-a") || !strings.HasSuffix(strings.TrimSpace(readTaskFile(t, dir, "cleanup.txt")), "root-a") {
		t.Fatalf("nested defer seam mismatch: err=%v defers=%q", err, defers)
	}
}

func TestGoTaskSeamIgnoredFailureContinues(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  tolerant:\n    cmds:\n      - defer: echo outer >> cleanup.txt\n      - defer: echo inner >> cleanup.txt\n      - cmd: false\n        ignore_error: true\n      - echo continued > continued.txt\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "tolerant", nil, "continued", "continued.txt", "cleanup", "cleanup.txt"))
	commands, defers := strings.Join(eventValues(receipt, "command"), "\n"), eventValues(receipt, "defer")
	if err != nil || receipt.Status != task.ReceiptCompleted || !strings.Contains(commands, "|false|ignored") || len(defers) != 2 || !strings.Contains(defers[0], "inner") || receipt.Workspace["continued"] == "missing" {
		t.Fatalf("ignored failure seam mismatch: err=%v receipt=%#v", err, receipt)
	}
}

func TestGoTaskSeamChecksumSkipReceipt(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "one")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  build:\n    method: checksum\n    sources: [source.txt]\n    generates: [output.txt]\n    cmds: [cp source.txt output.txt]\n")
	plan := selectPlan(t, "build", nil, "source", "source.txt", "output", "output.txt")
	first, firstErr := captureTask(t, newTaskHarness(t, dir), plan)
	second, secondErr := captureTask(t, newTaskHarness(t, dir), plan)
	writeTaskFile(t, dir, "source.txt", "two")
	changed, changedErr := captureTask(t, newTaskHarness(t, dir), plan)
	if firstErr != nil || secondErr != nil || changedErr != nil || second.Status != task.ReceiptSkippedCurrent || first.Fingerprint != second.Fingerprint || changed.Fingerprint == first.Fingerprint {
		t.Fatalf("checksum lifecycle mismatch: %v/%v/%v %v/%v/%v", firstErr, secondErr, changedErr, first.Status, second.Status, changed.Status)
	}
}

func TestGoTaskSeamMissingGeneratedRerun(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "payload")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  primary:\n    method: checksum\n    sources: [source.txt]\n    generates: [primary.txt]\n    cmds: [cp source.txt primary.txt]\n  alternate:\n    method: checksum\n    sources: [source.txt]\n    generates: [alternate.txt]\n    cmds: [cp source.txt alternate.txt]\n")
	primaryPlan := selectPlan(t, "primary", nil, "output", "primary.txt")
	first, firstErr := captureTask(t, newTaskHarness(t, dir), primaryPlan)
	if err := os.Remove(filepath.Join(dir, "primary.txt")); err != nil {
		t.Fatal(err)
	}
	rerun, rerunErr := captureTask(t, newTaskHarness(t, dir), primaryPlan)
	alternate, alternateErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "alternate", nil, "output", "alternate.txt"))
	if firstErr != nil || rerunErr != nil || alternateErr != nil || rerun.Status != task.ReceiptCompleted || rerun.Workspace["output"] == "missing" || alternate.Fingerprint == rerun.Fingerprint || first.Fingerprint == "" {
		t.Fatalf("missing generated seam mismatch: %v/%v/%v", firstErr, rerunErr, alternateErr)
	}
}

func TestGoTaskSeamTaskScopedFingerprint(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "shared")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  left:\n    method: checksum\n    sources: [source.txt]\n    generates: [left.txt]\n    cmds: [cp source.txt left.txt]\n  right:\n    method: checksum\n    sources: [source.txt]\n    generates: [right.txt]\n    cmds: [cp source.txt right.txt]\n")
	left, leftErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "left", nil, "output", "left.txt"))
	right, rightErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "right", nil, "output", "right.txt"))
	leftAgain, againErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "left", nil, "output", "left.txt"))
	if leftErr != nil || rightErr != nil || againErr != nil || left.Fingerprint == right.Fingerprint || leftAgain.Status != task.ReceiptSkippedCurrent || leftAgain.Fingerprint != left.Fingerprint {
		t.Fatalf("task-scoped fingerprint mismatch: %v/%v/%v", leftErr, rightErr, againErr)
	}
}

func TestGoTaskSeamPreconditionBlocksEffects(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  publish:\n    preconditions: [{sh: 'test -f approved.flag'}]\n    cmds:\n      - echo staged > stage.txt\n      - echo published > publish.txt\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "publish", nil, "stage", "stage.txt", "publish", "publish.txt"))
	if !errors.Is(err, task.ErrPreconditionFailed) || receipt.Status != task.ReceiptFailedPrecondition || receipt.Workspace["stage"] != "missing" || receipt.Workspace["publish"] != "missing" || len(eventValues(receipt, "command")) != 2 {
		t.Fatalf("precondition effect seam mismatch: err=%v receipt=%#v", err, receipt)
	}
}

func TestGoTaskSeamStatusForcesRerun(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "source.txt", "source")
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  guard:\n    preconditions: [{sh: 'test -f permit.flag'}]\n    cmds: [echo guard > guard.txt]\n  statused:\n    method: checksum\n    sources: [source.txt]\n    generates: [output.txt]\n    status: [test -f current.flag]\n    cmds:\n      - echo run >> runs.txt\n      - cp source.txt output.txt\n")
	blocked, blockedErr := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "guard", nil, "guard", "guard.txt"))
	plan := selectPlan(t, "statused", nil, "output", "output.txt", "runs", "runs.txt")
	first, firstErr := captureTask(t, newTaskHarness(t, dir), plan)
	writeTaskFile(t, dir, "current.flag", "current")
	skipped, skippedErr := captureTask(t, newTaskHarness(t, dir), plan)
	if err := os.Remove(filepath.Join(dir, "current.flag")); err != nil {
		t.Fatal(err)
	}
	rerun, rerunErr := captureTask(t, newTaskHarness(t, dir), plan)
	if !errors.Is(blockedErr, task.ErrPreconditionFailed) || blocked.Status != task.ReceiptFailedPrecondition || firstErr != nil || first.Status != task.ReceiptCompleted || skippedErr != nil || rerunErr != nil || skipped.Status != task.ReceiptSkippedCurrent || rerun.Status != task.ReceiptCompleted || strings.Count(readTaskFile(t, dir, "runs.txt"), "run") != 2 {
		t.Fatalf("status rerun seam mismatch: %v/%v/%v/%v", blockedErr, firstErr, skippedErr, rerunErr)
	}
}

func TestGoTaskSeamDryGraphPlanned(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  dependency:\n    cmds: [echo dependency > dependency.txt]\n  root:\n    deps: [dependency]\n    cmds: [echo root > root.txt]\n")
	receipt, err := captureTask(t, newTaskHarness(t, dir), selectPlan(t, "root", nil, "dependency", "dependency.txt", "root", "root.txt").WithDryRun(true))
	planned := 0
	for _, event := range receipt.Events {
		if event.Kind != "status" && event.Outcome == "planned" {
			planned++
		}
	}
	if err != nil || receipt.Status != task.ReceiptRenderedDry || receipt.Workspace["dependency"] != "missing" || receipt.Workspace["root"] != "missing" || planned < 4 || receipt.Fingerprint != "" {
		t.Fatalf("dry graph seam mismatch: err=%v planned=%d receipt=%#v", err, planned, receipt)
	}
}

func TestGoTaskSeamFailureKeepsLastGoodFingerprint(t *testing.T) {
	dir := t.TempDir()
	writeTaskFile(t, dir, "Taskfile.yml", "version: '3'\ntasks:\n  guarded:\n    cmds:\n      - test ! -f fail.flag\n      - echo success >> history.txt\n")
	plan := selectPlan(t, "guarded", nil, "history", "history.txt")
	good, goodErr := captureTask(t, newTaskHarness(t, dir), plan)
	writeTaskFile(t, dir, "fail.flag", "fail")
	dry, dryErr := captureTask(t, newTaskHarness(t, dir), plan.WithDryRun(true))
	failed, failedErr := captureTask(t, newTaskHarness(t, dir), plan)
	if goodErr != nil || dryErr != nil || failedErr == nil || dry.Status != task.ReceiptRenderedDry || dry.Fingerprint != good.Fingerprint || failed.Status != task.ReceiptFailedCommand || failed.Fingerprint != good.Fingerprint || strings.Count(readTaskFile(t, dir, "history.txt"), "success") != 1 {
		t.Fatalf("last-good publication seam mismatch: good=%v dry=%v failed=%v", goodErr, dryErr, failedErr)
	}
}
