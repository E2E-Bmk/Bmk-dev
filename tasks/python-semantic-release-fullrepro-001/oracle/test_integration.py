from __future__ import annotations

from conftest import (
    commit_file,
    commit_subjects,
    commit_with_body,
    git,
    last_stdout_line,
    psr,
    read_version,
    tags,
)
import pytest


@pytest.mark.depends_on(
    "test_fix_commit_projects_patch_release",
    "test_no_commit_no_tag_updates_version_without_git_tag",
)
def test_release_command_updates_project_version_changelog_commit_and_tag(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix(core): repair parser (#12)")
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert read_version(repo) == "1.0.1"
    assert "v1.0.1" in changelog
    assert "Bug Fixes" in changelog
    assert "Repair parser" in changelog
    assert tags(repo) == ["v1.0.0", "v1.0.1"]
    assert commit_subjects(repo, 1) == ["release: 1.0.1"]


@pytest.mark.depends_on(
    "test_fix_commit_projects_patch_release",
    "test_no_commit_no_tag_updates_version_without_git_tag",
)
def test_release_commit_includes_version_variable_file_replacements(make_project):
    repo = make_project(
        version_variables=[
            "pkg.py:__version__:nf",
            "VERSION:*:nf",
            "RELEASE:*:tf",
        ]
    )
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert '__version__ = "1.0.1"' in (repo / "pkg.py").read_text(encoding="utf-8")
    assert (repo / "VERSION").read_text(encoding="utf-8").strip() == "1.0.1"
    assert (repo / "RELEASE").read_text(encoding="utf-8").strip() == "v1.0.1"


@pytest.mark.depends_on(
    "test_feat_commit_projects_minor_release",
    "test_fix_commit_projects_patch_release",
)
def test_changelog_groups_feature_and_fix_sections_from_same_history(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat(ui): add dashboard", day=2)
    commit_file(repo, "fix.txt", "fixed\n", "fix(api): repair response", day=3)
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Features" in changelog
    assert "Bug Fixes" in changelog
    assert "Add dashboard" in changelog
    assert "Repair response" in changelog


@pytest.mark.depends_on("test_breaking_change_footer_projects_major_release")
def test_breaking_change_section_is_rendered_for_major_release(make_project):
    repo = make_project()
    commit_with_body(
        repo,
        "api.txt",
        "api\n",
        "feat(api): replace output",
        "BREAKING CHANGE: old config keys are removed",
    )
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert read_version(repo) == "2.0.0"
    assert "Breaking Changes" in changelog
    assert "Old config keys are removed" in changelog
    assert "v2.0.0" in tags(repo)


@pytest.mark.depends_on("test_feat_commit_projects_minor_release")
def test_print_projection_and_release_side_effect_agree(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat(cli): add command")
    projected = last_stdout_line(psr(repo, "version", "--print"))
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert projected == read_version(repo)
    assert f"v{projected}" in tags(repo)


@pytest.mark.depends_on("test_print_tag_uses_custom_tag_format")
def test_print_tag_projection_and_git_tag_agree_for_custom_format(make_project):
    repo = make_project(tag="pkg-v1.0.0", tag_format="pkg-v{version}")
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    projected = last_stdout_line(psr(repo, "version", "--print-tag"))
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert projected == "pkg-v1.0.1"
    assert projected in tags(repo)


@pytest.mark.depends_on("test_last_released_version_prints_plain_version")
def test_last_released_projection_moves_after_local_release(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    assert last_stdout_line(psr(repo, "version", "--print-last-released")) == "1.0.0"
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert last_stdout_line(psr(repo, "version", "--print-last-released")) == "1.0.1"


@pytest.mark.depends_on("test_no_commit_no_tag_updates_version_without_git_tag")
def test_no_commit_workflow_stamps_files_without_release_commit(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    before = commit_subjects(repo, 1)
    psr(repo, "version", "--no-commit", "--no-tag", "--no-changelog", "--skip-build")
    assert read_version(repo) == "1.0.1"
    assert commit_subjects(repo, 1) == before
    assert tags(repo) == ["v1.0.0"]


@pytest.mark.depends_on("test_no_commit_no_tag_updates_version_without_git_tag")
def test_no_tag_workflow_creates_release_commit_without_new_tag(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    psr(repo, "version", "--no-tag", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == "1.0.1"
    assert commit_subjects(repo, 1) == ["release: 1.0.1"]
    assert tags(repo) == ["v1.0.0"]


@pytest.mark.depends_on("test_no_changelog_keeps_existing_changelog_body")
def test_no_changelog_release_updates_version_and_tag_only(make_project):
    repo = make_project()
    before = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    psr(repo, "version", "--no-changelog", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == "1.0.1"
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == before
    assert "v1.0.1" in tags(repo)


@pytest.mark.depends_on("test_noop_version_does_not_update_project_file")
def test_noop_workflow_preserves_files_tags_and_head(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    before_version = read_version(repo)
    before_tags = tags(repo)
    before_subject = commit_subjects(repo, 1)
    psr(repo, "--noop", "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == before_version
    assert tags(repo) == before_tags
    assert commit_subjects(repo, 1) == before_subject


@pytest.mark.depends_on(
    "test_feat_commit_projects_minor_release",
    "test_no_commit_no_tag_updates_version_without_git_tag",
)
def test_version_toml_and_version_variable_views_stay_in_sync(make_project):
    repo = make_project(version_variables=["pkg.py:__version__:nf", "VERSION:*:nf"])
    commit_file(repo, "feature.txt", "feature\n", "feat: add api")
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    pyproject_version = read_version(repo)
    assert pyproject_version == "1.1.0"
    assert f'__version__ = "{pyproject_version}"' in (repo / "pkg.py").read_text(encoding="utf-8")
    assert (repo / "VERSION").read_text(encoding="utf-8").strip() == pyproject_version


@pytest.mark.depends_on("test_json_configuration_file_is_accepted")
def test_json_config_release_updates_toml_project_file(make_project):
    repo = make_project(json_config=True)
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    psr(repo, "-c", "releaserc.json", "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == "1.0.1"
    assert "v1.0.1" in tags(repo)


@pytest.mark.depends_on(
    "test_main_help_lists_release_commands",
    "test_fix_commit_projects_patch_release",
)
def test_changelog_command_renders_history_without_version_command(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix(core): repair changelog")
    result = psr(repo, "changelog")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert result.returncode == 0
    assert "Unreleased" in changelog
    assert "Repair changelog" in changelog


@pytest.mark.depends_on(
    "test_main_help_lists_release_commands",
    "test_noop_version_does_not_update_project_file",
)
def test_changelog_noop_leaves_existing_changelog_unchanged(make_project):
    repo = make_project()
    before = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    commit_file(repo, "fix.txt", "fixed\n", "fix(core): repair changelog")
    psr(repo, "--noop", "changelog")
    assert (repo / "CHANGELOG.md").read_text(encoding="utf-8") == before


@pytest.mark.depends_on("test_prerelease_print_uses_configured_token")
def test_prerelease_release_creates_prerelease_tag_and_version(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat: add api")
    psr(
        repo,
        "version",
        "--minor",
        "--as-prerelease",
        "--no-push",
        "--no-vcs-release",
        "--skip-build",
    )
    assert read_version(repo) == "1.1.0-rc.1"
    assert "v1.1.0-rc.1" in tags(repo)


@pytest.mark.depends_on("test_build_metadata_is_appended_to_printed_version")
def test_build_metadata_release_stamps_metadata_in_tag_and_project(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    psr(
        repo,
        "version",
        "--build-metadata",
        "local.5",
        "--no-push",
        "--no-vcs-release",
        "--skip-build",
    )
    assert read_version(repo) == "1.0.1+local.5"
    assert "v1.0.1+local.5" in tags(repo)


@pytest.mark.depends_on("test_feat_commit_projects_minor_release")
def test_release_commit_message_template_uses_new_version(make_project):
    repo = make_project()
    commit_file(repo, "feature.txt", "feature\n", "feat: add api")
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert commit_subjects(repo, 2)[0] == "release: 1.1.0"


@pytest.mark.depends_on("test_custom_tag_format_selects_matching_release_tag")
def test_release_history_ignores_unmatched_tag_format(make_project):
    repo = make_project(tag="release-9.9.9", tag_format="v{version}", version="1.0.0")
    git_tags_before = tags(repo)
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair")
    projected = last_stdout_line(psr(repo, "version", "--print"))
    assert git_tags_before == ["release-9.9.9"]
    assert projected == "0.0.1"


@pytest.mark.depends_on("test_last_released_version_prints_plain_version")
def test_release_history_uses_highest_matching_semver_tag(make_project):
    repo = make_project()
    commit_file(repo, "older.txt", "older\n", "fix: older", day=2)
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    commit_file(repo, "newer.txt", "newer\n", "fix: newer", day=3)
    assert last_stdout_line(psr(repo, "version", "--print")) == "1.0.2"


@pytest.mark.depends_on("test_fix_commit_projects_patch_release")
def test_multiple_patch_commits_roll_up_to_one_patch_release(make_project):
    repo = make_project()
    commit_file(repo, "fix1.txt", "one\n", "fix: first repair", day=2)
    commit_file(repo, "fix2.txt", "two\n", "fix: second repair", day=3)
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == "1.0.1"
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "First repair" in changelog
    assert "Second repair" in changelog


@pytest.mark.depends_on(
    "test_feat_commit_projects_minor_release",
    "test_fix_commit_projects_patch_release",
)
def test_minor_release_wins_over_patch_commits(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair", day=2)
    commit_file(repo, "feature.txt", "feature\n", "feat: add api", day=3)
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == "1.1.0"
    assert "v1.1.0" in tags(repo)


@pytest.mark.depends_on(
    "test_breaking_change_footer_projects_major_release",
    "test_fix_commit_projects_patch_release",
)
def test_major_release_wins_over_minor_and_patch_commits(make_project):
    repo = make_project()
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair", day=2)
    commit_with_body(
        repo,
        "feature.txt",
        "feature\n",
        "feat: add api",
        "BREAKING CHANGE: behavior is replaced",
        day=3,
    )
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert read_version(repo) == "2.0.0"
    assert "v2.0.0" in tags(repo)


@pytest.mark.depends_on("test_docs_commit_does_not_force_release")
def test_docs_only_workflow_makes_no_release_side_effects(make_project):
    repo = make_project()
    commit_file(repo, "README.md", "docs\n", "docs: guide")
    result = psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert result.returncode == 0
    assert read_version(repo) == "1.0.0"
    assert tags(repo) == ["v1.0.0"]
    assert commit_subjects(repo, 1) == ["docs: guide"]


@pytest.mark.depends_on(
    "test_feat_commit_projects_minor_release",
    "test_fix_commit_projects_patch_release",
    "test_print_tag_uses_custom_tag_format",
)
def test_end_to_end_local_release_views_agree(make_project):
    repo = make_project(version_variables=["pkg.py:__version__:nf", "VERSION:*:nf", "RELEASE:*:tf"])
    commit_file(repo, "feature.txt", "feature\n", "feat(cli): add report", day=2)
    commit_file(repo, "fix.txt", "fixed\n", "fix(core): repair parser", day=3)
    projected_version = last_stdout_line(psr(repo, "version", "--print"))
    projected_tag = last_stdout_line(psr(repo, "version", "--print-tag"))
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert projected_version == read_version(repo) == "1.1.0"
    assert projected_tag == "v1.1.0"
    assert (repo / "VERSION").read_text(encoding="utf-8").strip() == projected_version
    assert (repo / "RELEASE").read_text(encoding="utf-8").strip() == projected_tag
    assert projected_tag in tags(repo)
    assert "Add report" in changelog
    assert "Repair parser" in changelog


@pytest.mark.depends_on("test_fix_commit_projects_patch_release")
def test_perf_commit_projects_patch_release(make_project):
    repo = make_project()
    commit_file(repo, "speed.txt", "faster\n", "perf: reduce startup work")
    projected = last_stdout_line(psr(repo, "version", "--print"))
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert projected == read_version(repo) == "1.0.1"
    assert "v1.0.1" in tags(repo)


@pytest.mark.depends_on("test_feat_commit_projects_minor_release")
def test_scope_and_pull_request_are_rendered_in_release_history(make_project):
    repo = make_project()
    commit_file(repo, "ui.txt", "dashboard\n", "feat(ui): add dashboard (#42)")
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "**ui**" in changelog
    assert "Add dashboard" in changelog
    assert "#42" in changelog


@pytest.mark.depends_on("test_fix_commit_projects_patch_release")
def test_release_notice_is_rendered_in_additional_information(make_project):
    repo = make_project()
    commit_with_body(
        repo,
        "compat.txt",
        "compatibility\n",
        "fix: document compatibility",
        "NOTICE: Consumers should refresh their generated client.",
    )
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Additional Release Information" in changelog
    assert "Consumers should refresh their generated client." in changelog


@pytest.mark.depends_on("test_fix_commit_projects_patch_release")
def test_exclude_commit_pattern_removes_matching_history_from_changelog(make_project):
    repo = make_project(
        extra_config="""
        [tool.semantic_release.changelog]
        exclude_commit_patterns = ["^chore"]
        """
    )
    commit_file(repo, "housekeeping.txt", "internal\n", "chore: internal housekeeping", day=2)
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair user flow", day=3)
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Repair user flow" in changelog
    assert "Internal housekeeping" not in changelog


@pytest.mark.depends_on("test_fix_commit_projects_patch_release")
def test_update_mode_preserves_manual_changelog_history(make_project):
    repo = make_project()
    (repo / "CHANGELOG.md").write_text(
        "# CHANGELOG\n\n<!-- version list -->\n\n## 0.9.0\n\n- manual note\n",
        encoding="utf-8",
    )
    git(repo, "add", "CHANGELOG.md", date="2024-01-02T00:00:00+0000")
    git(
        repo,
        "commit",
        "-m",
        "chore: preserve manual history",
        date="2024-01-02T00:00:00+0000",
    )
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair current release", day=3)
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "- manual note" in changelog
    assert "Repair current release" in changelog


@pytest.mark.depends_on("test_prerelease_print_uses_configured_token")
def test_prerelease_print_increments_existing_same_version_prerelease(make_project):
    repo = make_project(version="1.1.0")
    git(repo, "tag", "v1.1.0-rc.1")
    before = (read_version(repo), tags(repo), commit_subjects(repo, 1))
    result = psr(repo, "version", "--prerelease", "--print")
    assert last_stdout_line(result) == "1.1.0-rc.2"
    assert (read_version(repo), tags(repo), commit_subjects(repo, 1)) == before


@pytest.mark.depends_on("test_unknown_commit_does_not_force_release")
def test_default_bump_level_changes_allowed_chore_commit(make_project):
    repo = make_project(
        extra_config="commit_parser_options = { default_bump_level = 2 }"
    )
    commit_file(repo, "maintenance.txt", "maintained\n", "chore: refresh maintenance")
    projected = last_stdout_line(psr(repo, "version", "--print"))
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert projected == read_version(repo) == "1.0.1"
    assert "v1.0.1" in tags(repo)


@pytest.mark.depends_on(
    "test_feat_commit_projects_minor_release",
    "test_fix_commit_projects_patch_release",
)
def test_squashed_conventional_messages_use_highest_bump(make_project):
    repo = make_project()
    commit_with_body(
        repo,
        "squashed.txt",
        "squashed\n",
        "fix: summarize squashed work",
        "* feat: add release option\n\n* docs: explain release option",
    )
    projected = last_stdout_line(psr(repo, "version", "--print"))
    psr(repo, "version", "--no-push", "--no-vcs-release", "--skip-build")
    assert projected == read_version(repo) == "1.1.0"
    assert "v1.1.0" in tags(repo)


@pytest.mark.depends_on("test_docs_commit_does_not_force_release")
def test_strict_mode_rejects_a_history_with_no_release(make_project):
    repo = make_project()
    commit_file(repo, "README.md", "docs\n", "docs: clarify usage")
    before = (read_version(repo), tags(repo), commit_subjects(repo, 1))
    result = psr(
        repo,
        "--strict",
        "version",
        "--no-push",
        "--no-vcs-release",
        "--skip-build",
        check=False,
    )
    assert result.returncode != 0
    assert (read_version(repo), tags(repo), commit_subjects(repo, 1)) == before


@pytest.mark.depends_on("test_fix_commit_projects_patch_release")
def test_strict_mode_rejects_a_non_release_branch(make_project):
    repo = make_project()
    git(repo, "checkout", "-b", "feature")
    commit_file(repo, "fix.txt", "fixed\n", "fix: repair on feature branch")
    result = psr(
        repo,
        "--strict",
        "version",
        "--no-push",
        "--no-vcs-release",
        "--skip-build",
        check=False,
    )
    assert result.returncode != 0
    assert read_version(repo) == "1.0.0"
    assert tags(repo) == ["v1.0.0"]
