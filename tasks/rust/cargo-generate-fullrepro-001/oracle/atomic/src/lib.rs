// Spec2Repo oracle - atomic tests for cargo-generate-fullrepro-001
#![allow(dead_code, unused_imports)]

use cargo_generate::{Cli, GenerateArgs, TemplatePath, Vcs};
use clap::Parser;

fn parse_generate(args: &[&str]) -> GenerateArgs {
    let mut argv = vec!["cargo", "generate"];
    argv.extend_from_slice(args);
    match Cli::parse_from(argv) {
        Cli::Generate(args) => args,
        _ => panic!("expected generate command"),
    }
}

fn try_parse_generate(args: &[&str]) -> Result<Cli, clap::Error> {
    let mut argv = vec!["cargo", "generate"];
    argv.extend_from_slice(args);
    Cli::try_parse_from(argv)
}

/// Verifies: CG-OUT-003
#[test]
fn cli_parses_vcs_git_case_insensitively() {
    let lower = parse_generate(&["--path", "template", "--vcs", "git"]);
    let upper = parse_generate(&["--path", "template", "--vcs", "GIT"]);
    assert!(matches!(lower.vcs, Some(Vcs::Git)));
    assert!(matches!(upper.vcs, Some(Vcs::Git)));
}

/// Verifies: CG-OUT-003
#[test]
fn cli_parses_vcs_none_case_insensitively() {
    let lower = parse_generate(&["--path", "template", "--vcs", "none"]);
    let upper = parse_generate(&["--path", "template", "--vcs", "NONE"]);
    assert!(matches!(lower.vcs, Some(Vcs::None)));
    assert!(matches!(upper.vcs, Some(Vcs::None)));
}

/// Verifies: CG-OUT-003
#[test]
fn cli_rejects_unknown_vcs_values() {
    assert!(try_parse_generate(&["--path", "template", "--vcs", "hg"]).is_err());
}

/// Verifies: CG-OUT-003
#[test]
fn generate_args_default_does_not_force_vcs() {
    let args = parse_generate(&["--path", "template"]);
    assert_eq!(args.template_path.path.as_deref(), Some("template"));
    assert!(args.vcs.is_none());
}

/// Verifies: CG-OUT-003
#[test]
fn cli_leaves_vcs_unset_without_vcs_flag() {
    let args = parse_generate(&["--path", "template"]);
    assert_eq!(args.template_path.path.as_deref(), Some("template"));
    assert!(args.vcs.is_none());
}

/// Verifies: CG-VAL-009
#[test]
fn generate_args_default_selects_library_crate_type() {
    let args = GenerateArgs::default();
    assert!(args.lib);
    assert!(!args.bin);
}

/// Verifies: CG-VAL-009
#[test]
fn generate_args_default_does_not_select_optional_modes() {
    let args = GenerateArgs::default();
    assert!(!args.list_favorites);
    assert!(!args.silent);
    assert!(!args.force);
}

/// Verifies: CG-SRC-003
#[test]
fn template_path_reports_explicit_path_source() {
    let args = parse_generate(&["--path", "template"]);
    assert_eq!(args.template_path.path.as_deref(), Some("template"));
}

/// Verifies: CG-SRC-004
#[test]
fn template_path_reports_explicit_git_source() {
    let args = parse_generate(&["--git", "https://example.test/repo.git"]);
    assert_eq!(
        args.template_path.git.as_deref(),
        Some("https://example.test/repo.git")
    );
}

/// Verifies: CG-INV-006
#[test]
fn template_path_reports_explicit_favorite_source() {
    let args = parse_generate(&["--favorite", "starter"]);
    assert_eq!(args.template_path.favorite.as_deref(), Some("starter"));
}

/// Verifies: CG-SRC-005
#[test]
fn template_path_reports_auto_path_source() {
    let args = parse_generate(&["owner/repo"]);
    assert_eq!(args.template_path.auto_path.as_deref(), Some("owner/repo"));
}

/// Verifies: CG-SRC-009
#[test]
fn template_path_uses_positional_subfolder_for_auto_source() {
    let args = parse_generate(&["owner/repo", "inner"]);
    assert_eq!(args.template_path.auto_path.as_deref(), Some("owner/repo"));
    assert_eq!(args.template_path.subfolder.as_deref(), Some("inner"));
}

/// Verifies: CG-SRC-009
#[test]
fn template_path_uses_auto_path_as_subfolder_with_explicit_git() {
    let args = parse_generate(&["--git", "repo", "inner"]);
    assert_eq!(args.template_path.git.as_deref(), Some("repo"));
    assert_eq!(args.template_path.auto_path.as_deref(), Some("inner"));
}

/// Verifies: CG-SRC-001
#[test]
fn cli_parses_generate_with_path_and_name() {
    let args = parse_generate(&["--path", "template", "--name", "demo"]);
    assert_eq!(args.template_path.path.as_deref(), Some("template"));
    assert_eq!(args.name.as_deref(), Some("demo"));
}

/// Verifies: CG-SRC-001
#[test]
fn cli_parses_generate_alias() {
    let args = match Cli::parse_from(["cargo", "gen", "--path", "template"]) {
        Cli::Generate(args) => args,
        _ => panic!("expected generate command"),
    };
    assert_eq!(args.template_path.path.as_deref(), Some("template"));
}

/// Verifies: CG-SRC-003
#[test]
fn cli_rejects_simultaneous_path_and_git() {
    assert!(try_parse_generate(&["--path", "template", "--git", "repo"]).is_err());
}

/// Verifies: CG-VAL-008
#[test]
fn cli_parses_list_favorites_mode() {
    let args = parse_generate(&["--list-favorites"]);
    assert!(args.list_favorites);
}

/// Verifies: CG-VAL-008
#[test]
fn cli_rejects_list_favorites_with_generation_name() {
    assert!(try_parse_generate(&["--list-favorites", "--name", "demo"]).is_err());
}

/// Verifies: CG-VAL-009
#[test]
fn cli_parses_library_crate_type_flag() {
    let args = parse_generate(&["--path", "template", "--lib"]);
    assert!(args.lib);
    assert!(!args.bin);
}

/// Verifies: CG-VAL-009
#[test]
fn cli_parses_binary_crate_type_flag() {
    let args = parse_generate(&["--path", "template", "--bin"]);
    assert!(args.bin);
    assert!(!args.lib);
}

/// Verifies: CG-VAL-009
#[test]
fn cli_rejects_simultaneous_lib_and_bin() {
    assert!(try_parse_generate(&["--path", "template", "--lib", "--bin"]).is_err());
}

/// Verifies: CG-VAL-006
#[test]
fn cli_collects_multiple_define_values() {
    let args = parse_generate(&["--path", "template", "--define", "a=1", "--define", "b=2"]);
    assert_eq!(args.define, vec!["a=1", "b=2"]);
}

/// Verifies: CG-VAL-006
#[test]
fn cli_parses_template_values_file_alias() {
    let args = parse_generate(&["--path", "template", "--values-file", "values.toml"]);
    assert!(format!("{:?}", args.template_values_file).contains("values.toml"));
}

/// Verifies: CG-OUT-003
#[test]
fn cli_rejects_quiet_without_continue_on_error() {
    assert!(try_parse_generate(&["--path", "template", "--quiet"]).is_err());
}

/// Verifies: CG-OUT-003
#[test]
fn cli_rejects_simultaneous_quiet_and_verbose() {
    assert!(try_parse_generate(&[
        "--path",
        "template",
        "--quiet",
        "--continue-on-error",
        "--verbose",
    ])
    .is_err());
}

/// Verifies: CG-VAL-010
#[test]
fn cli_rejects_silent_without_name() {
    assert!(try_parse_generate(&["--path", "template", "--silent"]).is_err());
}

/// Verifies: CG-SRC-007
#[test]
fn cli_parses_git_branch_flag() {
    let args = parse_generate(&["--git", "https://example.test/repo.git", "--branch", "main"]);
    assert_eq!(
        args.template_path.git.as_deref(),
        Some("https://example.test/repo.git")
    );
}

/// Verifies: CG-SRC-007
#[test]
fn cli_parses_git_tag_flag() {
    let args = parse_generate(&["--git", "https://example.test/repo.git", "--tag", "v1.2.3"]);
    assert_eq!(
        args.template_path.git.as_deref(),
        Some("https://example.test/repo.git")
    );
}

/// Verifies: CG-SRC-007
#[test]
fn cli_parses_git_revision_flag() {
    let args = parse_generate(&["--git", "https://example.test/repo.git", "--rev", "abc123"]);
    assert_eq!(
        args.template_path.git.as_deref(),
        Some("https://example.test/repo.git")
    );
}

/// Verifies: CG-HOOK-007
#[test]
fn cli_parses_allow_commands_flag() {
    let args = parse_generate(&["--path", "template", "--allow-commands"]);
    assert!(args.allow_commands);
}

/// Verifies: CG-OUT-001
#[test]
fn cli_parses_destination_flag() {
    let args = parse_generate(&["--path", "template", "--destination", "out"]);
    assert_eq!(
        args.destination.as_deref(),
        Some(std::path::Path::new("out"))
    );
}
