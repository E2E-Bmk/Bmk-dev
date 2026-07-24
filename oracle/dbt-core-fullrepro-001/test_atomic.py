# Spec2Repo oracle - atomic tests for dbt-core-fullrepro-001
from dbt.cli.main import dbtRunner, dbtRunnerResult


def _assert_usage_failure(args):
    outcome = dbtRunner().invoke(args)
    assert isinstance(outcome, dbtRunnerResult)
    assert outcome.success is False
    assert outcome.result is None
    assert isinstance(outcome.exception, BaseException)


def test_runner_rejects_empty_argument_list():
    _assert_usage_failure([])


def test_runner_rejects_unknown_command():
    _assert_usage_failure(["not-a-dbt-command"])


def test_runner_rejects_unknown_top_level_option():
    _assert_usage_failure(["--not-a-real-option"])


def test_parse_rejects_unknown_option():
    _assert_usage_failure(["parse", "--not-a-real-option"])


def test_parse_rejects_missing_project_dir_value():
    _assert_usage_failure(["parse", "--project-dir"])


def test_parse_rejects_non_integer_threads():
    _assert_usage_failure(["parse", "--threads", "many"])


def test_parse_rejects_malformed_vars_yaml():
    _assert_usage_failure(["parse", "--vars", "[unterminated"])


def test_list_rejects_invalid_output_choice():
    _assert_usage_failure(["list", "--output", "yaml"])


def test_compile_rejects_invalid_output_choice():
    _assert_usage_failure(["compile", "--output", "yaml"])


def test_list_rejects_invalid_resource_type():
    _assert_usage_failure(["list", "--resource-type", "bogus"])


def test_run_rejects_invalid_resource_type():
    _assert_usage_failure(["run", "--resource-type", "bogus"])


def test_parse_rejects_unexpected_positional_argument():
    _assert_usage_failure(["parse", "extra"])


def test_compile_rejects_missing_inline_value():
    _assert_usage_failure(["compile", "--inline"])


def test_list_rejects_missing_output_keys_value():
    _assert_usage_failure(["list", "--output-keys"])


def test_list_rejects_models_with_select():
    _assert_usage_failure(["list", "--models", "alpha", "--select", "beta"])


def test_list_rejects_models_with_resource_type():
    _assert_usage_failure(
        ["list", "--models", "alpha", "--resource-type", "model"]
    )


def test_parse_fails_for_missing_local_project(tmp_path):
    _assert_usage_failure(
        [
            "parse",
            "--project-dir",
            str(tmp_path / "missing-project"),
            "--no-version-check",
            "--quiet",
        ]
    )


def test_list_fails_for_missing_local_project(tmp_path):
    _assert_usage_failure(
        [
            "list",
            "--project-dir",
            str(tmp_path / "missing-project"),
            "--no-version-check",
            "--quiet",
        ]
    )


def test_compile_fails_for_missing_local_project(tmp_path):
    _assert_usage_failure(
        [
            "compile",
            "--project-dir",
            str(tmp_path / "missing-project"),
            "--no-version-check",
            "--quiet",
        ]
    )


def test_run_fails_for_missing_local_project(tmp_path):
    _assert_usage_failure(
        [
            "run",
            "--project-dir",
            str(tmp_path / "missing-project"),
            "--no-version-check",
            "--quiet",
        ]
    )
