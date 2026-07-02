# Spec Test Map

Track A Step 2 map for public-API rewrites in `filter/rewritten_upstream_tests.py`, rerun against `spec/spec_v3.md`.

This map is paired with the Step 3 dummy gate artifacts for the covered set.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| filter/rewritten_upstream_tests.py::test_config_programmatic_options_and_attributes_round_trip | atomic | section Configuration | covered | Public Config option and attributes behavior is specified. |
| filter/rewritten_upstream_tests.py::test_config_print_stdout_uses_configured_stream | atomic | section Configuration | covered | `stdout` and `Config.print_stdout()` behavior is specified. |
| filter/rewritten_upstream_tests.py::test_script_directory_requires_script_location | atomic | section Error Semantics | covered | Missing `script_location` error is specified. |
| filter/rewritten_upstream_tests.py::test_init_creates_environment_files | integration | section Installable Surface + section Migration Environment + section Command Line Interface | covered | Environment creation and script directory visibility are specified. |
| filter/rewritten_upstream_tests.py::test_init_package_creates_package_markers | atomic | section Python Command API | covered | `command.init(..., package=True)` package marker behavior is specified in spec_v2. |
| filter/rewritten_upstream_tests.py::test_init_rejects_non_empty_directory | atomic | section Error Semantics | covered | Non-empty init target error is specified. |
| filter/rewritten_upstream_tests.py::test_list_templates_writes_known_template_names | atomic | section Command Line Interface | covered | `list_templates` output of available templates and the generic template are specified/derivable. |
| filter/rewritten_upstream_tests.py::test_command_revision_creates_script_file | integration | section Python Command API | covered | Revision creation return/file behavior is specified. |
| filter/rewritten_upstream_tests.py::test_script_directory_heads_follow_revision_graph | integration | section Script Directory And Revision Graph | covered | Bases, heads, graph inspection, and `get_heads()` list return type are specified in spec_v3. |
| filter/rewritten_upstream_tests.py::test_script_directory_multiple_heads_raise_for_single_head | atomic | section Script Directory And Revision Graph | covered | Multiple-head single-head error behavior is specified. |
| filter/rewritten_upstream_tests.py::test_merge_revision_resolves_multiple_heads | integration | section Script Directory And Revision Graph | covered | Merge revision and resulting single head are specified. |
| filter/rewritten_upstream_tests.py::test_walk_revisions_returns_scripts_from_graph | atomic | section Script Directory And Revision Graph | covered | Graph traversal through `walk_revisions()` is specified. |
| filter/rewritten_upstream_tests.py::test_upgrade_applies_revision_and_updates_current | system_e2e | section Cross-View Invariants | covered | File, database schema, and current revision views must agree after upgrade. |
| filter/rewritten_upstream_tests.py::test_downgrade_base_reverts_schema_and_version | system_e2e | section Cross-View Invariants | covered | Downgrade graph movement and database/version-table state agreement are specified. |
| filter/rewritten_upstream_tests.py::test_stamp_sets_current_revision_without_running_upgrade | system_e2e | section Cross-View Invariants | covered | Stamp changes version-table state without running migrations. |
| filter/rewritten_upstream_tests.py::test_ensure_version_creates_version_table | integration | section Command Line Interface | covered | `ensure_version` creates the version table. |
| filter/rewritten_upstream_tests.py::test_offline_upgrade_writes_sql_without_mutating_database | system_e2e | section Offline SQL | covered | Offline upgrade writes SQL for graph movement instead of mutating the database. |
| filter/rewritten_upstream_tests.py::test_offline_downgrade_range_writes_drop_sql | integration | section Offline SQL | covered | Offline range syntax and downgrade SQL output are specified. |
| filter/rewritten_upstream_tests.py::test_migration_context_offline_current_heads_from_starting_rev | atomic | section Runtime Context | covered | Offline current-head behavior from `starting_rev` is specified. |
| filter/rewritten_upstream_tests.py::test_operations_create_table_online | integration | section Operations API | covered | Online operation directives execute through an explicit public `Operations(ctx)` object. |
| filter/rewritten_upstream_tests.py::test_operations_execute_online_sql_string | atomic | section Operations API | covered | `Operations(ctx).execute()` accepts SQL strings and executes online. |
| filter/rewritten_upstream_tests.py::test_operations_bulk_insert_online | integration | section Operations API | covered | `Operations(ctx).bulk_insert()` online insertion behavior is specified. |
| filter/rewritten_upstream_tests.py::test_operations_create_table_offline_renders_sql | atomic | section Operations API | covered | Offline operation directives render SQL through an explicit public `Operations(ctx)` object. |
| filter/rewritten_upstream_tests.py::test_batch_alter_table_adds_column_on_sqlite | integration | section Batch Mode | covered | Batch mode add-column behavior through `Operations(ctx).batch_alter_table()` on SQLite is specified. |
| filter/rewritten_upstream_tests.py::test_batch_alter_table_drop_column_recreates_sqlite_table | integration | section Batch Mode | covered | Batch mode table recreation/drop-column behavior through `Operations(ctx).batch_alter_table()` on SQLite is specified. |
| filter/rewritten_upstream_tests.py::test_autogenerate_detects_added_table | atomic | section Autogenerate | covered | Added-table detection through public `compare_metadata()` is checked without relying on exact tuple positions. |
| filter/rewritten_upstream_tests.py::test_autogenerate_detects_removed_table | atomic | section Autogenerate | covered | Removed-table detection through public `compare_metadata()` is checked without relying on exact tuple positions. |
| filter/rewritten_upstream_tests.py::test_autogenerate_detects_added_column | atomic | section Autogenerate | covered | Added-column detection through public `compare_metadata()` is checked without relying on exact tuple positions. |
| filter/rewritten_upstream_tests.py::test_environment_receives_shared_connection_for_upgrade | system_e2e | section Cross-View Invariants | covered | `Config.attributes`, environment runtime, command API, and database effects agree. |
| filter/rewritten_upstream_tests.py::test_command_heads_and_history_write_revision_state | integration | section Command Line Interface | covered | Heads/history command reporting of revision state is specified. |

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|---|
| filter/generated_tests.py::test_installable_surface_exports_version_config_and_command_api | atomic | section Installable Surface | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_config_file_name_and_attributes_are_public_state | atomic | section Configuration | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_command_init_creates_generic_template_environment | system_e2e | section Command Line Interface | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_script_directory_from_config_reads_revision_files | integration | section Script Directory And Revision Graph | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_environment_context_online_upgrade_runs_env_script | system_e2e | section Migration Environment | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_environment_context_offline_upgrade_uses_output_buffer | system_e2e | section Migration Environment | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_migration_context_reports_current_heads_from_database | atomic | section Runtime Context | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_migration_context_offline_version_table_name_is_configurable | atomic | section Runtime Context | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_operations_add_column_offline_renders_sql | atomic | section Offline SQL | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_operations_drop_column_offline_renders_sql | atomic | section Offline SQL | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_batch_alter_table_offline_requires_copy_from_for_sqlite | atomic | section Batch Mode | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_command_stamp_creates_version_table_without_running_migrations | system_e2e | section Python Command API | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_command_current_reports_database_revision | integration | section Command Line Interface | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_command_history_reports_revision_message | integration | section Command Line Interface | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_command_branches_reports_branch_point | integration | section Script Directory And Revision Graph | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_revision_autogenerate_requires_database_connection | atomic | section Error Semantics | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_missing_revision_raises_command_error | atomic | section Error Semantics | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_ensure_version_is_idempotent | integration | section Cross-View Invariants | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_cross_view_heads_match_history_and_script_directory | integration | section Cross-View Invariants | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |
| filter/generated_tests.py::test_representative_init_revision_upgrade_current_workflow | system_e2e | section Migration Environment + section Representative Workflow | covered | Retroactive public Alembic API/CLI/runtime oracle supplement for Gate D coverage. |

Total: 50 | kept (covered): 50 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 50
