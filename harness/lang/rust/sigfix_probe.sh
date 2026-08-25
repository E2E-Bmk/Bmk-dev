#!/usr/bin/env bash
# sigfix_probe.sh — convert a Mechanism-9 build annihilation into a real score.
#
# A single signature divergence fails the whole cargo workspace and zeroes every
# assertion, so the run reports status=error and measures no behaviour at all.
# This stages the agent's own output, lets the operator patch ONLY signature
# divergences (types, arity, absent public items -> unimplemented!() stubs),
# and re-scores. Logic is never supplied, so every test still passes or fails on
# the candidate's own merits.
#
# Usage:
#   sigfix_probe.sh <task_id> stage           # copy agent workspace -> sigfix
#   sigfix_probe.sh <task_id> build           # compile against the oracle, show errors
#   sigfix_probe.sh <task_id> score           # re-score the patched workspace
#   sigfix_probe.sh <task_id> diff            # show what the patch changed

set -euo pipefail

ID="${1:?usage: sigfix_probe.sh <task_id> stage|build|score|diff}"
CMD="${2:?usage: sigfix_probe.sh <task_id> stage|build|score|diff}"
SRC_RUN="${3:-qwen3.8-max}"

BMK="$(cd "$(dirname "$0")/../../.." && pwd)"
S2R="${SPEC2REPO_DIR:-$BMK/../spec2repo}"
W="$BMK/wip/rust/$ID"
AGENT_WS="$W/eval/runs/$SRC_RUN/$ID/workspace"
SIGFIX_WS="$W/eval/runs/sigfix/$ID/workspace"

case "$CMD" in
stage)
    [ -d "$AGENT_WS" ] || { echo "no agent workspace at $AGENT_WS" >&2; exit 1; }
    rm -rf "$SIGFIX_WS"
    mkdir -p "$(dirname "$SIGFIX_WS")"
    cp -r "$AGENT_WS" "$SIGFIX_WS"
    rm -rf "$SIGFIX_WS/target"
    echo "staged $SIGFIX_WS"
    find "$SIGFIX_WS" -name '*.rs' | sed "s|$SIGFIX_WS/||"
    ;;

build)
    # Mirror what harness/lang/rust/runner.py does: candidate crate + oracle workspace,
    # with [patch.crates-io] redirecting the target crate at the candidate.
    rm -rf "$W/eval/oracle/$ID"
    mkdir -p "$W/eval/oracle"
    cp -r "$W/oracle" "$W/eval/oracle/$ID"
    rm -rf "$W/eval/oracle/$ID/target" "$W/eval/oracle/$ID/gates"

    CRATE=$(python3 -c "
import json;print(json.load(open('$W/eval/target_imports.json'))['$ID'][0])")
    BUILD=$(mktemp -d /tmp/sigfix-build-XXXXXX)
    cp -r "$SIGFIX_WS" "$BUILD/candidate"
    cp -r "$W/eval/oracle/$ID" "$BUILD/oracle"
    cat >> "$BUILD/oracle/Cargo.toml" <<EOF

[patch.crates-io]
$CRATE = { path = "/eval/workspace" }
EOF
    echo "=== building in $BUILD ==="
    mkdir -p /tmp/sigfix-cargo-cache-$ID
    docker run --rm \
        -v "$BUILD/oracle":/eval/oracle \
        -v "$BUILD/candidate":/eval/workspace \
        -v /tmp/sigfix-cargo-cache-$ID:/usr/local/cargo/registry \
        -w /eval spec2repo-rust:latest bash -c '
          cd /eval/workspace && cargo fetch 2>&1 | tail -3
          cd /eval/oracle    && cargo fetch 2>&1 | tail -3
          cd /eval/oracle    && cargo nextest run --no-run 2>&1 | tail -100
        '
    echo "build tree: $BUILD"
    ;;

score)
    export SPEC2REPO_TARGET_IMPORTS="$W/eval/target_imports.json"
    rm -rf "$W/eval/oracle/$ID"
    mkdir -p "$W/eval/oracle"
    cp -r "$W/oracle" "$W/eval/oracle/$ID"
    rm -rf "$W/eval/oracle/$ID/target" "$W/eval/oracle/$ID/gates"
    mkdir -p "$W/eval/runs/sigfix"
    cd "$S2R"
    # evaluate.py validates --model against the registered model config even
    # under --score-only, and "sigfix" is not a registered model. The run is
    # identified by its output directory instead, so result.json carries
    # model=qwen3.8-max while holding the SIGFIX score -- read runs/sigfix/.
    python3 harness/evaluate.py --score-only \
        --model qwen3.8-max \
        --tasks "$ID" \
        --tasks-dir "$W/eval/tasks" \
        --oracle-dir "$W/eval/oracle" \
        --output-dir "$W/eval/runs/sigfix"
    python3 -c "
import json
d=json.load(open('$W/eval/runs/sigfix/$ID/result.json'))
s=d['score']
if s['status']=='ok':
    t=s['atomic_passed']+s['integ_passed']; n=s['atomic_total']+s['integ_total']
    print(f\"SIGFIX $ID: {t}/{n} = {100*t/n:.1f}%  (a={s['atomic_passed']}/{s['atomic_total']} i={s['integ_passed']}/{s['integ_total']})\")
else:
    print(f\"SIGFIX $ID: status={s['status']} {s.get('error','')[:200]}\")
"
    ;;

diff)
    # `diff -rq` exits 1 when it finds differences, which under `set -e` would
    # abort before the verdict prints -- so capture, then decide.
    out=$(diff -rq "$AGENT_WS" "$SIGFIX_WS" 2>/dev/null | grep -v 'Only in.*target' || true)
    if [ -n "$out" ]; then echo "$out"; else echo "IDENTICAL — no patch landed"; fi
    ;;

*) echo "unknown command $CMD" >&2; exit 2 ;;
esac
