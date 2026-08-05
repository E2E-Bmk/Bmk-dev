from __future__ import annotations

import json

from conftest import commit_file, commit_with_body, last_stdout_line, psr, python_snippet, read_version, tags


def test_package_reports_documented_distribution_version(tmp_path):
    result = python_snippet(
        tmp_path,
        "import semantic_release; print(semantic_release.__version__)",
    )
    assert last_stdout_line(result) == "10.6.1"


def test_public_version_parse_preserves_number_text(tmp_path):
    result = python_snippet(
        tmp_path,
        "from semantic_release import Version; print(Version.parse('1.2.3'))",
    )
    assert last_stdout_line(result) == "1.2.3"


def test_public_version_parse_preserves_prerelease_text(tmp_path):
    result = python_snippet(
        tmp_path,
        "from semantic_release import Version; print(Version.parse('1.2.3-rc.1'))",
    )
    assert last_stdout_line(result) == "1.2.3-rc.1"


def test_public_version_parse_preserves_build_metadata_text(tmp_path):
    result = python_snippet(
        tmp_path,
        "from semantic_release import Version; print(Version.parse('1.2.3+build.5'))",
    )
    assert last_stdout_line(result) == "1.2.3+build.5"


def test_public_level_bump_exports_semantic_names(tmp_path):
    result = python_snippet(
        tmp_path,
        "from semantic_release import LevelBump; print(','.join(sorted(item.name for item in LevelBump)))",
    )
    names = last_stdout_line(result).split(",")
    assert {"MAJOR", "MINOR", "PATCH", "NO_RELEASE"}.issubset(set(names))


def test_generate_config_toml_uses_plain_semantic_release_root(make_project):
    result = psr(make_project(), "generate-config", "-f", "toml")
    assert "[semantic_release]" in result.stdout
    assert "tag_format" in result.stdout


def test_generate_config_pyproject_uses_tool_root(make_project):
    result = psr(make_project(), "generate-config", "--pyproject")
    assert "[tool.semantic_release]" in result.stdout
    assert "[semantic_release]" not in result.stdout.splitlines()[0]


def test_generate_config_json_uses_top_level_semantic_release_key(make_project):
    result = psr(make_project(), "generate-config", "-f", "json")
    payload = json.loads(result.stdout)
    assert "semantic_release" in payload
    assert "tag_format" in payload["semantic_release"]


def test_main_help_lists_release_commands(tmp_path):
    result = psr(tmp_path, "-h")
    assert "version" in result.stdout
    assert "changelog" in result.stdout
    assert "publish" in result.stdout


def test_version_help_lists_print_and_local_side_effect_toggles(tmp_path):
    result = psr(tmp_path, "version", "-h")
    assert "--print" in result.stdout
    assert "--no-push" in result.stdout
    assert "--no-vcs-release" in result.stdout


def test_last_released_version_prints_plain_version(make_project):
    repo = make_project()
    result = psr(repo, "version", "--print-last-released")
    assert last_stdout_line(result) == "1.0.0"


def test_last_released_tag_prints_configured_tag(make_project):
    repo = make_project()
    result = psr(repo, "version", "--print-last-released-tag")
    assert last_stdout_line(result) == "v1.0.0"


def test_custom_tag_format_selects_matching_release_tag(make_project):
    repo = make_project(tag="pkg-v2.4.0", tag_format="pkg-v{version}", version="2.4.0")
    result = psr(repo, "version", "--print-last-released-tag")
    assert last_stdout_line(result) == "pkg-v2.4.0"


def test_fix_commit_projects_patch_release(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix(core): repair parser")
    result = psr(repo, "version", "--print")
    assert last_stdout_line(result) == "1.0.1"


def test_feat_commit_projects_minor_release(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat(cli): add print mode")
    result = psr(repo, "version", "--print")
    assert last_stdout_line(result) == "1.1.0"


def test_breaking_change_footer_projects_major_release(make_project):
    repo = make_project()
    commit_with_body(
        repo,
        "api.txt",
        "new api\n",
        "feat(api): reshape public command",
        "BREAKING CHANGE: command output shape changed",
    )
    result = psr(repo, "version", "--print")
    assert last_stdout_line(result) == "2.0.0"


def test_docs_commit_does_not_force_release(make_project):
    repo = make_project()
    commit_file(repo, "README.md", "docs\n", "docs: expand release guide")
    result = psr(repo, "version", "--print")
    assert last_stdout_line(result) == "1.0.0"


def test_unknown_commit_does_not_force_release(make_project):
    repo = make_project()
    commit_file(repo, "note.txt", "note\n", "rewrite notes")
    result = psr(repo, "version", "--print")
    assert last_stdout_line(result) == "1.0.0"


def test_forced_major_overrides_patch_history(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(repo, "version", "--major", "--print")
    assert last_stdout_line(result) == "2.0.0"


def test_forced_minor_overrides_patch_history(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(repo, "version", "--minor", "--print")
    assert last_stdout_line(result) == "1.1.0"


def test_forced_patch_overrides_no_release_history(make_project):
    repo = make_project()
    commit_file(repo, "README.md", "docs\n", "docs: guide")
    result = psr(repo, "version", "--patch", "--print")
    assert last_stdout_line(result) == "1.0.1"


def test_build_metadata_is_appended_to_printed_version(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(repo, "version", "--print", "--build-metadata", "run.7")
    assert last_stdout_line(result) == "1.0.1+run.7"


def test_print_tag_uses_custom_tag_format(make_project):
    repo = make_project(tag="pkg-v1.0.0", tag_format="pkg-v{version}")
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(repo, "version", "--print-tag")
    assert last_stdout_line(result) == "pkg-v1.0.1"


def test_json_configuration_file_is_accepted(make_project):
    repo = make_project(json_config=True)
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(repo, "-c", "releaserc.json", "version", "--print")
    assert last_stdout_line(result) == "1.0.1"


def test_noop_version_does_not_update_project_file(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(repo, "--noop", "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert result.returncode == 0
    assert read_version(repo) == "1.0.0"


def test_no_commit_no_tag_updates_version_without_git_tag(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    result = psr(
        repo,
        "version",
        "--no-commit",
        "--no-tag",
        "--no-changelog",
        "--skip-build",
    )
    assert result.returncode == 0
    assert read_version(repo) == "1.0.1"
    assert tags(repo) == ["v1.0.0"]


def test_no_changelog_keeps_existing_changelog_body(make_project):
    repo = make_project()
    before = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    commit_file(repo, "fix.txt", "fixed\n", "fix: bug")
    psr(repo, "version", "--no-commit", "--no-tag", "--no-changelog", "--skip-build")
    after = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert after == before


def test_allow_zero_version_keeps_minor_bump_under_zero_major(make_project):
    repo = make_project(version="0.1.0", tag="v0.1.0")
    commit_file(repo, "feature.txt", "feature\n", "feat: add api")
    result = psr(repo, "version", "--print")
    assert last_stdout_line(result) == "0.2.0"


def test_prerelease_print_uses_configured_token(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat: add api")
    result = psr(repo, "version", "--minor", "--as-prerelease", "--print")
    assert last_stdout_line(result) == "1.1.0-rc.1"


def test_prerelease_token_option_overrides_branch_token(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat: add api")
    result = psr(
        repo,
        "version",
        "--minor",
        "--as-prerelease",
        "--prerelease-token",
        "beta",
        "--print",
    )
    assert last_stdout_line(result) == "1.1.0-beta.1"
