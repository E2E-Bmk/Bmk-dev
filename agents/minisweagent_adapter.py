"""
mini-swe-agent adapter — tool_call mode + isolated Docker.

Flow:
  Host (any OS)                         Container (Linux --network=none)
  ─────────────                         ──────────────────────────────────
  spec.md        ──docker cp──>  /workspace/spec.md
                                 Agent bash commands execute here
                 <──docker cp──  /workspace/*  → host workspace_path

The agent process runs on HOST (needs internet for LLM API).
Bash commands run inside Docker with --network=none.
All container-internal paths are pure Linux; no host paths leak.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from .base import AgentConfig, AgentResult, BaseAgent

logger = logging.getLogger("spec2repo.agent")

#: What differs between languages when writing an implementation from a spec.
#:
#: Every entry is checked against that language's `Appendix A: Environment`,
#: because the agent prompt and the spec have to describe the same container.
#: A Go task told to produce `pyproject.toml`, or a Rust task told `pytest` is
#: available, gets a candidate that cannot score — and a candidate that cannot
#: score is indistinguishable from a task that is merely hard.
LANGUAGE_PROFILES = {
    "python": {
        "display": "Python",
        "packaging": (
            "Include pyproject.toml (or setup.py) so the package is pip-installable."
        ),
        "verify": (
            "`pytest` is available — write and run your own tests locally to verify "
            "behavior before finishing."
        ),
        "deps": (
            "The third-party packages listed in the spec's Environment section are "
            "already installed in this container, and the same packages are installed "
            "in the assessment environment."
        ),
    },
    "go": {
        "display": "Go",
        "packaging": (
            "Include a go.mod at /workspace declaring the module path the spec names, "
            "with a language version no higher than the installed toolchain."
        ),
        "verify": (
            "`go build ./...`, `go vet ./...` and `go test ./...` all work offline — "
            "write your own _test.go files and run them before finishing."
        ),
        "deps": (
            "The module must declare NO dependency outside the Go standard library: "
            "the module cache is empty and nothing can be downloaded."
        ),
    },
    "rust": {
        "display": "Rust",
        "packaging": (
            "Include a Cargo.toml at /workspace declaring a library crate with exactly "
            "the crate name and edition the spec names. The library target must be the "
            "default one."
        ),
        "verify": (
            "`cargo build` and `cargo test` work offline — add your own tests and run "
            "them before finishing."
        ),
        "deps": (
            "Only the crates named in the spec's Environment appendix are vendored and "
            "available offline; declaring any other dependency fails to resolve."
        ),
    },
    "typescript": {
        "display": "TypeScript/Node.js",
        "packaging": (
            "Include a package.json at /workspace with the package name the spec names "
            "and a root entry point Node resolves through `main`, `exports`, or both. "
            "If you write TypeScript, you MUST also ship the compiled JavaScript that "
            "entry point refers to: the assessment installs this directory as a package "
            "and imports it by name, and it never runs a build step for you."
        ),
        "verify": (
            "`node`, `npx tsc` and `npx vitest run` are available offline — compile and "
            "run your own tests before finishing."
        ),
        "deps": (
            "Only the Node.js standard library is available at run time; no third-party "
            "runtime dependency can be installed."
        ),
    },
    "java": {
        "display": "Java",
        "packaging": (
            "Include a Maven pom.xml at /workspace producing a jar under exactly the "
            "groupId, artifactId and version the spec names, with sources under "
            "src/main/java and resources under src/main/resources."
        ),
        "verify": (
            "`mvn -o -DskipTests install` and `mvn -o test` work offline against the "
            "pre-populated local repository — add your own JUnit 5 tests and run them "
            "before finishing."
        ),
        "deps": (
            "Only the artifacts named in the spec's Environment appendix are present in "
            "the local Maven repository; Maven is offline and resolves nothing else."
        ),
    },
}

SYSTEM_PROMPT = """\
You are a senior software engineer. You can execute bash commands in an isolated Linux container.
Your task is to implement a complete {display} package from a specification document.

Rules:
- The spec is at /workspace/spec.md. Read it carefully FIRST.
- Implement ALL source code in /workspace/.
- {packaging}
- There is NO internet access. {deps}
- {verify}
- Work step by step: read spec → plan structure → create files → verify the public
  surface and the behavior it describes.
- When finished, run: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT
"""

INSTANCE_PROMPT = """\
Implement the {display} package described in /workspace/spec.md.

The spec is {spec_kb} KB. Any command whose output exceeds 10000 characters
reaches you with only its first and last 5000, so `cat` on a file this size
would silently hide most of it. Read it in order, in slices you can hold:
`sed -n '1,250p' /workspace/spec.md`, then `251,500p`, and so on to the end.
`wc -l /workspace/spec.md` tells you how far that is. Read every slice before
you write code — a section you skipped is a behaviour you will not implement.

Requirements:
1. Read the whole spec first, sliced as above
2. Create all necessary source files in /workspace/
3. The package must be importable under the name the spec gives it
4. {packaging}
5. Verify your implementation behaves as specified: build it, exercise the main
   workflows from the spec, and run any tests you wrote. {verify}
6. When done: `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`

<system_information>
{{{{system}}}} {{{{release}}}} {{{{version}}}} {{{{machine}}}}
</system_information>
"""

#: Language images carrying the toolchain, used when no per-task agent image
#: exists. These are the same images the scoring sandbox uses, and they were
#: checked to contain neither the target package nor its source.
LANGUAGE_IMAGES = {
    "go": "spec2repo-go:latest",
    "rust": "spec2repo-rust:latest",
    "typescript": "spec2repo-typescript:latest",
    "java": "spec2repo-java:latest",
}

BASE_IMAGE = "spec2repo-base:latest"

#: Ceiling on one command inside the agent container, by language. 120s was
#: sized for ``pytest``. A cold ``cargo build``, ``mvn -o install`` or ``tsc``
#: runs well past it, and the overrun reaches the model as ``returncode: -1``
#: — indistinguishable from its own command failing, so it edits code that was
#: never actually broken. The scoring sandbox refused a single constant for the
#: same reason; see ``harness/sandbox.py``.
COMMAND_TIMEOUT = {
    "python": 120,
    "go": 600,
    "typescript": 600,
    "java": 900,
    "rust": 1200,
}

#: Memory ceiling by language. 1g holds a Python interpreter. It does not hold
#: rustc linking a dependency graph, nor a JVM alongside Maven, and the OOM kill
#: arrives disguised as a failed build rather than as a resource error.
AGENT_MEMORY = {
    "python": "1g",
    "go": "2g",
    "typescript": "2g",
    "java": "3g",
    "rust": "4g",
}

#: ``bash -lc`` is mini-swe-agent's default. A login shell re-sources
#: ``/etc/profile``, which overwrites ``PATH`` with the distribution default and
#: drops anything the image added through Docker ``ENV``. In
#: ``spec2repo-agent-rust`` that is ``/usr/local/cargo/bin``, so every ``cargo``
#: and ``rustc`` call the agent makes answers ``command not found`` — it writes
#: the whole crate unable to compile it once. Dropping ``-l`` keeps the
#: container's own environment, which is what the scoring side already runs
#: under.
INTERPRETER = ["bash", "-c"]


#: Warming the dependency cache also drags in the crate the task is *about*:
#: ``gix-protocol`` depends on ``gix-ref`` non-optionally, so preheating one
#: preheats the other, and cargo leaves the sources extracted under
#: ``registry/src``. The agent would then be reconstructing ``gix-ref`` from a
#: specification with the real ``gix-ref`` readable on the same filesystem.
#:
#: Trajectory audit of the first ten scored Rust runs found zero reads of the
#: crate under test, so no score to date is contaminated — but the exposure is
#: real and silent, and a single agent that thinks to look scores 100% for the
#: wrong reason. Scrubbed per-run rather than removed from the image, because
#: the same crate is a legitimate dependency of other tasks.
def _scrub_crate_under_test(cid: str, task_id: str) -> list[str]:
    """Delete the crate the task delivers from the container's cargo registry.

    Task ids are ``<crate>-<carve>-<NNN>``, and the crate name itself contains
    hyphens, so the boundary is found by testing successively longer prefixes
    against what is actually present rather than by guessing where it falls.
    Matching requires a version digit right after the name: ``gix-config-1`` is
    the crate under test, ``gix-config-value-0.19.1`` is a dependency that must
    survive.
    """
    parts = task_id.split("-")
    names = ["-".join(parts[:i]) for i in range(1, len(parts))]
    if not names:
        return []
    patterns = " ".join(
        f"'{n}'" for n in names
    )
    script = f"""
    set -u
    removed=""
    for name in {patterns}; do
      for base in "$CARGO_HOME"/registry/src/*/ "$CARGO_HOME"/registry/cache/*/; do
        [ -d "$base" ] || continue
        for hit in "$base$name"-[0-9]*; do
          [ -e "$hit" ] || continue
          rm -rf "$hit" && removed="$removed $(basename "$hit")"
        done
      done
    done
    echo "$removed"
    """
    probe = subprocess.run(
        ["docker", "exec", cid, "bash", "-c", script],
        capture_output=True, text=True, timeout=60,
    )
    return probe.stdout.split()


def _image_exists(tag: str) -> bool:
    probe = subprocess.run(
        ["docker", "image", "inspect", tag],
        capture_output=True, timeout=15,
    )
    return probe.returncode == 0


def agent_image_for(task_id: str, language: str = "python") -> str:
    """Pick the container the agent writes code in.

    Preference order, most task-specific first:

    1. ``spec2repo-agent-<task_id>`` — oracle deps preinstalled, target package
       stripped. Built by ``docker/build_images.py --agent-images`` (Python only).
    2. ``spec2repo-agent-<language>`` — the language toolchain plus the
       dependency set that language's specs promise, vendored for offline use.
    3. ``spec2repo-<language>`` — the scoring image: toolchain, no dependencies.
    4. ``spec2repo-base`` — Python only.

    The base image contains python3 and nothing else, so a compiled-language
    task that reaches step 4 produces a candidate written entirely blind. That
    scores near zero and reads exactly like a hard task, so it is logged as an
    error rather than passed over quietly.
    """
    language = (language or "python").lower()

    for tag in (
        f"spec2repo-agent-{task_id}:latest",
        f"spec2repo-agent-{language}:latest",
        LANGUAGE_IMAGES.get(language, ""),
    ):
        if tag and _image_exists(tag):
            return tag

    if language != "python":
        logger.error(
            "[%s] no %s toolchain image found (tried spec2repo-agent-%s, "
            "spec2repo-agent-%s, %s); falling back to %s, which has no %s "
            "compiler. The candidate will be written without being able to "
            "build or test, and the resulting score will understate the model.",
            task_id, language, task_id, language,
            LANGUAGE_IMAGES.get(language, "<no language image>"),
            BASE_IMAGE, language,
        )
    return BASE_IMAGE


class MiniSweAgentAdapter(BaseAgent):
    """
    Run tasks using mini-swe-agent (tool_call mode) + Docker isolation.

    The agent loop runs on the host; bash tool-calls execute inside
    a Docker container with --network=none.  After the agent finishes,
    generated files are copied out via `docker cp`.
    """

    def solve(self, task_id: str, spec_path: Path, workspace_path: Path,
              language: str = "python") -> AgentResult:
        start = time.time()
        cost = 0.0
        n_calls = 0
        language = (language or "python").lower()
        profile = LANGUAGE_PROFILES.get(language)
        if profile is None:
            logger.warning("[%s] unknown language %r; using the Python profile",
                           task_id, language)
            profile = LANGUAGE_PROFILES["python"]
        # The prompt tells the agent how large the spec is so it can plan its
        # reads. Measured here rather than hard-coded: specs range from 10 KB to
        # over 120 KB, and the advice is only useful if it matches the file the
        # agent actually receives.
        try:
            spec_kb = max(1, round(spec_path.stat().st_size / 1024))
        except OSError:
            spec_kb = 0
        profile = {**profile, "spec_kb": spec_kb}

        agent = None
        env = None
        try:
            from minisweagent.agents.default import DefaultAgent
            from minisweagent.models.litellm_model import LitellmModel
            from minisweagent.environments.docker import DockerEnvironment
        except ImportError as e:
            return AgentResult(
                task_id=task_id, workspace_path=workspace_path,
                success=False, elapsed_seconds=time.time() - start,
                error=f"mini-swe-agent not installed: {e}",
            )

        try:
            model_kwargs = {"drop_params": True}
            if self.config.api_key:
                model_kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                model_kwargs["api_base"] = self.config.base_url
            # Gateway-specific parameters from config.json, forwarded verbatim.
            # `drop_params` above means an unrecognised one is discarded by
            # litellm rather than failing the call.
            model_kwargs.update(self.config.extra_params)

            model = LitellmModel(
                model_name=self.config.model,
                model_kwargs=model_kwargs,
                cost_tracking="ignore_errors",
                observation_template=(
                    "{%- if output.output | length < 10000 -%}"
                    '{"returncode": {{ output.returncode }}, "output": {{ output.output | tojson }}'
                    "{% if output.exception_info %}, \"exception_info\": {{ output.exception_info | tojson }}{% endif %}"
                    "}"
                    "{%- else -%}"
                    '{"returncode": {{ output.returncode }}, '
                    '"output_head": {{ output.output[:5000] | tojson }}, '
                    '"output_tail": {{ output.output[-5000:] | tojson }}, '
                    '"warning": "Output truncated"'
                    "{% if output.exception_info %}, \"exception_info\": {{ output.exception_info | tojson }}{% endif %}"
                    "}"
                    "{%- endif -%}"
                ),
                format_error_template=(
                    "{% if finish_reason is defined and finish_reason == 'length' -%}"
                    "Output token limit reached. Be more concise and finish with a bash tool call."
                    "{%- else -%}"
                    "Tool call error: {{error}}. "
                    'Every response MUST include at least one bash tool call with {"command": "..."}. '
                    "To finish: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"
                    "{%- endif %}"
                ),
            )

            # Docker environment — pure Linux, network isolated
            image = agent_image_for(task_id, language)
            lang = (language or "python").lower()
            env = DockerEnvironment(
                image=image,
                cwd="/workspace",
                interpreter=INTERPRETER,
                run_args=[
                    "--network=none",
                    f"--memory={AGENT_MEMORY.get(lang, '1g')}",
                    f"--cpus={self.config.max_cpus}",
                    "--pids-limit=512",
                    "--security-opt=no-new-privileges",
                ],
                timeout=COMMAND_TIMEOUT.get(lang, 120),
                env={
                    "PAGER": "cat",
                    "MANPAGER": "cat",
                    "PIP_PROGRESS_BAR": "off",
                    "TQDM_DISABLE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    # Progress bars and colour codes are pure noise once the
                    # transcript is the model's only view of the container.
                    "CARGO_TERM_COLOR": "never",
                    "CARGO_TERM_PROGRESS_WHEN": "never",
                    "NPM_CONFIG_PROGRESS": "false",
                    "NO_COLOR": "1",
                },
            )

            # Inject spec via docker cp (host path → container Linux path)
            cid = env.container_id
            scrubbed = _scrub_crate_under_test(cid, task_id)
            logger.info("[%s] registry scrub removed: %s", task_id,
                        ", ".join(scrubbed) if scrubbed else "nothing")
            # -L dereferences a symlinked source. Without it docker cp copies
            # the link itself, so a pool assembled by symlinking spec.md leaves
            # a dangling /workspace/spec.md and the candidate builds from recall
            # instead of the spec -- a silently invalid run, not a low score.
            subprocess.run(
                ["docker", "cp", "-L", str(spec_path), f"{cid}:/workspace/spec.md"],
                check=True, capture_output=True, timeout=15,
            )
            probe = subprocess.run(
                ["docker", "exec", cid, "wc", "-l", "/workspace/spec.md"],
                capture_output=True, text=True, timeout=15,
            )
            if probe.returncode != 0 or not probe.stdout.split():
                raise RuntimeError(
                    f"spec.md unreadable inside container: {probe.stderr.strip()}"
                )
            spec_lines = int(probe.stdout.split()[0])
            if spec_lines < 50:
                raise RuntimeError(
                    f"spec.md staged with only {spec_lines} lines; refusing to run"
                )
            logger.info("[%s] spec.md staged: %d lines", task_id, spec_lines)

            agent = DefaultAgent(
                model=model,
                env=env,
                system_template=SYSTEM_PROMPT.format(**profile),
                instance_template=INSTANCE_PROMPT.format(**profile),
                # 0 disables the limit in mini-swe-agent. Budgets are recorded
                # in the result, never enforced, so pricing and gateway latency
                # cannot truncate a run and contaminate the score.
                step_limit=self.config.max_iterations,
                cost_limit=self.config.cost_limit,
                wall_time_limit_seconds=self.config.timeout_seconds,
            )

            logger.info("[%s] Agent start: lang=%s image=%s model=%s steps=%s wall=%s cost=%s",
                        task_id, language, image, self.config.model,
                        self.config.max_iterations or "unlimited",
                        f"{self.config.timeout_seconds}s" if self.config.timeout_seconds else "unlimited",
                        f"${self.config.cost_limit}" if self.config.cost_limit else "unlimited")

            result = agent.run()
            exit_status = (
                result.get("exit_status")
                or result.get("extra", {}).get("exit_status")
                or result.get("content")
                or "unknown"
            )
            cost = agent.cost
            n_calls = agent.n_calls
            logger.info("[%s] Agent done: status=%s calls=%d cost=$%.4f",
                        task_id, exit_status, n_calls, cost)

            # Extract workspace from container → host via docker cp
            workspace_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["docker", "cp", f"{cid}:/workspace/.", str(workspace_path)],
                check=True, capture_output=True, timeout=60,
            )

            # Save trajectory alongside workspace
            traj_path = workspace_path.parent / "trajectory.json"
            agent.save(traj_path)

            success = exit_status == "Submitted"
            error = None if success else f"agent exit status: {exit_status}"

        except Exception as e:
            logger.exception("[%s] Agent error", task_id)
            success = False
            error = f"{type(e).__name__}: {e}"
            exit_status = "error"
            # Usage consumed before the failure is still reportable data.
            if agent is not None:
                cost = getattr(agent, "cost", cost)
                n_calls = getattr(agent, "n_calls", n_calls)
        finally:
            if env is not None:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", env.container_id],
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                except Exception:
                    logger.warning("[%s] Failed to clean up agent container", task_id,
                                   exc_info=True)

        return AgentResult(
            task_id=task_id,
            workspace_path=workspace_path,
            success=success,
            elapsed_seconds=time.time() - start,
            cost=cost,
            n_calls=n_calls,
            error=error,
            exit_status=exit_status,
        )
