# Reinstated

~~This task was previously retired because `filter_iter=3` exceeded the repair budget.~~

**2026-07-13 reinstatement**: The filter iteration budget is a pipeline efficiency guard to prevent wasted compute, not a quality gate. This task's final oracle (481 tests, reference 481/481, candidate 98/481) is independently verified as QUALIFIED by the task-judge. A task that passes all quality gates (reference ≥95%, dummy ≈0%, spec-test coverage, fairness audit) is valid regardless of how many iterations it took to get there. Reinstated to active benchmark set.
