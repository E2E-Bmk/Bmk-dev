#!/usr/bin/env bash
# Stage 1 build-and-test probe for a Java candidate carve.
#
# candidate-selector rejects a repo whose test suite is absent, network-bound or
# unbuildable, and the four-language round established that a plausible-looking
# 0% is indistinguishable from a hard task. So every hard gate that can be
# measured is measured here, inside the same image the scorer uses, rather than
# inferred from the build files.
#
# Usage: java_stage1_probe.sh <repo> <tag> <module|.> [extra mvn args...]
#
#   repo    directory name under source-clones/
#   tag     git tag or commit to pin; the worktree is created detached at it
#   module  -pl argument, or "." for a single-module project
#
# Writes probe/reports/<repo>@<tag>[<module>].log and appends one row to
# probe/reports/SUMMARY.tsv. Reruns are idempotent: the worktree and the report
# are replaced.

set -uo pipefail

ROOT=/root/research/javabench
REPO=${1:?usage: java_stage1_probe.sh <repo> <tag> <module|.> [extra mvn args]}
TAG=${2:?missing tag}
MODULE=${3:?missing module (use . for single-module)}
shift 3
EXTRA=("$@")

# The Apache and Google parents wire release-time plugins into the default
# lifecycle. They fail without signing keys or a network, and none of them
# affects whether the tests pass, which is the only thing this probe measures.
#
# bnd is deliberately NOT skipped. maven-resolver generates META-INF/MANIFEST.MF
# with bnd-maven-plugin and maven-jar-plugin then requires that file, so skipping
# bnd turns a healthy repo into `Error assembling JAR: Manifest file ... does not
# exist` -- a false negative produced by the probe rather than by the candidate.
SKIPS=(
  -Dcheckstyle.skip -Drat.skip -Dspotbugs.skip -Denforcer.skip
  -Dmaven.javadoc.skip=true -Dgpg.skip -Danimal.sniffer.skip=true
  -Dmaven.source.skip=true -Dinvoker.skip=true
)

# Keyed on the module as well as repo and tag: two carves of one repo at one tag
# are two probes, and a shared path makes the second `git worktree add` fail.
WT=$ROOT/probe/${REPO}-${TAG//\//_}-$(echo "$MODULE" | tr '/.' '__')
REPORTS=$ROOT/probe/reports
LABEL="${REPO}@${TAG}[${MODULE}]"
LOG=$REPORTS/$(echo "$LABEL" | tr '/[]@' '____').log
CONTAINER=jb-s1-${REPO}
mkdir -p "$REPORTS"

# Reuse an existing worktree when it already sits at the requested commit: the
# probe is rerun whenever a build flag turns out wrong, and re-checking out costs
# a full rebuild. `git worktree add -f` refuses an existing directory, so a rerun
# has to either reuse or remove -- silently failing is what produced a
# WORKTREE_FAIL for a repo that was fine.
WANT=$(git -C "$ROOT/source-clones/$REPO" rev-parse "$TAG" 2>/dev/null)
HAVE=$(git -C "$WT" rev-parse HEAD 2>/dev/null)
if [ -n "$WANT" ] && [ "$WANT" = "$HAVE" ]; then
  :
else
  if [ -d "$WT" ]; then
    git -C "$ROOT/source-clones/$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || rm -rf "$WT"
    git -C "$ROOT/source-clones/$REPO" worktree prune >/dev/null 2>&1
  fi
  git -C "$ROOT/source-clones/$REPO" worktree add -f "$WT" "$TAG" >/dev/null 2>&1 \
    || { echo "WORKTREE_FAIL $LABEL"; exit 2; }
fi

docker rm -f "$CONTAINER" >/dev/null 2>&1
docker run -d --name "$CONTAINER" -v "$WT:/src" -w /src \
  spec2repo-java:latest sleep infinity >/dev/null || { echo "DOCKER_FAIL $LABEL"; exit 2; }

PL=()
[ "$MODULE" != "." ] && PL=(-pl "$MODULE" -am)

{
  echo "== $LABEL"
  echo "== commit $(git -C "$WT" rev-parse HEAD)"
  echo "== install -DskipTests"
} > "$LOG"

docker exec "$CONTAINER" mvn -B "${PL[@]}" install -DskipTests \
  "${SKIPS[@]}" "${EXTRA[@]}" >> "$LOG" 2>&1
BUILD_RC=$?

TEST_RC=skipped
TOTALS="-"
if [ "$BUILD_RC" -eq 0 ]; then
  PLT=()
  [ "$MODULE" != "." ] && PLT=(-pl "$MODULE")
  echo "== test" >> "$LOG"
  docker exec "$CONTAINER" mvn -B "${PLT[@]}" test \
    "${SKIPS[@]}" "${EXTRA[@]}" >> "$LOG" 2>&1
  TEST_RC=$?
  # Surefire prints a per-class "Tests run: ... - in <Class>" line for every
  # class and then, under a `Results:` banner, one cumulative line with no `- in`
  # suffix. Taking the last "Tests run:" line picks a single test class instead of
  # the total, which is how cache2k first reported "Tests run: 3" for a 1000-test
  # module. Select on the absence of the suffix instead of on position.
  TOTALS=$(grep -E "Tests run:" "$LOG" | grep -v -- " - in " | tail -1 \
           | sed 's/^\[INFO\] //' | tr -s ' ')
  [ -z "$TOTALS" ] && TOTALS="no-surefire-summary"
fi

docker rm -f "$CONTAINER" >/dev/null 2>&1

printf '%s\tbuild_rc=%s\ttest_rc=%s\t%s\n' "$LABEL" "$BUILD_RC" "$TEST_RC" "$TOTALS" \
  | tee -a "$REPORTS/SUMMARY.tsv"
