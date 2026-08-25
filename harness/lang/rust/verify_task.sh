#!/usr/bin/env bash
# verify_rust_task.sh — Pre-graduation and post-graduation checker for Rust tasks.
# Usage: verify_rust_task.sh <task_id> [--stage]
#
# Without --stage: runs verify_task.py on tasks/rust/<id>/ (post-graduation)
# With --stage: stages wip/rust/<id>/ into a temp dir, runs all checks

set -euo pipefail

TASK_ID="${1:?usage: verify_rust_task.sh <task_id> [--stage]}"
STAGE="${2:-}"

BMK_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
WIP_DIR="$BMK_DIR/wip/rust/$TASK_ID"
TASKS_DIR="$BMK_DIR/tasks/rust/$TASK_ID"
TARGET_IMPORTS="$BMK_DIR/harness/lang/rust/target_imports.json"

export SPEC2REPO_TARGET_IMPORTS="$TARGET_IMPORTS"

errors=0
warn() { echo "  WARN: $*"; }
fail() { echo "  FAIL: $*"; errors=$((errors + 1)); }
pass() { echo "  PASS: $*"; }

if [ "$STAGE" = "--stage" ]; then
    echo "=== Staging wip/rust/$TASK_ID ==="
    STAGING=$(mktemp -d)
    TASK_STAGED="$STAGING/$TASK_ID"
    mkdir -p "$TASK_STAGED"

    # Copy oracle
    if [ -d "$WIP_DIR/oracle" ]; then
        cp -r "$WIP_DIR/oracle" "$TASK_STAGED/oracle"
    else
        fail "No oracle/ directory"
    fi

    # Stage spec.md (strip internal header if present)
    SPEC_SRC="$WIP_DIR/spec/spec_v1.md"
    if [ -f "$SPEC_SRC" ]; then
        # Strip HTML comment block at top (lines starting with <!-- through -->)
        python3 -c "
import re, sys
text = open('$SPEC_SRC', encoding='utf-8').read()
# Remove leading HTML comment block
text = re.sub(r'^<!--.*?-->\s*\n?', '', text, count=1, flags=re.DOTALL)
sys.stdout.write(text)
" > "$TASK_STAGED/spec.md"
    else
        fail "No spec/spec_v1.md"
    fi

    # Copy task.json if it exists
    if [ -f "$WIP_DIR/task.json" ]; then
        cp "$WIP_DIR/task.json" "$TASK_STAGED/task.json"
    else
        warn "No task.json (will fail verify_task)"
    fi

    export SPEC2REPO_TASKS_DIR="$STAGING"
    CHECK_DIR="$TASK_STAGED"
    echo "  Staged to $STAGING"
else
    CHECK_DIR="$TASKS_DIR"
    if [ ! -d "$CHECK_DIR" ]; then
        echo "FAIL: tasks/rust/$TASK_ID/ does not exist. Use --stage for wip tasks."
        exit 1
    fi
    # The in-repo checker resolves tasks/rust/<id> through harness/core/layout.py,
    # so no sibling checkout or environment override is needed.
fi

echo ""
echo "=== 1. Oracle Import Lint ==="
LINT_FILE="$WIP_DIR/filter/lint_result.txt"
if [ -f "$LINT_FILE" ]; then
    FIRST_LINE=$(head -1 "$LINT_FILE")
    if [[ "$FIRST_LINE" == "LINT_PASS"* ]]; then
        pass "lint_result.txt starts with LINT_PASS"
    else
        fail "lint_result.txt first line: $FIRST_LINE"
    fi
else
    fail "No filter/lint_result.txt"
fi

echo ""
echo "=== 2. Test Counts ==="
if [ -d "$WIP_DIR/oracle" ]; then
    ATOMIC=$(grep -r '#\[test\]' "$WIP_DIR/oracle/atomic/" 2>/dev/null | wc -l)
    INTEG=$(grep -r '#\[test\]' "$WIP_DIR/oracle/integration/" 2>/dev/null | wc -l)
    TOTAL=$((ATOMIC + INTEG))
    echo "  atomic=$ATOMIC integ=$INTEG total=$TOTAL"
    [ $ATOMIC -ge 30 ] && pass "atomic >= 30" || fail "atomic $ATOMIC < 30"
    [ $INTEG -ge 25 ] && pass "integ >= 25" || fail "integ $INTEG < 25"
    [ $TOTAL -ge 60 ] && pass "total >= 60" || fail "total $TOTAL < 60"
fi

echo ""
echo "=== 3. Reference Score ==="
# Rule 4 is non-negotiable, so this check must move the error counter. Either
# evidence path is accepted: the eval run, or the gate runner's bookkeeping file.
REF_RESULT="$WIP_DIR/eval/runs/reference/$TASK_ID/result.json"
REF_BOOK="$WIP_DIR/filter/reference_score.json"
REF_VERDICT=$(python3 - "$REF_RESULT" "$REF_BOOK" <<'PYEOF'
import json, os, sys
run, book = sys.argv[1], sys.argv[2]
if os.path.isfile(run):
    s = json.load(open(run)).get("score", {})
    if s.get("status") == "ok":
        if s.get("atomic_rate") == 1.0 and s.get("integ_rate") == 1.0:
            print("PASS reference 100% (eval/runs/reference)")
            raise SystemExit
        print(f"FAIL reference a={s.get('atomic_rate')} i={s.get('integ_rate')}")
        raise SystemExit
if os.path.isfile(book):
    d = json.load(open(book))
    if d.get("pass_rate") == 1.0 and d.get("failed", 1) == 0 and d.get("errors", 1) == 0:
        print(f"PASS reference {d['passed']}/{d['total']} = 100% (filter/reference_score.json)")
    else:
        print(f"FAIL reference pass_rate={d.get('pass_rate')} failed={d.get('failed')} errors={d.get('errors')}")
    raise SystemExit
print("FAIL no reference evidence: neither eval/runs/reference nor filter/reference_score.json")
PYEOF
)
case "$REF_VERDICT" in
    PASS*) pass "${REF_VERDICT#PASS }" ;;
    *)     fail "${REF_VERDICT#FAIL }" ;;
esac

echo ""
echo "=== 4. Dummy Score ==="
DUMMY_RESULT="$WIP_DIR/eval/runs/dummy/$TASK_ID/result.json"
if [ -f "$DUMMY_RESULT" ]; then
    python3 -c "
import json
d = json.load(open('$DUMMY_RESULT'))
s = d['score']
if s['status'] == 'ok' and s['atomic_passed'] == 0 and s['integ_passed'] == 0:
    print('  PASS: dummy 0%')
else:
    print(f'  FAIL: dummy a={s.get(\"atomic_passed\",\"?\")}/{s.get(\"atomic_total\",\"?\")}, i={s.get(\"integ_passed\",\"?\")}/{s.get(\"integ_total\",\"?\")}')
"
elif [ -f "$WIP_DIR/oracle/gates/run_dummy.log" ]; then
    DUMMY_OK=$(grep -c '^  ok ' "$WIP_DIR/oracle/gates/run_dummy.log" || true)
    DUMMY_FAIL=$(grep -c '^  failed ' "$WIP_DIR/oracle/gates/run_dummy.log" || true)
    if [ "$DUMMY_OK" -eq 0 ] && [ "$DUMMY_FAIL" -gt 0 ]; then
        pass "dummy 0% ($DUMMY_FAIL reported failed, 0 ok — oracle/gates/run_dummy.log)"
    else
        fail "dummy log shows $DUMMY_OK ok / $DUMMY_FAIL failed"
    fi
else
    fail "No dummy result.json and no oracle/gates/run_dummy.log"
fi

echo ""
echo "=== 5. Probe Score ==="
# Newest first. Taking the first match in a fixed order silently reports a stale
# probe when a task has been re-measured, which is how a 41.2% reading survived
# alongside a fresh 51.8% one on the same task.
PROBE_RUNS=$( { ls -1dt "$WIP_DIR"/eval/runs/sigfix "$WIP_DIR"/eval/runs/_probe_sigfix \
                     "$WIP_DIR"/eval/runs/probe-qwen3.8-max 2>/dev/null || true; } \
             | sed "s|.*/eval/runs/||" || true)
for run in $PROBE_RUNS; do
    PROBE_RESULT="$WIP_DIR/eval/runs/$run/$TASK_ID/result.json"
    if [ -f "$PROBE_RESULT" ]; then
        # This verdict has to move the error counter: the 50% ceiling is an
        # admission criterion, and a bare print let a 67.2% task report
        # "ALL CHECKS PASSED".
        PROBE_VERDICT=$(python3 - "$PROBE_RESULT" "$run" <<'PYEOF'
import json, sys
s = json.load(open(sys.argv[1]))["score"]
run = sys.argv[2]
if s.get("status") == "ok":
    total = s["atomic_passed"] + s["integ_passed"]
    denom = s["atomic_total"] + s["integ_total"]
    pct = 100 * total / denom if denom else 0
    label = "PASS" if pct < 50 else "FAIL"
    print(f"{label} {run} score {total}/{denom} = {pct:.1f}%")
else:
    print(f"FAIL {run} status={s.get('status')} — not a valid measurement")
PYEOF
)
        case "$PROBE_VERDICT" in
            PASS*) pass "${PROBE_VERDICT#PASS }" ;;
            *)     fail "${PROBE_VERDICT#FAIL }" ;;
        esac
        break
    fi
done

echo ""
echo "=== 6. verify_task.py ==="
if [ -f "$CHECK_DIR/task.json" ] && [ -f "$CHECK_DIR/spec.md" ]; then
    cd "$BMK_DIR"
    RESULT=$(python3 harness/core/verify_task.py "$TASK_ID" 2>&1) || true
    echo "$RESULT" | head -20
    if echo "$RESULT" | grep -q "STATIC_VALID"; then
        pass "verify_task: STATIC_VALID"
    else
        fail "verify_task: not STATIC_VALID"
    fi
else
    warn "Skipping verify_task (missing spec.md or task.json)"
fi

echo ""
echo "=== 7. DependsOn Coverage ==="
if [ -d "$WIP_DIR/oracle/integration" ]; then
    TOTAL_INTEG=$(grep -r '#\[test\]' "$WIP_DIR/oracle/integration/" 2>/dev/null | wc -l)
    WITH_DEPS=$(grep -r '// DependsOn:' "$WIP_DIR/oracle/integration/" 2>/dev/null | wc -l)
    if [ $TOTAL_INTEG -gt 0 ]; then
        PCT=$(python3 -c "print(f'{$WITH_DEPS/$TOTAL_INTEG*100:.0f}')")
        [ $WITH_DEPS -ge $((TOTAL_INTEG / 2)) ] && pass "DependsOn $WITH_DEPS/$TOTAL_INTEG = ${PCT}% >= 50%" || fail "DependsOn $WITH_DEPS/$TOTAL_INTEG = ${PCT}% < 50%"
    fi
fi

echo ""
echo "=== 8. Candidate Spec Staging ==="
STAGED_SPEC="$WIP_DIR/eval/tasks/$TASK_ID/spec.md"
if [ -L "$STAGED_SPEC" ]; then
    # docker cp without -L copies the link, leaving /workspace/spec.md dangling
    # inside the container. The candidate then builds from recall and the score
    # measures nothing.
    fail "staged spec.md is a symlink; stage a real file"
elif [ -f "$STAGED_SPEC" ]; then
    SPEC_LINES=$(wc -l < "$STAGED_SPEC")
    if [ "$SPEC_LINES" -lt 50 ]; then
        fail "staged spec.md has only $SPEC_LINES lines"
    elif head -1 "$STAGED_SPEC" | grep -q '<!--'; then
        fail "staged spec.md still carries the INTERNAL header"
    elif grep -q '<!-- INTERNAL' "$STAGED_SPEC"; then
        fail "staged spec.md contains an INTERNAL block"
    else
        pass "staged spec.md is a real file, $SPEC_LINES lines, no INTERNAL block"
    fi
else
    warn "No staged candidate spec at eval/tasks/$TASK_ID/spec.md"
fi

echo ""
echo "=== 9. Mutation controls ==="
# Mutation is product design applied when the spec is written, not a later stage
# (AGENTS.md Rule 6a). What must exist on disk:
#   - task.json.mutation naming the clauses/families and the tests that diverge
#   - ROOT-MAP.json, preregistered, passing the gate-design audit
#   - a clean-upstream (M2) control log showing exactly that set failing
#   - // MUTATED: markers on the diverging oracle tests
# The reference gate at 100% already serves as M1, so it is not re-checked here.
MUT_JSON=$(python3 - "$CHECK_DIR/task.json" <<'PYMUT'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8-sig"))
except Exception as e:
    print("FAIL cannot read task.json: %s" % e); raise SystemExit
m = d.get("mutation")
if not m:
    print("FAIL task.json carries no mutation block"); raise SystemExit
tests = m.get("tests") or []
clauses = m.get("clauses") or []
fams = m.get("families") or []
if len(tests) < 2:
    print("FAIL mutation.tests lists %d test(s); need >= 2 that diverge" % len(tests)); raise SystemExit
if not clauses:
    print("FAIL mutation.clauses is empty"); raise SystemExit
print("PASS mutation: %d clause(s), %d family(ies), %d diverging test(s)" % (len(clauses), len(fams), len(tests)))
PYMUT
)
case "$MUT_JSON" in
    PASS*) pass "${MUT_JSON#PASS }" ;;
    *)     fail "${MUT_JSON#FAIL }" ;;
esac

# ROOT-MAP.json: preregistered design, audited. Thresholds follow AGENTS.md Rule 8 —
# every task needs at least one measured family, and only a task scoring >= 50% needs the
# mutation-rich union as well. The audit exits non-zero on a violation, so it is run with
# `set +e` and no pipe: `set -euo pipefail` would otherwise abort the whole checker here.
ROOTMAP=""
for cand in "$WIP_DIR/ROOT-MAP.json" "$WIP_DIR/filter/ROOT-MAP.json" "$CHECK_DIR/ROOT-MAP.json"; do
    [ -f "$cand" ] && ROOTMAP="$cand" && break
done
if [ -n "$ROOTMAP" ]; then
    SCORE_PCT=$(python3 - "$CHECK_DIR/task.json" <<'PYSC'
import json, sys, re
try:
    d = json.load(open(sys.argv[1], encoding="utf-8-sig"))
except Exception:
    print("0"); raise SystemExit
# Characterise the task by the MEDIAN of its samples, not the maximum. Taking the
# maximum would let one high draw force the pass-rate instrument onto a task whose
# distribution already sits below the ceiling — the same conflation AGENTS.md Rule 8
# corrects. See Rule 9.
vals = []
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("score_pct", "candidate_score") and isinstance(v, (int, float)):
                vals.append(float(v))
            walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(d)
if not vals:
    print("0.0")
else:
    vals.sort()
    n = len(vals)
    med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
    print(f"{med:.1f}")
PYSC
)
    if python3 -c "import sys; sys.exit(0 if float('$SCORE_PCT') >= 50.0 else 1)"; then
        AUDIT_ARGS="--mutation-min 0.25 --mutation-max 0.75 --family-max-share 0.25"
        AUDIT_MODE="mutation-rich (score ${SCORE_PCT}% >= 50)"
    else
        AUDIT_ARGS="--mutation-min 0.0 --mutation-max 1.0 --family-max-share 1.0"
        AUDIT_MODE="structural only (score ${SCORE_PCT}% < 50)"
    fi
    set +e
    AUDIT=$(python3 "$BMK_DIR/skills/spec2repo-gate-calibration/scripts/audit_gate_design.py" \
              "$ROOTMAP" $AUDIT_ARGS 2>&1)
    AUDIT_RC=$?
    set -e
    if [ "$AUDIT_RC" -eq 0 ]; then
        pass "ROOT-MAP.json design audit clean — $AUDIT_MODE"
    else
        fail "ROOT-MAP.json audit violation ($AUDIT_MODE): $(printf '%s' "$AUDIT" | tr '\n' ' ' | cut -c1-300)"
    fi
else
    fail "no ROOT-MAP.json found (register the root inventory from the measured mutation set)"
fi

# clean-upstream (M2) control log
M2LOG=""
for cand in "$WIP_DIR/oracle/gates/run_clean_upstream.log" "$WIP_DIR/mutation/gate_m2_unpatched.log"; do
    [ -f "$cand" ] && M2LOG="$cand" && break
done
if [ -n "$M2LOG" ]; then
    pass "clean-upstream (M2) control log present ($(basename "$M2LOG"))"
else
    fail "no clean-upstream (M2) control log under oracle/gates/ or mutation/"
fi

# KNOWN-ISSUE (2026-08-25): this line reads $WIP_DIR, not $CHECK_DIR, and that part is
# deliberate -- the graduated oracle under tasks/ has its markers stripped, since publishing
# them would name the diverging tests. The defect is what follows from it: the check cannot
# tell a live mutation from an abandoned attempt. gix-config-file-001 carries no mutation
# block and zero markers under tasks/, yet two marked files survive in wip/ from three
# rejected targets, so it passes this line. Read a PASS here as "markers exist somewhere in
# wip" only; the task.json mutation block checked above is the authority on whether a
# mutation is actually in force. Left unchanged on purpose -- tightening it means deciding
# where the marker record for a published task should live, which is a design question.
MARKED=$(grep -rl '// MUTATED:' "$WIP_DIR/oracle" 2>/dev/null | wc -l)
[ "$MARKED" -ge 1 ] && pass "oracle carries // MUTATED: markers" || fail "no // MUTATED: marker found in oracle"

echo ""
echo "=== Summary ==="
if [ $errors -eq 0 ]; then
    echo "ALL CHECKS PASSED"
else
    echo "$errors FAILURE(S)"
fi

# Cleanup staging
if [ -n "${STAGING:-}" ] && [ -d "${STAGING:-}" ]; then
    rm -rf "$STAGING"
fi

exit $errors
