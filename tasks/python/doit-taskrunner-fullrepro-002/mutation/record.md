target clause:   spec.md:207-210 — Command result codes (failure=2, error=1, swapped from upstream 1/2)
                 spec.md:368 — CLI Entry Points summary (same swap)
upstream form:   doit maps failure→1, error→2. Source: runner.py:20-22 SUCCESS=0/FAILURE=1/ERROR=2.
                 Verified on doit 0.37.0 installed from PyPI.
mutated form:    failure→2, error→1. Codes 0 and 3 unchanged.
oracle tests:    test_atomic::test_python_action_returning_false_reports_task_failure     (1→2)
                 test_atomic::test_python_action_exception_reports_task_error             (2→1)
                 test_atomic::test_command_action_nonzero_exit_reports_failure             (1→2)
                 test_atomic::test_command_exit_above_125_reports_error_not_failure        (2→1)
                 test_integration::test_continue_runs_independent_task_after_failure       (1→2)
implementable:   Two module-level constant assignments: runner.FAILURE=2, runner.ERROR=1.
                 No other module imports these constants. Severity-precedence guard in
                 runner.py:67 continues to work under the swap.
divergent:       Upstream returns 1 for failure, 2 for error. Verified by running:
                 python-action-False→1, python-action-raise→2, cmd-exit-5→1, cmd-exit-126→2,
                 --continue-with-fail→1.
unguessable:     1=light/2=severe is the universal CLI convention (grep, diff, make, pytest).
                 No engineer writes failure=2, error=1 without being told.
                 Symmetric swap: dummy-gate neutral (same count of dummy-passable tests).
