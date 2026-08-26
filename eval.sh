#!/usr/bin/env bash
# Spec2Repo evaluation one-stop entrypoint.
#
# Path-independent: resolves the repo from this script's own location, so it
# works from any checkout without hard-coded paths (clone and run).
#
# Subcommands:
#   run        run the evaluation pipeline (wraps harness/evaluate.py)
#   report     print an evaluation ledger    (wraps analysis/ledger.py)
#   attribute  print an attribution report   (wraps analysis/attribution.py)
#   clean      remove transient eval leftovers under results/ (dry-run default)
#
# Examples:
#   ./eval.sh run --model qwen3.8-max --tasks all
#   ./eval.sh run --model qwen3.8-max --tasks lsm-tree-001 --score-only
#   ./eval.sh run --model qwen3.8-max --tasks all --batch-timeout 600
#   ./eval.sh report --model qwen3.8-max --view avg
#   ./eval.sh attribute --model qwen3.8-max --view verify
#   ./eval.sh clean --force
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"
export PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

usage() { sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

cmd="${1:-}"; [ $# -gt 0 ] && shift || true
case "$cmd" in
  run)
    # Consume timeout knobs here (mapped to env the sandbox reads); everything
    # else is passed through to evaluate.py verbatim.
    pass=()
    while [ $# -gt 0 ]; do
      case "$1" in
        --batch-timeout) export SCORE_BATCH_TIMEOUT="$2"; shift 2;;
        --setup-timeout) export SCORE_SETUP_TIMEOUT="$2"; shift 2;;
        *) pass+=("$1"); shift;;
      esac
    done
    exec "$PY" harness/evaluate.py "${pass[@]}"
    ;;
  report)    exec "$PY" -m analysis.ledger "$@";;
  attribute) exec "$PY" -m analysis.attribution "$@";;
  clean)
    force=0; [ "${1:-}" = "--force" ] && force=1
    mapfile -t targets < <(
      { find results -maxdepth 2 -type d -name '*.old' 2>/dev/null;
        ls -d results/rerun3 results/rerun_timeout 2>/dev/null; } | sort -u)
    if [ "${#targets[@]}" -eq 0 ]; then echo "clean: nothing to remove"; exit 0; fi
    printf '%s\n' "${targets[@]}"
    if [ "$force" -eq 1 ]; then
      rm -rf "${targets[@]}"; echo "clean: removed ${#targets[@]} path(s)"
    else
      echo "clean: dry-run (${#targets[@]} path(s)); pass --force to delete"
    fi
    ;;
  ""|-h|--help|help) usage;;
  *) echo "unknown subcommand: $cmd" >&2; usage; exit 1;;
esac
