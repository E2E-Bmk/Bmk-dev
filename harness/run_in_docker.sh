#!/usr/bin/env bash
set -euo pipefail

IMAGE="${SCORER_IMAGE:-scorer-image}"

usage() {
  cat >&2 <<'EOF'
usage: run_in_docker.sh --source-repo PATH --solution-dir PATH --nodeids PATH --run-dir PATH [score_pytest_original.py args...]
EOF
}

host_path() {
  local path="$1"
  if [[ "$path" =~ ^[A-Za-z]:[\\/] ]]; then
    if command -v wslpath >/dev/null 2>&1; then
      wslpath -a "$path"
      return
    fi
    if command -v cygpath >/dev/null 2>&1; then
      cygpath -a "$path"
      return
    fi
  fi
  if command -v realpath >/dev/null 2>&1; then
    realpath -m "$path"
  else
    printf '%s\n' "$path"
  fi
}

basename_of() {
  local path="${1//\\//}"
  printf '%s\n' "${path##*/}"
}

source_repo=""
solution_dir=""
nodeids=""
run_dir=""
taxonomy=""
json_out=""
args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-repo)
      source_repo="$2"
      args+=("$1" "/workspace/source_repo")
      shift 2
      ;;
    --solution-dir)
      solution_dir="$2"
      args+=("$1" "/workspace/solution")
      shift 2
      ;;
    --nodeids)
      nodeids="$2"
      args+=("$1" "/workspace/nodeids/$(basename_of "$2")")
      shift 2
      ;;
    --run-dir)
      run_dir="$2"
      args+=("$1" "/workspace/run_dir")
      shift 2
      ;;
    --taxonomy)
      taxonomy="$2"
      args+=("$1" "/workspace/taxonomy/$(basename_of "$2")")
      shift 2
      ;;
    --json-out)
      json_out="$2"
      args+=("$1" "/workspace/json_out/$(basename_of "$2")")
      shift 2
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$source_repo" || -z "$solution_dir" || -z "$nodeids" || -z "$run_dir" ]]; then
  usage
  exit 2
fi

source_repo_host="$(host_path "$source_repo")"
solution_dir_host="$(host_path "$solution_dir")"
nodeids_host="$(host_path "$nodeids")"
nodeids_dir_host="$(dirname "$nodeids_host")"
run_dir_host="$(host_path "$run_dir")"
mkdir -p "$run_dir_host"

docker_args=(
  run --rm
  -v "${source_repo_host}:/workspace/source_repo:ro"
  -v "${solution_dir_host}:/workspace/solution:ro"
  -v "${run_dir_host}:/workspace/run_dir"
  -v "${nodeids_dir_host}:/workspace/nodeids:ro"
)

if [[ -n "$taxonomy" ]]; then
  taxonomy_host="$(host_path "$taxonomy")"
  docker_args+=(-v "$(dirname "$taxonomy_host"):/workspace/taxonomy:ro")
fi

if [[ -n "$json_out" ]]; then
  json_out_host="$(host_path "$json_out")"
  json_out_dir_host="$(dirname "$json_out_host")"
  mkdir -p "$json_out_dir_host"
  docker_args+=(-v "${json_out_dir_host}:/workspace/json_out")
fi

exec docker "${docker_args[@]}" "$IMAGE" "${args[@]}"
