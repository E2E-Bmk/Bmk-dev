"""
OpenHands adapter with Docker isolation.

OpenHands manages its own container lifecycle.
We inject security constraints via environment variables.
"""

import json
import os
import subprocess
import time
from pathlib import Path

from .base import AgentConfig, AgentResult, BaseAgent


class OpenHandsAdapter(BaseAgent):
    """
    Run tasks using OpenHands in headless Docker mode.

    OpenHands runs its own sandbox internally.  We pass
    --network constraints via SANDBOX_NETWORK_MODE=none.
    """

    def solve(self, task_id: str, spec_path: Path, workspace_path: Path,
              language: str = "python") -> AgentResult:
        start = time.time()
        workspace_path.mkdir(parents=True, exist_ok=True)

        spec_dest = workspace_path / "spec.md"
        spec_dest.write_text(spec_path.read_text(encoding="utf-8"), encoding="utf-8")

        # OpenHands supplies its own runtime image, which is Python-oriented and
        # is not one of the spec2repo language images. Naming the language in
        # the prompt keeps the instructions honest, but it does not put a
        # toolchain in the sandbox: only Python tasks are supported here.
        language = (language or "python").lower()
        if language != "python":
            return AgentResult(
                task_id=task_id, workspace_path=workspace_path,
                success=False, elapsed_seconds=time.time() - start,
                error=(
                    f"openhands adapter supports Python only; task language is "
                    f"{language!r}. Its runtime image carries no {language} "
                    f"toolchain, so the candidate would be written blind. Use "
                    f"--agent minisweagent for this task."
                ),
                exit_status="unsupported_language",
            )

        prompt = (
            "Read /workspace/spec.md carefully. "
            "Implement the COMPLETE Python package described in it. "
            "Create all source files in /workspace with a proper pyproject.toml. "
            "The package must be pip-installable and importable as described in the spec. "
            "You have NO internet access inside the sandbox."
        )

        cmd = [
            "docker", "run", "--rm",
            "-e", "SANDBOX_RUNTIME_CONTAINER_IMAGE="
                  "docker.all-hands.dev/all-hands-ai/runtime:0.56-nikolaik",
            "-e", "LOG_ALL_EVENTS=true",
            "-e", f"LLM_MODEL={self.config.model}",
            "-e", f"LLM_API_KEY={self.config.api_key}",
            "-e", f"LLM_BASE_URL={self.config.base_url or ''}",
            "-e", "SANDBOX_NETWORK_MODE=none",
            "-e", f"MAX_ITERATIONS={self.config.max_iterations}",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-v", f"{workspace_path}:/workspace:rw",
            "--add-host", "host.docker.internal:host-gateway",
            "--network=bridge",
            "docker.all-hands.dev/all-hands-ai/openhands:0.56",
            "python", "-m", "openhands.core.main",
            "-t", prompt,
        ]

        try:
            # timeout_seconds == 0 means unlimited; None disables the timeout.
            timeout = self.config.timeout_seconds + 120 if self.config.timeout_seconds else None
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            success = r.returncode == 0
            error = r.stderr[:500] if not success else None
        except subprocess.TimeoutExpired:
            success, error = False, "OpenHands timed out"
        except Exception as e:
            success, error = False, str(e)

        return AgentResult(
            task_id=task_id, workspace_path=workspace_path,
            success=success, elapsed_seconds=time.time() - start,
            error=error,
        )
