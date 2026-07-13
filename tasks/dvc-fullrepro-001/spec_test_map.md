# Spec Test Map

filter/oracle_source: generated_only

Source file: `filter/generated_tests.py`

Excluded generated tests:

- `generated_tests.py::test_stage_add_records_deps_outs_and_command` - excluded from the final oracle because the reference gate showed it was order-sensitive for dependency serialization order while the behavioral contract is set membership, not exact list order.

| test_nodeid | source | layer | spec_section | status | notes |
|-------------|--------|-------|--------------|--------|-------|
| generated_tests.py::test_stage_add_success_exit_code | generated | integration | Installable Surface + Stage Creation | covered | Stage creation through the public CLI succeeds for a valid named stage. |
| generated_tests.py::test_stage_add_writes_named_stage_to_dvc_yaml | generated | integration | Pipeline Files | covered | A created stage is serialized under the public `stages` mapping in `dvc.yaml`. |
| generated_tests.py::test_stage_add_without_run_does_not_create_lockfile | generated | integration | Stage Creation | covered | `stage add` without `--run` writes the definition but does not execute and therefore does not create `dvc.lock`. |
| generated_tests.py::test_stage_list_name_only_reports_created_stage | generated | integration | Cross-View Invariants | covered | A stage written by `stage add` is visible through `dvc stage list --name-only`. |
| generated_tests.py::test_repro_no_commit_executes_command_and_writes_output | generated | system_e2e | Reproduction Behavior | covered | Reproduction executes the stage command and updates the workspace output even with `--no-commit`. |
| generated_tests.py::test_repro_no_commit_writes_public_lock_stage | generated | integration | Pipeline Files | covered | Successful reproduction writes a public lockfile stage entry. |
| generated_tests.py::test_status_json_reports_no_commit_output_not_in_cache | generated | integration | Status, Freeze, And Pull | covered | JSON status reports a changed stage after no-commit reproduction leaves produced data out of cache. |
| generated_tests.py::test_status_quiet_is_nonzero_when_pipeline_has_reported_changes | generated | integration | Status, Freeze, And Pull | covered | Quiet status exits nonzero when local pipeline changes are reported. |
| generated_tests.py::test_status_json_changes_after_dependency_file_changes | generated | integration | Cross-View Invariants | covered | Changing a dependency file makes the dependent stage show as changed in JSON status. |
| generated_tests.py::test_dry_repro_does_not_modify_workspace_output | generated | system_e2e | Reproduction Behavior | covered | Dry reproduction succeeds without modifying the existing workspace output. |
| generated_tests.py::test_force_repro_updates_workspace_output | generated | system_e2e | Reproduction Behavior | covered | Forced reproduction reruns the selected stage and updates the output after an input change. |
| generated_tests.py::test_repro_invalid_target_fails_nonzero | generated | atomic | Error Semantics | covered | Reproducing an unknown target fails with a nonzero CLI exit code. |
| generated_tests.py::test_no_commit_repro_runs_stage_each_time_when_output_is_uncached | generated | integration | Reproduction Behavior | covered | With `--no-commit --no-run-cache`, repeated reproductions execute the stage instead of restoring from cache. |
| generated_tests.py::test_no_commit_repro_runs_after_dependency_change | generated | integration | Cross-View Invariants | covered | A dependency change makes the stage eligible to run again. |
| generated_tests.py::test_no_commit_repro_runs_after_output_deletion | generated | integration | Reproduction Behavior | covered | Removing a declared output causes reproduction to execute the stage again. |
| generated_tests.py::test_no_commit_repro_recreates_deleted_output | generated | integration | Reproduction Behavior | covered | Reproduction materializes the deleted output back into the workspace. |
| generated_tests.py::test_nonpersistent_outputs_are_removed_before_forced_rerun | generated | integration | Stage Creation | covered | Non-persistent outputs are removed before a forced rerun so the command recreates them. |
| generated_tests.py::test_persistent_outputs_remain_before_forced_rerun | generated | integration | Stage Creation | covered | Persistent outputs remain in place before command execution. |
| generated_tests.py::test_outs_no_cache_is_serialized_with_cache_false | generated | atomic | Pipeline Files | covered | A no-cache output is serialized in `dvc.yaml` with `cache: false`. |
| generated_tests.py::test_missing_no_cache_output_reports_status_change | generated | integration | Cross-View Invariants | covered | Missing no-cache outputs still affect local status. |
| generated_tests.py::test_metric_output_is_recorded_in_lockfile_outputs | generated | atomic | Pipeline Files | covered | Metric outputs participate in lockfile output metadata after reproduction. |
| generated_tests.py::test_plot_output_is_recorded_in_lockfile_outputs | generated | atomic | Pipeline Files | covered | Plot outputs participate in lockfile output metadata after reproduction. |
| generated_tests.py::test_stage_wdir_runs_command_from_declared_directory | generated | integration | Reproduction Behavior | covered | Stage commands run from the declared working directory and interpret relative paths there. |
| generated_tests.py::test_stage_command_receives_dvc_root_environment | generated | atomic | Reproduction Behavior | covered | Stage command execution exposes `DVC_ROOT` as the project root. |
| generated_tests.py::test_stage_command_receives_dvc_stage_environment | generated | atomic | Reproduction Behavior | covered | Stage command execution exposes `DVC_STAGE` as the stage address. |
| generated_tests.py::test_command_list_runs_commands_in_order | generated | integration | Reproduction Behavior | covered | A list-valued command runs sequentially in the listed order. |
| generated_tests.py::test_failing_command_list_stage_returns_nonzero | generated | atomic | Error Semantics | covered | A failing stage command makes reproduction fail nonzero. |
| generated_tests.py::test_failing_command_list_does_not_run_later_commands | generated | integration | Error Semantics | covered | Later commands in the same stage do not run after an earlier command fails. |
| generated_tests.py::test_params_dependency_initial_repro_uses_param_value | generated | integration | Pipeline Files | covered | Declared params are read as pipeline dependencies and affect reproduced output. |
| generated_tests.py::test_params_change_reports_status_change | generated | integration | Cross-View Invariants | covered | Changing a parameter value makes status report a changed pipeline state. |
| generated_tests.py::test_freeze_writes_frozen_to_stage_definition | generated | atomic | Status, Freeze, And Pull | covered | Freezing a stage writes the frozen state to the project file. |
| generated_tests.py::test_frozen_stage_does_not_reproduce_changed_params | generated | system_e2e | Status, Freeze, And Pull | covered | A frozen stage does not reproduce through changed parameters. |
| generated_tests.py::test_unfreeze_removes_frozen_flag_and_repro_updates_output | generated | system_e2e | Status, Freeze, And Pull | covered | Unfreezing removes the frozen state and normal reproduction updates resume. |
| generated_tests.py::test_local_status_rejects_revision_expansion_option | generated | atomic | Error Semantics | covered | Local status rejects revision expansion options that apply only to cache-vs-remote status. |
| generated_tests.py::test_duplicate_stage_name_without_force_fails | generated | atomic | Stage Creation | covered | Adding a duplicate stage name without force is rejected. |
| generated_tests.py::test_duplicate_stage_name_with_force_succeeds | generated | atomic | Stage Creation | covered | Adding a duplicate stage name with force succeeds as an overwrite. |
| generated_tests.py::test_overlapping_stage_outputs_are_rejected | generated | atomic | Error Semantics | covered | Stage creation rejects output ownership conflicts. |
| generated_tests.py::test_targeted_repro_runs_upstream_dependency_for_target | generated | system_e2e | Cross-View Invariants + Representative Workflows | covered | Targeted reproduction of a downstream stage runs required upstream stages first. |
| generated_tests.py::test_downstream_repro_updates_descendant_stage_output | generated | system_e2e | Reproduction Behavior | covered | Downstream reproduction starts from the selected stage and updates descendants. |
| generated_tests.py::test_repo_reproduce_force_returns_reproduced_stages | generated | integration | Public API | covered | `Repo.reproduce` returns the stages that actually reproduced. |
| generated_tests.py::test_repo_freeze_writes_same_frozen_state_as_cli | generated | integration | Public API | covered | `Repo.freeze` writes the same frozen project-file state as the CLI workflow. |
| generated_tests.py::test_repo_unfreeze_removes_frozen_state | generated | integration | Public API | covered | `Repo.unfreeze` removes the project-file frozen state. |
| generated_tests.py::test_repo_run_no_exec_writes_stage_but_does_not_create_output | generated | integration | Public API | covered | `Repo.run(..., no_exec=True)` creates the stage definition without creating the declared output. |
| generated_tests.py::test_clean_status_reports_up_to_date_after_committed_repro | generated | integration | Status, Freeze, And Pull | covered | Clean local status reports the project is up to date after committed reproduction. |
| generated_tests.py::test_status_quiet_success_when_pipeline_is_clean | generated | atomic | Status, Freeze, And Pull | covered | Quiet status exits successfully when no local pipeline changes are reported. |
| generated_tests.py::test_run_cache_restores_deleted_output_without_rerunning_command | generated | system_e2e | Cache And Run Cache | covered | Run cache restores a deleted output without executing the command again. |
| generated_tests.py::test_pull_restores_stage_output_from_local_remote | generated | system_e2e | Status, Freeze, And Pull | covered | Pull restores a tracked stage output from a configured local remote. |
| generated_tests.py::test_always_changed_stage_serializes_public_flag | generated | atomic | Pipeline Files | covered | An always-changed stage serializes the public always_changed flag. |
| generated_tests.py::test_always_changed_stage_runs_even_without_input_changes | generated | integration | Reproduction Behavior | covered | An always-changed stage reproduces on repeated runs even without input changes. |
| generated_tests.py::test_status_json_returns_mapping_for_changed_stage | generated | integration | Status, Freeze, And Pull | covered | JSON status returns a mapping keyed by changed stage name. |

Total: 50 | kept (covered): 50 | spec_gap: 0 | source-only: 0 | excluded: 1 | final_scoreable: 50
