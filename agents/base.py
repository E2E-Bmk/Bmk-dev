"""Abstract base class for agent adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for running an agent.

    Budgets are unlimited by default. A resource budget expressed in steps,
    seconds or dollars is not a capability attribute: the same dollar ceiling
    buys an expensive model far fewer steps than a cheap one, and the same wall
    clock buys a slow gateway far fewer steps than a fast one. Capping any of
    them injects model pricing and transport latency into the score. Usage is
    recorded instead, so a report can state cost and duration without letting
    them truncate a run.

    `0` means "no limit" for all three budgets, matching mini-swe-agent's own
    convention (`if 0 < limit <= actual: stop`).
    """
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_iterations: int = 0      # 0 = unlimited steps
    timeout_seconds: int = 0     # 0 = unlimited wall clock
    cost_limit: float = 0.0      # 0 = unlimited spend
    max_cpus: int = 2

    #: Extra provider parameters, forwarded verbatim to the completion call.
    #:
    #: A gateway occasionally needs a parameter that is neither a budget nor a
    #: capability, and hard-coding one model's quirk into the adapter would put
    #: model-specific behaviour in the layer that is supposed to be neutral
    #: about models. Populated from the per-model `extra_params` object in
    #: agents/config.json.
    #:
    #: The case that motivated it: qwen3.8-max defaults to a reasoning mode that
    #: spends ~29k thinking tokens per turn, so a single call takes ~10 minutes
    #: and a 40-turn task takes most of a day. `enable_thinking: false` brings
    #: the same call to ~36s. That is a transport property of one gateway, not
    #: a statement about the model's ability, so it belongs in config.
    extra_params: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from an agent run.

    `n_calls`, `cost` and `elapsed_seconds` are reported, never enforced.
    """
    task_id: str
    workspace_path: Path
    success: bool
    elapsed_seconds: float
    cost: float = 0.0
    n_calls: int = 0
    error: Optional[str] = None
    exit_status: Optional[str] = None


class BaseAgent(ABC):
    """Abstract interface for coding agents."""

    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    def solve(self, task_id: str, spec_path: Path, workspace_path: Path,
              language: str = "python") -> AgentResult:
        """
        Given a spec, produce a complete implementation in workspace_path.

        The agent operates inside a Docker container with --network=none.
        It reads spec.md and produces an installable package.

        Args:
            task_id: Unique task identifier
            spec_path: Path to spec.md (copied INTO the container)
            workspace_path: Host directory to receive extracted output
            language: Implementation language declared by the task. It selects
                the container image and the packaging instructions, both of
                which are language-specific: an image without the toolchain
                cannot compile, and a candidate told to write `pyproject.toml`
                for a Go task writes the wrong files. Defaults to `python`,
                which is what every task in the release set is.

        Returns:
            AgentResult with the outcome
        """
        ...
